"""
Symbol Oracle (Elixir target 版) — Python 内 hardcoded stdlib + 軽量パターン解析

src_min_go/go_symbol_oracle.py の Go 用 stdio daemon に対し、Elixir 版は **Python 内で
完結する hardcoded stdlib lookup** に倒している。理由:

  1. humaneval-elixir / mbpp-elixir は stdlib (String/Enum/Map/List/Keyword 等) を
     ほぼカバーすれば十分。user-defined module は prompt 内に出る分のみ
  2. subprocess `elixir -e` の startup overhead が 200-500 ms あり、token-by-token
     decode の hot path には乗せられない
  3. Erlang daemon (Go 版と同等) は実装コスト大、初期は不要

将来、user-defined module を扱う必要が出たら subprocess fallback or BEAM daemon を追加。
interface は src_min_go の OracleClient / OracleResult と同形のため kotodama_decoder
を切り替え対応にできる。

## 検出する context

prefix を末尾から見て:
  - `Module.<cursor>` 形 → そのモジュールの function 集合を返す
  - `%Module{<cursor>` 形 → そのモジュールの struct field 集合 (現状未対応、TBD)
  - その他 → None (= bias 加算 skip)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

EXPECTED_MAJOR = "0.2"


@dataclass(frozen=True)
class OracleResult:
    """oracle の `query` 戻り値。Go 版と同一フィールド (vars は Elixir では unused)"""
    types: tuple[str, ...]
    vars: tuple[str, ...]
    scope_kind: str
    ast_ok: bool
    elapsed_ms: int


# Elixir stdlib の主要 module → public function 名 一覧。
# Elixir 1.18 ベース、humaneval-elixir / mbpp-elixir の出現頻度が高いものを優先で網羅。
# trailing `_` 等の私的 API は除外、`is_*` 系 guard は kotodama_context で別途扱う。
_STDLIB_FUNCTIONS: dict[str, tuple[str, ...]] = {
    "String": (
        "at", "capitalize", "chunk", "codepoints", "contains?",
        "downcase", "duplicate", "ends_with?", "equivalent?",
        "first", "graphemes", "jaro_distance", "last", "length",
        "match?", "next_codepoint", "next_grapheme", "pad_leading",
        "pad_trailing", "printable?", "replace", "replace_leading",
        "replace_prefix", "replace_suffix", "replace_trailing",
        "reverse", "slice", "split", "split_at", "splitter",
        "starts_with?", "to_atom", "to_charlist", "to_existing_atom",
        "to_float", "to_integer", "trim", "trim_leading", "trim_trailing",
        "upcase", "valid?",
    ),
    "Enum": (
        "all?", "any?", "at", "chunk_by", "chunk_every", "chunk_while",
        "concat", "count", "count_until", "dedup", "dedup_by", "drop",
        "drop_every", "drop_while", "each", "empty?", "fetch", "fetch!",
        "filter", "find", "find_index", "find_value", "flat_map",
        "flat_map_reduce", "frequencies", "frequencies_by", "group_by",
        "intersperse", "into", "join", "map", "map_every", "map_intersperse",
        "map_join", "map_reduce", "max", "max_by", "member?", "min",
        "min_by", "min_max", "min_max_by", "product", "random",
        "reduce", "reduce_while", "reject", "reverse", "reverse_slice",
        "scan", "shuffle", "slice", "slide", "sort", "sort_by", "split",
        "split_while", "split_with", "sum", "take", "take_every",
        "take_random", "take_while", "to_list", "uniq", "uniq_by",
        "unzip", "with_index", "zip", "zip_reduce", "zip_with",
    ),
    "Map": (
        "delete", "drop", "equal?", "fetch", "fetch!", "filter", "from_keys",
        "from_struct", "get", "get_and_update", "get_and_update!",
        "get_lazy", "has_key?", "intersect", "keys", "merge",
        "new", "pop", "pop_lazy", "put", "put_new", "put_new_lazy",
        "reject", "replace", "replace!", "split", "take", "to_list",
        "update", "update!", "values",
    ),
    "List": (
        "ascii_printable?", "delete", "delete_at", "duplicate", "first",
        "flatten", "foldl", "foldr", "improper?", "insert_at",
        "keydelete", "keyfind", "keymember?", "keyreplace", "keysort",
        "keystore", "keytake", "last", "myers_difference", "pop_at",
        "replace_at", "starts_with?", "to_atom", "to_charlist",
        "to_existing_atom", "to_float", "to_integer", "to_string",
        "to_tuple", "update_at", "wrap", "zip",
    ),
    "Keyword": (
        "delete", "delete_first", "drop", "equal?", "fetch", "fetch!",
        "filter", "get", "get_and_update", "get_lazy", "get_values",
        "has_key?", "keys", "keyword?", "merge", "new", "pop",
        "pop_first", "pop_lazy", "put", "put_new", "put_new_lazy",
        "replace", "split", "take", "to_list", "update", "update!",
        "validate", "validate!", "values",
    ),
    "Tuple": (
        "append", "delete_at", "duplicate", "insert_at", "product",
        "sum", "to_list",
    ),
    "Integer": (
        "digits", "extended_gcd", "floor_div", "gcd", "is_even", "is_odd",
        "mod", "parse", "pow", "to_charlist", "to_string", "undigits",
    ),
    "Float": (
        "ceil", "floor", "max_finite", "min_finite", "parse", "pow",
        "ratio", "round", "to_charlist", "to_string",
    ),
    "Atom": (
        "to_charlist", "to_string",
    ),
    "Stream": (
        "chunk_by", "chunk_every", "chunk_while", "concat", "cycle",
        "dedup", "dedup_by", "drop", "drop_every", "drop_while",
        "duplicate", "each", "filter", "flat_map", "interval", "into",
        "iterate", "map", "map_every", "reject", "repeatedly", "resource",
        "run", "scan", "take", "take_every", "take_while", "timer",
        "transform", "unfold", "uniq", "uniq_by", "with_index",
        "zip", "zip_with",
    ),
    "IO": (
        "binread", "binstream", "binwrite", "chardata_to_string",
        "gets", "inspect", "iodata_length", "iodata_to_binary",
        "puts", "read", "stream", "warn", "write",
    ),
    "Process": (
        "alive?", "delete", "exit", "flag", "get", "info", "list",
        "monitor", "put", "register", "registered", "send", "sleep",
        "spawn", "spawn_link", "spawn_monitor", "unregister", "whereis",
    ),
    "Kernel": (
        "abs", "apply", "binding", "ceil", "div", "elem", "exit",
        "floor", "function_exported?", "get_in", "hd", "inspect",
        "length", "macro_exported?", "make_ref", "map_size", "max",
        "min", "node", "not", "put_elem", "put_in", "raise",
        "rem", "round", "self", "send", "spawn", "spawn_link",
        "spawn_monitor", "struct", "struct!", "throw", "tl",
        "to_charlist", "to_string", "trunc", "tuple_size",
        "update_in", "use",
    ),
}

# 末尾が `Module.` の形になっているかを判定する regex。
# `Module.<here>` の前は識別子境界、`Module` 自体は `[A-Z]` で始まる atom。
_MODULE_DOT_PATTERN = re.compile(r"(?<![A-Za-z0-9_.])([A-Z][A-Za-z0-9_]*)\.\s*$")


class OracleClient:
    """Elixir Symbol Oracle 本実装 v1。

    現状 hardcoded stdlib のみ対応 (humaneval-elixir / mbpp-elixir のカバレッジで十分)。
    user-defined module への対応は将来 subprocess fallback で追加可。

    Go 版 OracleClient と interface 互換のため、kotodama_decoder.py からは差し替えのみで
    動く。
    """

    def __init__(
        self,
        oracle_bin: Path | None = None,
        timeout_sec: float = 0.5,
        max_restart: int = 3,
    ) -> None:
        # Go 版と同 signature 維持。stdlib lookup なので oracle_bin は使わない。
        self.oracle_bin = oracle_bin
        self.timeout_sec = timeout_sec
        self.max_restart = max_restart

    def __enter__(self) -> "OracleClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def query(
        self,
        prefix: str,
        cursor: int,
        session_id: str,  # noqa: ARG002 — Go 版 daemon の session 管理用、本実装では未使用
    ) -> OracleResult | None:
        """末尾文脈に応じて symbol 集合を返す。

        Args:
            prefix: cursor 位置までの生成済 text
            cursor: prefix 内の cursor 位置 (通常 len(prefix))
            session_id: Go 版互換のため受け取るが本実装では使わない

        Returns:
            OracleResult。文脈が認識できない場合は None
            (decoder 側で bias 加算 skip)。
        """
        relevant = prefix[:cursor] if 0 <= cursor < len(prefix) else prefix

        # `Module.` 直後 (Module の public function を呼ぼうとしている)
        m = _MODULE_DOT_PATTERN.search(relevant)
        if m:
            mod = m.group(1)
            funcs = _STDLIB_FUNCTIONS.get(mod)
            if funcs is not None:
                return OracleResult(
                    types=funcs,            # bias 対象 symbol を `types` フィールドに乗せる (Go 版と同形)
                    vars=(),
                    scope_kind="module_function_call",
                    ast_ok=True,
                    elapsed_ms=0,
                )
            # 未知 module は None (bias なし)。将来 subprocess fallback で対応可。
            return None

        # その他の文脈は現状未対応。bias 加算 skip = vanilla 同等で続行。
        return None

    def close(self) -> None:
        pass


def supported_modules() -> tuple[str, ...]:
    """ベンチ runner 等から、bias 対象になっている stdlib module 一覧を取得"""
    return tuple(sorted(_STDLIB_FUNCTIONS.keys()))
