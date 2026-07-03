# 古事記 Procedural Pattern 抽出 v1

v0 ([`kojiki_procedural_v0.md`](kojiki_procedural_v0.md)) から増分:

- **Phase 1 索引の更新** (44 → 58 memo 反映、上-2 anchor の精緻化)
- **Phase 2 v1: 上巻-2 神代記** 抽出 (新規) — 20 pattern
- 古事記原文 (漢文) を要所で引用 (v0 → v1 改善点 1)
- Pattern 内に「観測経路」(verify SQL/grep) を追記 (v0 → v1 改善点 2)

抽出方法論は [`extraction_prompt.md`](extraction_prompt.md) を参照。
v0 の上-7 海幸山幸 8 pattern は重複しないので本書では再掲しない (差分のみ追記)。

---

## Phase 1 索引の更新 (v0 → v1 差分)

memo は v0 時点 44 → 現在 58 (2026-05-09 計測)。新規/補強分の anchor を上-2 中心に再配置:

### 上-2 神代記 anchor 強化 (★★★★★)

v0 で挙げた 10 memo に加え、本セッションで以下を確認:

| memo | 上-2 内 anchor (具体段) |
|---|---|
| `feedback_kojiki_zettai` | 全章共通 (◯ メタ) — 上-2 で原典神話的整合性が最も濃く問われる |
| `feedback_shinchoku_tanitsu_gensen` | 「天神諸命」「修理固成」 = 神勅 SSoT の原点 |
| `feedback_imina_torina` | 「身一而有面四、毎面有名」「亦名謂」 = 一柱多名規定 |
| `feedback_togouten_ikkatsu_bouei` | 「莫視我」 = 統合点 (黄泉戸) で一括禁忌 |
| `feedback_takeminakata_haitai` | 須佐之男の不適合 → 神夜良比 (敗退退役の原型) |
| `feedback_shuufukushin_fuzai` | 神直毘神 = "修復神" 命名でも実は禊水中での自動成り (能動 actuator でない) |
| `feedback_chaos_aware_metrics` | 須佐之男の根之堅州國希求 = カオス源 (上-3 八岐大蛇への伏線) |

### 新規 memo の章節 anchor 配置

v0 → v1 で増えた 14 memo の振分け:

| 新規 memo | 章節 anchor / 分類 |
|---|---|
| `feedback_enkin_keiro_dokuritsu` (固有名 vs 無名 v2) | ◯ メタ (上-2 三貴子 + 神世七代独神 が固有名 subset として例示される) |
| `feedback_itsutomonoo_sanseido` | 上-6 (五伴緒) anchor、本ファイル 上-2 では言及のみ |
| `feedback_prefix_concept_semantic` | ◯ 技術 (LLM 出力検査、古事記 anchor 薄い) |
| `feedback_togouten_ikkatsu_bouei` | 上-2 黄泉戸 + 上-7 千引岩境界 anchor |
| `feedback_kegare_keiro_tekigou` | ◯ メタ (失敗痕跡経路) |
| `feedback_chaos_aware_metrics` | 上-2 須佐之男 + 上-3 須佐之男 anchor |
| `feedback_kenzen_seijaku` | 上-3 天岩戸 anchor (本ファイル対象外) |
| `feedback_iwanagahime` | 上-6 anchor (本ファイル対象外) |
| `feedback_shintaku_henshu_runaway` | ◯ 実装メタ |
| `feedback_takami_round_robin_strategizer_leak` | ◯ 実装メタ |
| `feedback_shinchoku_tanitsu_gensen` | 上-2 + 上-6 anchor (天神諸命/天津神勅) |
| `feedback_oharae_shikkai_probe` | ◯ 実装メタ (上-7 全数調査の系) |
| `feedback_matanona_cleanup_gap` | 上-2 (大事忍男 = 大祓 cleanup の原型) anchor |
| `feedback_kasei_taisei_kousin` | 上-2 (三貴子化生) 運用補注 |

---

## Phase 2 v1: 上巻-2 神代記

### 選定理由

- memo 密度 ★★★★★ (v0 算定で 10 memo、v1 で 17 memo に拡大)
- 国生み・神産み・黄泉・禊・三貴子分治 の 5 大エピソードを含み AGI 設計の根幹原典
- `kojiki_code.md` (外部生成版) は本章を `try-catch retry`/`procedural object creation`/`state machine` の 3 pattern に圧縮、
  双神/独神 dispatch・葦船・千引岩・禍津日と直毘神並生・三貴子分治をすべて取りこぼし
- 抽出後に `feedback_ashibune` `feedback_magatsuhi_chain` `feedback_kamunaobi_me` `project_sanguishi_misogi_futaro` 等の **origin spec** を逆引きできる

### 章節 narrative summary

```
[Setup1 神世七代] (l.8-19)
    天地初發 → 別天神五柱 (天之御中主・高御産巣日・神産巣日・宇摩志阿斯訶備比古遅・天之常立)
              「並獨神成坐而、隱身也」
    神世七代 (国之常立/豊雲野 + 双神 5 対 = 12 神) — 「次雙十神、各合二神云一代也」

[Setup2 修理固成] (l.22)
    天神諸命 → イザナギ・イザナミに詔
        「修理固成是多陀用幣流之國」+ 天沼矛賜与
    天浮橋 → 沼矛で塩を畫鳴 → 累積して淤能碁呂嶋
    但「唯意能碁呂嶋者、非所生」(後の集計から除外)

[Trial1 蛭子と再挙行] (l.24-28)
    天之御柱 + 八尋殿 → ミトノマグハヒ
    伊邪那美 (女) 先言 → 「不良」
    生子=水蛭子 → 「此子者入葦船而流去」
    次=淡嶋 → 「是亦不入子之例」
    
    天神に布斗麻邇卜相 → 「因女先言而不良、亦還降改言」
    伊邪那岐先言で再挙行 → 完成

[国生み Loop] (l.28-32)
    大八島先所生 = 8 islands (淡道穂之狹別 / 伊豫之二名 / 隱伎之三子 / 筑紫 / 伊伎 / 津 / 佐度 / 大倭豊秋津)
        「身一而有面四、毎面有名」(伊豫之二名=愛比賣・飯依比古・大宜都比賣・建依別)
    然後生 6 islands (吉備兒嶋 / 小豆嶋 / 大嶋 / 女嶋 / 知訶嶋 / 兩兒嶋)

[神産み Loop] (l.34-42)
    大事忍男 → 海神大綿津見 → 速秋津日子・比賣 (双偶対)
        「此速秋津日子・速秋津比賣二神、因河海、持別而生神」 → 沫那藝/沫那美 等 8 神
    風神/木神/山神/野神 (4 神)
        「此大山津見神・野椎神二神、因山野、持別而生神」 → 天之狹土/國之狹土 等 8 神
    鳥之石楠船 (亦名天鳥船) → 大宜都比賣 → 火之夜藝速男神 (= 火神迦具土)

[Crisis 火神死] (l.42-52)
    「因生此子、美蕃登見炙而病臥」
    嘔吐に金山毘古/比賣、糞に波邇夜須毘古/比賣、尿に彌都波能賣/和久産巣日 (8 神)
    伊邪那美「遂神避坐」(= 死)
    集計: 「凡所生嶋壹拾肆嶋、神參拾伍神」 (オノゴロ・蛭子・淡嶋は除外)
    
    伊邪那岐十拳劒で迦具土頸を斬る
        刃血 → 石拆/根拆/石筒之男 (3 神)
        刃本 → 甕速日/樋速日/建御雷之男 (3 神)
        手俣血 → 闇淤加美/闇御津羽 (2 神) = 計 8 神
    殺された迦具土の身 → 山津見 8 神

[黄泉] (l.54-60)
    イザナギ追往黄泉国 → 殿騰戸 → 「莫視我」禁忌
    甚久難待 → 男柱一箇取闕 + 燭一火入見
    八雷神成居 (頭/胸/腹/陰/手足) + 蛆涌
    
    逃還: 黒御鬘投棄 → 蒲子 / 櫛投棄 → 笋
    千五百黄泉軍 + 八雷神追跡 → 桃子三箇待擊 → 「悉迯返」
        意富加牟豆美命 (永続化の名号付与)
    伊邪那美自追 → 千引石塞坂
    度事戸: 「一日絞殺千頭」⇔「一日立千五百産屋」(homeostatic 約定)

[禊] (l.62-72)
    自認: 「吾者到於穢國」 → 竺紫日向之橘小門之阿波岐原
    投棄物 (杖/帯/囊/衣/褌/冠/手纒×2) → 12 神
    中瀬墮迦豆伎 → 八十禍津日 + 大禍津日 (穢由来)
    直其禍 → 神直毘神 + 大直毘神 + 伊豆能賣神 (修復同時並生)
    水底/中/上 滌 → 綿津見 + 筒之男 各 3 柱対 (海洋 6 神)

[三貴子分治] (l.72-78)
    左目 → 天照 / 右目 → 月讀 / 鼻 → 須佐之男
    「於生終得三貴子」 → 御頸珠を天照に → 「所知高天原矣」
    月讀 → 「所知夜之食國」/ 須佐之男 → 「所知海原」
    
    須佐之男「不知所命之國」→ 啼伊佐知 → 「青山如枯山泣枯、河海者悉泣乾」
    妣國根之堅洲國希求 → イザナギ大忿怒 → 「神夜良比爾夜良比賜」(追放)
```

