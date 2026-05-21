defmodule KojikiLM.VerdictTest do
  use ExUnit.Case, async: true

  require KojikiLM.Verdict
  alias KojikiLM.Verdict

  describe "valid?/1" do
    test "accepts the three canonical verdicts" do
      assert Verdict.valid?(:commit)
      assert Verdict.valid?(:repair)
      assert Verdict.valid?(:halt)
    end

    test "rejects unknown atoms" do
      refute Verdict.valid?(:abort)
      refute Verdict.valid?(:ok)
      refute Verdict.valid?(nil)
    end

    test "rejects non-atom terms" do
      refute Verdict.valid?("commit")
      refute Verdict.valid?(0)
      refute Verdict.valid?(%{})
    end
  end

  describe "is_verdict/1 guard" do
    defp classify(v) when Verdict.is_verdict(v), do: :verdict
    defp classify(_), do: :other

    test "guard accepts canonical verdicts" do
      assert classify(:commit) == :verdict
      assert classify(:repair) == :verdict
      assert classify(:halt) == :verdict
    end

    test "guard rejects everything else" do
      assert classify(:abort) == :other
      assert classify("commit") == :other
      assert classify(0) == :other
    end
  end
end
