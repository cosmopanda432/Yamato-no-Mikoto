defmodule KojikiLM.Verdict do
  @moduledoc """
  L5 → L3 で許可される verdict atom: `:commit | :repair | :halt`。

  Python 版の `Verdict` Enum に対応。Elixir では atom 集合を `defguard` で公開し、
  パターンマッチ・guard・関数ヘッダ条件のいずれでも型レベル拘束できるようにする。
  """

  @type t :: :commit | :repair | :halt

  @valid_verdicts [:commit, :repair, :halt]

  defguard is_verdict(v) when v in [:commit, :repair, :halt]

  @spec valid?(any()) :: boolean()
  def valid?(v), do: v in @valid_verdicts

  @spec valid_verdicts() :: [t()]
  def valid_verdicts, do: @valid_verdicts
end
