defmodule KojikiLM.MixProject do
  use Mix.Project

  def project do
    [
      app: :kojiki_lm,
      version: "0.1.0",
      elixir: "~> 1.20",
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
      # {:bumblebee, "~> 0.6"},
      # {:nx, "~> 0.9"},
      # {:exla, "~> 0.9"}
    ]
  end
end
