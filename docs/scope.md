# Scope — yamatoLLM 設計の TypeScript 実装

## 戦略

既存の Python 実装 (`~/yamatoLLM/yamatoLLM/kojiki_lm/`) は **13,500 LOC が完成済**。これをこのリポジトリの [current_target/](../current_target/) 配下に **再実装 + TS 翻案 + 一部新規** で書き起こす。

学習データ新規作成・追加学習・RunPod 費用は **不要**。推論時アーキテクチャの実装のみ。

## ソース実装の内訳

### A. 直接実装可能 (Julia 依存薄、論理ほぼそのまま)

`~/yamatoLLM/yamatoLLM/kojiki_lm/julia_no_mikoto/` の中で、TS でも論理がそのまま使えるもの:

| ソースファイル | LOC | 配置先 (current_target/) | TS 適応箇所 |
|------|----|---|---|
| `zoka_sanshin.py` | 372 | `kojiki_lm/zoka_sanshin.py` | なし（純粋ロジック） |
| `yomotsu_hirasaka.py` | 554 | `kojiki_lm/yomotsu_hirasaka.py` | なし |
| `yomi_evaluator.py` | 873 | `kojiki_lm/yomi_evaluator.py` | hallucination 検知のヒューリスティック関数を TS 用に置換 |
| `ashihara_runtime.py` | 579 | `kojiki_lm/ashihara_runtime.py` | なし |
| `amenomihashira.py` | 996 | `kojiki_lm/amenomihashira.py` | Phase 1/2 のプロンプトを TS 用に置換 |
| `hieda_no_are.py` | 636 | `kojiki_lm/hieda_no_are.py` | なし |
| `takamagahara_feedback.py` | 807 | `kojiki_lm/takamagahara_feedback.py` | なし |
| `layer4_unabara.py` | 755 | `kojiki_lm/layer4_unabara.py` | 4a 常世の参照データを TS 関連に差替 |
| **小計** | **5572** | | |

**作業内容**: コピー → import 修正 → TS 文字列差替 → テスト
**期間**: 1.5 週

### B. TS 翻案が大きい

| ソースファイル | LOC | 配置先 (current_target/) | TS 適応箇所 |
|------|----|---|---|
| `iwato/omoikane_intent.py` | 163 | `kojiki_lm/iwato/omoikane_intent.py` | 意図分類プロンプト、ルーティング基準を TS 文脈に |
| `iwato/kotoyosashi_protocol.py` | 228 | `kojiki_lm/iwato/kotoyosashi_protocol.py` | NL → TS コード生成指示の変換 |
| `iwato/inbe_sanitizer.py` | 373 | `kojiki_lm/iwato/inbe_sanitizer.py` | TS コード用の入出力浄化 |
| `iwato/futodama_retriever.py` | 241 | `kojiki_lm/iwato/futodama_retriever.py` | RAG 対象を TS ドキュメント (DefinitelyTyped 等) に |
| `iwato/amenouzume_decoder.py` | 218 | `kojiki_lm/iwato/amenouzume_decoder.py` | 生成制御パラメータ |
| `iwato/tajikarao_output.py` | 231 | `kojiki_lm/iwato/tajikarao_output.py` | 出力 post-process |
| `iwato/yasukawara_embedding.py` | 102 | `kojiki_lm/iwato/yasukawara_embedding.py` | 入力埋め込みラッパー |
| `kenpou/bonpu_confidence.py` | 169 | 既存 (`kenpou/bonpu_confidence.py`) | ✅ すでに存在 |
| `kenpou/shotoku_consensus.py` | 260 | `kojiki_lm/kenpou/shotoku_consensus.py` | TS 出力の同義判定基準 |
| `kenpou/kenpou_config.py` | 101 | `kojiki_lm/kenpou/kenpou_config.py` | 設定値 |
| `julia_no_mikoto/config.py` | 587 | `kojiki_lm/config.py` (既存と統合) | FiveLayerConfig を yamato_config に追加 |
| `julia_no_mikoto/layers.py` | 814 | `kojiki_lm/layers.py` | Julia 型語彙 → TS 型語彙、KojikiLM の内部層は再利用 |
| `julia_no_mikoto/model.py` | 457 | `kojiki_lm/model.py` | Qwen2 backbone と接続 |
| `julia_no_mikoto/definition_detector.py` | 160 | `kojiki_lm/definition_detector.py` | Julia の struct/function → TS の class/function/interface |
| `julia_no_mikoto/yata_kagami_attention.py` | 192 | `kojiki_lm/yata_kagami_attention.py` | なし or 削除 (Qwen attention 流用なら不要) |
| **小計** | **4296** (~3500 LOC が実際に書き換え対象) | | |

