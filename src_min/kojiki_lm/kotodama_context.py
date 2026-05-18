"""
言霊コンテキスト検出 (heuristic)

decode 時の text buffer 末尾を見て、「次のトークンが TS 型でなければならない」
位置に居るかを判定する。判定結果は KotodamaDecoder が **マスクを適用するか** を
決めるスイッチに使う。

M2 最小では正規表現ベースの heuristic。M2.5 で TS Compiler API (ts_tools) を
組み込んでより精度の高い判定に置換する想定。
"""

from __future__ import annotations

import re

# 「次トークンが TS 型」となる典型パターン。text の末尾にマッチさせる。
_TYPE_CONTEXT_PATTERNS: tuple[re.Pattern[str], ...] = (
    # 関数引数の型注釈:  function foo(x: |
    re.compile(r"\b[A-Za-z_$][\w$]*\s*:\s*$"),
    # 関数戻り値型:       function foo(...): |
    re.compile(r"\)\s*:\s*$"),
    # 変数宣言:           const x: |  let y: |  var z: |
    re.compile(r"\b(?:const|let|var)\s+[A-Za-z_$][\w$]*\s*:\s*$"),
    # ジェネリック引数:   Array< |   Promise< |
    re.compile(r"\b[A-Za-z_$][\w$]*\s*<\s*$"),
    # 型エイリアス:       type Foo = |
    re.compile(r"\btype\s+[A-Za-z_$][\w$]*\s*=\s*$"),
    # interface フィールド型:  prop: |  (オブジェクトリテラル内も含む)
    re.compile(r"^\s*[A-Za-z_$][\w$]*\??\s*:\s*$", re.MULTILINE),
)

# context 判定で見る末尾ウィンドウ (LOC が長くても regex を高速に保つ)
_CONTEXT_WINDOW = 200


def is_type_context(text: str) -> bool:
    """text の末尾が「次は TS 型」位置かを heuristic 判定"""
    if not text:
        return False
    tail = text[-_CONTEXT_WINDOW:]
    return any(p.search(tail) for p in _TYPE_CONTEXT_PATTERNS)
