"""
ashihara_runtime.py — 葦原中国（Layer 3 推論ランタイム）

Layer 3: 推論環境（ランタイム）
天御柱オーケストレータから呼び出され、実際の推論を実行する。

責務:
- Forward Pass の実行（チケット検証付き）
- 自己回帰生成ループ
- 言霊（Kotonodama）によるLogits操作
- 直毘神（NaobiValidator）による修復実行

設計原則:
- AshiharaRuntimeは「生成」のみを担当
- 評価はLayer 5（YomiEvaluator）に委譲
- 座標系はAmeNoMinakaNushiから取得
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import math

# Optional torch import for type hints
try:
    import torch
    import torch.nn.functional as F
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    torch = None


# 直接実行時とモジュールimport時の両方に対応
try:
    from .zoka_sanshin import (
        AmeNoMinakaNushi,
        TakamiMusubi,
        ForwardPassTicket,
        TicketStatus,
    )
except ImportError:
    from kojiki_lm.julia_no_mikoto.zoka_sanshin import (
        AmeNoMinakaNushi,
        TakamiMusubi,
        ForwardPassTicket,
        TicketStatus,
    )


# ============================================================
# 生成フェーズ（従来のGenerationPhaseを継承）
# ============================================================

class GenerationPhase:
    """
    天の御柱の儀式における3段階

    KuniumiLayer.phase_embedding の 0/1/2 に直接対応。
    """
    IZANAGI = 0    # 構造先導: struct, abstract type, const
    IZANAMI = 1    # 実体応答: function signatures
    KAMIYUMI = 2   # 万物生成: implementation (神産み)


# ============================================================
# 生成結果データクラス
# ============================================================

@dataclass
class GenerationResult:
    """
    単一フェーズの生成結果

    Attributes:
        phase: 生成フェーズ（IZANAGI / IZANAMI / KAMIYUMI）
        text: 生成されたテキスト
        token_ids: トークンIDシーケンス
        type_ids: 型IDシーケンス（オプション）
        logits: 最終ステップのlogits（オプション）
        diagnostics: YomiLayerからの診断情報（オプション）
        stability_scores: トークンごとの安定性スコア
        error_scores: トークンごとのエラースコア
        type_distribution: 型IDの分布
    """
    phase: int
    text: str
    token_ids: List[int]
    type_ids: Optional[List[int]] = None
    logits: Optional[List[float]] = None
    diagnostics: Dict[str, Any] = field(default_factory=dict)
    stability_scores: List[float] = field(default_factory=list)
    error_scores: List[float] = field(default_factory=list)
    type_distribution: Dict[int, int] = field(default_factory=dict)


@dataclass
class PipelineOutput:
    """
    Layer 3パイプライン全体の出力

    黄泉比良坂を通過してLayer 5に送られる形式。
    """
    text: str
    logits: Optional[List[List[float]]] = None
    query: Optional[dict] = None
    type_ids: Optional[List[int]] = None
    constraints: Optional[dict] = None
    diagnostics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """黄泉比良坂に送る辞書形式に変換"""
        return {
            "text": self.text,
            "logits": self.logits,
            "query": self.query,
            "type_ids": self.type_ids,
            "constraints": self.constraints,
            "diagnostics": self.diagnostics,
        }


# ============================================================
# 葦原中国ランタイム
# ============================================================

class AshiharaRuntime:
    """
    葦原中国（Ashihara-no-Nakatsukuni）= Layer 3 推論ランタイム

    天御柱オーケストレータの「右旋」フェーズで呼び出される。
    実際のモデル推論とテキスト生成を担当。

    設計原則:
    - チケット検証: TakamiMusubiからのForwardPassTicketが必要
    - 3段階生成: IZANAGI → IZANAMI → KAMIYUMI
    - 言霊統合: HiedaNoAreからのKotonodamaを適用
    - 診断情報: YomiLayerの出力をdiagnosticsとして保持

    Args:
        model: KojikiLM or KojikiMoE モデル
        tokenizer: JuliaTokenizer
        device: torch.device
        config: KojikiConfig（オプション）
    """

    def __init__(
        self,
        model=None,
        tokenizer=None,
        device=None,
        config=None,
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.config = config

        # 設定値の取得
        if config is not None:
            self.max_seq_len = getattr(config, 'max_seq_len', 1024)
            self.phase1_max_tokens = getattr(config, 'phase1_max_tokens', 256)
            self.phase2_max_tokens = getattr(config, 'phase2_max_tokens', 256)
            self.phase3_max_tokens = getattr(config, 'phase3_max_tokens', 512)
            self.eos_token_id = getattr(config, 'eos_token_id', 2)
        else:
            self.max_seq_len = 1024
            self.phase1_max_tokens = 256
            self.phase2_max_tokens = 256
            self.phase3_max_tokens = 512
            self.eos_token_id = 2

    def execute_pipeline(
        self,
        context: dict,
        ticket: ForwardPassTicket,
    ) -> dict:
        """
        Layer 3パイプラインを実行。

        Parameters:
            context: 天御柱から渡されるコンテキスト
                - query: dict (元のリクエスト)
                - external_context: dict (稗田阿礼からの外部データ)
                - repair_hints: List[str] (修復ヒント、REPAIRループ時)
                - coordinate_axes: dict (評価軸)
                - origin: dict (閾値)

            ticket: ForwardPassTicket
                TakamiMusubiから発行されたチケット

        Returns:
            dict: 黄泉比良坂に送る形式
                - text: str
                - logits: List[List[float]] (オプション)
                - query: dict
                - type_ids: List[int] (オプション)
                - constraints: dict (オプション)
                - diagnostics: dict
        """
        # チケット検証
        status = TakamiMusubi.validate_ticket(ticket)
        if status != TicketStatus.VALID:
            return {
                "text": "",
                "error": f"ticket_{status.value}",
                "query": context.get("query"),
                "diagnostics": {"ticket_status": status.value},
            }

        # クエリの抽出
        query = context.get("query", {})
        prompt = query.get("prompt", "")

        # 修復ヒントがあればプロンプトに追加
        repair_hints = context.get("repair_hints", [])
        if repair_hints:
            hint_text = "\n".join(f"# HINT: {h}" for h in repair_hints)
            prompt = f"{hint_text}\n{prompt}"

        # 外部コンテキストの注入
        external_context = context.get("external_context", {})
        recitation = external_context.get("recitation", "")
        if recitation:
            prompt = f"{recitation}\n\n{prompt}"

        # モデルが設定されていない場合のフォールバック
        if self.model is None or self.tokenizer is None:
            return self._fallback_generate(prompt, query)

        # 3段階生成を実行
        results = self._execute_three_phase_generation(
            prompt=prompt,
            context=context,
        )

        # 結果を統合
        return self._build_pipeline_output(results, query, context)

    def _execute_three_phase_generation(
        self,
        prompt: str,
        context: dict,
    ) -> List[GenerationResult]:
        """
        3段階生成（IZANAGI → IZANAMI → KAMIYUMI）を実行。

        各フェーズでKuniumiLayerのgeneration_phaseを切り替え。
        """
        results: List[GenerationResult] = []

        # 生成パラメータ
        temperature = context.get("temperature", 0.7)
        top_p = context.get("top_p", 0.9)
        error_threshold = AmeNoMinakaNushi.get_origin("naobi_error_threshold")

        # 外部コンテキスト（言霊用）
        external_context = context.get("external_context", {})
        kotonodama = external_context.get("kotonodama")

        # === Phase 1: IZANAGI（型定義） ===
        phase1 = self._generate_phase(
            prompt_text=prompt,
            phase=GenerationPhase.IZANAGI,
            max_tokens=self.phase1_max_tokens,
            temperature=temperature,
            top_p=top_p,
            error_threshold=error_threshold,
            kotonodama=kotonodama,
        )
        results.append(phase1)

        # === Phase 2: IZANAMI（インターフェース） ===
        phase2_prompt = f"{prompt}\n{phase1.text}" if phase1.text else prompt
        phase2 = self._generate_phase(
            prompt_text=phase2_prompt,
            phase=GenerationPhase.IZANAMI,
            max_tokens=self.phase2_max_tokens,
            temperature=temperature,
            top_p=top_p,
            error_threshold=error_threshold,
            kotonodama=kotonodama,
        )
        results.append(phase2)

        # === Phase 3: KAMIYUMI（実装） ===
        phase3_prompt = f"{phase2_prompt}\n{phase2.text}" if phase2.text else phase2_prompt
        phase3 = self._generate_phase(
            prompt_text=phase3_prompt,
            phase=GenerationPhase.KAMIYUMI,
            max_tokens=self.phase3_max_tokens,
            temperature=temperature,
            top_p=top_p,
            error_threshold=error_threshold,
            kotonodama=kotonodama,
        )
        results.append(phase3)

        return results

    def _generate_phase(
        self,
        prompt_text: str,
        phase: int,
        max_tokens: int,
        temperature: float = 0.7,
        top_p: float = 0.9,
        error_threshold: float = 0.8,
        kotonodama=None,
    ) -> GenerationResult:
        """
        単一フェーズの自己回帰生成を実行。

        Parameters:
            prompt_text: 入力プロンプト
            phase: GenerationPhase (0, 1, 2)
            max_tokens: 最大生成トークン数
            temperature: サンプリング温度
            top_p: Nucleus sampling閾値
            error_threshold: 黄泉行き判定の閾値
            kotonodama: 言霊プロセッサ（オプション）

        Returns:
            GenerationResult: 生成結果
        """
        if not HAS_TORCH or self.model is None:
            return GenerationResult(
                phase=phase,
                text="",
                token_ids=[],
            )

        self.model.eval()

        # トークン化
        encoded = self.tokenizer.encode(prompt_text, add_special_tokens=False)
        token_ids = torch.tensor([encoded], device=self.device)
        type_ids = torch.full_like(token_ids, 1)  # Any で初期化

        seq_len = token_ids.size(1)
        type_spec = torch.zeros(1, seq_len, dtype=torch.long, device=self.device)
        type_depth = torch.zeros(1, seq_len, dtype=torch.long, device=self.device)

        # 生成中の系列
        gen_tokens = token_ids.clone()
        gen_types = type_ids.clone()
        gen_spec = type_spec.clone()
        gen_depth = type_depth.clone()

        stability_scores: List[float] = []
        error_scores: List[float] = []
        type_counts: Dict[int, int] = {}
        all_diagnostics: Dict[str, Any] = {}

        with torch.no_grad():
            for step in range(max_tokens):
                if gen_tokens.size(1) >= self.max_seq_len:
                    break

                # Forward pass with generation_phase
                outputs = self.model(
                    token_ids=gen_tokens,
                    type_ids=gen_types,
                    type_specificity=gen_spec,
                    type_depth=gen_depth,
                    generation_phase=phase,
                )

                # 次トークンの予測
                token_logits = outputs["logits"][:, -1, :] / temperature

                # 言霊（Kotonodama）の適用
                if kotonodama is not None:
                    last_tid = gen_tokens[0, -1].item() if gen_tokens.size(1) > 0 else None
                    token_logits = kotonodama.apply(token_logits, last_token_id=last_tid)

                next_token = self._sample_top_p(token_logits, top_p)

                # 型の予測
                type_logits = outputs["type_logits"][:, -1, :]
                next_type = torch.argmax(type_logits, dim=-1)

                # エラースコアのチェック
                error_score = outputs["error_score"][:, -1, :].squeeze(-1)
                error_val = error_score.mean().item()

                if error_val > error_threshold:
                    break

                # 診断情報の収集
                diag = outputs.get("diagnostics", {})
                stab_logits = diag.get("stability_logits")
                if stab_logits is not None:
                    stab_pred = stab_logits[:, -1, :].argmax(dim=-1).item()
                    stability_scores.append(float(stab_pred))
                else:
                    stability_scores.append(0.0)

                error_scores.append(error_val)

                # 型分布の集計
                tid = next_type.item()
                type_counts[tid] = type_counts.get(tid, 0) + 1

                # 型メタデータ推定
                next_spec, next_depth = self.model._infer_type_metadata(next_type)

                # 系列に追加
                gen_tokens = torch.cat([gen_tokens, next_token.unsqueeze(1)], dim=1)
                gen_types = torch.cat([gen_types, next_type.unsqueeze(1)], dim=1)
                gen_spec = torch.cat([gen_spec, next_spec.unsqueeze(1)], dim=1)
                gen_depth = torch.cat([gen_depth, next_depth.unsqueeze(1)], dim=1)

                # EOS判定
                if (next_token == self.eos_token_id).all():
                    break

                # 最終ステップの診断情報を保存
                if stab_logits is not None:
                    all_diagnostics["stability_logits"] = stab_logits[:, -1, :].tolist()
                boundary = diag.get("boundary_score")
                if boundary is not None:
                    all_diagnostics["boundary_score"] = boundary[:, -1, :].tolist()

        # デコード
        new_token_ids = gen_tokens[0, seq_len:].tolist()
        text = self.tokenizer.decode(new_token_ids, skip_special_tokens=True)

        return GenerationResult(
            phase=phase,
            text=text,
            token_ids=new_token_ids,
            type_ids=gen_types[0, seq_len:].tolist() if gen_types.size(1) > seq_len else [],
            diagnostics=all_diagnostics,
            stability_scores=stability_scores,
            error_scores=error_scores,
            type_distribution=type_counts,
        )

    def _sample_top_p(
        self,
        logits: "torch.Tensor",
        top_p: float
    ) -> "torch.Tensor":
        """Top-p (nucleus) sampling"""
        sorted_logits, sorted_indices = torch.sort(logits, descending=True)
        cumsum = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)

        mask = cumsum - F.softmax(sorted_logits, dim=-1) > top_p
        sorted_logits[mask] = float("-inf")

        probs = F.softmax(sorted_logits, dim=-1)
        next_token_idx = torch.multinomial(probs, num_samples=1)

        return sorted_indices.gather(-1, next_token_idx).squeeze(-1)

    def _build_pipeline_output(
        self,
        results: List[GenerationResult],
        query: dict,
        context: dict,
    ) -> dict:
        """
        3フェーズの結果を統合してパイプライン出力を構築。
        """
        # テキストを結合
        text_parts = []
        all_type_ids = []
        all_diagnostics: Dict[str, Any] = {}
        all_stability_scores = []
        all_error_scores = []
        all_type_distribution: Dict[int, int] = {}

        for i, result in enumerate(results):
            if result.text.strip():
                phase_name = ["IZANAGI", "IZANAMI", "KAMIYUMI"][result.phase]
                text_parts.append(f"# === Phase {i+1}: {phase_name} ===")
                text_parts.append(result.text.strip())
                text_parts.append("")

            if result.type_ids:
                all_type_ids.extend(result.type_ids)

            all_stability_scores.extend(result.stability_scores)
            all_error_scores.extend(result.error_scores)

            for tid, count in result.type_distribution.items():
                all_type_distribution[tid] = all_type_distribution.get(tid, 0) + count

            # 診断情報をマージ
            for k, v in result.diagnostics.items():
                all_diagnostics[f"phase{i}_{k}"] = v

        # 統計情報を診断に追加
        all_diagnostics["stability_scores"] = all_stability_scores
        all_diagnostics["error_scores"] = all_error_scores
        all_diagnostics["type_distribution"] = all_type_distribution

        return {
            "text": "\n".join(text_parts),
            "query": query,
            "type_ids": all_type_ids if all_type_ids else None,
            "constraints": context.get("constraints"),
            "diagnostics": all_diagnostics,
        }

    def _fallback_generate(self, prompt: str, query: dict) -> dict:
        """
        モデルがない場合のフォールバック生成。
        テスト用にダミー出力を返す。
        """
        return {
            "text": f"# Fallback output for: {prompt[:50]}...",
            "query": query,
            "type_ids": None,
            "constraints": None,
            "diagnostics": {
                "fallback": True,
                "reason": "model_not_available",
            },
        }


# ============================================================
# テスト用ユーティリティ
# ============================================================

def test_ashihara_runtime():
    """葦原中国ランタイムの基本動作テスト"""
    print("=== 葦原中国ランタイムテスト ===\n")

    # モデルなしでのテスト
    runtime = AshiharaRuntime()

    print("【チケット検証テスト】")

    # 有効なチケットで実行
    ticket = TakamiMusubi.grant_forward_pass("attempt_0")
    context = {
        "query": {"prompt": "struct Point2D"},
        "external_context": {},
        "coordinate_axes": AmeNoMinakaNushi.get_all_axes(),
        "origin": AmeNoMinakaNushi.get_all_origins(),
        "safety_status": "ACTIVE",
        "resource_available": True,
    }

    result = runtime.execute_pipeline(context, ticket)
    print(f"  有効チケット: text={result.get('text', '')[:50]}...")
    print(f"  diagnostics: {result.get('diagnostics', {})}")

    # 期限切れチケットをシミュレート（テスト用に即期限切れ）
    print("\n【期限切れチケットテスト】")
    import time
    expired_ticket = ForwardPassTicket(
        ticket_id="expired-test",
        stage="attempt_0",
        granted_by="takami_musubi",
        timestamp=time.time() - 100,  # 100秒前
        expires_in_seconds=30,
    )
    result2 = runtime.execute_pipeline(context, expired_ticket)
    print(f"  期限切れ: error={result2.get('error', 'none')}")

    # 修復ヒント付きテスト
    print("\n【修復ヒント付きテスト】")
    context_with_hints = {
        **context,
        "repair_hints": ["型名をPoint2Dに統一", "フィールドはxとyのFloat64"],
    }
    ticket3 = TakamiMusubi.grant_forward_pass("attempt_1")
    result3 = runtime.execute_pipeline(context_with_hints, ticket3)
    print(f"  ヒント付き生成: {result3.get('text', '')[:80]}...")

    print("\n=== テスト完了 ===")


if __name__ == "__main__":
    test_ashihara_runtime()
