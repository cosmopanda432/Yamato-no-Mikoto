package oracle

import (
	"go/ast"
	"go/parser"
	"go/token"
	"regexp"
	"sort"
	"strings"
)

// scope_kind 判定用の末尾パターン。AST 補完が信頼できない場面 (戻り値型位置で
// 補完がはまらない等) では regex で補完する。TS 版の偽陽性教訓 (ジェネリック
// `<` を不等式と誤認、三項 `:` を戻り値型と誤認) は Go では発生しない:
//   - Go にはジェネリックの `<>` 構文がない (`[T any]` を使う)
//   - Go には三項演算子がない (`a ? b : c` は構文エラー)
//
//	`)\s+$`         → func_return (引数閉じ後の空白)
//	`var\s+\w+\s+$` → var_decl
//	`const\s+\w+\s+$` → const_decl
// 注意: Qwen BPE は token に前置空白を含むため、decode 中の text_buffer は
// `var result` (空白なし末尾) で 1 step 止まることが typical。Python 側 filter
// と歩調を合わせ、ここでも `\s*$` (0 個以上の末尾空白) を使う。
var (
	reFuncReturn = regexp.MustCompile(`\)\s*$`)
	reVarDecl    = regexp.MustCompile(`\bvar\s+\w+\s*$`)
	reConstDecl  = regexp.MustCompile(`\bconst\s+\w+\s*$`)
	// 不等式 `i <`, `x <`, `len(s) <` を偽陽性で食わないことを担保。
	// (Go では `<` を「ジェネリック」と誤認することはないので影響は限定的だが
	//  decode 時のロバスト性のため明示する。)
	reInequalityTail = regexp.MustCompile(`[a-zA-Z0-9_)\]]\s*[<>]=?\s*$`)

	// 2026-05-21 追加: 「難所」型位置の regex 検出 (Python 側 kotodama_context.py と同期)
	reChanElem        = regexp.MustCompile(`\bchan\s*$|<-chan\s*$|\bchan<-\s*$`)
	reMapKey          = regexp.MustCompile(`\bmap\[\s*$`)
	reMapVal          = regexp.MustCompile(`\bmap\[\w+\]\s*$|\bmap\[\[\]\w+\]\s*$`)
	reSliceElem       = regexp.MustCompile(`(?:^|[^\w\)])\[\]\s*$|\b\[\d+\]\s*$`)
	reInterfaceMethod = regexp.MustCompile(`\binterface\s*\{[^}]*\)\s*$`)
	reTypeAssert      = regexp.MustCompile(`\)\s*\.\(\s*$|\w\.\(\s*$`)
	reStructField     = regexp.MustCompile(`\bstruct\s*\{[^}]*\b\w+\s*$`)
)

// Query は prompt[:cursor] を Go source として解析し、その位置で参照可能な
// シンボル集合 (types ∪ vars) を返す。
//
// AST がそのままでは parse できないことが大半 (decode 中の prompt は途中)。
// 末尾を best-effort で補完して再試行する。完全失敗時は builtin types のみを返す。
//
// 仕様: docs/symbol_oracle_contract.md (v0.1)
func Query(prompt string, cursor int) QueryResult {
	src := prompt
	if cursor >= 0 && cursor <= len(prompt) {
		src = prompt[:cursor]
	}

	result := QueryResult{
		Types:     append([]string{}, BuiltinTypes...),
		Vars:      []string{},
		ScopeKind: ScopeUnknown,
		ASTOK:     false,
	}

	fset := token.NewFileSet()
	astFile, astOK := tryParse(fset, src)
	result.ASTOK = astOK

	if astFile == nil {
		// 完全失敗: builtin types のみ返す (best-effort 仕様)
		result.Types = dedup(result.Types)
		return result
	}

	collectPackageScope(astFile, &result)

	// cursor を含む関数を見つけて、その引数とローカル var を加える
	cursorPos := token.Pos(len(src) + 1) // ast の Pos は 1-origin
	if fd := findEnclosingFunc(astFile, cursorPos); fd != nil {
		collectFuncScope(fd, cursorPos, &result)
		result.ScopeKind = detectScopeKind(fd, cursorPos, src)
	}

	result.Types = dedup(result.Types)
	result.Vars = dedup(result.Vars)
	return result
}

