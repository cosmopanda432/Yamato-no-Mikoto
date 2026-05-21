"""
Symbol Oracle (Elixir target 版) — **stub**

src_min_go/go_symbol_oracle.py の interface を Elixir target 向けに移植する予定。
本ファイルは現時点では stub で、`query` は常に None を返す (= kotodama_decoder 側で
bias 加算 skip、vanilla 同等で続行)。

予定する本実装:
  - subprocess で `elixir -e "..."` を呼び、`Module.__info__/1` 経由で
    scope に居る function atom / struct field atom を列挙
  - 速度が許容できない場合は GenServer port 経由の常駐 daemon に切替
  - 起動直後に version 整合確認 (src_min_go と同じパターン)

interface は src_min_go/go_symbol_oracle.py と同形 (OracleResult / OracleClient)
で揃え、kotodama_decoder.py が両 target で共通の型注釈を使えるようにする。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

EXPECTED_MAJOR = "0.1"


@dataclass(frozen=True)
class OracleResult:
    """oracle の `query` 戻り値。Go 版と同一フィールド (vars は Elixir では unused)"""
    types: tuple[str, ...]
    vars: tuple[str, ...]
    scope_kind: str
    ast_ok: bool
    elapsed_ms: int


class OracleClient:
    """Elixir Symbol Oracle stub.

    本実装までは `.query` が常に None を返す。
    `kotodama_decoder.py` 側は `r is None` のとき bias 加算 skip するので、
    vanilla 同等の挙動になる。
    """

    def __init__(
        self,
        oracle_bin: Path | None = None,
        timeout_sec: float = 0.5,
        max_restart: int = 3,
    ) -> None:
        self.oracle_bin = oracle_bin
        self.timeout_sec = timeout_sec
        self.max_restart = max_restart
        logger.warning(
            "elixir_symbol_oracle: stub mode (.query returns None, bias 加算 skip)"
        )

    def __enter__(self) -> "OracleClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def query(
        self,
        prefix: str,
        cursor: int,
        session_id: str,
    ) -> OracleResult | None:
        # Stub: 常に None。Elixir 本実装後に差し替え。
        return None

    def close(self) -> None:
        pass
