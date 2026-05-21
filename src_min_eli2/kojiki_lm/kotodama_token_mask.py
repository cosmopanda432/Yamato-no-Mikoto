"""
言霊トークン bias 配列 (言語非依存) — symbol names → BPE first-token logit bias

Oracle (Go: daemon / Elixir: Python 内 hardcoded stdlib) が返す symbol 名リストを、
Qwen BPE のトークン ID 集合に変換し、**logit に加算する bias 配列** を作る。

クラス名は `SymbolBiasBuilder` (旧 `GoSymbolBiasBuilder` を 2026-05-21 rename、
src_min_go では historical 名のまま、src_min_eli2 で言語非依存に統一)。

TS 版 src_min/kojiki_lm/kotodama_token_mask.py との設計上の違い (致命的):
  - TS 版は bool マスクを作って logits を `masked_fill_(-inf)` していた
    → LM の正解 token を物理的に殺し、tsc strict pass rate を −24pp 悪化させた
  - 本実装は **+k (デフォルト +2.0) の bias を加算** する、float tensor を作る
    → LM の正解を残しつつ、許可された token に確率重み付けで誘導する

Bias 配列は `[V]` (vocab_size 長の float32 tensor)。許可された token id の位置に +k、
それ以外 0。decode 時 `last_logits += bias` で適用する。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import torch


@dataclass(frozen=True)
class BiasConfig:
    """logit bias の重み設定"""
    bias_value: float = 2.0
    """logit に加算する bias の大きさ。+2.0 でだいたい softmax 確率が e^2 ≈ 7.4 倍
    に押し上げられる感覚。-inf 強制でないので、LM の強い確信を持つ正解 token は
    bias を当てなくても勝てる"""

    include_space_prefix: bool = True
    """`number` と ` number` の両方を許可するか。Go の BPE では `int` と ` int`
    が別 token になることが多いので True 推奨"""


class SymbolBiasBuilder:
    """allowed symbol 名 → logit bias 配列 [V]

    使い方:
        builder = SymbolBiasBuilder(tokenizer, lm_vocab_size=152064)
        bias = builder.build_bias_for_symbols(
            types=("int", "string", "MyStruct"),
            vars_=("a", "b"),
            scope_kind="func_arg",
            config=BiasConfig(bias_value=2.0),
        )
        # bias は [V] の float tensor, 該当 id に +2.0, それ以外 0
        last_logits += bias.to(last_logits.device)
    """

    def __init__(self, tokenizer, vocab_size: int) -> None:
        self.tokenizer = tokenizer
        self.vocab_size = int(vocab_size)
        self._cache: dict[tuple, torch.Tensor] = {}

    def build_bias_for_symbols(
        self,
        types: Iterable[str],
        vars_: Iterable[str],
        scope_kind: str,
        config: BiasConfig | None = None,
    ) -> torch.Tensor:
        """symbol 集合から bias 配列 [V] を作る (cache 付き)。

        scope_kind が "func_return" / "func_arg" / "var_decl" / "const_decl" /
        "type_alias" のとき: 主に types に bias
        scope_kind が "var_decl" の代入位置や式位置のとき: 主に vars にも bias
        v0.1 は単純化: 常に types ∪ vars に bias を当てる
        """
        cfg = config or BiasConfig()

        key_types = tuple(sorted(set(types)))
        key_vars = tuple(sorted(set(vars_)))
        cache_key = (key_types, key_vars, scope_kind, cfg.bias_value, cfg.include_space_prefix)

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        # 全 symbol 名を first-token id に変換
        allowed_ids: set[int] = set()
        for name in key_types + key_vars:
            for tid in self._first_tokens_for_name(name, cfg.include_space_prefix):
                if 0 <= tid < self.vocab_size:
                    allowed_ids.add(tid)

        bias = torch.zeros(self.vocab_size, dtype=torch.float32)
        if allowed_ids:
            ids_t = torch.tensor(sorted(allowed_ids), dtype=torch.long)
            bias[ids_t] = cfg.bias_value

        self._cache[cache_key] = bias
        return bias

    def _first_tokens_for_name(self, name: str, include_space: bool) -> list[int]:
        """`name` (および ` name`) を encode してそれぞれの第 1 token を返す"""
        if not name:
            return []
        out: list[int] = []
        variants = [name]
        if include_space:
            variants.append(" " + name)
        for variant in variants:
            try:
                ids = self.tokenizer.encode(variant, add_special_tokens=False)
            except TypeError:
                ids = self.tokenizer.encode(variant)
            if ids:
                out.append(int(ids[0]))
        return out

    def clear_cache(self) -> None:
        self._cache.clear()
