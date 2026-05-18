"""
Julia-no-Mikoto: 古事記LLM設定 (Kojiki LLM Configuration)

古事記の神々をJuliaの型システム・多重ディスパッチにマッピング

=== v0.3.0: 五層アーキテクチャ対応 ===

config.py は以下を管理:
1. KojikiConfig: モデル内部（layers.py）の設定
2. FiveLayerConfig: パイプライン層（五層アーキテクチャ）の設定

注意:
- 評価閾値等は AmeNoMinakaNushi.ORIGIN が正（zoka_sanshin.py）
- 本ファイルの閾値は既存互換性のため残存（非推奨）
- 新規コードは AmeNoMinakaNushi.get_origin() を使用すること
"""

from dataclasses import dataclass, field
from enum import IntEnum, Enum
from typing import Dict, Optional, Any


class TokenRole(IntEnum):
    """
    トークンの役割タグ

    コードの各トークンがどのような役割を持つかを定義
    Multiple Dispatch Attentionでのマスキングに使用
    """
    UNKNOWN = 0
    FUNCTION_NAME = 1      # 関数名 (add, multiply, ...)
    VARIABLE = 2           # 変数 (x, y, result, ...)
    TYPE_ANNOTATION = 3    # 型注釈 (::Int64, ::Array{Float64}, ...)
    KEYWORD = 4            # キーワード (function, struct, if, ...)
    OPERATOR = 5           # 演算子 (+, -, *, ...)
    LITERAL = 6            # リテラル (42, 3.14, "hello", ...)
    PUNCTUATION = 7        # 句読点 (, ; ( ) { } ...)


# 型カテゴリの定義（計128枠）
TYPE_CATEGORIES: Dict[int, str] = {
    # === 標準型（0-63） ===
    # 数値型
    0: "Any",
    1: "Number",
    2: "Real",
    3: "Integer",
    4: "Int64",
    5: "Int32",
    6: "Int16",
    7: "Int8",
    8: "UInt64",
    9: "UInt32",
    10: "AbstractFloat",
    11: "Float64",
    12: "Float32",
    13: "Float16",
    14: "Complex",
    15: "Rational",
    16: "Signed",
    17: "Unsigned",
    18: "BigInt",
    19: "BigFloat",

    # コレクション型
    20: "AbstractArray",
    21: "Array",
    22: "Vector",
    23: "Matrix",
    24: "AbstractDict",
    25: "Dict",
    26: "AbstractSet",
    27: "Set",
    28: "Tuple",
    29: "NamedTuple",
    30: "Pair",
    31: "AbstractRange",
    32: "UnitRange",
    33: "StepRange",

    # 文字列・シンボル
    34: "AbstractString",
    35: "String",
    36: "Symbol",
    37: "Char",
    38: "SubString",
    39: "Regex",

    # 関数・型
    40: "Function",
    41: "Type",
    42: "DataType",
    43: "UnionAll",
    44: "Union",
    45: "Callable",

    # その他
    50: "Nothing",
    51: "Missing",
    52: "Bool",
    53: "IO",
    54: "Module",
    55: "Expr",
    56: "LineNumberNode",
    57: "QuoteNode",
    58: "Ref",
    59: "Ptr",
    60: "Exception",
    61: "Task",
    62: "Channel",
    63: "Condition",

    # === ユーザー定義型カテゴリ（64-95） ===
    64: "UserDefinedStruct",      # struct Foo ... end
    65: "UserDefinedMutable",     # mutable struct Bar ... end
    66: "UserDefinedAbstract",    # abstract type Baz end
    67: "UserDefinedPrimitive",   # primitive type Qux 8 end
    68: "UserDefinedParametric",  # struct Container{T} ... end
    69: "UserDefinedSingleton",   # struct Singleton end (no fields)

    # === 特殊カテゴリ（96-127） ===
    96: "UnknownType",            # 推論不能
    97: "UnstableUnion",          # Union{A, B}（型不安定）
    98: "TypeParameter",          # T, S などの型パラメータ
    99: "Vararg",                 # Vararg{T}
    100: "TypeVar",               # where T
    101: "Bottom",                # Union{} (空の型)
    102: "TypeofVararg",          # typeof(Vararg)

    # 予約枠（103-127）
}

