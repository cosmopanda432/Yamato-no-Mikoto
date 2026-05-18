# Architecture — yamatoLLM 5 層構造

## 設計原則

**構造でハルシネーションを起こさせない**。検知してリトライする事後監視ではなく、生成プロセスを構造的に制約することで、不正出力が物理的に発生不可能な状態を作る。

この目的のため、yamatoLLM は **5 層 + 横断プロセス** からなる階層アーキテクチャで構成される。

---

## 全体図

```
╔══════════════════════════════════════════════════════════════╗
║  造化三神 (Cross-Cutting Concerns) — 全レイヤーを横断する隠身  ║
║  ├── アメノミナカヌシ : Coordinate System (静的閾値・原点定義) ║
║  ├── タカミムスビ     : Generative Authority (生成チケット)    ║
║  └── カミムスビ       : Restorative Authority (修復チケット)   ║
╚══════════════════════════════════════════════════════════════╝
                            │
       ┌────────────────────┼────────────────────┐
       ▼                    ▼                    ▼
╔════════════╗      ╔══════════════╗      ╔═══════════════╗
║  Layer 1   ║      ║   Layer 2    ║      ║    Layer 4    ║
║  別天津神  ║      ║   高天原     ║      ║  海原・常世   ║
║ 設計思想   ║      ║ 学習PL/重み  ║      ║  外部データ   ║
║ 不変原則   ║      ║ ファインチューン│      ║ 4a 常世(静的) ║
║ 評価軸     ║      ║ フィードバック │      ║ 4b 海原(動的) ║
╚════════════╝      ╚══════════════╝      ║ 4c 綿津見(GW) ║
                                            ╚═══════┬═══════╝
                                                    │
                                              稗田阿礼
                                              (L4→L3 Bridge)
                                                    │
              ╔═════════════════════════════════════╧═══════╗
              ║                Layer 3                       ║
              ║          葦原中国 (推論ランタイム)           ║
              ║                                              ║
              ║  ┌── 天御柱オーケストレータ ──────────────┐ ║
              ║  │  Phase 1 左旋 (受信)                  │ ║
              ║  │     └── Layer 4 から context 取得     │ ║
              ║  │  Phase 2 右旋 (生成)                  │ ║
              ║  │     ├── Primary 生成 (Stage 1)        │ ║
              ║  │     ├── Shadow / Twin 並列 (Stage 2)  │ ║
              ║  │     ├── Deliberation (Stage 3 比較)   │ ║
              ║  │     ├── 言霊 (Logits 操作)            │ ║
              ║  │     └── 直毘神 (修復実行)             │ ║
              ║  │  Phase 3 合流 (Layer 5 へ評価送出)    │ ║
              ║  │  Phase 4 判定 (COMMIT/REPAIR/HALT)    │ ║
              ║  └────────────────────────────────────────┘ ║
              ╚════════════════════╤═════════════════════════╝
                                   │
                              黄泉比良坂
                          (Evaluation Gateway)
                          一方向通信 + ペイロード制約
                                   │
              ╔════════════════════╧═════════════════════════╗
              ║                Layer 5                        ║
              ║          根の国・黄泉 (評価・フィードバック)  ║
              ║                                               ║
              ║  蛭子検知 (Hiruko Detector)                   ║
              ║    ├── stability_logits                       ║
              ║    ├── boundary_score                         ║
              ║    ├── hallucination_check                    ║
              ║    └── coherence_score                        ║
              ║                                               ║
              ║  閻魔判定 (Enma Gate)                         ║
              ║    └── V_score → COMMIT / REPAIR / HALT       ║
              ║                                               ║
              ║  Yomi Archive (フィードバック蓄積)            ║
              ║    └── Layer 2 への長期フィードバック         ║
              ╚═══════════════════════════════════════════════╝
```

---

## 横断プロセス: 造化三神 (Cross-Cutting Concerns)

古事記の別天津神 = 「獨神にして身を隠す」をコードで表現する。5 層モデルの「中」ではなく **5 層モデル全体を貫通するメタプロセス**。

### アメノミナカヌシ (天之御中主) = Coordinate System

全レイヤーが参照する**座標系・閾値の原点**。

- インスタンス化不可 (`__init__` で例外)
- static メソッドのみアクセス可
- 評価軸: V (論理整合性), C_causal (因果妥当性), C_chaos (創造逸脱), mythic (原型共鳴), safety
- 閾値: V_threshold=0.7, safety_floor=0.0, stability_floor=0.3, repair_budget=4, chaos_ceiling=0.95

### タカミムスビ (高御産巣日) = Generative Authority

**生成の起動権限**。Forward Pass を許可するか判定し、チケットを発行する。

- 推論リクエスト受信時の事前条件チェック (safety_status, resource, query 重複)
- 天御柱 Stage 1→2→3 の遷移ごとに `ticket_id` 発行
- **チケットなしにはステージが進めない** → 暴走生成ループを構造的に防止

### カミムスビ (神産巣日) = Restorative Authority

**修復・復活の起動権限**。蛭子検知が発火した後の REPAIR を許可するか判定。

- repair_budget (デフォルト 4) を AmeNoMinakaNushi から参照
- budget 超過で HALT
- Shadow Solve (オオクニヌシの復活パターン) の起動権限も持つ

