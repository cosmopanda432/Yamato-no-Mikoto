"""
yomotsu_hirasaka.py — 黄泉比良坂（Evaluation Gateway）

Layer 3（葦原中国）とLayer 5（根の国・黄泉）の境界。
通過できる情報を厳密に制限する。

=== 五層アーキテクチャでの役割 ===

黄泉比良坂はLayer 3とLayer 5の間のファイアウォール。
古事記でイザナギがイザナミから逃げる際に通った坂。
「千引の岩」で封印され、二度と戻れなくなった。

=== 通信制約（P2厳密実装） ===

1. 一方向性制約:
   - 出力候補はL3→L5へ送るが、L5の内部状態はL3に漏洩しない
   - 深いコピーを使用して参照リークを防止

2. 不可逆性制約:
   - 一度L5に送った出力候補はL3に「そのまま」戻せない
   - 返却されるのはverdictと修復ヒントのみ

3. 千引の岩制約:
   - L5の内部データ（archive等）をL3側から参照不可
   - セッション間の情報漏洩を防止

4. ペイロード制約:
   - サイズ制限による過負荷防止
   - 型検証による不正データ排除

5. 監査制約:
   - 全通信のログ記録
   - セッションID追跡

=== 通過できる情報 ===

往路 (L3→L5):
├── text: str (max 100KB)
├── logits: List[List[float]] (max 10MB)
├── query: dict
├── type_ids: List[int] (max 10000)
├── constraints: dict
└── diagnostics: dict

復路 (L5→L3):
├── verdict: str ("COMMIT" | "REPAIR" | "HALT")
├── repair_hints: List[str] (max 10 hints, 500 chars each)
└── quality_score: float (0.0-1.0)

通過できない情報:
├── 生出力候補そのもの
├── 他セッションの評価データ
├── YomiArchiveの生データ（L2にのみ開放）
└── 内部状態への参照
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Set, Optional
import copy
import time
import uuid
import hashlib

# 直接実行時とモジュールimport時の両方に対応
try:
    from .yomi_evaluator import YomiEvaluator
except ImportError:
    from kojiki_lm.julia_no_mikoto.yomi_evaluator import YomiEvaluator


# ============================================================
# 通信制約定数
# ============================================================

# === 往路ペイロード（L3 → L5）===

ALLOWED_OUTBOUND_KEYS: Set[str] = {
    "text",         # 生成されたコード
    "logits",       # logit分布（オプション）
    "query",        # 元のリクエスト
    "type_ids",     # 型IDシーケンス（オプション）
    "constraints",  # 制約条件（オプション）
    "diagnostics",  # YomiLayerの出力（オプション）
}

# === 復路ペイロード（L5 → L3）===

ALLOWED_INBOUND_KEYS: Set[str] = {
    "verdict",        # COMMIT / REPAIR / HALT
    "repair_hints",   # 修復ヒントのリスト
    "quality_score",  # 品質スコア（数値のみ）
}

# === サイズ制限 ===

MAX_TEXT_SIZE = 100 * 1024           # 100KB
MAX_LOGITS_SIZE = 10 * 1024 * 1024   # 10MB
MAX_TYPE_IDS_LENGTH = 10000
MAX_REPAIR_HINTS = 10
MAX_REPAIR_HINT_LENGTH = 500

# === 有効なverdictの値 ===

VALID_VERDICTS: Set[str] = {"COMMIT", "REPAIR", "HALT"}


# ============================================================
# 監査ログエントリ
# ============================================================

@dataclass
class AuditLogEntry:
    """
    通信監査ログエントリ

    全てのLayer 3/5間通信を記録する。
    """
    timestamp: float
    session_id: str
    direction: str  # "outbound" or "inbound"
    payload_hash: str
    payload_size: int
    filtered_keys: List[str]
    passed_keys: List[str]
    verdict: Optional[str] = None
    quality_score: Optional[float] = None
    validation_errors: List[str] = field(default_factory=list)


# ============================================================
# 黄泉比良坂（Evaluation Gateway）
# ============================================================

class YomotsuHirasaka:
    """
    黄泉比良坂 = Evaluation Gateway。
    Layer 3/5間の通信を仲介し、情報の通過を厳密に制限する。

    自身はYomiEvaluatorを内包し、
    Layer 3側からはsend_for_evaluation()のみが呼び出せる。

    === P2 厳密化された設計原則 ===

    1. 往路フィルタリング:
       - 許可されたキーのみL5に送出
       - サイズ制限の適用
       - 深いコピーによる参照リーク防止

    2. 復路フィルタリング:
       - 許可されたキーのみL3に返却
       - verdict値の検証
       - repair_hintsのサイズ制限

    3. 千引の岩:
       - L5の内部状態はL3からアクセス不可
       - セッション分離
       - 監査ログによる追跡

    4. セッション管理:
       - 各評価にセッションIDを付与
       - セッション間の情報漏洩を防止

    Args:
        max_archive_records: YomiArchiveの最大保持件数
        enable_audit_log: 監査ログを有効にするか
        max_audit_log_size: 監査ログの最大サイズ
    """

    def __init__(
        self,
        max_archive_records: int = 1000,
        enable_audit_log: bool = True,
        max_audit_log_size: int = 1000,
    ):
        self._evaluator = YomiEvaluator(max_archive_records=max_archive_records)
        self._enable_audit_log = enable_audit_log
        self._max_audit_log_size = max_audit_log_size
        self._audit_log: List[AuditLogEntry] = []
        self._session_counter = 0

    def _generate_session_id(self) -> str:
        """セッションIDを生成"""
        self._session_counter += 1
        return f"yomi-{self._session_counter}-{uuid.uuid4().hex[:8]}"

    def _compute_payload_hash(self, payload: dict) -> str:
        """ペイロードのハッシュを計算（監査用）"""
        try:
            content = str(sorted(payload.items()))
            return hashlib.sha256(content.encode()).hexdigest()[:16]
        except Exception:
            return "unhashable"

    def _deep_copy_value(self, value: Any) -> Any:
        """
        値の深いコピーを作成（参照リーク防止）

        千引の岩の原則: Layer 5の内部データへの参照を
        Layer 3に渡さない。
        """
        try:
            return copy.deepcopy(value)
        except Exception:
            # コピーできない場合は文字列化
            return str(value)

    def _validate_outbound(self, candidate: dict) -> tuple[dict, List[str]]:
        """
        往路ペイロードの検証とフィルタリング

        Returns:
            tuple: (フィルタリング済みペイロード, 検証エラーリスト)
        """
        errors: List[str] = []
        filtered: Dict[str, Any] = {}

        for key, value in candidate.items():
            if key not in ALLOWED_OUTBOUND_KEYS:
                continue

            # text のサイズチェック
            if key == "text":
                if not isinstance(value, str):
                    errors.append(f"text must be str, got {type(value).__name__}")
                    continue
                if len(value) > MAX_TEXT_SIZE:
                    errors.append(f"text exceeds {MAX_TEXT_SIZE} bytes")
                    value = value[:MAX_TEXT_SIZE]  # 切り詰め

            # type_ids の長さチェック
            elif key == "type_ids":
                if value is not None:
                    if not isinstance(value, (list, tuple)):
                        errors.append(f"type_ids must be list, got {type(value).__name__}")
                        continue
                    if len(value) > MAX_TYPE_IDS_LENGTH:
                        errors.append(f"type_ids exceeds {MAX_TYPE_IDS_LENGTH} items")
                        value = list(value)[:MAX_TYPE_IDS_LENGTH]

            # logits のサイズチェック（概算）
            elif key == "logits":
                if value is not None:
                    try:
                        estimated_size = len(str(value))
                        if estimated_size > MAX_LOGITS_SIZE:
                            errors.append(f"logits exceeds {MAX_LOGITS_SIZE} bytes")
                            value = None
                    except Exception:
                        errors.append("logits validation failed")
                        value = None

            # 深いコピーを作成
            filtered[key] = self._deep_copy_value(value)

        return filtered, errors

    def _validate_inbound(self, result: dict) -> tuple[dict, List[str]]:
        """
        復路ペイロードの検証とフィルタリング

        Returns:
            tuple: (フィルタリング済みペイロード, 検証エラーリスト)
        """
        errors: List[str] = []
        filtered: Dict[str, Any] = {}

        for key, value in result.items():
            if key not in ALLOWED_INBOUND_KEYS:
                continue

            # verdict の検証
            if key == "verdict":
                if not isinstance(value, str):
                    errors.append(f"verdict must be str, got {type(value).__name__}")
                    value = "HALT"
                elif value not in VALID_VERDICTS:
                    errors.append(f"invalid verdict: {value}")
                    value = "HALT"

            # quality_score の検証
            elif key == "quality_score":
                if not isinstance(value, (int, float)):
                    errors.append(f"quality_score must be numeric, got {type(value).__name__}")
                    value = 0.0
                else:
                    value = max(0.0, min(1.0, float(value)))  # 0.0-1.0にクランプ

            # repair_hints の検証
            elif key == "repair_hints":
                if not isinstance(value, list):
                    errors.append(f"repair_hints must be list, got {type(value).__name__}")
                    value = []
                else:
                    # サイズ制限と各ヒントの長さ制限
                    value = value[:MAX_REPAIR_HINTS]
                    value = [
                        str(h)[:MAX_REPAIR_HINT_LENGTH]
                        for h in value
                        if h is not None
                    ]

            # 深いコピーを作成
            filtered[key] = self._deep_copy_value(value)

        return filtered, errors

    def _add_audit_log(self, entry: AuditLogEntry) -> None:
        """監査ログにエントリを追加"""
        if not self._enable_audit_log:
            return

        self._audit_log.append(entry)

        # 最大サイズを超えたら古いエントリを削除
        if len(self._audit_log) > self._max_audit_log_size:
            self._audit_log = self._audit_log[-self._max_audit_log_size:]

    def send_for_evaluation(self, output_candidate: dict) -> dict:
        """
        出力候補をLayer 5に送り、評価結果を受け取る。

        Parameters:
            output_candidate: Layer 3からの出力候補
                許可されたキーのみ通過（それ以外は除去）

        Returns:
            dict: 評価結果（許可されたキーのみ含む）
                - verdict: str ("COMMIT" | "REPAIR" | "HALT")
                - repair_hints: List[str]
                - quality_score: float

        Note:
            output_candidate自体は返却されない。
            「一度黄泉に送ったものは戻らない」原則。
        """
        session_id = self._generate_session_id()
        timestamp = time.time()

        # === 往路フィルタリング ===
        filtered_candidate, outbound_errors = self._validate_outbound(output_candidate)

        # 往路監査ログ
        outbound_entry = AuditLogEntry(
            timestamp=timestamp,
            session_id=session_id,
            direction="outbound",
            payload_hash=self._compute_payload_hash(output_candidate),
            payload_size=len(str(output_candidate)),
            filtered_keys=list(set(output_candidate.keys()) - ALLOWED_OUTBOUND_KEYS),
            passed_keys=list(filtered_candidate.keys()),
            validation_errors=outbound_errors,
        )
        self._add_audit_log(outbound_entry)

        # === Layer 5で評価 ===
        raw_result = self._evaluator.evaluate(filtered_candidate)

        # === 復路フィルタリング ===
        filtered_result, inbound_errors = self._validate_inbound(raw_result)

        # 復路監査ログ
        inbound_entry = AuditLogEntry(
            timestamp=time.time(),
            session_id=session_id,
            direction="inbound",
            payload_hash=self._compute_payload_hash(raw_result),
            payload_size=len(str(raw_result)),
            filtered_keys=list(set(raw_result.keys()) - ALLOWED_INBOUND_KEYS),
            passed_keys=list(filtered_result.keys()),
            verdict=filtered_result.get("verdict"),
            quality_score=filtered_result.get("quality_score"),
            validation_errors=inbound_errors,
        )
        self._add_audit_log(inbound_entry)

        return filtered_result

    def get_stats_for_layer2(self) -> Dict[str, Any]:
        """
        Layer 2（学習パイプライン）向けの統計取得。
        Layer 3からは呼び出さない。
        天御柱オーケストレータのみがL2フィードバック時に使用。

        Returns:
            dict: セッション統計
                - total: int
                - commit_count: int
                - repair_count: int
                - halt_count: int
                - avg_v_score: float
                - min_v_score: float
                - max_v_score: float
                - commit_rate: float
        """
        return self._evaluator.get_stats()

    def get_allowed_outbound_keys(self) -> Set[str]:
        """往路で許可されたキーを取得（ドキュメント用）"""
        return ALLOWED_OUTBOUND_KEYS.copy()

    def get_allowed_inbound_keys(self) -> Set[str]:
        """復路で許可されたキーを取得（ドキュメント用）"""
        return ALLOWED_INBOUND_KEYS.copy()

    def get_audit_log(self, last_n: Optional[int] = None) -> List[dict]:
        """
        監査ログを取得（Layer 2 / 管理者向け）

        Layer 3からは呼び出さない。

        Parameters:
            last_n: 最新N件のみ取得（Noneで全件）

        Returns:
            List[dict]: 監査ログエントリのリスト
        """
        entries = self._audit_log if last_n is None else self._audit_log[-last_n:]
        return [
            {
                "timestamp": e.timestamp,
                "session_id": e.session_id,
                "direction": e.direction,
                "payload_hash": e.payload_hash,
                "payload_size": e.payload_size,
                "filtered_keys": e.filtered_keys,
                "passed_keys": e.passed_keys,
                "verdict": e.verdict,
                "quality_score": e.quality_score,
                "validation_errors": e.validation_errors,
            }
            for e in entries
        ]

    def get_security_status(self) -> dict:
        """
        セキュリティステータスを取得

        Returns:
            dict: セキュリティ関連の統計
        """
        total_entries = len(self._audit_log)
        error_entries = sum(1 for e in self._audit_log if e.validation_errors)
        filtered_key_count = sum(len(e.filtered_keys) for e in self._audit_log)

        return {
            "audit_log_size": total_entries,
            "entries_with_errors": error_entries,
            "total_filtered_keys": filtered_key_count,
            "session_counter": self._session_counter,
            "constraints": {
                "max_text_size": MAX_TEXT_SIZE,
                "max_type_ids_length": MAX_TYPE_IDS_LENGTH,
                "max_repair_hints": MAX_REPAIR_HINTS,
                "allowed_outbound_keys": list(ALLOWED_OUTBOUND_KEYS),
                "allowed_inbound_keys": list(ALLOWED_INBOUND_KEYS),
            },
        }


# ============================================================
# テスト用ユーティリティ
# ============================================================

def test_yomotsu_hirasaka():
    """黄泉比良坂の基本動作テスト"""
    print("=== 黄泉比良坂テスト ===\n")

    gateway = YomotsuHirasaka()

    # 許可されたキーの確認
    print("【許可されたキー】")
    print(f"  往路 (L3→L5): {gateway.get_allowed_outbound_keys()}")
    print(f"  復路 (L5→L3): {gateway.get_allowed_inbound_keys()}")

    # テストケース1: 許可されたキーのみ
    print("\n【テストケース1: 許可されたキーのみ】")
    candidate1 = {
        "text": "struct Point2D\n    x::Float64\n    y::Float64\nend",
        "query": {"prompt": "struct Point2D"},
    }
    result1 = gateway.send_for_evaluation(candidate1)
    print(f"  verdict: {result1['verdict']}")
    print(f"  quality_score: {result1['quality_score']:.3f}")
    print(f"  返却キー: {set(result1.keys())}")

    # テストケース2: 不正なキーを含む（フィルタリングされるべき）
    print("\n【テストケース2: 不正なキーを含む】")
    candidate2 = {
        "text": "struct Point2D\n    x::Float64\n    y::Float64\nend",
        "query": {"prompt": "struct Point2D"},
        "secret_data": "これはL5に渡すべきでない",
        "internal_state": {"should_not_pass": True},
    }
    result2 = gateway.send_for_evaluation(candidate2)
    print(f"  verdict: {result2['verdict']}")
    print(f"  返却キー: {set(result2.keys())}")
    print(f"  'secret_data'が返却に含まれない: {'secret_data' not in result2}")

    # テストケース3: 空の出力
    print("\n【テストケース3: 空の出力】")
    candidate3 = {
        "text": "",
        "query": {"prompt": "struct Point2D"},
    }
    result3 = gateway.send_for_evaluation(candidate3)
    print(f"  verdict: {result3['verdict']}")
    print(f"  quality_score: {result3['quality_score']:.3f}")

    # 統計（L2向け）
    print("\n【L2向け統計】")
    stats = gateway.get_stats_for_layer2()
    print(f"  total: {stats['total']}")
    print(f"  commit_rate: {stats.get('commit_rate', 0):.3f}")

    # P2: セキュリティステータス
    print("\n【P2: セキュリティステータス】")
    security = gateway.get_security_status()
    print(f"  監査ログサイズ: {security['audit_log_size']}")
    print(f"  セッション数: {security['session_counter']}")
    print(f"  フィルタされた総キー数: {security['total_filtered_keys']}")

    # P2: 監査ログ確認
    print("\n【P2: 監査ログ (最新2件)】")
    audit_log = gateway.get_audit_log(last_n=2)
    for entry in audit_log:
        direction = "→" if entry['direction'] == 'outbound' else "←"
        print(f"  {direction} session={entry['session_id'][:12]}...")
        print(f"    passed_keys: {entry['passed_keys']}")
        if entry['filtered_keys']:
            print(f"    filtered_keys: {entry['filtered_keys']}")
        if entry['verdict']:
            print(f"    verdict: {entry['verdict']}, score: {entry['quality_score']:.3f}")

    # P2: サイズ制限テスト
    print("\n【P2: サイズ制限テスト】")
    huge_text = "x" * (MAX_TEXT_SIZE + 1000)
    candidate4 = {
        "text": huge_text,
        "query": {"prompt": "test"},
    }
    result4 = gateway.send_for_evaluation(candidate4)
    print(f"  巨大テキスト送信後: verdict={result4['verdict']}")

    # エラーを含む監査ログを確認
    recent_log = gateway.get_audit_log(last_n=1)[0]
    if recent_log['validation_errors']:
        print(f"  検証エラー: {recent_log['validation_errors']}")

    print("\n=== テスト完了 ===")


if __name__ == "__main__":
    test_yomotsu_hirasaka()