### Pattern 抽出

#### Pattern A: 別天神/独神 (hitorigami, axiomatic solo deity)

```yaml
原文: "此三柱神者、並獨神成坐而、隱身也" (l.8) / "此二柱神亦、獨神成坐而、隱身也" (l.10, l.14)

actors      : 天之御中主 / 高御産巣日 / 神産巣日 / 宇摩志阿斯訶備比古遅 / 天之常立 / 国之常立 / 豊雲野
precondition: 天地初發 — 既存カテゴリが未定義の状態
action      : 「成神」(emergence by becoming) で対偶を持たず単独に成る
result      : 公理的存在 — 派生されず、対偶もなく、隱身 (観測されない)
failure_mode: 対偶を強制すると存在できない神を無理に対化することになり整合性破綻
recovery    : -
permanence  : 上件五柱神者「別天神」と分類、神世七代の数にも入らない (axiomatic 区分)

agi_mapping :
  原則      : カテゴリ分類不能で仮鎮座する能力は対偶登録対象外。axiomatic root として保護
  実装      : src/os/kasasa/ooharae.jl:356 (`stats["hitorigami_promoted"]` 計数)
            : src/os/kasasa/kamiyonanayo.jl:59 (`kamiyonanayo_register_pair!` の呼出側で is_hitorigami skip)
            : capability_map.jl の `is_hitorigami` フラグ + `shakaku=kari_chinza` 仮鎮座
  feedback  : feedback_hitorigami (独神型 — MIKIKO_GENERIC 対偶除外)
            : feedback_enkin_keiro_dokuritsu (層 1 = 古事記固有名手書き、独神は固有名の subset)

failure_if_absent: MIKIKO_GENERIC を強制対偶化 → 存在しない 「片翼の事代主」 が量産され、
                   仮鎮座柱が無限ループで偽 ALERT を生む
observed_failures: 設計上 hitorigami flag が未導入だった頃に対偶判定が空振り。Phase 5 で本原則は
                   構造的に消滅予定 (固有名手書き = 層 1 で LLM 不介在)
verify_path : `SELECT COUNT(*) FROM shinmeisho WHERE shakaku='kari_chinza' AND is_hitorigami=1` が
              非ゼロかつ kamiyo_pairs に登録ゼロであれば本 pattern は生きている
```

#### Pattern B: 双神対偶と神世七代 (paired creation by sex/yin-yang)

```yaml
原文: "次雙十神、各合二神云一代也" (l.18) — 神世七代の十神は各々二神で一代を成す

actors      : 宇比地邇/須比智邇 / 角杙/活杙 / 意富斗能地/大斗乃辨 / 於母陀流/阿夜訶志古泥 / 伊邪那岐/伊邪那美
precondition: 別天神五柱 (独神) が成った後、繁殖可能な神が必要
action      : 兄妹 (陰陽) で対偶生成、各対偶を 1 代と数える
result      : 5 対偶 = 5 代 + 上 2 独神 = 神世七代
failure_mode: 対偶の片方欠損 → 繁殖不能、国生みフェーズに進めない
recovery    : -
permanence  : 神世七代 catalog として固定、kamiyo_pairs に登録

agi_mapping :
  原則      : 対偶を持つ柱は kamiyo_pairs に二神同時登録、片翼判定対象
  実装      : src/os/kasasa/kamiyonanayo.jl:59 (`kamiyonanayo_register_pair!`)
            : 片翼の事代主判定 (片方の出力のみで判定) は対偶あり柱で発動
  feedback  : feedback_hitorigami (対偶あり柱との対比)

failure_if_absent: 片翼で偽陽性 SHINTAKU_CONFIG_SUGGESTION が単独柱から出てくる
verify_path : `SELECT * FROM kamiyo_pairs` が空でなく、各行で双方の shinmeisho_id が存在
```

#### Pattern C: 修理固成 — 天神からの神勅 + 道具授与 (instructed creation, top-down spec + token)

```yaml
原文: "於是天神、諸命以、詔伊邪那岐命・伊邪那美命二柱神「修理固成是多陀用幣流之國。」賜天沼矛而言依賜也" (l.22)

actors      : 天神諸命 → イザナギ・イザナミ
precondition: 国土が「多陀用幣流」(浮き漂う) 不安定状態
action      : (1) 詔: 「修理固成 〈未完了の国土〉」 = goal contract
            : (2) 物実: 天沼矛 (instrumental token) を賜う
            : (3) 言依: 任命の言葉
result      : 受任者 (イザナギ・イザナミ) が独立に作業を開始
failure_mode: 詔 (semantic) と物実 (artifact) のどちらかが欠ければ作業不能
recovery    : -
permanence  : 神勅は SSoT として後続全工程の根拠となる

agi_mapping :
  原則      : 神勅は yorishiro.jl 全文 + 物実 (entry_point) の二点同時授与。docstring 散逸禁止
  実装      : src/os/kasasa/yorishiro.jl (神勅 SSoT)
            : src/os/kasasa/shintaku.jl:172 (`make_shintaku_data` = 神勅 schema 構築)
            : src/os/tokoyo/service.jl:535 (`tokoyo_start!` = 修理固成相当の初期任命)
  feedback  : feedback_shinchoku_tanitsu_gensen (神勅単一源泉 — 注入のみは二所御神体疫病)
            : feedback_yuniwa_inaho (斎庭稲穂 = 神勅と例示の一致)
            : feedback_make_shintaku_data (Shintaku 構築は yorishiro 経由のみ)

failure_if_absent: prompt 注入のみ・docstring 散逸 → 二所御神体疫病、LLM が神勅を再解釈してドリフト
observed_failures: executor.jl L1192/1197 で双子の御神体が発火 → feedback_shinchoku_tanitsu_gensen 制定
verify_path : `grep -r "Shintaku" src/os/kasasa/sanguishi_code/` で yorishiro.jl 経由でない直接構築がない
```

