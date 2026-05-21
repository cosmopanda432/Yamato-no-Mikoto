defmodule KojikiLM.TestEvaluator do
  @moduledoc """
  テスト専用 evaluator GenServer。`KojikiLM.YomotsuHirasaka` の evaluator として注入し、
  BEAM プロセス境界 (= 別 PID) の上で Firewall が機能することを検証する。

  与えられた関数 (`L3ToL5Payload -> L5ToL3Verdict`) を別プロセスから提供する薄い shim。
  """

  use GenServer

  alias KojikiLM.L3ToL5Payload

  @spec start_link(keyword()) :: GenServer.on_start()
  def start_link(opts) do
    {gen_opts, init_opts} = Keyword.split(opts, [:name])
    GenServer.start_link(__MODULE__, init_opts, gen_opts)
  end

  @impl true
  def init(opts) do
    fun = Keyword.fetch!(opts, :fun)
    {:ok, %{fun: fun, last_caller_pid: nil}}
  end

  @impl true
  def handle_call({:evaluate, %L3ToL5Payload{} = payload}, {caller, _ref}, state) do
    {:reply, state.fun.(payload), %{state | last_caller_pid: caller}}
  end

  def handle_call(:last_caller_pid, _from, state) do
    {:reply, state.last_caller_pid, state}
  end

  @doc "直近の呼び出し元 PID (= YomotsuHirasaka GenServer の PID) を取得"
  @spec last_caller_pid(GenServer.server()) :: pid() | nil
  def last_caller_pid(server), do: GenServer.call(server, :last_caller_pid)
end
