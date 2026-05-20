#!/usr/bin/env bash
# RunPod 上で SWE-bench Multilingual (Go subset) を評価する runbook
#
# 前提 pod 環境:
#   - Docker-enabled テンプレート (docker info が通る)
#   - /workspace に 200GB+ の NW Volume (harness が per-instance Docker image を pull/build するため)
#   - GPU: A6000 48GB 推奨 (Qwen 7B bf16)
#
# 推奨フロー (新しい pod で SSH 接続後):
#   # 0. Go tarball / Qwen モデルが必要な場合は事前に upload
#   scp /c/Users/mimat/Downloads/go1.26.3.linux-amd64.tar.gz root@<pod>:/workspace/
#   export GO_TARBALL=/workspace/go1.26.3.linux-amd64.tar.gz
#
#   bash scripts/runpod_swebench.sh setup        # harness + dataset + repos clone (~10 min)
#   bash scripts/runpod_swebench.sh smoke        # 1 instance だけ生成して動作確認 (~3 min)
#   bash scripts/runpod_swebench.sh infer        # 全 42 instance を生成 (~30-60 min)
#   bash scripts/runpod_swebench.sh eval         # SWE-bench harness で docker 評価 (~30-90 min)
#   bash scripts/runpod_swebench.sh report       # results.json から resolved/unresolved 集計
#
# 環境変数:
#   MODEL_DIR         Qwen モデル dir (default: /workspace/Yamato-no-Mikoto/models/Qwen2.5-Coder-7B-Instruct)
#   QUANTIZE          "none" (bf16) | "4bit" | "8bit"  (default: none)
#   MAX_NEW_TOKENS    (default: 1024、diff は長くなりがち)
#   TEMPERATURE       (default: 0.2)
#   SEED              (default: 0)
#   MAX_WORKERS       SWE-bench harness の並列度 (default: 4)
#   RUN_ID            harness の run identifier (default: yamato_<date>)
#   MODEL_TAG         predictions 内 model_name_or_path (default: qwen2.5-coder-7b-oracle)

set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$REPO_ROOT"

WORK=/workspace/swebench
MODEL_DIR="${MODEL_DIR:-$REPO_ROOT/models/Qwen2.5-Coder-7B-Instruct}"
QUANTIZE="${QUANTIZE:-none}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-1024}"
TEMPERATURE="${TEMPERATURE:-0.2}"
SEED="${SEED:-0}"
MAX_WORKERS="${MAX_WORKERS:-4}"
RUN_ID="${RUN_ID:-yamato_$(date +%Y%m%d_%H%M%S)}"
MODEL_TAG="${MODEL_TAG:-qwen2.5-coder-7b-oracle}"

PRED_JSONL="$WORK/predictions/${MODEL_TAG}.seed${SEED}.jsonl"
PRED_JSON="$WORK/predictions/${MODEL_TAG}.seed${SEED}.json"

log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }
err() { printf '[%s] ERROR: %s\n' "$(date +%H:%M:%S)" "$*" >&2; }

# --- sub-commands -----------------------------------------------------------

cmd_setup() {
    log "=== SWE-bench setup ==="
    bash scripts/swebench/setup_pod.sh all
}

cmd_smoke() {
    log "=== smoke: 1 instance で動作確認 ==="
    local first_id
    first_id=$(head -1 "$WORK/go_instance_ids.txt")
    log "smoke target: $first_id"
    mkdir -p "$WORK/predictions"
    python3 scripts/swebench/build_predictions.py \
        --instances "$WORK/go_instances.jsonl" \
        --repos-dir "$WORK/repos" \
        --out "$WORK/predictions/smoke.jsonl" \
        --model "$MODEL_DIR" --quantize "$QUANTIZE" \
        --max-new-tokens "$MAX_NEW_TOKENS" --temperature "$TEMPERATURE" \
        --seed "$SEED" \
        --instance-ids "$first_id"
    log "smoke completed. inspect $WORK/predictions/smoke.jsonl"
    python3 -c "
import json
rec = json.loads(open('$WORK/predictions/smoke.jsonl').readline())
print('--- prompt_tokens:', rec['prompt_tokens'])
print('--- completion_tokens:', rec['completion_tokens'])
print('--- oracle_paths:', rec['oracle_paths'])
print('--- diff (first 400 chars):')
print(rec['model_patch'][:400])
"
}

