"""
Symbol Oracle RPC client (Python side)

go_tools/cmd/symbol_oracle daemon に stdio JSONL でリクエストを送る薄い client。
仕様は docs/symbol_oracle_contract.md (v0.1)。

責務:
  - subprocess.Popen で daemon プロセスを起動・管理する
  - 1 query を JSON で送り、1 response を受け取る
  - timeout / daemon クラッシュ時は **None を返す** (decoder 側で bias 加算 skip)
  - 起動直後に version method を呼んでバージョン整合を確認
"""

from __future__ import annotations

import json
import logging
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

EXPECTED_MAJOR = "0.1"  # daemon と整合する semver の major.minor


@dataclass(frozen=True)
class OracleResult:
    """oracle daemon の `query` 戻り値 (成功時)"""
    types: tuple[str, ...]
    vars: tuple[str, ...]
    scope_kind: str
    ast_ok: bool
    elapsed_ms: int


class OracleClient:
    """daemon と 1:1 で stdio 通信する client

    使い方:
        with OracleClient(Path("bin/symbol_oracle")) as oracle:
            r = oracle.query("func add(a int, b ", cursor=18, session_id="s1")
            if r is not None:
                logger.info("types=%s", r.types)

    decoder 側は r is None のとき bias 加算を skip (= vanilla 同等で続行) する。
    """

    def __init__(
        self,
        oracle_bin: Path,
        timeout_sec: float = 0.5,
        max_restart: int = 3,
    ) -> None:
        self.oracle_bin = Path(oracle_bin)
        self.timeout_sec = timeout_sec
        self.max_restart = max_restart

        self._proc: subprocess.Popen | None = None
        self._restart_count = 0
        self._disabled = False  # 再起動上限に達した後は permanent OFF
        self._start()

    # --- subprocess lifecycle ---

    def _start(self) -> None:
        if not self.oracle_bin.exists():
            raise FileNotFoundError(
                f"symbol_oracle binary not found at {self.oracle_bin}. "
                "Build it with: (cd src_min_go/go_tools && go build -o bin/symbol_oracle ./cmd/symbol_oracle)"
            )
        logger.info("Starting symbol_oracle daemon: %s", self.oracle_bin)
        self._proc = subprocess.Popen(
            [str(self.oracle_bin)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # line-buffered
        )
        # ハンドシェイク: version を投げて整合確認
        v = self._raw_call({"id": "init", "method": "version"})
        if v is None or v.get("error") is not None:
            raise RuntimeError(f"version handshake failed: {v}")
        ver = v.get("result", {}).get("version", "")
        if not ver.startswith(EXPECTED_MAJOR):
            logger.warning(
                "oracle version mismatch: client expects %s.x, daemon says %s",
                EXPECTED_MAJOR, ver,
            )
        logger.info(
            "oracle ready: daemon=%s, go=%s",
            ver, v.get("result", {}).get("go_version", "?"),
        )

    def _restart(self) -> bool:
        """daemon を再起動。上限を超えていたら False を返して以後 permanent OFF"""
        if self._restart_count >= self.max_restart:
            logger.error(
                "oracle restart limit (%d) reached; disabling bias permanently",
                self.max_restart,
            )
            self._disabled = True
            return False
        self._restart_count += 1
        self._stop()
        try:
            self._start()
            return True
        except Exception as e:
            logger.error("oracle restart %d failed: %s", self._restart_count, e)
            self._disabled = True
            return False

    def _stop(self) -> None:
        if self._proc is None:
            return
        try:
            if self._proc.stdin is not None:
                self._proc.stdin.close()
        except Exception:
            pass
        try:
            self._proc.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            self._proc.kill()
        self._proc = None

    def close(self) -> None:
        if self._proc is None or self._disabled:
            return
        # shutdown を送って gracefully stop
        try:
            self._raw_call({"id": "bye", "method": "shutdown"})
        except Exception:
            pass
        self._stop()

    def __enter__(self) -> "OracleClient":
        return self

    def __exit__(self, *_) -> None:
        self.close()

    # --- request/response ---

    def _raw_call(self, req: dict) -> dict | None:
        """1 line JSONL を送って 1 line を取る。失敗時 None"""
        if self._proc is None or self._proc.stdin is None or self._proc.stdout is None:
            return None
        try:
            line = json.dumps(req, ensure_ascii=False) + "\n"
            self._proc.stdin.write(line)
            self._proc.stdin.flush()
        except (BrokenPipeError, OSError) as e:
            logger.warning("oracle write failed: %s", e)
            return None

        # readline は blocking。timeout は select で実装すべきだが、ここでは
        # daemon が短時間で必ず 1 行返す前提なのと、Python の subprocess pipe で
        # OS レベル timeout を強制するのが面倒なため、簡略化して blocking。
        # daemon クラッシュ時は readline が EOF → 空文字を返す。
        t0 = time.monotonic()
        try:
            resp_line = self._proc.stdout.readline()
        except Exception as e:
            logger.warning("oracle read failed: %s", e)
            return None
        elapsed = time.monotonic() - t0

        if not resp_line:
            # EOF = daemon が exit したかクラッシュ
            logger.warning("oracle returned EOF (likely crashed)")
            return None

        if elapsed > self.timeout_sec:
            logger.warning(
                "oracle slow response: %.3fs > %.3fs (id=%s)",
                elapsed, self.timeout_sec, req.get("id"),
            )

        try:
            return json.loads(resp_line)
        except json.JSONDecodeError as e:
            logger.warning("oracle returned non-JSON: %s | line=%r", e, resp_line[:200])
            return None

    def query(
        self,
        prompt: str,
        cursor: int,
        session_id: str,
    ) -> OracleResult | None:
        """oracle に scope を問い合わせる。失敗時 None"""
        if self._disabled:
            return None

        req_id = uuid.uuid4().hex
        req = {
            "id": req_id,
            "method": "query",
            "params": {
                "prompt": prompt,
                "cursor": cursor,
                "session_id": session_id,
            },
        }
        resp = self._raw_call(req)
        if resp is None:
            # daemon クラッシュ可能性、再起動を試す
            if self._restart():
                # 再起動成功、改めて 1 回だけ送り直す
                resp = self._raw_call(req)
            if resp is None:
                return None

        if "error" in resp and resp["error"] is not None:
            err = resp["error"]
            logger.warning(
                "oracle returned error code=%s msg=%s",
                err.get("code"), err.get("message"),
            )
            return None

        result = resp.get("result", {})
        try:
            return OracleResult(
                types=tuple(result["types"]),
                vars=tuple(result["vars"]),
                scope_kind=result.get("scope_kind", "unknown"),
                ast_ok=bool(result.get("ast_ok", False)),
                elapsed_ms=int(result.get("elapsed_ms", -1)),
            )
        except (KeyError, TypeError) as e:
            logger.warning("oracle response malformed: %s | %s", e, result)
            return None
