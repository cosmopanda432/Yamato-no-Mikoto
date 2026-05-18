"""
Julia-no-Mikoto: 学習ユーティリティ (Training Utilities)

損失関数、学習率スケジューラ、学習ループなど。
"""

from typing import Dict, Optional, Tuple, Any
import math

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import AdamW
from torch.optim.lr_scheduler import LambdaLR

from .config import KojikiConfig
from .model import KojikiLM


class KojikiLoss(nn.Module):
    """
    古事記Loss (v2)

    複合損失関数。各タスクの重みは設定から取得。

    【v2変更点】
    - 型予測（月読）の重みを増加（推論時に重要なため）
    - 0.5 → 0.8
    """

    def __init__(self, config: KojikiConfig):
        super().__init__()
        self.config = config

        # 各タスクの損失関数
        self.token_loss = nn.CrossEntropyLoss(ignore_index=-100)
        self.type_loss = nn.CrossEntropyLoss(ignore_index=-100)
        self.stability_loss = nn.CrossEntropyLoss()
        self.binary_loss = nn.BCELoss()

        # 損失の重み
        self.weights = config.get_loss_weights()

    def forward(
        self,
        outputs: Dict[str, torch.Tensor],
        targets: Dict[str, torch.Tensor],
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """
        損失計算

        Args:
            outputs: モデル出力
            targets: 教師データ
                - next_tokens: 次トークンの正解 [batch, seq_len]
                - next_types: 次型の正解 [batch, seq_len]
                - stability_labels: 型安定性ラベル [batch, seq_len]
                - simd_labels: SIMD可能性ラベル [batch, seq_len]
                - diff_labels: 自動微分可能性ラベル [batch, seq_len]
                - error_labels: エラーラベル [batch, seq_len]

        Returns:
            (total_loss, loss_dict)
        """
        losses = {}

        # === 天照: 次トークン予測 ===
        if "next_tokens" in targets:
            losses["token"] = self.token_loss(
                outputs["logits"].view(-1, outputs["logits"].size(-1)),
                targets["next_tokens"].view(-1),
            )

        # === 月読: 型予測 (v2: 重要度UP) ===
        if "next_types" in targets:
            losses["type"] = self.type_loss(
                outputs["type_logits"].view(-1, outputs["type_logits"].size(-1)),
                targets["next_types"].view(-1),
            )

        # === 黄泉: 安定性 ===
        if "stability_labels" in targets:
            stability_probs = outputs["diagnostics"]["stability_probs"]
            losses["stability"] = self.stability_loss(
                stability_probs.view(-1, 3),
                targets["stability_labels"].view(-1),
            )

        # === 最適化ヒント ===
        optional_tasks = [
            ("simd", "simd_labels", "simd_score"),
            ("diff", "diff_labels", "differentiable"),
            ("error", "error_labels", "error_score"),
        ]

        for task_name, label_key, score_key in optional_tasks:
            if label_key in targets and score_key in outputs:
                score = outputs[score_key]
                # スコアが3次元の場合はsqueeze
                if score.dim() == 3:
                    score = score.squeeze(-1)
                losses[task_name] = self.binary_loss(
                    score,
                    targets[label_key].float(),
                )

        # 重み付け合計
        total = torch.tensor(0.0, device=next(iter(outputs.values())).device)
        for key, loss in losses.items():
            weight = self.weights.get(key, 0.1)
            total = total + weight * loss

        return total, losses


def get_cosine_schedule_with_warmup(
    optimizer: torch.optim.Optimizer,
    num_warmup_steps: int,
    num_training_steps: int,
    num_cycles: float = 0.5,
    last_epoch: int = -1,
) -> LambdaLR:
    """
    Cosine learning rate schedule with linear warmup

    Args:
        optimizer: Optimizer
        num_warmup_steps: Warmup steps
        num_training_steps: Total training steps
        num_cycles: Number of cosine cycles
        last_epoch: Last epoch

    Returns:
        LambdaLR scheduler
    """

    def lr_lambda(current_step: int) -> float:
        if current_step < num_warmup_steps:
            return float(current_step) / float(max(1, num_warmup_steps))
        progress = float(current_step - num_warmup_steps) / float(
            max(1, num_training_steps - num_warmup_steps)
        )
        return max(
            0.0, 0.5 * (1.0 + math.cos(math.pi * float(num_cycles) * 2.0 * progress))
        )

    return LambdaLR(optimizer, lr_lambda, last_epoch)


def create_optimizer(
    model: KojikiLM,
    config: KojikiConfig,
) -> AdamW:
    """
    Optimizerを作成

    Weight decayをEmbedding層とLayerNormには適用しない。

    Args:
        model: KojikiLM model
        config: Configuration

    Returns:
        AdamW optimizer
    """
    # Weight decay対象外のパラメータ名パターン
    no_decay = ["bias", "LayerNorm.weight", "layer_norm.weight", "embedding"]

    optimizer_grouped_parameters = [
        {
            "params": [
                p
                for n, p in model.named_parameters()
                if not any(nd in n for nd in no_decay)
            ],
            "weight_decay": config.weight_decay,
        },
        {
            "params": [
                p
                for n, p in model.named_parameters()
                if any(nd in n for nd in no_decay)
            ],
            "weight_decay": 0.0,
        },
    ]

    optimizer = AdamW(
        optimizer_grouped_parameters,
        lr=config.learning_rate,
        betas=(0.9, 0.999),
        eps=1e-8,
    )

    return optimizer


class Trainer:
    """
    学習管理クラス
    """

    def __init__(
        self,
        model: KojikiLM,
        config: KojikiConfig,
        device: torch.device,
    ):
        self.model = model.to(device)
        self.config = config
        self.device = device

        self.loss_fn = KojikiLoss(config)
        self.optimizer = create_optimizer(model, config)
        self.scheduler = get_cosine_schedule_with_warmup(
            self.optimizer,
            config.warmup_steps,
            config.max_steps,
        )

        self.global_step = 0
        self.best_loss = float("inf")

    def train_step(
        self,
        batch: Dict[str, torch.Tensor],
    ) -> Dict[str, float]:
        """
        単一学習ステップ

        Args:
            batch: バッチデータ
                - token_ids: [batch, seq_len]
                - type_ids: [batch, seq_len]
                - type_specificity: [batch, seq_len]
                - type_depth: [batch, seq_len]
                - token_roles: [batch, seq_len]
                - next_tokens: [batch, seq_len]
                - next_types: [batch, seq_len]
                - stability_labels: [batch, seq_len]

        Returns:
            Dict with loss values
        """
        self.model.train()
        self.optimizer.zero_grad()

        # デバイスに移動
        batch = {k: v.to(self.device) for k, v in batch.items()}

        # Forward
        outputs = self.model(
            token_ids=batch["token_ids"],
            type_ids=batch["type_ids"],
            type_specificity=batch["type_specificity"],
            type_depth=batch["type_depth"],
            token_roles=batch.get("token_roles"),
            type_hash=batch.get("type_hash"),
        )

        # 教師データの準備
        targets = {
            "next_tokens": batch.get("next_tokens"),
            "next_types": batch.get("next_types"),
            "stability_labels": batch.get("stability_labels"),
            "simd_labels": batch.get("simd_labels"),
            "diff_labels": batch.get("diff_labels"),
            "error_labels": batch.get("error_labels"),
        }
        targets = {k: v for k, v in targets.items() if v is not None}

        # Loss計算
        total_loss, loss_dict = self.loss_fn(outputs, targets)

        # Backward
        total_loss.backward()

        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)

        # Update
        self.optimizer.step()
        self.scheduler.step()

        self.global_step += 1

        # ログ用に数値化
        return {
            "total_loss": total_loss.item(),
            **{f"loss_{k}": v.item() for k, v in loss_dict.items()},
            "learning_rate": self.scheduler.get_last_lr()[0],
        }

    @torch.no_grad()
    def eval_step(
        self,
        batch: Dict[str, torch.Tensor],
    ) -> Dict[str, float]:
        """
        評価ステップ
        """
        self.model.eval()

        batch = {k: v.to(self.device) for k, v in batch.items()}

        outputs = self.model(
            token_ids=batch["token_ids"],
            type_ids=batch["type_ids"],
            type_specificity=batch["type_specificity"],
            type_depth=batch["type_depth"],
            token_roles=batch.get("token_roles"),
            type_hash=batch.get("type_hash"),
        )

        targets = {
            "next_tokens": batch.get("next_tokens"),
            "next_types": batch.get("next_types"),
            "stability_labels": batch.get("stability_labels"),
        }
        targets = {k: v for k, v in targets.items() if v is not None}

        total_loss, loss_dict = self.loss_fn(outputs, targets)

        return {
            "total_loss": total_loss.item(),
            **{f"loss_{k}": v.item() for k, v in loss_dict.items()},
        }

    def save_checkpoint(self, path: str):
        """チェックポイント保存"""
        torch.save(
            {
                "model_state_dict": self.model.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
                "scheduler_state_dict": self.scheduler.state_dict(),
                "global_step": self.global_step,
                "best_loss": self.best_loss,
                "config": self.config,
            },
            path,
        )

    def load_checkpoint(self, path: str):
        """チェックポイント読み込み"""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
        self.global_step = checkpoint["global_step"]
        self.best_loss = checkpoint["best_loss"]


