# Sampling Path Issue — 2026-05-20 mbpp-go ablation で発覚

## TL;DR

`KotodamaDecoder._sample` が `transformers` の `model.generate` と**異なる確率過程**を
実装していた (`top_k` / `top_p` フィルタなし)。これが原因で:

- baseline (`model.generate` 経由) と yamato 3 mode (`KotodamaDecoder` 経由) の間に
  実装非依存の系統差が出る
- mbpp-go 1 seed 実験で **+4.01pp pass@1** の lift が見えたが、機構ではなく
  サンプラー差が出している可能性が極めて高い
- humaneval-go 3 seed の **Win Condition ACHIEVED (+7.14pp / +15.37pp)** 主張も
  同じバグの可能性が高い → verification 完了まで主張保留

このコミットに **code fix** は入っているが **数字での検証は未了**。隣のマシンで
verification → 結果次第で過去の Win 主張を訂正 or 確定する。

## 経緯 (どうやって発覚したか)

1. **humaneval-go 3 seed Win**: 2026-05-20 朝、A6000 bf16 で baseline / yamato_full
   を 3 seed ずつ取り `+7.14pp pass@1 / +15.37pp vet` で Win Condition ACHIEVED 宣言
   (commit `4a5992b`)
2. **mbpp-go 1 seed × 4 mode ablation**: 同日午後、A5000 bf16 で全 ablation を取得:

   | Mode | bias | firewall | pass@1 | Δ pass | vet | Δ vet |
   |---|---|---|---|---|---|---|
   | baseline (`model.generate`) | — | — | 46.26% | — | 67.65% | — |
   | no-kotodama (`KotodamaDecoder`) | OFF | ON | 50.00% | +3.74 | 74.87% | +7.22 |
   | no-firewall (`KotodamaDecoder`) | ON | OFF | 50.00% | +3.74 | 75.13% | +7.49 |
   | full (`KotodamaDecoder`) | ON | ON | 50.27% | +4.01 | 74.87% | +7.22 |

3. **異常**: yamato 3 mode (bias/firewall の組合せが違う) が **ほぼ同点** (±0.27pp)。
   bias を on/off しても結果がほぼ動かない、firewall も同じ。

4. **completion レベル比較**: 全 374 問で:
   - **bias を on/off で出力が変わるのは 3/374 = 0.8%**
   - **firewall を on/off で出力が変わるのは 181/374 = 48.4%**
   - だが firewall は HALT=0 / REPAIR=10 のみ。意図された機構ではなく **副作用** (RNG drift)
     で出力を変えている

5. **bias 発火頻度**: 374 問中 365 問 (97.59%) で bias は発火している。だが発火率は
   生成全体の **1.14%** (1 サンプル平均 2-6 step / 256 step)。発火はしているが結果に出ない。

6. **コードレビューで発見**:
   - `scripts/eval/run_baseline_go.py` は `model.generate(do_sample=True, temperature=0.2,
     top_p=0.95)` を呼ぶ → transformers が自動で `TopK(50) → TopP(0.95)` を適用
   - `src_min_go/kojiki_lm/kotodama_decoder.py:_sample` は **temperature だけ** で
     `torch.multinomial(probs, 1)` に渡していた → 152K 全 vocab から抽出
   - 両者は同じ確率分布だが、フィルタ有無で実質的に異なる stochastic process

## 問題コード (修正前)

```python
def _sample(self, logits: torch.Tensor) -> torch.Tensor:
    cfg = self.config
    if cfg.do_sample and cfg.temperature > 0:
        probs = torch.softmax(logits / cfg.temperature, dim=-1)
        return torch.multinomial(probs, 1)            # ← 全 152K vocab から抽出
    return logits.argmax(dim=-1, keepdim=True)
```

vs baseline (`run_baseline_go.py:134-141`):

```python
output_ids = model.generate(
    **inputs,
    do_sample=True,
    temperature=0.2,
    top_p=0.95,                                       # ← TopP(0.95) 適用
    # 暗黙: TopK(50) も transformers のデフォルトとして自動適用
    ...
)
```

## 修正 (このコミット)

`KotodamaConfig` に `top_k: int = 50`, `top_p: float = 0.95` を追加し、`_sample` で
`Temperature → TopK(50) → TopP(0.95) → multinomial` の順に適用する transformers
互換のサンプラーに書き換え。

