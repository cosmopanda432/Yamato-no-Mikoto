#!/usr/bin/env bash
# ⛔ 【中止 2026-05-21】本スクリプトは src_min_elixir/ (BEAM 完結 Mix project) 用で、
# その路線は中止 (docs/旧ドキュメント/roadmap_min_elixir.md 参照)。
# 新計画 src_min_eli2 (Python + Qwen2.5-Coder + Elixir target) では
# scripts/runpod_bench_eli2.sh を使うこと。本スクリプトは将来 Bumblebee が
# Qwen3 MoE / Qwen2 をサポートした時に再利用可能なため保存。
#
# ↓ 旧コンテンツ (中止時点のスナップショット) ↓
#
# RunPod 上での Yamato Elixir 版ベンチ実行 runbook
#
# Go 版 (scripts/runpod_bench.sh) と同じ設計方針:
#   - 全フェーズ idempotent: 既出力 / 既 install は skip
#   - フェーズ単位で sub-command 化、setup → smoke → phase1 → (Step 5 実装) → phase2 の順
#   - 検証順序は docs/roadmap_min_elixir.md Step 8 (Phase 1 → Step 5 → Phase 2) に従う
#
# 想定フロー (RunPod A6000 48GB pod に SSH 接続後):
#   bash scripts/runpod_bench_elixir.sh setup       # 約 20-30 分 (Erlang source build + 30B DL が支配的)
#   bash scripts/runpod_bench_elixir.sh mix-test    # 即時。Step 3/4/6 の 62 tests を確認
#   bash scripts/runpod_bench_elixir.sh smoke       # 1 問で pipeline 動作確認 (Step 2 実装後)
#   bash scripts/runpod_bench_elixir.sh phase1 0    # Firewall byte-identical 検証 (bare vs firewall-only、Step 1+2 後)
#   bash scripts/runpod_bench_elixir.sh phase2 0    # 4 mode ablation (Step 5 完了後)
#
# 環境変数:
#   REPO_ROOT       リポジトリルート (default: スクリプトの 1 つ上)
#   ELIXIR_PROJECT  src_min_elixir のパス (default: $REPO_ROOT/src_min_elixir)
#   ELIXIR_VERSION  (default: 1.18.4-otp-27、user 検証済)
#   ERLANG_VERSION  (default: 27.3.4.11、user 検証済)
#   ASDF_DIR        asdf install dir (default: $HOME/.asdf)
#   MODEL_DIR       Qwen3 モデルディレクトリ (default: $REPO_ROOT/models/Qwen3-Coder-30B-A3B-Instruct)
#   HF_REPO         HuggingFace repo (default: Qwen/Qwen3-Coder-30B-A3B-Instruct)
#   QUANTIZE        "int8" | "none" (default: int8、Bumblebee は int4/GGUF 未対応 ([Issue #249/#413] Open))
#   DATASET         MultiPL-E subset (default: humaneval-elixir)。mbpp-elixir も可
#   MAX_NEW_TOKENS  (default: 256)
#   TEMPERATURE     (default: 0.2)
#   SEED            (default: 0)
#   LIMIT           smoke の問題数上限 (default: 1)
#   SKIP_EXISTING   "1" で既出力を skip (default: 1)
#
# 終了コード:
#   0 = フェーズ正常終了
#   1 = フェーズ途中で失敗 / 必要な runner スクリプト未実装

set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$REPO_ROOT"

ELIXIR_PROJECT="${ELIXIR_PROJECT:-$REPO_ROOT/src_min_elixir}"
ELIXIR_VERSION="${ELIXIR_VERSION:-1.18.4-otp-27}"
ERLANG_VERSION="${ERLANG_VERSION:-27.3.4.11}"
ASDF_DIR="${ASDF_DIR:-$HOME/.asdf}"

