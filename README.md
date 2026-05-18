# Yamato-no-Mikoto

yamatoLLM の TypeScript 型認識特化版を実装するリポジトリ。設計ドキュメントと実装本体を 1 箇所に集約する。

## このリポジトリの目的

このリポジトリ自体で yamatoLLM 設計の TypeScript 版を実装する。
設計の正史・実装規模・神名↔技術役割マッピング、そして実装本体を 1 箇所にまとめる。

## 一次情報源

- yamatoLLM 設計書群: `~/yamatoLLM/yamatoLLM/docs/`
- yamatoLLM 既存 Python 実装: `~/yamatoLLM/yamatoLLM/kojiki_lm/`
- 実装先 (TypeScript 版): このリポジトリの [src/](src/)
- Julia-no-Mikoto 設計原典: `~/Julia-no-Mikoto/Julia-no-Mikoto/docs/julia_no_mikoto_design_v2.md`

## このリポジトリの構成

```
Yamato-no-Mikoto/
├── README.md                  ← この文書
├── docs/                      ← 設計ドキュメント
│   ├── architecture.md        ← 5 層構造の全体像
│   ├── scope.md               ← 移植規模・タイムライン
│   └── glossary.md            ← 神名 ↔ 技術役割マッピング
├── src/                       ← 実装本体
│   ├── kojiki_lm/             ← Python core (Qwen integration + TypeHead + BonpuConfidence)
│   │   ├── yamato_model.py
│   │   ├── yamato_config.py
│   │   ├── qwen_adapter.py
│   │   ├── tenson_korin_quantizer.py
│   │   ├── kenpou/            ← ガバナンス層
│   │   └── yomi/              ← Layer 5 (TsukuyomiTypeHead)
│   └── ts_tools/              ← TS Compiler API ツール (Node プロジェクト)
│       ├── package.json
│       ├── tsconfig.json
│       └── src/               ← tsc_strict_runner.ts, mutate_for_hallucination.ts
├── scripts/                   ← train / eval / data
│   ├── data/
│   ├── eval/
│   └── train/
├── config/                    ← ts_type_vocab.json 他
├── source_reference/          ← Python 既存実装 (READ-ONLY)
│   ├── julia_no_mikoto/       ← 5 層 + KojikiLM 内部 (17 files, 9047 LOC)
│   ├── iwato/                 ← 言語処理層 (8 files, 1591 LOC)
│   └── kenpou/                ← ガバナンス層 (6 files, 993 LOC)
├── current_target/            ← yamato-public 2026-05-18 スナップショット (src/ への集約後、参照のみ)
├── checkpoints/               ← Stage 2 学習済資産 (gitignore 対象)
│   └── step_2000/             ← custom_heads.pt (29MB, ローカル管理) + training_log.json
├── baselines/                 ← 評価結果 (baseline と Stage 2 比較用)
│   ├── humaneval-ts.{baseline,step2000}.{summary,aux}.json
│   ├── mbpp-ts.{baseline,step2000}.{summary,aux}.json
│   └── type_head.{random_init,step2000}.json
├── data/                      ← gitignore、ローカル管理 (1.6GB)
│   ├── raw/                   ← DefinitelyTyped, MultiPL-E, ManyTypes4TS の生データ
│   ├── processed/sft/         ← トークン化済 SFT parquet
│   └── eval/                  ← humaneval-ts 生成結果、type_head 評価結果
└── models/                    ← gitignore、ローカル管理 (15GB)
    └── Qwen2.5-Coder-7B-Instruct/  ← HF 重み + tokenizer (--model-name のデフォルト先)
```

### 設計ドキュメント

| ファイル | 内容 |
|---------|------|
| [docs/roadmap_min.md](docs/roadmap_min.md) | **実装パス (簡易版)**: 型予測 + ファイヤーウォール 2 本柱の最短コース |
| [docs/旧ドキュメント/architecture.md](docs/旧ドキュメント/architecture.md) | 設計の全体像（5 層 + 横断 + 天御柱 4 Phase + 言霊）※フル版 |
| [docs/旧ドキュメント/roadmap.md](docs/旧ドキュメント/roadmap.md) | M0〜M6 フル版マイルストーン |
| [docs/旧ドキュメント/scope.md](docs/旧ドキュメント/scope.md) | 実装規模、ファイル対応表、Phase A〜E |
| [docs/旧ドキュメント/glossary.md](docs/旧ドキュメント/glossary.md) | 神名 ↔ 技術役割マッピング表 |

### セットアップ

Python パッケージは src レイアウト。editable install すれば `kojiki_lm` をどこからでも import できる:

```bash
pip install -e .                  # 必須依存のみ
pip install -e ".[quantization]"  # bitsandbytes (4bit/8bit ロード) も入れる
```

TS Compiler API ツール:

```bash
cd src/ts_tools && npm install
```

`models/` と `data/` は git 管理外 (15GB + 1.6GB)。HuggingFace から取り直すか、別所からコピーする:

```bash
# Qwen2.5-Coder-7B-Instruct (15GB)
huggingface-cli download Qwen/Qwen2.5-Coder-7B-Instruct --local-dir models/Qwen2.5-Coder-7B-Instruct

# SFT データは scripts/data/prepare_sft_dataset.py で再生成
python3 scripts/data/prepare_sft_dataset.py
```

### コードとデータの使い方

- `src/` が**実装本体**。`src/kojiki_lm/` (Python core) と `src/ts_tools/` (TS Compiler API) で構成。今後の編集はすべてここで行う。
- `source_reference/` は**参照のみ**。Python 13,500 LOC の既存実装をそのまま閲覧。実装時はここを読みながら `src/` に書き起こす。
- `current_target/` は yamato-public からの 2026-05-18 スナップショット。`src/` への集約後は履歴比較用に保持しており、編集はしない。
- `checkpoints/step_2000/custom_heads.pt` は Stage 2 SFT で学習済の TsukuyomiTypeHead + BonpuConfidence パラメータ (14.82M params)。新アーキテクチャでも再利用可能。
- `baselines/` は Win Condition 判定の数値根拠。新実装の評価では必ずこれと比較する。

## 現状サマリ

- Stage 1 国譲り (Qwen2.5-Coder-7B-Instruct 重み継承 + ヘッド初期化): ✅ 完了
- Stage 2 天孫降臨 (QLoRA SFT, ManyTypes4TS): ✅ 学習完了。Win Condition は未達。理由: **設計の核 (5 層 + 横断 + 天御柱 4 Phase + 言霊) がほぼ未実装** だったため、TypeHead が単独存在しても生成に転移しない
- Stage 3 禊以降: 着手前。**先に 5 層構造を [src/](src/) に実装する**のが本来の道

## 重要原則

**構造でハルシネーションを起こさせない**。

検知 → リトライ型の事後監視ではなく、生成プロセス自体を制約することで不正出力が**物理的に起こり得ない**形にする。これは複数の構造機構（順序制約・チケット制 Authority・言霊 Logits 操作・Shadow/Twin 並列・黄泉比良坂 firewall・修復予算・閻魔判定）の合成で実現される。単一機構だけでは効かない。

詳細は [docs/旧ドキュメント/architecture.md](docs/旧ドキュメント/architecture.md) を参照。
