"""
Julia-no-Mikoto: 神話層 (Mythology Layers)

古事記の神々をTransformer層にマッピング:
- 第一章: 天地開闢層 (Genesis Layer) - Embeddings
- 第二章: 神世七代層 (Seven Generations) - Attention + FFN
- 第三章: 国生み層 (Kuniumi Layer) - Struct Generation
- 第四章: 黄泉国層 (Yomi Layer) - Type Instability Detection
- 第五章: 禊層 (Misogi Layer) - Output Heads
"""

import math
from typing import Dict, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from .config import KojikiConfig, TYPE_SPECIFICITY, TYPE_DEPTH


# =============================================================================
# 第一章: 天地開闢層 (Genesis Layer) - Embeddings
# =============================================================================


class AmenominakanushiPositionalEncoding(nn.Module):
    """
    天之御中主神 - Positional Encoding

    宇宙の中心に座す神。位置情報を付与する。
    標準的なSinusoidal Positional Encodingを使用。
    """

    def __init__(self, d_model: int, max_seq_len: int = 2048, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        # Sinusoidal positional encoding
        pe = torch.zeros(max_seq_len, d_model)
        position = torch.arange(0, max_seq_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # [1, max_seq_len, d_model]

        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [batch, seq_len, d_model]
        Returns:
            [batch, seq_len, d_model] with positional encoding added
        """
        seq_len = x.size(1)
        x = x + self.pe[:, :seq_len, :]
        return self.dropout(x)


class TakamimusubiTokenEmbedding(nn.Module):
    """
    高御産巣日神 - Token Embedding

    万物を生み出す神。トークンを埋め込み空間に変換。
    """

    def __init__(self, vocab_size: int, d_model: int, padding_idx: int = 0):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, d_model, padding_idx=padding_idx)
        self.d_model = d_model

    def forward(self, token_ids: torch.Tensor) -> torch.Tensor:
        """
        Args:
            token_ids: [batch, seq_len]
        Returns:
            [batch, seq_len, d_model]
        """
        # Scale by sqrt(d_model) following Transformer convention
        return self.embedding(token_ids) * math.sqrt(self.d_model)


class KamimusubiTypeHierarchyEmbedding(nn.Module):
    """
    神産巣日神 - 型階層埋め込み (v2: Hash Embedding対応)

    万物に霊力を与える神。型の階層構造を埋め込む。

    標準型: 直接埋め込み
    ユーザー定義型: 型名のハッシュ + カテゴリ埋め込み
    """

    def __init__(
        self,
        type_vocab_size: int = 128,
        d_model: int = 512,
        hierarchy_depth: int = 8,
        hash_bucket_size: int = 1024,
    ):
        super().__init__()

        # 標準型埋め込み
        self.type_embedding = nn.Embedding(type_vocab_size, d_model)

        # ユーザー定義型のハッシュ埋め込み
        self.hash_embedding = nn.Embedding(hash_bucket_size, d_model // 2)

        # 具体度埋め込み (0=Any, 1=Abstract, 2=Concrete)
        self.specificity_embedding = nn.Embedding(3, d_model)

        # 型階層深度埋め込み
        self.depth_embedding = nn.Embedding(hierarchy_depth, d_model)

        # ユーザー定義型用の統合層
        self.user_type_fusion = nn.Linear(d_model + d_model // 2, d_model)

        # 最終統合
        self.projection = nn.Linear(d_model * 3, d_model)

        # ユーザー定義型の範囲
        self.user_type_start = 64
        self.user_type_end = 96

    def forward(
        self,
        type_ids: torch.Tensor,            # [batch, seq_len]
        type_specificity: torch.Tensor,    # [batch, seq_len]
        type_depth: torch.Tensor,          # [batch, seq_len]
        type_hash: Optional[torch.Tensor] = None,  # [batch, seq_len]
    ) -> torch.Tensor:
        """
        型情報を統合した埋め込みを生成

        Args:
            type_ids: 型カテゴリID
            type_specificity: 型の具体度 (0=Any, 1=Abstract, 2=Concrete)
            type_depth: 型階層の深さ
            type_hash: ユーザー定義型のハッシュ値（オプション）

        Returns:
            [batch, seq_len, d_model]
        """
        batch_size, seq_len = type_ids.shape

        # 基本型埋め込み
        type_emb = self.type_embedding(type_ids)

        # ユーザー定義型の場合、ハッシュ埋め込みを追加
        if type_hash is not None:
            is_user_type = (type_ids >= self.user_type_start) & (
                type_ids < self.user_type_end
            )

            if is_user_type.any():
                hash_emb = self.hash_embedding(type_hash)

                # ユーザー定義型の埋め込みを強化
                # マスクを使って選択的に処理
                user_mask = is_user_type.unsqueeze(-1).expand_as(type_emb)
                user_type_emb = type_emb[is_user_type]
                user_hash_emb = hash_emb[is_user_type]

                user_combined = torch.cat([user_type_emb, user_hash_emb], dim=-1)
                fused = self.user_type_fusion(user_combined)

                # 更新
                type_emb = type_emb.clone()
                type_emb[is_user_type] = fused

        # 具体度・深度埋め込み
        spec_emb = self.specificity_embedding(type_specificity)
        depth_emb = self.depth_embedding(type_depth.clamp(max=7))  # 深さを制限

        # 統合
        combined = torch.cat([type_emb, spec_emb, depth_emb], dim=-1)
        return self.projection(combined)


class GenesisLayer(nn.Module):
    """
    第一章: 天地開闢層 - 統合埋め込み層

    三柱の造化三神が協調して入力を埋め込み空間に変換:
    - 天之御中主神: 位置情報
    - 高御産巣日神: トークン情報
    - 神産巣日神: 型階層情報
    """

    def __init__(self, config: KojikiConfig):
        super().__init__()
        self.config = config

        # 三柱の造化三神
        self.amenominakanushi = AmenominakanushiPositionalEncoding(
            config.d_model, config.max_seq_len, config.dropout
        )
        self.takamimusubi = TakamimusubiTokenEmbedding(
            config.vocab_size, config.d_model, config.pad_token_id
        )
        self.kamimusubi = KamimusubiTypeHierarchyEmbedding(
            config.type_vocab_size,
            config.d_model,
            config.type_hierarchy_depth,
            config.hash_bucket_size,
        )

        # トークン埋め込みと型埋め込みの統合
        self.fusion = nn.Linear(config.d_model * 2, config.d_model)
        self.layer_norm = nn.LayerNorm(config.d_model)

    def forward(
        self,
        token_ids: torch.Tensor,
        type_ids: torch.Tensor,
        type_specificity: torch.Tensor,
        type_depth: torch.Tensor,
        type_hash: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        入力を埋め込み空間に変換

        Returns:
            (combined_embedding, type_specificity_embedding)
        """
        # 高御産巣日神: トークン埋め込み
        token_emb = self.takamimusubi(token_ids)

        # 神産巣日神: 型階層埋め込み
        type_emb = self.kamimusubi(type_ids, type_specificity, type_depth, type_hash)

        # 融合
        combined = torch.cat([token_emb, type_emb], dim=-1)
        fused = self.fusion(combined)

        # 天之御中主神: 位置情報を付与
        output = self.amenominakanushi(fused)
        output = self.layer_norm(output)

        # 型具体度埋め込みも返す（Multiple Dispatch Attentionで使用）
        type_spec_emb = self.kamimusubi.specificity_embedding(type_specificity)

        return output, type_spec_emb


# =============================================================================
# 第二章: 神世七代層 (Seven Generations) - Attention + FFN
# =============================================================================


class KuninotokotachiSelfAttention(nn.Module):
    """
    国之常立神 - Self-Attention

    国土の礎を築く神。標準的なMulti-Head Self-Attention。
    """

    def __init__(self, d_model: int, n_heads: int, dropout: float = 0.1):
        super().__init__()
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k = d_model // n_heads

        self.w_q = nn.Linear(d_model, d_model)
        self.w_k = nn.Linear(d_model, d_model)
        self.w_v = nn.Linear(d_model, d_model)
        self.output = nn.Linear(d_model, d_model)

        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Args:
            x: [batch, seq_len, d_model]
            mask: [batch, 1, seq_len, seq_len] causal mask

        Returns:
            [batch, seq_len, d_model]
        """
        batch_size, seq_len, _ = x.shape

        # Q, K, V projections
        q = self.w_q(x).view(batch_size, seq_len, self.n_heads, self.d_k).transpose(1, 2)
        k = self.w_k(x).view(batch_size, seq_len, self.n_heads, self.d_k).transpose(1, 2)
        v = self.w_v(x).view(batch_size, seq_len, self.n_heads, self.d_k).transpose(1, 2)

        # Attention scores
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.d_k)

        # Apply causal mask
        if mask is not None:
            scores = scores.masked_fill(mask == 0, float("-inf"))

        attn = F.softmax(scores, dim=-1)
        attn = self.dropout(attn)

        # Output
        out = torch.matmul(attn, v)
        out = out.transpose(1, 2).contiguous().view(batch_size, seq_len, self.d_model)

        return self.output(out)


class ToyokumoFeedForward(nn.Module):
    """
    豊雲野神 - Feed-Forward Network

    豊かな雲の野の神。情報を変換・拡張する。
    """

    def __init__(self, d_model: int, d_ff: int, dropout: float = 0.1):
        super().__init__()
        self.linear1 = nn.Linear(d_model, d_ff)
        self.linear2 = nn.Linear(d_ff, d_model)
        self.dropout = nn.Dropout(dropout)
        self.activation = nn.GELU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear2(self.dropout(self.activation(self.linear1(x))))


class MultipleDispatchAttention(nn.Module):
    """
    対の神々 - 多重ディスパッチ機構 (v2: Role-based Masking)

    伊邪那岐・伊邪那美のように、関数と型のマッチングを模倣。

    【v2変更点】
    - トークンの役割（関数/変数/型注釈）に基づくマスキング
    - Query: 関数呼び出し位置
    - Key: 変数定義とその型注釈
    - より正確なディスパッチシミュレーション
    """

    def __init__(
        self,
        d_model: int,
        n_heads: int,
        num_token_roles: int = 8,
        dropout: float = 0.1,
    ):
        super().__init__()

        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k = d_model // n_heads

        self.w_q = nn.Linear(d_model, d_model)  # 男神（関数）
        self.w_k = nn.Linear(d_model, d_model)  # 女神（型）
        self.w_v = nn.Linear(d_model, d_model)  # 結実（メソッド）

        # 役割埋め込み
        self.role_embedding = nn.Embedding(num_token_roles, d_model)

        # 役割間の相互作用行列（どの役割がどの役割にAttendすべきか）
        # 学習可能なパラメータ
        self.role_interaction = nn.Parameter(torch.ones(num_token_roles, num_token_roles))

        # 型特異度スケーリング
        self.specificity_scale = nn.Linear(d_model, n_heads)

        self.output = nn.Linear(d_model, d_model)
        self.dropout = nn.Dropout(dropout)

        # 役割相互作用の初期化
        self._init_role_interaction()

    def _init_role_interaction(self):
        """役割間相互作用の初期化"""
        # FUNCTION_NAME(1) → TYPE_ANNOTATION(3) は高いスコア
        # VARIABLE(2) → VARIABLE(2) も高いスコア
        with torch.no_grad():
            # 基本は1.0
            self.role_interaction.fill_(1.0)
            # 関数 → 型注釈: 1.5
            self.role_interaction[1, 3] = 1.5
            # 変数 → 変数: 1.3
            self.role_interaction[2, 2] = 1.3
            # 関数 → 関数: 1.2
            self.role_interaction[1, 1] = 1.2
            # 型注釈 → 型注釈: 1.2
            self.role_interaction[3, 3] = 1.2

    def forward(
        self,
        x: torch.Tensor,                     # [batch, seq_len, d_model]
        type_specificity_emb: torch.Tensor,  # [batch, seq_len, d_model]
        token_roles: torch.Tensor,           # [batch, seq_len]
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        batch_size, seq_len, _ = x.shape

        # 役割埋め込みを追加
        role_emb = self.role_embedding(token_roles)
        x_with_role = x + role_emb * 0.1  # 軽く加算

        # Q, K, V projections
        q = self.w_q(x_with_role).view(batch_size, seq_len, self.n_heads, self.d_k).transpose(1, 2)
        k = self.w_k(x_with_role).view(batch_size, seq_len, self.n_heads, self.d_k).transpose(1, 2)
        v = self.w_v(x_with_role).view(batch_size, seq_len, self.n_heads, self.d_k).transpose(1, 2)

        # 基本Attentionスコア
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.d_k)

        # === 【v2】役割ベースマスキング ===
        role_mask = self._compute_role_mask(token_roles)  # [batch, seq, seq]
        scores = scores + role_mask.unsqueeze(1) * 0.5  # ヘッド次元を追加

        # === 型特異度による調整 ===
        spec_weight = self.specificity_scale(type_specificity_emb)
        spec_weight = spec_weight.transpose(1, 2).unsqueeze(-1)
        scores = scores * (1 + spec_weight.expand_as(scores) * 0.1)

        # Causal mask
        if mask is not None:
            scores = scores.masked_fill(mask == 0, float("-inf"))

        attn = F.softmax(scores, dim=-1)
        attn = self.dropout(attn)

        out = torch.matmul(attn, v)
        out = out.transpose(1, 2).contiguous().view(batch_size, seq_len, self.d_model)

        return self.output(out)

    def _compute_role_mask(self, token_roles: torch.Tensor) -> torch.Tensor:
        """
        役割間の相互作用マスクを計算

        例: FUNCTION_NAME(Q) → TYPE_ANNOTATION(K) は高いスコア
            VARIABLE(Q) → VARIABLE(K) も高いスコア
        """
        batch_size, seq_len = token_roles.shape

        # 役割相互作用行列から、各位置ペアのスコアを取得
        q_roles = token_roles.unsqueeze(-1).expand(-1, -1, seq_len)  # [batch, seq, seq]
        k_roles = token_roles.unsqueeze(1).expand(-1, seq_len, -1)   # [batch, seq, seq]

        # interaction[q_role, k_role] を取得
        role_scores = self.role_interaction[q_roles, k_roles]

        return role_scores


class SevenGenerationsBlock(nn.Module):
    """
    神世七代 - 単一Transformer Block

    国之常立神（Self-Attention）+ 豊雲野神（FFN）+ 対の神々（Multiple Dispatch）
    """

    def __init__(self, config: KojikiConfig):
        super().__init__()

        # 国之常立神: Self-Attention
        self.kuninotokotachi = KuninotokotachiSelfAttention(
            config.d_model, config.n_heads, config.dropout
        )

        # 豊雲野神: Feed-Forward
        self.toyokumo = ToyokumoFeedForward(
            config.d_model, config.d_ff, config.dropout
        )

        # 対の神々: Multiple Dispatch Attention
        self.izanagi_izanami = MultipleDispatchAttention(
            config.d_model, config.n_heads, config.num_token_roles, config.dropout
        )

        # Layer Normalization
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
    ) -> torch.Tensor:
        # Self-Attention (Pre-LN)
        residual = x
        x = self.norm1(x)
        x = residual + self.dropout(self.kuninotokotachi(x, mask))

        # Multiple Dispatch Attention
        residual = x
        x = self.norm2(x)
        x = residual + self.dropout(
            self.izanagi_izanami(x, type_specificity_emb, token_roles, mask)
        )

        # Feed-Forward
        residual = x
        x = self.norm3(x)
        x = residual + self.dropout(self.toyokumo(x))

        return x


class SevenGenerationsStack(nn.Module):
    """
    第二章: 神世七代層 - N層のTransformer Stack
    """

    def __init__(self, config: KojikiConfig):
        super().__init__()
        self.blocks = nn.ModuleList([
            SevenGenerationsBlock(config) for _ in range(config.n_generations)
        ])

    def forward(
        self,
        x: torch.Tensor,
        type_specificity_emb: torch.Tensor,
        token_roles: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        for block in self.blocks:
            x = block(x, type_specificity_emb, token_roles, mask)
        return x


# =============================================================================
# 第三章: 国生み層 (Kuniumi Layer) - Struct Generation
# =============================================================================


class KuniumiLayer(nn.Module):
    """
    国生み層 - struct生成 (v2: マクロはData Augmentationで対応)

    淤能碁呂島から大八洲を生み出すように、コード構造を生成。
    """

    def __init__(self, config: KojikiConfig):
        super().__init__()

        # 淤能碁呂島: struct生成
        self.onogoro_struct = nn.Sequential(
            nn.Linear(config.d_model, config.d_model),
            nn.GELU(),
            nn.Linear(config.d_model, config.vocab_size),
        )

        # 【v2】マクロ展開はシンプルな変換層に簡略化
        # 実際のマクロ学習はData Augmentationで行う
        self.amenonuboko = nn.Sequential(
            nn.Linear(config.d_model, config.d_model),
            nn.GELU(),
            nn.Linear(config.d_model, config.d_model),
        )

        # 生成フェーズ: struct → function → expression
        # 【v2】macro フェーズは削除（Data Augmentationで対応）
        self.phase_embedding = nn.Embedding(3, config.d_model)

    def forward(
        self,
        x: torch.Tensor,
        generation_phase: int = 0,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            x: [batch, seq_len, d_model]
            generation_phase: 0=struct, 1=function, 2=expression

        Returns:
            (transformed, struct_logits)
        """
        device = x.device
        phase_emb = self.phase_embedding(
            torch.tensor([generation_phase], device=device)
        ).unsqueeze(1)
        x = x + phase_emb

        transformed = self.amenonuboko(x)
        struct_logits = self.onogoro_struct(transformed)

        return transformed, struct_logits


# =============================================================================
# 第四章: 黄泉国層 (Yomi Layer) - Type Instability Detection
# =============================================================================


class YomiLayer(nn.Module):
    """
    黄泉国層 - 型不安定性検出

    黄泉国（死の国）は型不安定なコードの「地獄」を表す。
    @code_warntype の警告に相当する問題を検出。

    - 黄泉津大神: Type Instability Detection
    - 予母都志許売: Performance Warning Collection
    - 黄泉比良坂: Concrete/Abstract Type Boundary
    """

    def __init__(self, config: KojikiConfig):
        super().__init__()

        # 黄泉津大神: 型安定性分類 (stable / warning / critical)
        self.yomotsushikome = nn.Sequential(
            nn.Linear(config.d_model, config.d_model // 2),
            nn.GELU(),
            nn.Linear(config.d_model // 2, 3),  # 3クラス分類
        )

        # 予母都志許売: パフォーマンス警告収集
        self.performance_collector = nn.Sequential(
            nn.Linear(config.d_model, config.d_model // 2),
            nn.GELU(),
            nn.Linear(config.d_model // 2, config.d_model),
        )

        # 黄泉比良坂: 具体型/抽象型の境界検出
        self.yomohirasaka = nn.Sequential(
            nn.Linear(config.d_model, config.d_model // 2),
            nn.GELU(),
            nn.Linear(config.d_model // 2, 1),
            nn.Sigmoid(),
        )

        self.norm = nn.LayerNorm(config.d_model)

    def forward(
        self,
        x: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:
        """
        Args:
            x: [batch, seq_len, d_model]

        Returns:
            Dict containing:
                - stability_logits: [batch, seq_len, 3] 型安定性分類
                - boundary_score: [batch, seq_len, 1] 抽象/具体境界スコア
                - warnings: [batch, seq_len, d_model] 警告情報
        """
        x = self.norm(x)

        stability_logits = self.yomotsushikome(x)
        boundary_score = self.yomohirasaka(x)
        warnings = self.performance_collector(x)

        return {
            "stability_logits": stability_logits,
            "boundary_score": boundary_score,
            "warnings": warnings,
        }


# =============================================================================
# 第五章: 禊層 (Misogi Layer) - Output Heads
# =============================================================================


class AmaterasuTokenHead(nn.Module):
    """
    天照大御神 - 次トークン予測 + SIMD可能性

    太陽神として、コード生成を照らし導く。
    """

    def __init__(self, config: KojikiConfig):
        super().__init__()

        # 次トークン予測
        self.token_predictor = nn.Linear(config.d_model, config.vocab_size)

        # SIMD可能性スコア
        self.simd_scorer = nn.Sequential(
            nn.Linear(config.d_model, config.d_model // 4),
            nn.GELU(),
            nn.Linear(config.d_model // 4, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns:
            (token_logits, simd_score)
        """
        token_logits = self.token_predictor(x)
        simd_score = self.simd_scorer(x)
        return token_logits, simd_score


class TsukuyomiTypeHead(nn.Module):
    """
    月読命 - 次トークンの型予測 (v2: 推論時も使用)

    月神として、夜（不確実性）を司り、型を予測する。
    """

    def __init__(self, config: KojikiConfig):
        super().__init__()

        # 型予測
        self.type_predictor = nn.Linear(config.d_model, config.type_vocab_size)

        # 自動微分可能性スコア
        self.diff_scorer = nn.Sequential(
            nn.Linear(config.d_model, config.d_model // 4),
            nn.GELU(),
            nn.Linear(config.d_model // 4, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns:
            (type_logits, differentiable_score)
        """
        type_logits = self.type_predictor(x)
        diff_score = self.diff_scorer(x)
        return type_logits, diff_score


class SusanooErrorHead(nn.Module):
    """
    須佐之男命 - エラー予測 + 動的ディスパッチ

    嵐の神として、コードの「荒ぶる」部分（エラー・動的要素）を予測。
    """

    def __init__(self, config: KojikiConfig):
        super().__init__()

        # エラー予測
        self.error_predictor = nn.Sequential(
            nn.Linear(config.d_model, config.d_model // 2),
            nn.GELU(),
            nn.Linear(config.d_model // 2, 1),
            nn.Sigmoid(),
        )

        # 動的ディスパッチスコア（静的 vs 動的）
        self.dynamic_dispatch_scorer = nn.Sequential(
            nn.Linear(config.d_model, config.d_model // 4),
            nn.GELU(),
            nn.Linear(config.d_model // 4, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns:
            (error_score, dynamic_dispatch_score)
        """
        error_score = self.error_predictor(x)
        dynamic_score = self.dynamic_dispatch_scorer(x)
        return error_score, dynamic_score


class MisogiLayer(nn.Module):
    """
    第五章: 禊層 - 出力ヘッド統合

    禊（身を清める儀式）のように、最終出力を整える。
    三貴子（天照・月読・須佐之男）が協調して出力を生成。
    """

    def __init__(self, config: KojikiConfig):
        super().__init__()

        # 祓戸の神々: Layer Normalization
        self.haraedo = nn.LayerNorm(config.d_model)

        # 三貴子
        self.amaterasu = AmaterasuTokenHead(config)
        self.tsukuyomi = TsukuyomiTypeHead(config)
        self.susanoo = SusanooErrorHead(config)

    def forward(
        self,
        x: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:
        """
        Args:
            x: [batch, seq_len, d_model]

        Returns:
            Dict containing all output predictions
        """
        x = self.haraedo(x)

        # 天照: トークン + SIMD
        token_logits, simd_score = self.amaterasu(x)

        # 月読: 型 + 微分可能性
        type_logits, diff_score = self.tsukuyomi(x)

        # 須佐之男: エラー + 動的ディスパッチ
        error_score, dynamic_score = self.susanoo(x)

        return {
            "logits": token_logits,
            "type_logits": type_logits,
            "simd_score": simd_score,
            "differentiable": diff_score,
            "error_score": error_score,
            "dynamic_dispatch": dynamic_score,
        }
