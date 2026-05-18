"""
layer4_unabara.py — 海原・常世（Layer 4 外部データソース）

Layer 4: 外部データソース
推論ランタイム（Layer 3）に外部からデータを供給する。

=== 3分割アーキテクチャ ===

4a: 常世（Tokoyo）= Stable External Storage
├── 学習済みモデルの知識ベース
├── 静的リファレンスデータ
├── システム設定・Config
└── 「不老不死の国」= 変化しないデータ

4b: 海原（Unabara）= Dynamic External Fetch
├── Web検索・RAG
├── API呼び出し
├── リアルタイムデータ取得
└── 「荒ぶる海」= 変動的・不確実なデータ

4c: 綿津見（Watatsumi）= Gateway/Protocol
├── 外部データの正規化
├── 信頼度スコアの付与
├── キャッシュ管理
└── 「海神」= 海の門番

設計原則:
- 常世: 変更不可、キャッシュ永続、高信頼
- 海原: 変動的、キャッシュ短命、信頼度可変
- 綿津見: 両者のゲートキーパー、正規化担当
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Set
import hashlib
import time
import re


# ============================================================
# 信頼度レベル
# ============================================================

class TrustLevel(Enum):
    """外部データの信頼度レベル"""
    IMMUTABLE = "immutable"    # 常世: 不変データ（設定、組み込み知識）
    VERIFIED = "verified"      # 検証済み（信頼できるソース）
    CACHED = "cached"          # キャッシュ済み（前回取得時は検証済み）
    DYNAMIC = "dynamic"        # 動的取得（リアルタイム、未検証）
    UNTRUSTED = "untrusted"    # 信頼できない（外部API応答、ユーザー入力）


@dataclass
class ExternalData:
    """
    外部から取得したデータの統一形式

    Attributes:
        content: データ内容
        source: データソース識別子
        trust_level: 信頼度レベル
        timestamp: 取得時刻
        ttl_seconds: 有効期限（秒）
        metadata: 追加メタデータ
    """
    content: Any
    source: str
    trust_level: TrustLevel
    timestamp: float = field(default_factory=time.time)
    ttl_seconds: int = 3600  # デフォルト1時間
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """有効期限切れかどうか"""
        if self.trust_level == TrustLevel.IMMUTABLE:
            return False  # 不変データは期限切れなし
        return time.time() > self.timestamp + self.ttl_seconds

    def get_age_seconds(self) -> float:
        """データの経過時間（秒）"""
        return time.time() - self.timestamp


# ============================================================
# 4a: 常世（Tokoyo）= Stable External Storage
# ============================================================

class Tokoyo:
    """
    常世（Tokoyo）= 不変の外部ストレージ

    古事記の常世:
        海の彼方にある「不老不死の国」。
        時間が止まった永遠の世界。

    責務:
    - 静的リファレンスデータの保持
    - Julia型システムの組み込み知識
    - システム設定の管理
    - 変更されないデータの永続キャッシュ

    設計原則:
    - データは一度登録したら変更不可
    - 信頼度は常に IMMUTABLE
    - TTLは無限（期限切れなし）
    """

    # Julia組み込み型の知識ベース（不変）
    JULIA_BUILTIN_TYPES: Dict[str, Dict[str, Any]] = {
        # 数値型
        "Int": {"category": "numeric", "bits": 64, "signed": True},
        "Int8": {"category": "numeric", "bits": 8, "signed": True},
        "Int16": {"category": "numeric", "bits": 16, "signed": True},
        "Int32": {"category": "numeric", "bits": 32, "signed": True},
        "Int64": {"category": "numeric", "bits": 64, "signed": True},
        "Int128": {"category": "numeric", "bits": 128, "signed": True},
        "UInt": {"category": "numeric", "bits": 64, "signed": False},
        "UInt8": {"category": "numeric", "bits": 8, "signed": False},
        "UInt16": {"category": "numeric", "bits": 16, "signed": False},
        "UInt32": {"category": "numeric", "bits": 32, "signed": False},
        "UInt64": {"category": "numeric", "bits": 64, "signed": False},
        "UInt128": {"category": "numeric", "bits": 128, "signed": False},
        "Float16": {"category": "numeric", "bits": 16, "floating": True},
        "Float32": {"category": "numeric", "bits": 32, "floating": True},
        "Float64": {"category": "numeric", "bits": 64, "floating": True},
        "Bool": {"category": "numeric", "bits": 8},
        "Char": {"category": "character", "bits": 32},
        # コレクション型
        "Array": {"category": "collection", "parametric": True},
        "Vector": {"category": "collection", "parametric": True, "alias": "Array{T,1}"},
        "Matrix": {"category": "collection", "parametric": True, "alias": "Array{T,2}"},
        "Dict": {"category": "collection", "parametric": True},
        "Set": {"category": "collection", "parametric": True},
        "Tuple": {"category": "collection", "parametric": True},
        "NamedTuple": {"category": "collection", "parametric": True},
        # 文字列型
        "String": {"category": "string", "mutable": False},
        "SubString": {"category": "string", "mutable": False},
        # その他
        "Nothing": {"category": "singleton", "value": "nothing"},
        "Missing": {"category": "singleton", "value": "missing"},
        "Any": {"category": "abstract", "top_type": True},
        "Function": {"category": "abstract"},
    }

    # Julia標準ライブラリのモジュール
    JULIA_STDLIB_MODULES: Set[str] = {
        "Base", "Core", "Main",
        "LinearAlgebra", "Statistics", "Random",
        "Dates", "Printf", "Logging",
        "Test", "Pkg", "REPL",
        "Distributed", "SharedArrays", "Threads",
        "FileWatching", "Mmap", "Serialization",
    }

    def __init__(self):
        self._custom_registry: Dict[str, ExternalData] = {}

    def get_builtin_type(self, type_name: str) -> Optional[ExternalData]:
        """Julia組み込み型の情報を取得"""
        if type_name in self.JULIA_BUILTIN_TYPES:
            return ExternalData(
                content=self.JULIA_BUILTIN_TYPES[type_name],
                source="tokoyo:builtin_types",
                trust_level=TrustLevel.IMMUTABLE,
                ttl_seconds=-1,  # 無期限
                metadata={"type_name": type_name},
            )
        return None

    def is_stdlib_module(self, module_name: str) -> bool:
        """標準ライブラリのモジュールかどうか"""
        return module_name in self.JULIA_STDLIB_MODULES

    def register_immutable(self, key: str, content: Any, metadata: Optional[dict] = None) -> bool:
        """
        不変データを登録。一度登録したら変更不可。

        Returns:
            bool: 登録成功（既存キーがある場合はFalse）
        """
        if key in self._custom_registry:
            return False  # 既存キーは上書き不可

        self._custom_registry[key] = ExternalData(
            content=content,
            source=f"tokoyo:custom:{key}",
            trust_level=TrustLevel.IMMUTABLE,
            ttl_seconds=-1,
            metadata=metadata or {},
        )
        return True

    def get(self, key: str) -> Optional[ExternalData]:
        """カスタム登録データを取得"""
        return self._custom_registry.get(key)

    def get_all_builtin_types(self) -> List[str]:
        """全組み込み型名を取得"""
        return list(self.JULIA_BUILTIN_TYPES.keys())


# ============================================================
# 4b: 海原（Unabara）= Dynamic External Fetch
# ============================================================

class UnabaraSource(ABC):
    """
    海原のデータソース抽象基底クラス

    海原は「荒ぶる海」であり、様々なソースから
    動的にデータを取得する。各ソースはこのインターフェースを実装する。
    """

    @abstractmethod
    def fetch(self, query: dict) -> Optional[ExternalData]:
        """
        クエリに基づいてデータを取得

        Parameters:
            query: 検索クエリ
                - prompt: str (検索キーワード)
                - filters: dict (オプション)

        Returns:
            ExternalData or None
        """
        pass

    @abstractmethod
    def get_source_id(self) -> str:
        """ソース識別子を返す"""
        pass


class JuliaDocSource(UnabaraSource):
    """
    Juliaドキュメントからの情報取得（シミュレート）

    実際のWeb検索/RAGの代わりに、
    ローカルの知識ベースから検索する。
    """

    # シミュレートされたドキュメントDB
    _DOC_DB: Dict[str, str] = {
        "struct": "Juliaでは`struct`キーワードで不変の複合型を定義します。フィールドは宣言後変更不可。",
        "mutable struct": "`mutable struct`は変更可能な複合型を定義します。フィールドの値を後から変更可能。",
        "function": "`function`キーワードで関数を定義します。複数のメソッドを持てます（多重ディスパッチ）。",
        "abstract type": "`abstract type`は具象型の親となる抽象型を定義します。インスタンス化不可。",
        "parametric": "Juliaの型は型パラメータを持てます。`struct Point{T} x::T; y::T end`のように定義。",
        "multiple dispatch": "Juliaは引数の型に基づいて呼び出すメソッドを決定する多重ディスパッチを採用。",
    }

    def fetch(self, query: dict) -> Optional[ExternalData]:
        prompt = query.get("prompt", "").lower()

        # キーワードマッチング
        matches = []
        for keyword, doc in self._DOC_DB.items():
            if keyword in prompt:
                matches.append(doc)

        if matches:
            return ExternalData(
                content="\n".join(matches),
                source="unabara:julia_doc",
                trust_level=TrustLevel.VERIFIED,
                ttl_seconds=86400,  # 24時間
                metadata={"query": prompt, "match_count": len(matches)},
            )
        return None

    def get_source_id(self) -> str:
        return "julia_doc"


class CodeExampleSource(UnabaraSource):
    """
    コード例のデータソース

    プロンプトに含まれるパターンに基づいて
    関連するコード例を提供する。
    """

    _EXAMPLES: Dict[str, str] = {
        "point": """
