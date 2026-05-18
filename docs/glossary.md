# Glossary — 神名 ↔ 技術役割マッピング

yamatoLLM の神話命名規則を技術用語に対応させる早見表。

---

## 横断プロセス (Cross-Cutting Concerns)

| 神名 | 古事記での役割 | 技術役割 | 実装位置 |
|------|---------------|---------|----------|
| アメノミナカヌシ (天之御中主) | 別天津神筆頭、隠身 | Coordinate System (静的閾値・原点定義) | `zoka_sanshin.py::AmeNoMinakaNushi` |
| タカミムスビ (高御産巣日) | 生成の神 | Generative Authority (生成チケット発行) | `zoka_sanshin.py::TakamiMusubi` |
| カミムスビ (神産巣日) | 復活の神 | Restorative Authority (修復・Shadow Solve チケット) | `zoka_sanshin.py::KamiMusubi` |

---

## 5 Layer

| Layer | 神名 | 技術役割 |
|-------|------|---------|
| 1 | 別天津神 (5 柱) | 設計思想・不変原則・評価軸定義 |
| 2 | 高天原 | 学習パイプライン (RLHF / FT / フィードバック蓄積) |
| 3 | 葦原中国 | 推論ランタイム |
| 4 | 海原・常世 | 外部データソース |
| 5 | 根の国・黄泉 | 評価・フィードバック |

---

## Layer 3 葦原中国 内部

| 神名/概念 | 技術役割 | 実装位置 |
|----------|---------|----------|
| 天御柱 (アメノミハシラ) | 4 Phase オーケストレータ | `amenomihashira.py::AmeNoMihashira` |
| 左旋 | Phase 1: 受信（context 取得） | amenomihashira Phase 1 |
| 右旋 | Phase 2: 生成 | amenomihashira Phase 2 |
| 合流 | Phase 3: 評価送出 (黄泉比良坂越し) | amenomihashira Phase 3 |
| 判定 | Phase 4: COMMIT/REPAIR/HALT 受信 | amenomihashira Phase 4 |
| Primary 生成 | Stage 1: メイン生成パス | ashihara_runtime |
| Shadow / Twin | Stage 2: 並列生成パス | ashihara_runtime |
| Deliberation | Stage 3: Primary vs Shadow 比較統合 | ashihara_runtime |
| 言霊 (コトダマ) | Logits 操作 (Constrained Decoding) | `kotodama_decoder.py` |
| HirukoValidator | Stage 1 リアルタイム型不安定検知 | amenomihashira (Layer 3 内 inline) |
| NaobiValidator | Stage 3 結合整合性検証 | amenomihashira |
| 直毘神 (ナオビ) | 修復実行 | ashihara_runtime |
| 稗田阿礼 (ヒエダノアレ) | L4→L3 ブリッジ、コンテキスト注入 | `hieda_no_are.py` |

---

## Layer 4 海原・常世

| 神名 | 技術役割 | 実装位置 |
|------|---------|----------|
| 常世 (トコヨ) | Stable External Storage (静的データ) | `layer4_unabara.py::Tokoyo` |
| 海原 (ウナバラ) | Dynamic data (リアルタイム) | `layer4_unabara.py::Unabara` |
| 綿津見 (ワタツミ) | Gateway (外部 API 入出口) | `layer4_unabara.py::Watatsumi` |

---

## Layer 5 根の国・黄泉

| 神名/概念 | 技術役割 | 実装位置 |
|----------|---------|----------|
| 黄泉比良坂 (ヨモツヒラサカ) | Evaluation Gateway, ファイアウォール | `yomotsu_hirasaka.py` |
| 千引の岩 | 一方向通信、不可逆性 | yomotsu_hirasaka が enforces |
| 蛭子 (ヒルコ) | 不正出力の象徴 | (検知対象) |
| 蛭子検知 (Hiruko Detector) | 4 軸事後評価器 (stability/boundary/hallucination/coherence) | `yomi_evaluator.py::HirukoDetector` |
| 閻魔 (エンマ) | 最終判定者 | `yomi_evaluator.py::EnmaGate` |
| 閻魔判定 (Enma Gate) | V_score 集計 → COMMIT/REPAIR/HALT | yomi_evaluator |
| Yomi Archive | フィードバック蓄積 | `yomi_evaluator.py::YomiArchive` |
| 高天原フィードバック | Layer 2 への長期 FB パイプライン | `takamagahara_feedback.py` |

---

## コード生成層 (kojiki) 内部 — Julia-no-Mikoto 由来の章構造