# 型ID → 型名の逆引き
TYPE_ID_TO_NAME: Dict[int, str] = TYPE_CATEGORIES

# 型名 → 型IDの順引き
TYPE_NAME_TO_ID: Dict[str, int] = {v: k for k, v in TYPE_CATEGORIES.items()}


# 型の具体度マッピング (0=Any/最抽象, 1=Abstract, 2=Concrete)
TYPE_SPECIFICITY: Dict[int, int] = {
    0: 0,   # Any → 最も抽象
    1: 1,   # Number → 抽象
    2: 1,   # Real → 抽象
    3: 1,   # Integer → 抽象
    4: 2,   # Int64 → 具体
    5: 2,   # Int32 → 具体
    6: 2,   # Int16 → 具体
    7: 2,   # Int8 → 具体
    8: 2,   # UInt64 → 具体
    9: 2,   # UInt32 → 具体
    10: 1,  # AbstractFloat → 抽象
    11: 2,  # Float64 → 具体
    12: 2,  # Float32 → 具体
    13: 2,  # Float16 → 具体
    14: 2,  # Complex → 具体
    15: 2,  # Rational → 具体
    16: 1,  # Signed → 抽象
    17: 1,  # Unsigned → 抽象
    18: 2,  # BigInt → 具体
    19: 2,  # BigFloat → 具体
    20: 1,  # AbstractArray → 抽象
    21: 2,  # Array → 具体
    22: 2,  # Vector → 具体
    23: 2,  # Matrix → 具体
    24: 1,  # AbstractDict → 抽象
    25: 2,  # Dict → 具体
    26: 1,  # AbstractSet → 抽象
    27: 2,  # Set → 具体
    28: 2,  # Tuple → 具体
    29: 2,  # NamedTuple → 具体
    30: 2,  # Pair → 具体
    31: 1,  # AbstractRange → 抽象
    32: 2,  # UnitRange → 具体
    33: 2,  # StepRange → 具体
    34: 1,  # AbstractString → 抽象
    35: 2,  # String → 具体
    36: 2,  # Symbol → 具体
    37: 2,  # Char → 具体
    38: 2,  # SubString → 具体
    39: 2,  # Regex → 具体
    40: 1,  # Function → 抽象
    41: 1,  # Type → 抽象
    42: 2,  # DataType → 具体
    43: 1,  # UnionAll → 抽象
    44: 1,  # Union → 抽象
    45: 1,  # Callable → 抽象
    50: 2,  # Nothing → 具体
    51: 2,  # Missing → 具体
    52: 2,  # Bool → 具体
    53: 1,  # IO → 抽象
    54: 2,  # Module → 具体
    55: 2,  # Expr → 具体
    56: 2,  # LineNumberNode → 具体
    57: 2,  # QuoteNode → 具体
    58: 2,  # Ref → 具体
    59: 2,  # Ptr → 具体
    60: 1,  # Exception → 抽象
    61: 2,  # Task → 具体
    62: 2,  # Channel → 具体
    63: 2,  # Condition → 具体
    64: 2,  # UserDefinedStruct → 具体
    65: 2,  # UserDefinedMutable → 具体
    66: 1,  # UserDefinedAbstract → 抽象
    67: 2,  # UserDefinedPrimitive → 具体
    68: 2,  # UserDefinedParametric → 具体
    69: 2,  # UserDefinedSingleton → 具体
    96: 0,  # UnknownType → 最抽象
    97: 1,  # UnstableUnion → 抽象（警告対象）
    98: 1,  # TypeParameter → 抽象
    99: 1,  # Vararg → 抽象
    100: 1, # TypeVar → 抽象
    101: 0, # Bottom → 特殊
    102: 1, # TypeofVararg → 抽象
}


