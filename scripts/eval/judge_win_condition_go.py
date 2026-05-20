"""
M6 (Go) — Win Condition 判定スクリプト

docs/roadmap_min_go.md の Win Condition:

    PRIMARY   go test pass@1     baseline +5pp 以上
    SECONDARY go vet clean 率    baseline +5pp 以上
    INDICATOR go build pass / undefined rate (参考表示のみ、判定対象外)

baseline 側 / yamato 側ともに `scripts/eval/go_eval.py` が出した
per-seed `_summary.json` を 1〜N 個まとめて受け取り、本スクリプト内で
平均 / SD / 95% CI を計算する。1 seed のみ (smoke run) でも判定可能、
3 seed なら 95% CI も併せて表示。

事前に各 seed で:
    1. scripts/eval/run_baseline_go.py     baseline 生成 (seed 0..N)
    2. scripts/eval/run_yamato_min_go.py   mode 別 yamato 生成 (seed 0..N)
    3. scripts/eval/go_eval.py             各生成 dir を評価して _summary.json を出す

使い方:
    # 1 seed (smoke)
    python3 scripts/eval/judge_win_condition_go.py \\
        --baseline data/eval/results/humaneval-go.baseline.seed0/_summary.json \\
        --yamato   data/eval/results/humaneval-go.yamato_min_go.full.seed0/_summary.json \\
        --mode full \\
        --out      baselines/yamato_min_go.full.smoke.judge.json

    # 3 seed (本番)
    python3 scripts/eval/judge_win_condition_go.py \\
        --baseline data/eval/results/humaneval-go.baseline.seed{0,1,2}/_summary.json \\
        --yamato   data/eval/results/humaneval-go.yamato_min_go.full.seed{0,1,2}/_summary.json \\
        --mode full \\
        --out      baselines/yamato_min_go.full.judge.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Win Condition 閾値 (roadmap_min_go.md)
TEST_DELTA_PT = 0.05   # PRIMARY: pass@1 baseline +5pp 以上
VET_DELTA_PT = 0.05    # SECONDARY: vet clean baseline +5pp 以上

# 95% CI 用 Student t 値 (両側 0.025, df=n-1)。n=1 のときは CI なし。
T_CRITICAL_95 = {1: None, 2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571}

METRIC_KEYS = ("test_pass_rate", "vet_pass_rate", "build_pass_rate", "undefined_rate")


def load_summaries(paths: list[Path]) -> list[dict]:
    out = []
    for p in paths:
        if not p.exists():
            raise SystemExit(f"summary file not found: {p}")
        out.append(json.loads(p.read_text()))
    return out


def aggregate(summaries: list[dict]) -> dict:
    """per-seed _summary.json 群 → metric ごとの mean / sd / 95% CI"""
    if not summaries:
        raise SystemExit("no summaries given")

    n = len(summaries)
    n_total = summaries[0].get("n_total")
    for s in summaries:
        if s.get("n_total") != n_total:
            raise SystemExit(
                f"n_total mismatch across seeds: expected {n_total}, "
                f"got {s.get('n_total')} in one of the summaries"
            )

    result: dict = {"n_seeds": n, "n_total": n_total, "metrics": {}}
    t_crit = T_CRITICAL_95.get(n)

    for key in METRIC_KEYS:
        values = [float(s.get(key, 0.0)) for s in summaries]
        mean = sum(values) / n
        if n >= 2:
            var = sum((v - mean) ** 2 for v in values) / (n - 1)
            sd = math.sqrt(var)
        else:
            sd = 0.0
        if t_crit is not None and n >= 2:
            half = t_crit * sd / math.sqrt(n)
            ci_low = mean - half
            ci_high = mean + half
        else:
            ci_low = ci_high = mean
        result["metrics"][key] = {
            "mean": mean,
            "sd": sd,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "per_seed": values,
        }
    return result


def judge(baseline: dict, yamato: dict, mode: str) -> dict:
    bm = baseline["metrics"]
    ym = yamato["metrics"]

    test_delta = ym["test_pass_rate"]["mean"] - bm["test_pass_rate"]["mean"]
    vet_delta = ym["vet_pass_rate"]["mean"] - bm["vet_pass_rate"]["mean"]
    build_delta = ym["build_pass_rate"]["mean"] - bm["build_pass_rate"]["mean"]
    undef_delta = ym["undefined_rate"]["mean"] - bm["undefined_rate"]["mean"]

    test_pass = test_delta >= TEST_DELTA_PT
    vet_pass = vet_delta >= VET_DELTA_PT
    overall = test_pass and vet_pass

    # CI 信頼性チェック (informational): yamato の CI 下限が baseline の +5pp 閾値を上回るか
    test_threshold = bm["test_pass_rate"]["mean"] + TEST_DELTA_PT
    vet_threshold = bm["vet_pass_rate"]["mean"] + VET_DELTA_PT
    test_ci_clears = ym["test_pass_rate"]["ci_low"] >= test_threshold
    vet_ci_clears = ym["vet_pass_rate"]["ci_low"] >= vet_threshold

    return {
        "mode": mode,
        "n_seeds_baseline": baseline["n_seeds"],
        "n_seeds_yamato": yamato["n_seeds"],
        "n_total": baseline["n_total"],
        "baseline": {k: bm[k] for k in METRIC_KEYS},
        "yamato": {k: ym[k] for k in METRIC_KEYS},
        "deltas_pp": {
            "test_pass_rate": test_delta,
            "vet_pass_rate": vet_delta,
            "build_pass_rate": build_delta,
            "undefined_rate": undef_delta,
        },
        "win_condition": {
            "primary": {
                "metric": "test_pass_rate",
                "threshold_pp": TEST_DELTA_PT,
                "delta_pp": test_delta,
                "passed": test_pass,
                "ci_lower_clears_threshold": test_ci_clears,
            },
            "secondary": {
                "metric": "vet_pass_rate",
                "threshold_pp": VET_DELTA_PT,
                "delta_pp": vet_delta,
                "passed": vet_pass,
                "ci_lower_clears_threshold": vet_ci_clears,
            },
            "overall": overall,
        },
    }


def fmt_pct(x: float) -> str:
    return f"{x * 100:6.2f}%"


def fmt_ci(stat: dict) -> str:
    # n=1 の smoke でも同じ幅で出すため CI は常に表示 (n=1 では CI 下限=上限=mean)
    return (
        f"{stat['mean'] * 100:6.2f}% "
        f"[{stat['ci_low'] * 100:6.2f},{stat['ci_high'] * 100:6.2f}]"
    )


def render_report(verdict: dict) -> str:
    b = verdict["baseline"]
    y = verdict["yamato"]
    d = verdict["deltas_pp"]
    wc = verdict["win_condition"]

    lines = [
        f"=== Win Condition (Go) — mode={verdict['mode']} ===",
        f"  N_total={verdict['n_total']}  seeds: baseline={verdict['n_seeds_baseline']}, yamato={verdict['n_seeds_yamato']}",
        "",
        f"                       baseline                    yamato                      Δ (pp)",
        f"  PRIMARY   pass@1   {fmt_ci(b['test_pass_rate'])}   {fmt_ci(y['test_pass_rate'])}   {d['test_pass_rate']*100:+6.2f}",
        f"  SECONDARY vet      {fmt_ci(b['vet_pass_rate'])}   {fmt_ci(y['vet_pass_rate'])}   {d['vet_pass_rate']*100:+6.2f}",
        f"  INDICATOR build    {fmt_ci(b['build_pass_rate'])}   {fmt_ci(y['build_pass_rate'])}   {d['build_pass_rate']*100:+6.2f}",
        f"  INDICATOR undef    {fmt_ci(b['undefined_rate'])}   {fmt_ci(y['undefined_rate'])}   {d['undefined_rate']*100:+6.2f}",
        "",
        f"  PRIMARY   pass@1 Δ ≥ +{TEST_DELTA_PT*100:.0f}pp     : {'PASS' if wc['primary']['passed'] else 'FAIL'}"
        f"    (CI lower clears threshold: {'yes' if wc['primary']['ci_lower_clears_threshold'] else 'no'})",
        f"  SECONDARY vet    Δ ≥ +{VET_DELTA_PT*100:.0f}pp     : {'PASS' if wc['secondary']['passed'] else 'FAIL'}"
        f"    (CI lower clears threshold: {'yes' if wc['secondary']['ci_lower_clears_threshold'] else 'no'})",
        "",
        f"  >> Win Condition: {'ACHIEVED' if wc['overall'] else 'NOT MET'}",
    ]
    return "\n".join(lines)


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", nargs="+", required=True,
                    help="baseline 側の per-seed _summary.json (1 個以上)")
    ap.add_argument("--yamato", nargs="+", required=True,
                    help="yamato 側の per-seed _summary.json (1 個以上)")
    ap.add_argument("--mode", default="full",
                    choices=["full", "no-kotodama", "no-firewall", "vanilla"],
                    help="表示用 (yamato 側がどの ablation mode で生成されたか)")
    ap.add_argument("--out", required=True)
    return ap.parse_args()


def main():
    # Windows cp932 等の非 UTF-8 stdout で日本語 / 罫線文字を吐けるようにする
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass

    args = parse_args()

    base_summaries = load_summaries([Path(p) for p in args.baseline])
    yam_summaries = load_summaries([Path(p) for p in args.yamato])

    baseline = aggregate(base_summaries)
    yamato = aggregate(yam_summaries)

    verdict = judge(baseline, yamato, args.mode)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(verdict, ensure_ascii=False, indent=2))

    print(render_report(verdict))
    print(f"\nwrote -> {out_path}")

    sys.exit(0 if verdict["win_condition"]["overall"] else 1)


if __name__ == "__main__":
    main()
