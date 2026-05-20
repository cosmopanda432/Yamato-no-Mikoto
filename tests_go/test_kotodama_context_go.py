"""kotodama_context (Go 用 事前 filter) のテスト"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src_min_go"))

from kojiki_lm.kotodama_context import looks_like_type_position  # noqa: E402


@pytest.mark.parametrize("text", [
    # === 宣言位置 (残置: var_decl は唯一 argmax を動かす実績あり) ===
    # 変数宣言
    "var x ",
    "const Z ",
    # type alias
    "type Foo ",
    # === 2026-05-21 追加: 「難所」型位置 (func_arg / func_return より優先) ===
    # チャネル elem
    "ch := make(chan ",
    "var c chan",
    "<-chan",
    # マップ key/val
    "m := map[",
    "var m map[string]",
    # スライス elem
    "var s []",
    "return []",
    # interface method return
    "type R interface { Foo() ",
    # type assertion
    "v.(",
    "x.(",
    # struct field
    "type T struct { Name ",
])
def test_pass_filter_for_likely_type_position(text: str):
    assert looks_like_type_position(text), f"expected to pass: {text!r}"


@pytest.mark.parametrize("text", [
    # 不等式末尾は skip
    "for i := 0; i < ",
    "if x > ",
    "if balance != ",
    # 算術演算子末尾は skip
    "x + ",
    "y * ",
    # 代入 / short var
    "x := ",
    "x = ",
    # 空テキスト
    "",
    # === 2026-05-21 追加: func_arg / func_return は除外 (LM 高確信、bias 不発) ===
    "func add(a int, b ",
    "func f(\n  bar ",
    "func process(data ",
    "func square(x ",
    "func Greet(name string) ",
    "func Distance(p Point, q Point) ",
])
def test_skip_filter_for_non_type_tails(text: str):
    assert not looks_like_type_position(text), f"expected to skip: {text!r}"


def test_long_text_only_examines_tail():
    head = "func add(a int, b " + " " * 500 + "{ return a + b }"
    assert not looks_like_type_position(head)


def test_prompt_docstring_does_not_block_var_decl():
    """HumanEval-Go の prompt に含まれる `// xxx` コメント行があっても、
    その後の `var result ` で正しく言霊 filter が True を返すこと (回帰)。
    smoke で発覚: MULTILINE な `//.*$` regex は prompt 中の任意の行にマッチして
    全 step で skip 判定されてしまう"""
    prompt = (
        "// Check if in given list of numbers, are any two numbers closer\n"
        "// to each other than given threshold.\n"
        "func has_close_elements(numbers []float64, threshold float64) bool {\n"
        "\tvar result "
    )
    assert looks_like_type_position(prompt)


def test_slice_elem_does_not_match_array_index():
    """`arr[i]` のような添字アクセスを slice elem 型として誤検出しないこと"""
    # `arr[i]` の後の末尾は `]` で終わる、slice elem 型位置 (`[]`) と区別する必要
    assert not looks_like_type_position("if arr[i] == 0")
    assert not looks_like_type_position("v := arr[i]")


def test_current_line_comment_still_rejected():
    """現在の (末尾の) 行が `//` から始まる場合は引き続き reject する"""
    text = "package main\n\nfunc f() {\n\t// TODO: type "
    assert not looks_like_type_position(text)
