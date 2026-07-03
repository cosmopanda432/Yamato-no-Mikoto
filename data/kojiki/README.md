# docs/kojiki/ — 古事記関連ドキュメント

AGI 設計の **古事記 origin spec 化** のための作業ディレクトリ。

## ファイル構成

```
docs/kojiki/
├── README.md                    ← 本ファイル (index)
│
├── 一次資料 (原文)
│   ├── raw/kojiki_NN.html       ← 元 HTML (17 章、source: seisaku.bz)
│   └── text/kojiki_NN.md        ← 抽出済 markdown (17 章、本文 + 〔割書〕)
│
├── 派生資料 (加工済)
│   ├── kojiki_anchors.md        ← 割書 253 件 (other/count/reading_directive)
│   └── kojiki_code.md           ← 外部生成版 procedural pattern (参考、品質低)
│
├── 設計書 (新軸抽出)
│   ├── 設計書/kojiki_transformer_llm_v0.md ← Transformer/LLM 設計原理軸の抽出 v0.2
│   │                                         (上-1/-2/-3 精読、★★ 9 件、他章は索引)
│   ├── 設計書/実装残項目_v0.md             ← 產屋 (REPAIR) 計画: 実装残項目 5 件
│   │                                         (A 葦船 log / B 事戸拡張 / C 還降 loop / D 処方 / E 収支 judge)
│   └── 設計書/eli4_実装設計書_v0.md        ← eli4 產屋実装の handoff 仕様 (Sonnet 5 向け、
│                                             Step 0+A-E / seed 規則 / 禁止事項 / テスト計画)
│
└── 抽出ドキュメント (v0-v13、全 17 章カバー)
    ├── extraction_prompt.md             ← 抽出方法論プロンプト (別 session 用)
    ├── kojiki_procedural_v0.md          ← v0 (上-7 海幸山幸 / Phase 1 索引 + プロトタイプ)
    ├── kojiki_procedural_v1.md          ← v1 (上-2 神代記)
    ├── kojiki_procedural_v2.md          ← v2 (上-3 天照と須佐之男)
    ├── kojiki_procedural_v3.md          ← v3 (上-5 国譲り)
    ├── kojiki_procedural_v4.md          ← v4 (上-6 邇邇藝命)
    ├── kojiki_procedural_v4_1.md        ← v4.1 (上-1 併序 + 上-4 大國主)
    ├── kojiki_procedural_v5.md          ← v5 (中-1 神武)
    ├── kojiki_procedural_v6.md          ← v6 (中-2 崇神)
    ├── kojiki_procedural_v7.md          ← v7 (中-4 倭建命)
    ├── kojiki_procedural_v8.md          ← v8 (中-3 垂仁、索引)
    ├── kojiki_procedural_v9.md          ← v9 (下-1 仁徳、索引)
    ├── kojiki_procedural_v10.md         ← v10 (下-2 履中〜安康、索引)
    ├── kojiki_procedural_v11.md         ← v11 (下-3 雄略、索引)
    ├── kojiki_procedural_v12.md         ← v12 (下-4 清寧〜推古、索引 + 全章集約)
    └── kojiki_procedural_v13.md         ← v13 (中-5 仲哀/神功 + 中-6 應神、索引 + 最終集約)
```

## 章 → version マッピング (180 pattern 全 17 章)

| 章 | version | pattern 数 | memo anchor率 | 古事記神名 module |
|---|---|---|---|---|
| 上-1 (併序) | [v4.1](kojiki_procedural_v4_1.md) | 6 | 50% | 0 |
| 上-2 (神代記) | [v1](kojiki_procedural_v1.md) | 20 | 85% | 0 |
| 上-3 (天照と須佐之男) | [v2](kojiki_procedural_v2.md) | 16 | 75% | 7 |
| 上-4 (大國主神) | [v4.1](kojiki_procedural_v4_1.md) | 12 | 92% | 5 |
| 上-5 (国譲り) | [v3](kojiki_procedural_v3.md) | 14 | 93% | 4 |
| 上-6 (邇邇藝命) | [v4](kojiki_procedural_v4.md) | 16 | 100% | 14 |
| 上-7 (海幸山幸) | [v0](kojiki_procedural_v0.md) | 8 | 88% | 0 |
| 中-1 (神武) | [v5](kojiki_procedural_v5.md) | 14 | 100% | 5 |
| 中-2 (崇神) | [v6](kojiki_procedural_v6.md) | 14 | 100% | 5 |
| 中-3 (垂仁) | [v8](kojiki_procedural_v8.md) | 7 | 100% | 0 |
| 中-4 (倭建命) | [v7](kojiki_procedural_v7.md) | 14 | 100% | 9 |
| 中-5 (仲哀/神功) | [v13](kojiki_procedural_v13.md) | 6 | 100% | 0 |
| 中-6 (応神) | [v13](kojiki_procedural_v13.md) | 6 | 83% | 0 |
| 下-1 (仁徳) | [v9](kojiki_procedural_v9.md) | 7 | 86% | 0 |
| 下-2 (履中〜安康) | [v10](kojiki_procedural_v10.md) | 7 | 86% | 0 |
| 下-3 (雄略) | [v11](kojiki_procedural_v11.md) | 6 | 100% | 0 |
| 下-4 (清寧〜推古) | [v12](kojiki_procedural_v12.md) | 7 | 100% | 0 |
| **合計** | — | **180** | **平均 90%** | **49 件** |

