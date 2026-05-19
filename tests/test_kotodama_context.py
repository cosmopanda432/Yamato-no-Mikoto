"""is_type_context / find_predict_target_char_span (heuristic) のテスト"""

import pytest

from kojiki_lm.kotodama_context import find_predict_target_char_span, is_type_context


@pytest.mark.parametrize("text", [
    "function foo(x: ",
    "function add(a: number, b: ",
    "function get(): ",
    "const x: ",
    "let y: ",
    "var z: ",
    "type MyType = ",
    "Array<",
    "Promise<",
    "interface Foo {\n  bar: ",
])
def test_recognises_type_context(text: str):
    assert is_type_context(text), f"should detect type context in: {text!r}"


@pytest.mark.parametrize("text", [
    "",
    "function foo() {",
    "const x = 1",
    "if (a > b) {",
    "return ",
    "console.log(",
    "// comment",
    "import { Foo } from 'bar'",
])
def test_rejects_non_type_context(text: str):
    assert not is_type_context(text), f"should NOT detect in: {text!r}"


@pytest.mark.parametrize("text", [
    # for/while ループ内の不等式 — `i < numbers.length` の `numbers` を生成すべき位置で
    # 「`i <` をジェネリック `Array<` と誤認」しないこと
    "for (let i = 0; i < ",
    "for (let i = 0; i <",
    "    for (let j = i + 1; j < ",
    "while (i < ",
    # if 内の不等式 — `balance < 0` のリテラル位置で型強制しないこと
    "    if (balance < ",
    "if (x < ",
    # 三項演算子の `: ` — `cond ? a : b` の b 位置で型強制しないこと
    "    index % 3 === 0 ? sorted.shift() : ",
    "    cond ? foo() : ",
    # case ラベル — TS の switch case で型強制しないこと
    "        case 'o':",
    # 小文字始まりの「ジェネリックっぽい」識別子 (関数名など) — 偽陽性回避
    "isLessThan(a, b) <",
])
def test_rejects_inequality_and_ternary_false_positives(text: str):
    """ロードマップ M2: ジェネリック検出と戻り値型検出の偽陽性回帰テスト

    `for (i < )` を `Array<` と、`shift() : ` を `): ` (戻り値型) と
    誤認すると、識別子位置で型語彙が強制され `number.length` 等の TS2304
    エラーを量産する (2026-05-19 smoke run で確認)。
    """
    assert not is_type_context(text), f"should NOT detect in: {text!r}"


@pytest.mark.parametrize("text", [
    # 大文字始まりのジェネリック型 (TS 慣習) は引き続き正しく検出する
    "    const x: Array<",
    "    return Promise<",
    "    let m: Map<",
    "Record<",
    "Partial<",
    # 関数戻り値型 (function キーワード経由) は検出する
    "function foo(): ",
    "function bar(x: number): ",
    # arrow function の戻り値型も検出する
    "const f = (x: number): ",
])
def test_keeps_legitimate_type_context_detection(text: str):
    assert is_type_context(text), f"should detect type context in: {text!r}"


def test_long_text_only_examines_tail():
    # 末尾 200 文字だけ見る → 前半にある "function foo(x:" は無視されるべき
    head = "function foo(x: " + " " * 500 + "{ return 1; }"
    assert not is_type_context(head)


# --- find_predict_target_char_span ---
# Stage 2 学習データ (scripts/data/prepare_sft_dataset.py の align_labels) は
# **identifier 自身の最初の subword** に型 label を乗せている。decode 時に
# TypeHead を呼ぶべき hidden 位置をこのヘルパーで取り出す。

@pytest.mark.parametrize("text,expected_substr", [
    # 関数引数: `(x: ` → identifier `x`
    ("function foo(x: ", "x"),
    # 関数引数 (連続): `, b: ` → identifier `b` (最後の引数)
    ("function add(a: number, b: ", "b"),
    # 関数引数 (改行入り): JS の typical な書き方
    ("function f(\n  bar: ", "bar"),
    # 変数宣言: `const x: ` → identifier `x`
    ("const x: ", "x"),
    ("let foo: ", "foo"),
    ("var bar: ", "bar"),
    # 関数戻り値型 (named function): `function foo(): ` → identifier `foo`
    ("function foo(): ", "foo"),
    ("function process(data: string[]): ", "process"),
    # arrow function 戻り値型: `const f = (...): ` → identifier `f`
    ("const f = (x: number): ", "f"),
    # interface フィールド: 行頭 `prop: ` → identifier `prop`
    ("interface Foo {\n  bar: ", "bar"),
])
def test_finds_predict_target_identifier(text: str, expected_substr: str):
    span = find_predict_target_char_span(text)
    assert span is not None, f"should find identifier in: {text!r}"
    s, e = span
    assert text[s:e] == expected_substr, (
        f"expected {expected_substr!r} but got {text[s:e]!r} at [{s},{e}) in {text!r}"
    )


@pytest.mark.parametrize("text", [
    # type-context ですらない場面では None
    "for (let i = 0; i < ",
    "if (balance < ",
    "    cond ? foo() : ",
    "        case 'o':",
    "",
    "function foo() {",
])
def test_no_target_for_non_type_context(text: str):
    assert find_predict_target_char_span(text) is None


def test_picks_last_identifier_when_multiple_candidates():
    """`function add(a: number, b: ` の場合、最後の identifier (b) を返す"""
    text = "function add(a: number, b: "
    span = find_predict_target_char_span(text)
    assert span is not None
    s, e = span
    assert text[s:e] == "b"
