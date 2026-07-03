# eli4 產屋 (REPAIR) 実装設計書 v0 — 実装 agent handoff 仕様

作成: 2026-07-03
実装先: `src_min_eli4/` (新規、eli3 完全 copy ベース) — 決定済み ([実装残項目_v0.md](実装残項目_v0.md) §4 の選択肢 (a))
実装者: コード生成 agent (Sonnet 5 想定)。**本書単体で実装可能**なように書いてある。
本書に無い判断が必要になったら、勝手に決めずに TODO コメントを残して人間に確認すること。

## 0. ゴール / 非ゴール

**ゴール**: eli3 の HALT-only 光明想 (pass@1 −13.66pp / undef 0%) に **REPAIR (再生成) 機構**を
追加し、undef 低位を維持したまま pass@1 損失を回収する。名称は產屋 (ubuya)。

**非ゴール** (やらないこと):
- eli2 / eli3 のソース変更 (`src_min_eli2/` `src_min_eli3/` は 1 byte も触らない)
- 生成済み completion の in-place 編集による「修復」(禁止。修正は先頭からの再生成のみ)
- LLM-as-judge の導入 (すべて決定論的 structural check)
- v_score の scoring 方式変更 (§11 参照 — 既知の非対称も含めて eli3 と同一に保つ)
- attention sink / 長系列対応 (棚上げ済み)

## 1. 参照文書 (why を知りたいとき)

| 文書 | 内容 |
|---|---|
| [実装残項目_v0.md](実装残項目_v0.md) | 残項目 A-E の定義・DoD・依存関係 (本書はその実装仕様化) |
| [kojiki_transformer_llm_v0.md](kojiki_transformer_llm_v0.md) | 設計原理の origin spec (還降/如先/事戸/葦船) |
| `docs/memo/2026-07-03_須弥山報酬ハック原理.md` | hack_gap 指標の根拠 (§7-8)、DoD 双方向拘束 (§4b) |
| `src_min_eli3/README.md` | eli3 の構成と eli2 との差分 |

## 2. Step 0: eli4 の作成 (copy 手順)

1. `src_min_eli3/` を `src_min_eli4/` へ丸ごと copy。ただし `__pycache__/` は除外
2. `src_min_eli4/README.md` を書き換え: 「eli3 完全 copy + 產屋 (REPAIR) 統合実装
   (2026-07-03〜)。本設計書: data/kojiki/設計書/eli4_実装設計書_v0.md」+ 差分表
   (Step A-E 完了後に最終化)
3. runner は `scripts/eval/run_yamato_min_elixir4.py` (新規、Step C)。
   `sys.path.insert(0, str(REPO_ROOT / "src_min_eli4"))` で eli4 の `kojiki_lm` を import
   (eli3 runner の line 42 と同形式。package 名は `kojiki_lm` のまま)

## 3. Step A: 葦船 log — `src_min_eli4/kojiki_lm/ashibune.py` (新規)

棄却された生成 sample を理由コード付きで永続化する (消さない・成功集合に混ぜない)。

```python
@dataclass(frozen=True)
class AshibuneRecord:
    ts: str                 # ISO 8601
    prompt_id: str          # 例 "HumanEval_0"
    mode: str               # "repair-on" 等
    round: int              # 0 = 初回生成
    seed_used: int          # この attempt の sampling_seed 実値
    verdict: str | None     # final_verdict ("commit"/"repair"/"halt"/None)
    v_score: float | None
    reason_code: str        # ReasonCode.value (Step B)
    hint_used: str          # この attempt の prompt に注入された hint ("" = なし)
    halted_early: bool
    stopped_at_stop_token: bool
    test_ok: bool | None    # post-hoc eval 結果 (未 eval なら None)
    has_undefined: bool | None
    exit_code: int | None
    completion_chars: int
    raw_completion: str     # 全文 (卜相 = 失敗分布分析の資源)
    accepted: bool          # この attempt が最終回答として採用されたか
    is_final_answer: bool   # rounds 消尽時の最終 attempt (不合格でも True)

class AshibuneLog:
    def __init__(self, path: Path): ...   # 親 dir が無ければ作る
    def append(self, record: AshibuneRecord) -> None:
        # 1 record = 1 行 JSON (JSONL)。append mode で開き、書いたら即 flush + close
```

