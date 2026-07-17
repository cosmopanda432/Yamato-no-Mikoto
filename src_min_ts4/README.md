# src_min_eli4

**eli3 完全 copy + 產屋 (REPAIR) 統合実装** (2026-07-03〜)。
本設計書: `data/kojiki/設計書/eli4_実装設計書_v0.md`

## eli3 との差分表 (Step A-E 完了)

`src_min_eli3/` の完全 copy (`__pycache__/` 除外) をベースに、產屋 (REPAIR) を Step A-E
で積み上げた。`diff -rq src_min_eli3 src_min_eli4` で確認できる差分は以下の通り。

| ファイル | 差分 | Step |
|---|---|---|
| `kojiki_lm/ashibune.py` | **新規**。葦船 — 棄却 attempt を理由コード付きで JSONL 永続化する rejected sample log (`AshibuneRecord`/`AshibuneLog`) | A |
| `kojiki_lm/yomotsu_hirasaka.py` | `ReasonCode` enum ( `trace_missing`/`trace_insufficient`/`bracket_mismatch`/`do_end_mismatch`/`bad_pattern`/`low_score`/`undef_symbol` ) を新設し、`L5ToL3Verdict` に `reason_code`・`hint` (≤200 文字) を default 付きで追加 (事戸拡張、後方互換) | B |
| `kojiki_lm/elixir_evaluator.py` | `_compute_v_score` の数値計算はそのまま (`_compute_score_and_flags` に一本化) しつつ検出フラグを追加し、`__call__` が `reason_code` を優先順位 (`TRACE_MISSING`/`TRACE_INSUFFICIENT` > `BRACKET_MISMATCH` > `DO_END_MISMATCH` > `BAD_PATTERN` > `LOW_SCORE`) で `L5ToL3Verdict` に付与するよう拡張 | B |

新規スクリプト (`src_min_eli4/` 外だが產屋の一部):

| ファイル | 内容 | Step |
|---|---|---|
| `scripts/eval/run_yamato_min_elixir4.py` | 還降 (再生成) loop runner。`--mode repair-on` で HALT/REPAIR 時に `reason_code`/`hint` を prompt に注入して再試行し、全 attempt を `ashibune.jsonl` に記録 | C |
| `scripts/eval/elixir_eval.py` | 既存の post-hoc 評価に additive 拡張 (`undef_symbols`/`did_you_mean`/`hack_gap` 指標を追加、既存出力は不変) | D |
| `scripts/eval/judge_win_condition_elixir.py` | `--mode repair-on` を追加し、二段階警報 (pass@1 低下と手抜き率上昇を別々に検知) で勝敗判定 | E |
| `scripts/runpod_bench_eli4.sh` | eli4 (repair-on) 用の RunPod ベンチ実行スクリプト | C |
| `tests_eli4/` | Step A-E の単体テスト (`test_ashibune.py`/`test_yomotsu_reason_code.py`/`test_elixir_eval_undef.py`/`test_repair_runner.py`/`test_judge_repair_on.py`) | A-E |

eli3 は **一切変更していない** (`feedback-prove-and-handoff` の保全方針を継承)。

## 関連文書

- `src_min_eli3/README.md`: eli3 の構成、eli2 との差分、光明想 (KoumyouSo) の設計
- `data/kojiki/設計書/eli4_実装設計書_v0.md`: 本実装の設計原理・Step A-E の DoD・禁止事項
