"""
葦船 (ashibune) log — 棄却 sample 永続化のテスト

DoD-A: 全 attempt (全 round) が記録される。unit test: 2 record 書いて読み戻し一致。
"""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src_min_eli4"))

from kojiki_lm.ashibune import AshibuneLog, AshibuneRecord  # noqa: E402


def _make_record(idx: int) -> AshibuneRecord:
    return AshibuneRecord(
        ts=f"2026-07-03T00:00:0{idx}Z",
        prompt_id=f"HumanEval_{idx}",
        mode="repair-on",
        round=idx,
        seed_used=1000 + idx,
        verdict="repair" if idx == 0 else "commit",
        v_score=0.42 if idx == 0 else None,
        reason_code="TRACE_MISSING" if idx == 0 else "OK",
        hint_used="日本語ヒント: 中間推論を書け" if idx == 0 else "",
        halted_early=idx == 0,
        stopped_at_stop_token=idx == 1,
        test_ok=None if idx == 0 else True,
        has_undefined=None if idx == 0 else False,
        exit_code=None if idx == 0 else 0,
        completion_chars=123 + idx,
        raw_completion=f"# 思考: 日本語のコメント {idx} 🎌\ndef foo():\n    pass\n",
        accepted=idx == 1,
        is_final_answer=idx == 1,
    )


def test_append_and_read_back_two_records(tmp_path: Path) -> None:
    path = tmp_path / "ashibune.jsonl"
    log = AshibuneLog(path)

    record_0 = _make_record(0)
    record_1 = _make_record(1)

    log.append(record_0)
    log.append(record_1)

    assert path.exists()
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2

    loaded_0 = AshibuneRecord(**json.loads(lines[0]))
    loaded_1 = AshibuneRecord(**json.loads(lines[1]))

    assert loaded_0 == record_0
    assert loaded_1 == record_1

    # 非 ASCII 文字がエスケープされず (ensure_ascii=False) そのまま書かれていること
    assert "日本語" in lines[0]
    assert "🎌" in lines[0]


def test_append_creates_parent_dir(tmp_path: Path) -> None:
    nested_path = tmp_path / "nested" / "sub" / "ashibune.jsonl"
    assert not nested_path.parent.exists()

    log = AshibuneLog(nested_path)
    log.append(_make_record(0))

    assert nested_path.parent.exists()
    assert nested_path.exists()
    lines = nested_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1


def test_record_is_frozen() -> None:
    record = _make_record(0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.ts = "changed"  # type: ignore[misc]