struct Point2D
    x::Float64
    y::Float64
end

function distance(p1::Point2D, p2::Point2D)
    sqrt((p1.x - p2.x)^2 + (p1.y - p2.y)^2)
end
""",
        "vector": """
struct Vec3D{T<:Real}
    x::T
    y::T
    z::T
end

Base.:+(a::Vec3D, b::Vec3D) = Vec3D(a.x + b.x, a.y + b.y, a.z + b.z)
""",
        "tree": """
abstract type AbstractTree end

struct BinaryTree{T} <: AbstractTree
    value::T
    left::Union{BinaryTree{T}, Nothing}
    right::Union{BinaryTree{T}, Nothing}
end
""",
    }

    def fetch(self, query: dict) -> Optional[ExternalData]:
        prompt = query.get("prompt", "").lower()

        for pattern, example in self._EXAMPLES.items():
            if pattern in prompt:
                return ExternalData(
                    content=example.strip(),
                    source="unabara:code_examples",
                    trust_level=TrustLevel.VERIFIED,
                    ttl_seconds=86400,
                    metadata={"pattern": pattern},
                )
        return None

    def get_source_id(self) -> str:
        return "code_examples"


class Unabara:
    """
    海原（Unabara）= 動的外部データフェッチャー

    古事記の海原:
        荒ぶる海。スサノオが支配する領域。
        予測不能で変動的な世界。

    責務:
    - 複数のソースからの動的データ取得
    - 取得結果のマージと優先度付け
    - 失敗時のフォールバック

    設計原則:
    - 結果は常に不確実（信頼度 DYNAMIC or UNTRUSTED）
    - キャッシュは短命（TTL短め）
    - ソースの追加・削除が可能
    """

    def __init__(self):
        self._sources: List[UnabaraSource] = [
            JuliaDocSource(),
            CodeExampleSource(),
        ]

    def add_source(self, source: UnabaraSource) -> None:
        """データソースを追加"""
        self._sources.append(source)

    def remove_source(self, source_id: str) -> bool:
        """データソースを削除"""
        original_len = len(self._sources)
        self._sources = [s for s in self._sources if s.get_source_id() != source_id]
        return len(self._sources) < original_len

    def fetch_all(self, query: dict) -> List[ExternalData]:
        """
        全ソースからデータを取得

        Parameters:
            query: 検索クエリ

        Returns:
            List[ExternalData]: 取得できた全データ
        """
        results = []
        for source in self._sources:
            try:
                data = source.fetch(query)
                if data is not None:
                    results.append(data)
            except Exception:
                # ソースのエラーは無視して続行
                pass
        return results

    def fetch_best(self, query: dict) -> Optional[ExternalData]:
        """
        最も信頼度の高いデータを1つ取得

        Returns:
            ExternalData or None
        """
        results = self.fetch_all(query)
        if not results:
            return None

        # 信頼度でソート（VERIFIED > CACHED > DYNAMIC > UNTRUSTED）
        trust_order = {
            TrustLevel.IMMUTABLE: 0,
            TrustLevel.VERIFIED: 1,
            TrustLevel.CACHED: 2,
            TrustLevel.DYNAMIC: 3,
            TrustLevel.UNTRUSTED: 4,
        }
        results.sort(key=lambda d: trust_order.get(d.trust_level, 5))
        return results[0]

    def get_source_ids(self) -> List[str]:
        """登録されているソースIDを取得"""
        return [s.get_source_id() for s in self._sources]


# ============================================================
# 4c: 綿津見（Watatsumi）= Gateway/Protocol
# ============================================================

@dataclass
class CacheEntry:
    """キャッシュエントリ"""
    data: ExternalData
    access_count: int = 0
    last_access: float = field(default_factory=time.time)


class Watatsumi:
    """
    綿津見（Watatsumi）= 海のゲートウェイ

    古事記の綿津見:
        海を統べる神。イザナギの禊から生まれた。
        底津綿津見・中津綿津見・上津綿津見の三神。

    責務:
    - 常世と海原からのデータを統合
    - 外部データの正規化
    - 信頼度スコアの調整
    - キャッシュ管理

    設計原則:
    - Layer 3からのアクセスは全てWatatsumiを経由
    - 常世を優先、海原をフォールバック
    - キャッシュヒット時は信頼度を CACHED に降格
    """

    def __init__(
        self,
        tokoyo: Optional[Tokoyo] = None,
        unabara: Optional[Unabara] = None,
        cache_max_size: int = 1000,
    ):
        self.tokoyo = tokoyo or Tokoyo()
        self.unabara = unabara or Unabara()
        self._cache: Dict[str, CacheEntry] = {}
        self._cache_max_size = cache_max_size

    def _make_cache_key(self, query: dict) -> str:
        """クエリからキャッシュキーを生成"""
        prompt = query.get("prompt", "")
        filters = query.get("filters", {})
        key_str = f"{prompt}:{sorted(filters.items())}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _evict_cache(self) -> None:
        """古いキャッシュエントリを削除（LRU）"""
        if len(self._cache) <= self._cache_max_size:
            return

        # 最終アクセス時刻でソートして古いものから削除
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].last_access,
        )
        entries_to_remove = len(self._cache) - self._cache_max_size
        for key, _ in sorted_entries[:entries_to_remove]:
            del self._cache[key]

    def fetch(self, query: dict) -> Optional[ExternalData]:
        """
        統合データフェッチ

        優先順位:
        1. 常世（不変データ）
        2. キャッシュ（前回の取得結果）
        3. 海原（動的取得）

        Parameters:
            query: 検索クエリ
                - prompt: str
                - filters: dict (オプション)
                - bypass_cache: bool (オプション)

        Returns:
            ExternalData or None
        """
        prompt = query.get("prompt", "")
        bypass_cache = query.get("bypass_cache", False)

        # 1. 常世からの型情報チェック
        # プロンプト内の型名を抽出して照合
        type_pattern = re.compile(r'\b([A-Z][A-Za-z0-9]*(?:\{[^}]+\})?)\b')
        for match in type_pattern.finditer(prompt):
            type_name = match.group(1).split('{')[0]  # パラメータ部分を除去
            tokoyo_data = self.tokoyo.get_builtin_type(type_name)
            if tokoyo_data:
                return tokoyo_data

        # 2. キャッシュチェック
        cache_key = self._make_cache_key(query)
        if not bypass_cache and cache_key in self._cache:
            entry = self._cache[cache_key]
            if not entry.data.is_expired():
                entry.access_count += 1
                entry.last_access = time.time()

                # キャッシュヒット時は信頼度を降格
                cached_data = ExternalData(
                    content=entry.data.content,
                    source=entry.data.source,
                    trust_level=TrustLevel.CACHED,
                    timestamp=entry.data.timestamp,
                    ttl_seconds=entry.data.ttl_seconds,
                    metadata={**entry.data.metadata, "cache_hit": True},
                )
                return cached_data

        # 3. 海原から動的取得
        unabara_data = self.unabara.fetch_best(query)
        if unabara_data:
            # キャッシュに保存
            self._cache[cache_key] = CacheEntry(data=unabara_data)
            self._evict_cache()
            return unabara_data

        return None

    def normalize(self, data: ExternalData) -> dict:
        """
        外部データをLayer 3で使える形式に正規化

        Returns:
            dict: 正規化されたデータ
                - content: str (テキスト化されたコンテンツ)
                - trust_score: float (0.0-1.0)
                - source: str
                - age_seconds: float
        """
        # 信頼度スコアの計算
        trust_scores = {
            TrustLevel.IMMUTABLE: 1.0,
            TrustLevel.VERIFIED: 0.9,
            TrustLevel.CACHED: 0.7,
            TrustLevel.DYNAMIC: 0.5,
            TrustLevel.UNTRUSTED: 0.2,
        }
        trust_score = trust_scores.get(data.trust_level, 0.1)

        # 経過時間による減衰（IMMUTABLE以外）
        if data.trust_level != TrustLevel.IMMUTABLE:
            age = data.get_age_seconds()
            decay = max(0.5, 1.0 - (age / (data.ttl_seconds * 2)))
            trust_score *= decay

        # コンテンツのテキスト化
        if isinstance(data.content, str):
            content_str = data.content
        elif isinstance(data.content, dict):
            content_str = str(data.content)
        else:
            content_str = repr(data.content)

        return {
            "content": content_str,
            "trust_score": trust_score,
            "source": data.source,
            "age_seconds": data.get_age_seconds(),
            "metadata": data.metadata,
        }

    def get_cache_stats(self) -> dict:
        """キャッシュ統計を取得"""
        total_entries = len(self._cache)
        expired_entries = sum(1 for e in self._cache.values() if e.data.is_expired())
        total_accesses = sum(e.access_count for e in self._cache.values())

        return {
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "valid_entries": total_entries - expired_entries,
            "total_accesses": total_accesses,
            "max_size": self._cache_max_size,
        }

    def clear_cache(self) -> int:
        """キャッシュをクリア"""
        count = len(self._cache)
        self._cache.clear()
        return count


# ============================================================
# Layer 4 統合インターフェース
# ============================================================

class Layer4Gateway:
    """
    Layer 4 統合ゲートウェイ

    常世・海原・綿津見を統合し、
    稗田阿礼（HiedaNoAre）から呼び出される単一インターフェースを提供。

    使用例:
        gateway = Layer4Gateway()
        result = gateway.fetch_context({"prompt": "struct Point2D"})
    """

    def __init__(self):
        self.tokoyo = Tokoyo()
        self.unabara = Unabara()
        self.watatsumi = Watatsumi(self.tokoyo, self.unabara)

    def fetch_context(self, query: dict) -> dict:
        """
        クエリに基づいて外部コンテキストを取得

        Parameters:
            query: 検索クエリ
                - prompt: str (必須)
                - filters: dict (オプション)
                - bypass_cache: bool (オプション)

        Returns:
            dict: 取得したコンテキスト
                - data: 正規化されたデータ or None
                - builtin_types: 検出された組み込み型
                - source_stats: ソース統計
        """
        prompt = query.get("prompt", "")

        # 組み込み型の検出
        builtin_types = []
        type_pattern = re.compile(r'\b([A-Z][A-Za-z0-9]*)\b')
        for match in type_pattern.finditer(prompt):
            type_name = match.group(1)
            if type_name in self.tokoyo.JULIA_BUILTIN_TYPES:
                builtin_types.append(type_name)

        # 綿津見経由でデータ取得
        raw_data = self.watatsumi.fetch(query)
        normalized_data = None
        if raw_data:
            normalized_data = self.watatsumi.normalize(raw_data)

        return {
            "data": normalized_data,
            "builtin_types": list(set(builtin_types)),
            "source_stats": {
                "tokoyo_types": len(self.tokoyo.get_all_builtin_types()),
                "unabara_sources": self.unabara.get_source_ids(),
                "cache_stats": self.watatsumi.get_cache_stats(),
            },
        }

    def get_status(self) -> dict:
        """Layer 4の現在のステータスを取得"""
        return {
            "tokoyo": {
                "builtin_type_count": len(self.tokoyo.get_all_builtin_types()),
                "stdlib_module_count": len(self.tokoyo.JULIA_STDLIB_MODULES),
            },
            "unabara": {
                "sources": self.unabara.get_source_ids(),
            },
            "watatsumi": {
                "cache_stats": self.watatsumi.get_cache_stats(),
            },
        }


# ============================================================
# テスト用ユーティリティ
# ============================================================

def test_layer4():
    """Layer 4の基本動作テスト"""
    print("=== Layer 4 (海原・常世) テスト ===\n")

    # --- 常世テスト ---
    print("【常世（Tokoyo）テスト】")
    tokoyo = Tokoyo()

    # 組み込み型取得
    int_data = tokoyo.get_builtin_type("Int64")
    print(f"  Int64: {int_data.content if int_data else 'Not found'}")

    # 不変データ登録
    success = tokoyo.register_immutable("custom_const", {"value": 42})
    print(f"  カスタム登録: {success}")
    success2 = tokoyo.register_immutable("custom_const", {"value": 100})  # 上書き試行
    print(f"  上書き試行: {success2} (Falseが正解)")

    # --- 海原テスト ---
    print("\n【海原（Unabara）テスト】")
    unabara = Unabara()

    results = unabara.fetch_all({"prompt": "struct Point definition"})
    print(f"  'struct Point'検索: {len(results)} 件")
    for r in results:
        print(f"    - {r.source}: {r.content[:50]}...")

    # --- 綿津見テスト ---
    print("\n【綿津見（Watatsumi）テスト】")
    watatsumi = Watatsumi(tokoyo, unabara)

    # 組み込み型クエリ
    data1 = watatsumi.fetch({"prompt": "Float64 variable"})
    if data1:
        normalized = watatsumi.normalize(data1)
        print(f"  'Float64'クエリ: trust={normalized['trust_score']:.2f}")

    # 動的クエリ
    data2 = watatsumi.fetch({"prompt": "tree structure"})
    if data2:
        normalized = watatsumi.normalize(data2)
        print(f"  'tree'クエリ: trust={normalized['trust_score']:.2f}, source={normalized['source']}")

    # キャッシュ統計
    stats = watatsumi.get_cache_stats()
    print(f"  キャッシュ: {stats['total_entries']} entries")

    # --- 統合ゲートウェイテスト ---
    print("\n【Layer 4 Gateway テスト】")
    gateway = Layer4Gateway()

    result = gateway.fetch_context({"prompt": "struct Vec3D with Float64 fields"})
    print(f"  組み込み型検出: {result['builtin_types']}")
    if result['data']:
        print(f"  データ取得: source={result['data']['source']}")

    status = gateway.get_status()
    print(f"  常世: {status['tokoyo']['builtin_type_count']} types")
    print(f"  海原: {status['unabara']['sources']}")

    print("\n=== テスト完了 ===")


if __name__ == "__main__":
    test_layer4()