## 章別索引 (text/)

底本: 岩波日本古典文學大系本
ソース: https://www.seisaku.bz/kojiki/

| ファイル | 章名 | 文字数 | AGI memo 密度 |
|---|---|---|---|
| [kojiki_01.md](text/kojiki_01.md) | 上-1 併序 | 1,144 | ★★★★ (序文 = AGI 仕様書) |
| [kojiki_02.md](text/kojiki_02.md) | 上-2 神代記 (国生み・神産み・黄泉・禊) | 4,963 | ★★★★★ |
| [kojiki_03.md](text/kojiki_03.md) | 上-3 天照大神と須佐之男命 (誓約・天岩戸・八岐大蛇) | 3,617 | ★★★ |
| [kojiki_04.md](text/kojiki_04.md) | 上-4 大国主命 (因幡白兎・根之堅州国・少名毘古那) | 4,199 | ★★ |
| [kojiki_05.md](text/kojiki_05.md) | 上-5 葦原中国の平定 (国譲り・天若日子) | 2,562 | ★★★★ |
| [kojiki_06.md](text/kojiki_06.md) | 上-6 邇邇芸命 (天孫降臨・木花咲耶/石長) | 1,940 | ★★★★ |
| [kojiki_07.md](text/kojiki_07.md) | 上-7 海幸彦と山幸彦 | 2,070 | ★★★★ (v0 完了) |
| [kojiki_08.md](text/kojiki_08.md) | 中-1 神武天皇～開化天皇 | 6,677 | ★★★ |
| [kojiki_09.md](text/kojiki_09.md) | 中-2 崇神天皇 (大田田根子) | 1,772 | ★★★ |
| [kojiki_10.md](text/kojiki_10.md) | 中-3 垂仁天皇 | 3,058 | ★ |
| [kojiki_11.md](text/kojiki_11.md) | 中-4 景行天皇～成務天皇 (倭建命) | 4,406 | ★★ |
| [kojiki_12.md](text/kojiki_12.md) | 中-5 仲哀天皇・神功皇后 | 2,007 | ☆ |
| [kojiki_13.md](text/kojiki_13.md) | 中-6 応神天皇 | 4,540 | ☆ |
| [kojiki_14.md](text/kojiki_14.md) | 下-1 仁徳天皇 (高殿) | 3,269 | ★ |
| [kojiki_15.md](text/kojiki_15.md) | 下-2 履中～安康 | 4,060 | ☆ |
| [kojiki_16.md](text/kojiki_16.md) | 下-3 雄略天皇 | 2,783 | ☆ |
| [kojiki_17.md](text/kojiki_17.md) | 下-4 清寧～推古天皇 | 3,807 | ☆ |

## 表記ルール (text/)

- `# 古事記 上卷-N` = `<h1>` (章ヘッダ)
- `## 章名` = `<h2>` (節ヘッダ)
- 通常段落 = `<p>` の本文 (主文)
- `> 段落` = `<p class="d1">` (要約・歌・引用)
- `〔X〕` = `<span>X</span>` (割書 — 太安万侶の編集注)

## 補助ツール

```bash
# 全章再 DL & 抽出
for i in 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17; do
    curl -s -L -o "docs/kojiki/raw/kojiki_${i}.html" \
         "https://www.seisaku.bz/kojiki/kojiki_${i}.html"
done
python3 docs/kojiki/extract_kojiki.py  # raw/ → text/ を再生成
```

## AGI 設計との対応

