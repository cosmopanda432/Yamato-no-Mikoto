defmodule KojikiLM.L3ToL5Payload do
  @moduledoc """
  葦原 (L3, 生成ランタイム) → 黄泉 (L5, 評価器) ペイロード。

  text と最小メタのみ。tensor / Nx.Tensor / 高次元データ構造は構造的に渡せない。

  - `text`     : 生成テキスト (binary)。`Nx.Tensor` 等は `is_binary/1` を満たさないので reject
  - `step_idx` : decode step (non_neg_integer)
  - `prompt_id`: 識別子 (binary)

  Python 版の `@dataclass(frozen=True)` + `__post_init__` 相当を `@enforce_keys` と
  `new!/3` の guard validator で表現する。
  """

  @enforce_keys [:text, :step_idx, :prompt_id]
  defstruct [:text, :step_idx, :prompt_id]

  @type t :: %__MODULE__{
          text: String.t(),
          step_idx: non_neg_integer(),
          prompt_id: String.t()
        }

  @spec new!(any(), any(), any()) :: t()
  def new!(text, step_idx, prompt_id) do
    validate_text!(text)
    validate_step_idx!(step_idx)
    validate_prompt_id!(prompt_id)
    %__MODULE__{text: text, step_idx: step_idx, prompt_id: prompt_id}
  end

  defp validate_text!(text) when is_binary(text), do: :ok

  defp validate_text!(text) do
    raise ArgumentError,
          "L3ToL5Payload.text must be binary (String), got #{inspect_type(text)}. " <>
            "L5 への送信ペイロードに tensor / hidden_state は渡せません。"
  end

  defp validate_step_idx!(step_idx) when is_integer(step_idx) and step_idx >= 0, do: :ok

  defp validate_step_idx!(step_idx) when is_integer(step_idx) do
    raise ArgumentError, "L3ToL5Payload.step_idx must be >= 0, got #{step_idx}"
  end

  defp validate_step_idx!(step_idx) do
    raise ArgumentError,
          "L3ToL5Payload.step_idx must be integer, got #{inspect_type(step_idx)}"
  end

  defp validate_prompt_id!(prompt_id) when is_binary(prompt_id), do: :ok

  defp validate_prompt_id!(prompt_id) do
    raise ArgumentError,
          "L3ToL5Payload.prompt_id must be binary, got #{inspect_type(prompt_id)}"
  end

  defp inspect_type(value) do
    cond do
      is_list(value) -> "list"
      is_tuple(value) -> "tuple"
      is_map(value) and not is_struct(value) -> "map"
      is_struct(value) -> inspect(value.__struct__)
      is_function(value) -> "function"
      is_pid(value) -> "pid"
      is_reference(value) -> "reference"
      is_port(value) -> "port"
      is_atom(value) -> "atom(#{inspect(value)})"
      is_integer(value) -> "integer"
      is_float(value) -> "float"
      is_binary(value) -> "binary"
      is_bitstring(value) -> "bitstring"
      true -> inspect(value)
    end
  end
end