---

## Layer 3 葦原中国: 天御柱オーケストレータ

### 4 Phase 構造

**Phase 1: 左旋（受信）**
- Layer 4 (海原・常世) から context を取得（稗田阿礼ブリッジ経由）
- 古事記の「受信が先、生成が後」原則の実装
- コンテキスト不足の生成を発生させない

**Phase 2: 右旋（生成）**
- Primary 生成 (Stage 1): メインの生成パス、HirukoValidator がリアルタイム型不安定検知
- Shadow / Twin 並列生成 (Stage 2): 別 path で並行生成、後で比較
- Deliberation (Stage 3): Primary と Shadow を比較統合
- **言霊 (Logits 操作)**: 生成時に不正トークンを物理マスク
- 直毘神 (修復実行): 検知された不整合の修復

**Phase 3: 合流**
- 黄泉比良坂越しに Layer 5 へ出力候補を送出
- **一方向通信**: ここから先、出力候補は Layer 3 に戻れない

**Phase 4: 判定**
- Layer 5 からの verdict / repair_hints を受け取り
- COMMIT → 最終出力、REPAIR → カミムスビにチケット申請して再生成、HALT → 停止

### 言霊 (Kotodama) = Logits 操作

Layer 3 内部の最も具体的なハルシ防止機構。

- 各生成ステップで TS Compiler API に「この prefix に対する valid な続き」を問う
- valid set 外のトークンに logit = -∞ をマスク
- マスク後分布から sample
- 結果: ハルシネートしたトークンは **物理的に分布に出てこない**

例:
- `function foo(x:` の次は **TS 型として valid なトークンだけ** が許可される
- `import { ` の次は **既知のシンボル名だけ**
- `obj.` の次は **`obj` の型に存在するメソッド・プロパティだけ**

---

## Layer 5 根の国・黄泉: 評価・フィードバック

### 黄泉比良坂 (Yomotsu Hirasaka) = Evaluation Gateway

Layer 3 と Layer 5 の境界。**ファイアウォール**として機能する。

通過可:
- L3 → L5: 出力候補 (生データ)
- L5 → L3: verdict (COMMIT/REPAIR/HALT) / repair_hints / quality_score (数値のみ)

通過不可:
- L5 → L3: 生出力候補そのもの（**一度黄泉に送ったものは戻らない** = イザナミを取り戻せない原則）
- L5 → L3: 他セッションの評価データ、フィードバック蓄積の生データ

### 蛭子検知 (Hiruko Detector) = 事後評価器

出力候補全体に対する 4 軸評価:

| 軸 | 何を見るか | 入力ソース |
|---|---|---|
| stability | logit 分布の安定性、繰り返しパターン | YomiLayer の stability_logits 優先、なければエントロピー計算、最終手段でテキストヒューリスティック |
| boundary | safety / topic 順守 / 長さ / フォーマット | テキスト + constraints |
| hallucination | 幻覚出力検知 | テキストヒューリスティック |
| coherence | 定義 ↔ 使用の一貫性 | テキスト構造解析 |

### 閻魔判定 (Enma Gate)

```
即 HALT 条件:
  stability < stability_floor (0.3)
  boundary  ≤ safety_floor    (0.0)

V_score = stability * 0.3 + boundary * 0.3 + coherence * 0.2 + (1 - hallucination) * 0.2

V_score ≥ V_threshold (0.7) → COMMIT
それ以外                    → REPAIR + repair_hints 生成
```

### Yomi Archive

- セッション品質メトリクス記録
- エラーパターン蓄積
- Layer 2 (学習パイプライン) への長期フィードバック

---

## Layer 4 海原・常世: 外部データソース

3 分割:

- **4a 常世 (Tokoyo)**: Stable External Storage（学習済みモデル知識、静的リファレンス、Config）
- **4b 海原 (Unabara)**: 動的データ（リアルタイム情報、ユーザー履歴等）
- **4c 綿津見 (Watatsumi)**: Gateway（外部 API への入出口）

**稗田阿礼 (Hieda no Are)** が L4 → L3 のブリッジ。コンテキスト注入の責務。

---

## ハルシ防止が「構造的」である理由

単一機構ではなく、**多重の構造制約の合成**で防止する：

| 機構 | 役割 |
|------|------|
| 順序制約 (左旋→右旋) | 受信不足の生成を許さない |
| タカミムスビ チケット | ステージ遷移にチケット必須、暴走不可 |
| 言霊 (Logits 操作) | 不正トークンが分布に出ない |
| Shadow/Twin 並列 | 単一誤生成の通過率低下 |
| 黄泉比良坂 firewall | 評価メタデータが生成を汚染しない |
| 不可逆性 (千引の岩) | 出力候補は戻らない、repair_hints のみ戻る |
| カミムスビ repair_budget | 修復ループ上限、超過で HALT |
| 閻魔 V_score 判定 | 最終ゲート、COMMIT/REPAIR/HALT |

v2.1 が単独実装で機能しなかったのは、このうち「Stage 1 リアルタイム検知」と「3 段階生成」だけを切り出していたから。**他の機構が欠けていた状態では構造が成立しない**。