MODEL_DIR="${MODEL_DIR:-$REPO_ROOT/models/Qwen3-Coder-30B-A3B-Instruct}"
HF_REPO="${HF_REPO:-Qwen/Qwen3-Coder-30B-A3B-Instruct}"
QUANTIZE="${QUANTIZE:-int8}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-256}"
TEMPERATURE="${TEMPERATURE:-0.2}"
SEED="${SEED:-0}"
SKIP_EXISTING="${SKIP_EXISTING:-1}"
DATASET="${DATASET:-humaneval-elixir}"
LIMIT="${LIMIT:-1}"

PARQUET="$REPO_ROOT/data/raw/multipl_e/${DATASET}/test-00000-of-00001.parquet"

# Phase 1 (Step 5 着手前): Firewall pathway byte-identical 検証用 2 mode
PHASE1_MODES=("bare" "firewall-only")
# Phase 2 (Step 5 完了後): 4 mode ablation
PHASE2_MODES=("bare" "firewall-only" "l5-enhanced-no-fw" "full")

# --- helpers ----------------------------------------------------------------

log() { printf '[%s] %s\n' "$(date +'%H:%M:%S')" "$*"; }
err() { printf '[%s] ERROR: %s\n' "$(date +'%H:%M:%S')" "$*" >&2; }

# sudo が要らない (root) なら no-op、それ以外なら sudo を付ける
maybe_sudo() {
    if [[ "$EUID" -eq 0 ]] || ! command -v sudo >/dev/null 2>&1; then
        "$@"
    else
        sudo "$@"
    fi
}

# asdf を current shell に source して PATH に通す
source_asdf() {
    if [[ -f "$ASDF_DIR/asdf.sh" ]]; then
        # shellcheck disable=SC1091
        . "$ASDF_DIR/asdf.sh"
    fi
    export PATH="$ASDF_DIR/shims:$ASDF_DIR/bin:$PATH"
}

# --- install steps ----------------------------------------------------------

# Erlang/OTP ソースビルドに最低限必要な apt パッケージを入れる
install_build_deps() {
    if command -v elixir >/dev/null 2>&1; then
        log "elixir already in PATH, skip apt deps"
        return 0
    fi
    log "installing build dependencies for Erlang/OTP source build"
    export DEBIAN_FRONTEND=noninteractive
    maybe_sudo apt-get update -qq
    # 軽量セット: GUI 系 (wx / observer / debugger) は build 時に除外するので不要
    maybe_sudo apt-get install -y --no-install-recommends \
        build-essential autoconf m4 \
        libncurses-dev libssl-dev libgmp3-dev \
        unixodbc-dev unzip curl git ca-certificates \
        >/dev/null
}

# asdf-vm を $HOME/.asdf に clone (idempotent)
install_asdf_if_missing() {
    if [[ -d "$ASDF_DIR" && -d "$ASDF_DIR/.git" ]]; then
        log "asdf already installed at $ASDF_DIR, skip"
        return 0
    fi
    log "cloning asdf-vm to $ASDF_DIR (branch v0.14.1)"
    git clone --depth=1 --branch v0.14.1 https://github.com/asdf-vm/asdf.git "$ASDF_DIR"
    # bashrc に source 行を idempotent に追加 (interactive shell 用)
    if ! grep -qF 'asdf.sh' "$HOME/.bashrc" 2>/dev/null; then
        printf '\n# yamato Elixir pivot (asdf-vm)\n. %s/asdf.sh\n' "$ASDF_DIR" >> "$HOME/.bashrc"
    fi
}

install_erlang_if_missing() {
    source_asdf
    asdf plugin add erlang 2>/dev/null || true
    if asdf list erlang 2>/dev/null | tr -d ' *' | grep -qx "$ERLANG_VERSION"; then
        log "erlang/OTP $ERLANG_VERSION already installed, skip"
        return 0
    fi
    log "building erlang/OTP $ERLANG_VERSION from source (約 10-15 分)"
    # 軽量化フラグ: GUI / debugger / et / java integration を除外して build 時間と容量を削る。
    # user の Ubuntu 検証時と同じ構成 (memory: project-elixir-pivot-viability)
    export KERL_CONFIGURE_OPTIONS="--without-wx --without-observer --without-debugger --without-et --without-jinterface --disable-hipe"
    asdf install erlang "$ERLANG_VERSION"
}

