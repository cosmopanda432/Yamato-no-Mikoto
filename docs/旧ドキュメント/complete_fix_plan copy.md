# 完全修正プラン (2026-05-21)

mbpp-go ablation (2026-05-20) で **言霊 v2 機構 + Firewall は理論通りに動いていない**
ことが判明した状態を、コミットも handoff もせず**完全に修正してから commit する**
ためのプラン。

## 0. 設計の再認識 (まず最初に)

### Firewall (黄泉比良坂 / `YomotsuHirasaka`) の本来の目的

**「コード品質ゲート」ではない**。本来の目的は:

> **L3 (生成ランタイム) と L5 (評価器) の内部データ・状態が相互に干渉・汚染し合うのを、
> 型レベルで物理的に遮断する隔離壁**

実装は `L3ToL5Payload` (frozen dataclass, `text` + `step_idx` + `prompt_id` のみ)
と `L5ToL3Verdict` (Verdict enum + v_score スカラのみ) による型契約。テンソル・
hidden states・logits・評価器の内部状態は**型システムレベルで通れない**。

これを「HALT で悪い生成を止める装置」と誤認すると、`halted_early=0/374` を見て
「機能していない」と判断する誤りに陥る。HALT 不発 = 隔離壁として正常作動中
(L3↔L5 にテンソル/内部状態を流していない、毎ステップ仕事をしている)。

詳細: [memory: project-firewall-purpose](../../../../.claude/projects/c--Users-mimat-Yamato-no-Mikoto/memory/project-firewall-purpose.md)

### 言霊 (`KotodamaDecoder` + bias) の役割

`symbol-aware logit bias` で「現在 scope 内の許可シンボル token」に `+k` 加算し、
LM が**型/シンボルの選択に迷ったとき**にスコープ内の正しい選択肢へ誘導する。
`-inf` マスクではなく soft bias を採用するのは TS 版で実証された轍 ([memory:
feedback-kotodama-mask-counterproductive](../../../../.claude/projects/c--Users-mimat-Yamato-no-Mikoto/memory/feedback-kotodama-mask-counterproductive.md))。

ablation で「bias toggle で 0.8% しか出力が変わらない」は **bias が確信度の高い
位置でしか発火していなかった** ことが原因 ([memory: project-go-roadmap-state](../../../../.claude/projects/c--Users-mimat-Yamato-no-Mikoto/memory/project-go-roadmap-state.md))。

---

## 1. 既に修正したもの (ローカル、未 commit)

**コミットしていない理由**: 検証前の段階で broken な可能性がある修正を git に残すと
[memory: feedback-prove-and-handoff](../../../../.claude/projects/c--Users-mimat-Yamato-no-Mikoto/memory/feedback-prove-and-handoff.md) /
[memory: feedback-ablate-before-celebrating](../../../../.claude/projects/c--Users-mimat-Yamato-no-Mikoto/memory/feedback-ablate-before-celebrating.md)
の原則に反する。**GPU 検証で各修正が想定通り動くことが確認できてから commit**。

### 修正 A: サンプラーを transformers 公式の Warper 実装に置き換え

**何が問題だった**: `KotodamaDecoder._sample` が `temperature / top_k / top_p` フィルタ
なしに `torch.multinomial(probs, 1)` を呼んでいた。`run_baseline_go.py` の
`model.generate(..., top_p=0.95)` は transformers の内部で
`TopKLogitsWarper(50) → TopPLogitsWarper(0.95) → multinomial` を経由するため、
**同 seed/temperature でも実質異なる確率過程**となり、baseline と yamato_full の
出力が系統的に分岐していた。

私が一度手書きで top_k/top_p を実装したが、`float32` 累積加算の丸め誤差
(例: `0.8+0.1+0.05 = 0.950000047... > 0.95`) で off-by-1 が出ていた。

**修正内容**:
- [src_min_go/kojiki_lm/kotodama_decoder.py](../src_min_go/kojiki_lm/kotodama_decoder.py):
  `_sample` を以下に置き換え:
  ```python
  from transformers.generation.logits_process import (
      LogitsProcessorList, TemperatureLogitsWarper,
      TopKLogitsWarper, TopPLogitsWarper,
  )
  # __init__ で warpers を遅延構築
  # _sample で:
  scores = self._warpers(input_ids, logits)
  probs = torch.softmax(scores, dim=-1)
  return torch.multinomial(probs, 1)
  ```
