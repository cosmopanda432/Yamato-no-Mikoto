"""修正 D (Generator 分離) のスモーク検証スクリプト。

2 つの生成ディレクトリ (vanilla / no-kotodama) を読み込み、prompt ごとに
`completion` フィールドの byte-identical 率を集計する。

期待:
  vanilla ↔ no-kotodama : N/N 完全一致 (修正 D の Generator 分離)
                          ※ HALT が発火した prompt は除外して集計

オプション --baseline で baseline 生成 dir も指定すると、修正 A の sampler 等価性
(baseline ↔ vanilla) も一緒に集計する。baseline は通常事前保存しておく
(scripts/runpod_bench.sh からは自動生成しない)。

最低限の出力例:
    [pair=vanilla-no-kotodama]   identical=10/10 (100.0%)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_outputs(gen_dir: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in sorted(gen_dir.glob("*__s0.json")):
        # Windows のデフォルト encoding (cp932) では Go source の特殊文字で fail する
        data = json.loads(p.read_text(encoding="utf-8"))
        out[data["name"]] = data
    return out


def compare(label: str, left: dict[str, dict], right: dict[str, dict],
            exclude_halted: bool, field: str = "completion") -> None:
    """left/right の指定 field (completion or raw_completion) を per-prompt 比較。

    Firewall 隔離テストの strict 判定には field="raw_completion" を使う。
    stop_tokens 後の truncate を経ない生の生成テキストで比較するため、
    L3↔L5 干渉が generation のあらゆる step で起きていないかを検出できる。"""
    names = sorted(set(left) & set(right))
    if not names:
        print(f"[pair={label}] no overlap")
        return
    skipped_halt = 0
    identical = 0
    diffs: list[str] = []
    for name in names:
        l_data = left[name]
        r_data = right[name]
        if exclude_halted and (
            l_data.get("halted_early") or r_data.get("halted_early")
        ):
            skipped_halt += 1
            continue
        if l_data.get(field) == r_data.get(field):
            identical += 1
        else:
            diffs.append(name)
    total = len(names) - skipped_halt
    pct = 100.0 * identical / total if total else 0.0
    skip_note = f", halted-skipped={skipped_halt}" if exclude_halted else ""
    print(f"[pair={label}, field={field}]  identical={identical}/{total} "
          f"({pct:.1f}%){skip_note}")
    for name in diffs[:5]:
        l_c = left[name].get(field, "")
        r_c = right[name].get(field, "")
        # 最初の差分 char index を簡易表示
        idx = next((i for i, (a, b) in enumerate(zip(l_c, r_c)) if a != b),
                   min(len(l_c), len(r_c)))
        print(f"    diff: {name}  first_diff_at={idx} "
              f"(left_len={len(l_c)}, right_len={len(r_c)})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vanilla", required=True, type=Path)
    ap.add_argument("--no-kotodama", required=True, type=Path)
    ap.add_argument("--baseline", type=Path, default=None,
                    help="任意。指定すると修正 A の sampler 等価性も集計する")
    args = ap.parse_args()

    vanilla = load_outputs(args.vanilla)
    no_koto = load_outputs(getattr(args, "no_kotodama"))
    baseline = load_outputs(args.baseline) if args.baseline else {}

    print(f"loaded: vanilla={len(vanilla)}  no-kotodama={len(no_koto)}  "
          f"baseline={len(baseline)}")

    # 修正 D / Firewall 隔離検証: vanilla vs no-kotodama
    # completion (post-truncate) と raw_completion (生の生成) の両方を見る。
    # raw_completion が完全一致なら、全 step で L3↔L5 干渉なし = 隔離壁完成。
    # completion だけ一致なら、stop_tokens 後の test driver 領域でだけ差がある状態
    # (Firewall 隔離としては十分、機能的にも問題なし)。
    compare("vanilla-no-kotodama", vanilla, no_koto, exclude_halted=True,
            field="completion")
    compare("vanilla-no-kotodama", vanilla, no_koto, exclude_halted=True,
            field="raw_completion")

    # 修正 A 検証 (任意): baseline vs vanilla。HALT は baseline 側にないので除外不要
    if baseline:
        compare("baseline-vanilla", baseline, vanilla, exclude_halted=False,
                field="completion")


if __name__ == "__main__":
    main()