**制約**:
- 書き込みは orchestrator (Step C) 側から行う。`FirewallDecoder` の decode loop 内からは
  絶対に呼ばない (生成 byte への影響を構造的にゼロにするため)
- ファイルは `<out_dir>/ashibune.jsonl`。`elixir_eval.py` は `*.json` を glob するので
  拡張子 `.jsonl` により誤読み込みされない (確認済みの現行実装: `gen_dir.glob("*.json")`)

**DoD-A**: 全 attempt (全 round) が記録される。unit test: 2 record 書いて読み戻し一致。

## 4. Step B: 事戸拡張 — `src_min_eli4/kojiki_lm/yomotsu_hirasaka.py` / `elixir_evaluator.py`

### 4.1 ReasonCode enum (yomotsu_hirasaka.py に追加)

```python
class ReasonCode(Enum):
    NONE = "none"
    TRACE_MISSING = "trace_missing"
    TRACE_INSUFFICIENT = "trace_insufficient"
    BRACKET_MISMATCH = "bracket_mismatch"
    DO_END_MISMATCH = "do_end_mismatch"
    BAD_PATTERN = "bad_pattern"
    LOW_SCORE = "low_score"
    UNDEF_SYMBOL = "undef_symbol"   # post-hoc 専用 (in-loop evaluator は使わない)
```

### 4.2 L5ToL3Verdict 拡張

既存 `{verdict, v_score}` に追加 (default 付きで後方互換):

```python
@dataclass(frozen=True)
class L5ToL3Verdict:
    verdict: Verdict
    v_score: float
    reason_code: ReasonCode = ReasonCode.NONE
    hint: str = ""          # 最大 200 文字
```

`__post_init__` に既存と同じ防御スタイルで追加:
- `reason_code` が `ReasonCode` instance でなければ TypeError
- `hint` が str でなければ TypeError、`len(hint) > 200` なら ValueError
- **既存 validation は一切変更しない**

### 4.3 ElixirEvaluator の reason_code 設定 (eli4 copy 内)

`__call__` の返り値に reason_code を付ける。判定規則 (優先順位順):

1. 光明想 terminal failure → `trace.status` を対応させる:
   `TraceStatus.TRACE_MISSING → ReasonCode.TRACE_MISSING`、
   `TraceStatus.TRACE_INSUFFICIENT → ReasonCode.TRACE_INSUFFICIENT`
   (verdict=HALT, v_score=0.0 は現行のまま)
2. verdict == COMMIT → `NONE`
3. それ以外 (REPAIR/HALT): `_compute_v_score` 内で判定済みの信号を優先順位
   `BRACKET_MISMATCH > DO_END_MISMATCH > BAD_PATTERN > LOW_SCORE` で 1 つ選ぶ。
   実装は `_compute_v_score` を「score と検出フラグ dict を返す」形にリファクタして良い
   (**score の数値計算は 1 bit も変えない** — 検出フラグは既に計算している bool の再利用)

**DoD-B**: 既存 unit test green (あれば)。新規 test: (i) reason_code/hint の型・長さ
validation、(ii) `L5ToL3Verdict(verdict=Verdict.HALT, v_score=0.0)` が従来通り動く
(後方互換)、(iii) bracket 崩れ入力で `BRACKET_MISMATCH` が返る。

## 5. Step C: 還降 loop — `scripts/eval/run_yamato_min_elixir4.py` (新規)

`run_yamato_min_elixir3.py` を出発点に copy し、以下を追加する。
既存 3 mode (`firewall-off` / `firewall-on` / `koumyou-on`) は**挙動を一切変えず**残す。

### 5.1 新 mode と CLI

- `--mode repair-on` を追加: koumyou-on の全設定 + round 型 REPAIR
- `--max-rounds` (int, default 2): round 0 (初回) の後に許す repair round 数
- `--eval-timeout` (float, default 5.0): round 内 post-hoc eval の timeout
- `--elixir-bin` (default None → PATH 検索): repair-on 時は起動直後に
  `shutil.which` で fail-fast (「repair-on は生成 host に elixir が必要」を明示)