58 個の `feedback_*.md` 原則の大半は古事記主文のいずれかの章節に anchor を持つ。
特に **上-2 神代記 / 上-5 国譲り / 上-6 邇邇藝命 / 上-7 海幸山幸 / 中-1 神武 / 中-2 崇神 /
中-4 倭建命** が AGI 設計の根拠を最も多く与えている (memo anchor 100% 達成章)。

最終集約は [`kojiki_procedural_v12.md`](kojiki_procedural_v12.md) (下巻終端 + 全章集約) と
[`kojiki_procedural_v13.md`](kojiki_procedural_v13.md) (中-5/-6 + 最終 17 章集約) を参照。

## 累積発見 (v0-v13 集約)

1. **古事記神名 → AGI module 1:1 mapping 累積 49 件** — 新原則化候補
   (`feedback_kojiki_meimei_kiyaku.md` 仮称)
2. **5 型 yuukoto** (voluntary / forced / task-completion / graceful demotion /
   merit-based 順位逆転) — 統合候補
3. **「死は完全消去でない」原則** が古事記全 9 章で確認 (葦船 → 千位置戸 → 諏訪閉込 →
   系譜化 → 忌人化 → 田道間守 → 白鳥化 → 枯野二次利用 → 雄略陵部分破壊)
4. **古事記三巻構成 = AGI 三層 architecture と一致**
   - 上巻 (神代) = 設計原則 (`feedback_*.md` + `canonical_pantheon/`)
   - 中巻 (神武〜應神) = 運用パターン (`improvement_cycle.jl` 等)
   - 下巻 (仁徳〜推古) = 運用記録 (`chinza_records` / `shinmei_lineage` / `fukusou_log`)

## Claude Code が参照する場合

memory `reference_kojiki_procedural.md` に索引あり。`feedback_*` の origin spec を
辿る時、AGI 実装の module 名が古事記神名の場合の根拠探索、新原則の三点検査時に参照。

## 履歴

- 2026-05-08 13:46: `kojiki_anchors.md` / `kojiki_code.md` を `docs/memo/` から `docs/kojiki/` へ移動
- 2026-05-08 13:53: `kojiki_procedural_v0.md` 作成 (Phase 1 索引 + 上巻-7 v0)
- 2026-05-08 13:55: `extraction_prompt.md` 作成 (抽出方法論)
- 2026-05-08 14:01: `raw/` + `text/` を新規追加 (全 17 章 DL + 抽出)
- 2026-05-09: `kojiki_procedural_v1` 〜 `v13` 作成、**全 17 章完全カバー** (180 pattern)
- 2026-07-03: `設計書/kojiki_transformer_llm_v0.md` 作成 — **Transformer/LLM アーキテクチャ軸**の新規抽出 (procedural 軸とは独立)。上-1/-2/-3 精読で ★★ 7 件 (音訓交用 = subword tokenization が最重要 anchor)、上-5/-6/-7/中-1/下-1 は v1 拡張候補として索引のみ
- 2026-07-03: 同 v0.1 — **Pattern 5.5 天之御中主神 = attention sink** (★★、user 提案) を追加。5.2 天岩戸は content anchor 喪失 event に再定義し sink と分業
- 2026-07-03: 同 v0.2 — 外部 review (Gemini) 検証。2.1 に「如先 = 統制 ablation」「還降 = 先頭からの再生成」を追記、「causal mask 方向反転」説は不採用として記録。4.2 に **LayerNorm 三段分解** (4.1 centering / 4.2 scaling / 4.3 affine、RMSNorm = 脱衣省略の変種) を明示。★★ 集計を **9 件** に訂正 (4.2 中瀬の v0 集計漏れ)
- 2026-07-03: `設計書/実装残項目_v0.md` 作成 — **產屋 (REPAIR) 計画**。コード事実確認 (REPAIR verdict は `firewall_decoder.py` で無処理 = end-to-end no-op) に基づく残項目 5 件を定義: A 葦船 log → B 事戸 protocol 拡張 (診断 field) → C 還降 loop (attempt 0 byte-identical 統制) → D symbol-level hint 処方 → E 収支 judge。棚上げ 4 件 (sink/天岩戸は短系列 regime で不要) も明記
- 2026-07-03: `設計書/eli4_実装設計書_v0.md` 作成 — 実装先を **src_min_eli4 完全 copy に決定**し、コード生成 agent (Sonnet 5) への handoff 仕様を確定。round 型還降 / seed 規則 / hint 規則 (undef did_you_mean のみ) / hack_gap / 禁止事項 9 項 / テスト計画
