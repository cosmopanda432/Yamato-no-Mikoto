"""KotodamaDecoder の統合テスト (mock backbone + mock TypeHead)"""

from pathlib import Path

import pytest
import torch

from kojiki_lm.kotodama_decoder import (
    KotodamaConfig,
    KotodamaDecoder,
    KotodamaResult,
)
from kojiki_lm.kotodama_token_mask import KotodamaMaskBuilder, TypeVocabIndex
from kojiki_lm.yomi_evaluator import EvaluatorConfig, YomiEvaluator
from kojiki_lm.yomotsu_hirasaka import (
    L3ToL5Payload,
    L5ToL3Verdict,
    Verdict,
    YomotsuHirasaka,
)

from .conftest import MockBackbone, MockTokenizer, MockTypeHead

REAL_VOCAB = Path(__file__).resolve().parent.parent / "config" / "ts_type_vocab.json"


def _build_setup(
    forced_type_id: int = 3,           # "number"
    n_tokens: int = 12,
    firewall_evaluator=None,
):
    """テスト用の決定論セットアップを構築"""
    # 語彙: TS 型キーワード + 識別子
    tok = MockTokenizer({
        "function": 100,
        " ": 101,
        "foo": 102,
        "(": 103,
        "x": 104,
        ":": 105,
        " number": 106,    # type-context 後に期待される
        " string": 107,    # 同上
        "number": 108,
        "string": 109,
        ")": 110,
        "{": 111,
        "}": 112,
        "garbage": 200,    # マスク対象外、出てはならない (type-context 時)
    })
    vocab_size = len(tok)

    backbone = MockBackbone(vocab_size=vocab_size, d_model=8, n_layers=2)
    type_head = MockTypeHead(type_vocab_size=256, forced_top_id=forced_type_id)

    idx = TypeVocabIndex(REAL_VOCAB)
    mask_builder = KotodamaMaskBuilder(tok, idx)

    evaluator = firewall_evaluator or YomiEvaluator(
        EvaluatorConfig(commit_threshold=0.6, halt_threshold=0.2)
    )
    firewall = YomotsuHirasaka(evaluator)

    decoder = KotodamaDecoder(
        mask_builder=mask_builder,
        type_head=type_head,
        firewall=firewall,
        config=KotodamaConfig(
            max_new_tokens=n_tokens,
            firewall_interval=4,
            top_k_types=1,             # mock TypeHead は top-1 が forced_id
            do_sample=False,
        ),
    )
    return decoder, backbone, tok


class TestKotodamaDecoderBasic:
    def test_returns_result(self):
        decoder, backbone, tok = _build_setup()
        result = decoder.generate(backbone, tok, prompt_text="function foo(x:")
        assert isinstance(result, KotodamaResult)
        assert isinstance(result.text, str)
        assert len(result.generated_ids) > 0
        assert result.final_verdict is not None
        assert isinstance(result.final_verdict, L5ToL3Verdict)

    def test_prompt_id_propagated(self):
        decoder, backbone, tok = _build_setup()
        result = decoder.generate(backbone, tok, "function foo(x:", prompt_id="abc123")
        assert result.prompt_id == "abc123"


