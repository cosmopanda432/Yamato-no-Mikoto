"""
閻魔 (Yomi Evaluator) — 簡略版

L3 から流れてきたテキスト (L3ToL5Payload) を評価して
V_score を計算し、閾値 2 段で COMMIT / REPAIR / HALT を返す。

M1' 簡略版の評価項目 (テキストのみから決定論的に計算):
  1. 空テキスト       → 即 HALT
  2. 極端に短い (< 5) → v_score 低
  3. TS らしいキーワード (function/const/let/interface 等) の存在 → 加点
  4. 危険パターン (any/unknown/@ts-ignore) → 減点
  5. 中括弧/丸括弧の収支 → 不一致は減点

実物の tsc strict / TypeHead 連動は M2 (言霊) で kotodama_decoder が
TypeHead 出力 → 物理マスクの経路を確立してから、ここを置換する。

Yomi Archive (Stage 別 verdict 履歴の長期保管) はカット。
"""

from __future__ import annotations

from dataclasses import dataclass

from .yomotsu_hirasaka import L3ToL5Payload, L5ToL3Verdict, Verdict

# TS で「型情報を提供する」キーワード (加点対象)
_TS_GOOD_KEYWORDS = (
    "function", "const", "let", "interface", "type ",
    "class ", "enum ", ": number", ": string", ": boolean",
    ": void", "Promise<", "Array<", "Record<", "=>",
)

# 型安全性を損なうパターン (減点対象)
_TS_BAD_PATTERNS = (
    " any", ": any", "<any>", "as any",
    " unknown", ": unknown",
    "@ts-ignore", "@ts-nocheck",
    "// TODO", "// FIXME",
)


@dataclass(frozen=True)
class EvaluatorConfig:
    """V_score → verdict の閾値設定"""
    commit_threshold: float = 0.7   # v_score >= → COMMIT
    halt_threshold: float = 0.3     # v_score <  → HALT
    # 上記の間 → REPAIR

    min_text_length: int = 5
    good_keyword_weight: float = 0.05    # 1 ヒットあたり
    bad_pattern_penalty: float = 0.10    # 1 ヒットあたり
    bracket_mismatch_penalty: float = 0.20


class YomiEvaluator:
    """簡略版 Evaluator: L3ToL5Payload → L5ToL3Verdict"""

    def __init__(self, config: EvaluatorConfig | None = None) -> None:
        self.config = config or EvaluatorConfig()
        if not (0.0 <= self.config.halt_threshold <= self.config.commit_threshold <= 1.0):
            raise ValueError(
                f"thresholds must satisfy 0 <= halt ({self.config.halt_threshold}) "
                f"<= commit ({self.config.commit_threshold}) <= 1"
            )

    def __call__(self, payload: L3ToL5Payload) -> L5ToL3Verdict:
        v_score = self._compute_v_score(payload.text)
        verdict = self._decide(v_score)
        return L5ToL3Verdict(verdict=verdict, v_score=v_score)

    def _compute_v_score(self, text: str) -> float:
        if not text:
            return 0.0
        if len(text) < self.config.min_text_length:
            return 0.1

        score = 0.5

        for kw in _TS_GOOD_KEYWORDS:
            if kw in text:
                score += self.config.good_keyword_weight

        for pat in _TS_BAD_PATTERNS:
            if pat in text:
                score -= self.config.bad_pattern_penalty

        if not self._brackets_balanced(text):
            score -= self.config.bracket_mismatch_penalty

        return max(0.0, min(1.0, score))

    @staticmethod
    def _brackets_balanced(text: str) -> bool:
        pairs = {")": "(", "]": "[", "}": "{"}
        stack: list[str] = []
        for ch in text:
            if ch in "([{":
                stack.append(ch)
            elif ch in ")]}":
                if not stack or stack[-1] != pairs[ch]:
                    return False
                stack.pop()
        return not stack

    def _decide(self, v_score: float) -> Verdict:
        if v_score >= self.config.commit_threshold:
            return Verdict.COMMIT
        if v_score < self.config.halt_threshold:
            return Verdict.HALT
        return Verdict.REPAIR
