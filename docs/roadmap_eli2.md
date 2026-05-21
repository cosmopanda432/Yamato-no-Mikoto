# Roadmap — yamatoLLM Elixir target (Python + Elixir ハイブリッド版)

**作成 2026-05-21**。src_min_elixir/ (Mix project) の中止 ([docs/旧ドキュメント/roadmap_min_elixir.md](旧ドキュメント/roadmap_min_elixir.md))
を受けて、Python ベースで Elixir をターゲット言語にする新計画。実装は `src_min_eli2/`。

## なぜハイブリッドか

src_min_elixir/ の Mix project 路線で発覚した: **Elixir LM エコシステム (Bumblebee 0.7.0) は
我々が使いたい Qwen2/Qwen3 MoE を未対応で、近い将来も対応見込みなし**。

教訓: 言語の理論的優位 (Erlang/Elixir の BEAM プロセス境界が Firewall を自動成立させる) を
取りに行く前に、**その言語の LM SDK が現行モデルを追えているか**を確認すべきだった。

→ LM 部分は Python の成熟した ecosystem (transformers + bnb 量子化) に任せ、Elixir は
ターゲット言語 (生成対象) と AST/symbol 処理ツールとして使う、というハイブリッド構成へ転換。

## アーキテクチャ

```
┌───────────────────────────────────────────────────────────────┐
│ Python (src_min_go から大半再利用、src_min_eli2 が Elixir 拡張)│
│                                                                │
│  L3 (生成ランタイム)                                            │
│   ├─ Qwen2.5-Coder-7B (transformers, bnb 4bit/8bit)            │
│   ├─ KotodamaDecoder (src_min_go から、bias 対象 token のみ拡張) │
│   └─ token-by-token decode loop                                 │
│         │                                                       │
│         ▼ %L3ToL5Payload{text, step_idx, prompt_id}             │
│  YomotsuHirasaka (src_min_go から **100% 再利用**、言語非依存)  │
│         │                                                       │
│         ▼                                                       │
│  L5 (評価器)                                                    │
│   ├─ src_min_eli2/elixir_evaluator.py                          │
│   ├─ subprocess.run(["elixir", tmp.exs], timeout=5)            │
│   └─ exit code + stderr で verdict 決定                         │
│         │                                                       │
│         ▼ %L5ToL3Verdict{verdict, v_score}                      │
│  L3 (続き、verdict に応じて continue / repair / halt)            │
└───────────────────────────────────────────────────────────────┘
```

## src_min_go との関係 (再利用マップ)

| 観点 | src_min_go | src_min_eli2 |
|---|---|---|
| LM | Qwen2.5-Coder-7B | **同じ** |
| Firewall (YomotsuHirasaka) | [yomotsu_hirasaka.py](../src_min_go/kojiki_lm/yomotsu_hirasaka.py) | **100% 再利用** (言語非依存 contract) |
| KotodamaDecoder | [kotodama_decoder.py](../src_min_go/kojiki_lm/kotodama_decoder.py) | **再利用、bias 対象 oracle のみ差し替え** |
| L5 評価器 | [yomi_evaluator.py](../src_min_go/kojiki_lm/yomi_evaluator.py) (Go 用語彙) | `src_min_eli2/elixir_evaluator.py` 新規 |
| Symbol oracle | `go/types` daemon (Go 専用) | `subprocess.run(["elixir", "-e", "Module.__info__/1"])` 新規 |
| Mechanical REPAIR | `goimports` | `mix format` + AST 変形 (新規) |
| Dataset | humaneval-go (154) / mbpp-go (374) | humaneval-elixir (161) / mbpp-elixir (397) |

## Step 計画

| Step | 内容 | 工数 | 状態 |
|---|---|---|---|
| 1 | `src_min_eli2/elixir_evaluator.py` 最小版 (subprocess `elixir <file>` を呼ぶだけ、既存 `scripts/eval/elixir_eval.py` 構造を流用) | 0.5d | ⬜ |
| 2 | `scripts/eval/run_baseline_elixir.py` (Go 版 baseline runner を Elixir target 用に移植) | 0.5d | ⬜ |
| 3 | smoke 1 問動作確認 (Qwen2.5-Coder-7B + humaneval-elixir 1 問で end-to-end) | 0.5d | ⬜ |
| 4 | `scripts/eval/run_yamato_min_elixir.py` (yamato pipeline、KotodamaDecoder 経由) | 0.5d | ⬜ |
| 5 | `src_min_eli2/kotodama_context_elixir.py` (text position 判定の Elixir 用 re-tune) | 0.5d | ⬜ |
| 6 | `src_min_eli2/elixir_symbol_oracle.py` (`Module.__info__/1` 経由の symbol 列挙) | 1d | ⬜ |
| 7 | `src_min_eli2/elixir_mechanical_repair.py` (`mix format` + Code.string_to_quoted hint) | 0.5d | ⬜ |
| 8 | `scripts/runpod_bench.sh` の DATASET=humaneval-elixir / mbpp-elixir 対応 (eval routing) | 0.5d | ⬜ |
| 9 | humaneval-elixir 161 問 baseline + yamato 4 mode × 3 seed | A5000 6h | ⬜ |
| 10 | mbpp-elixir 397 問 同様 | A5000 12h | ⬜ |
| **合計** | | **約 4-5 day + 18h compute** | |

