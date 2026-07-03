#!/usr/bin/env bash
# RunPod 上での Yamato Elixir target (src_min_eli4, 產屋 REPAIR) ベンチ実行 runbook
#
# eli3 (`scripts/runpod_bench_eli3.sh`) と同形だが、Step C (還降 loop) を追加:
#   - 3 mode (firewall-off / firewall-on / koumyou-on) → 4 mode に拡張
#     (koumyou-on と全く同じ Firewall/KoumyouSo 設定 + round 型 REPAIR = repair-on)
#   - 新規 mode `repair-on`: round 0 (koumyou-on と byte-identical) の後、
#     test_ok==False の sample だけ最大 --max-rounds 回、先頭から全再生成する
#     (詳細: .superpowers/sdd/task-C-brief.md §5、src_min_eli4/kojiki_lm/ashibune.py)
#   - repair-on は生成 host に elixir が必須 (round 内 post-hoc eval を回すため)。
#     elixir install step は eli3 から流用済み (`install_elixir_if_missing`)
#
# 設計方針 (eli3 と同じ):
#   - 全フェーズ idempotent: 出力 _summary.json が既にあればスキップ
#   - フェーズ単位で sub-command 化、smoke → pilot → 3seed の順
#   - judge 用 baseline は同 pod で取り直す
#
# 想定フロー (RunPod A5000 24GB pod に SSH 接続後):
#   bash scripts/runpod_bench_eli4.sh setup              # 約 10-15 分 (eli3 setup 済なら数十秒)
#   bash scripts/runpod_bench_eli4.sh smoke              # 約 3-5 分 (koumyou-on × 5 問)
#   bash scripts/runpod_bench_eli4.sh smoke_repair       # 約 10-15 分 (repair-on × 20 問、還降発火確認、DoD-C-3)
#   bash scripts/runpod_bench_eli4.sh dod_round0         # 約 5-10 分 (DoD-C-1: round0 byte-identity vs eli3 koumyou-on)
#   bash scripts/runpod_bench_eli4.sh dod_regression     # 約 10-15 分 (DoD-C-2: 既存 3 mode の出力が eli3 と一致、--limit 5)
#   bash scripts/runpod_bench_eli4.sh baseline 0         # 約 15-25 分 (1 seed × 161 問、eli2/eli3 baseline と同一なので skip 可)
#   bash scripts/runpod_bench_eli4.sh pilot 0            # 約 2-2.5h   (4 mode × seed 0 + judge)
#   bash scripts/runpod_bench_eli4.sh ci                 # 約 6-8h     (4 mode × seed 0/1/2 + judge、3 seed CI)
#
# 環境変数:
#   REPO_ROOT          リポジトリルート (default: スクリプトの 1 つ上)
#   MODEL_DIR          Qwen モデルディレクトリ (default: $REPO_ROOT/models/Qwen2.5-Coder-7B-Instruct)
#   QUANTIZE           "4bit" | "8bit" | "none" (default: 4bit)
#   MAX_NEW_TOKENS     (default: 256)
#   TEMPERATURE        (default: 0.2)
#   DATASET            MultiPL-E subset (default: humaneval-elixir)。mbpp-elixir (397 問) も可
#   SKIP_EXISTING      "1" で既出力を skip (default: 1)
#   LIMIT              生成上限 (smoke 系以外では未設定 = 全問)
#   MIN_TRACE_LINES    KoumyouSo 閾値 (default: 1)
#   MIN_TRACE_CHARS    KoumyouSo 閾値 (default: 20)
#   MAX_ROUNDS         repair-on の repair round 数上限 (default: 2)
#   EVAL_TIMEOUT       repair-on の round 内 post-hoc eval timeout 秒 (default: 5.0)
#
# eli3 との実行ファイル差分:
#   - runner = run_yamato_min_elixir4.py (4 mode 対応、repair-on で round 型 REPAIR)
#   - eval = elixir_eval.py (共通、変更なし)
#   - gen/eval dir prefix: yamato_min_elixir4 (eli3 とは別ディレクトリ)
#   - repair-on のみ出力に round_0/ round_1/ ... ashibune.jsonl _repair_summary.json が追加される
#
# 終了コード:
#   0 = フェーズ正常終了 (judge は Win Condition 達成時のみ 0)
#   1 = フェーズ途中で失敗 / Win Condition 未達 / DoD 比較で diff あり

