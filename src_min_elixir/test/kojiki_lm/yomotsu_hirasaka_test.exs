defmodule KojikiLM.YomotsuHirasakaTest do
  use ExUnit.Case, async: true

  alias KojikiLM.{L3ToL5Payload, L5ToL3Verdict, TestEvaluator, YomotsuHirasaka}

  describe "send/2 with inline function evaluator" do
    setup do
      fun = fn %L3ToL5Payload{} -> L5ToL3Verdict.new!(:commit, 0.9) end
      {:ok, gw} = YomotsuHirasaka.start_link(evaluator: fun)
      %{gw: gw}
    end

    test "returns evaluator verdict on valid payload", %{gw: gw} do
      payload = L3ToL5Payload.new!("ok", 0, "p1")
      verdict = YomotsuHirasaka.send(gw, payload)
      assert %L5ToL3Verdict{verdict: :commit, v_score: 0.9} = verdict
    end

    test "raises ArgumentError when payload is not %L3ToL5Payload{}", %{gw: gw} do
      assert_raise ArgumentError, ~r/requires %L3ToL5Payload\{\}/, fn ->
        YomotsuHirasaka.send(gw, "just a string")
      end
    end

    test "raises ArgumentError when payload is a bare map", %{gw: gw} do
      assert_raise ArgumentError, ~r/requires %L3ToL5Payload\{\}/, fn ->
        YomotsuHirasaka.send(gw, %{text: "x", step_idx: 0, prompt_id: "p1"})
      end
    end
  end

  describe "send/2 with bad evaluator return type" do
    test "raises when evaluator returns a non-Verdict map" do
      fun = fn _ -> %{verdict: :commit, v_score: 0.9} end
      {:ok, gw} = YomotsuHirasaka.start_link(evaluator: fun)

      assert_raise ArgumentError, ~r/must return %L5ToL3Verdict\{\}/, fn ->
        YomotsuHirasaka.send(gw, L3ToL5Payload.new!("ok", 0, "p1"))
      end
    end

    test "raises when evaluator returns plain string" do
      fun = fn _ -> "commit" end
      {:ok, gw} = YomotsuHirasaka.start_link(evaluator: fun)

      assert_raise ArgumentError, ~r/must return %L5ToL3Verdict\{\}/, fn ->
        YomotsuHirasaka.send(gw, L3ToL5Payload.new!("ok", 0, "p1"))
      end
    end
  end

  describe "start_link/1 evaluator option" do
    test "rejects missing evaluator option" do
      Process.flag(:trap_exit, true)
      assert {:error, {:bad_evaluator, _}} = YomotsuHirasaka.start_link([])
    end

    test "rejects non-pid non-function evaluator" do
      Process.flag(:trap_exit, true)
      assert {:error, {:bad_evaluator, _}} = YomotsuHirasaka.start_link(evaluator: "not callable")
    end

    test "accepts function/1 evaluator" do
      fun = fn _ -> L5ToL3Verdict.new!(:commit, 1.0) end
      assert {:ok, _} = YomotsuHirasaka.start_link(evaluator: fun)
    end
  end

  describe "BEAM process boundary (Firewall 物理層)" do
    setup do
      # evaluator は別 GenServer = 別 PID = 別 heap
      fun = fn %L3ToL5Payload{} -> L5ToL3Verdict.new!(:commit, 0.7) end
      {:ok, eval_pid} = TestEvaluator.start_link(fun: fun)
      {:ok, gw} = YomotsuHirasaka.start_link(evaluator: eval_pid)

      %{eval_pid: eval_pid, gw: gw}
    end

    test "evaluator runs in a different PID than the gateway", %{eval_pid: eval_pid, gw: gw} do
      assert is_pid(eval_pid)
      assert is_pid(gw)
      refute eval_pid == gw
    end

    test "verdict flows through message passing (term copy, not shared reference)",
         %{eval_pid: eval_pid, gw: gw} do
      payload = L3ToL5Payload.new!("hello", 3, "p42")
      verdict = YomotsuHirasaka.send(gw, payload)

      assert %L5ToL3Verdict{verdict: :commit, v_score: 0.7} = verdict
      # evaluator が実際に受け取ったときの caller が YomotsuHirasaka の PID であることを確認
      # (= 直接 caller の PID は流れていない、GenServer.call を経由している)
      assert TestEvaluator.last_caller_pid(eval_pid) == gw
    end
  end

  describe "Firewall 隔離契約 — Python 版テストの port" do
    # Python: test_firewall_go.py の TestYomotsuHirasaka 3 ケースに対応

    test "send returns verdict (test_send_returns_verdict 相当)" do
      fun = fn _ -> L5ToL3Verdict.new!(:commit, 0.9) end
      {:ok, gw} = YomotsuHirasaka.start_link(evaluator: fun)
      payload = L3ToL5Payload.new!("ok", 0, "p1")
      assert YomotsuHirasaka.send(gw, payload).verdict == :commit
    end

    test "rejects non-payload (test_send_rejects_non_payload 相当)" do
      fun = fn _ -> L5ToL3Verdict.new!(:commit, 0.9) end
      {:ok, gw} = YomotsuHirasaka.start_link(evaluator: fun)

      assert_raise ArgumentError, ~r/requires %L3ToL5Payload\{\}/, fn ->
        YomotsuHirasaka.send(gw, "just a string")
      end
    end

    test "rejects evaluator returning wrong type (test_send_rejects_evaluator_returning_wrong_type 相当)" do
      fun = fn _ -> %{verdict: "commit", v_score: 0.9} end
      {:ok, gw} = YomotsuHirasaka.start_link(evaluator: fun)

      assert_raise ArgumentError, ~r/must return %L5ToL3Verdict\{\}/, fn ->
        YomotsuHirasaka.send(gw, L3ToL5Payload.new!("ok", 0, "p1"))
      end
    end
  end
end
