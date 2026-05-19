# Roadmap (Minimum) — yamatoLLM Go 版

Win Condition (**baseline 比 `go build` 成功率 +5pp / undefined-symbol 出現率 ×0.5**)
に最短到達するための Go ターゲット版。TS 版 ([docs/roadmap_min.md](roadmap_min.md))
で「言霊マスク (−inf 強制) は逆効果」が実測で確定したのを受け、その教訓を骨格に組み込む。

## なぜ TS から Go へ

TS 版の 3 mode ablation (humaneval-ts, A6000 bf16, N=159) 結果:

| Mode | pass@1 | tsc strict | TS2304 halluc |
|---|---|---|---|
| baseline (step2000) | 74.84% | 91.19% | 5.03% |
| vanilla (mask=off, fw=off) | **77.36%** | **94.34%** | **3.77%** |
| no-firewall (mask=on, fw=off) | 59.75% | 69.81% | 14.47% |
| full (mask=on, fw=on) | 59.75% | 66.04% | 13.84% |

判明したこと:

1. **言霊マスク (-inf 物理印加) が逆効果**: 同じ Stage 2 ヘッドを使っても、マスクとして
   強制した瞬間 vanilla 比 tsc −24.5pp / hallucination ×3.84 に悪化。原因は TS 型語彙
   (256 種) が `HTMLElement` / `Record<K,V>` / `Promise<T>` 等の豊かな型を網羅できず、
   LM の正解 token を −inf で殺していた。
2. **Firewall (層分離装置) は中立**: 介入点を持たない設計のため害なし。
3. **vanilla bf16 自体は baseline を超える** (+2.5pp pass@1 / +3.14pp tsc)。Win
   Condition (tsc +5pp) にあと 1.86pp で届く位置。

Go の型システムは TS よりはるかに単純で、symbol-aware 制約が **標準ライブラリ
(`go/parser` + `go/types`) のみで完結する**。これが本物の勝ち筋。

## 売り (この簡易版で立てる 2 本柱)

1. **言霊 v2 (symbol-aware logit bias)** — `go/types` で「現在のスコープで参照可能
   なシンボル (types ∪ vars)」を取り出し、その対応 BPE token に **logit `+k` の
   ソフトバイアス** を加算する。**マスク (-inf 強制) は採らない** ([[feedback-kotodama-mask-counterproductive]] 参照)。
2. **ファイヤーウォール** — TS 版の `yomotsu_hirasaka` をそのまま流用。L3 (生成) と
   L5 (評価) を frozen dataclass で構造的に隔離。

## 楽観の禁止 (TS 版で踏んだ轍を踏まない)

- **「型語彙 ~70 種」は静的下限**。stdlib 由来のみが ~70。user-defined types は
  全て symbol oracle 経由で per-context に取り出す。oracle が機能しなければ
  実用不能になる、という前提を持って設計する。
- **ジェネリクスは v1 で除外**。`func F[T any](...)` の `T` は関数スコープに動的
  追加されるので、v1 の oracle は generic params をスコープに加えない (= 黙って
  ジェネリクス問題で精度を落とす)。v1 評価は **non-generic subset** で実施。
- **Win Condition は baseline 測定後に確定**。bare Qwen2.5-Coder-7B で humaneval-go
  の数値を計測してから初めて「+5pp」が意味を持つ。
- **3 seed 平均 + 95% CI で有意性判定**。N=159 では 3-4pp 程度の差は run-to-run の
  ブレに紛れる (TS 版 no-firewall vs full の −3.8pp が好例)。
- **BonpuConfidence は vocab 非依存だが distribution 依存**。TS コードで学習された
  hidden 分布上の confidence は Go の hidden 分布で calibration がずれる可能性。
  v1 は **使わない**、必要なら M2.5 以降で再 calibration。

## 現状 (2026-05-19)

| 項目 | 状態 |
|---|---|
| TS 版 3 mode ablation 結果 (A6000 bf16) | ✅ `data/eval/results/_a6000_bf16/` に保存 |
| `src_min/` (TS 版) | 🟡 アーカイブ扱い、編集しない |
| `src_min_go/` (Go 版) | 🔴 未着手 |
| Stage 2 `custom_heads.pt` (TS 特化) | 🟡 流用しない (vocab/distribution 共に不整合) |
| Go 用 baseline | 🔴 未測定 |

