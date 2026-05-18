# Roadmap (Minimum) — yamatoLLM TS 版

Win Condition (`tsc strict +5pt` / `hallucination ×0.5`) に最短到達するための簡易版。
フル版は [旧ドキュメント/roadmap.md](旧ドキュメント/roadmap.md) 参照。

## 売り (この簡易版で立てる 2 本柱)

1. **型予測** — Stage 2 で学習済の `TsukuyomiTypeHead` (per-token TS 型) を、
   ランタイム時に **言霊 (Kotodama)** で物理的トークンマスクとして強制する。
   ハルシネーション (存在しない型/シンボル) を生成不可能にする。
2. **ファイヤーウォール** — `yomotsu_hirasaka` で L3 (生成) と L5 (評価) を
   構造的に隔離。評価器内部状態が生成側に漏れない。

この 2 つに振り切るため、フル版の 22 モジュール (~9,200 LOC) → **9 モジュール (~1,800 LOC)** に絞る。

## 現状 (2026-05-18)

| 項目 | 状態 | コミット |
|---|---|---|
| Stage 1 国譲り (Qwen 重み継承) | ✅ | (継承) |
| Stage 2 天孫降臨 (TypeHead/BonpuConfidence 学習) | ✅ Win Condition 未達 | (継承) |
| **M0** yamato_qwen サブクラス空殻 | ✅ | `a584326` |
| **M1'** Firewall + 簡略 Evaluator | ✅ | `ca2e69f` |
| **M2 (min)** 言霊 + Kotodama decoder + Firewall 統合 | ✅ | `376945d` |
| **M6 (min)** run_yamato_min.py + Win Condition 判定 | ✅ | `8dfbe60` |
| M2.5 (Node IPC + TS Compiler API, symbol-aware 制約) | 未着手 (Win 未達なら追加) | — |

簡易版コードは [src_min/kojiki_lm/](../src_min/kojiki_lm/) に集約。テスト 70 件全 pass (CPU 環境で全結合検証可能)。

## マイルストーン

### M0 — Qwen サブクラス骨格 ✅

`YamatoQwenForCausalLM(Qwen2ForCausalLM)` を空殻として配置。後続 M の override 点
(generate / forward) を docstring に明記。

**実装**
- ✅ [src_min/kojiki_lm/yamato_qwen.py](../src_min/kojiki_lm/yamato_qwen.py) — 空殻 + M2 で `generate_kotodama` 追加
- ✅ [src_min/kojiki_lm/qwen_adapter.py](../src_min/kojiki_lm/qwen_adapter.py) — `load_base_model` を新クラス経由に
- ✅ [scripts/eval/eval_type_head.py](../scripts/eval/eval_type_head.py) — 同上 (QwenAdapter 経由化)

---

### M1' — Firewall + Evaluator (簡略版) ✅

L3↔L5 境界を**型で**強制。評価器は V_score と 3 verdict だけ返す。

**実装**
- ✅ [src_min/kojiki_lm/yomotsu_hirasaka.py](../src_min/kojiki_lm/yomotsu_hirasaka.py) (~115 LOC)
  - `L3ToL5Payload` (frozen, `__post_init__` で型 assert): `text`, `step_idx`, `prompt_id` のみ
  - `L5ToL3Verdict` (frozen): `verdict ∈ {COMMIT, REPAIR, HALT}`, `v_score ∈ [0,1]` のみ
  - `YomotsuHirasaka.send(payload) → verdict` で evaluator 戻り値型を実行時検査
- ✅ [src_min/kojiki_lm/yomi_evaluator.py](../src_min/kojiki_lm/yomi_evaluator.py) (~110 LOC)
  - V_score 決定論計算 (TS 良キーワード加点 / `any`・`unknown`・`@ts-ignore` 減点 / ブラケット収支)
  - 2 段閾値で 3 verdict
  - Yomi Archive はカット
- ✅ [tests/test_firewall.py](../tests/test_firewall.py) (14 tests) / [tests/test_evaluator.py](../tests/test_evaluator.py) (11 tests)

