"""
zoka_sanshin.py — 造化三神（Cross-Cutting Concerns）

全レイヤーを横断するメタプロセス群。
「獨神にして身を隠す」= インスタンス化不可、staticアクセスのみ。

設計原則:
- アメノミナカヌシ: 座標系（不変の評価軸と閾値）
- タカミムスビ: 生成起動権限（Forward Passの許可）
- カミムスビ: 修復起動権限（Repair/Recoveryの許可）

注意:
- layers.py の造化三神（埋め込み層）とは異なる責務
- こちらは「権限管理」、あちらは「埋め込み」
"""

from __future__ import annotations
import uuid
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum


# ============================================================
# アメノミナカヌシ（天之御中主）= Global Coordinate System
# ============================================================

class AmeNoMinakaNushi:
    """
    全レイヤーが参照する不変の座標系。
    推論パイプライン全体の「真ん中」を定義する。

    設計制約:
    - インスタンス化不可（__init__で例外）
    - 全フィールドはクラス変数（immutable dict）
    - staticメソッドでのみアクセス
    - 実行時の値変更は禁止（frozen）

    注意:
    - layers.py の AmenominakanushiPositionalEncoding（位置符号化）とは別物
    - こちらは推論パイプラインの座標系・閾値を管理する横断プロセス
    """

    # --- 不変の評価軸（全レイヤー共通） ---
    COORDINATE_AXES: Dict[str, str] = {
        "V":          "論理的整合性",      # Verification
        "C_causal":   "因果的妥当性",      # Causal Consistency
        "C_chaos":    "創造的逸脱",        # Creative Chaos
        "mythic":     "原型的共鳴",        # Mythic Resonance
        "safety":     "安全性",            # Safety
    }

    # --- 全レイヤーで使用する閾値の「原点」 ---
    ORIGIN: Dict[str, Union[float, int]] = {
        # === 評価閾値 ===
        "V_threshold":       0.7,   # これ以上でCOMMIT
        "safety_floor":      0.0,   # これ以下で即HALT
        "stability_floor":   0.3,   # stability_logitsの下限（これ以下でHALT）
        "repair_budget":     4,     # REPAIRループ上限（回）
        "chaos_ceiling":     0.95,  # 創造的逸脱の天井

        # === 既存config.pyから統合（将来移行） ===
        "hiruko_unknown_threshold":   0.3,   # UnknownType率の閾値
        "hiruko_unstable_threshold":  0.2,   # UnstableUnion率の閾値
        "naobi_error_threshold":      0.5,   # 直毘神のエラー閾値
    }

    def __init__(self):
        raise RuntimeError("獨神にして身を隠す — 直接生成不可")

    @staticmethod
    def get_axis(name: str) -> str:
        """評価軸の名称を取得"""
        if name not in AmeNoMinakaNushi.COORDINATE_AXES:
            raise KeyError(f"未知の評価軸: {name}")
        return AmeNoMinakaNushi.COORDINATE_AXES[name]

    @staticmethod
    def get_origin(param: str) -> Union[float, int]:
        """原点パラメータを取得"""
        if param not in AmeNoMinakaNushi.ORIGIN:
            raise KeyError(f"未知の原点パラメータ: {param}")
        return AmeNoMinakaNushi.ORIGIN[param]

    @staticmethod
    def get_all_axes() -> Dict[str, str]:
        """全評価軸を取得（コピーを返す）"""
        return dict(AmeNoMinakaNushi.COORDINATE_AXES)

    @staticmethod
    def get_all_origins() -> Dict[str, Union[float, int]]:
        """全原点パラメータを取得（コピーを返す）"""
        return dict(AmeNoMinakaNushi.ORIGIN)


# ============================================================
# タカミムスビ（高御産巣日）= Generative Authority
# ============================================================

class TicketStatus(Enum):
    """チケットの状態"""
    VALID = "valid"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass(frozen=True)
class ForwardPassTicket:
    """
    Forward Passチケット。
    天の御柱プロトコルの各ステージ遷移に必要。
    チケットなしにはステージが進まない。

    frozen=True: 発行後の改竄防止
    """
    ticket_id: str
    stage: str
    granted_by: str          # 常に "takami_musubi"
    timestamp: float         # time.time()
    expires_in_seconds: int  # デフォルト30秒