// tryParse は src の末尾を補完しながら parse を試みる best-effort。
// 返り値: AST file (nil なら完全失敗), AST が補完なしで通ったか (= ast_ok)。
func tryParse(fset *token.FileSet, src string) (*ast.File, bool) {
	// 補完戦略の優先順:
	//   1. そのまま
	//   2. 末尾に `\n}\n`   (関数本体の中で止まっている)
	//   3. 末尾に `int)\n}\n` (引数リストの型位置で止まっている)
	//   4. 末尾に `int\n}\n`  (式途中)
	//   5. package 宣言だけ抜き出す
	candidates := []struct {
		suffix string
		clean  bool // 補完なし = ast_ok true
	}{
		{"", true},
		{"\n}\n", false},
		{"int)\n}\n", false},
		{"int\n}\n", false},
		{")\n}\n", false},
	}
	for _, c := range candidates {
		attempt := src + c.suffix
		f, err := parser.ParseFile(fset, "src.go", attempt, parser.AllErrors)
		if f != nil && err == nil {
			return f, c.clean
		}
		if f != nil && len(f.Decls) > 0 {
			// 部分的にでも decls が取れていれば使う (= ast_ok=false で返す)
			return f, false
		}
	}

	// 最後の砦: package 宣言行だけ取り出して parse
	pkgIdx := strings.Index(src, "package ")
	if pkgIdx >= 0 {
		if nl := strings.IndexByte(src[pkgIdx:], '\n'); nl > 0 {
			fake := src[pkgIdx:pkgIdx+nl] + "\n"
			if f, err := parser.ParseFile(fset, "src.go", fake, 0); err == nil && f != nil {
				return f, false
			}
		}
	}

	return nil, false
}

// collectPackageScope は file の top-level decls から types/vars/imports を集める。
func collectPackageScope(file *ast.File, result *QueryResult) {
	for _, decl := range file.Decls {
		gd, ok := decl.(*ast.GenDecl)
		if !ok {
			continue
		}
		for _, spec := range gd.Specs {
			switch s := spec.(type) {
			case *ast.TypeSpec:
				if s.Name != nil {
					result.Types = append(result.Types, s.Name.Name)
				}
			case *ast.ValueSpec:
				for _, name := range s.Names {
					if name.Name != "_" {
						result.Vars = append(result.Vars, name.Name)
					}
				}
			case *ast.ImportSpec:
				name := importPackageName(s)
				if name != "" {
					// パッケージ名は型 namespace として参照されるため types 側に入れる
					result.Types = append(result.Types, name)
				}
			}
		}
	}
}

// importPackageName は ImportSpec から package 名を取り出す。
// `import foo "x/y/z"` なら "foo"、 `import "x/y/z"` なら "z"。
func importPackageName(s *ast.ImportSpec) string {
	if s.Name != nil && s.Name.Name != "" && s.Name.Name != "_" {
		return s.Name.Name
	}
	if s.Path == nil {
		return ""
	}
	path := strings.Trim(s.Path.Value, `"`)
	if path == "" {
		return ""
	}
	segs := strings.Split(path, "/")
	return segs[len(segs)-1]
}

// findEnclosingFunc は cursor を含む func decl を返す (なければ nil)。
func findEnclosingFunc(file *ast.File, cursor token.Pos) *ast.FuncDecl {
	var enclosing *ast.FuncDecl
	for _, decl := range file.Decls {
		fd, ok := decl.(*ast.FuncDecl)
		if !ok {
			continue
		}
		// 補完で本体が膨らんでいる可能性があるので End() による厳密判定はしない。
		// Pos() <= cursor の最後の func を採用する。
		if fd.Pos() <= cursor {
			enclosing = fd
		}
	}
	return enclosing
}