- `KotodamaConfig` に `top_k: int = 50` / `top_p: float = 0.95` 追加
- `_sample(logits)` → `_sample(logits, input_ids)` シグネチャ変更
- [scripts/eval/run_yamato_min_go.py](../scripts/eval/run_yamato_min_go.py):
  `--top-k 50 --top-p 0.95` CLI 追加、KotodamaConfig に渡す

**現時点で動作確認できたこと**: `tests_go/test_kotodama_decoder_go.py` 9/9 pass。
**未確認**: 実 LM での baseline 等価性 (GPU 必須、次節 4 で検証)。

### 修正 B: kotodama_context を「難所位置」検出に絞る

**何が問題だった**: 既存 filter が `func_arg` / `func_return` を主に検出していた。
これらの位置は **LM が top-1 で 0.9+ の確信度で正解 token を選ぶ場所**で、bias
+2.0 加算しても argmax は変わらない。ablation で bias toggle が 0.8% しか出力を
変えなかった主因。

**修正内容**:
- [src_min_go/kojiki_lm/kotodama_context.py](../src_min_go/kojiki_lm/kotodama_context.py):
  `_TYPE_POSITION_HINTS` を全面改訂
  - **除外**: `func_arg`, `func_return` (LM 高確信のため bias 無意味)
  - **残置**: `var_decl`, `const_decl`, `type_alias` (`var_decl` だけは唯一 argmax を変えた実績 = cosmetic だが)
  - **新規追加**: `chan_elem`, `map_key`, `map_val`, `slice_elem`, `interface_method`,
    `type_assert`, `struct_field` (= 複合型 elem 位置、LM が迷う「難所」)
- [src_min_go/go_tools/internal/oracle/types.go](../src_min_go/go_tools/internal/oracle/types.go):
  対応する `ScopeKind` 定数を追加 (`ScopeChanElem`, `ScopeMapKey`, etc.)
- [src_min_go/go_tools/internal/oracle/scope.go](../src_min_go/go_tools/internal/oracle/scope.go):
  `detectScopeKind` に新 scope_kind の regex 検出を追加 (難所判定を AST/func_arg 判定より**優先**)
- [tests_go/test_kotodama_context_go.py](../tests_go/test_kotodama_context_go.py):
  新設計に合わせて pass/skip ケース更新 + 偽陽性 regression (`arr[i]` を slice_elem に誤検出しない) 追加
- [tests_go/test_kotodama_decoder_go.py](../tests_go/test_kotodama_decoder_go.py):
  `func a(b ` prompt を `var x ` に差し替え (新 filter に通す)

**現時点で動作確認できたこと**: Python tests 79/79 pass (7 skipped は GPU 依存)。
**未確認**: Go 側 (oracle daemon の `scope.go` 変更) の単体テスト + 動作。ローカル
には Go 未インストールのため pod / 隣マシンで `cd src_min_go/go_tools && go test ./...`。

### 修正 C: bias 加算ステップに pre/post argmax 診断 log

**目的**: bias が実際に argmax を変えているかを直接観測する診断。

**修正内容**:
- [src_min_go/kojiki_lm/kotodama_decoder.py](../src_min_go/kojiki_lm/kotodama_decoder.py)
  `_maybe_apply_bias` で bias 加算前後の top-1 token id / logit を `logger.info` で出す
  ```
  BIAS_DIAG scope=var_decl n_allowed=12  pre_top1=314 (logit=8.234, bias=2.00)
            post_top1=314 (logit=10.234)  changed=False
  ```
- これにより検証時に「bias が何ステップ中何回 argmax を変えたか」を log grep で集計可能

**修正未確認** (検証時に実際に集計する)。

---

## 2. これから修正するもの (未着手)

### 修正 D: 物理レベル非干渉化 (`torch.Generator` 分離)

**動機**: ablation で `firewall_enabled` toggle により 374 問中 **181 問 (48.4%)**
の出力が変動。Firewall の概念的な隔離 (frozen dataclass による型契約) は完璧だが、
`firewall.send()` を呼ぶ際の Python オブジェクト生成 / GC タイミング / CUDA stream
同期タイミングが微小に変わり、**CUDA RNG state が間接的に影響を受ける** サイド
チャネルリーク。

**正しい状態**: firewall toggle で出力が **byte-identical** であること
(Firewall が HALT/REPAIR で actual 介入したときだけ出力が変わる)。

**修正内容 (予定)**:
- [src_min_go/kojiki_lm/kotodama_decoder.py](../src_min_go/kojiki_lm/kotodama_decoder.py)
  `KotodamaDecoder` に `self._sampling_rng: torch.Generator` を持たせる
