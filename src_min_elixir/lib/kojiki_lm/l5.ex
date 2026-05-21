defmodule KojikiLM.L5 do
  @moduledoc """
  黄泉 (L5, 評価器) GenServer。

  葦原 (L3) から `%KojikiLM.L3ToL5Payload{}` を受け取り、`%KojikiLM.L5ToL3Verdict{}` を返す。
  YomotsuHirasaka の evaluator PID として注入されることで、BEAM プロセス境界 = Firewall
  物理層が成立する。

  ## 評価フロー

      1. text == ""                           → :halt   v_score = 0.0
      2. Code.string_to_quoted/1
         a. {:error, "missing terminator"}    → :repair v_score = 0.4   (生成途中)
         b. {:error, その他}                  → :halt   v_score = 0.1   (壊れている)
         c. {:ok, _ast}
            i.  tests for prompt_id 有        → System.cmd("elixir", [tmp.exs]) で実行
                                                exit/stderr を classify_subprocess/1 で判定
            ii. tests 無                      → ヒューリスティック (Elixir キーワード/危険語/括弧)

  ## tests_by_prompt_id の所有

  各サンプルの ExUnit テスト文字列は **L5 が保持**し、L3 には絶対に渡さない (Firewall
  隔離契約)。`start_link(tests_by_prompt_id: %{...})` で init 時に注入する。

  ## 注意: BEAM 内で Code.eval_string を呼ばない

  L5 の評価器プロセス内で `Code.eval_string/3` を直接実行すると、評価対象の AST が
  この BEAM ノードの code server にロードされる可能性があり、Firewall の主張が弱まる
  (L3 が同 node にあれば、`Code.fetch_docs/2` 等で間接的に内容を伺える)。
  そのため **必ず別 OS プロセス (`System.cmd("elixir", ...)`) を経由** する。
  """

  use GenServer

  alias KojikiLM.{L3ToL5Payload, L5ToL3Verdict}

  @default_timeout_ms 5_000
  @default_commit_threshold 0.7
  @default_halt_threshold 0.3

  # subprocess の OS 側強制終了に使う。GNU coreutils 想定 (Linux)。
  @timeout_bin "timeout"

  @elixir_good_keywords [
    "defmodule ",
    "defstruct ",
    "def ",
    "defp ",
    "defmacro ",
    "defguard ",
    "do:",
    " do\n",
    " do\r",
    "fn ",
    "fn(",
    "when ",
    "|>",
    "case ",
    "cond do",
    "with ",
    "@spec ",
    "@moduledoc ",
    "@type ",
    "@callback ",
    ":ok",
    ":error",
    "is_binary(",
    "is_atom(",
    "is_list(",
    "is_map(",
    "is_integer(",
    "is_number(",
    "Enum.",
    "String.",
    "Map.",
    "List.",
    "Keyword.",
    "Stream."
  ]

  @elixir_bad_patterns [
    "# TODO",
    "# FIXME",
    "# XXX",
    "raise \"not implemented",
    "raise \"TODO",
    "raise \"unimplemented",
    "raise \"todo"
  ]

  # ---------------- Public API ----------------

  @spec start_link(keyword()) :: GenServer.on_start()
  def start_link(opts \\ []) do
    {gen_opts, init_opts} = Keyword.split(opts, [:name])
    GenServer.start_link(__MODULE__, init_opts, gen_opts)
  end

  @doc """
  本 module を GenServer を介さず直接呼ぶ用のヘルパ (主にテスト/デバッグ用途)。
  production では evaluator PID として YomotsuHirasaka に渡し、BEAM 境界経由で呼ぶこと。
  """
  @spec evaluate(L3ToL5Payload.t(), keyword()) :: L5ToL3Verdict.t()
  def evaluate(%L3ToL5Payload{} = payload, opts \\ []) do
    do_evaluate(payload, build_state(opts))
  end

  # ---------------- GenServer callbacks ----------------

  @impl true
  def init(opts), do: {:ok, build_state(opts)}

  @impl true
  def handle_call({:evaluate, %L3ToL5Payload{} = payload}, _from, state) do
    {:reply, do_evaluate(payload, state), state}
  end

  # ---------------- Internal ----------------

  defp build_state(opts) do
    %{
      tests_by_prompt_id: Keyword.get(opts, :tests_by_prompt_id, %{}),
      timeout_ms: Keyword.get(opts, :timeout_ms, @default_timeout_ms),
      elixir_bin: Keyword.get(opts, :elixir_bin, "elixir"),
      timeout_bin: Keyword.get(opts, :timeout_bin, @timeout_bin),
      commit_threshold: Keyword.get(opts, :commit_threshold, @default_commit_threshold),
      halt_threshold: Keyword.get(opts, :halt_threshold, @default_halt_threshold)
    }
  end

  defp do_evaluate(%L3ToL5Payload{text: ""}, _state) do
    L5ToL3Verdict.new!(:halt, 0.0)
  end

  defp do_evaluate(%L3ToL5Payload{text: text, prompt_id: prompt_id}, state) do
    case parse_status(text) do
      :incomplete ->
        L5ToL3Verdict.new!(:repair, 0.4)

      :broken ->
        L5ToL3Verdict.new!(:halt, 0.1)

      :ok ->
        case Map.fetch(state.tests_by_prompt_id, prompt_id) do
          {:ok, tests} when is_binary(tests) and tests != "" ->
            run_subprocess(text, tests, state)

          _ ->
            heuristic_verdict(text, state)
        end
    end
  end

  # ---- 構文 status ----

  defp parse_status(text) do
    case Code.string_to_quoted(text) do
      {:ok, _ast} ->
        :ok

      {:error, {_meta, payload, _token}} ->
        if incomplete?(error_message(payload)), do: :incomplete, else: :broken

      {:error, _} ->
        :broken
    end
  rescue
    # 古い Elixir / 異常系で raise されるケースは broken 扱い。
    _ -> :broken
  end

  defp error_message(msg) when is_binary(msg), do: msg
  defp error_message({prefix, suffix}) when is_binary(prefix), do: prefix <> to_string(suffix)
  defp error_message(other), do: inspect(other)

  defp incomplete?(msg) when is_binary(msg) do
    String.contains?(msg, "missing terminator") or
      String.contains?(msg, "expecting end-of") or
      String.contains?(msg, "missing interpolation") or
      String.contains?(msg, "incomplete")
  end

  defp incomplete?(_), do: false

  # ---- subprocess 評価 ----

  defp run_subprocess(text, tests, state) do
    full_source = text <> "\n\n" <> tests <> "\n"

    tmp_path =
      Path.join(System.tmp_dir!(), "kojiki_l5_#{System.unique_integer([:positive])}.exs")

    File.write!(tmp_path, full_source)

    try do
      result = exec_elixir(tmp_path, state)
      classify_subprocess(result)
    after
      File.rm(tmp_path)
    end
  end

  # `timeout` (GNU coreutils) があれば OS レベルの強制終了付きで実行。
  # 無ければ素の `elixir` だけで実行 (hang リスク有)。
  defp exec_elixir(path, %{elixir_bin: ebin, timeout_bin: tbin, timeout_ms: ms}) do
    timeout_sec = ms |> div(1000) |> max(1) |> Integer.to_string()

    case System.find_executable(tbin) do
      nil ->
        try do
          System.cmd(ebin, [path], stderr_to_stdout: true)
        rescue
          e in ErlangError -> {Exception.message(e), 127}
        end

      _path ->
        try do
          System.cmd(tbin, [timeout_sec, ebin, path], stderr_to_stdout: true)
        rescue
          e in ErlangError -> {Exception.message(e), 127}
        end
    end
  end

  defp classify_subprocess({_output, 0}), do: L5ToL3Verdict.new!(:commit, 1.0)
  # GNU `timeout` は SIGTERM 殺害時に exit code 124
  defp classify_subprocess({_output, 124}), do: L5ToL3Verdict.new!(:halt, 0.1)
  defp classify_subprocess({_output, 137}), do: L5ToL3Verdict.new!(:halt, 0.1)

  defp classify_subprocess({output, _code}) do
    cond do
      assertion_failure?(output) ->
        L5ToL3Verdict.new!(:halt, 0.2)

      compile_or_syntax_failure?(output) ->
        L5ToL3Verdict.new!(:repair, 0.4)

      undefined_or_arity_failure?(output) ->
        L5ToL3Verdict.new!(:halt, 0.25)

      true ->
        L5ToL3Verdict.new!(:halt, 0.15)
    end
  end

  defp assertion_failure?(out) do
    String.contains?(out, "ExUnit.AssertionError") or
      String.contains?(out, "Assertion with") or
      String.contains?(out, "match (=) failed") or
      String.contains?(out, "FunctionClauseError")
  end

  defp compile_or_syntax_failure?(out) do
    String.contains?(out, "TokenMissingError") or
      String.contains?(out, "SyntaxError") or
      String.contains?(out, "** (CompileError)") or
      String.contains?(out, "missing terminator") or
      String.contains?(out, "syntax error")
  end

  defp undefined_or_arity_failure?(out) do
    String.contains?(out, "undefined function") or
      String.contains?(out, "is undefined") or
      String.contains?(out, "UndefinedFunctionError") or
      String.contains?(out, "function ") and String.contains?(out, "is undefined or private")
  end

  # ---- ヒューリスティック (tests 未付与時) ----

  defp heuristic_verdict(text, state) do
    score = heuristic_score(text)
    {verdict, _} = decide(score, state)
    L5ToL3Verdict.new!(verdict, score)
  end

  defp heuristic_score(text) do
    base = if byte_size(text) < 5, do: 0.1, else: 0.5
    good = Enum.count(@elixir_good_keywords, &String.contains?(text, &1))
    bad = Enum.count(@elixir_bad_patterns, &String.contains?(text, &1))
    bracket_pen = if brackets_balanced?(text), do: 0.0, else: 0.2

    (base + good * 0.05 - bad * 0.1 - bracket_pen)
    |> max(0.0)
    |> min(1.0)
  end

  defp decide(score, state) do
    cond do
      score >= state.commit_threshold -> {:commit, score}
      score < state.halt_threshold -> {:halt, score}
      true -> {:repair, score}
    end
  end

  defp brackets_balanced?(text) do
    text
    |> String.to_charlist()
    |> Enum.reduce_while([], fn
      ?(, acc -> {:cont, [?( | acc]}
      ?[, acc -> {:cont, [?[ | acc]}
      ?{, acc -> {:cont, [?{ | acc]}
      ?), [?( | rest] -> {:cont, rest}
      ?], [?[ | rest] -> {:cont, rest}
      ?}, [?{ | rest] -> {:cont, rest}
      ?), _ -> {:halt, :bad}
      ?], _ -> {:halt, :bad}
      ?}, _ -> {:halt, :bad}
      _, acc -> {:cont, acc}
    end)
    |> case do
      :bad -> false
      [] -> true
      _ -> false
    end
  end
end
