"""
言霊コンテキスト (Elixir target 版) — Oracle 呼び出しの **事前 filter**

src_min_go/kojiki_lm/kotodama_context.py の Go 用「型位置 hint」を Elixir 用に書き換えた。
Elixir は静的型を持たないため「型位置」概念は無く、代わりに **シンボル位置** (Module の
function 呼び出し位置、struct field 位置) を検出する ([[feedback-elixir-has-no-static-types]])。

責務分担:
  - Python (本ファイル): text_buffer 末尾の安価な regex で「シンボル位置候補」を pass
  - oracle (elixir_symbol_oracle): hardcoded stdlib lookup で実際の symbol 集合を返す

False positive 寄りで OK (= oracle 側で最終判定して None なら bias 加算 skip)。
False negative の方が痛い (bias 加算機会の見逃し)。

## Elixir で検出するシンボル位置

| 位置 | 例 | 判定 |
|---|---|---|
| `Module.<cursor>` | `String.<cursor>` | True (Module function 呼び出し) |
| `%Module{<cursor>:` | `%User{<cursor>` | True (struct field、将来対応) |
| `Module.func(<cursor>` | 関数引数 | False (引数の型は動的、bias 対象なし) |
| `def foo(<cursor>` | パラメータ位置 | False (動的) |
| `case x do; <cursor>` | clause head | False (任意 atom) |

注: `looks_like_type_position` という関数名は **Go 版からの継承で historical**。
Elixir では「型」ではなく「シンボル」位置だが、kotodama_decoder.py が同 symbol を import
しているため互換性のために名前を維持。
"""

from __future__ import annotations

import re

# 「次トークンが Elixir のシンボル (Module function / struct field)」の典型パターン
# (text の末尾にマッチ)。**過剰検出寄り**: oracle 側で最終判定するため、Python 側は
# filter として「明らかにシンボル位置でない場合は skip」だけが役割。
#
# Qwen の BPE 特性 (token に前置空白を含む) は Go 版と同じため、`\s*$` (0 個以上) を
# 使う。
_SYMBOL_POSITION_HINTS: tuple[re.Pattern[str], ...] = (
    # Module.func 呼び出し位置: `Module.` (cursor 直後)
    # 例: `String.`, `Enum.`, `Kernel.`, `MyModule.`
    # Module は必ず大文字始まり (Elixir の `module()` 関数値などとは別)
    re.compile(r"(?<![A-Za-z0-9_.])[A-Z][A-Za-z0-9_]*\.\s*$"),

    # struct field 位置: `%Module{` (cursor 直後、struct field 名が来る)
    re.compile(r"%[A-Z][A-Za-z0-9_.]*\{\s*$"),

    # `|>` パイプ後 (次のトークンは関数 or `Module.func` の可能性)
    re.compile(r"\|>\s*$"),
)

# 偽陽性ガード。明らかにシンボル位置でない末尾を弾く保険。
_NON_SYMBOL_TAILS: tuple[re.Pattern[str], ...] = (
    # 比較演算子の直後 (右辺は値、シンボル選択ではない)
    re.compile(r"[a-zA-Z0-9_)\]\}]\s*(?:==|!=|<=|>=|<|>)\s*$"),
    # 算術 / 論理 二項演算子の直後
    re.compile(r"[+\-*/%]\s*$"),
    # 単独 `=` (代入直後、値が来る)
    re.compile(r"(?<![=!<>])=\s*$"),
    # 末尾の行が `#` コメント中
    re.compile(r"(?:\A|\n)[^\n]*#[^\n]*$"),
    # `~` sigil 直後 (e.g., `~r/.../`, sigil 引数は型 atom ではない)
    re.compile(r"~[a-zA-Z]\s*$"),
)

_CONTEXT_WINDOW = 200


def looks_like_type_position(text: str) -> bool:
    """text の末尾が **シンボル位置の可能性ある形** か、安価な regex で判定する。

    関数名は Go 版からの継承 (historical)。Elixir では「型位置」ではなく
    「シンボル位置 (Module.func / %Struct{)」を意味する。

    True を返したら oracle に symbol 集合を問い合わせる価値があり、
    False ならスキップ (decode を vanilla で進める)。False positive 寄り。
    """
    if not text:
        return False
    tail = text[-_CONTEXT_WINDOW:]

    # 偽陽性ガード: 明らかにシンボル位置でない末尾なら早期 reject
    for p in _NON_SYMBOL_TAILS:
        if p.search(tail):
            return False

    # symbol-position hint のどれかにヒット
    return any(p.search(tail) for p in _SYMBOL_POSITION_HINTS)
