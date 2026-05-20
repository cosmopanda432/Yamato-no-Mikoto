#!/usr/bin/env bash
# RunPod 上での Yamato Go 版ベンチ実行 runbook
#
# 設計方針:
#   - 全フェーズ idempotent: 出力 _summary.json が既にあればスキップ
#   - フェーズ単位で sub-command 化、smoke → pilot → 3seed の順で確認しながら進む
#   - judge 用 baseline は A6000 上で同じ条件で取り直す (M0 は RTX 3060 で取得、ハード違うため)
#
# 想定フロー (RunPod pod に SSH 接続後):
#   # 0. ローカルから Go tarball をアップロード (Windows ローカルから)
#   #    scp /c/Users/mimat/Downloads/go1.26.3.linux-amd64.tar.gz root@<pod>:/root/
#   export GO_TARBALL=/root/go1.26.3.linux-amd64.tar.gz
#
#   bash scripts/runpod_bench.sh setup            # 約 15 分 (model DL が支配的)
#   bash scripts/runpod_bench.sh smoke            # 約 2 分    (vanilla × 5 問)
#   bash scripts/runpod_bench.sh baseline 0       # 約 15-25 分 (1 seed × 154 問 on A6000)
#   bash scripts/runpod_bench.sh pilot 0          # 約 1.5-2h   (4 mode × seed 0 × 154 問 + judge full)
#   bash scripts/runpod_bench.sh ci               # 約 3-4h     (4 mode × seed 1+2 を追加 + judge full)
#
# 環境変数:
#   REPO_ROOT          リポジトリルート (default: スクリプトの 1 つ上)
#   MODEL_DIR          Qwen モデルディレクトリ (default: $REPO_ROOT/models/Qwen2.5-Coder-7B-Instruct)
#   QUANTIZE           "4bit" | "8bit" | "none" (default: 4bit)
#   MAX_NEW_TOKENS     (default: 256)
#   TEMPERATURE        (default: 0.2)
#   BIAS_VALUE         言霊 v2 のソフトバイアス加算量 (default: 2.0、docs/roadmap_min_go.md 推奨)
#   GO_TARBALL         Go ツールチェーン tarball (go1.26.3.linux-amd64.tar.gz)
#                      未設定なら /root/go1.26.3.linux-amd64.tar.gz をデフォルトで探す
#   GO_BIN             go コマンドパス (default: 自動検出 → /usr/local/go/bin/go fallback)
#   SKIP_EXISTING      "1" で既出力を skip (default: 1)
#   LIMIT              生成上限 (smoke 以外では未設定 = 全問)
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

ORACLE_BIN="$REPO_ROOT/src_min_go/go_tools/bin/symbol_oracle"
PARQUET="$REPO_ROOT/data/raw/multipl_e/humaneval-go/test-00000-of-00001.parquet"
MODES=("full" "no-kotodama" "no-firewall" "vanilla")

# --- helpers ----------------------------------------------------------------

log() { printf '[%s] %s\n' "$(date +'%H:%M:%S')" "$*"; }
err() { printf '[%s] ERROR: %s\n' "$(date +'%H:%M:%S')" "$*" >&2; }

resolve_go_bin() {
    if [[ -n "${GO_BIN:-}" && -x "$GO_BIN" ]]; then
        echo "$GO_BIN"; return
    fi
    if command -v go >/dev/null 2>&1; then
        command -v go; return
    fi
    if [[ -x /usr/local/go/bin/go ]]; then
        echo /usr/local/go/bin/go; return
    fi
    err "go not found in PATH and /usr/local/go/bin/go absent."
    err "  → upload go1.26.3.linux-amd64.tar.gz to the pod (e.g. /root/) and re-run 'setup',"
    err "    or set GO_BIN to an existing go binary."
    exit 1
}

# Go ツールチェーンを /usr/local に展開 (既にあれば no-op)
install_go_if_missing() {
    if [[ -x /usr/local/go/bin/go ]] || command -v go >/dev/null 2>&1; then
        log "go already installed, skip"
        return 0
    fi
    local tarball="${GO_TARBALL:-/root/go1.26.3.linux-amd64.tar.gz}"
    if [[ ! -f "$tarball" ]]; then
        err "Go tarball not found at $tarball"
        err "  → upload from local: scp /c/Users/mimat/Downloads/go1.26.3.linux-amd64.tar.gz root@<pod>:/root/"
        err "  → then export GO_TARBALL=/root/go1.26.3.linux-amd64.tar.gz and re-run setup"
        exit 1
    fi
    log "extracting $tarball -> /usr/local/go"
    rm -rf /usr/local/go
    tar -C /usr/local -xzf "$tarball"
    if [[ ! -x /usr/local/go/bin/go ]]; then
        err "go binary not present after extract; tarball may be corrupted"
        exit 1
    fi
    log "go $( /usr/local/go/bin/go version ) installed"
}

