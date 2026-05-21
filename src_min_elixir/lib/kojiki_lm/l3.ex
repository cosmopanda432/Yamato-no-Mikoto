defmodule KojikiLM.L3 do
  @moduledoc """
  葦原 (L3, 生成ランタイム) GenServer の **stub**。

  Step 2 で実装する内容:

  - Bumblebee で load した Qwen3-Coder-Next を保持
  - `generate/2` で 1-prompt あたり token-by-token decode を実行
  - 各 token 後に `KojikiLM.YomotsuHirasaka.send/2` で L5 verdict を取得
  - verdict = `:halt` なら early stop、`:repair` なら error_message を prompt 末尾に追加して再 decode

  本 module は Step 2 着手時に GenServer 化する。現段階はインタフェースのみ。
  """

  alias KojikiLM.{L3ToL5Payload, YomotsuHirasaka}

  @doc """
  Step 2 で本実装する。現状は NotImplementedError 相当を raise。
  """
  @spec generate(GenServer.server(), String.t(), keyword()) :: String.t()
  def generate(_gateway, _prompt, _opts \\ []) do
    raise "KojikiLM.L3.generate/3 is not implemented yet (Step 2)"
  end

  @doc """
  step 番号 + 中間 text を YomotsuHirasaka 経由で L5 に問い合わせるヘルパ。

  実装済 — Step 2 の中で内部呼び出し用に使う。
  """
  @spec query_verdict(GenServer.server(), String.t(), non_neg_integer(), String.t()) ::
          KojikiLM.L5ToL3Verdict.t()
  def query_verdict(gateway, text, step_idx, prompt_id) do
    payload = L3ToL5Payload.new!(text, step_idx, prompt_id)
    YomotsuHirasaka.send(gateway, payload)
  end
end