## モジュール構成 (予定)

```
src_min_go/
├── kojiki_lm/                          Python (Qwen 推論 + 言霊 + Firewall)
│   ├── yamato_qwen.py                  Qwen2.5-Coder backbone (TS 版から流用、トリビアル改変)
│   ├── qwen_adapter.py                 同上
│   ├── kotodama_decoder.py             言霊 v2: symbol-aware logit bias decode loop
│   ├── kotodama_context.py             Go の type-annotation 位置を AST ベースで判定
│   ├── kotodama_token_mask.py          allowed symbols → BPE first-token bias 配列
│   ├── go_symbol_oracle.py             go_tools への RPC クライアント (stdio JSONL)
│   ├── yomotsu_hirasaka.py             Firewall (TS 版から bit-for-bit 流用)
│   └── yomi_evaluator.py               Evaluator (キーワードを Go 用に差替: func/var/type/chan/go/defer 等)
├── go_tools/                           Go (symbol oracle daemon + 評価ツール)
│   ├── go.mod
│   ├── cmd/symbol_oracle/
│   │   └── main.go                     stdio JSONL daemon, go/parser + go/types 経由
│   └── cmd/go_evaluator/
│       └── main.go                     go vet / go build / go test ラッパー
└── config/
    └── go_type_vocab.json              stdlib primitives + builtin composite + 代表的 stdlib types ~70 種
```

`scripts/` (data/eval/train) と `data/raw/multipl_e/` は src_min/ と共有。

## マイルストーン

### M0 — baseline 測定 (humaneval-go × 3 seed)

bare Qwen2.5-Coder-7B-Instruct で humaneval-go を 3 seed (温度 0.2) 生成し、
**Win Condition の baseline 数値を確定** する。実装は不要、評価インフラのみ。

**Done 条件**
- humaneval-go 159 問 × 3 seed = 477 generation 完了
- 各 seed で:
  - pass@1 (`go test`)
  - go build 成功率
  - go vet clean 率
  - undefined symbol (`undefined: foo` 等) 出現サンプル率
- 3 seed 平均 ± 95% CI を [data/eval/results/_baselines/](../data/eval/results/_baselines/) に保存
- **この数値を見てから** M6 の Win Condition 閾値を確定する

**実装**
- `scripts/data/download_humaneval_go.py` — MultiPL-E `humaneval-go` を取得
- `scripts/eval/run_baseline_go.py` — bare Qwen で生成 (seed 引数あり)
- `scripts/eval/go_eval.py` — `go build` / `go vet` / `go test` の wrapper、JSON 集計

---

### M1' — Firewall + Evaluator (簡略版、Go 用キーワード差替)

L3↔L5 境界を型で強制。Evaluator は v1 では **TS 版から fork して GOOD/BAD キーワード
だけ差し替える**。Go 固有構文 (`:=`, iota, goroutine, channel op) の判定ロジック
拡張は **v1 では入れない**、必要が立証されてから追加。

**実装**
- `src_min_go/kojiki_lm/yomotsu_hirasaka.py` — TS 版 [src_min/kojiki_lm/yomotsu_hirasaka.py](../src_min/kojiki_lm/yomotsu_hirasaka.py) を bit-for-bit 流用 (~115 LOC)
- `src_min_go/kojiki_lm/yomi_evaluator.py` (~120 LOC)
  - GOOD keywords: `func`, `var ` , `const`, `type`, `interface`, `struct`, `chan`, `:=`, `error`, `: int`, `: string`, `: bool`, `: error`, `return ` 等
  - BAD patterns: ` interface{}` (any 相当), ` any`, `// TODO`, `// FIXME`, `panic(`
  - bracket balance チェック (TS 版と同じロジック流用)
- 単体テスト: `tests/test_evaluator_go.py` — Go コード snippet で V_score 計算が妥当か検証
- 単体テスト: `tests/test_firewall_go.py` — TS 版から流用 (yomotsu_hirasaka は変えてないので)