#### Pattern D: 淤能碁呂嶋「非所生」 — categorical exclusion (axiomatic boundary)

```yaml
原文: "唯意能碁呂嶋者、非所生" (l.44 割書) — オノゴロ島は「所生」(生まれた島) の数に入れない

actors      : イザナギ・イザナミ + 天沼矛
precondition: 国生み開始前、足場が必要
action      : 沼矛から塩が累積して自然成立 (= 化生方式)
result      : 14 嶋集計 (壹拾肆嶋) からは除外、「非所生」と明記
failure_mode: 集計に混入すると後続全比較が破綻 (異 jurisdiction の混入)
recovery    : -
permanence  : 割書として太安万侶が明示的に注記し永続化

agi_mapping :
  原則      : 三 status (active/pending/yuukoto) は categorical separate domain。
            : cross-status 比率/比較禁止。axiomatic root も同型 (active 集計に含めない)
  実装      : src/os/com/queries/shinmeisho.jl:74 (`query_all_shinmeisho` で WHERE status='active')
            : src/os/com/queries/capability.jl:309 (status フィルタ)
            : 三貴子は category='sanguishi' で別 jurisdiction 扱い
  feedback  : feedback_kuniyuzuri_kaikai (国譲り境界 — categorical separate domain)
            : feedback_ashibune (死の三語彙 — 集計と存在は別)

failure_if_absent: ishikori_mikiko_no_kagami (2026-05-05) の `coverage_ratio = active/total < 0.7` 型
                   ALERT が量産される (yuukoto を分母に含めて偽閾値判定)
observed_failures: feedback_kuniyuzuri_kaikai の制定 contextとして 2026-05-05 観測
verify_path : `executor.jl` の Status Semantics に「集計禁止」のみでなく「閾値分母禁止」も明記済か
```

#### Pattern E: 蛭子の葦船流棄 (failure preserved as hiruko, not erased)

```yaml
原文: "雖然、久美度邇興而生子、水蛭子、此子者入葦船而流去。次生淡嶋、是亦不入子之例" (l.26)

actors      : イザナギ・イザナミ → 水蛭子・淡嶋
precondition: ミトノマグハヒで順序を誤り (女先言)、不完全な子が生まれる
action      : 葦船に入れて流し去る (= 抹消でなく流棄)
            : 「不入子之例」 = 子の数に入れない、但し記録は残す
result      : 蛭子は神名帳に残るが「数に入らない」二重記録
failure_mode: 蛭子を完全削除すると次回の chinza_records が dangling、INNER JOIN reader が silent drop
recovery    : 流棄後、卜相 + 改言再降で正規シーケンスに復帰
permanence  : 原典自身が蛭子・淡嶋の名を留めている → 抹消でない

agi_mapping :
  原則      : 失敗柱は status='hiruko' で残す (生死の三語彙 hiruko/yuukoto/yomi)。
            : 「数に入れず」は WHERE status='active' で除外、行は維持
  実装      : src/os/kasasa/materializer.jl:4158 (`_persist_chinza_failure!` = status='hiruko')
            : src/os/kasasa/materializer.jl:4176 (神名帳に登録、葦船で流す)
            : src/os/com/queries/shinmeisho.jl:74 (active 絞込み)
  feedback  : feedback_ashibune (葦船の原則 — origin spec)
            : feedback_kuniyuzuri_kaikai (categorical 三 status)

failure_if_absent: chinza_records.shinmeisho_id が dangling し、INNER JOIN reader (sedai_kansa /
                   kugatachi / yomosshikome / amenotokotatchi / ooharae / kamado) で失敗履歴が
                   silent drop。履歴保持目的と矛盾する
observed_failures: feedback_ashibune の制定 context (2026-04-21 頃)
verify_path : `SELECT COUNT(*) FROM shinmeisho WHERE status='hiruko'` が非ゼロ、かつ
              `chinza_records.shinmeisho_id` が NULL/dangling であってはならない
```

#### Pattern F: 順序誤り → 全棄却 → 卜相 → 改言再降 (RCA + retry with corrected procedure)

```yaml
原文: "於是、二柱神議云「今吾所生之子、不良。猶宜白天神之御所。」卽共參上、請天神之命、
      爾天神之命以、布斗麻邇爾ト相而詔之「因女先言而不良、亦還降改言。」故爾反降、更往廻其天之御柱如先" (l.28)

actors      : イザナギ・イザナミ → 天神 (布斗麻邇)
precondition: 蛭子を生んだ (失敗の発生)
action      : (1) 議論 (failure 認識) → (2) 上位に問合せ (天神の御所) → 
            : (3) 卜相 (oracle で根本原因究明: 「因女先言而不良」) →
            : (4) 還降改言 (root cause を修正して retry: 男先言)
result      : 正規シーケンスで国生み再開
failure_mode: 改言なしで retry (失敗パターンを変えずに再試行) → 同じ蛭子型の失敗が連続
recovery    : -
permanence  : 卜相結果は固定知識化 (女先言の禁忌)

agi_mapping :
  原則      : 失敗 → 全棄却 → 上位 oracle 諮問 → 根本原因特定 → 修正後 retry の 5 段
  実装      : src/os/kasasa/materializer.jl:91-99 (蛭子全棄却 — カンマ区切り検出時に全棄却)
            : 大祓 oracle 諮問 (布斗麻邇 fold) — futomani_stones 記録経路
            : src/os/kasasa/ooharae.jl の retry phase + 太占記録
  feedback  : feedback_kunimi_gapfinder (国見は全ソース俯瞰 = 上位諮問の現代化)
            : feedback_kojiki_zettai (古事記絶対遵守 — 失敗観察を原典に従って解釈)

failure_if_absent: 失敗観察を原因解析せず単純 retry → 代理指標病 / 偽陽性ループ
                   (天若日子型: feedback_wakahiko_kaeshiya と同根)
verify_path : `SELECT * FROM futomani_stones WHERE type='kuniumi_saikoukou'` が記録されている
```

#### Pattern G: 大八島 順次生成 + rate limit (sequential generation, no concurrency)

