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
#
# 各パターンは「**直近の text_buffer 末尾**で型注釈位置にあるか」を保守的に判定する。
# 偽陽性は型マスクで識別子生成を阻害するため (例: `for (i < ` の `<` をジェネリック
# `Array<` と誤認すると `number.length` 等の混入を招く)、できるだけタイトに書く。
_TYPE_CONTEXT_PATTERNS: tuple[re.Pattern[str], ...] = (
    # 関数引数の型注釈:  function foo(x: |
    re.compile(r"\b[A-Za-z_$][\w$]*\s*:\s*$"),
    # 関数戻り値型:       function foo(...): |   |  () => ...): |  |  const f = (...): |
    # ※ 三項演算子 (`? ...() : `) との誤発火を避けるため、直近に次のいずれかを要求:
    #   - `function` キーワード経由 (named function)
    #   - `=>` 経由 (既に arrow body 内にある場合)
    #   - `=` 直後の `(...)` 経由 (arrow function 定義の最中)
    #   いずれの場合も直近の `?` (三項) を含まないこと
    re.compile(
        r"(?:"
        r"\bfunction\b"
        r"|"
        r"=>"
        r"|"
        r"=\s*(?=\()"       # `= (` を 0-width で確認 ((...) は後段に消費させる)
        r")"
        r"[^?\n]{0,300}\)\s*:\s*$"
    ),
    # 変数宣言:           const x: |  let y: |  var z: |
    re.compile(r"\b(?:const|let|var)\s+[A-Za-z_$][\w$]*\s*:\s*$"),
    # ジェネリック引数:   Array< |   Promise< |   Map< |
    # ※ for/if 不等式 (`i < `, `balance < `) との誤発火を避けるため、
    #   慣習に従い **大文字始まりの識別子直後の `<`** のみに限定。
    #   TS の組み込みジェネリック (Array/Promise/Map/Set/Record/Partial/Readonly/...)
    #   は全て大文字始まりで、小文字始まりの primitive (string/number/boolean) は
    #   `<>` を取らないため、これで実用上ほぼ網羅できる。
    re.compile(r"\b[A-Z][\w$]*\s*<\s*$"),
    # 型エイリアス:       type Foo = |
    re.compile(r"\btype\s+[A-Za-z_$][\w$]*\s*=\s*$"),
    # interface フィールド型:  prop: |  (オブジェクトリテラル内も含む)
    re.compile(r"^\s*[A-Za-z_$][\w$]*\??\s*:\s*$", re.MULTILINE),
)

# context 判定で見る末尾ウィンドウ (LOC が長くても regex を高速に保つ)
_CONTEXT_WINDOW = 200


# 型注釈位置で「予測対象 identifier」を抜き出すパターン群。
# 学習データ (ManyTypes4TS, scripts/data/prepare_sft_dataset.py) は per-token labeling で
# **identifier 自身の最初の subword** に型 label を乗せている。よって decode 時に TypeHead
# を呼ぶ正しい位置は、`:` の直後の空白ではなく **その identifier の最初 subword 位置**。
# ここでは text_buffer 末尾の型 context パターンごとに、その predict-target identifier の
# **char span** (キャプチャグループ 1) を取り出す。
_IDENTIFIER_FOR_TYPE_PATTERNS: tuple[re.Pattern[str], ...] = (
    # 関数引数: `(x:` / `, y:` の x / y
    re.compile(r"[(,]\s*([A-Za-z_$][\w$]*)\s*:\s*$"),
    # 変数宣言: `const x:` / `let y:` / `var z:` の x / y / z
    re.compile(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*:\s*$"),
    # 関数戻り値型 (named function): `function foo(...):` の foo
    re.compile(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\([^()]*\)\s*:\s*$"),
    # arrow function 戻り値型: `const f = (...): ` の f (引数 () は空でも可)
    re.compile(
        r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\([^()]*\)\s*:\s*$"
    ),
    # interface / object literal フィールド: `prop:` の prop (行頭起点)
    re.compile(r"^\s*([A-Za-z_$][\w$]*)\??\s*:\s*$", re.MULTILINE),
)


def is_type_context(text: str) -> bool:
    """text の末尾が「次は TS 型」位置かを heuristic 判定"""
    if not text:
        return False
    tail = text[-_CONTEXT_WINDOW:]
    return any(p.search(tail) for p in _TYPE_CONTEXT_PATTERNS)


def find_predict_target_char_span(text: str) -> tuple[int, int] | None:
    """type-context 中に「学習時に label が付いていた identifier」の char span を返す

    Stage 2 の per-token labeling では identifier 自身の subword に型 label が乗っているため、
    decode 時に TypeHead を呼ぶべき hidden は「: の直前の空白」ではなく
    **その identifier の最初 subword** の hidden。本関数はその identifier の **char 範囲**
    を text 全体の絶対 offset で返す。

    Returns:
        (start, end) — text[start:end] が identifier 文字列
        type-context でない、または identifier が抽出できない場合は None
    """
    if not text:
        return None
    tail = text[-_CONTEXT_WINDOW:]
    base = len(text) - len(tail)
    # 末尾に最も近い (最後のヒット) を採用するため、各パターンでマッチを取り
    # キャプチャ start が最も大きいものを選ぶ
    best: tuple[int, int] | None = None
    for pat in _IDENTIFIER_FOR_TYPE_PATTERNS:
        for m in pat.finditer(tail):
            # 末尾までヒットしないパターンはスキップ (末尾要件は各パターンに `$` で表現済み)
            s, e = m.span(1)
            if best is None or s > best[0]:
                best = (s, e)
    if best is None:
        return None
    return (base + best[0], base + best[1])
