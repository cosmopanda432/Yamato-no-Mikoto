"""
SWE-bench Multilingual (Go subset) 用に bare Qwen2.5-Coder-7B-Instruct で predictions を生成する。

設計方針 (Phase A):
    - yamato 言霊デコーダは使わない (kotodama_context は Go コード本体の型注釈位置を見るが、
      SWE-bench の出力は unified diff であってその文法に kotodama を直接適用するのは未検証)。
    - localization は **oracle** モード (正解 patch から変更ファイルを抽出、それを LLM に教える)。
      これは SWE-bench コミュニティの一般的な簡易ベースライン手法 (Agentless 等が同様)。
    - 1 instance あたり: problem_statement + 各 oracle ファイル内容を prompt に詰めて、unified
      diff を出力させる。生成後は ```diff fence や explanation を剥がして model_patch にする。

使い方:
    python3 scripts/swebench/build_predictions.py \\
        --instances /workspace/swebench/go_instances.jsonl \\
        --repos-dir /workspace/swebench/repos \\
        --out        /workspace/swebench/predictions/qwen_oracle.jsonl \\
        --model      /workspace/Yamato-no-Mikoto/models/Qwen2.5-Coder-7B-Instruct \\
        --max-new-tokens 1024 --temperature 0.2 \\
        --max-files 3 --max-file-chars 12000

出力 (JSONL, 1 行 1 instance):
    {"instance_id": "...", "model_name_or_path": "qwen2.5-coder-7b-oracle", "model_patch": "..."}

SWE-bench harness に渡すときは jsonl ではなく list-of-dict (JSON) を期待するので、最後に
別の小さなスクリプト (or eval_predictions.sh) で jsonl -> json に変換する。
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
import sys
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger(__name__)

REPO_BASENAME = {
    "caddyserver/caddy": "caddy",
    "hashicorp/terraform": "terraform",
    "prometheus/prometheus": "prometheus",
    "gohugoio/hugo": "hugo",
    "gin-gonic/gin": "gin",
}


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", required=True,
                    help="setup_pod.sh が出した go_instances.jsonl")
    ap.add_argument("--repos-dir", required=True,
                    help="setup_pod.sh が clone した repos/ ディレクトリ")
    ap.add_argument("--out", required=True, help="predictions JSONL 出力先")
    ap.add_argument("--model", required=True)
    ap.add_argument("--quantize", choices=["4bit", "8bit", "none"], default="none")
    ap.add_argument("--max-new-tokens", type=int, default=1024)
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--top-p", type=float, default=0.95)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max-files", type=int, default=3,
                    help="oracle file が複数あるとき、prompt に詰める上限")
    ap.add_argument("--max-file-chars", type=int, default=12000,
                    help="1 ファイルあたり prompt に含める文字数の上限 (頭から切る)")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--instance-ids", nargs="*", default=None,
                    help="特定 instance_id のみ生成 (デバッグ用)")
    ap.add_argument("--model-tag", default="qwen2.5-coder-7b-oracle",
                    help="predictions JSON の model_name_or_path フィールド")
    ap.add_argument("--skip-existing", action="store_true")
    return ap.parse_args()


def extract_modified_paths(patch: str) -> list[str]:
    """unified diff から変更されたファイルパスを抽出 (oracle localization)。"""
    paths = []
    for line in patch.splitlines():
        if line.startswith("diff --git "):
            # `diff --git a/foo/bar.go b/foo/bar.go` → foo/bar.go
            m = re.match(r"diff --git a/(\S+) b/", line)
            if m:
                paths.append(m.group(1))
        elif line.startswith("+++ b/"):
            paths.append(line[len("+++ b/"):].strip())
    # 重複排除しつつ順序保持
    seen, out = set(), []
    for p in paths:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def read_file_at_commit(repo_dir: Path, commit: str, file_path: str) -> str | None:
    """git show <commit>:<path> でファイル内容を取得 (存在しなければ None)。"""
    try:
        result = subprocess.run(
            ["git", "show", f"{commit}:{file_path}"],
            cwd=str(repo_dir),
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            return None
        return result.stdout
    except (subprocess.TimeoutExpired, OSError):
        return None


def build_prompt(instance: dict, file_contents: list[tuple[str, str]],
                 max_file_chars: int) -> str:
    """Qwen-instruct 用の prompt を組み立てる。"""
    repo = instance["repo"]
    issue = instance["problem_statement"]
    hints = instance.get("hints_text", "")

    parts = []
    parts.append(f"You are fixing an issue in the {repo} Go repository.")
    parts.append("")
    parts.append("# Issue")
    parts.append(issue.strip())
    if hints.strip():
        parts.append("")
        parts.append("# Hints")
        parts.append(hints.strip())
    parts.append("")
    parts.append("# Files you may need to modify")
    for path, content in file_contents:
        truncated = content[:max_file_chars]
        ellipsis = "" if len(content) <= max_file_chars else f"\n... [+{len(content)-max_file_chars} chars truncated]"
        parts.append(f"\n## File: {path}")
        parts.append(f"```go\n{truncated}{ellipsis}\n```")
    parts.append("")
    parts.append("# Task")
    parts.append("Output a unified diff (in `diff --git a/... b/...` format) that fixes the issue. "
                 "Modify only the files listed above. Output ONLY the diff, no explanation, no markdown fence.")
    return "\n".join(parts)


def chat_format(tokenizer, prompt: str) -> str:
    """Qwen2.5-Coder-Instruct の chat template を適用。"""
    msgs = [
        {"role": "system", "content": "You are an expert Go developer who fixes bugs by producing precise unified diffs."},
        {"role": "user", "content": prompt},
    ]
    return tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)


def extract_diff(text: str) -> str:
    """生成テキストから unified diff 部分を抽出。
    LLM は ```diff fence や前後の説明を付けがちなので削ぐ。"""
    # ```diff ... ``` フェンスがあれば中身を取る
    m = re.search(r"```(?:diff|patch)?\s*\n(diff --git .*?)```", text, re.DOTALL)
    if m:
        return m.group(1).rstrip() + "\n"
    # フェンス無しで diff --git から始まる行を頭にする
    idx = text.find("diff --git ")
    if idx >= 0:
        body = text[idx:]
        # 末尾に余計な説明が付いていればトリム (最後の diff hunk 以降の non-diff 行を切る)
        # 単純化: 連続する diff/index/---/+++/@@/+/-/<space> 以外の行で fenced 風なら止める
        lines = body.splitlines(keepends=True)
        cut = len(lines)
        for i, ln in enumerate(lines):
            if ln.startswith("```") or ln.startswith("Note:") or ln.startswith("Explanation"):
                cut = i
                break
        return "".join(lines[:cut])
    # diff が見つからなければ raw を返す (harness が拒絶するが、何を出したかの記録になる)
    return text


