"""
M6 — yamatoLLM (簡易版) の e2e 生成スクリプト

generate_multipl_e.py の Yamato 版。Qwen2.5-Coder backbone に Stage 2 学習済 TypeHead
(custom_heads.pt) を attach し、YamatoQwenForCausalLM.generate_kotodama 経由で
**言霊マスク + 黄泉比良坂 Firewall** を通した decode を実行する。

出力 JSON フォーマットは generate_multipl_e.py と互換 (`scripts/eval/run_tests.py` と
`scripts/eval/aux_metrics.py` がそのまま流用可能)。加えて Kotodama 専用フィールド
(`kotodama_mode`, `mask_step_count`, `final_verdict`, `v_score`) を付加する。

Mode (Ablation 用 --mode):
    full         : 言霊 ON + Firewall ON  (簡易版の本命)
    no-kotodama  : 言霊 OFF + Firewall ON (Firewall のみ)
    no-firewall  : 言霊 ON  + Firewall OFF (Kotodama のみ, 常時 COMMIT 扱い)
    vanilla      : 言霊 OFF + Firewall OFF (= HF generate, baseline 同等)

使い方:
    python3 scripts/eval/run_yamato_min.py \\
        --input data/raw/multipl_e/humaneval-ts/test-00000-of-00001.parquet \\
        --out-dir data/eval/generated/humaneval-ts.yamato_min \\
        --custom-heads checkpoints/yamato_sft_a6000/step_2000/custom_heads.pt \\
        --mode full --quantize 4bit
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

import pyarrow.parquet as pq
import torch

from kojiki_lm.kotodama_decoder import KotodamaConfig
from kojiki_lm.kotodama_token_mask import KotodamaMaskBuilder, TypeVocabIndex
from kojiki_lm.qwen_adapter import QwenAdapter
from kojiki_lm.yamato_config import YamatoConfig
from kojiki_lm.yamato_model import YamatoLLM
from kojiki_lm.yomi_evaluator import YomiEvaluator
from kojiki_lm.yomotsu_hirasaka import YomotsuHirasaka

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

logger = logging.getLogger(__name__)


MODE_FLAGS = {
    # mode → (mask_enabled, firewall_enabled)
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
    ap.add_argument("--input", required=True, help="MultiPL-E parquet (humaneval-ts / mbpp-ts)")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--mode", choices=list(MODE_FLAGS.keys()), default="full")

    ap.add_argument("--model", default=str(REPO_ROOT / "models" / "Qwen2.5-Coder-7B-Instruct"))
    ap.add_argument("--quantize", choices=["4bit", "8bit", "none"], default="4bit")
    ap.add_argument("--custom-heads", required=True,
                    help="checkpoints/.../custom_heads.pt (Stage 2 学習済ヘッド)")
    ap.add_argument("--type-vocab", default=str(REPO_ROOT / "config" / "ts_type_vocab.json"))

    ap.add_argument("--max-new-tokens", type=int, default=512)
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--top-k-types", type=int, default=5,
                    help="言霊マスク時に union する TypeHead top-K")
    ap.add_argument("--firewall-interval", type=int, default=16,
                    help="N トークンごとに Firewall 問い合わせ")

    ap.add_argument("--limit", type=int, default=None, help="最初の N 問のみ")
    ap.add_argument("--skip-existing", action="store_true")
    return ap.parse_args()


def build_yamato(args) -> tuple[YamatoLLM, KotodamaMaskBuilder, YomotsuHirasaka]:
    quantize = None if args.quantize == "none" else args.quantize

    logger.info("Loading backbone %s (quantize=%s)", args.model, quantize)
    backbone, tokenizer = QwenAdapter.load_base_model(
        model_name=args.model,
        quantize=quantize,
    )
    backbone.eval()

    config = YamatoConfig()
    config.backbone.model_name = args.model
    yamato = YamatoLLM(backbone=backbone, tokenizer=tokenizer, config=config)
    yamato.init_custom_heads()

    sd = torch.load(args.custom_heads, map_location="cpu")
    yamato.custom_heads.load_state_dict(sd)
    yamato.custom_heads.eval()
    # device / dtype を backbone と揃える
    device = next(backbone.parameters()).device
    dtype = torch.bfloat16 if hasattr(next(backbone.parameters()), "quant_state") \
        else next(backbone.parameters()).dtype
    yamato.custom_heads = yamato.custom_heads.to(device=device, dtype=dtype)
    logger.info("Loaded custom_heads from %s", args.custom_heads)

    type_vocab = TypeVocabIndex(args.type_vocab)
    # LM head の真の幅 (Qwen2.5 では len(tokenizer) より大きいことがある) に合わせる
    lm_vocab_size = int(getattr(backbone.config, "vocab_size", len(tokenizer)))
    mask_builder = KotodamaMaskBuilder(tokenizer, type_vocab, vocab_size=lm_vocab_size)

    firewall = YomotsuHirasaka(YomiEvaluator())

    return yamato, mask_builder, firewall


def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    mask_enabled, firewall_enabled = MODE_FLAGS[args.mode]
    logger.info(
        "Mode=%s (mask_enabled=%s, firewall_enabled=%s)",
        args.mode, mask_enabled, firewall_enabled,
    )

    yamato, mask_builder, firewall = build_yamato(args)
    tokenizer = yamato.tokenizer
    backbone = yamato.backbone   # YamatoQwenForCausalLM
    type_head = yamato.custom_heads["type_head"]

    kotodama_cfg = KotodamaConfig(
        max_new_tokens=args.max_new_tokens,
        top_k_types=args.top_k_types,
        firewall_interval=args.firewall_interval,
        temperature=args.temperature,
        do_sample=args.temperature > 0,
        mask_enabled=mask_enabled,
        firewall_enabled=firewall_enabled,
    )

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

        t0 = time.time()
        result = backbone.generate_kotodama(
            prompt_text=prompt,
            tokenizer=tokenizer,
            mask_builder=mask_builder,
            type_head=type_head,
            firewall=firewall,
            config=kotodama_cfg,
            prompt_id=name,
        )
        elapsed = time.time() - t0
        t_total += elapsed

        completion = truncate_at_stop_tokens(result.text, stop_tokens)

        out_path.write_text(json.dumps({
            "name": name,
            "sample_id": 0,
            "prompt": prompt,
            "completion": completion,
            "raw_completion": result.text,
            "tests": row["tests"],
            "stop_tokens": stop_tokens,
            "model": args.model,
            "quantize": args.quantize,
            "temperature": args.temperature,
            "elapsed_sec": elapsed,
            # Kotodama 追加メタ
            "kotodama_mode": args.mode,
            "mask_step_count": result.num_masked_steps,
            "total_step_count": len(result.steps),
            "halted_early": result.halted_early,
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
            "[%d/%d] %s  %dc / mask=%d/%d / verdict=%s / %.1fs",
            i + 1, len(rows), name,
            len(completion), result.num_masked_steps, len(result.steps),
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
