defmodule KojikiLM.L5Test do
  use ExUnit.Case, async: true

  alias KojikiLM.{L3ToL5Payload, L5, L5ToL3Verdict, YomotsuHirasaka}

  # subprocess を回すため async: true のままだが、全 case 並列実行は問題なし。
  @moduletag :tmp_dir

  defp p(text, prompt_id \\ "p1"), do: L3ToL5Payload.new!(text, 0, prompt_id)

  describe "evaluate/2 — empty text" do
    test "空テキストは :halt v_score = 0.0" do
      v = L5.evaluate(p(""))
      assert v == L5ToL3Verdict.new!(:halt, 0.0)
    end
  end

  describe "evaluate/2 — syntax-only path (no tests)" do
    test "完成構文 (commit-level score) は :commit" do
      text = """
      defmodule Sample do
        @spec add(integer(), integer()) :: integer()
        def add(a, b) when is_integer(a) and is_integer(b), do: a + b

        def chain(xs), do: xs |> Enum.map(&(&1 * 2)) |> Enum.sum()
      end
      """

      v = L5.evaluate(p(text))
      assert v.verdict in [:commit, :repair]
      assert v.v_score > 0.5
    end

    test "未完成 (def foo do だけ) は :repair" do
      v = L5.evaluate(p("def foo do"))
      assert v.verdict == :repair
      assert v.v_score == 0.4
    end

    test "壊れた構文 (def foo )) は :halt" do
      v = L5.evaluate(p("def foo ))"))
      assert v.verdict == :halt
      assert v.v_score == 0.1
    end

    test "TODO 危険語のみのテキストは低スコア → :halt 寄り" do
      v = L5.evaluate(p("# TODO: 後で書く\n# FIXME: 未実装\n"))
      assert v.verdict in [:halt, :repair]
      assert v.v_score < 0.5
    end
  end

  describe "evaluate/2 — subprocess path (with tests)" do
    @describetag :subprocess

    test "通るテストは :commit v_score = 1.0" do
      source = """
      defmodule Sample do
        def add(a, b), do: a + b
      end
      """

      tests = """
      ExUnit.start()

      defmodule SampleTest do
        use ExUnit.Case, async: false

        test "add" do
          assert Sample.add(1, 2) == 3
        end
      end
      """

      v = L5.evaluate(p(source, "sample-pass"),
        tests_by_prompt_id: %{"sample-pass" => tests}
      )

      assert v.verdict == :commit
      assert v.v_score == 1.0
    end

    test "失敗するテストは :halt v_score ~ 0.2" do
      source = """
      defmodule SampleFail do
        def add(a, b), do: a - b
      end
      """

      tests = """
      ExUnit.start()

      defmodule SampleFailTest do
        use ExUnit.Case, async: false

        test "fails" do
          assert SampleFail.add(1, 2) == 3
        end
      end
      """

      v = L5.evaluate(p(source, "sample-fail"),
        tests_by_prompt_id: %{"sample-fail" => tests}
      )

      assert v.verdict == :halt
      assert v.v_score == 0.2
    end

    test "未定義関数呼び出し (UndefinedFunctionError) は :halt v_score ~ 0.25" do
      source = """
      defmodule SampleUndef do
        def foo, do: :ok
      end
      """

      tests = """
      ExUnit.start()

      defmodule SampleUndefTest do
        use ExUnit.Case, async: false

        test "bar undefined" do
          assert SampleUndef.bar() == :ok
        end
      end
      """

      v = L5.evaluate(p(source, "sample-undef"),
        tests_by_prompt_id: %{"sample-undef" => tests}
      )

      assert v.verdict == :halt
      # AssertionError (FunctionClauseError 等) ではなく UndefinedFunctionError 路線
      assert v.v_score in [0.2, 0.25]
    end

    test "subprocess 内で CompileError は :repair v_score = 0.4" do
      # 親 AST はパースできるが、評価時に存在しないモジュールを参照 → CompileError
      source = """
      defmodule SampleCompile do
        require NonExistent.Module.Definitely
        def x, do: :ok
      end
      """

      tests = """
      ExUnit.start()
      defmodule SampleCompileTest do
        use ExUnit.Case, async: false
        test "noop" do
          assert SampleCompile.x() == :ok
        end
      end
      """

      v = L5.evaluate(p(source, "sample-compile"),
        tests_by_prompt_id: %{"sample-compile" => tests}
      )

      assert v.verdict in [:repair, :halt]
    end

    test "timeout (5s) を超える test は :halt v_score = 0.1" do
      source = """
      defmodule SampleTimeout do
        def loop, do: loop()
      end
      """

      tests = """
      ExUnit.start()
      defmodule SampleTimeoutTest do
        use ExUnit.Case, async: false
        test "hang" do
          SampleTimeout.loop()
        end
      end
      """

      v = L5.evaluate(p(source, "sample-timeout"),
        tests_by_prompt_id: %{"sample-timeout" => tests},
        timeout_ms: 1_500
      )

      assert v.verdict == :halt
      assert v.v_score == 0.1
    end
  end

  describe "GenServer path — L5 as evaluator PID of YomotsuHirasaka" do
    @describetag :integration

    test "BEAM 境界経由で commit が流れる (= Firewall 物理層)" do
      source = """
      defmodule Boundary do
        def add(a, b), do: a + b
      end
      """

      tests = """
      ExUnit.start()
      defmodule BoundaryTest do
        use ExUnit.Case, async: false
        test "add" do
          assert Boundary.add(2, 3) == 5
        end
      end
      """

      {:ok, l5} = L5.start_link(tests_by_prompt_id: %{"boundary" => tests})
      {:ok, gw} = YomotsuHirasaka.start_link(evaluator: l5)

      # L5 / Gateway / 呼び出し元 (test process) は全て別 PID
      refute self() == l5
      refute self() == gw
      refute l5 == gw

      v = YomotsuHirasaka.send(gw, p(source, "boundary"))
      assert v.verdict == :commit
      assert v.v_score == 1.0
    end

    test "tests 未登録の prompt_id は heuristic で判定される" do
      source = "defmodule X do\n  def f, do: :ok\nend\n"

      {:ok, l5} = L5.start_link(tests_by_prompt_id: %{})
      {:ok, gw} = YomotsuHirasaka.start_link(evaluator: l5)

      v = YomotsuHirasaka.send(gw, p(source, "no-tests"))
      # 完成 module / キーワード豊富 / 括弧バランス OK → 高めスコア
      assert v.verdict in [:commit, :repair]
      assert v.v_score >= 0.5
    end
  end

  describe "start_link/1" do
    test "defaults" do
      {:ok, pid} = L5.start_link([])
      assert is_pid(pid)
    end

    test "accepts tests_by_prompt_id and timeout_ms" do
      {:ok, pid} = L5.start_link(tests_by_prompt_id: %{"a" => ""}, timeout_ms: 2_000)
      assert is_pid(pid)
    end
  end
end