### 5.2 seed 規則 (最重要 — 統制条件)

```python
BASE = args.seed * 1_000_003 + i          # round 0。eli3 line 192 と完全同値であること
R_STRIDE = 999_999_937                    # 大素数。round 衝突回避
seed(i, r) = BASE + r * R_STRIDE          # round r >= 1
```

- **round 0 の生成は eli3 koumyou-on と byte-identical でなければならない**
  (同一 args・同一 limit で `raw_completion` が全 sample 一致)。これが repair の
  marginal effect を測る ablation の統制条件
- `torch.manual_seed(args.seed)` 等の初期化順序も eli3 runner と同一に保つ

### 5.3 round アルゴリズム

```
round 0: 全 prompt を生成 (koumyou-on と同一) → out_dir/round_0/ に per-sample JSON
         → 各 sample を elixir_eval.run_one で即時評価 (import: 同 dir なので
            `from elixir_eval import run_one`)
for r in 1..max_rounds:
    fail_set = {test_ok == False の sample}   # HALT・compile fail・undef・assertion・timeout 全部
    if not fail_set: break
    各 fail sample について:
        hint = build_hint(前 round の eval 結果)      # Step D の規則
        if hint == "" and not do_sample: skip         # greedy では無 hint 再試行は無意味
        wrapped_prompt = prompt + hint_line + TRACE_SEED   # hint_line = f"  # 補足: {hint}\n"、
                                                           # hint 無しなら round 0 と同一形
        生成 (seed = BASE + r * R_STRIDE) → out_dir/round_{r}/ → 即時評価
最終回答: sample ごとに「最初に test_ok になった attempt」、無ければ最終 round の attempt。
         out_dir/ 直下に {name}__s0.json として書く (eli3 と同 schema + 追加 field)
```

- 追加 field (最終回答 JSON): `"round"` (採用 attempt の round)、`"hint"` (同 attempt の hint、
  無ければ "")、`"n_attempts"`、`"repair_reason"` (retry を起こした reason_code、round 0 採用なら "")
- **completion の構成**: hint 付き attempt では
  `completion = hint_line + TRACE_SEED + truncate(result.text)`
  (`prompt + completion` が valid Elixir になる — eli3 の TRACE_SEED prepend と同じ理屈)。
  JSON の `"prompt"` は元 prompt のまま
- 全 attempt を AshibuneLog に記録 (Step A)
- `out_dir/_repair_summary.json` を書く: `{n_prompts, max_rounds, per_round_pass:
  [round0_pass, round1_pass, ...], n_recovered (round>=1 で救済された数),
  avg_attempts, hints_used: {reason_code: count}}`
- model は process 内に保持したまま全 round を回す (再ロードしない)

### 5.4 DoD-C

1. `--mode repair-on --max-rounds 0 --limit 20 --seed 0` の round_0 出力が、eli3
   `--mode koumyou-on --limit 20 --seed 0` の出力と `raw_completion` 全一致
   (`scripts/eval/diff_smoke_outputs.py` が使えるか確認し、使えなければ raw_completion を
   突き合わせる 20 行程度の比較 script を書いて `scripts/eval/` に置く)
2. 既存 3 mode の出力が eli3 と一致 (regression、--limit 5 で可)
3. smoke (--limit 20, --max-rounds 2) で retry が発火し、`ashibune.jsonl` と
   `_repair_summary.json` が書かれる

## 6. Step D: 処方 — hint 構築規則 + `scripts/eval/elixir_eval.py` の additive 拡張

### 6.1 elixir_eval.py の拡張 (共有 script。**additive のみ**)

`run_one` 内、`combined` を trim する**前**に構造化抽出し、result に field 追加:

```python
result["undef_symbols"] = [...]     # 例 ["Enum.fitler/2", "MyModule"]
result["did_you_mean"] = [...]      # 例 ["filter/2"]
result["final_v_score"] = sample.get("final_v_score")    # hack_gap 用に転記
result["final_verdict"] = sample.get("final_verdict")
```

