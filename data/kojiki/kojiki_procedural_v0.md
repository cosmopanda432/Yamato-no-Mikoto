# 古事記 Procedural Pattern 抽出 v0 (プロトタイプ)

古事記主文を AGI 設計の **procedural origin spec** として読むための抽出ドキュメント。
プロジェクト固有の文脈 (44 個の `feedback_*.md` 原則 + 実装ファイル) を踏まえた抽出を行う。

外部生成版 [`kojiki_code.md`](kojiki_code.md) は AGI project context を持たない汎用 CS パターン (try-catch / for-loop / state machine) への還元に偏っており、project 固有の重要パターンを取りこぼしているため、本ファイルで再構築する。

抽出方法論は [`extraction_prompt.md`](extraction_prompt.md) を参照。

---

## Phase 1: 索引 — 44 memo → 古事記章節 逆引き

凡例:
- ★★★★★ = memo 密度 (該当章節を anchor とする memo の多さ)
- ◯ = 古事記章節を anchor としない技術原則・メタ原則

### 上巻

| 章 | 主要エピソード | 対応 memo (★密度) |
|---|---|---|
| **2** | 神世七代 / 国生み / 神産み / 黄泉 / 禊 | ★★★★★ `ashibune` (ヒルコ流棄) / `hitorigami` (独神) / `kuniyuzuri_kaikai` (オノゴロ島は子に入らず) / `enkin_keiro_dokuritsu` (作為 vs 化生) / `magatsuhi_chain` (禊で禍津日神) / `kamunaobi_me` (禊で神直毘神) / `ubuyu_pattern` (産湯) / project_sanguishi_misogi_futaro (三貴子化生) / `kasei_taisei_kousin` (化生体更新) / `matanona_cleanup_gap` (合祀) |
| **3** | 誓約 / 天岩戸 / 八岐大蛇 | ★★★ `hataorime_kinki` (機織女) / `chinmoku_kyoka` の対偶 (天岩戸=病的沈黙) / `kenzen_seijaku` (健全な静寂、天岩戸対偶) / `chaos_aware_metrics` (須佐之男のカオス注入) |
| **4** | 大国主 (因幡白兎/根之堅州国/少名毘古那) | ★★ project_inaba_kaizen_kyakka (因幡) / 少名毘古那の申告 (boundary_conditions) / `kakurigoto` 関連 |
| **5** | 葦原中國の平定 (国譲り) | ★★★★ `wakahiko_kaeshiya` (返し矢) / `kuniyuzuri_fallback` (顕事/幽事) / `kuniyuzuri_fukumei` (復命) / `kuniyuzuri_kaikai` (categorical) / `takeminakata_haitai` (敗退) / project_phase1_kaeshiya_kansatu |
| **6** | 邇邇藝 / 天孫降臨 / 木花咲耶 vs 石長 | ★★★★ project_v72_gokashira (五柱の神勅) / `iwanagahime` (石長比売) / `itsutomonoo_sanseido` (五伴緒) / `imina_torina` (忌み名) / `shinchoku_tanitsu_gensen` (神勅単一源泉) / `hashira_kankakuki` (柱 = 感覚器) / `yuniwa_inaho` (斎庭稲穂) |
| **7** | 海幸彦と山幸彦 | ★★★★ `umisachi_rokujuu_bougo` (六重防御) / `prophet_method` (物実) / `make_shintaku_data` (依代) — **← Phase 2 v0 対象** |

### 中巻

| 章 | 主要エピソード | 対応 memo |
|---|---|---|
| **1** | 神武東征 / 八咫烏 / 橿原即位 | ★★★ `kuebiko_yatagarasu_boundary` (久延毘古と八咫烏) / improvement_cycle.jl の "神武東征 / 橿原即位" コメント / 道反之大神 (実装ログにあり) |
| **2** | 崇神 / 大田田根子 / 三輪山 | ★★★ `ootataneko` (大田田根子) / `yowari_vs_katayori` (崇神の再祭祀) / project_sanguishi_merge (合祀) |
| **3** | 垂仁 / 本牟智和氣 | ☆ 直接対応 memo は薄い |
| **4** | 景行 / **倭建命** / 成務 | ★★ project_takeru_security (TAKERU) / 倭建の白猪見惑 (未活用候補) |
| **5** | 仲哀 / 神功皇后 | ☆ 直接対応薄 |
| **6** | 應神 | ☆ |