- `generate()` 冒頭で device-specific `Generator` を作成し、外部 seed を `manual_seed`
- `_sample` の `torch.multinomial(probs, 1)` を `torch.multinomial(probs, 1, generator=self._sampling_rng)` に
- これで sampling の確率過程は他の Python ops や firewall.send() の有無に**全く影響されない**

**注意点**: `model.generate` (baseline) は global RNG を使うので、baseline と完全 byte-identical を
狙うなら baseline 側も同じ Generator を使う必要がある。あるいは検証時には「言霊
ON/OFF」のペアで isolation を確認するだけでよい (baseline との等価性は warper で担保)。

### 修正 E: REPAIR retry loop (隔離契約を保ったままフィードバック loop 成立)

**動機**: 現在の Firewall は `Verdict.REPAIR` を返しても decoder 側で**何もしていない**
(`steps.append(step_log); continue`)。REPAIR の本来の意味「コンパイラのエラー
メッセージを L5 → L3 に **純粋テキストとして** 戻し、L3 が自律的に retry する
クリーンなループ」が未実装。

**修正内容 (予定)**:
- [src_min_go/kojiki_lm/yomotsu_hirasaka.py](../src_min_go/kojiki_lm/yomotsu_hirasaka.py)
  `L5ToL3Verdict` に `error_message: str = ""` フィールドを追加 (デフォルト空文字、隔離契約は維持: text のみ)
- [src_min_go/kojiki_lm/yomi_evaluator.py](../src_min_go/kojiki_lm/yomi_evaluator.py)
  `YomiEvaluator` に `_try_go_build(text, package_name)` を追加。subprocess で `go build` を tempdir で実行、
  stderr を捕捉してエラーメッセージを抽出。コンパイル失敗時 `Verdict.REPAIR` + `error_message` を返す。
- [src_min_go/kojiki_lm/kotodama_decoder.py](../src_min_go/kojiki_lm/kotodama_decoder.py)
  `KotodamaDecoder.generate` を**外側 retry ループ**でくるむ。`KotodamaConfig.max_retries: int = 2` 追加。
  - REPAIR + 非空 error_message を受け取ったら、prompt 末尾に
    ```
    // Previous attempt:
    <prev_completion>
    // Compiler error:
    // <error_message>
    // Try again:
    ```
    を追加して decode を再起動。
  - retry が max_retries に達するか、COMMIT/HALT が出るか、go build が通るまで継続。
- `KotodamaConfig.evaluator_use_go_build: bool = True` で ablation 可能に

**隔離契約の維持**: `error_message` は **純粋なテキスト** であり、評価器の内部状態
やテンソルは含まれない。型契約に違反しない。Goodhart 回避: error_message に
「テストの期待値」等を含めない (Evaluator 側で sanitize)。

### 修正 F: 「難所」発火率の検証データ集計

**目的**: 修正 B (難所位置) で bias がどの位置で何回発火するか、そのうち何回 argmax
を変えたか、を新ベンチ run で集計するスクリプトを準備。

**修正内容 (予定)**:
- [scripts/eval/aggregate_bias_diag.py](../scripts/eval/aggregate_bias_diag.py) (新規)
  - 生成 JSON 群と verify.log を読み、`BIAS_DIAG` 行を parse
  - 集計: 全 bias step / argmax 変化数 / scope_kind 別の発火頻度・変化率
  - 出力: 1 表形式 (markdown / TSV)

---

## 3. 動作確認 (GPU 必須)

### 環境準備

```bash
# 新 pod (A5000 推奨、A6000/A100 でも可、24GB+ VRAM)
git pull origin main  # 当面 commit していないので、後で push 後に
# OR: scp の修正ファイル群を upload

export GO_TARBALL=/workspace/go1.26.3.linux-amd64.tar.gz
export DATASET=mbpp-go
export QUANTIZE=none  # bf16 で行く

bash scripts/runpod_bench.sh setup   # Qwen DL + parquet + oracle build
```

### 検証 1: 修正 A (サンプラー等価性) の単独確認

**問い**: 修正 A 適用後、`KotodamaDecoder` の vanilla mode (bias OFF + firewall OFF)
は `run_baseline_go.py` (model.generate) と**何%出力が一致するか**?

**手順**:

```bash
# baseline は model.generate 経由 (変更なし)
bash scripts/runpod_bench.sh run baseline 0

# yamato vanilla mode = KotodamaDecoder で bias OFF + firewall OFF (修正 A 後)
bash scripts/runpod_bench.sh run vanilla 0
```

**期待**:
- 修正前: baseline と vanilla が 23% しか一致しなかった (sampler 差)
- **修正 A 後の目標**: baseline と vanilla が **95% 以上一致** (warper byte-equivalent)
- 一致率は `analysis/mbpp-go-fixed-sampler/` を作って Python で diff 集計

