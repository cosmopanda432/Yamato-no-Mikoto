"""v_score slice 改訂 Phase A — オフライン再採点分析 (GPU 不要)。

vscore_slice_設計書_v0.md Phase A の実装。eli4 pilot 0 の実生成ダンプ
(`pilot0_full_outputs.tar.gz`) を展開し、`src_min_eli4/kojiki_lm/elixir_evaluator.py`
の `_compute_score_and_flags` を **import のみ** (変更なし) で 3 通りに呼ぶ:

  (a) `wrapped_prompt + raw_completion` 全文  = 現行方式の再現 (replay)
  (b) `raw_completion` のみ                   = slice 案
  (c) `prompt` のみ                           = prompt インフレの直接証拠

wrapped_prompt の再構築は runner (`scripts/eval/run_yamato_min_elixir4.py`) の
`build_wrapped_prompt` と同値:

    wrapped_prompt = prompt + (f"  # 補足: {hint}\n" if hint else "") + trace_seed

(runner を import すると torch/pyarrow が必要になるため、この 1 式のみ複製する。
`trace_seed` / `hint` はダンプ JSON のフィールドをそのまま使う。)

光明想 (KoumyouSo) の overriding HALT gate は evaluator と同じく
`generated_text = raw_completion` に対して適用する (gate は old/new 共通なので
採点方式の比較には影響しない)。KoumyouSo 閾値は pilot0.log 記載の実行値
(min_lines=1, min_chars=20, grace=16, seed='  # 思考: ') をデフォルトにしている。

既知の再現限界 (レポートに明記):
  - decoder の final_verdict は「最後の firewall check step (16 token 刻み or
    最終 step)」時点の text に対する評価。stop_token 途中終了 sample では
    check 時点 text ⊂ 全文となるため、(a) 全文 replay と一致しない場合がある。
    token 単位の途中 text はダンプから復元不能 (tokenizer 非依存で解析するため)。
    → 再現率と不一致内訳を出力する。

使い方:
    python3 scripts/analysis/replay_vscore_slice.py \
        --tar data/eval/results/runpod_eli4_20260717/pilot0_full_outputs.tar.gz \
        --workdir /tmp/vscore_replay \
        --out-json /tmp/vscore_replay/metrics.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import tarfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# 再採点で HALT/COMMIT 圏の判定に使う閾値 (EvaluatorConfig デフォルトと同値、
# 設計書の指示により据え置きで評価する)
COMMIT_THRESHOLD = 0.7
HALT_THRESHOLD = 0.3

SWEEP_THRESHOLDS = [round(0.1 * i, 1) for i in range(1, 10)]  # 0.1 .. 0.9


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument(
        "--tar",
        default=str(
            REPO_ROOT
            / "data/eval/results/runpod_eli4_20260717/pilot0_full_outputs.tar.gz"
        ),
        help="pilot0_full_outputs.tar.gz へのパス",
    )
    ap.add_argument(
        "--workdir",
        required=True,
        help="tar の展開先 (既に展開済みなら再展開しない)",
    )
    ap.add_argument("--out-json", default=None, help="集計 metrics の JSON 出力先")
    # KoumyouSo 閾値 (pilot0.log 記載の実行値をデフォルトに)
    ap.add_argument("--min-trace-lines", type=int, default=1)
    ap.add_argument("--min-trace-chars", type=int, default=20)
    ap.add_argument("--grace-period-chars", type=int, default=16)
    return ap.parse_args()


def load_kojiki_lm():
    """src_min_eli4 の kojiki_lm を sys.path 挿入で import する (変更は一切しない)。

    他 variant の kojiki_lm が既に import 済みだと module cache 衝突で
    別実装を掴むため、その場合は fail-fast する。
    """
    if "kojiki_lm" in sys.modules:
        raise SystemExit(
            "kojiki_lm が既に import されています (module cache 衝突)。"
            "新しい Python プロセスで実行してください。"
        )
    sys.path.insert(0, str(REPO_ROOT / "src_min_eli4"))
    from kojiki_lm.elixir_evaluator import ElixirEvaluator  # noqa: E402
    from kojiki_lm.koumyou_so import KoumyouSo, KoumyouSoConfig  # noqa: E402

    return ElixirEvaluator, KoumyouSo, KoumyouSoConfig


def extract_tar(tar_path: Path, workdir: Path) -> Path:
    """tar を workdir に展開する (展開済みならスキップ)。展開 root を返す。"""
    marker = workdir / "data" / "eval" / "generated"
    if not marker.is_dir():
        workdir.mkdir(parents=True, exist_ok=True)
        with tarfile.open(tar_path, "r:gz") as tf:
            tf.extractall(workdir)
    return workdir


def load_results(results_dir: Path) -> dict[str, dict]:
    """results dir の `<name>__s0.result.json` 群を name -> dict で返す。"""
    out = {}
    if not results_dir.is_dir():
        return out
    for p in sorted(results_dir.glob("*__s0.result.json")):
        d = json.loads(p.read_text())
        out[d["name"]] = d
    return out


def build_wrapped_prompt_from_sample(sample: dict) -> str:
    """runner の build_wrapped_prompt / round0 式と同値の wrapped_prompt を再構築。

    round 0 / 非 repair mode: hint フィールドが無い or 空 → prompt + trace_seed。
    repair round >= 1: prompt + hint_line + trace_seed。
    非 koumyou mode: trace_seed == "" なので prompt のまま。
    """
    prompt = sample["prompt"]
    hint = sample.get("hint") or ""
    trace_seed = sample.get("trace_seed") or ""
    hint_line = f"  # 補足: {hint}\n" if hint else ""
    return prompt + hint_line + trace_seed


def replay_mode(gen_dir: Path, results_by_name: dict[str, dict],
                evaluator, koumyou_so) -> list[dict]:
    """1 mode dir の最終回答 JSON 群を 3 通りに再採点した per-sample record を返す。"""
    records = []
    for p in sorted(gen_dir.glob("*__s0.json")):
        s = json.loads(p.read_text())
        name = s["name"]
        raw = s["raw_completion"]
        wrapped = build_wrapped_prompt_from_sample(s)
        full = wrapped + raw

        score_a, _ = evaluator._compute_score_and_flags(full)
        score_b, _ = evaluator._compute_score_and_flags(raw)
        score_c, _ = evaluator._compute_score_and_flags(s["prompt"])

        # 光明想 gate (koumyou mode のみ)。evaluator.__call__ と同じく
        # generated 部分 (= raw_completion) に対して判定する。
        gate_halt = False
        gate_status = None
        if s.get("koumyou_enabled") and koumyou_so is not None:
            tv = koumyou_so.validate(raw)
            gate_status = tv.status.value
            gate_halt = tv.is_terminal_failure

        v_a = 0.0 if gate_halt else score_a
        v_b = 0.0 if gate_halt else score_b
        verdict_a = "halt" if gate_halt else decide(score_a)
        verdict_b = "halt" if gate_halt else decide(score_b)

        res = results_by_name.get(name, {})
        trace_info = s.get("trace_info") or {}
        records.append({
            "name": name,
            "test_ok": res.get("test_ok"),
            "has_undefined": res.get("has_undefined"),
            "dump_v": s.get("final_v_score"),
            "dump_verdict": s.get("final_verdict"),
            "score_a": score_a,
            "score_b": score_b,
            "score_c": score_c,
            "v_a": v_a,
            "v_b": v_b,
            "verdict_a": verdict_a,
            "verdict_b": verdict_b,
            "gate_halt": gate_halt,
            "gate_status": gate_status,
            "dump_trace_status": trace_info.get("status"),
            "halted_early": s.get("halted_early"),
            "stopped_at_stop_token": s.get("stopped_at_stop_token"),
            "round": s.get("round"),
            "hint": s.get("hint") or "",
        })
    return records


def decide(v: float) -> str:
    if v >= COMMIT_THRESHOLD:
        return "commit"
    if v < HALT_THRESHOLD:
        return "halt"
    return "repair"


def hack_gap(records: list[dict], v_key: str) -> tuple[float, int, int]:
    """P(test_ok == False | v >= 0.7)。(rate, numer, denom) を返す。

    scripts/eval/elixir_eval.py compute_hack_gap と同定義
    (v is None → 分母から除外、分母 0 → 0.0)。test_ok 不明 sample は除外。
    """
    numer = denom = 0
    for r in records:
        v = r[v_key]
        if v is None or v < COMMIT_THRESHOLD or r["test_ok"] is None:
            continue
        denom += 1
        if not r["test_ok"]:
            numer += 1
    return (numer / denom) if denom else 0.0, numer, denom


def verdict_dist(records: list[dict], key: str) -> dict[str, int]:
    dist: dict[str, int] = {}
    for r in records:
        k = r[key] if r[key] is not None else "none"
        dist[k] = dist.get(k, 0) + 1
    return dist


def halt_zone_rate_given_test_ok(records: list[dict], v_key: str) -> tuple[float, int, int]:
    """P(v < 0.3 | test_ok == True)。「test_ok なのに halt 圏」取りこぼし率。"""
    numer = denom = 0
    for r in records:
        if r["test_ok"] is not True or r[v_key] is None:
            continue
        denom += 1
        if r[v_key] < HALT_THRESHOLD:
            numer += 1
    return (numer / denom) if denom else 0.0, numer, denom


def sweep_tpr_fpr(records: list[dict], v_key: str) -> list[dict]:
    """閾値 sweep: TPR = P(v>=t | test_ok), FPR = P(v>=t | test fail)。"""
    labeled = [r for r in records if r["test_ok"] is not None and r[v_key] is not None]
    pos = [r[v_key] for r in labeled if r["test_ok"]]
    neg = [r[v_key] for r in labeled if not r["test_ok"]]
    rows = []
    for t in SWEEP_THRESHOLDS:
        tpr = sum(1 for v in pos if v >= t) / len(pos) if pos else float("nan")
        fpr = sum(1 for v in neg if v >= t) / len(neg) if neg else float("nan")
        rows.append({"threshold": t, "tpr": tpr, "fpr": fpr})
    return rows


def rank_auc(records: list[dict], v_key: str) -> float | None:
    """Mann-Whitney U ベースの AUC (tie は 0.5)。pos/neg いずれか空なら None。"""
    labeled = [r for r in records if r["test_ok"] is not None and r[v_key] is not None]
    pos = [r[v_key] for r in labeled if r["test_ok"]]
    neg = [r[v_key] for r in labeled if not r["test_ok"]]
    if not pos or not neg:
        return None
    total = 0.0
    for p in pos:
        for n in neg:
            if p > n:
                total += 1.0
            elif p == n:
                total += 0.5
    return total / (len(pos) * len(neg))


def score_stats(values: list[float]) -> dict:
    if not values:
        return {}
    qs = statistics.quantiles(values, n=4)
    return {
        "n": len(values),
        "min": min(values),
        "q1": qs[0],
        "median": qs[1],
        "q3": qs[2],
        "max": max(values),
        "mean": statistics.fmean(values),
        "ge_0.7": sum(1 for v in values if v >= COMMIT_THRESHOLD) / len(values),
        "ge_0.5": sum(1 for v in values if v >= 0.5) / len(values),
    }


def reproduction_report(records: list[dict], atol: float = 1e-6) -> dict:
    """(a) 全文 replay がダンプの final_v_score をどの程度再現するか + 不一致内訳。"""
    with_dump = [r for r in records if r["dump_v"] is not None]
    if not with_dump:
        return {"n": 0}
    exact = [r for r in with_dump if abs(r["v_a"] - r["dump_v"]) < atol]
    mism = [r for r in with_dump if abs(r["v_a"] - r["dump_v"]) >= atol]
    breakdown = {"stopped_at_stop_token": 0, "halted_early": 0, "other": 0}
    for r in mism:
        if r["stopped_at_stop_token"]:
            breakdown["stopped_at_stop_token"] += 1
        elif r["halted_early"]:
            breakdown["halted_early"] += 1
        else:
            breakdown["other"] += 1
    diffs = [abs(r["v_a"] - r["dump_v"]) for r in mism]
    verdict_match = [
        r for r in with_dump
        if r["dump_verdict"] is not None and r["verdict_a"] == r["dump_verdict"]
    ]
    trace_cmp = [
        r for r in records
        if r["gate_status"] is not None and r["dump_trace_status"] is not None
    ]
    trace_match = [r for r in trace_cmp if r["gate_status"] == r["dump_trace_status"]]
    return {
        "n": len(with_dump),
        "v_exact": len(exact),
        "v_exact_rate": len(exact) / len(with_dump),
        "verdict_match": len(verdict_match),
        "verdict_match_rate": len(verdict_match) / len(with_dump),
        "mismatch_breakdown": breakdown,
        "mismatch_abs_diff_median": statistics.median(diffs) if diffs else 0.0,
        "mismatch_abs_diff_max": max(diffs) if diffs else 0.0,
        "trace_status_n": len(trace_cmp),
        "trace_status_match": len(trace_match),
    }


def summarize_mode(records: list[dict]) -> dict:
    labeled = [r for r in records if r["test_ok"] is not None]
    hg_dump = hack_gap(records, "dump_v")
    hg_a = hack_gap(records, "v_a")
    hg_b = hack_gap(records, "v_b")
    hz_a = halt_zone_rate_given_test_ok(records, "v_a")
    hz_b = halt_zone_rate_given_test_ok(records, "v_b")
    return {
        "n": len(records),
        "n_with_test": len(labeled),
        "test_pass_rate": (
            sum(1 for r in labeled if r["test_ok"]) / len(labeled) if labeled else None
        ),
        "hack_gap_dump": {"rate": hg_dump[0], "numer": hg_dump[1], "denom": hg_dump[2]},
        "hack_gap_replay_full": {"rate": hg_a[0], "numer": hg_a[1], "denom": hg_a[2]},
        "hack_gap_slice": {"rate": hg_b[0], "numer": hg_b[1], "denom": hg_b[2]},
        "verdict_dist_dump": verdict_dist(records, "dump_verdict"),
        "verdict_dist_replay_full": verdict_dist(records, "verdict_a"),
        "verdict_dist_slice": verdict_dist(records, "verdict_b"),
        "test_ok_halt_zone_full": {"rate": hz_a[0], "numer": hz_a[1], "denom": hz_a[2]},
        "test_ok_halt_zone_slice": {"rate": hz_b[0], "numer": hz_b[1], "denom": hz_b[2]},
        "sweep_full": sweep_tpr_fpr(records, "v_a"),
        "sweep_slice": sweep_tpr_fpr(records, "v_b"),
        "auc_full": rank_auc(records, "v_a"),
        "auc_slice": rank_auc(records, "v_b"),
        "prompt_only_stats": score_stats([r["score_c"] for r in records]),
        "reproduction": reproduction_report(records),
    }


def fmt_pct(x) -> str:
    return "-" if x is None else f"{x * 100:.2f}%"


def print_report(all_summaries: dict[str, dict]) -> None:
    for mode, s in all_summaries.items():
        print(f"\n=== {mode} (n={s['n']}, with_test={s['n_with_test']}, "
              f"pass={fmt_pct(s['test_pass_rate'])}) ===")
        rep = s["reproduction"]
        if rep.get("n"):
            print(f"  再現率: v_score exact {rep['v_exact']}/{rep['n']} "
                  f"({rep['v_exact_rate']*100:.1f}%), verdict match "
                  f"{rep['verdict_match']}/{rep['n']} ({rep['verdict_match_rate']*100:.1f}%)")
            print(f"    不一致内訳: {rep['mismatch_breakdown']}  "
                  f"|Δv| median={rep['mismatch_abs_diff_median']:.3f} "
                  f"max={rep['mismatch_abs_diff_max']:.3f}")
            if rep["trace_status_n"]:
                print(f"    trace status 一致: {rep['trace_status_match']}/{rep['trace_status_n']}")
        for k, label in (("hack_gap_dump", "hack_gap (dump)"),
                         ("hack_gap_replay_full", "hack_gap (replay 全文 a)"),
                         ("hack_gap_slice", "hack_gap (slice b)")):
            h = s[k]
            print(f"  {label:28s}: {fmt_pct(h['rate'])} ({h['numer']}/{h['denom']})")
        print(f"  verdict dist  dump : {s['verdict_dist_dump']}")
        print(f"  verdict dist  a 全文: {s['verdict_dist_replay_full']}")
        print(f"  verdict dist  b slice: {s['verdict_dist_slice']}")
        ha, hb = s["test_ok_halt_zone_full"], s["test_ok_halt_zone_slice"]
        print(f"  test_ok∧halt圏 (<0.3)  a: {fmt_pct(ha['rate'])} ({ha['numer']}/{ha['denom']})"
              f"  b: {fmt_pct(hb['rate'])} ({hb['numer']}/{hb['denom']})")
        if s["auc_full"] is not None:
            print(f"  AUC (rank)  a 全文: {s['auc_full']:.3f}  b slice: {s['auc_slice']:.3f}")
            print("  sweep t: " + "  ".join(
                f"{row['threshold']:.1f}" for row in s["sweep_full"]))
            print("   a TPR : " + "  ".join(f"{row['tpr']:.2f}" for row in s["sweep_full"]))
            print("   a FPR : " + "  ".join(f"{row['fpr']:.2f}" for row in s["sweep_full"]))
            print("   b TPR : " + "  ".join(f"{row['tpr']:.2f}" for row in s["sweep_slice"]))
            print("   b FPR : " + "  ".join(f"{row['fpr']:.2f}" for row in s["sweep_slice"]))
        ps = s["prompt_only_stats"]
        if ps:
            print(f"  prompt-only (c): median={ps['median']:.2f} "
                  f"q1={ps['q1']:.2f} q3={ps['q3']:.2f} mean={ps['mean']:.2f} "
                  f">=0.7: {fmt_pct(ps['ge_0.7'])}  >=0.5: {fmt_pct(ps['ge_0.5'])}")


def main():
    args = parse_args()
    ElixirEvaluator, KoumyouSo, KoumyouSoConfig = load_kojiki_lm()

    root = extract_tar(Path(args.tar), Path(args.workdir))
    gen_root = root / "data" / "eval" / "generated"
    res_root = root / "data" / "eval" / "results"

    evaluator = ElixirEvaluator()
    koumyou_so = KoumyouSo(KoumyouSoConfig(
        min_trace_lines=args.min_trace_lines,
        min_trace_chars=args.min_trace_chars,
        grace_period_chars=args.grace_period_chars,
        trace_seed="  # 思考: ",
    ))

    all_summaries: dict[str, dict] = {}
    all_records: dict[str, list[dict]] = {}
    for gen_dir in sorted(gen_root.iterdir()):
        if not gen_dir.is_dir():
            continue
        mode = gen_dir.name
        results_by_name = load_results(res_root / mode)
        records = replay_mode(gen_dir, results_by_name, evaluator, koumyou_so)
        if not records:
            continue
        all_records[mode] = records
        all_summaries[mode] = summarize_mode(records)

    print_report(all_summaries)

    if args.out_json:
        out = Path(args.out_json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(
            {"summaries": all_summaries, "records": all_records},
            ensure_ascii=False, indent=2,
        ))
        print(f"\nmetrics written: {out}")


if __name__ == "__main__":
    main()
