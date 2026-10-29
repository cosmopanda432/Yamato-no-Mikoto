# v_score v2 設計書 v0 — 加点系から構造検分への骨格再設計

2026-07-17。前提となる実証 (「vscore_slice_設計書_v0.md」Phase A / `docs/memo/2026-07-17_vscore_slice再採点.md`):

- 現行 v_score (keyword 存在 +0.05、初期値 0.5) は **無情報** — prompt 単体で 96.89% が commit
  閾値 0.7 を超え、gate 通過 sample での AUC 0.40〜0.41 (chance 未満)。
- prompt slice は**必要条件だが十分条件ではない** (slice だけでは commit 圏が崩壊)。
- 須弥山メモ §7 の処方「v_score は verdict gate 専用」は本設計でも維持する (選別・報酬への
  昇格禁止)。§7 の記述訂正はしない — 仕様自体を置き換えるため。

## 1. 目的と役割

decode ループ中 (16-token 刻み) の in-loop 評価器を、「テストに通りそうか」について
**chance を明確に上回る識別力を持つ構造検分 (structure check) 型**に置き換える。
役割は従来どおり COMMIT / REPAIR / HALT の verdict gate 専用。

## 2. 制約 (実装環境から導かれる)

- hot path: 16-token ごとに呼ばれる。subprocess・モデル内部状態へのアクセス禁止
  (L3/L5 firewall の str-only 契約は不変)。軽量な純 Python 文字列処理のみ。
- **採点対象は生成部分のみ** (`payload.text[payload.prompt_len:]`) — 必要条件として確定。
- 生成途中の partial text に対して壊れないこと (途中状態を過剰に罰しない)。

## 3. 候補スコアラー (C0〜C4、オフラインで競わせる)

| 案 | 内容 |
|---|---|
| C0 | 現行方式 (全文 keyword 加点) — baseline、AUC 0.40 の再確認用 |
| C1 | slice + **構造 check のみ** (keyword 加点全廃): 括弧/do-end 収支、未終端 string、空 body |
| C2 | C1 + **切断検出**: 未終端構文の深さ、末尾が識別子/演算子途中か、行の完結性 (token_missing 50-70% の主因である max_new_tokens 切断を in-loop で予知する) |
| C3 | C2 + **劣化パターン検出**: n-gram 反復ループ、comment-only 生成、TODO/未実装系 |
| C4 | C3 の少パラメータ校正: 各 check の重みを replay データの **train split で fit** し holdout で評価 (パラメータ数 ≤ 6、単調な線形結合に限定 — 過学習と Goodhart 耐性のため) |

各 check は「存在で稼げる加点」を持たない (減点・ゲート型のみ) — keyword stuffing 耐性を
構造的に持たせる。

## 4. オフライン評価 (GPU 不要、replay 基盤の拡張)

- データ: eli4 pilot dump (161問 × 4 mode) + eli3 + baseline (`pilot0_full_outputs.tar.gz`)。
- **split は問題単位** (HumanEval 番号で train/holdout を分ける — 同一問題の mode 違いが
  両側に入る leakage を防ぐ)。split は seed 固定で再現可能に。
- KPI (事前定義):
  - 主基準: **holdout AUC ≥ 0.65** (chance 0.5、現行 0.40) — v_score による test_ok 分離
  - 副基準1: test_ok sample の halt 誤爆 (v2 で halt 圏に落ちる率) **≤ 5%**
  - 副基準2: 閾値 sweep で commit precision / recall と verdict 分布を併記し、commit 圏が
    実用的な広さを保つこと (定量は sweep 表で判断、崩壊 = C1 の二の舞を防ぐ)
  - hack_gap は参考指標に格下げ (precision 型で base rate に汚染されるため — Phase A の教訓)
- 実装: `scripts/analysis/` に候補スコアラーを **standalone で** 追加 (src_min* は import のみ・
  変更禁止)。`replay_vscore_slice.py` の読み込み部を流用。
- 閾値: 0.7/0.3 に固執しない。候補ごとに sweep で最適動作点を提示し、採用時に新閾値を仕様化。

## 5. 採否と実装先

- 採用基準を満たす候補があれば、**ts4 の `TsEvaluator` を v2 に置き換える** (v1 は残さない —
  ts4 は pilot 未実施なので対照は不要、死にフラグを作らない)。TS への feature 対応表
  (do/end → brace/paren depth、未終端 template literal、`//` comment-only 等) を実装時に仕様化。
- Elixir データで選定した骨格を TS に移す妥当性は ASSUMED — ts4 pilot (保留中) で実測する。
  この移送リスクは設計上の既知の限界として記録。
- どの候補も基準を満たさない場合: 「in-loop 静的検分では test 予測は不可能」という結論自体を
  レポート化し、v_score の役割縮小 (切断検出のみの HALT gate 化など) を代替提案する。
- 凍結 arm (`src_min/` `src_min_go/` `src_min_eli2/3/4`) は不変。

## 6. スコープ外

- 光明想 gate の副次発見 2 件 (16-token check 境界の marker 誤判定、per-token decode "�" の
  gate すり抜け) — 別 issue (メモリ記録済み、次回 pod で tokenizer 検証)。
- eli 系への v2 適用 (eli4 は ci 保留中のため凍結継続)。
- v_score の best-of-n 選別・報酬への昇格 (§7 の禁止事項を継承)。
