"""
言霊デコーダ (Kotodama Decoder)

TypeHead 条件付きマスクと黄泉比良坂 Firewall を 1 つの decode ループで統合する。
M2 最小版の核となる「**売り**」結合点:

  - 売り #1 (型予測): is_type_context が真なら TsukuyomiTypeHead の top-K 予測 →
                       KotodamaMaskBuilder でマスク → logits に -inf を物理印加
  - 売り #2 (Firewall): firewall_interval ごとに L3ToL5Payload を生成し、
                        YomotsuHirasaka 経由で Evaluator 判定。HALT で即停止。

Step ごとの mask 適用状況・top type ID・verdict を StepLog として記録するので、
M2 Done 条件の「-inf がログで確認できる」「Firewall→Evaluator→COMMIT/HALT が返る」
を再現可能に証跡化できる。
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

import torch

from .kotodama_context import find_predict_target_char_span, is_type_context
from .kotodama_token_mask import KotodamaMaskBuilder
from .yomotsu_hirasaka import (
    L3ToL5Payload,
    L5ToL3Verdict,
    Verdict,
    YomotsuHirasaka,
)

logger = logging.getLogger(__name__)


@dataclass
class KotodamaConfig:
    max_new_tokens: int = 64
    top_k_types: int = 5         # TypeHead top-K を mask union
    firewall_interval: int = 8   # この step 数ごとに Firewall に問い合わせ
    temperature: float = 1.0
    do_sample: bool = False      # 既定は greedy (再現性のため)

    # Ablation 用 (M6 評価)
    mask_enabled: bool = True       # False: 言霊マスクを掛けない (= vanilla decode)
    firewall_enabled: bool = True   # False: Firewall を介さず常に COMMIT 扱い


@dataclass
class StepLog:
    step_idx: int
    next_token_id: int
    masked: bool
    num_allowed: int = 0                 # マスク True 数 (= 許可されたトークン数)
    top_type_ids: tuple[int, ...] = ()
    verdict: str | None = None           # この step で firewall を引いた場合
    v_score: float | None = None


@dataclass
class KotodamaResult:
    text: str
    generated_ids: list[int] = field(default_factory=list)
    final_verdict: L5ToL3Verdict | None = None
    steps: list[StepLog] = field(default_factory=list)
    halted_early: bool = False
    prompt_id: str = ""

    @property
    def num_masked_steps(self) -> int:
        return sum(1 for s in self.steps if s.masked)


class KotodamaDecoder:
    """TypeHead 駆動マスク decode + Firewall 統合ループ"""

    def __init__(
        self,
        mask_builder: KotodamaMaskBuilder,
        type_head: torch.nn.Module,
        firewall: YomotsuHirasaka,
        config: KotodamaConfig | None = None,
    ):
        self.mask_builder = mask_builder
        self.type_head = type_head
        self.firewall = firewall
        self.config = config or KotodamaConfig()

    @torch.no_grad()
    def generate(
        self,
        backbone: Any,
        tokenizer: Any,
        prompt_text: str,
        prompt_id: str | None = None,
    ) -> KotodamaResult:
        cfg = self.config
        pid = prompt_id or uuid.uuid4().hex[:8]

        enc = tokenizer(prompt_text, return_tensors="pt")
        input_ids: torch.Tensor = enc["input_ids"]
        attention_mask: torch.Tensor = enc.get("attention_mask")
        if attention_mask is None:
            attention_mask = torch.ones_like(input_ids)

        device = self._infer_device(backbone, fallback=input_ids.device)
        input_ids = input_ids.to(device)
        attention_mask = attention_mask.to(device)

        text_buffer = prompt_text
        generated_ids: list[int] = []
        steps: list[StepLog] = []
        final_verdict: L5ToL3Verdict | None = None
        halted = False

        eos_id = getattr(tokenizer, "eos_token_id", None)

        for step in range(cfg.max_new_tokens):
            outputs = backbone(
                input_ids=input_ids,
                attention_mask=attention_mask,
                output_hidden_states=True,
                use_cache=False,
                return_dict=True,
            )
            full_hidden = outputs.hidden_states[-1]              # [B, L, d]
            last_logits = outputs.logits[:, -1, :]               # [B, V]

            masked, num_allowed, top_type_ids = self._maybe_apply_mask(
                text_buffer=text_buffer,
                full_hidden=full_hidden,
                last_logits=last_logits,
                tokenizer=tokenizer,
            )

            next_tok = self._sample(last_logits)
            tok_id = int(next_tok.item())
            generated_ids.append(tok_id)

            input_ids = torch.cat([input_ids, next_tok], dim=-1)
            attention_mask = torch.cat(
                [attention_mask, torch.ones_like(next_tok)], dim=-1
            )
            piece = tokenizer.decode([tok_id], skip_special_tokens=True)
            text_buffer = text_buffer + piece

            step_log = StepLog(
                step_idx=step,
                next_token_id=tok_id,
                masked=masked,
                num_allowed=num_allowed,
                top_type_ids=top_type_ids,
            )

            # Firewall 問い合わせ (firewall_enabled=False の場合は bypass)
            is_last = step == cfg.max_new_tokens - 1
            should_check = cfg.firewall_enabled and (
                (step + 1) % cfg.firewall_interval == 0 or is_last
            )
            if should_check:
                verdict = self.firewall.send(
                    L3ToL5Payload(
                        text=text_buffer,
                        step_idx=step,
                        prompt_id=pid,
                    )
                )
                final_verdict = verdict
                step_log.verdict = verdict.verdict.value
                step_log.v_score = verdict.v_score

                steps.append(step_log)

                if verdict.verdict is Verdict.HALT:
                    halted = True
                    break
                continue

            steps.append(step_log)

            if eos_id is not None and tok_id == eos_id:
                break

        return KotodamaResult(
            text=tokenizer.decode(generated_ids, skip_special_tokens=True),
            generated_ids=generated_ids,
            final_verdict=final_verdict,
            steps=steps,
            halted_early=halted,
            prompt_id=pid,
        )

    def _maybe_apply_mask(
        self,
        text_buffer: str,
        full_hidden: torch.Tensor,
        last_logits: torch.Tensor,
        tokenizer: Any,
    ) -> tuple[bool, int, tuple[int, ...]]:
        """type-context なら mask を適用し、適用フラグ + 統計を返す

        TypeHead の入力 hidden は **学習時の label 位置 (= type-annotated identifier の
        最初の subword)** に揃える。これが取れない場合は mask しない (旧版の「:
        直後の空白で TypeHead を呼ぶ」フォールバックは学習タスクと不整合な予測になり、
        識別子位置で型語彙を強制してハルシネーションを増やすため廃止)。
        """
        if not self.config.mask_enabled:
            return False, 0, ()
        if not is_type_context(text_buffer):
            return False, 0, ()

        target_span = find_predict_target_char_span(text_buffer)
        if target_span is None:
            return False, 0, ()

        target_pos = self._char_span_to_token_index(
            text_buffer, target_span, tokenizer, full_hidden.size(1)
        )
        if target_pos is None:
            return False, 0, ()

        identifier_hidden = full_hidden[:, target_pos:target_pos + 1, :]   # [B, 1, d]
        type_out = self.type_head(identifier_hidden)
        type_logits: torch.Tensor = type_out["type_logits"]                # [B, 1, T]
        topk = type_logits[0, 0].topk(self.config.top_k_types)
        top_type_ids = tuple(int(i) for i in topk.indices.tolist())

        mask = self.mask_builder.build_mask_for_type_ids(top_type_ids)
        num_allowed = int(mask.sum().item())

        if num_allowed == 0:
            logger.warning(
                "type-context but mask empty for top_type_ids=%s; skip masking",
                top_type_ids,
            )
            return False, 0, top_type_ids

        mask_dev = mask.to(last_logits.device)
        # last_logits は [B, V]。in-place で -inf を適用
        last_logits.masked_fill_(~mask_dev.unsqueeze(0), float("-inf"))
        return True, num_allowed, top_type_ids

    @staticmethod
    def _char_span_to_token_index(
        text: str,
        char_span: tuple[int, int],
        tokenizer: Any,
        max_token_pos: int,
    ) -> int | None:
        """text を tokenize し直し、char_span と最初に overlap する token index を返す

        学習時の align_labels (scripts/data/prepare_sft_dataset.py) と同じロジック:
        identifier の char-span と最初に overlap する Qwen subword を採用。
        """
        cs, ce = char_span
        try:
            enc = tokenizer(
                text, add_special_tokens=False, return_offsets_mapping=True,
            )
        except (TypeError, ValueError):
            # offset_mapping 非対応 tokenizer (テスト用 mock など)
            return None
        offsets = enc.get("offset_mapping")
        if not offsets:
            return None
        for i, (s, e) in enumerate(offsets):
            if s >= ce:
                break
            if e > cs:  # overlap
                # generate ループで input_ids 全体に対応する hidden だけが取れる。
                # 再 tokenize の結果が hidden の長さを超えるレアケースは弾く。
                if i >= max_token_pos:
                    return None
                return i
        return None

    def _sample(self, logits: torch.Tensor) -> torch.Tensor:
        cfg = self.config
        if cfg.do_sample and cfg.temperature > 0:
            probs = torch.softmax(logits / cfg.temperature, dim=-1)
            return torch.multinomial(probs, 1)
        return logits.argmax(dim=-1, keepdim=True)

    @staticmethod
    def _infer_device(backbone: Any, fallback: torch.device) -> torch.device:
        try:
            return next(backbone.parameters()).device
        except (StopIteration, AttributeError):
            return fallback
