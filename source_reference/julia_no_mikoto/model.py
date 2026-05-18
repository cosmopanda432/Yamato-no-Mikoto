"""
Julia-no-Mikoto: 古事記LLM (Kojiki Language Model)

Julia言語特化型LLMのメインモデル。
Autoregressive Type Prediction（二人三脚生成）を実装。
"""

from typing import Dict, Optional, Tuple, List

import torch
import torch.nn as nn
import torch.nn.functional as F

from .config import KojikiConfig, TYPE_SPECIFICITY, TYPE_DEPTH
from .layers import (
    GenesisLayer,
    SevenGenerationsStack,
    KuniumiLayer,
    YomiLayer,
    MisogiLayer,
)
from .yata_kagami_attention import YataKagamiAttention
from .definition_detector import DefinitionDetector


class KojikiLM(nn.Module):
    """
    古事記言語モデル (Kojiki Language Model)

    Julia言語の型システム・多重ディスパッチを古事記の神話構造にマッピング。

    アーキテクチャ:
        第一章: 天地開闢層 (Genesis) - Embeddings
        第二章: 神世七代層 (Seven Generations) - Transformer Blocks
        第三章: 国生み層 (Kuniumi) - Struct Generation
        第四章: 黄泉国層 (Yomi) - Type Instability Detection
        第五章: 禊層 (Misogi) - Output Heads

    v2特徴:
        - Autoregressive Type Prediction: トークンと型を二人三脚で生成
        - Hash Embedding: ユーザー定義型対応
        - Role-based Masking: Multiple Dispatch Attentionの改善

    v3特徴:
        - 八咫鏡Attention: 定義位置への減衰なしAttention
        - DefinitionDetector: struct/function定義の自動検出
    """

    def __init__(self, config: KojikiConfig, tokenizer=None):
        super().__init__()
        self.config = config

        # 第一章: 天地開闢層
        self.genesis = GenesisLayer(config)

        # 八咫鏡: 定義位置への減衰なしAttention（Genesis→SevenGenerationsの間）
        self.yata_kagami = YataKagamiAttention(
            d_model=config.d_model,
            n_heads=config.n_heads,
            dropout=config.dropout,
        )

        # 定義位置検出器（推論時に使用、パラメータなし）
        self.definition_detector = DefinitionDetector(
            tokenizer=tokenizer,
            definition_span=20,
        )

        # 第二章: 神世七代層
        self.seven_generations = SevenGenerationsStack(config)

        # 第三章: 国生み層
        self.kuniumi = KuniumiLayer(config)

        # 第四章: 黄泉国層
        self.yomi = YomiLayer(config)

        # 第五章: 禊層
        self.misogi = MisogiLayer(config)

        # 型メタデータテーブル（推論時に使用）
        self._init_type_metadata()

        # パラメータ初期化
        self.apply(self._init_weights)

    def _init_weights(self, module):
        """パラメータ初期化"""
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
        """型メタデータテーブルの初期化"""
        # 型ID → 具体度
        spec_tensor = torch.zeros(self.config.type_vocab_size, dtype=torch.long)
        for type_id, spec in TYPE_SPECIFICITY.items():
            if type_id < self.config.type_vocab_size:
                spec_tensor[type_id] = spec
        self.register_buffer("type_metadata_spec", spec_tensor)

        # 型ID → 階層深度
        depth_tensor = torch.zeros(self.config.type_vocab_size, dtype=torch.long)
        for type_id, depth in TYPE_DEPTH.items():
            if type_id < self.config.type_vocab_size:
                depth_tensor[type_id] = min(depth, self.config.type_hierarchy_depth - 1)
        self.register_buffer("type_metadata_depth", depth_tensor)

    def _create_causal_mask(
        self,
        seq_len: int,
        device: torch.device,
    ) -> torch.Tensor:
        """Causal attention mask作成"""
        mask = torch.triu(torch.ones(seq_len, seq_len, device=device), diagonal=1)
        mask = mask.masked_fill(mask == 1, float("-inf"))
        mask = mask.masked_fill(mask == 0, float(0.0))
        return mask.unsqueeze(0).unsqueeze(0)  # [1, 1, seq_len, seq_len]

    def forward(
        self,
        token_ids: torch.Tensor,           # [batch, seq_len]
        type_ids: torch.Tensor,            # [batch, seq_len]
        type_specificity: torch.Tensor,    # [batch, seq_len]
        type_depth: torch.Tensor,          # [batch, seq_len]
        token_roles: Optional[torch.Tensor] = None,  # [batch, seq_len]
        type_hash: Optional[torch.Tensor] = None,    # [batch, seq_len]
        definition_mask: Optional[torch.Tensor] = None,  # [batch, seq_len]
        generation_phase: int = 0,
    ) -> Dict[str, torch.Tensor]:
        """
        順伝播

        Args:
            token_ids: トークンID列
            type_ids: 型ID列
            type_specificity: 型の具体度
            type_depth: 型階層の深さ
            token_roles: トークンの役割（オプション）
            type_hash: ユーザー定義型のハッシュ（オプション）
            definition_mask: 定義位置マスク（オプション、Noneの場合は自動検出）
            generation_phase: 生成フェーズ (0=struct, 1=function, 2=expression)

        Returns:
            Dict containing:
                - logits: 次トークン予測 [batch, seq_len, vocab_size]
                - type_logits: 次型予測 [batch, seq_len, type_vocab_size]
                - simd_score: SIMD可能性スコア
                - differentiable: 自動微分可能性スコア
                - error_score: エラー確率
                - dynamic_dispatch: 動的ディスパッチスコア
                - diagnostics: 診断情報
        """
        batch_size, seq_len = token_ids.shape
        device = token_ids.device

        # デフォルトのトークン役割（全てUNKNOWN）
        if token_roles is None:
            token_roles = torch.zeros(batch_size, seq_len, dtype=torch.long, device=device)

        # 定義位置マスクの自動検出
        if definition_mask is None:
            if self.definition_detector._keyword_token_ids is not None:
                definition_mask = self.definition_detector.detect(token_ids)
            elif token_roles is not None and token_roles.any():
                definition_mask = self.definition_detector.detect_from_roles(token_roles)

        # 第一章: 天地開闢 - 埋め込み
        x, type_spec_emb = self.genesis(
            token_ids, type_ids, type_specificity, type_depth, type_hash
        )

        # Causal mask作成
        causal_mask = self._create_causal_mask(seq_len, device)
        # Boolean maskに変換（0は許可、-infは禁止）
        attn_mask = (causal_mask == 0).float()

        # 八咫鏡: 定義位置への減衰なしAttention
        x = self.yata_kagami(x, definition_mask=definition_mask, causal_mask=attn_mask)

        # 第二章: 神世七代 - Transformer
        x = self.seven_generations(x, type_spec_emb, token_roles, attn_mask)

        # 第三章: 国生み - 構造生成
        x, struct_logits = self.kuniumi(x, generation_phase)

        # 第四章: 黄泉国 - 型安定性検出
        yomi_outputs = self.yomi(x)

        # 第五章: 禊 - 最終出力
        misogi_outputs = self.misogi(x)

        # 出力の統合
        return {
            **misogi_outputs,
            "struct_logits": struct_logits,
            "diagnostics": {
                "stability_logits": yomi_outputs["stability_logits"],
                "stability_probs": F.softmax(yomi_outputs["stability_logits"], dim=-1),
                "boundary_score": yomi_outputs["boundary_score"],
                "warnings": yomi_outputs["warnings"],
            },
        }

    @torch.no_grad()
    def generate(
        self,
        prompt_tokens: torch.Tensor,       # [batch, seq_len]
        prompt_types: torch.Tensor,        # [batch, seq_len]
        prompt_specificity: torch.Tensor,  # [batch, seq_len]
        prompt_depth: torch.Tensor,        # [batch, seq_len]
        prompt_roles: Optional[torch.Tensor] = None,
        prompt_hash: Optional[torch.Tensor] = None,
        max_length: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        error_threshold: float = 0.8,
    ) -> Dict[str, torch.Tensor]:
        """
        【v2】Autoregressive Type Prediction

        トークンと型を二人三脚で自己回帰生成。
        月読（型予測）が推論時にも重要な役割を果たす。

        Args:
            prompt_tokens: プロンプトのトークンID
            prompt_types: プロンプトの型ID
            prompt_specificity: プロンプトの型具体度
            prompt_depth: プロンプトの型階層深度
            prompt_roles: プロンプトのトークン役割
            prompt_hash: プロンプトのユーザー定義型ハッシュ
            max_length: 生成する最大トークン数
            temperature: サンプリング温度
            top_p: Nucleus samplingの閾値
            error_threshold: エラースコア閾値（黄泉行き判定）

        Returns:
            Dict containing:
                - generated_tokens: 生成されたトークン列
                - generated_types: 生成された型列
                - log: 生成ログ
        """
        self.eval()
        device = prompt_tokens.device
        batch_size = prompt_tokens.size(0)

        # 生成中の系列
        generated_tokens = prompt_tokens.clone()
        generated_types = prompt_types.clone()
        generated_spec = prompt_specificity.clone()
        generated_depth = prompt_depth.clone()

        # 役割とハッシュの初期化
        if prompt_roles is not None:
            generated_roles = prompt_roles.clone()
        else:
            generated_roles = torch.zeros_like(prompt_tokens)

        if prompt_hash is not None:
            generated_hash = prompt_hash.clone()
        else:
            generated_hash = torch.zeros_like(prompt_tokens)

        # 診断情報の記録
        generation_log: Dict[str, List] = {
            "tokens": [],
            "types": [],
            "stability_scores": [],
            "error_scores": [],
        }

        for step in range(max_length):
            # シーケンス長制限チェック
            if generated_tokens.size(1) >= self.config.max_seq_len:
                generation_log["early_stop"] = "max_seq_len_reached"
                break

            # Forward pass
            outputs = self.forward(
                generated_tokens,
                generated_types,
                generated_spec,
                generated_depth,
                generated_roles,
                generated_hash,
            )

            # === 天照: 次トークン予測 ===
            token_logits = outputs["logits"][:, -1, :] / temperature
            next_token = self._sample_top_p(token_logits, top_p)

            # === 月読: 次トークンの型予測 ===
            type_logits = outputs["type_logits"][:, -1, :]
            next_type = torch.argmax(type_logits, dim=-1)

            # === 須佐之男: エラーチェック ===
            error_score = outputs["error_score"][:, -1, :].squeeze(-1)

            # 黄泉行き判定（エラー確率が高すぎる場合）
            if error_score.mean().item() > error_threshold:
                generation_log["early_stop"] = "yomi_threshold_exceeded"
                break

            # === 型の具体度と深さを推定 ===
            next_spec, next_depth = self._infer_type_metadata(next_type)

            # === 次のトークン役割を推定（簡易版: UNKNOWNとする） ===
            next_role = torch.zeros(batch_size, dtype=torch.long, device=device)

            # === ハッシュは0とする（推論時は新しいユーザー定義型は出ない想定） ===
            next_hash = torch.zeros(batch_size, dtype=torch.long, device=device)

            # === 系列に追加 ===
            generated_tokens = torch.cat([
                generated_tokens,
                next_token.unsqueeze(1),
            ], dim=1)
            generated_types = torch.cat([
                generated_types,
                next_type.unsqueeze(1),
            ], dim=1)
            generated_spec = torch.cat([
                generated_spec,
                next_spec.unsqueeze(1),
            ], dim=1)
            generated_depth = torch.cat([
                generated_depth,
                next_depth.unsqueeze(1),
            ], dim=1)
            generated_roles = torch.cat([
                generated_roles,
                next_role.unsqueeze(1),
            ], dim=1)
            generated_hash = torch.cat([
                generated_hash,
                next_hash.unsqueeze(1),
            ], dim=1)

            # ログ記録
            generation_log["tokens"].append(next_token.cpu().tolist())
            generation_log["types"].append(next_type.cpu().tolist())
            generation_log["stability_scores"].append(
                outputs["diagnostics"]["stability_probs"][:, -1, :].cpu().tolist()
            )
            generation_log["error_scores"].append(error_score.cpu().tolist())

            # EOS判定
            if (next_token == self.config.eos_token_id).all():
                break

        return {
            "generated_tokens": generated_tokens,
            "generated_types": generated_types,
            "generated_specificity": generated_spec,
            "generated_depth": generated_depth,
            "log": generation_log,
        }

    def _sample_top_p(
        self,
        logits: torch.Tensor,
        top_p: float,
    ) -> torch.Tensor:
        """
        Top-p (nucleus) sampling

        Args:
            logits: [batch, vocab_size]
            top_p: cumulative probability threshold

        Returns:
            [batch] sampled token ids
        """
        sorted_logits, sorted_indices = torch.sort(logits, descending=True)
        cumsum = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)

        # top_pを超えたところでマスク
        mask = cumsum - F.softmax(sorted_logits, dim=-1) > top_p
        sorted_logits[mask] = float("-inf")

        probs = F.softmax(sorted_logits, dim=-1)
        next_token_idx = torch.multinomial(probs, num_samples=1)

        return sorted_indices.gather(-1, next_token_idx).squeeze(-1)

    def _infer_type_metadata(
        self,
        type_id: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        型IDから具体度と階層深度を導出

        Args:
            type_id: [batch] type IDs

        Returns:
            (specificity, depth) both [batch]
        """
        spec = self.type_metadata_spec[type_id]
        depth = self.type_metadata_depth[type_id]
        return spec, depth

    def get_num_params(self, non_embedding: bool = True) -> int:
        """
        モデルのパラメータ数を取得

        Args:
            non_embedding: Embedding層を除くかどうか

        Returns:
            パラメータ数
        """
        n_params = sum(p.numel() for p in self.parameters())
        if non_embedding:
            # Genesis層のEmbeddingを除く
            n_params -= self.genesis.takamimusubi.embedding.weight.numel()
            n_params -= self.genesis.kamimusubi.type_embedding.weight.numel()
            n_params -= self.genesis.kamimusubi.hash_embedding.weight.numel()
            n_params -= self.genesis.kamimusubi.specificity_embedding.weight.numel()
            n_params -= self.genesis.kamimusubi.depth_embedding.weight.numel()
        return n_params

    def count_parameters(self) -> Dict[str, int]:
        """
        層ごとのパラメータ数を集計

        Returns:
            Dict with layer names and parameter counts
        """
        counts = {}
        for name, module in self.named_children():
            count = sum(p.numel() for p in module.parameters())
            counts[name] = count
        counts["total"] = sum(counts.values())
        return counts


def create_model(config: Optional[KojikiConfig] = None, tokenizer=None) -> KojikiLM:
    """
    モデルのファクトリ関数

    Args:
        config: 設定（Noneの場合はデフォルト設定）
        tokenizer: トークナイザー（八咫鏡Attentionの定義検出に使用）

    Returns:
        KojikiLM instance
    """
    if config is None:
        config = KojikiConfig()
    return KojikiLM(config, tokenizer=tokenizer)
