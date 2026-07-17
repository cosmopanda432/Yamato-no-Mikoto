"""
光明想 (こうみょうそう) — Reasoning Trace Validator

仏教五蓋の第三「惛沈睡眠 (こんちんすいみん)」= 怠惰・手抜き への対治法は
「光明想」= 光を観想すること、つまり「闇 (出力の不透明性) を照明 (中間推論の可視化) で
破る」というもの。

役割: 出力テキストが `// 思考: ...` で始まる reasoning trace を持つことを強制する。
trace 不在 = 惛沈睡眠 (model が思考過程を見せずに code に直行) → HALT 信号を生成。

設計原則 (docs/memo/2026-05-26_須弥山設計原理.md Part 2 §6 より):
  - 光明想は「中間推論を verifier に見せないと submit させない」を強制機構
  - LLM judge は gameable のため使わず、structural check のみ
  - 「閻魔の浄玻璃鏡」原理 (改竄不能性) に従い、決定論的 regex / カウントベース

trace format (本実装で強制する形式):
    // 思考: <content line 1>
    // 思考: <content line 2>
    ...
    <code (TypeScript 関数本体 or `function`/`const` 等)>

判定ルール:
  - 生成テキストの **先頭から連続する** 「空白行 or `// 思考:` 行」を trace prefix と
    みなす。
  - 最初に出現する「trace でも空白でもない行」を「code 開始」と判定する。
  - code 開始時点で trace 行数 ≥ min_trace_lines かつ trace 本文文字数 ≥ min_trace_chars
    なら TRACE_VALID。
  - そうでなければ TRACE_INSUFFICIENT / TRACE_MISSING (= HALT)。

判定の状態:
    STILL_GENERATING:   text 長 < grace_period_chars かつ code 未開始 (生成初期、保留)
    TRACE_ONLY:         code 未開始 (text は長いが trace のみ) — 生成途中として許容
    TRACE_VALID:        code 開始済 + trace 行数・文字数 ≥ 閾値
    TRACE_INSUFFICIENT: code 開始済 + trace は存在するが不足
    TRACE_MISSING:      code 開始済 + trace marker が皆無 (最悪)

呼び出し側 (`ts_evaluator.py`) は TRACE_INSUFFICIENT / TRACE_MISSING を
v_score = 0.0 + HALT に直接マッピングする。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


THOUGHT_MARKER = "// 思考:"


class TraceStatus(Enum):
    STILL_GENERATING = "still_generating"
    TRACE_ONLY = "trace_only"
    TRACE_VALID = "trace_valid"
    TRACE_INSUFFICIENT = "trace_insufficient"
    TRACE_MISSING = "trace_missing"


@dataclass(frozen=True)
class KoumyouSoConfig:
    """光明想の閾値設定。"""

    min_trace_lines: int = 1
    """`// 思考:` 行が最低この本数なければ INSUFFICIENT。

    Note (2026-05-26 smoke 知見): Qwen2.5-Coder-Instruct は「1 行に comma 区切りで
    全 step を詰める」スタイル (e.g. `1. ..., 2. ..., 3. ...`) を好む。bare prompt
    + trace seed のみだと multi-line trace に誘導しきれないため、デフォルトは 1
    に下げた。multi-line trace を要求する場合は呼び出し側で 2 以上に設定する
    (prompt 強化と組み合わせる前提)。
    """

    min_trace_chars: int = 20
    """trace の中身 (marker を除いた本文) の合計文字数の下限。
    無意味な padding (e.g. `// 思考: a`) で gaming するのを防ぐ。
    1 行 trace でも substance を担保する主要 gate (上記 min_trace_lines の制約緩和
    に伴い、こちらが事実上の主軸チェックになる)。
    """

    grace_period_chars: int = 16
    """generated text 長がこれ未満なら STILL_GENERATING で保留する。
    生成初期に code/trace 判定を急いで HALT するのを避ける。
    """

    trace_seed: str = ""
    """prompt 末尾に pre-seed された trace prefix (e.g. `"  // 思考: "`)。
    runner が prompt 末尾に注入した場合、generated_text はその「続き」から始まる
    ので、validate 時に trace_seed を prepend して整合させる。
    空文字列なら無効 (生成テキスト全体を validator が見る)。
    """


@dataclass(frozen=True)
class TraceVerdict:
    status: TraceStatus
    n_thought_lines: int
    trace_body_chars: int
    """marker を除いた trace 本文の合計文字数。"""
    code_started: bool

    @property
    def is_terminal_failure(self) -> bool:
        """`True` のとき呼び出し側は HALT すべき。"""
        return self.status in (TraceStatus.TRACE_INSUFFICIENT, TraceStatus.TRACE_MISSING)


class KoumyouSo:
    """光明想 — generated_text → TraceVerdict の純粋関数 (state を持たない)。

    `validate(generated_text)` は **prompt を含まない、生成された部分のみ** を
    引数に取る。呼び出し側 (evaluator) が prompt_len を使ってスライスする責務を持つ。
    """

    def __init__(self, config: KoumyouSoConfig | None = None) -> None:
        self.config = config or KoumyouSoConfig()
        if self.config.min_trace_lines < 0:
            raise ValueError(
                f"min_trace_lines must be >= 0, got {self.config.min_trace_lines}"
            )
        if self.config.min_trace_chars < 0:
            raise ValueError(
                f"min_trace_chars must be >= 0, got {self.config.min_trace_chars}"
            )
        if self.config.grace_period_chars < 0:
            raise ValueError(
                f"grace_period_chars must be >= 0, got {self.config.grace_period_chars}"
            )

    def validate(self, generated_text: str) -> TraceVerdict:
        cfg = self.config

        # Grace period — 生成初期 (generated 部分が短い) は code/trace 判定を急がず
        # 保留する。これがないと、e.g. 最初の 3 char で非 trace 行を検出して
        # 誤って TRACE_MISSING を返してしまう。code_started の判定より先に効かせる。
        if len(generated_text) < cfg.grace_period_chars:
            return TraceVerdict(
                status=TraceStatus.STILL_GENERATING,
                n_thought_lines=0,
                trace_body_chars=0,
                code_started=False,
            )

        # runner が prompt 末尾に trace_seed (e.g. `"  // 思考: "`) を pre-seed して
        # いる場合、generated_text はその「続き」から始まる。validator から見ると
        # 1 行目の先頭に marker が無いように見えるので、prepend して整合させる。
        if cfg.trace_seed:
            text_to_scan = cfg.trace_seed + generated_text
        else:
            text_to_scan = generated_text

        n_thought_lines = 0
        trace_body_chars = 0
        code_started = False

        # 生成テキストの先頭から1行ずつ走査:
        #   - 空白行 → スキップ (trace の前後の余白を許容)
        #   - `// 思考:` 行 → trace としてカウント
        #   - それ以外 → code 開始としてループ離脱
        for raw_line in text_to_scan.split("\n"):
            stripped = raw_line.strip()
            if not stripped:
                continue
            if stripped.startswith(THOUGHT_MARKER):
                body = stripped[len(THOUGHT_MARKER):].strip()
                n_thought_lines += 1
                trace_body_chars += len(body)
                continue
            # trace marker でも空行でもない → code 開始と判定
            code_started = True
            break

        if not code_started:
            # text は十分長いが code は始まっていない (trace prefix のみ、or 空白のみ)。
            return TraceVerdict(
                status=TraceStatus.TRACE_ONLY,
                n_thought_lines=n_thought_lines,
                trace_body_chars=trace_body_chars,
                code_started=False,
            )

        # code が始まった以降、trace の十分性を最終判定する。
        if n_thought_lines == 0:
            return TraceVerdict(
                status=TraceStatus.TRACE_MISSING,
                n_thought_lines=0,
                trace_body_chars=0,
                code_started=True,
            )

        if n_thought_lines < cfg.min_trace_lines or trace_body_chars < cfg.min_trace_chars:
            return TraceVerdict(
                status=TraceStatus.TRACE_INSUFFICIENT,
                n_thought_lines=n_thought_lines,
                trace_body_chars=trace_body_chars,
                code_started=True,
            )

        return TraceVerdict(
            status=TraceStatus.TRACE_VALID,
            n_thought_lines=n_thought_lines,
            trace_body_chars=trace_body_chars,
            code_started=True,
        )
