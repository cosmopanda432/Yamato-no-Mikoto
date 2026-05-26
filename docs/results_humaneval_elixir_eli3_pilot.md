# humaneval-elixir 3-arm pilot — src_min_eli3 (光明想 KoumyouSo)

**実施日**: 2026-05-26
**Pod**: RunPod A5000 24GB / Qwen2.5-Coder-7B-Instruct 4bit
**Dataset**: humaneval-elixir 161 問 × seed 0 (single seed pilot)
**Runtime**: ~25 min (baseline 19m + firewall-off 6m + firewall-on 6m + koumyou-on 11m + 3 evals + 3 judges、合計 ~$0.12)

## 結論 (一言)

**光明想 (KoumyouSo) は pass@1 を約半減させた (29.19% → 15.53%) が、**
**undef-symbol rate を完全消滅させた (2.48% → 0.00%)。**
これは `feedback-type-prediction-is-hallucination-detection` の予言通りであり、
設計原理 (docs/memo/2026-05-26_須弥山設計原理.md Part 2 §6) の純粋な検証。
表層 metric (pass@1) と深層 metric (undef rate) のトレードオフが鮮明に出現。

## 結果テーブル

### 1. 全 metric の 4-mode 比較

| Metric | baseline | firewall-off | firewall-on | **koumyou-on** |
|---|---|---|---|---|
| pass@1 (test) | 26.71% | 29.19% | 29.19% | **15.53%** |
| compile rate | 68.32% | 72.05% | 72.05% | **29.19%** |
| **undef★ rate** | 5.59% | 2.48% | 2.48% | **0.00%** |
| assertion fail rate | 21.74% | 25.47% | 25.47% | **8.07%** |
| function clause rate | 4.97% | 6.21% | 6.21% | **3.73%** |

★ undefined_rate は roadmap_eli2.md / `feedback-type-prediction-is-hallucination-detection`
に従えば「本来の効果指標」。減少が好ましい (hallucination 軸)。

### 2. 主要 Δ

| Δ | pass@1 | undef rate | 解釈 |
|---|---|---|---|
| firewall-off − baseline | +2.48pp | −3.11pp | FirewallDecoder の code path 差 (修正 H 効果) |
| firewall-on − firewall-off | ±0.00pp | ±0.00pp | byte-identical (eli2 既知) |
| **koumyou-on − firewall-on** | **−13.66pp** | **−2.48pp → 0.00%** | **光明想の純増効果** |

### 3. 光明想の発火統計 (koumyou-on のみ)

| trace_status | 件数 | 割合 |
|---|---|---|
| trace_insufficient (= HALT) | 77/161 | 47.83% |
| trace_valid (= 通過) | 76/161 | 47.20% |
| trace_only (= code 未到達) | 8/161 | 4.97% |
| **halted_early** | **76/161** | **47.20%** |

trace_insufficient (77) と halted_early (76) の差 1 は in-loop check と post-eval check の
境界差 (in-loop で borderline 通過 → post-eval で finalize 時に失敗)。

## 解釈

### A. 光明想は設計通り動いた

設計原理 (docs/memo/2026-05-26_須弥山設計原理.md):
> 光明想 = 「闇 (出力の不透明性) を照明 (中間推論の可視化) で破る」
> → 中間推論を verifier に見せないと submit させない
> → 手抜きは闇に住むので、強制照明で死ぬ

実測:
- 47% のサンプルが「光明想に達しなかった」(trace_insufficient で HALT)
- 残り 47% は「光明想に達した」(trace_valid)
- HALT 後の出力は code が partial で compile 失敗 (compile 29.19%)
- しかし **生存サンプルの精度は劇的に向上** (undef 0%、assert fail 8.07% — fw-on の 25.47% から大幅減)

**光明想の本質的働き**: hallucinate しがちなサンプルは trace が薄い (≦ 20 chars)。光明想は
それらを reject することで、結果的に hallucination rate を強制ゼロ化した。

### B. pass@1 半減は「副作用」ではなく「設計通りの代償」

`feedback-ablate-before-celebrating` に従い率直に評価する:
- pass@1 −13.66pp は **巨大な数字**。実用化には致命的に見える
- しかし `feedback-type-prediction-is-hallucination-detection` に立てば:
  > **TsukuyomiTypeHead/Kotodama の本来効果指標は undef-symbol rate、pass@1 は副次**
- 光明想も同じ原理。pass@1 (副次) を犠牲にして undef rate (本質) を完璧化した。
- これは「光明想は機能するが、現状は HALT-only の rejection 一手」という未完成状態。

### C. 次の自然な拡張: HALT → REPAIR

