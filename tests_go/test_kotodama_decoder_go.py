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
        result = decoder.generate(backbone, tok, "func a(b ")
        bias_steps = [s for s in result.steps if s.bias_applied]
        assert len(bias_steps) == 0

    def test_no_bias_when_value_zero(self):
        """bias_value=0 で実質 vanilla"""
        oracle_resp = OracleResult(
            types=("int",), vars=("a",),
            scope_kind="func_arg", ast_ok=True, elapsed_ms=1,
        )
        decoder, backbone, tok, oracle = _build_decoder(
            oracle_response=oracle_resp, bias_value=0.0,
        )
        result = decoder.generate(backbone, tok, "func a(b ")
        bias_steps = [s for s in result.steps if s.bias_applied]
        assert len(bias_steps) == 0

    def test_oracle_called_when_filter_passes(self):
        """事前 filter を通る位置 (`func a(b `) で oracle が呼ばれる"""
        oracle_resp = OracleResult(
            types=("int",), vars=("a",),
            scope_kind="func_arg", ast_ok=True, elapsed_ms=1,
        )
        decoder, backbone, tok, oracle = _build_decoder(oracle_response=oracle_resp)
        decoder.generate(backbone, tok, "func a(b ")
        assert oracle.call_count >= 1

    def test_bias_applied_when_oracle_returns_scope(self):
        """oracle が valid な scope を返すと bias 加算が記録される"""
        oracle_resp = OracleResult(
            types=("int", "string"), vars=("a",),
            scope_kind="func_arg", ast_ok=True, elapsed_ms=1,
        )
        decoder, backbone, tok, _ = _build_decoder(
            oracle_response=oracle_resp,
            firewall_enabled=False,
        )
        result = decoder.generate(backbone, tok, "func a(b ")
        bias_steps = [s for s in result.steps if s.bias_applied]
        assert len(bias_steps) >= 1
        # bias 加算された step は scope_kind = func_arg
        assert all(s.scope_kind == "func_arg" for s in bias_steps)

    def test_no_inf_in_logits_after_bias(self):
        """bias は加算なので、logits に -inf が入らない (TS 版の轍を踏まない回帰)"""
        oracle_resp = OracleResult(
            types=("int",), vars=("a",),
            scope_kind="func_arg", ast_ok=True, elapsed_ms=1,
        )
        decoder, backbone, tok, _ = _build_decoder(oracle_response=oracle_resp)

        # 直接 _maybe_apply_bias を呼んで logits を観察
        prompt = "func a(b "
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
