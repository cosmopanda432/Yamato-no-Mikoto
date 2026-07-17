# ts4 実装設計書 v0 — eli4 同型スタックの TypeScript 移植

2026-07-17。eli4 (產屋/還降) の pilot 0 で repair-on が Win Condition を達成した (+11.80pp vs
koumyou-on、undef 0.00%) のを受け、**同じ 4-arm ablation を人気言語 TypeScript で再現**する。
第 1 弾のゴールは「全機構が TS で動き ablation データが取れること」。**数値の勝敗はゲートに
しない** (judge は情報として実行する)。kotodama 復活は本設計のスコープ外 (将来の第 5 arm 候補)。

## 1. 目的と非目的

- 目的: eli4 の firewall + 光明想 + 還降ループを humaneval-ts (MultiPL-E) で動かし、
  4 mode (firewall-off / firewall-on / koumyou-on / repair-on) × seed0 の ablation データを取る。
- 目的: 「還降の効果は Elixir 固有か言語横断か」に答えるための、eli4 と構造同型な比較対象を作る。
- 非目的: Win Condition 達成 (情報として judge するが合否ゲートにしない)。
- 非目的: kotodama token masking の復活。src_min/ (原点 TS 変異体) への変更。

## 2. 変異体フォルダ `src_min_ts4/`

`src_min_eli4/` の**フルコピー**から出発し、以下だけ差し替える (eli2→eli3→eli4 と同じ
copy-based 変異体方式。共有コードで ablation を汚さない)。

| ファイル | 扱い |
|---|---|
| `yomotsu_hirasaka.py` `firewall_decoder.py` `ashibune.py` `yamato_config.py` `yamato_model.py` `yamato_qwen.py` `qwen_adapter.py` `kenpou/` `yomi/` | **verbatim** (言語非依存) |
| `koumyou_so.py` | trace コメント prefix を `# 思考:` → `// 思考:` に変更 (検出 regex とも)。行数/文字数閾値・TraceStatus の意味論は不変 |
| `elixir_evaluator.py` → `ts_evaluator.py` | in-loop heuristic 評価器の TS 語彙版 (§3)。クラス名 `TsEvaluator` |
| `data.py` | MultiPL-E parquet schema は言語共通なのでほぼ verbatim。stop_tokens は parquet 由来をそのまま使用。dataset 名の既定値のみ humaneval-ts に |

## 3. `ts_evaluator.py` (in-loop heuristic)

スコア計算の骨格 (0.5 起点、キーワード +0.05/hit、bad pattern −0.10、bracket 不一致 −0.20、
commit≥0.7 / halt<0.3、光明想 terminal failure は overriding HALT) は **eli4 と 1 bit も
変えない**。差し替えるのは語彙と言語固有チェックのみ:

- GOOD keywords (TS): `function `, `const `, `let `, `return `, `=>`, `interface `, `type `,
  `: number`, `: string`, `: boolean`, `[]`, `Array<`, `Math.`, `String(`, `Number(`,
  `.map(`, `.filter(`, `.reduce(`, `.length`, `===`, `!==`, `for (`, `while (`, `if (` 等
- BAD patterns: `// TODO`, `// FIXME`, `throw new Error("not implemented`, `any` の乱用は
  減点しない (誤爆リスク)
- `do/end` 収支チェックは TS に存在しないため**削除**し、既存の bracket 収支 (`()[]{}`)
  に一本化する。`ReasonCode.DO_END_MISMATCH` は ts4 では発生しない dead code として残す
  (yomotsu_hirasaka を verbatim に保つため。判定優先順位から自然に外れる)
- template literal / string 内の括弧は近似のまま (eli4 と同水準の割り切り)

## 4. scripts/eval (すべて eli4 対応物の copy + 適応)

| 新規ファイル | 出発点 | 主な差分 |
|---|---|---|
| `run_yamato_min_ts4.py` | `run_yamato_min_elixir4.py` | import 先 src_min_ts4、TRACE_SEED を `// 思考: ` 形式に、in-loop eval の import を `ts_eval` に、`resolve_elixir_bin` → `resolve_node_bin`/`resolve_tsc_bin` (repair-on は生成 host に node+tsc 必須、fail-fast) |
| `ts_eval.py` | `elixir_eval.py` | §5 の実行方式。summary キーは elixir 版と同名を維持 (+ `type_error_rate` 追加) |
| `run_baseline_ts.py` | `run_baseline_elixir.py` | dataset/stop_tokens 以外ほぼ verbatim |
| `judge_win_condition_ts.py` | `judge_win_condition_elixir.py` | 閾値・警報 (+5pp、hack_gap 15% 小衰等) は**同値のまま** (情報値として出す)。repair-on の baseline=koumyou-on も同じ |
| `scripts/runpod_bench_ts4.sh` | `runpod_bench_eli4.sh` | DATASET=humaneval-ts、setup に node20+typescript (apt/nvm + `npm i -g typescript`)、`install_elixir_if_missing` → `install_node_if_missing` |

