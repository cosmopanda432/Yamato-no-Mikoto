"""GoSymbolBiasBuilder (allowed symbols → logit bias 配列) のテスト"""

from __future__ import annotations

import sys
from pathlib import Path

import torch

# 共通の MockTokenizer は tests/conftest.py にあるが、tests_go から re-use する
# のは複雑なので、ここでは最小版を内蔵する
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src_min_go"))

from kojiki_lm.kotodama_token_mask import BiasConfig, GoSymbolBiasBuilder  # noqa: E402


class MiniTokenizer:
    """encode(text) -> [first_token_id, ...] を返すだけの最小トークナイザ"""

    UNK = 0

    def __init__(self, s2i: dict[str, int]) -> None:
        self._s2i = dict(s2i)

    def __len__(self) -> int:
        return max(self._s2i.values()) + 1

    def encode(self, text: str, add_special_tokens: bool = False) -> list[int]:
        ids: list[int] = []
        i = 0
        while i < len(text):
            matched = False
            for L in range(min(20, len(text) - i), 0, -1):
                cand = text[i : i + L]
                if cand in self._s2i:
                    ids.append(self._s2i[cand])
                    i += L
                    matched = True
                    break
            if not matched:
                ids.append(self.UNK)
                i += 1
        return ids


VOCAB = {
    "int": 10, " int": 11,
    "string": 12, " string": 13,
    "bool": 14, " bool": 15,
    "error": 16, " error": 17,
    "MyStruct": 20, " MyStruct": 21,
    "a": 30, " a": 31,
    "b": 32, " b": 33,
    # 修正 G (2026-05-21): 型 composition keyword
    "interface": 40, " interface": 41,
    "struct": 42, " struct": 43,
    "map": 44, " map": 45,
    "chan": 46, " chan": 47,
    "func": 48, " func": 49,
    "</s>": 99,
}


def test_bias_array_shape_and_dtype():
    tok = MiniTokenizer(VOCAB)
    builder = GoSymbolBiasBuilder(tok, vocab_size=100)
    bias = builder.build_bias_for_symbols(
        types=("int", "string"),
        vars_=(),
        scope_kind="func_arg",
    )
    assert bias.shape == (100,)
    assert bias.dtype == torch.float32


def test_bias_value_applied_to_allowed_tokens():
    tok = MiniTokenizer(VOCAB)
    builder = GoSymbolBiasBuilder(tok, vocab_size=100)
    bias = builder.build_bias_for_symbols(
        types=("int", "string"),
        vars_=(),
        scope_kind="func_arg",
        config=BiasConfig(bias_value=2.5, include_space_prefix=True),
    )
    # int (10) と  int (11) と string (12) と  string (13) に +2.5
    for tid in (10, 11, 12, 13):
        assert bias[tid].item() == 2.5, f"expected bias at id {tid}"
    # 他は 0
    for tid in (0, 5, 50, 99):
        if tid not in (10, 11, 12, 13):
            assert bias[tid].item() == 0.0


def test_vars_also_get_bias():
    tok = MiniTokenizer(VOCAB)
    builder = GoSymbolBiasBuilder(tok, vocab_size=100)
    bias = builder.build_bias_for_symbols(
        types=(),
        vars_=("a", "b"),
        scope_kind="var_decl",
    )
    # `a` (30) / ` a` (31) / `b` (32) / ` b` (33) に bias
    for tid in (30, 31, 32, 33):
        assert bias[tid].item() > 0.0


def test_disable_space_prefix():
    tok = MiniTokenizer(VOCAB)
    builder = GoSymbolBiasBuilder(tok, vocab_size=100)
    bias = builder.build_bias_for_symbols(
        types=("int",),
        vars_=(),
        scope_kind="func_arg",
        config=BiasConfig(bias_value=1.0, include_space_prefix=False),
    )
    assert bias[10].item() == 1.0   # `int` のみ
    assert bias[11].item() == 0.0   # ` int` は除外


def test_no_inf_in_bias_array():
    """-inf は絶対に入れない (TS 版の轍を踏まない回帰テスト)"""
    tok = MiniTokenizer(VOCAB)
    builder = GoSymbolBiasBuilder(tok, vocab_size=100)
    bias = builder.build_bias_for_symbols(
        types=("int", "string"),
        vars_=("a",),
        scope_kind="func_arg",
        config=BiasConfig(bias_value=2.0),
    )
    assert torch.isfinite(bias).all().item(), \
        "bias array must contain only finite values; -inf is forbidden in Go 版"


def test_cache_returns_same_tensor():
    tok = MiniTokenizer(VOCAB)
    builder = GoSymbolBiasBuilder(tok, vocab_size=100)
    a = builder.build_bias_for_symbols(types=("int",), vars_=(), scope_kind="func_arg")
    b = builder.build_bias_for_symbols(types=("int",), vars_=(), scope_kind="func_arg")
    assert a is b  # 同じ key → cache hit


def test_composition_keywords_get_bias():
    """修正 G (2026-05-21): `interface` / `struct` / `map` / `chan` / `func` が
    Types として渡された場合に bias が乗ること。mbpp-go full run で
    `[]interface{}` の `interface` が allowed に含まれず bias=0 だった発見が動機"""
    tok = MiniTokenizer(VOCAB)
    builder = GoSymbolBiasBuilder(tok, vocab_size=100)
    bias = builder.build_bias_for_symbols(
        types=("int", "interface", "struct", "map", "chan", "func"),
        vars_=(),
        scope_kind="slice_elem",
        config=BiasConfig(bias_value=2.0, include_space_prefix=True),
    )
    # int / interface / struct / map / chan / func それぞれの bare 形と空白前置形
    expected_ids = (10, 11, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49)
    for tid in expected_ids:
        assert bias[tid].item() == 2.0, (
            f"expected bias=2.0 at token {tid}, got {bias[tid].item()}"
        )


def test_unknown_symbol_does_not_crash():
    tok = MiniTokenizer(VOCAB)
    builder = GoSymbolBiasBuilder(tok, vocab_size=100)
    bias = builder.build_bias_for_symbols(
        types=("WeirdNonExistentType",),
        vars_=(),
        scope_kind="func_arg",
    )
    # 未知シンボルは UNK_ID にエンコードされる、bias は UNK 位置に乗る可能性あるが
    # vocab_size に収まれば例外を投げない (実際には builder 側で 0 <= id < vocab を check)
    assert bias.shape == (100,)
    assert torch.isfinite(bias).all().item()
