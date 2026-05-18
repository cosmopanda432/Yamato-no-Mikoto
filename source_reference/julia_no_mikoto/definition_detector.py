"""
定義位置検出 (Definition Detector)

Juliaコードのトークン列からstruct/function/const/abstract/primitiveの
定義位置を特定し、八咫鏡Attentionで使用するマスクを生成する。

トークンIDベースで検出を行うため、トークナイザーに依存する。
"""

from typing import Optional, Set

import torch


class DefinitionDetector:
    """
    Juliaコードから定義位置を検出

    struct, mutable struct, function, const, abstract type, primitive type
    の定義キーワードから一定範囲をマーキングする。

    Args:
        tokenizer: トークナイザー（encode メソッドを持つオブジェクト）
        definition_span: 定義キーワードからマーキングするトークン数
    """

    def __init__(self, tokenizer=None, definition_span: int = 20):
        self.definition_span = definition_span

        # 定義キーワード群
        self._definition_keywords = [
            "struct", "mutable", "function", "const",
            "abstract", "primitive",
        ]

        # トークンIDのキャッシュ
        self._keyword_token_ids: Optional[Set[int]] = None
        self._struct_token_ids: Optional[Set[int]] = None
        self._function_token_ids: Optional[Set[int]] = None
        self._const_token_ids: Optional[Set[int]] = None
        self._type_token_ids: Optional[Set[int]] = None

        if tokenizer is not None:
            self._init_token_ids(tokenizer)

    def _init_token_ids(self, tokenizer):
        """トークナイザーからキーワードのトークンIDを取得"""
        self._struct_token_ids = self._get_token_ids(tokenizer, ["struct", "mutable"])
        self._function_token_ids = self._get_token_ids(tokenizer, ["function"])
        self._const_token_ids = self._get_token_ids(tokenizer, ["const"])
        self._type_token_ids = self._get_token_ids(tokenizer, ["abstract", "primitive"])

        # 全キーワードの統合セット
        self._keyword_token_ids = set()
        for ids in [
            self._struct_token_ids,
            self._function_token_ids,
            self._const_token_ids,
            self._type_token_ids,
        ]:
            self._keyword_token_ids.update(ids)

    @staticmethod
    def _get_token_ids(tokenizer, keywords):
        """キーワードのトークンIDを取得"""
        ids = set()
        for kw in keywords:
            try:
                encoded = tokenizer.encode(kw)
                if isinstance(encoded, list):
                    ids.update(encoded)
                elif isinstance(encoded, int):
                    ids.add(encoded)
                else:
                    # torch.Tensor等の場合
                    ids.update(encoded.tolist() if hasattr(encoded, "tolist") else [encoded])
            except Exception:
                continue
        return ids

    def detect(self, token_ids: torch.Tensor) -> torch.Tensor:
        """
        定義位置のマスクを生成

        Args:
            token_ids: [batch, seq_len] トークンID列

        Returns:
            definition_mask: [batch, seq_len] 定義位置は1.0、それ以外は0.0
        """
        batch_size, seq_len = token_ids.shape
        mask = torch.zeros(
            batch_size, seq_len,
            dtype=torch.float,
            device=token_ids.device,
        )

        if self._keyword_token_ids is None:
            # トークナイザーが設定されていない場合は空マスクを返す
            return mask

        for b in range(batch_size):
            tokens = token_ids[b].tolist()
            in_definition = False
            definition_start = 0

            for i, tok in enumerate(tokens):
                # 定義開始を検出
                if tok in self._keyword_token_ids:
                    in_definition = True
                    definition_start = i

                # 定義範囲内をマーク
                if in_definition:
                    mask[b, i] = 1.0

                    # definition_span トークン以内を定義とみなす
                    if i - definition_start >= self.definition_span:
                        in_definition = False

        return mask

    def detect_from_roles(self, token_roles: torch.Tensor) -> torch.Tensor:
        """
        トークン役割から定義位置を推定（トークナイザー不要版）

        KEYWORD(4)ロールのトークンから一定範囲を定義としてマーキング。
        token_rolesが利用可能な場合のフォールバック。

        Args:
            token_roles: [batch, seq_len] トークン役割ID

        Returns:
            definition_mask: [batch, seq_len]
        """
        batch_size, seq_len = token_roles.shape
        mask = torch.zeros(
            batch_size, seq_len,
            dtype=torch.float,
            device=token_roles.device,
        )

        # KEYWORD = 4, TYPE_ANNOTATION = 3
        keyword_mask = (token_roles == 4)  # KEYWORD

        for b in range(batch_size):
            in_definition = False
            definition_start = 0

            for i in range(seq_len):
                if keyword_mask[b, i]:
                    in_definition = True
                    definition_start = i

                if in_definition:
                    mask[b, i] = 1.0
                    if i - definition_start >= self.definition_span:
                        in_definition = False

        return mask