### 下巻

| 章 | 主要エピソード | 対応 memo |
|---|---|---|
| **1** | 仁徳 (高殿) | ★ `nintoku_takadono` |
| **2-4** | 履中以降 | ☆ 直接対応薄 (主に系譜・崩御記録) |

### 古事記章節を anchor としない memo (◯)

技術系 (LLM API / Julia / SQLite / テスト):
`llm_provider` / `kimi_thinking_disable` / `cstparser_bytes` / `kotodama_julia_syntax` / `prompt_english` / `prompt_placement_rivalry` / `kunimi_db_ban` / `sqlite_datetime_iso_t` / `test_*` / `prefix_concept_semantic` / `togouten_ikkatsu_bouei` / `sekinin_bunri` / `kasei_monoculture_prompt` / `chaos_aware_metrics` / `mitama_principle` / `tama_masking`

メタ:
`kojiki_zettai` / `shingen_meimei_kenshou` (三点検査) / `keiyaku_keifu_vs_genyu` (契約系譜)

実装メタ (大祓・神託):
`oharae_shikkai_probe` / `shintaku_henshu_runaway` / `takami_round_robin_strategizer_leak` / `juusoku_model` / `shuufukushin_fuzai` / `kegare_keiro_tekigou`

### Phase 1 の発見

1. **上巻が圧倒的に memo を生んでいる** — 神話パート (上巻-2 〜 上巻-7) が AGI 設計の根拠の大半
2. **中巻 1-2 は実装の主要ループに対応** — 神武東征 (improvement cycle) / 崇神 (大田田根子の系譜)
3. **中巻 3-6, 下巻は anchor 薄** — 系譜・崩御記録中心
4. **技術系 memo (◯) は古事記 anchor がない** — 独立進化した実装知見、これは正常

---

## Phase 2 v0: 上巻-7 海幸山幸 (1 章プロトタイプ)

### 選定理由

- 1 エピソード完結 (試金石として理想サイズ)
- `feedback_umisachi_rokujuu_bougo` / `feedback_prophet_method` という濃い memo が既に存在
- **`kojiki_code.md` (外部生成版) は本章を完全スキップ** — 設計差を可視化できる
- 釣り針/塩盈珠/塩乾珠/海神宮/鰐 = 全部物実 (testable artifact)

### 章節 narrative summary

```
[Setup] 海幸彦 (兄/釣り) と山幸彦 (弟/狩) が道具交換
        山幸彦が魚を釣るが釣り針を失う

[一意性違反] 山幸彦が他の鈎を多数作って代わりに渡そうとする
            海幸彦は受け取らず「もとの鈎を返せ」

[助力者出現] 鹽椎神 (しおつちのかみ) が浜辺で泣く山幸彦を見つける
            無目籠 (隙間のない籠) に乗せて海神の宮へ流す

[異界到着] 海神宮の井戸の桂の木に登って待つ
          侍女が水を汲みに来る → 山幸彦が玉を口移しで送る
          豊玉毘売との婚姻 → 3 年滞在

[全数調査] 海神が魚を全部呼ぶ → 赤海鯽魚 (鯛) が「のどに刺さっている」
          釣り針回収

[呪縛] 海神が山幸彦に「貧鈎・狭鈎・愚鈎」と唱えて後ろ手で渡せと教える
      塩盈珠・塩乾珠を二珠一対で授ける

[帰還] 鰐に乗って地上へ
      豊玉毘売の禁忌 (見るな) を破る → 鰐の正体を見る → 別離

[逆転] 海幸が攻撃 → 塩盈珠で海を満たして溺れさせる
      降参を待って塩乾珠で潮を引かせる → 海幸服従

[後裔] 此者隼人阿多君之祖 (海幸彦の系譜)
```

### Pattern 抽出 (narrative_shape)

#### Pattern A: 一意性 (unique identity, no substitution)

