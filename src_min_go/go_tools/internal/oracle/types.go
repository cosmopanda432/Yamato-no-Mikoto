// Package oracle は Symbol Oracle daemon の RPC 型定義を提供する。
// 仕様: docs/symbol_oracle_contract.md (v0.1)
package oracle

// Version の semver (現状 v0.1)。
const Version = "0.1.0"

// JSON-RPC エラーコード (docs/symbol_oracle_contract.md より)。
const (
	ErrParseJSON     = -32700 // JSON 自体が壊れている
	ErrParseSource   = -32602 // Go source の parse 失敗で何も返せない
	ErrInternal      = -32603 // daemon 内部例外
	ErrTimeout       = -32001 // 50ms 超過
	ErrUnknownMethod = -32601 // 未対応 method
)

// Request は client (Python decoder) から受け取る JSONL の 1 行。
type Request struct {
	ID     string         `json:"id"`
	Method string         `json:"method"`
	Params map[string]any `json:"params,omitempty"`
}

// QueryParams は method="query" の params 部分。
type QueryParams struct {
	Prompt    string `json:"prompt"`
	Cursor    int    `json:"cursor"`
	SessionID string `json:"session_id"`
}

// Response は成功・エラーの両方を表現する。client は error が non-nil なら失敗扱い。
type Response struct {
	ID     string         `json:"id"`
	Result map[string]any `json:"result,omitempty"`
	Error  *RPCError      `json:"error,omitempty"`
}

// RPCError は JSON-RPC エラー object。
type RPCError struct {
	Code    int            `json:"code"`
	Message string         `json:"message"`
	Data    map[string]any `json:"data,omitempty"`
}

// QueryResult は method="query" の result 部分。
type QueryResult struct {
	Types     []string `json:"types"`
	Vars      []string `json:"vars"`
	ScopeKind string   `json:"scope_kind"`
	ASTOK     bool     `json:"ast_ok"`
	ElapsedMS int64    `json:"elapsed_ms"`
}

// ToMap は client が map[string]any として受け取りやすいように変換する。
func (r QueryResult) ToMap() map[string]any {
	return map[string]any{
		"types":      r.Types,
		"vars":       r.Vars,
		"scope_kind": r.ScopeKind,
		"ast_ok":     r.ASTOK,
		"elapsed_ms": r.ElapsedMS,
	}
}

// ScopeKind は QueryResult.ScopeKind の取り得る値。
const (
	ScopeFuncArg    = "func_arg"
	ScopeFuncReturn = "func_return"
	ScopeVarDecl    = "var_decl"
	ScopeConstDecl  = "const_decl"
	ScopeTypeAlias  = "type_alias"
	ScopeField      = "field"
	ScopeUnknown    = "unknown"
)