install_elixir_if_missing() {
    source_asdf
    asdf plugin add elixir 2>/dev/null || true
    if asdf list elixir 2>/dev/null | tr -d ' *' | grep -qx "$ELIXIR_VERSION"; then
        log "elixir $ELIXIR_VERSION already installed, skip"
        return 0
    fi
    log "installing elixir $ELIXIR_VERSION (precompiled binary)"
    asdf install elixir "$ELIXIR_VERSION"
}

install_mix_deps() {
    source_asdf
    if [[ ! -f "$ELIXIR_PROJECT/mix.exs" ]]; then
        err "mix.exs not found at $ELIXIR_PROJECT/mix.exs"
        exit 1
    fi
    log "installing hex + rebar (if missing)"
    (cd "$ELIXIR_PROJECT" && \
        mix local.hex --force --if-missing >/dev/null && \
        mix local.rebar --force --if-missing >/dev/null)
    log "running mix deps.get in $ELIXIR_PROJECT"
    # src_min_elixir/.tool-versions が asdf auto-switch を効かせる
    (cd "$ELIXIR_PROJECT" && mix deps.get)
    log "running mix compile (warning 検出のため)"
    (cd "$ELIXIR_PROJECT" && mix compile --warnings-as-errors) || \
        err "mix compile produced warnings — fix before proceeding"
}

run_mix_test() {
    source_asdf
    if [[ ! -f "$ELIXIR_PROJECT/mix.exs" ]]; then
        err "mix.exs not found, run 'setup' first"
        exit 1
    fi
    log "running mix test in $ELIXIR_PROJECT"
    (cd "$ELIXIR_PROJECT" && mix test)
}

download_model_if_missing() {
    if [[ -d "$MODEL_DIR" && -n "$(ls -A "$MODEL_DIR" 2>/dev/null)" ]]; then
        log "model already present at $MODEL_DIR, skip"
        return 0
    fi
    if ! command -v hf >/dev/null 2>&1; then
        log "huggingface_hub CLI not found, installing"
        python3 -m pip install --quiet --upgrade "huggingface_hub>=0.27"
    fi
    log "downloading $HF_REPO → $MODEL_DIR (約 60 GB at bf16、数分〜10 分)"
    log "  → int8 量子化は Elixir 側 (Axon.Quantization) で適用、download は bf16 のまま"
    mkdir -p "$(dirname "$MODEL_DIR")"
    hf download "$HF_REPO" --local-dir "$MODEL_DIR"
}

download_parquet_if_missing() {
    if [[ -s "$PARQUET" ]]; then
        log "parquet already present at $PARQUET, skip"
        return 0
    fi
    log "downloading MultiPL-E $DATASET → $PARQUET"
    python3 -m pip install --quiet "datasets>=2.14" "pyarrow>=14"
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
}

# --- bench-run helpers ------------------------------------------------------

