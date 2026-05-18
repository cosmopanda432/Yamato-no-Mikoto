"""
yomi_evaluator.py — Layer 5: 根の国・黄泉（評価・フィードバック）

推論出力の評価を担当。
Layer 3とは黄泉比良坂（EvaluationGateway）越しに通信。

構成:
- HirukoDetector: 蛭子検知器（4軸評価）
- EnmaGate: 閻魔判定（COMMIT/REPAIR/HALT）
- YomiArchive: フィードバック蓄積

注意:
- layers.py の YomiLayer（モデル内部層）とは異なる責務
- YomiLayer: モデル内部でリアルタイムに型安定性を検出
- YomiEvaluator: パイプラインで事後に出力候補の品質を総合評価
- YomiEvaluatorはYomiLayerの出力（stability_logits, boundary_score）を入力として使用
"""

from __future__ import annotations
import math
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from collections import deque
from enum import Enum

# 直接実行時とモジュールimport時の両方に対応
try:
    from .zoka_sanshin import AmeNoMinakaNushi
except ImportError:
    from kojiki_lm.julia_no_mikoto.zoka_sanshin import AmeNoMinakaNushi


# ============================================================
# 蛭子検知器（Hiruko Detector）
# ============================================================

@dataclass
class HirukoReport:
    """蛭子検知の結果レポート"""
    stability: float          # 0.0〜1.0 (1.0=完全安定)
    boundary: float           # 0.0〜1.0 (1.0=完全準拠)
    hallucination: float      # 0.0〜1.0 (0.0=幻覚なし)
    coherence: float          # 0.0〜1.0 (1.0=完全一貫)
    details: Dict[str, Any] = field(default_factory=dict)


