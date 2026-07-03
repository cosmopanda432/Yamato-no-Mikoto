"""raw_completion field を任意の 2 生成 out_dir 間で突き合わせる最小 diff tool。

Step C (產屋 還降 loop) の DoD-C-1 用: `run_yamato_min_elixir4.py --mode repair-on
--max-rounds 0` の `round_0/` 出力が eli3 `--mode koumyou-on` の出力と
raw_completion 全一致であることを確認する (round 0 byte-identity、§5.2 統制条件)。

`diff_smoke_outputs.py` は修正D検証用の --vanilla/--no-kotodama という固有命名
CLI で、halted サンプルを既定で除外する等この用途には過剰・不整合なため、
任意の 2 dir を「全サンプル・raw_completion のみ」で比較する薄いラッパーを別途用意する。

使い方:
    python3 scripts/eval/diff_raw_completions.py \\
        --dir-a data/eval/generated/humaneval-elixir.yamato_min_elixir4.repair-on.seed0/round_0 \\
        --dir-b data/eval/generated/humaneval-elixir.yamato_min_elixir3.koumyou-on.seed0

終了コード: 全一致なら 0、1 件でも diff があれば 1。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_raw_completions(gen_dir: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in sorted(gen_dir.glob("*__s0.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        out[data["name"]] = data.get("raw_completion", "")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir-a", required=True, type=Path)
    ap.add_argument("--dir-b", required=True, type=Path)
    args = ap.parse_args()

    a = load_raw_completions(args.dir_a)
    b = load_raw_completions(args.dir_b)
    names = sorted(set(a) & set(b))
    if not names:
        raise SystemExit(f"no overlapping samples between {args.dir_a} and {args.dir_b}")

    diffs = [n for n in names if a[n] != b[n]]
    print(f"compared={len(names)} identical={len(names) - len(diffs)} diffs={len(diffs)}")
    for n in diffs[:10]:
        idx = next(
            (i for i, (x, y) in enumerate(zip(a[n], b[n])) if x != y),
            min(len(a[n]), len(b[n])),
        )
        print(f"  DIFF {n}: first_diff_at={idx} len_a={len(a[n])} len_b={len(b[n])}")

    if diffs:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