**Done**
- ✅ Firewall: tensor を payload に渡すと TypeError、verdict 以外を返そうとすると拒絶
- ✅ Evaluator: ダミーテキストで V_score → verdict が決定論的に出る
- ✅ `pytest tests/` パス

---

### M2 (min) — 言霊 (Constrained Decoding) + Firewall 統合 ✅

**売りの本体**。TypeHead 出力 → BPE トークンマスク → Qwen logits に物理マスク (-inf)。
Firewall は decode ループ内で interval 起動。

**実装**
- ✅ [src_min/kojiki_lm/kotodama_token_mask.py](../src_min/kojiki_lm/kotodama_token_mask.py) (~140 LOC)
  - `TypeVocabIndex` — `config/ts_type_vocab.json` ロード
  - `KotodamaMaskBuilder` — 型 ID 集合 → bool マスク [V] (キャッシュ付)
  - `instability` / `special` カテゴリは除外
- ✅ [src_min/kojiki_lm/kotodama_context.py](../src_min/kojiki_lm/kotodama_context.py) (~40 LOC)
  - 「次は TS 型」 context を末尾 200 文字に対する regex で heuristic 判定
- ✅ [src_min/kojiki_lm/kotodama_decoder.py](../src_min/kojiki_lm/kotodama_decoder.py) (~230 LOC)
  - decode ループ: forward → TypeHead → mask → `masked_fill_(-inf)` → sample → Firewall.send → HALT 判定
  - `mask_enabled` / `firewall_enabled` フラグで ablation 可
  - StepLog に mask 適用状況・top type ID・verdict を記録
- ✅ [src_min/kojiki_lm/yamato_qwen.py](../src_min/kojiki_lm/yamato_qwen.py) — `generate_kotodama` メソッド追加
- ✅ tests: [test_kotodama_mask.py](../tests/test_kotodama_mask.py) (10) / [test_kotodama_context.py](../tests/test_kotodama_context.py) (19) / [test_kotodama_decoder.py](../tests/test_kotodama_decoder.py) (9)

**Done**
- ✅ prompt `function foo(x:` で次トークンが TS 型語彙のみにマスク
- ✅ logits に物理 `-inf` が乗ることを `torch.isneginf().any()` で直接確認
- ✅ 1 prompt 通しで Firewall→Evaluator→COMMIT/REPAIR/HALT が返る
- ✅ HALT verdict で decode ループが即停止

**M2.5 にカット (Win 未達なら追加)**
- Node サブプロセスでの TS Compiler API (`valid_continuations.ts` ~500 LOC)
- BPE prefix tree (`token_mask_builder.ts` ~300 LOC)
- Python ↔ Node stdio jsonl IPC (`kotodama_service.py` ~200 LOC)
- vanilla `generate` の完全 override (現状は `generate_kotodama` を別メソッドとして追加)

簡易版では heuristic context 検出 + TypeHead top-K による型語彙マスクに留め、
シンボル参照 (変数名/import 名) の制約は M2.5 で TS Compiler API 経由に拡張する。

---

### M6 (min) — e2e 評価 + Win Condition 判定 ✅

`baselines/` と直接比較し、1 ファイルで Win Condition 達成可否を判定。

**実装**
- ✅ [scripts/eval/run_yamato_min.py](../scripts/eval/run_yamato_min.py) (~230 LOC)
  - Qwen + Stage 2 `custom_heads.pt` ロード → Kotodama + Firewall 経由で MultiPL-E 生成
  - 出力 JSON は既存 `generate_multipl_e.py` 互換 (`run_tests.py` / `aux_metrics.py` 流用可)
  - 4 ablation モード: `full` / `no-kotodama` / `no-firewall` / `vanilla`
- ✅ [scripts/eval/judge_win_condition.py](../scripts/eval/judge_win_condition.py) (~180 LOC)
  - `baselines/<dataset>.<stem>.{summary,aux}.json` と新規結果を比較
  - tsc strict pp 差分 と TS2304 (Cannot find name) ratio を計算
  - `>> Win Condition: ACHIEVED / NOT MET` を JSON + stdout に出力
- ✅ [tests/test_e2e.py](../tests/test_e2e.py) (7 tests) — 4 mode × ablation 統合 + 判定ロジック

