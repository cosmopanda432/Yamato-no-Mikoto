"""
Firewall (yomotsu_hirasaka) — Go 版テスト

TS 版から bit-for-bit 流用しているため、テスト内容は等価。Go 版 import から
辿れること、Go 用 Evaluator と組み合わせても挙動が変わらないことを担保する。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch

# src_min_go をテスト import path に通す
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src_min_go"))

from kojiki_lm.yomotsu_hirasaka import (  # noqa: E402
    L3ToL5Payload,
    L5ToL3Verdict,
    Verdict,
    YomotsuHirasaka,
)


# --- L3ToL5Payload ---

class TestL3ToL5Payload:
    def test_valid_payload(self):
        p = L3ToL5Payload(text="hello", step_idx=1, prompt_id="p1")
        assert p.text == "hello"
        assert p.step_idx == 1

    def test_rejects_tensor_like_text(self):
        with pytest.raises(TypeError, match="must be str"):
            L3ToL5Payload(text=torch.zeros(3), step_idx=1, prompt_id="p1")  # type: ignore[arg-type]

    def test_rejects_dict_text(self):
        with pytest.raises(TypeError, match="must be str"):
            L3ToL5Payload(text={"hidden_state": 1}, step_idx=1, prompt_id="p1")  # type: ignore[arg-type]

    def test_rejects_non_int_step(self):
        with pytest.raises(TypeError, match="must be int"):
            L3ToL5Payload(text="x", step_idx="1", prompt_id="p1")  # type: ignore[arg-type]

    def test_rejects_negative_step(self):
        with pytest.raises(ValueError, match=">= 0"):
            L3ToL5Payload(text="x", step_idx=-1, prompt_id="p1")

    def test_frozen(self):
        p = L3ToL5Payload(text="hello", step_idx=1, prompt_id="p1")
        with pytest.raises(Exception):
            p.text = "modified"  # type: ignore[misc]


# --- L5ToL3Verdict ---

class TestL5ToL3Verdict:
    def test_valid_verdict(self):
        v = L5ToL3Verdict(verdict=Verdict.COMMIT, v_score=0.85)
        assert v.verdict is Verdict.COMMIT

    def test_rejects_string_verdict(self):
        with pytest.raises(TypeError, match="Verdict enum"):
            L5ToL3Verdict(verdict="commit", v_score=0.85)  # type: ignore[arg-type]

    def test_rejects_out_of_range_v_score(self):
        with pytest.raises(ValueError, match=r"\[0\.0, 1\.0\]"):
            L5ToL3Verdict(verdict=Verdict.COMMIT, v_score=1.5)

    def test_rejects_non_numeric_v_score(self):
        with pytest.raises(TypeError, match="must be float"):
            L5ToL3Verdict(verdict=Verdict.COMMIT, v_score="0.5")  # type: ignore[arg-type]


# --- YomotsuHirasaka ---

class TestYomotsuHirasaka:
    def test_send_returns_verdict(self):
        def evaluator(p):
            return L5ToL3Verdict(verdict=Verdict.COMMIT, v_score=0.9)
        gw = YomotsuHirasaka(evaluator)
        result = gw.send(L3ToL5Payload(text="ok", step_idx=0, prompt_id="p1"))
        assert result.verdict is Verdict.COMMIT

    def test_send_rejects_non_payload(self):
        gw = YomotsuHirasaka(lambda p: L5ToL3Verdict(Verdict.COMMIT, 0.9))
        with pytest.raises(TypeError, match="requires L3ToL5Payload"):
            gw.send("just a string")  # type: ignore[arg-type]

    def test_send_rejects_evaluator_returning_wrong_type(self):
        gw = YomotsuHirasaka(lambda p: {"verdict": "commit", "v_score": 0.9})  # type: ignore[arg-type]
        with pytest.raises(TypeError, match="must return L5ToL3Verdict"):
            gw.send(L3ToL5Payload(text="ok", step_idx=0, prompt_id="p1"))

    def test_init_rejects_non_callable(self):
        with pytest.raises(TypeError, match="callable evaluator"):
            YomotsuHirasaka(evaluator="not callable")  # type: ignore[arg-type]
