# src_min_eli2

**Python + Elixir-target ハイブリッド実装** (2026-05-21 〜)。

`src_min_elixir/` (Mix project で BEAM 完結を目指した路線) は **中止**
([docs/旧ドキュメント/roadmap_min_elixir.md](../docs/旧ドキュメント/roadmap_min_elixir.md) 参照、Bumblebee の Qwen2/Qwen3 MoE
サポート欠如で頓挫)。代わりに本フォルダで以下の設計を採る:

## 設計

```
┌─────────────────────────────────────────────────────────┐
│ Python (LM + Firewall、src_min_go から再利用)             │
│   - L3 = Qwen2.5-Coder-7B (transformers + bnb 4bit/8bit)  │
│   - L3 decode loop + KotodamaDecoder                      │
│   - YomotsuHirasaka (frozen dataclass、言語非依存契約)    │
│   - L5 = Elixir evaluator (subprocess `elixir <file>`)    │
└─────────────┬───────────────────────────────────────────┘
              │ subprocess (Elixir CLI)
              ▼
┌─────────────────────────────────────────────────────────┐
│ Elixir (AST/型/symbol 処理の CLI tool)                    │
│   - `elixir <file>` で .exs 実行 (既存 scripts/eval/elixir_eval.py) │
│   - `elixir -e "..."` で symbol enumeration               │
│   - `mix format` で機械的整形                              │
└─────────────────────────────────────────────────────────┘
```

## src_min_go との関係

| 観点 | src_min_go | **src_min_eli2** |
|---|---|---|
| LM | Qwen2.5-Coder-7B | **同じ** |
| L3 decode loop | `KotodamaDecoder` (src_min_go) | **同じものを import** |
| Firewall | [yomotsu_hirasaka.py](../src_min_go/kojiki_lm/yomotsu_hirasaka.py) | **同じものを import** ([feedback-prove-and-handoff](../docs/) 主旨で言語非依存) |
| Target 言語 | Go | **Elixir** |
| Evaluator | [go_eval.py](../scripts/eval/go_eval.py) + [yomi_evaluator.py](../src_min_go/kojiki_lm/yomi_evaluator.py) | `elixir_evaluator.py` (本フォルダ) + 既存 [elixir_eval.py](../scripts/eval/elixir_eval.py) |
| Symbol oracle | `go/types` daemon | `elixir -e "Module.__info__/1"` 経由 |
| Mechanical REPAIR | `goimports` | `mix format` + `Code.string_to_quoted/1` hint |

## 実装ファイル (2026-05-21、kotodama 撤去後の最小構成)

| ファイル | 内容 |
|---|---|
| `yomotsu_hirasaka.py` | Firewall (黄泉比良坂) 本体、src_min_go から 100% identical |
| `firewall_decoder.py` | token-by-token decode loop + Firewall 統合 (`FirewallDecoder`)。 旧 `KotodamaDecoder` から bias 機構を撤去したもの |
| `elixir_evaluator.py` | L5 ヒューリスティック評価器、Elixir keyword 辞書 |
| `elixir_mechanical_repair.py` | `Code.format_string!` を subprocess で適用 |
| `qwen_adapter.py` + `yamato_qwen.py` + `yamato_model.py` + `yamato_config.py` | Qwen2.5-Coder backbone wrap (src_min_go から copy) |
| `data.py` | parquet I/O |
| `kenpou/bonpu_confidence.py` + `yomi/tsukuyomi_type_head.py` | 言語非依存の head architecture (現状 inference path では未使用、訓練用に保存) |

| Runner script (scripts/eval/) | 内容 |
|---|---|
| `run_baseline_elixir.py` | bare `model.generate()` (kojiki_lm 依存なし) |
| `run_yamato_min_elixir.py` | FirewallDecoder 経由、`firewall-on` / `firewall-off` 2 mode |
| `elixir_eval.py` | `elixir <file>` subprocess で評価 (生成完了後の採点) |
| `judge_win_condition_elixir.py` | 95% CI で Win Condition 判定 |

## 削除されたファイル (2026-05-21、kotodama 撤去で死コード化)

| 旧ファイル | 撤去理由 |
|---|---|
| ~~`kotodama_decoder.py`~~ | `firewall_decoder.py` に置換 |
| ~~`kotodama_context.py`~~ | bias 用 position 判定、bias なしで不要 |
| ~~`kotodama_token_mask.py`~~ | bias 配列構築、不要 |
| ~~`elixir_symbol_oracle.py`~~ | bias 用 symbol lookup、不要 |

理由: Go 版 mbpp-go ablation で「言霊 bias 単独寄与が不可視」、Elixir では surface area
さらに狭い ([[feedback-elixir-has-no-static-types]])。本プロジェクト主目的は Firewall
([[project-firewall-purpose]]) のため、bias を撤去して decode+Firewall の最小核に絞る。

## 再利用しない (src_min_elixir 由来) もの

`src_min_elixir/` の Mix project (Step 3/4/6/7 = 62 tests 緑) は archived 扱い:
- `src_min_elixir/lib/kojiki_lm/yomotsu_hirasaka.ex` — Python 版に役目を譲る (BEAM プロセス境界での Firewall 実装の証拠としてのみ価値あり)
- `src_min_elixir/lib/kojiki_lm/l5.ex` — Python から `elixir <file>` で代替
- `src_min_elixir/lib/kojiki_lm/mechanical_repair.ex` — `mix format` 直接呼びで代替

将来 Bumblebee が Qwen2 / Qwen3 MoE を追加した時に再起動可能なよう、保存する方針 (中止扱い)。

## Win Condition (再定義)

`docs/roadmap_min_elixir.md` の Win Condition は Mix project 前提で書かれていたため無効。
新基準を `docs/roadmap_eli2.md` (TBD) で定義する。当面の最小目標:

1. Qwen2.5-Coder-7B + humaneval-elixir 161 問で **baseline pass@1 を測定** (Go 版 humaneval-go と同条件で比較可能)
2. Firewall ON/OFF で byte-identical 確認 (Go 版 374/374 達成済の延長)
3. (任意) mbpp-elixir 397 問でも同じ
