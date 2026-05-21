defmodule KojikiLM.Config do
  @moduledoc """
  Step 1 の stub — Qwen3-Coder-Next を Bumblebee で load するときの設定。

  Step 4 + 骨格段階では未使用。Step 1 着手時に Bumblebee/Nx/EXLA を deps に追加した
  上で、本 module から `Bumblebee.load_model/2` を呼ぶ予定。
  """

  defstruct model_repo: "Qwen/Qwen3-Coder-Next-80B-A3B",
            backend: :exla,
            dtype: :bf16,
            max_new_tokens: 256,
            temperature: 1.0,
            top_p: 0.95,
            seed: 0

  @type t :: %__MODULE__{
          model_repo: String.t(),
          backend: :exla | :binary,
          dtype: :bf16 | :fp16 | :fp32,
          max_new_tokens: pos_integer(),
          temperature: float(),
          top_p: float(),
          seed: non_neg_integer()
        }

  @spec default() :: t()
  def default, do: %__MODULE__{}
end
