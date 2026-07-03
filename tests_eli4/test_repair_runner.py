"""
產屋 (ubuya) 還降 loop runner (Step C) の pure function 単体テスト。

DoD-C の unit で検証可能な部分:
  - seed 式 (§5.2, §9): attempt_seed(s,i,0) == s*1_000_003+i、r>=1 では + r*R_STRIDE
  - 如先 (§5.3): hint なし → prompt+TRACE_SEED (round 0 と byte 一致)、
                 hint あり → diff は hint_line 1 行のみ
  - _repair_summary.json 構造 (build_repair_summary) の合成データ検証
  - build_hint stub は常に "" を返す (Step D で処方規則に差し替え)
  - resolve_elixir_bin の fail-fast (repair-on は生成 host に elixir 必須)
  - TRACE_SEED / MODE_FLAGS / truncate_at_stop_tokens が eli3 runner と一致すること
    (round 0 byte-identity の統制条件の前提を静的にも保証する)

GPU/model の実ロードは行わない。runner モジュール自体の import は torch/transformers
を要するが (CPU で可)、main() は一切呼ばず、モジュールレベル関数だけを対象にする。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src_min_eli4"))

_RUNNER_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "eval" / "run_yamato_min_elixir4.py"
)
_ELI3_RUNNER_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "eval" / "run_yamato_min_elixir3.py"
)


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def runner():
    return _load_module(_RUNNER_PATH, "run_yamato_min_elixir4")


@pytest.fixture(scope="module")
def eli3_runner():
    return _load_module(_ELI3_RUNNER_PATH, "run_yamato_min_elixir3")


# ---------------------------------------------------------------------------
# seed 式 (§5.2 統制条件, §9)
# ---------------------------------------------------------------------------


def test_attempt_seed_round0_matches_eli3_formula(runner):
    assert runner.attempt_seed(0, 0, 0) == 0 * 1_000_003 + 0
    assert runner.attempt_seed(7, 3, 0) == 7 * 1_000_003 + 3


def test_attempt_seed_round_r_adds_stride(runner):
    base = 7 * 1_000_003 + 3
    assert runner.attempt_seed(7, 3, 1) == base + 1 * runner.R_STRIDE
    assert runner.attempt_seed(7, 3, 2) == base + 2 * runner.R_STRIDE


def test_r_stride_is_large_prime_constant(runner):
    assert runner.R_STRIDE == 999_999_937


# ---------------------------------------------------------------------------
# 如先 (§5.3): wrapped_prompt 構成
# ---------------------------------------------------------------------------


def test_wrapped_prompt_no_hint_matches_round0(runner):
    prompt = "defmodule Foo do\n  def bar(x) do\n"
    round0_style = prompt + runner.TRACE_SEED  # eli3 line 189 と同形の式
    assert runner.build_wrapped_prompt(prompt, "", True) == round0_style


def test_wrapped_prompt_with_hint_diff_is_hint_line_only(runner):
    prompt = "defmodule Foo do\n  def bar(x) do\n"
    no_hint = runner.build_wrapped_prompt(prompt, "", True)
    with_hint = runner.build_wrapped_prompt(prompt, "型を確認せよ", True)

    assert with_hint != no_hint
    assert with_hint.startswith(prompt)
    assert with_hint.endswith(runner.TRACE_SEED)

    inserted = with_hint[len(prompt): len(with_hint) - len(runner.TRACE_SEED)]
    assert inserted == runner.build_hint_line("型を確認せよ")
    assert inserted.count("\n") == 1
    # prompt と TRACE_SEED はそのまま保たれている (hint 以外の prompt 差分を作らない, §8-7)
    assert with_hint == prompt + inserted + runner.TRACE_SEED


def test_wrapped_prompt_koumyou_disabled_no_trace_seed(runner):
    prompt = "defmodule Foo do\n"
    assert runner.build_wrapped_prompt(prompt, "", False) == prompt
    assert runner.build_wrapped_prompt(prompt, "note", False) == (
        prompt + runner.build_hint_line("note")
    )


def test_wrapped_prompt_with_real_build_hint_undef_symbol_diff_is_hint_line_only(runner):
    """如先の担保 (§6.2): 実 build_hint 出力を使った retry でも round 0 との
    diff は hint_line 1 行のみであること。"""
    prompt = "defmodule Foo do\n  def bar(x) do\n"
    round0 = runner.build_wrapped_prompt(prompt, "", True)

    eval_result = {
        "undef_symbols": ["Enum.fitler/2"],
        "did_you_mean": ["filter/2"],
        "reason_code": "undef_symbol",
    }
    hint = runner.build_hint(eval_result)
    assert hint != ""

    retry = runner.build_wrapped_prompt(prompt, hint, True)
    assert retry != round0
    assert retry == prompt + runner.build_hint_line(hint) + runner.TRACE_SEED


def test_wrapped_prompt_with_real_build_hint_trace_halt_matches_round0(runner):
    """如先の担保 (§6.2): 光明想 HALT (trace_*) の hint は "" なので、
    retry の wrapped_prompt は round 0 と byte 一致する。"""
    prompt = "defmodule Foo do\n  def bar(x) do\n"
    round0 = runner.build_wrapped_prompt(prompt, "", True)

    eval_result = {"undef_symbols": [], "reason_code": "trace_missing"}
    hint = runner.build_hint(eval_result)
    assert hint == ""

    retry = runner.build_wrapped_prompt(prompt, hint, True)
    assert retry == round0


def test_wrapped_prompt_trace_halt_with_undef_symbols_still_matches_round0(runner):
    """如先の担保 (§6.2、reviewer 指摘の衝突経路): post-hoc eval が halted_early な
    attempt に対しても走り、たまたま undef_symbols が非空になったとしても、
    reason_code が trace_missing/trace_insufficient なら hint なしのまま
    (undef_symbols チェックより trace_* 判定が優先される)。"""
    prompt = "defmodule Foo do\n  def bar(x) do\n"
    round0 = runner.build_wrapped_prompt(prompt, "", True)

    for reason in ("trace_missing", "trace_insufficient"):
        eval_result = {
            "undef_symbols": ["Enum.fitler/2"],
            "did_you_mean": ["filter/2"],
            "reason_code": reason,
        }
        hint = runner.build_hint(eval_result)
        assert hint == ""

        retry = runner.build_wrapped_prompt(prompt, hint, True)
        assert retry == round0


# ---------------------------------------------------------------------------
# build_hint (Step D §6.2 処方規則)
# ---------------------------------------------------------------------------


def test_build_hint_no_undef_no_trace_is_empty(runner):
    assert runner.build_hint({}) == ""
    # has_undefined はあるが undef_symbols が空 (regex 未マッチ) なら hint なし
    assert runner.build_hint({"reason_code": "undef_symbol", "test_stderr": "boom"}) == ""


def test_build_hint_single_undef_symbol_with_dym(runner):
    eval_result = {
        "undef_symbols": ["Enum.fitler/2"],
        "did_you_mean": ["filter/2"],
        "reason_code": "undef_symbol",
    }
    assert runner.build_hint(eval_result) == "Enum.fitler/2 は未定義。候補: filter/2"


def test_build_hint_single_undef_symbol_no_dym(runner):
    eval_result = {
        "undef_symbols": ["MyModule"],
        "did_you_mean": [],
        "reason_code": "undef_symbol",
    }
    assert runner.build_hint(eval_result) == "MyModule は未定義"


def test_build_hint_dym_capped_at_2(runner):
    eval_result = {
        "undef_symbols": ["Enum.fitler/2"],
        "did_you_mean": ["filter/2", "filter/3", "reject/2"],
        "reason_code": "undef_symbol",
    }
    assert runner.build_hint(eval_result) == "Enum.fitler/2 は未定義。候補: filter/2, filter/3"


def test_build_hint_symbols_capped_at_2(runner):
    eval_result = {
        "undef_symbols": ["Foo.bar/1", "Baz.qux/2", "Ignored.sym/0"],
        "did_you_mean": [],
        "reason_code": "undef_symbol",
    }
    hint = runner.build_hint(eval_result)
    assert "Foo.bar/1" in hint
    assert "Baz.qux/2" in hint
    assert "Ignored.sym/0" not in hint


def test_build_hint_truncated_to_200_chars(runner):
    long_sym = "A" * 250 + "/1"
    eval_result = {"undef_symbols": [long_sym], "did_you_mean": [], "reason_code": "undef_symbol"}
    hint = runner.build_hint(eval_result)
    assert len(hint) <= 200


def test_build_hint_koumyou_halt_trace_missing_is_empty(runner):
    eval_result = {"undef_symbols": [], "reason_code": "trace_missing"}
    assert runner.build_hint(eval_result) == ""


def test_build_hint_koumyou_halt_trace_insufficient_is_empty(runner):
    eval_result = {"undef_symbols": [], "reason_code": "trace_insufficient"}
    assert runner.build_hint(eval_result) == ""


def test_build_hint_trace_missing_wins_over_undef_symbols(runner):
    """reason_code (resolve_reason_code の優先順位1) は trace_missing/insufficient
    のとき undef_symbols より優先される (§6.2)。post-hoc eval が halted_early な
    attempt に対しても走るため、部分コードがたまたま undef_symbols を生む
    ケースがあり得るが、それでも hint なしになるべき (reviewer 指摘)。"""
    eval_result = {
        "undef_symbols": ["Enum.fitler/2"],
        "did_you_mean": ["filter/2"],
        "reason_code": "trace_missing",
    }
    assert runner.build_hint(eval_result) == ""


def test_build_hint_trace_insufficient_wins_over_undef_symbols(runner):
    eval_result = {
        "undef_symbols": ["Enum.fitler/2"],
        "did_you_mean": ["filter/2"],
        "reason_code": "trace_insufficient",
    }
    assert runner.build_hint(eval_result) == ""


def test_build_hint_other_reasons_are_empty(runner):
    for reason in ("bracket_mismatch", "do_end_mismatch", "bad_pattern", "low_score", "none"):
        eval_result = {"undef_symbols": [], "reason_code": reason}
        assert runner.build_hint(eval_result) == ""


def test_build_hint_result_fits_l5_verdict_hint_len_constraint(runner):
    from kojiki_lm.yomotsu_hirasaka import L5ToL3Verdict, ReasonCode, Verdict

    long_sym = "B" * 250 + "/3"
    eval_result = {"undef_symbols": [long_sym], "did_you_mean": [], "reason_code": "undef_symbol"}
    hint = runner.build_hint(eval_result)
    # L5ToL3Verdict.hint の <=200 制約 (§6.2) を満たす文字列であることを実際に
    # dataclass 経由で検証する。
    v = L5ToL3Verdict(verdict=Verdict.HALT, v_score=0.0, reason_code=ReasonCode.NONE, hint=hint)
    assert len(v.hint) <= 200


# ---------------------------------------------------------------------------
# resolve_reason_code (post-hoc + in-loop verdict の統合)
# ---------------------------------------------------------------------------


def test_resolve_reason_code_prefers_verdict_reason(runner):
    from kojiki_lm.yomotsu_hirasaka import L5ToL3Verdict, ReasonCode, Verdict

    fv = L5ToL3Verdict(verdict=Verdict.HALT, v_score=0.0, reason_code=ReasonCode.BRACKET_MISMATCH)
    assert runner.resolve_reason_code(fv, {"has_undefined": True}) == "bracket_mismatch"


def test_resolve_reason_code_falls_back_to_undef_symbol(runner):
    assert runner.resolve_reason_code(None, {"has_undefined": True}) == "undef_symbol"


def test_resolve_reason_code_none_when_nothing_fires(runner):
    assert runner.resolve_reason_code(None, {"has_undefined": False}) == "none"


# ---------------------------------------------------------------------------
# resolve_elixir_bin fail-fast (repair-on は生成 host に elixir 必須)
# ---------------------------------------------------------------------------


def test_resolve_elixir_bin_uses_explicit_arg(runner):
    assert runner.resolve_elixir_bin("/custom/path/elixir") == "/custom/path/elixir"


def test_resolve_elixir_bin_finds_on_path(runner):
    # このサンドボックスでは elixir が PATH 上にある (asdf)
    resolved = runner.resolve_elixir_bin(None)
    assert resolved
    assert "elixir" in resolved


def test_resolve_elixir_bin_fails_fast_when_missing(runner, monkeypatch):
    monkeypatch.setattr(runner.shutil, "which", lambda name: None)
    with pytest.raises(SystemExit):
        runner.resolve_elixir_bin(None)


# ---------------------------------------------------------------------------
# _repair_summary.json 構造 (build_repair_summary、合成データ)
# ---------------------------------------------------------------------------


def _synthetic_attempts():
    return {
        # round 0 で即成功
        "HumanEval_0": [
            {"round": 0, "test_ok": True, "hint_used": "", "repair_reason": ""},
        ],
        # round 0 失敗 -> round 1 で救済
        "HumanEval_1": [
            {"round": 0, "test_ok": False, "hint_used": "", "repair_reason": ""},
            {"round": 1, "test_ok": True, "hint_used": "", "repair_reason": "undef_symbol"},
        ],
        # round 0, 1, 2 全滅 (max_rounds=2 消尽)
        "HumanEval_2": [
            {"round": 0, "test_ok": False, "hint_used": "", "repair_reason": ""},
            {"round": 1, "test_ok": False, "hint_used": "", "repair_reason": "bracket_mismatch"},
            {"round": 2, "test_ok": False, "hint_used": "", "repair_reason": "bracket_mismatch"},
        ],
    }


def test_build_repair_summary_structure(runner):
    attempts = _synthetic_attempts()
    summary = runner.build_repair_summary(attempts, max_rounds=2)

    assert summary["n_prompts"] == 3
    assert summary["max_rounds"] == 2
    assert summary["per_round_pass"] == [1, 1, 0]
    assert summary["n_recovered"] == 1
    # total attempts = 1 + 2 + 3 = 6 / 3 prompts = 2.0
    assert summary["avg_attempts"] == pytest.approx(2.0)
    assert summary["hints_used"] == {"undef_symbol": 1, "bracket_mismatch": 2}


def test_build_repair_summary_no_prompts_is_safe(runner):
    summary = runner.build_repair_summary({}, max_rounds=2)
    assert summary["n_prompts"] == 0
    assert summary["avg_attempts"] == 0.0
    assert summary["per_round_pass"] == [0, 0, 0]
    assert summary["n_recovered"] == 0
    assert summary["hints_used"] == {}


# ---------------------------------------------------------------------------
# eli3 との静的整合性 (round 0 byte-identity の前提条件)
# ---------------------------------------------------------------------------


def test_trace_seed_matches_eli3(runner, eli3_runner):
    assert runner.TRACE_SEED == eli3_runner.TRACE_SEED


def test_mode_flags_superset_of_eli3(runner, eli3_runner):
    for mode, flags in eli3_runner.MODE_FLAGS.items():
        assert runner.MODE_FLAGS[mode] == flags
    assert "repair-on" in runner.MODE_FLAGS
    assert runner.MODE_FLAGS["repair-on"] == runner.MODE_FLAGS["koumyou-on"]


def test_truncate_at_stop_tokens_matches_eli3(runner, eli3_runner):
    text = "abc STOP def"
    assert runner.truncate_at_stop_tokens(text, ["STOP"]) == (
        eli3_runner.truncate_at_stop_tokens(text, ["STOP"])
    )
