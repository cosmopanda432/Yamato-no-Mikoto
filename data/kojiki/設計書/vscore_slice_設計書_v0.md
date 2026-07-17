# v_score slice 改訂 設計書 v0 — proxy の prompt インフレ修正

2026-07-17。eli4 pilot 0 で小衰警報 (repair-on hack_gap 57.47%、koumyou-on 単体 75.29%、閾値 15%)。
本命原因は §11 で棚上げされていた既知の弱点: **in-loop 評価器 (`ElixirEvaluator`/`TsEvaluator`) が
v_score を prompt を含む全文で採点している** こと (`_compute_score_and_flags(payload.text)`)。
prompt はキーワードの塊なので、生成部分が空でもスコアが 0.7 近くまでインフレし、
「良さそうに見えるが動かないコード」を COMMIT してしまう。なお光明想チェックは既に
`payload.text[payload.prompt_len:]` で slice 済み — 採点だけが全文のまま。

## 方針

1. **凍結 arm は不変**: `src_min/` `src_min_go/` `src_min_eli2/3/4` は変更しない (eli4 は 3-seed ci が
   保留中のため比較可能性を守る)。修正の実装先は **ts4 のみ** (pilot 未実施なので数値の非連続が発生しない)。
2. **採用判断はデータで**: 実装の前に、ローカルにある eli4 pilot の実生成ダンプで slice 版を
   オフライン再採点し、効果を定量してから default を決める。

## Phase A — オフライン再採点分析 (GPU 不要、先行)

- 入力: `data/eval/results/runpod_eli4_20260717/pilot0_full_outputs.tar.gz` (161問 × {baseline, eli4 4 mode,
  eli3 koumyou}。生成 JSON に `prompt` / `raw_completion` / `final_v_score` / `final_verdict`、results に
  test 結果あり — 確認済み)。
- 手法: `src_min_eli4/kojiki_lm/elixir_evaluator.py` を **import のみ** (変更禁止) し、
  `_compute_score_and_flags` を (a) `prompt + raw_completion` 全文 = 現行方式の再現、
  (b) `raw_completion` のみ = slice 案、(c) `prompt` のみ = インフレの直接証拠、の 3 通りで呼ぶ。
  (a) が dump の `final_v_score` を再現することで replay の妥当性をまず確認する
  (halt 途中終了 sample は最終 payload と異なりうる — 再現率をレポートに明記)。
- 指標 (mode 別):
  1. hack_gap 相当 (v_score≥0.7 かつ test fail) の old vs new
  2. verdict 分布 (commit/repair/halt) の変化 — 特に「test_ok なのに new では halt 圏 (<0.3)」の
     取りこぼし率
  3. v_score による test_ok 分離度 (閾値 sweep での TPR/FPR、簡易 AUC)
  4. prompt-only スコアの分布 (中央値が 0.7 に迫っていればインフレ実証)
- 成果物: `scripts/analysis/replay_vscore_slice.py` (再実行可能な形) + レポート
  `docs/memo/2026-07-17_vscore_slice再採点.md` (数表と採否判断)。
- **事前定義の採用基準**: slice 版で hack_gap 相当が大幅 (目安: 半減以上) 低下し、かつ
  test_ok サンプルの halt 化が急増 (目安: +10pp 超) しないこと。閾値 0.7/0.3 は据え置きで評価し、
  据え置きでは崩れる場合は代替案 (閾値・重みの再調整) を数値付きでレポートに記す。

## Phase B — ts4 実装 (Phase A の結果を受けて)

- `src_min_ts4/kojiki_lm/ts_evaluator.py`: `EvaluatorConfig` に `score_generated_only: bool` を追加
  (default は Phase A の結果で確定、採用基準を満たせば True)。`__call__` で採点対象を
  `payload.text[payload.prompt_len:]` に (光明想と同じ既存フィールド、payload 契約は不変)。
  False で旧挙動 (比較・デバッグ用)。score 骨格・reason_code 優先順位は不変。
- tests_ts4: 「キーワード満載 prompt + 空/劣悪 completion」が旧方式 COMMIT 圏 / 新方式 HALT 圏に
  分かれる対比テスト、flag off で旧挙動維持、既存テストの期待値追随。
- 統制条件 (repair round0 ≡ koumyou-on) は評価器が両 mode 共通のため不変 (DoD-T-2 の性質は保持)。
  過去の ts4 N=20 DoD 数値とは非連続になるが pilot 未実施のため実害なし (本設計書が記録)。

## Phase C — QA レビュー → merge 判断 (ユーザー)

## 禁止事項

- `src_min/` `src_min_go/` `src_min_eli2/` `src_min_eli3/` `src_min_eli4/` の変更 (import は可)。
- 閾値 0.7/0.3・スコア骨格の無断変更 (変えるなら Phase A の数値を根拠にレポートで提案)。
- GPU を要する実行 (再検証は次回 pod で ts4 pilot として実施)。

## Phase A 判定 (2026-07-17 追記) — 不採用、Phase B は中止

オフライン再採点 (`scripts/analysis/replay_vscore_slice.py`、全数表は
`docs/memo/2026-07-17_vscore_slice再採点.md`) の結果:

- **インフレ仮説は実証**: prompt 単体で median 0.75、**96.89% が commit 閾値 0.7 を単体で超える**。
  現行の hack_gap はベース失敗率とほぼ一致 = v_score は無情報。
- **しかし slice は救済にならない**: 閾値据え置きで COMMIT 圏が 161 件中 1〜5 件に崩壊。
  閾値 sweep (0.40〜0.70) 全域でも hack_gap 40〜83% / halt 側は 0.35 で早くも test_ok
  取りこぼし 11.9%。原因は閾値ではなく**キーワード加点という骨格自体に識別力が無い**こと
  (gate 通過 sample 限定 AUC 0.40〜0.41 = chance 未満)。
- 判定: 採用基準 ①hack_gap 半減 不成立 (分母崩壊による見かけの低下のみ)。
  **`score_generated_only` flag の ts4 実装も見送り** (default False の flag は死にコード、YAGNI)。
- 後続提案 (別プロジェクトとして): v_score の再設計は「加点系 → 構造 check 中心」への骨格変更が
  必要条件。replay harness が整備されたので、候補スコアラーは GPU なしで offline AUC 評価できる。
- 副次発見 2 件 (ts4 にも同種リスク、次回 pod で tokenizer 検証可能):
  ① 16-token 刻み check 境界で `# 思考:` marker 生成途中を code と誤判定して誤 HALT (6件)、
  ② 中国語 trace の per-token decode "�" による光明想 gate すり抜け COMMIT (4件)。
