"""
TypeScript 版 e2e 評価 — 生成 JSON 群を `tsc` (compile) → `node` (run) で評価する。

`scripts/eval/elixir_eval.py` の TypeScript 版 (data/kojiki/設計書/ts4_実装設計書_v0.md §5)。

Elixir 版との違い:
  - Elixir: `elixir <file>` 一発で parse + compile + load + ExUnit 実行が走る (単一 subprocess)。
  - TypeScript: `tsc --noEmitOnError --outDir <tmp> <file>` を **1 回** 呼んで compile 専任させ、
    診断が無ければ emit された `.js` を `node` で実行する (2 段 subprocess)。tsc は診断を
    停止コードと stdout に返すので、compile 成否は tsc の exit code から直接判定できる
    (Elixir 版のように「エラーパターン正規表現の否定」で compile_ok を合成する必要が無い —
    tsc に compile 専任の exit code があるという言語差)。
  - 診断コードでの分類:
      TS2304 / TS2552 (`Cannot find name 'X'`) → undefined 扱い + symbol `X` を抽出
      TS1xxx                                    → syntax_error
      その他 TS2xxx / TS7xxx                    → type_error (新分類)
  - Elixir 版の `has_token_missing` / `has_compile_error` (かつ summary の
    `token_missing_rate` / `compile_error_rate`) は削除した。判断根拠:
    judge_win_condition_elixir.py の `METRIC_KEYS` はこの 2 つを参照しない
    (test_pass_rate / compile_pass_rate / undefined_rate / assertion_failure_rate /
    function_clause_rate / timeout_rate / hack_gap のみ参照)。TS1xxx は syntax_error に
    完全に吸収され、Elixir の `CompileError` (token_missing/syntax_error のどちらでもない
    構造的コンパイル失敗) に対応する TS 診断カテゴリは無い (tsc の診断は必ず
    undefined/syntax_error/type_error のどれかに落ちる) ため、削除して schema を単純化した。
  - `function_clause_rate` は judge が参照するため key は残すが、TS に `FunctionClauseError`
    相当の概念が無いため値は常に 0.0 (dead field、ts_evaluator.py の `DO_END_MISMATCH` 同様の
    後方互換維持パターン)。
  - `has_assertion_failure`: Elixir 版は ExUnit の assertion error 文字列を正規表現で検出するが、
    TS には対応する単一の文字列規約が無い。tsc の compile が通ったのに node の実行が非 0
    exit で終わった場合を「assertion/runtime failure」とみなす (best-effort、eli4 と同水準の
    割り切り)。
  - `run_one` の `source` は `prompt + completion + tests` の連結を丸ごと 1 ファイルとして
    compile する (Elixir 版と同じ方式)。そのため `has_undefined` は completion 由来の未定義
    シンボルだけでなく、テストハーネス (`tests` 文字列) 側だけが参照する未定義シンボルにも
    等しく反応する best-effort な判定である (eli4 の Elixir 版が抱える同じ制限を継承)。

使い方:
    python3 scripts/eval/ts_eval.py \\
        --generated-dir data/eval/generated/humaneval-ts.baseline.seed0 \\
        --out-dir data/eval/results/humaneval-ts.baseline.seed0
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# tsc 診断行: "<file>(<line>,<col>): error TS<code>: <message>"
RE_DIAGNOSTIC = re.compile(r"^.+?\(\d+,\d+\): error (TS\d+): (.+)$", re.MULTILINE)

# undefined 扱いにする診断コード (§5: Cannot find name 系)
UNDEF_CODES = {"TS2304", "TS2552"}

# "Cannot find name 'X'" から symbol 名を抽出 (TS2304/TS2552 共通の message 文言)
RE_UNDEF_NAME = re.compile(r"Cannot find name '([^']+)'")


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def classify_diagnostics(tsc_stdout: str) -> dict:
    """tsc の stdout (診断テキスト) を診断コードごとに分類する (產屋 ts4 §5)。

    1 サンプルに複数種の診断が混在しうる (例: 構文エラーの周辺で type エラーも
    連鎖して出る) ため、各カテゴリの has_* は独立した bool として立てる
    (Elixir 版の has_token_missing/has_syntax_error/has_compile_error が並行検出
    だったのと同じ設計)。
    """
    has_undefined = False
    has_syntax_error = False
    has_type_error = False
    undef_symbols: list[str] = []
    first_type_error_msg = ""

    for code, msg in RE_DIAGNOSTIC.findall(tsc_stdout or ""):
        if code in UNDEF_CODES:
            has_undefined = True
            m = RE_UNDEF_NAME.search(msg)
            if m:
                undef_symbols.append(m.group(1))
        elif code.startswith("TS1"):
            has_syntax_error = True
        else:
            has_type_error = True
            if not first_type_error_msg:
                first_type_error_msg = msg

    # syntax_error と type_error は互いに排他的な分類にする (QA 指摘、clean partition)。
    # 構文破壊ファイルでは TS1xxx 診断の周辺に連鎖的な TS2xxx (e.g. パーサが recovery
    # した結果の "function implementation is missing" 等) が同時に出ることがあり、
    # そのまま両方 True にすると summary の type_error_rate が syntax 失敗を二重計上
    # してしまう。has_syntax_error が立っていれば has_type_error は常に False に倒す
    # (syntax_error 優先)。undefined と type_error / undefined と syntax_error の共存は
    # 既存のまま変えない (undef 優先の判定は build_hint/resolve_reason_code 側で担保)。
    if has_syntax_error:
        has_type_error = False
        first_type_error_msg = ""

    return {
        "has_undefined": has_undefined,
        "has_syntax_error": has_syntax_error,
        "has_type_error": has_type_error,
        "undef_symbols": _dedupe_preserve_order(undef_symbols),
        "first_type_error_msg": first_type_error_msg,
    }


def compute_hack_gap(samples: list[dict]) -> float:
    """不浄観 audit 指標: in-loop proxy (`final_v_score`) が COMMIT (>= 0.7) と
    判定したのに大地 (subprocess の `test_ok`) が否定した率 (elixir_eval.py と同一定義)。

    `P(test_ok == False | final_v_score is not None and final_v_score >= 0.7)`。
    分母 (final_v_score >= 0.7 の件数) が 0 のときは 0.0 を返す。
    """
    denom = 0
    numer = 0
    for s in samples:
        v = s.get("final_v_score")
        if v is None or v < 0.7:
            continue
        denom += 1
        if not s.get("test_ok"):
            numer += 1
    return (numer / denom) if denom else 0.0


def resolve_tsc_bin(tsc_bin_arg: str | None) -> str:
    """tsc 実行ファイルを解決する (產屋 ts4 §5.4)。

    優先順位: `--tsc-bin` CLI 引数 → env `TS4_TSC` →
    `<repo>/ts_tools/node_modules/.bin/tsc` → PATH。
    見つからなければ fail-fast (`resolve_elixir_bin` と同じ思想)。
    """
    if tsc_bin_arg:
        return tsc_bin_arg

    env_tsc = os.environ.get("TS4_TSC")
    if env_tsc:
        return env_tsc

    repo_tsc = REPO_ROOT / "ts_tools" / "node_modules" / ".bin" / "tsc"
    if repo_tsc.exists():
        return str(repo_tsc)

    which = shutil.which("tsc")
    if which:
        return which

    raise SystemExit(
        "tsc binary not found (--tsc-bin / env TS4_TSC / "
        "ts_tools/node_modules/.bin/tsc / PATH の順で検索し、全て失敗しました)。"
        "`npm ci --prefix ts_tools` を実行してください。"
    )


def resolve_node_bin(node_bin_arg: str | None) -> str:
    """node 実行ファイルを解決する。`--node-bin` か PATH 検索、無ければ fail-fast。"""
    resolved = node_bin_arg or shutil.which("node")
    if not resolved:
        raise SystemExit(
            "node binary not found on PATH. "
            "PATH に無ければ --node-bin で明示的にパスを指定してください。"
        )
    return resolved


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--generated-dir",
        required=True,
        help="run_yamato_min_ts4.py / baseline runner の出力 JSON 群が置かれた dir",
    )
    ap.add_argument("--out-dir", required=True)
    ap.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="1 サンプルあたりの tsc/node 実行タイムアウト秒 (post-hoc デフォルト、"
        "設計書 §5.3: in-loop 5.0s / post-hoc 10s)。tsc 呼び出し・node 呼び出し"
        "それぞれ独立にこの秒数まで許容する",
    )
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--tsc-bin", default=None, help="tsc CLI へのパス")
    ap.add_argument("--node-bin", default=None, help="node CLI へのパス")
    return ap.parse_args()


def run_one(
    sample: dict,
    tsc_bin: str,
    node_bin: str,
    timeout: float,
) -> dict:
    """1 サンプル評価。`tsc --noEmitOnError` で compile 専任させ、クリーンなら
    emit された `.js` を `node` で実行する (§5)。"""
    prompt = sample["prompt"]
    completion = sample["completion"]
    tests = sample["tests"]

    result = {
        "name": sample["name"],
        "seed": sample.get("seed", 0),
        "test_ok": False,
        "compile_ok": False,
        "has_undefined": False,
        "has_assertion_failure": False,
        # TS に FunctionClauseError 相当の概念は無い。judge_win_condition_ts.py の
        # METRIC_KEYS が function_clause_rate を参照するため key のみ維持する
        # dead field (ts_evaluator.py の DO_END_MISMATCH と同じ後方互換パターン)。
        "has_function_clause": False,
        "has_syntax_error": False,
        "has_type_error": False,
        "test_stderr": "",
        "exit_code": None,
        "elapsed_sec": 0.0,
        "timed_out": False,
        "undef_symbols": [],
        # TS2552 の "Did you mean 'Y'?" 抽出は設計スコープ外 (§6 は symbol 抽出のみ要求)。
        # 常に空リスト (Elixir 版との schema 互換のため key のみ維持)。
        "did_you_mean": [],
        "type_error_msg": "",
        "final_v_score": sample.get("final_v_score"),
        "final_verdict": sample.get("final_verdict"),
    }

    source = prompt + completion + "\n\n" + tests + "\n"

    t0 = time.time()
    try:
        with tempfile.TemporaryDirectory(prefix=f"ts-eval-{sample['name']}-") as td:
            tmp = Path(td)
            ts_path = tmp / "sample.ts"
            ts_path.write_text(source)
            out_dir = tmp / "out"

            tsc_proc = subprocess.run(
                [tsc_bin, "--noEmitOnError", "--outDir", str(out_dir), str(ts_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            diag = classify_diagnostics(tsc_proc.stdout)
            result["has_undefined"] = diag["has_undefined"]
            result["has_syntax_error"] = diag["has_syntax_error"]
            result["has_type_error"] = diag["has_type_error"]
            result["undef_symbols"] = diag["undef_symbols"]
            result["type_error_msg"] = diag["first_type_error_msg"]
            # tsc は compile 専任の exit code を返すので、Elixir 版のように
            # エラーパターンの否定から合成する必要がない (言語差、モジュール docstring 参照)。
            result["compile_ok"] = tsc_proc.returncode == 0

            if not result["compile_ok"]:
                result["exit_code"] = tsc_proc.returncode
                result["test_stderr"] = _trim(tsc_proc.stdout or tsc_proc.stderr)
            else:
                js_path = out_dir / "sample.js"
                node_proc = subprocess.run(
                    [node_bin, str(js_path)],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                combined = (node_proc.stderr or "") + "\n" + (node_proc.stdout or "")
                result["exit_code"] = node_proc.returncode
                result["test_ok"] = node_proc.returncode == 0
                result["test_stderr"] = _trim(combined)
                if not result["test_ok"]:
                    result["has_assertion_failure"] = True
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

    tsc_bin = resolve_tsc_bin(args.tsc_bin)
    node_bin = resolve_node_bin(args.node_bin)

    gen_dir = Path(args.generated_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 產屋 (ts4) runner が out_dir 直下に置く `_repair_summary.json` 等の
    # メタファイルを sample として誤読しないよう、先頭 "_" のファイルは除外する
    # (elixir_eval.py と同じ対策)。
    sample_files = sorted(
        f for f in gen_dir.glob("*.json") if not f.name.startswith("_")
    )
    if args.limit is not None:
        sample_files = sample_files[: args.limit]
    print(f"Evaluating {len(sample_files)} samples from {gen_dir}")
    print(f"  tsc = {tsc_bin}")
    print(f"  node = {node_bin}")

    per_sample = []
    counts = Counter()
    t_start = time.time()

    for i, sf in enumerate(sample_files):
        sample = json.loads(sf.read_text())
        r = run_one(
            sample,
            tsc_bin=tsc_bin,
            node_bin=node_bin,
            timeout=args.timeout,
        )
        per_sample.append(r)

        counts["total"] += 1
        for key in (
            "test_ok",
            "compile_ok",
            "has_undefined",
            "has_assertion_failure",
            "has_syntax_error",
            "has_type_error",
            "timed_out",
        ):
            if r[key]:
                counts[key] += 1

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
        # dead field、値は常に 0.0 (モジュール docstring / run_one の説明を参照)
        "function_clause_rate": 0.0,
        "syntax_error_rate": counts["has_syntax_error"] / max(n, 1),
        "type_error_rate": counts["has_type_error"] / max(n, 1),
        "timeout_rate": counts["timed_out"] / max(n, 1),
        "elapsed_total_sec": elapsed,
        "generated_dir": str(gen_dir),
        "tsc_bin": tsc_bin,
        "node_bin": node_bin,
        # 產屋 Step D 追加 key 相当 (elixir_eval.py と同一定義)
        "hack_gap": compute_hack_gap(per_sample),
    }
    (out_dir / "_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))

    print()
    print(f"=== Summary ({n} samples, {elapsed:.0f}s) ===")
    print(
        f"  PRIMARY   ts test pass rate     : "
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
    print(f"\nwrote -> {out_dir / '_summary.json'}")


if __name__ == "__main__":
    main()
