# Roadmap (Minimum) — yamatoLLM TS 版

Win Condition (`tsc strict +5pt` / `hallucination ×0.5`) に最短到達するための簡易版。
フル版は [旧ドキュメント/roadmap.md](旧ドキュメント/roadmap.md) 参照。

## 売り (この簡易版で立てる 2 本柱)

1. **型予測** — Stage 2 で学習済の `TsukuyomiTypeHead` (per-token TS 型) を、
   ランタイム時に **言霊 (Kotodama)** で物理的トークンマスクとして強制する。
   ハルシネーション (存在しない型/シンボル) を生成不可能にする。
2. **ファイヤーウォール** — `yomotsu_hirasaka` で L3 (生成) と L5 (評価) を
   構造的に隔離。評価器内部状態が生成側に漏れない。

この 2 つに振り切るため、フル版の 22 モジュール (~9,200 LOC) → **5 モジュール (~1,600 LOC)** に絞る。

## 現状 (2026-05-18)

| 項目 | 状態 |
|---|---|
| Stage 1 国譲り (Qwen 重み継承) | ✅ |
| Stage 2 天孫降臨 (TypeHead/BonpuConfidence 学習) | ✅ Win Condition 未達 |
| M0 yamato_qwen サブクラス空殻 | ✅ (2026-05-18) |
| 言霊 / Firewall / Evaluator | ❌ 未実装 |

Stage 2 未達原因: 学習済 TypeHead を**呼び出す側**が存在しなかった。
M2 で「ランタイム制約として TypeHead 出力を使う」経路を立てれば、既存の学習資産を活かして Win Condition を狙える。

## やること (4 マイルストーン)

### M0 — Qwen サブクラス骨格 ✅ 完了

`YamatoQwenForCausalLM(Qwen2ForCausalLM)` を空殻として配置済。
後続 M の override 点 (generate / forward) を docstring に明記。

**Files**
- ✅ `src/kojiki_lm/yamato_qwen.py`
- ✅ `src/kojiki_lm/qwen_adapter.py` — `load_base_model` を新クラス経由に
- ✅ `scripts/eval/eval_type_head.py` — 同上

---

### M1' — Firewall + Evaluator (簡略版)

L3↔L5 境界を**型で**強制する。評価器は V_score と 3 verdict だけ返す。

**Files**
- `src/kojiki_lm/yomotsu_hirasaka.py` (~100 LOC)
  - `L3ToL5Payload` (frozen dataclass): `text`, `step_idx`, `prompt_id`
  - `L5ToL3Verdict` (frozen dataclass): `verdict ∈ {COMMIT, REPAIR, HALT}`, `v_score ∈ [0,1]`
  - `YomotsuHirasaka.send(payload) -> verdict`
- `src/kojiki_lm/yomi_evaluator.py` (~200 LOC)
  - 蛭子検知の最小実装: 型不整合スコア (TypeHead confidence × tsc local check)
  - 閻魔判定: V_score → 閾値 2 段で 3 verdict
  - Yomi Archive はカット (M1' では持たない)
- `tests/test_firewall.py` / `tests/test_evaluator.py`

**Done**
- Firewall: tensor を `L3ToL5Payload` に渡すと `TypeError`、 verdict 以外を返そうとすると拒絶
- Evaluator: ダミーテキストで V_score → verdict が決定論的に出る
- `pytest tests/` がパス

---

### M2 — 言霊 (Constrained Decoding) + generate override

**売りの本体**。M0 で空殻にした `generate` をここで埋める。
TypeHead が出した型予測を Kotodama が「次トークンが取れる型語彙」に変換、Qwen の logits に物理マスク (-inf) を乗せる。

**Files**
- `src/kojiki_lm/kotodama_decoder.py` (~400 LOC)
  - Logits マスク付き decode ループ
  - 各ステップ: TypeHead → expected type set → ts_tools 経由で valid token id 集合 → mask
  - 各 step 後に Firewall 経由で Evaluator に問い合わせ、HALT なら中断
- `src/ts_tools/src/valid_continuations.ts` (~500 LOC)
  - TS Compiler API で prefix → valid シンボル/型集合
- `src/ts_tools/src/token_mask_builder.ts` (~300 LOC)
  - valid 集合 → Qwen BPE トークン ID マスク (prefix tree)
- `src/kojiki_lm/kotodama_service.py` (~200 LOC)
  - Python ↔ Node stdio jsonl IPC
- `src/kojiki_lm/yamato_qwen.py` (改修)
  - `generate` を `kotodama_decoder` 経由に差替

**Done**
- prompt `function foo(x: ` に対し、次トークンが TS 型語彙のみにマスク (`number` / `string` 等)
- マスク前後の logits を JSON で出力、`-inf` が乗っていることをログ確認
- 1 prompt 通しで Firewall 通過 → Evaluator 判定 → COMMIT/HALT が返る

---

### M6 — e2e 評価 + Win Condition 判定

`baselines/` と直接比較。

**Files**
- `scripts/eval/run_yamato_min.py` (新規, ~150 LOC)
  - 新アーキで `humaneval-ts` / `mbpp-ts` を生成
- `tests/test_e2e.py` (1 問の end-to-end)

**評価項目**
- pass@1 / tsc strict 通過率
- ハルシネーション率 (生成コード中の未定義シンボル参照率)
- Ablation: **言霊 off** と **Firewall bypass** の 2 通り

**Win Condition**
- `tsc strict` が `baselines/humaneval-ts.step2000.summary.json` 比で **+5pt 以上**
- ハルシネーション率が **×0.5 以下**

**Done**
- `baselines/yamato_min.summary.json` を出力し、1 ファイルで達成可否判定可能

---

## 依存関係

```
M0 ✅ ──┬─→ M1' (Firewall + Evaluator)
        └─→ M2  (言霊 + generate)
                  │
                  ▼
                M6 (e2e 評価)
```

M1' と M2 は並列可。M2 の Kotodama ループは M1' の Firewall を経由するので、結合は M2 完了直前に行う。

## やらないこと (この簡易版)

- **再学習** — Stage 2 の `custom_heads.pt` を再利用
- **Authority チケット (造化三神)** — Single Primary path では budget 管理が過剰、predicate 1 本で代替
- **天御柱 4 Phase** — Primary 1 path で Win Condition を狙う
- **Shadow / Twin 並列** — Kotodama が効けば単一 path で足りる前提
- **Layer 4 (海原/常世/綿津見)** — RAG 不要、TS Compiler API で型情報は得られる
- **Layer 2 長期 feedback** — 学習しないので不要
- **iwato 前処理 / kenpou 後処理** — prompt template と tsc 直結で代替

## 達成後 (M6 通過後の拡張順)

Win Condition 達成後、未達なら以下を**根拠付きで**追加:

1. ハルシネーション削減不足 → Shadow / Twin (Phase 2 並列)
2. tsc 通過率不足 → 天御柱 4 Phase (左旋/右旋/合流/判定で repair loop)
3. プロンプト多様性不足 → iwato 前処理
4. 長期改善が必要 → Layer 2 feedback + Yomi Archive 復活

世界観 (5層/天御柱/造化三神) はこのタイミングで段階的に復活させる。
