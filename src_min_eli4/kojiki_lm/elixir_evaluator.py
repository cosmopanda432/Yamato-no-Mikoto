"""
閻魔 (Yomi Evaluator) — Elixir target 版 + 光明想 (こうみょうそう) 統合 (eli3)

L3 から流れてきたテキスト (L3ToL5Payload) を **decode ループ中** に評価して、
V_score を計算し、閾値 2 段で COMMIT / REPAIR / HALT を返す。

eli2 との差分 (2026-05-26、docs/memo/2026-05-26_須弥山設計原理.md Part 7 より):
  - **光明想 (KoumyouSo) を統合**: reasoning trace (`# 思考: ...`) の不在/不足を
    検出した場合、v_score 計算より先に **即 HALT を返す** (= overriding gate)
  - 仏教五蓋の第三「惛沈睡眠」(怠惰) を「光明想」(中間推論の強制照明) で対治する設計
  - KoumyouSo を None で初期化すれば eli2 と同等動作 (ablation 対照用)

Go 版 (src_min_go/kojiki_lm/yomi_evaluator.py) と同形、語彙だけ Elixir に差し替えた。
本ファイルは **生成中の hot path** で呼ばれる軽量 heuristic 評価器。実 subprocess
(`elixir <file>` でテスト実行) は別経路 scripts/eval/elixir_eval.py が **生成完了後** に行う。

評価フロー:
  1. (新) 光明想チェック: KoumyouSo.validate(text).is_terminal_failure → 即 HALT
  2. 空テキスト           → 即 HALT
  3. 極端に短い (< 5)     → v_score 低
  4. Elixir らしいキーワード (defmodule, def, |>, do/end 等) の存在 → 加点
  5. 危険パターン (# TODO, raise "not implemented" 等) → 減点
  6. 中括弧/丸括弧/角括弧の収支 + do/end の対応 → 不一致は減点

Elixir 固有の注意点:
  - `do` `end` のブロック対応をカウントする (Elixir 独自、Go の `{}` に相当)
  - `|>` (pipe) は Elixir コードの強い signal、加点ウェイトを高めに
  - `@spec` は optional だが付いていれば「型情報を意識した生成」の signal
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .koumyou_so import KoumyouSo
from .yomotsu_hirasaka import L3ToL5Payload, L5ToL3Verdict, Verdict


# Elixir で「正しい Elixir 構文に向かっている」キーワード (加点対象)。
# 末尾スペースを含むものは「キーワードであって識別子の一部ではない」ことの担保。
_ELIXIR_GOOD_KEYWORDS = (
    # 宣言
    "defmodule ", "def ", "defp ", "defmacro ", "defmacrop ",
    "defguard ", "defguardp ", "defstruct ", "defprotocol ", "defimpl ",
    # ブロック
    " do\n", " do\r\n", "do:", "fn ", "fn(",
    # 制御
    "case ", "cond do", "with ", "when ", "if ", "unless ", "for ",
    "try do", "rescue", "after",
    # Elixir 固有 (強い signal)
    "|>", ":ok", ":error",
    # @ attribute (型/spec/doc)
    "@spec ", "@type ", "@callback ", "@moduledoc ", "@doc ",
    "@behaviour ", "@impl ",
    # 標準ライブラリ呼び出し (型のヒント)
    "Enum.", "String.", "Map.", "List.", "Keyword.", "Stream.",
    "Tuple.", "Atom.", "Integer.", "Float.",
    # guard 述語 (型の signal)
    "is_atom(", "is_binary(", "is_boolean(", "is_function(",
    "is_integer(", "is_list(", "is_map(", "is_nil(",
    "is_number(", "is_pid(", "is_reference(", "is_tuple(",
    # match
    " = ", "->",
)

# 危険・未完成パターン (減点対象)
_ELIXIR_BAD_PATTERNS = (
    "# TODO", "# FIXME", "# XXX",
    'raise "not implemented',
    'raise "TODO',
    'raise "unimplemented',
    'raise "todo',
    "# unimplemented",
)


@dataclass(frozen=True)
class EvaluatorConfig:
    """V_score → verdict の閾値設定。Go/TS 版と同じデフォルト値を採用"""
    commit_threshold: float = 0.7   # v_score >= → COMMIT
    halt_threshold: float = 0.3     # v_score <  → HALT
    # 上記の間 → REPAIR

    min_text_length: int = 5
    good_keyword_weight: float = 0.05    # 1 ヒットあたり
    bad_pattern_penalty: float = 0.10    # 1 ヒットあたり
    bracket_mismatch_penalty: float = 0.20
    do_end_mismatch_penalty: float = 0.20  # do の数 != end の数 で減点


class ElixirEvaluator:
    """簡略版 Evaluator: L3ToL5Payload → L5ToL3Verdict (Elixir ターゲット)"""

    # do/end カウント用。識別子の一部ではない (e.g., `do_something` の `do_` ではない) ことを担保
    _DO_PATTERN = re.compile(r"(?<![A-Za-z0-9_])do(?![A-Za-z0-9_])")
    _END_PATTERN = re.compile(r"(?<![A-Za-z0-9_])end(?![A-Za-z0-9_])")

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
        # 光明想 (None なら ablation 対照 = eli2 と同等動作)
        self.koumyou_so = koumyou_so

    def __call__(self, payload: L3ToL5Payload) -> L5ToL3Verdict:
        # 1. 光明想チェック (有効時のみ): trace 不在/不足は v_score 計算より先に HALT。
        # 「闇 (中間推論の不在) を照明で破る」原理 — gameable な scoring に
        # 折り込むのではなく、structural gate として overriding させる。
        # generated text のみを渡す (prompt の中の `def` を code 開始と誤検出しないため)。
        if self.koumyou_so is not None:
            generated_text = payload.text[payload.prompt_len:]
            trace = self.koumyou_so.validate(generated_text)
            if trace.is_terminal_failure:
                return L5ToL3Verdict(verdict=Verdict.HALT, v_score=0.0)

        v_score = self._compute_v_score(payload.text)
        verdict = self._decide(v_score)
        return L5ToL3Verdict(verdict=verdict, v_score=v_score)

    def _compute_v_score(self, text: str) -> float:
        if not text:
            return 0.0
        if len(text) < self.config.min_text_length:
            return 0.1

        score = 0.5

        for kw in _ELIXIR_GOOD_KEYWORDS:
            if kw in text:
                score += self.config.good_keyword_weight

        for pat in _ELIXIR_BAD_PATTERNS:
            if pat in text:
                score -= self.config.bad_pattern_penalty

        if not self._brackets_balanced(text):
            score -= self.config.bracket_mismatch_penalty

        if not self._do_end_balanced(text):
            score -= self.config.do_end_mismatch_penalty

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

    @classmethod
    def _do_end_balanced(cls, text: str) -> bool:
        """Elixir の `do`/`end` ブロックの数が合っているかを近似 (識別子境界考慮)。

        近似のため不完全: `do: ...` の inline 形式や string literal 内の "do"/"end"
        などは ignore できないが、生成中の partial text に対する大まかな signal としては
        十分。
        """
        # `do:` (inline keyword list 形式) は除外したいので、シンプルに数を見る:
        # 「`do` (block) の数」≈「pattern マッチ数 − `do:` の数」
        do_block_count = len(cls._DO_PATTERN.findall(text))
        do_inline_count = text.count("do:")
        do_block_count -= do_inline_count
        end_count = len(cls._END_PATTERN.findall(text))

        # 生成途中 (do の方が多い) は許容、end の方が多いのは異常
        return do_block_count >= end_count

    def _decide(self, v_score: float) -> Verdict:
        if v_score >= self.config.commit_threshold:
            return Verdict.COMMIT
        if v_score < self.config.halt_threshold:
            return Verdict.HALT
        return Verdict.REPAIR
