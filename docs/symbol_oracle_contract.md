# Symbol Oracle RPC Contract — v0.1

`src_min_go/kojiki_lm/kotodama_decoder.py` (Python decode loop, **client**) ↔
`src_min_go/go_tools/cmd/symbol_oracle/` (Go daemon, **server**) の RPC 通信仕様。

言霊 v2 の核心: 「decode 中、type-annotation 位置に到達したら、その scope で
**参照可能なシンボル (types ∪ vars)** を Go AST + 型情報から取り出し、
対応する BPE first-token に **logit `+k` の bias** を加算する」。

## 役割と非役割

### 役割 (v0.1 で必ず満たす)

- prompt + cursor position から、その位置で **named entity として参照可能な
  シンボル名 (string) のリスト** を返す
- 名前のみを返す (型の構造分析や代入可能性判定はしない)
- 失敗時は空集合を返す (= 言霊 OFF と同等にフォールバック)、例外で decode を止めない

### 非役割 (v0.1 では明示的にやらない)

- ジェネリクス型パラメータ (`func F[T any]` の `T`) のスコープ追跡 — v0.2 で対応
- methods / channel ops / closure capture の scope-aware 解析 — v0.2 で対応
- 候補シンボルの **ランキング** や **確率** — Python 側で TypeHead と AND する想定
- prompt の syntactic validity 保証 — broken AST でも best-effort で何か返す

## いつ呼ばれるか (call site)

Python `kotodama_decoder.py` の decode ループ内で、**以下の AND 条件** を満たす step
**のみ** で 1 query 発行する:

1. `kotodama_context.is_type_annotation_position(text_buffer)` が True
2. その step で前回 query から **prompt prefix が伸びている** (= incremental update が必要)
3. ablation flag `mask_enabled=True`

token ごとに query しない (= 1 prompt あたり数回〜数十回の呼び出し)。これが
性能要件 (後述) を満たす前提。

## プロトコル

stdio JSONL (line-delimited JSON)。1 request 1 行、1 response 1 行。

### Request

```json
{
  "id": "01HF8...",
  "method": "query",
  "params": {
    "prompt": "package main\n\nfunc add(a int, b ",
    "cursor": 31,
    "session_id": "humaneval-go-001/seed-0"
  }
}
```

| Field | Type | 必須 | 説明 |
|---|---|---|---|
| `id` | string | ✅ | UUID v7 等の単調増加 ID。response でエコー |
| `method` | string | ✅ | `"query"` のみ (v0.1)。将来 `"shutdown"`, `"stats"` を追加 |
| `params.prompt` | string | ✅ | UTF-8 source code の prefix。cursor 位置までの全文 |
| `params.cursor` | int | ✅ | バイト offset (UTF-8 ベース)。`prompt[:cursor]` がパース対象 |
| `params.session_id` | string | ✅ | 1 prompt 1 セッション。daemon 側で incremental cache 用 |

`cursor` が `len(prompt)` と等価な場面が大半 (decode 末尾). 将来 prompt 末尾以外で
query したい用途のために独立フィールドにしている。

### Response (成功)

```json
{
  "id": "01HF8...",
  "result": {
    "types": ["int", "int8", "int16", "int32", "int64",
              "uint", "uint8", "uint16", "uint32", "uint64",
              "float32", "float64", "bool", "string", "byte", "rune",
              "error", "any",
              "Point", "Handler"],
    "vars": ["a"],
    "scope_kind": "func_arg",
    "ast_ok": true,
    "elapsed_ms": 12
  }
}
```

| Field | Type | 説明 |
|---|---|---|
| `result.types` | string[] | scope で参照可能な型名 (primitive + stdlib + user-defined struct/interface/type alias) |
| `result.vars` | string[] | scope で参照可能な変数名 (引数 + ローカル変数 + 同 package の top-level vars/consts) |
| `result.scope_kind` | string | `"func_arg"` / `"func_return"` / `"var_decl"` / `"const_decl"` / `"type_alias"` / `"field"` / `"unknown"` |
| `result.ast_ok` | bool | AST 全体がパースできたか。false の場合は best-effort 結果 |
| `result.elapsed_ms` | int | サーバ側処理時間 (デバッグ用) |