**判定**:
- 一致率 ≥ 95% → 修正 A 成功、sampler 等価性確立
- 一致率 < 95% → まだ何か code path 差がある。深掘り (`tokenizer.decode` per-step
  の影響、attention_mask の扱い、KV cache 経路の差等)

### 検証 2: 修正 D (物理非干渉化) の確認

**問い**: 修正 D 適用後、`firewall_enabled` の toggle で出力は byte-identical になるか?

**手順**:

```bash
bash scripts/runpod_bench.sh run vanilla 0      # bias OFF + fw OFF
bash scripts/runpod_bench.sh run no-kotodama 0  # bias OFF + fw ON
```

両者は bias 共に OFF で firewall だけが違う設定。修正 D の `Generator` 分離が効いていれば
出力は完全一致するはず。

**期待**:
- 修正前: 48.4% の問題で出力が違った
- **修正 D 後の目標**: vanilla と no-kotodama が **374/374 完全一致** (byte-identical)

**判定**:
- 完全一致 → 物理非干渉化成功
- 不一致 → さらに別のサイドチャネルがある。Python オブジェクト生成タイミング以外の
  要因 (例: `cudnn` の非決定性、`atomic` reduction op の順序) を疑う

### 検証 3: 修正 B (難所位置) の bias 発火頻度確認

**問い**: 新しい難所位置 (`chan_elem`, `map_*`, `slice_elem`, etc.) で bias が
実際に何回発火し、何回 argmax を変えるか?

**手順**:

```bash
bash scripts/runpod_bench.sh run full 0     # bias ON + fw ON
python3 scripts/eval/aggregate_bias_diag.py \
    --log /workspace/Yamato-no-Mikoto/run.log \
    --gen-dir data/eval/generated/mbpp-go.yamato_min_go.full.seed0
```

**期待**:
- 旧設計: bias_step_count ≈ 2-6 per sample、`func_arg/func_return` 主、argmax 変化 ≈ 0%
- **修正 B 後の目標**:
  - bias が新しい scope_kind (`map_val`, `slice_elem`, etc.) で発火している
  - argmax を変えた step が**有意な数** (具体的目標: 全 bias step の 10% 以上)
  - scope_kind 別の内訳が出る

**判定**:
- argmax 変化率 ≥ 10% → 新位置は LM が迷う位置として有効。次のステップへ。
- argmax 変化率 < 10% → 新位置でも LM はほぼ確信。bias_value を +2 → +5/+10 に上げる
  か、もっと違う位置を探す必要あり。

### 検証 4: 修正 E (REPAIR retry loop) の効果確認

**問い**: 修正 E 適用後、go build error を起点とした retry で pass@1 が上がるか?

**手順**:

```bash
bash scripts/runpod_bench.sh run baseline 0   # 既に取れていれば skip
bash scripts/runpod_bench.sh run full 0       # 修正 A+B+D+E すべて適用済
bash scripts/runpod_bench.sh judge full 0
```

**期待**:
- 修正 A + D で yamato 3 mode 全部が baseline 等価 (= sampler 差の lift 消失)
- 修正 B + E が**正味の機構的効果**として pass@1 を押し上げる
- **目標**: `full` の pass@1 が baseline + 5pp 以上

**判定**:
- baseline + 5pp 達成 → 「**完全修正成功、理論が数字で実証された**」
- baseline + 1〜4pp → 部分的成功、修正 B (bias 位置) or 修正 E (retry の効き目) を再調整
- baseline ± 1pp → 機構は無効。理論の根本的見直しが必要

### 検証 5: 全 ablation (mode × 1 seed)

修正 1-5 すべて適用済の状態で 4 mode 走らせ、各機構の寄与を切り分け:

```bash
bash scripts/runpod_bench.sh pilot 0   # 4 mode × seed 0
```

| Mode | bias | firewall | 期待 |
|---|---|---|---|
| baseline (`model.generate`) | — | — | reference |
| vanilla (`KotodamaDecoder`) | OFF | OFF | baseline と完全一致 (修正 A) |
| no-kotodama | OFF | ON | vanilla と完全一致 (修正 D) |
| no-firewall | ON | OFF | vanilla + bias 効果 (修正 B 由来) |
| full | ON | ON | vanilla + bias 効果 + retry 効果 (修正 E) |

これで「**どの機構がどれだけ pass@1 に寄与しているか**」が線形的に分離される。

### 検証 6: 3 seed CI で統計的有意性確認

