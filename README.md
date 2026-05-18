# Yamato-no-Mikoto

yamatoLLM の TypeScript 型認識特化版を実装するリポジトリ。
**簡易版ロードマップ全マイルストーン (M0 / M1' / M2 / M6) は実装完了**。
GPU 環境での評価実行を待つ状態。

## 売り (簡易版で立てる 2 本柱)

1. **型予測** — Stage 2 学習済 `TsukuyomiTypeHead` を、ランタイム時に **言霊 (Kotodama)** で
   物理的トークンマスクとして強制する。ハルシネーション (存在しない型) を生成不可能にする。
2. **ファイヤーウォール** — `yomotsu_hirasaka` で L3 (生成) と L5 (評価) を構造的に隔離。
   評価器の内部状態は frozen dataclass の型契約で L3 に漏れない。

詳細は [docs/roadmap_min.md](docs/roadmap_min.md) 参照。

## このリポジトリの構成

```
Yamato-no-Mikoto/
├── README.md                    ← この文書
├── pyproject.toml               ← packages.find は src_min/ を指す
├── docs/
│   ├── roadmap_min.md           ← **実装パス (簡易版)**
│   └── 旧ドキュメント/           ← フル版設計ドキュメント (参照用)
│       ├── architecture.md
│       ├── roadmap.md
│       ├── scope.md
│       └── glossary.md
├── src_min/                     ← **実装本体 (active)**
│   └── kojiki_lm/
│       ├── yamato_qwen.py             ← M0: Qwen2 サブクラス + generate_kotodama
│       ├── yamato_model.py            ← YamatoLLM wrapper (backbone + custom heads)
│       ├── yamato_config.py
│       ├── qwen_adapter.py
│       ├── data.py
│       ├── yomotsu_hirasaka.py        ← M1': L3↔L5 firewall
│       ├── yomi_evaluator.py          ← M1': 簡略 evaluator
│       ├── kotodama_token_mask.py     ← M2: TypeVocab + MaskBuilder
│       ├── kotodama_context.py        ← M2: 型 context heuristic
│       ├── kotodama_decoder.py        ← M2: masked decode + Firewall 統合
│       ├── kenpou/bonpu_confidence.py
│       └── yomi/tsukuyomi_type_head.py
├── src/                         ← フル版実装の参照用 (frozen)
│   ├── kojiki_lm/               ← Stage 1/2 当時のオリジナル
│   └── ts_tools/                ← TS Compiler API (M2.5 で活用予定)
├── tests/                       ← pytest 70 件全 pass (CPU で全結合検証)
│   ├── conftest.py              ← MockTokenizer / MockBackbone / MockTypeHead
│   ├── test_firewall.py / test_evaluator.py             (M1')
│   ├── test_kotodama_{mask,context,decoder}.py          (M2)
│   └── test_e2e.py                                      (M6 ablation)
├── scripts/
│   ├── eval/
│   │   ├── run_yamato_min.py            ← M6: Kotodama 生成
│   │   ├── judge_win_condition.py       ← M6: Win Condition 判定
│   │   ├── generate_multipl_e.py        ← vanilla baseline 生成
│   │   ├── run_tests.py / aux_metrics.py
│   │   └── eval_type_head.py
│   ├── train/ / data/
├── config/
│   └── ts_type_vocab.json       ← 256 entry TS 型 vocab (ManyTypes4TS 由来)
├── baselines/                   ← Win Condition 比較根拠
│   ├── humaneval-ts.{baseline,step2000}.{summary,aux}.json
│   ├── mbpp-ts.{baseline,step2000}.{summary,aux}.json
│   └── type_head.{random_init,step2000}.json
├── source_reference/            ← フル版 Python 13,500 LOC 既存実装 (READ-ONLY)
├── current_target/              ← 過去スナップショット (参照のみ)
├── checkpoints/step_2000/       ← Stage 2 custom_heads.pt (gitignore)
├── data/                        ← 1.6GB (gitignore)
└── models/                      ← 15GB (gitignore)
```

### 設計ドキュメント

| ファイル | 内容 |
|---------|------|
| [docs/roadmap_min.md](docs/roadmap_min.md) | **実装パス (簡易版)**: 完了済 + 実行手順 |
| [docs/旧ドキュメント/architecture.md](docs/旧ドキュメント/architecture.md) | 設計の全体像（5 層 + 横断 + 天御柱 4 Phase + 言霊）※フル版 |
| [docs/旧ドキュメント/roadmap.md](docs/旧ドキュメント/roadmap.md) | M0〜M6 フル版マイルストーン |
| [docs/旧ドキュメント/scope.md](docs/旧ドキュメント/scope.md) | 実装規模、ファイル対応表 |
| [docs/旧ドキュメント/glossary.md](docs/旧ドキュメント/glossary.md) | 神名 ↔ 技術役割マッピング表 |

### セットアップ

`pyproject.toml` の `packages.find` は `src_min/` を指す。editable install で `kojiki_lm` を import 可能:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"             # torch / transformers / peft / accelerate / pyarrow / pytest
pip install -e ".[quantization]"    # bitsandbytes (4bit/8bit ロード) を追加
```

TS Compiler API ツール (現状はフル版 src/ts_tools/ のみ。M2.5 で活用予定):

```bash
cd src/ts_tools && npm install
```

`models/` と `data/` は git 管理外:

```bash
# Qwen2.5-Coder-7B-Instruct (15GB)
huggingface-cli download Qwen/Qwen2.5-Coder-7B-Instruct --local-dir models/Qwen2.5-Coder-7B-Instruct

# SFT データは scripts/data/prepare_sft_dataset.py で再生成
python3 scripts/data/prepare_sft_dataset.py
```

### コードの使い分け

- `src_min/` が**現在の実装本体**。Kotodama + Firewall + Evaluator の簡易版アーキ。
- `src/kojiki_lm/` は Stage 1/2 当時のフル版オリジナル (frozen)。`src_min/` への差分参考のため保持。
- `src/ts_tools/` は TS Compiler API ツール。M2.5 (symbol-aware 制約) で `valid_continuations.ts` / `token_mask_builder.ts` を追加する想定。
- `source_reference/` は**参照のみ**。Python 13,500 LOC を読みながら必要なら `src_min/` に書き起こす。
- `checkpoints/step_2000/custom_heads.pt` は Stage 2 学習済 14.82M params。簡易版でもそのまま再利用 (再学習しない)。
- `baselines/` は Win Condition 比較根拠。`judge_win_condition.py` がここを読む。

## 実装状況

| マイルストーン | 内容 | コミット |
|---|---|---|
| Stage 1 国譲り | Qwen2.5-Coder-7B-Instruct 重み継承 + ヘッド初期化 | (継承) |
| Stage 2 天孫降臨 | QLoRA SFT, ManyTypes4TS (Win Condition 未達) | (継承) |
| **M0** | YamatoQwenForCausalLM 空殻 | `a584326` |
| **M1'** | Firewall + 簡略 Evaluator | `ca2e69f` |
| **M2 (min)** | 言霊 + Kotodama decoder + Firewall 統合 | `376945d` |
| **M6 (min)** | run_yamato_min.py + Win Condition 判定 | `8dfbe60` |

テスト: `pytest tests/` で **70 / 70 pass** (CPU 環境で全結合検証可能)。

次は GPU 環境での実評価。実行手順は [docs/roadmap_min.md#実行手順-gpu-環境](docs/roadmap_min.md#実行手順-gpu-環境) 参照。

## 重要原則

**構造でハルシネーションを起こさせない**。検知 → リトライ型の事後監視ではなく、
生成プロセス自体を制約することで不正出力が**物理的に起こり得ない**形にする。

簡易版で投入しているのは以下 2 機構:

1. **言霊 (Kotodama)** — TypeHead が予測した型語彙の外を logit = -∞ で物理マスク。
2. **黄泉比良坂 (Yomotsu Hirasaka)** — L3 (生成) と L5 (評価) の境界を frozen
   dataclass で構造的に隔離。評価器の内部状態が生成に影響しないことを型で保証。

これで Win Condition を満たさなければ、設計の核 (Authority / 天御柱 4 Phase /
Shadow・Twin / 言霊 symbol-aware 拡張 / iwato 前処理) を**根拠付きで** 1 つずつ追加する。
拡張優先順は [docs/roadmap_min.md#達成後](docs/roadmap_min.md#達成後-win-condition-通過後の拡張順) を参照。

フル版設計 (上記すべて積んだ完成形) は [docs/旧ドキュメント/architecture.md](docs/旧ドキュメント/architecture.md) を参照。