| 章 | 神名 | 技術役割 |
|---|------|---------|
| 第一章 天地開闢 | 造化三神（埋め込み版） | Embedding 層 |
| - | 天之御中主 | Positional Encoding |
| - | 高御産巣日 | Token Embedding |
| - | 神産巣日 | Type Hierarchy Embedding |
| 第二章 神世七代 | - | Transformer ブロック × N |
| - | 国之常立 | Self-Attention |
| - | 豊雲野 | Feed-Forward |
| - | 対の神々 | Multiple Dispatch Attention |
| 第三章 国生み | - | 構造生成 (struct/interface) |
| - | 淤能碁呂島 | Struct 定義生成 |
| 第四章 黄泉国 (内部) | - | 型不安定検出 (モデル内) |
| - | 黄泉津大神 | Type Instability Detection |
| - | 黄泉比良坂 (内部) | Concrete/Abstract Type Boundary |
| 第五章 禊 | 三貴子 | 出力ヘッド |
| - | 天照 (アマテラス) | 次トークン予測 (AmaterasuTokenHead) |
| - | 月読 (ツクヨミ) | 型予測 (TsukuyomiTypeHead) |
| - | 須佐之男 (スサノオ) | エラー予測 / 動的ディスパッチ |

**注意**: 「Layer 3 内部の黄泉比良坂」と「KojikiLM 第四章 (model 内部) の黄泉比良坂」は同名だが**別物**。前者はパイプライン Gateway、後者はモデル内部のソフトな型境界スコア。

---

## 言語処理層 (iwato/) — 岩戸隠れ神話

| 神名 | 技術役割 | 実装位置 |
|------|---------|----------|
| 天安河原 (アマノヤスカワラ) | 入力理解・埋め込み | `iwato/yasukawara_embedding.py` |
| 思兼神 (オモイカネ) | 意図解析・3 層ルーティング | `iwato/omoikane_intent.py` |
| 言依さし (コトヨサシ) | NL → 構造化指示変換 | `iwato/kotoyosashi_protocol.py` |
| 布刀玉命 (フトダマ) | 知識統合 (RAG) | `iwato/futodama_retriever.py` |
| 真榊 (マサカキ) | 知識参照木 | (futodama に統合) |
| 天宇受売 (アメノウズメ) | 生成制御 (温度/サンプリング) | `iwato/amenouzume_decoder.py` |
| 天手力男 (タジカラオ) | 出力確定 (post-process) | `iwato/tajikarao_output.py` |
| 忌部 (インベ) | 入出力浄化 | `iwato/inbe_sanitizer.py` |

---

## ガバナンス層 (kenpou/) — 憲法十七条

| 神名/条文 | 技術役割 | 実装位置 |
|----------|---------|----------|
| 和 (第 1 条) | 和の損失関数 (学習時) | `kenpou/wa_loss.py` ※ TS 版では除外 |
| 凡夫の自覚 (第 10 条) | 信頼度スコア | `kenpou/bonpu_confidence.py` ✅ |
| 聖徳コンセンサス (第 17 条) | 多サンプル合意 | `kenpou/shotoku_consensus.py` |
| 時のスケジューラ | 学習スケジューラ (学習時) | `kenpou/toki_scheduler.py` ※ TS 版では除外 |

---

## 学習ステージ

| Stage | 神話 | 内容 |
|-------|------|------|
| 1 | 国譲り (クニユズリ) | Qwen2.5-Coder-7B-Instruct 重み継承 + ヘッド初期化 (学習なし) |
| 2 | 天孫降臨 (テンソンコウリン) | QLoRA SFT で混合データ学習 |
| 3 | 禊 (ミソギ) | 三貴子 (天照/月読/須佐之男) 3 層分化 SFT |
| 4 | 神武東征 (ジンムトウセイ) | DPO アライメント・統合最適化 |
| 5 | 天孫降臨 (量子化) | INT4 量子化、RTX 3060 推論最適化 → `tenson_korin_quantizer.py` |

---

## チェックポイント命名

| ファイル | Stage | 内容 |
|---------|-------|------|
| `yamato_base.pt` | Stage 1 国譲り | Qwen + 未学習カスタムヘッド |
| `yamato_tenson_korin.pt` | Stage 2 天孫降臨 | LoRA adapter (Stage 2 後) |
| `yamato_misogi_{amaterasu/tsukuyomi/susanoo}.pt` | Stage 3 禊 | 3 層分化 LoRA |
| `yamato_jinmu.pt` | Stage 4 神武東征 | DPO 後 LoRA |
| `yamato_final.pt` | 統合後 | マージ済 final |