# baseline 生成 + 評価
run_baseline_seed() {
    local seed="$1"
    local gen_dir="data/eval/generated/humaneval-go.baseline.seed${seed}"
    local eval_dir="data/eval/results/humaneval-go.baseline.seed${seed}"

    if [[ "$SKIP_EXISTING" == "1" && -s "$eval_dir/_summary.json" ]]; then
        log "baseline seed=$seed already evaluated, skip"; return
    fi

    log "baseline seed=$seed: generating to $gen_dir"
    python3 scripts/eval/run_baseline_go.py \
        --input "$PARQUET" \
        --out-dir "$gen_dir" \
        --model "$MODEL_DIR" \
        --quantize "$QUANTIZE" \
        --max-new-tokens "$MAX_NEW_TOKENS" \
        --temperature "$TEMPERATURE" \
        --seed "$seed" \
        $( [[ "$SKIP_EXISTING" == "1" ]] && echo --skip-existing )

    log "baseline seed=$seed: evaluating with go_eval.py"
    python3 scripts/eval/go_eval.py \
        --generated-dir "$gen_dir" \
        --out-dir "$eval_dir" \
        --go-bin "$(resolve_go_bin)"
}

# yamato (mode, seed) 生成 + 評価
run_yamato_mode_seed() {
    local mode="$1"
    local seed="$2"
    local gen_dir="data/eval/generated/humaneval-go.yamato_min_go.${mode}.seed${seed}"
    local eval_dir="data/eval/results/humaneval-go.yamato_min_go.${mode}.seed${seed}"

    if [[ "$SKIP_EXISTING" == "1" && -s "$eval_dir/_summary.json" ]]; then
        log "yamato mode=$mode seed=$seed already evaluated, skip"; return
    fi

    log "yamato mode=$mode seed=$seed: generating to $gen_dir"
    local limit_flag=()
    if [[ -n "${LIMIT:-}" ]]; then
        limit_flag=(--limit "$LIMIT")
    fi
    python3 scripts/eval/run_yamato_min_go.py \
        --input "$PARQUET" \
        --out-dir "$gen_dir" \
        --mode "$mode" \
        --model "$MODEL_DIR" \
        --quantize "$QUANTIZE" \
        --oracle-bin "$ORACLE_BIN" \
        --max-new-tokens "$MAX_NEW_TOKENS" \
        --temperature "$TEMPERATURE" \
        --bias-value "$BIAS_VALUE" \
        --seed "$seed" \
        "${limit_flag[@]}" \
        $( [[ "$SKIP_EXISTING" == "1" ]] && echo --skip-existing )

    log "yamato mode=$mode seed=$seed: evaluating with go_eval.py"
    python3 scripts/eval/go_eval.py \
        --generated-dir "$gen_dir" \
        --out-dir "$eval_dir" \
        --go-bin "$(resolve_go_bin)"
}

# judge: あるモードについて、利用可能な seed 群で 95% CI 判定
judge_mode() {
    local mode="$1"; shift
    local seeds=("$@")

    local base_summaries=()
    local yam_summaries=()
    for s in "${seeds[@]}"; do
        local bs="data/eval/results/humaneval-go.baseline.seed${s}/_summary.json"
        local ys="data/eval/results/humaneval-go.yamato_min_go.${mode}.seed${s}/_summary.json"
        if [[ ! -s "$bs" ]]; then err "missing baseline summary: $bs"; return 1; fi
        if [[ ! -s "$ys" ]]; then err "missing yamato summary: $ys"; return 1; fi
        base_summaries+=("$bs")
        yam_summaries+=("$ys")
    done

    local out="baselines/yamato_min_go.${mode}.seed$(IFS=_; echo "${seeds[*]}").judge.json"
    mkdir -p "$(dirname "$out")"
    log "judge mode=$mode seeds=[${seeds[*]}] -> $out"
    python3 scripts/eval/judge_win_condition_go.py \
        --baseline "${base_summaries[@]}" \
        --yamato   "${yam_summaries[@]}" \
        --mode "$mode" \
        --out "$out" || true
}

