"""機械的 REPAIR (L5 内部の post-process) — Elixir target 版

src_min_go/kojiki_lm/mechanical_repair.py の Elixir 版。Go 版が `goimports` を使うのに
対し、本ファイルは `elixir -e "Code.format_string!(...)"` を subprocess 呼び出しで使う。

## Firewall 隔離契約との関係

- L3 (生成 LM) と L5 (評価器) は本モジュールの動作中に**通信しない**
- 入力: prompt + completion (= L3 が生成した text)
- 出力: 修復後 text (= L5 内部で完結)
- L3 は修復後 text を**見ない** → L5→L3 経路を使わない
- 「テストの期待値」等は引数に渡さない → 構造的に L3 に漏らせない

## 実装

`elixir -e ...` で `Code.format_string!/2` を呼ぶ。Mix project root が無くても
動作するため (`mix format` と違い `.formatter.exs` 不要)、stdalone な subprocess で
完結する。

将来の追加候補:
  - `Code.string_to_quoted/2` のエラー hint ("did you mean ...") を parse して
    typo を機械修復 (src_min_elixir/lib/kojiki_lm/mechanical_repair.ex の hint 抽出と同じ)
  - alias 補完 (Module.func の自動 alias 挿入)

## 制限

- 整形しかしないので、関数呼び出しの typo 修正等はカバーしない
- Code.format_string! は **構文エラーの input には raise** する。失敗時は元 text を返す
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
    """適用したツール名 ('elixir_format' / 'noop')"""

    stderr: str = ""
    """ツールの stderr (失敗時 / warning の記録用、L3 には絶対渡さない)"""


# Elixir スクリプト本体。stdin から source を読んで Code.format_string! で整形し
# stdout に出す。失敗時は exit 1 + stderr にエラーを出す。
_FORMAT_SNIPPET = """
source = IO.read(:stdio, :eof)
try do
  formatted = source |> Code.format_string!() |> IO.iodata_to_binary()
  IO.write(formatted)
  if not String.ends_with?(formatted, "\\n"), do: IO.write("\\n")
catch
  kind, reason ->
    IO.write(:stderr, "format_failed: \#{kind} \#{inspect(reason)}")
    System.halt(1)
end
""".strip()


def elixir_format_repair(
    text: str,
    *,
    elixir_bin: str | None = None,
    timeout_sec: float = 5.0,
) -> RepairResult:
    """`elixir -e "Code.format_string!(...)"` で text を修復 (整形) する。

    stdin から source を渡して stdout を受け取る。

    Args:
        text: 修復対象の Elixir source (prompt + completion 等)。 **tests を含めない**
              (テストの期待値を repair の context に乗せない、Goodhart 回避のため)
        elixir_bin: バイナリパス。None なら PATH から検索
        timeout_sec: subprocess timeout

    Returns:
        RepairResult。失敗時 (binary 無し / timeout / 非 0 exit) は元 text を返し
        `applied=False`、stderr に状況を記録。
    """
    bin_path = elixir_bin or shutil.which("elixir")
    if not bin_path:
        return RepairResult(
            text=text, applied=False, tool="noop",
            stderr="elixir binary not found in PATH",
        )

    try:
        proc = subprocess.run(
            [bin_path, "-e", _FORMAT_SNIPPET],
            input=text,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired:
        return RepairResult(
            text=text, applied=False, tool="elixir_format",
            stderr=f"timeout after {timeout_sec}s",
        )
    except OSError as e:
        return RepairResult(
            text=text, applied=False, tool="elixir_format",
            stderr=f"OSError: {e}",
        )

    # Code.format_string! は構文エラー時に raise → exit 1。
    # 失敗時は元 text を返す (修復不能なので壊さない)。
    if proc.returncode != 0:
        return RepairResult(
            text=text, applied=False, tool="elixir_format",
            stderr=proc.stderr.strip(),
        )

    repaired = proc.stdout
    return RepairResult(
        text=repaired,
        applied=(repaired != text),
        tool="elixir_format",
        stderr=proc.stderr.strip(),  # warning がある場合のみ非空
    )
