"""
八咫鏡Attention (Yata-no-Kagami Attention)

定義位置への減衰なしAttention機構。

通常のSelf-Attentionでは距離が遠いトークンへのAttention重みが減衰し、
struct/functionの定義情報を忘れてしまう。
八咫鏡Attentionは「定義位置マスク」を使って、定義位置への
Attentionを常に維持する追加ヘッドを持つ。

構成:
  1. 通常のSelf-Attention（既存のKuninotokotachiと同様）
  2. Definition-Attention（定義位置専用、減衰なし）
  3. 両者の融合ゲート

追加パラメータ: 約2-3M（RTX 4060 8GBで動作可能）
"""

import math
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


class YataKagamiAttention(nn.Module):
    """
    八咫鏡Attention

    通常のSelf-Attentionに加えて、定義位置への減衰なしAttentionヘッドを持つ。
    融合ゲートで両者の出力を適応的にブレンドする。

    Args:
        d_model: モデル次元
        n_heads: 通常Attentionのヘッド数
        n_def_heads: Definition-Attentionのヘッド数（通常の半分）
        dropout: ドロップアウト率
    """

    def __init__(
        self,
        d_model: int,
        n_heads: int,
        n_def_heads: Optional[int] = None,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.d_model = d_model
        self.n_heads = n_heads
        self.n_def_heads = n_def_heads or max(1, n_heads // 2)
        self.d_k = d_model // n_heads
        self.d_k_def = d_model // self.n_def_heads

        # === 通常のSelf-Attention ===
        self.self_q = nn.Linear(d_model, d_model)
        self.self_k = nn.Linear(d_model, d_model)
        self.self_v = nn.Linear(d_model, d_model)
        self.self_out = nn.Linear(d_model, d_model)

        # === Definition-Attention（定義位置専用） ===
        self.def_q = nn.Linear(d_model, d_model)
        self.def_k = nn.Linear(d_model, d_model)
        self.def_v = nn.Linear(d_model, d_model)
        self.def_out = nn.Linear(d_model, d_model)

        # === 融合ゲート ===
        # self_outとdef_outを入力として、ブレンド比率を決定
        self.fusion_gate = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.Sigmoid(),
        )

        # === 出力投影 ===
        self.output_proj = nn.Linear(d_model, d_model)

        # === Layer Norm（Pre-LN） ===
        self.norm = nn.LayerNorm(d_model)

        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        x: torch.Tensor,
        definition_mask: Optional[torch.Tensor] = None,
        causal_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Args:
            x: [batch, seq, d_model]
            definition_mask: [batch, seq] 定義位置は1.0、それ以外は0.0
            causal_mask: [batch, 1, seq, seq] 1=許可, 0=禁止

        Returns:
            output: [batch, seq, d_model]
        """
        residual = x
        x = self.norm(x)

        # 1. 通常のSelf-Attention
        self_out = self._self_attention(x, causal_mask)

        # 2. Definition-Attention
        if definition_mask is not None and definition_mask.any():
            def_out = self._definition_attention(x, definition_mask, causal_mask)
        else:
            def_out = torch.zeros_like(self_out)

        # 3. 融合ゲート
        combined = torch.cat([self_out, def_out], dim=-1)
        gate = self.fusion_gate(combined)

        # gate: self_attentionの重み、(1-gate): def_attentionの重み
        output = gate * self_out + (1.0 - gate) * def_out

        # 出力投影 + 残差接続
        output = self.output_proj(output)
        output = self.dropout(output)

        return residual + output

    def _self_attention(
        self,
        x: torch.Tensor,
        causal_mask: Optional[torch.Tensor],
    ) -> torch.Tensor:
        """通常のScaled Dot-Product Self-Attention"""
        batch_size, seq_len, _ = x.shape

        q = self.self_q(x).view(batch_size, seq_len, self.n_heads, self.d_k).transpose(1, 2)
        k = self.self_k(x).view(batch_size, seq_len, self.n_heads, self.d_k).transpose(1, 2)
        v = self.self_v(x).view(batch_size, seq_len, self.n_heads, self.d_k).transpose(1, 2)

        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.d_k)

        if causal_mask is not None:
            scores = scores.masked_fill(causal_mask == 0, float("-inf"))

        attn = F.softmax(scores, dim=-1)
        attn = self.dropout(attn)

        out = torch.matmul(attn, v)
        out = out.transpose(1, 2).contiguous().view(batch_size, seq_len, self.d_model)

        return self.self_out(out)

    def _definition_attention(
        self,
        x: torch.Tensor,
        definition_mask: torch.Tensor,
        causal_mask: Optional[torch.Tensor],
    ) -> torch.Tensor:
        """
        定義位置への減衰なしAttention

        定義位置のKey/Valueのみを参照し、
        距離による減衰なしでAttentionを計算する。
        """
        batch_size, seq_len, _ = x.shape

        q = self.def_q(x).view(batch_size, seq_len, self.n_def_heads, self.d_k_def).transpose(1, 2)
        k = self.def_k(x).view(batch_size, seq_len, self.n_def_heads, self.d_k_def).transpose(1, 2)
        v = self.def_v(x).view(batch_size, seq_len, self.n_def_heads, self.d_k_def).transpose(1, 2)

        # Attentionスコア（距離による減衰なし）
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.d_k_def)

        # 定義位置へのマスクを作成
        # definition_mask: [batch, seq] → [batch, 1, 1, seq]
        def_mask = definition_mask.unsqueeze(1).unsqueeze(2)
        # 定義位置以外は-infにして、定義位置のみAttention可能に
        def_attn_mask = def_mask.expand_as(scores)
        scores = scores.masked_fill(def_attn_mask == 0, float("-inf"))

        # Causal maskも適用（未来の定義は参照不可）
        if causal_mask is not None:
            scores = scores.masked_fill(causal_mask == 0, float("-inf"))

        # 全て-infの行（定義トークンがまだ出現していない場合）を処理
        all_masked = scores.eq(float("-inf")).all(dim=-1, keepdim=True)
        # softmaxがnanを出さないようにフォールバック
        scores = scores.masked_fill(all_masked.expand_as(scores), 0.0)

        attn = F.softmax(scores, dim=-1)
        # 全マスク行はゼロアウト
        attn = attn.masked_fill(all_masked.expand_as(attn), 0.0)
        attn = self.dropout(attn)

        out = torch.matmul(attn, v)
        out = out.transpose(1, 2).contiguous().view(batch_size, seq_len, self.d_model)

        return self.def_out(out)
