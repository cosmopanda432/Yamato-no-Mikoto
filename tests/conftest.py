"""
共通テストユーティリティ: GPU 非搭載 CPU で Kotodama を検証するためのモック群。
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn


class MockTokenizer:
    """
    語彙を辞書として明示する超簡易トークナイザ。
    Kotodama mask builder と decoder のテストに必要な API のみ実装する。

    encode は **最長一致 greedy**。未知文字は UNK_ID にフォールバック。
    """

    UNK_ID = 0
    PAD_ID = 1

    def __init__(self, str_to_id: dict[str, int], eos_token: str = "</s>") -> None:
        # 0/1 は UNK/PAD で予約。語彙に上書きされてはならない
        for sp in (self.UNK_ID, self.PAD_ID):
            assert sp not in str_to_id.values(), "0/1 は予約 ID"
        self._s2i = dict(str_to_id)
        if eos_token not in self._s2i:
            self._s2i[eos_token] = max(self._s2i.values()) + 1
        self._i2s = {v: k for k, v in self._s2i.items()}
        self.eos_token_id = self._s2i[eos_token]
        self.pad_token_id = self.PAD_ID

    def __len__(self) -> int:
        return max(self._s2i.values()) + 1

    def _encode_with_offsets(self, text: str) -> tuple[list[int], list[tuple[int, int]]]:
        """encode + (start, end) offset を同時に返す"""
        ids: list[int] = []
        offsets: list[tuple[int, int]] = []
        i = 0
        while i < len(text):
            matched = False
            for length in range(min(20, len(text) - i), 0, -1):
                cand = text[i : i + length]
                if cand in self._s2i:
                    ids.append(self._s2i[cand])
                    offsets.append((i, i + length))
                    i += length
                    matched = True
                    break
            if not matched:
                ids.append(self.UNK_ID)
                offsets.append((i, i + 1))
                i += 1
        return ids, offsets

    def encode(self, text: str, add_special_tokens: bool = False) -> list[int]:
        ids, _ = self._encode_with_offsets(text)
        return ids

    def __call__(
        self,
        text: str,
        return_tensors: str | None = None,
        return_offsets_mapping: bool = False,
        add_special_tokens: bool = False,
    ):
        ids, offsets = self._encode_with_offsets(text)
        result: dict = {"input_ids": ids, "attention_mask": [1] * len(ids)}
        if return_offsets_mapping:
            result["offset_mapping"] = offsets
        if return_tensors == "pt":
            t = torch.tensor([ids], dtype=torch.long)
            result["input_ids"] = t
            result["attention_mask"] = torch.ones_like(t)
        return result

    def decode(self, ids, skip_special_tokens: bool = True) -> str:
        out = []
        if isinstance(ids, torch.Tensor):
            ids = ids.tolist()
        for i in ids:
            i = int(i)
            if skip_special_tokens and i in (self.UNK_ID, self.PAD_ID, self.eos_token_id):
                continue
            out.append(self._i2s.get(i, ""))
        return "".join(out)


@dataclass
class MockOutput:
    """Qwen2ForCausalLM の出力に最低限互換な構造"""
    logits: torch.Tensor                       # [B, L, V]
    hidden_states: tuple[torch.Tensor, ...]    # 各層 [B, L, d]


class MockBackbone(nn.Module):
    """
    小型な「Qwen-like」backbone。embedding + linear LM head のみ。

    output_hidden_states=True で hidden_states を返す。decoder テストの
    forward 経路を回すだけの最小実装。
    """

    def __init__(self, vocab_size: int, d_model: int = 16, n_layers: int = 2) -> None:
        super().__init__()
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.n_layers = n_layers
        self.embed = nn.Embedding(vocab_size, d_model)
        self.lm_head = nn.Linear(d_model, vocab_size)

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
        output_hidden_states: bool = False,
        use_cache: bool = False,
        return_dict: bool = True,
        **kwargs,
    ) -> MockOutput:
        emb = self.embed(input_ids)                      # [B, L, d]
        logits = self.lm_head(emb)                       # [B, L, V]
        hidden_states = tuple(emb for _ in range(self.n_layers + 1))
        return MockOutput(logits=logits, hidden_states=hidden_states)


class MockTypeHead(nn.Module):
    """
    任意の type_id を「常に top-1 で返す」TypeHead のモック。
    KotodamaDecoder のテストで mask が掛かることを決定論的に検証する。
    """

    def __init__(self, type_vocab_size: int, forced_top_id: int) -> None:
        super().__init__()
        self.type_vocab_size = type_vocab_size
        self.forced_top_id = forced_top_id

    def forward(self, hidden_states: torch.Tensor) -> dict[str, torch.Tensor]:
        b, l, _ = hidden_states.shape
        logits = torch.full(
            (b, l, self.type_vocab_size), -1e3, dtype=hidden_states.dtype
        )
        logits[..., self.forced_top_id] = 100.0
        # 2 位以下も低いけど一応 deterministic に
        next_idx = (self.forced_top_id + 1) % self.type_vocab_size
        logits[..., next_idx] = 50.0
        return {"type_logits": logits, "type_preds": logits.argmax(dim=-1)}
