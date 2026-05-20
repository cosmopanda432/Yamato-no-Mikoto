package oracle

// BuiltinTypes は Go の組み込み型 (universe block) の名前。
// `go/types.Universe` でも取得できるが、安定した順序を保つために明示する。
// docs/symbol_oracle_contract.md の「stdlib primitives + builtin composite」相当。
var BuiltinTypes = []string{
	// numeric primitives
	"int", "int8", "int16", "int32", "int64",
	"uint", "uint8", "uint16", "uint32", "uint64", "uintptr",
	"float32", "float64",
	"complex64", "complex128",
	// other primitives
	"bool", "string", "byte", "rune",
	// universal interfaces / aliases
	"error", "any", "comparable",
}

// CompositionKeywords は Go の型 composition keyword (named type ではないが、
// 型 position に頻出する文法要素)。bias_builder はこれらを Types と同じ扱いで
// bias の対象にする。
//
// 2026-05-21 追加: mbpp-go full run で `[]interface{}` 系の position で、LM の
// top-1 が token `"interface"` なのに oracle の allowed (= Types ∪ Vars) に含まれ
// ず bias=0 のまま機能していなかった発見が動機 (修正 G)。`interface` / `struct` /
// `map` / `chan` / `func` は named type ではなく型を組み立てる keyword だが、
// 型 position の next token として頻出するため bias 対象に入れる必要がある。
//
// `func` は first-class function type (`func() int`) として型位置に来る。
var CompositionKeywords = []string{
	"interface",
	"struct",
	"map",
	"chan",
	"func",
}

// CommonStdlibTypes は import を必要とするが頻出する stdlib 型。
// query 時に「現 prompt が import している package」由来の型は ImportedNames で
// 補足するが、まだ import 文がない段階でも候補として混ぜたいシンボルをここに置く。
// **注意**: これは v0.1 のスタブで、本来は AST の import 宣言を見て解決すべき。
// ハードコードによる誤解釈を避けるため、デフォルトでは scope に **含めない**。
// 呼び出し側が明示的に opt-in する用途のための参考リスト。
var CommonStdlibTypes = []string{
	"io.Reader", "io.Writer", "io.Closer",
	"context.Context",
	"time.Time", "time.Duration",
	"sync.Mutex", "sync.WaitGroup",
	"fmt.Stringer",
	"http.Handler", "http.HandlerFunc",
}