// collectFuncScope は cursor 以前で declare された引数とローカル var を集める。
func collectFuncScope(fd *ast.FuncDecl, cursor token.Pos, result *QueryResult) {
	// 引数 (receivers + params)
	for _, fl := range []*ast.FieldList{fd.Recv, fd.Type.Params} {
		if fl == nil {
			continue
		}
		for _, field := range fl.List {
			for _, name := range field.Names {
				if name.Name != "_" && name.Pos() < cursor {
					result.Vars = append(result.Vars, name.Name)
				}
			}
		}
	}

	if fd.Body == nil {
		return
	}

	// 本体の cursor 以前で declare された var/const/short-var/range
	ast.Inspect(fd.Body, func(n ast.Node) bool {
		if n == nil {
			return false
		}
		if n.Pos() >= cursor {
			return false
		}
		switch s := n.(type) {
		case *ast.AssignStmt:
			// `x := ...` の左辺だけ拾う (代入 `=` ではなく `:=` のみ)
			if s.Tok == token.DEFINE {
				for _, lhs := range s.Lhs {
					if id, ok := lhs.(*ast.Ident); ok && id.Name != "_" {
						result.Vars = append(result.Vars, id.Name)
					}
				}
			}
		case *ast.DeclStmt:
			if gd, ok := s.Decl.(*ast.GenDecl); ok {
				for _, spec := range gd.Specs {
					if vs, ok := spec.(*ast.ValueSpec); ok {
						for _, name := range vs.Names {
							if name.Name != "_" {
								result.Vars = append(result.Vars, name.Name)
							}
						}
					}
				}
			}
		case *ast.RangeStmt:
			for _, expr := range []ast.Expr{s.Key, s.Value} {
				if id, ok := expr.(*ast.Ident); ok && id.Name != "_" {
					result.Vars = append(result.Vars, id.Name)
				}
			}
		}
		return true
	})
}

// detectScopeKind は cursor がどの構文位置にあるかを判定する。
// 戦略: 偽陽性ガード (不等式の末尾) → 難所 regex → AST ベース → 既存 regex fallback。
//
// 2026-05-21 更新: mbpp-go ablation で func_arg / func_return では LM がほぼ確実に
// 正解を出すため bias 無意味と判明。難所 (複合型 elem 位置) を**先に**判定し、
// func_arg / func_return より優先する。
func detectScopeKind(fd *ast.FuncDecl, cursor token.Pos, src string) string {
	// 偽陽性ガード: 末尾が比較演算 (`<`, `>`, `<=`, `>=`) なら絶対に型 context ではない
	if reInequalityTail.MatchString(src) {
		return ScopeUnknown
	}

	// 難所 regex を先に判定 (より具体的なパターンが優先)
	if reChanElem.MatchString(src) {
		return ScopeChanElem
	}
	if reMapKey.MatchString(src) {
		return ScopeMapKey
	}
	if reMapVal.MatchString(src) {
		return ScopeMapVal
	}
	if reSliceElem.MatchString(src) {
		return ScopeSliceElem
	}
	if reInterfaceMethod.MatchString(src) {
		return ScopeInterfaceMethod
	}
	if reTypeAssert.MatchString(src) {
		return ScopeTypeAssert
	}
	if reStructField.MatchString(src) {
		return ScopeStructField
	}

	// AST ベース: fd.Type.Params の `(...)` 内に cursor があるか
	// (Python 側 filter は func_arg を除外しているので通常ここには来ないが、
	//  defense-in-depth として残す。届いた場合は bias は無害だが効果も期待しない)
	if fd.Type.Params != nil {
		op, cl := fd.Type.Params.Opening, fd.Type.Params.Closing
		if op != token.NoPos && cursor > op && cursor <= cl {
			return ScopeFuncArg
		}
	}
	// AST ベース: 戻り値型 (Results が `(...)` 形式)
	if fd.Type.Results != nil {
		res := fd.Type.Results
		if res.Opening != token.NoPos && cursor > res.Opening && cursor <= res.Closing {
			return ScopeFuncReturn
		}
	}

	// regex fallback: 補完で戻り値型の AST まで届かないケース (補完戦略の制約)
	if reFuncReturn.MatchString(src) {
		return ScopeFuncReturn
	}
	if reVarDecl.MatchString(src) {
		return ScopeVarDecl
	}
	if reConstDecl.MatchString(src) {
		return ScopeConstDecl
	}

	return ScopeUnknown
}

// dedup はソート + 重複削除して安定した順序を保証する。
func dedup(xs []string) []string {
	if len(xs) == 0 {
		return xs
	}
	sorted := append([]string{}, xs...)
	sort.Strings(sorted)
	out := sorted[:0]
	for i, x := range sorted {
		if i == 0 || x != sorted[i-1] {
			out = append(out, x)
		}
	}
	return out
}
