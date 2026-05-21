# Roadmap (Minimum) — yamatoLLM Elixir 版

主目的: **L3 ↔ L5 の絶対的隔離壁 (Firewall / 黄泉比良坂) を BEAM プロセス境界で完成
させる** (`project-firewall-purpose.md` / `project-elixir-pivot-viability.md` 参照)。

Go 版 ([docs/roadmap_min_go.md](roadmap_min_go.md)) で「言霊 bias の単独寄与が不可視」
だった一方、**Firewall の隔離契約は 374/374 byte-identical で確認済** ([sampling_path_issue.md](sampling_path_issue.md))。
本ターゲットは「Firewall を Python の `__post_init__` で **手で** 守る」から「言語/ランタイム
が **構造的に** 守る」へのレベルアップ。

## なぜ Go から Elixir へ

Go 版で苦労した:

| Go 版での苦労 | Elixir では |
|---|---|
| frozen dataclass + `__post_init__` 型 assert | `defstruct` + `@enforce_keys` + guard validator |
| 修正 D (`torch.Generator` 分離 = 物理サイドチャネル除去) | 各プロセスが独自 heap、無関係 |
| vanilla vs no-kotodama byte-identical 検証 | プロセス境界をまたいだ干渉が原理的に発生しない |
| `goimports` による機械的 REPAIR (mbpp-go で surface area ゼロ) | `Mix.format` + `Code.string_to_quoted/1` + "did you mean" parser で広い surface |
| 型位置 bias の surface area が小さい (動的型) | Elixir 1.20 (2026-05) set-theoretic types で全構文に型推論 |

技術的ボトルネックはほぼ無いと評価済 (`project-elixir-pivot-viability.md`)。投資判断
として **5-7 day**。

## 構成 (2026-05-21 確定: option A = 30B + int8 + A6000)

