"""
黄泉比良坂 (Yomotsu Hirasaka) — L3 ↔ L5 一方向ゲートウェイ

役割: 葦原 (L3, 生成ランタイム) と 黄泉 (L5, 評価器) の間の通信を
frozen dataclass + 型バリデーションで構造的に強制する。

通信契約:
  L3 → L5:  L3ToL5Payload   (text + meta のみ)
  L5 → L3:  L5ToL3Verdict   (verdict ∈ {COMMIT, REPAIR, HALT} + v_score ∈ [0,1] のみ)

L3 → L5 で **モデル内部状態 (hidden_states, logits, tensor)** を渡そうとすると
__post_init__ が TypeError を投げる。L5 → L3 で **verdict 以外の値** を返そうとすると
YomotsuHirasaka.send の戻り値型チェックで TypeError を投げる。

設計原則:
  - 評価器の内部状態 (Yomi Archive, 過去 verdict, 累積統計) は L3 に漏れない
  - L3 の内部状態 (型ヘッド出力, attention weight) は L5 に漏れない
  - L3 から L5 に渡す情報は L3 側で明示的に整形 (str/int) する必要がある
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable


class Verdict(Enum):
    COMMIT = "commit"
    REPAIR = "repair"
    HALT = "halt"


@dataclass(frozen=True)
class L3ToL5Payload:
    """葦原 → 黄泉: text と最小メタのみ。tensor 等は受け付けない。

    eli3 で `prompt_len` を追加 (default 0、後方互換)。光明想 (KoumyouSo) など
    「生成部分のみ」を検査したい L5 評価器が `text[prompt_len:]` でスライスする
    ために必要。L3 側 (FirewallDecoder) が prompt 投入時に len を設定する。
    """
    text: str
    step_idx: int
    prompt_id: str
    prompt_len: int = 0
    """text 中で `text[:prompt_len]` は prompt、`text[prompt_len:]` は生成部分。
    0 は「prompt 境界情報なし」(全体を生成扱い、eli2 互換)。
    """

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError(
                f"L3ToL5Payload.text must be str, got {type(self.text).__name__}. "
                "L5 への送信ペイロードに tensor / hidden_state は渡せません。"
            )
        if not isinstance(self.step_idx, int) or isinstance(self.step_idx, bool):
            raise TypeError(
                f"L3ToL5Payload.step_idx must be int, got {type(self.step_idx).__name__}"
            )
        if self.step_idx < 0:
            raise ValueError(f"L3ToL5Payload.step_idx must be >= 0, got {self.step_idx}")
        if not isinstance(self.prompt_id, str):
            raise TypeError(
                f"L3ToL5Payload.prompt_id must be str, got {type(self.prompt_id).__name__}"
            )
        if not isinstance(self.prompt_len, int) or isinstance(self.prompt_len, bool):
            raise TypeError(
                f"L3ToL5Payload.prompt_len must be int, got {type(self.prompt_len).__name__}"
            )
        if self.prompt_len < 0:
            raise ValueError(
                f"L3ToL5Payload.prompt_len must be >= 0, got {self.prompt_len}"
            )
        if self.prompt_len > len(self.text):
            raise ValueError(
                f"L3ToL5Payload.prompt_len ({self.prompt_len}) > len(text) "
                f"({len(self.text)})"
            )


@dataclass(frozen=True)
class L5ToL3Verdict:
    """黄泉 → 葦原: verdict と v_score のみ。それ以外の評価器内部状態は持たせない"""
    verdict: Verdict
    v_score: float

    def __post_init__(self) -> None:
        if not isinstance(self.verdict, Verdict):
            raise TypeError(
                f"L5ToL3Verdict.verdict must be Verdict enum, "
                f"got {type(self.verdict).__name__}. "
                "L5 から L3 へ返せるのは COMMIT / REPAIR / HALT のみ。"
            )
        if isinstance(self.v_score, bool) or not isinstance(self.v_score, (int, float)):
            raise TypeError(
                f"L5ToL3Verdict.v_score must be float, got {type(self.v_score).__name__}"
            )
        if not (0.0 <= float(self.v_score) <= 1.0):
            raise ValueError(
                f"L5ToL3Verdict.v_score must be in [0.0, 1.0], got {self.v_score}"
            )


EvaluatorFn = Callable[[L3ToL5Payload], L5ToL3Verdict]


class YomotsuHirasaka:
    """
    L3 ↔ L5 ゲートウェイ本体。

    L3 側コードは `gateway.send(payload)` のみを呼び、L5 評価器に直接アクセスしない。
    評価器の戻り値が L5ToL3Verdict 型でないことを send() で検出し、契約違反を弾く。
    """

    def __init__(self, evaluator: EvaluatorFn) -> None:
        if not callable(evaluator):
            raise TypeError(
                f"YomotsuHirasaka requires a callable evaluator, "
                f"got {type(evaluator).__name__}"
            )
        self._evaluator = evaluator

    def send(self, payload: L3ToL5Payload) -> L5ToL3Verdict:
        if not isinstance(payload, L3ToL5Payload):
            raise TypeError(
                f"YomotsuHirasaka.send requires L3ToL5Payload, "
                f"got {type(payload).__name__}. L3 → L5 は frozen dataclass 経由のみ。"
            )

        result = self._evaluator(payload)

        if not isinstance(result, L5ToL3Verdict):
            raise TypeError(
                f"Evaluator must return L5ToL3Verdict, got {type(result).__name__}. "
                "L5 → L3 で許可されているのは {verdict, v_score} のみ。"
            )

        return result