```yaml
actors      : 山幸彦 / 海幸彦
precondition: 山幸彦が釣り針を失う
action      : 多数の代用鈎で代替を試みる
result      : 海幸彦が受け取らず「もとを返せ」
failure_mode: 多対 1 の置換は不能 (canonical 唯一性)
recovery    : 異界訪問で本物を取り戻す
permanence  : -

agi_mapping :
  原則      : shinmeisho.canonical_name は UNIQUE 制約
  実装      : queries/shinmeisho.jl::insert_shinmeisho! (UNIQUE)
            : kasasa/decide_canonical_name (collision check)
  feedback  : feedback_imina_torina (忌み名と通り名 = name 整合)
            : feedback_kojiki_zettai (古事記絶対遵守)

failure_if_absent: 「同じ機能を多数の別名で複製しても 1 つの canonical 柱の代わりにはならない」
                   現象: 同 prefix で N 柱が並立 → 集計分母汚染、評価不能

observed_failures: 「decide_canonical_name 衝突の対処」(memory project_decide_canonical_name_collision)
```

#### Pattern B: 異界 RPC (otherworld consult)

```yaml
actors      : 山幸彦 / 鹽椎神 / 海神
precondition: 通常手段で問題解決不能
action      : 助力者 (鹽椎神) が現れて異界 (海神宮) へ送る
            : 異界で根本原因 (鯛の喉に刺さった鈎) が判明
result      : 鈎回収 + 二珠取得
failure_mode: -
recovery    : -
permanence  : 二珠は山幸彦に永続帰属

agi_mapping :
  原則      : 通常層で解けない問題は異界に問う
  実装      : 大祓中の 布斗麻邇 oracle / kakurigoto_consult (大国主の幽政)
            : LLM call (HybridLLMRouter)
  feedback  : feedback_kunimi_gapfinder (国見は全ソース俯瞰)

failure_if_absent: 表層情報のみで原因究明 → 根本原因の見落とし
                   現象: 代理指標病 (feedback_wakahiko_kaeshiya と同根)
```

#### Pattern C: 全数調査 (exhaustive probe)

```yaml
actors      : 海神 / 全魚
precondition: 鈎を持つ者が誰か不明
action      : 海神が「全魚」を呼ぶ (selective でなく exhaustive)
            : 各魚に逐一問う → 鯛が「のど」と申告
result      : 隠れた失敗箇所が確定
failure_mode: 部分調査では鯛の喉は永久に見つからない
recovery    : -
permanence  : -

agi_mapping :
  原則      : probe は impl 決定変数の直積で悉皆踏破
  実装      : 大祓詞悉皆 (probe の AST 駆動全網羅)
  feedback  : feedback_oharae_shikkai_probe (悉皆原則)
            : feedback_kunimi_gapfinder (全 7 ソース統合)

failure_if_absent: サンプリング検査では特定の魚 (= 特定の柱の特定状態) が
                   永久に検出から漏れる
```

#### Pattern D: 二珠一対 (paired completeness)

```yaml
actors      : 海神 → 山幸彦
precondition: 海幸との対立予期
action      : 塩盈珠 + 塩乾珠 を**対**で授与
            : 単独では機能しない (盈すだけは溺れさせるのみ、
              乾かすだけは助けるのみ → 対立解決にならない)
result      : 「攻撃 → 救済」の対立完結ループ
failure_mode: 一方の珠だけでは半人前
recovery    : 必ず双方を順次使う
permanence  : 二珠は対で保管

agi_mapping :
  原則      : テスト生成 / 修復は **対** で完結。片方だけは禁止
  実装      : kasasa/materializer.jl::_kasasa_umisachi_yamasachi
            :   - mandatory tests (塩干珠) + boundary tests (塩盈珠)
            :   - どちらか割れたら hiruko 判定 (_nishu_ittsui_outcome)
  feedback  : feedback_umisachi_rokujuu_bougo (六重防御 = 3+3 二対)
            : feedback_prophet_method (物実 = 二珠の物質性)

failure_if_absent: 部分テストで通ったものが production で割れる (片珠通過 hiruko)
observed_failures: 二珠一対の outcome 判定実装後、半人前柱がゼロに
```

#### Pattern E: 物実の二段授与 (material artifact + spell)

