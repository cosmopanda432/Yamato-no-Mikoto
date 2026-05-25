"""
yamatoLLM Elixir target e2e 生成スクリプト — src_min_eli3 (光明想統合版)

eli2 の run_yamato_min_elixir.py と同形だが、以下の差分:
  - import 元が src_min_eli3
  - mode に "koumyou-on" を追加 (Firewall ON + KoumyouSo ON + trace seed 注入)
  - 各サンプル JSON に trace_info (KoumyouSo 判定結果) を追加

光明想 (KoumyouSo) は仏教五蓋の第三「惛沈睡眠 (こうちんすいみん)」=怠惰の対治法。
出力テキストの先頭に reasoning trace (`# 思考: ...`) を強制し、不在/不足を即 HALT する
ことで、model が思考過程を見せずに code に直行する手抜きを物理的に困難にする。
(docs/memo/2026-05-26_須弥山設計原理.md Part 2 §6)

Mode (3-arm ablation):
    firewall-off : Firewall OFF + KoumyouSo OFF (eli2 firewall-off と等価)
    firewall-on  : Firewall ON  + KoumyouSo OFF (eli2 firewall-on と等価)
    koumyou-on   : Firewall ON  + KoumyouSo ON  + trace seed 注入 (eli3 主流)

trace seed の効果:
  prompt 末尾に `"  # 思考: "` を注入 → model の最初の生成トークンは trace 本文の続き。
  KoumyouSo がその先の trace 行数 / 文字数 / code 開始位置をチェックして HALT 判定。

使い方:
    python3 scripts/eval/run_yamato_min_elixir3.py \\
        --input data/raw/multipl_e/humaneval-elixir/test-00000-of-00001.parquet \\
        --out-dir data/eval/generated/humaneval-elixir.yamato_min_elixir3.koumyou-on.seed0 \\
        --mode koumyou-on --quantize 4bit --seed 0
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
sys.path.insert(0, str(REPO_ROOT / "src_min_eli3"))

import torch  # noqa: E402

from kojiki_lm.elixir_evaluator import ElixirEvaluator  # noqa: E402
from kojiki_lm.firewall_decoder import FirewallConfig, FirewallDecoder  # noqa: E402
from kojiki_lm.koumyou_so import KoumyouSo, KoumyouSoConfig  # noqa: E402
from kojiki_lm.qwen_adapter import QwenAdapter  # noqa: E402
from kojiki_lm.yomotsu_hirasaka import YomotsuHirasaka  # noqa: E402


logger = logging.getLogger(__name__)


# Elixir 関数本体内の trace コメント。2-space indent で MultiPL-E elixir prompt の
# `def foo(...) do\n` 直後に注入する想定。
TRACE_SEED = "  # 思考: "


# mode → (firewall_enabled, koumyou_enabled)
MODE_FLAGS = {
    "firewall-off": (False, False),
    "firewall-on":  (True,  False),
    "koumyou-on":   (True,  True),
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
    ap.add_argument("--mode", choices=list(MODE_FLAGS.keys()), default="koumyou-on")

    ap.add_argument("--model", default=str(REPO_ROOT / "models" / "Qwen2.5-Coder-7B-Instruct"))
    ap.add_argument("--quantize", choices=["4bit", "8bit", "none"], default="4bit")

    ap.add_argument("--max-new-tokens", type=int, default=256)
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--top-k", type=int, default=50)
    ap.add_argument("--top-p", type=float, default=0.95)
    ap.add_argument("--firewall-interval", type=int, default=16)
    ap.add_argument("--seed", type=int, default=0)

    # 光明想 (KoumyouSo) thresholds
    # default 1 line / 20 chars (2026-05-26 smoke 知見: Qwen は 1 行 comma-separated
    # 形式を好み、min_trace_lines=2 では over-rejection になる)
    ap.add_argument("--min-trace-lines", type=int, default=1,
                    help="`# 思考:` 行が最低この本数なければ HALT (mode=koumyou-on のみ有効)")
    ap.add_argument("--min-trace-chars", type=int, default=20,
                    help="trace 本文の合計文字数下限 (mode=koumyou-on のみ有効、主軸 gate)")
    ap.add_argument("--grace-period-chars", type=int, default=16,
                    help="generated text 長がこれ未満なら trace 判定保留 (HALT しない)")

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

    firewall_enabled, koumyou_enabled = MODE_FLAGS[args.mode]
    logger.info(
        "Mode=%s (firewall=%s, koumyou=%s)",
        args.mode, firewall_enabled, koumyou_enabled,
    )

    # 光明想 (None なら eli2 と同等動作)
    koumyou_so = None
    if koumyou_enabled:
        koumyou_so = KoumyouSo(KoumyouSoConfig(
            min_trace_lines=args.min_trace_lines,
            min_trace_chars=args.min_trace_chars,
            grace_period_chars=args.grace_period_chars,
            trace_seed=TRACE_SEED,
        ))
        logger.info(
            "KoumyouSo enabled: min_lines=%d, min_chars=%d, grace=%d, seed=%r",
            args.min_trace_lines, args.min_trace_chars, args.grace_period_chars,
            TRACE_SEED,
        )

    # backbone
    quantize = None if args.quantize == "none" else args.quantize
    logger.info("Loading backbone %s (quantize=%s)", args.model, quantize)
    backbone, tokenizer = QwenAdapter.load_base_model(
        model_name=args.model, quantize=quantize,
    )
    backbone.eval()

    firewall = YomotsuHirasaka(ElixirEvaluator(koumyou_so=koumyou_so))

    fw_cfg = FirewallConfig(
        max_new_tokens=args.max_new_tokens,
        firewall_interval=args.firewall_interval,
        temperature=args.temperature,
        do_sample=args.temperature > 0,
        top_k=args.top_k,
        top_p=args.top_p,
        firewall_enabled=firewall_enabled,
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
    n_trace_failure = 0
    t_total = 0.0

    for i, row in enumerate(rows):
        name = row["name"]
        out_path = out_dir / f"{name}__s0.json"
        if args.skip_existing and out_path.exists():
            n_skipped += 1
            continue

        prompt = row["prompt"]
        stop_tokens = list(row.get("stop_tokens") or [])

        # koumyou モードでは prompt 末尾に trace seed を注入。
        # この変更により、model の最初の生成 token は `# 思考: ` の続き = trace 本文となる。
        wrapped_prompt = prompt + TRACE_SEED if koumyou_enabled else prompt

        # prompt 単位の deterministic seed (eli2 と同じ式)
        fw_cfg.sampling_seed = args.seed * 1_000_003 + i

        t0 = time.time()
        result = decoder.generate(
            backbone, tokenizer, wrapped_prompt,
            prompt_id=name, stop_tokens=tuple(stop_tokens),
        )
        elapsed = time.time() - t0
        t_total += elapsed

        # 評価器のために completion を構築。koumyou モードでは TRACE_SEED を prepend して
        # `prompt + completion` が valid Elixir になるようにする。
        if koumyou_enabled:
            completion_raw = TRACE_SEED + result.text
        else:
            completion_raw = result.text
        completion = truncate_at_stop_tokens(completion_raw, stop_tokens)

        # トレース統計を最終 generated_text に対して計算。
        # KoumyouSo OFF の mode でも統計だけ取りたい場合に備えて、ad-hoc KoumyouSo を作る。
        trace_info = None
        if koumyou_so is not None:
            trace_v = koumyou_so.validate(result.text)
            trace_info = {
                "status": trace_v.status.value,
                "n_thought_lines": trace_v.n_thought_lines,
                "trace_body_chars": trace_v.trace_body_chars,
                "code_started": trace_v.code_started,
            }
            if trace_v.is_terminal_failure:
                n_trace_failure += 1

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
            # Firewall フィールド
            "firewall_mode": args.mode,
            "firewall_enabled": firewall_enabled,
            "koumyou_enabled": koumyou_enabled,
            "trace_seed": TRACE_SEED if koumyou_enabled else "",
            "total_step_count": len(result.steps),
            "halted_early": result.halted_early,
            "stopped_at_stop_token": result.stopped_at_stop_token,
            "final_verdict": (
                result.final_verdict.verdict.value if result.final_verdict else None
            ),
            "final_v_score": (
                result.final_verdict.v_score if result.final_verdict else None
            ),
            # 光明想フィールド
            "trace_info": trace_info,
        }, ensure_ascii=False))

        n_done += 1
        if result.halted_early:
            n_halted += 1
        logger.info(
            "[%d/%d] %s  %dc / steps=%d / verdict=%s / trace=%s / %.1fs",
            i + 1, len(rows), name,
            len(completion), len(result.steps),
            (result.final_verdict.verdict.value if result.final_verdict else "-"),
            (trace_info["status"] if trace_info else "-"),
            elapsed,
        )

    avg = t_total / max(n_done, 1)
    logger.info(
        "Done: generated=%d, skipped=%d, halted_early=%d, "
        "trace_failure=%d, avg=%.1fs/q, total=%.0fs",
        n_done, n_skipped, n_halted, n_trace_failure, avg, t_total,
    )


if __name__ == "__main__":
    main()
