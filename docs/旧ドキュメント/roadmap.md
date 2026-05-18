# Roadmap (Full) — yamatoLLM TS 版実装

[architecture.md](architecture.md) が要求する **5 層 + 横断 + 天御柱 4 Phase + 言霊** を `src/` に積むまでの順序 (フル版、~9,200 LOC)。

実装パスは **簡易版** [roadmap_min.md](roadmap_min.md) に切替。フル版は Win Condition 達成後の拡張参照用として保持。

## 現状 (2026-05-18)

| 項目 | 状態 |
|---|---|
| Stage 1 国譲り (Qwen 重み継承 + ヘッド初期化) | ✅ 完了 |
| Stage 2 天孫降臨 (QLoRA SFT, ManyTypes4TS) | ✅ 学習完了、Win Condition 未達 |
| 5 層 / 横断 / 天御柱 / 言霊 | ❌ ほぼ未実装 |
| src/ レイアウト、pyproject、データ/モデルローカル配置 | ✅ 整備済 |
| Qwen 改造方針 | ✅ サブクラス化で確定 ([memory](../.claude/projects/-home-matsu-Yamato-no-Mikoto/memory/project_qwen_subclass_direction.md)) |

Stage 2 で Win Condition 未達だった原因は明確: TypeHead と BonpuConfidence を訓練しても、それを呼び出すべき **5 層オーケストレータ・言霊・Authority** が一つも存在しないため、ヘッドが「単独で島になっている」。Phase A 以降はその島同士を繋ぐ作業。

## 前提

- 実装は `src/kojiki_lm/` 配下に集約。`source_reference/` (Python 13,500 LOC) は参照のみ
- Qwen2.5-Coder-7B は **fork / サブクラス化** で扱う。`YamatoQwenForCausalLM(Qwen2ForCausalLM)` を作り、forward と generate の internal を改造
- Stage 2 学習済 `custom_heads.pt` (14.82M params) は新アーキ上でも attach 可能な構成を維持
- Win Condition: [baselines/](../baselines/) と直接比較し、`tsc strict +5pt` / `hallucination ×0.5` を達成

## マイルストーン

依存関係順。各 M の Done は **観測可能な単一条件** に揃える。

### M0 — Qwen サブクラスの骨格

`YamatoQwenForCausalLM` を空殻として立てる。中身の hook 点は後続 M で順次埋める。

**Files**
- `src/kojiki_lm/yamato_qwen.py` (新規) — `class YamatoQwenForCausalLM(Qwen2ForCausalLM)`
- `src/kojiki_lm/yamato_model.py` (改修) — 既存 wrapper をこの新クラスに乗せ替え

**Override 想定箇所** (この M ではまだ空、コメントだけ残す)
- `forward`: 各 decoder layer 出力を 5 層オーケストレータに渡す hook
- `generate`: 言霊 logits 操作と Authority チケット消費を組み込む自前ループに置換予定
- `Qwen2DecoderLayer` の attention: `yata_kagami_attention` で置換予定

**Done**: `YamatoQwenForCausalLM.from_pretrained("models/Qwen2.5-Coder-7B-Instruct")` で重みロードし、既存 `custom_heads.pt` を attach した上で、`scripts/eval/eval_type_head.py` が同じ数値を出す (回帰なし)。

---

### M1 — Phase A: 被依存側 3 点 (Authority / Gateway / Layer 5)

天御柱から呼ばれる側を先に立てる。これがないと天御柱 (M3) が依存先を解決できない。

**Files** (`source_reference/julia_no_mikoto/` から TS 文脈へ翻案)
- `src/kojiki_lm/zoka_sanshin.py` (← 372 LOC) — 造化三神: AmeNoMinakaNushi (閾値原点) / Takamimusubi (生成チケット) / Kamimusubi (修復チケット)
- `src/kojiki_lm/yomotsu_hirasaka.py` (← 554 LOC) — 黄泉比良坂 firewall: L3↔L5 一方向通信、ペイロード制約
- `src/kojiki_lm/yomi_evaluator.py` (← 873 LOC) — 蛭子検知 (4 軸) + 閻魔判定 (V_score → COMMIT/REPAIR/HALT) + YomiArchive

**Done**: 3 ファイルそれぞれに単体テストを置き、`pytest src/kojiki_lm/` がパス。
- Authority: ticket 発行 → 消費 → budget 超過で HALT
- Gateway: L3→L5 はテキスト通す、L5→L3 は数値 + verdict のみ通す
- Evaluator: ダミー出力に対し V_score 計算 → 閾値判定が動く

---

### M2 — 言霊 (Constrained Decoding) + Qwen generate override

「ハルシネーションを物理的に発生不可能にする」核機構。M0 で空殻にしておいた `generate` をここで埋める。

**Files** (新規実装、Python 設計書にはコンセプトのみ存在)
- `src/kojiki_lm/kotodama_decoder.py` (~400 LOC) — Logits マスク付き decode ループ
- `src/ts_tools/src/valid_continuations.ts` (~500 LOC) — TS Compiler API で prefix → valid シンボル/型集合
- `src/ts_tools/src/token_mask_builder.ts` (~300 LOC) — valid 集合 → Qwen BPE トークン ID マスク (prefix tree ベース)
- `src/kojiki_lm/kotodama_service.py` (~200 LOC) — Python ↔ Node 間 IPC (stdio jsonl)
- `src/kojiki_lm/yamato_qwen.py` (改修) — `generate` を `kotodama_decoder` 経由に差替

**Done**: `function foo(x:` を prompt として与えると、次トークンは **TS 型語彙のみ** にマスクされ、`number` / `string` 等しか出ない (logit = -∞ で物理的にマスクされていることをログで確認)。

