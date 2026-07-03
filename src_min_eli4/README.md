# src_min_eli4

**eli3 完全 copy + 產屋 (REPAIR) 統合実装** (2026-07-03〜)。
本設計書: `data/kojiki/設計書/eli4_実装設計書_v0.md`

## 現状 (Step 0)

このディレクトリは `src_min_eli3/` を `__pycache__/` 除外で丸ごと copy したものであり、
現時点では README.md 以外に eli3 との差分は無い。Step A-E の実装が進むにつれて、下記の
差分表を随時更新する。

## eli3 との差分表 (Step A-E 完了後に最終化)

> 以下は現時点で計画されている差分の見取り図であり、実装が進むにつれて内容・行数・
> ファイル名は変わりうる。最終版は Step A-E 完了後にこの節を書き換える。

| ファイル | 差分 (計画) | 状態 |
|---|---|---|
| `kojiki_lm/ashibune.py` | **新規**。產屋 (REPAIR) 本体 — 還降 (再生成) 機構 | 未着手 |
| `kojiki_lm/yomotsu_hirasaka.py` | 拡張 (REPAIR 経路対応) | 未着手 (eli3 と同一) |
| `kojiki_lm/elixir_evaluator.py` | 拡張 (REPAIR 経路対応) | 未着手 (eli3 と同一) |
| `scripts/eval/run_yamato_min_elixir4.py` | **新規** runner (Step C) | 未着手 |

## 関連文書

- `src_min_eli3/README.md`: eli3 の構成、eli2 との差分、光明想 (KoumyouSo) の設計
- `data/kojiki/設計書/eli4_実装設計書_v0.md`: 本実装の設計原理・Step A-E の DoD・禁止事項