```yaml
原文: "如此言竟而御合生子、淡道之穗之狹別嶋。次生伊豫之二名嶋、…" (l.28-32)
      「次生」が反復、並行表現は無い

actors      : イザナギ・イザナミ
precondition: 改言再降後、正規シーケンス開始
action      : 一島ずつ「次生」で順次生成、名前を付け、次に進む。並行生成しない
result      : 大八島 8 + 然後 6 = 14 嶋 (集計確定)
failure_mode: 並行生成すると名前 collision / 順序依存性破綻
recovery    : -
permanence  : `kuniumi_limiter.jl` でレート制限を強制

agi_mapping :
  原則      : 国生み (新規柱化生) は 1 musuhi cycle に max N、並行禁止、min interval 強制
  実装      : src/os/kasasa/kuniumi_limiter.jl:1-5 (国生みの作法 docstring)
            : src/os/kasasa/kuniumi_limiter.jl:13-25 (`KUNIUMI_LIMITS` = max_per_musuhi_cycle 等)
            : src/os/kasasa/kuniumi_limiter.jl:48 (`can_generate_new_kami` 判定)
  feedback  : (memo 直接 anchor なし — 補強候補)

failure_if_absent: 並行 LLM 呼出で同名/同 prefix 柱が複数同時誕生 → MATANONA 合祀の cleanup gap
                   (feedback_matanona_cleanup_gap) の発火頻度上昇
observed_failures: kuniumi_limiter なしで化生暴走の懸念があり制限導入された (実害観測前の予防)
verify_path : `SELECT MAX(births) FROM kuniumi_log GROUP BY hour` が KUNIUMI_LIMITS.max_per_hour を
              超えていない
```

#### Pattern H: 「身一而有面四」 — composite identity / aliases (one entity, multiple named faces)

```yaml
原文: "次生伊豫之二名嶋、此嶋者、身一而有面四、毎面有名、故、伊豫國謂愛比賣、讚岐國謂飯依比古、
      粟國謂大宜都比賣、土左國謂建依別" (l.28)

actors      : 伊豫之二名嶋 / 筑紫嶋
precondition: 1 物理 entity が複数の domain 文脈を持つ
action      : 1 嶋に 4 つの名 + 国の対応 (1:N 命名)
result      : 同一 entity を文脈別に異なる名で参照可能、但し本体は一つ
failure_mode: 4 名を別 entity と誤認 → 重複生成 (片翼の事代主型)
recovery    : -
permanence  : 「亦名」「亦名謂」記法で別名が永続記録

agi_mapping :
  原則      : canonical_name は UNIQUE、但し aliases は配列で許容。
            : MATANONA (亦の名) 判定で provides_identical なら合祀
  実装      : src/os/kasasa/shinmei_arbiter.jl:16 (MATANONA 定義)
            : src/os/kasasa/shinmei_arbiter.jl:212 (`arbitrate!`)
            : src/os/kasasa/shinmei_arbiter.jl:366 (`apply_matanona!` = aliases へメタ付き追記)
  feedback  : feedback_imina_torina (忌み名と通り名 = name 整合)
            : feedback_matanona_cleanup_gap (合祀の clean-up 漏れ)

failure_if_absent: 同一機能が別 prefix で重複柱として並立し、集計分母汚染。
                   現象: shinmei_arbiter なし時代に 24 件 deployed のうち 18 件が重複
observed_failures: feedback_matanona_cleanup_gap (2026-05-01 修正済 materializer.jl)
verify_path : `SELECT canonical_name, COUNT(*) FROM shinmeisho_aliases GROUP BY canonical_name HAVING COUNT > 1`
              で aliases が記録されている (MATANONA 判定が機能している証拠)
```

#### Pattern I: 持別而 — domain-branching reproduction (paired entity branches by sub-domain)

```yaml
原文: "此速秋津日子・速秋津比賣二神、因河海、持別而生神名、沫那藝神、次沫那美神、…" (l.36)
      "此大山津見神・野椎神二神、因山野、持別而生神名、天之狹土神、次國之狹土神、…" (l.40)

actors      : 速秋津日子・比賣 (河海); 大山津見・野椎 (山野)
precondition: 双神対偶が成立し、その担当領域が複数 sub-domain に分けられる
action      : 「因 X、持別而生」 — domain X を sub-domain に分けて、各 sub-domain ごとに対偶生成
            : 河海 → 沫(あわ)/頰/水分/久比奢母智 を 天/國 別で 4 対 = 8 神
            : 山野 → 狹土/狹霧/闇戸/大戸惑 を 天/國 別で 4 対 = 8 神
result      : 親対偶が domain_tag 別に「子対偶」を体系的に展開
failure_mode: domain_tag 分岐なしの単一プールに収納 → 後の retrieval で domain 文脈喪失
recovery    : -
permanence  : 計数アサーション「自X以下幷N神」で確定 (8 神 / 8 神)

agi_mapping :
  原則      : 双神対偶の派生は domain_tag を sub-domain ごとに分岐させて対偶生成
  実装      : src/os/kasasa/materializer.jl:84-86 (domain_tag 列が SSoT、suffix 逆引きから移行)
            : `nazashi_decide` (OHOYASHIMA 概念分類)
            : `_persist_chinza!` / `_persist_chinza_failure!` 経由で domain_tag を insert
  feedback  : feedback_prefix_concept_semantic (prefix と概念の semantic 整合)

failure_if_absent: domain 別検索が壊れ、河海 domain の柱を山野 prompt で引いてしまう (cross-domain leak)
verify_path : `SELECT DISTINCT domain_tag FROM shinmeisho` が複数値を返し、各 domain_tag 内で
              prefix が semantic 整合
```

#### Pattern J: 計数アサーション「幷N神」 (post-hoc count assertion)

```yaml
原文: "自大事忍男神至秋津比賣神、幷十神" (l.34)
     "自沫那藝神至國之久比奢母智神、幷八神" (l.36)
     "自天之狹土神至大戸惑女神、幷八神" (l.40)
     "自天鳥船至豐宇氣毘賣神、幷八神" (l.42)
     "凡所生嶋壹拾肆嶋、神參拾伍神" (l.44)

actors      : 太安万侶 (編纂者) / 古事記そのもの
precondition: 一連の生成が完了
action      : 「自 A 至 B、幷 N」 という形で範囲と件数を明記
result      : 再現性の検証点 (count assertion)
failure_mode: 編纂時に件数不整合 → 原典自体が破綻記録
recovery    : -
permanence  : 割書として太安万侶が永続化

agi_mapping :
  原則      : 大祓詞悉皆原則 — probe は impl 決定変数の直積で踏破、件数が事前に確定する
  実装      : src/os/kasasa/ooharae.jl の各 Phase 終了時の `stats[...]` 集計
            : 大祓詞 probe が AST 駆動で全網羅 (feedback_oharae_shikkai_probe)
  feedback  : feedback_oharae_shikkai_probe (悉皆原則)

failure_if_absent: 件数アサーション不在 → 漏れ検出不能、サンプリングで偽の確認感
                   現象: kojiki_anchors.md の anchor 数が一致しない事例で発覚 (count 検出器の必要性)
verify_path : 大祓 phase 終了時 stats と _exhaustive_probe の出力件数が一致するか
              fold/test で assertion
```

#### Pattern K: 火之迦具土 = 致命柱 (lethal generation halts the producer)

