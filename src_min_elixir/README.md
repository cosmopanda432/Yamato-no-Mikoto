# src_min_elixir 【中止 2026-05-21、保存のみ】

> ⛔ **本 Mix project 路線は中止**。Bumblebee 0.7.0 が Qwen3 MoE / Qwen2 系を未対応のため
> Step 1 (LM load) 不可。詳細は [docs/旧ドキュメント/roadmap_min_elixir.md](../docs/旧ドキュメント/roadmap_min_elixir.md) の
> 「中止理由」セクション参照。
>
> 新計画 = `src_min_eli2/` (Python + Elixir target ハイブリッド、Firewall は src_min_go 再利用)。
> 詳細 [docs/roadmap_eli2.md](../docs/roadmap_eli2.md)。
>
> 本フォルダは **「Firewall を BEAM プロセス境界で書けた証拠」** として保存。62 tests 緑、
> Step 3 (L5) / Step 4 (YomotsuHirasaka) / Step 6 (機械的 REPAIR) / Step 7 (MultiPL-E runner) 実装済。
> 将来 Bumblebee が Qwen2/Qwen3 MoE をサポートした時に Step 1 だけ書けば再起動可能。

yamatoLLM Elixir 版 — Firewall (黄泉比良坂) を **BEAM プロセス境界** で実装する pivot 試験。

詳細背景: `~/.claude/projects/c--Users-mimat-Yamato-no-Mikoto/memory/project-elixir-pivot-viability.md`

## 現状 (2026-05-21)

8 ステップのうち **Step 3 / 4 / 6 / 7 を本実装**。Linux + Elixir 1.18 ローカル
(asdf 経由) で `mix test` が 62/62 緑。Step 1 / 2 / 5 / 8 は GPU (RunPod A6000)
依存のため未着手。

| Step | 内容 | 状態 |
|---|---|---|
| 1 | Mix project + Bumblebee (~> 0.7) + Qwen3-Coder-30B-A3B-Instruct load (int8 量子化) | mix.exs の deps を comment-out で配置、本実装は RunPod 待ち |
| 2 | `KojikiLM.L3` GenServer (generate + sampling) | stub のみ (Step 1 待ち) |
| 3 | `KojikiLM.L5` GenServer (`System.cmd("elixir", [.exs])` で別プロセス実行) | **本実装** (subprocess + heuristic 二段) |
| 4 | `KojikiLM.YomotsuHirasaka` (BEAM proc 境界の薄ラッパー) | **本実装** |
| 5 | 型位置 bias (set-theoretic types からの抽出) | 未着手 (Elixir 1.20 待ち) |
| 6 | 機械的 REPAIR (`Code.format_string!` + `Code.string_to_quoted` hint パーサ) | **本実装** |
| 7 | MultiPL-E elixir runner (`elixir <file>` CLI ベース、`mix test` 不要) | **本実装** ([scripts/eval/elixir_eval.py](../scripts/eval/elixir_eval.py)) |
| 8 | 検証 + ablation (vanilla vs full の byte-identical) | 未着手 (Step 1/2 待ち) |

**2026-05-21 確定方針** (詳細 [docs/旧ドキュメント/roadmap_min_elixir.md](../docs/旧ドキュメント/roadmap_min_elixir.md)):

- **LM**: Qwen3-Coder-**30B**-A3B-Instruct (80B Next は Bumblebee の int4/GGUF 未対応のためコスト 6× で除外)
- **量子化**: weight-only int8 (`Axon.Quantization`)
- **GPU**: A6000 48GB ($0.49/h)

## 何を Step 4 で実証するか

`project-firewall-purpose.md` で定義した「L3 (生成ランタイム) と L5 (評価器) の **構造的データ非干渉壁**」を、Elixir では **BEAM プロセス境界** で自動成立させる。

- L3 → L5 ペイロードは `%KojikiLM.L3ToL5Payload{}` struct のみ (`text/step_idx/prompt_id`、tensor 不可)
- L5 → L3 verdict は `%KojikiLM.L5ToL3Verdict{}` struct のみ (`verdict ∈ {commit, repair, halt}` と `v_score ∈ [0,1]`)
- 評価器を別 GenServer として動かせば、各プロセスが独自 heap を持つため、Python 版で苦労した「hidden_state がオブジェクト参照経由で漏れる」事故が **言語レベルで不可能**

