"""
M6 — e2e 統合テスト

mock backbone + 実 ts_type_vocab.json + 実 Firewall/Evaluator/MaskBuilder/Decoder
で「prompt → 言霊マスク → Firewall→Evaluator → result」 を回す。

GPU 環境で Qwen 7B を回すまで本物の数値は出ないが、パイプラインの結線と
ablation スイッチが期待通り動くことを CPU でも担保する。
"""

from __future__ import annotations

from pathlib import Path

import pytest
import torch

from kojiki_lm.kotodama_decoder import (
    KotodamaConfig,
    KotodamaDecoder,
    KotodamaResult,
)
from kojiki_lm.kotodama_token_mask import KotodamaMaskBuilder, TypeVocabIndex
from kojiki_lm.yomi_evaluator import YomiEvaluator
from kojiki_lm.yomotsu_hirasaka import Verdict, YomotsuHirasaka

from .conftest import MockBackbone, MockTokenizer, MockTypeHead

REAL_VOCAB = Path(__file__).resolve().parent.parent / "config" / "ts_type_vocab.json"


def _humaneval_like_setup(*, mask_enabled=True, firewall_enabled=True):
    """humaneval-ts 風 prompt を 1 つ通すための設定"""
    tok = MockTokenizer({
        # prompt 用
        "function": 200,
        " ": 201,
        "add": 202,
        "(": 203,
        "a": 204,
        ":": 205,
        ",": 206,
        " b": 207,
        ")": 208,
        " { return a + b; }": 209,
        # type-context 後に生成され得るトークン (TypeHead が "number"=3 を返す前提)
        " number": 210,
        "number": 211,
        " string": 212,
        # ハルシネーション源 (mask で弾かれるべき)
        "FooBar": 250,
    })
    backbone = MockBackbone(vocab_size=len(tok), d_model=8, n_layers=2)
    type_head = MockTypeHead(type_vocab_size=256, forced_top_id=3)

    mask_builder = KotodamaMaskBuilder(tok, TypeVocabIndex(REAL_VOCAB))
    firewall = YomotsuHirasaka(YomiEvaluator())

    decoder = KotodamaDecoder(
        mask_builder=mask_builder,
        type_head=type_head,
        firewall=firewall,
        config=KotodamaConfig(
            max_new_tokens=10,
            top_k_types=1,
            firewall_interval=4,
            do_sample=False,
            mask_enabled=mask_enabled,
            firewall_enabled=firewall_enabled,
        ),
    )
    return decoder, backbone, tok


class TestEndToEnd:
    """簡易版 humaneval-ts 1 問の end-to-end 検証"""

    def test_full_mode_returns_result_with_verdict(self):
        decoder, backbone, tok = _humaneval_like_setup()
        result = decoder.generate(
            backbone, tok,
            prompt_text="function add(a:",
            prompt_id="HumanEval_test",
        )
        assert isinstance(result, KotodamaResult)
        assert result.prompt_id == "HumanEval_test"
        assert result.final_verdict is not None
        assert result.final_verdict.verdict in {Verdict.COMMIT, Verdict.REPAIR, Verdict.HALT}
        # mask が掛かるべき step (`:` の直後 = step 0) が masked=True
        assert result.steps[0].masked is True
        # 売り 2 本柱が両方アクティブだったことを記録
        verdict_step_count = sum(1 for s in result.steps if s.verdict is not None)
        assert verdict_step_count >= 1

    def test_no_kotodama_mode_disables_mask(self):
        decoder, backbone, tok = _humaneval_like_setup(mask_enabled=False)
        result = decoder.generate(backbone, tok, "function add(a:")
        # mask_enabled=False なら type-context でも masked=False
        assert all(s.masked is False for s in result.steps)
        # Firewall は引かれる
        assert any(s.verdict is not None for s in result.steps)

    def test_no_firewall_mode_disables_verdicts(self):
        decoder, backbone, tok = _humaneval_like_setup(firewall_enabled=False)
        result = decoder.generate(backbone, tok, "function add(a:")
        # mask は掛かる
        assert any(s.masked for s in result.steps)
        # Firewall は引かれない (verdict 記録なし)
        assert all(s.verdict is None for s in result.steps)
        assert result.final_verdict is None

    def test_vanilla_mode_passes_through(self):
        decoder, backbone, tok = _humaneval_like_setup(
            mask_enabled=False, firewall_enabled=False
        )
        result = decoder.generate(backbone, tok, "function add(a:")
        # 完全 vanilla: マスクなし、Firewall 呼ばれず
        assert all(s.masked is False for s in result.steps)
        assert all(s.verdict is None for s in result.steps)
        assert result.final_verdict is None
        # それでも text は生成される
        assert isinstance(result.text, str)
        assert len(result.generated_ids) > 0


class TestAblationStats:
    """Ablation で mask_step_count が変化することを確認"""

    def test_mask_count_zero_when_disabled(self):
        d_off, b, t = _humaneval_like_setup(mask_enabled=False)
        r_off = d_off.generate(b, t, "function add(a:")
        assert r_off.num_masked_steps == 0

    def test_mask_count_positive_when_enabled(self):
        d_on, b, t = _humaneval_like_setup(mask_enabled=True)
        r_on = d_on.generate(b, t, "function add(a:")
        assert r_on.num_masked_steps >= 1


class TestJudgeHallucinationRate:
    """judge_win_condition.py の hallucination 計算ロジック単体テスト"""

    def test_ts2304_extracted_from_top_codes(self):
        # スクリプトをモジュールとして import
        import importlib.util
        path = Path(__file__).resolve().parent.parent / "scripts" / "eval" / "judge_win_condition.py"
        spec = importlib.util.spec_from_file_location("judge_win_condition", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        aux = {
            "n_total": 100,
            "top_error_codes": [[2304, 7], [1160, 3]],
        }
        assert abs(mod.hallucination_rate_from_aux(aux) - 0.07) < 1e-9

        # TS2304 が無いケース
        aux_no = {"n_total": 100, "top_error_codes": [[1160, 3]]}
        assert mod.hallucination_rate_from_aux(aux_no) == 0.0

        # 空ケース
        assert mod.hallucination_rate_from_aux({"n_total": 0}) == 0.0
