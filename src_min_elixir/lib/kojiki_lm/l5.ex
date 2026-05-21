defmodule KojikiLM.L5 do
  @moduledoc """
  黄泉 (L5, 評価器) GenServer の **stub**。

  Step 3 で実装する内容:

  - `Code.string_to_quoted/1` で構文 sanity check
  - 中括弧/丸括弧の収支、危険パターン (`raise "not implemented"` 等) を text レベルで検査
  - 完成コードなら `Code.eval_string/3` で sandbox 実行
  - ExUnit テストハーネスから verdict (`:commit / :repair / :halt`) を決定

  本 module は Step 3 着手時に GenServer 化する。現状は本 module の名前を持つ最低限の
  evaluator process を起動し、`%L3ToL5Payload{}` を受け取ると `:repair` を返す。
  Step 4 の動作確認 (process boundary が成立しているか) には十分。
  """

  use GenServer

  alias KojikiLM.{L3ToL5Payload, L5ToL3Verdict}

  @spec start_link(keyword()) :: GenServer.on_start()
  def start_link(opts \\ []) do
    {gen_opts, init_opts} = Keyword.split(opts, [:name])
    GenServer.start_link(__MODULE__, init_opts, gen_opts)
  end

  @impl true
  def init(_opts), do: {:ok, %{}}

  @impl true
  def handle_call({:evaluate, %L3ToL5Payload{} = payload}, _from, state) do
    verdict = stub_evaluate(payload)
    {:reply, verdict, state}
  end

  # Step 3 までは「空テキストは halt、それ以外は repair (中間状態)」だけ返す。
  # Step 3 で `Code.string_to_quoted/1` + `Code.eval_string/3` + ExUnit を組み込む。
  defp stub_evaluate(%L3ToL5Payload{text: ""}), do: L5ToL3Verdict.new!(:halt, 0.0)
  defp stub_evaluate(%L3ToL5Payload{}), do: L5ToL3Verdict.new!(:repair, 0.5)
end
