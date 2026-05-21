# Roadmap (Minimum) — yamatoLLM Elixir 版 **【中止 2026-05-21】**

> ⛔ **本 pivot は 2026-05-21 に中止**。
> Bumblebee 0.7.0 (現行最新) では Step 1 (Bumblebee + Qwen 系 load) を満たせる組み合わせが
> 存在しないことが pod 上の実機検証で確定。代替モデルもすべて未対応。詳細は本 doc 末尾の
> 「中止理由」セクション参照。**Step 3/4/6/7 (62 tests 緑) のコード/Mix project は保存**
> (Firewall を BEAM プロセス境界で書ける証拠として価値あり)。

主目的: **L3 ↔ L5 の絶対的隔離壁 (Firewall / 黄泉比良坂) を BEAM プロセス境界で完成
させる** (`project-firewall-purpose.md` / `project-elixir-pivot-viability.md` 参照)。

Go 版 ([docs/roadmap_min_go.md](roadmap_min_go.md)) で「言霊 bias の単独寄与が不可視」
だった一方、**Firewall の隔離契約は 374/374 byte-identical で確認済** ([sampling_path_issue.md](sampling_path_issue.md))。
本ターゲットは「Firewall を Python の `__post_init__` で **手で** 守る」から「言語/ランタイム
が **構造的に** 守る」へのレベルアップ **を狙ったが、LM 側のエコシステム未成熟で頓挫**。

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
| 1 | Mix project + Bumblebee + Qwen3-Coder-Next load | 0.5d | 🟡 mix.exs の deps 配置のみ (comment-out)。本実装は RunPod A6000 待ち |
| 2 | `KojikiLM.L3` GenServer (generate + sampling) | 1-2d | 🟡 stub のみ (Step 1 待ち) |
| 3 | `KojikiLM.L5` GenServer (`Code.eval_string` + ExUnit) | 1d | ✅ **本実装完了** (subprocess + heuristic 二段、14 tests 緑) |
| 4 | `KojikiLM.YomotsuHirasaka` (BEAM proc 境界の薄ラッパー) | 0.5d | ✅ **本実装完了** |
| 5 | **L5 ハルシネーション検出器拡張** (Gemini 精査由来 3 項目: ghost function / defstruct mismatch / hint field) | 1d | ⬜ **着手前提**: Step 1+2 完了 → Step 8 Phase 1 (Firewall byte-identical) **緑** を確認してから |
| 6 | 機械的 REPAIR (`Mix.format` + AST + "did you mean" parser) | 0.5d | ✅ **本実装完了** (`Code.format_string!` + hint パーサ、9 tests 緑) |
| 7 | MultiPL-E elixir runner (humaneval/mbpp 共通) | 0.5d | ✅ **本実装完了** ([scripts/eval/elixir_eval.py](../scripts/eval/elixir_eval.py)、smoke 4 サンプル OK) |
| 8 | 検証 (Phase 1: Firewall 物理隔離 byte-identical) + ablation (Phase 2: 4 mode pass@1) | 0.5d + 0.5d | ⬜ 未着手 (Step 1/2 完了後に走らせる)。**Phase 1 → Step 5 → Phase 2 の順** |

## 2026-05-21 (午後) セッションで完了したもの (Step 3 / 6 / 7、Linux 検証)

Linux + RTX 3060 + asdf 環境 (GPU 不要分のみ) で:

- Erlang/OTP 27.3.4.11 + Elixir 1.18.4-otp-27 を asdf でユーザー領域に install
- `mix.exs` の elixir 制約を `~> 1.20` → `~> 1.18` に緩和 (Step 5 着手時に戻す)
- `.tool-versions` を `src_min_elixir/` に置いて asdf auto-switch
- **Step 4 再検証**: 既存テスト 39/39 緑、compile warning 2 件 (handle_call の clause grouping / `0.0` パターン) を修正
- **Step 3 本実装**: `lib/kojiki_lm/l5.ex`
  - 評価フロー: 空 → :halt / `Code.string_to_quoted` → :repair (incomplete) / :halt (broken) / :ok → tests あれば `System.cmd("timeout 5 elixir tmp.exs")`、なければヒューリスティック
  - subprocess 結果分類: exit 0 → :commit、AssertionError → :halt 0.2、CompileError → :repair 0.4、UndefinedFunctionError → :halt 0.25、timeout (124/137) → :halt 0.1
  - tests を **L5 が所有** (tests_by_prompt_id) → L3 には絶対漏れない
  - 14 tests: empty / 構文 4 種 / subprocess passing/failing/undef/compile-error/timeout / YomotsuHirasaka 経由 BEAM 境界 / start_link
