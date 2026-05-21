# Step 1 smoke — Bumblebee で Qwen3-Coder-30B-A3B を load → Axon int8 量子化 → 1-prompt 生成
#
# 実行: cd src_min_elixir && mix run scripts/smoke_qwen3.exs
#
# 環境変数:
#   MODEL_DIR   モデルディレクトリ (default: /workspace/Yamato-no-Mikoto/models/Qwen3-Coder-30B-A3B-Instruct)
#   QUANTIZE    "int8" | "none" (default: int8)
#   MAX_TOKENS  生成最大 token 数 (default: 32)
#   PROMPT      生成 prompt (default: シンプルな Elixir 関数定義)
#   XLA_TARGET  EXLA backend target (cuda12 for CUDA 12.x, cpu for CPU-only)
#
# 観測点:
#   1. Bumblebee.load_model が Qwen3 系で通るか (v0.7.0 で追加されたサポート)
#   2. Axon.Quantization int8 が MoE 構造 (Qwen3-Coder-30B-A3B) に通るか — 前例なし、最大の不確定要素
#   3. VRAM 実測値が 48 GB に収まるか (理論 ~30-35 GB)
#   4. 1-prompt 生成レイテンシ (初回は JIT compile 込み)

model_path =
  System.get_env(
    "MODEL_DIR",
    "/workspace/Yamato-no-Mikoto/models/Qwen3-Coder-30B-A3B-Instruct"
  )

quantize = System.get_env("QUANTIZE", "int8")
max_tokens = System.get_env("MAX_TOKENS", "32") |> String.to_integer()

prompt =
  System.get_env(
    "PROMPT",
    """
    defmodule Math do
      @doc "Returns the factorial of n."
      def factorial(0), do: 1
      def factorial(n) when n > 0 do
    """
  )

defmodule SmokeUtil do
  def section(title) do
    IO.puts("")
    IO.puts("=== #{title} ===")
  end

  def step(label, fun) do
    t0 = System.monotonic_time(:millisecond)
    result = fun.()
    t1 = System.monotonic_time(:millisecond)
    IO.puts("[#{label}] OK (#{t1 - t0} ms)")
    {result, t1 - t0}
  end

  def gpu_memory_summary do
    case System.cmd("nvidia-smi",
           ["--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
           stderr_to_stdout: true
         ) do
      {output, 0} ->
        [used, total] =
          output |> String.trim() |> String.split(",") |> Enum.map(&String.trim/1)

        "VRAM #{used} / #{total} MiB"

      _ ->
        "(nvidia-smi unavailable)"
    end
  end
end

SmokeUtil.section("env")
IO.puts("model_path: #{model_path}")
IO.puts("quantize:   #{quantize}")
IO.puts("max_tokens: #{max_tokens}")
IO.puts("XLA_TARGET: #{System.get_env("XLA_TARGET", "(unset)")}")
IO.puts("Initial #{SmokeUtil.gpu_memory_summary()}")

# EXLA backend をデフォルトに設定
Nx.global_default_backend({EXLA.Backend, client: :cuda})
Nx.Defn.default_options(compiler: EXLA)

SmokeUtil.section("load model (bf16, host RAM 経由)")
# host RAM (1.5 TB) に bf16 で load。GPU 直接は 60GB > 48GB で OOM するため一旦 host へ。
{{:ok, model_info}, _} =
  SmokeUtil.step("Bumblebee.load_model", fn ->
    Bumblebee.load_model({:local, model_path},
      type: :bf16,
      backend: Nx.BinaryBackend
    )
  end)

IO.puts("  → architecture: #{inspect(model_info.spec.architecture)}")
IO.puts("  → after load #{SmokeUtil.gpu_memory_summary()}")

SmokeUtil.section("load tokenizer + generation config")
{{:ok, tokenizer}, _} =
  SmokeUtil.step("load_tokenizer", fn ->
    Bumblebee.load_tokenizer({:local, model_path})
  end)

{{:ok, generation_config}, _} =
  SmokeUtil.step("load_generation_config", fn ->
    Bumblebee.load_generation_config({:local, model_path})
  end)

generation_config =
  Bumblebee.configure(generation_config,
    max_new_tokens: max_tokens,
    strategy: %{type: :greedy_search}
  )

model_info =
  case quantize do
    "int8" ->
      SmokeUtil.section("quantize → int8 (Axon.Quantization)")

      {{quantized_model, quantized_params}, _} =
        SmokeUtil.step("Axon.Quantization.quantize", fn ->
          Axon.Quantization.quantize(model_info.model, model_info.params)
        end)

      %{model_info | model: quantized_model, params: quantized_params}

    _ ->
      IO.puts("[quantize] skipped (QUANTIZE=#{quantize})")
      model_info
  end

SmokeUtil.section("transfer params → GPU (EXLA cuda)")

{params_on_gpu, _} =
  SmokeUtil.step("Nx.backend_transfer", fn ->
    Nx.backend_transfer(model_info.params, {EXLA.Backend, client: :cuda})
  end)

model_info = %{model_info | params: params_on_gpu}
IO.puts("  → after transfer #{SmokeUtil.gpu_memory_summary()}")

SmokeUtil.section("build serving + JIT compile + first generation")

{serving, _} =
  SmokeUtil.step("Bumblebee.Text.generation", fn ->
    Bumblebee.Text.generation(model_info, tokenizer, generation_config,
      defn_options: [compiler: EXLA]
    )
  end)

IO.puts("[gen] prompt:\n#{prompt}")
IO.puts("[gen] running (first call includes JIT compilation, expect 30-90 s)...")

t_gen_start = System.monotonic_time(:millisecond)
result = Nx.Serving.run(serving, prompt)
t_gen_end = System.monotonic_time(:millisecond)

IO.puts("[gen] first generation: #{t_gen_end - t_gen_start} ms")
IO.puts("  → #{SmokeUtil.gpu_memory_summary()}")
IO.puts("[gen] output:")
IO.inspect(result, pretty: true, limit: :infinity)

# 2 回目 (JIT compile 済、純粋な生成レイテンシ)
SmokeUtil.section("second generation (post-JIT)")
t2_start = System.monotonic_time(:millisecond)
_result2 = Nx.Serving.run(serving, prompt)
t2_end = System.monotonic_time(:millisecond)
IO.puts("[gen2] second generation: #{t2_end - t2_start} ms")

SmokeUtil.section("smoke summary")
IO.puts("first gen (with JIT): #{t_gen_end - t_gen_start} ms")
IO.puts("second gen (no JIT):  #{t2_end - t2_start} ms")
IO.puts("final #{SmokeUtil.gpu_memory_summary()}")
IO.puts("")
IO.puts("[SMOKE] OK ✅")