set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$REPO_ROOT"

MODEL_DIR="${MODEL_DIR:-$REPO_ROOT/models/Qwen2.5-Coder-7B-Instruct}"
QUANTIZE="${QUANTIZE:-4bit}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-256}"
TEMPERATURE="${TEMPERATURE:-0.2}"
SKIP_EXISTING="${SKIP_EXISTING:-1}"
DATASET="${DATASET:-humaneval-elixir}"
MIN_TRACE_LINES="${MIN_TRACE_LINES:-1}"
MIN_TRACE_CHARS="${MIN_TRACE_CHARS:-20}"
MAX_ROUNDS="${MAX_ROUNDS:-2}"
EVAL_TIMEOUT="${EVAL_TIMEOUT:-5.0}"

PARQUET="$REPO_ROOT/data/raw/multipl_e/${DATASET}/test-00000-of-00001.parquet"
MODES=("firewall-off" "firewall-on" "koumyou-on" "repair-on")

# --- helpers ----------------------------------------------------------------

log() { printf '[%s] %s\n' "$(date +'%H:%M:%S')" "$*"; }
err() { printf '[%s] ERROR: %s\n' "$(date +'%H:%M:%S')" "$*" >&2; }

maybe_sudo() {
    if [[ "$EUID" -eq 0 ]] || ! command -v sudo >/dev/null 2>&1; then
        "$@"
    else
        sudo "$@"
    fi
}

install_elixir_if_missing() {
    if command -v elixir >/dev/null 2>&1; then
        log "elixir already in PATH ($(elixir --version 2>&1 | head -1)), skip"
        return 0
    fi
    log "installing elixir via apt (Ubuntu bundled, ~1.12+)"
    export DEBIAN_FRONTEND=noninteractive
    maybe_sudo apt-get update -qq
    maybe_sudo apt-get install -y --no-install-recommends elixir 2>&1 | tail -3
    log "elixir installed: $(elixir --version 2>&1 | head -1)"
}

# baseline 生成 + 評価 (eli2/eli3 と同じ runner / 同じ出力先 — 共有可能)
run_baseline_seed() {
    local seed="$1"
    local gen_dir="data/eval/generated/${DATASET}.baseline.seed${seed}"
    local eval_dir="data/eval/results/${DATASET}.baseline.seed${seed}"

    if [[ "$SKIP_EXISTING" == "1" && -s "$eval_dir/_summary.json" ]]; then
        log "baseline seed=$seed already evaluated, skip"; return
    fi

    log "baseline seed=$seed: generating to $gen_dir"
    local limit_flag=()
    if [[ -n "${LIMIT:-}" ]]; then
        limit_flag=(--limit "$LIMIT")
    fi
    python3 scripts/eval/run_baseline_elixir.py \
        --input "$PARQUET" \
        --out-dir "$gen_dir" \
        --model "$MODEL_DIR" \
        --quantize "$QUANTIZE" \
        --max-new-tokens "$MAX_NEW_TOKENS" \
        --temperature "$TEMPERATURE" \
        --seed "$seed" \
        "${limit_flag[@]}" \
        $( [[ "$SKIP_EXISTING" == "1" ]] && echo --skip-existing )

    log "baseline seed=$seed: evaluating with elixir_eval.py"
    python3 scripts/eval/elixir_eval.py \
        --generated-dir "$gen_dir" \
        --out-dir "$eval_dir"
}