class TestMaskApplication:
    """売り #1: type-context で TypeHead 由来マスクが logits に -inf として刻まれる"""

    def test_mask_applied_after_type_context(self):
        decoder, backbone, tok = _build_setup()
        result = decoder.generate(backbone, tok, "function foo(x:")
        # `:` の直後は type-context → 1 step 目は masked=True であってほしい
        first = result.steps[0]
        assert first.masked, (
            "type-context (':' 直後) で mask が適用されていない: "
            f"top_type_ids={first.top_type_ids}, num_allowed={first.num_allowed}"
        )
        assert first.num_allowed > 0
        # TypeHead が forced_top_id=3 ("number") を返す設定なので top に 3 が含まれる
        assert 3 in first.top_type_ids

    def test_no_mask_outside_type_context(self):
        decoder, backbone, tok = _build_setup()
        result = decoder.generate(
            backbone, tok, prompt_text="function foo()"  # `:` で終わらない
        )
        # 開始直後は type-context ではないので mask されない
        assert result.steps[0].masked is False
        assert result.steps[0].num_allowed == 0

    def test_masked_step_produces_allowed_token(self):
        """mask がかかった step で生成される next_token_id は mask 内"""
        decoder, backbone, tok = _build_setup()
        # MaskBuilder を直接呼んで TypeHead top-1 の許可集合を取得
        mask = decoder.mask_builder.build_mask_for_type_ids([3])  # "number"
        allowed_ids = {i for i in range(len(mask)) if bool(mask[i].item())}
        assert allowed_ids, "テスト前提: number の許可集合は非空"

        result = decoder.generate(backbone, tok, "function foo(x:")
        first_step = result.steps[0]
        if first_step.masked:
            assert first_step.next_token_id in allowed_ids, (
                f"masked step なのに非許可トークン {first_step.next_token_id} が選ばれた"
            )


class TestFirewallIntegration:
    """売り #2: Firewall 経由で Evaluator 判定が返り、HALT で停止する"""

    def test_firewall_called_at_interval(self):
        decoder, backbone, tok = _build_setup(n_tokens=12)
        result = decoder.generate(backbone, tok, "function foo(x:")
        verdicts_in_steps = [s.verdict for s in result.steps if s.verdict is not None]
        # interval=4 で max_new_tokens=12 → 少なくとも 3 回は引かれる想定
        assert len(verdicts_in_steps) >= 2
        for v in verdicts_in_steps:
            assert v in {"commit", "repair", "halt"}

    def test_halt_verdict_stops_loop(self):
        """常に HALT を返す evaluator を渡せば、最初の firewall check で止まる"""
        def always_halt(payload: L3ToL5Payload) -> L5ToL3Verdict:
            return L5ToL3Verdict(verdict=Verdict.HALT, v_score=0.0)

        decoder, backbone, tok = _build_setup(
            n_tokens=20,
            firewall_evaluator=always_halt,
        )
        result = decoder.generate(backbone, tok, "function foo(x:")
        assert result.halted_early
        assert result.final_verdict.verdict is Verdict.HALT
        # firewall_interval=4 なので 4 step 以内で止まる
        assert len(result.generated_ids) <= 4

    def test_v_score_logged(self):
        decoder, backbone, tok = _build_setup()
        result = decoder.generate(backbone, tok, "function foo(x:")
        verdict_steps = [s for s in result.steps if s.verdict is not None]
        for s in verdict_steps:
            assert s.v_score is not None
            assert 0.0 <= s.v_score <= 1.0


class TestLogitMaskingPhysics:
    """Done 条件: マスク後の logits に物理的に -inf が乗ることを直接観察"""

    def test_masked_fill_creates_neg_inf(self):
        decoder, backbone, tok = _build_setup()

        # 直接 _maybe_apply_mask を呼んで logits を観察
        prompt = "function foo(x:"
        enc = tok(prompt, return_tensors="pt")
        out = backbone(input_ids=enc["input_ids"], output_hidden_states=True)
        last_h = out.hidden_states[-1][:, -1:, :]
        last_logits = out.logits[:, -1, :].clone()

        before_finite = torch.isfinite(last_logits).all().item()
        assert before_finite, "mask 前は全有限であるべき"

        masked, num_allowed, top_ids = decoder._maybe_apply_mask(
            text_buffer=prompt,
            last_hidden=last_h,
            last_logits=last_logits,
        )
        assert masked, "type-context で mask 適用されなかった"
        assert num_allowed > 0
        # -inf を含む & 完全に -inf ではない (許可トークンは finite)
        assert torch.isneginf(last_logits).any().item(), "-inf がどこにも乗っていない"
        assert torch.isfinite(last_logits).any().item(), "全部 -inf になっている (mask が広すぎる)"