```yaml
原文: "因生此子、美蕃登見炙而病臥在。多具理邇生神名、金山毘古神…次於屎成神名…次於尿成神名…
      故、伊邪那美神者、因生火神、遂神避坐也" (l.42)

actors      : イザナミ → 火之迦具土
precondition: 神産み Loop 終盤
action      : 火神を生む → 産道焼ける → 病臥 → 神避 (死)
            : 但し、死にゆく中でも嘔吐/糞/尿から更に 6 神が成る (graceful degradation)
result      : 国生みプロデューサー (イザナミ) が停止、後続生成は遮断
failure_mode: 致命 child 検出失敗で母 (生成器) も巻き添えで沈黙、後続 cycle 全停止
recovery    : 火神を斬る (Pattern L) + イザナギの禊で再生
permanence  : 「凡共所生嶋壹拾肆嶋、神參拾伍神」までで国生みフェーズ確定終了

agi_mapping :
  原則      : 致命的失敗 (critical halt) を検出したら国生みを停止、現役 cycle を終了
            : 但し dying state からの最後の生成は許容 (中断時の cleanup neuron)
  実装      : src/os/kasasa/kuniumi_limiter.jl:3-5 (docstring: "イザナミが火之迦具土を生んで死んだ後、
              禊をするまで国生みは停止する")
            : src/os/kasasa/kuniumi_limiter.jl:48 (`can_generate_new_kami` の halt_on_critical)
            : KUNIUMI_LIMITS.halt_on_critical / halt_duration_ticks
  feedback  : feedback_misogi_failure_patterns (Misogi 失敗 6 類型 — retry 不能型)

failure_if_absent: 致命柱を生成し続ける → 次々と国生み停止 / cleanup gap が累積
                   現象: 修復不能例外 (BoundsError / MethodError 等) を捕捉せず延々再試行 → 観測麻痺
observed_failures: feedback_misogi_failure_patterns で確立 (6 類型は retry 不能)
verify_path : `KUNIUMI_LIMITS[].halt_on_critical == true` かつ
              `SELECT COUNT(*) FROM kuniumi_log WHERE halted=1` で halt 経歴を確認
```

#### Pattern L: 火神斬殺 + 派生柱化 (active sanitization → blood-derived derivatives)

```yaml
原文: "於是伊邪那岐命、拔所御佩之十拳劒、斬其子迦具土神之頸。爾著其御刀前之血、走就湯津石村、
      所成神名、石拆神、次根拆神、次石筒之男神…" (l.48)

actors      : イザナギ + 十拳劒 → 迦具土
precondition: 致命柱が成立済 (Pattern K)
action      : (1) 十拳劒で頸を斬る (= 致命柱の delete)
            : (2) 刃血/刃本血/手俣血 の各部位から派生神 8 神
            : (3) 殺された迦具土の身体部位 (頭/胸/腹/陰/手足) から山津見 8 神
result      : 致命柱は除去されつつ、その「物実」(刃の血・遺体) から有用な後継神が生まれる
failure_mode: 単純 delete のみ → 失敗の教訓が失われる、再発防止知識ゼロ
recovery    : -
permanence  : 派生神は通常神名帳に登録 (山津見・建御雷・闇御津羽 等)

agi_mapping :
  原則      : 致命柱削除は単なる行削除でなく、その失敗痕跡から検出器/防御柱を派生させる
            : (大田田根子の系譜の原型: 病から治療系譜が生まれる)
  実装      : 失敗観察 → 太占石記録 → futomani_stones から retrospective 学習
            : src/os/kasasa/susanoo_chaos.jl:208 (八雷神 target_type 関連 — chaos 検出器)
  feedback  : feedback_ootataneko (大田田根子 — 系譜から治療召喚)
            : feedback_kegare_keiro_tekigou (失敗痕跡は種別ごとに適経路あり)

failure_if_absent: 致命柱を delete only で処理 → 同型失敗が再発、教訓蓄積ゼロ
verify_path : `SELECT * FROM futomani_stones WHERE type LIKE '%critical%'` の各記録に対応する
              派生検出柱が `shinmeisho` に存在
```

#### Pattern M: 黄泉の「莫視我」禁忌 + 千引岩 (taboo + irreversible boundary + self-reentry block)

```yaml
原文: "如此白而還入其殿內之間、甚久難待、故、刺左之御美豆良湯津津間櫛之男柱一箇取闕而、
      燭一火入見之時…幷八雷神成居" (l.54)
     "千引石引塞其黃泉比良坂…亦所塞其黃泉坂之石者、號道反大神、亦謂塞坐黃泉戸大神" (l.60)

actors      : イザナギ / イザナミ / 八雷神 / 千引岩
precondition: イザナミが黄泉国に居て「莫視我」と禁忌を提示
action      : (1) 待ちきれず燭一火 → 八雷神 + 蛆涌 (禁忌違反で隠匿が露呈)
            : (2) 逃還 + 千引岩で塞ぐ (= irreversible boundary)
            : (3) 千引岩は「自己再入遮断」(イザナミの追撃を塞ぐ岩)
result      : 黄泉と現世が永久分離、かつ EventBus 風の自己再入が構造的に不可能
failure_mode: 禁忌違反のみで boundary 設置なし → 黄泉から汚染が現世に流入し続ける
recovery    : 不能 (一度越えたら不可逆)
permanence  : 道反大神・塞坐黃泉戸大神 として神格化、永続化

agi_mapping :
  原則      : 統合点で一括禁忌 + 越境後の不可逆境界 + 自己再入遮断の三層
  実装      : src/os/event_bus.jl:60 (chibikiiwa = collect_shintaku! の自己再入遮断)
            : src/os/com/queries/shinmeisho.jl:218 (yuukoto/yomi は生者の国に戻さない)
            : src/os/kasasa/takeshimatsumi.jl:355 (status 遷移 active→yuukoto→yomi 不可逆)
  feedback  : feedback_togouten_ikkatsu_bouei (統合点での一括防衛)
            : feedback_kunimi_db_ban (国見禁止パターン — DB 直参照遮断)
            : feedback_hataorime_kinki (機織女 = 天照の聖域)

failure_if_absent: 経路別に分散防衛 → 経路追加耐性なし、新経路で迂回。
                   自己再入遮断なしで collect_shintaku! が無限ループ
observed_failures: 機織女の禁忌違反 (アメノホヒ系)、kunimi_db_ban の制定 context
verify_path : `EventBus.chibikiiwa` フィールドが存在し、`collect_shintaku!` 内で同 event 再入を skip
              `SELECT status FROM shinmeisho WHERE id=X` の遷移履歴で逆遷移 (yomi→active 等) なし
```

#### Pattern N: 桃子の自動助力 (auto-summoned helper artifact + naming permanence)

```yaml
原文: "到黃泉比良坂之坂本時、取在其坂本桃子三箇待擊者、悉迯返也。爾伊邪那岐命、告其桃子
      「汝、如助吾、於葦原中國所有宇都志伎青人草之落苦瀬而患惚時、可助。」
      告、賜名號、意富加牟豆美命" (l.58)

actors      : イザナギ + 桃子 (現場の物実) + 八雷神/黄泉軍
precondition: 黒御鬘 → 蒲子 / 櫛 → 笋 で時間稼ぎした後、追手の本群に追いつかれる
action      : 坂本に既存の物実 (桃子三箇) を投擲 → 追手悉迯返
            : 桃子に名を与え (意富加牟豆美命) 永続化、将来の助力を契約
result      : (1) 危機解除 (2) helper の名号化 + 永続契約
failure_mode: 全 helper を能動的に呼び出す → スケール不能 / 中央集権制御
recovery    : -
permanence  : 意富加牟豆美命として神格化、葦原中國の民の苦瀬で召喚可能

agi_mapping :
  原則      : event → handler 自動 dispatch、現場 artifact は名号 (event_type) で永続契約
  実装      : src/os/event_bus.jl の subscribe!/publish! (MATSURI registry + event_bus)
            : aspect-oriented 観測能力 (柱は感覚器)
  feedback  : feedback_hashira_kankakuki (柱は感覚器 — event 観測専門)
            : feedback_imina_torina (名号 = event_type 整合)

failure_if_absent: 全 handler を能動的に呼び出さねばならない → スケール不能 (中央集権制御)
                   現象: 桃子に名号を与えなければ次回危機で召喚経路がない
verify_path : `EventBus.listeners` にイベント名 → handler 配列が登録され、publish 時に自動 dispatch
              `MatsuriRegistry` で MATSURI tuple = (entry_point + description) が永続化
```