# 型階層の深さマッピング
TYPE_DEPTH: Dict[int, int] = {
    0: 0,   # Any → 深さ0
    1: 1,   # Number → 深さ1
    2: 2,   # Real → 深さ2
    3: 3,   # Integer → 深さ3
    4: 4,   # Int64 → 深さ4
    5: 4,   # Int32 → 深さ4
    6: 4,   # Int16 → 深さ4
    7: 4,   # Int8 → 深さ4
    8: 4,   # UInt64 → 深さ4
    9: 4,   # UInt32 → 深さ4
    10: 2,  # AbstractFloat → 深さ2
    11: 3,  # Float64 → 深さ3
    12: 3,  # Float32 → 深さ3
    13: 3,  # Float16 → 深さ3
    14: 2,  # Complex → 深さ2
    15: 2,  # Rational → 深さ2
    16: 2,  # Signed → 深さ2
    17: 2,  # Unsigned → 深さ2
    18: 4,  # BigInt → 深さ4
    19: 3,  # BigFloat → 深さ3
    20: 1,  # AbstractArray → 深さ1
    21: 2,  # Array → 深さ2
    22: 3,  # Vector → 深さ3
    23: 3,  # Matrix → 深さ3
    24: 1,  # AbstractDict → 深さ1
    25: 2,  # Dict → 深さ2
    26: 1,  # AbstractSet → 深さ1
    27: 2,  # Set → 深さ2
    28: 1,  # Tuple → 深さ1
    29: 2,  # NamedTuple → 深さ2
    30: 1,  # Pair → 深さ1
    31: 1,  # AbstractRange → 深さ1
    32: 2,  # UnitRange → 深さ2
    33: 2,  # StepRange → 深さ2
    34: 1,  # AbstractString → 深さ1
    35: 2,  # String → 深さ2
    36: 1,  # Symbol → 深さ1
    37: 1,  # Char → 深さ1
    38: 3,  # SubString → 深さ3
    39: 2,  # Regex → 深さ2
    40: 1,  # Function → 深さ1
    41: 1,  # Type → 深さ1
    42: 2,  # DataType → 深さ2
    43: 2,  # UnionAll → 深さ2
    44: 1,  # Union → 深さ1
    45: 1,  # Callable → 深さ1
    50: 1,  # Nothing → 深さ1
    51: 1,  # Missing → 深さ1
    52: 1,  # Bool → 深さ1
    53: 1,  # IO → 深さ1
    54: 1,  # Module → 深さ1
    55: 1,  # Expr → 深さ1
    56: 2,  # LineNumberNode → 深さ2
    57: 2,  # QuoteNode → 深さ2
    58: 1,  # Ref → 深さ1
    59: 1,  # Ptr → 深さ1
    60: 1,  # Exception → 深さ1
    61: 1,  # Task → 深さ1
    62: 1,  # Channel → 深さ1
    63: 1,  # Condition → 深さ1
    64: 2,  # UserDefinedStruct → 深さ2
    65: 2,  # UserDefinedMutable → 深さ2
    66: 1,  # UserDefinedAbstract → 深さ1
    67: 2,  # UserDefinedPrimitive → 深さ2
    68: 2,  # UserDefinedParametric → 深さ2
    69: 2,  # UserDefinedSingleton → 深さ2
    96: 0,  # UnknownType → 深さ0
    97: 1,  # UnstableUnion → 深さ1
    98: 1,  # TypeParameter → 深さ1
    99: 1,  # Vararg → 深さ1
    100: 1, # TypeVar → 深さ1
    101: 0, # Bottom → 深さ0
    102: 1, # TypeofVararg → 深さ1
}