# baseline (bare Bumblebee) を 1 seed 走らせる
# 注: scripts/eval/run_baseline_elixir.py は Step 2 完了後に書く (現状未実装)
run_baseline_seed() {
    local seed="$1"
    local gen_dir="data/eval/generated/${DATASET}.baseline.seed${seed}"
    local eval_dir="data/eval/results/${DATASET}.baseline.seed${seed}"

    if [[ "$SKIP_EXISTING" == "1" && -s "$eval_dir/_summary.json" ]]; then
        log "baseline seed=$seed already evaluated, skip"; return
    fi

    if [[ ! -f scripts/eval/run_baseline_elixir.py ]]; then
        err "scripts/eval/run_baseline_elixir.py 未実装"
        err "  → Step 2 (L3 GenServer 本実装) 完了後に scripts/eval/run_baseline_go.py を移植"
        return 1
    fi

    log "baseline seed=$seed: generating to $gen_dir"
    python3 scripts/eval/run_baseline_elixir.py \
        --input "$PARQUET" \
        --out-dir "$gen_dir" \
        --model "$MODEL_DIR" \
        --quantize "$QUANTIZE" \
        --max-new-tokens "$MAX_NEW_TOKENS" \
        --temperature "$TEMPERATURE" \
        --seed "$seed" \
        $( [[ -n "${LIMIT:-}" ]] && echo --limit "$LIMIT" ) \
        $( [[ "$SKIP_EXISTING" == "1" ]] && echo --skip-existing )

    log "baseline seed=$seed: evaluating with elixir_eval.py"
    python3 scripts/eval/elixir_eval.py \
        --generated-dir "$gen_dir" \
        --out-dir "$eval_dir"
}

# yamato (mode, seed) を走らせる
# 注: scripts/eval/run_yamato_min_elixir.py は Step 2 完了後に書く
run_yamato_mode_seed() {
    local mode="$1"
    local seed="$2"
    local gen_dir="data/eval/generated/${DATASET}.yamato_min_elixir.${mode}.seed${seed}"
    local eval_dir="data/eval/results/${DATASET}.yamato_min_elixir.${mode}.seed${seed}"

    if [[ "$SKIP_EXISTING" == "1" && -s "$eval_dir/_summary.json" ]]; then
        log "yamato mode=$mode seed=$seed already evaluated, skip"; return
    fi

    if [[ ! -f scripts/eval/run_yamato_min_elixir.py ]]; then
        err "scripts/eval/run_yamato_min_elixir.py 未実装"
        err "  → Step 2 完了後に scripts/eval/run_yamato_min_go.py を移植"
        return 1
    fi

    log "yamato mode=$mode seed=$seed: generating to $gen_dir"
    python3 scripts/eval/run_yamato_min_elixir.py \
        --input "$PARQUET" \
        --out-dir "$gen_dir" \
        --mode "$mode" \
        --model "$MODEL_DIR" \
        --quantize "$QUANTIZE" \
        --max-new-tokens "$MAX_NEW_TOKENS" \
        --temperature "$TEMPERATURE" \
        --seed "$seed" \
        --elixir-project "$ELIXIR_PROJECT" \
        $( [[ -n "${LIMIT:-}" ]] && echo --limit "$LIMIT" ) \
        $( [[ "$SKIP_EXISTING" == "1" ]] && echo --skip-existing )

    log "yamato mode=$mode seed=$seed: evaluating with elixir_eval.py"
    python3 scripts/eval/elixir_eval.py \
        --generated-dir "$gen_dir" \
        --out-dir "$eval_dir"
}

# --- sub-commands -----------------------------------------------------------

cmd_setup() {
    log "=== setup: apt deps, asdf, Erlang, Elixir, mix deps, model, dataset ==="

    log "[1/8] build deps (apt)"
    install_build_deps

    log "[2/8] asdf-vm"
    install_asdf_if_missing

    log "[3/8] Erlang/OTP $ERLANG_VERSION (source build, --without-wx 等で軽量化)"
    install_erlang_if_missing

    log "[4/8] Elixir $ELIXIR_VERSION (precompiled)"
    install_elixir_if_missing

    log "[5/8] mix deps.get + compile (src_min_elixir)"
    install_mix_deps

    log "[6/8] Python orchestrator deps (huggingface_hub, datasets, pyarrow)"
    python3 -m pip install --upgrade --quiet pip
    python3 -m pip install --quiet "huggingface_hub>=0.27" "datasets>=2.14" "pyarrow>=14"

    log "[7/8] Qwen3-Coder-30B-A3B-Instruct download → $MODEL_DIR"
    download_model_if_missing

    log "[8/8] MultiPL-E $DATASET parquet → $PARQUET"
    download_parquet_if_missing

    log "running mix test for sanity (Step 3/4/6 = 62 tests expected)"
    if ! run_mix_test; then
        err "mix test failed — investigate before proceeding"
        exit 1
    fi

    log "setup complete."
    log "next: bash $0 smoke"
}

