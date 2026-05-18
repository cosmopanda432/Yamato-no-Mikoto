"""
Julia-no-Mikoto: Data Augmentation

マクロ展開やコード変換によるデータ拡張。
v2ではEncoder-Decoderではなく、Data Augmentationでマクロを学習。
"""

import re
from typing import List, Dict, Callable, Optional
from dataclasses import dataclass


@dataclass
class AugmentedSample:
    """拡張されたサンプル"""
    original: str
    augmented: str
    augmentation_type: str


# =============================================================================
# マクロ展開
# =============================================================================


def expand_inline_macro(code: str) -> str:
    """@inline マクロを展開（単純削除）"""
    return re.sub(r"@inline\s+", "", code)


def expand_noinline_macro(code: str) -> str:
    """@noinline マクロを展開（単純削除）"""
    return re.sub(r"@noinline\s+", "", code)


def expand_simd_macro(code: str) -> str:
    """
    @simd マクロを展開

    @simd for i in 1:n
        body
    end

    →

    for i in 1:n
        # SIMD vectorized
        body
    end
    """
    # 単純なパターンマッチング
    pattern = r"@simd\s+(for\s+)"
    replacement = r"\1"
    return re.sub(pattern, replacement, code)


def expand_threads_macro(code: str) -> str:
    """
    Threads.@threads マクロを展開

    Threads.@threads for i in 1:n
        body
    end

    →

    for i in 1:n
        # Threaded execution
        body
    end
    """
    pattern = r"Threads\.@threads\s+(for\s+)"
    replacement = r"\1"
    return re.sub(pattern, replacement, code)


def expand_views_macro(code: str) -> str:
    """
    @views マクロを展開

    @views A[1:n]  →  view(A, 1:n)
    """
    # 単純な削除として実装
    return re.sub(r"@views\s+", "", code)


def expand_inbounds_macro(code: str) -> str:
    """@inbounds マクロを展開（単純削除）"""
    return re.sub(r"@inbounds\s+", "", code)


def expand_fastmath_macro(code: str) -> str:
    """@fastmath マクロを展開（単純削除）"""
    return re.sub(r"@fastmath\s+", "", code)


# マクロ展開関数のマッピング
MACRO_EXPANDERS: Dict[str, Callable[[str], str]] = {
    "@inline": expand_inline_macro,
    "@noinline": expand_noinline_macro,
    "@simd": expand_simd_macro,
    "Threads.@threads": expand_threads_macro,
    "@views": expand_views_macro,
    "@inbounds": expand_inbounds_macro,
    "@fastmath": expand_fastmath_macro,
}


def detect_macros(code: str) -> List[str]:
    """コード内のマクロを検出"""
    found = []
    for macro in MACRO_EXPANDERS.keys():
        if macro in code:
            found.append(macro)
    return found


def augment_with_macro_expansion(code: str) -> List[AugmentedSample]:
    """
    マクロを含むコードを展開して、学習データを増やす

    Args:
        code: 元のJuliaコード

    Returns:
        拡張されたサンプルのリスト
    """
    augmented = [AugmentedSample(code, code, "original")]

    macros = detect_macros(code)
    expanded_code = code

    for macro in macros:
        if macro in MACRO_EXPANDERS:
            expanded_code = MACRO_EXPANDERS[macro](expanded_code)
            augmented.append(AugmentedSample(
                original=code,
                augmented=expanded_code,
                augmentation_type=f"expand_{macro}",
            ))

    return augmented


# =============================================================================
# 型注釈の追加/削除
# =============================================================================


def remove_type_annotations(code: str) -> str:
    """
    型注釈を削除

    function foo(x::Int64, y::Float64)::Vector{Int}
    →
    function foo(x, y)
    """
    # 引数の型注釈を削除
    code = re.sub(r"(\w+)::[^\s,)]+", r"\1", code)
    # 戻り値の型注釈を削除
    code = re.sub(r"\)::[^\s\n]+", ")", code)
    return code


