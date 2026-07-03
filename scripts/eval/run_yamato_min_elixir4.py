"""
yamatoLLM Elixir target e2e 生成スクリプト — src_min_eli4 (產屋 REPAIR 統合版)

`run_yamato_min_elixir3.py` (光明想統合版) を出発点にした copy。既存 3 mode
(`firewall-off` / `firewall-on` / `koumyou-on`) は挙動を一切変えず残し、
新 mode `repair-on` (koumyou-on の全設定 + round 型 REPAIR) を追加する。

產屋 (ubuya) REPAIR とは:
  round 0 (初回生成、koumyou-on と byte-identical) の後、test_ok == False の
  sample だけを対象に「先頭からの全再生成」を最大 `--max-rounds` 回まで繰り返す
  (生成済みテキストの部分書き換えは禁止 — 還降 = 全再生成のみ)。
  各 attempt は葦船 (`kojiki_lm.ashibune`) に全件記録される。

seed 規則 (§5.2 統制条件):
    BASE = args.seed * 1_000_003 + i          # round 0。eli3 と完全同値
    R_STRIDE = 999_999_937                    # 大素数。round 衝突回避
    seed(i, r) = BASE + r * R_STRIDE          # round r >= 1

round 0 の生成は eli3 koumyou-on と byte-identical でなければならない
(repair の marginal effect を測る ablation の統制条件)。このため round 0 の
生成コードは eli3 runner と同一の式・同一の呼び出し順序を保つ。

使い方:
    python3 scripts/eval/run_yamato_min_elixir4.py \\
        --input data/raw/multipl_e/humaneval-elixir/test-00000-of-00001.parquet \\
        --out-dir data/eval/generated/humaneval-elixir.yamato_min_elixir4.repair-on.seed0 \\
        --mode repair-on --quantize 4bit --seed 0 --max-rounds 2
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "src_min_eli4"))
# elixir_eval.py は本スクリプトと同 dir にある (§5.3: "同 dir import")。
# `python3 scripts/eval/run_yamato_min_elixir4.py` として実行する場合は Python が
# 自動でスクリプトの dir を sys.path[0] に入れるが、importlib 経由 (unit test) で
# 読み込む場合はそれが起きないため、明示的に insert しておく。
sys.path.insert(0, str(SCRIPT_DIR))

import torch  # noqa: E402

from elixir_eval import run_one  # noqa: E402

from kojiki_lm.ashibune import AshibuneLog, AshibuneRecord  # noqa: E402
from kojiki_lm.elixir_evaluator import ElixirEvaluator  # noqa: E402
from kojiki_lm.firewall_decoder import FirewallConfig, FirewallDecoder  # noqa: E402
from kojiki_lm.koumyou_so import KoumyouSo, KoumyouSoConfig  # noqa: E402
from kojiki_lm.qwen_adapter import QwenAdapter  # noqa: E402
from kojiki_lm.yomotsu_hirasaka import ReasonCode, YomotsuHirasaka  # noqa: E402


logger = logging.getLogger(__name__)


# Elixir 関数本体内の trace コメント。eli3 と完全同値でなければならない
# (round 0 byte-identity の前提)。
TRACE_SEED = "  # 思考: "


# round 間の sampling_seed 衝突を避けるための大素数 stride (§5.2)。
R_STRIDE = 999_999_937


# mode → (firewall_enabled, koumyou_enabled)
# repair-on は koumyou-on と全く同じ Firewall/KoumyouSo 設定で走る
# (round 型 REPAIR のみが追加差分)。
MODE_FLAGS = {
    "firewall-off": (False, False),
    "firewall-on":  (True,  False),
    "koumyou-on":   (True,  True),
    "repair-on":    (True,  True),
}


def truncate_at_stop_tokens(text: str, stop_tokens) -> str:
    cut = len(text)
    for st in stop_tokens or []:
        idx = text.find(st)
        if 0 <= idx < cut:
            cut = idx
    return text[:cut]


# ---------------------------------------------------------------------------
# 純粋関数 (unit test 対象)
# ---------------------------------------------------------------------------


def attempt_seed(base_seed: int, i: int, r: int) -> int:
    """(base_seed, prompt index, round) から deterministic な sampling seed を導出する。

    round 0: `base_seed * 1_000_003 + i` (eli3 run_yamato_min_elixir3.py の
    `fw_cfg.sampling_seed = args.seed * 1_000_003 + i` と完全同値であること — §5.2
    の統制条件)。
    round r >= 1: 上記 + `r * R_STRIDE` (大素数 stride で round 間の衝突を回避)。
    """
    return base_seed * 1_000_003 + i + r * R_STRIDE


def build_hint_line(hint: str) -> str:
    """hint 文字列から prompt に挿入する 1 行を組み立てる。hint == "" なら空文字列。"""
    return f"  # 補足: {hint}\n" if hint else ""


def build_wrapped_prompt(prompt: str, hint: str, koumyou_enabled: bool) -> str:
    """round >= 1 (退避 retry) の wrapped prompt を組み立てる (§5.3)。

    `wrapped_prompt = prompt + hint_line + TRACE_SEED`。

    如先 (前例踏襲):
      - hint == "" のとき、round 0 の式 (`prompt + TRACE_SEED`) と byte 一致する。
      - hint != "" のとき、round 0 との差分は挿入された hint_line 1 行のみ
        (§8-7: hint 以外の prompt 差分を作らない)。
    """
    base = prompt + build_hint_line(hint)
    return base + TRACE_SEED if koumyou_enabled else base


def build_hint(eval_result: dict) -> str:
    """前 round の評価結果から retry hint 文字列を組み立てる。

    Step D (次 task) が処方規則本体を実装する。現時点では常に "" を返す
    (= repair round は「無 hint 再試行」のみ行う。--temperature 0 (greedy) の
    場合は §5.3 の `if hint == "" and not do_sample: skip` により実質 retry しない)。

    TODO(Step D): 処方規則を実装
    """
    return ""


def resolve_reason_code(final_verdict, eval_res: dict) -> str:
    """in-loop evaluator の verdict と post-hoc (`elixir_eval.run_one`) の結果を
    統合し、機械可読な reason_code 文字列を 1 つ返す。

    優先順位:
      1. in-loop evaluator が HALT/REPAIR で reason_code を立てていればそれを使う
         (TRACE_MISSING / BRACKET_MISMATCH / ... — ReasonCode.NONE 以外)
      2. post-hoc eval が UndefinedFunctionError 系を検出していれば UNDEF_SYMBOL
         (in-loop evaluator は絶対に発行しない post-hoc 専用 reason)
      3. どちらも該当なければ NONE (compile は通ったが assertion 不合格、等)
    """
    if final_verdict is not None and final_verdict.reason_code is not ReasonCode.NONE:
        return final_verdict.reason_code.value
    if eval_res.get("has_undefined"):
        return ReasonCode.UNDEF_SYMBOL.value
    return ReasonCode.NONE.value


def resolve_elixir_bin(elixir_bin_arg: str | None) -> str:
    """--elixir-bin か PATH 検索で elixir 実行ファイルを解決する。

    repair-on は生成 host で round 内 post-hoc eval (`elixir <file>`) を回すため
    elixir が必須。見つからなければ起動直後 (モデルロード前) に fail-fast する。
    """
    resolved = elixir_bin_arg or shutil.which("elixir")
    if not resolved:
        raise SystemExit(
            "repair-on mode には生成 host に elixir が必要です "
            '(shutil.which("elixir") が見つかりませんでした)。'
            "PATH に無ければ --elixir-bin で明示的にパスを指定してください。"
        )
    return resolved


def build_repair_summary(attempts_by_name: dict[str, list[dict]], max_rounds: int) -> dict:
    """`_repair_summary.json` の中身を合成する純粋関数。

    `attempts_by_name`: prompt 名 -> その prompt の全 attempt (round 昇順) のリスト。
    各 attempt dict は少なくとも `round` (int) / `test_ok` (bool|None) /
    `repair_reason` (str) キーを持つことを期待する (round >= 1 の attempt のみ
    `repair_reason` を集計対象にする)。
    """
    n_prompts = len(attempts_by_name)
    per_round_pass = [0] * (max_rounds + 1)
    n_recovered = 0
    total_attempts = 0
    hints_used: dict[str, int] = {}

    for attempts in attempts_by_name.values():
        total_attempts += len(attempts)
        for a in attempts:
            r = a["round"]
            if a.get("test_ok") and 0 <= r < len(per_round_pass):
                per_round_pass[r] += 1
            if r >= 1:
                reason = a.get("repair_reason") or "none"
                hints_used[reason] = hints_used.get(reason, 0) + 1

        if attempts:
            final = attempts[-1]
            if final.get("test_ok") and final.get("round", 0) >= 1:
                n_recovered += 1

    avg_attempts = (total_attempts / n_prompts) if n_prompts else 0.0

    return {
        "n_prompts": n_prompts,
        "max_rounds": max_rounds,
        "per_round_pass": per_round_pass,
        "n_recovered": n_recovered,
        "avg_attempts": avg_attempts,
        "hints_used": hints_used,
    }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    ap.add_argument("--min-trace-lines", type=int, default=1,
                    help="`# 思考:` 行が最低この本数なければ HALT (mode=koumyou-on/repair-on のみ有効)")
    ap.add_argument("--min-trace-chars", type=int, default=20,
                    help="trace 本文の合計文字数下限 (mode=koumyou-on/repair-on のみ有効、主軸 gate)")
    ap.add_argument("--grace-period-chars", type=int, default=16,
                    help="generated text 長がこれ未満なら trace 判定保留 (HALT しない)")

    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--skip-existing", action="store_true")

    # 產屋 REPAIR (mode=repair-on 専用、§5.1)
    ap.add_argument("--max-rounds", type=int, default=2,
                    help="round 0 (初回) の後に許す repair round 数 (mode=repair-on のみ有効)")
    ap.add_argument("--eval-timeout", type=float, default=5.0,
                    help="round 内 post-hoc eval (elixir subprocess) の 1 サンプルあたり timeout 秒")
    ap.add_argument("--elixir-bin", default=None,
                    help="elixir CLI へのパス。デフォルト: PATH から検索 "
                         "(mode=repair-on は起動直後に fail-fast する)")
    return ap.parse_args()


# ---------------------------------------------------------------------------
# 既存 3 mode (firewall-off / firewall-on / koumyou-on): eli3 と挙動を変えない
# ---------------------------------------------------------------------------


def _run_single_pass(args, rows, decoder, fw_cfg, backbone, tokenizer, out_dir,
                      firewall_enabled, koumyou_enabled, koumyou_so):
    """eli3 runner の main loop と完全に同一の順序・同一の式 (§5.2 統制条件)。"""
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
        wrapped_prompt = prompt + TRACE_SEED if koumyou_enabled else prompt

        # prompt 単位の deterministic seed (eli2/eli3 と同じ式)
        fw_cfg.sampling_seed = args.seed * 1_000_003 + i

        t0 = time.time()
        result = decoder.generate(
            backbone, tokenizer, wrapped_prompt,
            prompt_id=name, stop_tokens=tuple(stop_tokens),
        )
        elapsed = time.time() - t0
        t_total += elapsed

        if koumyou_enabled:
            completion_raw = TRACE_SEED + result.text
        else:
            completion_raw = result.text
        completion = truncate_at_stop_tokens(completion_raw, stop_tokens)

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


# ---------------------------------------------------------------------------
# repair-on: 產屋 還降 loop (§5.3)
# ---------------------------------------------------------------------------


def _finish_attempt(*, args, name, round_, hint, repair_reason, prompt, tests,
                     stop_tokens, completion, raw_completion, seed_used, elapsed,
                     result, trace_info, firewall_enabled, elixir_bin, eval_timeout) -> dict:
    """1 attempt の生成結果を post-hoc eval (`elixir_eval.run_one`) にかけ、
    ashibune 記録・最終回答 JSON の両方に必要な情報をまとめた dict を返す。"""
    final_verdict = result.final_verdict

    sample_for_eval = {
        "name": name,
        "seed": seed_used,
        "prompt": prompt,
        "completion": completion,
        "tests": tests,
    }
    eval_res = run_one(sample_for_eval, elixir_bin=elixir_bin, timeout=eval_timeout)

    reason_code = resolve_reason_code(final_verdict, eval_res)

    return {
        "name": name,
        "round": round_,
        "hint": hint,
        "repair_reason": repair_reason,
        "prompt": prompt,
        "tests": tests,
        "stop_tokens": stop_tokens,
        "completion": completion,
        "raw_completion": raw_completion,
        "seed_used": seed_used,
        "elapsed_sec": elapsed,
        "firewall_enabled": firewall_enabled,
        "total_step_count": len(result.steps),
        "halted_early": result.halted_early,
        "stopped_at_stop_token": result.stopped_at_stop_token,
        "final_verdict": final_verdict.verdict.value if final_verdict else None,
        "v_score": final_verdict.v_score if final_verdict else None,
        "hint_from_verdict": final_verdict.hint if final_verdict else "",
        "trace_info": trace_info,
        "test_ok": eval_res["test_ok"],
        "has_undefined": eval_res["has_undefined"],
        "exit_code": eval_res["exit_code"],
        "test_stderr": eval_res["test_stderr"],
        "reason_code": reason_code,
        "accepted": False,
        "is_final_answer": False,
    }


def _write_round_sample_json(round_dir: Path, attempt: dict, args, koumyou_enabled: bool) -> None:
    out_path = round_dir / f"{attempt['name']}__s0.json"
    out_path.write_text(json.dumps({
        "name": attempt["name"],
        "sample_id": 0,
        "seed": attempt["seed_used"],
        "prompt": attempt["prompt"],
        "completion": attempt["completion"],
        "raw_completion": attempt["raw_completion"],
        "tests": attempt["tests"],
        "stop_tokens": attempt["stop_tokens"],
        "model": args.model,
        "quantize": args.quantize,
        "temperature": args.temperature,
        "elapsed_sec": attempt["elapsed_sec"],
        "language": "elixir",
        "firewall_mode": args.mode,
        "firewall_enabled": attempt["firewall_enabled"],
        "koumyou_enabled": koumyou_enabled,
        "trace_seed": TRACE_SEED if koumyou_enabled else "",
        "total_step_count": attempt["total_step_count"],
        "halted_early": attempt["halted_early"],
        "stopped_at_stop_token": attempt["stopped_at_stop_token"],
        "final_verdict": attempt["final_verdict"],
        "final_v_score": attempt["v_score"],
        "trace_info": attempt["trace_info"],
        # 產屋 REPAIR 追加 field
        "round": attempt["round"],
        "hint": attempt["hint"],
    }, ensure_ascii=False))


def _run_repair_loop(args, rows, decoder, fw_cfg, backbone, tokenizer, out_dir,
                      firewall_enabled, koumyou_enabled, koumyou_so, elixir_bin):
    ashibune_log = AshibuneLog(out_dir / "ashibune.jsonl")
    attempts_by_name: dict[str, list[dict]] = {}
    prompts_by_name: dict[str, dict] = {}
    name_to_index: dict[str, int] = {}

    round0_dir = out_dir / "round_0"
    round0_dir.mkdir(parents=True, exist_ok=True)

    logger.info("repair-on round 0: generating %d prompts (koumyou-on と同一設定)", len(rows))

    for i, row in enumerate(rows):
        name = row["name"]
        prompt = row["prompt"]
        stop_tokens = list(row.get("stop_tokens") or [])
        prompts_by_name[name] = row
        name_to_index[name] = i

        # round 0 の生成は koumyou-on と byte-identical でなければならない
        # (§5.2 統制条件、eli3 と完全同一の式)。
        wrapped_prompt = prompt + TRACE_SEED if koumyou_enabled else prompt
        fw_cfg.sampling_seed = attempt_seed(args.seed, i, 0)

        t0 = time.time()
        result = decoder.generate(
            backbone, tokenizer, wrapped_prompt,
            prompt_id=name, stop_tokens=tuple(stop_tokens),
        )
        elapsed = time.time() - t0

        if koumyou_enabled:
            completion_raw = TRACE_SEED + result.text
        else:
            completion_raw = result.text
        completion = truncate_at_stop_tokens(completion_raw, stop_tokens)

        trace_info = None
        if koumyou_so is not None:
            trace_v = koumyou_so.validate(result.text)
            trace_info = {
                "status": trace_v.status.value,
                "n_thought_lines": trace_v.n_thought_lines,
                "trace_body_chars": trace_v.trace_body_chars,
                "code_started": trace_v.code_started,
            }

        attempt = _finish_attempt(
            args=args, name=name, round_=0, hint="", repair_reason="",
            prompt=prompt, tests=row["tests"], stop_tokens=stop_tokens,
            completion=completion, raw_completion=result.text,
            seed_used=fw_cfg.sampling_seed, elapsed=elapsed,
            result=result, trace_info=trace_info,
            firewall_enabled=firewall_enabled,
            elixir_bin=elixir_bin, eval_timeout=args.eval_timeout,
        )
        attempts_by_name[name] = [attempt]
        _write_round_sample_json(round0_dir, attempt, args, koumyou_enabled)

        logger.info(
            "[round0 %d/%d] %s test_ok=%s verdict=%s reason=%s",
            i + 1, len(rows), name, attempt["test_ok"],
            attempt["final_verdict"], attempt["reason_code"],
        )

    # --- repair rounds (§5.3) ------------------------------------------------
    for r in range(1, args.max_rounds + 1):
        fail_names = [
            name for name, atts in attempts_by_name.items() if not atts[-1]["test_ok"]
        ]
        if not fail_names:
            logger.info("round %d: no failing sample remains, stop repair loop", r)
            break

        round_dir = out_dir / f"round_{r}"
        round_dir.mkdir(parents=True, exist_ok=True)
        logger.info("round %d: %d failing sample(s)", r, len(fail_names))

        for name in fail_names:
            i = name_to_index[name]
            row = prompts_by_name[name]
            prompt = row["prompt"]
            stop_tokens = list(row.get("stop_tokens") or [])
            prev_attempt = attempts_by_name[name][-1]

            eval_result = {
                "reason_code": prev_attempt["reason_code"],
                "test_ok": prev_attempt["test_ok"],
                "has_undefined": prev_attempt["has_undefined"],
                "test_stderr": prev_attempt["test_stderr"],
                "hint_from_verdict": prev_attempt["hint_from_verdict"],
                "exit_code": prev_attempt["exit_code"],
            }
            hint = build_hint(eval_result)

            if hint == "" and not fw_cfg.do_sample:
                # greedy では無 hint 再試行は無意味 (§5.3)
                continue

            wrapped_prompt = build_wrapped_prompt(prompt, hint, koumyou_enabled)
            fw_cfg.sampling_seed = attempt_seed(args.seed, i, r)

            t0 = time.time()
            result = decoder.generate(
                backbone, tokenizer, wrapped_prompt,
                prompt_id=name, stop_tokens=tuple(stop_tokens),
            )
            elapsed = time.time() - t0

            hint_line = build_hint_line(hint)
            body_truncated = truncate_at_stop_tokens(result.text, stop_tokens)
            if koumyou_enabled:
                completion = hint_line + TRACE_SEED + body_truncated
            else:
                completion = hint_line + body_truncated

            trace_info = None
            if koumyou_so is not None:
                trace_v = koumyou_so.validate(result.text)
                trace_info = {
                    "status": trace_v.status.value,
                    "n_thought_lines": trace_v.n_thought_lines,
                    "trace_body_chars": trace_v.trace_body_chars,
                    "code_started": trace_v.code_started,
                }

            attempt = _finish_attempt(
                args=args, name=name, round_=r, hint=hint,
                repair_reason=prev_attempt["reason_code"],
                prompt=prompt, tests=row["tests"], stop_tokens=stop_tokens,
                completion=completion, raw_completion=result.text,
                seed_used=fw_cfg.sampling_seed, elapsed=elapsed,
                result=result, trace_info=trace_info,
                firewall_enabled=firewall_enabled,
                elixir_bin=elixir_bin, eval_timeout=args.eval_timeout,
            )
            attempts_by_name[name].append(attempt)
            _write_round_sample_json(round_dir, attempt, args, koumyou_enabled)

            logger.info(
                "[round%d] %s test_ok=%s verdict=%s reason=%s (repair_reason=%s)",
                r, name, attempt["test_ok"], attempt["final_verdict"],
                attempt["reason_code"], attempt["repair_reason"],
            )

    # --- finalize: 最終回答 = 「最初に test_ok になった attempt」、
    #     無ければ最終 round の attempt (§5.3) ------------------------------
    for attempts in attempts_by_name.values():
        final = attempts[-1]
        final["accepted"] = True
        final["is_final_answer"] = True

    for name, attempts in attempts_by_name.items():
        for a in attempts:
            ashibune_log.append(AshibuneRecord(
                ts=_now_iso(),
                prompt_id=name,
                mode=args.mode,
                round=a["round"],
                seed_used=a["seed_used"],
                verdict=a["final_verdict"],
                v_score=a["v_score"],
                reason_code=a["reason_code"],
                hint_used=a["hint"],
                halted_early=a["halted_early"],
                stopped_at_stop_token=a["stopped_at_stop_token"],
                test_ok=a["test_ok"],
                has_undefined=a["has_undefined"],
                exit_code=a["exit_code"],
                completion_chars=len(a["completion"]),
                raw_completion=a["raw_completion"],
                accepted=a["accepted"],
                is_final_answer=a["is_final_answer"],
            ))

        final = attempts[-1]
        row = prompts_by_name[name]
        final_path = out_dir / f"{name}__s0.json"
        final_path.write_text(json.dumps({
            "name": name,
            "sample_id": 0,
            "seed": args.seed,
            "prompt": final["prompt"],
            "completion": final["completion"],
            "raw_completion": final["raw_completion"],
            "tests": row["tests"],
            "stop_tokens": final["stop_tokens"],
            "model": args.model,
            "quantize": args.quantize,
            "temperature": args.temperature,
            "elapsed_sec": final["elapsed_sec"],
            "language": "elixir",
            "firewall_mode": args.mode,
            "firewall_enabled": final["firewall_enabled"],
            "koumyou_enabled": koumyou_enabled,
            "trace_seed": TRACE_SEED if koumyou_enabled else "",
            "total_step_count": final["total_step_count"],
            "halted_early": final["halted_early"],
            "stopped_at_stop_token": final["stopped_at_stop_token"],
            "final_verdict": final["final_verdict"],
            "final_v_score": final["v_score"],
            "trace_info": final["trace_info"],
            # 產屋 REPAIR 追加 field (§5.3)
            "round": final["round"],
            "hint": final["hint"],
            "n_attempts": len(attempts),
            "repair_reason": final["repair_reason"],
        }, ensure_ascii=False))

    summary = build_repair_summary(attempts_by_name, args.max_rounds)
    (out_dir / "_repair_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2)
    )
    logger.info("repair-on done: %s", summary)


def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    is_repair = args.mode == "repair-on"
    elixir_bin = None
    if is_repair:
        # repair-on は生成 host に elixir が必須。モデルロード前 (起動直後) に
        # fail-fast する。
        elixir_bin = resolve_elixir_bin(args.elixir_bin)
        logger.info("repair-on: elixir_bin=%s", elixir_bin)

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

    if not is_repair:
        _run_single_pass(
            args, rows, decoder, fw_cfg, backbone, tokenizer, out_dir,
            firewall_enabled, koumyou_enabled, koumyou_so,
        )
        return

    _run_repair_loop(
        args, rows, decoder, fw_cfg, backbone, tokenizer, out_dir,
        firewall_enabled, koumyou_enabled, koumyou_so, elixir_bin,
    )


if __name__ == "__main__":
    main()
