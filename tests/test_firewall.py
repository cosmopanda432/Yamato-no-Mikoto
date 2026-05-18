"""M1' Firewall (yomotsu_hirasaka) の契約強制テスト"""

import pytest

from kojiki_lm.yomotsu_hirasaka import (
    L3ToL5Payload,
    L5ToL3Verdict,
    Verdict,
    YomotsuHirasaka,
)


class TestL3ToL5Payload:
    def test_valid_payload(self):
        p = L3ToL5Payload(text="hello", step_idx=0, prompt_id="p1")
        assert p.text == "hello"
        assert p.step_idx == 0

    def test_rejects_tensor_like_text(self):
        with pytest.raises(TypeError, match="text must be str"):
            L3ToL5Payload(text=[1, 2, 3], step_idx=0, prompt_id="p1")  # type: ignore[arg-type]

    def test_rejects_dict_text(self):
        with pytest.raises(TypeError, match="text must be str"):
            L3ToL5Payload(text={"hidden": 0.1}, step_idx=0, prompt_id="p1")  # type: ignore[arg-type]

    def test_rejects_non_int_step(self):
        with pytest.raises(TypeError, match="step_idx must be int"):
            L3ToL5Payload(text="x", step_idx=1.5, prompt_id="p1")  # type: ignore[arg-type]

    def test_rejects_negative_step(self):
        with pytest.raises(ValueError, match="step_idx must be >= 0"):
            L3ToL5Payload(text="x", step_idx=-1, prompt_id="p1")

    def test_frozen(self):
        p = L3ToL5Payload(text="x", step_idx=0, prompt_id="p1")
        with pytest.raises(Exception):  # dataclasses.FrozenInstanceError
            p.text = "tampered"  # type: ignore[misc]


class TestL5ToL3Verdict:
    def test_valid_verdict(self):
        v = L5ToL3Verdict(verdict=Verdict.COMMIT, v_score=0.8)
        assert v.verdict is Verdict.COMMIT
        assert v.v_score == 0.8

    def test_rejects_string_verdict(self):
        with pytest.raises(TypeError, match="verdict must be Verdict enum"):
            L5ToL3Verdict(verdict="commit", v_score=0.8)  # type: ignore[arg-type]

    def test_rejects_out_of_range_v_score(self):
        with pytest.raises(ValueError, match="v_score must be in"):
            L5ToL3Verdict(verdict=Verdict.COMMIT, v_score=1.5)
        with pytest.raises(ValueError, match="v_score must be in"):
            L5ToL3Verdict(verdict=Verdict.COMMIT, v_score=-0.1)

    def test_rejects_non_numeric_v_score(self):
        with pytest.raises(TypeError, match="v_score must be float"):
            L5ToL3Verdict(verdict=Verdict.COMMIT, v_score="0.5")  # type: ignore[arg-type]

    def test_rejects_extra_internal_state(self):
        # frozen dataclass なので未定義フィールドは渡せない (構造的隔離)
        with pytest.raises(TypeError):
            L5ToL3Verdict(  # type: ignore[call-arg]
                verdict=Verdict.COMMIT,
                v_score=0.8,
                archive_snapshot={"past": 1},
            )


class TestYomotsuHirasaka:
    def test_send_returns_verdict(self):
        def evaluator(p: L3ToL5Payload) -> L5ToL3Verdict:
            return L5ToL3Verdict(verdict=Verdict.COMMIT, v_score=0.9)

        gate = YomotsuHirasaka(evaluator)
        result = gate.send(L3ToL5Payload(text="x", step_idx=0, prompt_id="p"))
        assert result.verdict is Verdict.COMMIT

    def test_send_rejects_non_payload(self):
        gate = YomotsuHirasaka(lambda p: L5ToL3Verdict(Verdict.COMMIT, 0.9))
        with pytest.raises(TypeError, match="requires L3ToL5Payload"):
            gate.send("plain string")  # type: ignore[arg-type]

    def test_send_rejects_evaluator_returning_wrong_type(self):
        def bad_evaluator(p: L3ToL5Payload):
            # 内部状態を辞書で返そうとする (契約違反)
            return {"verdict": "commit", "archive": [1, 2, 3]}

        gate = YomotsuHirasaka(bad_evaluator)  # type: ignore[arg-type]
        with pytest.raises(TypeError, match="must return L5ToL3Verdict"):
            gate.send(L3ToL5Payload(text="x", step_idx=0, prompt_id="p"))

    def test_init_rejects_non_callable(self):
        with pytest.raises(TypeError, match="callable evaluator"):
            YomotsuHirasaka(evaluator="not_callable")  # type: ignore[arg-type]