def load_model(model_path: str, quantize: str):
    kwargs = {"device_map": "auto"}
    if quantize == "4bit":
        from transformers import BitsAndBytesConfig
        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )
    elif quantize == "8bit":
        from transformers import BitsAndBytesConfig
        kwargs["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)
    else:
        kwargs["torch_dtype"] = torch.bfloat16
    tok = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path, **kwargs)
    model.eval()
    return model, tok


def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 既存予測の skip 対応 (resume)
    done_ids: set[str] = set()
    if args.skip_existing and out_path.exists():
        with out_path.open() as f:
            for line in f:
                try:
                    done_ids.add(json.loads(line)["instance_id"])
                except (json.JSONDecodeError, KeyError):
                    pass
        logger.info("resume: %d instances already in %s", len(done_ids), out_path)

    instances = []
    with open(args.instances) as f:
        for line in f:
            line = line.strip()
            if line:
                instances.append(json.loads(line))
    if args.instance_ids:
        keep = set(args.instance_ids)
        instances = [r for r in instances if r["instance_id"] in keep]
    if args.limit is not None:
        instances = instances[: args.limit]
    logger.info("targeting %d instances", len(instances))

    logger.info("loading model %s (quantize=%s)", args.model, args.quantize)
    model, tok = load_model(args.model, args.quantize)
    device = next(model.parameters()).device
    do_sample = args.temperature > 0

    repos_dir = Path(args.repos_dir)
    with out_path.open("a") as out_f:
        for i, inst in enumerate(instances):
            iid = inst["instance_id"]
            if iid in done_ids:
                logger.info("[%d/%d] %s SKIP (already in predictions)", i+1, len(instances), iid)
                continue

            paths = extract_modified_paths(inst["patch"])
            paths = paths[: args.max_files]
            repo_dir = repos_dir / REPO_BASENAME[inst["repo"]]
            file_contents = []
            for p in paths:
                content = read_file_at_commit(repo_dir, inst["base_commit"], p)
                if content is None:
                    logger.warning("  could not read %s @ %s in %s", p, inst["base_commit"], inst["repo"])
                    content = "(file not found at base_commit)"
                file_contents.append((p, content))

            prompt = build_prompt(inst, file_contents, args.max_file_chars)
            chat = chat_format(tok, prompt)
            inputs = tok(chat, return_tensors="pt", truncation=True, max_length=32000).to(device)

            t0 = time.time()
            with torch.no_grad():
                out_ids = model.generate(
                    **inputs,
                    max_new_tokens=args.max_new_tokens,
                    do_sample=do_sample,
                    temperature=args.temperature if do_sample else None,
                    top_p=args.top_p if do_sample else None,
                    pad_token_id=tok.eos_token_id,
                )
            gen_ids = out_ids[0, inputs["input_ids"].shape[1]:]
            raw = tok.decode(gen_ids, skip_special_tokens=True)
            diff = extract_diff(raw)
            elapsed = time.time() - t0

            out_f.write(json.dumps({
                "instance_id": iid,
                "model_name_or_path": args.model_tag,
                "model_patch": diff,
                "raw_completion": raw,
                "oracle_paths": paths,
                "prompt_tokens": int(inputs["input_ids"].shape[1]),
                "completion_tokens": int(gen_ids.shape[0]),
                "elapsed_sec": elapsed,
            }) + "\n")
            out_f.flush()

            logger.info("[%d/%d] %s  prompt=%d, completion=%d, diff_len=%d, %.1fs",
                        i+1, len(instances), iid,
                        inputs["input_ids"].shape[1], gen_ids.shape[0], len(diff), elapsed)

    logger.info("done. wrote %s", out_path)


if __name__ == "__main__":
    main()