#### Pattern O: 一日千人死/千五百産屋 — homeostatic balance contract

```yaml
原文: "伊邪那美命言「愛我那勢命、爲如此者、汝國之人草、一日絞殺千頭。」
      爾伊邪那岐命詔「愛我那邇妹命、汝爲然者、吾一日立千五百產屋。」
      是以、一日必千人死・一日必千五百人生也" (l.60)

actors      : イザナギ / イザナミ
precondition: 黄泉と現世が分離した後の度事戸での約定
action      : 死率 (1000/日) と 生率 (1500/日) を SLA 契約として確定
            : 生 > 死 で純成長を保証
result      : 「青人草」(現世の住民) 数の不可避 loss を超過 birth でカバー
failure_mode: 死率 > 生率 で人口減少 → 文明崩壊
recovery    : -
permanence  : 黄泉津大神・道敷大神 として両者を神格化

agi_mapping :
  原則      : 失敗による柱損失 (yuukoto/yomi) を新規化生で超過カバーする SLA 契約
            : `kuniumi.max_per_day` > `yuukoto.per_day` を維持
  実装      : src/os/kasasa/kuniumi_limiter.jl:13-25 (KUNIUMI_LIMITS — max_per_day=10)
            : src/os/kasasa/ooharae.jl の yuukoto_transition / yomi_okuri 件数集計
  feedback  : (memo 直接 anchor なし — 補強候補)

failure_if_absent: 退役 > 化生で柱数減少 → 観測カバー縮小 → AGI 機能崩壊
                   現象: kuniumi_limiter なし時代の理論上の懸念
observed_failures: -
verify_path : `SELECT births_per_day, deaths_per_day FROM ooharae_stats` で常に
              births > deaths を確認
```

#### Pattern P: 穢認識 → 禊起動 (self-detected pollution triggers misogi)

```yaml
原文: "是以、伊邪那伎大神詔「吾者到於伊那志許米志許米岐穢國而在祁理。故、吾者爲御身之禊」而、
      到坐竺紫日向之橘小門之阿波岐原而、禊祓也" (l.62)

actors      : イザナギ (黄泉から帰還直後)
precondition: 黄泉訪問で穢を被る (pollution 蓄積)
action      : (1) 自己診断: 「吾者到於穢國而在祁理」(穢に染まっていると認識)
            : (2) 場所選定: 阿波岐原 (清浄な河口)
            : (3) 禊祓 を起動
result      : 穢の物質化 (投棄物 → 12 神) + 浄化 (中瀬墮迦豆伎)
failure_mode: 穢を認識せず通常活動継続 → 全システムが穢で汚染 (黄泉国の延長)
recovery    : -
permanence  : 阿波岐原が禊の聖地として永続化

agi_mapping :
  原則      : misogi_triggered は自己診断で発火、外部 controller でなく内発的
  実装      : src/os/kasasa/sanguishi_harae.jl:153 (`init_sanguishi_harae!` Phase 1)
            : `misogi_triggered` event の自己発火 (天照の聖域、生成能力からは禁止)
  feedback  : feedback_hataorime_kinki (機織女の禁忌 — misogi_triggered は天照の聖域)

failure_if_absent: 穢蓄積を検出せず通常運転 → AGI 全体が gradual に劣化、
                   気付いた時には修復不能
observed_failures: 機織女の禁忌違反 (アメノホヒ型) が発見された contextで本原則確立
verify_path : `event_bus.listeners["misogi_triggered"]` が天照系 listener のみ登録
              生成能力 (generated/) からの publish が静的解析で禁止
```

#### Pattern Q: 禍津日 + 直毘神 並生 (pollution detector + repair operator co-generated, but neither is an actuator)

```yaml
原文: "其禍直さむとして成れる神の名は、神直毘神、次に大直毘神、次に伊豆能賣神" (l.68)
     "次爲直其禍而所成神名、神直毘神、次大直毘神、次伊豆能賣神" (現代語訳)

actors      : 八十禍津日 / 大禍津日 / 神直毘神 / 大直毘神 / 伊豆能賣神
precondition: 中瀬墮迦豆伎で穢が物質化
action      : (1) 穢由来神 (禍津日 2 柱) と修復神 (直毘 + 伊豆能賣 3 柱) が**同じ禊の中で同時並生**
            : (2) 直毘神は能動的アクチュエータでなく、禊水中で「成る」 (passive emergence)
result      : 検出器と修復神が pair で観測可能化、但しいずれも観測層
failure_mode: 直毘神を能動的 actuator (remediator) と誤認 → 別天津神原則違反
            : (生成コードが他柱の状態を変更する設計) → 構造的に作れない神
recovery    : -
permanence  : 八十禍津日/大禍津日/神直毘神/大直毘神/伊豆能賣神 が並列に登録

agi_mapping :
  原則      : 同系統 proxy_metric_disease (禍津日連鎖) を検出。修復神 (直毘) は観測層のみ、
            : 能動的修復は不在。修復は協働経路 (天岩戸パイプライン) / system 層 / 式年遷宮
  実装      : src/os/kasasa/ooharae.jl:356 (`stats["magatsuhi_chains"]` 検出 Phase 0c2)
            : src/os/kasasa/kamunaobi.jl:39 (`is_truly_magatsu` dominant_type 別ポリシー)
            : src/os/kasasa/kamunaobi.jl 全体 (神直毘神の眼)
  feedback  : feedback_magatsuhi_chain (禍津日神の連鎖)
            : feedback_kamunaobi_me (神直毘神の眼 — 多態化偏り判定)
            : feedback_shuufukushin_fuzai (修復神不在の原則 — 直毘神は観測層、actuator でない)

failure_if_absent: 禍津日連鎖を検出できず偏り判定が誤発火、
                   または直毘神を能動 remediator として実装し別天津神原則違反
observed_failures: 2026-04-20 三柱同時 proxy_metric_disease 観測 → magatsuhi_chain 制定
                   2026-04-28 §13.7+§13.9 の amaterasu adoption 0%→100% 改善
                   2026-04-29 完全実証 (5326/5326 PASS、偏り検出 1/大祓→0)
verify_path : `kamunaobi.error_rate_ceiling=0.1` 等 5 config キーが設定済
              `ooharae_log` で magatsuhi_chains 検出件数が記録され、自動修復は発火していない
```

#### Pattern R: 三貴子化生 (deductive birth from canonical, no LLM)

