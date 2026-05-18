"""
Mixture of Experts モデル (KojikiMoE)

shared_layers (標準ブロック) + moe_layers (MoEブロック) の構成。
MoEブロックではFFN部分が4エキスパート+ルーターに置換される。

アーキテクチャ:
    Genesis → YataKagami → shared_layers×2 → moe_layers×4 → Kuniumi → Yomi → Misogi
"""

from typing import Dict, List, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from .config import KojikiConfig, TYPE_SPECIFICITY, TYPE_DEPTH
from .layers import (
    GenesisLayer,
    SevenGenerationsBlock,
    KuninotokotachiSelfAttention,
    MultipleDispatchAttention,
    ToyokumoFeedForward,
    KuniumiLayer,
    YomiLayer,
    MisogiLayer,
)
from .yata_kagami_attention import YataKagamiAttention
from .definition_detector import DefinitionDetector


# ---------------------------------------------------------------------------
# MoE FFN
# ---------------------------------------------------------------------------

class MoERouter(nn.Module):
    """Top-k ルーター"""

    def __init__(self, d_model: int, num_experts: int, top_k: int = 2):
        super().__init__()
        self.gate = nn.Linear(d_model, num_experts, bias=False)
        self.top_k = top_k
        self.num_experts = num_experts

    def forward(self, x: torch.Tensor):
        """
        Args:
            x: [batch, seq, d_model]
        Returns:
            weights: [batch, seq, top_k]
            indices: [batch, seq, top_k]
            router_logits: [batch, seq, num_experts]
        """
        logits = self.gate(x)  # [batch, seq, num_experts]
        top_k_logits, top_k_indices = torch.topk(logits, self.top_k, dim=-1)
        top_k_weights = F.softmax(top_k_logits, dim=-1)
        return top_k_weights, top_k_indices, logits


