defmodule KojikiLM.MechanicalRepair do
  @moduledoc """
  機械的 REPAIR — L5 内部の決定論的 text → text 変換。

  L3 (生成 LM) を呼び戻さずに L5 が壊れたコードを修復する層。Go 版の
  `goimports_repair` ([../../../src_min_go/kojiki_lm/mechanical_repair.py]) と
  同じ Firewall 隔離契約:

  - 入力 = prompt + completion 文字列のみ (tests は含めない、Goodhart 回避)
  - 出力 = 修復後文字列
  - L3 は修復後 text を**見ない** → L5 → L3 経路は使わない
  - LLM は呼ばない、決定論的処理のみ

  ## ツール段階 (現状 2 種)

  1. **`Code.format_string!/2`** — `mix format` 相当の整形。Elixir 公式 formatter。
  2. **"did you mean" hint 抽出** — `Code.string_to_quoted/2` のエラーから
     `did you mean: foo, bar` を機械パース。`hints` フィールドに格納するだけで自動
     適用はしない (未宣言識別子の自動置換は危険なため、エラー位置 + 候補のみ返す)。

  Go の `goimports` 単機能と比べると surface area が広い (formatter + hint parser +
  将来の AST 変形が同 module に同居)。
  """

  alias __MODULE__.Result

  defmodule Result do
    @moduledoc """
    機械的修復の結果。元 text と修復後 text を返す。
    """

    @enforce_keys [:text, :applied, :tool]
    defstruct [:text, :applied, :tool, hints: [], stderr: ""]

    @type t :: %__MODULE__{
            text: String.t(),
            applied: boolean(),
            tool: String.t(),
            hints: [String.t()],
            stderr: String.t()
          }
  end

  @doc """
  text に対して順番に修復段階を適用する。各段階は失敗しても元 text を返すので、
  チェーン全体は壊れない。

  ## opts

    * `:tools` — 適用するツールの順序。デフォルト `[:format, :hint]`
    * `:formatter_opts` — `Code.format_string!/2` に渡すオプション
  """
  @spec repair(String.t(), keyword()) :: Result.t()
  def repair(text, opts \\ []) when is_binary(text) do
    tools = Keyword.get(opts, :tools, [:format, :hint])
    initial = %Result{text: text, applied: false, tool: "noop"}

    Enum.reduce(tools, initial, fn tool, acc ->
      apply_tool(tool, acc, opts)
    end)
  end

  @doc """
  `Code.format_string!/2` だけを単発で適用する薄ラッパー。テスト用。
  """
  @spec format_only(String.t(), keyword()) :: Result.t()
  def format_only(text, opts \\ []) when is_binary(text) do
    apply_tool(:format, %Result{text: text, applied: false, tool: "noop"}, opts)
  end

  @doc """
  `Code.string_to_quoted/2` の error から "did you mean: ..." hint だけを抽出する。
  text 自体は変更しない。
  """
  @spec hint_only(String.t()) :: Result.t()
  def hint_only(text) when is_binary(text) do
    apply_tool(:hint, %Result{text: text, applied: false, tool: "noop"}, [])
  end

  # ---------------- internal: tool dispatch ----------------

  defp apply_tool(:format, %Result{text: text} = acc, opts) do
    fmt_opts = Keyword.get(opts, :formatter_opts, [])

    try do
      formatted = text |> Code.format_string!(fmt_opts) |> IO.iodata_to_binary()
      formatted_eof = ensure_trailing_newline(formatted)
      changed = formatted_eof != text

      %Result{
        text: formatted_eof,
        applied: acc.applied or changed,
        tool: merge_tool(acc.tool, if(changed, do: "format", else: nil)),
        hints: acc.hints,
        stderr: acc.stderr
      }
    rescue
      e ->
        # formatter は壊れた構文では raise する。元 text を返して次段階へ。
        %Result{
          acc
          | stderr: acc.stderr <> "format: " <> Exception.message(e) <> "\n"
        }
    end
  end

  defp apply_tool(:hint, %Result{text: text} = acc, _opts) do
    hints =
      case Code.string_to_quoted(text, emit_warnings: false) do
        {:ok, _ast} ->
          []

        {:error, {meta, payload, _token}} ->
          extract_hints(payload, meta)

        {:error, _} ->
          []
      end

    %Result{acc | hints: acc.hints ++ hints}
  end

  defp apply_tool(other, acc, _opts) do
    %Result{
      acc
      | stderr: acc.stderr <> "unknown tool: #{inspect(other)}\n"
    }
  end

  # ---------------- internal: helpers ----------------

  defp ensure_trailing_newline(s) do
    if String.ends_with?(s, "\n"), do: s, else: s <> "\n"
  end

  defp merge_tool(prev, nil), do: prev
  defp merge_tool("noop", t), do: t
  defp merge_tool(prev, t), do: prev <> "+" <> t

  # `Code.string_to_quoted` の error payload は版差があるので柔軟に拾う。
  # 想定形:
  #   - {meta, "syntax error before: ", "foo"}
  #   - {meta, {"prefix", "suffix"}, "foo"}
  defp extract_hints(payload, meta) when is_tuple(payload) and tuple_size(payload) == 2 do
    {prefix, suffix} = payload
    full = to_string(prefix) <> to_string(suffix)
    parse_did_you_mean(full, meta)
  end

  defp extract_hints(payload, meta) when is_binary(payload) do
    parse_did_you_mean(payload, meta)
  end

  defp extract_hints(_payload, _meta), do: []

  defp parse_did_you_mean(msg, meta) do
    case Regex.run(~r/did you mean[:?]?\s*([A-Za-z0-9_\.\,\s\/]+?)(?:\?|\.|$)/i, msg) do
      [_, suggestions] ->
        loc = format_location(meta)

        suggestions
        |> String.split([","])
        |> Enum.map(&String.trim/1)
        |> Enum.reject(&(&1 == ""))
        |> Enum.map(&"#{loc}did you mean: #{&1}")

      _ ->
        []
    end
  end

  defp format_location(meta) when is_list(meta) do
    line = Keyword.get(meta, :line)
    col = Keyword.get(meta, :column)

    cond do
      line && col -> "L#{line}:C#{col} "
      line -> "L#{line} "
      true -> ""
    end
  end

  defp format_location(_), do: ""
end
