package oracle

import (
	"strings"
	"testing"
)

// contains は xs に target が含まれるかをテスト用に判定する。
func contains(xs []string, target string) bool {
	for _, x := range xs {
		if x == target {
			return true
		}
	}
	return false
}

// builtin (`int`/`string` 等) が全リクエストで返ることを担保。
func TestQuery_BuiltinTypesAlwaysPresent(t *testing.T) {
	r := Query("", 0)
	for _, want := range []string{"int", "string", "error", "any", "byte"} {
		if !contains(r.Types, want) {
			t.Errorf("missing builtin type %q in %v", want, r.Types)
		}
	}
}

// 関数引数の途中。`a` は宣言済み、`b` の型位置に居る。
//
//	package main
//	func add(a int, b _   ← cursor
func TestQuery_FuncArgPosition_PreviousArgInVars(t *testing.T) {
	src := "package main\n\nfunc add(a int, b "
	r := Query(src, len(src))
	if r.ScopeKind != ScopeFuncArg {
		t.Errorf("scope_kind: want %q, got %q", ScopeFuncArg, r.ScopeKind)
	}
	if !contains(r.Vars, "a") {
		t.Errorf("vars should contain previous arg 'a', got %v", r.Vars)
	}
}

// パッケージレベルの type 定義が同 file 内にある場合、その名前が types に入る。
// cursor は次の引数 (`q ` の型位置)、引数 `p` は既に declared。
func TestQuery_FuncArgPosition_UserTypeAndPreviousArg(t *testing.T) {
	src := `package main

type Point struct {
	X, Y int
}

func Distance(p Point, q `
	r := Query(src, len(src))
	if r.ScopeKind != ScopeFuncArg {
		t.Errorf("scope_kind: want %q, got %q", ScopeFuncArg, r.ScopeKind)
	}
	if !contains(r.Vars, "p") {
		t.Errorf("vars should contain previous arg 'p', got %v", r.Vars)
	}
	if !contains(r.Types, "Point") {
		t.Errorf("types should contain user-defined 'Point', got %v", r.Types)
	}
}

// 戻り値型の位置。`func Greet(name string) ` の `): ` 直後。
func TestQuery_FuncReturnPosition(t *testing.T) {
	src := "package main\n\nimport \"fmt\"\n\nfunc Greet(name string) "
	r := Query(src, len(src))
	if r.ScopeKind != ScopeFuncReturn {
		t.Errorf("scope_kind: want %q, got %q (src=%q)", ScopeFuncReturn, r.ScopeKind, src)
	}
	if !contains(r.Vars, "name") {
		t.Errorf("vars should contain func arg 'name', got %v", r.Vars)
	}
	if !contains(r.Types, "fmt") {
		t.Errorf("types should contain import name 'fmt', got %v", r.Types)
	}
}

// 変数宣言: `var x ` の型位置。
func TestQuery_VarDeclPosition(t *testing.T) {
	src := "package main\n\nfunc main() {\n\tvar x "
	r := Query(src, len(src))
	if r.ScopeKind != ScopeVarDecl {
		t.Errorf("scope_kind: want %q, got %q", ScopeVarDecl, r.ScopeKind)
	}
}

// for ループの不等式 `i < ` は type-context **ではない**。
// (TS 版で踏んだ偽陽性パターンの Go 版回帰テスト)
func TestQuery_InequalityIsNotTypeContext(t *testing.T) {
	src := "package main\n\nfunc main() {\n\tfor i := 0; i < "
	r := Query(src, len(src))
	if r.ScopeKind == ScopeFuncArg || r.ScopeKind == ScopeFuncReturn {
		t.Errorf("inequality must not be detected as type context; got %q", r.ScopeKind)
	}
}

// ローカル変数 + range は scope に入る。
func TestQuery_LocalVarsAndRange(t *testing.T) {
	src := `package main

func sum(xs []int) int {
	total := 0
	for _, x := range xs {
		total = total + x
		var y `
	r := Query(src, len(src))
	if !contains(r.Vars, "total") {
		t.Errorf("vars should contain local 'total', got %v", r.Vars)
	}
	if !contains(r.Vars, "x") {
		t.Errorf("vars should contain range-bound 'x', got %v", r.Vars)
	}
	if !contains(r.Vars, "xs") {
		t.Errorf("vars should contain func arg 'xs', got %v", r.Vars)
	}
}

// import がない場合に fmt 等が **混入しない** ことを保証。
// (ハードコード Stdlib types を勝手に混ぜていないか)
func TestQuery_NoImportNoStdlibLeak(t *testing.T) {
	src := "package main\n\nfunc main() {\n\tvar x "
	r := Query(src, len(src))
	for _, leaked := range []string{"fmt", "io", "os"} {
		if contains(r.Types, leaked) {
			t.Errorf("types should not contain %q without import, got %v", leaked, r.Types)
		}
	}
}

// パッケージ定義もない壊れた入力 → builtin だけ返って例外なし。
func TestQuery_BrokenInputStillReturnsBuiltins(t *testing.T) {
	src := "this is not Go code at all !@#$"
	r := Query(src, len(src))
	if len(r.Types) == 0 {
		t.Errorf("must always return builtin types, got empty")
	}
	if r.ASTOK {
		t.Errorf("ast_ok should be false for garbage input")
	}
}

// types の重複削除が安定動作することを担保。
func TestDedup(t *testing.T) {
	got := dedup([]string{"int", "string", "int", "bool", "string"})
	want := []string{"bool", "int", "string"}
	if strings.Join(got, ",") != strings.Join(want, ",") {
		t.Errorf("dedup: want %v, got %v", want, got)
	}
}
