# v_score slice 再採点 (Phase A) — 結果と採否判断

2026-07-17。`vscore_slice_設計書_v0.md` Phase A の実施結果。
入力: `data/eval/results/runpod_eli4_20260717/pilot0_full_outputs.tar.gz`
(161 prompt × {baseline, eli4 4 mode} は results 付き完全ダンプ、eli3 は部分ダンプ
5/5/20 件・results なし → 再現率確認のみ)。
再実行: `python3 scripts/analysis/replay_vscore_slice.py --workdir <展開先>`
(evaluator は `src_min_eli4/kojiki_lm/` を import のみ、変更なし。KoumyouSo 閾値は
pilot0.log 記載の実行値 min_lines=1 / min_chars=20 / grace=16 / seed='  # 思考: ')。

## 結論 (要旨)

1. **prompt インフレは実証された**: prompt 単体の v_score が median 0.75
   (q1=0.70, q3=0.75)、**161 prompt 中 96.89% が単体で COMMIT 閾値 0.7 以上**。
   現行の全文採点はほぼ「prompt を採点している」。全文方式の COMMIT は
   ほぼ無条件 (光明想 gate 通過分の 88〜93% が commit 圏) で、hack_gap ≈
   ベース失敗率、すなわち audit 信号として無情報。
2. **しかし事前定義の採用基準は不成立**。slice 版 (raw_completion のみ採点) は
   閾値 0.7/0.3 据え置きだと COMMIT 圏がほぼ消滅する (commit 161 件中 1〜5 件)。
   repair-on の hack_gap 58.89%→40.00% は「半減以上」に届かず、しかも分母
   90→5 の崩壊による見かけの改善で、統計的に無意味。
3. **深掘りの発見: slice スコアには正の識別力が無い**。光明想 gate 通過
   sample に限った rank AUC は score_b (slice) = 0.40〜0.41 と **chance 未満**
   (全文 score_a も 0.35〜0.59 で大差なし)。keyword 加点 heuristic 自体が
   test 合否とほぼ無相関〜逆相関であり、slice しても「良い proxy」にはならない。
   観測される分離力 (koumyou-on AUC 0.81) の大半は光明想 gate (v=0.0 HALT) の寄与。
4. **閾値再調整でも救えない** (下記 sweep 表): slice 版の commit 閾値を
   0.40〜0.65 のどこに置いても hack_gap 42.9〜82.5% で、小衰閾値 15% どころか
   半減目標 (≤29%) にも届かない。
5. **ts4 `score_generated_only` の推奨 default: False** (旧挙動維持)。
   flag 自体は Phase B どおり実装して A/B 可能にするが、True を default に
   するのは「スコア骨格の再設計 + 閾値再設定」とセットのときのみ
   (slice はインフレ除去の必要条件だが十分条件ではない、が本分析の結論)。
6. 閾値 0.7/0.3 据え置きのままの slice 化は不可 (COMMIT 消滅、hack_gap の
   分母が audit に耐えない)。

## 再現率 (riskiest assumption の検証)

(a) `wrapped_prompt + raw_completion` 全文再採点 (+光明想 gate replay) と
ダンプ `final_v_score` の一致率。wrapped_prompt は runner の式
`prompt + hint_line + trace_seed` で再構築 (repair round≥1 の hint 込み)。

| mode | v_score 完全一致 | verdict 一致 | 不一致内訳 (stop_token / halted / other) | \|Δv\| median / max |
|---|---|---|---|---|
| eli4 firewall-on | 78/148 (52.7%) | 126/148 (85.1%) | 70 / 0 / 0 | 0.200 / 0.250 |
| eli4 koumyou-on | 135/161 (83.9%) | 143/161 (88.8%) | 16 / 6 / 4 | 0.450 / 1.000 |
| eli4 repair-on | 133/160 (83.1%) | 145/160 (90.6%) | 23 / 2 / 2 | 0.200 / 0.900 |
| eli3 koumyou-on (n=20) | 15/20 | 18/20 | 4 / 0 / 1 | 0.200 / 0.700 |

- 光明想 trace status の replay は dump `trace_info.status` と **161/161 一致**
  (eli4 koumyou-on / repair-on とも) — gate replay の妥当性は VERIFIED。
- 不一致の主因は設計書が予見したとおり **stop_token 途中終了**: decoder の
  final_verdict は「最後の firewall check step (16 token 刻み)」時点の
  部分 text への評価で、全文とは bracket/do-end 収支が違う (Δv はほぼ
  ±0.20 = mismatch penalty 1 個分)。token 単位の途中 text はダンプから
  復元不能のため、これ以上の再現は不可能 (既知の限界)。
- `other` 4 件 (koumyou-on) は「in-loop では gate 通過 → COMMIT (v 0.70〜0.95)
  したが、最終 text は trace_insufficient」: 中国語 trace の per-token decode
  ("�" 置換) で in-loop の trace_body_chars が全文 decode と食い違う、
  というのが最も整合的な説明 (REASONED、tokenizer 検証は次回 pod)。
