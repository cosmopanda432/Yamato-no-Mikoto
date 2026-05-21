defmodule KojikiLM.L5ToL3Verdict do
  @moduledoc """
  黄泉 (L5, 評価器) → 葦原 (L3, 生成ランタイム) verdict。

  `verdict ∈ {:commit, :repair, :halt}` と `v_score ∈ [0.0, 1.0]` のみ。
  評価器の内部状態 (累積統計・Yomi Archive・テストケース正解) は構造的に渡せない。

  Python 版の `L5ToL3Verdict` frozen dataclass + `__post_init__` 相当を、
  `@enforce_keys` と `new!/2` の `KojikiLM.Verdict.is_verdict/1` guard で表現する。
  """

  require KojikiLM.Verdict

  alias KojikiLM.Verdict

  @enforce_keys [:verdict, :v_score]
  defstruct [:verdict, :v_score]

  @type t :: %__MODULE__{
          verdict: Verdict.t(),
          v_score: float()
        }

  @spec new!(any(), any()) :: t()
  def new!(verdict, v_score) do
    validate_verdict!(verdict)
    validate_v_score!(v_score)
    %__MODULE__{verdict: verdict, v_score: v_score * 1.0}
  end

  defp validate_verdict!(verdict) when Verdict.is_verdict(verdict), do: :ok

  defp validate_verdict!(verdict) do
    raise ArgumentError,
          "L5ToL3Verdict.verdict must be one of #{inspect(Verdict.valid_verdicts())}, " <>
            "got #{inspect(verdict)}. " <>
            "L5 から L3 へ返せるのは :commit / :repair / :halt のみ。"
  end

  defp validate_v_score!(v_score)
       when is_number(v_score) and v_score >= 0.0 and v_score <= 1.0,
       do: :ok

  defp validate_v_score!(v_score) when is_number(v_score) do
    raise ArgumentError, "L5ToL3Verdict.v_score must be in [0.0, 1.0], got #{v_score}"
  end

  defp validate_v_score!(v_score) do
    raise ArgumentError,
          "L5ToL3Verdict.v_score must be number, got #{inspect(v_score)}"
  end
end