# yamato (mode, seed) 生成 + 評価 — eli4 runner、出力 dir prefix が eli4 専用
# mode=repair-on のときのみ --max-rounds / --eval-timeout を付与する
# (他 3 mode には無関係な引数のため)。
run_yamato_mode_seed() {
    local mode="$1"
    local seed="$2"
    local gen_dir="data/eval/generated/${DATASET}.yamato_min_elixir4.${mode}.seed${seed}"
    local eval_dir="data/eval/results/${DATASET}.yamato_min_elixir4.${mode}.seed${seed}"

    if [[ "$SKIP_EXISTING" == "1" && -s "$eval_dir/_summary.json" ]]; then
        log "yamato4 mode=$mode seed=$seed already evaluated, skip"; return
    fi

    log "yamato4 mode=$mode seed=$seed: generating to $gen_dir"
    local limit_flag=()
    if [[ -n "${LIMIT:-}" ]]; then
        limit_flag=(--limit "$LIMIT")
    fi
    local repair_flags=()
    if [[ "$mode" == "repair-on" ]]; then
        repair_flags=(--max-rounds "$MAX_ROUNDS" --eval-timeout "$EVAL_TIMEOUT")
    fi
    python3 scripts/eval/run_yamato_min_elixir4.py \
        --input "$PARQUET" \
        --out-dir "$gen_dir" \
        --mode "$mode" \
        --model "$MODEL_DIR" \
        --quantize "$QUANTIZE" \
        --max-new-tokens "$MAX_NEW_TOKENS" \
        --temperature "$TEMPERATURE" \
        --seed "$seed" \
        --min-trace-lines "$MIN_TRACE_LINES" \
        --min-trace-chars "$MIN_TRACE_CHARS" \
        "${repair_flags[@]}" \
        "${limit_flag[@]}" \
        $( [[ "$SKIP_EXISTING" == "1" && "$mode" != "repair-on" ]] && echo --skip-existing )

    log "yamato4 mode=$mode seed=$seed: evaluating with elixir_eval.py"
    python3 scripts/eval/elixir_eval.py \
        --generated-dir "$gen_dir" \
        --out-dir "$eval_dir"
}

# judge: あるモードについて、利用可能な seed 群で 95% CI 判定
judge_mode() {
    local mode="$1"; shift
    local seeds=("$@")

    if [[ ! -f scripts/eval/judge_win_condition_elixir.py ]]; then
        err "scripts/eval/judge_win_condition_elixir.py 未実装"
        return 1
    fi

    local base_summaries=()
    local yam_summaries=()
    for s in "${seeds[@]}"; do
        # repair-on の収支判定は vanilla baseline ではなく koumyou-on を基準にする
        # (repair loop の marginal effect を測るため。設計書 §7-5/§10)。
        # koumyou-on は MODES 内で repair-on より先に走るのでファイルは既に揃っている。
        local bs
        if [[ "$mode" == "repair-on" ]]; then
            bs="data/eval/results/${DATASET}.yamato_min_elixir4.koumyou-on.seed${s}/_summary.json"
        else
            bs="data/eval/results/${DATASET}.baseline.seed${s}/_summary.json"
        fi
        local ys="data/eval/results/${DATASET}.yamato_min_elixir4.${mode}.seed${s}/_summary.json"
        if [[ ! -s "$bs" ]]; then err "missing baseline summary: $bs"; return 1; fi
        if [[ ! -s "$ys" ]]; then err "missing yamato4 summary: $ys"; return 1; fi
        base_summaries+=("$bs")
        yam_summaries+=("$ys")
    done

    local out="baselines/yamato_min_elixir4.${DATASET}.${mode}.seed$(IFS=_; echo "${seeds[*]}").judge.json"
    mkdir -p "$(dirname "$out")"
    log "judge mode=$mode seeds=[${seeds[*]}] -> $out"
    python3 scripts/eval/judge_win_condition_elixir.py \
        --baseline "${base_summaries[@]}" \
        --yamato   "${yam_summaries[@]}" \
        --mode "$mode" \
        --out "$out" || true
}

# --- sub-commands -----------------------------------------------------------

cmd_setup() {
    log "=== setup: elixir CLI, pip, model, dataset ==="

    log "[1/4] elixir CLI (apt)"
    install_elixir_if_missing

    log "[2/4] pip install"
    python3 -m pip install --upgrade pip
    python3 -m pip install -e ".[dev,quantization]"

    log "[3/4] Qwen2.5-Coder-7B-Instruct download -> $MODEL_DIR"
    if [[ ! -d "$MODEL_DIR" || -z "$(ls -A "$MODEL_DIR" 2>/dev/null)" ]]; then
        hf download Qwen/Qwen2.5-Coder-7B-Instruct \
            --local-dir "$MODEL_DIR"
    else
        log "model already present, skip"
    fi

    log "[4/4] ${DATASET} parquet"
    if [[ ! -s "$PARQUET" ]]; then
        python3 -m pip install --quiet "datasets>=2.14"
        mkdir -p "$(dirname "$PARQUET")"
        DATASET="$DATASET" PARQUET="$PARQUET" python3 - <<'PY'
import os
from datasets import load_dataset
dataset = os.environ["DATASET"]
out = os.environ["PARQUET"]
ds = load_dataset("nuprl/MultiPL-E", dataset, split="test")
os.makedirs(os.path.dirname(out), exist_ok=True)
ds.to_parquet(out)
print(f"wrote {out} rows={len(ds)}")
PY
    else
        log "parquet already present, skip"
    fi

    log "setup done."
}

