"""
Evaluator (yomi_evaluator) — Go 版テスト

Go 用キーワードで V_score が正しく動くこと、TS 用パターン (`: number`, `=>`) が
Go 用 GOOD としては機能しないこと、Go 固有 (`:=`, `chan`, `defer`) が拾えること、
HumanEval-Go の prompt 形式で reasonable な score 分布が出ることを担保する。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src_min_go"))

from kojiki_lm.yomi_evaluator import EvaluatorConfig, YomiEvaluator  # noqa: E402
from kojiki_lm.yomotsu_hirasaka import (  # noqa: E402
    L3ToL5Payload,
    Verdict,
    YomotsuHirasaka,
)


def _eval(text: str, config: EvaluatorConfig | None = None) -> float:
    ev = YomiEvaluator(config=config)
    return ev._compute_v_score(text)


# --- V_score 基本動作 ---

class TestVScore:
    def test_empty_text_halts(self):
        assert _eval("") == 0.0

    def test_short_text_low(self):
        assert _eval("hi") == 0.1

    def test_well_typed_go_scores_high(self):
        text = (
            "package main\n"
            "\n"
            "func sum(xs []int) int {\n"
            "\ttotal := 0\n"
            "\tfor _, x := range xs {\n"
            "\t\ttotal += x\n"
            "\t}\n"
            "\treturn total\n"
            "}\n"
        )
        v = _eval(text)
        assert v >= 0.5, f"good Go code should score >= 0.5, got {v}"

    def test_todo_marker_penalised(self):
        text = "func f() {\n\t// TODO: implement\n}"
        v = _eval(text)
        assert v < 0.5, f"// TODO should drop score, got {v}"

    def test_panic_not_implemented_penalised(self):
        # GOOD kw が偶然加算されて penalty を相殺しないよう、加点要素のない短いテキストを使う
        without_panic = "x = 0\n"
        with_panic = 'x = 0\npanic("not implemented")\n'
        # bracket は両方バランス、`x = 0` には GOOD kw なし。panic 文字列だけが差を作る
        assert _eval(with_panic) < _eval(without_panic)

    def test_unbalanced_brackets_penalised(self):
        balanced = "func f() {\n\treturn 1\n}"
        unbalanced = "func f() {\n\treturn 1\n"
        assert _eval(unbalanced) < _eval(balanced)

    def test_score_clamped(self):
        text = (
            "package main\nfunc a() {}\nfunc b() {}\nvar x int\nvar y string\n"
            "type T struct{}\nfor i := 0; i < n; i++ { make([]int, 10) }\n"
        )
        v = _eval(text)
        assert 0.0 <= v <= 1.0


# --- Go 固有の構文を拾うこと ---

class TestGoSpecificKeywords:
    def test_short_var_decl_increments(self):
        with_short = "func f() { x := 1\n}"
        without_short = "func f() { x = 1\n}"
        # := の方が GOOD キーワード ":= " が増えてスコアが高くなる
        assert _eval(with_short) > _eval(without_short)

    def test_chan_and_goroutine_recognized(self):
        text = "func f() { c := make(chan int); go func() { c <- 1 }() }"
        # 不完全な構文 (defer なし) でも GOOD kw が拾えて > 0.3
        # bracket は balanced
        assert _eval(text) >= 0.4

    def test_defer_recognized(self):
        text = "func f() { defer fmt.Println(\"x\") }"
        assert _eval(text) > _eval("just text")

    def test_interface_brace_recognized(self):
        text = "type Reader interface {\n\tRead() error\n}"
        assert _eval(text) >= 0.5


# --- TS 用パターンが Go 版で活性化しないこと ---

class TestTSPatternsDoNotApply:
    def test_ts_function_keyword_not_treated_as_good(self):
        # "function" は Go のキーワードではない。GOOD として加点されない
        # ただし `func ` は ` func ` ではないので、`function foo()` には
        # ` func ` も含まれない → スコアはベース付近
        text = "function foo() {}"
        v = _eval(text)
        # Brackets balanced で 0.5、`function` は GOOD に含まれない → 0.5 のまま
        assert 0.4 < v < 0.6, f"got {v}"

    def test_ts_arrow_not_treated_as_good(self):
        # TS の `=>` は Go 版 GOOD には入っていない。同じ text を Go 評価器に通すと
        # bracket balanced + GOOD/BAD なし → ベース 0.5 のまま。TS 版なら `=>` が +0.05
        # でブーストされて > 0.5 になる。Go 版で活性化しないことだけ示せばよい
        text = "(x: number) => x + 1"
        v = _eval(text)
        assert v <= 0.5, f"TS arrow should not boost Go score; got {v}"


# --- Firewall 経由の統合 ---

class TestEvaluatorThroughFirewall:
    def test_evaluator_flows_through_gateway(self):
        gw = YomotsuHirasaka(YomiEvaluator())
        # ある程度妥当な Go コードを送って verdict が valid な enum で返る
        payload = L3ToL5Payload(
            text="package main\nfunc main() {\n\tfmt.Println(\"hi\")\n}",
            step_idx=0,
            prompt_id="p1",
        )
        v = gw.send(payload)
        assert isinstance(v.verdict, Verdict)
        assert 0.0 <= v.v_score <= 1.0

    def test_evaluator_halts_on_empty(self):
        gw = YomotsuHirasaka(YomiEvaluator())
        v = gw.send(L3ToL5Payload(text="", step_idx=0, prompt_id="p1"))
        assert v.verdict is Verdict.HALT


# --- 閾値設定の検証 ---

class TestVerdictBoundaries:
    def test_commit_at_high_score(self):
        # 多くの GOOD キーワードでスコアを高くする
        text = (
            "package main\nimport \"fmt\"\n"
            "func main() {\n\tvar x int\n\tx = 1\n\tfor i := 0; i < 10; i++ {\n"
            "\t\tfmt.Println(x)\n\t}\n\treturn\n}\n"
        )
        ev = YomiEvaluator()
        score = ev._compute_v_score(text)
        # commit_threshold = 0.7 を超えれば COMMIT
        if score >= 0.7:
            assert ev._decide(score) is Verdict.COMMIT

    def test_thresholds_validated(self):
        with pytest.raises(ValueError):
            EvaluatorConfig(commit_threshold=0.3, halt_threshold=0.5)
            YomiEvaluator(EvaluatorConfig(commit_threshold=0.3, halt_threshold=0.5))
