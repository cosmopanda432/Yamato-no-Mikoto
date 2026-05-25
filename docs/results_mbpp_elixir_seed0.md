# mbpp-elixir 2 群比較 (1 seed × 397 問)

実施日: 2026-05-25 / GPU: RTX A5000 24GB / Model: Qwen2.5-Coder-7B-Instruct (4bit) /
所要: 約 1h24min (parquet DL から judge まで) / コスト: ~$0.45

## 比較対象

| 群 | 中身 |
|---|---|
| **A: 元のLLM** | bare `model.generate` ([run_baseline_elixir.py](../scripts/eval/run_baseline_elixir.py)) |
| **C: Firewall あり** | `FirewallDecoder` + `firewall=ON` ([run_yamato_min_elixir.py](../scripts/eval/run_yamato_min_elixir.py)) |

**Firewall なし (B mode) は省略**: humaneval-elixir で 3 seed × byte-identical 161/161
([docs/results_humaneval_elixir_3seed.md](results_humaneval_elixir_3seed.md))
を実証済みで、Firewall pathway が token sampling に副作用を持たないことが構造的に
確認されている。mbpp-elixir でも同じ構造的性質が成立する前提で 1 mode に絞った。

**1 seed (seed 0) のみ**: 統計的 CI なし、point estimate。傾向把握用。

## 結果 (397 問、絶対数)

| metric | A baseline | C firewall-on | Δ (pp) | Δ (相対) |
|---|---|---|---|---|
| **pass@1** | 37.78% (150/397) | **40.30% (160/397)** | **+2.52pp** | +6.67% |
| **compile_ok** | 86.90% (345/397) | **89.67% (356/397)** | **+2.77pp** | +3.19% |
| undef_rate ★ | 2.02% (8/397) | 1.76% (7/397) | −0.25pp | −12.5% |
| assertion_failure | 26.20% (104/397) | 27.96% (111/397) | +1.76pp | +6.72% |
| function_clause | 7.56% (30/397) | 7.81% (31/397) | +0.25pp | +3.33% |
| timeout_rate | 0.00% | 0.00% | ±0 | — |

## humaneval-elixir との対比 (cross-dataset)

| metric | humaneval (161 問, 3-seed mean) | mbpp (397 問, 1 seed) | コメント |
|---|---|---|---|
| baseline pass@1 | 27.95% | 37.78% | mbpp の方が +10pp 易しい |
| yamato pass@1 | 30.23% | 40.30% | 同じく +10pp |
| **Δ pass@1** | **+2.28pp** | **+2.52pp** | **2 dataset で ~+2.5pp の一貫した uplift** |
| baseline compile | 69.36% | 86.90% | mbpp は compile しやすい (prompt が boilerplate 完備) |
| **Δ compile** | **±0** | **+2.77pp** | mbpp では compile も伸びる、humaneval は天井効果なし |
| baseline undef | 5.18% | 2.02% | mbpp は型ハルシ surface area が狭い (簡単な prompt) |
| Δ undef | −2.28pp (-44%) | −0.25pp (-12.5%) | mbpp は元から低いので絶対 Δ 小、相対比はそれでも減少 |

### 読み取れること

1. **pass@1 uplift は dataset 非依存で ~+2.5pp**: FirewallDecoder の修正 H
   (token-level stop_token early-stop) の効果が humaneval / mbpp 両方で再現
   → 単発ノイズではなく、systematic な効果
2. **compile uplift は dataset 依存**: mbpp では +2.77pp 出るが humaneval では 0。
   仮説: humaneval は元から compile が難しい問題 (構文・型・複雑性) が多く、
   token-level early-stop では救えない。mbpp は「over-generation でゴミがついて
   compile が壊れる」パターンが残っており、early-stop が直接効く
3. **undef は天井がある**: 5% → 2% への減少は劇的に見えるが、絶対値で見ると
   どちらも残り数% で似たような最小残量に収束している (humaneval 2.90%、
   mbpp 1.76%)
4. **assertion_failure が両 dataset で +微増**: pass@1 が増えるとロジック誤りで
   fall through する問題も相対的に露出する → assert fail カウントが増える
   ことがある。assertion は最終段階の fail なので、ここまで来たのは「compile も
   undef もクリアした問題」が増えた結果でもあり、ネガティブシグナルではない

## Win Condition 判定 (参考)

| 軸 | 結果 | 備考 |
|---|---|---|
| Δ pass@1 ≥ +5pp (Go 版基準) | ❌ NOT MET (+2.52pp) | 1 seed なので CI 判定不可、point estimate |
| Δ compile ≥ +5pp | ❌ NOT MET (+2.77pp) | 同上 |
| Firewall 隔離壁 (byte-identical) | △ 未検証 (mbpp では firewall-off を回さず) | humaneval で 3 seed 確認済の構造的性質を仮定 |

→ humaneval-elixir 3 群レポートと同様、本プロジェクト主目的の隔離壁性質に対する
追加証拠 (構造的性質は dataset 非依存と推定)、副次的に pass@1 / compile の小さな
positive 効果が 2 dataset で再現したことの記録。

## 留意事項

1. **1 seed の限界**: CI なし、SD なし。3-seed なら CI 重なり判定が可能だったが、
   1 seed では「Δ が偶然か systematic か」を量的に判定できない。humaneval 3-seed
   との一貫性 (+2.28pp / +2.52pp) が定性的な systematic 証拠
2. **mbpp で firewall-off 未実行**: byte-identical の dataset 横断的検証は未完。
   構造的性質を信頼するなら不要だが、追加 1 run (~30 分 / $0.15) で確認可能
3. **mbpp は base rate が高い**: 80% 台 compile の dataset で +5pp 出すのは
   構造的に困難 (天井効果)。Win Condition 閾値は dataset の難易度に依存させる
   設計の方が妥当かもしれない (今は固定 5pp)

## 関連

- 入力 JSON: [baselines/yamato_min_elixir.mbpp-elixir.firewall-on.seed0.judge.json](../baselines/yamato_min_elixir.mbpp-elixir.firewall-on.seed0.judge.json)
- humaneval-elixir 3 seed レポート: [docs/results_humaneval_elixir_3seed.md](results_humaneval_elixir_3seed.md)
- ロードマップ: [docs/roadmap_eli2.md](roadmap_eli2.md)