- **Step 6 本実装**: `lib/kojiki_lm/mechanical_repair.ex`
  - `Code.format_string!/2` で整形 + `Code.string_to_quoted/2` の error から "did you mean" hint パース
  - chain 構造で複数 tool を順次適用 (`[:format, :hint]` がデフォルト)
  - 9 tests: format-only / hint-only / chain / 壊れた構文での graceful fallback / arity 2 限定 (tests を渡せないことの構造的保証)
- **Step 7 本実装**: `scripts/eval/elixir_eval.py`
  - go_eval.py を Elixir 用に port。`elixir <file>` + 5s timeout、exit code + stderr パターンで分類
  - PRIMARY: test_pass_rate / SECONDARY: compile_pass_rate / TERTIARY': undefined_rate
  - `--mechanical-repair` で `Code.format_string!` を subprocess で適用 (tests は context に渡さない、Goodhart 回避)
  - smoke 4 サンプル (pass/wrong/undef/syntax_err) で classification 正常動作確認
- **全体**: `mix test` で **62/62 緑** (Step 4 の 39 + Step 3 の 14 + Step 6 の 9)

ローカルで検証できないのは Step 1/2/5/8 (GPU/A6000 必須 or Elixir 1.20 待ち)。

## 2026-05-21 (午前) セッションで完了したもの (Step 4 + 骨格)

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

### Step 5 — L5 ハルシネーション検出器拡張 (1d)

**着手条件**: Step 1 + Step 2 + Step 8 Phase 1 (Firewall byte-identical 検証) が緑になってから。
先に物理隔離が成立していることを確認してから L5 を改造する (Firewall の効果と L5 改善効果を切り分けるため)。

Gemini 精査 (2026-05-21) で Julia 論文の Elixir 翻案案を検討した結果、本プロジェクト
(pre-trained Qwen3-Coder-30B + frozen) で**取り込めるのは以下 3 項目のみ**。
モデル architecture 改造 / fine-tuning / auxiliary loss 系の提案は scope 外。

#### Step 5a — Ghost function checker (AST レベル)

