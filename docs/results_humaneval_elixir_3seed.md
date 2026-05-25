# humaneval-elixir 3 群比較 (3 seed × 161 問)

実施日: 2026-05-25 / GPU: RTX A5000 24GB / Model: Qwen2.5-Coder-7B-Instruct (4bit) /
所要: 約 2h08min (clone + setup から ci 完了まで) / コスト: ~$0.65

## 比較対象

| 群 | 中身 | 何を測る |
|---|---|---|
| **A: 元のLLM** | bare `model.generate` ([run_baseline_elixir.py](../scripts/eval/run_baseline_elixir.py)) | プレーンな Qwen2.5-Coder-7B Elixir 性能 |
| **B: Firewall なし** | `FirewallDecoder` + `firewall=OFF` ([run_yamato_min_elixir.py](../scripts/eval/run_yamato_min_elixir.py)) | FirewallDecoder の code path 効果 (修正 H: token-level stop_token early-stop) |
| **C: Firewall あり** | `FirewallDecoder` + `firewall=ON` | + Firewall (黄泉比良坂、L3↔L5 隔離壁) の効果 |

## 一次結果 (3 seed mean ± 95% CI、t 分布 df=2)

| metric | A baseline | B firewall-off | C firewall-on | Δ (B−A) |
|---|---|---|---|---|
| **pass@1** (PRIMARY) | 27.95% ± 2.67pp | **30.23% ± 4.45pp** | **30.23% ± 4.45pp** | **+2.28pp** |
| compile_ok (SECONDARY) | 69.36% ± 3.21pp | 69.36% ± 9.04pp | 69.36% ± 9.04pp | +0.00pp |
| **undef_rate** ★ | 5.18% ± 0.89pp | **2.90% ± 0.89pp** | **2.90% ± 0.89pp** | **−2.28pp** |
| assertion_failure | 20.08% ± 3.56pp | 21.53% ± 8.77pp | 21.53% ± 8.77pp | +1.45pp |
| function_clause | 6.21% ± 3.09pp | 6.42% ± 0.89pp | 6.42% ± 0.89pp | +0.21pp |
| timeout_rate | 0.00% | 0.62% | 0.62% | +0.62pp |

★ undef_rate は型ハルシネーション (`UndefinedFunctionError` / module not loaded 等) の発現率。
減少が好ましい ([feedback-type-prediction-is-hallucination-detection](C:/Users/mimat/.claude/projects/c--Users-mimat-Yamato-no-Mikoto/memory/feedback-type-prediction-is-hallucination-detection.md))。

## per-seed 詳細

| seed | A pass@1 | B/C pass@1 | A compile | B/C compile | A undef | B/C undef |
|---|---|---|---|---|---|---|
| 0 | 26.71% | 29.19% | 68.32% | 72.05% | 5.59% | 2.48% |
| 1 | 28.57% | 32.30% | 68.94% | 70.81% | 4.97% | 3.11% |
| 2 | 28.57% | 29.19% | 70.81% | 65.22% | 4.97% | 3.11% |

## ★ Firewall 物理隔離 (B vs C) の検証

**Result: 3/3 seed で B == C byte-identical**

[baselines/yamato_min_elixir.humaneval-elixir.firewall-off.seed0_1_2.judge.json](../baselines/yamato_min_elixir.humaneval-elixir.firewall-off.seed0_1_2.judge.json)
と
[baselines/yamato_min_elixir.humaneval-elixir.firewall-on.seed0_1_2.judge.json](../baselines/yamato_min_elixir.humaneval-elixir.firewall-on.seed0_1_2.judge.json)
は `"mode"` フィールド以外 **完全一致** (per_seed の各値が float レベルで bit-for-bit 同一)。

これは Firewall pathway が生成 token に物理サイドチャネルを持たないこと
= **黄泉比良坂 (L3↔L5 隔離壁) が token sampling path に副作用を与えない**
という構造的性質を、seed 0/1/2 すべてで実測確認した結果。

Go 版 mbpp-go 374/374 ([sampling_path_issue.md](sampling_path_issue.md)) の Elixir target
再現 ([project-firewall-purpose](C:/Users/mimat/.claude/projects/c--Users-mimat-Yamato-no-Mikoto/memory/project-firewall-purpose.md))。

