"""TypeVocabIndex と KotodamaMaskBuilder の単体テスト"""

import json
from pathlib import Path

import pytest
import torch

from kojiki_lm.kotodama_token_mask import (
    GENERATABLE_CATEGORIES,
    KotodamaMaskBuilder,
    TypeVocabIndex,
)

from .conftest import MockTokenizer

REAL_VOCAB = Path(__file__).resolve().parent.parent / "config" / "ts_type_vocab.json"


class TestTypeVocabIndex:
    def test_loads_real_vocab(self):
        idx = TypeVocabIndex(REAL_VOCAB)
        assert idx.vocab_size == 256
        assert len(idx) > 0
        # id=2 は "string" / primitives であるはず
        e = idx.get(2)
        assert e is not None
        assert e.name == "string"
        assert e.category == "primitives"
        assert e.is_generatable

    def test_unknown_id(self):
        idx = TypeVocabIndex(REAL_VOCAB)
        assert idx.get(99999) is None

    def test_generatable_excludes_instability_and_special(self):
        idx = TypeVocabIndex(REAL_VOCAB)
        gen = idx.generatable_ids()
        # 0 は special (UNK) なので含まれない
        assert 0 not in gen
        # 個別に category を確認
        for tid in gen:
            entry = idx.get(tid)
            assert entry is not None
            assert entry.category in GENERATABLE_CATEGORIES


class TestKotodamaMaskBuilder:
    def setup_method(self):
        self.tokenizer = MockTokenizer({
            "number": 10,
            " number": 11,
            "string": 20,
            " string": 21,
            "Promise": 30,
            " Promise": 31,
            "ImplicitAny": 40,         # category="instability" → 除外されるはず
            " ImplicitAny": 41,
        })
        self.idx = TypeVocabIndex(REAL_VOCAB)
        self.builder = KotodamaMaskBuilder(self.tokenizer, self.idx)

    def test_mask_shape(self):
        mask = self.builder.build_mask_for_type_ids([3])  # number
        assert mask.shape == (len(self.tokenizer),)
        assert mask.dtype == torch.bool

    def test_number_mask_allows_number_token(self):
        # id=3 が "number" であることを vocab で確認してから
        assert self.idx.get(3).name == "number"
        mask = self.builder.build_mask_for_type_ids([3])
        assert mask[10].item() is True   # "number"
        assert mask[11].item() is True   # " number"
        # 関係ない token は False
        assert mask[20].item() is False
        assert mask[30].item() is False

    def test_mask_union_for_multiple_type_ids(self):
        # number(3) + string(2)
        mask = self.builder.build_mask_for_type_ids([2, 3])
        assert mask[10].item() and mask[11].item()  # number
        assert mask[20].item() and mask[21].item()  # string

    def test_instability_category_excluded(self):
        # vocab に ImplicitAny が存在することを確認 (vocab json 内 reserved の最初)
        raw = json.loads(REAL_VOCAB.read_text())
        implicit_any_id = next(
            int(k) for k, v in raw["id_to_type"].items()
            if v.get("name") == "ImplicitAny"
        )
        e = self.idx.get(implicit_any_id)
        assert e is not None and e.category == "instability"

        mask = self.builder.build_mask_for_type_ids([implicit_any_id])
        # ImplicitAny は instability → どのトークンも許可されない
        assert mask[40].item() is False
        assert mask[41].item() is False
        assert int(mask.sum().item()) == 0

    def test_empty_input(self):
        mask = self.builder.build_mask_for_type_ids([])
        assert mask.shape == (len(self.tokenizer),)
        assert int(mask.sum().item()) == 0

    def test_unknown_type_id(self):
        mask = self.builder.build_mask_for_type_ids([99999])
        assert int(mask.sum().item()) == 0

    def test_cache_returns_same_tensor(self):
        a = self.builder.build_mask_for_type_ids([2, 3])
        b = self.builder.build_mask_for_type_ids([3, 2])  # 順番違っても同じ key
        assert a is b
