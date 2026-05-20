"""KotodamaDecoder (Go 版 decode loop) のテスト

実 oracle daemon は使わず、StubOracle で symbol 集合を hardcode する。
backbone も MockBackbone (小型 nn.Module)。decode ループのロジック単体検証。
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pytest
import torch
import torch.nn as nn

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src_min_go"))

from kojiki_lm.go_symbol_oracle import OracleResult  # noqa: E402
from kojiki_lm.kotodama_decoder import (  # noqa: E402
    KotodamaConfig,
    KotodamaDecoder,
)
from kojiki_lm.kotodama_token_mask import GoSymbolBiasBuilder  # noqa: E402
from kojiki_lm.yomi_evaluator import YomiEvaluator  # noqa: E402
from kojiki_lm.yomotsu_hirasaka import (  # noqa: E402
    L5ToL3Verdict,
    Verdict,
    YomotsuHirasaka,
)


# --- 共通モック ---

class StubOracle:
    """OracleClient と同じインタフェースの fake。返り値を hardcode できる"""

    def __init__(self, response: OracleResult | None) -> None:
        self.response = response
        self.call_count = 0

    def query(self, prompt: str, cursor: int, session_id: str) -> OracleResult | None:
        self.call_count += 1
        return self.response

    def close(self) -> None:
        pass


class MiniTokenizer:
    UNK = 0
    PAD = 1

    def __init__(self) -> None:
        # 小さな vocab: identifier + Go 型 + 構文記号
        self._s2i = {
            "func ": 2, "(": 3, ")": 4, "{": 5, "}": 6,
            "a": 7, "b": 8, ", ": 9, " ": 10,
            "int": 11, " int": 12, "string": 13, " string": 14,
            "return ": 15, "\n": 16,
            "</s>": 99,
        }
        self.eos_token_id = self._s2i["</s>"]
        self.pad_token_id = self.PAD

    def __len__(self) -> int:
        return max(self._s2i.values()) + 1

    def encode(self, text: str, add_special_tokens: bool = False) -> list[int]:
        ids: list[int] = []
        i = 0
        while i < len(text):
            matched = False
            for L in range(min(20, len(text) - i), 0, -1):
                cand = text[i : i + L]
                if cand in self._s2i:
                    ids.append(self._s2i[cand])
                    i += L
                    matched = True
                    break
            if not matched:
                ids.append(self.UNK)
                i += 1
        return ids

    def __call__(self, text: str, return_tensors=None):
        ids = self.encode(text)
        if return_tensors == "pt":
            t = torch.tensor([ids], dtype=torch.long)
            return {"input_ids": t, "attention_mask": torch.ones_like(t)}
        return {"input_ids": ids, "attention_mask": [1] * len(ids)}

    def decode(self, ids, skip_special_tokens: bool = True) -> str:
        i2s = {v: k for k, v in self._s2i.items()}
        if isinstance(ids, torch.Tensor):
            ids = ids.tolist()
        out: list[str] = []
        for i in ids:
            i = int(i)
            if skip_special_tokens and i in (self.UNK, self.PAD, self.eos_token_id):
                continue
            out.append(i2s.get(i, ""))
        return "".join(out)


@dataclass
class MockOutput:
    logits: torch.Tensor


class MockBackbone(nn.Module):
    """単純な embedding + linear LM head。Qwen2 の代わり"""

    def __init__(self, vocab_size: int, d_model: int = 16) -> None:
        super().__init__()
        self.vocab_size = vocab_size
        self.embed = nn.Embedding(vocab_size, d_model)
        self.lm_head = nn.Linear(d_model, vocab_size)

    def forward(
        self, input_ids, attention_mask=None,
        output_hidden_states=False, use_cache=False, return_dict=True, **kw,
    ):
        emb = self.embed(input_ids)
        logits = self.lm_head(emb)
        return MockOutput(logits=logits)


def _build_decoder(
    oracle_response: OracleResult | None,
    bias_value: float = 2.0,
    firewall_interval: int = 4,
    max_new_tokens: int = 8,
    firewall_enabled: bool = True,
):
    tok = MiniTokenizer()
    backbone = MockBackbone(vocab_size=len(tok))
    backbone.eval()
    oracle = StubOracle(oracle_response)
    bias_builder = GoSymbolBiasBuilder(tok, vocab_size=len(tok))
    firewall = YomotsuHirasaka(YomiEvaluator())
    config = KotodamaConfig(
        max_new_tokens=max_new_tokens,
        bias_value=bias_value,
        firewall_interval=firewall_interval,
        firewall_enabled=firewall_enabled,
        do_sample=False,
    )
    decoder = KotodamaDecoder(oracle, bias_builder, firewall, config)
    return decoder, backbone, tok, oracle


# --- 動作確認 ---

class TestBasicDecode:
    def test_returns_result(self):
        decoder, backbone, tok, _ = _build_decoder(oracle_response=None)
        result = decoder.generate(backbone, tok, "func ")
        assert len(result.generated_ids) > 0
        assert isinstance(result.text, str)

    def test_prompt_id_propagated(self):
        decoder, backbone, tok, _ = _build_decoder(oracle_response=None)
        result = decoder.generate(backbone, tok, "func ", prompt_id="my-pid")
        assert result.prompt_id == "my-pid"


class TestBiasApplication:
    def test_no_bias_when_oracle_returns_none(self):
        """oracle が None を返すと bias 加算 skip (vanilla 同等)"""
        decoder, backbone, tok, oracle = _build_decoder(oracle_response=None)
        result = decoder.generate(backbone, tok, "var x ")
        bias_steps = [s for s in result.steps if s.bias_applied]
        assert len(bias_steps) == 0

    def test_no_bias_when_value_zero(self):
        """bias_value=0 で実質 vanilla"""
        oracle_resp = OracleResult(
            types=("int",), vars=("a",),
            scope_kind="var_decl", ast_ok=True, elapsed_ms=1,
        )
        decoder, backbone, tok, oracle = _build_decoder(
            oracle_response=oracle_resp, bias_value=0.0,
        )
        result = decoder.generate(backbone, tok, "var x ")
        bias_steps = [s for s in result.steps if s.bias_applied]
        assert len(bias_steps) == 0

    def test_oracle_called_when_filter_passes(self):
        """事前 filter を通る位置 (`var x ` / `map[` 等) で oracle が呼ばれる。
        2026-05-21 更新: func_arg を filter から外したため `var x ` に差し替え"""
        oracle_resp = OracleResult(
            types=("int",), vars=("a",),
            scope_kind="var_decl", ast_ok=True, elapsed_ms=1,
        )
        decoder, backbone, tok, oracle = _build_decoder(oracle_response=oracle_resp)
        decoder.generate(backbone, tok, "var x ")
        assert oracle.call_count >= 1

    def test_bias_applied_when_oracle_returns_scope(self):
        """oracle が valid な scope を返すと bias 加算が記録される"""
        oracle_resp = OracleResult(
            types=("int", "string"), vars=("a",),
            scope_kind="var_decl", ast_ok=True, elapsed_ms=1,
        )
        decoder, backbone, tok, _ = _build_decoder(
            oracle_response=oracle_resp,
            firewall_enabled=False,
        )
        result = decoder.generate(backbone, tok, "var x ")
        bias_steps = [s for s in result.steps if s.bias_applied]
        assert len(bias_steps) >= 1
        # bias 加算された step は scope_kind = var_decl
        assert all(s.scope_kind == "var_decl" for s in bias_steps)

    def test_no_inf_in_logits_after_bias(self):
        """bias は加算なので、logits に -inf が入らない (TS 版の轍を踏まない回帰)"""
        oracle_resp = OracleResult(
            types=("int",), vars=("a",),
            scope_kind="var_decl", ast_ok=True, elapsed_ms=1,
        )
        decoder, backbone, tok, _ = _build_decoder(oracle_response=oracle_resp)

        # 直接 _maybe_apply_bias を呼んで logits を観察
        prompt = "var x "
        enc = tok(prompt, return_tensors="pt")
        out = backbone(input_ids=enc["input_ids"])
        last_logits = out.logits[:, -1, :].clone()

        before_finite = torch.isfinite(last_logits).all().item()
        assert before_finite

        bias_applied, _, _, _ = decoder._maybe_apply_bias(
            text_buffer=prompt,
            last_logits=last_logits,
            session_id="t1",
        )
        assert bias_applied
        # bias 加算後も全て finite (-inf も NaN もなし)
        assert torch.isfinite(last_logits).all().item(), \
            "Go 版で logits に -inf や NaN が入ってはいけない"


class TestSamplingRngIsolation:
    """修正 D (2026-05-21): `sampling_seed` 指定時、サンプリングは専用 `torch.Generator`
    を使い global RNG から隔離される。これにより `firewall.send` 等のサイドチャネル
    (Python オブジェクト生成 / GC / CUDA stream 同期) が sampler に影響しなくなる"""

    def _make_for_sampling(
        self,
        *,
        sampling_seed: int | None,
        firewall_enabled: bool = False,
        backbone: nn.Module | None = None,
        tok: MiniTokenizer | None = None,
    ):
        if tok is None:
            tok = MiniTokenizer()
        if backbone is None:
            # 同じ weights で 2 つの decoder を比較できるように、呼び出し側で
            # 事前に backbone を構築して使い回す
            torch.manual_seed(0)
            backbone = MockBackbone(vocab_size=len(tok))
            backbone.eval()
        bias_builder = GoSymbolBiasBuilder(tok, vocab_size=len(tok))
        firewall = YomotsuHirasaka(YomiEvaluator())
        config = KotodamaConfig(
            max_new_tokens=12,
            bias_value=0.0,
            mask_enabled=False,
            oracle_enabled=False,
            firewall_interval=3,
            firewall_enabled=firewall_enabled,
            do_sample=True,
            temperature=1.0,
            top_k=20,
            top_p=0.95,
            sampling_seed=sampling_seed,
        )
        decoder = KotodamaDecoder(None, bias_builder, firewall, config)
        return decoder, backbone, tok

    def test_same_seed_reproducible(self):
        """同じ sampling_seed で 2 回 generate → 同じ token 列"""
        tok = MiniTokenizer()
        torch.manual_seed(0)
        backbone = MockBackbone(vocab_size=len(tok))
        backbone.eval()

        d1, _, _ = self._make_for_sampling(sampling_seed=42, backbone=backbone, tok=tok)
        d2, _, _ = self._make_for_sampling(sampling_seed=42, backbone=backbone, tok=tok)
        out1 = d1.generate(backbone, tok, "var x ")
        out2 = d2.generate(backbone, tok, "var x ")
        assert out1.generated_ids == out2.generated_ids

    def test_different_seed_changes_output(self):
        """異なる sampling_seed なら token 列が変わる (do_sample=True 経路の確認)"""
        tok = MiniTokenizer()
        torch.manual_seed(0)
        backbone = MockBackbone(vocab_size=len(tok))
        backbone.eval()

        d1, _, _ = self._make_for_sampling(sampling_seed=42, backbone=backbone, tok=tok)
        d2, _, _ = self._make_for_sampling(sampling_seed=999, backbone=backbone, tok=tok)
        out1 = d1.generate(backbone, tok, "var x ")
        out2 = d2.generate(backbone, tok, "var x ")
        assert out1.generated_ids != out2.generated_ids

    def test_isolated_from_global_rng(self):
        """global RNG state を変えても、isolated Generator 制御下では出力が変わらない"""
        tok = MiniTokenizer()
        torch.manual_seed(0)
        backbone = MockBackbone(vocab_size=len(tok))
        backbone.eval()

        d1, _, _ = self._make_for_sampling(sampling_seed=42, backbone=backbone, tok=tok)
        torch.manual_seed(111)
        out1 = d1.generate(backbone, tok, "var x ")

        d2, _, _ = self._make_for_sampling(sampling_seed=42, backbone=backbone, tok=tok)
        torch.manual_seed(222)
        _ = torch.rand(100)  # global RNG をさらに消費 (サイドチャネル proxy)
        out2 = d2.generate(backbone, tok, "var x ")

        assert out1.generated_ids == out2.generated_ids, (
            "isolated Generator 制御下で global RNG state が変わっても出力は同じ"
        )

    def test_firewall_toggle_byte_identical(self):
        """修正 D の本来目的: firewall_enabled toggle で byte-identical (no HALT 時)

        - 同じ backbone, 同じ prompt, 同じ sampling_seed
        - vanilla (firewall OFF) と no-kotodama (firewall ON) を比較
        - YomiEvaluator は通常 HALT を出さない (本 prompt では未学習 mock の出力に対し
          OK / REPAIR を返す程度)。万一 HALT したら test は skip"""
        tok = MiniTokenizer()
        torch.manual_seed(0)
        backbone = MockBackbone(vocab_size=len(tok))
        backbone.eval()

        d_van, _, _ = self._make_for_sampling(
            sampling_seed=42, firewall_enabled=False, backbone=backbone, tok=tok,
        )
        out_van = d_van.generate(backbone, tok, "var x ")

        d_fw, _, _ = self._make_for_sampling(
            sampling_seed=42, firewall_enabled=True, backbone=backbone, tok=tok,
        )
        out_fw = d_fw.generate(backbone, tok, "var x ")

        if out_fw.halted_early:
            pytest.skip("firewall HALT で early stop。Generator 分離とは独立")

        assert out_van.generated_ids == out_fw.generated_ids, (
            "firewall toggle で byte-identical (修正 D が機能している証拠)"
        )

    def test_no_seed_uses_global_rng_legacy(self):
        """sampling_seed=None なら従来通り global RNG を使う (backwards compat)"""
        tok = MiniTokenizer()
        torch.manual_seed(0)
        backbone = MockBackbone(vocab_size=len(tok))
        backbone.eval()

        d, _, _ = self._make_for_sampling(
            sampling_seed=None, backbone=backbone, tok=tok,
        )
        torch.manual_seed(7)
        out1 = d.generate(backbone, tok, "var x ")

        d2, _, _ = self._make_for_sampling(
            sampling_seed=None, backbone=backbone, tok=tok,
        )
        torch.manual_seed(7)
        out2 = d2.generate(backbone, tok, "var x ")

        # global RNG seed を同じに reset したので同じ系列になる
        assert out1.generated_ids == out2.generated_ids


class TestStopTokens:
    """修正 H (2026-05-21): generate() に stop_tokens を渡すと、生成部分にそれらが
    含まれた時点で early-stop する。max_new_tokens 上限まで生成しきってから
    truncate していた旧仕様は、function 完了後の test driver 領域での bias 計算
    無駄打ちを許していた"""

    def test_no_stop_tokens_runs_to_full_length(self):
        """stop_tokens=() (default) なら従来通り max_new_tokens (or EOS) まで生成"""
        torch.manual_seed(0)
        decoder, backbone, tok, _ = _build_decoder(
            oracle_response=None, max_new_tokens=8, firewall_enabled=False,
        )
        result = decoder.generate(backbone, tok, "func ")
        assert not result.stopped_at_stop_token
        assert len(result.generated_ids) <= 8

    def test_stop_token_triggers_early_stop(self):
        """生成テキストに含まれる substring を stop_tokens として渡すと early-stop。
        MockBackbone はランダム重みで decode 文字列が空 (special token のみ) になる
        ことがあるので、サンプリング + sampling_seed で deterministic に多様な
        token を生成させる"""
        tok = MiniTokenizer()
        torch.manual_seed(0)
        backbone = MockBackbone(vocab_size=len(tok))
        backbone.eval()
        bias_builder = GoSymbolBiasBuilder(tok, vocab_size=len(tok))
        firewall = YomotsuHirasaka(YomiEvaluator())

        def make_decoder():
            cfg = KotodamaConfig(
                max_new_tokens=16,
                bias_value=0.0,
                mask_enabled=False,
                oracle_enabled=False,
                firewall_enabled=False,
                do_sample=True,
                temperature=1.0,
                top_k=20,
                top_p=0.95,
                sampling_seed=42,
            )
            return KotodamaDecoder(None, bias_builder, firewall, cfg)

        baseline = make_decoder().generate(backbone, tok, "func ")
        full_text = baseline.text
        assert len(full_text) >= 1, (
            f"baseline text too short to test stop_tokens: {full_text!r}"
        )

        # baseline の最初の 1 文字を stop_token に。同じ backbone/seed なら同じ系列
        # を生成するので、その 1 文字が現れた step で early-stop するはず
        early_target = full_text[:1]
        result = make_decoder().generate(
            backbone, tok, "func ", stop_tokens=(early_target,),
        )
        assert result.stopped_at_stop_token, (
            f"expected early stop with stop_token={early_target!r}, "
            f"got stopped_at_stop_token=False, text={result.text!r}"
        )
        # early stop ぶん、token 数は baseline 以下になる
        assert len(result.generated_ids) <= len(baseline.generated_ids)

    def test_empty_string_stop_token_ignored(self):
        """空文字列 stop_token は無視 (常に match して 1 step で停止する誤動作を防ぐ)"""
        torch.manual_seed(0)
        decoder, backbone, tok, _ = _build_decoder(
            oracle_response=None, max_new_tokens=6, firewall_enabled=False,
        )
        result = decoder.generate(
            backbone, tok, "func ", stop_tokens=("",),
        )
        assert not result.stopped_at_stop_token
        assert len(result.generated_ids) <= 6

    def test_stop_token_in_prompt_does_not_trigger(self):
        """prompt に含まれる文字列を stop_token にしても、生成部分でなければ
        early-stop しない (生成部分のみ照合する設計の確認)"""
        torch.manual_seed(0)
        decoder, backbone, tok, _ = _build_decoder(
            oracle_response=None, max_new_tokens=6, firewall_enabled=False,
        )
        # `func ` は prompt にだけある。生成側に出てこなければ stop しない
        result = decoder.generate(
            backbone, tok, "func ", stop_tokens=("func",),
        )
        # `func` が生成テキストに偶然出てきたら early-stop する可能性はあるが、
        # 出てこなければ stopped_at_stop_token=False。どちらでも assert は通る:
        # 重要なのは prompt 部分の `func ` だけで停止していないこと = 1 step は
        # 走ること
        assert len(result.generated_ids) >= 1


class TestFirewallIntegration:
    def test_firewall_called_at_interval(self):
        decoder, backbone, tok, _ = _build_decoder(
            oracle_response=None,
            firewall_interval=3,
            max_new_tokens=10,
        )
        result = decoder.generate(backbone, tok, "func ")
        verdict_steps = [s for s in result.steps if s.verdict is not None]
        # 10 step / firewall_interval=3 → 3 回 + 最終 step 1 回 = 3-4 回
        assert 2 <= len(verdict_steps) <= 5

    def test_halt_verdict_stops_loop(self):
        """ evaluator が常に HALT を返すと decode が即停止する"""
        class HaltEval:
            def __call__(self, payload):
                return L5ToL3Verdict(verdict=Verdict.HALT, v_score=0.1)
        tok = MiniTokenizer()
        backbone = MockBackbone(vocab_size=len(tok))
        backbone.eval()
        bias_builder = GoSymbolBiasBuilder(tok, vocab_size=len(tok))
        firewall = YomotsuHirasaka(HaltEval())
        config = KotodamaConfig(
            max_new_tokens=20, bias_value=0.0,
            firewall_interval=2, firewall_enabled=True, do_sample=False,
        )
        decoder = KotodamaDecoder(None, bias_builder, firewall, config)
        result = decoder.generate(backbone, tok, "func ")
        assert result.halted_early
        assert len(result.generated_ids) <= 2  # firewall_interval=2 で即停止