検証 5 で full が baseline +5pp 以上を達成したら、3 seed まで広げて CI で確定:

```bash
bash scripts/runpod_bench.sh ci   # seed 1, 2 を追加
```

`baselines/yamato_min_go.mbpp-go.full.seed0_1_2.judge.json` の `win_condition.overall=true`
+ `primary.ci_lower_clears_threshold=true` まで来たら「**完全 win**」。

---

## 4. コスト・所要時間見積もり

A100 80GB pod 想定 (~$1.89/h on RunPod Secure Cloud)。

| 段階 | run | 所要 | コスト |
|---|---|---|---|
| 検証 1 + 2 (vanilla + no-kotodama + baseline) | 3 run × ~25 min | ~1.25h | ~$2.40 |
| 検証 3 (full × seed 0、診断 log 集計込) | 1 run × ~30 min + 5 min 集計 | ~0.6h | ~$1.15 |
| 検証 4 (judge) | <1 min | — | — |
| 検証 5 (pilot 4 mode × seed 0) | 4 run × ~30 min | ~2h | ~$3.80 |
| 検証 6 (3 seed 拡張) | 8 run × ~30 min | ~4h | ~$7.60 |
| **小計 (検証 1-5 のみ)** | 8 run | **~4h** | **~$7.50** |
| **完全 win 確定まで (3 seed 込)** | 16 run | **~8h** | **~$15** |

A5000 24GB なら速度ほぼ同等 (memory bandwidth 同じ) で **$0.30/h** なので $2-3 で
完了する見込み ([memory: project-runpod-gpu-choice](../../../../.claude/projects/c--Users-mimat-Yamato-no-Mikoto/memory/project-runpod-gpu-choice.md))。
A100 を選ぶ必要は無い (というか A5000 のほうがコスパ良)。

---

## 5. commit 戦略 (検証完了後)

検証 1-6 が**すべて合格**して初めて commit。一括ではなく以下の論理単位で分割:

1. **Solution 1 commit**: `_sample` を transformers Warper 直使いに置き換え (vanilla=baseline 一致を verify した数字を commit message に明記)
2. **Solution 3 commit**: kotodama_context + scope.go の難所位置検出 (新位置での発火・argmax 変化率を commit message に明記)
3. **Solution D commit**: torch.Generator 分離 (firewall toggle で byte-identical の証拠を明記)
4. **Solution 2 commit (旧名 E)**: REPAIR retry loop (pass@1 改善数字を明記)
5. **メタ commit**: `docs/complete_fix_plan.md` (このドキュメント) + `docs/sampling_path_issue.md` を**最終結果で書き直して** archive
6. **Win Condition 訂正 commit**: 旧 `baselines/yamato_min_go.full.seed0_1_2.judge.json` (humaneval-go 3 seed) を**新 sampler で再生成**して上書き。`commit 4a5992b` の主張が訂正される

検証中に各修正が **fail** したら commit せず、修正のテコ入れに戻る。

---

## 6. 関連 memory (前提として読んでおく)

- [feedback-kotodama-mask-counterproductive](../../../../.claude/projects/c--Users-mimat-Yamato-no-Mikoto/memory/feedback-kotodama-mask-counterproductive.md) — `-inf` マスクは TS 構文と相性が悪い (TS 限定の現象、Go は別軸)
- [feedback-distinguish-symptom-from-cause](../../../../.claude/projects/c--Users-mimat-Yamato-no-Mikoto/memory/feedback-distinguish-symptom-from-cause.md) — 表層と本質を区別する
- [feedback-ablate-before-celebrating](../../../../.claude/projects/c--Users-mimat-Yamato-no-Mikoto/memory/feedback-ablate-before-celebrating.md) — Win 数字を「理論証明」と早合点しない
- [feedback-prove-and-handoff](../../../../.claude/projects/c--Users-mimat-Yamato-no-Mikoto/memory/feedback-prove-and-handoff.md) — 動かない処理は repo に残さない
- [project-firewall-purpose](../../../../.claude/projects/c--Users-mimat-Yamato-no-Mikoto/memory/project-firewall-purpose.md) — Firewall は L3↔L5 隔離壁、HALT/REPAIR は副次的
- [project-runpod-gpu-choice](../../../../.claude/projects/c--Users-mimat-Yamato-no-Mikoto/memory/project-runpod-gpu-choice.md) — A5000 が推論ベンチでは最適コスパ
- [project-go-roadmap-state](../../../../.claude/projects/c--Users-mimat-Yamato-no-Mikoto/memory/project-go-roadmap-state.md) — 現状スナップショット (2026-05-20、attribution 未解決)