```python
def _sample(self, logits: torch.Tensor) -> torch.Tensor:
    cfg = self.config
    if not (cfg.do_sample and cfg.temperature > 0):
        return logits.argmax(dim=-1, keepdim=True)

    logits = logits.clone() / cfg.temperature

    # top-k: 上位 k 個以外を -inf
    if cfg.top_k > 0 and cfg.top_k < logits.size(-1):
        kth_vals, _ = torch.topk(logits, cfg.top_k, dim=-1)
        logits = torch.where(logits < kth_vals[..., -1, None],
                             torch.full_like(logits, float("-inf")), logits)

    # top-p (nucleus): 累積 top_p を超えた tail を -inf
    if 0.0 < cfg.top_p < 1.0:
        sorted_logits, sorted_idx = torch.sort(logits, descending=True, dim=-1)
        cum_probs = torch.cumsum(torch.softmax(sorted_logits, dim=-1), dim=-1)
        sorted_remove = cum_probs > cfg.top_p
        sorted_remove[..., 1:] = sorted_remove[..., :-1].clone()
        sorted_remove[..., 0] = False
        remove_mask = torch.zeros_like(sorted_remove)
        remove_mask.scatter_(-1, sorted_idx, sorted_remove)
        logits = torch.where(remove_mask, torch.full_like(logits, float("-inf")), logits)

    probs = torch.softmax(logits, dim=-1)
    return torch.multinomial(probs, 1)
```

`scripts/eval/run_yamato_min_go.py` に `--top-k 50 --top-p 0.95` をデフォルト追加。

## 仮説と分岐シナリオ

検証ランの結果次第で以下のどれかに確定する:

| シナリオ | 修正後 yamato_full の pass@1 | 結論 |
|---|---|---|
| **A: 全部 sampler** | baseline と ±1pp 以内 | 機構 (bias/firewall) は完全にノーオペ。Win 主張は撤回。 |
| **B: 一部機構** | baseline +1〜+3pp | 機構が貢献するが微小。Win 閾値 +5pp には届かない。 |
| **C: 機構は本当に効く** | baseline +5pp 以上 | 機構は実際に効いていた。サンプラー差は別ノイズで両者キャンセル。Win 主張継続。 |

A の確率が一番高そう (mbpp-go ablation で機構 toggle が結果に出ないことから)。

## 検証手順 (隣のマシンでやること)

### 0. リポジトリ最新化

```bash
git pull origin main
```

### 1. 環境セットアップ

隣のマシンに以下が揃っているか確認:

