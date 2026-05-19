"""
Go 版 e2e 評価 — 生成 JSON 群を `go build` / `go vet` / `go test` で評価する。

docs/roadmap_min_go.md の評価指標 (重要度順):
    PRIMARY:   go build 成功率
    SECONDARY: undefined-symbol 出現率 (`undefined: xxx` のエラーが出るサンプル率)
    TERTIARY:  go vet clean 率, go test pass@1

各サンプルにつき独立した一時 Go module を作って実行する (cross-sample 干渉を避ける)。
prompt 末尾の package 名を保ち、completion をそのままぶら下げて *_test.go として書き出す。

使い方:
    python3 scripts/eval/go_eval.py \\
        --generated-dir data/eval/generated/humaneval-go.baseline.seed0 \\
        --out-dir data/eval/results/humaneval-go.baseline.seed0
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
import time
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# undefined symbol を表す Go コンパイラエラー (PRIMARY = 型ハルシ判定の核)
RE_UNDEFINED = re.compile(
    r"undefined:\s*\w+"          # 普通のシンボル参照失敗
    r"|undeclared name:\s*\w+"   # local var の typo 等
    r"|cannot find package"      # import パスがおかしい
    r"|imported and not used"    # import したのに使ってない
)

# `go test -run` 用にテストケース名を抽出する正規表現 (用途: pass 数の細分化、現状未使用)
RE_TEST_FUNC = re.compile(r"^func\s+(Test\w+)\s*\(", re.MULTILINE)


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--generated-dir", required=True,
                    help="run_baseline_go.py の出力 JSON 群が置かれたディレクトリ")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--timeout", type=float, default=30.0,
                    help="1 サンプルあたりの go test タイムアウト秒")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--go-bin", default="/usr/local/go/bin/go",
                    help="go コマンドへのパス (PATH に通っていなくても動くように)")
    ap.add_argument("--no-test", action="store_true",
                    help="go test を skip (go build + vet のみ、デバッグ用)")
    return ap.parse_args()


def derive_package_name(prompt: str) -> str:
    """prompt 先頭の `package <name>` を抜き出す。見つからなければ 'pkg'"""
    m = re.search(r"^\s*package\s+(\w+)", prompt, re.MULTILINE)
    return m.group(1) if m else "pkg"


def run_one(
    sample: dict,
    go_bin: str,
    timeout: float,
    skip_test: bool,
) -> dict:
    """1 サンプル評価。go build → go vet → go test の順で run、各成否を records"""
    prompt = sample["prompt"]
    completion = sample["completion"]
    tests = sample["tests"]
    pkg_name = derive_package_name(prompt)

    source = prompt + completion + "\n\n" + tests + "\n"

    result = {
        "name": sample["name"],
        "seed": sample.get("seed", 0),
        "pkg_name": pkg_name,
        "build_ok": False,
        "build_stderr": "",
        "vet_ok": False,
        "vet_stderr": "",
        "test_ok": False,
        "test_stderr": "",
        "has_undefined": False,
        "elapsed_sec": 0.0,
    }

    t0 = time.time()
    try:
        with tempfile.TemporaryDirectory(prefix=f"go-eval-{sample['name']}-") as td:
            tmp = Path(td)
            # 各サンプル独立 module
            (tmp / "go.mod").write_text(f"module sample\n\ngo 1.21\n")
            (tmp / "main_test.go").write_text(source)

            # 1. go build
            build = _run([go_bin, "build", "./..."], cwd=tmp, timeout=timeout)
            result["build_ok"] = build.returncode == 0
            result["build_stderr"] = _trim(build.stderr)
            combined_err = build.stderr

            # 2. go vet (build が通った場合のみ意味がある)
            if result["build_ok"]:
                vet = _run([go_bin, "vet", "./..."], cwd=tmp, timeout=timeout)
                result["vet_ok"] = vet.returncode == 0
                result["vet_stderr"] = _trim(vet.stderr)
                combined_err += "\n" + vet.stderr

            # 3. go test (skip 可能)
            if not skip_test and result["build_ok"]:
                test = _run([go_bin, "test", "-count=1", "./..."], cwd=tmp, timeout=timeout)
                result["test_ok"] = test.returncode == 0
                result["test_stderr"] = _trim(test.stderr) + "\n" + _trim(test.stdout)
                combined_err += "\n" + test.stderr

            # 型ハルシの純粋指標: build_ok=False で undefined パターンが出たもののみ true。
            # (build 成功時の `imported and not used` 等の警告は型ハルシではない)
            result["has_undefined"] = (
                not result["build_ok"] and bool(RE_UNDEFINED.search(combined_err))
            )
    except subprocess.TimeoutExpired as e:
        result["build_stderr"] = f"timeout: {e}"
    except Exception as e:
        result["build_stderr"] = f"exception: {e}"

    result["elapsed_sec"] = time.time() - t0
    return result


def _run(cmd, cwd, timeout):
    """subprocess.run の薄ラッパー (stdout/stderr を text mode で受ける)"""
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _trim(s: str, max_chars: int = 800) -> str:
    if s is None:
        return ""
    if len(s) <= max_chars:
        return s
    return s[:max_chars] + f"... [+{len(s) - max_chars} chars]"


def main():
    args = parse_args()

    if not Path(args.go_bin).exists():
        which = shutil.which("go")
        if which is None:
            raise SystemExit(f"go binary not found at {args.go_bin} and not on PATH")
        args.go_bin = which

    gen_dir = Path(args.generated_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    sample_files = sorted(gen_dir.glob("*.json"))
    if args.limit is not None:
        sample_files = sample_files[: args.limit]
    print(f"Evaluating {len(sample_files)} samples from {gen_dir}")

    per_sample = []
    counts = Counter()
    t_start = time.time()

    for i, sf in enumerate(sample_files):
        sample = json.loads(sf.read_text())
        r = run_one(sample, args.go_bin, args.timeout, args.no_test)
        per_sample.append(r)

        # 集計
        counts["total"] += 1
        if r["build_ok"]:
            counts["build_ok"] += 1
        if r["vet_ok"]:
            counts["vet_ok"] += 1
        if r["test_ok"]:
            counts["test_ok"] += 1
        if r["has_undefined"]:
            counts["has_undefined"] += 1

        status = "BUILD ✓" if r["build_ok"] else "BUILD ✗"
        if not args.no_test:
            status += " · " + ("TEST ✓" if r["test_ok"] else "TEST ✗")
        print(f"  [{i+1}/{len(sample_files)}] {sample['name']:<55s} {status}  ({r['elapsed_sec']:.1f}s)")

        # 個別 result を保存
        (out_dir / f"{sample['name']}__s0.result.json").write_text(
            json.dumps(r, ensure_ascii=False, indent=2)
        )

    elapsed = time.time() - t_start
    n = counts["total"]
    summary = {
        "n_total": n,
        "build_pass_rate": counts["build_ok"] / max(n, 1),
        "vet_pass_rate": counts["vet_ok"] / max(n, 1),
        "test_pass_rate": counts["test_ok"] / max(n, 1),
        "undefined_rate": counts["has_undefined"] / max(n, 1),
        "elapsed_total_sec": elapsed,
        "generated_dir": str(gen_dir),
    }
    (out_dir / "_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))

    print()
    print(f"=== Summary ({n} samples, {elapsed:.0f}s) ===")
    print(f"  PRIMARY   go build pass rate : {summary['build_pass_rate']*100:6.2f}% ({counts['build_ok']}/{n})")
    print(f"  SECONDARY undefined rate     : {summary['undefined_rate']*100:6.2f}% ({counts['has_undefined']}/{n})")
    print(f"  TERTIARY  go vet  clean rate : {summary['vet_pass_rate']*100:6.2f}% ({counts['vet_ok']}/{n})")
    if not args.no_test:
        print(f"  TERTIARY  go test pass rate  : {summary['test_pass_rate']*100:6.2f}% ({counts['test_ok']}/{n})")
    print(f"\nwrote -> {out_dir/'_summary.json'}")


if __name__ == "__main__":
    main()
