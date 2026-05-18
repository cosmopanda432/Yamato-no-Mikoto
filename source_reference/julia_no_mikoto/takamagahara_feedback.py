"""
takamagahara_feedback.py — 高天原（Layer 2 学習フィードバック）

Layer 2: 高天原（学習パイプライン）
Layer 5（黄泉）からのフィードバックを収集し、学習シグナルに変換する。

=== 五層アーキテクチャでの役割 ===

高天原は神々が住む天上界。
地上（葦原中国 = Layer 3）での出来事を俯瞰し、
黄泉（Layer 5）からの報告を受けて、長期的な改善を行う。

フィードバックパス:
Layer 5 (YomiArchive) → 黄泉比良坂 → Layer 2 (TakamagaharaFeedback)
                                         ↓
                                    TrainingSignal
                                         ↓
                                    モデル改善

=== 設計原則 ===

1. 一方向フィードバック:
   - Layer 5 → Layer 2 のみ
   - Layer 2 → Layer 5 への逆流は禁止

2. 集約と抽象化:
   - 個別セッションのデータは集約して統計化
   - 個人情報や具体的な出力内容は含まない

3. 長期傾向の追跡:
   - 品質スコアの推移
   - エラーパターンの分析
   - 改善ポイントの特定

4. 千人殺す/千五百人生むのバランス:
   - HALT率が一定以下であれば許容
   - 完璧を目指さず、全体の品質向上を重視
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import time
import json
import hashlib


# ============================================================
# フィードバック種別
# ============================================================

class FeedbackType(Enum):
    """フィードバックの種別"""
    QUALITY_SCORE = "quality_score"        # 品質スコア
    VERDICT_DISTRIBUTION = "verdict_dist"  # COMMIT/REPAIR/HALT の分布
    ERROR_PATTERN = "error_pattern"        # エラーパターン
    REPAIR_EFFECTIVENESS = "repair_eff"    # 修復の有効性
    TYPE_STABILITY = "type_stability"      # 型安定性
    HALLUCINATION_RATE = "hallucination"   # 幻覚率


class TrainingPriority(Enum):
    """学習シグナルの優先度"""
    CRITICAL = "critical"    # 即時対応が必要
    HIGH = "high"           # 次回学習で対応
    MEDIUM = "medium"       # 定期学習で対応
    LOW = "low"             # 長期改善項目
    INFO = "info"           # 情報のみ


# ============================================================
# 学習シグナル
# ============================================================

@dataclass
class TrainingSignal:
    """
    学習パイプラインへのシグナル

    YomiArchiveの評価データを学習に使える形式に変換したもの。
    具体的な出力内容は含まず、統計情報のみを含む。

    Attributes:
        signal_id: シグナルID
        signal_type: フィードバック種別
        priority: 優先度
        timestamp: 生成時刻
        metrics: 数値メトリクス
        patterns: 検出されたパターン
        recommendations: 改善推奨事項
        sample_count: 集約したサンプル数
    """
    signal_id: str
    signal_type: FeedbackType
    priority: TrainingPriority
    timestamp: float
    metrics: Dict[str, float]
    patterns: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    sample_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "signal_id": self.signal_id,
            "signal_type": self.signal_type.value,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "metrics": self.metrics,
            "patterns": self.patterns,
            "recommendations": self.recommendations,
            "sample_count": self.sample_count,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TrainingSignal":
        """辞書から復元"""
        return cls(
            signal_id=data["signal_id"],
            signal_type=FeedbackType(data["signal_type"]),
            priority=TrainingPriority(data["priority"]),
            timestamp=data["timestamp"],
            metrics=data["metrics"],
            patterns=data.get("patterns", []),
            recommendations=data.get("recommendations", []),
            sample_count=data.get("sample_count", 0),
            metadata=data.get("metadata", {}),
        )


# ============================================================
# 品質傾向トラッカー
# ============================================================

@dataclass
class QualityWindow:
    """品質ウィンドウ（一定期間の統計）"""
    window_id: str
    start_time: float
    end_time: float
    total_count: int
    commit_count: int
    repair_count: int
    halt_count: int
    avg_quality: float
    min_quality: float
    max_quality: float
    repair_success_rate: float


class QualityTrendTracker:
    """
    品質傾向トラッカー

    時系列での品質変化を追跡し、
    改善傾向・悪化傾向を検出する。
    """

    def __init__(self, window_size_seconds: int = 3600):
        """
        Parameters:
            window_size_seconds: ウィンドウサイズ（秒）、デフォルト1時間
        """
        self._window_size = window_size_seconds
        self._windows: List[QualityWindow] = []
        self._current_window: Optional[QualityWindow] = None
        self._current_scores: List[float] = []
        self._current_verdicts: List[str] = []
        self._window_counter = 0

    def record(self, quality_score: float, verdict: str) -> None:
        """品質スコアとverdictを記録"""
        now = time.time()

        # 新しいウィンドウが必要か確認
        if self._current_window is None:
            self._start_new_window(now)
        elif now > self._current_window.end_time:
            self._finalize_current_window()
            self._start_new_window(now)

        self._current_scores.append(quality_score)
        self._current_verdicts.append(verdict)

    def _start_new_window(self, start_time: float) -> None:
        """新しいウィンドウを開始"""
        self._window_counter += 1
        self._current_window = QualityWindow(
            window_id=f"window-{self._window_counter}",
            start_time=start_time,
            end_time=start_time + self._window_size,
            total_count=0,
            commit_count=0,
            repair_count=0,
            halt_count=0,
            avg_quality=0.0,
            min_quality=1.0,
            max_quality=0.0,
            repair_success_rate=0.0,
        )
        self._current_scores = []
        self._current_verdicts = []

    def _finalize_current_window(self) -> None:
        """現在のウィンドウを確定"""
        if not self._current_scores:
            return

        w = self._current_window
        w.total_count = len(self._current_scores)
        w.commit_count = self._current_verdicts.count("COMMIT")
        w.repair_count = self._current_verdicts.count("REPAIR")
        w.halt_count = self._current_verdicts.count("HALT")
        w.avg_quality = sum(self._current_scores) / len(self._current_scores)
        w.min_quality = min(self._current_scores)
        w.max_quality = max(self._current_scores)

        # 修復成功率（REPAIRの後にCOMMITがあった割合）
        repair_success = 0
        for i, v in enumerate(self._current_verdicts):
            if v == "REPAIR" and i + 1 < len(self._current_verdicts):
                if self._current_verdicts[i + 1] == "COMMIT":
                    repair_success += 1
        w.repair_success_rate = repair_success / max(w.repair_count, 1)

        self._windows.append(w)

        # 古いウィンドウを削除（最新100個を保持）
        if len(self._windows) > 100:
            self._windows = self._windows[-100:]

    def get_trend(self, n_windows: int = 5) -> dict:
        """
        最近のN個のウィンドウから傾向を分析

        Returns:
            dict: 傾向分析結果
                - trend: "improving" | "stable" | "degrading"
                - avg_quality_change: float
                - commit_rate_change: float
        """
        if len(self._windows) < 2:
            return {
                "trend": "insufficient_data",
                "avg_quality_change": 0.0,
                "commit_rate_change": 0.0,
            }

        recent = self._windows[-n_windows:]
        if len(recent) < 2:
            recent = self._windows

        # 品質スコアの変化
        first_quality = recent[0].avg_quality
        last_quality = recent[-1].avg_quality
        quality_change = last_quality - first_quality

        # コミット率の変化
        first_commit_rate = recent[0].commit_count / max(recent[0].total_count, 1)
        last_commit_rate = recent[-1].commit_count / max(recent[-1].total_count, 1)
        commit_rate_change = last_commit_rate - first_commit_rate

        # 傾向判定
        if quality_change > 0.05 and commit_rate_change > 0.05:
            trend = "improving"
        elif quality_change < -0.05 or commit_rate_change < -0.1:
            trend = "degrading"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "avg_quality_change": quality_change,
            "commit_rate_change": commit_rate_change,
            "window_count": len(recent),
        }

    def get_summary(self) -> dict:
        """全体サマリーを取得"""
        if not self._windows:
            return {"total_windows": 0}

        total_count = sum(w.total_count for w in self._windows)
        total_commit = sum(w.commit_count for w in self._windows)
        total_repair = sum(w.repair_count for w in self._windows)
        total_halt = sum(w.halt_count for w in self._windows)

        return {
            "total_windows": len(self._windows),
            "total_evaluations": total_count,
            "overall_commit_rate": total_commit / max(total_count, 1),
            "overall_repair_rate": total_repair / max(total_count, 1),
            "overall_halt_rate": total_halt / max(total_count, 1),
            "avg_quality": sum(w.avg_quality for w in self._windows) / len(self._windows),
        }


# ============================================================
# エラーパターン分析
# ============================================================

class ErrorPatternAnalyzer:
    """
    エラーパターン分析器

    繰り返し発生するエラーパターンを検出し、
    学習シグナルに変換する。
    """

    def __init__(self, pattern_threshold: int = 5):
        """
        Parameters:
            pattern_threshold: パターンとみなす最小出現回数
        """
        self._pattern_threshold = pattern_threshold
        self._error_counts: Dict[str, int] = {}
        self._recent_errors: List[Tuple[float, str]] = []

    def record_error(self, error_type: str, details: Optional[str] = None) -> None:
        """エラーを記録"""
        pattern_key = self._normalize_error(error_type, details)
        self._error_counts[pattern_key] = self._error_counts.get(pattern_key, 0) + 1
        self._recent_errors.append((time.time(), pattern_key))

        # 古いエラーを削除（24時間以上前）
        cutoff = time.time() - 86400
        self._recent_errors = [(t, e) for t, e in self._recent_errors if t > cutoff]

    def _normalize_error(self, error_type: str, details: Optional[str]) -> str:
        """エラーを正規化してパターンキーを生成"""
        # 具体的な値を抽象化
        if details:
            # 数値を[N]に置換
            import re
            details = re.sub(r'\d+', '[N]', details)
            # 長い文字列を省略
            if len(details) > 50:
                details = details[:50] + "..."
            return f"{error_type}:{details}"
        return error_type

    def get_frequent_patterns(self) -> List[Tuple[str, int]]:
        """頻出パターンを取得"""
        patterns = [
            (pattern, count)
            for pattern, count in self._error_counts.items()
            if count >= self._pattern_threshold
        ]
        return sorted(patterns, key=lambda x: x[1], reverse=True)

    def get_recent_spike(self, window_hours: int = 1) -> List[str]:
        """直近で急増しているパターンを検出"""
        cutoff = time.time() - (window_hours * 3600)
        recent = [e for t, e in self._recent_errors if t > cutoff]

        # 最近の出現回数が全体の50%以上のパターン
        spike_patterns = []
        for pattern, total_count in self._error_counts.items():
            recent_count = recent.count(pattern)
            if total_count > 0 and recent_count / total_count > 0.5:
                spike_patterns.append(pattern)

        return spike_patterns


# ============================================================
# 高天原フィードバックコレクター
# ============================================================

class TakamagaharaFeedback:
    """
    高天原（Takamagahara）フィードバックコレクター

    Layer 5（黄泉）からの評価データを収集し、
    Layer 2（学習パイプライン）向けのシグナルに変換する。

    === 設計原則 ===

    1. データの抽象化:
       - 具体的な出力内容は含まない
       - 統計情報と傾向のみを提供

    2. プライバシー保護:
       - セッション固有の情報は匿名化
       - 個別クエリは記録しない

    3. 長期学習への貢献:
       - 傾向分析による改善ポイントの特定
       - エラーパターンの学習
       - 品質向上のためのシグナル生成

    Args:
        quality_window_size: 品質ウィンドウサイズ（秒）
        error_pattern_threshold: エラーパターン閾値
    """

    def __init__(
        self,
        quality_window_size: int = 3600,
        error_pattern_threshold: int = 5,
    ):
        self._quality_tracker = QualityTrendTracker(quality_window_size)
        self._error_analyzer = ErrorPatternAnalyzer(error_pattern_threshold)
        self._signals: List[TrainingSignal] = []
        self._signal_counter = 0
        self._total_feedback_count = 0

        # 累積統計
        self._cumulative_stats = {
            "total_evaluations": 0,
            "total_commit": 0,
            "total_repair": 0,
            "total_halt": 0,
            "sum_quality": 0.0,
        }

    def _generate_signal_id(self) -> str:
        """シグナルIDを生成"""
        self._signal_counter += 1
        timestamp = int(time.time())
        return f"signal-{timestamp}-{self._signal_counter}"

    def collect_from_yomi_stats(self, yomi_stats: dict) -> List[TrainingSignal]:
        """
        YomiArchiveの統計からフィードバックを収集

        Parameters:
            yomi_stats: YomiEvaluator.get_stats() の結果
                - total: int
                - commit_count: int
                - repair_count: int
                - halt_count: int
                - avg_v_score: float
                - min_v_score: float
                - max_v_score: float
                - commit_rate: float

        Returns:
            List[TrainingSignal]: 生成された学習シグナル
        """
        signals: List[TrainingSignal] = []
        now = time.time()

        total = yomi_stats.get("total", 0)
        if total == 0:
            return signals

        commit_count = yomi_stats.get("commit_count", 0)
        repair_count = yomi_stats.get("repair_count", 0)
        halt_count = yomi_stats.get("halt_count", 0)
        avg_quality = yomi_stats.get("avg_v_score", 0.0)
        commit_rate = yomi_stats.get("commit_rate", 0.0)

        # 累積統計を更新
        self._cumulative_stats["total_evaluations"] += total
        self._cumulative_stats["total_commit"] += commit_count
        self._cumulative_stats["total_repair"] += repair_count
        self._cumulative_stats["total_halt"] += halt_count
        self._cumulative_stats["sum_quality"] += avg_quality * total

        # 1. 品質スコアシグナル
        quality_signal = TrainingSignal(
            signal_id=self._generate_signal_id(),
            signal_type=FeedbackType.QUALITY_SCORE,
            priority=self._determine_quality_priority(avg_quality),
            timestamp=now,
            metrics={
                "avg_quality": avg_quality,
                "min_quality": yomi_stats.get("min_v_score", 0.0),
                "max_quality": yomi_stats.get("max_v_score", 1.0),
                "quality_range": yomi_stats.get("max_v_score", 1.0) - yomi_stats.get("min_v_score", 0.0),
            },
            sample_count=total,
        )
        signals.append(quality_signal)

        # 2. Verdict分布シグナル
        verdict_signal = TrainingSignal(
            signal_id=self._generate_signal_id(),
            signal_type=FeedbackType.VERDICT_DISTRIBUTION,
            priority=self._determine_verdict_priority(commit_rate, halt_count / max(total, 1)),
            timestamp=now,
            metrics={
                "commit_rate": commit_rate,
                "repair_rate": repair_count / max(total, 1),
                "halt_rate": halt_count / max(total, 1),
            },
            sample_count=total,
        )

        # 推奨事項を追加
        if commit_rate < 0.5:
            verdict_signal.recommendations.append(
                "COMMIT率が50%未満。品質閾値の調整または生成品質の改善が必要。"
            )
        if halt_count / max(total, 1) > 0.3:
            verdict_signal.recommendations.append(
                "HALT率が30%超過。重大な品質問題の可能性。"
            )

        signals.append(verdict_signal)

        # シグナルを保存
        self._signals.extend(signals)
        self._total_feedback_count += 1

        return signals

    def collect_evaluation_result(
        self,
        quality_score: float,
        verdict: str,
        error_type: Optional[str] = None,
        error_details: Optional[str] = None,
    ) -> None:
        """
        個別の評価結果を収集

        Parameters:
            quality_score: 品質スコア (0.0-1.0)
            verdict: "COMMIT" | "REPAIR" | "HALT"
            error_type: エラー種別（オプション）
            error_details: エラー詳細（オプション）
        """
        # 品質トラッカーに記録
        self._quality_tracker.record(quality_score, verdict)

        # エラーパターンを記録
        if error_type:
            self._error_analyzer.record_error(error_type, error_details)

    def _determine_quality_priority(self, avg_quality: float) -> TrainingPriority:
        """品質スコアから優先度を決定"""
        if avg_quality < 0.3:
            return TrainingPriority.CRITICAL
        elif avg_quality < 0.5:
            return TrainingPriority.HIGH
        elif avg_quality < 0.7:
            return TrainingPriority.MEDIUM
        else:
            return TrainingPriority.LOW

    def _determine_verdict_priority(self, commit_rate: float, halt_rate: float) -> TrainingPriority:
        """verdict分布から優先度を決定"""
        if halt_rate > 0.5:
            return TrainingPriority.CRITICAL
        elif commit_rate < 0.3:
            return TrainingPriority.HIGH
        elif commit_rate < 0.6:
            return TrainingPriority.MEDIUM
        else:
            return TrainingPriority.LOW

    def generate_error_pattern_signal(self) -> Optional[TrainingSignal]:
        """エラーパターンシグナルを生成"""
        patterns = self._error_analyzer.get_frequent_patterns()
        if not patterns:
            return None

        spike_patterns = self._error_analyzer.get_recent_spike()

        signal = TrainingSignal(
            signal_id=self._generate_signal_id(),
            signal_type=FeedbackType.ERROR_PATTERN,
            priority=TrainingPriority.HIGH if spike_patterns else TrainingPriority.MEDIUM,
            timestamp=time.time(),
            metrics={
                "unique_patterns": len(patterns),
                "spike_patterns": len(spike_patterns),
            },
            patterns=[p[0] for p in patterns[:10]],  # 上位10パターン
            sample_count=sum(p[1] for p in patterns),
        )

        if spike_patterns:
            signal.recommendations.append(
                f"急増中のエラーパターン: {spike_patterns[:3]}"
            )

        self._signals.append(signal)
        return signal

    def get_training_signals(
        self,
        priority_filter: Optional[TrainingPriority] = None,
        signal_type_filter: Optional[FeedbackType] = None,
        limit: int = 100,
    ) -> List[TrainingSignal]:
        """
        学習シグナルを取得

        Parameters:
            priority_filter: 優先度でフィルタ
            signal_type_filter: 種別でフィルタ
            limit: 最大件数

        Returns:
            List[TrainingSignal]: フィルタされたシグナル
        """
        signals = self._signals

        if priority_filter:
            signals = [s for s in signals if s.priority == priority_filter]

        if signal_type_filter:
            signals = [s for s in signals if s.signal_type == signal_type_filter]

        # 新しい順でソート
        signals = sorted(signals, key=lambda s: s.timestamp, reverse=True)

        return signals[:limit]

    def get_quality_trend(self) -> dict:
        """品質傾向を取得"""
        return self._quality_tracker.get_trend()

    def get_cumulative_stats(self) -> dict:
        """累積統計を取得"""
        total = self._cumulative_stats["total_evaluations"]
        return {
            "total_evaluations": total,
            "overall_commit_rate": self._cumulative_stats["total_commit"] / max(total, 1),
            "overall_repair_rate": self._cumulative_stats["total_repair"] / max(total, 1),
            "overall_halt_rate": self._cumulative_stats["total_halt"] / max(total, 1),
            "overall_avg_quality": self._cumulative_stats["sum_quality"] / max(total, 1),
            "feedback_collection_count": self._total_feedback_count,
            "total_signals_generated": len(self._signals),
        }

    def export_for_training(self) -> dict:
        """
        学習パイプライン向けにエクスポート

        Returns:
            dict: 学習に必要なデータ
                - signals: List[dict]
                - quality_trend: dict
                - error_patterns: List[str]
                - cumulative_stats: dict
                - export_timestamp: float
        """
        return {
            "signals": [s.to_dict() for s in self._signals[-100:]],  # 最新100件
            "quality_trend": self.get_quality_trend(),
            "quality_summary": self._quality_tracker.get_summary(),
            "error_patterns": [p[0] for p in self._error_analyzer.get_frequent_patterns()],
            "cumulative_stats": self.get_cumulative_stats(),
            "export_timestamp": time.time(),
        }

    def clear_old_signals(self, max_age_hours: int = 24) -> int:
        """古いシグナルをクリア"""
        cutoff = time.time() - (max_age_hours * 3600)
        original_count = len(self._signals)
        self._signals = [s for s in self._signals if s.timestamp > cutoff]
        return original_count - len(self._signals)


# ============================================================
# Layer 2/5 統合インターフェース
# ============================================================

class FeedbackPipeline:
    """
    フィードバックパイプライン

    Layer 5 (YomotsuHirasaka) と Layer 2 (TakamagaharaFeedback) を接続し、
    定期的にフィードバックを収集・処理する。

    使用例:
        pipeline = FeedbackPipeline(gateway=yomotsu_hirasaka)
        pipeline.collect_feedback()  # 定期的に呼び出し
        signals = pipeline.get_high_priority_signals()
    """

    def __init__(
        self,
        gateway=None,  # YomotsuHirasaka
        feedback_collector: Optional[TakamagaharaFeedback] = None,
    ):
        self.gateway = gateway
        self.feedback = feedback_collector or TakamagaharaFeedback()
        self._last_collection_time = 0.0

    def collect_feedback(self) -> List[TrainingSignal]:
        """
        Layer 5からフィードバックを収集

        Returns:
            List[TrainingSignal]: 新規生成されたシグナル
        """
        signals = []

        if self.gateway is not None:
            # YomotsuHirasaka経由でYomiArchiveの統計を取得
            stats = self.gateway.get_stats_for_layer2()
            signals.extend(self.feedback.collect_from_yomi_stats(stats))

        # エラーパターンシグナルを生成
        error_signal = self.feedback.generate_error_pattern_signal()
        if error_signal:
            signals.append(error_signal)

        self._last_collection_time = time.time()
        return signals

    def get_high_priority_signals(self) -> List[TrainingSignal]:
        """高優先度のシグナルを取得"""
        critical = self.feedback.get_training_signals(priority_filter=TrainingPriority.CRITICAL)
        high = self.feedback.get_training_signals(priority_filter=TrainingPriority.HIGH)
        return critical + high

    def get_status(self) -> dict:
        """パイプラインのステータスを取得"""
        return {
            "last_collection_time": self._last_collection_time,
            "quality_trend": self.feedback.get_quality_trend(),
            "cumulative_stats": self.feedback.get_cumulative_stats(),
            "gateway_connected": self.gateway is not None,
        }


# ============================================================
# テスト用ユーティリティ
# ============================================================

def test_takamagahara_feedback():
    """高天原フィードバックの基本動作テスト"""
    print("=== 高天原フィードバックテスト ===\n")

    feedback = TakamagaharaFeedback()

    # テストデータ: YomiArchiveの統計をシミュレート
    print("【テスト1: Yomi統計からのフィードバック収集】")
    test_stats = {
        "total": 100,
        "commit_count": 65,
        "repair_count": 25,
        "halt_count": 10,
        "avg_v_score": 0.72,
        "min_v_score": 0.15,
        "max_v_score": 0.98,
        "commit_rate": 0.65,
    }

    signals = feedback.collect_from_yomi_stats(test_stats)
    print(f"  生成されたシグナル数: {len(signals)}")
    for s in signals:
        print(f"    - {s.signal_type.value}: priority={s.priority.value}")
        if s.recommendations:
            print(f"      推奨: {s.recommendations[0][:50]}...")

    # テスト2: 個別評価結果の収集
    print("\n【テスト2: 個別評価結果の収集】")
    import random
    for i in range(20):
        quality = random.uniform(0.4, 0.95)
        verdict = random.choice(["COMMIT", "COMMIT", "COMMIT", "REPAIR", "HALT"])
        feedback.collect_evaluation_result(quality, verdict)
        if verdict == "HALT":
            feedback.collect_evaluation_result(
                quality, verdict,
                error_type="stability_low",
                error_details=f"score={quality:.2f}"
            )

    trend = feedback.get_quality_trend()
    print(f"  品質傾向: {trend.get('trend', 'N/A')}")

    # テスト3: エラーパターンシグナル
    print("\n【テスト3: エラーパターン分析】")
    for _ in range(10):
        feedback.collect_evaluation_result(
            0.3, "HALT",
            error_type="hallucination",
            error_details="undefined reference"
        )

    error_signal = feedback.generate_error_pattern_signal()
    if error_signal:
        print(f"  パターン数: {len(error_signal.patterns)}")
        print(f"  検出パターン: {error_signal.patterns[:3]}")

    # テスト4: 学習用エクスポート
    print("\n【テスト4: 学習用エクスポート】")
    export_data = feedback.export_for_training()
    print(f"  シグナル数: {len(export_data['signals'])}")
    print(f"  累積統計: {export_data['cumulative_stats']}")

    # テスト5: フィードバックパイプライン
    print("\n【テスト5: フィードバックパイプライン】")
    pipeline = FeedbackPipeline(feedback_collector=feedback)
    high_priority = pipeline.get_high_priority_signals()
    print(f"  高優先度シグナル: {len(high_priority)} 件")

    status = pipeline.get_status()
    print(f"  パイプラインステータス: {status['quality_trend']}")

    print("\n=== テスト完了 ===")


if __name__ == "__main__":
    test_takamagahara_feedback()
