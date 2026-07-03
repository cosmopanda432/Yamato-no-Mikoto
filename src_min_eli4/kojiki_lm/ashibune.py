"""
葦船 (あしぶね) — Rejected Sample Log

古事記において、蛭子 (ひるこ) は葦船に乗せて流された = 「消す」のではなく
「記録に残しつつ、成功集合からは外す」という扱いを受ける。本モジュールはこの
比喩を実装したもので、REPAIR loop (orchestrator, Step C) が棄却した生成 sample
を理由コード付きで JSONL に永続化する。

役割:
  - 棄却された attempt (round 0 の初回生成も含む、全 attempt) を **消さずに**
    1 record = 1 行の JSON として追記する (卜相 = 失敗分布分析の資源)。
  - 成功集合 (最終的に採用される completion) と混ぜない。採用可否は
    `AshibuneRecord.accepted` field で判別できるが、ファイル自体は
    「合否を問わず全 attempt の記録」であって、成功のみを集めた別ファイルではない。

書き込みは orchestrator (Step C) 側の責務であり、`FirewallDecoder` の decode loop
内から呼んではならない (生成 byte への影響を構造的にゼロにするため)。

ファイルは `<out_dir>/ashibune.jsonl` に置く想定。`elixir_eval.py` は `*.json` を
glob するため、拡張子 `.jsonl` により誤って読み込まれることはない。
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AshibuneRecord:
    """1 attempt (1 生成 round) の棄却記録。"""

    ts: str
    """ISO 8601 timestamp。"""

    prompt_id: str
    """例: "HumanEval_0"。"""

    mode: str
    """例: "repair-on"。"""

    round: int
    """0 = 初回生成。"""

    seed_used: int
    """この attempt の sampling_seed 実値。"""

    verdict: str | None
    """final_verdict ("commit"/"repair"/"halt"/None)。"""

    v_score: float | None

    reason_code: str
    """ReasonCode.value (Step B)。"""

    hint_used: str
    """この attempt の prompt に注入された hint ("" = なし)。"""

    halted_early: bool

    stopped_at_stop_token: bool

    test_ok: bool | None
    """post-hoc eval 結果 (未 eval なら None)。"""

    has_undefined: bool | None

    exit_code: int | None

    completion_chars: int

    raw_completion: str
    """全文 (卜相 = 失敗分布分析の資源)。"""

    accepted: bool
    """この attempt が最終回答として採用されたか。"""

    is_final_answer: bool
    """rounds 消尽時の最終 attempt (不合格でも True)。"""


class AshibuneLog:
    """`AshibuneRecord` を JSONL 1 行 1 record で追記する永続化 log。"""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: AshibuneRecord) -> None:
        """`record` を JSON 1 行として末尾に追記する。

        呼び出しごとに append mode で開き、書いたら即 flush + close する
        (プロセス途中終了時の記録欠落を防ぐため)。
        """
        line = json.dumps(dataclasses.asdict(record), ensure_ascii=False)
        f = open(self.path, mode="a", encoding="utf-8")
        try:
            f.write(line + "\n")
            f.flush()
        finally:
            f.close()
