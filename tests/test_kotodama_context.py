"""is_type_context (heuristic) のテスト"""

import pytest

from kojiki_lm.kotodama_context import is_type_context


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


def test_long_text_only_examines_tail():
    # 末尾 200 文字だけ見る → 前半にある "function foo(x:" は無視されるべき
    head = "function foo(x: " + " " * 500 + "{ return 1; }"
    assert not is_type_context(head)
