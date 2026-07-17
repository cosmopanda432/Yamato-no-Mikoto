"""
光明想 (KoumyouSo) — ts4 trace marker (`// 思考:`) のテスト

eli4 の `# 思考:` を TS コメント記法 `// 思考:` に置き換えたことの検証。
行数/文字数閾値・TraceStatus の意味論自体は eli4 から不変 (koumyou_so.py の
docstring 仕様どおり) なので、ここでは「マーカーが `// 思考:` に切り替わったこと」
と「旧マーカー `# 思考:` はもう検出されないこと」を中心に確認する。

eli4 (elixir 系) には koumyou_so.py 単体のテストファイルが存在しなかったため
(tests_eli4/ は evaluator/ashibune/reason_code/repair_runner/judge のみ)、本ファイルは
ts4 で新規に追加する。既存挙動は koumyou_so.py の docstring を仕様として TDD で書き起こす。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src_min_ts4"))

from kojiki_lm.koumyou_so import (  # noqa: E402
    THOUGHT_MARKER,
    KoumyouSo,
    KoumyouSoConfig,
    TraceStatus,
)


def test_thought_marker_is_ts_comment():
    assert THOUGHT_MARKER == "// 思考:"


def test_detects_ts_marker_valid_trace():
    so = KoumyouSo()
    text = "// 思考: これは二十文字以上ある十分な長さの理由付けコメントです\nfunction foo(): number {\n  return 1;\n}"
    verdict = so.validate(text)
    assert verdict.status == TraceStatus.TRACE_VALID
    assert verdict.code_started is True
    assert verdict.n_thought_lines == 1
    assert not verdict.is_terminal_failure


def test_old_python_style_marker_is_not_detected():
    """旧 `# 思考:` (eli4 以前の記法) はもう trace として認識されない。

    marker でも空行でもない行として即座に code_started=True になり、
    trace 行数 0 のまま TRACE_MISSING (HALT) に落ちる。
    """
    so = KoumyouSo()
    text = "# 思考: これは十分な長さの理由付けコメントです\nfunction foo(): number {\n  return 1;\n}"
    verdict = so.validate(text)
    assert verdict.status == TraceStatus.TRACE_MISSING
    assert verdict.n_thought_lines == 0
    assert verdict.code_started is True
    assert verdict.is_terminal_failure


def test_trace_insufficient_when_body_too_short():
    so = KoumyouSo()
    text = "// 思考: ab\nfunction foo(): number {\n  return 1;\n}"
    verdict = so.validate(text)
    assert verdict.status == TraceStatus.TRACE_INSUFFICIENT
    assert verdict.is_terminal_failure


def test_trace_missing_when_no_marker_at_all():
    so = KoumyouSo()
    text = "function foo(): number {\n  return 1;\n}"
    verdict = so.validate(text)
    assert verdict.status == TraceStatus.TRACE_MISSING
    assert verdict.n_thought_lines == 0
    assert verdict.is_terminal_failure


def test_still_generating_for_short_text():
    so = KoumyouSo()
    text = "// 思考"  # grace_period_chars (16) 未満
    verdict = so.validate(text)
    assert verdict.status == TraceStatus.STILL_GENERATING
    assert not verdict.is_terminal_failure


def test_trace_only_when_code_not_started_yet():
    so = KoumyouSo()
    text = "// 思考: まだ続きの生成が完了していない状態を模したテキストです"
    verdict = so.validate(text)
    assert verdict.status == TraceStatus.TRACE_ONLY
    assert not verdict.is_terminal_failure


def test_trace_seed_is_prepended_before_scan():
    """runner が prompt 末尾に `// 思考: ` を pre-seed した場合、generated_text は
    その続きから始まるので、trace_seed を prepend して整合させる。"""
    so = KoumyouSo(KoumyouSoConfig(trace_seed="// 思考: "))
    text = "これは十分な長さの理由付けコメントの続きです\nfunction foo(): number {\n  return 1;\n}"
    verdict = so.validate(text)
    assert verdict.status == TraceStatus.TRACE_VALID
    assert verdict.n_thought_lines == 1


def test_multi_line_trace_counts_each_marker_line():
    so = KoumyouSo(KoumyouSoConfig(min_trace_lines=2))
    text = (
        "// 思考: 1行目の理由はこれくらいの長さです\n"
        "// 思考: 2行目の理由もこれくらいの長さです\n"
        "function foo(): number {\n"
        "  return 1;\n"
        "}"
    )
    verdict = so.validate(text)
    assert verdict.status == TraceStatus.TRACE_VALID
    assert verdict.n_thought_lines == 2