def add_any_type_annotations(code: str) -> str:
    """
    Any型注釈を追加（型不安定なコードのシミュレーション）

    function foo(x, y)
    →
    function foo(x::Any, y::Any)
    """
    # 簡易パターン: 引数リストの各引数にAnyを追加
    # 実際にはより高度なパースが必要

    def add_any_to_args(match):
        args = match.group(1)
        # 既に型注釈がある引数はスキップ
        new_args = []
        for arg in args.split(","):
            arg = arg.strip()
            if "::" not in arg and arg:
                new_args.append(f"{arg}::Any")
            else:
                new_args.append(arg)
        return f"({', '.join(new_args)})"

    # function定義の引数を処理
    code = re.sub(r"function\s+\w+\(([^)]*)\)", lambda m: f"function {m.group(0).split('(')[0].split()[-1]}({add_any_to_args(m).strip('()')})", code)

    return code


def augment_with_type_variations(code: str) -> List[AugmentedSample]:
    """
    型注釈のバリエーションを生成

    Args:
        code: 元のJuliaコード

    Returns:
        拡張されたサンプルのリスト
    """
    augmented = []

    # 型注釈削除版
    no_types = remove_type_annotations(code)
    if no_types != code:
        augmented.append(AugmentedSample(
            original=code,
            augmented=no_types,
            augmentation_type="remove_types",
        ))

    return augmented


# =============================================================================
# 同義変換
# =============================================================================


def transform_for_to_map(code: str) -> str:
    """
    簡単なforループをmap/broadcastに変換

    for i in 1:n
        result[i] = f(x[i])
    end
    →
    result = map(f, x)

    注: 完全な変換は困難なため、単純なケースのみ対応
    """
    # この実装は概念的なものであり、実際には構文解析が必要
    return code  # プレースホルダー


def transform_broadcast(code: str) -> str:
    """
    ブロードキャスト変換

    map(f, x)  →  f.(x)
    """
    # map(f, x) → f.(x) の変換
    code = re.sub(r"map\((\w+),\s*(\w+)\)", r"\1.(\2)", code)
    return code


def transform_dot_syntax(code: str) -> str:
    """
    ドット構文の正規化

    sin.(x)  →  broadcast(sin, x)
    """
    code = re.sub(r"(\w+)\.\(([^)]+)\)", r"broadcast(\1, \2)", code)
    return code


def augment_with_equivalent_transforms(code: str) -> List[AugmentedSample]:
    """
    同義変換によるデータ拡張

    Args:
        code: 元のJuliaコード

    Returns:
        拡張されたサンプルのリスト
    """
    augmented = []

    # ブロードキャスト変換
    broadcasted = transform_broadcast(code)
    if broadcasted != code:
        augmented.append(AugmentedSample(
            original=code,
            augmented=broadcasted,
            augmentation_type="broadcast",
        ))

    # ドット構文正規化
    dotted = transform_dot_syntax(code)
    if dotted != code:
        augmented.append(AugmentedSample(
            original=code,
            augmented=dotted,
            augmentation_type="dot_syntax",
        ))

    return augmented


# =============================================================================
# 統合API
# =============================================================================


def augment_julia_code(
    code: str,
    enable_macro_expansion: bool = True,
    enable_type_variations: bool = True,
    enable_equivalent_transforms: bool = True,
) -> List[AugmentedSample]:
    """
    全ての拡張を適用

    Args:
        code: 元のJuliaコード
        enable_macro_expansion: マクロ展開を有効化
        enable_type_variations: 型バリエーションを有効化
        enable_equivalent_transforms: 同義変換を有効化

    Returns:
        拡張されたサンプルのリスト（元のコードを含む）
    """
    all_augmented = [AugmentedSample(code, code, "original")]

    if enable_macro_expansion:
        all_augmented.extend(augment_with_macro_expansion(code)[1:])

    if enable_type_variations:
        all_augmented.extend(augment_with_type_variations(code))

    if enable_equivalent_transforms:
        all_augmented.extend(augment_with_equivalent_transforms(code))

    return all_augmented


def augment_dataset(
    samples: List[str],
    **kwargs,
) -> List[AugmentedSample]:
    """
    データセット全体を拡張

    Args:
        samples: Juliaコードのリスト
        **kwargs: augment_julia_codeに渡すオプション

    Returns:
        拡張されたサンプルのリスト
    """
    all_augmented = []
    for sample in samples:
        all_augmented.extend(augment_julia_code(sample, **kwargs))
    return all_augmented