- [ ] **GPU**: VRAM 24GB+ なら bf16、12GB なら 4bit 必須
- [ ] **Python 3.9+** と `pip install -e ".[dev,quantization]"` 済み
- [ ] **Go 1.26.3+** (`go version` で確認)
- [ ] **models/Qwen2.5-Coder-7B-Instruct/** ローカル展開済 (15GB)
- [ ] **data/raw/multipl_e/mbpp-go/test-00000-of-00001.parquet** あり
- [ ] **src_min_go/go_tools/bin/symbol_oracle** ビルド済
  (なければ `cd src_min_go/go_tools && go build -o bin/symbol_oracle ./cmd/symbol_oracle`)

不足を一括 setup するなら:

```bash
# Qwen モデル
hf download Qwen/Qwen2.5-Coder-7B-Instruct --local-dir models/Qwen2.5-Coder-7B-Instruct

# mbpp-go parquet
python3 -m pip install "datasets>=2.14"
python3 -c "
from datasets import load_dataset
import os
ds = load_dataset('nuprl/MultiPL-E', 'mbpp-go', split='test')
os.makedirs('data/raw/multipl_e/mbpp-go', exist_ok=True)
ds.to_parquet('data/raw/multipl_e/mbpp-go/test-00000-of-00001.parquet')
print('rows:', len(ds))
"

# oracle daemon
(cd src_min_go/go_tools && go build -o bin/symbol_oracle ./cmd/symbol_oracle)
```

### 2. apples-to-apples 比較のため baseline + yamato_full を**同じ量子化で**再生成

VRAM 不足で 4bit を使うなら baseline も 4bit に揃える。前回 pod では bf16 で
baseline / yamato_full を取ってあるが、これと **量子化が違う数字は混ぜない**
([[feedback-distinguish-symptom-from-cause]] の轍を踏まない)。

```bash
# 量子化に合わせて QUANTIZE 環境変数を選ぶ
export DATASET=mbpp-go
export QUANTIZE=4bit              # VRAM 12GB GPU の場合 (RTX 3060 等)
# または
export QUANTIZE=none              # VRAM 24GB+ の場合 (bf16)

# baseline (run_baseline_go.py = model.generate、変更なし。確認用に再生成)
bash scripts/runpod_bench.sh run baseline 0

# yamato_full (KotodamaDecoder = 修正後 sampler 経由)
bash scripts/runpod_bench.sh run full 0
```

旧 baseline / yamato_full の `data/eval/generated/mbpp-go.*.seed0/` がある場合、
SKIP_EXISTING の挙動 (`_summary.json` あれば skip) でぶつかるので、検証前に
削除すること:

```bash
rm -rf data/eval/{generated,results}/mbpp-go.baseline.seed0 \
       data/eval/{generated,results}/mbpp-go.yamato_min_go.full.seed0
```

### 3. judge

```bash
DATASET=mbpp-go bash scripts/runpod_bench.sh judge full 0
```

出力: `baselines/yamato_min_go.mbpp-go.full.seed0.judge.json`。

### 4. シナリオ判定

修正後 yamato_full の pass@1 と baseline pass@1 を比べる:

- **A シナリオ (差 ≤ 1pp)**: code fix で消えた = サンプラー差が +4.01pp の正体。
  bias / firewall は機構として効いていない。**過去の Win 主張は撤回。**
- **B シナリオ (差 +1〜+3pp)**: 部分的に機構の貢献あり。Win 閾値には届かず。
- **C シナリオ (差 +5pp 以上)**: 機構が本当に効く。Win 主張継続可能、サンプラー差は別ノイズで打ち消し。

## 確認すべきこと (verification 後に対応)

- [ ] mbpp-go 1 seed で **修正後 yamato_full vs baseline** の Δ を測定 (上記手順)
- [ ] シナリオ判定に応じて memory `project-go-roadmap-state` と
      `baselines/yamato_min_go.full.seed0_1_2.judge.json` の主張を訂正
- [ ] [ABLATE BEFORE CELEBRATING memory] と整合する形で commit ログを残す
- [ ] **(オプション)** humaneval-go 3 seed × 4 mode × bf16/4bit で再検証 ($1.80 程度)。
      過去の Win 主張を完全にクリアにしたい場合
- [ ] verification 後、本ドキュメントの「シナリオ」項を実際の数字で更新

## 2026-05-21 Verification 結果

mbpp-go × seed 0 × A5000 bf16 で 3 mode を取得 (修正 A/B/C/D/G/H 全部入り):

| Mode | bias | firewall | pass@1 | vet |
|---|---|---|---|---|
| baseline (`model.generate`, 5/20 保存値) | — | — | 46.26% (173) | 67.65% |
| vanilla (`KotodamaDecoder`) | OFF | OFF | 50.00% (187) | 73.26% |
| no-kotodama (`KotodamaDecoder`) | OFF | ON  | 49.73% (186) | 73.26% |
| full (`KotodamaDecoder`) | ON  | ON  | 50.27% (188) | 73.26% |

### Pass@1 観点 (= 型予測精度ゲーム軸): scenario A 確定

vanilla vs full 差 = 1 問 (0.27pp) → 言霊機構 (bias+firewall) の pass@1 寄与は実質ゼロ。
`docs/sampling_path_issue.md` の scenario A (修正前 +4.01pp の正体は sampler 差) 確定。

過去の Win Condition 主張 (`4a5992b` の humaneval-go +7.14pp など) は**型予測精度軸の数字**
で、機構由来とは言い切れない。判定 JSON も合わせて訂正する必要がある。

### Firewall 隔離観点 (= 本プロジェクトの主目的軸): 悪影響なしを確認

vanilla vs no-kotodama の byte-identical 検証 (= firewall toggle で出力が変わるか):

| 検証軸 | 修正前 (旧 sampler) | 修正後 (修正 A+D) |
|---|---|---|
| 出力が変わる prompt 数 | 181/374 (48.4%) | **0/374 (0.0%)** |
| completion byte-identical | — | **374/374 (100.0%)** |
| raw_completion byte-identical | — | **374/374 (100.0%)** |

pass@1 が 1 問差 (vanilla 187 / no-kotodama 186) になる理由:
- `mbpp_130_max_occurrences` で **生成コードは完全同一** だが、Go の `map[int]int` iteration
  順序が非決定的 (Go runtime が意図的にシャッフル) なため、同頻度タイ時の出力が `8` か `7`
  でフラップする
- Firewall とは無関係な Go test 実行の flakiness

### "Firewall 完成" 主張の節制

byte-identical 100% が証明したのは「firewall を入れても生成への観測可能な悪影響は無い」
までで、絶対的な Firewall 完成ではない。

- ✅ 観測レベルの物理サイドチャネル不在 (vanilla vs no-kotodama 100% byte-identical)
- ✅ L3↔L5 の型契約 (frozen dataclass) 維持 (`test_firewall_go.py` 14/14 pass)
- ❌ 修正 E (REPAIR retry loop) の隔離設計実装 — 未着手
- ❓ タイミング/メモリ等の output に出ないサイドチャネル — 未測定

正確な主張: **「Firewall が生成に悪影響を与えていないことを 374 問規模で確認。型契約は
両方向で維持。残る作業は修正 E の隔離設計実装」**。

### 訂正すべきもの

- [ ] `baselines/yamato_min_go.full.seed0_1_2.judge.json` の Win Condition ACHIEVED 主張
  → 型予測精度軸の数字で本プロジェクト評価軸ではない旨を明示。または撤回。
- [ ] `4a5992b` コミットの主張も同様 (humaneval-go の Win も sampler 差由来の可能性大)
- [x] `memory/project-firewall-purpose.md` → "byte-identical = 悪影響不在" の限定を追記済 (2026-05-21)

### 修正 E 代替: 機械的 REPAIR の試行と結果 (2026-05-21)

LLM-in-loop の REPAIR (元 修正 E プラン) は循環的処理になりがちなので、代替として
**L5 内部の機械的修復 (`goimports`)** を実装した (`scripts/eval/go_eval.py
--mechanical-repair`)。L3 (`KotodamaDecoder`) は触らず、L3→L5 経路だけを使う。
tests は repair の context に含めない (Goodhart 回避)。

| | repair OFF | repair ON |
|---|---|---|
| go build | 100% | 100% |
| go vet | 73.26% | 73.26% |
| go test | 50.00% (187) | 50.27% (188) |
| goimports applied | — | **0/374** |

**結論: mbpp-go では surface area ゼロ**。`goimports` は 1 件も適用されず、
test pass の 1 問差は `mbpp_130_max_occurrences` の Go map iteration flake
(過去確認済) で repair とは無関係。

理由: mbpp-go の prompt は既に必要 import を含む形で来るため、LM が import を
追加/削除する余地が構造的に発生しない。`build_ok=100%` (型ハルシ無し) が既に
達成されているのも同じ理由による。

実装は repository に残置 — 別 dataset (swebench 等で missing import が頻出
するもの) や別 repair 戦略 (`}` バランス補完 / `return zero_value` 挿入 / gopls
codeAction) で活きる可能性あり。隔離契約 (L3↔L5 text-only) は保持されている。

データスナップショット: `data/eval/results/mbpp-go.yamato_min_go.full.seed0.repair-ablation/`

## 過去のコミット履歴との関係

- `4a5992b` (M6 Win Condition ACHIEVED): pass@1 +7.14pp / vet +15.37pp の Win 主張。
  本 issue で根拠が揺らいでいる。verification 後に追記コミットで補足。
- `1a03acf` (mbpp-go ablation): mbpp-go の 3 mode 同点が初めて見え、attribution
  unresolved を明示した commit。**ここで気付くべきだった**。
- このコミット: code fix + 本 doc。Verification は隣のマシンで実施。

## 教訓 (memory に保存済み)

- [[feedback-ablate-before-celebrating]] — Win 数字を「理論証明」と早合点しない
- [[feedback-distinguish-symptom-from-cause]] — 「+7.14pp = bias が効いた」は表層の対応
- [[feedback-kotodama-mask-counterproductive]] — TS 版の轍は別軸の話 (今回の sampler bug とは独立)

## 関連ファイル

- 修正コード: [src_min_go/kojiki_lm/kotodama_decoder.py](../src_min_go/kojiki_lm/kotodama_decoder.py)
- 修正コード: [scripts/eval/run_yamato_min_go.py](../scripts/eval/run_yamato_min_go.py)
- baseline (変更なし): [scripts/eval/run_baseline_go.py](../scripts/eval/run_baseline_go.py)
- runbook: [scripts/runpod_bench.sh](../scripts/runpod_bench.sh)
- judge: [scripts/eval/judge_win_condition_go.py](../scripts/eval/judge_win_condition_go.py)
- 既存 judge JSON: [baselines/yamato_min_go.full.seed0_1_2.judge.json](../baselines/yamato_min_go.full.seed0_1_2.judge.json) (humaneval-go, 旧 sampler)
- 既存 judge JSON: [baselines/yamato_min_go.mbpp-go.*.judge.json](../baselines/) (mbpp-go, 旧 sampler)