class HirukoDetector:
    """
    蛭子検知器。
    出力候補の品質を多角的に評価する。

    既存のHirukoValidatorとの関係:
    - HirukoValidator（amenomihashira.py内）:
      型IDベースの蛭子検知（モデル出力のtype_idsを直接見る）
      Phase 1実行中のリアルタイム検知
    - HirukoDetector（本クラス）:
      テキスト+logitsベースの総合評価（Layer 5の責務）
      Phase完了後の事後評価

    両者は補完的に動作する。
    """

    def __init__(self):
        # Julia構文パターン（境界チェック用）
        self._julia_struct_pattern = re.compile(
            r'(?:mutable\s+)?struct\s+\w+', re.MULTILINE
        )
        self._julia_function_pattern = re.compile(
            r'function\s+\w+', re.MULTILINE
        )
        self._julia_end_pattern = re.compile(r'^\s*end\s*$', re.MULTILINE)

    def detect(self, candidate: dict) -> HirukoReport:
        """
        出力候補に対して蛭子検知を実行。

        Parameters:
            candidate: 以下のキーを含むdict
                - text: str (生成されたコード)
                - logits: List[List[float]] (各トークンのlogit分布、オプション)
                - query: dict (元のリクエスト)
                - type_ids: List[int] (型IDシーケンス、オプション)
                - constraints: dict (長さ・フォーマット制約、オプション)
                - diagnostics: dict (YomiLayerの出力、オプション)

        Returns:
            HirukoReport: 4軸の評価結果
        """
        stability = self._compute_stability(candidate)
        boundary = self._compute_boundary(candidate)
        hallucination = self._compute_hallucination(candidate)
        coherence = self._compute_coherence(candidate)

        return HirukoReport(
            stability=stability,
            boundary=boundary,
            hallucination=hallucination,
            coherence=coherence,
            details={
                "text_length": len(candidate.get("text", "")),
                "has_logits": "logits" in candidate,
                "has_type_ids": "type_ids" in candidate,
                "has_diagnostics": "diagnostics" in candidate,
            },
        )

    def _compute_stability(self, candidate: dict) -> float:
        """
        logit分布の安定性を計算。
        高エントロピー = 不安定 = 蛭子的。

        優先順位:
        1. YomiLayer の stability_logits（モデル出力）があれば使用
        2. なければ logits からエントロピー計算
        3. それもなければテキストベースのヒューリスティック
        """
        # YomiLayerの出力を優先使用
        diagnostics = candidate.get("diagnostics", {})
        stability_probs = diagnostics.get("stability_probs")

        if stability_probs is not None:
            # stability_probs: [Stable=0, Warning=1, Critical=2]
            # torch.Tensorの場合の処理
            try:
                if hasattr(stability_probs, 'mean'):
                    # PyTorch Tensor
                    stable_prob = stability_probs[..., 0].mean().item()
                else:
                    # numpy array or list
                    import numpy as np
                    arr = np.array(stability_probs)
                    stable_prob = arr[..., 0].mean()
                return float(stable_prob)
            except (IndexError, TypeError):
                pass

        # logitsベースの安定性計算
        logits = candidate.get("logits")
        if logits and len(logits) > 0:
            entropies = []
            for logit_dist in logits:
                if not logit_dist or len(logit_dist) == 0:
                    continue
                # softmax
                max_l = max(logit_dist)
                exp_l = [math.exp(l - max_l) for l in logit_dist]
                sum_exp = sum(exp_l)
                if sum_exp == 0:
                    continue
                probs = [e / sum_exp for e in exp_l]
                # entropy
                entropy = -sum(p * math.log(p) for p in probs if p > 0)
                max_entropy = math.log(len(logit_dist))
                if max_entropy > 0:
                    entropies.append(1.0 - (entropy / max_entropy))

            if entropies:
                return sum(entropies) / len(entropies)

        # テキストベースのフォールバック
        return self._text_based_stability(candidate.get("text", ""))

    def _text_based_stability(self, text: str) -> float:
        """テキストベースの安定性ヒューリスティック"""
        if not text:
            return 0.0

        score = 1.0

        # 同じ行の連続繰り返し検出
        lines = text.strip().split("\n")
        if len(lines) >= 3:
            repeats = 0
            for i in range(1, len(lines)):
                if lines[i].strip() == lines[i-1].strip() and lines[i].strip():
                    repeats += 1
            repeat_ratio = repeats / len(lines)
            score -= repeat_ratio * 0.5

        # end の不一致検出
        openers = len(re.findall(
            r'\b(struct|function|if|for|while|begin|let|do|module)\b', text
        ))
        closers = len(self._julia_end_pattern.findall(text))
        if openers > 0:
            balance = abs(openers - closers) / openers
            score -= min(balance * 0.3, 0.3)

        return max(0.0, min(1.0, score))

    def _compute_boundary(self, candidate: dict) -> float:
        """
        出力がシステム境界を逸脱していないか評価。

        チェック項目:
        - safety: 危険なパターンの検出
        - topic_adherence: クエリとの関連性
        - length_compliance: 長さ制約の準拠
        - format_compliance: フォーマット制約の準拠
        """
        text = candidate.get("text", "")
        query = candidate.get("query", {}) or {}
        constraints = candidate.get("constraints", {}) or {}

        # YomiLayerのboundary_scoreがあれば参考にする
        diagnostics = candidate.get("diagnostics", {})
        model_boundary = diagnostics.get("boundary_score")

        scores = {}

        # safety check
        unsafe_patterns = [
            r'rm\s+-rf\s+/',
            r'eval\s*\(',
            r'@ccall.*unsafe',
            r'Base\.invokelatest',
            r'include\s*\(\s*"/',
        ]
        safety_score = 1.0
        for pattern in unsafe_patterns:
            if re.search(pattern, text):
                safety_score -= 0.3
        scores["safety"] = max(0.0, safety_score)

        # topic adherence（クエリのキーワードが出力に含まれるか）
        prompt = query.get("prompt", "") if isinstance(query, dict) else str(query)
        if prompt:
            keywords = set(re.findall(r'\b\w{3,}\b', prompt.lower()))
            text_words = set(re.findall(r'\b\w{3,}\b', text.lower()))
            if keywords:
                overlap = len(keywords & text_words) / len(keywords)
                scores["topic"] = min(1.0, overlap * 2)  # 半分以上で満点
            else:
                scores["topic"] = 1.0
        else:
            scores["topic"] = 1.0

        # length compliance
        max_len = constraints.get("max_length")
        if max_len and len(text) > max_len:
            scores["length"] = max_len / len(text)
        else:
            scores["length"] = 1.0

        # format compliance（Juliaコードとして最低限の構文を持つか）
        has_julia = bool(
            self._julia_struct_pattern.search(text)
            or self._julia_function_pattern.search(text)
            or re.search(r'\b(const|let|for|if|while)\b', text)
        )
        scores["format"] = 1.0 if has_julia else 0.5

        # モデルのboundary_scoreがあれば加味
        if model_boundary is not None:
            try:
                if hasattr(model_boundary, 'mean'):
                    model_score = model_boundary.mean().item()
                else:
                    model_score = float(model_boundary)
                scores["model_boundary"] = model_score
            except (TypeError, AttributeError):
                pass

        return min(scores.values())

    def _compute_hallucination(self, candidate: dict) -> float:
        """
        幻覚度を計算。0.0=幻覚なし、1.0=完全幻覚。

        検出パターン:
        - 未定義の型・変数への参照
        - 存在しないJulia標準ライブラリ関数の使用
        - コンテキストで定義されていない識別子の使用
        """
        text = candidate.get("text", "")
        query = candidate.get("query", {})

        if not text:
            return 1.0  # 空出力は完全幻覚

        score = 0.0

        # 存在しないJulia関数の参照検出
        # （軽量なヒューリスティック: 明らかに不正なパターンのみ）
        fake_patterns = [
            r'\bPython\.',           # Pythonモジュール参照
            r'\bimport\s+\w+',       # Pythonスタイルのimport
            r'\bself\.',             # Pythonスタイルのself
            r'\bclass\s+\w+',        # Pythonスタイルのclass
            r'\bdef\s+\w+\s*\(',     # Pythonスタイルの関数定義
            r'\b__init__\b',         # Python特有
            r'\bprint\s*\(',         # printはJuliaでは println
        ]
        for pattern in fake_patterns:
            if re.search(pattern, text):
                score += 0.15

        # クエリで指定された型名と異なる型名の使用を検出
        prompt = query.get("prompt", "") if isinstance(query, dict) else str(query)
        if prompt:
            # プロンプトからstruct名を抽出
            expected_structs = set(re.findall(
                r'struct\s+(\w+)', prompt
            ))
            # 出力からstruct名を抽出
            actual_structs = set(re.findall(
                r'struct\s+(\w+)', text
            ))
            # プロンプトにない型名が出力に含まれている場合
            unexpected = actual_structs - expected_structs
            if expected_structs and unexpected:
                score += 0.2 * len(unexpected) / max(len(actual_structs), 1)

        return min(1.0, score)

    def _compute_coherence(self, candidate: dict) -> float:
        """
        一貫性スコアを計算。1.0=完全一貫。

        チェック項目:
        - 定義された変数/型が実際に使用されているか
        - スコープの一貫性
        """
        text = candidate.get("text", "")
        if not text:
            return 0.0

        score = 1.0

        # struct定義→使用の一貫性
        defined_structs = set(re.findall(r'struct\s+(\w+)', text))
        for struct_name in defined_structs:
            # 定義以外で使用されているか
            uses = len(re.findall(
                rf'\b{struct_name}\b', text
            )) - 1  # 定義自体を除く
            if uses <= 0:
                score -= 0.1  # 定義したが未使用

        # function定義→呼び出しの一貫性
        # 関数は定義だけでもOK（外部から呼ばれる想定）

        # フィールドの型一貫性
        # struct内で定義された型が実際に存在するか
        field_types = re.findall(r'::\s*(\w+)', text)
        julia_builtin_types = {
            'Int', 'Int8', 'Int16', 'Int32', 'Int64', 'Int128',
            'UInt', 'UInt8', 'UInt16', 'UInt32', 'UInt64', 'UInt128',
            'Float16', 'Float32', 'Float64',
            'Bool', 'Char', 'String', 'Symbol',
            'Any', 'Nothing', 'Missing',
            'Vector', 'Array', 'Matrix', 'Dict', 'Set', 'Tuple',
            'Function', 'Type', 'DataType',
        }
        for ft in field_types:
            if ft not in julia_builtin_types and ft not in defined_structs:
                # 未定義の型を参照している可能性
                # ただし外部で定義されている可能性もあるので軽いペナルティ
                score -= 0.05

        return max(0.0, min(1.0, score))


