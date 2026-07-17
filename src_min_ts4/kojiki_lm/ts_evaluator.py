"""
閻魔 (Yomi Evaluator) — TypeScript target 版 + 光明想 (こうみょうそう) 統合 (ts4)

L3 から流れてきたテキスト (L3ToL5Payload) を **decode ループ中** に評価して、
V_score を計算し、閾値 2 段で COMMIT / REPAIR / HALT を返す。

eli4 (`kojiki_lm/elixir_evaluator.py`) からの ts4 差分 (data/kojiki/設計書/ts4_実装設計書_v0.md
§2-3 より):
  - クラス名 `ElixirEvaluator` → `TsEvaluator`
  - キーワード語彙を Elixir → TypeScript に差し替え (`_TS_GOOD_KEYWORDS` / `_TS_BAD_PATTERNS`)
  - `do`/`end` ブロック収支チェックは TS に存在しないため **削除**し、既存の bracket 収支
    (`()[]{}`) に一本化する。`ReasonCode.DO_END_MISMATCH` は enum に残る (yomotsu_hirasaka.py
    を verbatim に保つため) が、ts4 の判定優先順位には現れない dead code
  - **スコア計算の骨格 (0.5 起点、good keyword +0.05/hit、bad pattern -0.10、bracket 不一致
    -0.20、commit>=0.7 / halt<0.3、光明想 terminal failure は overriding HALT) は 1 bit も
    変えていない**

Go 版 (src_min_go/kojiki_lm/yomi_evaluator.py) / eli4 版と同形、語彙だけ TypeScript に
差し替えた。本ファイルは **生成中の hot path** で呼ばれる軽量 heuristic 評価器。実 subprocess
(`tsc`/`node` でテスト実行) は別経路 scripts/eval/ts_eval.py が **生成完了後** に行う
(第2段の担当、本ファイルの守備範囲外)。

評価フロー:
  1. (新) 光明想チェック: KoumyouSo.validate(text).is_terminal_failure → 即 HALT
  2. 空テキスト           → 即 HALT
  3. 極端に短い (< 5)     → v_score 低
  4. TypeScript らしいキーワード (function, const, =>, 型注釈 等) の存在 → 加点
  5. 危険パターン (// TODO, throw new Error("not implemented 等) → 減点
  6. 中括弧/丸括弧/角括弧の収支 → 不一致は減点

TypeScript 固有の注意点:
  - `do`/`end` の概念が無いため、ブロック境界は bracket 収支のみで近似する
  - template literal / 文字列内の括弧は近似のまま (eli4 と同水準の割り切り)
"""

from __future__ import annotations

from dataclasses import dataclass

from .koumyou_so import KoumyouSo, TraceStatus
from .yomotsu_hirasaka import L3ToL5Payload, L5ToL3Verdict, ReasonCode, Verdict


# TypeScript で「正しい TypeScript 構文に向かっている」キーワード (加点対象)。
# 末尾スペースを含むものは「キーワードであって識別子の一部ではない」ことの担保。
_TS_GOOD_KEYWORDS = (
    # 宣言
    "function ", "const ", "let ", "return ",
    "interface ", "type ",
    # 型注釈
    ": number", ": string", ": boolean", "[]", "Array<",
    # 標準ライブラリ呼び出し (型のヒント)
    "Math.", "String(", "Number(",
    ".map(", ".filter(", ".reduce(", ".length",
    # 制御・演算子
    "=>", "===", "!==", "for (", "while (", "if (",
)

# 危険・未完成パターン (減点対象)
_TS_BAD_PATTERNS = (
    "// TODO", "// FIXME", "// XXX",
    'throw new Error("not implemented',
    'throw new Error("TODO',
    'throw new Error("unimplemented',
    'throw new Error("todo',
    "// unimplemented",
)


@dataclass(frozen=True)
class EvaluatorConfig:
    """V_score → verdict の閾値設定。Go/Elixir 版と同じデフォルト値を採用"""
    commit_threshold: float = 0.7   # v_score >= → COMMIT
    halt_threshold: float = 0.3     # v_score <  → HALT
    # 上記の間 → REPAIR

    min_text_length: int = 5
    good_keyword_weight: float = 0.05    # 1 ヒットあたり
    bad_pattern_penalty: float = 0.10    # 1 ヒットあたり
    bracket_mismatch_penalty: float = 0.20
    do_end_mismatch_penalty: float = 0.20  # ts4 では発生しない (dead code、後方互換のため残置)


