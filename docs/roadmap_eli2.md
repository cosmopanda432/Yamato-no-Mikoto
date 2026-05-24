# Roadmap — yamatoLLM Elixir target (Python + Elixir ハイブリッド版)

**作成 2026-05-21**。src_min_elixir/ (Mix project) の中止 ([docs/旧ドキュメント/roadmap_min_elixir.md](旧ドキュメント/roadmap_min_elixir.md))
を受けて、Python ベースで Elixir をターゲット言語にする新計画。実装は `src_min_eli2/`。

## ✅ 2026-05-21 一次基準達成 (humaneval-elixir 161 問 × seed 0)

**Firewall 物理隔離: 161/161 byte-identical (100%)** — `firewall-off` vs `firewall-on` で
completion / raw_completion ともに完全一致。Go 版 mbpp-go 374/374 達成
([sampling_path_issue.md](sampling_path_issue.md)) の Elixir target 再現完了。

| metric | baseline (model.generate) | firewall-* (両 mode 同じ) | Δ |
|---|---|---|---|
| pass@1 | 26.71% (43/161) | 28.57% (46/161) | +1.86pp |
| compile pass rate | 68.32% (110/161) | 72.05% (116/161) | +3.73pp |
| **undef rate★** | 5.59% (9/161) | **2.48% (4/161)** | **−3.11pp** ✅ |
| assertion failure | 22.36% | 26.09% | +3.73pp |

★ hallucination 検出本来の効果指標 ([feedback-type-prediction-is-hallucination-detection](../C:/Users/mimat/.claude/projects/c--Users-mimat-Yamato-no-Mikoto/memory/feedback-type-prediction-is-hallucination-detection.md))。

setup: Qwen2.5-Coder-7B + 4bit + RunPod RTX 4090 24GB / Ubuntu 22.04 / CUDA 12.4。
setup 80 秒 + smoke 51 秒 + smoke-fix-d 92 秒 + baseline 65 秒 + pilot 1027 秒 = 全 ~24 分。

副次的発見 (修正 H = FirewallDecoder の token-level stop_token early-stop):
- baseline は max_new_tokens=256 まで生成後 truncate、firewall-* は stop_token 検出で早期 stop
- 早期 stop で test driver 領域の汚染を防ぎ pass@1 / compile rate が改善
- 1 seed のみのため統計検定不可。3 seed × 95% CI 検定は将来課題

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
│   ├─ FirewallDecoder (src_min_go から bias 撤去版)               │
│   └─ token-by-token decode loop + Firewall 統合                 │
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

2026-05-21 update: src_min_eli2 から bias 機構 (Kotodama 関連) を撤去。
Go 版 mbpp-go ablation で bias 単独寄与が不可視、Elixir では surface area さらに狭い
([[feedback-elixir-has-no-static-types]]) ため。Decode loop + Firewall の最小核に絞る。

| 観点 | src_min_go | src_min_eli2 |
|---|---|---|
| LM | Qwen2.5-Coder-7B | **同じ** |
| Firewall (YomotsuHirasaka) | [yomotsu_hirasaka.py](../src_min_go/kojiki_lm/yomotsu_hirasaka.py) | **100% 再利用** (言語非依存 contract) |
| Decoder | `KotodamaDecoder` (decode + bias + Firewall) | **`FirewallDecoder`** (decode + Firewall、bias 撤去) |
| L5 評価器 | [yomi_evaluator.py](../src_min_go/kojiki_lm/yomi_evaluator.py) (Go 用語彙) | `src_min_eli2/elixir_evaluator.py` 新規 |
| ~~Symbol oracle~~ | `go/types` daemon | **撤去** (bias 機構と一緒に) |
| Mechanical REPAIR | `goimports` | **撤去** (`Code.format_string!` は AST 保存変換で compile/test に効果ゼロのため、効果対象が出てから再設計) |
| Dataset | humaneval-go (154) / mbpp-go (374) | humaneval-elixir (161) / mbpp-elixir (397) |
| Ablation mode | 4 (full / no-kotodama / no-firewall / vanilla) | **2** (firewall-on / firewall-off) |

## Step 計画 (2026-05-21 更新、kotodama 撤去後)

| Step | 内容 | 状態 |
|---|---|---|
| 1 | src_min_go から Python core を copy (Firewall / Qwen adapter / data 等) | ✅ |
| 2 | `elixir_evaluator.py` (L5 ヒューリスティック評価器) | ✅ |
| 3 | ~~`elixir_mechanical_repair.py`~~ | 撤去 (整形のみで compile/test 影響ゼロ、surface area 不在) |
| 4 | `firewall_decoder.py` (旧 KotodamaDecoder から bias 撤去) | ✅ |
| 5 | `run_baseline_elixir.py` / `run_yamato_min_elixir.py` (2 mode: firewall-on / firewall-off) | ✅ |
| 6 | `elixir_eval.py` (`elixir <file>` subprocess 評価) | ✅ |
| 7 | `judge_win_condition_elixir.py` (95% CI 判定) | ✅ |
| 8 | `runpod_bench_eli2.sh` (RunPod setup + bench runbook) | ✅ |
| 9 | smoke 5 問 (pipeline 動作確認) | ✅ pass@1 40% (2/5) |
| 10 | smoke-fix-d 10 問 (Firewall byte-identical) | ✅ **10/10 完全一致** |
| 11 | baseline 161 問 × seed 0 | ✅ pass@1 26.71% (43/161)、compile 68.32%、undef 5.59% |
| 12 | firewall-on 161 問 × seed 0 | ⬜ 次の一手 |
| 13 | baseline vs firewall-on byte-identical 検証 (161/161 期待) | ⬜ 12 の直後 |
| 14 | judge (1 seed smoke) | ⬜ |
| 15 | 3 seed × 2 mode (full ci) | ⬜ A5000 ~30 分 |

撤去された旧 Step (kotodama 機構と一緒に):
- ~~symbol oracle / kotodama context / token mask~~ (bias 単独寄与不可視のため除去)
- ~~4 mode ablation (full / no-kotodama / no-firewall / vanilla)~~ → 2 mode に簡素化

src_min_elixir/ の Mix project 実装は **使わない** (本路線では Python 側が肩代わり)。

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
   - `firewall-off` (FirewallDecoder + firewall=OFF) vs `firewall-on` (firewall=ON) で humaneval-elixir 161 問 × 3 seed が完全一致
   - = Firewall 物理層が target 言語に依存しないことの証拠
   - 進捗: smoke-fix-d (10 問) で **10/10 達成** (2026-05-21)、161 問本ベンチへ
2. **`YomotsuHirasaka` 型契約の Python 単体テストが既存通り緑** ([test_firewall_go.py](../tests_go/test_firewall_go.py) を流用)

### 二次基準 (Elixir 生成品質)

- humaneval-elixir 161 問 × 3 seed × **2 mode** (firewall-off / firewall-on)
- ablation で見るのは「Firewall ON/OFF で pass@1 / compile_pass_rate / undef_rate が変化するか」
- 期待: Firewall ON は OFF と byte-identical (一次基準) のため LM 性能は同じ。Firewall の目的は L5 verdict signal の取得であって LM 性能向上ではない
- baseline (bare `model.generate`) との比較は code path 差を含む参考値
- 結論的に: Firewall の Win Condition は「LM 性能を変えないこと」であり「+5pp」ではない

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
