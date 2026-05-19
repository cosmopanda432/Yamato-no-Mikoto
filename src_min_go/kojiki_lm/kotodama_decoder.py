"""
言霊デコーダ (Go 版) — symbol-aware logit bias + Firewall 統合

TS 版 src_min/kojiki_lm/kotodama_decoder.py との設計上の差分:
  - **TypeHead を使わない** (Stage 2 ヘッドは TS 型 vocab 特化のため Go 版では破棄)
  - **AST-based symbol oracle (Go daemon) から types ∪ vars を取得**
  - **mask (-inf 強制) ではなく logit `+k` bias 加算**
    → LM の正解 token を殺さず、symbol との一致に確率重み付け
  - **Python 側で context 事前 filter** → oracle 呼び出しを decode 全体で
    数回〜十数回に抑える

責務分担:
  - Python (このファイル): 事前 filter, oracle query, bias 加算, sample, Firewall
  - Go daemon (oracle):     AST 解析, scope walk, symbol 集合 (types ∪ vars) 返却
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

import torch

from .go_symbol_oracle import OracleClient, OracleResult
from .kotodama_context import looks_like_type_position
from .kotodama_token_mask import BiasConfig, GoSymbolBiasBuilder
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
    bias_value: float = 2.0
    """logit に加算する bias の大きさ。0.0 にすると vanilla 同等"""

    firewall_interval: int = 8
    """N step ごとに Firewall に問い合わせ"""

    temperature: float = 1.0
    do_sample: bool = False

    # Ablation 用
    mask_enabled: bool = True
    """False で言霊 bias OFF (= vanilla 同等)"""

    firewall_enabled: bool = True
    """False で Firewall OFF (HALT 介入なし)"""

    oracle_enabled: bool = True
    """False で oracle 呼ばずに bias 加算スキップ (debug 用)"""


@dataclass
class StepLog:
    step_idx: int
    next_token_id: int
    bias_applied: bool = False
    scope_kind: str = "unknown"
    num_allowed: int = 0
    """oracle が返した types + vars の合計 (重複除去前)"""
    sample_top_types: tuple[str, ...] = ()
    """この step で bias の対象になった types の先頭数件 (debug)"""
    verdict: str | None = None
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
    def num_biased_steps(self) -> int:
        return sum(1 for s in self.steps if s.bias_applied)


class KotodamaDecoder:
    """symbol-aware bias decode + Firewall 統合ループ"""

    def __init__(
        self,
        oracle: OracleClient | None,
        bias_builder: GoSymbolBiasBuilder,
        firewall: YomotsuHirasaka,
        config: KotodamaConfig | None = None,
    ) -> None:
        self.oracle = oracle
        self.bias_builder = bias_builder
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
                output_hidden_states=False,
                use_cache=False,
                return_dict=True,
            )
            last_logits = outputs.logits[:, -1, :]   # [B, V]

            bias_applied, scope_kind, num_allowed, sample_types = self._maybe_apply_bias(
                text_buffer=text_buffer,
                last_logits=last_logits,
                session_id=pid,
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
                bias_applied=bias_applied,
                scope_kind=scope_kind,
                num_allowed=num_allowed,
                sample_top_types=sample_types,
            )

            # Firewall 問い合わせ
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

    def _maybe_apply_bias(
        self,
        text_buffer: str,
        last_logits: torch.Tensor,
        session_id: str,
    ) -> tuple[bool, str, int, tuple[str, ...]]:
        """type position なら oracle 問い合わせ → bias 加算。戻り値は debug 用"""
        cfg = self.config
        if not cfg.mask_enabled or cfg.bias_value == 0.0:
            return False, "unknown", 0, ()

        # 事前 filter: 明らかに型 position でない位置は skip
        if not looks_like_type_position(text_buffer):
            return False, "unknown", 0, ()

        # oracle 不在/無効化なら bias 加算しない
        if self.oracle is None or not cfg.oracle_enabled:
            return False, "unknown", 0, ()

        result: OracleResult | None = self.oracle.query(
            prompt=text_buffer,
            cursor=len(text_buffer),
            session_id=session_id,
        )
        if result is None:
            # oracle 失敗時は bias 加算 skip (vanilla 同等で続行)
            return False, "unknown", 0, ()

        # oracle が unknown を返す = 型 position ではなかった (事前 filter 偽陽性)
        if result.scope_kind == "unknown":
            return False, "unknown", 0, ()

        bias = self.bias_builder.build_bias_for_symbols(
            types=result.types,
            vars_=result.vars,
            scope_kind=result.scope_kind,
            config=BiasConfig(bias_value=cfg.bias_value),
        )
        num_allowed = len(result.types) + len(result.vars)
        if num_allowed == 0:
            return False, result.scope_kind, 0, ()

        bias_dev = bias.to(last_logits.device, dtype=last_logits.dtype)
        # last_logits は [B, V]、bias は [V]。ブロードキャスト加算
        last_logits.add_(bias_dev.unsqueeze(0))

        return True, result.scope_kind, num_allowed, result.types[:5]

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