class MoEFeedForward(nn.Module):
    """
    Mixture of Experts FFN

    複数のToyokumoFeedForwardエキスパートとルーターで構成。
    """

    def __init__(
        self,
        d_model: int,
        d_ff: int,
        num_experts: int = 4,
        top_k: int = 2,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.num_experts = num_experts
        self.top_k = top_k

        self.router = MoERouter(d_model, num_experts, top_k)
        self.experts = nn.ModuleList([
            ToyokumoFeedForward(d_model, d_ff, dropout)
            for _ in range(num_experts)
        ])

    def forward(self, x: torch.Tensor):
        """
        Args:
            x: [batch, seq, d_model]
        Returns:
            output: [batch, seq, d_model]
            router_logits: [batch, seq, num_experts]
        """
        batch, seq, d = x.shape
        weights, indices, router_logits = self.router(x)

        # 全エキスパートの出力を計算（簡易実装）
        output = torch.zeros_like(x)
        for k in range(self.top_k):
            expert_idx = indices[:, :, k]  # [batch, seq]
            expert_weight = weights[:, :, k].unsqueeze(-1)  # [batch, seq, 1]

            for e in range(self.num_experts):
                mask = (expert_idx == e)  # [batch, seq]
                if not mask.any():
                    continue
                # 該当トークンだけ処理
                expert_input = x * mask.unsqueeze(-1).float()
                expert_output = self.experts[e](expert_input)
                output = output + expert_output * expert_weight * mask.unsqueeze(-1).float()

        return output, router_logits


# ---------------------------------------------------------------------------
# MoE Transformer Block
# ---------------------------------------------------------------------------

class MoEBlock(nn.Module):
    """
    MoE版Transformerブロック

    SevenGenerationsBlockと同じAttention構造だが、
    FFN部分がMoEFeedForwardに置換されている。
    """

    def __init__(
        self,
        config: KojikiConfig,
        num_experts: int = 4,
        top_k: int = 2,
    ):
        super().__init__()

        self.kuninotokotachi = KuninotokotachiSelfAttention(
            config.d_model, config.n_heads, config.dropout
        )
        self.izanagi_izanami = MultipleDispatchAttention(
            config.d_model, config.n_heads, config.num_token_roles, config.dropout
        )
        self.moe_ffn = MoEFeedForward(
            config.d_model, config.d_ff, num_experts, top_k, config.dropout
        )

        self.norm1 = nn.LayerNorm(config.d_model)
        self.norm2 = nn.LayerNorm(config.d_model)
        self.norm3 = nn.LayerNorm(config.d_model)
        self.dropout = nn.Dropout(config.dropout)

    def forward(
        self,
        x: torch.Tensor,
        type_specificity_emb: torch.Tensor,
        token_roles: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns:
            x: [batch, seq, d_model]
            router_logits: [batch, seq, num_experts]
        """
        # Self-Attention
        residual = x
        x = self.norm1(x)
        x = residual + self.dropout(self.kuninotokotachi(x, mask))

        # Multiple Dispatch Attention
        residual = x
        x = self.norm2(x)
        x = residual + self.dropout(
            self.izanagi_izanami(x, type_specificity_emb, token_roles, mask)
        )

        # MoE FFN
        residual = x
        x = self.norm3(x)
        moe_out, router_logits = self.moe_ffn(x)
        x = residual + self.dropout(moe_out)

        return x, router_logits


# ---------------------------------------------------------------------------
# KojikiMoE Model
# ---------------------------------------------------------------------------

class KojikiMoE(nn.Module):
    """
    Mixture of Experts版 古事記言語モデル

    アーキテクチャ:
        Genesis → YataKagami → shared_layers×N → moe_layers×M → Kuniumi → Yomi → Misogi

    チェックポイント kojiki_moe_best.pt との互換性:
        shared_layers: 2 blocks (standard SevenGenerationsBlock)
        moe_layers: 4 blocks (MoEBlock with 4 experts)
    """

    def __init__(
        self,
        config: KojikiConfig,
        num_shared: int = 2,
        num_moe: int = 4,
        num_experts: int = 4,
        top_k: int = 2,
        tokenizer=None,
    ):
        super().__init__()
        self.config = config
        self.num_shared = num_shared
        self.num_moe = num_moe

        # 第一章: 天地開闢層
        self.genesis = GenesisLayer(config)

        # 八咫鏡Attention
        self.yata_kagami = YataKagamiAttention(
            d_model=config.d_model,
            n_heads=config.n_heads,
            dropout=config.dropout,
        )

        # 定義位置検出器
        self.definition_detector = DefinitionDetector(
            tokenizer=tokenizer,
            definition_span=20,
        )

        # 共有層（標準ブロック）
        self.shared_layers = nn.ModuleList([
            SevenGenerationsBlock(config) for _ in range(num_shared)
        ])

        # MoE層
        self.moe_layers = nn.ModuleList([
            MoEBlock(config, num_experts, top_k) for _ in range(num_moe)
        ])

        # 第三章: 国生み層
        self.kuniumi = KuniumiLayer(config)

        # 第四章: 黄泉国層
        self.yomi = YomiLayer(config)

        # 第五章: 禊層
        self.misogi = MisogiLayer(config)

        # 型メタデータテーブル
        self._init_type_metadata()

        # パラメータ初期化
        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
        elif isinstance(module, nn.LayerNorm):
            torch.nn.init.ones_(module.weight)
            torch.nn.init.zeros_(module.bias)

    def _init_type_metadata(self):
        spec_tensor = torch.zeros(self.config.type_vocab_size, dtype=torch.long)
        for type_id, spec in TYPE_SPECIFICITY.items():
            if type_id < self.config.type_vocab_size:
                spec_tensor[type_id] = spec
        self.register_buffer("type_metadata_spec", spec_tensor)

        depth_tensor = torch.zeros(self.config.type_vocab_size, dtype=torch.long)
        for type_id, depth in TYPE_DEPTH.items():
            if type_id < self.config.type_vocab_size:
                depth_tensor[type_id] = min(depth, self.config.type_hierarchy_depth - 1)
        self.register_buffer("type_metadata_depth", depth_tensor)

    def _create_causal_mask(self, seq_len: int, device: torch.device) -> torch.Tensor:
        mask = torch.triu(torch.ones(seq_len, seq_len, device=device), diagonal=1)
        mask = mask.masked_fill(mask == 1, float("-inf"))
        mask = mask.masked_fill(mask == 0, float(0.0))
        return mask.unsqueeze(0).unsqueeze(0)

    def forward(
        self,
        token_ids: torch.Tensor,
        type_ids: torch.Tensor,
        type_specificity: torch.Tensor,
        type_depth: torch.Tensor,
        token_roles: Optional[torch.Tensor] = None,
        type_hash: Optional[torch.Tensor] = None,
        definition_mask: Optional[torch.Tensor] = None,
        generation_phase: int = 0,
    ) -> Dict[str, torch.Tensor]:
        batch_size, seq_len = token_ids.shape
        device = token_ids.device

        if token_roles is None:
            token_roles = torch.zeros(batch_size, seq_len, dtype=torch.long, device=device)

        # 定義位置マスクの自動検出
        if definition_mask is None:
            if self.definition_detector._keyword_token_ids is not None:
                definition_mask = self.definition_detector.detect(token_ids)
            elif token_roles is not None and token_roles.any():
                definition_mask = self.definition_detector.detect_from_roles(token_roles)

        # 第一章: 天地開闢
        x, type_spec_emb = self.genesis(
            token_ids, type_ids, type_specificity, type_depth, type_hash
        )

        # Causal mask
        causal_mask = self._create_causal_mask(seq_len, device)
        attn_mask = (causal_mask == 0).float()

        # 八咫鏡
        x = self.yata_kagami(x, definition_mask=definition_mask, causal_mask=attn_mask)

        # 共有層
        for block in self.shared_layers:
            x = block(x, type_spec_emb, token_roles, attn_mask)

        # MoE層
        all_router_logits: List[torch.Tensor] = []
        for moe_block in self.moe_layers:
            x, router_logits = moe_block(x, type_spec_emb, token_roles, attn_mask)
            all_router_logits.append(router_logits)

        # 第三章: 国生み
        x, struct_logits = self.kuniumi(x, generation_phase)

        # 第四章: 黄泉国
        yomi_outputs = self.yomi(x)

        # 第五章: 禊
        misogi_outputs = self.misogi(x)

        return {
            **misogi_outputs,
            "struct_logits": struct_logits,
            "router_logits": all_router_logits,
            "diagnostics": {
                "stability_logits": yomi_outputs["stability_logits"],
                "stability_probs": F.softmax(yomi_outputs["stability_logits"], dim=-1),
                "boundary_score": yomi_outputs["boundary_score"],
                "warnings": yomi_outputs["warnings"],
            },
        }

    def _infer_type_metadata(
        self, type_id: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.type_metadata_spec[type_id], self.type_metadata_depth[type_id]

    def count_parameters(self) -> Dict[str, int]:
        counts = {}
        for name, module in self.named_children():
            count = sum(p.numel() for p in module.parameters())
            counts[name] = count
        counts["total"] = sum(counts.values())
        return counts


def create_moe_model(
    config: Optional[KojikiConfig] = None,
    num_shared: int = 2,
    num_moe: int = 4,
    num_experts: int = 4,
    top_k: int = 2,
    tokenizer=None,
) -> KojikiMoE:
    """MoEモデルのファクトリ関数"""
    if config is None:
        config = KojikiConfig()
    return KojikiMoE(
        config,
        num_shared=num_shared,
        num_moe=num_moe,
        num_experts=num_experts,
        top_k=top_k,
        tokenizer=tokenizer,
    )
