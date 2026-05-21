"""機械的 REPAIR (L5 内部の post-process)

L3 (KotodamaDecoder) を一切呼び戻さずに、L5 が決定論的にコードを修復する層。
LLM-in-loop の REPAIR (修正 E の原案) は「LM が自分の誤りを LM で直す」循環的
処理になりがちで、Goodhart hack も生まれやすい。本モジュールは LLM を使わない
機械的修復のみを提供する。

## Firewall 隔離契約との関係

- L3 (生成 LM) と L5 (評価器) は本モジュールの動作中に**通信しない**
- 入力: prompt + completion (= L3 が生成した text)
- 出力: 修復後 text (= L5 内部で完結)
- L3 は修復後 text を**見ない** → L5→L3 経路を使わない
- 「テストの期待値」等は引数に渡さない → 構造的に L3 に漏らせない

## 実装

現状は `goimports` のみ。`goimports` は使用識別子を解析して不足 import を
標準ライブラリ + 設定された vendor から自動補完し、未使用 import を削除する。
gofmt 相当の整形も含む。pure な決定論的変換。

## 将来の追加候補

- gopls の textDocument/codeAction 経由で fix-it 取得 (broader coverage)
- `}` のバランス補完
- 未宣言関数のスタブ挿入 (危険、保留)

## 制限

- mbpp-go では効果限定的 (build_ok=100% 達成済みなので import 系の修復対象は少ない)
- swebench 等の import 忘れが多いタスクで有効性が出る想定
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass


@dataclass
class RepairResult:
    """機械的修復の結果。

    元 text と修復後 text を返し、呼び出し側が「適用されたか」を比較できる形にする。
    Verdict としての記録用に applied フラグも持つ。
    """

    text: str
    """修復後 text (失敗時は元 text をそのまま返す)"""

    applied: bool
    """元 text から変化があったか"""

    tool: str
    """適用したツール名 ('goimports' / 'noop')"""

    stderr: str = ""
    """ツールの stderr (失敗時 / warning の記録用、L3 には絶対渡さない)"""


def goimports_repair(
    text: str,
    *,
    goimports_bin: str | None = None,
    timeout_sec: float = 5.0,
) -> RepairResult:
    """`goimports` で text を修復する。stdin から渡して stdout を受け取る。

    Args:
        text: 修復対象の Go source (prompt + completion 等)。 **tests を含めない**
              (テストの期待値を repair の context に乗せない、Goodhart 回避のため)
        goimports_bin: バイナリパス。None なら PATH から検索
        timeout_sec: subprocess timeout

    Returns:
        RepairResult。失敗時 (binary 無し / timeout / 非 0 exit) は元 text を返し
        `applied=False`、stderr に状況を記録。
    """
    bin_path = goimports_bin or shutil.which("goimports")
    if not bin_path:
        return RepairResult(
            text=text, applied=False, tool="noop",
            stderr="goimports binary not found in PATH",
        )

    try:
        proc = subprocess.run(
            [bin_path],
            input=text,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired:
        return RepairResult(
            text=text, applied=False, tool="goimports",
            stderr=f"timeout after {timeout_sec}s",
        )
    except OSError as e:
        return RepairResult(
            text=text, applied=False, tool="goimports",
            stderr=f"OSError: {e}",
        )

    # goimports は構文エラー時に非 0 で stderr に診断を出す。
    # 失敗時は元 text を返す (修復不能なので壊さない)。
    if proc.returncode != 0:
        return RepairResult(
            text=text, applied=False, tool="goimports",
            stderr=proc.stderr.strip(),
        )

    repaired = proc.stdout
    return RepairResult(
        text=repaired,
        applied=(repaired != text),
        tool="goimports",
        stderr=proc.stderr.strip(),  # warning がある場合のみ非空
    )
