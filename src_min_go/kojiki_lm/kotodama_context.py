"""
言霊コンテキスト (Go 版) — Oracle 呼び出しの **事前 filter**

decode 中、毎 token oracle (Go daemon) を呼ぶと P95 50ms × 256 token = 12.8s/q
の overhead になる。Python 側で安価な regex 事前 filter を入れ、「型 context の
可能性が低い位置」を skip して oracle 呼び出し回数を減らす。

責務分担:
  - Python (本ファイル):  text_buffer 末尾の安価な regex で「型位置候補」を pass
  - Go daemon (oracle):    AST ベースの精密判定 (scope_kind を含む QueryResult)

最終判定は oracle daemon 側に委ねるため、本ファイルは **false positive 寄り**
(過剰に oracle を呼ぶ) でよい。false negative (oracle を呼ばない判定ミス) が
あると bias 加算の機会損失になるので、誤検知よりも見落としを避ける。

TS 版 src_min/kojiki_lm/kotodama_context.py との違い:
  - Go には `<>` ジェネリック構文がない → for/if 不等式 `i <` の偽陽性が
    そもそも起きない。寛容な regex でよい
  - Go には三項演算子がない → `): ` の偽陽性なし
  - Go では戻り値型は `): ` の代わりに `) ` (型を伴う場合)、`) {` (戻り値型なし)
    の二択。区別は AST が行う
"""

from __future__ import annotations

import re

# 「次トークンが Go の型または識別子」の典型パターン (text の末尾にマッチ)。
# **過剰検出寄り**: oracle 側で AST 判定するため、Python 側は filter として
# 「明らかに型位置でない場合は skip」だけが役割。
# 重要: Qwen の BPE は token に前置空白を含む (例: `' result'` は 1 token)。
# decode 中の text_buffer は `var result` のように **末尾空白なし** で 1 step
# 止まる場合が typical。次の token (` []` や ` int`) が前置空白を含むため、
# `var result ` のような空白で終わる中間状態は生まれない。
#
# したがって filter pattern は `\s*$` (0 個以上) を使う。`\s+$` だと Qwen の
# 生成パターンを取り逃して言霊が一度も発火しない (smoke で実証済み)。
#
# 設計の歴史 (2026-05-21 更新):
# 初期実装は func_arg / func_return / var_decl / const_decl / type_alias を入れていた
# が、mbpp-go ablation (2026-05-20) で「**func_arg / func_return 位置は LM が既に
# top-1 で 0.9+ の確率で正解 token を選んでおり、+2.0 加算しても argmax は変わら
# ない**」ことが判明。bias_step_count が 374 問中 365 問で発火していたが、bias
# toggle で実際に出力が変わったのは 3 問 (0.8%) だけ。それも cosmetic な var_decl
# のスタイル差で pass@1 / vet に効かなかった。
#
# 修正方針: 「LM が確信してる関数シグネチャ位置」を除外し、**LM が型の選択に迷う
# 難所** に発火位置を絞る。具体的には:
#   - chan の elem type: `chan ___`
#   - map の key/val type: `map[___]V` / `map[K]___`
#   - slice の elem type: `[]___`
#   - interface method の return type: `interface { M() ___ }`
#   - type assertion の型: `x.(___)`
# これら複合型の elem 位置は LM の確信度が低く、bias で誘導できる余地がある。
_TYPE_POSITION_HINTS: tuple[re.Pattern[str], ...] = (
    # === 既存: 宣言位置 (var_decl は唯一 argmax を動かす実績あり) ===
    # var 宣言の型位置: `var x` / `var x `
    re.compile(r"\bvar\s+\w+\s*$"),
    # const 宣言の型位置: `const x` / `const x `
    re.compile(r"\bconst\s+\w+\s*$"),
    # type alias の右辺: `type T` / `type T `
    re.compile(r"\btype\s+\w+\s*$"),

    # === 新規: 複合型の elem 位置 (難所、LM の確信度低め) ===
    # チャネル elem 型: `chan` / `chan ` / `chan<- ` / `<-chan `
    re.compile(r"\bchan\s*$"),
    re.compile(r"<-chan\s*$"),
    re.compile(r"\bchan<-\s*$"),
    # マップ key 型: `map[` (cursor 直後)
    re.compile(r"\bmap\[\s*$"),
    # マップ value 型: `map[K]` (key 閉じ後)
    re.compile(r"\bmap\[\w+\]\s*$"),
    re.compile(r"\bmap\[\[\]\w+\]\s*$"),  # `map[[]K]` のように key が slice
    # スライス elem 型: `[]` (前に整数リテラルや変数が無いことが必要、`a[i]` を弾く)
    re.compile(r"(?:^|[^\w\)])\[\]\s*$"),
    # 配列 elem 型: `[3]` のように数値長
    re.compile(r"\b\[\d+\]\s*$"),
    # interface method の return: `interface { Method() ` (引数閉じ後で `{` 内)
    re.compile(r"\binterface\s*\{[^}]*\)\s*$"),
    # type assertion `.(`: `x.(`
    re.compile(r"\)\s*\.\(\s*$"),
    re.compile(r"\w\.\(\s*$"),
    # struct field の型位置: `type T struct { Field ` (フィールド名の後)
    re.compile(r"\bstruct\s*\{[^}]*\b\w+\s*$"),
)

# 偽陽性ガード。Go ではジェネリック `<` も三項 `:` もないので積極的なガードは
# 不要だが、明らかに型位置でない末尾を弾く保険として。
#
# 重要: 全て **text の末尾 (cursor 直前)** を見る regex。MULTILINE で
# prompt 中の任意行にマッチさせると、HumanEval-Go の docstring の `// ...` で
# 常時 reject されて言霊が一度も発火しない不具合になる (smoke で確認)。
_NON_TYPE_TAILS: tuple[re.Pattern[str], ...] = (
    re.compile(r"[a-zA-Z0-9_)\]]\s*[<>!=]=?\s*$"),    # 比較演算子
    re.compile(r"[+\-*/%&|^]\s*$"),                     # 算術 / 論理 二項演算子
    re.compile(r":=\s*$"),                              # short var decl
    re.compile(r"=\s*$"),                               # 代入
    # 末尾の行 (最後の改行以降) が `//` で始まるなら、現在のカーソルはコメント中
    re.compile(r"(?:\A|\n)[^\n]*//[^\n]*$"),
)

_CONTEXT_WINDOW = 200


def looks_like_type_position(text: str) -> bool:
    """text の末尾が **型 position の可能性ある形** か、安価な regex で判定する。

    True を返したら oracle daemon に scope_kind を問い合わせる価値があり、
    False ならスキップ (decode を vanilla で進める)。False positive 寄り。
    """
    if not text:
        return False
    tail = text[-_CONTEXT_WINDOW:]

    # 偽陽性ガード: 明らかに型位置でない末尾なら早期 reject
    for p in _NON_TYPE_TAILS:
        if p.search(tail):
            return False

    # type-position hint のどれかにヒット
    return any(p.search(tail) for p in _TYPE_POSITION_HINTS)