@dataclass
class KojikiConfig:
    """
    古事記LLM設定（v2）

    Julia言語特化型LLMの設定クラス。
    神話の構造とJuliaの型システムをマッピング。

    目標スペック（プロトタイプ）:
    - パラメータ数: 20M〜50M（RTX 3060で学習可能）
    - コンテキスト長: 2048トークン
    """

    # === 語彙設定 ===
    vocab_size: int = 8000          # トークン語彙サイズ
    type_vocab_size: int = 128      # v2: 64 → 128 (型カテゴリ)
    hash_bucket_size: int = 1024    # v2: ユーザー定義型用ハッシュバケット

    # === モデル次元 ===
    d_model: int = 512              # モデル次元
    n_heads: int = 8                # Attentionヘッド数
    n_generations: int = 6          # 神世七代層の数（Transformer層数）
    d_ff: int = 2048                # Feed-Forward中間次元

    # === シーケンス ===
    max_seq_len: int = 2048         # 最大シーケンス長

    # === ドロップアウト ===
    dropout: float = 0.1

    # === 型階層 ===
    type_hierarchy_depth: int = 8   # v2: 5 → 8

    # === 特殊トークン ===
    pad_token_id: int = 0
    eos_token_id: int = 1
    unk_token_id: int = 2
    bos_token_id: int = 3

    # === トークン役割 ===
    num_token_roles: int = 8        # TokenRoleの数

    # === 学習設定 ===
    learning_rate: float = 1e-4
    weight_decay: float = 0.01
    warmup_steps: int = 1000
    max_steps: int = 100000

    # === 損失重み ===
    loss_weight_token: float = 1.0
    loss_weight_type: float = 0.8   # v2: 0.5 → 0.8（推論時に重要）
    loss_weight_stability: float = 0.3
    loss_weight_simd: float = 0.1
    loss_weight_diff: float = 0.1
    loss_weight_error: float = 0.2

    # === 天の御柱（Amenomihashira）プロトコル設定 ===
    amenomihashira_max_retries: int = 3          # ヒルコ発生時の最大リトライ
    hiruko_unknown_threshold: float = 0.3        # UnknownType(96)率の閾値
    hiruko_unstable_threshold: float = 0.2       # UnstableUnion(97)率の閾値
    naobi_error_threshold: float = 0.5           # 直毘神のエラー閾値
    phase1_max_tokens: int = 256                 # Phase 1（イザナギ）の最大トークン数
    phase2_max_tokens: int = 256                 # Phase 2（イザナミ）の最大トークン数
    phase3_max_tokens: int = 512                 # Phase 3（万物生成）の最大トークン数

    # === 稗田阿礼 (Hieda-no-Are) 設定 ===
    hieda_no_are_enabled: bool = True             # 阿礼の有効/無効
    hieda_no_are_max_context_tokens: int = 512    # 誦習に使う最大トークン数

    def __post_init__(self):
        """設定の妥当性チェック"""
        assert self.d_model % self.n_heads == 0, \
            f"d_model ({self.d_model}) must be divisible by n_heads ({self.n_heads})"
        assert self.type_vocab_size <= 128, \
            f"type_vocab_size ({self.type_vocab_size}) exceeds maximum 128"

    @property
    def d_k(self) -> int:
        """各Attentionヘッドの次元"""
        return self.d_model // self.n_heads

    def get_loss_weights(self) -> Dict[str, float]:
        """損失関数の重み辞書を取得"""
        return {
            "token": self.loss_weight_token,
            "type": self.loss_weight_type,
            "stability": self.loss_weight_stability,
            "simd": self.loss_weight_simd,
            "diff": self.loss_weight_diff,
            "error": self.loss_weight_error,
        }


# ============================================================
# 五層アーキテクチャ設定 (v0.3.0)
# ============================================================


class TrustLevel(IntEnum):
    """
    Layer 4（海原・常世）の信頼度レベル

    外部データソースの信頼度を5段階で分類。
    """
    IMMUTABLE = 4    # 不変データ（Julia組込み型定義等）
    VERIFIED = 3     # 検証済み（公式ドキュメント等）
    CACHED = 2       # キャッシュ済み（過去セッションで検証）
    DYNAMIC = 1      # 動的取得（未検証だが信頼できるソース）
    UNTRUSTED = 0    # 未信頼（ユーザー入力等）