cmd_smoke() {
    log "=== smoke: 1 問で pipeline 動作確認 ==="
    if [[ ! -f scripts/eval/run_yamato_min_elixir.py ]]; then
        log "scripts/eval/run_yamato_min_elixir.py 未実装 (Step 2 待ち)"
        log "現状は mix test で骨格テスト (62 tests) のみ検証可"
        run_mix_test
        return 0
    fi
    LIMIT=1 SKIP_EXISTING=0 run_yamato_mode_seed firewall-only "$SEED"
    log "smoke complete. inspect data/eval/results/${DATASET}.yamato_min_elixir.firewall-only.seed${SEED}/_summary.json"
}

# Step 8 Phase 1: Firewall byte-identical 検証 (Step 5 着手前)
cmd_phase1() {
    local seed="${1:-$SEED}"
    log "=== phase1: Firewall byte-identical 検証 (bare vs firewall-only × seed $seed × 161 問) ==="

    run_baseline_seed "$seed"
    run_yamato_mode_seed "firewall-only" "$seed"

    if [[ ! -f scripts/eval/diff_smoke_outputs.py ]]; then
        err "diff_smoke_outputs.py が見つからない、byte-identical 比較を skip"
        return 1
    fi

    log "comparing bare vs firewall-only outputs (byte-identical 期待値: 161/161)"
    python3 scripts/eval/diff_smoke_outputs.py \
        --vanilla     "data/eval/generated/${DATASET}.baseline.seed${seed}" \
        --no-kotodama "data/eval/generated/${DATASET}.yamato_min_elixir.firewall-only.seed${seed}"

    log "phase1 done. Win Condition 一次基準達成なら Step 5 (L5 ハルシネーション検出器) 着手可"
}

# Step 8 Phase 2: 4 mode ablation (Step 5 完了後)
cmd_phase2() {
    local seed="${1:-$SEED}"
    log "=== phase2: 4 mode ablation × seed $seed (Step 5 完了が前提) ==="
    log "modes: ${PHASE2_MODES[*]}"

    # mode 'bare' は baseline と同義
    run_baseline_seed "$seed"
    for mode in "firewall-only" "l5-enhanced-no-fw" "full"; do
        run_yamato_mode_seed "$mode" "$seed"
    done

    if [[ ! -f scripts/eval/judge_win_condition_elixir.py ]]; then
        err "scripts/eval/judge_win_condition_elixir.py が未実装"
        err "  → judge_win_condition_go.py を移植する必要あり"
        return 1
    fi

    log "phase2 done. Win Condition 二次基準は undef-symbol rate の mode 間差で判定"
}

cmd_mix_test() {
    run_mix_test
}

cmd_clean_data() {
    log "removing data/eval/generated/${DATASET}.* and data/eval/results/${DATASET}.* (model and asdf は残す)"
    read -r -p "OK to delete? [y/N] " ans
    case "$ans" in
        y|Y|yes) rm -rf "data/eval/generated/${DATASET}".* "data/eval/results/${DATASET}".* ;;
        *) log "abort"; exit 0 ;;
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
    phase1)       cmd_phase1 "$@" ;;
    phase2)       cmd_phase2 "$@" ;;
    mix-test)     cmd_mix_test ;;
    clean-data)   cmd_clean_data ;;
    ""|-h|--help) usage ;;
    *) err "unknown subcommand: $cmd"; usage ;;
esac