def create_dummy_batch(
    batch_size: int = 2,
    seq_len: int = 128,
    config: Optional[KojikiConfig] = None,
    device: torch.device = torch.device("cpu"),
) -> Dict[str, torch.Tensor]:
    """
    テスト用のダミーバッチを作成

    Args:
        batch_size: バッチサイズ
        seq_len: シーケンス長
        config: 設定
        device: デバイス

    Returns:
        ダミーバッチ
    """
    if config is None:
        config = KojikiConfig()

    return {
        "token_ids": torch.randint(0, config.vocab_size, (batch_size, seq_len), device=device),
        "type_ids": torch.randint(0, config.type_vocab_size, (batch_size, seq_len), device=device),
        "type_specificity": torch.randint(0, 3, (batch_size, seq_len), device=device),
        "type_depth": torch.randint(0, config.type_hierarchy_depth, (batch_size, seq_len), device=device),
        "token_roles": torch.randint(0, config.num_token_roles, (batch_size, seq_len), device=device),
        "type_hash": torch.randint(0, config.hash_bucket_size, (batch_size, seq_len), device=device),
        "next_tokens": torch.randint(0, config.vocab_size, (batch_size, seq_len), device=device),
        "next_types": torch.randint(0, config.type_vocab_size, (batch_size, seq_len), device=device),
        "stability_labels": torch.randint(0, 3, (batch_size, seq_len), device=device),
        "simd_labels": torch.randint(0, 2, (batch_size, seq_len), device=device),
        "diff_labels": torch.randint(0, 2, (batch_size, seq_len), device=device),
        "error_labels": torch.randint(0, 2, (batch_size, seq_len), device=device),
    }
