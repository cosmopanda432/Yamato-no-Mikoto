"""
yamatoLLM Go 版 e2e 生成スクリプト

Qwen2.5-Coder backbone + (任意の言霊 v2 = symbol-aware logit bias) + Firewall
を通して humaneval-go を解く。`scripts/eval/run_baseline_go.py` (vanilla 専用)
と並列で M2 以降の評価に使う。

Mode (Ablation):
    full         : 言霊 ON + Firewall ON (Go 版の本命)
    no-kotodama  : 言霊 OFF + Firewall ON (Firewall のみ)
    no-firewall  : 言霊 ON + Firewall OFF (Kotodama のみ)
    vanilla      : 言霊 OFF + Firewall OFF (= run_baseline_go.py と同等)

使い方:
    python3 scripts/eval/run_yamato_min_go.py \\
        --input data/raw/multipl_e/humaneval-go/test-00000-of-00001.parquet \\
        --out-dir data/eval/generated/humaneval-go.yamato_min_go.full \\
        --mode full --quantize 4bit --max-new-tokens 256
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
sys.path.insert(0, str(REPO_ROOT / "src_min_go"))

import torch  # noqa: E402

from kojiki_lm.go_symbol_oracle import OracleClient  # noqa: E402
from kojiki_lm.kotodama_decoder import KotodamaConfig, KotodamaDecoder  # noqa: E402
from kojiki_lm.kotodama_token_mask import GoSymbolBiasBuilder  # noqa: E402
from kojiki_lm.qwen_adapter import QwenAdapter  # noqa: E402
from kojiki_lm.yomi_evaluator import YomiEvaluator  # noqa: E402
from kojiki_lm.yomotsu_hirasaka import YomotsuHirasaka  # noqa: E402


logger = logging.getLogger(__name__)


MODE_FLAGS = {
    # mode → (bias_enabled, firewall_enabled)
    "full":        (True,  True),
    "no-kotodama": (False, True),
    "no-firewall": (True,  False),
    "vanilla":     (False, False),
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
    ap.add_argument("--input", required=True, help="MultiPL-E parquet (humaneval-go)")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--mode", choices=list(MODE_FLAGS.keys()), default="full")

    ap.add_argument("--model", default=str(REPO_ROOT / "models" / "Qwen2.5-Coder-7B-Instruct"))
    ap.add_argument("--quantize", choices=["4bit", "8bit", "none"], default="4bit")
    ap.add_argument("--oracle-bin",
                    default=str(REPO_ROOT / "src_min_go" / "go_tools" / "bin" / "symbol_oracle"))

    ap.add_argument("--max-new-tokens", type=int, default=256)
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--top-k", type=int, default=50,
                    help="run_baseline_go.py (model.generate) と一致させるためのデフォルト")
    ap.add_argument("--top-p", type=float, default=0.95,
                    help="run_baseline_go.py の top_p=0.95 と一致")
    ap.add_argument("--bias-value", type=float, default=2.0,
                    help="言霊 bias の加算量 (0.0 で実質 vanilla)")
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

    bias_enabled, firewall_enabled = MODE_FLAGS[args.mode]
    logger.info(
        "Mode=%s (bias=%s, firewall=%s, bias_value=%.2f)",
        args.mode, bias_enabled, firewall_enabled, args.bias_value,
    )

    # backbone
    quantize = None if args.quantize == "none" else args.quantize
    logger.info("Loading backbone %s (quantize=%s)", args.model, quantize)
    backbone, tokenizer = QwenAdapter.load_base_model(
        model_name=args.model, quantize=quantize,
    )
    backbone.eval()

    # bias builder (vocab 幅は LM head に合わせる)
    lm_vocab_size = int(getattr(backbone.config, "vocab_size", len(tokenizer)))
    bias_builder = GoSymbolBiasBuilder(tokenizer, vocab_size=lm_vocab_size)

    # oracle (bias 有効モードのときだけ起動)
    oracle: OracleClient | None = None
    if bias_enabled:
        oracle_bin = Path(args.oracle_bin)
        oracle = OracleClient(oracle_bin, timeout_sec=2.0)
        logger.info("Oracle daemon started: %s", oracle_bin)

    firewall = YomotsuHirasaka(YomiEvaluator())

    kotodama_cfg = KotodamaConfig(
        max_new_tokens=args.max_new_tokens,
        bias_value=args.bias_value if bias_enabled else 0.0,
        firewall_interval=args.firewall_interval,
        temperature=args.temperature,
        do_sample=args.temperature > 0,
        top_k=args.top_k,
        top_p=args.top_p,
        mask_enabled=bias_enabled,
        firewall_enabled=firewall_enabled,
        oracle_enabled=bias_enabled,
    )

    decoder = KotodamaDecoder(oracle, bias_builder, firewall, kotodama_cfg)

    table = pq.read_table(args.input)
    rows = table.to_pylist()
    if args.limit is not None:
        rows = rows[: args.limit]
    logger.info("Loaded %d prompts from %s", len(rows), args.input)

    n_done = 0
    n_skipped = 0
    n_halted = 0
    t_total = 0.0

    try:
        for i, row in enumerate(rows):
            name = row["name"]
            out_path = out_dir / f"{name}__s0.json"
            if args.skip_existing and out_path.exists():
                n_skipped += 1
                continue

            prompt = row["prompt"]
            stop_tokens = list(row.get("stop_tokens") or [])

            t0 = time.time()
            result = decoder.generate(backbone, tokenizer, prompt, prompt_id=name)
            elapsed = time.time() - t0
            t_total += elapsed

            completion = truncate_at_stop_tokens(result.text, stop_tokens)
            n_biased = result.num_biased_steps

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
                # 言霊 (Go) 専用フィールド
                "kotodama_mode": args.mode,
                "bias_value": kotodama_cfg.bias_value,
                "bias_step_count": n_biased,
                "total_step_count": len(result.steps),
                "halted_early": result.halted_early,
                "final_verdict": (
                    result.final_verdict.verdict.value if result.final_verdict else None
                ),
                "final_v_score": (
                    result.final_verdict.v_score if result.final_verdict else None
                ),
                # scope_kind の分布 (debug)
                "scope_kind_counts": _count_scopes(result.steps),
            }, ensure_ascii=False))

            n_done += 1
            if result.halted_early:
                n_halted += 1
            logger.info(
                "[%d/%d] %s  %dc / bias=%d/%d / verdict=%s / %.1fs",
                i + 1, len(rows), name,
                len(completion), n_biased, len(result.steps),
                (result.final_verdict.verdict.value if result.final_verdict else "-"),
                elapsed,
            )
    finally:
        if oracle is not None:
            oracle.close()

    avg = t_total / max(n_done, 1)
    logger.info(
        "Done: generated=%d, skipped=%d, halted_early=%d, avg=%.1fs/q, total=%.0fs",
        n_done, n_skipped, n_halted, avg, t_total,
    )


def _count_scopes(steps) -> dict[str, int]:
    counts: dict[str, int] = {}
    for s in steps:
        if s.bias_applied:
            counts[s.scope_kind] = counts.get(s.scope_kind, 0) + 1
    return counts


if __name__ == "__main__":
    main()