src_min_elixir/ の Step 3/4/6/7 は **使わない** (本路線では Python 側が肩代わり、ただし設計
インスピレーションとしては有効)。

## GPU/インフラ要件

| 観点 | 旧 (src_min_elixir) | 新 (src_min_eli2) |
|---|---|---|
| GPU | A6000 48GB ($0.49/h) 必須 | **A5000 24GB ($0.30/h) で十分** |
| Model | Qwen3-Coder-30B-A3B (60 GB) | Qwen2.5-Coder-7B (~14 GB at bf16, ~4 GB at 4bit) |
| Runtime | Erlang + Elixir + Bumblebee + EXLA (環境構築 30 分) | Python + transformers (既存 setup そのまま) |
| 再現性 | CUDA 互換性で大量パッチ要 | Go 版 setup と同一、scripts/runpod_bench.sh 流用 |

→ コスパは Go 版とほぼ同じ ($0.30/h)、`project-runpod-gpu-choice.md` の旧 A5000 推奨が
本路線でも適用可。

## Win Condition (再定義)

src_min_elixir/ の旧 Win Condition (Firewall byte-identical + LM pass@1) は本路線でも継承、
ただし「Firewall を BEAM プロセス境界で完成させる」一点 (旧主目的) は **本路線では狙わない**
(Python で Go 版同等の dataclass-based Firewall を使うため)。

### 一次基準 (必達)

1. **Go 版で達成済の Firewall byte-identical 性質が Elixir target でも保たれる**
   - vanilla (firewall OFF) vs no-kotodama (firewall ON、bias OFF) で humaneval-elixir 161 問 × 3 seed が完全一致
   - = Firewall 物理層が target 言語に依存しないことの証拠
2. **`YomotsuHirasaka` 型契約の Python 単体テストが既存通り緑** (= [test_firewall_go.py](../tests_go/test_firewall_go.py) を `target=elixir` 構成でも回す)

### 二次基準 (Elixir 生成品質)

- humaneval-elixir 161 問 × 3 seed × 4 mode (baseline / no-kotodama / no-firewall / full)
- **pass@1** で baseline 比 +5pp (Go 版と同じ目標値、Qwen2.5-Coder-7B での達成可能性は未測定)
- **undef-symbol rate / `mix compile` 成功率** で同様に改善 (型予測 = hallucination 検出の本来効果指標)

### 三次基準 (3 言語の通底)

3 言語 (TS / Go / Elixir) で同じ Qwen2.5-Coder-7B + Firewall + KotodamaDecoder + 同 seed・同 hyperparameter
で測れば、**「Firewall の効果は target 言語に依らず保たれる」「言霊 bias の効果は言語の
型表面に依存する」**という対比が可能になる。これは src_min_elixir/ 旧計画では得られなかった
比較軸。

## 残る不確定要素

- Qwen2.5-Coder-7B の Elixir 生成品質は未測定 (Python は学習データに多いが Elixir は少ない)
- mbpp-elixir のテスト形式が humaneval-elixir と完全互換か未確認 (ヘッダ差 / `mix test` 期待など)
- `mix format` subprocess の latency が許容範囲か (1 prompt あたり 100 ms 程度想定、batch で重なると問題)

## 関連

- [docs/旧ドキュメント/roadmap_min_elixir.md](旧ドキュメント/roadmap_min_elixir.md) — 中止された旧 Mix project 計画 (中止理由 + 教訓)
- [docs/roadmap_min_go.md](roadmap_min_go.md) — Go 版現状、Python infrastructure の親 (本路線が大半再利用)
- [src_min_eli2/README.md](../src_min_eli2/README.md) — 本路線の実装フォルダ説明
- [src_min_elixir/](../src_min_elixir/) — 中止された Mix project (保存のみ、本路線では未使用)
- memory: `project-firewall-purpose.md`, `project-elixir-pivot-viability.md`, `project-runpod-gpu-choice.md`