Python 版で `__post_init__` で手動 assert していた型契約は、Elixir では `defstruct` の `@enforce_keys` + guard ベース validator + `defguard is_verdict/1` で表現する。`Nx.Tensor` は binary でないため、`is_binary/1` guard を通れば自動的に rejection される。

## 動かし方

Elixir 1.18 以上 + Erlang/OTP 27 が必要 (Step 5 の set-theoretic types を使うとき
だけ Elixir 1.20 が要る。Step 3/4/6/7 は 1.18 で動く)。

Linux (Ubuntu) で asdf を使うなら:

```bash
# 1. ビルド deps (Erlang を source build するため)
sudo apt-get install -y build-essential autoconf m4 libssl-dev libncurses-dev

# 2. asdf 導入
git clone https://github.com/asdf-vm/asdf.git ~/.asdf --branch v0.14.1 --depth 1
echo '. "$HOME/.asdf/asdf.sh"' >> ~/.bashrc && . ~/.asdf/asdf.sh

# 3. plugin + 本体
asdf plugin add erlang && asdf plugin add elixir
KERL_CONFIGURE_OPTIONS="--without-wx --without-debugger --without-observer --without-jinterface --without-megaco --without-odbc --without-javac" \
  asdf install erlang 27.3.4.11
asdf install elixir 1.18.4-otp-27
# src_min_elixir/ には .tool-versions が置いてあるので cd するだけで切替わる
```

Windows なら `winget install Erlang.Erlang && winget install ElixirLang.Elixir`。

```bash
cd src_min_elixir
mix deps.get        # Step 4 + 3 + 6 段階では deps なしなので no-op
mix test            # 62 tests, 0 failures が想定値
mix format          # `.formatter.exs` に従う
```

## ディレクトリ

```
src_min_elixir/
├── mix.exs
├── .formatter.exs
├── .tool-versions                # erlang 27.3.4.11 / elixir 1.18.4-otp-27
├── README.md
├── lib/
│   └── kojiki_lm/
│       ├── verdict.ex            # Verdict atom + defguard is_verdict/1
│       ├── l3_to_l5_payload.ex   # 葦原 → 黄泉 struct + new!/3 validator
│       ├── l5_to_l3_verdict.ex   # 黄泉 → 葦原 struct + new!/2 validator
│       ├── yomotsu_hirasaka.ex   # GenServer ゲートウェイ本体
│       ├── l3.ex                 # Step 2 stub (Bumblebee 待ち)
│       ├── l5.ex                 # Step 3 本実装 (subprocess + heuristic 二段)
│       ├── mechanical_repair.ex  # Step 6 本実装 (Code.format_string! + hint)
│       └── config.ex             # Step 1 stub
└── test/
    ├── test_helper.exs
    ├── support/
    │   └── test_evaluator.ex     # 別プロセス評価器 (BEAM 境界テスト用)
    └── kojiki_lm/
        ├── verdict_test.exs
        ├── l3_to_l5_payload_test.exs
        ├── l5_to_l3_verdict_test.exs
        ├── yomotsu_hirasaka_test.exs
        ├── l5_test.exs                # 14 tests: empty / 構文 / subprocess / GenServer 境界
        └── mechanical_repair_test.exs # 9 tests: format / hint / chain
```

## Python 版との対応

| Python (src_min_go/kojiki_lm/yomotsu_hirasaka.py) | Elixir |
|---|---|
| `@dataclass(frozen=True)` | `defstruct` (BEAM 上では値は不変) |
| `__post_init__` の `isinstance` assert | guard ベース private validator (`is_binary/1`, `is_integer/1`, `>= 0`) |
| `Verdict` Enum class | `:commit / :repair / :halt` atoms + `defguard is_verdict/1` |
| `YomotsuHirasaka` class | `KojikiLM.YomotsuHirasaka` GenServer |
| `gateway.send(payload)` | `KojikiLM.YomotsuHirasaka.send(server, payload)` |
| evaluator は callable | evaluator は `pid` (別 GenServer) もしくは 1-arg 関数 |
