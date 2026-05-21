#!/usr/bin/env bash
# RunPod 上での Yamato Elixir target (src_min_eli2) ベンチ実行 runbook
#
# Go 版 (scripts/runpod_bench.sh) の Elixir target 版。LM は同じ Qwen2.5-Coder-7B、
# target 言語が Elixir、L5 評価器が `elixir <file>` subprocess に変わる。
#
# 設計方針 (Go 版と同じ):
#   - 全フェーズ idempotent: 出力 _summary.json が既にあればスキップ
#   - フェーズ単位で sub-command 化、smoke → pilot → 3seed の順
#   - judge 用 baseline は同 pod で取り直す
#
# 想定フロー (RunPod A5000 24GB pod に SSH 接続後):
#   bash scripts/runpod_bench_eli2.sh setup            # 約 10-15 分 (model DL 14GB が支配的)
#   bash scripts/runpod_bench_eli2.sh smoke            # 約 2 分    (vanilla × 5 問)
#   bash scripts/runpod_bench_eli2.sh baseline 0       # 約 15-25 分 (1 seed × 161 問)
#   bash scripts/runpod_bench_eli2.sh pilot 0          # 約 1.5-2h   (4 mode × seed 0 + judge)
#   bash scripts/runpod_bench_eli2.sh ci               # 約 3-4h     (4 mode × seed 1+2 を追加)
#
# 環境変数:
#   REPO_ROOT          リポジトリルート (default: スクリプトの 1 つ上)
#   MODEL_DIR          Qwen モデルディレクトリ (default: $REPO_ROOT/models/Qwen2.5-Coder-7B-Instruct)
#   QUANTIZE           "4bit" | "8bit" | "none" (default: 4bit)
#   MAX_NEW_TOKENS     (default: 256)
#   TEMPERATURE        (default: 0.2)
#   BIAS_VALUE         言霊 v2 のソフトバイアス加算量 (default: 2.0)
#   DATASET            MultiPL-E subset (default: humaneval-elixir)。mbpp-elixir (397 問) も可
#   SKIP_EXISTING      "1" で既出力を skip (default: 1)
#   LIMIT              生成上限 (smoke 以外では未設定 = 全問)
#
# Go 版との差分:
#   - Go toolchain install / symbol_oracle daemon build / goimports install を削除
#   - 代わりに elixir CLI を apt install (subprocess `elixir <file>` 評価のため)
#   - runner = run_baseline_elixir.py / run_yamato_min_elixir.py
#   - eval = elixir_eval.py
#
# 終了コード:
#   0 = フェーズ正常終了 (judge は Win Condition 達成時のみ 0)
#   1 = フェーズ途中で失敗 / Win Condition 未達

set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$REPO_ROOT"

MODEL_DIR="${MODEL_DIR:-$REPO_ROOT/models/Qwen2.5-Coder-7B-Instruct}"
QUANTIZE="${QUANTIZE:-4bit}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-256}"
TEMPERATURE="${TEMPERATURE:-0.2}"
BIAS_VALUE="${BIAS_VALUE:-2.0}"
SKIP_EXISTING="${SKIP_EXISTING:-1}"
DATASET="${DATASET:-humaneval-elixir}"

PARQUET="$REPO_ROOT/data/raw/multipl_e/${DATASET}/test-00000-of-00001.parquet"
MODES=("full" "no-kotodama" "no-firewall" "vanilla")

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

# Elixir CLI を install (apt の bundled version で十分、Mix project は不要)
# `elixir <file>` と `elixir -e "..."` だけ使うため最低限の install で OK。
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

# baseline 生成 + 評価
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

# yamato (mode, seed) 生成 + 評価
run_yamato_mode_seed() {
    local mode="$1"
    local seed="$2"
    local gen_dir="data/eval/generated/${DATASET}.yamato_min_elixir.${mode}.seed${seed}"
    local eval_dir="data/eval/results/${DATASET}.yamato_min_elixir.${mode}.seed${seed}"

    if [[ "$SKIP_EXISTING" == "1" && -s "$eval_dir/_summary.json" ]]; then
        log "yamato mode=$mode seed=$seed already evaluated, skip"; return
    fi

    log "yamato mode=$mode seed=$seed: generating to $gen_dir"
    local limit_flag=()
    if [[ -n "${LIMIT:-}" ]]; then
        limit_flag=(--limit "$LIMIT")
    fi
    python3 scripts/eval/run_yamato_min_elixir.py \
        --input "$PARQUET" \
        --out-dir "$gen_dir" \
        --mode "$mode" \
        --model "$MODEL_DIR" \
        --quantize "$QUANTIZE" \
        --max-new-tokens "$MAX_NEW_TOKENS" \
        --temperature "$TEMPERATURE" \
        --bias-value "$BIAS_VALUE" \
        --seed "$seed" \
        "${limit_flag[@]}" \
        $( [[ "$SKIP_EXISTING" == "1" ]] && echo --skip-existing )

    log "yamato mode=$mode seed=$seed: evaluating with elixir_eval.py"
    python3 scripts/eval/elixir_eval.py \
        --generated-dir "$gen_dir" \
        --out-dir "$eval_dir"
}