**types / vars の同一性**: scope_kind が `func_arg` や `func_return` のときは型位置
なので `vars` が空でも valid (= Python 側は types のみを bias 対象に使う想定)。
`var_decl` のときは右辺で literal や式が来る可能性があるので `vars` も bias 対象に
加えうる。

### Response (エラー)

```json
{
  "id": "01HF8...",
  "error": {
    "code": -32602,
    "message": "ParseError",
    "data": {"detail": "expected '{', got EOF", "line": 5}
  }
}
```

| Code | Message | 意味 | client の対応 |
|---|---|---|---|
| -32700 | ParseError | JSON-RPC 自体の parse 失敗 | daemon 再起動 |
| -32602 | ParseError | Go source の parse 失敗で何も返せない | bias 加算 skip、decode 続行 |
| -32603 | InternalError | daemon 内部例外 (panic 等) | daemon 再起動 + skip |
| -32001 | Timeout | 50ms 内に処理完了せず | skip + 統計記録 |

エラー時、**Python 側は decode を止めず**、その step の言霊 bias を skip (= vanilla
として続行) する。エラー多発時は metrics に記録して後で分析。

## スコープルール (v0.1)

### 含むもの

- **現在の関数** のローカル変数 (cursor 位置 **以前** で declared されたもの)
- **現在の関数** の引数 (cursor 以前に出てきたもの)
- **現在の package** の top-level types (struct / interface / type alias)
- **現在の package** の top-level vars / consts
- **import された package** の **exported names** (シンボル単位のみ、深い API 解析なし)
  - 例: `import "strings"` で `strings.Builder`, `strings.HasPrefix` 等が types/vars に入る
  - **ドット表記での扱い**: prompt に `strings.` が直前にあるとき、types/vars は
    その package の exported names に絞る (v0.2 で精緻化、v0.1 では package 修飾を
    分離せず全て fully-qualified name で返す)

### 含まないもの (v0.1 で意図的に除外)

- **ジェネリクス型パラメータ** (`func F[T any]` の `T`)
- **methods** (receiver type に紐付くので scope は別 query が必要)
- **closure capture** (closure 内の captured vars は親関数 scope を引き継ぐが、v0.1 は
  関数ごとに切る)
- **未参照の package import** (パースは通るが scope には入らない)

## キャッシュ戦略

### Session ベース incremental

`session_id` 単位で daemon は以下を保持:

```go
type SessionCache struct {
    lastPrompt   string             // 前回 query 時の prompt
    fileSet      *token.FileSet     // 共通 fileset
    parsedFile   *ast.File          // ベースの AST (= 関数定義などの大枠)
    typesInfo    *types.Info        // 型情報
    parsedUpTo   int                // どこまで成功して parse できたか (byte offset)
}
```

各 query で `params.prompt` を `lastPrompt` と比較:

1. `lastPrompt` が `params.prompt` の **prefix** であれば **incremental update**:
   差分部分のみを再 parse、AST を継ぎ足す。最頻ケース (decode 中の連続 query)
2. それ以外 (新しい session / prompt が分岐した) は full re-parse

### キャッシュサイズ

- 最大 64 session、LRU で eviction
- 1 session あたりメモリ ~1 MB を想定 (typical な HumanEval-Go 問題で AST + types info)

### キャッシュ無効化

- 明示的: `method: "invalidate"` (v0.1 では未実装、v0.2 で追加検討)
- 暗黙的: session_id 一致 + prompt が前回の prefix でない → full re-parse

## 失敗モード (best-effort 戦略)

### 1. prompt が syntactically broken

```go
func add(a int, b in    // ← `in` まで生成、`int` を期待
```

戦略 (優先順):

1. **末尾を補完してパース試行**: `int)` を仮で補完してパース。失敗したら次
2. **行頭まで戻して再パース**: 最後の関数定義の `{` までを切り出してパース
3. **package level だけパース**: トップレベルの type 定義は取れる、ローカル scope
   は空集合
4. **完全失敗**: 空集合を返す (`ast_ok: false`)

