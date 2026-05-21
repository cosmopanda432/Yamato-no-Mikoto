defmodule KojikiLM.MixProject do
  use Mix.Project

  def project do
    [
      app: :kojiki_lm,
      version: "0.1.0",
      elixir: "~> 1.18",
      start_permanent: Mix.env() == :prod,
      deps: deps(),
      elixirc_paths: elixirc_paths(Mix.env()),
      description:
        "yamatoLLM Elixir pivot — L3 ↔ L5 Firewall (黄泉比良坂) as BEAM process boundary."
    ]
  end

  def application do
    [
      extra_applications: [:logger]
    ]
  end

  defp elixirc_paths(:test), do: ["lib", "test/support"]
  defp elixirc_paths(_), do: ["lib"]

  defp deps do
    [
      # Step 1 (Bumblebee + Nx + EXLA) で有効化する。Step 4 + 骨格段階では未使用。
      # v0.7.0 (2026-05-16) で Qwen3 サポート追加 (PR #423)、Qwen3-Coder-30B-A3B 系を要求するため最低 0.7。
      # int4/GGUF は未対応 (Issue #249 / #413 Open)、量子化は Axon.Quantization の weight-only int8 のみ。
      # {:bumblebee, "~> 0.7"},
      # {:nx, "~> 0.9"},
      # {:exla, "~> 0.9"},
      # {:axon, "~> 0.7"}    # Axon.Quantization 用
    ]
  end
end
