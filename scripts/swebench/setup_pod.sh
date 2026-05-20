#!/usr/bin/env bash
# SWE-bench Multilingual (Go subset) を新しい RunPod pod で評価する準備
#
# 前提条件:
#   - Docker-enabled な pod テンプレート (`docker info` が通る、または /var/run/docker.sock がマウントされている)
#   - /workspace に 200GB+ の空き (SWE-bench harness は per-instance Docker image を引くので最低 120GB 推奨)
#   - Go subset = 42 タスク (caddyserver/caddy, hashicorp/terraform, prometheus/prometheus, gohugoio/hugo, gin-gonic/gin)
#
# 構成:
#   /workspace/swebench/
#     ├── SWE-bench/                       (harness clone)
#     ├── dataset/multilingual.parquet     (HF からダウンロード)
#     ├── go_instance_ids.txt              (42 行)
#     └── repos/                           (oracle localization 用の git clone)

set -euo pipefail

WORK=/workspace/swebench
GO_REPOS=(
    "caddyserver/caddy"
    "hashicorp/terraform"
    "prometheus/prometheus"
    "gohugoio/hugo"
    "gin-gonic/gin"
)

log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }
err() { printf '[%s] ERROR: %s\n' "$(date +%H:%M:%S)" "$*" >&2; }

# --- 0. fail-fast: docker が無いと harness が動かない -----------------------
check_docker() {
    log "[0/4] docker availability"
    if ! command -v docker >/dev/null; then
        err "docker command not found in PATH"
        err "  → choose a RunPod template that includes Docker (look for 'docker', 'devops', or bare-metal),"
        err "    or mount /var/run/docker.sock from the host."
        exit 1
    fi
    if ! docker info >/dev/null 2>&1; then
        err "docker daemon not reachable. Output of 'docker info':"
        docker info >&2 || true
        err "  → pod likely doesn't expose docker.sock; need a different template."
        exit 1
    fi
    log "docker OK: $(docker --version)"
    log "disk free at /workspace: $(df -h /workspace 2>/dev/null | awk 'NR==2 {print $4}')"
}

# --- 1. SWE-bench harness をクローンして pip install -----------------------
install_harness() {
    log "[1/4] SWE-bench harness"
    mkdir -p "$WORK"
    if [[ ! -d "$WORK/SWE-bench/.git" ]]; then
        git clone --depth 1 https://github.com/swe-bench/SWE-bench.git "$WORK/SWE-bench"
    else
        log "harness already cloned, pulling latest"
        (cd "$WORK/SWE-bench" && git pull --ff-only)
    fi
    python3 -m pip install --quiet -e "$WORK/SWE-bench"
    python3 -c "import swebench; print('swebench imported:', swebench.__file__)"
}

# --- 2. データセット取得 + Go subset 抽出 ----------------------------------
fetch_dataset() {
    log "[2/4] SWE-bench_Multilingual dataset"
    mkdir -p "$WORK/dataset"
    python3 -m pip install --quiet "datasets>=2.14"

    python3 - <<'PY'
import json
from collections import Counter
from datasets import load_dataset

WORK = "/workspace/swebench"

ds = load_dataset("SWE-bench/SWE-bench_Multilingual", split="test")
print(f"loaded {len(ds)} multilingual instances")
ds.to_parquet(f"{WORK}/dataset/multilingual.parquet")

GO_REPOS = {
    "caddyserver/caddy",
    "hashicorp/terraform",
    "prometheus/prometheus",
    "gohugoio/hugo",
    "gin-gonic/gin",
}
go_instances = [r for r in ds if r["repo"] in GO_REPOS]
print(f"Go instances: {len(go_instances)}")
for repo, n in Counter(r["repo"] for r in go_instances).most_common():
    print(f"  {repo}: {n}")

with open(f"{WORK}/go_instance_ids.txt", "w") as f:
    f.write("\n".join(r["instance_id"] for r in go_instances) + "\n")

# build_predictions.py が読む metadata-only jsonl (LLM プロンプト構築用)。
# patch / test_patch は oracle localization で「正解パッチが触ったファイル」
# を抽出する用途に使う (実行時の正解情報は与えない、ファイルパスのみ)。
with open(f"{WORK}/go_instances.jsonl", "w") as f:
    for r in go_instances:
        f.write(json.dumps({
            "instance_id": r["instance_id"],
            "repo": r["repo"],
            "base_commit": r["base_commit"],
            "problem_statement": r["problem_statement"],
            "hints_text": r.get("hints_text", "") or "",
            "patch": r["patch"],
            "FAIL_TO_PASS": r["FAIL_TO_PASS"],
            "PASS_TO_PASS": r["PASS_TO_PASS"],
        }) + "\n")
print(f"wrote {WORK}/go_instance_ids.txt and go_instances.jsonl")
PY
}

# --- 3. Go 対象 repo を base_commit 揃いで clone (oracle localization 用) ---
clone_repos() {
    log "[3/4] git clone Go repos for oracle localization"
    mkdir -p "$WORK/repos"
    for r in "${GO_REPOS[@]}"; do
        local owner="${r%%/*}"
        local name="${r##*/}"
        local dir="$WORK/repos/$name"
        if [[ -d "$dir/.git" ]]; then
            log "  $r: already cloned, fetching"
            (cd "$dir" && git fetch --all --tags --quiet)
        else
            log "  $r: cloning to $dir"
            git clone --quiet "https://github.com/$r.git" "$dir"
        fi
    done
    log "repos cloned. Total size: $(du -sh "$WORK/repos" | awk '{print $1}')"
}

# --- 4. eval driver の存在確認 ---------------------------------------------
verify_harness() {
    log "[4/4] harness verification"
    python3 -m swebench.harness.run_evaluation --help 2>&1 | head -5
    log "setup complete."
}

# --- entry ------------------------------------------------------------------
cmd="${1:-all}"
case "$cmd" in
    all)
        check_docker
        install_harness
        fetch_dataset
        clone_repos
        verify_harness
        ;;
    docker)  check_docker ;;
    harness) install_harness ;;
    dataset) fetch_dataset ;;
    repos)   clone_repos ;;
    verify)  verify_harness ;;
    *)
        echo "usage: $0 [all|docker|harness|dataset|repos|verify]" >&2
        exit 1
        ;;
esac