**Done 条件**
- 全テスト pass
- 既知の良いコード (公式 Go example) で score > 0.7 (= COMMIT 判定) が出る
- 既知の悪いコード (`panic`/`TODO` 入り) で score < 0.5

---

### M2 — 言霊 v2 (symbol-aware + logit bias)

**売りの本体**。「learned TypeHead 予測 → mask」ではなく、「**現在 scope の参照可能
シンボル → logit bias**」で運用する。AST/types 解析は Go daemon (separate process)
が担い、Python decode loop が JSON-RPC で query する。

**仕様**
- 詳細仕様: [docs/symbol_oracle_contract.md](symbol_oracle_contract.md)
- 呼び出し条件: kotodama_context が True を返したとき **のみ** (= type-annotation
  位置で 1 query)。token ごとには呼ばない。
- 適用方法: `last_logits[:, allowed_first_tokens] += k` で +k の bias を加算
  (k は config 化、初期値 +2.0)。**−inf マスクは絶対に採らない**。

**実装**
- `src_min_go/kojiki_lm/kotodama_decoder.py` (~250 LOC)
  - decode ループ: forward → kotodama_context 判定 → 真なら oracle query →
    bias 加算 → sample → Firewall.send
  - `mask_enabled` / `firewall_enabled` ablation flag は TS 版と同じ