class TakamiMusubi:
    """
    生成（ムスビ = 産霊）の起動権限。
    Forward Passを許可するかどうかの判定。
    「高」= 上位から下位への指令。

    設計制約:
    - インスタンス化不可
    - 全メソッドstatic
    - チケット発行が唯一の副作用

    注意:
    - layers.py の TakamimusubiTokenEmbedding（トークン埋め込み）とは別物
    - こちらは推論の起動権限を管理する横断プロセス
    """

    # 最近のリクエストハッシュ（重複防止用、クラス変数）
    _recent_request_hashes: List[str] = []
    _max_recent: int = 10

    def __init__(self):
        raise RuntimeError("獨神にして身を隠す — 直接生成不可")

    @staticmethod
    def authorize_generation(context: dict) -> bool:
        """
        推論リクエストを受けた時、生成を開始してよいか判定。
        全レイヤーの事前条件チェック。

        Parameters:
            context: 以下のキーを含むdict
                - safety_status: str ("ACTIVE" | "BLOCKED")
                - resource_available: bool
                - query: dict | None
                - request_hash: str (オプション、重複チェック用)

        Returns:
            bool: 生成を許可するか
        """
        checks = [
            context.get("safety_status") != "BLOCKED",
            context.get("resource_available", False),
            context.get("query") is not None,
        ]

        # 重複リクエスト防止
        req_hash = context.get("request_hash")
        if req_hash and req_hash in TakamiMusubi._recent_request_hashes:
            checks.append(False)

        return all(checks)

    @staticmethod
    def grant_forward_pass(
        stage: str,
        expires_in_seconds: int = 30,
    ) -> ForwardPassTicket:
        """
        天の御柱の各段階に対してForward Passチケットを発行。

        Parameters:
            stage: ステージ識別子 ("attempt_0", "attempt_1", ...)
            expires_in_seconds: 有効期限（秒）

        Returns:
            ForwardPassTicket: 発行されたチケット
        """
        return ForwardPassTicket(
            ticket_id=str(uuid.uuid4()),
            stage=stage,
            granted_by="takami_musubi",
            timestamp=time.time(),
            expires_in_seconds=expires_in_seconds,
        )

    @staticmethod
    def validate_ticket(ticket: ForwardPassTicket) -> TicketStatus:
        """
        チケットの有効性を検証。

        Returns:
            TicketStatus: VALID / EXPIRED / REVOKED
        """
        elapsed = time.time() - ticket.timestamp
        if elapsed > ticket.expires_in_seconds:
            return TicketStatus.EXPIRED
        return TicketStatus.VALID

    @staticmethod
    def record_request(request_hash: str) -> None:
        """重複防止用にリクエストハッシュを記録"""
        TakamiMusubi._recent_request_hashes.append(request_hash)
        if len(TakamiMusubi._recent_request_hashes) > TakamiMusubi._max_recent:
            TakamiMusubi._recent_request_hashes.pop(0)

    @staticmethod
    def clear_request_history() -> None:
        """リクエスト履歴をクリア（テスト用）"""
        TakamiMusubi._recent_request_hashes.clear()


# ============================================================
# カミムスビ（神産巣日）= Restorative Authority
# ============================================================

@dataclass(frozen=True)
class RepairTicket:
    """修復チケット"""
    ticket_id: str
    action: str              # "REPAIR" | "HALT"
    remaining_budget: int
    granted_by: str          # 常に "kami_musubi"
    reason: Optional[str] = None