- halted 6 件 (dump v=0.0、replay は trace_only) は「check 境界で 2 行目の
  `# 思考:` marker が生成途中 (`# 思` 等) → code 開始と誤判定 → 早期 HALT」
  で説明できる (REASONED。例: HumanEval_144_simplify、32 step で halt、
  raw は trace 2 行のみ)。
- firewall-on の dump verdict `none` 13 件は total_step_count < 16
  (初回 check 前に stop_token 到達)。repair-on の `none` 1 件も同様。

**結論: 再現率は水準として十分** (koumyou 系で v 完全一致 83〜84%、verdict
一致 89〜91%、乖離は全件がメカニズム的に説明可能で、方式比較 (a) vs (b) には
影響しない — 両者とも同じ全文/同じ slice を見るため)。

## 数表: hack_gap old vs new (mode 別)

hack_gap = P(test fail | v ≥ 0.7) (`elixir_eval.compute_hack_gap` と同定義)。
(a)=全文 replay、(b)=slice。n=161、test 結果は pilot0 の subprocess 実測。

| mode | pass率 | hack_gap dump | hack_gap (a) 全文 | hack_gap (b) slice | commit 数 (a)→(b) |
|---|---|---|---|---|---|
| baseline | 27.33% | — (v なし) | 71.13% (101/142) | 100.00% (21/21) | 142→21 |
| eli4 firewall-off | 28.57% | — (v なし) | 72.00% (108/150) | 100.00% (2/2) | 150→2 |
| eli4 firewall-on | 28.57% | 77.95% (99/127) | 72.00% (108/150) | 100.00% (2/2) | 150→2 |
| eli4 koumyou-on | 14.29% | 75.29% (64/85) | 74.12% (63/85) | 0.00% (0/1) | 85→1 |
| eli4 repair-on | 26.09% | 57.47% (50/87) | 58.89% (53/90) | 40.00% (2/5) | 90→5 |

- dump との整合: repair-on 57.47% vs replay 58.89%、koumyou-on 75.29% vs
  74.12% — 再採点は pilot の観測を再現している (VERIFIED)。
- (b) の見かけの改善は **分母崩壊** (90→5 等)。分母 ≤5 の率に意味はない。

## verdict 分布と test_ok 取りこぼし

| mode | dump | (a) 全文 | (b) slice |
|---|---|---|---|
| firewall-on | c127 / r21 / none13 | c150 / r11 | c2 / r158 / h1 |
| koumyou-on | c85 / h73 / r3 | c85 / h74 / r2 | c1 / r86 / h74 |
| repair-on | c87 / h63 / r10 / none1 | c90 / h66 / r5 | c5 / r89 / h67 |

「test_ok なのに halt 圏 (<0.3)」取りこぼし率 (採用基準 2):

| mode | (a) 全文 | (b) slice | Δ |
|---|---|---|---|
| firewall-on | 0.00% (0/46) | 0.00% (0/46) | +0.00pp |
| koumyou-on | 0.00% (0/23) | 0.00% (0/23) | +0.00pp |
| repair-on | 4.76% (2/42) | 4.76% (2/42) | +0.00pp |

→ **採用基準 2 (halt 化 +10pp 以内) は満たす**。halt はほぼ全て光明想 gate 由来
で、gate は old/new 共通のため slice で halt が増えない。逆に言えば slice の
効果は commit→repair への大量移動のみ (in-loop では commit も repair も生成
継続なので挙動影響は小さいが、audit 指標 hack_gap の分母が消える)。

## 閾値 sweep (TPR/FPR、簡易 AUC)

TPR = P(v≥t | test_ok), FPR = P(v≥t | test fail)。AUC は rank (Mann-Whitney)。

repair-on (n=161, pass 42 / fail 119):

| t | 0.1 | 0.2 | 0.3 | 0.4 | 0.5 | 0.6 | 0.7 | 0.8 | 0.9 |
|---|---|---|---|---|---|---|---|---|---|
| (a) TPR | 0.95 | 0.95 | 0.95 | 0.95 | 0.95 | 0.95 | 0.88 | 0.45 | 0.10 |
| (a) FPR | 0.46 | 0.46 | 0.46 | 0.46 | 0.46 | 0.45 | 0.45 | 0.22 | 0.09 |
| (b) TPR | 0.95 | 0.95 | 0.95 | 0.79 | 0.40 | 0.12 | 0.07 | 0.00 | 0.00 |
| (b) FPR | 0.46 | 0.46 | 0.45 | 0.42 | 0.34 | 0.09 | 0.02 | 0.00 | 0.00 |

| AUC | baseline | firewall-off | firewall-on | koumyou-on | repair-on |
|---|---|---|---|---|---|
| (a) 全文 | 0.353 | 0.351 | 0.351 | 0.808 | 0.763 |
| (b) slice | 0.263 | 0.329 | 0.329 | 0.723 | 0.704 |
| (a) gate 通過のみ | — | — | 0.351 | 0.586 | 0.540 |
| (b) gate 通過のみ | — | — | 0.329 | 0.403 | 0.408 |

