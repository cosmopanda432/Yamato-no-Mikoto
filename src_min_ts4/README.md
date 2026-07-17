# src_min_ts4

**eli4 (`src_min_eli4/`) 同型スタックの TypeScript 移植** (2026-07-17〜)。
本設計書: `data/kojiki/設計書/ts4_実装設計書_v0.md`

目的: eli4 の firewall + 光明想 (KoumyouSo) + 產屋 (REPAIR) ループを人気言語 TypeScript
(humaneval-ts, MultiPL-E) で再現し、4 mode (`firewall-off` / `firewall-on` / `koumyou-on` /
`repair-on`) の ablation データを取る。「還降の効果は Elixir 固有か言語横断か」に答える
ための比較対象。**数値の勝敗 (Win Condition) はゲートにしない** (judge は情報として実行する)。

## eli4 との差分表

`src_min_eli4/` の完全 copy から出発し、以下だけ差し替えた (eli2→eli3→eli4→ts4 と同じ
copy-based 変異体方式。共有コードで ablation を汚さない)。

| ファイル | 扱い |
|---|---|
| `yomotsu_hirasaka.py` `firewall_decoder.py` `ashibune.py` `yamato_config.py` `yamato_model.py` `yamato_qwen.py` `qwen_adapter.py` `kenpou/` `yomi/` | **verbatim** (言語非依存) |
| `koumyou_so.py` | trace コメント prefix を `# 思考:` → `// 思考:` に変更 (`THOUGHT_MARKER`、検出 regex とも)。行数/文字数閾値・`TraceStatus` の意味論は不変 |
| `elixir_evaluator.py` → `ts_evaluator.py` | in-loop heuristic 評価器の TS 語彙版。クラス名 `ElixirEvaluator` → `TsEvaluator`。スコア計算の骨格 (0.5 起点・keyword +0.05/hit・bad pattern −0.10・bracket 不一致 −0.20・commit≥0.7/halt<0.3) は 1 bit も変えていない。`do`/`end` 収支チェックは TS に存在しないため削除し bracket 収支に一本化 (`ReasonCode.DO_END_MISMATCH` は dead code として残置) |
| `data.py` | ほぼ verbatim (MultiPL-E parquet schema は言語共通) |

新規スクリプト (`src_min_ts4/` 外だが ts4 移植の一部、いずれも eli4 対応物の copy + 適応):

| ファイル | 出発点 | 内容 |
|---|---|---|
| `scripts/eval/run_yamato_min_ts4.py` | `run_yamato_min_elixir4.py` | 還降 (再生成) loop runner。TRACE_SEED を `// 思考: ` 形式に、in-loop post-hoc eval の import を `ts_eval` に、`resolve_elixir_bin` を `resolve_tsc_bin`/`resolve_node_bin` に (repair-on は生成 host に tsc+node 必須で fail-fast)。`build_hint` を tsc 診断ベース (undefined/syntax_error/type_error の 3 分岐) に拡張 — eli4 は undef_symbol のみの stub だった |
| `scripts/eval/ts_eval.py` | `elixir_eval.py` | `tsc --noEmitOnError` で compile 専任させ (診断コードで undefined/TS2304・2552、syntax_error/TS1xxx、type_error/その他 TS2xxx・TS7xxx に分類)、クリーンなら emit された `.js` を `node` で実行する 2 段 subprocess 評価。summary は elixir 版とほぼ同名キーを維持 + `type_error_rate` を追加。`token_missing_rate`/`compile_error_rate` は judge が参照しない (`judge_win_condition_ts.py` の `METRIC_KEYS` に無い) ため削除、`function_clause_rate` は judge が参照するため key のみ維持し値は常に 0.0 (dead field) |
| `scripts/eval/run_baseline_ts.py` | `run_baseline_elixir.py` | dataset/stop_tokens 以外ほぼ verbatim |
| `scripts/eval/judge_win_condition_ts.py` | `judge_win_condition_elixir.py` | 閾値・警報 (+5pp、hack_gap 15% 小衰、大衰条件、repair-on の baseline=koumyou-on) は同値のまま |
| `scripts/runpod_bench_ts4.sh` | `runpod_bench_eli4.sh` | DATASET=humaneval-ts。`install_elixir_if_missing` → `install_node_if_missing` (apt nodejs/npm、古ければ NodeSource) + `npm ci --prefix ts_tools`。`dod_regression` は削除 (eli3 相当の既存 TS runner が無い)。`dod_round0` は同 runner 内部比較 (repair-on `--max-rounds 0` の round_0 vs 同 runner koumyou-on) に変更 |
| `tests_ts4/` | `tests_eli4/` | 単体テスト。詳細下記 |
| `ts_tools/` | — | `tsc`/`typescript` の npm パッケージ置き場 (`npm ci` で導入、`ts_tools/node_modules/.bin/tsc`) |

`diff_raw_completions.py` は言語非依存なのでそのまま流用 (新規コピーなし)。

## `tests_ts4/`

`tests_eli4/` からの移植 + 新規。**他スイート (`tests/` `tests_go/` `tests_eli4/`) と
混ぜて 1 回の `pytest` invocation に渡さないこと** — `import kojiki_lm` が
`sys.path` 挿入順に依存するため、別ディレクトリ向けの `sys.path` insert と衝突する
(ルートの `CLAUDE.md` の既存ルールと同じ理由)。

- `test_ashibune.py` / `test_koumyou_so.py` / `test_yomotsu_reason_code.py`: 第1段 (src_min_ts4
  変異体フォルダ新設 + koumyou_so TS 化 + ts_evaluator.py) のテスト
- `test_repair_runner.py`: `run_yamato_min_ts4.py` の pure function 単体テスト
  (seed 式、如先の wrapped_prompt、`build_hint` の TS 3 分岐、`resolve_reason_code`、
  `resolve_tsc_bin`/`resolve_node_bin` の fail-fast、`build_repair_summary`、ashibune 記録)
- `test_ts_eval.py`: `ts_eval.py` の単体テスト。**実 tsc + node を使う** (`ts_tools/`
  の `npm ci` 済み typescript、モックしない) — pass / test fail / TS2304 undef /
  TS1005 syntax / timeout の 5 ケース + `classify_diagnostics` の純粋関数テスト

GPU/model の実ロードは行わない。runner モジュールの `main()` は一切呼ばず、
モジュールレベルの pure function のみを対象にする。

eli4 は **一切変更していない** (`src_min/` `src_min_go/` `src_min_eli2/` `src_min_eli3/`
`src_min_eli4/` を変更・import しないという ts4 実装設計書 §9 の禁止事項を継承)。

## 関連文書

- `src_min_eli4/README.md`: eli4 (產屋 REPAIR) の構成、eli3 との差分
- `data/kojiki/設計書/ts4_実装設計書_v0.md`: 本実装の設計原理・§8 DoD・§9 禁止事項