---

### M3 — 天御柱 4 Phase + Layer 4 ブリッジ + ランタイム本体

5 層を順序駆動する中枢。

**Files**
- `src/kojiki_lm/amenomihashira.py` (← 996 LOC) — 天御柱: Phase 1 左旋 / Phase 2 右旋 / Phase 3 合流 / Phase 4 判定
- `src/kojiki_lm/ashihara_runtime.py` (← 579 LOC) — Layer 3 ランタイム本体
- `src/kojiki_lm/hieda_no_are.py` (← 636 LOC) — 稗田阿礼: L4 → L3 context bridge
- `src/kojiki_lm/layer4_unabara.py` (← 755 LOC) — Layer 4: 常世 (静的) / 海原 (動的) / 綿津見 (Gateway)
- `src/kojiki_lm/takamagahara_feedback.py` (← 807 LOC) — Layer 2 への長期 feedback (Yomi Archive 連携)

この時点では **Primary 生成のみ** で 4 Phase を完走させる。Shadow/Twin は M4。

**Done**: 1 つの prompt に対し Phase 1→2→3→4 が順序通り実行され、Authority チケットが各遷移で消費され、Layer 5 評価を経て COMMIT/REPAIR/HALT が返る。end-to-end ログでフェーズ遷移が観測可能。

---

### M4 — Shadow / Twin 並列 + Deliberation

Phase 2 右旋に並列パスを足す。単一誤生成の通過率を構造的に下げる。

**Files** (主に `amenomihashira.py` の改修)
- Primary path に加え Shadow / Twin path を並列起動
- 3 path の出力を Deliberation (Stage 3) で比較統合
- Authority チケットは 3 path 分発行

**Done**: 同じ prompt で Shadow / Twin が並列に走り、3 path のうち Primary が hallucinate しても Shadow / Twin が catch するケースを 1 件以上テストで再現。

---

### M5 — iwato / kenpou 翻案 (入出力前後処理)

入力前処理と出力後処理を 5 層に組み込む。

**Files** (`source_reference/iwato/` ・ `source_reference/kenpou/` から TS 翻案)
- `src/kojiki_lm/iwato/omoikane_intent.py` (← 163 LOC) — 意図分類
- `src/kojiki_lm/iwato/kotoyosashi_protocol.py` (← 228 LOC) — NL → TS コード生成指示
- `src/kojiki_lm/iwato/inbe_sanitizer.py` (← 373 LOC) — 入出力浄化
- `src/kojiki_lm/iwato/futodama_retriever.py` (← 241 LOC) — RAG (DefinitelyTyped 等)
- `src/kojiki_lm/iwato/amenouzume_decoder.py` (← 218 LOC) — 生成制御パラメータ
- `src/kojiki_lm/iwato/tajikarao_output.py` (← 231 LOC) — 出力 post-process
- `src/kojiki_lm/iwato/yasukawara_embedding.py` (← 102 LOC) — 入力埋め込みラッパー
- `src/kojiki_lm/kenpou/shotoku_consensus.py` (← 260 LOC) — TS 出力の同義判定
- `src/kojiki_lm/kenpou/kenpou_config.py` (← 101 LOC) — 設定値

**Done**: 自然言語 prompt → iwato で前処理 → 天御柱 → tajikarao で後処理 → 最終 TS コード、の流れが end-to-end で通る。

---

### M6 — e2e 評価 + Win Condition 判定

実装が揃ったところで `baselines/` と直接比較する。

**Files**
- `src/kojiki_lm/__init__.py` — 公開 API (現状空)
- `tests/test_e2e.py` (新規、`humaneval-ts` 1 問の end-to-end)
- `scripts/eval/run_yamato.py` (新規、または既存 generate_multipl_e.py 改修) — 新アーキで baselines と同条件で生成

**評価項目**
- humaneval-ts / mbpp-ts: pass@1, tsc strict 通過率
- type_head 精度 (M0 で回帰なしを担保した上で再測)
- Ablation: Authority off / 言霊 off / Shadow off の 3 通り
- Win Condition: tsc strict が `baselines/humaneval-ts.step2000.summary.json` 比で **+5pt 以上**、hallucination 率が **×0.5 以下**

**Done**: `baselines/` と新生成結果を JSON で並列比較したレポート (`baselines/yamato_full.summary.json` 等) を作成、Win Condition の達成可否を 1 ファイルで判定可能にする。

---

## 依存関係グラフ

```
M0 (Qwen subclass) ──┬─→ M1 (Authority/Gateway/Evaluator)
                      └─→ M2 (言霊 + generate override)
                              │
                              ▼
                            M3 (天御柱 4 Phase + Layer 4)
                              │
                              ▼
                            M4 (Shadow/Twin)
                              │
                              ▼
                            M5 (iwato/kenpou)
                              │
                              ▼
                            M6 (e2e 評価)
```

M1 と M2 は並列可。それ以外は直列。

## やらないこと (現時点で)

- 再学習 — Stage 2 の `custom_heads.pt` を再利用、追加 SFT は M6 で必要性判明してから検討
- ts_tools 以外の Node サブシステム導入 — 言霊で必要な範囲のみ
- マルチセッション / Multi-user 機構 — Layer 4 海原 (動的) のスコープに将来含むが M3 では空 stub
- llm-jp-4 等の他 backbone 切り替え — Qwen2.5-Coder 一本で評価まで通す

## 振り返り

各 M 完了時に [README.md](../README.md) 現状サマリと [memory](../.claude/projects/-home-matsu-Yamato-no-Mikoto/memory/) を更新する。M3 終了時点で当初設計の仮定が破綻していたらここを書き換える。
