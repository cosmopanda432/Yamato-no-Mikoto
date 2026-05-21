"""
yamatoLLM Elixir target e2e 生成スクリプト (Firewall 専用版)

Qwen2.5-Coder backbone + Firewall (YomotsuHirasaka) を通して humaneval-elixir /
mbpp-elixir を解く。`scripts/eval/run_baseline_elixir.py` (bare model.generate) と
並列で、Firewall pathway の効果を検証する。

src_min_eli2 では言霊 (Kotodama / symbol-aware bias) を撤去 (2026-05-21、
docs/roadmap_eli2.md 参照)。本 runner は 2 mode のみ:

Mode (Ablation):
    firewall-on   : FirewallDecoder + Firewall ON (本命、L5 verdict 信号活性)
    firewall-off  : FirewallDecoder + Firewall OFF (code path 差中和の対照)

baseline (`run_baseline_elixir.py`) と firewall-off は code path が違う:
    baseline       : transformers の `model.generate()`
    firewall-off   : FirewallDecoder の token-by-token decode (firewall_enabled=False)
両者は修正 A (LogitsWarper 公式版を使う) により byte-equivalent な sampling になる
よう設計済み。検証は別途 byte-identical 比較で行う。

使い方:
    python3 scripts/eval/run_yamato_min_elixir.py \\
        --input data/raw/multipl_e/humaneval-elixir/test-00000-of-00001.parquet \\
        --out-dir data/eval/generated/humaneval-elixir.yamato_min_elixir.firewall-on.seed0 \\
        --mode firewall-on --quantize 4bit --seed 0
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "src_min_eli2"))

import torch  # noqa: E402

from kojiki_lm.elixir_evaluator import ElixirEvaluator  # noqa: E402
from kojiki_lm.firewall_decoder import FirewallConfig, FirewallDecoder  # noqa: E402
from kojiki_lm.qwen_adapter import QwenAdapter  # noqa: E402
from kojiki_lm.yomotsu_hirasaka import YomotsuHirasaka  # noqa: E402


logger = logging.getLogger(__name__)


MODE_FLAGS = {
    # mode → firewall_enabled
    "firewall-on":  True,
    "firewall-off": False,
}


def truncate_at_stop_tokens(text: str, stop_tokens) -> str:
    cut = len(text)
    for st in stop_tokens or []:
        idx = text.find(st)
        if 0 <= idx < cut:
            cut = idx
    return text[:cut]


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True,
                    help="MultiPL-E parquet (humaneval-elixir / mbpp-elixir)")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--mode", choices=list(MODE_FLAGS.keys()), default="firewall-on")

    ap.add_argument("--model", default=str(REPO_ROOT / "models" / "Qwen2.5-Coder-7B-Instruct"))
    ap.add_argument("--quantize", choices=["4bit", "8bit", "none"], default="4bit")

    ap.add_argument("--max-new-tokens", type=int, default=256)
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--top-k", type=int, default=50,
                    help="run_baseline_elixir.py と一致させるためのデフォルト")
    ap.add_argument("--top-p", type=float, default=0.95,
                    help="run_baseline_elixir.py の top_p=0.95 と一致")
    ap.add_argument("--firewall-interval", type=int, default=16)
    ap.add_argument("--seed", type=int, default=0)

    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--skip-existing", action="store_true")
    return ap.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    firewall_enabled = MODE_FLAGS[args.mode]
    logger.info("Mode=%s (firewall=%s)", args.mode, firewall_enabled)

    # backbone
    quantize = None if args.quantize == "none" else args.quantize
    logger.info("Loading backbone %s (quantize=%s)", args.model, quantize)
    backbone, tokenizer = QwenAdapter.load_base_model(
        model_name=args.model, quantize=quantize,
    )
    backbone.eval()

    firewall = YomotsuHirasaka(ElixirEvaluator())

    fw_cfg = FirewallConfig(
        max_new_tokens=args.max_new_tokens,
        firewall_interval=args.firewall_interval,
        temperature=args.temperature,
        do_sample=args.temperature > 0,
        top_k=args.top_k,
        top_p=args.top_p,
        firewall_enabled=firewall_enabled,
        # sampling_seed は prompt 単位で派生させる (loop 内で再設定)
        sampling_seed=args.seed,
    )

    decoder = FirewallDecoder(firewall, fw_cfg)

    table = pq.read_table(args.input)
    rows = table.to_pylist()
    if args.limit is not None:
        rows = rows[: args.limit]
    logger.info("Loaded %d prompts from %s", len(rows), args.input)

    n_done = 0
    n_skipped = 0
    n_halted = 0
    t_total = 0.0

    for i, row in enumerate(rows):
        name = row["name"]
        out_path = out_dir / f"{name}__s0.json"
        if args.skip_existing and out_path.exists():
            n_skipped += 1
            continue

        prompt = row["prompt"]
        stop_tokens = list(row.get("stop_tokens") or [])

        # 修正 D: prompt 単位の deterministic seed を派生させる。
        # mode 間 (firewall-off / firewall-on) で同一 prompt は同一 seed となり、
        # `firewall.send` のサイドチャネルが sampler に影響しなくなる
        # (firewall_enabled toggle で byte-identical を狙う)。
        # 1_000_003 は prime > 397 (mbpp-elixir 最大) なので衝突なし。
        fw_cfg.sampling_seed = args.seed * 1_000_003 + i

        t0 = time.time()
        result = decoder.generate(
            backbone, tokenizer, prompt,
            prompt_id=name, stop_tokens=tuple(stop_tokens),
        )
        elapsed = time.time() - t0
        t_total += elapsed

        completion = truncate_at_stop_tokens(result.text, stop_tokens)

        out_path.write_text(json.dumps({
            "name": name,
            "sample_id": 0,
            "seed": args.seed,
            "prompt": prompt,
            "completion": completion,
            "raw_completion": result.text,
            "tests": row["tests"],
            "stop_tokens": stop_tokens,
            "model": args.model,
            "quantize": args.quantize,
            "temperature": args.temperature,
            "elapsed_sec": elapsed,
            "language": "elixir",
            # Firewall 専用フィールド
            "firewall_mode": args.mode,
            "total_step_count": len(result.steps),
            "halted_early": result.halted_early,
            "stopped_at_stop_token": result.stopped_at_stop_token,
            "final_verdict": (
                result.final_verdict.verdict.value if result.final_verdict else None
            ),
            "final_v_score": (
                result.final_verdict.v_score if result.final_verdict else None
            ),
        }, ensure_ascii=False))

        n_done += 1
        if result.halted_early:
            n_halted += 1
        logger.info(
            "[%d/%d] %s  %dc / steps=%d / verdict=%s / %.1fs",
            i + 1, len(rows), name,
            len(completion), len(result.steps),
            (result.final_verdict.verdict.value if result.final_verdict else "-"),
            elapsed,
        )

    avg = t_total / max(n_done, 1)
    logger.info(
        "Done: generated=%d, skipped=%d, halted_early=%d, avg=%.1fs/q, total=%.0fs",
        n_done, n_skipped, n_halted, avg, t_total,
    )


if __name__ == "__main__":
    main()