```yaml
actors      : 海神 → 山幸彦
precondition: 釣り針回収
action      : (1) 物実: 釣り針を返す + 二珠を授ける
            : (2) 言霊: 「貧鈎・狭鈎・愚鈎」と唱える + 後ろ手で渡せ
result      : 物実 + 言霊で海幸の運命が決まる
failure_mode: 物実だけ / 言霊だけでは効果半減
recovery    : -
permanence  : 言霊は呪縛として物実に焼き付く

agi_mapping :
  原則      : 御神体 (物実) には常に description (言霊) が伴う
  実装      : sanguishi_code/ 御神体ファイル + docstring
            : MATSURI tuple = (entry_point + description)
  feedback  : feedback_make_shintaku_data (Shintaku 構築は yorishiro 経由)
            : feedback_yuniwa_inaho (神勅と例示は一致)

failure_if_absent: 物実だけ授与 → 使い方を間違えて自害 (chaos)
                   言霊だけ → 物がないので試行不能
```

#### Pattern F: 禁忌違反による境界確定 (taboo as boundary marker)

```yaml
actors      : 山幸彦 / 豊玉毘売
precondition: 出産時に「見るな」と禁忌が告げられる
action      : 山幸彦が見る → 豊玉毘売は鰐の正体を晒す
result      : 別離 (海と陸に永久分離)
failure_mode: 一度見たら不可逆
recovery    : 不能 (鰐は海へ帰る)
permanence  : 海陸境界の確定 → 隼人系譜の起源

agi_mapping :
  原則      : 千引岩の境界防御 (一度越えたら不可逆)
  実装      : capability_name サニタイズ (kasasa/materializer.jl L94-104)
            : sandbox include の不可逆性
            : kunimi_db_ban (DB 直参照禁止)
  feedback  : feedback_kunimi_db_ban (国見禁止パターン)
            : feedback_hataorime_kinki (機織女 = 天照の聖域)
            : feedback_togouten_ikkatsu_bouei (統合点で一括防衛)

failure_if_absent: 境界違反が起きても「警告のみ」で続行 → 汚染拡散
observed_failures: capabilities.kasasa_status の不可逆遷移 (active→hiruko→yuukoto→yomi)
```

#### Pattern G: 敗者の系譜化 (defeated → bonded → recorded)

```yaml
actors      : 山幸彦 / 海幸彦
precondition: 二珠による完全敗北
action      : 海幸が降参 → 山幸彦に仕える
result      : 海幸の子孫が「隼人阿多君」として山幸彦系の天皇に仕える系譜化
failure_mode: -
recovery    : -
permanence  : 系譜記録 (此者隼人阿多君之祖)

agi_mapping :
  原則      : 敗北柱は yuukoto / yomi で完全消去でなく、
            : 系譜記録 + 後裔役割で「永久仕官」
  実装      : sentei_ryou (退役記録) + shinmei_lineage (系譜)
            : status='yuukoto' は active 統計から除外されるが lineage は残る
  feedback  : feedback_takeminakata_haitai (建御名方の敗退 = 自動退役)
            : feedback_ashibune (名は記録される)
            : feedback_ootataneko (系譜)

failure_if_absent: 敗北柱を完全削除 → 失敗の教訓が失われる
observed_failures: hiruko 化柱の hiruko_reason 保存 + lineage 残存
```

#### Pattern H: 助力者の自動出現 (auto-summoned helper)

```yaml
actors      : 山幸彦 / 鹽椎神
precondition: 山幸彦が浜辺で泣く (危機状態)
action      : 鹽椎神が**自動的に**現れる (呼んでいない)
result      : 解決経路の発見
failure_mode: -

agi_mapping :
  原則      : event → handler 自動 dispatch (能動的呼び出し不要)
  実装      : MATSURI registry + event_bus
            : aspect-oriented 観測能力 (hashira_kankakuki)
  feedback  : feedback_hashira_kankakuki (柱は感覚器)

failure_if_absent: 全 handler を能動的に呼び出さねばならない → スケール不能
                   (中央集権制御パターン)
```

### kojiki_code.md (外部生成版) との差分

