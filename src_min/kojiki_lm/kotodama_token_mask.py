"""
言霊トークンマスク (Kotodama Token Mask) — TypeHead 予測 → BPE トークンマスク

TsukuyomiTypeHead が出力する TS 型 ID から、その型の名前 ("number", "Promise", ...) を
Qwen BPE トークン ID 列の **先頭トークン** に変換し、bool マスク [vocab_size] を構築する。

decode 時にこのマスクで logits を masked_fill(-inf) すれば、次トークンは
TypeHead が許可した型名で始まるものに**物理的に**制限される。

カテゴリ "instability" (ImplicitAny 等のメタ型) と "special" (UNK) は生成不可なので除外。

将来 (M2.5) この層を TS Compiler API (ts_tools) からの valid シンボル/型集合と
union するように拡張する。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import torch


# 生成可能 (literal text として TS コードに登場できる) カテゴリ
GENERATABLE_CATEGORIES: frozenset[str] = frozenset({
    "primitives",   # any, string, number, void, boolean, ...
    "library",      # Element, Response, ...
    "builtins",     # Promise, Array, Buffer, ...
    "type_param",   # T, K, V, ...
    "utility",      # Partial, Required, ...
    "structural",   # tuple types etc.
})


@dataclass(frozen=True)
class TypeVocabEntry:
    type_id: int
    name: str
    category: str
    freq: int = 0

    @property
    def is_generatable(self) -> bool:
        return self.category in GENERATABLE_CATEGORIES


class TypeVocabIndex:
    """`ts_type_vocab.json` をロードして型 ID ↔ 型情報の双方向参照を提供"""

    def __init__(self, vocab_path: str | Path):
        raw = json.loads(Path(vocab_path).read_text())
        self.vocab_size: int = raw["vocab_size"]
        self._entries: dict[int, TypeVocabEntry] = {}

        for k, v in raw.get("id_to_type", {}).items():
            try:
                tid = int(k)
            except (ValueError, TypeError):
                continue
            if not isinstance(v, dict) or "name" not in v:
                continue
            self._entries[tid] = TypeVocabEntry(
                type_id=tid,
                name=v["name"],
                category=v.get("category", "special"),
                freq=int(v.get("freq", 0) or 0),
            )

    def get(self, type_id: int) -> TypeVocabEntry | None:
        return self._entries.get(type_id)

    def ids_in_categories(self, categories: Iterable[str]) -> set[int]:
        cats = set(categories)
        return {tid for tid, e in self._entries.items() if e.category in cats}

    def generatable_ids(self) -> set[int]:
        return self.ids_in_categories(GENERATABLE_CATEGORIES)

    def __len__(self) -> int:
        return len(self._entries)


class KotodamaMaskBuilder:
    """
    TypeHead 予測 (top-K type_ids) → bool マスク [tokenizer vocab_size]

    マスク True = 次トークンとして許可。FALSE 位置は decode 時に logit = -inf に置く。

    1 型名につき "name" と " name" (先頭スペース付き) の両形の **第 1 トークン** を許可する。
    Qwen の BPE では `: number` の `number` は ` number` の単一トークンになる場合と
    `n` + `umber` 等に分かれる場合があるが、第 1 トークンを許可すれば連鎖は自然に続く
    (続きは LM が学習済の分布で生成する)。
    """

    def __init__(self, tokenizer, type_vocab: TypeVocabIndex):
        self.tokenizer = tokenizer
        self.type_vocab = type_vocab
        self.vocab_size: int = len(tokenizer)
        self._cache: dict[frozenset[int], torch.Tensor] = {}

    def build_mask_for_type_ids(self, type_ids: Iterable[int]) -> torch.Tensor:
        """指定 type_id 集合の許可マスク [V] を返す (bool tensor)"""
        key = frozenset(int(t) for t in type_ids)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        allowed: set[int] = set()
        for tid in key:
            entry = self.type_vocab.get(tid)
            if entry is None or not entry.is_generatable:
                continue
            for first in self._first_tokens_for_name(entry.name):
                allowed.add(first)

        mask = torch.zeros(self.vocab_size, dtype=torch.bool)
        for tok_id in allowed:
            if 0 <= tok_id < self.vocab_size:
                mask[tok_id] = True

        self._cache[key] = mask
        return mask

    def _first_tokens_for_name(self, name: str) -> list[int]:
        """`name` と ` name` をエンコードして両者の第 1 トークン ID を返す"""
        if not name:
            return []
        first_tokens: list[int] = []
        for variant in (name, " " + name):
            try:
                ids = self.tokenizer.encode(variant, add_special_tokens=False)
            except TypeError:
                # add_special_tokens を受け付けない簡易トークナイザ向け
                ids = self.tokenizer.encode(variant)
            if ids:
                first_tokens.append(int(ids[0]))
        return first_tokens

    def clear_cache(self) -> None:
        self._cache.clear()