- koumyou 系の AUC 0.7〜0.8 は光明想 gate (v=0.0 の HALT 塊) の寄与。gate を
  除くと score 自体の分離力は (a) 0.54〜0.59 / **(b) 0.40〜0.41 (chance 未満)**。
- 非 koumyou mode では全文 slice とも AUC < 0.5: keyword 加点 heuristic は
  完成 code の合否に対してむしろ逆相関。

## 代替案の数値評価 (slice + 閾値再調整では救えない)

slice (b) の commit 閾値 sweep、repair-on / koumyou-on:

| commit_thr | repair-on hack_gap (commit率) | koumyou-on hack_gap (commit率) |
|---|---|---|
| 0.40 | 60.2% (51.6%) | 77.8% (50.3%) |
| 0.45 | 63.5% (46.0%) | 80.3% (44.1%) |
| 0.50 | 70.7% (36.0%) | 82.5% (39.1%) |
| 0.55 | 63.6% (20.5%) | 76.9% (16.1%) |
| 0.60 | 68.8% (9.9%) | 80.0% (6.2%) |
| 0.65 | 42.9% (4.3%) | 33.3% (1.9%) |
| 0.70 | 40.0% (3.1%) | 0.0% (0.6%) |

halt 閾値も 0.30 から上げると即 test_ok を取りこぼす (repair-on: 0.35 で
11.9%、0.40 で 21.4%)。**どの (commit, halt) の組でも「hack_gap 半減 (≤29%)
かつ分母が audit に耐える」点は存在しない**。原因は閾値ではなくスコア骨格
(AUC < 0.5) にあるため、重み (good_keyword_weight 等) の定数倍調整でも
順序はほぼ変わらず改善しない。

## 採用基準への判定

| 基準 (設計書で事前定義) | 結果 | 判定 |
|---|---|---|
| 1. hack_gap 相当が半減以上 | repair-on 58.89%→40.00% (−32% 相対)、かつ分母 90→5 に崩壊 | **不成立** |
| 2. test_ok の halt 化 +10pp 以内 | 全 mode +0.00pp | 成立 |

→ **総合: 不採用 (閾値据え置きの slice 化は行わない)**。

## ts4 (Phase B) への推奨

- `EvaluatorConfig.score_generated_only` は設計書どおり実装するが、
  **default は False** (採用基準不成立のため。事前定義ルールに従う)。
  対比テスト (「キーワード満載 prompt + 劣悪 completion」が方式で分かれる)
  は本分析の実データがそのまま根拠になる。
- True 化は「スコア骨格の再設計 (+ 閾値再設定)」を伴う別提案として扱う。
  本分析が示す設計制約: (i) prompt を含めてはならない (インフレ実証済み)、
  (ii) 現行 keyword 加点は completion 単体で負の信号 (AUC 0.40) なので、
  加点系ではなく構造 check (bracket/do-end 収支、光明想 gate) 中心に寄せる、
  (iii) hack_gap は precision 型で base rate (pass 14〜29%) に強く汚染される
  ため、proxy 改善の KPI には AUC / sweep を併記する。

## Phase B への引き継ぎ事項 (分析中の副次発見)

1. **in-loop gate の check 境界アーティファクト** (koumyou-on 161 件中 6 件):
   2 行目の `# 思考:` marker が 16-token check 時点で生成途中 (`# 思` 等) だと
   code 開始と誤判定され早期 HALT する (REASONED)。
2. **per-token decode と全文 decode の乖離** (同 4 件): 中国語 trace で
   in-loop の text_buffer ("�" 置換を含む) と最終 batch decode の文字数が
   食い違い、gate をすり抜けて trace_insufficient のまま COMMIT された
   (REASONED、次回 pod で tokenizer 検証可)。ts4 は `// 思考:` marker +
   同じ decode 方式なので同種の問題を持ち得る。
3. stop_token 途中終了 sample では final_v_score が全文でなく 16-token 刻みの
   途中 text への評価になる — v_score を audit に使うなら「最終 text への
   再評価を 1 回入れる」ことも Phase B' の検討候補 (今回の再現率 52.7〜83.9%
   の主因)。

## 限界 (ラベル付き)

- VERIFIED: 本メモの全数値 (`replay_vscore_slice.py` の実行出力)、
  dump hack_gap との整合、trace status 161/161 一致。
- REASONED: 再現不一致 6+4 件のメカニズム説明 (check 境界 / per-token decode)。
  raw ダンプの内容と koumyou_so.py のロジックから導出したが、in-loop の
  token 単位 text_buffer 自体は復元していない。
- REASONED: pilot 実行時の EvaluatorConfig が default (0.7/0.3, weight 0.05)
  であること (runner は `ElixirEvaluator(koumyou_so=...)` と config 引数なしで
  生成しており、コード上 default 確定。KoumyouSo 閾値は pilot0.log で VERIFIED)。
- ASSUMED: pilot 実行時の runner コードが本 worktree の
  `run_yamato_min_elixir4.py` と同一であること (pod 側の実体は未照合。
  ダンプ JSON の field 構成・hack_gap 数値の一致は間接的な裏付け)。
  eli3 部分ダンプ (results なし) は再現率確認以外に使っていない。