# smoke: koumyou-on mode × seed 0 × N=5 で光明想の発火 (TRACE_VALID / HALT) を確認
cmd_smoke() {
    log "=== smoke: koumyou-on mode × seed 0 × N=5 (光明想の発火確認) ==="
    LIMIT=5 SKIP_EXISTING=0 run_yamato_mode_seed koumyou-on 0
    local gen_dir="data/eval/generated/${DATASET}.yamato_min_elixir4.koumyou-on.seed0"
    log "smoke complete. trace_info の status 分布:"
    GEN_DIR="$gen_dir" python3 - <<'PY'
import json, os, glob
from collections import Counter
gen_dir = os.environ["GEN_DIR"]
files = sorted(glob.glob(gen_dir + "/*.json"))
print(f"  files: {len(files)}")
statuses = Counter()
halt_count = 0
for f in files:
    d = json.load(open(f, encoding="utf-8"))
    ti = d.get("trace_info") or {}
    statuses[ti.get("status", "-")] += 1
    if d.get("halted_early"):
        halt_count += 1
for s, n in statuses.most_common():
    print(f"  trace_status: {s:24s} = {n}")
print(f"  halted_early: {halt_count}/{len(files)}")
print(f"  inspect samples: head -200 {gen_dir}/*.json | head -50")
PY
    log "smoke done. results at data/eval/results/${DATASET}.yamato_min_elixir4.koumyou-on.seed0/_summary.json"
}

# smoke_repair: repair-on mode × seed 0 × N=20, max-rounds=2 で還降 loop の発火確認
# (DoD-C-3: retry 発火、ashibune.jsonl / _repair_summary.json の書き出し確認)
cmd_smoke_repair() {
    log "=== smoke_repair: repair-on mode × seed 0 × N=20 × max-rounds=2 (還降発火確認) ==="
    LIMIT=20 SKIP_EXISTING=0 MAX_ROUNDS=2 run_yamato_mode_seed repair-on 0
    local gen_dir="data/eval/generated/${DATASET}.yamato_min_elixir4.repair-on.seed0"

    if [[ ! -s "$gen_dir/ashibune.jsonl" ]]; then
        err "ashibune.jsonl が書かれていません: $gen_dir/ashibune.jsonl"
        return 1
    fi
    if [[ ! -s "$gen_dir/_repair_summary.json" ]]; then
        err "_repair_summary.json が書かれていません: $gen_dir/_repair_summary.json"
        return 1
    fi

    log "ashibune.jsonl: $(wc -l < "$gen_dir/ashibune.jsonl") attempt(s) recorded"
    log "_repair_summary.json:"
    cat "$gen_dir/_repair_summary.json"
    log "smoke_repair done."
}

# dod_round0: DoD-C-1 — repair-on --max-rounds 0 の round_0/ 出力と eli3 koumyou-on の
# 出力が raw_completion 全一致であることを確認する (round 0 byte-identity、統制条件)
cmd_dod_round0() {
    local seed="${1:-0}"
    log "=== dod_round0: repair-on(round0) vs eli3 koumyou-on の raw_completion 全一致確認 ==="

    LIMIT=20 SKIP_EXISTING=0 MAX_ROUNDS=0 run_yamato_mode_seed repair-on "$seed"

    local eli3_dir="data/eval/generated/${DATASET}.yamato_min_elixir3.koumyou-on.seed${seed}"
    if [[ ! -d "$eli3_dir" ]]; then
        log "eli3 koumyou-on 出力が無いので同条件で生成する: $eli3_dir"
        LIMIT=20 SKIP_EXISTING=0 python3 scripts/eval/run_yamato_min_elixir3.py \
            --input "$PARQUET" \
            --out-dir "$eli3_dir" \
            --mode koumyou-on \
            --model "$MODEL_DIR" \
            --quantize "$QUANTIZE" \
            --max-new-tokens "$MAX_NEW_TOKENS" \
            --temperature "$TEMPERATURE" \
            --seed "$seed" \
            --min-trace-lines "$MIN_TRACE_LINES" \
            --min-trace-chars "$MIN_TRACE_CHARS" \
            --limit 20
    fi

    python3 scripts/eval/diff_raw_completions.py \
        --dir-a "data/eval/generated/${DATASET}.yamato_min_elixir4.repair-on.seed${seed}/round_0" \
        --dir-b "$eli3_dir"
    log "dod_round0 done (exit code = diff 有無)."
}