class TsEvaluator:
    """簡略版 Evaluator: L3ToL5Payload → L5ToL3Verdict (TypeScript ターゲット)"""

    def __init__(
        self,
        config: EvaluatorConfig | None = None,
        koumyou_so: KoumyouSo | None = None,
    ) -> None:
        self.config = config or EvaluatorConfig()
        if not (0.0 <= self.config.halt_threshold <= self.config.commit_threshold <= 1.0):
            raise ValueError(
                f"thresholds must satisfy 0 <= halt ({self.config.halt_threshold}) "
                f"<= commit ({self.config.commit_threshold}) <= 1"
            )
        # 光明想 (None なら ablation 対照 = firewall-on/off と同等動作)
        self.koumyou_so = koumyou_so

    # 光明想 terminal failure → reason_code の対応表 (事戸拡張、優先順位 1)
    _TRACE_STATUS_TO_REASON = {
        TraceStatus.TRACE_MISSING: ReasonCode.TRACE_MISSING,
        TraceStatus.TRACE_INSUFFICIENT: ReasonCode.TRACE_INSUFFICIENT,
    }

    def __call__(self, payload: L3ToL5Payload) -> L5ToL3Verdict:
        # 1. 光明想チェック (有効時のみ): trace 不在/不足は v_score 計算より先に HALT。
        # 「闇 (中間推論の不在) を照明で破る」原理 — gameable な scoring に
        # 折り込むのではなく、structural gate として overriding させる。
        # generated text のみを渡す (prompt の中の `function` を code 開始と誤検出しないため)。
        if self.koumyou_so is not None:
            generated_text = payload.text[payload.prompt_len:]
            trace = self.koumyou_so.validate(generated_text)
            if trace.is_terminal_failure:
                reason_code = self._TRACE_STATUS_TO_REASON[trace.status]
                return L5ToL3Verdict(
                    verdict=Verdict.HALT, v_score=0.0, reason_code=reason_code
                )

        v_score, flags = self._compute_score_and_flags(payload.text)
        verdict = self._decide(v_score)

        # 3. reason_code 判定 (事戸拡張、優先順位 2-3):
        #   COMMIT → NONE。それ以外は検出済みフラグを
        #   BRACKET_MISMATCH > BAD_PATTERN > LOW_SCORE の優先順位で 1 つ選ぶ。
        #   (do_end_mismatch は TS には存在しないため優先順位から除外 — 設計書 §3)
        if verdict == Verdict.COMMIT:
            reason_code = ReasonCode.NONE
        elif flags["bracket_mismatch"]:
            reason_code = ReasonCode.BRACKET_MISMATCH
        elif flags["bad_pattern"]:
            reason_code = ReasonCode.BAD_PATTERN
        else:
            reason_code = ReasonCode.LOW_SCORE

        return L5ToL3Verdict(verdict=verdict, v_score=v_score, reason_code=reason_code)

    def _compute_v_score(self, text: str) -> float:
        """後方互換のための薄いラッパー。数値計算は `_compute_score_and_flags` に一本化。"""
        score, _flags = self._compute_score_and_flags(text)
        return score

    def _compute_score_and_flags(self, text: str) -> tuple[float, dict[str, bool]]:
        """v_score と、事戸拡張の reason_code 判定に使う検出フラグを同時に返す。

        **数値計算 (score の加減算・順序) は eli4 の `_compute_score_and_flags` と
        1 bit も変えていない** (do/end チェックのみ削除。以下は eli4 の該当コードと
        同一) — 各 if 節で既に判定している bool をそのまま流用しているだけ。
        """
        flags = {
            "bracket_mismatch": False,
            "do_end_mismatch": False,
            "bad_pattern": False,
        }

        if not text:
            return 0.0, flags
        if len(text) < self.config.min_text_length:
            return 0.1, flags

        score = 0.5

        for kw in _TS_GOOD_KEYWORDS:
            if kw in text:
                score += self.config.good_keyword_weight

        for pat in _TS_BAD_PATTERNS:
            if pat in text:
                score -= self.config.bad_pattern_penalty
                flags["bad_pattern"] = True

        if not self._brackets_balanced(text):
            score -= self.config.bracket_mismatch_penalty
            flags["bracket_mismatch"] = True

        # do/end 収支チェックは TS に存在しないため削除 (設計書 §3)。
        # flags["do_end_mismatch"] は常に False のまま (dead code、後方互換のため残置)。

        return max(0.0, min(1.0, score)), flags

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