| Component | 採用 | 備考 |
|---|---|---|
| LM | **Qwen3-Coder-30B-A3B-Instruct** (3B active MoE) | Bumblebee v0.7.0 (2026-05-16) で Qwen3 サポート追加済 ([PR #423](https://github.com/elixir-nx/bumblebee/pull/423))。SWE-Bench スコアは 80B 版 (70%+) に劣るが Bumblebee 純血で動かせる |
| 量子化 | **int8 (Axon.Quantization)** | Bumblebee 公式が現在サポートする唯一の量子化。bf16 比 半分の VRAM |
| 推論 | Bumblebee + Nx + EXLA | int8 weight-only quantization、bf16 activation |
| GPU | **A6000 48GB** ($0.49/h on RunPod) | 30B int8 ~30-35 GB + KV cache + activation で A6000 に収まる |
| Dataset | MultiPL-E humaneval-elixir (161) / mbpp-elixir (397) | `elixir <file>` CLI で `.exs` を直接実行 (5s timeout、exit code ベース、`mix test` 不要) |
| L3 / L5 | GenServer 2 つ | プロセス境界 = Firewall (VM 保証) |
| `YomotsuHirasaka` | GenServer + guard | `is_binary/1` 等で型不適合を VM レベルで reject |
| 機械的 REPAIR | `Mix.format` + AST 変形 + コンパイラエラーパース | Go の `goimports` より surface area 広い |
| 型位置 bias | `Code.Typespec` / set-theoretic types 由来 position 抽出 | 1.20 で実用 |

## GPU 要件 (2026-05-21 web 確認、Bumblebee 量子化サポート判明後の正直版)

**重要**: Bumblebee v0.7.0 (2026-05-16) は **int4 / GGUF を未サポート** ([Issue #249](https://github.com/elixir-nx/bumblebee/issues/249) / [#413](https://github.com/elixir-nx/bumblebee/issues/413) Open のまま)。Axon.Quantization の weight-only int8 のみ可。
したがって Q4 前提の VRAM 計算は無効で、**実態は int8 ベース**で見る必要がある。

| GPU | VRAM | Qwen3-Coder-30B int8 (~30-35 GB) | Qwen3-Coder-Next 80B int8 (~80-90 GB) | RunPod 価格目安 |
|---|---|---|---|---|
| A5000 | 24 GB | ❌ 乗らない | ❌ | $0.30/h |
| **A6000** | **48 GB** | **✅ 推奨ライン** | ❌ | **$0.49/h** |
| A100 40GB | 40 GB | △ KV cache 込みで微妙 | ❌ | $1.19/h |
| A100 80GB | 80 GB | ✅ 余裕 | △ ぎりぎり | $1.89/h |
| H100 80GB | 80 GB | ✅ 速い | △ ぎりぎり | $2.69/h |

**A5000 24GB は Elixir pivot の全 path で off-table**。Go 版 ($0.30/h A5000) と直接コスパ比較できない。

`project-runpod-gpu-choice.md` の「A5000 が最適コスパ」は **Qwen2.5-Coder-7B (Go/TS 版) 限定**で
あり、本 Elixir pivot では成立しない。

## 選択肢の検討と option A 採用理由

3 つの選択肢があった (2026-05-21 検討):

| 選択肢 | 構成 | コスパ | 採否 |
|---|---|---|---|
| **A: 30B + int8 + A6000** | $0.49/h、Bumblebee 純血 | ◎ | **採用** |
| B: 80B + int8 + A100 80GB | $1.89/h、Bumblebee 純血 | △ Go 版 ($0.30/h) の 6 倍コスト | 不採用 |
| C: 80B + Q4 + NIF→llama.cpp | $0.49/h (A6000)、Bumblebee 純血放棄 | ○ 速いがアーキ複雑、推論パスが C プロセス経由 | 不採用 |

**A 採用理由**: 本 pivot の主目的は「Firewall を BEAM プロセス境界で完成させる」ことであり、
LM 自体の絶対性能 (SWE-Bench 70%+) は副次。30B 版でも `is_binary/1` guard / GenServer 境界 /
byte-identical 検証は同じ精度で行える。コストを Go 版に近い水準 ($0.49/h vs $0.30/h) に
抑えられるため、ablation を多数回せる。

## 8 ステップ計画 (合計 5-7 day)

| Step | 内容 | 工数 | 状態 |
|---|---|---|---|
| 1 | Mix project + Bumblebee + Qwen3-Coder-Next load | 0.5d | 🟡 mix.exs の deps 配置のみ (comment-out) |
| 2 | `KojikiLM.L3` GenServer (generate + sampling) | 1-2d | 🟡 stub のみ (interface 確定) |
| 3 | `KojikiLM.L5` GenServer (`Code.eval_string` + ExUnit) | 1d | 🟡 stub のみ (空→halt / 非空→repair) |
| 4 | `KojikiLM.YomotsuHirasaka` (BEAM proc 境界の薄ラッパー) | 0.5d | ✅ **本実装完了** |
| 5 | 型位置 bias (set-theoretic types からの抽出) | 1-2d | ⬜ 未着手 |
| 6 | 機械的 REPAIR (`Mix.format` + AST + "did you mean" parser) | 0.5d | ⬜ 未着手 |
| 7 | MultiPL-E elixir runner (humaneval/mbpp 共通) | 0.5d | ⬜ 未着手 |
| 8 | 検証 + ablation (vanilla vs full の byte-identical) | 0.5d | ⬜ 未着手 |

## 2026-05-21 セッションで完了したもの (Step 4 + 骨格)

[src_min_elixir/](../src_min_elixir/) に Mix project を新設。実装範囲は Step 4 本体
(`KojikiLM.YomotsuHirasaka` GenServer + 型契約) と、Step 1-3 を後で埋めるための stub。

### 完了ファイル

| Path | 内容 |
|---|---|
| [mix.exs](../src_min_elixir/mix.exs) | Mix project (Elixir 1.20+)。Bumblebee/Nx/EXLA は Step 1 で deps に解放する位置に comment-out 配置 |
| [lib/kojiki_lm/verdict.ex](../src_min_elixir/lib/kojiki_lm/verdict.ex) | `:commit / :repair / :halt` atom + `defguard is_verdict/1` |
| [lib/kojiki_lm/l3_to_l5_payload.ex](../src_min_elixir/lib/kojiki_lm/l3_to_l5_payload.ex) | 葦原 → 黄泉 struct。`new!/3` で `is_binary/1` / `is_integer/1 and >= 0` を guard 強制 |
| [lib/kojiki_lm/l5_to_l3_verdict.ex](../src_min_elixir/lib/kojiki_lm/l5_to_l3_verdict.ex) | 黄泉 → 葦原 struct。`Verdict.is_verdict/1` + `[0.0, 1.0]` レンジを guard 強制 |
| [lib/kojiki_lm/yomotsu_hirasaka.ex](../src_min_elixir/lib/kojiki_lm/yomotsu_hirasaka.ex) | GenServer 本体。evaluator は `pid` (別 GenServer) または 1-arg 関数を受ける |
| [lib/kojiki_lm/l3.ex](../src_min_elixir/lib/kojiki_lm/l3.ex) | Step 2 stub。`generate/3` は未実装 raise、`query_verdict/4` は実装済 |
| [lib/kojiki_lm/l5.ex](../src_min_elixir/lib/kojiki_lm/l5.ex) | Step 3 stub。空テキスト → `:halt`、その他 → `:repair` を返す最小 evaluator |
| [lib/kojiki_lm/config.ex](../src_min_elixir/lib/kojiki_lm/config.ex) | Step 1 stub。Qwen3-Coder-Next 設定 placeholder (model_repo / backend / dtype 等) |
| [test/support/test_evaluator.ex](../src_min_elixir/test/support/test_evaluator.ex) | テスト用 evaluator GenServer (BEAM 境界テスト用に caller PID を記録) |
| [test/kojiki_lm/verdict_test.exs](../src_min_elixir/test/kojiki_lm/verdict_test.exs) | Verdict atom + `is_verdict/1` guard のテスト |
| [test/kojiki_lm/l3_to_l5_payload_test.exs](../src_min_elixir/test/kojiki_lm/l3_to_l5_payload_test.exs) | L3 → L5 ペイロードの型契約 (Nx.Tensor 風 list/map/atom 等を reject) |
| [test/kojiki_lm/l5_to_l3_verdict_test.exs](../src_min_elixir/test/kojiki_lm/l5_to_l3_verdict_test.exs) | L5 → L3 verdict の型契約 |
| [test/kojiki_lm/yomotsu_hirasaka_test.exs](../src_min_elixir/test/kojiki_lm/yomotsu_hirasaka_test.exs) | ゲートウェイ本体 + **BEAM プロセス境界テスト** (evaluator が別 PID で走ることを assert) |

### Step 4 で何が「VM 保証」になったか

Python 版 (`src_min_go/kojiki_lm/yomotsu_hirasaka.py`) との対応:

| Python 版が手で守っていたもの | Elixir 版での保証元 |
|---|---|
| `@dataclass(frozen=True)` で不変性 | BEAM 上の値は言語レベルで不変 |
| `__post_init__` で `isinstance` assert | `@enforce_keys` + `is_binary/1`, `is_integer/1` 等の guard |
| `Verdict` Enum class | atom + `defguard is_verdict/1` |
| evaluator の callable 性 | `is_pid/1` or `is_function/2` で `init/1` 時に強制 |
| 評価器を別プロセスに分離する自由度 | evaluator に PID を渡すと **強制的に GenServer.call 経由** (term copy) |

mbpp-go ablation で発覚した「物理サイドチャネル (CUDA RNG / Python GC タイミング)」は、
各プロセスが独自 heap を持つ BEAM では原理的に発生しない (= [修正 D](sampling_path_issue.md) 相当の対応が **不要**)。

### 検証手順 (今マシンには Elixir 未 install)

```powershell
winget install Erlang.Erlang
winget install ElixirLang.Elixir

cd src_min_elixir
mix deps.get   # Step 4 段階では deps なしなので no-op
mix test       # 全 4 ファイルが緑になる想定
mix format
```

## これからの予定

### Step 1 — Bumblebee 接続 (1d)

- [mix.exs](../src_min_elixir/mix.exs) の `deps/0` で `:bumblebee, :nx, :exla` を解放 (`{:bumblebee, "~> 0.7"}` 以上を要求 — Qwen3 サポートは v0.7.0 から)
- [lib/kojiki_lm/config.ex](../src_min_elixir/lib/kojiki_lm/config.ex) を本実装。
  - `model_repo: "Qwen/Qwen3-Coder-30B-A3B-Instruct"`
  - `quantization: :int8` (`Axon.Quantization.quantize/2` で weight-only int8)
  - `backend: EXLA.Backend`
- `Bumblebee.load_model({:hf, "Qwen/Qwen3-Coder-30B-A3B-Instruct"})` の smoke test を 1 件
- Windows ローカルでは load 不可。Linux + RunPod A6000 48GB pod を想定

**確認ポイント**:
1. Bumblebee v0.7.0+ の Qwen3 サポートで Qwen3-Coder-30B-A3B が `Bumblebee.load_model/2` から読めること
2. `Axon.Quantization.quantize/2` の weight-only int8 を 30B に適用して `Bumblebee.Text.generation/3` がエラーなく回ること
3. **VRAM 実測** — 30B int8 + KV cache + activation で A6000 48GB に収まること (理論 ~30-35 GB、実測で確認)
4. 1-prompt 推論レイテンシの実測 — Go 版 ($0.30/h A5000) との absolute throughput 比較

### Step 2 — L3 GenServer 本実装 (1-2d)

- [lib/kojiki_lm/l3.ex](../src_min_elixir/lib/kojiki_lm/l3.ex) を GenServer 化
- token-by-token decode (`Nx.Random.split` で sampler の RNG を物理的に分離 — 言語レベルでは不要だが、Bumblebee 内部の sampling RNG を明示分離して [修正 D](sampling_path_issue.md) の Elixir 版対応とする)
- 各 step で `KojikiLM.YomotsuHirasaka.send/2` 呼び出し → verdict に応じて continue / repair / halt
- 修正 H 相当の token-level early-stop も同じ層で

### Step 3 — L5 GenServer 本実装 (1d)

- [lib/kojiki_lm/l5.ex](../src_min_elixir/lib/kojiki_lm/l5.ex) の `stub_evaluate` を差し替え:
  - `Code.string_to_quoted/1` で構文検査 (verdict 計算の早期 path)
  - `System.cmd("elixir", [path], timeout: 5_000)` で `.exs` をサブプロセス実行 (MultiPL-E `eval_elixir.py` と同形式)
  - exit code 0 + stderr 中の `Assertion with == failed` / `SyntaxError` の有無で verdict (`:commit / :repair / :halt`) を決定
- L5 を `YomotsuHirasaka` の evaluator PID として注入 → BEAM 境界 = Firewall 物理層
- 注意: `Code.eval_string/3` を BEAM 内部で直接呼ぶと評価器側のプロセス heap に code が
  ロードされて Firewall の主張が弱まる。**必ず別 OS プロセス (`System.cmd`) を経由**

### Step 5 — 型位置 bias (1-2d)

- Elixir 1.20 set-theoretic types から「現在のスコープで参照可能な型・関数 atom」を抽出
- `KotodamaDecoder` Elixir 相当を実装 — Go 版 ([src_min_go/kojiki_lm/kotodama_decoder.py](../src_min_go/kojiki_lm/kotodama_decoder.py)) の構造を移植
- ただし **マスク (-inf) は採らない** ([feedback-kotodama-mask-counterproductive](../C:/Users/mimat/.claude/projects/c--Users-mimat-Yamato-no-Mikoto/memory/feedback-kotodama-mask-counterproductive.md))。soft bias `+k` のみ

### Step 6 — 機械的 REPAIR (0.5d)

- `Mix.format` で軽微な整形
- `Code.string_to_quoted/1` のエラーメッセージ + "did you mean ..." の機械パース
- AST 変形による軽微な fix-up (例: 未使用 alias 削除)
- Go 版 ([src_min_go/kojiki_lm/mechanical_repair.py](../src_min_go/kojiki_lm/mechanical_repair.py)) は `goimports` 1 種のみで surface area ゼロだった ([project-mechanical-repair-mbpp-go-zero](../C:/Users/mimat/.claude/projects/c--Users-mimat-Yamato-no-Mikoto/memory/project-mechanical-repair-mbpp-go-zero.md))。Elixir では複数経路で再評価する

### Step 7 — MultiPL-E elixir runner (0.5d、Step 3 と統合可能)

- MultiPL-E の humaneval-elixir (161 問) / mbpp-elixir (397 問) dataset を `scripts/eval/generate_multipl_e.py` で取得
- ランナーは `scripts/eval/go_eval.py` の Elixir 版 (`scripts/eval/elixir_eval.py`) を新規作成。MultiPL-E `eval_elixir.py` と同じく `subprocess.run(["elixir", file], timeout=5)` で .exs を実行、exit code ベースで判定
- `scripts/runpod_bench.sh` を Elixir 用に拡張 (`DATASET=humaneval-elixir` / `mbpp-elixir`)
- `scripts/eval/run_yamato_min_elixir.py` (Python runner) を新規作成、`run_yamato_min_go.py` を元に Elixir 用に移植
- `scripts/eval/judge_win_condition_elixir.py` を `judge_win_condition_go.py` から移植

### Step 8 — 検証 + ablation (0.5d)

- 4 mode を取る (Go 版 ablation と同じ構成):
  - baseline (bare Bumblebee `Bumblebee.Text.generation`)
  - no-kotodama (KotodamaDecoder elixir, bias=OFF, firewall=ON)
  - no-firewall (KotodamaDecoder elixir, bias=ON, firewall=OFF)
  - full (KotodamaDecoder elixir, bias=ON, firewall=ON)
- vanilla vs no-kotodama の **byte-identical** 確認 (Firewall の悪影響不在)
- pass@1 / mix compile rate の比較

## 残る不確定要素

- Qwen3-Coder-30B-A3B の Elixir 生成品質 (Qwen2.5-Coder の Go 生成と比較してどうか) は未測定。Step 1 ベンチで verify するまで分からない
- A6000 48GB pod が RunPod で常時確保可能か (region/queue 依存)
- 30B int8 が実測で本当に A6000 48GB に収まるか (理論 ~30-35 GB だが KV cache + activation のオーバーヘッド未測定)
- `Axon.Quantization.quantize/2` が Qwen3 系の MoE 構造で正しく動くか (Bumblebee 0.7.0 の Qwen3 サポートは bf16 主体、quantize と組み合わせた前例なし)

## 解消済の不確定要素 (2026-05-21 確認)

- ~~Bumblebee の int4 / GGUF サポート状況~~ → **未対応** ([Issue #249](https://github.com/elixir-nx/bumblebee/issues/249) / [#413](https://github.com/elixir-nx/bumblebee/issues/413) Open のまま、weight-only int8 のみ)。Q4 前提のロードマップは放棄、int8 ベースに切替
- ~~MultiPL-E elixir のテストハーネス互換性~~ → **`elixir <file>` CLI で `.exs` を直接実行、5s timeout、exit code ベース**。`mix test` 不要、Go 版 `go_eval.py` 構造を直接転用可

## Win Condition (option A 版に再定義)

本 pivot の主目的が **Firewall を BEAM プロセス境界で完成させる**ことなので、Win Condition も
LM 性能ではなく Firewall の隔離特性を中心に置く:

### 一次基準 (Firewall 検証 — 必達)

1. **vanilla (no-kotodama) vs no-firewall の byte-identical 完全一致** (humaneval-elixir 161 問 × 3 seed)
   - Firewall を入れても生成への観測可能な悪影響が無いこと
   - Go 版で 374/374 達成済 ([sampling_path_issue.md](sampling_path_issue.md))、Elixir では BEAM 隔離により **より低コスト**で達成できるはず
2. **`YomotsuHirasaka` の型契約テストが ExUnit で 100% 緑**
   - `is_binary/1` guard で `Nx.Tensor` 等が構造的に reject されること
   - evaluator が別 PID で動き、message passing 経由でしか verdict が流れないこと

### 二次基準 (LM 性能 — 参考値)

- humaneval-elixir 161 問 × 3 seed × 4 mode (baseline / no-kotodama / no-firewall / full)
- pass@1 の **mode 間差** を観測。Go 版 mbpp-go で attribution 未解決だった「言霊 bias 単独寄与」の Elixir での挙動を確認 ([project-go-roadmap-state](../C:/Users/mimat/.claude/projects/c--Users-mimat-Yamato-no-Mikoto/memory/project-go-roadmap-state.md))

**Go 版との pass@1 比較は行わない**:
- LM が違う (Qwen2.5-Coder-7B vs Qwen3-Coder-30B-A3B)、量子化が違う (bf16 vs int8)、言語が違う (Go vs Elixir)、ハードが違う (A5000 vs A6000)
- 同一条件で測れないものを比べても結論が出ない ([feedback-ablate-before-celebrating](../C:/Users/mimat/.claude/projects/c--Users-mimat-Yamato-no-Mikoto/memory/feedback-ablate-before-celebrating.md))
- Elixir 版の Win Condition は **Elixir 内**で完結させる (Firewall 一次基準 + mode 間差の二次基準)

## 関連メモリ

- `project-firewall-purpose.md` — Firewall = 隔離壁が本来目的、HALT/REPAIR は副次
- `project-elixir-pivot-viability.md` — 技術的ボトルネック評価
- `project-go-roadmap-state.md` — Go 版の現状 (attribution 未解決のまま国譲り)
- `feedback-kotodama-mask-counterproductive` — −inf マスクは TS で逆効果、soft bias 方針は Go/Elixir 共通
- [sampling_path_issue.md](sampling_path_issue.md) — Go 版の修正 D (物理サイドチャネル除去) ログ
