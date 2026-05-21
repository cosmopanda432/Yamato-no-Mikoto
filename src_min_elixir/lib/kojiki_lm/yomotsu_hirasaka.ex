defmodule KojikiLM.YomotsuHirasaka do
  @moduledoc """
  黄泉比良坂 (Yomotsu Hirasaka) — L3 ↔ L5 一方向ゲートウェイ (Elixir / BEAM 版)。

  Python 版の `YomotsuHirasaka` クラスを GenServer に置き換えたもの。

  ## BEAM プロセス境界 = Firewall 物理層

  - evaluator が `pid` (別 GenServer) の場合、L3 ↔ L5 の通信は **必ず Erlang メッセージ
    パッシング**を経由する。送信側のオブジェクト参照は受信側に渡らず (term は copy)、
    Python 版で問題になった「hidden_state がオブジェクト参照経由で漏れる」物理サイド
    チャネルは原理的に発生しない。
  - 通信契約 (term の **型**) は `%KojikiLM.L3ToL5Payload{}` / `%KojikiLM.L5ToL3Verdict{}`
    struct で表現。送信側で `KojikiLM.L3ToL5Payload.new!/3` を通すことで `is_binary/1` 等の
    guard が走り、`Nx.Tensor` 等は構造的に弾かれる。

  ## 公開 API

      {:ok, server} = KojikiLM.YomotsuHirasaka.start_link(evaluator: evaluator_pid)
      verdict = KojikiLM.YomotsuHirasaka.send(server, payload)

  evaluator は以下のいずれか:

  - `pid`: 別 GenServer。本 module は `GenServer.call(evaluator, {:evaluate, payload})` を行う。
  - `(L3ToL5Payload.t() -> L5ToL3Verdict.t())` 1-arg 関数: 単体テストでの簡便用途。
    同一プロセス内で実行されるため、production では別 GenServer 版を使うこと。
  """

  use GenServer

  # send/2 を Kernel.send/2 (プロセスへのメッセージ送信) と衝突させない。
  # 外部呼び出しは KojikiLM.YomotsuHirasaka.send/2 で完全修飾されているので、内部で
  # Kernel.send を使わない限り問題は起きないが、import 警告を抑止しておく。
  import Kernel, except: [send: 2]

  alias KojikiLM.{L3ToL5Payload, L5ToL3Verdict}

  @type evaluator :: pid() | (L3ToL5Payload.t() -> L5ToL3Verdict.t())

  # ---------------- Public API ----------------

  @spec start_link(keyword()) :: GenServer.on_start()
  def start_link(opts) do
    {gen_opts, init_opts} = Keyword.split(opts, [:name])
    GenServer.start_link(__MODULE__, init_opts, gen_opts)
  end

  @doc """
  L3 → L5 にペイロードを送り、verdict を受け取る。

  - 第二引数が `%L3ToL5Payload{}` でなければ `ArgumentError` を raise (FunctionClauseError と
    同じ guard 層で弾かれるよう pattern match)。
  - evaluator の返り値が `%L5ToL3Verdict{}` でなければ `ArgumentError` を raise。
  """
  @spec send(GenServer.server(), L3ToL5Payload.t()) :: L5ToL3Verdict.t()
  def send(server, %L3ToL5Payload{} = payload) do
    case GenServer.call(server, {:send, payload}) do
      %L5ToL3Verdict{} = v ->
        v

      other ->
        raise ArgumentError,
              "Evaluator must return %L5ToL3Verdict{}, got #{inspect(other)}. " <>
                "L5 → L3 で許可されているのは {verdict, v_score} のみ。"
    end
  end

  def send(_server, payload) do
    raise ArgumentError,
          "YomotsuHirasaka.send requires %L3ToL5Payload{}, got #{inspect(payload)}. " <>
            "L3 → L5 は struct 経由のみ。"
  end

  # ---------------- GenServer callbacks ----------------

  @impl true
  def init(opts) do
    case Keyword.fetch(opts, :evaluator) do
      {:ok, pid} when is_pid(pid) ->
        {:ok, %{evaluator: {:pid, pid}}}

      {:ok, fun} when is_function(fun, 1) ->
        {:ok, %{evaluator: {:fun, fun}}}

      {:ok, other} ->
        {:stop,
         {:bad_evaluator,
          "evaluator must be pid or 1-arg function, got #{inspect(other)}"}}

      :error ->
        {:stop, {:bad_evaluator, "evaluator option is required"}}
    end
  end

  @impl true
  def handle_call({:send, %L3ToL5Payload{} = payload}, _from, %{evaluator: ev} = state) do
    result =
      case ev do
        {:pid, pid} -> GenServer.call(pid, {:evaluate, payload})
        {:fun, fun} -> fun.(payload)
      end

    {:reply, result, state}
  end
end
