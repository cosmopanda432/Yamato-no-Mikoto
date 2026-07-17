"""
產屋 (ubuya) 還降 loop runner の TS 版 (`run_yamato_min_ts4.py`) の pure function 単体テスト。

`tests_eli4/test_repair_runner.py` の TS 移植。ports:
  - seed 式: attempt_seed(s,i,0) == s*1_000_003+i、r>=1 では + r*R_STRIDE (eli4 と同値)
  - 如先: hint なし → prompt+TRACE_SEED (round 0 と byte 一致)、
          hint あり → diff は hint_line 1 行のみ
  - _repair_summary.json 構造 (build_repair_summary) の合成データ検証
  - build_hint の TS 処方 3 分岐 (undefined/syntax_error/type_error) + テスト失敗時 ""
    (ts4_実装設計書_v0.md §6。eli4 は undef_symbol のみの stub だったが ts4 で拡張)
  - resolve_tsc_bin / resolve_node_bin の fail-fast (repair-on は生成 host に必須)
  - TRACE_SEED / MODE_FLAGS / truncate_at_stop_tokens が構造的に妥当であること
    (round 0 byte-identity の統制条件の前提を静的にも保証する)

GPU/model の実ロードは行わない。runner モジュール自体の import は torch/transformers
を要するが (CPU で可)、main() は一切呼ばず、モジュールレベル関数だけを対象にする。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src_min_ts4"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "eval"))

_RUNNER_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "eval" / "run_yamato_min_ts4.py"
)


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def runner():
    return _load_module(_RUNNER_PATH, "run_yamato_min_ts4")


# ---------------------------------------------------------------------------
# seed 式 (eli4 §5.2 統制条件と同値)
# ---------------------------------------------------------------------------


def test_attempt_seed_round0_formula(runner):
    assert runner.attempt_seed(0, 0, 0) == 0 * 1_000_003 + 0
    assert runner.attempt_seed(7, 3, 0) == 7 * 1_000_003 + 3


def test_attempt_seed_round_r_adds_stride(runner):
    base = 7 * 1_000_003 + 3
    assert runner.attempt_seed(7, 3, 1) == base + 1 * runner.R_STRIDE
    assert runner.attempt_seed(7, 3, 2) == base + 2 * runner.R_STRIDE


def test_r_stride_is_large_prime_constant(runner):
    assert runner.R_STRIDE == 999_999_937


# ---------------------------------------------------------------------------
# 如先: wrapped_prompt 構成
# ---------------------------------------------------------------------------


def test_wrapped_prompt_no_hint_matches_round0(runner):
    prompt = "function foo(x: number): number {\n"
    round0_style = prompt + runner.TRACE_SEED  # _run_repair_loop の round 0 と同形の式
    assert runner.build_wrapped_prompt(prompt, "", True) == round0_style


def test_wrapped_prompt_with_hint_diff_is_hint_line_only(runner):
    prompt = "function foo(x: number): number {\n"
    no_hint = runner.build_wrapped_prompt(prompt, "", True)
    with_hint = runner.build_wrapped_prompt(prompt, "型を確認せよ", True)

    assert with_hint != no_hint
    assert with_hint.startswith(prompt)
    assert with_hint.endswith(runner.TRACE_SEED)

    inserted = with_hint[len(prompt): len(with_hint) - len(runner.TRACE_SEED)]
    assert inserted == runner.build_hint_line("型を確認せよ")
    assert inserted.count("\n") == 1
    # prompt と TRACE_SEED はそのまま保たれている (hint 以外の prompt 差分を作らない)
    assert with_hint == prompt + inserted + runner.TRACE_SEED


def test_wrapped_prompt_koumyou_disabled_no_trace_seed(runner):
    prompt = "function foo(): void {\n"
    assert runner.build_wrapped_prompt(prompt, "", False) == prompt
    assert runner.build_wrapped_prompt(prompt, "note", False) == (
        prompt + runner.build_hint_line("note")
    )


def test_wrapped_prompt_with_real_build_hint_undef_symbol_diff_is_hint_line_only(runner):
    """如先の担保: 実 build_hint 出力を使った retry でも round 0 との
    diff は hint_line 1 行のみであること。"""
    prompt = "function foo(x: number): number {\n"
    round0 = runner.build_wrapped_prompt(prompt, "", True)

    eval_result = {
        "undef_symbols": ["bar"],
        "reason_code": "undef_symbol",
    }
    hint = runner.build_hint(eval_result)
    assert hint != ""

    retry = runner.build_wrapped_prompt(prompt, hint, True)
    assert retry != round0
    assert retry == prompt + runner.build_hint_line(hint) + runner.TRACE_SEED


def test_wrapped_prompt_with_real_build_hint_trace_halt_matches_round0(runner):
    """如先の担保: 光明想 HALT (trace_*) の hint は "" なので、
    retry の wrapped_prompt は round 0 と byte 一致する。"""
    prompt = "function foo(x: number): number {\n"
    round0 = runner.build_wrapped_prompt(prompt, "", True)

    eval_result = {"undef_symbols": [], "reason_code": "trace_missing"}
    hint = runner.build_hint(eval_result)
    assert hint == ""

    retry = runner.build_wrapped_prompt(prompt, hint, True)
    assert retry == round0


def test_wrapped_prompt_trace_halt_with_undef_symbols_still_matches_round0(runner):
    """如先の担保 (eli4 reviewer 指摘の衝突経路): post-hoc eval が halted_early な
    attempt に対しても走り、たまたま undef_symbols が非空になったとしても、
    reason_code が trace_missing/trace_insufficient なら hint なしのまま
    (undef_symbols チェックより trace_* 判定が優先される)。"""
    prompt = "function foo(x: number): number {\n"
    round0 = runner.build_wrapped_prompt(prompt, "", True)

    for reason in ("trace_missing", "trace_insufficient"):
        eval_result = {
            "undef_symbols": ["bar"],
            "reason_code": reason,
        }
        hint = runner.build_hint(eval_result)
        assert hint == ""

        retry = runner.build_wrapped_prompt(prompt, hint, True)
        assert retry == round0


# ---------------------------------------------------------------------------
# build_hint (ts4_実装設計書_v0.md §6 処方規則、3 分岐 + テスト失敗時 "")
# ---------------------------------------------------------------------------


def test_build_hint_no_undef_no_syntax_no_type_no_trace_is_empty(runner):
    assert runner.build_hint({}) == ""
    # has_undefined 相当のフラグはあるが undef_symbols が空 (regex 未マッチ) なら hint なし
    assert runner.build_hint({"reason_code": "undef_symbol", "test_stderr": "boom"}) == ""


def test_build_hint_undefined_single_symbol(runner):
    eval_result = {"undef_symbols": ["bar"], "reason_code": "undef_symbol"}
    assert runner.build_hint(eval_result) == (
        "'bar' は未定義です。標準ライブラリまたは自分で定義した名前だけを使ってください"
    )


def test_build_hint_undefined_multiple_symbols_capped_at_2(runner):
    eval_result = {
        "undef_symbols": ["foo", "bar", "ignored"],
        "reason_code": "undef_symbol",
    }
    hint = runner.build_hint(eval_result)
    assert "'foo'" in hint
    assert "'bar'" in hint
    assert "'ignored'" not in hint


def test_build_hint_undefined_truncated_to_200_chars(runner):
    long_sym = "A" * 250
    eval_result = {"undef_symbols": [long_sym], "reason_code": "undef_symbol"}
    hint = runner.build_hint(eval_result)
    assert len(hint) <= 200


def test_build_hint_syntax_error(runner):
    eval_result = {"undef_symbols": [], "has_syntax_error": True, "reason_code": "syntax_error"}
    assert runner.build_hint(eval_result) == "構文エラーがあります (括弧・文字列の閉じ忘れに注意)"


def test_build_hint_type_error_embeds_message_head(runner):
    eval_result = {
        "undef_symbols": [],
        "has_syntax_error": False,
        "has_type_error": True,
        "type_error_msg": "Type 'number' is not assignable to type 'string'.",
        "reason_code": "type_error",
    }
    hint = runner.build_hint(eval_result)
    assert hint.startswith("型エラーがあります: ")
    assert "Type 'number' is not assignable to type 'string'." in hint


def test_build_hint_type_error_message_truncated_to_80_chars(runner):
    long_msg = "X" * 200
    eval_result = {
        "undef_symbols": [],
        "has_syntax_error": False,
        "has_type_error": True,
        "type_error_msg": long_msg,
        "reason_code": "type_error",
    }
    hint = runner.build_hint(eval_result)
    embedded = hint[len("型エラーがあります: "):]
    assert len(embedded) <= 80


def test_build_hint_undefined_takes_priority_over_syntax_and_type(runner):
    eval_result = {
        "undef_symbols": ["bar"],
        "has_syntax_error": True,
        "has_type_error": True,
        "type_error_msg": "whatever",
        "reason_code": "undef_symbol",
    }
    hint = runner.build_hint(eval_result)
    assert "bar" in hint
    assert "構文" not in hint
    assert "型エラー" not in hint


def test_build_hint_syntax_takes_priority_over_type(runner):
    eval_result = {
        "undef_symbols": [],
        "has_syntax_error": True,
        "has_type_error": True,
        "type_error_msg": "whatever",
        "reason_code": "syntax_error",
    }
    assert runner.build_hint(eval_result) == "構文エラーがあります (括弧・文字列の閉じ忘れに注意)"


def test_build_hint_test_failure_only_is_empty(runner):
    """コンパイルは通ったがテストのみ失敗 (has_undefined/syntax/type すべて False) → hint なし。"""
    eval_result = {
        "undef_symbols": [],
        "has_syntax_error": False,
        "has_type_error": False,
        "reason_code": "none",
    }
    assert runner.build_hint(eval_result) == ""


def test_build_hint_koumyou_halt_trace_missing_is_empty(runner):
    eval_result = {"undef_symbols": [], "reason_code": "trace_missing"}
    assert runner.build_hint(eval_result) == ""


def test_build_hint_koumyou_halt_trace_insufficient_is_empty(runner):
    eval_result = {"undef_symbols": [], "reason_code": "trace_insufficient"}
    assert runner.build_hint(eval_result) == ""


def test_build_hint_trace_missing_wins_over_undef_symbols(runner):
    eval_result = {
        "undef_symbols": ["bar"],
        "reason_code": "trace_missing",
    }
    assert runner.build_hint(eval_result) == ""


def test_build_hint_trace_insufficient_wins_over_undef_symbols(runner):
    eval_result = {
        "undef_symbols": ["bar"],
        "reason_code": "trace_insufficient",
    }
    assert runner.build_hint(eval_result) == ""


def test_build_hint_other_in_loop_reasons_are_empty(runner):
    for reason in ("bracket_mismatch", "do_end_mismatch", "bad_pattern", "low_score", "none"):
        eval_result = {"undef_symbols": [], "reason_code": reason}
        assert runner.build_hint(eval_result) == ""


def test_build_hint_result_fits_l5_verdict_hint_len_constraint(runner):
    from kojiki_lm.yomotsu_hirasaka import L5ToL3Verdict, ReasonCode, Verdict

    long_sym = "B" * 250
    eval_result = {"undef_symbols": [long_sym], "reason_code": "undef_symbol"}
    hint = runner.build_hint(eval_result)
    # L5ToL3Verdict.hint の <=200 制約を満たす文字列であることを実際に
    # dataclass 経由で検証する。
    v = L5ToL3Verdict(verdict=Verdict.HALT, v_score=0.0, reason_code=ReasonCode.NONE, hint=hint)
    assert len(v.hint) <= 200


# ---------------------------------------------------------------------------
# resolve_reason_code (post-hoc + in-loop verdict の統合、ts4 で 3 分岐に拡張)
# ---------------------------------------------------------------------------


def test_resolve_reason_code_prefers_verdict_reason(runner):
    from kojiki_lm.yomotsu_hirasaka import L5ToL3Verdict, ReasonCode, Verdict

    fv = L5ToL3Verdict(verdict=Verdict.HALT, v_score=0.0, reason_code=ReasonCode.BRACKET_MISMATCH)
    assert runner.resolve_reason_code(fv, {"has_undefined": True}) == "bracket_mismatch"


def test_resolve_reason_code_falls_back_to_undef_symbol(runner):
    assert runner.resolve_reason_code(None, {"has_undefined": True}) == "undef_symbol"


def test_resolve_reason_code_falls_back_to_syntax_error(runner):
    assert runner.resolve_reason_code(
        None, {"has_undefined": False, "has_syntax_error": True}
    ) == "syntax_error"


def test_resolve_reason_code_falls_back_to_type_error(runner):
    assert runner.resolve_reason_code(
        None, {"has_undefined": False, "has_syntax_error": False, "has_type_error": True}
    ) == "type_error"


def test_resolve_reason_code_none_when_nothing_fires(runner):
    assert runner.resolve_reason_code(None, {"has_undefined": False}) == "none"


def test_resolve_reason_code_undef_takes_priority_over_syntax_and_type(runner):
    assert runner.resolve_reason_code(
        None, {"has_undefined": True, "has_syntax_error": True, "has_type_error": True}
    ) == "undef_symbol"


# ---------------------------------------------------------------------------
# resolve_tsc_bin / resolve_node_bin fail-fast (repair-on は生成 host に必須)
# ---------------------------------------------------------------------------


def test_resolve_tsc_bin_uses_explicit_arg(runner):
    assert runner.resolve_tsc_bin("/custom/path/tsc") == "/custom/path/tsc"


def test_resolve_tsc_bin_finds_repo_vendored_binary(runner):
    # このサンドボックスでは ts_tools/node_modules/.bin/tsc が npm ci 済み
    resolved = runner.resolve_tsc_bin(None)
    assert resolved
    assert "tsc" in resolved


def test_resolve_node_bin_uses_explicit_arg(runner):
    assert runner.resolve_node_bin("/custom/path/node") == "/custom/path/node"


def test_resolve_node_bin_finds_on_path(runner):
    resolved = runner.resolve_node_bin(None)
    assert resolved
    assert "node" in resolved


def test_resolve_node_bin_fails_fast_when_missing(runner, monkeypatch):
    import ts_eval

    monkeypatch.setattr(ts_eval.shutil, "which", lambda name: None)
    with pytest.raises(SystemExit):
        runner.resolve_node_bin(None)


# ---------------------------------------------------------------------------
# _repair_summary.json 構造 (build_repair_summary、合成データ) — eli4 と同一意味論
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
            {"round": 1, "test_ok": False, "hint_used": "", "repair_reason": "syntax_error"},
            {"round": 2, "test_ok": False, "hint_used": "", "repair_reason": "syntax_error"},
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
    assert summary["hints_used"] == {"undef_symbol": 1, "syntax_error": 2}


def test_build_repair_summary_no_prompts_is_safe(runner):
    summary = runner.build_repair_summary({}, max_rounds=2)
    assert summary["n_prompts"] == 0
    assert summary["avg_attempts"] == 0.0
    assert summary["per_round_pass"] == [0, 0, 0]
    assert summary["n_recovered"] == 0
    assert summary["hints_used"] == {}


# ---------------------------------------------------------------------------
# TRACE_SEED / MODE_FLAGS / truncate_at_stop_tokens の静的整合性
# (round 0 byte-identity の前提条件、koumyou_so.THOUGHT_MARKER との整合)
# ---------------------------------------------------------------------------


def test_trace_seed_matches_koumyou_so_thought_marker(runner):
    from kojiki_lm.koumyou_so import THOUGHT_MARKER

    assert runner.TRACE_SEED.strip() == THOUGHT_MARKER


def test_mode_flags_has_4_modes(runner):
    assert set(runner.MODE_FLAGS.keys()) == {
        "firewall-off", "firewall-on", "koumyou-on", "repair-on",
    }
    assert runner.MODE_FLAGS["firewall-off"] == (False, False)
    assert runner.MODE_FLAGS["firewall-on"] == (True, False)
    assert runner.MODE_FLAGS["koumyou-on"] == (True, True)
    assert runner.MODE_FLAGS["repair-on"] == runner.MODE_FLAGS["koumyou-on"]


def test_truncate_at_stop_tokens(runner):
    text = "abc STOP def"
    assert runner.truncate_at_stop_tokens(text, ["STOP"]) == "abc "
    assert runner.truncate_at_stop_tokens(text, []) == text
    assert runner.truncate_at_stop_tokens(text, None) == text


# ---------------------------------------------------------------------------
# ashibune 記録タイミング (fresh-run truncation / record 内容不変) — eli4 §Fix3 と同一設計
# ---------------------------------------------------------------------------


def _synthetic_attempt(**overrides) -> dict:
    base = {
        "name": "HumanEval_0",
        "round": 0,
        "hint": "",
        "repair_reason": "",
        "prompt": "function foo(): void {\n",
        "tests": "\n",
        "stop_tokens": [],
        "completion": "}\n",
        "raw_completion": "}\n",
        "seed_used": 12345,
        "elapsed_sec": 0.5,
        "firewall_enabled": True,
        "total_step_count": 3,
        "halted_early": False,
        "stopped_at_stop_token": False,
        "final_verdict": "commit",
        "v_score": 0.9,
        "hint_from_verdict": "",
        "trace_info": {"status": "ok", "n_thought_lines": 1,
                        "trace_body_chars": 30, "code_started": True},
        "test_ok": True,
        "has_undefined": False,
        "has_syntax_error": False,
        "has_type_error": False,
        "type_error_msg": "",
        "exit_code": 0,
        "test_stderr": "",
        "undef_symbols": [],
        "did_you_mean": [],
        "reason_code": "none",
        "accepted": False,
        "is_final_answer": False,
    }
    base.update(overrides)
    return base


def test_reset_ashibune_log_truncates_stale_file(runner, tmp_path):
    """再実行で同じ out_dir に前回実行の record が残っていても、
    `_reset_ashibune_log` はファイルを空にしてから返す (fresh run = fresh log)。"""
    path = tmp_path / "ashibune.jsonl"
    path.write_text('{"stale": "record from previous run"}\n', encoding="utf-8")

    log = runner._reset_ashibune_log(path)

    assert path.read_text(encoding="utf-8") == ""

    from kojiki_lm.ashibune import AshibuneRecord

    log.append(AshibuneRecord(
        ts="2026-07-17T00:00:00Z", prompt_id="HumanEval_0", mode="repair-on",
        round=0, seed_used=1, verdict="commit", v_score=0.9, reason_code="none",
        hint_used="", halted_early=False, stopped_at_stop_token=False,
        test_ok=True, has_undefined=False, exit_code=0, completion_chars=4,
        raw_completion="}\n", accepted=True, is_final_answer=True,
    ))

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert "stale" not in lines[0]


def test_reset_ashibune_log_creates_parent_dir(runner, tmp_path):
    path = tmp_path / "nested" / "ashibune.jsonl"
    assert not path.parent.exists()
    runner._reset_ashibune_log(path)
    assert path.exists()
    assert path.read_text(encoding="utf-8") == ""


def test_attempt_to_ashibune_record_transcribes_all_18_fields(runner):
    """`_attempt_to_ashibune_record` が旧 finalize 一括書き出しと同じ 18 field を
    同じ値で転記すること (WHAT は変えない、の担保)。"""
    attempt = _synthetic_attempt(accepted=True, is_final_answer=True)
    record = runner._attempt_to_ashibune_record("repair-on", attempt)

    assert record.prompt_id == attempt["name"]
    assert record.mode == "repair-on"
    assert record.round == attempt["round"]
    assert record.seed_used == attempt["seed_used"]
    assert record.verdict == attempt["final_verdict"]
    assert record.v_score == attempt["v_score"]
    assert record.reason_code == attempt["reason_code"]
    assert record.hint_used == attempt["hint"]
    assert record.halted_early == attempt["halted_early"]
    assert record.stopped_at_stop_token == attempt["stopped_at_stop_token"]
    assert record.test_ok == attempt["test_ok"]
    assert record.has_undefined == attempt["has_undefined"]
    assert record.exit_code == attempt["exit_code"]
    assert record.completion_chars == len(attempt["completion"])
    assert record.raw_completion == attempt["raw_completion"]
    assert record.accepted == attempt["accepted"]
    assert record.is_final_answer == attempt["is_final_answer"]
    assert record.ts  # 非空の ISO timestamp


def test_build_final_sample_payload_matches_expected_shape(runner):
    row = {"tests": "\n"}
    final = _synthetic_attempt(round=1, hint="型を確認せよ", repair_reason="undef_symbol")

    class _Args:
        seed = 7
        model = "m"
        quantize = "4bit"
        temperature = 0.2
        mode = "repair-on"

    payload = runner._build_final_sample_payload(
        "HumanEval_0", final, row, _Args(), koumyou_enabled=True, n_attempts=2,
    )

    assert payload["name"] == "HumanEval_0"
    assert payload["seed"] == 7
    assert payload["completion"] == final["completion"]
    assert payload["raw_completion"] == final["raw_completion"]
    assert payload["tests"] == row["tests"]
    assert payload["round"] == 1
    assert payload["hint"] == "型を確認せよ"
    assert payload["n_attempts"] == 2
    assert payload["repair_reason"] == "undef_symbol"
    assert payload["trace_seed"] == runner.TRACE_SEED


def test_resolve_sample_marks_only_last_attempt_accepted(runner, tmp_path):
    """`_resolve_sample` は attempts[-1] だけを accepted/is_final_answer=True にし、
    他の attempt は False のままにする (旧 finalize と同じ意味論)。"""
    attempts_by_name = {
        "HumanEval_0": [
            _synthetic_attempt(round=0, test_ok=False),
            _synthetic_attempt(round=1, test_ok=True),
        ]
    }
    prompts_by_name = {"HumanEval_0": {"tests": "\n"}}

    class _Args:
        seed = 0
        model = "m"
        quantize = "4bit"
        temperature = 0.2
        mode = "repair-on"

    ashibune_log = runner._reset_ashibune_log(tmp_path / "ashibune.jsonl")
    runner._resolve_sample(
        "HumanEval_0",
        attempts_by_name=attempts_by_name, prompts_by_name=prompts_by_name,
        args=_Args(), koumyou_enabled=True, ashibune_log=ashibune_log,
        out_dir=tmp_path,
    )

    atts = attempts_by_name["HumanEval_0"]
    assert atts[0]["accepted"] is False
    assert atts[0]["is_final_answer"] is False
    assert atts[1]["accepted"] is True
    assert atts[1]["is_final_answer"] is True

    lines = (tmp_path / "ashibune.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2

    import json as _json
    final_json = _json.loads((tmp_path / "HumanEval_0__s0.json").read_text(encoding="utf-8"))
    assert final_json["n_attempts"] == 2
    assert final_json["round"] == 1


# ---------------------------------------------------------------------------
# --skip-existing は mode=repair-on では fail-fast (eli4 §Fix4 と同一設計)
# ---------------------------------------------------------------------------


def test_validate_repair_skip_existing_raises_when_both_set(runner):
    class _Args:
        mode = "repair-on"
        skip_existing = True

    with pytest.raises(SystemExit):
        runner.validate_repair_skip_existing(_Args())


def test_validate_repair_skip_existing_ok_when_skip_existing_false(runner):
    class _Args:
        mode = "repair-on"
        skip_existing = False

    runner.validate_repair_skip_existing(_Args())  # raise しない


def test_validate_repair_skip_existing_ok_for_other_modes(runner):
    class _Args:
        mode = "koumyou-on"
        skip_existing = True

    runner.validate_repair_skip_existing(_Args())  # repair-on 以外は無関係


# ---------------------------------------------------------------------------
# _TRACE_HALT_REASON_CODES は ReasonCode enum 由来 (eli4 §Fix4 と同一設計)
# ---------------------------------------------------------------------------


def test_trace_halt_reason_codes_derived_from_reason_code_enum(runner):
    from kojiki_lm.yomotsu_hirasaka import ReasonCode

    assert runner._TRACE_HALT_REASON_CODES == {
        ReasonCode.TRACE_MISSING.value,
        ReasonCode.TRACE_INSUFFICIENT.value,
    }
