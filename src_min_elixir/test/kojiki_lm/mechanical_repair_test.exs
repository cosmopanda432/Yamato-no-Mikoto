defmodule KojikiLM.MechanicalRepairTest do
  use ExUnit.Case, async: true

  alias KojikiLM.MechanicalRepair
  alias KojikiLM.MechanicalRepair.Result

  describe "format_only/2" do
    test "整形済テキストは applied=false" do
      text = "defmodule Foo do\n  def bar, do: 1\nend\n"
      r = MechanicalRepair.format_only(text)
      assert %Result{text: ^text, applied: false} = r
    end

    test "ぐちゃぐちゃのスペースを mix format 相当で正規化する" do
      text = "defmodule Foo do\n  def  bar  ,  do:    1\nend"
      r = MechanicalRepair.format_only(text)

      assert r.applied
      assert r.tool == "format"
      assert String.contains?(r.text, "def bar, do: 1")
      assert String.ends_with?(r.text, "\n")
    end

    test "壊れた構文は元 text を返し stderr に記録 (applied=false)" do
      text = "def foo )"
      r = MechanicalRepair.format_only(text)

      assert r.text == text
      refute r.applied
      assert r.stderr =~ "format:"
    end
  end

  describe "hint_only/1" do
    test "正常な構文では hints が空" do
      r = MechanicalRepair.hint_only("defmodule X do\n  def y, do: 1\nend\n")
      assert r.hints == []
    end

    test "壊れた構文では空 hints (did you mean 形式でなければ)" do
      r = MechanicalRepair.hint_only("def foo )")
      # syntax error before は did you mean 形式ではないので hints は空
      assert r.hints == []
    end
  end

  describe "repair/2 — chain" do
    test "format + hint を順に走らせる" do
      text = "defmodule X do\n   def  y , do:   1\nend"
      r = MechanicalRepair.repair(text)

      assert r.applied
      assert String.contains?(r.text, "def y, do: 1")
      assert is_list(r.hints)
    end

    test "壊れた構文でも例外を投げず元 text を返す" do
      text = "def foo )"
      r = MechanicalRepair.repair(text)

      assert r.text == text
      refute r.applied
      assert r.stderr =~ "format:"
    end

    test ":tools オプションで段階をスキップできる" do
      text = "defmodule X do\n   def  y , do:   1\nend"
      r = MechanicalRepair.repair(text, tools: [:hint])

      # hint だけなので applied は false (text は変えない)
      refute r.applied
      assert r.text == text
    end
  end

  describe "Firewall 隔離契約 — repair は text → text のみ" do
    test "tests / verdict 等の外部状態を入力に取らない" do
      # signature 確認 (compile time): repair(binary, keyword) -> Result
      text = "defmodule Sample do\n  def add(a, b), do: a + b\nend\n"
      r = MechanicalRepair.repair(text)
      assert %Result{} = r
      # tests を渡す経路が無いことを arity で保証
      refute function_exported?(MechanicalRepair, :repair, 3)
    end
  end
end