# ============================================================
# 閻魔判定（Enma Gate）
# ============================================================

class Verdict(Enum):
    """判定結果"""
    COMMIT = "COMMIT"   # 出力確定（国が生まれた）
    REPAIR = "REPAIR"   # 修復要求（直毘神に委ねる）
    HALT   = "HALT"     # 停止（蛭子 = 不正出力を流す）


@dataclass
class EnmaVerdict:
    """閻魔判定の結果"""
    verdict: Verdict
    v_score: float                       # 0.0〜1.0
    repair_hints: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)


class EnmaGate:
    """
    閻魔 = 最終判定。
    全メトリクスを集約してverdictを出す。

    重み付け:
    - stability:    0.3 （不安定な出力を最も重くペナルティ）
    - boundary:     0.3 （境界逸脱も同等に重い）
    - coherence:    0.2 （一貫性は中程度）
    - hallucination: 0.2 （幻覚は反転して加算）
    """

    # V scoreの重み（合計1.0）
    WEIGHTS = {
        "stability": 0.3,
        "boundary": 0.3,
        "coherence": 0.2,
        "hallucination": 0.2,  # 1.0 - hallucination として加算
    }

    def judge(self, report: HirukoReport) -> EnmaVerdict:
        """
        蛭子検知レポートを受けて最終判定を下す。

        判定ロジック:
        1. stability < stability_floor → 即HALT
        2. boundary <= safety_floor → 即HALT
        3. V score >= V_threshold → COMMIT
        4. それ以外 → REPAIR（修復ヒント付き）
        """
        origin = AmeNoMinakaNushi.get_all_origins()

        # 即HALT条件
        if report.stability < origin["stability_floor"]:
            return EnmaVerdict(
                verdict=Verdict.HALT,
                v_score=0.0,
                metrics=self._to_metrics(report),
            )

        if report.boundary < origin["safety_floor"]:
            return EnmaVerdict(
                verdict=Verdict.HALT,
                v_score=0.0,
                metrics=self._to_metrics(report),
            )

        # V score計算
        v_score = (
            report.stability * self.WEIGHTS["stability"]
            + report.boundary * self.WEIGHTS["boundary"]
            + report.coherence * self.WEIGHTS["coherence"]
            + (1.0 - report.hallucination) * self.WEIGHTS["hallucination"]
        )

        metrics = self._to_metrics(report)
        metrics["v_score"] = v_score

        # COMMIT判定
        if v_score >= origin["V_threshold"]:
            return EnmaVerdict(
                verdict=Verdict.COMMIT,
                v_score=v_score,
                metrics=metrics,
            )

        # REPAIR（修復ヒント生成）
        hints = self._generate_repair_hints(report)
        return EnmaVerdict(
            verdict=Verdict.REPAIR,
            v_score=v_score,
            repair_hints=hints,
            metrics=metrics,
        )

    def _generate_repair_hints(self, report: HirukoReport) -> List[str]:
        """メトリクスの低い項目に基づいて修復ヒントを生成"""
        hints = []
        if report.stability < 0.5:
            hints.append("stability_low: 繰り返しパターンまたは未閉じ構文を検出")
        if report.boundary < 0.5:
            hints.append("boundary_violation: トピック逸脱または安全性問題")
        if report.hallucination > 0.3:
            hints.append("hallucination_detected: 未定義の参照または言語混在")
        if report.coherence < 0.5:
            hints.append("coherence_low: 定義-使用の不一致")
        return hints

    def _to_metrics(self, report: HirukoReport) -> Dict[str, float]:
        return {
            "stability": report.stability,
            "boundary": report.boundary,
            "hallucination": report.hallucination,
            "coherence": report.coherence,
        }