# dod_regression: DoD-C-2 — 既存 3 mode の出力 (--limit 5) が eli3 と一致することを確認
cmd_dod_regression() {
    local seed="${1:-0}"
    log "=== dod_regression: 既存 3 mode (--limit 5) の raw_completion が eli3 と一致するか ==="
    local mode
    for mode in "firewall-off" "firewall-on" "koumyou-on"; do
        LIMIT=5 SKIP_EXISTING=0 run_yamato_mode_seed "$mode" "$seed"
        local eli3_dir="data/eval/generated/${DATASET}.yamato_min_elixir3.${mode}.seed${seed}"
        if [[ ! -d "$eli3_dir" ]]; then
            log "eli3 $mode 出力が無いので同条件で生成する: $eli3_dir"
            LIMIT=5 SKIP_EXISTING=0 python3 scripts/eval/run_yamato_min_elixir3.py \
                --input "$PARQUET" \
                --out-dir "$eli3_dir" \
                --mode "$mode" \
                --model "$MODEL_DIR" \
                --quantize "$QUANTIZE" \
                --max-new-tokens "$MAX_NEW_TOKENS" \
                --temperature "$TEMPERATURE" \
                --seed "$seed" \
                --min-trace-lines "$MIN_TRACE_LINES" \
                --min-trace-chars "$MIN_TRACE_CHARS" \
                --limit 5
        fi
        python3 scripts/eval/diff_raw_completions.py \
            --dir-a "data/eval/generated/${DATASET}.yamato_min_elixir4.${mode}.seed${seed}" \
            --dir-b "$eli3_dir"
    done
    log "dod_regression done (exit code = diff 有無)."
}

cmd_baseline() {
    local seed="${1:?seed required, e.g. 0}"
    log "=== baseline: seed $seed × 全問 ==="
    run_baseline_seed "$seed"
}

cmd_pilot() {
    local seed="${1:-0}"
    log "=== pilot: 4 mode × seed $seed (then judge against saved baseline) ==="
    for mode in "${MODES[@]}"; do
        run_yamato_mode_seed "$mode" "$seed"
    done
    for mode in "${MODES[@]}"; do
        judge_mode "$mode" "$seed"
    done
    log "pilot done. judge JSONs at baselines/yamato_min_elixir4.*.seed${seed}.judge.json"
}

cmd_ci() {
    log "=== ci: baseline + 4 mode × seed 1/2 を追加で回し、3 seed で 95% CI 判定 ==="
    for seed in 1 2; do
        run_baseline_seed "$seed"
        for mode in "${MODES[@]}"; do
            run_yamato_mode_seed "$mode" "$seed"
        done
    done
    for mode in "${MODES[@]}"; do
        judge_mode "$mode" 0 1 2
    done
    log "ci done. 3-seed judge JSONs at baselines/yamato_min_elixir4.*.seed0_1_2.judge.json"
}

cmd_run() {
    local mode="${1:?mode required}"
    local seed="${2:?seed required}"
    case "$mode" in
        baseline) run_baseline_seed "$seed" ;;
        firewall-on|firewall-off|koumyou-on|repair-on) run_yamato_mode_seed "$mode" "$seed" ;;
        *) err "unknown mode: $mode"; exit 1 ;;
    esac
}

usage() {
    sed -n '2,45p' "$0"
    exit 1
}

# --- entry ------------------------------------------------------------------

cmd="${1:-}"; shift || true
case "$cmd" in
    setup)          cmd_setup ;;
    smoke)          cmd_smoke ;;
    smoke_repair)   cmd_smoke_repair ;;
    dod_round0)     cmd_dod_round0 "$@" ;;
    dod_regression) cmd_dod_regression "$@" ;;
    baseline)       cmd_baseline "$@" ;;
    pilot)          cmd_pilot "$@" ;;
    ci)             cmd_ci ;;
    run)            cmd_run "$@" ;;
    judge)          judge_mode "$@" ;;
    ""|-h|--help)   usage ;;
    *) err "unknown subcommand: $cmd"; usage ;;
esac
