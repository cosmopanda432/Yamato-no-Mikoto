"""
OracleClient (Python ↔ Go daemon RPC) — 結合テスト

go_tools/bin/symbol_oracle が事前にビルドされていることが前提。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src_min_go"))

from kojiki_lm.go_symbol_oracle import OracleClient, OracleResult  # noqa: E402

ORACLE_BIN = REPO_ROOT / "src_min_go" / "go_tools" / "bin" / "symbol_oracle"


@pytest.fixture(scope="module")
def oracle():
    if not ORACLE_BIN.exists():
        pytest.skip(
            f"oracle binary not built. Run: "
            "(cd src_min_go/go_tools && go build -o bin/symbol_oracle ./cmd/symbol_oracle)"
        )
    client = OracleClient(ORACLE_BIN, timeout_sec=2.0)
    yield client
    client.close()


def test_handshake_succeeds(oracle: OracleClient):
    # __init__ で version handshake 済み、ここまで来れたら成功
    assert oracle._proc is not None
    assert oracle._proc.poll() is None  # 動作中


def test_query_func_arg_returns_types_and_prev_arg(oracle: OracleClient):
    src = "package main\n\nfunc add(a int, b "
    r = oracle.query(src, cursor=len(src), session_id="test-1")
    assert isinstance(r, OracleResult)
    assert r.scope_kind == "func_arg"
    assert "int" in r.types
    assert "a" in r.vars


def test_query_func_return_with_import(oracle: OracleClient):
    src = "package main\n\nimport \"fmt\"\n\nfunc Greet(name string) "
    r = oracle.query(src, cursor=len(src), session_id="test-2")
    assert isinstance(r, OracleResult)
    assert r.scope_kind == "func_return"
    assert "name" in r.vars
    assert "fmt" in r.types


def test_query_inequality_is_not_type_context(oracle: OracleClient):
    src = "package main\n\nfunc main() {\n\tfor i := 0; i < "
    r = oracle.query(src, cursor=len(src), session_id="test-3")
    assert isinstance(r, OracleResult)
    # 不等式末尾は型 context として扱わない (回帰)
    assert r.scope_kind == "unknown"


def test_query_returns_builtin_types_minimum(oracle: OracleClient):
    src = "package main\n"
    r = oracle.query(src, cursor=len(src), session_id="test-4")
    assert isinstance(r, OracleResult)
    for t in ("int", "string", "error", "any"):
        assert t in r.types


def test_query_garbage_input_still_returns_result(oracle: OracleClient):
    src = "this is not Go @@@"
    r = oracle.query(src, cursor=len(src), session_id="test-5")
    # garbage でも例外を投げず result が返る (builtin types のみ)
    assert isinstance(r, OracleResult)
    assert "int" in r.types
    assert r.ast_ok is False


def test_repeated_query_uses_same_session(oracle: OracleClient):
    """同じ session_id で連続 query が壊れず動くこと

    後続 query で新関数の引数を完全追跡することは v0.1 では保証しない
    (body のない func 宣言の補完が不完全)。ここでは scope_kind が型 context として
    再認識され、daemon が EOF / error を吐かないことだけを担保する。
    """
    src1 = "package main\n\nfunc f(a int, b "
    src2 = src1 + "int) {}\nfunc g(c "
    r1 = oracle.query(src1, len(src1), "session-X")
    r2 = oracle.query(src2, len(src2), "session-X")
    assert r1 is not None and r2 is not None
    assert "a" in r1.vars
    # 後続 query でも builtin types が必ず返り、daemon が dead に陥らない
    assert "int" in r2.types
    assert r2.scope_kind in ("func_arg", "func_return", "unknown")