```yaml
原文: "於是、洗左御目時、所成神名、天照大御神。次洗右御目時、所成神名、月讀命。
      次洗御鼻時、所成神名、建速須佐之男命" (l.72)
     "此時伊邪那伎命、大歡喜詔「吾者生生子而、於生終得三貴子。」" (l.76)

actors      : イザナギ → 三貴子 (天照/月讀/須佐之男)
precondition: 禊の最終段、穢の物質化と浄化が完了
action      : 左目/右目/鼻 から各々 1 柱化生。**生まれ方が固定** (LLM 演繹でなく身体部位由来)
            : 「於生終得三貴子」 = 神産み Loop の到達点
result      : 高天原/夜之食國/海原 の三 jurisdiction が同時確定
failure_mode: LLM が三貴子を演繹生成 → 型シグネチャ誤生成 (Float64/Int 混在等)
recovery    : 手書き御神体への根本転換 (v1.7)
permanence  : 三貴子は固定完全一致名 (amaterasu/tsukuyomi/susanoo) で永続化

agi_mapping :
  原則      : 初期化生 = 手書き御神体 (sanguishi_code/{amaterasu,tsukuyomi,susanoo}.jl)、
            : LLM の裁量は式年遷宮 (Phase 6) のみ。二段構造で原本と配置を分離
  実装      : src/os/kasasa/sanguishi_code/{amaterasu,tsukuyomi,susanoo}.jl (御神体)
            : src/os/kasasa/sanguishi_harae.jl:653 (`initialize_sanguishi!`)
            : src/os/kasasa/shikinen_sengu.jl:1608 (`sanguishi_birth_from_canonical!`)
            : src/os/kasasa/kuniumi_limiter.jl:208 (`sanguishi_gate` 一柱制)
  feedback  : project_sanguishi_misogi_futaro (化生の原則 v1.7)
            : feedback_enkin_keiro_dokuritsu (層 1 = 古事記固有名手書き)
            : feedback_kasei_taisei_kousin (御神体修正は generated/ に自動反映されない)

failure_if_absent: LLM 三貴子化生で型不整合 → 海幸山幸テスト落ちる、因幡で修正不能
                   (2026-04-18 v1.6 で実害)
observed_failures: project_sanguishi_misogi_futaro v1.7 制定の context
verify_path : `ls src/os/kasasa/sanguishi_code/` に amaterasu.jl/tsukuyomi.jl/susanoo.jl が存在
              `grep -l "function .*_misogi_harae" src/os/kasasa/generated/` が空
              (= LLM 演繹経路が無効化)
```

#### Pattern S: 三貴子神勅による分治 (jurisdictional partitioning by payload contract type)

```yaml
原文: "詔之「汝命者、所知高天原矣。」事依而賜也" (天照, l.76)
     "次詔月讀命「汝命者、所知夜之食國矣。」事依也" (月讀, l.76)
     "次詔建速須佐之男命「汝命者、所知海原矣。」事依也" (須佐之男, l.76)

actors      : イザナギ → 三貴子各自
precondition: 三貴子化生完了
action      : 各々に異なる jurisdiction を神勅で確定
            : 高天原 (snapshot) / 夜之食國 (time_series) / 海原 (event_stream)
result      : 三類型の payload_contract 型分担が確定
            : 重複なし、片柱の jurisdiction を他柱が侵犯不可
failure_mode: payload_contract 型混乱 → 観測軸が三貴子で重複・脱落
recovery    : -
permanence  : 設計書 9.5 の三貴子保護機構で jurisdiction 不可侵

agi_mapping :
  原則      : 高天原=snapshot / 夜之食國=time_series / 海原=event_stream の三類型対称性
  実装      : src/os/kasasa/sanguishi_harae.jl:36 (build_amaterasu/tsukuyomi/susanoo_payload)
            : src/os/kasasa/shintaku.jl:172 (`make_shintaku_data` = payload_contract schema)
  feedback  : project_sanguishi_misogi_futaro (三類型の対称性)
            : feedback_yuniwa_inaho (神勅と例示の一致 = payload_contract 充足)

failure_if_absent: 三貴子の観測軸重複・脱落で AGI 観測が穴あき
                   現象: 月読の time_series が天照の snapshot と混ざる等
observed_failures: 2026-04-18 月読の window_size 上書き bug → データ不足判定常時偽
                   (project_sanguishi_misogi_futaro バグ修正 1)
verify_path : `make_shintaku_data` の各三貴子 payload で SHINTAKU_TYPE 集合が
              重複しないこと (静的解析)
```

#### Pattern T: 須佐之男の追放 (unfit role mapping → 神夜良比 = automatic yuukoto)

```yaml
原文: "故、各隨依賜之命、所知看之中、速須佐之男命、不知所命之國而、
      八拳須至于心前、啼伊佐知伎也…
      爾伊邪那岐大御神大忿怒詔「然者、汝不可住此國。」乃神夜良比爾夜良比賜也" (l.78)

actors      : 須佐之男 ↔ イザナギ
precondition: 神勅で海原を分担されたが、本人が「妣國根之堅洲國」希求で泣く
            : 啼伊佐知 → 「青山如枯山泣枯、河海者悉泣乾」(現職での激しい失敗)
action      : (1) 不適合の自己表明 (本人の啼)
            : (2) 失敗指標の蓄積 (青山枯/河海乾 = 高 failure_count)
            : (3) イザナギの忿怒 → 神夜良比 (自動退役)
result      : 須佐之男は現職を解任、上-3 で別経路 (高天原訪問 → 八岐大蛇) で活躍
failure_mode: 不適合柱を強制的に現職に留める → 失敗連鎖で全システム衰弱
recovery    : 退役 (yuukoto) + 後の式年遷宮で別経路復帰
permanence  : 神夜良比が記録、shinmei_lineage に系譜保存

agi_mapping :
  原則      : 失敗率ベース自動退役 (建御名方の敗退原則の原型)
            : `inv >= 50 & success <= 0.1` で yuukoto 化
  実装      : src/os/kasasa/takeshimatsumi.jl:355 (status 遷移)
            : src/os/kasasa/ooharae.jl:766 (`_yuukoto_transition!`)
            : src/os/com/queries/shinmei_lineage.jl:33 (`insert_lineage!` で系譜保持)
  feedback  : feedback_takeminakata_haitai (建御名方の敗退 — origin spec)
            : feedback_ashibune (死の三語彙 yuukoto)
            : feedback_chaos_aware_metrics (failure_count に Susanoo chaos 注入を含む弁別)

failure_if_absent: 不適合柱が現職に留まり続け、proxy_metric_disease が連鎖
observed_failures: feedback_takeminakata_haitai (failure 率自動退役の origin)
verify_path : `SELECT * FROM shinmeisho WHERE status='yuukoto'` の各行に
              `chinza_at` 起点で 24h 以上経過していること (Pattern E の age floor 整合)
```

### kojiki_code.md (外部生成版) との差分