`diff_raw_completions.py` は言語非依存なので**そのまま流用** (新規コピー不要)。

## 5. TS の subprocess 評価方式 (`ts_eval.py` の `run_one`)

1. 生成コード + MultiPL-E tests を 1 つの `.ts` に連結して temp dir に書く。
2. `tsc --noEmitOnError --outDir <tmp> <file>` を **1 回だけ**呼ぶ:
   - diagnostics が出れば compile 失敗。診断コードで分類する:
     - **TS2304 / TS2552** (`Cannot find name 'X'`) → `undefined` 扱い + シンボル名 `X` を抽出
       (elixir 版の undef 検出より高精度になる想定)
     - **TS1xxx** → `syntax_error` (elixir 版の TokenMissingError 系に対応)
     - その他 **TS2xxx/TS7xxx** → `type_error` (新分類、summary に `type_error_rate` を追加)
   - クリーンなら emit された `.js` を `node` で実行し、assert 失敗/exit code でテスト合否。
3. timeout は eli4 と同じ既定 (in-loop 5.0s / post-hoc 10s)。tsc 1 回 + node 1 回で収まる。
4. tsc の解決: `TS4_TSC` env → `ts_tools/node_modules/.bin/tsc` → PATH の順で探し、
   無ければ fail-fast (`resolve_elixir_bin` と同じ思想)。repo に `ts_tools/package.json`
   (devDependency: typescript ^5) を追加し、ローカル/pod とも `npm ci` で入れる。

## 6. 還降 hint 処方 (build_hint の TS 版)

eli4 Step D の処方規則を tsc 診断ベースで強化する:

- `undefined` (TS2304/2552): `// ヒント: 'X' は未定義です。標準ライブラリまたは自分で定義した名前だけを使ってください` (シンボル名を埋め込む)
- `syntax_error` (TS1xxx): `// ヒント: 構文エラーがあります (括弧・文字列の閉じ忘れに注意)`
- `type_error` (TS2xxx): `// ヒント: 型エラーがあります: <診断メッセージ先頭 80 字>`
- テスト失敗 (コンパイルは通過): eli4 と同じ (hint なし再サンプル)

`hints_used` の集計軸・`repair_reason` の意味論 (直前 attempt の reason_code) は eli4 と同一。

## 7. テスト `tests_ts4/`

`tests_eli4/` のコピー + 適応。sys.path 挿入方式・「他スイートと混ぜて pytest しない」制約も
同じ (CLAUDE.md に追記する)。

- 純粋関数 (attempt_seed / build_wrapped_prompt / build_repair_summary 等): ほぼ verbatim
  (TRACE_SEED の期待値だけ `// 思考:` 版に)
- `TsEvaluator`: 語彙・bracket 収支・光明想 HALT の単体テスト (eli4 の対応テストを TS 語彙に)
- `ts_eval.run_one`: **実 tsc + node を使う** (ローカル node v22 は確認済み、typescript は
  `ts_tools/` の `npm ci` で導入)。pass / test fail / TS2304 / TS1005 / timeout の 5 ケース
- `resolve_tsc_bin` の fail-fast

## 8. DoD

ローカル (この host、GPU 不要):
1. `pytest tests_ts4/` 全 pass、`pytest tests/` `pytest tests_go/` `pytest tests_eli4/` 回帰無傷
2. `ts_eval.py run_one` の実 tsc/node ケースが通る

RunPod (後日、pod 再開後):
- DoD-T-1: `smoke_repair` (--limit 20, max-rounds 2) で還降発火 + ashibune/_repair_summary 書き出し
- DoD-T-2: repair-on `--max-rounds 0` の round_0 が **同 runner の koumyou-on と** raw_completion
  全一致 (ts4 内部の統制条件。eli3 に相当する既存 TS runner は無いため内部比較とする)
- DoD-T-3: `pilot_ts 0` — baseline_ts 0 → 4 mode × seed0 → judge (情報値)。
  bench script は eli4 の「部分 results skip 罠」対策として、dod 系サブコマンドが results を
  残した場合の注意コメントを usage に明記する

## 9. 禁止事項 (eli4 §8 を継承)

- `src_min/` `src_min_go/` `src_min_eli2/` `src_min_eli3/` `src_min_eli4/` は変更・import しない
- `L3ToL5Payload` / `L5ToL3Verdict` の contract に手を入れない
- 生成済みテキストの部分書き換えをしない (還降は常に全再生成)
- `v_score` を attempt の合否・選別に使わない (`test_ok` のみ)
- 既存 eval スクリプト (elixir/go 系) は変更しない

## 10. 命名

フォルダ名 `src_min_ts4` (= TS ターゲット × 第 4 世代スタック)。モジュール名は eli4 の対応物を
機械的に対応させる (elixir_evaluator → ts_evaluator 等)。神名の新規追加はしない (既存の
yomotsu_hirasaka / koumyou_so / ashibune をそのまま使うため)。
