"""
`scripts/eval/ts_eval.py` の単体テスト。

data/kojiki/設計書/ts4_実装設計書_v0.md §7 の通り、**実 tsc + node を使う** (ローカル
node v22 / ts_tools/ の `npm ci` 済み typescript を使用、モックしない — スタブでは
tsc の診断コード分類ロジックの正しさを検証できないため)。5 ケース:
  1. pass (compile clean + test 成功)
  2. test fail (compile clean だが assert throw で node が非 0 終了)
  3. TS2304 (undefined + symbol 抽出)
  4. TS1005 系 syntax error
  5. timeout (無限ループ)

tsc は 1 回あたり ~1s なので、本ファイル全体で ~10s 程度の実行時間を許容する。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "eval"))

import ts_eval  # noqa: E402


@pytest.fixture(scope="module")
def tsc_bin():
    return ts_eval.resolve_tsc_bin(None)


@pytest.fixture(scope="module")
def node_bin():
    return ts_eval.resolve_node_bin(None)


# ---------------------------------------------------------------------------
# resolve_tsc_bin fail-fast
# ---------------------------------------------------------------------------


def test_resolve_tsc_bin_uses_explicit_arg():
    assert ts_eval.resolve_tsc_bin("/custom/path/tsc") == "/custom/path/tsc"


def test_resolve_tsc_bin_env_var_takes_priority_over_repo_default(monkeypatch):
    monkeypatch.setenv("TS4_TSC", "/env/path/tsc")
    assert ts_eval.resolve_tsc_bin(None) == "/env/path/tsc"


def test_resolve_tsc_bin_finds_repo_vendored_binary(monkeypatch):
    monkeypatch.delenv("TS4_TSC", raising=False)
    resolved = ts_eval.resolve_tsc_bin(None)
    assert resolved
    assert "ts_tools/node_modules/.bin/tsc" in resolved


def test_resolve_tsc_bin_fails_fast_when_nothing_found(monkeypatch, tmp_path):
    monkeypatch.delenv("TS4_TSC", raising=False)
    monkeypatch.setattr(ts_eval, "REPO_ROOT", tmp_path)  # ts_tools/ が存在しない tmp dir
    monkeypatch.setattr(ts_eval.shutil, "which", lambda name: None)
    with pytest.raises(SystemExit):
        ts_eval.resolve_tsc_bin(None)


def test_resolve_node_bin_fails_fast_when_missing(monkeypatch):
    monkeypatch.setattr(ts_eval.shutil, "which", lambda name: None)
    with pytest.raises(SystemExit):
        ts_eval.resolve_node_bin(None)


# ---------------------------------------------------------------------------
# classify_diagnostics (純粋関数、tsc 出力テキストを直接与える)
# ---------------------------------------------------------------------------


def test_classify_diagnostics_empty_is_clean():
    d = ts_eval.classify_diagnostics("")
    assert d == {
        "has_undefined": False,
        "has_syntax_error": False,
        "has_type_error": False,
        "undef_symbols": [],
        "first_type_error_msg": "",
    }


def test_classify_diagnostics_undef_extracts_symbol():
    stdout = "undef.ts(2,10): error TS2304: Cannot find name 'bar'.\n"
    d = ts_eval.classify_diagnostics(stdout)
    assert d["has_undefined"] is True
    assert d["undef_symbols"] == ["bar"]
    assert d["has_syntax_error"] is False
    assert d["has_type_error"] is False


def test_classify_diagnostics_dedupes_repeated_symbol():
    stdout = (
        "a.ts(1,1): error TS2304: Cannot find name 'bar'.\n"
        "a.ts(2,1): error TS2304: Cannot find name 'bar'.\n"
    )
    d = ts_eval.classify_diagnostics(stdout)
    assert d["undef_symbols"] == ["bar"]


def test_classify_diagnostics_ts1xxx_is_syntax_error():
    stdout = "a.ts(1,5): error TS1005: ',' expected.\n"
    d = ts_eval.classify_diagnostics(stdout)
    assert d["has_syntax_error"] is True
    assert d["has_undefined"] is False
    assert d["has_type_error"] is False


def test_classify_diagnostics_other_ts2xxx_is_type_error():
    stdout = "a.ts(2,3): error TS2322: Type 'number' is not assignable to type 'string'.\n"
    d = ts_eval.classify_diagnostics(stdout)
    assert d["has_type_error"] is True
    assert d["first_type_error_msg"] == "Type 'number' is not assignable to type 'string'."


def test_classify_diagnostics_ts7xxx_is_type_error():
    stdout = "a.ts(1,1): error TS7006: Parameter 'x' implicitly has an 'any' type.\n"
    d = ts_eval.classify_diagnostics(stdout)
    assert d["has_type_error"] is True


def test_classify_diagnostics_syntax_and_type_coexist_is_gated_to_syntax_only():
    """QA 指摘: 構文破壊ファイルで TS1005 (syntax) と TS2xxx (type、パーサ recovery の
    連鎖) が同一診断出力に混在しても、has_type_error は has_syntax_error に負けて False
    になる (clean partition、type_error_rate の二重計上を防ぐ)。実 tsc がこのパターンを
    出す例は下記コメントの通り (syntax.ts への `function foo(x: number { ... }` 相当)。"""
    stdout = (
        "syntax.ts(1,14): error TS2300: Duplicate identifier 'x'.\n"
        "syntax.ts(1,24): error TS1005: ',' expected.\n"
        "syntax.ts(2,10): error TS1005: ':' expected.\n"
        "syntax.ts(2,10): error TS2300: Duplicate identifier 'x'.\n"
        "syntax.ts(2,10): error TS2842: 'x' is an unused renaming of 'return'.\n"
        "syntax.ts(2,12): error TS1005: ',' expected.\n"
        "syntax.ts(3,1): error TS1128: Declaration or statement expected.\n"
    )
    d = ts_eval.classify_diagnostics(stdout)
    assert d["has_syntax_error"] is True
    assert d["has_type_error"] is False
    assert d["first_type_error_msg"] == ""


def test_classify_diagnostics_undefined_and_type_error_still_coexist():
    """undefined と type_error の共存は既存のまま変えない (QA 指摘は syntax/type のみ対象)。"""
    stdout = (
        "a.ts(1,1): error TS2304: Cannot find name 'bar'.\n"
        "a.ts(2,3): error TS2322: Type 'number' is not assignable to type 'string'.\n"
    )
    d = ts_eval.classify_diagnostics(stdout)
    assert d["has_undefined"] is True
    assert d["has_type_error"] is True


def test_classify_diagnostics_undefined_and_syntax_error_still_coexist():
    stdout = (
        "a.ts(1,1): error TS2304: Cannot find name 'bar'.\n"
        "a.ts(2,3): error TS1005: ',' expected.\n"
    )
    d = ts_eval.classify_diagnostics(stdout)
    assert d["has_undefined"] is True
    assert d["has_syntax_error"] is True


# ---------------------------------------------------------------------------
# run_one — 実 tsc + node を使う 5 ケース
# ---------------------------------------------------------------------------


def _sample(name, prompt, completion, tests):
    return {"name": name, "prompt": prompt, "completion": completion, "tests": tests}


def test_run_one_pass(tsc_bin, node_bin):
    sample = _sample(
        "t_pass",
        "function add(a: number, b: number): number {\n",
        "  return a + b;\n}\n",
        "if (add(2, 3) !== 5) { throw new Error('fail'); }\nconsole.log('ok');\n",
    )
    r = ts_eval.run_one(sample, tsc_bin, node_bin, timeout=10.0)
    assert r["compile_ok"] is True
    assert r["test_ok"] is True
    assert r["has_undefined"] is False
    assert r["has_syntax_error"] is False
    assert r["has_type_error"] is False
    assert r["timed_out"] is False
    assert r["exit_code"] == 0


def test_run_one_test_fail(tsc_bin, node_bin):
    """compile は通るが assert throw で node が非 0 終了 → has_assertion_failure。"""
    sample = _sample(
        "t_fail",
        "function add(a: number, b: number): number {\n",
        "  return a + b + 1;\n}\n",
        "if (add(2, 3) !== 5) { throw new Error('fail'); }\nconsole.log('ok');\n",
    )
    r = ts_eval.run_one(sample, tsc_bin, node_bin, timeout=10.0)
    assert r["compile_ok"] is True
    assert r["test_ok"] is False
    assert r["has_assertion_failure"] is True
    assert r["exit_code"] != 0


def test_run_one_undefined_ts2304(tsc_bin, node_bin):
    sample = _sample(
        "t_undef",
        "function foo(): number {\n",
        "  return bar(3);\n}\n",
        "console.log(foo());\n",
    )
    r = ts_eval.run_one(sample, tsc_bin, node_bin, timeout=10.0)
    assert r["compile_ok"] is False
    assert r["test_ok"] is False
    assert r["has_undefined"] is True
    assert r["undef_symbols"] == ["bar"]


def test_run_one_syntax_error_ts1xxx(tsc_bin, node_bin):
    sample = _sample(
        "t_syntax",
        "function foo(x: number {\n",
        "  return x + 1;\n}\n",
        "console.log(foo(1));\n",
    )
    r = ts_eval.run_one(sample, tsc_bin, node_bin, timeout=10.0)
    assert r["compile_ok"] is False
    assert r["test_ok"] is False
    assert r["has_syntax_error"] is True


def test_run_one_timeout(tsc_bin, node_bin):
    sample = _sample(
        "t_timeout",
        "function foo(): number {\n",
        "  while (true) {}\n}\n",
        "console.log(foo());\n",
    )
    r = ts_eval.run_one(sample, tsc_bin, node_bin, timeout=2.0)
    assert r["timed_out"] is True
    assert r["test_ok"] is False
    assert r["exit_code"] == -1


def test_run_one_generic_exception_sets_exit_code_minus_2(tsc_bin, node_bin, monkeypatch):
    """QA 指摘: run_one:277-279 の `except Exception` 分岐 (subprocess.run が
    TimeoutExpired 以外の例外 — 例えば OSError — を raise した場合) のカバー。"""

    def _raise_oserror(*args, **kwargs):
        raise OSError("boom: executable not runnable")

    monkeypatch.setattr(ts_eval.subprocess, "run", _raise_oserror)

    sample = _sample(
        "t_exc",
        "function foo(): number {\n",
        "  return 1;\n}\n",
        "console.log(foo());\n",
    )
    r = ts_eval.run_one(sample, tsc_bin, node_bin, timeout=10.0)
    assert r["exit_code"] == -2
    assert r["test_stderr"].startswith("exception:")
    assert "boom" in r["test_stderr"]
    assert r["test_ok"] is False
    assert r["timed_out"] is False


# ---------------------------------------------------------------------------
# compute_hack_gap (elixir_eval.py と同一定義、言語非依存)
# ---------------------------------------------------------------------------


def test_compute_hack_gap_no_high_score_samples_is_zero():
    samples = [{"final_v_score": 0.5, "test_ok": False}]
    assert ts_eval.compute_hack_gap(samples) == 0.0


def test_compute_hack_gap_computes_ratio():
    samples = [
        {"final_v_score": 0.9, "test_ok": True},
        {"final_v_score": 0.8, "test_ok": False},
        {"final_v_score": 0.2, "test_ok": False},  # v_score < 0.7 は分母に含まない
    ]
    assert ts_eval.compute_hack_gap(samples) == pytest.approx(0.5)
