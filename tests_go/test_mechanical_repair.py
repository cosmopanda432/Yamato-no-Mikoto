"""機械的 REPAIR (`goimports` 経由) のテスト

実 `goimports` バイナリが PATH に無くても fall back して exception を投げない
ことを確認するのが最低限。バイナリがある環境では実際の import 自動補完を検証。
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src_min_go"))

from kojiki_lm.mechanical_repair import RepairResult, goimports_repair  # noqa: E402


GOIMPORTS_AVAILABLE = shutil.which("goimports") is not None


class TestBinaryFallback:
    def test_missing_binary_returns_noop(self):
        """`goimports` バイナリが見つからない時、元 text を返して例外を投げない"""
        with patch("kojiki_lm.mechanical_repair.shutil.which", return_value=None):
            result = goimports_repair("package main\n", goimports_bin=None)
        assert isinstance(result, RepairResult)
        assert result.text == "package main\n"
        assert result.applied is False
        assert result.tool == "noop"
        assert "not found" in result.stderr

    def test_explicit_missing_binary(self):
        """明示的に存在しないパスを渡されても例外を出さず noop"""
        result = goimports_repair(
            "package main\n",
            goimports_bin="/no/such/binary/goimports-xyz",
        )
        # OSError 系を捕捉して noop result を返すこと
        assert isinstance(result, RepairResult)
        assert result.applied is False
        assert result.text == "package main\n"


@pytest.mark.skipif(not GOIMPORTS_AVAILABLE, reason="goimports not in PATH")
class TestGoImportsLive:
    """実 `goimports` バイナリが PATH にある環境のみ動作"""

    def test_no_changes_for_clean_code(self):
        """既に正しい import を持つコードは変更なし"""
        clean = (
            "package main\n\n"
            'import "fmt"\n\n'
            "func main() { fmt.Println(\"hi\") }\n"
        )
        result = goimports_repair(clean)
        assert result.tool == "goimports"
        # goimports は (もう正しいので) 変更なしか、空白整形のみ
        # applied は False か微小なフォーマット差で True。出力は valid な Go である
        assert "package main" in result.text
        assert "fmt" in result.text

    def test_missing_import_added(self):
        """使用されているが import されていない stdlib を自動補完"""
        broken = (
            "package main\n\n"
            "func main() { fmt.Println(\"hi\") }\n"
        )
        result = goimports_repair(broken)
        assert result.tool == "goimports"
        assert result.applied is True
        # `fmt` import が自動で挿入される
        assert '"fmt"' in result.text

    def test_unused_import_removed(self):
        """使われていない import が削除される"""
        with_unused = (
            "package main\n\n"
            'import "fmt"\n'
            'import "strings"\n\n'
            "func main() { fmt.Println(\"hi\") }\n"
        )
        result = goimports_repair(with_unused)
        assert result.tool == "goimports"
        assert result.applied is True
        # strings は使われていないので消える
        assert '"strings"' not in result.text
        # fmt は残る
        assert '"fmt"' in result.text

    def test_broken_syntax_returns_original(self):
        """構文エラーがあると goimports は非 0 で fail、元 text を返す"""
        broken_syntax = "package main\n\nfunc main() { this is not go }\n"
        result = goimports_repair(broken_syntax)
        # binary は存在するが処理失敗 → 元 text を返し applied=False
        assert result.tool == "goimports"
        assert result.applied is False
        assert result.text == broken_syntax
        # stderr に診断が乗ること (内容は環境依存なので非空のみ確認)
        assert len(result.stderr) > 0
