"""
YamatoQwenForCausalLM — Qwen2.5-Coder のサブクラス

M0: 空殻として導入し、from_pretrained の戻り値クラスを yamatoLLM 側で固定。
M2 (現状): `generate_kotodama` を提供。TypeHead 駆動マスクと黄泉比良坂 Firewall を
           統合した KotodamaDecoder に dispatch する。標準の `generate` は
           Qwen2ForCausalLM 親クラスのまま (vanilla baseline 用)。

後続 M で埋める予定の override 点:

  M3 (天御柱 4 Phase):
      forward 内で各 decoder layer の出力を amenomihashira (5 層
      オーケストレータ) に渡す hook を挿入。

  M3+ (八咫鏡):
      Qwen2DecoderLayer の attention 実装を yata_kagami_attention
      (多視点注意) に置換。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from transformers.models.qwen2.modeling_qwen2 import Qwen2ForCausalLM

if TYPE_CHECKING:
    import torch

    from .kotodama_decoder import KotodamaConfig, KotodamaResult
    from .kotodama_token_mask import KotodamaMaskBuilder
    from .yomotsu_hirasaka import YomotsuHirasaka

logger = logging.getLogger(__name__)


class YamatoQwenForCausalLM(Qwen2ForCausalLM):
    """yamatoLLM 用 Qwen2 サブクラス"""

    def generate_kotodama(
        self,
        prompt_text: str,
        tokenizer,
        mask_builder: "KotodamaMaskBuilder",
        type_head: "torch.nn.Module",
        firewall: "YomotsuHirasaka",
        config: "KotodamaConfig | None" = None,
        prompt_id: str | None = None,
    ) -> "KotodamaResult":
        """
        M2 エントリポイント: 言霊マスク decode + Firewall 統合。

        標準の HuggingFace `generate` は親クラスのまま残してあるので、
        baseline (vanilla Qwen) との Ablation 比較もこの 1 クラスで可能。
        """
        from .kotodama_decoder import KotodamaConfig, KotodamaDecoder

        decoder = KotodamaDecoder(
            mask_builder=mask_builder,
            type_head=type_head,
            firewall=firewall,
            config=config or KotodamaConfig(),
        )
        return decoder.generate(
            backbone=self,
            tokenizer=tokenizer,
            prompt_text=prompt_text,
            prompt_id=prompt_id,
        )
