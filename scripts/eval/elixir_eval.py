"""
Elixir 版 e2e 評価 — 生成 JSON 群を `elixir <file>` で評価する。

docs/roadmap_min_elixir.md Step 7 に対応。`scripts/eval/go_eval.py` の Elixir 版。

Go 版との違い:
  - Go: `go build` → `go vet` → `go test` の 3 段階。compile と test が分離
  - Elixir: `elixir <file>` 一発で parse + compile + load + ExUnit 実行が走るので
    PRIMARY = pass@1 のみ。compile-only / vet 相当の独立指標は無い
  - MultiPL-E `eval_elixir.py` と同形式 (5s timeout、exit code ベース)

指標 (重要度順):
  PRIMARY:    test_pass_rate           (= pass@1)
  SECONDARY:  compile_ok_rate           (= parse + compile が通った率)
  TERTIARY':  undefined_rate            (= UndefinedFunctionError 出現率、型ハルシ判定)
  TERTIARY:   assertion_failure_rate    (= 走ったがテスト assert で fail)

使い方:
    python3 scripts/eval/elixir_eval.py \\
        --generated-dir data/eval/generated/humaneval-elixir.baseline.seed0 \\
        --out-dir data/eval/results/humaneval-elixir.baseline.seed0

mechanical_repair オプションは `elixir -e "Code.format_string!"` をサブプロセス起動して
適用する。L3 を呼び戻さない決定論的 text → text 変換 (Goodhart 回避: tests は repair の
context に含めない)。
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Elixir コンパイラエラーパターン (型ハルシ / 構文不全 / 実行時エラーの分類)
RE_TOKEN_MISSING = re.compile(r"\bTokenMissingError\b|\bmissing terminator\b")
RE_SYNTAX_ERROR = re.compile(r"\bSyntaxError\b|\bsyntax error before\b")
RE_COMPILE_ERROR = re.compile(r"\*\* \(CompileError\)|\bCompileError\b")
RE_UNDEFINED = re.compile(
    r"\bUndefinedFunctionError\b"
    r"|\bfunction\s+[\w\.]+/\d+\s+is undefined"
    r"|\bmodule\s+[\w\.]+\s+is not loaded"
    r"|\bis undefined or private\b"
)
RE_ASSERTION = re.compile(
    r"\bExUnit\.AssertionError\b"
    r"|\bAssertion with\b"
    r"|\bmatch \(=\) failed\b"
)
RE_FUNCTION_CLAUSE = re.compile(r"\bFunctionClauseError\b|\bno function clause matching\b")
RE_MODULE_DEFN = re.compile(r"^\s*defmodule\s+([A-Z][\w\.]*)\s+do", re.MULTILINE)


@dataclass
class RepairResult:
    text: str
    applied: bool
    tool: str
    stderr: str = ""


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--generated-dir",
        required=True,
        help="run_yamato_min_elixir.py / baseline runner の出力 JSON 群が置かれた dir",
    )
    ap.add_argument("--out-dir", required=True)
    ap.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="1 サンプルあたりの elixir 実行タイムアウト秒 (MultiPL-E と同じ 5s デフォルト)",
    )
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument(
        "--elixir-bin",
        default=None,
        help="elixir CLI へのパス。デフォルト: PATH から検索",
    )
    ap.add_argument(
        "--mechanical-repair",
        action="store_true",
        help=(
            "elixir -e `Code.format_string!` で prompt+completion を整形してから評価。"
            "tests は repair の context に含めない (Goodhart 回避)。"
            "Firewall 隔離契約は維持: text→text の決定論的変換のみ"
        ),
    )
    return ap.parse_args()


def derive_module_name(prompt: str) -> str:
    """prompt 先頭の `defmodule <name> do` を抜き出す。見つからなければ 'Sample'"""
    m = RE_MODULE_DEFN.search(prompt)
    return m.group(1) if m else "Sample"


def format_repair(text: str, elixir_bin: str, timeout_sec: float = 5.0) -> RepairResult:
    """`Code.format_string!` を Elixir サブプロセスで適用する text → text 変換。

    L5 内部の決定論的 REPAIR。LLM は呼ばない。
    """
    # 注: `:all` を使うのは Elixir 1.12 互換のため (1.13+ では `:eof` が標準だが、
    # Ubuntu 22.04 apt bundled は Elixir 1.12.2 で `:eof` 未対応)。
    one_liner = (
        "IO.read(:stdio, :all) "
        "|> Code.format_string!() "
        "|> IO.iodata_to_binary() "
        "|> IO.write()"
    )
    try:
        proc = subprocess.run(
            [elixir_bin, "-e", one_liner],
            input=text,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired:
        return RepairResult(text=text, applied=False, tool="format", stderr="timeout")
    except OSError as e:
        return RepairResult(text=text, applied=False, tool="format", stderr=f"OSError: {e}")

    if proc.returncode != 0:
        # formatter は壊れた構文では非 0 を返す。元 text を返す。
        return RepairResult(text=text, applied=False, tool="format", stderr=_trim(proc.stderr))

    formatted = proc.stdout
    if not formatted.endswith("\n"):
        formatted += "\n"

    return RepairResult(
        text=formatted,
        applied=(formatted != text),
        tool="format",
        stderr=_trim(proc.stderr),
    )


def run_one(
    sample: dict,
    elixir_bin: str,
    timeout: float,
    mechanical_repair: bool = False,
) -> dict:
    """1 サンプル評価。`elixir <file>` で parse + compile + ExUnit を一気に走らせる。

    mechanical_repair=True なら `Code.format_string!` を **prompt+completion** に適用
    してから評価する。tests を repair の context に含めない (Goodhart 回避)。
    """
    prompt = sample["prompt"]
    completion = sample["completion"]
    tests = sample["tests"]
    module_name = derive_module_name(prompt)

    result = {
        "name": sample["name"],
        "seed": sample.get("seed", 0),
        "module_name": module_name,
        "test_ok": False,
        "compile_ok": False,
        "has_undefined": False,
        "has_assertion_failure": False,
        "has_function_clause": False,
        "has_token_missing": False,
        "has_syntax_error": False,
        "has_compile_error": False,
        "test_stderr": "",
        "exit_code": None,
        "elapsed_sec": 0.0,
        "repair_applied": False,
        "repair_tool": "",
        "timed_out": False,
    }

    body = prompt + completion
    if mechanical_repair:
        repair = format_repair(body, elixir_bin)
        body = repair.text
        result["repair_applied"] = repair.applied
        result["repair_tool"] = repair.tool

    # `.exs` は script モード。ExUnit.start() がテスト側に含まれている前提
    # (MultiPL-E elixir の test 文字列が ExUnit.start() を含む)。
    source = body + "\n\n" + tests + "\n"

    t0 = time.time()
    try:
        with tempfile.TemporaryDirectory(prefix=f"elixir-eval-{sample['name']}-") as td:
            tmp = Path(td)
            exs_path = tmp / "sample.exs"
            exs_path.write_text(source)

            proc = subprocess.run(
                [elixir_bin, str(exs_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            combined = (proc.stderr or "") + "\n" + (proc.stdout or "")
            result["exit_code"] = proc.returncode
            result["test_stderr"] = _trim(combined)

            # 各エラーパターンを並行検出 (1 サンプルが複数該当する可能性あり)
            result["has_token_missing"] = bool(RE_TOKEN_MISSING.search(combined))
            result["has_syntax_error"] = bool(RE_SYNTAX_ERROR.search(combined))
            result["has_compile_error"] = bool(RE_COMPILE_ERROR.search(combined))
            result["has_undefined"] = bool(RE_UNDEFINED.search(combined))
            result["has_assertion_failure"] = bool(RE_ASSERTION.search(combined))
            result["has_function_clause"] = bool(RE_FUNCTION_CLAUSE.search(combined))

            result["test_ok"] = proc.returncode == 0
            # compile_ok = 構文 + コンパイル両方通った (= AssertionError や
            # UndefinedFunctionError は compile_ok を阻害しない)
            result["compile_ok"] = not (
                result["has_token_missing"]
                or result["has_syntax_error"]
                or result["has_compile_error"]
            )
    except subprocess.TimeoutExpired:
        result["test_stderr"] = f"timeout after {timeout}s"
        result["exit_code"] = -1
        result["timed_out"] = True
    except Exception as e:
        result["test_stderr"] = f"exception: {e}"
        result["exit_code"] = -2

    result["elapsed_sec"] = time.time() - t0
    return result


def _trim(s: str, max_chars: int = 800) -> str:
    if s is None:
        return ""
    if len(s) <= max_chars:
        return s
    return s[:max_chars] + f"... [+{len(s) - max_chars} chars]"


def main():
    args = parse_args()

    elixir_bin = args.elixir_bin or shutil.which("elixir")
    if not elixir_bin:
        raise SystemExit(
            "elixir binary not found on PATH. asdf を使っているなら "
            "`source ~/.asdf/asdf.sh` してから実行するか、--elixir-bin で指定してください。"
        )

    gen_dir = Path(args.generated_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    sample_files = sorted(gen_dir.glob("*.json"))
    if args.limit is not None:
        sample_files = sample_files[: args.limit]
    print(f"Evaluating {len(sample_files)} samples from {gen_dir}")
    print(f"  elixir = {elixir_bin}")
    if args.mechanical_repair:
        print("  mechanical_repair = ON (Code.format_string!)")

    per_sample = []
    counts = Counter()
    t_start = time.time()

    for i, sf in enumerate(sample_files):
        sample = json.loads(sf.read_text())
        r = run_one(
            sample,
            elixir_bin=elixir_bin,
            timeout=args.timeout,
            mechanical_repair=args.mechanical_repair,
        )
        per_sample.append(r)

        counts["total"] += 1
        for key in (
            "test_ok",
            "compile_ok",
            "has_undefined",
            "has_assertion_failure",
            "has_function_clause",
            "has_token_missing",
            "has_syntax_error",
            "has_compile_error",
            "timed_out",
        ):
            if r[key]:
                counts[key] += 1
        if r.get("repair_applied"):
            counts["repair_applied"] += 1

        status = "TEST ✓" if r["test_ok"] else "TEST ✗"
        status += " · " + ("CMP ✓" if r["compile_ok"] else "CMP ✗")
        print(
            f"  [{i + 1}/{len(sample_files)}] {sample['name']:<55s} "
            f"{status}  ({r['elapsed_sec']:.1f}s)"
        )

        (out_dir / f"{sample['name']}__s{r['seed']}.result.json").write_text(
            json.dumps(r, ensure_ascii=False, indent=2)
        )

    elapsed = time.time() - t_start
    n = counts["total"]
    summary = {
        "n_total": n,
        "test_pass_rate": counts["test_ok"] / max(n, 1),
        "compile_pass_rate": counts["compile_ok"] / max(n, 1),
        "undefined_rate": counts["has_undefined"] / max(n, 1),
        "assertion_failure_rate": counts["has_assertion_failure"] / max(n, 1),
        "function_clause_rate": counts["has_function_clause"] / max(n, 1),
        "token_missing_rate": counts["has_token_missing"] / max(n, 1),
        "syntax_error_rate": counts["has_syntax_error"] / max(n, 1),
        "compile_error_rate": counts["has_compile_error"] / max(n, 1),
        "timeout_rate": counts["timed_out"] / max(n, 1),
        "elapsed_total_sec": elapsed,
        "generated_dir": str(gen_dir),
        "elixir_bin": elixir_bin,
        "mechanical_repair_enabled": args.mechanical_repair,
        "repair_applied_count": counts["repair_applied"],
    }
    (out_dir / "_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))

    print()
    print(f"=== Summary ({n} samples, {elapsed:.0f}s) ===")
    print(
        f"  PRIMARY   elixir test pass rate : "
        f"{summary['test_pass_rate'] * 100:6.2f}% ({counts['test_ok']}/{n})"
    )
    print(
        f"  SECONDARY compile pass rate     : "
        f"{summary['compile_pass_rate'] * 100:6.2f}% ({counts['compile_ok']}/{n})"
    )
    print(
        f"  TERTIARY' undefined rate        : "
        f"{summary['undefined_rate'] * 100:6.2f}% ({counts['has_undefined']}/{n})"
    )
    print(
        f"  TERTIARY  assertion failure rate: "
        f"{summary['assertion_failure_rate'] * 100:6.2f}% ({counts['has_assertion_failure']}/{n})"
    )
    if args.mechanical_repair:
        print(f"  REPAIR    format applied        : {counts['repair_applied']}/{n}")
    print(f"\nwrote -> {out_dir / '_summary.json'}")


if __name__ == "__main__":
    main()