# --- sub-commands -----------------------------------------------------------

cmd_setup() {
    log "=== setup: Go, dependencies, model, oracle daemon, dataset ==="

    log "[0/4] Go toolchain"
    install_go_if_missing

    log "[1/4] pip install"
    python3 -m pip install --upgrade pip
    python3 -m pip install -e ".[dev,quantization]"
    # huggingface_hub >= 1.x では `hf` コマンドが組み込み、`[cli]` extra は廃止済

    log "[2/4] Qwen2.5-Coder-7B-Instruct download -> $MODEL_DIR"
    if [[ ! -d "$MODEL_DIR" || -z "$(ls -A "$MODEL_DIR" 2>/dev/null)" ]]; then
        # 旧 `huggingface-cli download` は v1.x で stub 化 (deprecated)、`hf download` を使う
        hf download Qwen/Qwen2.5-Coder-7B-Instruct \
            --local-dir "$MODEL_DIR"
    else
        log "model already present, skip"
    fi

    log "[3/4] humaneval-go parquet"
    if [[ ! -s "$PARQUET" ]]; then
        # parquet 取得用に datasets が必要 (pyproject の dep には入れてない)
        python3 -m pip install --quiet "datasets>=2.14"
        mkdir -p "$(dirname "$PARQUET")"
        python3 - <<'PY'
from datasets import load_dataset
import os
ds = load_dataset("nuprl/MultiPL-E", "humaneval-go", split="test")
out = "data/raw/multipl_e/humaneval-go/test-00000-of-00001.parquet"
os.makedirs(os.path.dirname(out), exist_ok=True)
ds.to_parquet(out)
print("wrote", out, "rows=", len(ds))
PY
    else
        log "parquet already present, skip"
    fi

    log "[4/4] symbol_oracle daemon (go build)"
    if [[ ! -x "$ORACLE_BIN" ]]; then
        mkdir -p "$(dirname "$ORACLE_BIN")"
        local go_bin; go_bin="$(resolve_go_bin)"
        (cd src_min_go/go_tools && "$go_bin" build -o bin/symbol_oracle ./cmd/symbol_oracle)
        log "built $ORACLE_BIN"
    else
        log "oracle daemon already built, skip"
    fi

    log "setup done."
}

cmd_smoke() {
    log "=== smoke: vanilla mode × seed 0 × N=5 (env / pipeline 動作確認) ==="
    LIMIT=5 SKIP_EXISTING=0 run_yamato_mode_seed vanilla 0
    log "smoke complete. inspect data/eval/results/humaneval-go.yamato_min_go.vanilla.seed0/_summary.json"
}

cmd_baseline() {
    local seed="${1:?seed required, e.g. 0}"
    log "=== baseline: seed $seed × 154 問 ==="
    run_baseline_seed "$seed"
}

cmd_pilot() {
    local seed="${1:-0}"
    log "=== pilot: 4 mode × seed $seed × 154 問 (baseline + 4 ablation, then judge full) ==="
    run_baseline_seed "$seed"
    for mode in "${MODES[@]}"; do
        run_yamato_mode_seed "$mode" "$seed"
    done
    for mode in "${MODES[@]}"; do
        judge_mode "$mode" "$seed"
    done
    log "pilot done. judge JSONs at baselines/yamato_min_go.*.seed${seed}.judge.json"
}

cmd_ci() {
    log "=== ci: seeds 1 and 2 を追加で回し、3 seed で 95% CI 判定 ==="
    for seed in 1 2; do
        run_baseline_seed "$seed"
        for mode in "${MODES[@]}"; do
            run_yamato_mode_seed "$mode" "$seed"
        done
    done
    for mode in "${MODES[@]}"; do
        judge_mode "$mode" 0 1 2
    done
    log "ci done. 3-seed judge JSONs at baselines/yamato_min_go.*.seed0_1_2.judge.json"
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
    sed -n '2,30p' "$0"
    exit 1
}

# --- entry ------------------------------------------------------------------

cmd="${1:-}"; shift || true
case "$cmd" in
    setup)    cmd_setup ;;
    smoke)    cmd_smoke ;;
    baseline) cmd_baseline "$@" ;;
    pilot)    cmd_pilot "$@" ;;
    ci)       cmd_ci ;;
    run)      cmd_run "$@" ;;
    judge)    judge_mode "$@" ;;
    ""|-h|--help) usage ;;
    *) err "unknown subcommand: $cmd"; usage ;;
esac