cmd_infer() {
    log "=== inference: 全 Go instance (42 件) を生成 ==="
    mkdir -p "$WORK/predictions"
    python3 scripts/swebench/build_predictions.py \
        --instances "$WORK/go_instances.jsonl" \
        --repos-dir "$WORK/repos" \
        --out "$PRED_JSONL" \
        --model "$MODEL_DIR" --quantize "$QUANTIZE" \
        --max-new-tokens "$MAX_NEW_TOKENS" --temperature "$TEMPERATURE" \
        --seed "$SEED" --model-tag "$MODEL_TAG" \
        --skip-existing
    # SWE-bench harness は JSON list (or jsonl だが安全のため list 形式) を要求
    python3 -c "
import json, sys
items = [json.loads(l) for l in open('$PRED_JSONL') if l.strip()]
json.dump(items, open('$PRED_JSON', 'w'), ensure_ascii=False)
print('wrote', '$PRED_JSON', 'with', len(items), 'predictions')
"
}

cmd_eval() {
    log "=== eval: SWE-bench harness で docker 評価 ==="
    if [[ ! -s "$PRED_JSON" ]]; then
        err "predictions JSON not found at $PRED_JSON. Run 'infer' first."
        exit 1
    fi
    if ! command -v docker >/dev/null || ! docker info >/dev/null 2>&1; then
        err "docker not available. SWE-bench harness needs docker."
        exit 1
    fi

    # Go subset の instance_ids を space 区切りで渡す
    local ids
    ids=$(tr '\n' ' ' < "$WORK/go_instance_ids.txt")

    log "run_id=$RUN_ID, max_workers=$MAX_WORKERS, predictions=$PRED_JSON"
    log "evaluating ${ids// /, }"

    python3 -m swebench.harness.run_evaluation \
        --dataset_name SWE-bench/SWE-bench_Multilingual \
        --predictions_path "$PRED_JSON" \
        --max_workers "$MAX_WORKERS" \
        --run_id "$RUN_ID" \
        --instance_ids $ids
}

cmd_report() {
    log "=== report ==="
    local results_dir="logs/run_evaluation/$RUN_ID"
    # 互換: swebench harness は最近 logs/ ではなく カレント直下 evaluation_results/ や
    # ${MODEL_TAG}.${RUN_ID}.json に書く版もある。両方探す。
    local report_json="${MODEL_TAG}.${RUN_ID}.json"
    if [[ -f "$report_json" ]]; then
        log "report: $report_json"
        python3 -c "
import json
r = json.load(open('$report_json'))
print('total:', r.get('total_instances'))
print('resolved:', len(r.get('resolved_ids', [])))
print('unresolved:', len(r.get('unresolved_ids', [])))
print('empty_patch:', len(r.get('empty_patch_ids', [])))
print('error:', len(r.get('error_ids', [])))
"
    elif [[ -d "$results_dir" ]]; then
        log "results dir: $results_dir"
        ls -la "$results_dir" | head -20
    else
        err "no report found. expected ${report_json} or ${results_dir}/"
        err "check swebench harness output naming for your version"
        exit 1
    fi
}

usage() { sed -n '2,30p' "$0"; exit 1; }

case "${1:-}" in
    setup)   cmd_setup ;;
    smoke)   cmd_smoke ;;
    infer)   cmd_infer ;;
    eval)    cmd_eval ;;
    report)  cmd_report ;;
    ""|-h|--help) usage ;;
    *) err "unknown subcommand: $1"; usage ;;
esac
