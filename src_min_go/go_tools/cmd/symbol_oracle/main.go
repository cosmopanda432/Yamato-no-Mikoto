// Symbol Oracle daemon — Python decoder から stdio JSONL で query を受け、
// prompt + cursor から「現在 scope で参照可能なシンボル」を返す。
//
// 仕様: docs/symbol_oracle_contract.md (v0.1)
//
// 起動: `go run ./cmd/symbol_oracle` または `go build -o bin/symbol_oracle ./cmd/symbol_oracle`
// 通信: stdin から JSONL を 1 行ずつ読み、stdout に JSONL を 1 行ずつ書く。
package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"runtime"
	"time"

	"github.com/cosmopanda432/yamato-no-mikoto/src_min_go/go_tools/internal/oracle"
)

const (
	methodVersion  = "version"
	methodQuery    = "query"
	methodShutdown = "shutdown"
)

func main() {
	reader := bufio.NewReader(os.Stdin)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()

	for {
		line, err := reader.ReadString('\n')
		if err != nil {
			if err == io.EOF {
				// stdin が閉じられたら gracefully exit
				return
			}
			fatal(writer, "", oracle.ErrInternal, "read stdin: "+err.Error())
			return
		}
		// 末尾空白行は skip
		if len(line) == 1 && line[0] == '\n' {
			continue
		}

		var req oracle.Request
		if err := json.Unmarshal([]byte(line), &req); err != nil {
			writeResponse(writer, oracle.Response{
				ID: "", // request の ID が取れていないので空
				Error: &oracle.RPCError{
					Code:    oracle.ErrParseJSON,
					Message: "JSON parse error",
					Data:    map[string]any{"detail": err.Error()},
				},
			})
			continue
		}

		switch req.Method {
		case methodVersion:
			writeResponse(writer, oracle.Response{
				ID: req.ID,
				Result: map[string]any{
					"version":    oracle.Version,
					"go_version": runtime.Version(),
				},
			})
		case methodQuery:
			handleQuery(writer, req)
		case methodShutdown:
			writeResponse(writer, oracle.Response{
				ID:     req.ID,
				Result: map[string]any{"ok": true},
			})
			writer.Flush()
			return
		default:
			writeResponse(writer, oracle.Response{
				ID: req.ID,
				Error: &oracle.RPCError{
					Code:    oracle.ErrUnknownMethod,
					Message: "unknown method: " + req.Method,
				},
			})
		}
	}
}

func handleQuery(w *bufio.Writer, req oracle.Request) {
	// params の取り出し (defensive)
	prompt, _ := req.Params["prompt"].(string)
	cursorF, hasCursor := req.Params["cursor"].(float64)
	if !hasCursor {
		writeResponse(w, oracle.Response{
			ID: req.ID,
			Error: &oracle.RPCError{
				Code:    oracle.ErrParseJSON,
				Message: "missing required params.cursor (int)",
			},
		})
		return
	}
	cursor := int(cursorF)

	t0 := time.Now()
	res := oracle.Query(prompt, cursor)
	res.ElapsedMS = time.Since(t0).Milliseconds()

	writeResponse(w, oracle.Response{
		ID:     req.ID,
		Result: res.ToMap(),
	})
}

// writeResponse は JSONL の 1 行を書き出す。エラー時は stderr に panic 記録だけ
// 残し、daemon 自体は exit しない (= client が次の query を投げてきたら復旧する想定)。
func writeResponse(w *bufio.Writer, resp oracle.Response) {
	buf, err := json.Marshal(resp)
	if err != nil {
		fmt.Fprintf(os.Stderr, "marshal error: %v\n", err)
		return
	}
	buf = append(buf, '\n')
	if _, err := w.Write(buf); err != nil {
		fmt.Fprintf(os.Stderr, "write error: %v\n", err)
		return
	}
	w.Flush()
}

// fatal は最終手段。1 行書いて exit (現状未使用、将来の保険)。
func fatal(w *bufio.Writer, id string, code int, msg string) {
	writeResponse(w, oracle.Response{
		ID: id,
		Error: &oracle.RPCError{
			Code:    code,
			Message: msg,
		},
	})
}
