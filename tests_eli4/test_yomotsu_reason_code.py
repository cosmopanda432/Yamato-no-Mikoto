"""
事戸拡張 (ReasonCode) のテスト — 產屋 Step B

DoD-B:
  (i)   reason_code / hint の型・長さ validation が正しく raise する
  (ii)  L5ToL3Verdict(verdict=Verdict.HALT, v_score=0.0) が従来通り動く (後方互換)
  (iii) bracket 崩れ入力で BRACKET_MISMATCH が返る

追加:
  - trace-missing 入力 → TRACE_MISSING (verdict HALT, v_score 0.0 は不変)
  - trace-insufficient 入力 → TRACE_INSUFFICIENT
  - COMMIT ケース → NONE
  - 複数フラグが立つ場合の優先順位 (bracket > do_end > bad_pattern > low_score)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src_min_eli4"))

from kojiki_lm.elixir_evaluator import ElixirEvaluator  # noqa: E402
from kojiki_lm.koumyou_so import KoumyouSo  # noqa: E402
from kojiki_lm.yomotsu_hirasaka import (  # noqa: E402
    L3ToL5Payload,
    L5ToL3Verdict,
    ReasonCode,
    Verdict,
)


# ---------------------------------------------------------------------------
# (ii) 後方互換: 既存の 2 引数コンストラクタが従来通り動く
# ---------------------------------------------------------------------------


def test_l5tol3verdict_backward_compat_defaults():
    v = L5ToL3Verdict(verdict=Verdict.HALT, v_score=0.0)
    assert v.verdict == Verdict.HALT
    assert v.v_score == 0.0
    assert v.reason_code == ReasonCode.NONE
    assert v.hint == ""


def test_l5tol3verdict_accepts_reason_code_and_hint():
    v = L5ToL3Verdict(
        verdict=Verdict.HALT,
        v_score=0.0,
        reason_code=ReasonCode.BRACKET_MISMATCH,
        hint="unbalanced parens",
    )
    assert v.reason_code == ReasonCode.BRACKET_MISMATCH
    assert v.hint == "unbalanced parens"


# ---------------------------------------------------------------------------
# (i) reason_code / hint validation
# ---------------------------------------------------------------------------


def test_l5tol3verdict_reason_code_type_error():
    with pytest.raises(TypeError):
        L5ToL3Verdict(verdict=Verdict.HALT, v_score=0.0, reason_code="bracket_mismatch")


def test_l5tol3verdict_hint_type_error():
    with pytest.raises(TypeError):
        L5ToL3Verdict(verdict=Verdict.HALT, v_score=0.0, hint=123)


def test_l5tol3verdict_hint_too_long_raises():
    with pytest.raises(ValueError):
        L5ToL3Verdict(verdict=Verdict.HALT, v_score=0.0, hint="a" * 201)


def test_l5tol3verdict_hint_max_length_ok():
    v = L5ToL3Verdict(verdict=Verdict.HALT, v_score=0.0, hint="a" * 200)
    assert len(v.hint) == 200


def test_l5tol3verdict_existing_validation_unchanged():
    # verdict 型チェックは既存のまま
    with pytest.raises(TypeError):
        L5ToL3Verdict(verdict="commit", v_score=0.0)
    # v_score 範囲チェックは既存のまま
    with pytest.raises(ValueError):
        L5ToL3Verdict(verdict=Verdict.HALT, v_score=1.5)


# ---------------------------------------------------------------------------
# ReasonCode enum の値
# ---------------------------------------------------------------------------


def test_reason_code_enum_values():
    assert ReasonCode.NONE.value == "none"
    assert ReasonCode.TRACE_MISSING.value == "trace_missing"
    assert ReasonCode.TRACE_INSUFFICIENT.value == "trace_insufficient"
    assert ReasonCode.BRACKET_MISMATCH.value == "bracket_mismatch"
    assert ReasonCode.DO_END_MISMATCH.value == "do_end_mismatch"
    assert ReasonCode.BAD_PATTERN.value == "bad_pattern"
    assert ReasonCode.LOW_SCORE.value == "low_score"
    assert ReasonCode.UNDEF_SYMBOL.value == "undef_symbol"


# ---------------------------------------------------------------------------
# (iii) evaluator: reason_code 判定
# ---------------------------------------------------------------------------


def _payload(text: str, prompt_len: int = 0) -> L3ToL5Payload:
    return L3ToL5Payload(text=text, step_idx=0, prompt_id="p", prompt_len=prompt_len)


def test_evaluator_bracket_mismatch():
    ev = ElixirEvaluator()  # koumyou_so=None → light path
    text = "def foo( do\n  :ok\nend"  # 開き括弧が閉じられていない
    verdict = ev(_payload(text))
    assert verdict.verdict != Verdict.COMMIT
    assert verdict.reason_code == ReasonCode.BRACKET_MISMATCH


def test_evaluator_do_end_mismatch():
    ev = ElixirEvaluator()
    text = "def foo do\nend\nend"  # end が do より多い
    verdict = ev(_payload(text))
    assert verdict.verdict != Verdict.COMMIT
    assert verdict.reason_code == ReasonCode.DO_END_MISMATCH


def test_evaluator_bad_pattern():
    ev = ElixirEvaluator()
    text = "def foo do\n  # FIXME need fix\n  :ok\nend"
    verdict = ev(_payload(text))
    assert verdict.verdict != Verdict.COMMIT
    assert verdict.reason_code == ReasonCode.BAD_PATTERN


def test_evaluator_low_score():
    ev = ElixirEvaluator()
    text = "hello world this is plain text over five chars"
    verdict = ev(_payload(text))
    assert verdict.verdict != Verdict.COMMIT
    assert verdict.reason_code == ReasonCode.LOW_SCORE


def test_evaluator_priority_bracket_over_bad_pattern():
    ev = ElixirEvaluator()
    # bracket mismatch AND bad pattern both fire -> BRACKET_MISMATCH should win
    text = "def foo( do\n  # TODO\nend"
    verdict = ev(_payload(text))
    assert verdict.reason_code == ReasonCode.BRACKET_MISMATCH


def test_evaluator_commit_gives_none():
    ev = ElixirEvaluator()
    text = (
        "defmodule Foo do\n"
        "  @spec bar(integer()) :: :ok\n"
        "  def bar(x) do\n"
        "    x |> IO.inspect()\n"
        "    :ok\n"
        "  end\n"
        "end\n"
    )
    verdict = ev(_payload(text))
    assert verdict.verdict == Verdict.COMMIT
    assert verdict.reason_code == ReasonCode.NONE


def test_evaluator_trace_missing():
    ev = ElixirEvaluator(koumyou_so=KoumyouSo())
    text = "def foo() do\n  :ok\nend"  # trace marker が皆無、十分な長さ
    verdict = ev(_payload(text))
    assert verdict.verdict == Verdict.HALT
    assert verdict.v_score == 0.0
    assert verdict.reason_code == ReasonCode.TRACE_MISSING


def test_evaluator_trace_insufficient():
    ev = ElixirEvaluator(koumyou_so=KoumyouSo())
    text = "# 思考: ab\ndef foo do\n  :ok\nend"  # trace はあるが文字数不足
    verdict = ev(_payload(text))
    assert verdict.verdict == Verdict.HALT
    assert verdict.v_score == 0.0
    assert verdict.reason_code == ReasonCode.TRACE_INSUFFICIENT