class VerdictType(str, Enum):
    """
    Layer 5（黄泉）の判定結果

    閻魔判定の3種類の結果。
    """
    COMMIT = "COMMIT"   # 出力確定（国が生まれた）
    REPAIR = "REPAIR"   # 修復要求（直毘神に委ねる）
    HALT = "HALT"       # 停止（蛭子 = 不正出力を流す）


class FeedbackType(str, Enum):
    """
    Layer 2（高天原）フィードバックシグナルの種類
    """
    QUALITY_SCORE = "quality_score"      # 品質スコア傾向
    VERDICT_DIST = "verdict_dist"        # 判定分布
    ERROR_PATTERN = "error_pattern"      # エラーパターン
    REPAIR_HINT = "repair_hint"          # 修復ヒント統計
    STABILITY_TREND = "stability_trend"  # 安定性傾向


class TrainingPriority(IntEnum):
    """
    学習シグナルの優先度
    """
    CRITICAL = 3   # 即時対応必要（HALT多発等）
    HIGH = 2       # 高優先度（品質低下傾向）
    MEDIUM = 1     # 中優先度（軽微な問題）
    LOW = 0        # 低優先度（情報提供のみ）


@dataclass
class FiveLayerConfig:
    """
    五層アーキテクチャ設定

    Layer 1: 別天津神（設計原則）— AmeNoMinakaNushi.ORIGIN で定義
    Layer 2: 高天原（学習パイプライン）— 本設定で管理
    Layer 3: 葦原中国（推論ランタイム）— 本設定で管理
    Layer 4: 海原・常世（外部データ）— 本設定で管理
    Layer 5: 根の国・黄泉（評価）— 本設定で管理

    造化三神: zoka_sanshin.py で管理（横断プロセス）
    """

    # ================================================================
    # Layer 2: 高天原（学習パイプライン）
    # ================================================================

    # フィードバック収集設定
    feedback_window_size: int = 100            # 品質トレンドウィンドウサイズ
    feedback_max_signals: int = 1000           # 保持する最大シグナル数
    error_pattern_threshold: int = 5           # エラーパターン検出閾値

    # 学習シグナル設定
    quality_alert_threshold: float = 0.5       # 品質アラート閾値
    halt_rate_alert_threshold: float = 0.2     # HALT率アラート閾値

    # ================================================================
    # Layer 3: 葦原中国（推論ランタイム）
    # ================================================================

    # 天御柱4Phaseオーケストレータ
    max_repair_attempts: int = 4               # 最大修復試行回数
    phase_timeout_ms: int = 30000              # 各フェーズのタイムアウト（ms）
    enable_parallel_generation: bool = False   # 並列生成の有効化

    # 推論パイプライン
    default_temperature: float = 0.7           # デフォルト温度
    default_top_p: float = 0.9                 # デフォルトtop_p
    max_output_tokens: int = 1024              # 最大出力トークン数

    # ================================================================
    # Layer 4: 海原・常世（外部データソース）
    # ================================================================

    # キャッシュ設定
    cache_ttl_seconds: int = 3600              # キャッシュTTL（秒）
    max_cache_entries: int = 1000              # 最大キャッシュエントリ数

    # 外部データ取得
    fetch_timeout_ms: int = 5000               # 外部取得タイムアウト（ms）
    max_external_context_tokens: int = 512     # 外部コンテキスト最大トークン数

    # 信頼度設定
    default_trust_level: TrustLevel = TrustLevel.DYNAMIC
    min_trust_for_context: TrustLevel = TrustLevel.DYNAMIC  # コンテキスト注入の最低信頼度

    # ================================================================
    # Layer 5: 根の国・黄泉（評価・フィードバック）
    # ================================================================

    # YomiArchive設定
    max_archive_records: int = 1000            # 最大アーカイブレコード数

    # 黄泉比良坂（通信制約）
    max_text_size: int = 100 * 1024            # 最大テキストサイズ（100KB）
    max_type_ids_length: int = 10000           # 最大type_ids長
    max_repair_hints: int = 10                 # 最大修復ヒント数
    max_repair_hint_length: int = 500          # 修復ヒント最大長

    # 監査ログ
    enable_audit_log: bool = True              # 監査ログ有効化
    max_audit_log_size: int = 1000             # 監査ログ最大サイズ

    # ================================================================
    # 横断設定（造化三神関連）
    # ================================================================

    # 注意: 以下の閾値は AmeNoMinakaNushi.ORIGIN が正
    # ここでは参照用のデフォルト値のみ定義

    # 評価閾値（参照用 — 実際は AmeNoMinakaNushi.ORIGIN を使用）
    v_threshold: float = 0.7                   # COMMIT判定閾値
    safety_floor: float = 0.0                  # 安全性下限（即HALT）
    stability_floor: float = 0.3               # 安定性下限（即HALT）
    repair_budget: int = 4                     # 修復予算
    chaos_ceiling: float = 0.95                # 創造的逸脱上限

    def __post_init__(self):
        """設定の妥当性チェック"""
        assert 0.0 <= self.v_threshold <= 1.0, \
            f"v_threshold must be in [0, 1], got {self.v_threshold}"
        assert 0.0 <= self.safety_floor <= 1.0, \
            f"safety_floor must be in [0, 1], got {self.safety_floor}"
        assert self.repair_budget >= 0, \
            f"repair_budget must be non-negative, got {self.repair_budget}"

    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書として取得"""
        return {
            # Layer 2
            "feedback_window_size": self.feedback_window_size,
            "feedback_max_signals": self.feedback_max_signals,
            "error_pattern_threshold": self.error_pattern_threshold,
            "quality_alert_threshold": self.quality_alert_threshold,
            "halt_rate_alert_threshold": self.halt_rate_alert_threshold,
            # Layer 3
            "max_repair_attempts": self.max_repair_attempts,
            "phase_timeout_ms": self.phase_timeout_ms,
            "enable_parallel_generation": self.enable_parallel_generation,
            "default_temperature": self.default_temperature,
            "default_top_p": self.default_top_p,
            "max_output_tokens": self.max_output_tokens,
            # Layer 4
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "max_cache_entries": self.max_cache_entries,
            "fetch_timeout_ms": self.fetch_timeout_ms,
            "max_external_context_tokens": self.max_external_context_tokens,
            "default_trust_level": self.default_trust_level.name,
            "min_trust_for_context": self.min_trust_for_context.name,
            # Layer 5
            "max_archive_records": self.max_archive_records,
            "max_text_size": self.max_text_size,
            "max_type_ids_length": self.max_type_ids_length,
            "max_repair_hints": self.max_repair_hints,
            "enable_audit_log": self.enable_audit_log,
            "max_audit_log_size": self.max_audit_log_size,
            # 横断
            "v_threshold": self.v_threshold,
            "safety_floor": self.safety_floor,
            "stability_floor": self.stability_floor,
            "repair_budget": self.repair_budget,
            "chaos_ceiling": self.chaos_ceiling,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FiveLayerConfig":
        """辞書から設定を構築"""
        # TrustLevelの変換
        if "default_trust_level" in data and isinstance(data["default_trust_level"], str):
            data["default_trust_level"] = TrustLevel[data["default_trust_level"]]
        if "min_trust_for_context" in data and isinstance(data["min_trust_for_context"], str):
            data["min_trust_for_context"] = TrustLevel[data["min_trust_for_context"]]
        return cls(**data)


# デフォルト設定インスタンス
DEFAULT_CONFIG = KojikiConfig()
DEFAULT_FIVE_LAYER_CONFIG = FiveLayerConfig()
