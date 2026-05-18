"""
M0 — YamatoQwenForCausalLM: Qwen2.5-Coder のサブクラス骨格

roadmap.md M0 で定める「空殻」。具体的な hook 点 (forward / generate /
attention override) はこのファイル内に **コメントで宣言** するだけで、
中身は親 Qwen2ForCausalLM の挙動をそのまま継承する。

後続マイルストーンで埋める override 点:

  M2 (言霊):
      generate を kotodama_decoder 経由の自前 decode ループに置換。
      各ステップで Authority チケットを消費し、TS Compiler API 由来の
      valid token id 集合で logits を物理マスク (= -inf) する。

  M3 (天御柱 4 Phase):
      forward 内で各 decoder layer の出力を amenomihashira (5 層
      オーケストレータ) に渡す hook を挿入。Phase 1→2→3→4 を駆動。
      output_hidden_states=True で hidden_states を露出する親実装を
      そのまま使い、外側 (YamatoLLM) ラッパーが消費する構成も可。

  M3+ (八咫鏡):
      Qwen2DecoderLayer の attention 実装を yata_kagami_attention
      (多視点注意) に置換。eager/sdpa 実装の差し替え点を経由する。

このクラスを M0 段階で導入する理由:
  - 後続 M でアーキ改造を加える際、from_pretrained の戻り値クラスを
    一貫させる
  - YamatoLLM (wrapper) の backbone 型を Qwen2ForCausalLM ではなく
    YamatoQwenForCausalLM に固定し、isinstance 分岐や mypy 上の識別を可能にする
  - 既存 custom_heads.pt の attach パスに回帰を生じさせない (空殻のため)
"""

from __future__ import annotations

import logging

from transformers.models.qwen2.modeling_qwen2 import Qwen2ForCausalLM

logger = logging.getLogger(__name__)


class YamatoQwenForCausalLM(Qwen2ForCausalLM):
    """
    yamatoLLM 用 Qwen2 サブクラス (M0 空殻)

    現状は親 Qwen2ForCausalLM をそのまま継承するのみ。後続 M で
    forward / generate / decoder attention の override を順次注入する。
    """

    pass