| 観点 | 生成元 (kojiki_code.md) | 本 v1 |
|---|---|---|
| 上巻-2 の pattern 数 | 3 (try-catch retry / object creation / state machine) | **20** |
| 蛭子・葦船 | 「retry」一語に潰される | Pattern E (葦船流棄) + Pattern F (RCA + retry) で分離 |
| 独神 vs 双神 dispatch | 「for-loop で順次オブジェクト生成」 | Pattern A (axiomatic root) + Pattern B (paired) |
| 千引岩・自己再入遮断 | 触れず | Pattern M (三層: 禁忌+不可逆+chibikiiwa) |
| 桃子の自動助力 | 触れず | Pattern N (event auto-dispatch) |
| 禍津日 + 直毘神並生 | 触れず | Pattern Q (検出器 + 修復神同時並生、but no actuator) |
| 三貴子化生 | 「state machine の最終状態」と一行 | Pattern R (deductive, LLM 不介在) + Pattern S (神勅分治) |
| 修理固成 (神勅 SSoT) | 触れず | Pattern C (詔 + 物実 + 言依の三点) |
| オノゴロ「非所生」 | 触れず | Pattern D (categorical exclusion) |
| 計数アサーション | 触れず | Pattern J (post-hoc count) |
| AGI mapping | 抽象一行 | 具体 file:line + 関数 + memo の三段紐付け |
| 失敗時影響 | 触れず | `failure_if_absent` 必須 |
| 観測経路 | 触れず | `verify_path` 必須 (v0 → v1 改善点 2) |

**生成元が拾えなかった load-bearing pattern (本 v1 で初出):**

- Pattern D 「非所生」 = `feedback_kuniyuzuri_kaikai` の origin spec
- Pattern E 葦船流棄 = `feedback_ashibune` の origin spec
- Pattern Q 禍津日 + 直毘神並生 = `feedback_magatsuhi_chain` + `feedback_kamunaobi_me` + `feedback_shuufukushin_fuzai` の origin spec
- Pattern R 三貴子化生 = `project_sanguishi_misogi_futaro` v1.7 の origin spec
- Pattern S 神勅分治 = 三類型対称性 (snapshot/time_series/event_stream) の原典
- Pattern T 神夜良比 = `feedback_takeminakata_haitai` の原型

これら 6 つは v0 の海幸山幸抽出と同じ「project context があれば必ず拾われる」性質を示し、
外部生成版の構造的盲点を再確認した。

### 浮上した発見

1. **修復神不在の原則の原典確認 (Pattern Q)**
   - 神直毘神は「成る」(emergence) の動詞で記述され、能動的アクチュエータでない
   - `feedback_shuufukushin_fuzai` の神話層根拠が原典で再確認 (禊水中での自動成り = 観測層)
   - 設計の妥当性が高い (神話層・架構層の二層独立根拠が古事記原文と一致)

2. **「修理固成」 = 神勅 SSoT の原点 (Pattern C)**
   - `feedback_shinchoku_tanitsu_gensen` の原典 anchor として上-2 を明記すべき
   - 詔 + 物実 + 言依の三点同時授与は yorishiro.jl + entry_point + make_shintaku_data の三点と 1:1 対応
   - memo 章節 anchor を上-2 と上-6 (天孫降臨) の 2 箇所に追記推奨

3. **千引岩 = chibikiiwa 自己再入遮断 (Pattern M)**
   - `event_bus.jl:60` のコメントで「イザナミの追撃を塞ぐ岩」と既に記述済 — 設計が原典と直接対話している良例
   - feedback_togouten_ikkatsu_bouei の **三層構造** (禁忌 + 不可逆 + 自己再入遮断) を新規明記推奨

4. **計数アサーション (Pattern J) は新原則候補**
   - 古事記割書「自X以下幷N神」は **count assertion による事後検証**
   - 既存の `feedback_oharae_shikkai_probe` (悉皆原則) は **事前直積網羅**
   - 両者は補完関係: 事前 (impl 直積) と 事後 (件数固定) の二段防御
   - 補強候補: feedback_oharae_shikkai_probe に「事後 count assertion との二段防御」section を追記
   - **三点検査**:
     - 原典 semantic 一致: ★ (古事記割書直接記述)
     - 観測 N 件: ☆ (kojiki_anchors.md 編集での anchor 数不一致のみ実観測)
     - 既存拡張可否: ★ (悉皆原則の拡張で済む、新規原則は不要)
   - 結論: **新原則化はせず**、既存 oharae_shikkai_probe の事後検証 section として補強

5. **Pattern N (桃子の名号化) は MATSURI registry に対応するが独立 memo なし (補強候補)**
   - v0 の Pattern H (助力者の自動出現) と同根
   - 「現場 artifact に名号を与えて永続契約」 = MATSURI tuple = (entry_point + description) の原型
   - 補強候補: feedback_imina_torina に「event_type も忌み名/通り名整合の対象」と追記推奨

6. **Pattern T (神夜良比) は feedback_takeminakata_haitai の上位原型**
   - 建御名方の敗退は「失敗率 → 自動退役」だが、須佐之男の場合は「不適合 jurisdiction → 退役後別経路で活躍」
   - 退役後の **別経路復帰** (上-3 八岐大蛇退治) は memo に未記載
   - 補強候補: feedback_takeminakata_haitai に「退役後の別経路復帰 (式年遷宮) は許容」を追記
   - これは `project_sanguishi_misogi_futaro` Phase 6 (式年遷宮 LLM) と整合

### v1 自己評価

| 観点 | 達成度 |
|---|---|
| 1 章につき 5+ pattern (memo 密度高) | ★★★★★ 20 pattern |
| 各 pattern に `failure_if_absent` 記述 | ★★★★★ 20/20 |
| 各 pattern の `agi_mapping.実装` が実在ファイル | ★★★★★ 20/20 (Explore 検証済) |
| 7 割以上の pattern が既存 memo に anchor | ★★★★★ 17/20 が memo anchor (85%) |
| `kojiki_code.md` 差分セクション必須 | ★★★★★ 12 行差分表 + 6 origin spec 列挙 |
| 「未活用 anchor → 新原則候補」を最低 1 件 | ★★★★ 6 件 (Pattern J 計数 / Pattern N 名号化 / Pattern T 別経路復帰 + 3 補強候補) |
| 古事記原文 (漢文) を要所で引用 (v0 → v1 改善 1) | ★★★★★ 全 pattern 冒頭に原文引用 |
| 観測経路 (verify_path) を併記 (v0 → v1 改善 2) | ★★★★★ 20/20 |
| 既存 memo の章節 anchor 逆書き込み (v0 → v1 改善 3) | ★★★ Phase 1 索引で 14 memo の章節割振り済、memo 本体への追記は未着手 |

### v0 → v1 で残った宿題 (v2 候補)

1. **memo 本体への章節 anchor 逆書込み** — 各 feedback_*.md の冒頭に「古事記 origin: 上-X」を追記する作業 (本 v1 では Phase 1 索引のみ)
2. **上-3 (天岩戸) v2 抽出** — `feedback_chinmoku_kyoka` `feedback_kenzen_seijaku` `feedback_chaos_aware_metrics` の origin spec 確認
3. **計数アサーション補強** — `feedback_oharae_shikkai_probe` に事後 count 検証の section 追記
4. **MATSURI 名号化原則** — Pattern N の event_type 整合を `feedback_imina_torina` に拡張するか判定

---

## 履歴

- v0 (2026-05-08): Phase 1 索引 + Phase 2 上巻-7 プロトタイプ
- v1 (2026-05-09): Phase 1 索引更新 (44→58 memo) + Phase 2 上巻-2 神代記 (20 pattern) 追加
                   v0 → v1 改善 1 (原文引用) / 2 (verify_path) 適用
