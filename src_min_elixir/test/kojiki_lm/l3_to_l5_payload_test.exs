defmodule KojikiLM.L3ToL5PayloadTest do
  use ExUnit.Case, async: true

  alias KojikiLM.L3ToL5Payload

  describe "new!/3 — happy path" do
    test "builds a struct with valid fields" do
      p = L3ToL5Payload.new!("hello", 1, "p1")
      assert %L3ToL5Payload{text: "hello", step_idx: 1, prompt_id: "p1"} = p
    end

    test "accepts empty string for text" do
      p = L3ToL5Payload.new!("", 0, "p1")
      assert p.text == ""
    end
  end

  describe "new!/3 — text validation" do
    test "rejects non-binary text (list — Nx.Tensor data 相当)" do
      assert_raise ArgumentError, ~r/must be binary/, fn ->
        L3ToL5Payload.new!([0.1, 0.2, 0.3], 1, "p1")
      end
    end

    test "rejects map text (hidden_state dict 相当)" do
      assert_raise ArgumentError, ~r/must be binary/, fn ->
        L3ToL5Payload.new!(%{hidden_state: 1}, 1, "p1")
      end
    end

    test "rejects integer text" do
      assert_raise ArgumentError, ~r/must be binary/, fn ->
        L3ToL5Payload.new!(42, 1, "p1")
      end
    end

    test "rejects atom text" do
      assert_raise ArgumentError, ~r/must be binary/, fn ->
        L3ToL5Payload.new!(:not_a_string, 1, "p1")
      end
    end
  end

  describe "new!/3 — step_idx validation" do
    test "rejects non-integer step_idx" do
      assert_raise ArgumentError, ~r/must be integer/, fn ->
        L3ToL5Payload.new!("x", "1", "p1")
      end
    end

    test "rejects float step_idx" do
      assert_raise ArgumentError, ~r/must be integer/, fn ->
        L3ToL5Payload.new!("x", 1.0, "p1")
      end
    end

    test "rejects negative step_idx" do
      assert_raise ArgumentError, ~r/must be >= 0/, fn ->
        L3ToL5Payload.new!("x", -1, "p1")
      end
    end

    test "accepts zero step_idx" do
      assert L3ToL5Payload.new!("x", 0, "p1").step_idx == 0
    end
  end

  describe "new!/3 — prompt_id validation" do
    test "rejects atom prompt_id" do
      assert_raise ArgumentError, ~r/prompt_id must be binary/, fn ->
        L3ToL5Payload.new!("x", 0, :p1)
      end
    end

    test "rejects integer prompt_id" do
      assert_raise ArgumentError, ~r/prompt_id must be binary/, fn ->
        L3ToL5Payload.new!("x", 0, 1)
      end
    end
  end

  describe "struct immutability (frozen equivalent)" do
    test "BEAM 上で struct は値であって参照ではない" do
      p1 = L3ToL5Payload.new!("a", 0, "p1")
      p2 = %L3ToL5Payload{p1 | text: "b"}
      # 新しい struct が返るだけで、p1 の text は変わらない
      assert p1.text == "a"
      assert p2.text == "b"
    end
  end
end
