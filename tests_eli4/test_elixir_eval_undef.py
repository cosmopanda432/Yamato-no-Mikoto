"""
`scripts/eval/elixir_eval.py` の additive 拡張 (產屋 Step D §6.1) 単体テスト。

対象:
  - `run_one` result に追加される `undef_symbols` / `did_you_mean` /
    `final_v_score` / `final_verdict` field
  - `_summary.json` に追加される `hack_gap`
  - 既存 field / 既存 metric の意味が変わっていないことの回帰確認

elixir が PATH に無い環境でも regex 抽出そのものは fixture 文字列で検証できるよう
分離する (DoD-D (i))。実 elixir 実行を伴うテストのみ `skipif` する。
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src_min_eli4"))

_MODULE_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "eval" / "elixir_eval.py"
)


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def ee():
    return _load_module(_MODULE_PATH, "elixir_eval_for_test")


# ---------------------------------------------------------------------------
# regex 抽出 (fixture stderr 文字列を直接通す — elixir 不要)
# ---------------------------------------------------------------------------

# 実 elixir 1.19.5 (asdf, Erlang/OTP 27) で `Enum.fitler/2` を実行して得た実際の
# combined (stderr + "\n" + stdout) 全文をそのまま貼付 (Step D 実装時に採取)。
_REAL_STDERR_UNDEF_FUNC = (
    "    warning: Enum.fitler/2 is undefined or private. Did you mean:\n\n"
    "        * filter/2\n\n"
    "    │\n"
    "  3 │     Enum.fitler(xs, fn x -> x > 0 end)\n"
    "    │          ~\n"
    "    │\n"
    "    └─ /tmp/undef_fixture.exs:3:10: Sample.foo/1\n"
)

_REAL_STDOUT_UNDEF_FUNC = (
    "Running ExUnit with seed: 971139, max_cases: 4\n\n\n\n"
    "  1) test foo (SampleTest)\n"
    "     /tmp/undef_fixture.exs:12\n"
    "     ** (UndefinedFunctionError) function Enum.fitler/2 is undefined or private."
    " Did you mean:\n\n"
    "         * filter/2\n\n"
    "     code: assert Sample.foo([1, 2, 3]) == [1, 2, 3]\n"
    "     stacktrace:\n"
    "       (elixir 1.19.5) Enum.fitler([1, 2, 3], #Function<0.67662795/1 in Sample.foo/1>)\n"
    "       /tmp/undef_fixture.exs:13: (test)\n\n\n"
    "Finished in 0.03 seconds (0.03s on load, 0.00s async, 0.00s sync)\n"
    "1 test, 1 failure\n"
)

_REAL_COMBINED_UNDEF_MODULE = (
    "    warning: NoSuchModule.bar/1 is undefined (module NoSuchModule is not"
    " available or is yet to be defined). Make sure the module name is correct"
    " and has been specified in full (or that an alias has been defined)\n"
    "\n"
    "  1) test foo (SampleTest)\n"
    "     ** (UndefinedFunctionError) function NoSuchModule.bar/1 is undefined"
    " (module NoSuchModule is not available). Make sure the module name is"
    " correct and has been specified in full (or that an alias has been defined)\n"
)


def test_extract_undef_func_and_dym_from_real_stderr_fixture(ee):
    combined = _REAL_STDERR_UNDEF_FUNC + "\n" + _REAL_STDOUT_UNDEF_FUNC
    undef_symbols = ee.extract_undef_symbols(combined)
    dym = ee.extract_did_you_mean(combined)

    assert "Enum.fitler/2" in undef_symbols
    assert dym == ["filter/2"]


def test_extract_undef_module_from_real_stderr_fixture(ee):
    undef_symbols = ee.extract_undef_symbols(_REAL_COMBINED_UNDEF_MODULE)
    assert "NoSuchModule.bar/1" in undef_symbols
    assert "NoSuchModule" in undef_symbols


# 実 elixir 1.19.5 で `Enum.memberr?/2` (`?` 付き関数名) を実行して得た実際の
# combined 全文 (brief §6.1 が明示的に "Elixir の関数名は `?` `!` を含み得る" と
# 検証必須事項として挙げているケース)。
_REAL_COMBINED_UNDEF_FUNC_WITH_QUESTION_MARK = (
    "    warning: Enum.memberr?/2 is undefined or private. Did you mean:\n\n"
    "        * member?/2\n\n"
    "    │\n"
    "  3 │     Enum.memberr?(xs, 1)\n"
    "    │          ~\n"
    "    │\n"
    "    └─ /tmp/undef_bang_q.exs:3:10: Sample.foo/1\n"
    "\n"
    "  1) test foo (SampleTest)\n"
    "     ** (UndefinedFunctionError) function Enum.memberr?/2 is undefined or"
    " private. Did you mean:\n\n"
    "         * member?/2\n\n"
    "     code: assert Sample.foo([1, 2, 3]) == true\n"
)


def test_extract_undef_func_and_dym_with_question_mark_symbol(ee):
    combined = _REAL_COMBINED_UNDEF_FUNC_WITH_QUESTION_MARK
    undef_symbols = ee.extract_undef_symbols(combined)
    dym = ee.extract_did_you_mean(combined)

    assert "Enum.memberr?/2" in undef_symbols
    assert dym == ["member?/2"]


def test_extract_undef_symbols_empty_when_no_error(ee):
    assert ee.extract_undef_symbols("all good, 1 test, 0 failures") == []
    assert ee.extract_did_you_mean("all good, 1 test, 0 failures") == []


def test_extract_dedupes_preserving_order(ee):
    combined = _REAL_STDERR_UNDEF_FUNC + "\n" + _REAL_STDOUT_UNDEF_FUNC
    # 同じ symbol / did-you-mean item が stderr と stdout の両方に出現するが
    # dedupe されて 1 度だけ現れること
    undef_symbols = ee.extract_undef_symbols(combined)
    dym = ee.extract_did_you_mean(combined)
    assert undef_symbols.count("Enum.fitler/2") == 1
    assert dym.count("filter/2") == 1


# ---------------------------------------------------------------------------
# run_one() result への field 追加 (elixir 不要 — sample dict を直接組み立てる)
# ---------------------------------------------------------------------------


def test_run_one_result_has_final_v_score_and_verdict_transcribed(ee, monkeypatch):
    # subprocess を叩かず run_one の transcribe 部分だけを検証したいので、
    # 存在しない elixir_bin を渡して except 経路 (exception) に落ちても
    # sample.get() の転記は run_one 冒頭で行われることを期待する。
    sample = {
        "name": "HumanEval_0",
        "seed": 0,
        "prompt": "defmodule Sample do\n",
        "completion": "end\n",
        "tests": "",
        "final_v_score": 0.85,
        "final_verdict": "commit",
    }
    r = ee.run_one(sample, elixir_bin="/nonexistent/elixir/binary/xyz", timeout=1.0)
    assert r["final_v_score"] == 0.85
    assert r["final_verdict"] == "commit"
    assert "undef_symbols" in r
    assert "did_you_mean" in r


def test_run_one_result_defaults_when_sample_lacks_fields(ee):
    sample = {
        "name": "HumanEval_1",
        "seed": 0,
        "prompt": "defmodule Sample do\n",
        "completion": "end\n",
        "tests": "",
    }
    r = ee.run_one(sample, elixir_bin="/nonexistent/elixir/binary/xyz", timeout=1.0)
    assert r["final_v_score"] is None
    assert r["final_verdict"] is None
    assert r["undef_symbols"] == []
    assert r["did_you_mean"] == []


@pytest.mark.skipif(shutil.which("elixir") is None, reason="elixir not on PATH")
def test_run_one_extracts_from_real_elixir_undefined_function(ee):
    prompt = "defmodule Sample do\n  def foo(xs) do\n    Enum.fitler(xs, fn x -> x > 0 end)\n  end\nend\n"
    tests = (
        "ExUnit.start()\n\n"
        "defmodule SampleTest do\n"
        "  use ExUnit.Case\n\n"
        "  test \"foo\" do\n"
        "    assert Sample.foo([1, 2, 3]) == [1, 2, 3]\n"
        "  end\n"
        "end\n"
    )
    sample = {
        "name": "HumanEval_live_undef",
        "seed": 0,
        "prompt": prompt,
        "completion": "",
        "tests": tests,
    }
    elixir_bin = shutil.which("elixir")
    r = ee.run_one(sample, elixir_bin=elixir_bin, timeout=10.0)

    assert r["test_ok"] is False
    assert r["has_undefined"] is True
    assert "Enum.fitler/2" in r["undef_symbols"]
    assert "filter/2" in r["did_you_mean"]


# ---------------------------------------------------------------------------
# hack_gap (§6.1) — 不浄観 audit: in-loop proxy COMMIT の post-hoc 否定率
# ---------------------------------------------------------------------------


def test_hack_gap_basic_ratio(ee):
    samples = [
        {"final_v_score": 0.9, "test_ok": False},  # proxy COMMIT, 大地は否定
        {"final_v_score": 0.75, "test_ok": True},   # proxy COMMIT, 大地も肯定
        {"final_v_score": 0.5, "test_ok": False},   # 閾値未満 -> 分母に含めない
        {"final_v_score": None, "test_ok": False},  # None -> 分母に含めない
    ]
    assert ee.compute_hack_gap(samples) == pytest.approx(0.5)


def test_hack_gap_zero_denominator_is_zero(ee):
    samples = [
        {"final_v_score": 0.5, "test_ok": False},
        {"final_v_score": None, "test_ok": True},
    ]
    assert ee.compute_hack_gap(samples) == 0.0


def test_hack_gap_empty_list_is_zero(ee):
    assert ee.compute_hack_gap([]) == 0.0


def test_hack_gap_all_recovered_is_zero(ee):
    samples = [
        {"final_v_score": 0.9, "test_ok": True},
        {"final_v_score": 0.8, "test_ok": True},
    ]
    assert ee.compute_hack_gap(samples) == 0.0


def test_hack_gap_boundary_0_7_is_included(ee):
    samples = [
        {"final_v_score": 0.7, "test_ok": False},
    ]
    assert ee.compute_hack_gap(samples) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# 既存 field / 既存 metric の回帰確認 (DoD-D (iii))
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# main() の sample glob — `_repair_summary.json` 等のメタファイルを除外する
# (產屋 eli4 runner の出力 dir に対する回帰: KeyError: 'prompt' クラッシュ防止)
# ---------------------------------------------------------------------------


def _stub_run_one_result(name: str) -> dict:
    return {
        "name": name,
        "seed": 0,
        "module_name": "Sample",
        "test_ok": True,
        "compile_ok": True,
        "has_undefined": False,
        "has_assertion_failure": False,
        "has_function_clause": False,
        "has_token_missing": False,
        "has_syntax_error": False,
        "has_compile_error": False,
        "test_stderr": "",
        "exit_code": 0,
        "elapsed_sec": 0.01,
        "timed_out": False,
        "undef_symbols": [],
        "did_you_mean": [],
        "final_v_score": None,
        "final_verdict": None,
    }


def test_main_skips_underscore_prefixed_meta_files(ee, tmp_path, monkeypatch):
    """gen dir に `_repair_summary.json` (產屋 eli4 の repair-loop 出力) が
    混ざっていても、main() は sample として読まずクラッシュしないこと。"""
    gen_dir = tmp_path / "gen"
    gen_dir.mkdir()
    out_dir = tmp_path / "out"

    sample = {
        "name": "HumanEval_0",
        "seed": 0,
        "prompt": "defmodule Sample do\n",
        "completion": "end\n",
        "tests": "",
    }
    (gen_dir / "HumanEval_0__s0.json").write_text(json.dumps(sample), encoding="utf-8")
    # prompt 等を持たない meta file。誤って sample として読まれると
    # run_one 内で KeyError: 'prompt' になる。
    (gen_dir / "_repair_summary.json").write_text(
        json.dumps({"n_prompts": 1}), encoding="utf-8"
    )

    calls = []

    def _fake_run_one(sample, elixir_bin, timeout):
        calls.append(sample["name"])
        return _stub_run_one_result(sample["name"])

    monkeypatch.setattr(ee, "run_one", _fake_run_one)
    monkeypatch.setattr(ee.shutil, "which", lambda name: "/usr/bin/elixir")

    argv_backup = sys.argv
    try:
        sys.argv = [
            "elixir_eval.py",
            "--generated-dir", str(gen_dir),
            "--out-dir", str(out_dir),
        ]
        ee.main()
    finally:
        sys.argv = argv_backup

    assert calls == ["HumanEval_0"]
    summary = json.loads((out_dir / "_summary.json").read_text(encoding="utf-8"))
    assert summary["n_total"] == 1


def test_run_one_existing_fields_unchanged_shape(ee):
    sample = {
        "name": "HumanEval_2",
        "seed": 0,
        "prompt": "defmodule Sample do\n",
        "completion": "end\n",
        "tests": "",
    }
    r = ee.run_one(sample, elixir_bin="/nonexistent/elixir/binary/xyz", timeout=1.0)
    for key in (
        "name", "seed", "module_name", "test_ok", "compile_ok",
        "has_undefined", "has_assertion_failure", "has_function_clause",
        "has_token_missing", "has_syntax_error", "has_compile_error",
        "test_stderr", "exit_code", "elapsed_sec", "timed_out",
    ):
        assert key in r
    assert r["name"] == "HumanEval_2"
    assert r["test_ok"] is False
    assert r["exit_code"] == -2