class KamiMusubi:
    """
    結合・復活（ムスビ = 産霊）の権限。
    REPAIR / Recovery を許可する。

    古事記でカミムスビはオオクニヌシの復活を許可した神。
    → 障害復旧の最終権限。

    設計制約:
    - インスタンス化不可
    - 全メソッドstatic
    - repair_budgetはアメノミナカヌシから取得（自身では保持しない）

    注意:
    - layers.py の KamimusubiTypeHierarchyEmbedding（型階層埋め込み）とは別物
    - こちらは修復権限を管理する横断プロセス
    """

    def __init__(self):
        raise RuntimeError("獨神にして身を隠す — 直接生成不可")

    @staticmethod
    def authorize_repair(failure_context: dict) -> RepairTicket:
        """
        蛭子検知が発火した後、直毘神（修復プロセス）を
        起動してよいか判定。

        Parameters:
            failure_context: 以下のキーを含むdict
                - repair_count: int (これまでの修復回数)
                - hints: List[str] (修復ヒント、オプション)
                - error_type: str (エラー種別、オプション)

        Returns:
            RepairTicket: action="REPAIR" or "HALT"
        """
        budget = AmeNoMinakaNushi.get_origin("repair_budget")
        current_count = failure_context.get("repair_count", 0)

        if current_count >= budget:
            return RepairTicket(
                ticket_id=str(uuid.uuid4()),
                action="HALT",
                remaining_budget=0,
                granted_by="kami_musubi",
                reason="repair_budget_exhausted",
            )

        return RepairTicket(
            ticket_id=str(uuid.uuid4()),
            action="REPAIR",
            remaining_budget=int(budget) - current_count - 1,
            granted_by="kami_musubi",
        )

    @staticmethod
    def authorize_resurrection(context: dict) -> bool:
        """
        オオクニヌシの復活パターン。
        完全に失敗したプロセスを別コンテキストで再起動する。
        = Shadow Solve の起動権限。

        Parameters:
            context: 以下のキーを含むdict
                - primary_failed: bool
                - shadow_available: bool
                - safety_status: str

        Returns:
            bool: Shadow Solveを起動してよいか
        """
        return (
            context.get("primary_failed", False)
            and context.get("shadow_available", True)
            and context.get("safety_status") != "BLOCKED"
        )


# ============================================================
# テスト用ユーティリティ
# ============================================================

def test_zoka_sanshin():
    """造化三神の基本動作テスト"""
    print("=== 造化三神テスト ===\n")

    # --- アメノミナカヌシ ---
    print("【アメノミナカヌシ】")
    try:
        obj = AmeNoMinakaNushi()
        print("  ERROR: インスタンス化できてしまった")
    except RuntimeError as e:
        print(f"  OK: {e}")

    print(f"  V軸: {AmeNoMinakaNushi.get_axis('V')}")
    print(f"  V_threshold: {AmeNoMinakaNushi.get_origin('V_threshold')}")
    print(f"  repair_budget: {AmeNoMinakaNushi.get_origin('repair_budget')}")

    # --- タカミムスビ ---
    print("\n【タカミムスビ】")
    ctx = {
        "safety_status": "ACTIVE",
        "resource_available": True,
        "query": {"prompt": "struct Point2D"},
    }
    print(f"  authorize_generation: {TakamiMusubi.authorize_generation(ctx)}")

    ctx["safety_status"] = "BLOCKED"
    print(f"  (BLOCKED時): {TakamiMusubi.authorize_generation(ctx)}")

    ticket = TakamiMusubi.grant_forward_pass("attempt_0")
    print(f"  ticket: {ticket.ticket_id[:8]}... stage={ticket.stage}")
    print(f"  validate: {TakamiMusubi.validate_ticket(ticket)}")

    # --- カミムスビ ---
    print("\n【カミムスビ】")
    repair_ticket = KamiMusubi.authorize_repair({"repair_count": 0})
    print(f"  repair_count=0: action={repair_ticket.action}, remaining={repair_ticket.remaining_budget}")

    repair_ticket = KamiMusubi.authorize_repair({"repair_count": 4})
    print(f"  repair_count=4: action={repair_ticket.action}, reason={repair_ticket.reason}")

    resurrection_ctx = {
        "primary_failed": True,
        "shadow_available": True,
        "safety_status": "ACTIVE",
    }
    print(f"  resurrection: {KamiMusubi.authorize_resurrection(resurrection_ctx)}")

    print("\n=== テスト完了 ===")


if __name__ == "__main__":
    test_zoka_sanshin()