# ============================================================
# Yomi Archive（フィードバック蓄積）
# ============================================================

@dataclass
class YomiRecord:
    """黄泉の記録1件"""
    timestamp: float
    verdict: str
    v_score: float
    metrics: Dict[str, float]
    repair_hints: List[str]
    text_length: int


class YomiArchive:
    """
    Layer 5内部のフィードバック蓄積。
    Layer 3には直接公開しない（千引の岩）。
    Layer 2（学習パイプライン）への長期フィードバック用。

    保持上限: max_records件（古い記録から消去）
    """

    def __init__(self, max_records: int = 1000):
        self._records: deque[YomiRecord] = deque(maxlen=max_records)

    def archive(self, verdict: EnmaVerdict, text_length: int) -> None:
        """評価結果をアーカイブに追加"""
        self._records.append(YomiRecord(
            timestamp=time.time(),
            verdict=verdict.verdict.value,
            v_score=verdict.v_score,
            metrics=verdict.metrics,
            repair_hints=verdict.repair_hints,
            text_length=text_length,
        ))

    def get_session_stats(self) -> Dict[str, Any]:
        """
        現セッションの統計を返す。
        Layer 2へのフィードバック用。
        """
        if not self._records:
            return {"total": 0}

        verdicts = [r.verdict for r in self._records]
        scores = [r.v_score for r in self._records]

        return {
            "total": len(self._records),
            "commit_count": verdicts.count("COMMIT"),
            "repair_count": verdicts.count("REPAIR"),
            "halt_count": verdicts.count("HALT"),
            "avg_v_score": sum(scores) / len(scores),
            "min_v_score": min(scores),
            "max_v_score": max(scores),
            "commit_rate": verdicts.count("COMMIT") / len(verdicts),
        }

    def get_recent_records(self, n: int = 10) -> List[YomiRecord]:
        """最近のn件を取得"""
        return list(self._records)[-n:]

    def clear(self) -> None:
        """アーカイブをクリア（テスト用）"""
        self._records.clear()

    # ================================================================
    # Layer 2（高天原）向けエクスポート機能
    # ================================================================

    def export_for_training(self) -> Dict[str, Any]:
        """
        Layer 2（学習パイプライン）向けにアーカイブをエクスポート。

        Returns:
            dict:
                - records: List[dict] - 各レコードの詳細
                - summary: dict - 集計統計
                - error_patterns: List[dict] - REPAIR/HALTパターン
                - quality_trends: List[dict] - 時系列品質データ
        """
        if not self._records:
            return {
                "records": [],
                "summary": {"total": 0},
                "error_patterns": [],
                "quality_trends": [],
            }

        records = [
            {
                "timestamp": r.timestamp,
                "verdict": r.verdict,
                "v_score": r.v_score,
                "metrics": r.metrics,
                "repair_hints": r.repair_hints,
                "text_length": r.text_length,
            }
            for r in self._records
        ]

        return {
            "records": records,
            "summary": self.get_session_stats(),
            "error_patterns": self._extract_error_patterns(),
            "quality_trends": self._compute_quality_trends(),
        }

    def export_error_patterns(self) -> List[Dict[str, Any]]:
        """
        REPAIR/HALTとなったケースのパターンを抽出。
        Layer 2での重点学習対象特定に使用。

        Returns:
            List[dict]: 各エラーパターンの詳細
                - error_type: str
                - frequency: int
                - avg_v_score: float
                - example_hints: List[str]
        """
        return self._extract_error_patterns()

    def export_quality_trends(
        self, window_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        品質スコアの時系列トレンドを出力。
        Layer 2での学習進捗モニタリングに使用。

        Parameters:
            window_size: 移動平均のウィンドウサイズ

        Returns:
            List[dict]: 時系列データポイント
                - timestamp: float
                - v_score: float
                - moving_avg: float
                - verdict: str
        """
        return self._compute_quality_trends(window_size)

    def get_repair_hint_statistics(self) -> Dict[str, int]:
        """
        修復ヒントの出現頻度を集計。
        Layer 2での弱点分析に使用。

        Returns:
            dict: ヒント文字列 -> 出現回数
        """
        hint_counts: Dict[str, int] = {}
        for record in self._records:
            for hint in record.repair_hints:
                hint_counts[hint] = hint_counts.get(hint, 0) + 1
        return hint_counts

    def get_low_score_samples(
        self, threshold: float = 0.5, max_samples: int = 50
    ) -> List[YomiRecord]:
        """
        低スコアサンプルを取得。
        Layer 2での重点学習データ選定に使用。

        Parameters:
            threshold: この値未満のスコアを抽出
            max_samples: 最大取得件数

        Returns:
            List[YomiRecord]: 低スコアレコード（スコア昇順）
        """
        low_scores = [r for r in self._records if r.v_score < threshold]
        low_scores.sort(key=lambda r: r.v_score)
        return low_scores[:max_samples]

    def _extract_error_patterns(self) -> List[Dict[str, Any]]:
        """エラーパターンを抽出（内部実装）"""
        # ヒントをキーとしてグループ化
        pattern_groups: Dict[str, List[YomiRecord]] = {}

        for record in self._records:
            if record.verdict in ("REPAIR", "HALT"):
                # 修復ヒントをパターンキーとして使用
                key = "|".join(sorted(record.repair_hints)) if record.repair_hints else "no_hints"
                if key not in pattern_groups:
                    pattern_groups[key] = []
                pattern_groups[key].append(record)

        patterns = []
        for key, records in pattern_groups.items():
            patterns.append({
                "error_type": key,
                "frequency": len(records),
                "avg_v_score": sum(r.v_score for r in records) / len(records),
                "example_hints": records[0].repair_hints if records else [],
                "verdicts": {
                    "REPAIR": sum(1 for r in records if r.verdict == "REPAIR"),
                    "HALT": sum(1 for r in records if r.verdict == "HALT"),
                },
            })

        # 頻度順にソート
        patterns.sort(key=lambda p: p["frequency"], reverse=True)
        return patterns

    def _compute_quality_trends(
        self, window_size: int = 10
    ) -> List[Dict[str, Any]]:
        """品質トレンドを計算（内部実装）"""
        if not self._records:
            return []

        records_list = list(self._records)
        trends = []

        for i, record in enumerate(records_list):
            # 移動平均計算
            start_idx = max(0, i - window_size + 1)
            window = records_list[start_idx:i + 1]
            moving_avg = sum(r.v_score for r in window) / len(window)

            trends.append({
                "timestamp": record.timestamp,
                "v_score": record.v_score,
                "moving_avg": moving_avg,
                "verdict": record.verdict,
                "metrics": record.metrics,
            })

        return trends


# ============================================================
# YomiEvaluator（Layer 5 統合クラス）
# ============================================================

class YomiEvaluator:
    """
    Layer 5: 根の国・黄泉。
    蛭子検知 → 閻魔判定 → アーカイブ の一連のフローを管理。

    Layer 3からは evaluate() のみが呼び出せる。
    内部状態（archive）はLayer 3からアクセス不可。

    注意:
    - layers.py の YomiLayer（モデル内部層）とは異なる責務
    - YomiLayer: モデル内部でリアルタイムに型安定性を検出
    - YomiEvaluator: パイプラインで事後に出力候補の品質を総合評価
    """

    def __init__(self, max_archive_records: int = 1000):
        self._hiruko = HirukoDetector()
        self._enma = EnmaGate()
        self._archive = YomiArchive(max_records=max_archive_records)

    def evaluate(self, output_candidate: dict) -> dict:
        """
        Layer 3から送られた出力候補を評価。
        結果は黄泉比良坂を通過できる情報のみ返却。

        Parameters:
            output_candidate: 以下のキーを含むdict
                - text: str
                - logits: List[List[float]] (オプション)
                - query: dict
                - type_ids: List[int] (オプション)
                - constraints: dict (オプション)
                - diagnostics: dict (YomiLayerの出力、オプション)

        Returns:
            dict: 黄泉比良坂を通過できる情報のみ
                - verdict: str ("COMMIT" | "REPAIR" | "HALT")
                - repair_hints: List[str]
                - quality_score: float
                注意: output_candidate自体は返さない
                「一度黄泉に送ったものは戻らない」原則
        """
        # 蛭子検知
        report = self._hiruko.detect(output_candidate)

        # 閻魔判定
        verdict = self._enma.judge(report)

        # アーカイブ（Layer 5内部に保存）
        self._archive.archive(
            verdict,
            text_length=len(output_candidate.get("text", "")),
        )

        # 黄泉比良坂を通過できる情報のみ返却
        return {
            "verdict": verdict.verdict.value,
            "repair_hints": verdict.repair_hints,
            "quality_score": verdict.v_score,
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Layer 2（学習パイプライン）向けの統計。
        Layer 3からは呼び出さない（黄泉比良坂の制約）。
        """
        return self._archive.get_session_stats()

    def get_hiruko_report(self, output_candidate: dict) -> HirukoReport:
        """
        蛭子検知レポートを直接取得（デバッグ用）。
        通常のパイプラインでは使用しない。
        """
        return self._hiruko.detect(output_candidate)


# ============================================================
# テスト用ユーティリティ
# ============================================================

def test_yomi_evaluator():
    """黄泉評価器の基本動作テスト"""
    print("=== 黄泉評価器テスト ===\n")

    evaluator = YomiEvaluator()

    # テストケース1: 正常な出力
    print("【テストケース1: 正常な出力】")
    good_candidate = {
        "text": """
struct Point2D
    x::Float64
    y::Float64
end

function distance(p1::Point2D, p2::Point2D)
    dx = p1.x - p2.x
    dy = p1.y - p2.y
    return sqrt(dx^2 + dy^2)
end
""",
        "query": {"prompt": "struct Point2D"},
    }
    result = evaluator.evaluate(good_candidate)
    print(f"  verdict: {result['verdict']}")
    print(f"  quality_score: {result['quality_score']:.3f}")
    print(f"  repair_hints: {result['repair_hints']}")

    # テストケース2: 不安定な出力（繰り返し）
    print("\n【テストケース2: 不安定な出力（繰り返し）】")
    unstable_candidate = {
        "text": """
struct Point2D
    x::Float64
    x::Float64
    x::Float64
    x::Float64
    x::Float64
""",
        "query": {"prompt": "struct Point2D"},
    }
    result = evaluator.evaluate(unstable_candidate)
    print(f"  verdict: {result['verdict']}")
    print(f"  quality_score: {result['quality_score']:.3f}")
    print(f"  repair_hints: {result['repair_hints']}")

    # テストケース3: 幻覚を含む出力
    print("\n【テストケース3: 幻覚を含む出力】")
    hallucinated_candidate = {
        "text": """
class Point2D:
    def __init__(self, x, y):
        self.x = x
        self.y = y
""",
        "query": {"prompt": "struct Point2D"},
    }
    result = evaluator.evaluate(hallucinated_candidate)
    print(f"  verdict: {result['verdict']}")
    print(f"  quality_score: {result['quality_score']:.3f}")
    print(f"  repair_hints: {result['repair_hints']}")

    # 統計
    print("\n【セッション統計】")
    stats = evaluator.get_stats()
    print(f"  total: {stats['total']}")
    print(f"  commit_count: {stats['commit_count']}")
    print(f"  repair_count: {stats['repair_count']}")
    print(f"  halt_count: {stats['halt_count']}")
    print(f"  avg_v_score: {stats['avg_v_score']:.3f}")

    print("\n=== テスト完了 ===")


if __name__ == "__main__":
    test_yomi_evaluator()
