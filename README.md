# Yamato-no-Mikoto

yamatoLLM の TypeScript 型認識特化版を実装するリポジトリ。設計ドキュメントと実装本体を 1 箇所に集約する。

## このリポジトリの目的

このリポジトリ自体で yamatoLLM 設計の TypeScript 版を実装する。
設計の正史・実装規模・神名↔技術役割マッピング、そして実装本体を 1 箇所にまとめる。

## 一次情報源

- yamatoLLM 設計書群: `~/yamatoLLM/yamatoLLM/docs/`
- yamatoLLM 既存 Python 実装: `~/yamatoLLM/yamatoLLM/kojiki_lm/`
- 実装先 (TypeScript 版): このリポジトリの [current_target/kojiki_lm/](current_target/kojiki_lm/)
- Julia-no-Mikoto 設計原典: `~/Julia-no-Mikoto/Julia-no-Mikoto/docs/julia_no_mikoto_design_v2.md`

## このリポジトリの構成

```
Yamato-no-Mikoto/
├── README.md                  ← この文書
├── docs/                      ← 設計ドキュメント
│   ├── architecture.md        ← 5 層構造の全体像
│   ├── scope.md               ← 移植規模・タイムライン
│   └── glossary.md            ← 神名 ↔ 技術役割マッピング
├── source_reference/          ← 移植元 (yamatoLLM Python 実装、READ-ONLY)
│   ├── julia_no_mikoto/       ← 5 層 + KojikiLM 内部 (17 files, 9047 LOC)
│   ├── iwato/                 ← 言語処理層 (8 files, 1591 LOC)
│   └── kenpou/                ← ガバナンス層 (6 files, 993 LOC)
├── current_target/            ← 実装ディレクトリ本体 (TypeScript 版 yamatoLLM)
│   ├── kojiki_lm/             ← Qwen integration + TypeHead + BonpuConfidence
│   ├── scripts/               ← train / eval / data / ts_tools
│   └── config/                ← ts_type_vocab.json 他
├── checkpoints/               ← Stage 2 学習済資産 (29MB)
│   └── step_2000/             ← custom_heads.pt + training_log.json
└── baselines/                 ← 評価結果 (baseline と Stage 2 比較用)
    ├── humaneval-ts.{baseline,step2000}.{summary,aux}.json
    ├── mbpp-ts.{baseline,step2000}.{summary,aux}.json
    └── type_head.{random_init,step2000}.json
```

### 設計ドキュメント

| ファイル | 内容 |
|---------|------|
| [docs/architecture.md](docs/architecture.md) | 設計の全体像（5 層 + 横断 + 天御柱 4 Phase + 言霊） |
| [docs/scope.md](docs/scope.md) | 移植規模、ファイル対応表、タイムライン |
| [docs/glossary.md](docs/glossary.md) | 神名 ↔ 技術役割マッピング表 |

### コードとデータの使い方

- `source_reference/` は**参照のみ**。Python 13,500 LOC の既存実装をそのまま閲覧。実装時はここを読みながら `current_target/` に TypeScript で再実装する。
- `current_target/` が**実装ディレクトリ本体**。yamato-public からの 2026-05-18 時点スナップショットを出発点とし、以降の編集はすべてここで行う。
- `checkpoints/step_2000/custom_heads.pt` は Stage 2 SFT で学習済の TsukuyomiTypeHead + BonpuConfidence パラメータ (14.82M params)。新アーキテクチャでも再利用可能。
- `baselines/` は Win Condition 判定の数値根拠。新実装の評価では必ずこれと比較する。

## 現状サマリ

- Stage 1 国譲り (Qwen2.5-Coder-7B-Instruct 重み継承 + ヘッド初期化): ✅ 完了
- Stage 2 天孫降臨 (QLoRA SFT, ManyTypes4TS): ✅ 学習完了。Win Condition は未達。理由: **設計の核 (5 層 + 横断 + 天御柱 4 Phase + 言霊) がほぼ未実装** だったため、TypeHead が単独存在しても生成に転移しない
- Stage 3 禊以降: 着手前。**先に 5 層構造を [current_target/](current_target/) に実装する**のが本来の道

## 重要原則

**構造でハルシネーションを起こさせない**。

検知 → リトライ型の事後監視ではなく、生成プロセス自体を制約することで不正出力が**物理的に起こり得ない**形にする。これは複数の構造機構（順序制約・チケット制 Authority・言霊 Logits 操作・Shadow/Twin 並列・黄泉比良坂 firewall・修復予算・閻魔判定）の合成で実現される。単一機構だけでは効かない。

詳細は [docs/architecture.md](docs/architecture.md) を参照。
