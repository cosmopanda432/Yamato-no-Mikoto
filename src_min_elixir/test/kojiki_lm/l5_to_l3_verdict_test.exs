defmodule KojikiLM.L5ToL3VerdictTest do
  use ExUnit.Case, async: true

  alias KojikiLM.L5ToL3Verdict

  describe "new!/2 — happy path" do
    test "accepts :commit / :repair / :halt with valid v_score" do
      assert %L5ToL3Verdict{verdict: :commit, v_score: 0.85} =
               L5ToL3Verdict.new!(:commit, 0.85)

      assert %L5ToL3Verdict{verdict: :repair, v_score: 0.5} =
               L5ToL3Verdict.new!(:repair, 0.5)

      assert %L5ToL3Verdict{verdict: :halt, v_score: 0.0} = L5ToL3Verdict.new!(:halt, 0.0)
    end

    test "coerces integer v_score to float" do
      v = L5ToL3Verdict.new!(:commit, 1)
      assert v.v_score === 1.0
      assert is_float(v.v_score)
    end
  end

  describe "new!/2 — verdict validation" do
    test "rejects string verdict" do
      assert_raise ArgumentError, ~r/verdict must be one of/, fn ->
        L5ToL3Verdict.new!("commit", 0.85)
      end
    end

    test "rejects unknown verdict atom" do
      assert_raise ArgumentError, ~r/verdict must be one of/, fn ->
        L5ToL3Verdict.new!(:abort, 0.85)
      end
    end

    test "rejects nil verdict" do
      assert_raise ArgumentError, ~r/verdict must be one of/, fn ->
        L5ToL3Verdict.new!(nil, 0.85)
      end
    end
  end

  describe "new!/2 — v_score validation" do
    test "rejects out-of-range v_score (above 1)" do
      assert_raise ArgumentError, ~r/\[0\.0, 1\.0\]/, fn ->
        L5ToL3Verdict.new!(:commit, 1.5)
      end
    end

    test "rejects negative v_score" do
      assert_raise ArgumentError, ~r/\[0\.0, 1\.0\]/, fn ->
        L5ToL3Verdict.new!(:commit, -0.1)
      end
    end

    test "rejects non-numeric v_score" do
      assert_raise ArgumentError, ~r/must be number/, fn ->
        L5ToL3Verdict.new!(:commit, "0.5")
      end
    end
  end
end