- `src_min_go/kojiki_lm/kotodama_context.py` (~80 LOC)
  - Go の type-annotation 位置検出。**v1 は regex ベース、ただし TS の轍を踏まない**:
    - `func \w+\s*\(` 内の `, ?\w+\s+$` (引数の型位置)
    - `var \w+\s+$` / `const \w+\s+$`
    - `type \w+\s+$`
    - `func \w+\s*\([^)]*\)\s+$` (戻り値の型位置)
  - 偽陽性ガード: `if x < ` などの不等式は弾く ([[feedback-kotodama-mask-counterproductive]] と同じ知見)
  - 正確性が足りなければ AST ベースに昇格 ([Task 3](#着手前-3-タスク))
- `src_min_go/kojiki_lm/go_symbol_oracle.py` (~150 LOC)
  - stdio JSONL で go_tools/symbol_oracle daemon と通信
  - session 単位でキャッシュ、incremental update
  - daemon クラッシュ時の fallback (= bias 加算しない、vanilla として続行)
- `src_min_go/go_tools/cmd/symbol_oracle/main.go` (~400 LOC)
  - `go/parser` で AST、`go/types` で type info、scope walk
  - 詳細は [symbol_oracle_contract.md](symbol_oracle_contract.md)
- `src_min_go/kojiki_lm/kotodama_token_mask.py` (~100 LOC)
  - allowed symbol 名 → Qwen BPE first-token id 集合 → bool index array
  - cache: symbol 集合 (frozenset) keyed
- 単体テスト: `tests/test_kotodama_context_go.py`, `tests/test_oracle_client.py`,
  `tests/test_kotodama_decoder_go.py`

**Done 条件**
- `func add(a int, b ` 入力で oracle が `["int", "int8", ..., "any (interface{})"]` を返す
- decode 時に該当 token の logit が +2.0 加算されていることを直接観察 (テストで assert)
- ablation flag (`mask_enabled=False`) で bias OFF できる

---

### M6 — e2e 評価 + Win Condition 判定

**実装**
- `scripts/eval/run_yamato_min_go.py` (~250 LOC) — TS 版 run_yamato_min.py の Go 用 fork
- `scripts/eval/judge_win_condition_go.py` — baseline (M0 で取得) と比較
- 4 mode ablation:
  - `full`: 言霊 ON + Firewall ON
  - `no-kotodama`: 言霊 OFF + Firewall ON
  - `no-firewall`: 言霊 ON + Firewall OFF
  - `vanilla`: 言霊 OFF + Firewall OFF (= baseline)
- 各 mode で 3 seed、平均 ± 95% CI

**評価指標 (重要度順)**

| 順位 | 指標 | 計算方法 | Win 基準 |
|---|---|---|---|
| **PRIMARY** | go build 成功率 | `go build ./...` exit code = 0 のサンプル率 | baseline +5pp |
| **SECONDARY** | undefined-symbol 出現率 | `undefined: \w+` / `package \w+ is not in std` のエラー出るサンプル率 | baseline ×0.5 |
| TERTIARY | go vet clean 率 | `go vet ./...` 警告ゼロ率 | (情報) |
| TERTIARY | pass@1 | `go test` exit code = 0 のサンプル率 | (情報) |

PRIMARY が **go vet ではなく go build** であることを強調する: go vet は bug pattern
検出で型整合性は見ない。型ハルシ抑制を測る指標は **コンパイル成否** が正しい。

**Done 条件**
- 4 mode × 3 seed = 12 ラン
- Win Condition 判定 JSON で PRIMARY / SECONDARY を pass/fail 表示
- 95% CI で base vs full の差が有意であることを確認

---

### M2.5 (条件付き) — TypeHead 再学習 / BonpuConfidence 再 calibration

M6 で Win 未達の場合のみ追加検討。優先順位:

1. **TypeHead 再学習** — Go 型 vocab を新規設計し、Stage 2 を Go コーパスでやり直し。
   コスト: ~12h GPU + データ作り。oracle と AND して mask 候補を絞る。
2. **BonpuConfidence 再 calibration** — Go コードの hidden 分布で confidence を
   再学習。HALT 介入の精度向上。
3. **kotodama_context を AST ベース化** — regex で位置検出を間違えるケースが多発
   していたら、go/parser を Python 側からも参照して位置判定。

## 着手前 3 タスク (順序)

| Task | GPU 必要 | 所要 | 順序 |
|---|---|---|---|
| 1: M0 baseline 測定 | ✅ | A6000 cloud ~1.5h × 3 seed | ④ Win Condition 確定の前 |
| 2: symbol oracle RPC contract 仕様化 | ❌ | 0.5d | ① 着手の最先頭 |
| 3: type-annotation position 検出の AST ベース PoC (regex 不足ならここで補強) | ❌ | 1d | ② oracle 仕様の peer |
| 4: revised roadmap_min_go.md (本書) を確定 | ❌ | 0.5d | ⑤ baseline 数値で更新 |

## やらないこと (v1)

- **Stage 2 再学習** — まず vanilla bf16 + 言霊 v2 で勝負。学習はそのあと M2.5 で
- **ジェネリクス対応** — `func F[T any]` の `T` をスコープに含めない。評価も
  non-generic subset で
- **BonpuConfidence 流用 (再 calibration なし)** — distribution shift があるので
  v1 では使わない
- **Yomi Archive (長期 verdict 履歴)** — TS 簡易版でカット済、Go 簡易版でもカット
- **天御柱 4 Phase / Authority / Shadow-Twin** — Win 突破後の拡張枠
- **kenpou 後処理 / iwato 前処理** — prompt template と go build 直結で代替
- **methods, channel ops の scope-aware 解析** — v0.2 で対応 (`docs/symbol_oracle_contract.md` 参照)

## 達成後 (Win Condition 通過後の拡張順)

1. PRIMARY が baseline +5pp 未満 → **M2.5-1** (TypeHead 再学習 + oracle と AND)
2. SECONDARY (undefined ratio) 不足 → **M2.5-3** (kotodama_context を AST ベース化)
3. pass@1 が不足 → BonpuConfidence 再 calibration (M2.5-2) で HALT 精度を上げる
4. プロンプト多様性不足 → iwato 前処理
5. 長期改善 → Layer 2 feedback + Yomi Archive

世界観 (5 層 / 天御柱 / 造化三神) は Win 突破後に段階復活、TS 版ロードマップと同じ。

## 関連

- TS 版設計: [roadmap_min.md](roadmap_min.md) (アーカイブ)
- TS 版で得た知見: メモリ `feedback-kotodama-mask-counterproductive`
- Oracle 詳細仕様: [symbol_oracle_contract.md](symbol_oracle_contract.md)
- TS 版 3 mode ablation 結果: `data/eval/results/_a6000_bf16/{vanilla,no-firewall,full}/`
