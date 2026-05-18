"""
M6 — Win Condition 判定スクリプト

baselines/ にある Stage 2 学習済 (`*.step2000.summary.json` / `*.step2000.aux.json`) と、
新規生成した Yamato-min 簡易版の結果を比較し、roadmap_min.md の Win Condition

    tsc strict           +5 pt 以上
    hallucination 率    × 0.5 以下 (TS2304 "Cannot find name" 発生サンプル率)

の達成可否を 1 ファイル `baselines/yamato_min.summary.json` に書き出す。

事前に以下を実行しておく:
    1. scripts/eval/run_yamato_min.py    で完成形を生成
    2. scripts/eval/run_tests.py         で pass@1 を集計
    3. scripts/eval/aux_metrics.py       で tsc strict / any rate を集計

使い方:
    python3 scripts/eval/judge_win_condition.py \\
        --dataset humaneval-ts \\
        --yamato-summary data/eval/results/humaneval-ts.yamato_min/_summary.json \\
        --yamato-aux     data/eval/results/humaneval-ts.yamato_min/_aux_metrics.json \\
        --baseline-stem  step2000 \\
        --out            baselines/yamato_min.humaneval-ts.summary.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Win Condition の閾値 (roadmap_min.md 由来)
TSC_STRICT_DELTA_PT = 0.05   # +5 percentage points 以上
HALLUC_RATIO_MAX = 0.5       # ×0.5 以下

# 「未定義シンボル参照」を意味する TS エラーコード
HALLUCINATION_ERROR_CODE = 2304   # "Cannot find name"


def hallucination_rate_from_aux(aux: dict) -> float:
    """aux JSON の top_error_codes から TS2304 (Cannot find name) 発生率を抽出"""
    n_total = aux.get("n_total", 0)
    if n_total <= 0:
        return 0.0
    for code, count in aux.get("top_error_codes", []) or []:
        if int(code) == HALLUCINATION_ERROR_CODE:
            return count / n_total
    return 0.0


def load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"required file not found: {path}")
    return json.loads(path.read_text())


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, choices=["humaneval-ts", "mbpp-ts"])
    ap.add_argument("--yamato-summary", required=True,
                    help="run_tests.py が出した yamato-min の _summary.json")
    ap.add_argument("--yamato-aux", required=True,
                    help="aux_metrics.py が出した yamato-min の _aux_metrics.json")
    ap.add_argument("--baseline-stem", default="step2000",
                    choices=["baseline", "step2000"],
                    help="比較対象の baseline ファイル名語尾")
    ap.add_argument("--baselines-dir", default=str(REPO_ROOT / "baselines"))
    ap.add_argument("--out", required=True)
    return ap.parse_args()


def judge(args) -> dict:
    base_dir = Path(args.baselines_dir)
    base_summary = load_json(base_dir / f"{args.dataset}.{args.baseline_stem}.summary.json")
    base_aux = load_json(base_dir / f"{args.dataset}.{args.baseline_stem}.aux.json")

    yamato_summary = load_json(Path(args.yamato_summary))
    yamato_aux = load_json(Path(args.yamato_aux))

    # メトリクス抽出
    base_pass_at_1 = float(base_summary.get("pass_at_1", 0.0))
    yamato_pass_at_1 = float(yamato_summary.get("pass_at_1", 0.0))

    base_tsc = float(base_aux.get("tsc_strict_pass_rate", 0.0))
    yamato_tsc = float(yamato_aux.get("tsc_strict_pass_rate", 0.0))

    base_halluc = hallucination_rate_from_aux(base_aux)
    yamato_halluc = hallucination_rate_from_aux(yamato_aux)

    base_any = float(base_aux.get("any_usage_rate", 0.0))
    yamato_any = float(yamato_aux.get("any_usage_rate", 0.0))

    # 判定
    tsc_delta = yamato_tsc - base_tsc
    tsc_pass = tsc_delta >= TSC_STRICT_DELTA_PT

    if base_halluc <= 0.0:
        # ベースが既に 0 なら下げる先がない: Yamato も 0 ならパス
        halluc_pass = yamato_halluc <= 0.0
        halluc_ratio = 0.0 if yamato_halluc <= 0.0 else float("inf")
    else:
        halluc_ratio = yamato_halluc / base_halluc
        halluc_pass = halluc_ratio <= HALLUC_RATIO_MAX

    win = tsc_pass and halluc_pass

    return {
        "dataset": args.dataset,
        "baseline_stem": args.baseline_stem,
        "baseline": {
            "pass_at_1": base_pass_at_1,
            "tsc_strict_pass_rate": base_tsc,
            "hallucination_rate_ts2304": base_halluc,
            "any_usage_rate": base_any,
        },
        "yamato_min": {
            "pass_at_1": yamato_pass_at_1,
            "tsc_strict_pass_rate": yamato_tsc,
            "hallucination_rate_ts2304": yamato_halluc,
            "any_usage_rate": yamato_any,
        },
        "deltas": {
            "pass_at_1_pp": yamato_pass_at_1 - base_pass_at_1,
            "tsc_strict_pp": tsc_delta,
            "hallucination_ratio": halluc_ratio,
        },
        "win_condition": {
            "tsc_strict_pp_threshold": TSC_STRICT_DELTA_PT,
            "tsc_strict_pp_passed": tsc_pass,
            "hallucination_ratio_max": HALLUC_RATIO_MAX,
            "hallucination_ratio_passed": halluc_pass,
            "overall": win,
        },
    }


def render_report(verdict: dict) -> str:
    b = verdict["baseline"]
    y = verdict["yamato_min"]
    d = verdict["deltas"]
    w = verdict["win_condition"]
    lines = [
        f"=== Win Condition Judgement — {verdict['dataset']} vs {verdict['baseline_stem']} ===",
        f"",
        f"                         baseline      yamato_min    Δ",
        f"  pass@1                {b['pass_at_1']*100:6.2f}%       {y['pass_at_1']*100:6.2f}%      {d['pass_at_1_pp']*100:+5.2f}pp",
        f"  tsc strict pass rate  {b['tsc_strict_pass_rate']*100:6.2f}%       {y['tsc_strict_pass_rate']*100:6.2f}%      {d['tsc_strict_pp']*100:+5.2f}pp",
        f"  halluc rate (TS2304)  {b['hallucination_rate_ts2304']*100:6.2f}%       {y['hallucination_rate_ts2304']*100:6.2f}%      ratio={d['hallucination_ratio']:.2f}x",
        f"  any usage rate        {b['any_usage_rate']*100:6.2f}%       {y['any_usage_rate']*100:6.2f}%",
        f"",
        f"  tsc strict ≥ +{w['tsc_strict_pp_threshold']*100:.0f}pp        : {'PASS' if w['tsc_strict_pp_passed'] else 'FAIL'}",
        f"  halluc ratio ≤ {w['hallucination_ratio_max']:.2f}x      : {'PASS' if w['hallucination_ratio_passed'] else 'FAIL'}",
        f"",
        f"  >> Win Condition: {'ACHIEVED' if w['overall'] else 'NOT MET'}",
    ]
    return "\n".join(lines)


def main():
    args = parse_args()
    verdict = judge(args)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(verdict, ensure_ascii=False, indent=2))

    print(render_report(verdict))
    print(f"\nwrote -> {out_path}")

    sys.exit(0 if verdict["win_condition"]["overall"] else 1)


if __name__ == "__main__":
    main()
