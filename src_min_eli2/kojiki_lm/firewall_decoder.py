"""
Firewall デコーダ — token-by-token decode loop + 黄泉比良坂 (Firewall) 統合

src_min_eli2 では言霊 (Kotodama / symbol-aware bias) を **撤去**。
理由 (2026-05-21):
  - Go 版 mbpp-go ablation で bias 単独寄与が不可視 ([[project-go-roadmap-state]])
  - Elixir は静的型が無く bias 適用 surface area が狭い ([[feedback-elixir-has-no-static-types]])
  - 本プロジェクト主目的は Firewall 完成 ([[project-firewall-purpose]])、bias は副次
  - 死コードを保持しても次回 session の負担になるだけ

履歴的に bias 関連を残したい場合は src_min_go/kojiki_lm/kotodama_decoder.py 参照。
src_min_eli2 では「decode loop + Firewall」の最小核に絞る。

保持する重要修正:
  - 修正 A (transformers の LogitsWarper を直接使い byte-equivalent sampling)
  - 修正 D (`torch.Generator` 分離で `firewall.send` のサイドチャネルから隔離)
  - 修正 H (生成中の stop_token 検出で token-level early-stop)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

import torch
from transformers.generation.logits_process import (
    LogitsProcessorList,
    TemperatureLogitsWarper,
    TopKLogitsWarper,
    TopPLogitsWarper,
)

from .yomotsu_hirasaka import (
    L3ToL5Payload,
    L5ToL3Verdict,
    Verdict,
    YomotsuHirasaka,
)


@dataclass
class FirewallConfig:
    max_new_tokens: int = 64

    firewall_interval: int = 8
    """N step ごとに Firewall に問い合わせ"""

    temperature: float = 1.0
    do_sample: bool = False
    top_k: int = 50
    """transformers.generate のデフォルトに揃える (0 で disable)"""
    top_p: float = 0.95
    """nucleus sampling 上限累積確率 (1.0 で disable)"""

    # Ablation 用
    firewall_enabled: bool = True
    """False で Firewall OFF (HALT 介入なし、verdict 取得なし)"""

    sampling_seed: int | None = None
    """サンプリング専用 Generator の seed。None で global RNG を使う。

    指定するとデコード中の `tokenizer.decode` / `firewall.send` / Python GC 等が
    global CUDA RNG state を消費しても、`torch.multinomial` は影響を受けない。
    これにより `firewall_enabled` toggle で出力が byte-identical になる (修正 D)。

    複数 prompt を 1 つの decoder で回す場合、prompt ごとに seed を派生させる
    必要がある (全 prompt で同じ seed だと同じ系列になる)。呼び出し側で
    `args.seed * P + i` のような派生を行う。
    """


@dataclass
class StepLog:
    step_idx: int
    next_token_id: int
    verdict: str | None = None
    v_score: float | None = None


@dataclass
class FirewallResult:
    text: str
    generated_ids: list[int] = field(default_factory=list)
    final_verdict: L5ToL3Verdict | None = None
    steps: list[StepLog] = field(default_factory=list)
    halted_early: bool = False
    stopped_at_stop_token: bool = False
    """修正 H: generation 中に stop_token を検出して early-stop した"""
    prompt_id: str = ""


class FirewallDecoder:
    """token-by-token decode + Firewall 統合ループ (bias 機構なし)"""

    def __init__(
        self,
        firewall: YomotsuHirasaka,
        config: FirewallConfig | None = None,
    ) -> None:
        self.firewall = firewall
        self.config = config or FirewallConfig()
        # transformers の model.generate と byte-equivalent な sampling を実現するため、
        # 公式 LogitsWarper を直接使う。手書きで top_p を実装すると float32 累積加算の
        # 丸め誤差で off-by-1 になる (= 修正 A)。
        self._warpers: LogitsProcessorList | None = None
        # 修正 D: サンプリング専用 RNG (`generate()` 内で seed 指定時に初期化)。
        # `firewall.send` 等のサイドチャネルから sampler を物理的に隔離する。
        self._sampling_rng: torch.Generator | None = None

    def _build_warpers(self) -> LogitsProcessorList:
        cfg = self.config
        warpers = LogitsProcessorList()
        if cfg.temperature > 0 and cfg.temperature != 1.0:
            warpers.append(TemperatureLogitsWarper(cfg.temperature))
        if cfg.top_k > 0:
            warpers.append(TopKLogitsWarper(top_k=cfg.top_k, min_tokens_to_keep=1))
        if 0.0 < cfg.top_p < 1.0:
            warpers.append(TopPLogitsWarper(top_p=cfg.top_p, min_tokens_to_keep=1))
        return warpers

    @torch.no_grad()
    def generate(
        self,
        backbone: Any,
        tokenizer: Any,
        prompt_text: str,
        prompt_id: str | None = None,
        stop_tokens: tuple[str, ...] | list[str] = (),
    ) -> FirewallResult:
        """prompt_text から最大 cfg.max_new_tokens token 生成する。

        stop_tokens: 生成中に text_buffer の **生成部分** にこれらが現れたら
            early-stop する (修正 H)。post-process の truncate と同じセマンティクス。
        """
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

        # 修正 D: prompt 単位でサンプリング専用 Generator を初期化。
        if cfg.sampling_seed is not None:
            if (
                self._sampling_rng is None
                or self._sampling_rng.device != device
            ):
                self._sampling_rng = torch.Generator(device=device)
            self._sampling_rng.manual_seed(int(cfg.sampling_seed))

        text_buffer = prompt_text
        prompt_len = len(prompt_text)
        # 空文字列の stop_token は意味がないので除外
        active_stop_tokens = tuple(st for st in stop_tokens if st)

        generated_ids: list[int] = []
        steps: list[StepLog] = []
        final_verdict: L5ToL3Verdict | None = None
        halted = False
        stopped_at_stop = False

        eos_id = getattr(tokenizer, "eos_token_id", None)

        # KV cache を使った decode。初回は prompt 全体を forward、2 step 目以降は
        # 1 token のみを past_key_values と合わせて forward する。
        past_key_values = None
        cumulative_input_ids = input_ids

        for step in range(cfg.max_new_tokens):
            if past_key_values is None:
                step_input_ids = cumulative_input_ids
            else:
                step_input_ids = next_tok

            outputs = backbone(
                input_ids=step_input_ids,
                attention_mask=attention_mask,
                past_key_values=past_key_values,
                output_hidden_states=False,
                use_cache=True,
                return_dict=True,
            )
            last_logits = outputs.logits[:, -1, :]   # [B, V]
            past_key_values = getattr(outputs, "past_key_values", None)

            next_tok = self._sample(last_logits, cumulative_input_ids)
            tok_id = int(next_tok.item())
            generated_ids.append(tok_id)

            cumulative_input_ids = torch.cat([cumulative_input_ids, next_tok], dim=-1)
            attention_mask = torch.cat(
                [attention_mask, torch.ones_like(next_tok)], dim=-1
            )
            piece = tokenizer.decode([tok_id], skip_special_tokens=True)
            text_buffer = text_buffer + piece

            step_log = StepLog(
                step_idx=step,
                next_token_id=tok_id,
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

                if verdict.verdict is Verdict.HALT:
                    halted = True

            steps.append(step_log)

            if halted:
                break
            # EOS は firewall check の有無に依らず常に停止条件として評価する
            # (修正 D の byte-identical 性質に必要)
            if eos_id is not None and tok_id == eos_id:
                break
            # 修正 H: 生成部分に stop_token が含まれたら早期終了
            if active_stop_tokens:
                generated_text = text_buffer[prompt_len:]
                if any(st in generated_text for st in active_stop_tokens):
                    stopped_at_stop = True
                    break

        return FirewallResult(
            text=tokenizer.decode(generated_ids, skip_special_tokens=True),
            generated_ids=generated_ids,
            final_verdict=final_verdict,
            steps=steps,
            halted_early=halted,
            stopped_at_stop_token=stopped_at_stop,
            prompt_id=pid,
        )

    def _sample(self, logits: torch.Tensor, input_ids: torch.Tensor) -> torch.Tensor:
        """修正 A: transformers.generate と byte-equivalent な sampling。

        手書きの top_k/top_p は捨てて、`transformers.generation.logits_process` の
        公式 Warper をそのまま使う。
        """
        cfg = self.config
        if not (cfg.do_sample and cfg.temperature > 0):
            return logits.argmax(dim=-1, keepdim=True)

        if self._warpers is None:
            self._warpers = self._build_warpers()

        scores = self._warpers(input_ids, logits)
        probs = torch.softmax(scores, dim=-1)
        # 修正 D: 専用 Generator があればそれを使い、global RNG から隔離する。
        return torch.multinomial(probs, 1, generator=self._sampling_rng)

    @staticmethod
    def _infer_device(backbone: Any, fallback: torch.device) -> torch.device:
        try:
            return next(backbone.parameters()).device
        except (StopIteration, AttributeError):
            return fallback
