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
_TYPE_POSITION_HINTS: tuple[re.Pattern[str], ...] = (
    # 関数引数の型位置 (後続の引数): `func f(x int, y` / `func f(x int, y `
    re.compile(r"\bfunc\s+\w*\s*\([^)]*[,(]\s*\w+\s*$"),
    # 関数の最初の引数: `func f(x` / `func f(x `
    re.compile(r"\bfunc\s+\w*\s*\(\s*\w+\s*$"),
    # 関数戻り値型: `func f(...)` / `func f(...) ` (引数閉じた直後)
    re.compile(r"\bfunc\s+\w+\s*\([^()]*\)\s*$"),
    # var 宣言の型位置: `var x` / `var x `
    re.compile(r"\bvar\s+\w+\s*$"),
    # const 宣言の型位置: `const x` / `const x `
    re.compile(r"\bconst\s+\w+\s*$"),
    # type alias の右辺: `type T` / `type T `
    re.compile(r"\btype\s+\w+\s*$"),
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