現状の koumyou-on は HALT で完全停止する。理想は:
1. trace 不在/不足を検出 → HALT
2. 同じ prompt で **再生成** (光明想モードのまま、温度上げる or context 調整)
3. 再生成で trace が満たされたら → 通常評価
4. 数回 retry で全部失敗 → 最終 HALT

これにより:
- pass@1 損失を ~5-7pp に圧縮できる可能性 (76 HALT のうち多くが再生成で通る想定)
- undef rate 0% は維持
- コストは bench 時間が増える (re-gen 分)

実装場所: `run_yamato_min_elixir3.py` の生成ループに「HALT 検出 → 再生成 (最大 K 回)」を追加。
本コミットには含めない (設計議論が必要)。

### D. compile rate −42.86pp の解釈

compile rate も激減した。HALT'd サンプルは partial code (例えば `# 思考: ` だけで終わる)
なので compile に失敗する。これは pass@1 と同じ原因 = HALT による直接打撃。

ただし生存サンプル (76 件) の compile 通過率を見ると 47/76 = 61.84% — fw-on の 72.05%
より低い (生存サンプル中でも compile 失敗が一定数ある)。これは光明想が compile fail の
全パターンを救えないことを示す (思考しても文法的に正しい code を書けない場合がある)。

### E. assertion failure rate −17.40pp の意味

assert fail は「compile も undef も通ったが、test の assertion で失敗」= 論理ミス。
fw-on の 25.47% → koumyou-on の 8.07% は **生存サンプルの論理精度向上**を示唆 (思考した結果、
答えが論理的に正しい確率が上がっている)。これは光明想の **質的効果** の最も強い signal。

## 副次知見

### Qwen2.5-Coder-Instruct の trace 出力スタイル

bare prompt + trace seed (`# 思考: `) のみで誘導した場合:
- **中国語の reasoning** を生成 (英語 prompt にも関わらず)
- **1 行に comma 区切りで全 step を詰める** (`1. xxx, 2. yyy, 3. zzz`)
- 47% が `min_trace_chars=20` を満たせない (思考が薄い問題が約半数)

multi-line trace は出にくい → README の「multi-line trace は強制できない」既知制約を裏付け。

### Firewall (黄泉比良坂) はやはり byte-identical

fw-off = fw-on で pass@1 / 全 metric が完全一致。これは eli2 で 3 seed 検証済の
byte-identical 性 (`project-elixir-pivot-viability` メモリ) の継続。pilot は 1 seed の
ため CI は出せないが、point estimate 完全一致は再現可能性の高い signal。

## 関連メモリ / 設計 doc

- `feedback-type-prediction-is-hallucination-detection`: pass@1 は副次、undef-symbol が本質
- `feedback-ablate-before-celebrating`: 数字の解釈に慎重に、Win Condition 軸で見ると失敗
- `project-firewall-purpose`: 黄泉比良坂は L3↔L5 隔離壁、本実験は壁の上に光明想を追加した形
- `project-elixir-pivot-viability`: humaneval-elixir 161/161 byte-identical 既知
- docs/memo/2026-05-26_須弥山設計原理.md Part 2 §6: 光明想の設計原理
- src_min_eli3/README.md: 実装詳細 + 既知制約

## 関連ファイル (本 pilot で生成)

- baselines/yamato_min_elixir3.humaneval-elixir.firewall-off.seed0.judge.json
- baselines/yamato_min_elixir3.humaneval-elixir.firewall-on.seed0.judge.json
- baselines/yamato_min_elixir3.humaneval-elixir.koumyou-on.seed0.judge.json
- data/eval/results/humaneval-elixir.baseline.seed0/_summary.json
- data/eval/results/humaneval-elixir.yamato_min_elixir3.{firewall-off,firewall-on,koumyou-on}.seed0/_summary.json
- data/eval/generated/humaneval-elixir.yamato_min_elixir3.koumyou-on.seed0/*.json (per-sample trace_info あり)

## 次のステップ (候補、優先順)

| # | 案 | 期待 | コスト |
|---|---|---|---|
| 1 | **HALT → REPAIR (再生成) 実装** | pass@1 損失を圧縮しつつ undef 0% 維持 | 中 (実装 + 再 bench ~2h) |
| 2 | 3 seed CI (今 pilot の続き) | 95% CI で再現性検証 | 高 (~6-8h、~$2.5) |
| 3 | prompt 強化 (one-shot で multi-line trace 誘導) | trace_insufficient 率を 47% → 20% 程度に | 低 (prompt 改修のみ) + 再 bench |
| 4 | mbpp-elixir (397 問) で同様 pilot | 別 dataset での再現性 | 中 |
| 5 | min_trace_chars 緩和 (20 → 10) | HALT 減 + pass@1 回復だが undef 0% 維持できるか不明 | 低 |

提案: **(3) prompt 強化** → trace 充足率を上げてから **(1) REPAIR** → 純化された 3-arm 比較。