**作業内容**: ソースを参考に TS 用論理で再実装。Julia AST 検査 → TS Compiler API 呼び出しに差替
**期間**: 1 週

### C. 新規実装: 言霊 (Constrained Decoding)

yamatoLLM Python 実装にも「言霊」は概念としてはあるが、具体的な Logits 操作の TS 版は存在しない。新規実装が要る。

| 新規ファイル | LOC 目安 | 役割 |
|---|---|---|
| `kojiki_lm/kotodama_decoder.py` | 400 | logits マスク付き decode ループ |
| `scripts/ts_tools/src/valid_continuations.ts` | 500 | TS Compiler API で prefix → valid シンボル/型集合 |
| `scripts/ts_tools/src/token_mask_builder.ts` | 300 | valid 集合 → Qwen BPE トークン ID マスク (prefix tree ベース) |
| `kojiki_lm/kotodama_service.py` | 200 | Python ↔ Node 間 IPC (stdio jsonl) |
| **小計** | **1400** | |

**期間**: 1 週

### D. 統合・テスト

| ファイル | LOC | 内容 |
|---|---|---|
| `kojiki_lm/yamato_model.py` 改修 | 200 改修 | `generate()` を 天御柱オーケストレータ経由に置換、5 層連携 |
| `kojiki_lm/__init__.py` | 50 | 公開 API |
| `tests/test_zoka_sanshin.py` | 200 | Authority チケット発行・修復予算管理のテスト |
| `tests/test_yomi_evaluator.py` | 300 | 4 軸評価・閻魔判定のテスト |
| `tests/test_amenomihashira.py` | 250 | 4 Phase 連携テスト |
| `tests/test_kotodama.py` | 200 | Constrained Decoding 単体テスト |
| `tests/test_e2e.py` | 300 | humaneval-ts 1 問の end-to-end テスト |
| **小計** | **1500** | |

**期間**: 0.5 週

### 除外 (実装しない)

| ソース | 理由 |
|---|---|
| `julia_no_mikoto/training.py` (387) | 学習時コンポーネント、不要 |
| `julia_no_mikoto/moe.py` (382) | MoE 学習、不要 |
| `julia_no_mikoto/data_augmentation.py` (347) | Julia マクロ展開、TS では無関係 |
| `kenpou/wa_loss.py` (185) | 学習時損失関数 |
| `kenpou/toki_scheduler.py` (249) | 学習時スケジューラ |
| **合計除外** | **1550 LOC** |

---

## 全体スコープ

| 区分 | LOC 目安 | 期間 |
|---|---|---|
| A. 直接実装 | 5572 (修正 ~500) | 1.5 週 |
| B. TS 翻案 | 4296 (実書き換え ~3500) | 1 週 |
| C. 言霊新規 | 1400 | 1 週 |
| D. 統合・テスト | 1500 | 0.5 週 |
| **合計実装ライン** | **~8000-10000 LOC** | **約 4 週間** |

**期間目安**: 集中して 4 週間 (1 人)

## コスト

| 項目 | 必要量 |
|------|--------|
| 計算資源 | RTX 3060 12GB + Qwen2.5-Coder-7B-Instruct (既存) |
| 学習データ作成 | **不要** |
| RunPod 課金 | **0 円** |
| API 課金 | **0 円** |
| Stage 2 学習資産 | そのまま使う (custom_heads.pt) |

## 実行順 (依存関係順)

1. **Phase A** (week 1-1.5): `zoka_sanshin.py` (Authority) → `yomotsu_hirasaka.py` (Gateway) → `yomi_evaluator.py` (Layer 5) を実装。これらは天御柱から呼ばれる被依存側なので先
2. **Phase B** (week 2-2.5): `ashihara_runtime.py` → `amenomihashira.py` を実装。次に `hieda_no_are.py` → `layer4_unabara.py` → `takamagahara_feedback.py`
3. **Phase C** (week 3): `iwato/` + `kenpou/` を TS 用に翻案
4. **Phase D** (week 3.5): `kotodama_decoder.py` + TS Compiler API service を新規実装
5. **Phase E** (week 4): `yamato_model.py` 改修、e2e 統合、humaneval-ts/mbpp-ts 評価

## 評価

実装完了後:
- humaneval-ts / mbpp-ts で Stage 2 と直接比較
- 各機構の単独 ablation で寄与確認 (Authority off / 言霊 off / Shadow off など)
- Stage 2 で未達だった Win Condition (tsc strict +5pt, hallucination ×0.5) への到達確認
