"""
Julia-no-Mikoto: 天の御柱（Amenomihashira）プロトコル

古事記の「国生み」儀式に基づくコード生成パイプライン。

=== 五層アーキテクチャでの役割 ===

AmeNoMihashira（天御柱オーケストレータ）:
  5層の中心軸。全レイヤーの起動・停止・通信を制御。
  「柱を巡る」制御のみを行い、自身は処理しない。

4Phase制御ループ:
  Phase 1: 左旋（イザナミの巡り = 受信フェーズ）
  Phase 2: 右旋（イザナギの巡り = 生成フェーズ）
  Phase 3: 合流（二神の出会い = 評価フェーズ）
  Phase 4: 判定（国生み = 出力フェーズ）

=== 従来の3段階生成（互換性維持） ===

Phase 1 (イザナギ): 型・構造定義のみ生成（struct, abstract type, const）
Phase 2 (イザナミ): 関数シグネチャ生成（function signatures + docstring）
Phase 3 (万物生成): 関数本体の実装生成

ヒルコ検知: Phase 1の出力が型的に不整合な場合、やり直し（高天原への帰還）
直毘神検証: Phase 3完了後の結合整合性チェック

神話的背景:
    最初の国生みでイザナミが先に声をかけたことで、
    骨のないヒルコ（水蛭子）が生まれた。
    → 定義（構造）より先に処理（ロジック）を書くと不具のコードになる。
    高天原に戻り、イザナギ（構造/定義）から先に声をかけることで成功。
    → Top-Down: 型定義 → インターフェース → 実装 の順序を遵守。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING

# torch は AmenomihashiraGenerator（従来API）でのみ使用
# 五層オーケストレータ（AmeNoMihashira）は torch 不要
try:
    import torch
    import torch.nn.functional as F
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    # ダミーモジュールを作成してデコレータエラーを回避
    class _DummyTorch:
        @staticmethod
        def no_grad():
            """torch.no_grad() のダミー実装"""
            def decorator(func):
                return func
            return decorator
        Tensor = None
    torch = _DummyTorch()
    F = None

# 型アノテーション用: torch.Tensor を Any で代替
if TYPE_CHECKING:
    TensorType = "torch.Tensor"
else:
    TensorType = Any

# 直接実行時とモジュールimport時の両方に対応
try:
    from .config import KojikiConfig
except ImportError:
    from kojiki_lm.julia_no_mikoto.config import KojikiConfig


# =============================================================================
# 生成フェーズ定義
# =============================================================================


class GenerationPhase(IntEnum):
    """
    天の御柱の儀式における3段階

    KuniumiLayer.phase_embedding の 0/1/2 に直接対応。
    """
    IZANAGI = 0    # 構造先導: struct, abstract type, const
    IZANAMI = 1    # 実体応答: function signatures
    KAMIYUMI = 2   # 万物生成: implementation (神産み)


# =============================================================================
# Phase結果データクラス
# =============================================================================


@dataclass
class PhaseResult:
    """各Phaseの生成結果"""
    phase: GenerationPhase
    generated_tokens: TensorType       # [batch, seq_len]
    generated_types: TensorType        # [batch, seq_len]
    generated_spec: TensorType         # [batch, seq_len]
    generated_depth: TensorType        # [batch, seq_len]
    type_distribution: Dict[int, int]  # type_id → count
    stability_scores: List[float]      # per-token stability
    error_scores: List[float]          # per-token error scores
    text: str = ""                     # decoded text (set externally)


@dataclass
class HirukoReport:
    """ヒルコ検知レポート"""
    is_hiruko: bool                    # ヒルコ（不具）かどうか
    unknown_ratio: float               # UnknownType(96) の割合
    unstable_ratio: float              # UnstableUnion(97) の割合
    critical_ratio: float              # stability=Critical の割合
    details: str = ""                  # 説明


@dataclass
class NaobiReport:
    """直毘神（結合テスト）レポート"""
    passed: bool                       # 結合テスト合格
    mean_error_score: float            # 平均エラースコア
    type_consistency: float            # Phase1型とPhase3型の一致率
    stability_summary: Dict[str, int]  # {Stable: N, Warning: N, Critical: N}
    details: str = ""


@dataclass
class AmenomihashiraResult:
    """天の御柱プロトコル全体の結果"""
    phase1: PhaseResult                # イザナギ: 型定義
    phase2: PhaseResult                # イザナミ: I/F定義
    phase3: PhaseResult                # 万物生成: 実装
    hiruko_retries: int                # ヒルコ発生回数
    hiruko_reports: List[HirukoReport] # 各リトライのレポート
    naobi_report: NaobiReport          # 直毘神の結合テスト
    final_code: str                    # 最終生成コード（3Phase結合）
    generation_log: Dict = field(default_factory=dict)


# =============================================================================
# ヒルコ検知器
# =============================================================================


class HirukoValidator:
    """
    ヒルコ（水蛭子）検知器

    Phase 1（イザナギ: 型定義生成）の出力が型的に整合しているか検証。
    YomiLayerのstability_logitsとMisogiLayerのtype_logitsを活用。

    不具の子（ヒルコ）判定条件:
      1. UnknownType(96) の割合が閾値超過
      2. UnstableUnion(97) の割合が閾値超過
      3. stability=Critical の割合が50%超過
    """

    TYPE_ID_UNKNOWN = 96
    TYPE_ID_UNSTABLE_UNION = 97

    def __init__(self, config: KojikiConfig):
        self.unknown_threshold = config.hiruko_unknown_threshold
        self.unstable_threshold = config.hiruko_unstable_threshold

    def validate(self, phase_result: PhaseResult) -> HirukoReport:
        """Phase 1の結果を検証"""
        type_dist = phase_result.type_distribution
        total = max(sum(type_dist.values()), 1)

        unknown_count = type_dist.get(self.TYPE_ID_UNKNOWN, 0)
        unstable_count = type_dist.get(self.TYPE_ID_UNSTABLE_UNION, 0)

        unknown_ratio = unknown_count / total
        unstable_ratio = unstable_count / total

        # stability_scoresからCritical率を算出
        # stability: 0=Stable, 1=Warning, 2=Critical
        critical_count = sum(1 for s in phase_result.stability_scores if s >= 1.5)
        critical_ratio = critical_count / max(len(phase_result.stability_scores), 1)

        is_hiruko = (
            unknown_ratio > self.unknown_threshold
            or unstable_ratio > self.unstable_threshold
            or critical_ratio > 0.5
        )

        details_parts = []
        if unknown_ratio > self.unknown_threshold:
            details_parts.append(
                f"UnknownType率 {unknown_ratio:.1%} > 閾値 {self.unknown_threshold:.1%}"
            )
        if unstable_ratio > self.unstable_threshold:
            details_parts.append(
                f"UnstableUnion率 {unstable_ratio:.1%} > 閾値 {self.unstable_threshold:.1%}"
            )
        if critical_ratio > 0.5:
            details_parts.append(f"Critical率 {critical_ratio:.1%} > 50%")

        return HirukoReport(
            is_hiruko=is_hiruko,
            unknown_ratio=unknown_ratio,
            unstable_ratio=unstable_ratio,
            critical_ratio=critical_ratio,
            details="ヒルコ検知: " + "; ".join(details_parts) if is_hiruko
                    else "型整合性OK（国生み成功）",
        )


# =============================================================================
# 直毘神（結合テスト）
# =============================================================================


class NaobiValidator:
    """
    直毘神（なおびのかみ）— 結合整合性検証

    禊（みそぎ）で生まれた直毘神が、穢れ（バグ）を祓う。
    Phase 1で定義した型がPhase 3の実装で正しく使われているかを検証。

    検証項目:
      1. Phase 3のerror_score平均が閾値以下
      2. Phase 1の型定義がPhase 3で参照されている（型一致率）
      3. stability分布が健全
    """

    def __init__(self, config: KojikiConfig):
        self.error_threshold = config.naobi_error_threshold

    def validate(
        self,
        phase1: PhaseResult,
        phase2: PhaseResult,
        phase3: PhaseResult,
    ) -> NaobiReport:
        """3つのPhaseの結合整合性を検証"""

        # 1. Phase 3のエラースコア平均
        mean_error = (
            sum(phase3.error_scores) / max(len(phase3.error_scores), 1)
        )

        # 2. 型一致率: Phase 1で定義された型がPhase 3でも使われているか
        phase1_types = set(phase1.type_distribution.keys())
        phase3_types = set(phase3.type_distribution.keys())
        if phase1_types:
            overlap = phase1_types & phase3_types
            type_consistency = len(overlap) / len(phase1_types)
        else:
            type_consistency = 1.0

        # 3. stability分布の集計
        stability_summary = {"Stable": 0, "Warning": 0, "Critical": 0}
        for s in phase3.stability_scores:
            if s < 0.5:
                stability_summary["Stable"] += 1
            elif s < 1.5:
                stability_summary["Warning"] += 1
            else:
                stability_summary["Critical"] += 1

        passed = (
            mean_error <= self.error_threshold
            and type_consistency >= 0.5
        )

        details = (
            f"禊完了: error={mean_error:.3f}, 型一致率={type_consistency:.1%}, "
            f"安定性={stability_summary}"
        )
        if not passed:
            reasons = []
            if mean_error > self.error_threshold:
                reasons.append(f"error {mean_error:.3f} > {self.error_threshold}")
            if type_consistency < 0.5:
                reasons.append(f"型一致率 {type_consistency:.1%} < 50%")
            details = f"直毘神: 穢れ検出 — {'; '.join(reasons)}"

        return NaobiReport(
            passed=passed,
            mean_error_score=mean_error,
            type_consistency=type_consistency,
            stability_summary=stability_summary,
            details=details,
        )


# =============================================================================
# 天の御柱 生成エンジン
# =============================================================================


class AmenomihashiraGenerator:
    """
    天の御柱（Amenomihashira）プロトコル — 3段階生成エンジン

    古事記の国生み儀式を模した3段階ステートマシン:
      1. イザナギ（構造先導）: struct/type定義のみ生成
      2. イザナミ（実体応答）: 関数シグネチャ生成
      3. 万物生成: 関数本体の実装

    各段階でKuniumiLayerのgeneration_phaseを切り替え、
    モデルの生成バイアスをPhaseに合わせて変化させる。

    稗田阿礼 (Hieda-no-Are):
      有効な場合、各Phase間でREPL形式の「誦習」コンテキスト注入を行う。
      66Mモデルが構造体定義を忘れる問題（例: Point2D→Point3D変異）を防ぐ。
    """

    def __init__(
        self,
        model,  # KojikiLM or KojikiMoE
        tokenizer,
        type_vocab: Dict[int, str],
        device,  # torch.device (型アノテーションは torch 依存を避ける)
        config: Optional[KojikiConfig] = None,
        enable_hieda_no_are: bool = True,
    ):
        if not HAS_TORCH:
            raise RuntimeError(
                "AmenomihashiraGenerator requires PyTorch. "
                "Use AmeNoMihashira (五層オーケストレータ) for torch-free operation."
            )
        self.model = model
        self.tokenizer = tokenizer
        self.type_vocab = type_vocab
        self.device = device
        self.config = config or model.config

        self.hiruko_validator = HirukoValidator(self.config)
        self.naobi_validator = NaobiValidator(self.config)

        # 稗田阿礼 (外部コンテキスト管理)
        self.hieda_no_are = None
        if enable_hieda_no_are:
            from .hieda_no_are import HiedaNoAre
            max_ctx = getattr(
                self.config, 'hieda_no_are_max_context_tokens', 512
            )
            self.hieda_no_are = HiedaNoAre(
                tokenizer=tokenizer,
                max_context_tokens=max_ctx,
            )

    @torch.no_grad()
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 0.9,
        error_threshold: float = 0.8,
    ) -> AmenomihashiraResult:
        """
        天の御柱プロトコルによる3段階生成

        Args:
            prompt: 生成指示（例: "HTTP server with routing"）
            temperature: サンプリング温度
            top_p: Nucleus samplingの閾値
            error_threshold: 黄泉行き判定の閾値

        Returns:
            AmenomihashiraResult: 3段階の生成結果 + 検証レポート
        """
        self.model.eval()
        gen_params = {
            "temperature": temperature,
            "top_p": top_p,
            "error_threshold": error_threshold,
        }

        # 稗田阿礼: セッションリセット & ユーザープロンプトの定義を記憶
        if self.hieda_no_are:
            self.hieda_no_are.reset()
            self.hieda_no_are.memorize_prompt(prompt)

        # ============================================================
        # Phase 1: イザナギ — 型・構造定義（柱を建てる）
        # ============================================================
        hiruko_reports: List[HirukoReport] = []
        phase1_result = None

        # 阿礼あり: REPL形式プロンプトに変換
        phase1_prompt = prompt
        if self.hieda_no_are:
            # REPL形式化: MoEモデルが理解できる形式にする
            lines = prompt.split('\n')
            if not prompt.strip().startswith('julia>'):
                phase1_prompt = 'julia> ' + lines[0] + '\n' + '\n'.join(lines[1:])

        for retry in range(self.config.amenomihashira_max_retries + 1):
            phase1_result = self._phase_generate(
                prompt_text=phase1_prompt,
                phase=GenerationPhase.IZANAGI,
                max_tokens=self.config.phase1_max_tokens,
                context_tokens=None,
                context_types=None,
                **gen_params,
            )

            report = self.hiruko_validator.validate(phase1_result)
            hiruko_reports.append(report)

            if not report.is_hiruko:
                break
            # ヒルコ発生: 高天原に帰還してやり直し（温度を少し上げる）
            gen_params["temperature"] = min(
                gen_params["temperature"] + 0.1, 1.2
            )

        hiruko_retries = len(hiruko_reports) - 1

        # 阿礼: Phase 1 の出力を記憶
        if self.hieda_no_are:
            self.hieda_no_are.memorize_output(phase1_result.text, phase=0)

        # ============================================================
        # Phase 2: イザナミ — 関数シグネチャ（国を産む）
        # ============================================================
        if self.hieda_no_are:
            # 阿礼が Phase 1 の定義を誦習 → REPL形式コンテキスト構築
            phase2_prompt = self.hieda_no_are.build_recitation(
                target_phase=1,
                generation_prompt="julia> ",
            )
            phase2_result = self._phase_generate(
                prompt_text=phase2_prompt,
                phase=GenerationPhase.IZANAMI,
                max_tokens=self.config.phase2_max_tokens,
                context_tokens=None,
                context_types=None,
                **gen_params,
            )
        else:
            # フォールバック: 従来のテンソルベースコンテキスト
            phase2_result = self._phase_generate(
                prompt_text=prompt,
                phase=GenerationPhase.IZANAMI,
                max_tokens=self.config.phase2_max_tokens,
                context_tokens=phase1_result.generated_tokens,
                context_types=phase1_result.generated_types,
                **gen_params,
            )

        # 阿礼: Phase 2 の出力を記憶
        if self.hieda_no_are:
            self.hieda_no_are.memorize_output(phase2_result.text, phase=1)

        # ============================================================
        # Phase 3: 万物生成 — 関数本体（神々を産む）
        # ============================================================
        if self.hieda_no_are:
            # 阿礼が Phase 1+2 の全定義を誦習 → REPL形式コンテキスト構築
            phase3_prompt = self.hieda_no_are.build_recitation(
                target_phase=2,
                generation_prompt="julia> ",
            )
            phase3_result = self._phase_generate(
                prompt_text=phase3_prompt,
                phase=GenerationPhase.KAMIYUMI,
                max_tokens=self.config.phase3_max_tokens,
                context_tokens=None,
                context_types=None,
                **gen_params,
            )
        else:
            # フォールバック: 従来のテンソル結合コンテキスト
            combined_tokens = torch.cat([
                phase1_result.generated_tokens,
                phase2_result.generated_tokens[:, phase1_result.generated_tokens.size(1):],
            ], dim=1)
            combined_types = torch.cat([
                phase1_result.generated_types,
                phase2_result.generated_types[:, phase1_result.generated_types.size(1):],
            ], dim=1)

            phase3_result = self._phase_generate(
                prompt_text=prompt,
                phase=GenerationPhase.KAMIYUMI,
                max_tokens=self.config.phase3_max_tokens,
                context_tokens=combined_tokens,
                context_types=combined_types,
                **gen_params,
            )

        # ============================================================
        # 直毘神: 結合テスト（禊）
        # ============================================================
        naobi_report = self.naobi_validator.validate(
            phase1_result, phase2_result, phase3_result
        )

        # 最終コードの構築
        final_code = self._build_final_code(
            phase1_result, phase2_result, phase3_result
        )

        return AmenomihashiraResult(
            phase1=phase1_result,
            phase2=phase2_result,
            phase3=phase3_result,
            hiruko_retries=hiruko_retries,
            hiruko_reports=hiruko_reports,
            naobi_report=naobi_report,
            final_code=final_code,
            generation_log={
                "prompt": prompt,
                "temperature": temperature,
                "top_p": top_p,
                "error_threshold": error_threshold,
                "hiruko_retries": hiruko_retries,
                "naobi_passed": naobi_report.passed,
            },
        )

    def _phase_generate(
        self,
        prompt_text: str,
        phase: GenerationPhase,
        max_tokens: int,
        context_tokens: Optional[torch.Tensor],
        context_types: Optional[torch.Tensor],
        temperature: float = 0.7,
        top_p: float = 0.9,
        error_threshold: float = 0.8,
    ) -> PhaseResult:
        """
        単一Phaseの生成を実行

        generation_phaseをKuniumiLayerに渡すことで、
        Phase固有の生成バイアスが適用される。
        """
        # エンコード: コンテキストがあれば先頭に配置
        if context_tokens is not None and context_types is not None:
            token_ids = context_tokens
            type_ids = context_types
        else:
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

        for step in range(max_tokens):
            if gen_tokens.size(1) >= self.config.max_seq_len:
                break

            # Forward pass with generation_phase
            outputs = self.model(
                token_ids=gen_tokens,
                type_ids=gen_types,
                type_specificity=gen_spec,
                type_depth=gen_depth,
                generation_phase=int(phase),  # KuniumiLayerへ伝達
            )

            # 天照: 次トークン
            token_logits = outputs["logits"][:, -1, :] / temperature

            # 言霊 (Kotonodama): 阿礼が記憶した定義名のlogitsを文脈依存ブースト
            if self.hieda_no_are:
                # 直前トークンIDを取得 (文脈依存型で使用)
                last_tid = gen_tokens[0, -1].item() if gen_tokens.size(1) > 0 else None
                kotonodama = self.hieda_no_are.get_contextual_kotonodama()
                if kotonodama is not None:
                    token_logits = kotonodama.apply(token_logits, last_token_id=last_tid)

            next_token = self._sample_top_p(token_logits, top_p)

            # 月読: 次トークンの型
            type_logits = outputs["type_logits"][:, -1, :]
            next_type = torch.argmax(type_logits, dim=-1)

            # 須佐之男: エラーチェック
            error_score = outputs["error_score"][:, -1, :].squeeze(-1)
            error_val = error_score.mean().item()

            if error_val > error_threshold:
                break

            # stability（黄泉国）
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
            if (next_token == self.config.eos_token_id).all():
                break

        # デコード
        new_token_ids = gen_tokens[0, seq_len:].tolist()
        text = self.tokenizer.decode(new_token_ids, skip_special_tokens=True)

        result = PhaseResult(
            phase=phase,
            generated_tokens=gen_tokens,
            generated_types=gen_types,
            generated_spec=gen_spec,
            generated_depth=gen_depth,
            type_distribution=type_counts,
            stability_scores=stability_scores,
            error_scores=error_scores,
            text=text,
        )
        return result

    def _sample_top_p(
        self, logits: torch.Tensor, top_p: float
    ) -> torch.Tensor:
        """Top-p (nucleus) sampling"""
        sorted_logits, sorted_indices = torch.sort(logits, descending=True)
        cumsum = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)

        mask = cumsum - F.softmax(sorted_logits, dim=-1) > top_p
        sorted_logits[mask] = float("-inf")

        probs = F.softmax(sorted_logits, dim=-1)
        next_token_idx = torch.multinomial(probs, num_samples=1)

        return sorted_indices.gather(-1, next_token_idx).squeeze(-1)

    def _build_final_code(
        self,
        phase1: PhaseResult,
        phase2: PhaseResult,
        phase3: PhaseResult,
    ) -> str:
        """3つのPhase出力を結合して最終コードを構築"""
        parts = []

        if phase1.text.strip():
            parts.append(f"# === Phase 1: 型定義（イザナギ） ===")
            parts.append(phase1.text.strip())
            parts.append("")

        if phase2.text.strip():
            parts.append(f"# === Phase 2: インターフェース（イザナミ） ===")
            parts.append(phase2.text.strip())
            parts.append("")

        if phase3.text.strip():
            parts.append(f"# === Phase 3: 実装（万物生成） ===")
            parts.append(phase3.text.strip())

        return "\n".join(parts)


# =============================================================================
# 4Phase オーケストレータ（五層アーキテクチャ用）
# =============================================================================


class PipelinePhase(IntEnum):
    """
    天御柱プロトコルの4フェーズ

    古事記の天御柱エピソード:
    - 左旋（イザナミ = 受信）: 外部データの取得
    - 右旋（イザナギ = 生成）: 実際の推論実行
    - 合流（二神の出会い）: 評価・判定
    - 判定（国生み）: 出力確定 or 修復 or 停止
    """
    HIDARI_MAWARI = 0  # 左旋: 受信フェーズ
    MIGI_MAWARI = 1    # 右旋: 生成フェーズ
    GOURYU = 2         # 合流: 評価フェーズ
    HANTEI = 3         # 判定: 出力フェーズ


@dataclass
class PipelineResult:
    """
    天御柱オーケストレータの実行結果

    Attributes:
        status: "COMMIT" | "HALT" | "REJECTED"
        output: 最終出力テキスト（COMMIT時のみ）
        quality_score: 品質スコア（0.0〜1.0）
        repair_count: 修復回数
        reason: 停止理由（HALT / REJECTED時）
        execution_log: 実行ログ（デバッグ用）
    """
    status: str
    output: Optional[str] = None
    quality_score: float = 0.0
    repair_count: int = 0
    reason: Optional[str] = None
    execution_log: Dict = field(default_factory=dict)


class AmeNoMihashira:
    """
    天御柱（AmeNoMihashira）オーケストレータ

    5層の中心軸として、全レイヤーの起動・停止・通信を制御。
    自身は処理しない。「柱を巡る」制御のみ。

    古事記の天御柱:
        イザナギとイザナミが「左右に分かれて巡り合う」ための中心軸。
        分離したプロセスが合流するための座標軸。

    設計原則:
    - 左旋（受信）が先、右旋（生成）が後
      → コンテキストを十分に構築してから生成に入る
      → この順序を守らないと蛭子（不正出力）が生まれる
    - 評価はLayer 5（黄泉）に委譲
    - 修復権限はカミムスビから取得

    Args:
        layer3: AshiharaRuntime（推論ランタイム）
        layer4: HiedaNoAre（外部データブリッジ）
        layer5: YomotsuHirasaka（評価ゲートウェイ）
    """

    def __init__(
        self,
        layer3=None,  # AshiharaRuntime
        layer4=None,  # HiedaNoAre
        layer5=None,  # YomotsuHirasaka
    ):
        self.layer3 = layer3
        self.layer4 = layer4
        self.layer5 = layer5

        # 遅延インポート（循環参照回避）
        self._zoka_sanshin_imported = False

    def _ensure_imports(self):
        """必要なモジュールを遅延インポート"""
        if not self._zoka_sanshin_imported:
            # 直接実行時とモジュールimport時の両方に対応
            try:
                from kojiki_lm.julia_no_mikoto.zoka_sanshin import (
                    AmeNoMinakaNushi,
                    TakamiMusubi,
                    KamiMusubi,
                )
            except ImportError:
                from .zoka_sanshin import (
                    AmeNoMinakaNushi,
                    TakamiMusubi,
                    KamiMusubi,
                )
            self._AmeNoMinakaNushi = AmeNoMinakaNushi
            self._TakamiMusubi = TakamiMusubi
            self._KamiMusubi = KamiMusubi
            self._zoka_sanshin_imported = True

    def execute(self, query: dict) -> PipelineResult:
        """
        天御柱プロトコル: 左旋 → 右旋 → 合流 → 判定

        Parameters:
            query: 推論リクエスト
                - prompt: str (必須)
                - constraints: dict (オプション)
                - temperature: float (オプション)
                - top_p: float (オプション)

        Returns:
            PipelineResult: 実行結果
        """
        self._ensure_imports()
        execution_log: Dict = {"phases": []}

        # === Phase 1: 左旋（受信） ===
        context = self._hidari_mawari(query)
        execution_log["phases"].append({
            "phase": "hidari_mawari",
            "status": "completed",
            "context_keys": list(context.keys()),
        })

        # 座標系パラメータの取得
        budget = self._AmeNoMinakaNushi.get_origin("repair_budget")
        repair_count = 0

        # === Phase 2-4: 生成→評価→判定ループ ===
        while repair_count <= budget:
            # === Phase 2: 右旋（生成） ===
            if not self._TakamiMusubi.authorize_generation(context):
                return PipelineResult(
                    status="REJECTED",
                    reason="generation_not_authorized",
                    execution_log=execution_log,
                )

            ticket = self._TakamiMusubi.grant_forward_pass(f"attempt_{repair_count}")
            output = self._migi_mawari(context, ticket)

            execution_log["phases"].append({
                "phase": "migi_mawari",
                "attempt": repair_count,
                "output_length": len(output.get("text", "")),
            })

            # === Phase 3: 合流（評価） ===
            evaluation = self._gouryu(output)

            execution_log["phases"].append({
                "phase": "gouryu",
                "verdict": evaluation.get("verdict"),
                "quality_score": evaluation.get("quality_score"),
            })

            # === Phase 4: 判定 ===
            verdict = evaluation.get("verdict", "HALT")

            if verdict == "COMMIT":
                return PipelineResult(
                    status="COMMIT",
                    output=output.get("text", ""),
                    quality_score=evaluation.get("quality_score", 0.0),
                    repair_count=repair_count,
                    execution_log=execution_log,
                )

            if verdict == "HALT":
                return PipelineResult(
                    status="HALT",
                    reason="quality_below_threshold",
                    quality_score=evaluation.get("quality_score", 0.0),
                    repair_count=repair_count,
                    execution_log=execution_log,
                )

            # REPAIR: カミムスビに修復権限を問う
            repair_auth = self._KamiMusubi.authorize_repair({
                "repair_count": repair_count,
                "hints": evaluation.get("repair_hints", []),
            })

            if repair_auth.action == "HALT":
                return PipelineResult(
                    status="HALT",
                    reason="repair_budget_exhausted",
                    repair_count=repair_count,
                    execution_log=execution_log,
                )

            # 修復ヒントをコンテキストに注入して再試行
            context["repair_hints"] = evaluation.get("repair_hints", [])
            repair_count += 1

            execution_log["phases"].append({
                "phase": "repair",
                "attempt": repair_count,
                "remaining_budget": repair_auth.remaining_budget,
            })

        return PipelineResult(
            status="HALT",
            reason="max_iterations_exceeded",
            repair_count=repair_count,
            execution_log=execution_log,
        )

    def _hidari_mawari(self, query: dict) -> dict:
        """
        Phase 1: 左旋（イザナミの巡り）

        外部データの取得とコンテキスト構築。
        古事記で「受信が先」でなければ蛭子が生まれるという原則。

        Parameters:
            query: 元のリクエスト

        Returns:
            dict: 生成フェーズ用のコンテキスト
        """
        self._ensure_imports()

        # Layer 4 → 稗田阿礼 → コンテキスト注入
        external_data = {}
        if self.layer4 is not None:
            external_data = self.layer4.fetch_and_contextualize(query)

        return {
            "query": query,
            "external_context": external_data,
            "coordinate_axes": self._AmeNoMinakaNushi.get_all_axes(),
            "origin": self._AmeNoMinakaNushi.get_all_origins(),
            "safety_status": "ACTIVE",
            "resource_available": True,
        }

    def _migi_mawari(self, context: dict, ticket) -> dict:
        """
        Phase 2: 右旋（イザナギの巡り）

        推論実行。天の御柱 Stage 1-3。

        Parameters:
            context: 左旋で構築したコンテキスト
            ticket: ForwardPassTicket

        Returns:
            dict: 出力候補（黄泉比良坂に送る形式）
        """
        if self.layer3 is None:
            # フォールバック: ダミー出力
            return {
                "text": f"# Fallback: {context.get('query', {}).get('prompt', '')}",
                "query": context.get("query"),
                "diagnostics": {"fallback": True},
            }

        return self.layer3.execute_pipeline(context, ticket)

    def _gouryu(self, output: dict) -> dict:
        """
        Phase 3: 合流（二神の出会い）

        出力をLayer 5に送って評価を受ける。
        黄泉比良坂越しの通信。

        Parameters:
            output: 右旋の出力

        Returns:
            dict: 評価結果
                - verdict: "COMMIT" | "REPAIR" | "HALT"
                - repair_hints: List[str]
                - quality_score: float
        """
        if self.layer5 is None:
            # フォールバック: 常にCOMMIT
            return {
                "verdict": "COMMIT",
                "repair_hints": [],
                "quality_score": 0.8,
            }

        return self.layer5.send_for_evaluation(output)


# =============================================================================
# テスト用ユーティリティ
# =============================================================================

def test_amenomihashira_orchestrator():
    """天御柱オーケストレータの基本動作テスト"""
    print("=== 天御柱オーケストレータテスト ===\n")

    # 依存なしでのテスト（フォールバックモード）
    orchestrator = AmeNoMihashira()

    print("【基本実行テスト】")
    result = orchestrator.execute({
        "prompt": "struct Point2D",
    })
    print(f"  status: {result.status}")
    print(f"  output: {result.output[:50] if result.output else 'None'}...")
    print(f"  quality_score: {result.quality_score}")
    print(f"  repair_count: {result.repair_count}")

    print("\n【実行ログ確認】")
    for phase in result.execution_log.get("phases", []):
        print(f"  - {phase.get('phase')}: {phase}")

    print("\n=== テスト完了 ===")


if __name__ == "__main__":
    test_amenomihashira_orchestrator()