抽出 regex の出発点 (**smoke で実際のエラー出力に対して検証してから確定**すること。
Elixir の関数名は `?` `!` を含み得る):

```python
RE_UNDEF_FUNC   = re.compile(r"function\s+([A-Za-z_][\w\.]*[.][\w!?]+/\d+)\s+is undefined")
RE_UNDEF_MODULE = re.compile(r"module\s+([A-Za-z_][\w\.]*)\s+is not loaded")
RE_DYM_BLOCK    = re.compile(r"Did you mean:((?:\s*\*\s*[\w\.!?]+/\d+)+)")
RE_DYM_ITEM     = re.compile(r"\*\s*([\w\.!?]+/\d+)")
```

`_summary.json` に追加 (既存 key は変更しない):
- `"hack_gap"`: `P(test_ok == False | final_v_score is not None and final_v_score >= 0.7)`
  (分母 0 なら 0.0)。根拠: 須弥山報酬ハック原理 §7-8 (不浄観 audit —
  in-loop proxy が COMMIT と言ったのに大地 = subprocess が否定した率)

### 6.2 hint 構築規則 (orchestrator 内 `build_hint`)

| 前 round の失敗 | hint | 根拠 |
|---|---|---|
| `undef_symbols` 非空 | `f"{sym} は未定義。候補: {', '.join(dym[:2])}"` (dym 空なら `f"{sym} は未定義"`)。最大 2 symbol、全体 200 字で切る | symbol レベルのみ認可 (`project-mechanical-repair-mbpp-go-zero`) |
| 光明想 HALT (trace_*) | hint なし (再サンプルのみ) | prompt 強化は別実験 (eli3 memo) |
| syntax / assertion / timeout / その他 | hint なし (再サンプルのみ) | 構文レベル処方は禁止経路 |

**如先の担保 (test で強制)**: hint なし retry の wrapped_prompt は round 0 と byte 一致。
hint あり retry の wrapped_prompt は round 0 との diff が hint_line 1 行のみ。

**DoD-D**: (i) 意図的に `Enum.fitler` を含む fixture で undef_symbols / did_you_mean が
抽出される (elixir が PATH に無い環境では fixture stderr 文字列を直接 regex に通す
unit test で代替可)、(ii) 如先 test 2 件 green、(iii) 既存 _summary.json の既存 key の
値が拡張前後で不変 (回帰)。

## 7. Step E: 収支 judge — `scripts/eval/judge_win_condition_elixir.py`

共有 script。変更は最小限に:

1. `--mode` choices に `"repair-on"` を追加 (現状: firewall-on / firewall-off / koumyou-on。
   先例: koumyou-on 追加 commit `2f0659e`)
2. `METRIC_KEYS` に `"hack_gap"` を追加 (`s.get(key, 0.0)` なので古い summary とも互換)
3. `render_report` に INDICATOR 行 `hack_gap` を追加
4. mode == "repair-on" のとき報告末尾に**二段階警報** (須弥山原理・天人五衰の小衰/大衰) を表示:
   - 小衰 (soft alarm): `hack_gap mean > 0.15` → 「proxy (v_score) 改訂を検討」
   - 大衰 (terminal alarm): `undefined_rate の Δ > 0 かつ test_pass_rate の Δ < 0` →
     「arm 廃棄を勧告」
   - 閾値はファイル冒頭の定数 (`HACK_GAP_SOFT_ALARM = 0.15`)
5. 判定ロジック (`judge()` の PRIMARY/SECONDARY) は**変更しない** — repair arm の収支判定は
   `--baseline` に koumyou-on の summaries、`--yamato` に repair-on の summaries を渡す
   運用で既存ロジックがそのまま働く

**DoD-E**: `--mode repair-on` で 3 指標 + hack_gap + 警報が表示される。既存 mode の出力不変。

## 8. 禁止事項 (実装 agent への guardrail)

1. `src_min_eli2/` `src_min_eli3/` を変更しない (import もしない)
2. `L3ToL5Payload` / `L5ToL3Verdict` に tensor・hidden state・評価器内部統計を載せない
   (既存 `__post_init__` の防御を弱めない)
