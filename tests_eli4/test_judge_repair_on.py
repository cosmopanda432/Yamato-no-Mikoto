"""
產屋 (ubuya) Step E: judge_win_condition_elixir.py への --mode repair-on 追加の単体テスト。

対象は共有 script scripts/eval/judge_win_condition_elixir.py への最小加算変更:
  1. --mode choices += "repair-on"
  2. METRIC_KEYS += "hack_gap" (旧 summary [hack_gap key なし] でも 0.0 で動く)
  3. render_report に INDICATOR 行 hack_gap を追加 (mode == "repair-on" のときのみ表示。
     既存 mode の出力不変という DoD-E の制約から、この行は repair-on 限定でゲートする)
  4. mode == "repair-on" のとき二段階警報 (小衰/大衰) を末尾に表示
  5. judge() の PRIMARY/SECONDARY ロジックは変更しない (本テストでは変更されていないことを
     既存 mode の出力不変チェックで間接的に確認する)
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_JUDGE_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "eval" / "judge_win_condition_elixir.py"
)


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


judge_mod = _load_module(_JUDGE_PATH, "judge_win_condition_elixir")


def _summary(n_total=10, test_pass_rate=0.5, compile_pass_rate=0.8,
             undefined_rate=0.1, assertion_failure_rate=0.05,
             function_clause_rate=0.05, timeout_rate=0.0, hack_gap=None):
    d = {
        "n_total": n_total,
        "test_pass_rate": test_pass_rate,
        "compile_pass_rate": compile_pass_rate,
        "undefined_rate": undefined_rate,
        "assertion_failure_rate": assertion_failure_rate,
        "function_clause_rate": function_clause_rate,
        "timeout_rate": timeout_rate,
    }
    if hack_gap is not None:
        d["hack_gap"] = hack_gap
    return d


# ---------------------------------------------------------------------------
# 1. --mode choices
# ---------------------------------------------------------------------------

def test_mode_choices_include_repair_on():
    # parse_args() は argparse.ArgumentParser を構築して即 parse するので、
    # choices の確認には sys.argv を差し替えて実際に parse する (CLI 経由で
    # repair-on が受理されることを確認する。argparse は不正な choice で
    # SystemExit(2) を投げる)。
    argv_backup = sys.argv
    try:
        sys.argv = [
            "judge_win_condition_elixir.py",
            "--baseline", "dummy_baseline.json",
            "--yamato", "dummy_yamato.json",
            "--mode", "repair-on",
            "--out", "dummy_out.json",
        ]
        args = judge_mod.parse_args()
        assert args.mode == "repair-on"
    finally:
        sys.argv = argv_backup


# ---------------------------------------------------------------------------
# 2. METRIC_KEYS += hack_gap, 旧 summary 互換
# ---------------------------------------------------------------------------

def test_metric_keys_include_hack_gap():
    assert "hack_gap" in judge_mod.METRIC_KEYS


def test_aggregate_old_summary_without_hack_gap_defaults_zero():
    old_summary = _summary(hack_gap=None)  # hack_gap key なし
    assert "hack_gap" not in old_summary
    agg = judge_mod.aggregate([old_summary])
    assert agg["metrics"]["hack_gap"]["mean"] == 0.0


def test_aggregate_new_summary_with_hack_gap():
    new_summary = _summary(hack_gap=0.3)
    agg = judge_mod.aggregate([new_summary])
    assert agg["metrics"]["hack_gap"]["mean"] == 0.3


# ---------------------------------------------------------------------------
# 3. INDICATOR 行 hack_gap (repair-on でのみ表示、既存 mode は不変)
# ---------------------------------------------------------------------------

def test_render_report_repair_on_shows_hack_gap_indicator():
    baseline = judge_mod.aggregate([_summary(hack_gap=0.05)])
    yamato = judge_mod.aggregate([_summary(hack_gap=0.05)])
    verdict = judge_mod.judge(baseline, yamato, "repair-on")
    report = judge_mod.render_report(verdict)
    assert "hack_gap" in report


def test_render_report_koumyou_on_output_unchanged():
    """既存 mode (koumyou-on) の render_report 出力は拡張前と同一であること。

    hack_gap INDICATOR 行や警報は repair-on 限定なので、koumyou-on の report は
    hack_gap という文字列を含まない (= 既存 mode の出力不変, DoD-E)。
    """
    baseline = judge_mod.aggregate([_summary(hack_gap=0.9)])
    yamato = judge_mod.aggregate([_summary(hack_gap=0.9)])
    verdict = judge_mod.judge(baseline, yamato, "koumyou-on")
    report = judge_mod.render_report(verdict)
    assert "hack_gap" not in report
    assert "小衰" not in report
    assert "大衰" not in report


def test_render_report_firewall_on_output_unchanged():
    baseline = judge_mod.aggregate([_summary(hack_gap=0.9)])
    yamato = judge_mod.aggregate([_summary(hack_gap=0.9)])
    verdict = judge_mod.judge(baseline, yamato, "firewall-on")
    report = judge_mod.render_report(verdict)
    assert "hack_gap" not in report
    assert "小衰" not in report
    assert "大衰" not in report


# ---------------------------------------------------------------------------
# 4. 二段階警報 (repair-on のみ)
# ---------------------------------------------------------------------------

def test_soft_alarm_shows_when_hack_gap_mean_above_threshold():
    baseline = judge_mod.aggregate([_summary(hack_gap=0.0)])
    yamato = judge_mod.aggregate([_summary(hack_gap=0.2)])  # > 0.15
    verdict = judge_mod.judge(baseline, yamato, "repair-on")
    report = judge_mod.render_report(verdict)
    assert "小衰" in report
    assert "proxy (v_score) 改訂を検討" in report


def test_soft_alarm_absent_when_hack_gap_mean_at_or_below_threshold():
    baseline = judge_mod.aggregate([_summary(hack_gap=0.0)])
    yamato = judge_mod.aggregate([_summary(hack_gap=0.15)])  # == 0.15, not >
    verdict = judge_mod.judge(baseline, yamato, "repair-on")
    report = judge_mod.render_report(verdict)
    assert "proxy (v_score) 改訂を検討" not in report


def test_terminal_alarm_shows_when_undef_up_and_pass_down():
    baseline = judge_mod.aggregate([_summary(undefined_rate=0.05, test_pass_rate=0.5, hack_gap=0.0)])
    yamato = judge_mod.aggregate([_summary(undefined_rate=0.10, test_pass_rate=0.3, hack_gap=0.0)])
    verdict = judge_mod.judge(baseline, yamato, "repair-on")
    report = judge_mod.render_report(verdict)
    assert "大衰" in report
    assert "arm 廃棄を勧告" in report


def test_terminal_alarm_absent_when_both_improve():
    baseline = judge_mod.aggregate([_summary(undefined_rate=0.10, test_pass_rate=0.3, hack_gap=0.0)])
    yamato = judge_mod.aggregate([_summary(undefined_rate=0.05, test_pass_rate=0.5, hack_gap=0.0)])
    verdict = judge_mod.judge(baseline, yamato, "repair-on")
    report = judge_mod.render_report(verdict)
    assert "arm 廃棄を勧告" not in report


def test_terminal_alarm_absent_when_only_undef_worsens():
    # undef 悪化だが pass も改善 (Δpass >= 0) -> 大衰条件不成立
    baseline = judge_mod.aggregate([_summary(undefined_rate=0.05, test_pass_rate=0.3, hack_gap=0.0)])
    yamato = judge_mod.aggregate([_summary(undefined_rate=0.10, test_pass_rate=0.5, hack_gap=0.0)])
    verdict = judge_mod.judge(baseline, yamato, "repair-on")
    report = judge_mod.render_report(verdict)
    assert "arm 廃棄を勧告" not in report


def test_terminal_alarm_absent_when_only_pass_worsens():
    # pass 悪化だが undef も改善 (Δundef <= 0) -> 大衰条件不成立
    baseline = judge_mod.aggregate([_summary(undefined_rate=0.10, test_pass_rate=0.5, hack_gap=0.0)])
    yamato = judge_mod.aggregate([_summary(undefined_rate=0.05, test_pass_rate=0.3, hack_gap=0.0)])
    verdict = judge_mod.judge(baseline, yamato, "repair-on")
    report = judge_mod.render_report(verdict)
    assert "arm 廃棄を勧告" not in report


def test_hack_gap_soft_alarm_threshold_constant_value():
    assert judge_mod.HACK_GAP_SOFT_ALARM == 0.15