## 解釈

### 1. Firewall (C vs B) — 一次基準

**Δ = 0 (byte-identical) ✅**

Firewall ON/OFF で生成が変わらない = Firewall は隔離契約として機能し、LM 性能には
干渉しない。これが本プロジェクトの **一次基準達成** ([docs/roadmap_eli2.md:128](roadmap_eli2.md#L128))。

### 2. FirewallDecoder vs bare model (B vs A) — 二次基準

**Δ pass@1 = +2.28pp / Δ undef = −2.28pp**

bare `model.generate` から `FirewallDecoder` (= decode loop + token-level
stop_token early-stop、修正 H) に切り替えただけで:
- pass@1: 27.95% → 30.23%
- undef_rate: 5.18% → 2.90% (44% 減少)
- compile_ok: 変わらず

undef_rate の半減は、token-level early-stop が「LM が次の関数を勝手に生成し始めて
未定義シンボルを呼ぶ」現象を抑制している signal と整合的。

**ただし 95% CI で見ると**:
- pass@1 Δ +2.28pp、CI 重なり (A CI=[25.28, 30.62] vs B CI=[25.77, 34.68])
- → 統計的有意性は弱い (3 seed では SE が大きく n=3 t-dist の CI が広い)
- 「+5pp 閾値」は Go 版の full mode (kotodama+firewall) 想定で書かれており、
  本構成 (kotodama 撤去後、FirewallDecoder only) には適用しない方が妥当

### 3. Win Condition 判定

| 軸 | 要件 | 結果 |
|---|---|---|
| **一次** Firewall byte-identical (3 seed) | C ≡ B 完全一致 | ✅ **MET** |
| **二次** 非後退 (regression なし) | B/C のいずれの指標も A を有意に下回らない | ✅ **MET** (どの metric も Δ ≥ 0 or 微増) |
| (副次) Δ pass@1 ≥ +5pp (Go 版基準) | CI 下限が +5pp を超える | ❌ NOT MET (Δ=+2.28pp、3 seed の SE 大) |

→ 本プロジェクト主目的 ([project-firewall-purpose](C:/Users/mimat/.claude/projects/c--Users-mimat-Yamato-no-Mikoto/memory/project-firewall-purpose.md))
の Win Condition (Firewall 隔離壁の構造的性質) は **達成**。
LM 性能向上 (+5pp) は副次基準で未達だが、+2.28pp / −2.28pp undef という小さな正の
シグナルは確認。

## 留意事項

1. **n=3 seed の限界**: t 分布 df=2 で CI 倍率 ~4.30、SE が大きく出る (yamato 側
   compile の SD が 3.64% → CI 幅 ±9pp)。Δ pass@1 +2.28pp が有意かどうかは、
   この標本サイズでは判定困難。3 seed は最小要件であって、効果検出力ではない
2. **timeout_rate 0.62% (1/161, 3 seed すべて)**: yamato 側のみ発生。同じ問題
   (おそらく 1 問が token budget 上限まで生成して 5s timeout) が 3 seed 共通で
   発生 → 構造的に再現するので調査価値あり (ただし pass@1 影響は限定的)
3. **compile_ok の 3 seed 平均一致 (69.36% 完全一致)**: 偶然の数値一致 (per_seed
   は異なる [68.32, 68.94, 70.81] vs [72.05, 70.81, 65.22])。誤読しないこと

## 関連

- 入力 JSON:
  - [baselines/yamato_min_elixir.humaneval-elixir.firewall-off.seed0_1_2.judge.json](../baselines/yamato_min_elixir.humaneval-elixir.firewall-off.seed0_1_2.judge.json)
  - [baselines/yamato_min_elixir.humaneval-elixir.firewall-on.seed0_1_2.judge.json](../baselines/yamato_min_elixir.humaneval-elixir.firewall-on.seed0_1_2.judge.json)
- 旧版 (seed 0 only): [baselines/yamato_min_elixir.humaneval-elixir.firewall-{off,on}.seed0.judge.json](../baselines/)
- ロードマップ: [docs/roadmap_eli2.md](roadmap_eli2.md)
