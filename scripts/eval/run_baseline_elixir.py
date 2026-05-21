"""
Elixir 版 baseline 生成スクリプト — bare Qwen2.5-Coder-7B-Instruct で humaneval-elixir
/ mbpp-elixir を解く。

kojiki_lm 依存なし。transformers.generate を直呼びする最小実装。Go 版 (run_baseline_go.py)
と本質的に同一だが、Elixir target の baseline run を分離して保存することで、後段の judge
が baseline.seedX vs yamato_min_elixir.seedX を 1:1 で比較できる。

ロードマップ:
- M0 (Elixir target): docs/roadmap_eli2.md の最初のマイルストーン
- 目的: Win Condition の baseline を確定 (yamato_min_elixir 比較対象)
- 3 seed (--seed 0/1/2) で run → 平均 ± 95% CI

使い方:
    python3 scripts/eval/run_baseline_elixir.py \\
        --input data/raw/multipl_e/humaneval-elixir/test-00000-of-00001.parquet \\
        --out-dir data/eval/generated/humaneval-elixir.baseline.seed0 \\
        --seed 0 --quantize 4bit

評価は別途 scripts/eval/elixir_eval.py で行う:
    python3 scripts/eval/elixir_eval.py \\
        --generated-dir data/eval/generated/humaneval-elixir.baseline.seed0 \\
        --out-dir data/eval/results/humaneval-elixir.baseline.seed0
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

import pyarrow.parquet as pq
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

logger = logging.getLogger(__name__)


def truncate_at_stop_tokens(text: str, stop_tokens) -> str:
    """生成テキストを stop_tokens で切る (各 stop_token の最初の occurrence で truncate)"""
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

    ap.add_argument("--model", default=str(REPO_ROOT / "models" / "Qwen2.5-Coder-7B-Instruct"))
    ap.add_argument("--quantize", choices=["4bit", "8bit", "none"], default="4bit")

    ap.add_argument("--max-new-tokens", type=int, default=256)
    ap.add_argument("--temperature", type=float, default=0.2,
                    help="temperature > 0 ならサンプリング、0 で greedy")
    ap.add_argument("--top-p", type=float, default=0.95)

    ap.add_argument("--seed", type=int, default=0,
                    help="サンプリング seed。3 seed (0/1/2) 流して baseline 平均を取る")

    ap.add_argument("--limit", type=int, default=None, help="最初の N 問のみ")
    ap.add_argument("--skip-existing", action="store_true")
    return ap.parse_args()


def load_backbone(model_path: str, quantize: str):
    logger.info("Loading %s (quantize=%s)", model_path, quantize)

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

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path, **kwargs)
    model.eval()

    n_params = sum(p.numel() for p in model.parameters()) / 1e9
    logger.info("Loaded %s: %.1fB params", model_path, n_params)
    return model, tokenizer


def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 再現性のため torch も含めて seed を固定
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    model, tokenizer = load_backbone(args.model, args.quantize)
    device = next(model.parameters()).device

    table = pq.read_table(args.input)
    rows = table.to_pylist()
    if args.limit is not None:
        rows = rows[: args.limit]
    logger.info("Loaded %d prompts from %s (seed=%d)", len(rows), args.input, args.seed)

    n_done = 0
    n_skipped = 0
    t_total = 0.0

    do_sample = args.temperature > 0

    for i, row in enumerate(rows):
        name = row["name"]
        out_path = out_dir / f"{name}__s0.json"
        if args.skip_existing and out_path.exists():
            n_skipped += 1
            continue

        prompt = row["prompt"]
        stop_tokens = list(row.get("stop_tokens") or [])

        # 修正 D 補助: prompt 単位で manual_seed を呼ぶ。run_yamato_min_elixir.py 側で
        # KotodamaConfig.sampling_seed = args.seed * 1_000_003 + i としているのと
        # 同じ式。これにより両 runner で「同一 prompt は同一 sampling RNG seed」
        # になり、baseline ↔ vanilla の sampler 等価性 (修正 A) を fair に比較できる。
        per_prompt_seed = args.seed * 1_000_003 + i
        torch.manual_seed(per_prompt_seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(per_prompt_seed)

        t0 = time.time()
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=args.max_new_tokens,
                do_sample=do_sample,
                temperature=args.temperature if do_sample else None,
                top_p=args.top_p if do_sample else None,
                pad_token_id=tokenizer.eos_token_id,
            )
        # prompt 部分を除いた完成文だけ
        generated_ids = output_ids[0, inputs["input_ids"].shape[1]:]
        text = tokenizer.decode(generated_ids, skip_special_tokens=True)
        elapsed = time.time() - t0
        t_total += elapsed

        completion = truncate_at_stop_tokens(text, stop_tokens)

        out_path.write_text(json.dumps({
            "name": name,
            "sample_id": 0,
            "seed": args.seed,
            "prompt": prompt,
            "completion": completion,
            "raw_completion": text,
            "tests": row["tests"],
            "stop_tokens": stop_tokens,
            "model": args.model,
            "quantize": args.quantize,
            "temperature": args.temperature,
            "elapsed_sec": elapsed,
            "language": "elixir",
        }, ensure_ascii=False))

        n_done += 1
        logger.info(
            "[%d/%d] %s  %dc / %.1fs",
            i + 1, len(rows), name, len(completion), elapsed,
        )

    avg = t_total / max(n_done, 1)
    logger.info(
        "Done: generated=%d, skipped=%d, avg=%.1fs/q, total=%.0fs",
        n_done, n_skipped, avg, t_total,
    )


if __name__ == "__main__":
    main()
