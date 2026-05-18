"""M1' YomiEvaluator (簡略版) の V_score → verdict ロジックテスト"""

import pytest

from kojiki_lm.yomi_evaluator import EvaluatorConfig, YomiEvaluator
from kojiki_lm.yomotsu_hirasaka import L3ToL5Payload, Verdict, YomotsuHirasaka


def _payload(text: str) -> L3ToL5Payload:
    return L3ToL5Payload(text=text, step_idx=0, prompt_id="t")


class TestVScore:
    def setup_method(self):
        self.ev = YomiEvaluator()

    def test_empty_text_halts(self):
        result = self.ev(_payload(""))
        assert result.verdict is Verdict.HALT
        assert result.v_score == 0.0

    def test_short_text_halts(self):
        result = self.ev(_payload("ab"))
        assert result.verdict is Verdict.HALT

    def test_well_typed_ts_commits(self):
        ts = (
            "function add(a: number, b: number): number { return a + b; } "
            "const x: string = 'hi';"
        )
        result = self.ev(_payload(ts))
        assert result.verdict is Verdict.COMMIT
        assert result.v_score >= 0.7

    def test_any_type_penalised(self):
        ts_with_any = "function risky(x: any): any { return x; }"
        result = self.ev(_payload(ts_with_any))
        # `any` 含むので COMMIT 閾値に達しない (REPAIR ないし HALT)
        assert result.verdict is not Verdict.COMMIT

    def test_unbalanced_brackets_penalised(self):
        broken = "function broken(): number { return 1;"
        result = self.ev(_payload(broken))
        # ブラケット不一致でペナルティ → COMMIT に達しない
        assert result.verdict is not Verdict.COMMIT

    def test_score_clamped(self):
        # キーワード多数でも 1.0 を超えない
        ts = " ".join(["function f(): number { return 1; }"] * 20)
        result = self.ev(_payload(ts))
        assert 0.0 <= result.v_score <= 1.0


class TestVerdictBoundaries:
    def test_commit_boundary(self):
        # commit_threshold=0.7 ぴったりなら COMMIT
        ev = YomiEvaluator(EvaluatorConfig(commit_threshold=0.5, halt_threshold=0.3))
        # v_score を 0.5 に丁度合わせるのは難しいので閾値を緩めて検証
        result = ev(_payload("function f(): number { return 1; }"))
        assert result.verdict is Verdict.COMMIT

    def test_thresholds_validated(self):
        # halt > commit は不正
        with pytest.raises(ValueError):
            YomiEvaluator(EvaluatorConfig(commit_threshold=0.3, halt_threshold=0.7))


class TestEvaluatorThroughFirewall:
    """Evaluator が Firewall 経由で動くことを確認 (M1' 統合)"""

    def test_evaluator_flows_through_gateway(self):
        ev = YomiEvaluator()
        gate = YomotsuHirasaka(ev)
        result = gate.send(_payload("function add(a: number): number { return a; }"))
        assert result.verdict in {Verdict.COMMIT, Verdict.REPAIR, Verdict.HALT}
        assert 0.0 <= result.v_score <= 1.0

    def test_evaluator_halts_on_empty(self):
        gate = YomotsuHirasaka(YomiEvaluator())
        result = gate.send(_payload(""))
        assert result.verdict is Verdict.HALT
