"""
yamatoLLM 学習・評価で共有するデータユーティリティ。

入力: data/processed/sft/*.parquet
列:  input_ids, attention_mask, labels, type_labels
"""

from __future__ import annotations

from typing import Dict, List, Optional

import pyarrow.parquet as pq
import torch
from torch.utils.data import Dataset

PAD_LABEL = -100


class ParquetSFTDataset(Dataset):
    """
    pyarrow Table を columnar のまま保持し、__getitem__ で 1 行ずつ Python に
    変換する。to_pylist() で全件 Python list 化すると 30 万行クラスの
    train.parquet で RAM 数十 GB を使い切るため。
    """

    def __init__(
        self,
        parquet_path: str,
        limit: Optional[int] = None,
        max_seq_length: Optional[int] = None,
    ):
        table = pq.read_table(parquet_path)
        if limit is not None:
            table = table.slice(0, limit)
        self._input_ids = table.column("input_ids")
        self._attention_mask = table.column("attention_mask")
        self._labels = table.column("labels")
        self._type_labels = table.column("type_labels")
        self._n_rows = table.num_rows
        self.max_seq_length = max_seq_length

    def __len__(self) -> int:
        return self._n_rows

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        ids = self._input_ids[idx].as_py()
        am = self._attention_mask[idx].as_py()
        lb = self._labels[idx].as_py()
        tl = self._type_labels[idx].as_py()
        if self.max_seq_length is not None and len(ids) > self.max_seq_length:
            ids = ids[: self.max_seq_length]
            am = am[: self.max_seq_length]
            lb = lb[: self.max_seq_length]
            tl = tl[: self.max_seq_length]
        return {
            "input_ids": torch.tensor(ids, dtype=torch.long),
            "attention_mask": torch.tensor(am, dtype=torch.long),
            "labels": torch.tensor(lb, dtype=torch.long),
            "type_labels": torch.tensor(tl, dtype=torch.long),
        }


def collate(batch: List[Dict[str, torch.Tensor]], pad_id: int) -> Dict[str, torch.Tensor]:
    max_len = max(item["input_ids"].shape[0] for item in batch)

    def pad(t: torch.Tensor, pad_val: int) -> torch.Tensor:
        n = max_len - t.shape[0]
        if n == 0:
            return t
        return torch.cat([t, torch.full((n,), pad_val, dtype=t.dtype)])

    return {
        "input_ids": torch.stack([pad(b["input_ids"], pad_id) for b in batch]),
        "attention_mask": torch.stack([pad(b["attention_mask"], 0) for b in batch]),
        "labels": torch.stack([pad(b["labels"], PAD_LABEL) for b in batch]),
        "type_labels": torch.stack([pad(b["type_labels"], PAD_LABEL) for b in batch]),
    }