- `Code.string_to_quoted/1` で生成テキストを AST 化
- AST walk で `{:., _, [{:__aliases__, _, mod}, fun]}` 形態の関数呼び出しを全部抽出
- 各 `(Mod, fun, arity)` について `Code.ensure_loaded?(Mod)` + `function_exported?(Mod, fun, arity)` で存在確認
- 未定義の関数呼び出しが見つかれば verdict = `:halt` v_score = 0.15、`hint = "Hint: #{Mod}.#{fun}/#{arity} is not defined. Did you mean ...?"`
- 既存の subprocess `UndefinedFunctionError` 検出 ([l5.ex:230-259](../src_min_elixir/lib/kojiki_lm/l5.ex#L230-L259)) と冗長だが、**こちらは実行前**に検出できるため early HALT が効く

#### Step 5b — defstruct ↔ %X{field:} mismatch checker

- AST walk で `{:defstruct, _, [fields]}` を集めて module ごとに field atom set を構築
- 同じ AST で `{:%{}, _, [{field_atom, _}, ...]}` を含む `{:%, _, [{:__aliases__, _, mod}, ...]}` ノードを走査
- 未定義 field を参照していれば verdict = `:repair` v_score = 0.4、`hint = "Hint: Struct %#{Mod}{} does not contain :#{field}. Check defstruct."`
- repair で hint を L3 に返し、prompt 末尾追加 → 再 decode

#### Step 5c — `%L5ToL3Verdict{}` に `hint: String.t() | nil` field 追加

- 現在の verdict は `verdict + v_score` のみ。修復ヒントを構造的に持たせる
- 隔離契約は維持: hint は **L5 が生成した自然言語文字列**であって、評価器内部状態 (テストケース・累積統計) は載せない (Goodhart 回避)
- L3 側は `verdict.hint` を prompt の末尾に追加して decode を再起動 (= [project-firewall-purpose](../C:/Users/mimat/.claude/projects/c--Users-mimat-Yamato-no-Mikoto/memory/project-firewall-purpose.md) の修正 E 相当)
- `%L5ToL3Verdict{}` の existing tests (`L5ToL3VerdictTest`) は `hint: nil` でも通る後方互換にする

#### 採用しなかった Gemini 提案 (記録)

| 不採用 | 理由 |
|---|---|
| @spec 整合性 = Julia type stability 代替 | MultiPL-E elixir prompts に @spec なし、Dialyzer の success typing は欠如を flag しない |
| 3-phase generation (Module → Specs → Implementations) | benchmark prompt 構造と非整合、可比性を失う |
| Definition-aware attention (Pathway 2) | architecture 改造、scope 外 |
| Type-Hierarchy Embedding (Ecto/Phoenix 静的ハッシュ) | fine-tuning 前提、benchmark は Ecto/Phoenix 不使用 |
| Pipeline 型伝播 auxiliary loss | training 前提、Elixir は値伝播 (型伝播ではない) |
| TsukuyomiTypeHead 直接移植 | Qwen3-Coder に第二 head 無し、再訓練必要 |

旧 Step 5 の「Elixir 1.20 set-theoretic types からの position 抽出」は**棚上げ** (1.20 stable 待ち + 動的型現実とのズレで効果検証経路が不明確)。

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

### Step 8 — 検証 + ablation (Phase 1 + Phase 2)

**実行順序が重要**: Phase 1 → Step 5 → Phase 2。Phase 1 で Firewall の物理隔離を先に
確認してから L5 改造に入り、Phase 2 で改造後の効果を測る。

#### Ablation の 2 軸

| 軸 | OFF | ON |
|---|---|---|
| A. Firewall pathway | L3 が完成テキストを自分で済ます (subprocess 検査せず) | L3 → YomotsuHirasaka → L5 (別 PID) で verdict 取得 |
| B. L5 拡張 (Step 5) | L5 は subprocess + heuristic 評価のみ (現状) | L5 に ghost function / defstruct mismatch checker と hint 追加 |

#### Phase 1 — Firewall 物理隔離 byte-identical 検証 (0.5d、Step 5 着手前)

- 2 mode のみ比較:
  - `bare` = bare Bumblebee `Bumblebee.Text.generation` (A=OFF)
  - `firewall-only` = L3 → YomotsuHirasaka → L5(現状の subprocess + heuristic) (A=ON, B=OFF)
- humaneval-elixir 161 問 × 3 seed
- **expected: 161/161 × 3 = 483/483 で raw_completion byte-identical**
  - Go 版で 374/374 達成済 ([sampling_path_issue.md](sampling_path_issue.md))、BEAM 隔離により Elixir は **より低コストで達成できるはず**
  - 不一致が出たら Firewall pathway に物理サイドチャネルがある証拠 = bug
- ここで Win Condition 一次基準が達成される。**Step 5 はこの後**

#### Phase 2 — 4 mode ablation (0.5d、Step 5 完了後)

| Mode | A: Firewall | B: L5 拡張 | 目的 |
|---|---|---|---|
| `bare` | OFF | — | LM 単体の baseline pass@1 / undef rate |
| `firewall-only` | ON | OFF | Firewall pathway の効果 (Phase 1 と同設定、pass@1 で見る) |
| `l5-enhanced-no-fw` | OFF | ON | Step 5 改造を Firewall なしで適用、isolation の対照 |
| `full` | ON | ON | 完成形 |

- 評価指標 (優先順):
  1. **undefined-symbol rate / compile pass rate** (= hallucination 軸、本プロジェクト主目的の補助) — Step 5 拡張で下がるか
  2. pass@1 (副次)
  3. byte-identical 保持 — `bare` vs `firewall-only` (Phase 1 と同じ)、`l5-enhanced-no-fw` vs `full` (B 軸 ON でも Firewall が悪影響を持たないこと)
- 二次基準: Step 5 拡張で undef rate が下がりかつ pass@1 が下がらないこと (Goodhart 回避)

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

### 一次基準 (Firewall 検証 — 必達、Step 8 Phase 1 で達成)

1. **`bare` vs `firewall-only` の byte-identical 完全一致** (humaneval-elixir 161 問 × 3 seed = 483 サンプル)
   - Firewall pathway を入れても生成への観測可能な悪影響が無いこと
   - Go 版で 374/374 達成済 ([sampling_path_issue.md](sampling_path_issue.md))、Elixir では BEAM 隔離により **より低コスト**で達成できるはず
2. **`YomotsuHirasaka` の型契約テストが ExUnit で 100% 緑**
   - `is_binary/1` guard で `Nx.Tensor` 等が構造的に reject されること
   - evaluator が別 PID で動き、message passing 経由でしか verdict が流れないこと

### 二次基準 (ハルシネーション軸 — Step 8 Phase 2 で測定)

- humaneval-elixir 161 問 × 3 seed × 4 mode (`bare` / `firewall-only` / `l5-enhanced-no-fw` / `full`)
- **undefined-symbol rate / compile pass rate** の mode 間差を優先指標とする
  - 本プロジェクトの設計意図では型予測 = ハルシネーション検出 (= 未定義シンボル / 型不整合の早期検知 → Firewall HALT/REPAIR signal) であり、pass@1 向上ではない
  - Step 5 拡張 (ghost function + defstruct checker) で undef rate が下がるかが本来の効果指標
- pass@1 は副次。Go 版 mbpp-go で attribution 未解決だった「言霊 bias 単独寄与」の Elixir 版での挙動を観察するに留める

**Go 版との pass@1 比較は行わない**:
- LM が違う (Qwen2.5-Coder-7B vs Qwen3-Coder-30B-A3B)、量子化が違う (bf16 vs int8)、言語が違う (Go vs Elixir)、ハードが違う (A5000 vs A6000)
- 同一条件で測れないものを比べても結論が出ない ([feedback-ablate-before-celebrating](../C:/Users/mimat/.claude/projects/c--Users-mimat-Yamato-no-Mikoto/memory/feedback-ablate-before-celebrating.md))
- Elixir 版の Win Condition は **Elixir 内**で完結させる (Firewall 一次基準 + mode 間差の二次基準)

## 関連メモリ

- `project-firewall-purpose.md` — Firewall = 隔離壁が本来目的、HALT/REPAIR は副次
- `project-elixir-pivot-viability.md` — 技術的ボトルネック評価 (本中止で前提が崩れたため要再検証)
- `project-go-roadmap-state.md` — Go 版の現状 (attribution 未解決のまま国譲り)
- `feedback-kotodama-mask-counterproductive` — −inf マスクは TS で逆効果、soft bias 方針は Go/Elixir 共通
- [sampling_path_issue.md](sampling_path_issue.md) — Go 版の修正 D (物理サイドチャネル除去) ログ

## 中止理由 (2026-05-21、RunPod RTX 6000 Ada 上の実機検証で確定)

memory `project-elixir-pivot-viability.md` の「技術的ボトルネックほぼ無し」評価は **誤り**だった。
実機 setup で発覚した複合的 blocker:

### 1. Bumblebee 0.7.0 が我々が使いたい LM を全部 サポートしていない

`bumblebee/lib/bumblebee.ex` の `@transformers_class_to_model` に登録されている causal LM:
Bart / Gemma / Gemma3 / GptBigCode / GptNeoX / Llama / MBart / Mistral / ModernBertDecoder / Phi / Phi3 / **Qwen3 (dense のみ)** / Roberta / SmolLM3 / XLMRoberta。

| LM 候補 | architecture (config.json) | Bumblebee 0.7.0 対応 |
|---|---|---|
| Qwen3-Coder-30B-A3B-Instruct (1st choice) | `Qwen3MoeForCausalLM` | ❌ Qwen3 MoE 未対応 (dense のみ) |
| Qwen3-Coder-Next 80B-A3B | `Qwen3NextForCausalLM` (MoE 派生) | ❌ 同上 |
| Qwen2.5-Coder-7B/32B (Go/TS 版 LM、互換性 desired) | `Qwen2ForCausalLM` | ❌ Qwen2 系 module 自体無し |
| StarCoder2-15B (代替 coder 候補) | `Starcoder2ForCausalLM` (model_type=`starcoder2`) | ❌ 新世代、GQA/SWA で別アーキ、未対応 |
| (旧) StarCoder / SantaCoder | `gpt_bigcode` | ✅ ただし code 性能古い |
| Qwen3-14B / 32B dense | `Qwen3ForCausalLM` | ✅ ただし code 特化なし |
| CodeLlama 7B/13B/34B | `LlamaForCausalLM` | ✅ ただし Llama license |

**Bumblebee 純血で「code 特化 + 現行 Qwen系」を動かす経路が無い**。

### 2. EXLA 0.12 + CUDA 12.4 pod の互換性問題 (解決済だが手間)

setup 中に判明した必要パッチ:
- `libnvshmem3-cuda-12` apt install + ldconfig 登録 (NVSHMEM 3.6.5)
- `libcudnn9-cuda-12` apt install (cuDNN 9)
- `libnvrtc-builtins.so.12.4` → `.so.12.9` の symlink (CUDA 12.9 期待)
- `nvshmem_transport_ibrc.so.5` → `.so.3` の symlink (ABI mismatch を symlink で凌ぐ)
- `libnccl2` を 2.21.5 → 2.30.4-1+cuda12.9 にアップグレード (`ncclCommWindowDeregister` symbol 必要)

EXLA 0.12 は CUDA 12.9 + NCCL 2.30+ + NVSHMEM 3.x 想定でビルドされているため、CUDA 12.4 pod では
これら全部を個別に対処する必要があり、re-pod 時に再現性が低い。

### 3. 全部終わってからの blocker (= LM load 不可) の被害が大きい

setup 約 30 分 (Erlang 22.8min + model DL 4min + その他) を消費した後、smoke 1 行目で:
```
** (ArgumentError) could not match the class name "Qwen3MoeForCausalLM" to any of the supported models
```
で停止。code path 上のごく早い段階で死ぬので「もう少し進めば動く」感触が無く、根本対策
(Bumblebee fork) が必要になることが pivot 開始から 5h 後に判明。

### 4. 投資判断の修正

memory `project-elixir-pivot-viability.md` の **5-7 day 投資** 見積もりは Bumblebee 側の
LM 対応工数 (Qwen3 MoE adapter or Qwen2 adapter の Elixir 移植) を含まない。これを足すと
**実態は 10-15 day 投資**で、Go 版に戻って attribution 解決する方が ROI 高い。

### 完了済の成果物 (保存)

中止時点で動いていたもの:
- `src_min_elixir/` Mix project 一式
- 62 tests 緑: Step 3 (L5 subprocess + heuristic 評価器) / Step 4 (YomotsuHirasaka BEAM 境界 Firewall) / Step 6 (Mix.format + hint パーサ)
- `scripts/eval/elixir_eval.py` (Python orchestrator、`elixir <file>` 実行 + classify)
- `scripts/runpod_bench_elixir.sh` (RunPod setup runbook)
- `scripts/smoke_qwen3.exs` (Step 1 smoke、Bumblebee Qwen MoE/Qwen2 が来たら再利用可)

これらは「Firewall を BEAM プロセス境界で書ける」ことの**コード上の証拠**として残す。将来
Bumblebee が Qwen2/Qwen3 MoE をサポートしたら、Step 1 だけ実行すれば pipeline 再起動可能。

### 教訓 (durable knowledge)

「動的型言語 + LM エコシステム」の組み合わせは **LM 側エコシステム**が律速であり、言語の
理論的優位 (Erlang/Elixir の BEAM プロセス境界による Firewall 自動成立) よりも、 **その
言語向けの LM SDK がどこまで現行モデルを追えているか** が pivot の成否を決める。

設計時点で確認すべきだったこと:
- 使いたい LM の `config.json` の `architectures` が SDK に登録されているか
- SDK の最新リリースで対応されているのか、Issue/PR レベルなのか
- CUDA / cuDNN / NCCL の pod 環境と SDK ビルドの整合性

これらは Python (transformers) ではほぼ全 LM がデフォルト対応のため見過ごしがち。
Elixir/Bumblebee / Rust/Candle / Go/llama.cpp など **後発 SDK** に行く前にチェックリスト化すべき。