**評価項目**
- pass@1 (`run_tests.py`)
- tsc strict 通過率 (`aux_metrics.py`)
- ハルシネーション率 = TS2304 "Cannot find name" 発生サンプル率 (`aux_metrics.py` の `top_error_codes`)
- Ablation: `--mode {full, no-kotodama, no-firewall, vanilla}` 4 通り

**Win Condition**
- tsc strict pass rate が baseline 比 **+5pt 以上**
- ハルシネーション率が baseline 比 **×0.5 以下**

**Done**
- ✅ Win Condition 達成可否を 1 JSON で判定可能
- ✅ 実 baseline で smoke-run: Stage 2 step2000 vs vanilla baseline は **NOT MET** と正しく判定 (tsc −1.89pp / halluc 1.60x) → Stage 2 ギャップが再現できる

---

## 実行手順 (GPU 環境)

```bash
# 0. setup
pip install -e ".[dev]"
cd src/ts_tools && npm install && cd -

# 1. Yamato 簡易版で生成 (full mode = 言霊 + Firewall)
python3 scripts/eval/run_yamato_min.py \
  --input data/raw/multipl_e/humaneval-ts/test-00000-of-00001.parquet \
  --out-dir data/eval/generated/humaneval-ts.yamato_min \
  --custom-heads checkpoints/yamato_sft_a6000/step_2000/custom_heads.pt \
  --mode full --quantize 4bit

# 2. pass@1
python3 scripts/eval/run_tests.py \
  --generated-dir data/eval/generated/humaneval-ts.yamato_min \
  --out-dir data/eval/results/humaneval-ts.yamato_min

# 3. tsc strict / hallucination 指標
python3 scripts/eval/aux_metrics.py \
  --generated-dir data/eval/generated/humaneval-ts.yamato_min \
  --out data/eval/results/humaneval-ts.yamato_min/_aux_metrics.json

# 4. Win Condition 判定
python3 scripts/eval/judge_win_condition.py \
  --dataset humaneval-ts \
  --yamato-summary data/eval/results/humaneval-ts.yamato_min/_summary.json \
  --yamato-aux     data/eval/results/humaneval-ts.yamato_min/_aux_metrics.json \
  --baseline-stem step2000 \
  --out baselines/yamato_min.humaneval-ts.summary.json
```

ablation を測るには `--mode no-kotodama` / `--mode no-firewall` / `--mode vanilla` を順に回し、
それぞれ手順 1〜4 を別の `out-dir` で実行。

## 依存関係

```
M0 ✅ ──┬─→ M1' ✅ ──┐
        └─→ M2  ✅ ─┤
                     ▼
                   M6 ✅
```

全マイルストーン完了。次のアクションは GPU 環境での実評価、または Win 未達時の M2.5 拡張。

## やらないこと (この簡易版)

- **再学習** — Stage 2 の `custom_heads.pt` を再利用
- **Authority チケット (造化三神)** — Single Primary path では budget 管理が過剰
- **天御柱 4 Phase** — Primary 1 path で Win Condition を狙う
- **Shadow / Twin 並列** — Kotodama が効けば単一 path で足りる前提
- **Layer 4 (海原/常世/綿津見)** — 簡易版では RAG なし、型情報は TypeHead で代用
- **Layer 2 長期 feedback** — 学習しないので不要
- **iwato 前処理 / kenpou 後処理** — prompt template と tsc 直結で代替
- **TS Compiler API による symbol-aware 制約** — M2.5 候補 (Win 未達なら追加)

## 達成後 (Win Condition 通過後の拡張順)

1. tsc 通過率 不足 → **M2.5** (TS Compiler API による symbol/scope-aware 制約)
2. ハルシネーション 削減不足 → Shadow / Twin (Phase 2 並列)
3. tsc 通過率さらに不足 → 天御柱 4 Phase (左旋/右旋/合流/判定で repair loop)
4. プロンプト多様性 不足 → iwato 前処理
5. 長期改善が必要 → Layer 2 feedback + Yomi Archive 復活

世界観 (5層/天御柱/造化三神) はこのタイミングで段階的に復活させる。