3. 生成済みテキストの部分書き換えによる「修復」を実装しない (還降 = 全再生成のみ)
4. v_score を best-of-n の選別基準や attempt 間の比較に**使わない**
   (gameable proxy。attempt の合否判定は subprocess の test_ok のみ)
5. v_score の計算式・`_ELIXIR_GOOD_KEYWORDS`・閾値 (0.3/0.7)・prompt 非 slice の
   非対称を変更しない (§11)
6. LLM-as-judge・embedding 類似度など非決定論的判定を導入しない
7. hint 以外の prompt 差分を作らない (few-shot 追加・指示文変更は別実験)
8. `elixir_eval.py` / `judge_win_condition_elixir.py` の既存 field・既存 metric の
   意味を変えない (追加のみ)
9. 乱数: `torch.Generator` の分離 (eli3 修正 D) を維持。retry でも `_sampling_rng` 経由

## 9. テスト計画 (集約)

| test | 対象 | 種別 |
|---|---|---|
| AshibuneLog 書き込み/読み戻し | Step A | unit |
| ReasonCode / hint validation + 後方互換 | Step B | unit |
| reason_code 判定 (bracket/do_end/bad_pattern/trace) | Step B | unit |
| seed 式: `seed(i,0) == args.seed*1_000_003+i` | Step C | unit |
| 如先: hint なし prompt 一致 / hint あり diff 1 行 | Step D | unit |
| undef_symbols / did_you_mean 抽出 (fixture stderr) | Step D | unit |
| hack_gap 計算 (合成 summary) | Step D/E | unit |
| round_0 byte-identity (eli3 koumyou-on 比較) | Step C | smoke (GPU) |
| 既存 3 mode regression | Step C | smoke (GPU) |
| repair round 発火 + ashibune + _repair_summary | Step C | smoke (GPU) |

テストの置き場所は既存 `tests/` の慣例に従う (実装前に `ls tests/` で確認)。
GPU smoke は RunPod (A5000、`scripts/runpod_bench_eli3.sh` を copy して
`runpod_bench_eli4.sh` を作成。elixir install step が入っていることを確認 —
repair-on は**生成 host に elixir が必要**という新依存)。

## 10. 実装順序と本番手順

実装順: **Step 0 → A → B → C → D → E** (残項目の依存順そのまま。A/B は独立なので並行可)。

本番 (実装完了後、人間が実施判断):
```bash
# seed 0..2 × mode {koumyou-on, repair-on} を eli4 runner で生成 (round_0 が koumyou-on を兼ねる訳ではない点に注意 — 別 run)
python3 scripts/eval/run_yamato_min_elixir4.py --input ... --mode repair-on --max-rounds 2 --seed {0,1,2} --out-dir ...
python3 scripts/eval/elixir_eval.py --generated-dir ... --out-dir ...
# 収支判定: baseline = koumyou-on (HALT-only)、yamato = repair-on
python3 scripts/eval/judge_win_condition_elixir.py --baseline <koumyou-on summaries> --yamato <repair-on summaries> --mode repair-on --out ...
```

期待収支 (memory `project-koumyou-so-halt-only-tradeoff`): pass@1 損失を −13.66pp から
−5〜7pp 程度へ圧縮しつつ undef ≈ 0% 維持。大衰警報が出たら arm 廃棄して設計に戻る。

## 11. 既知の非対称・棚上げ (触らない、が記録する)

- **v_score の prompt 非 slice**: `_compute_v_score(payload.text)` は prompt を含む全文を
  採点する (光明想 check は `text[prompt_len:]` に slice するのに、v_score はしない)。
  gameable proxy の一部だが、**eli4 では修正しない** — 修正すると verdict のタイミングが
  変わり round 0 の byte-identity (統制条件) が壊れるため。hack_gap 指標 (§6.1) が
  この proxy の健全性を監視する。修正は eli5 以降の独立 ablation で
- 天照/須佐之男の命名空間、attention sink 系: 棚上げ (実装残項目 §5)

## 履歴

- 2026-07-03: v0 作成。eli3 実コード (runner seed 式・elixir_eval の regex 群・judge の
  METRIC_KEYS 構造・KoumyouSo TraceStatus) を確認済みの上で仕様化
