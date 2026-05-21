# src_min_elixir

yamatoLLM Elixir 版 — Firewall (黄泉比良坂) を **BEAM プロセス境界** で実装する pivot 試験。

詳細背景: `~/.claude/projects/c--Users-mimat-Yamato-no-Mikoto/memory/project-elixir-pivot-viability.md`

## 現状 (2026-05-21)

8 ステップのうち **Step 4 (Firewall 本体) + 骨格 (L3/L5/Config の stub)** までを実装。

| Step | 内容 | 状態 |
|---|---|---|
| 1 | Mix project + Bumblebee + Qwen3-Coder-Next load | mix.exs の deps を comment-out で配置 |
| 2 | `KojikiLM.L3` GenServer (generate + sampling) | stub のみ |
| 3 | `KojikiLM.L5` GenServer (`Code.eval_string` + ExUnit) | stub のみ |
| 4 | `KojikiLM.YomotsuHirasaka` (BEAM proc 境界の薄ラッパー) | **本実装** |
| 5 | 型位置 bias (set-theoretic types からの抽出) | 未着手 |
| 6 | 機械的 REPAIR (`Mix.format` + AST + "did you mean" parser) | 未着手 |
| 7 | MultiPL-E elixir runner (humaneval/mbpp 共通) | 未着手 |
| 8 | 検証 + ablation (vanilla vs full の byte-identical) | 未着手 |

## 何を Step 4 で実証するか

`project-firewall-purpose.md` で定義した「L3 (生成ランタイム) と L5 (評価器) の **構造的データ非干渉壁**」を、Elixir では **BEAM プロセス境界** で自動成立させる。

- L3 → L5 ペイロードは `%KojikiLM.L3ToL5Payload{}` struct のみ (`text/step_idx/prompt_id`、tensor 不可)
- L5 → L3 verdict は `%KojikiLM.L5ToL3Verdict{}` struct のみ (`verdict ∈ {commit, repair, halt}` と `v_score ∈ [0,1]`)
- 評価器を別 GenServer として動かせば、各プロセスが独自 heap を持つため、Python 版で苦労した「hidden_state がオブジェクト参照経由で漏れる」事故が **言語レベルで不可能**

Python 版で `__post_init__` で手動 assert していた型契約は、Elixir では `defstruct` の `@enforce_keys` + guard ベース validator + `defguard is_verdict/1` で表現する。`Nx.Tensor` は binary でないため、`is_binary/1` guard を通れば自動的に rejection される。

## 動かし方

Elixir 1.20 と Mix が必要 (今のマシンには未 install)。Windows なら:

```powershell
# winget で導入
winget install Erlang.Erlang
winget install ElixirLang.Elixir
# あるいは asdf-vm + asdf install elixir 1.20.0-otp-27
```

```bash
cd src_min_elixir
mix deps.get        # Step 4 段階では deps なしなので no-op
mix test            # YomotsuHirasaka の単体テスト
mix format          # `.formatter.exs` に従う
```

## ディレクトリ

```
src_min_elixir/
├── mix.exs
├── .formatter.exs
├── .gitignore
├── README.md
├── lib/
│   └── kojiki_lm/
│       ├── verdict.ex            # Verdict atom + defguard is_verdict/1
│       ├── l3_to_l5_payload.ex   # 葦原 → 黄泉 struct + new!/3 validator
│       ├── l5_to_l3_verdict.ex   # 黄泉 → 葦原 struct + new!/2 validator
│       ├── yomotsu_hirasaka.ex   # GenServer ゲートウェイ本体
│       ├── l3.ex                 # Step 2 stub
│       ├── l5.ex                 # Step 3 stub
│       └── config.ex             # Step 1 stub
└── test/
    ├── test_helper.exs
    ├── support/
    │   └── test_evaluator.ex     # 別プロセス評価器 (BEAM 境界テスト用)
    └── kojiki_lm/
        ├── verdict_test.exs
        ├── l3_to_l5_payload_test.exs
        ├── l5_to_l3_verdict_test.exs
        └── yomotsu_hirasaka_test.exs
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
