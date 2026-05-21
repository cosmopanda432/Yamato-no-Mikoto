defmodule KojikiLM.Config do
  @moduledoc """
  Step 1 の stub — Qwen3-Coder-30B-A3B を Bumblebee で load するときの設定。

  2026-05-21 確定 option A (`docs/roadmap_min_elixir.md` 参照):

  - LM = Qwen3-Coder-30B-A3B-Instruct (Bumblebee v0.7.0 で Qwen3 サポート追加済)
  - 量子化 = weight-only int8 (`Axon.Quantization.quantize/2`、Bumblebee 公式の唯一の量子化)
  - GPU = A6000 48GB (int8 30B ~30-35 GB + KV cache + activation で収まる想定)

  80B (Qwen3-Coder-Next) は Bumblebee の int4/GGUF 未対応のため A100/H100 が必要となり
  コスト 6× で除外。詳細は docs/roadmap_min_elixir.md「選択肢の検討と option A 採用理由」参照。

  Step 4 + 骨格段階では未使用。Step 1 着手時に Bumblebee/Nx/EXLA を deps に追加した
  上で、本 module から `Bumblebee.load_model/2` を呼ぶ予定。
  """

  defstruct model_repo: "Qwen/Qwen3-Coder-30B-A3B-Instruct",
            quantization: :int8,
            backend: :exla,
            dtype: :bf16,
            max_new_tokens: 256,
            temperature: 1.0,
            top_p: 0.95,
            seed: 0

  @type t :: %__MODULE__{
          model_repo: String.t(),
          quantization: :int8 | :none,
          backend: :exla | :binary,
          dtype: :bf16 | :fp16 | :fp32,
          max_new_tokens: pos_integer(),
          temperature: float(),
          top_p: float(),
          seed: non_neg_integer()
        }

  @spec default() :: t()
  def default, do: %__MODULE__{}
end
