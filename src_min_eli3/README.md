# src_min_eli3

**Elixir target + 光明想 (KoumyouSo) 統合実装** (2026-05-26 〜)。

eli2 (`src_min_eli2/`) を完全 copy したベース + **reasoning trace 強制機構** を追加した
実験ブランチ。`docs/memo/2026-05-26_須弥山設計原理.md` Part 2 §6 「光明想 (惛沈睡眠の対治)」
の最初の実装。

## 設計原理 (光明想)

仏教五蓋の第三「惛沈睡眠 (こんちんすいみん)」= 怠惰・手抜き。対治法は「光明想」=
**光を観想する** こと、つまり **「闇 (出力の不透明性) を照明 (中間推論の可視化) で破る」**。

ML 解釈: model が「思考過程を見せずに code に直行する」手抜きを物理的に困難にする。
中間推論 (`# 思考: ...` lines) を出力先頭に強制し、不在/不足を **即 HALT** で reject する。

## eli2 との差分

| 観点 | eli2 | **eli3** |
|---|---|---|
| Firewall (黄泉比良坂) | あり | **同じ** (構造そのまま) |
| Evaluator | `ElixirEvaluator` | 同じだが `koumyou_so` 引数を追加 |
| L3ToL5Payload | text + meta | **`prompt_len: int = 0`** を追加 (生成部分の境界) |
| Reasoning trace | なし | **`KoumyouSo` で強制** (光明想) |
| Prompt | bare | mode=koumyou-on のとき末尾に `"  # 思考: "` を pre-seed |
| Runner | `run_yamato_min_elixir.py` | `run_yamato_min_elixir3.py` (3-arm ablation 対応) |

eli2 は **一切変更していない** (`feedback-prove-and-handoff` の保全方針)。完全 copy なので
共通修正の二重管理は発生するが、ablation の cleanness を優先。

## 新規ファイル

| ファイル | 内容 |
|---|---|
| `kojiki_lm/koumyou_so.py` | **光明想本体**。`KoumyouSo.validate(generated_text)` で `# 思考:` 行数・本文文字数・code 開始を判定 |

## 修正ファイル (eli2 からの diff)

| ファイル | 差分 |
|---|---|
| `kojiki_lm/yomotsu_hirasaka.py` | `L3ToL5Payload.prompt_len` を追加 |
| `kojiki_lm/firewall_decoder.py` | `firewall.send` 時に `prompt_len` を渡す |
| `kojiki_lm/elixir_evaluator.py` | `__init__(koumyou_so=None)` 追加、`__call__` で trace 不在を即 HALT |

## 光明想の判定ルール

`KoumyouSo.validate(generated_text)` は以下の状態を返す:

| 状態 | 条件 | 呼び出し側の動作 |
|---|---|---|
| `STILL_GENERATING` | generated text 長 < grace_period_chars かつ code 未開始 | 保留 (HALT しない) |
| `TRACE_ONLY` | code 未開始、trace prefix のみ | 保留 (HALT しない) |
| `TRACE_VALID` | code 開始済 + 行数 ≥ min_lines + 本文文字数 ≥ min_chars | normal evaluation 続行 |
| `TRACE_INSUFFICIENT` | code 開始済 + trace 不足 | **HALT (v_score=0.0)** |
| `TRACE_MISSING` | code 開始済 + trace marker 皆無 | **HALT (v_score=0.0)** |

「code 開始」= generated text の先頭から走査し、最初に出現する「空白でも `# 思考:` でも
ない行」。

デフォルト閾値 (`KoumyouSoConfig`):
- `min_trace_lines = 2`
- `min_trace_chars = 20` (marker 除く本文)
- `grace_period_chars = 16`

## Prompt の trace seed 注入

mode=koumyou-on のとき、runner は prompt 末尾に `"  # 思考: "` を append する。

```
<MultiPL-E prompt>
defmodule Solution do
  @doc """..."""
  def foo(x, y) do
  # 思考:                          ← seed (この時点で prompt 終端)
```

model の最初の生成 token は `# 思考: ` の **続き** = trace 本文の冒頭となる。
KoumyouSo はこの seed を知っているため (`KoumyouSoConfig.trace_seed`)、validate 時に
prepend して整合させる。

`prompt + completion` を組み立てる際は、runner が `completion = TRACE_SEED + result.text`
として保存。これで eval (`scripts/eval/elixir_eval.py`) は変更なしで動作する。

## Mode (3-arm ablation)

`scripts/eval/run_yamato_min_elixir3.py --mode <name>`:

| Mode | Firewall | KoumyouSo | trace seed | eli2 対応 |
|---|---|---|---|---|
| `firewall-off` | OFF | OFF | なし | eli2 firewall-off と等価 |
| `firewall-on` | ON | OFF | なし | eli2 firewall-on と等価 |
| `koumyou-on` | ON | ON | あり | **eli3 主流** |

3-arm 比較で:
- `firewall-on − firewall-off`: Firewall 単独効果 (eli2 で測定済、+2.28pp on humaneval-elixir)
- `koumyou-on − firewall-on`: **光明想の純増効果** (本実装の主目的)

## 使い方

```bash
# eli3 koumyou-on で humaneval-elixir を解く
python3 scripts/eval/run_yamato_min_elixir3.py \
    --input data/raw/multipl_e/humaneval-elixir/test-00000-of-00001.parquet \
    --out-dir data/eval/generated/humaneval-elixir.yamato_min_elixir3.koumyou-on.seed0 \
    --mode koumyou-on --quantize 4bit --seed 0

# 評価 (既存の elixir_eval.py をそのまま使う)
python3 scripts/eval/elixir_eval.py \
    --generated-dir data/eval/generated/humaneval-elixir.yamato_min_elixir3.koumyou-on.seed0 \
    --out-dir data/eval/results/humaneval-elixir.yamato_min_elixir3.koumyou-on.seed0
```

## 関連メモリ (auto-memory pointer)

- `project-firewall-purpose`: 黄泉比良坂は L3↔L5 隔離壁、HALT/REPAIR は副次 (本実装も準拠)
- `feedback-prove-and-handoff`: eli2 を壊さず copy する方針の根拠
- `feedback-ablate-before-celebrating`: 3-arm ablation で純増効果を測ってから判定
- `feedback-type-prediction-is-hallucination-detection`: trace 強制は表層 metric (pass@1) より
  深層 metric (undef-symbol rate / 手抜き率) に効く可能性

## 既知の制約と注意点

- **trace seed のフォーマット依存**: `"  # 思考: "` は 2-space indent を仮定。
  MultiPL-E elixir prompt が全て `def ... do\n` で終わる前提に依存。例外があれば調整が必要。
- **HALT は再生成しない**: 失敗サンプルは partial completion のまま保存される。`feedback`
  チャネルとしては reject signal だが、scoring 上は失敗扱い (pass@1 を下げる方向に作用)。
- **trace の gaming 可能性**: `# 思考: a a a a a a ...` のような padding は文字数閾値で
  弾けるが、`# 思考: 関数を実装する` のような汎用文は通過する。LLM judge 化はしない方針
  (gameable のため)。次の強化は「trace 本文と code の semantic 整合」だがコスト高。
- **chat template 未使用**: bare prompt で運用 (eli2 と同じ baseline 軸)。chat template 化
  すると trace 遵守率は上がるが、baseline との分布差で ablation が clean でなくなる。