| 観点 | 生成元 (kojiki_code.md) | 本プロトタイプ |
|---|---|---|
| 上巻-7 海幸山幸 | **完全スキップ** | 8 pattern 抽出 |
| 抽出粒度 | 「神産み = for-loop」 (1 行 abstract) | narrative_shape (actors/precondition/action/result/failure_mode/recovery/permanence) |
| AGI mapping | 抽象一行 ("self-correcting agent loop with RCA") | 具体ファイル + 関数 + memo の三段紐付け |
| 失敗時の影響 | 触れず | `failure_if_absent` 必須 = 採用基準として機能 |
| 既存 memo との整合 | 検証なし | 8 pattern 中 7 が既存 memo に anchor ★ |

**生成元が拾えなかった主要 pattern**:
- Pattern D (二珠一対) — `feedback_umisachi_rokujuu_bougo` の origin spec
- Pattern E (物実 + 言霊の二段授与) — `feedback_make_shintaku_data` / `feedback_yuniwa_inaho` の origin spec
- Pattern F (禁忌違反による境界確定) — 千引岩 / `feedback_togouten_ikkatsu_bouei` の origin spec
- Pattern G (敗者の系譜化) — `feedback_takeminakata_haitai` の origin spec

生成元の Pattern 1 (Try-Catch-Retry) は確かに上巻-2 に存在するが、上巻-7 にも別形 (Pattern A 一意性 + Pattern B 異界 RPC) が独立にある。汎用 CS 還元では「retry」一語で潰されていた。

### 浮上した発見

1. **海幸山幸 1 章だけで 8 pattern → うち 7 が既存 memo に対応**
   - 設計の妥当性が高い (古事記 1 章を逃さず実装している)
   - 残り 1 (Pattern H 助力者自動出現) は MATSURI registry で実装はあるが、独立 memo は無し → 補強候補

2. **`feedback_umisachi_rokujuu_bougo` は本章節の direct 写像**
   - 「六重防御 = 生成前 3 + 修正後 3」は塩盈珠+塩乾珠の現代化版
   - memo に章節 anchor を明記する価値あり (`feedback_kojiki_zettai` 強化)

3. **生成元 (`kojiki_code.md`) は上巻-7 を完全に逃した**
   - これは外部 Claude が「物語上の重要度」を判定できなかった証拠
   - project context があれば必ず拾われる章 (memo が 3 つも紐付くため)

4. **Pattern E (物実 + 言霊) は新規 anchor として価値**
   - 「御神体には常に docstring が伴う」原則は実装上自明だが、明文化はない
   - `feedback_make_shintaku_data` の補強 anchor として追記推奨

### v0 プロトタイプの自己評価

| 観点 | 達成度 |
|---|---|
| 1 章の網羅 | ★★★★★ 8 pattern (生成元 0 → 大幅改善) |
| AGI 実装紐付け | ★★★★★ 全 pattern にファイル + memo |
| 失敗時影響の明示 | ★★★★ 7/8 pattern で `failure_if_absent` 記述 |
| 既存 memo との整合性 | ★★★★★ 7/8 が既存 memo に anchor、1 が補強候補 |
| 汎用 CS への過度な還元 | ★ ほぼなし (二珠一対 / 物実言霊 等は project 固有) |

### 全章展開の見積り

1 章 = 8 pattern × 16 章 ≈ 130 pattern。各 pattern が 30-50 行 → 全章合計 4000-6500 行。重い。

実用的には:
- **memo 密度高** (上巻-2,3,5,6,7 + 中巻-1,2) = 7 章を本気で書く
- 残り 9 章 (中巻-3 以降) は索引のみ

これで主要 60-70 pattern を抽出できる。

---

## v0 → v1 で改善したいポイント

1. **章節別の原文 (主文) を併記** — 現状は "narrative summary" の意訳のみ。原文 (漢文) を要所で引用すると anchor 強度↑
2. **Pattern 内の「観測経路」を追加** — `failure_if_absent` だけでなく「これが実装されているか確かめる方法」(SQL クエリ / grep コマンド) を併記
3. **既存 memo の章節 anchor を逆書き込み** — 全 memo に「古事記 origin: 上巻-X / 章節」を追記する移行作業の TODO リスト

## 履歴

- v0 (2026-05-08): Phase 1 索引 + Phase 2 上巻-7 プロトタイプ。`extraction_prompt.md` の方法論で生成。