# judge: あるモードについて、利用可能な seed 群で 95% CI 判定
# 注: scripts/eval/judge_win_condition_elixir.py は未実装 (TBD)。
#     Go 版 (judge_win_condition_go.py) を移植する必要あり。
judge_mode() {
    local mode="$1"; shift
    local seeds=("$@")

    if [[ ! -f scripts/eval/judge_win_condition_elixir.py ]]; then
        err "scripts/eval/judge_win_condition_elixir.py 未実装"
        err "  → scripts/eval/judge_win_condition_go.py を移植する必要あり (TBD)"
        return 1
    fi

    local base_summaries=()
    local yam_summaries=()
    for s in "${seeds[@]}"; do
        local bs="data/eval/results/${DATASET}.baseline.seed${s}/_summary.json"
        local ys="data/eval/results/${DATASET}.yamato_min_elixir.${mode}.seed${s}/_summary.json"
        if [[ ! -s "$bs" ]]; then err "missing baseline summary: $bs"; return 1; fi
        if [[ ! -s "$ys" ]]; then err "missing yamato summary: $ys"; return 1; fi
        base_summaries+=("$bs")
        yam_summaries+=("$ys")
    done

    local out="baselines/yamato_min_elixir.${DATASET}.${mode}.seed$(IFS=_; echo "${seeds[*]}").judge.json"
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
    # huggingface_hub >= 1.x では `hf` コマンドが組み込み、`[cli]` extra は廃止済

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

cmd_smoke() {
    log "=== smoke: vanilla mode × seed 0 × N=5 (env / pipeline 動作確認) ==="
    LIMIT=5 SKIP_EXISTING=0 run_yamato_mode_seed vanilla 0
    log "smoke complete. inspect data/eval/results/${DATASET}.yamato_min_elixir.vanilla.seed0/_summary.json"
}

# Firewall byte-identical 検証 (Go 版 cmd_smoke_fix_d 相当)
# vanilla / no-kotodama × seed 0 × N=10 を回し、byte-identical 率を見る。
# 期待: vanilla ↔ no-kotodama : 10/10 完全一致 (Firewall pathway が生成に副作用なし)
cmd_smoke_fix_d() {
    local seed="${1:-0}"
    log "=== smoke-fix-d: vanilla + no-kotodama × seed $seed × N=10 (Firewall byte-identical 検証) ==="
    LIMIT=10 SKIP_EXISTING=0 run_yamato_mode_seed vanilla "$seed"
    LIMIT=10 SKIP_EXISTING=0 run_yamato_mode_seed no-kotodama "$seed"

    if [[ ! -f scripts/eval/diff_smoke_outputs.py ]]; then
        err "scripts/eval/diff_smoke_outputs.py 不在"
        return 1
    fi
    log "comparing outputs (vanilla vs no-kotodama)..."
    python3 scripts/eval/diff_smoke_outputs.py \
        --vanilla     "data/eval/generated/${DATASET}.yamato_min_elixir.vanilla.seed${seed}" \
        --no-kotodama "data/eval/generated/${DATASET}.yamato_min_elixir.no-kotodama.seed${seed}"
}

cmd_baseline() {
    local seed="${1:?seed required, e.g. 0}"
    log "=== baseline: seed $seed × 全問 ==="
    run_baseline_seed "$seed"
}

cmd_pilot() {
    local seed="${1:-0}"
    log "=== pilot: 4 ablation mode × seed $seed (then judge against saved baseline) ==="
    for mode in "${MODES[@]}"; do
        run_yamato_mode_seed "$mode" "$seed"
    done
    for mode in "${MODES[@]}"; do
        judge_mode "$mode" "$seed"
    done
    log "pilot done. judge JSONs at baselines/yamato_min_elixir.*.seed${seed}.judge.json"
}

cmd_ci() {
    log "=== ci: seeds 1 and 2 を追加で回し、3 seed で 95% CI 判定 ==="
    for seed in 1 2; do
        for mode in "${MODES[@]}"; do
            run_yamato_mode_seed "$mode" "$seed"
        done
    done
    for mode in "${MODES[@]}"; do
        judge_mode "$mode" 0 1 2
    done
    log "ci done. 3-seed judge JSONs at baselines/yamato_min_elixir.*.seed0_1_2.judge.json"
}

cmd_run() {
    local mode="${1:?mode required}"
    local seed="${2:?seed required}"
    case "$mode" in
        baseline) run_baseline_seed "$seed" ;;
        full|no-kotodama|no-firewall|vanilla) run_yamato_mode_seed "$mode" "$seed" ;;
        *) err "unknown mode: $mode"; exit 1 ;;
    esac
}

usage() {
    sed -n '2,40p' "$0"
    exit 1
}

# --- entry ------------------------------------------------------------------

cmd="${1:-}"; shift || true
case "$cmd" in
    setup)        cmd_setup ;;
    smoke)        cmd_smoke ;;
    smoke-fix-d)  cmd_smoke_fix_d "$@" ;;
    baseline)     cmd_baseline "$@" ;;
    pilot)        cmd_pilot "$@" ;;
    ci)           cmd_ci ;;
    run)          cmd_run "$@" ;;
    judge)        judge_mode "$@" ;;
    ""|-h|--help) usage ;;
    *) err "unknown subcommand: $cmd"; usage ;;
esac