### 2. daemon クラッシュ

Python client は:
- 3 秒タイムアウトで再起動
- 再起動回数を session 単位でカウント、3 回失敗で **言霊 OFF に降格** (decode 続行)
- metrics に記録

### 3. パース成功だが types check 失敗

`go/types` は前方参照や cross-file dependency があると失敗することがある。
v0.1 は **AST のみで動く scope walk** を主、`go/types` は補助:

- AST 走査で取れる名前 (引数、ローカル var/const decl、トップレベル struct/type
  alias) は **必ず scope に含める**
- `go/types` で取れる情報 (型の解決、import package の exported names) は
  **取れたら追加**、失敗してもエラーにしない

## 性能要件 (v0.1)

| 項目 | 目標 | 計測方法 |
|---|---|---|
| 1 query の P95 latency | < 50 ms | 1000 query 統計 |
| 1 query の P50 latency | < 10 ms | 同上 |
| daemon 起動時間 | < 500 ms | cold start から first response |
| メモリ常駐 | < 200 MB (64 session 時) | RSS 計測 |
| decode 全体への overhead | < 5% | full mode vs vanilla の生成時間比 |

P95 50ms は decode 1 token あたり <0.5ms オーバーヘッド (100 token 中 1 回 query
する想定) を目標。1 token あたり LM forward は 10-30ms なので、相対的に十分小さい。

## 接続管理

### 起動

Python `go_symbol_oracle.py` の `OracleClient.__init__` で `subprocess.Popen`:

```python
self.proc = subprocess.Popen(
    [str(oracle_bin)],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,  # line-buffered
)
```

`oracle_bin` は `src_min_go/go_tools/bin/symbol_oracle` (ビルド済バイナリ)。

### Shutdown

- 明示的: `method: "shutdown"` を送る (response 後に daemon が exit)
- 暗黙的: Python 終了時 `proc.stdin.close()` → daemon は EOF を検知して exit
- SIGTERM 受信: graceful shutdown (進行中の query を完了させてから exit)

### Concurrency

v0.1 は **1 daemon = 1 client = serial**。複数 prompt の並列処理は v0.2 以降で
session_id 単位の concurrent query を許可する。

## バージョニング

| Version | 機能 |
|---|---|
| **v0.1** (今) | types + vars (関数 scope + package top-level + import exported names), incremental cache, JSONL stdio |
| v0.2 (将来) | generics scope, methods (receiver-aware), channel ops, package-qualified resolution の精緻化, concurrent session |
| v0.3 (将来) | 型互換性判定 (`assignable_to`), method set, interface satisfaction |

`method: "version"` で daemon が自分のバージョンを返す:

```json
{"id": "...", "result": {"version": "0.1.0", "go_version": "go1.23.0"}}
```

## ハンドシェイク

Python client は起動直後に必ず `version` query を 1 回打つ。バージョン mismatch
ならフォールバック (= 言霊 OFF) + ログに警告。

## クライアント側 (Python) のインターフェース (参考)

```python
class OracleClient:
    def __init__(self, oracle_bin: Path, timeout_ms: int = 50) -> None: ...

    def query(
        self,
        prompt: str,
        cursor: int,
        session_id: str,
    ) -> OracleResult | None:
        """成功時 OracleResult、失敗時 None (caller は bias 加算を skip)"""

    def close(self) -> None:
        """gracefully shutdown daemon"""


@dataclass(frozen=True)
class OracleResult:
    types: tuple[str, ...]
    vars: tuple[str, ...]
    scope_kind: str
    ast_ok: bool
    elapsed_ms: int
```

## 関連

- ロードマップ: [roadmap_min_go.md](roadmap_min_go.md)
- TS 版で得た教訓 (なぜ -inf mask が失敗したか): メモリ `feedback-kotodama-mask-counterproductive`
- Go 言語仕様: [Go specification — Scopes](https://go.dev/ref/spec#Declarations_and_scope)
- 参照実装候補: `golang.org/x/tools/go/packages` (本格的なパッケージロード)、
  ただし v0.1 は `go/parser` + `go/types` で十分なので導入しない
