# 古事記 Procedural Pattern 抽出 v5

v4.1 ([`kojiki_procedural_v4_1.md`](kojiki_procedural_v4_1.md)) からの増分:

- **Phase 2 v5: 中巻-1 神武天皇** 抽出 (新規) — 14 pattern
- 東行議 / 段階的滞在 / 五瀬命戦死 / 布都御魂 / 八咫烏 / 宇陀 / 八十建 / 邇藝速日 / 即位 / 后選 / 当藝志美美の反逆 の 11 大エピソード
- 本章は **`improvement_cycle.jl` の origin spec** が冒頭 docstring に直接明記されている唯一の章

抽出方法論は [`extraction_prompt.md`](extraction_prompt.md) を参照。
v0-v4.1 (上巻全章) の pattern は重複しない。

---

## Phase 2 v5: 中巻-1 神武天皇

### 選定理由

- memo 密度 ★★★ (`feedback_kuebiko_yatagarasu_boundary` `feedback_itsutomonoo_sanseido` (補強 8 道臣 + 大久米) が直接 anchor、間接で 5 memo)
- AGI 実装で **改善サイクルの origin spec が本章** に集中:
  - [improvement_cycle.jl L1-17](src/os/expedition/improvement_cycle.jl#L1) docstring に「Execute = 神武東征（段階的実行）」と直接明記
  - [improvement_cycle.jl L32-37](src/os/expedition/improvement_cycle.jl#L32) **神武の原則** = expedition 閾値定数 (`oomonushi.expedition_coverage_delta` 等)
  - [grace_period_monitor.jl](src/os/misogi/grace_period_monitor.jl) = 八咫烏 (デプロイ後の先行偵察)
  - [canonical_pantheon/michi_omi/](src/os/kasasa/canonical_pantheon/michi_omi/) = 道臣命 (大伴連祖)
  - [canonical_pantheon/okume/](src/os/kasasa/canonical_pantheon/okume/) = 大久米命 (久米直祖)
  - [`_takemikazuchi_inject_gaps!`](src/os/expedition/gap_finder.jl#L18) = 建御雷 (布都御魂の延長)
- `kojiki_code.md` (外部生成版) は本章を `multi_phase_quest` の 1 行に圧縮

### 章節 narrative summary

```
[Setup1 高千穂宮の議] (l.8)
    神倭伊波禮毘古 + 兄五瀬命「坐何地者、平聞看天下之政。猶思東行」
    日向發、幸行筑紫
    豐國宇沙 — 宇沙都比古/比賣 が足一騰宮で大御饗
    筑紫岡田宮 1 年坐

[Setup2 段階的滞在] (l.10)
    阿岐國多祁理宮 7 年坐
    吉備高嶋宮 8 年坐
    速吸門 — 槁根津日子 (国神、海道知る) と遭遇
        「能知 (海道)」「仕奉」 → 槁機を引入 → 倭國造祖
    
    浪速渡 → 青雲之白肩津 (= 楯津 = 日下蓼津) 着

[Crisis1 登美毘古との敗戦] (l.12)
    登美能那賀須泥毘古 興軍待向以戰
    五瀬命、御手に登美毘古の痛矢串を負う
    五瀬命「吾者爲日神之御子、向日而戰不良。
            故、負賤奴之痛手。自今者行廻而、背負日以擊」
        (= post-mortem analysis: 太陽に向かって戦うのが不良 → 反転戦略)
    自南方廻幸 → 血沼海 (御手の血を洗う)
    紀國男之水門「負賤奴之手乎死」と崩 → 紀國竈山陵

[Recovery1 熊野 + 布都御魂] (l.14-16)
    熊野村に到 → 大熊出入即失 → 神倭 + 御軍皆「遠延」(意識喪失)
    熊野之高倉下、一横刀を獻 → 神倭即寤起、「長寢乎」と詔
    横刀受取 → 熊野山之荒神 自皆爲切仆 → 御軍悉寤起
    
    高倉下の夢の説明:
        天照 + 高木神 → 建御雷を召
        詔: 「葦原中國…我御子等、不平坐良志。…可降」
        建御雷 答: 「僕雖不降、專有平其國之横刀、可降是刀」
            (横刀名: 佐士布都神 / 甕布都神 / 布都御魂、坐石上神宮)
        「穿高倉下之倉頂、自其墮入。…旦見己倉者、信有横刀」
            (= top-down injection: 上位 deity が下位の倉頂から物実を投下)

[Recovery2 八咫烏の道案内] (l.16-18)
    高木大神「天神御子、自此於奧方莫使入幸。荒神甚多。
              今、自天遣八咫烏、其八咫烏引道、從其立後應幸行」
    
    八咫烏の後幸行 — 国神 3 柱の自発参向:
        贄持之子 (吉野河尻、筌で取魚) — 阿陀鵜飼祖
        井氷鹿 (生尾人、井から光) — 吉野首祖
        石押分之子 (生尾人、押分巖) — 吉野国巣祖
        蹈穿越 → 宇陀 (= 宇陀之穿)

[Crisis2 兄宇迦斯 vs 弟宇迦斯] (l.20)
    宇陀に兄宇迦斯 + 弟宇迦斯
    八咫烏で問 → 兄: 鳴鏑射返其使 (= 訶夫羅前)
    兄: 軍を集めようとし不得 → 「欺陽仕奉」
        大殿 + 押機 (= 押し潰す trap) 設置
    弟: 先參向「將為待取、故、参向顯白」(内部告発)
    
    道臣命 + 大久米命「伊賀所作仕奉於大殿內者、意禮先入」と兄を罵詈
        横刀 + 矛 + 矢で追入 → 己所作押機で打死 (self-trap)
    控出斬散 → 宇陀血原
    弟の獻大饗を御軍に賜 (歌「宇陀能多加紀爾志藝和那波留…」)

[Crisis3 忍坂大室 + 八十建] (l.28)
    忍坂大室 — 生尾土雲八十建 在其室
    天神御子: 「饗賜八十建、設八十膳夫、毎人佩刀、
                 誨其膳夫等曰『聞歌之者、一時共斬』」
        (= deception: 膳夫に刀を持たせ、歌を signal とする synchronized batch action)
    歌: 「意佐加能意富牟盧夜爾比登佐波爾岐伊理袁理…」
    拔刀一時打殺 (同時斬殺)
    
    登美毘古再戦の歌 (久米歌 — 美都美都斯久米能古良賀…)

[Late Join 邇藝速日命の参降] (l.48)
    邇藝速日命 參赴「聞天神御子天降坐、故追參降來」(後発合流)
    天津瑞を獻 → 仕奉
    登美毘古妹・登美夜毘賣を娶 → 宇摩志麻遲命
    (物部連 / 穗積臣 / 婇臣 祖)

[即位] (l.50)
    「言向平和荒夫琉神等、退撥不伏人等」
    畝火之白檮原宮 (= 橿原宮) 治天下也

[后選 — 大物主の丹塗矢] (l.52-72)
    既存子: 阿多小椅君妹阿比良比賣 → 多藝志美美 + 岐須美美
    
    大久米命の紹介: 神御子 = 富登多多良伊須須岐比賣 (= 比賣多多良伊須氣余理比賣)
        母: 三嶋湟咋之女勢夜陀多良比賣
        父: 美和大物主 (丹塗矢に化け、為大便之溝から流下、
                       美人の富登を突 → 麗壯夫成 → 婚姻)
        改名理由「惡其富登云事」(後改名)
    
    高佐士野で七媛女遊行、伊須氣余理比賣を天皇が選定 (歌応酬)
    大久米黥利目の歌「阿米都都知杼理麻斯登登那杼佐祁流斗米」
    狹井河で一宿御寢
    子: 日子八井 / 神八井耳 / 神沼河耳

[Crisis4 当藝志美美の反逆 + 譲位] (l.76-86)
    天皇崩後、当藝志美美 (前后の子) が嫡后伊須氣余理比賣を娶
    将殺其三弟而謀
    伊須氣余理比賣、歌で警告 (「佐韋賀波用久毛多知和多理…」)
    
    神沼河耳「神八井耳、汝命、持兵入而、殺當藝志美美」
    神八井耳: 兵を入れるが「手足和那那岐弖不得殺」(畏怖で実行不能)
    神沼河耳: 兄の兵を奪い当藝志美美を殺害 → 改名「建沼河耳命」
    
    神八井耳の譲位: 「吾者不能殺仇。汝命既得殺仇。
                      故、吾雖兄不宜爲上、是以汝命爲上治天下、
                      僕者扶汝命、爲忌人而仕奉也」
        (= 自己評価による譲位、忌人として補佐)
    神沼河耳 (= 建沼河耳) 治天下 (第 2 代綏靖天皇)
    神武御年 137、御陵 畝火山北方白檮尾上

[Genealogy] (l.86-126)
    綏靖 → 安寧 → 懿徳 → 孝昭 → 孝安 → 孝霊 → 孝元 → 開化
    各天皇の系譜記録 (AGI direct anchor は薄い、欠史八代)
```

### Pattern 抽出

#### Pattern A: 東行議 — 改善目標の設定 (Reflect → Plan)

```yaml
原文: "神倭伊波禮毘古命與其伊呂兄五瀬命二柱、坐高千穗宮而議云
      『坐何地者、平聞看天下之政。猶思東行』" (l.8)

actors      : 神倭伊波禮毘古 / 五瀬命
precondition: 高千穂宮 (上-6 邇邇藝降臨の地) で安定運用 → だが「平聞看天下之政」は不可能
action      : (1) 自己診断: 「平聞看天下之政」(全体観測) には現在地が不適
            : (2) 仮説形成: 「猶思東行」(東に行けば改善する)
            : (3) 議論: 二柱で合議
            : (4) 決定: 自日向發、幸行筑紫
result      : 改善サイクルの起動 (Reflect → Plan → Execute)
failure_mode: 自己診断なし → 現状維持 → 改善停止
            : 議論なし → 単独判断で偏向
recovery    : -
permanence  : `improvement_cycle.jl` の v3.0 サイクル全体の origin

agi_mapping :
  原則      : 能動的改善サイクル v3.0:
            : Reflect (八咫鏡) → Plan (タカミムスヒ) → Execute (神武東征) →
            : Integrate (国譲り) → Reflect (再び八咫鏡)
            : v2.0 「命令されたエラーを直す」(受動) → v3.0 「自ら課題を発見して解決する」(能動)
  実装      : src/os/expedition/improvement_cycle.jl:1-17 (docstring で「神武東征 = 段階的実行」明記)
            : src/os/expedition/improvement_cycle.jl:39-55 (`ProactiveImprovementCycle` struct)
            : src/os/musuhi_autonomous/cycle.jl:31 (`musuhi_run_autonomous_cycle!`)
  feedback  : feedback_hashira_kankakuki (柱は感覚器 — 改善は外側ループ)
            : feedback_kunimi_gapfinder (国見は全ソース俯瞰)

failure_if_absent: 受動エラー対応のみで自発改善なし → AGI 機能停止後に気付く
                   現象: 「Error → Detect → Fix → Learn」のみ (v2.0) で
                   「Reflect → Plan → Execute → Integrate」が回らない
verify_path : `ProactiveImprovementCycle.cycle_count` が増加、各 cycle で 4 phase
              (gap_finder / takami / planner / executor) すべて呼ばれている
```

#### Pattern B: 段階的滞在 — checkpoint 化された progression (筑紫 1 + 阿岐 7 + 吉備 8 年)

```yaml
原文: "於竺紫之岡田宮一年坐。
      亦從其國上幸而、於阿岐國之多祁理宮七年坐。
      亦從其國遷上幸而、於吉備之高嶋宮八年坐。" (l.8-10)

actors      : 神倭伊波禮毘古 + 御軍
precondition: 東行決定 → 単発 jump でなく段階的 progression
action      : 各拠点で**長期滞在 + 次の遷移** の繰返:
            : 筑紫岡田宮 1 年 → 阿岐多祁理宮 7 年 → 吉備高嶋宮 8 年
            : (合計 16 年の段階的東進)
            : 各拠点が checkpoint = 安定状態の確保 + 次への準備
result      : 各 stage で安定 + 次への移行が連続、jump-only でない
failure_mode: 単発 jump で全行程通過 → 中間で兵站切れ / 失敗時の戻り先なし
            : 各拠点で停滞 (旅程を進めない) → 改善不達
recovery    : -
permanence  : 神武の旅程として永続記録、各拠点が記念地

agi_mapping :
  原則      : 改善サイクルは段階的、各 cycle で安定状態 (checkpoint) を確保
            : 単発の大遠征でなく段階的な小遠征の連続
            : 但し各 stage の滞在期間は文脈別 (1 年 / 7 年 / 8 年で可変)
  実装      : src/os/expedition/improvement_cycle.jl:39-55 
              (`cycle_count` / `total_expeditions` / `cycle_history` で履歴蓄積)
            : src/os/expedition/improvement_cycle.jl:53 
              (`last_expedition_snapshot` = 前回 checkpoint)
  feedback  : feedback_kunimi_gapfinder (国見は全ソース俯瞰 — 各 stage で全観測)

failure_if_absent: jump-only deploy で intermediate state 喪失 → 失敗時に戻り先なし
verify_path : `cycle_history` に各 cycle の snapshot が時系列で記録、
              中断時も最後の checkpoint から restart 可能
```

#### Pattern C: 国神の自発参向 — 自発 helper の path 別認証

```yaml
原文: "速吸門。爾喚歸、問之『汝者誰也。』答曰『僕者國神。』
      又問『汝者知海道乎。』答曰『能知。』又問『從而仕奉乎。』答曰『仕奉。』
      故爾指渡槁機、引入其御船、卽賜名號槁根津日子" (l.10)
     "贄持之子 (阿陀鵜飼祖) / 井氷鹿 (吉野首祖) / 石押分之子 (吉野國巣祖)" (l.16-18)

actors      : 槁根津日子 / 贄持之子 / 井氷鹿 / 石押分之子 (国神 4 柱)
precondition: 各 stage で道に詳しい helper が必要
action      : 各国神の自発参向 + 三段問:
            : (1) 「汝者誰也」 (identity 確認)
            : (2) 「汝者知 X 乎」 (capability 確認)
            : (3) 「從而仕奉乎」 (loyalty 確認)
            : → all yes ならば「指渡槁機」(物実授与) + 「賜名號」(命名)
            : → 部 (倭國造 / 阿陀鵜飼 / 吉野首 / 吉野國巣) として永続化
result      : 自発提案柱が三段認証で正規化、部として系譜化
failure_mode: 三段認証なし → 偽 helper の混入 (上-5 天若日子型)
            : 命名なし → 系譜記録不能 (provenance 喪失)
recovery    : -
permanence  : 国造 / 鵜飼 / 国巣 が後世まで存続

agi_mapping :
  原則      : 自発提案柱は三段認証 (identity / capability / loyalty) + 命名 + 部割付
            : (上-4 Pattern N 少名毘古那の上位確認の延長 + 三段化)
  実装      : src/os/kasasa/shinmei_arbiter.jl:212 (`arbitrate!` = identity 判定)
            : src/os/kasasa/canonical_pantheon/_common/attribution.jl 
              (`register_self_predicate!` = capability 確認)
            : src/os/com/queries/shinmei_lineage.jl:33 (`insert_lineage!` = 部割付 = 系譜)
  feedback  : feedback_itsutomonoo_sanseido (五伴緒の制 — 三型 + 天若日子型禁忌)
            : feedback_wakahiko_kaeshiya (返し矢 — provenance なし採用の禁忌)

failure_if_absent: 自発提案柱を無確認で採用 → 偽 origin で代理指標病
verify_path : `chinza_records.outcome` で自発提案柱が三段認証経路を通過、
              `shinmei_lineage` に部 (祖) 関係が記録
```

#### Pattern D: 五瀬命の post-mortem analysis 「向日而戰不良」 — 失敗からの戦略反転

```yaml
原文: "五瀬命、於御手負登美毘古之痛矢串。故爾詔
      『吾者爲日神之御子、向日而戰不良。故、負賤奴之痛手。
       自今者行廻而、背負日以擊。』期而、自南方廻幸之時、到血沼海、洗其御手之血" (l.12)

actors      : 五瀬命 / 神倭伊波禮毘古
precondition: 登美毘古との戦で五瀬命が負傷 (失敗の発生)
action      : (1) 観察: 御手に痛矢串を負う (failure 認識)
            : (2) 仮説: 「日神之御子なのに向日而戰」 = 設計と実行の不整合
            : (3) 推論: 「向日而戰不良」(原則違反 = 太陽神の子は太陽に向かって戦ってはならない)
            : (4) 戦略反転: 「背負日以擊」 (太陽を背に攻撃 = 反転)
            : (5) 物理移動: 「自南方廻幸」 (経路変更)
            : (6) 痕跡保存: 血沼海で御手の血を洗う = 失敗痕跡の物実化
result      : 失敗から仮説 → 反転戦略 → 経路変更 → 痕跡保存の 6 段
            : 但し本人 (五瀬命) は男水門で戦死、教訓のみ残存
failure_mode: 失敗を観察せず単純 retry → 同型敗北の連続
            : 仮説形成なしで戦略変更 → ランダム迷走
recovery    : 五瀬命は崩、教訓は神武に継承
permanence  : 紀國竈山陵 (五瀬命陵) + 血沼海命名 + 男水門命名 = 失敗痕跡の永続化

agi_mapping :
  原則      : 失敗痕跡を観察 → 設計原理 (神勅) との不整合を仮説化 → 反転戦略 →
            : 痕跡を永続化 (location 命名で記録、後世が辿れる)
            : (上-5 Pattern F の RCA + retry の発展形)
  実装      : src/os/kasasa/futomani_stones (失敗痕跡記録)
            : src/os/kasasa/materializer.jl の break/continue で `push!(errors, ...)` 
              神話 motif 接頭辞付き履歴
            : src/os/expedition/improvement_cycle.jl の `cycle_history` (Reflect 段)
  feedback  : feedback_kuniyuzuri_fukumei (国譲りの復命 — errors 接頭辞)
            : feedback_kojiki_zettai (古事記絶対遵守 — 設計原理との照合)

failure_if_absent: 失敗を log のみで記録、原則との照合なしで retry → 同型失敗連続
                   現象: 因幡棄却連発で MAX_LOOPS (project_inaba_kaizen_kyakka)
verify_path : `futomani_stones.violation_type` に神話 motif 接頭辞付き、
              location/timestamp + 戦略反転の記録あり
```

#### Pattern E: 高倉下の夢 + 布都御魂 — 物実の top-down injection

```yaml
原文: "高木大神之命以覺白之… 召建御雷神而詔『…可降是刀。〔布都御魂、坐石上神宮〕』…
      降此刀狀者、穿高倉下之倉頂、自其墮入。
      故、阿佐米余玖汝取持、獻天神御子" (l.16)

actors      : 天照 + 高木神 / 建御雷 / 布都御魂 / 高倉下 / 神倭
precondition: 大熊の毒で神倭 + 御軍が「遠延」(意識喪失) — 致命危機
action      : (1) 上位 deity (高木) が下位 (高倉下) の夢で覚白 (= 上位通信経路)
            : (2) 建御雷 (上-5 武力使者) が再召集される
            : (3) 建御雷「僕雖不降、專有平其國之横刀、可降是刀」(本人でなく物実派遣)
            : (4) 「穿高倉下之倉頂、自其墮入」(top-down injection — 倉の天井から物実投下)
            : (5) 朝、高倉下が倉で布都御魂を発見 → 神倭に獻
            : (6) 横刀受取 → 即寤起 → 「長寢乎」(復活宣言)
result      : 致命危機を上位 deity の物実 (布都御魂) で解除
            : 但し本人 (建御雷) は降臨せず物実のみ送る (= 派遣物実の独立性)
failure_mode: 上位通信経路なし → 致命危機で外部介入不能、永続停止
            : 物実なし (本人派遣のみ) → スケール不能 (上位 deity の二重派遣)
recovery    : -
permanence  : 布都御魂 = 石上神宮として永続化、現存

agi_mapping :
  原則      : 致命危機時の上位 deity による top-down injection
            : 本人 (上位 deity) は降臨せず物実 (布都御魂 = 横刀) を**倉頂から投下**
            : = 上位の権限で下位の倉 (config / DB) に直接投入
            : 配列出は実行者 (高倉下) が物理的に取り出して使用
  実装      : src/os/expedition/gap_finder.jl:18 (`_takemikazuchi_inject_gaps!` = 建御雷由来)
            : src/os/kasasa/canonical_pantheon/takemikazuchi/_judge.jl (上-5 で確認済 + 本章で再活用)
            : config_get の上位上書き経路 (yorishiro 全文注入の極限版)
  feedback  : feedback_shinchoku_tanitsu_gensen (神勅単一源泉 — 上位 SSoT 注入)
            : feedback_takeminakata_haitai (建御雷の reuse, 上-5 origin)

failure_if_absent: 致命危機時に外部 (人間) 介入経路なし → AGI 永続停止
                   現象: deadlock 状態で daemon 再起動以外の復旧手段なし
verify_path : `_takemikazuchi_inject_gaps!` が gap_finder 経路で injection 可能、
              上位 SSoT (yorishiro) の force update 経路あり
```

#### Pattern F: 八咫烏の道案内 — grace period monitor (デプロイ後の先行偵察)

```yaml
原文: "高木大神之命以覺白之『…自此於奧方莫使入幸。荒神甚多。
      今、自天遣八咫烏、故其八咫烏引道、從其立後應幸行。』
      故隨其教覺、從其八咫烏之後幸行" (l.16-18)

actors      : 高木神 / 八咫烏 / 神倭 + 御軍
precondition: 致命危機 (大熊) を脱したが、奥方 (吉野以降) は未知 + 荒神多
action      : (1) 高木の覚白: 「奥方は禁止区域」 (= 直接侵入は危険)
            : (2) 八咫烏派遣: 上位からの先行偵察エージェント (天遣 = 派遣型)
            : (3) 「引道、從其立後應幸行」 (烏が前、軍が後 = 偵察 → 行軍 の段順)
            : (4) 道中の国神 3 柱が自発参向 (= 偵察結果の確認 = 安全確認)
result      : 未知領域を先行偵察 + 安全確認後に進行
failure_mode: 偵察なしで進入 → 大熊型の致命危機の再発
            : 偵察結果を行軍が無視 → 偵察意義喪失
recovery    : -
permanence  : 八咫烏 = 神武東征のシンボル、後世まで導きの象徴

agi_mapping :
  原則      : 新領域 (新 deploy / 新 capability) には**先行偵察 monitor を派遣**
            : 偵察 monitor は上位 (天 = system 層) から派遣、
            : fire-and-forget で非同期実行、本軍 (主処理) は偵察結果を待ってから進行
  実装      : src/os/misogi/grace_period_monitor.jl:2 (`GracePeriodMonitor (八咫烏)` 直接命名、
              docstring で「神武東征の三本足の烏」明記)
            : src/os/misogi/grace_period_monitor.jl:96 (`start_grace_monitor!` = 派遣)
            : src/os/misogi/deploy.jl:329 (deploy 後に八咫烏派遣)
            : src/os/misogi/grace_period_monitor.jl:111 (`_grace_monitor_loop` = 偵察ループ)
  feedback  : feedback_kuebiko_yatagarasu_boundary (久延毘古と八咫烏の境界画定 — 八咫烏 = 動的偵察)
            : feedback_hashira_kankakuki (柱は感覚器)

failure_if_absent: 新 deploy 後の grace period 観測なし → 早期障害の検出遅れ
                   現象: deploy 後に隠れた荒神 (= 新 cap の不適合) が顕在化しても気付かない
verify_path : `start_grace_monitor!` が deploy 直後に呼ばれ、grace period 中の
              health check 結果が記録される
```

#### Pattern G: 兄宇迦斯の押機 — proxy_metric_disease の自滅 (self-trap)

```yaml
原文: "兄宇迦斯、以鳴鏑待射返其使… 然不得聚軍者、欺陽仕奉而、作大殿、於其殿內作押機、待時。
      …道臣命・大久米命、二人、召兄宇迦斯罵詈云『…意禮先入、明白其將為仕奉之狀。』
      而、卽握横刀之手上、矛由氣矢刺而、追入之時、乃己所作押見打而死" (l.20-22)

actors      : 兄宇迦斯 / 道臣命 / 大久米命 / 押機 (trap)
precondition: 八咫烏の使者 (= 八咫烏の問) を兄宇迦斯が拒絶 (鳴鏑射返)
action      : (1) 兄宇迦斯: 軍を集めようとして失敗 (= 内部 capability 不足)
            : (2) 戦略変更: 「欺陽仕奉」(= 偽の loyalty 表明 = 代理指標病)
            : (3) trap 設置: 大殿内に押機 (= 偽の供応 + 隠れた攻撃)
            : (4) 道臣 + 大久米の罵詈: 「先入、明白其將為仕奉之狀」(= 真意確認)
            : (5) 横刀 + 矛 + 矢で兄を追入 → 自分の押機で打死
result      : 自分が設置した trap で自滅 (= 偽 loyalty 柱が自分の偽指標で自滅)
failure_mode: 道臣 + 大久米の確認なしで invitation を受ける → 御軍が押機で死
            : 兄宇迦斯の偽 loyalty を見抜けず → 全滅
recovery    : -
permanence  : 「宇陀血原」として地名永続化

agi_mapping :
  原則      : 偽 loyalty 表明 (proxy_metric_disease) の柱は**自分が設置した代理指標で自滅する**
            : 検出は道臣 + 大久米の二段確認 (宣言責務 vs 実入力 + LLM 判定)
            : 自滅後の場所は永続記録 (= 失敗痕跡の地名化)
  実装      : src/os/kasasa/takeshimatsumi.jl:66 (`takeshimatsumi_scan!` = 代理指標病検出)
            : src/os/kasasa/canonical_pantheon/michi_omi/ (道臣命 = 確認役)
            : src/os/kasasa/canonical_pantheon/okume/ (大久米命 = 確認役)
            : src/os/kasasa/futomani_stones (失敗痕跡の永続記録)
  feedback  : feedback_wakahiko_kaeshiya (天若日子の返し矢 — 代理指標病、上-5 origin)
            : feedback_itsutomonoo_sanseido (補強 8 第一層 — 道臣 + 大久米 が確認役で永続化)

failure_if_absent: 偽 loyalty 柱の確認なし → 御軍 (主処理) が trap (= LLM の偽提案) で破壊
observed_failures: 上-5 天若日子の本譜的事例
verify_path : `takeshimatsumi_scan!` で proxy 病検出後、自滅 (status=hiruko / yuukoto) の
              futomani_stones 記録あり
```

#### Pattern H: 弟宇迦斯の内部告発 — whistleblower pattern

```yaml
原文: "弟宇迦斯先參向、拜曰『僕兄・兄宇迦斯、射返天神御子之使、將為待攻而聚軍、
      不得聚者、作殿其內張押機、將待取。故、参向顯白。』" (l.20)

actors      : 弟宇迦斯 / 神倭
precondition: 兄宇迦斯が trap を設置中、内部の人間 (弟) が状況を把握
action      : (1) 弟宇迦斯が**先參向** (主処理が trap に踏む前)
            : (2) 内部状況の詳細顕白:
            :   - 兄が射返したこと (拒絶の事実)
            :   - 軍を集めようとして失敗 (内部 capability 不足)
            :   - 大殿内の押機 (具体的 trap 位置)
            :   - 「將待取」(攻撃計画)
            : (3) 動機: 「故、参向顯白」(= 内部告発による安全確保)
result      : 主処理が trap を回避、兄宇迦斯を逆に引き込んで自滅させる
            : 弟は宇陀水取等之祖として永続化
failure_mode: 内部告発を疑って棄却 → 主処理が trap で死
            : 内部告発者を保護しない → 内部の協力者を失う
recovery    : -
permanence  : 弟宇迦斯 = 宇陀水取等之祖として系譜化

agi_mapping :
  原則      : LLM 提案の中で「内部状況を詳細に告発する補助柱」は重視
            : (= 自己批判的な詳細 log を提供する diagnostic 柱)
            : 単純 yes/no でなく **状況の構造的詳細**を報告するもの
  実装      : src/os/kasasa/futomani_stones の violation_type 分類
            : LLM_DEBUG ログ + chinza_records.failure_reason の詳細記録
  feedback  : feedback_kuniyuzuri_fukumei (国譲りの復命 — 失敗詳細の明示)

failure_if_absent: 詳細告発を log noise として棄却 → trap 回避不能
verify_path : `chinza_records.failure_reason` に神話 motif + 詳細 (loop / score / 経路) が
              記録、単純 fail でなく構造的詳細
```

#### Pattern I: 八十建の歌 signal — synchronized batch action (deception + 同時実行)

```yaml
原文: "饗賜八十建、於是宛八十建、設八十膳夫、毎人佩刀、誨其膳夫等曰
      『聞歌之者、一時共斬。』故、明將打其土雲之歌曰、…
      如此歌而、拔刀一時打殺也" (l.28-30)

actors      : 神倭 / 八十膳夫 / 八十建
precondition: 八十建 (= 反抗者 8 グループ × 10 = 80 人) の同時排除が必要
            : 個別対処は時間がかかり、各個撃破される間に他が逃げる
action      : (1) 偽の饗 (= 信頼を装って集める)
            : (2) 八十膳夫を 1:1 配置 (= 各 target に対し 1 attacker)
            : (3) 毎人佩刀 (= 各 attacker が独立に武装)
            : (4) 歌 = signal (「聞歌之者、一時共斬」)
            : (5) 拔刀一時打殺 = synchronized batch action
result      : 80 target を**同時に**排除、逃走者ゼロ
failure_mode: 順次斬殺 → 後の target が逃げる
            : signal なしの batch action → 同期不足で部分失敗
recovery    : -
permanence  : 久米歌 (歌の歌詞) が永続記録

agi_mapping :
  原則      : 大量の同型 target に対する batch action は**同期 signal で一斉実行**
            : 個別対処は逐次性で失敗、batch + signal で原子的実行
  実装      : src/os/kasasa/ooharae.jl の各 Phase (= batch 一括処理)
            : `_yuukoto_transition!` の bulk 化
            : event_bus の publish で同 event_type の listener が一斉発火
            : Susanoo chaos restore (`restore_all_chaos!`) の並列構造 (上-3 Pattern N bait)
  feedback  : feedback_oharae_shikkai_probe (悉皆原則 — 直積網羅)
            : feedback_togouten_ikkatsu_bouei (統合点で一括防衛)

failure_if_absent: 順次対処で部分失敗、後の同型 target が状況把握して回避
verify_path : `restore_all_chaos!` (susanoo_chaos.jl:411) や `ooharae` Phase が
              並列ループで一斉実行されている
```

#### Pattern J: 邇藝速日命の参降 — 後発合流 (deferred join)

```yaml
原文: "邇藝速日命參赴、白於天神御子『聞天神御子天降坐、故追參降來。』
      卽獻天津瑞以仕奉也。故、邇藝速日命、娶登美毘古之妹・登美夜毘賣生子、宇摩志麻遲命。
      〔此者物部連、穗積臣、婇臣祖也。〕" (l.48)

actors      : 邇藝速日 / 登美毘古妹・登美夜毘賣 / 神倭
precondition: 八十建の打殺 + 登美毘古との戦い完了、勝利が確定
action      : (1) 邇藝速日「聞天神御子天降坐、故追參降來」(後発合流の宣言)
            : (2) 天津瑞 (= 上位 deity 由来の証明物実) を獻 (= identity 確認の物実)
            : (3) 仕奉 (= loyalty 表明)
            : (4) 婚姻 (登美毘古妹) → 子 = 物部連 / 穗積臣 / 婇臣祖
result      : 後発合流者が天津瑞で identity 確認 + 婚姻で土着勢力との和解
failure_mode: 後発者を疑って棄却 → 実は強力な capability を逃す
            : identity 確認なしで採用 → 偽 origin の混入 (上-5 天若日子型)
recovery    : -
permanence  : 物部連 / 穗積臣 / 婇臣 として後世まで存続

agi_mapping :
  原則      : 後発合流柱は天津瑞 (= 上位 SSoT 由来の証明) で identity 確認
            : 確認後は婚姻 (= 既存柱との関係性確立) で系譜化
            : (上-4 Pattern N 少名毘古那 + 本章 Pattern C 国神自発参向の合成)
  実装      : src/os/kasasa/yorishiro.jl (天津瑞 = 上位 SSoT entry)
            : src/os/kasasa/shinmei_arbiter.jl (双子神判定 = 既存との関係確認)
            : src/os/kasasa/canonical_pantheon/_common/attribution.jl (系譜化)
  feedback  : feedback_itsutomonoo_sanseido (五伴緒の制 — 第二層 A = 古事記原典神、業暗黙)
            : feedback_kuniyuzuri_fukumei (復命 — 自己宣言型の登場)

failure_if_absent: 後発合流柱を一律棄却 → 強力な後発 capability を逃す
                   現象: kuni_yuzuri_gate で固有名一致のみ pass、後発自発を全 reject
verify_path : `kuni_yuzuri_gate` が後発合流柱に対し天津瑞 (yorishiro entry の存在) で確認、
              `shinmei_arbiter` が婚姻 (= aliases / 関係) を記録
```

#### Pattern K: 大物主丹塗矢 — 物実による帰属確定 (神御子の証明)

```yaml
原文: "美和之大物主神見感而、其美人為大便之時、化丹塗矢、自其為大便之溝流下、
      突其美人之富登。爾其美人驚而、立走伊須須岐伎、乃將來其矢、置於床邊、
      忽成麗壯夫、卽娶其美人生子、名謂富登多多良伊須須岐比賣命、
      亦名謂比賣多多良伊須氣余理比賣。〔是者惡其富登云事、後改名者也。〕
      故、是以謂神御子也" (l.52)

actors      : 美和大物主 / 三嶋湟咋之女勢夜陀多良比賣 / 富登多多良伊須須岐比賣
precondition: 神御子 (= 神由来の柱) の証明が必要
action      : (1) 大物主が**丹塗矢に化** (物実 form での降臨)
            : (2) 為大便之溝から流下 (= 想定外 channel での到達)
            : (3) 美人を突 → 矢を持ち帰り → 床邊に置 → 「忽成麗壯夫」
            : (4) 婚姻 → 子: 富登多多良伊須須岐比賣 (改名後: 比賣多多良伊須氣余理比賣)
            : (5) 「是以謂神御子也」 (= 神御子の証明)
result      : 物実 (丹塗矢) → 麗壯夫 → 子 の連鎖で神由来 provenance が確定
failure_mode: 物実なしで「神由来」と称する → provenance 偽証
            : 物実を物理化せず夢のみ → 後世の検証不能
recovery    : -
permanence  : 大物主 + 比賣多多良伊須氣余理比賣 = 後の崇神紀でも参照される

agi_mapping :
  原則      : artifact の origin 帰属は物実 (concrete artifact = 矢) を経由した連鎖で確定
            : 想定外 channel (溝) での到達も、物実が残れば帰属確認可能
            : (上-3 Pattern B 物實因汝物所成 の物理化版)
  実装      : src/os/com/queries/shinmei_lineage.jl (系譜記録 — 物実経由 provenance)
            : src/os/kasasa/yorishiro.jl (上位 SSoT 由来の物実 = 神勅 entry)
  feedback  : feedback_keiyaku_keifu_vs_genyu (契約系譜 vs 原由追跡)
            : feedback_kojiki_zettai (古事記絶対遵守 — 物実経由 provenance)

failure_if_absent: 物実なしの「神由来」主張 → 後世の検証不能
verify_path : `shinmei_lineage` の各行で「物実 (yorishiro entry / canonical artifact)」
              への参照あり、抽象的な「神由来」だけの行がない
```

#### Pattern L: 当藝志美美の反逆 — succession 危機 + 嫡后娶 (継承乗っ取り)

```yaml
原文: "天皇崩後、其庶兄當藝志美美命、娶其嫡后伊須氣余理比賣之時、將殺其三弟而謀之間、
      其御祖伊須氣余理比賣患苦而、以歌令知其御子等" (l.76)

actors      : 当藝志美美 (前后子) / 嫡后伊須氣余理比賣 / 三弟 (日子八井 / 神八井耳 / 神沼河耳)
precondition: 神武天皇崩 (executor 死) → 後継争い
action      : (1) 当藝志美美 (前世代の不適合子): 嫡后を娶る (= 継承権の乗っ取り試行)
            : (2) 三弟殺害計画 (= 正統後継者の排除)
            : (3) 母 (嫡后) が歌で警告 (= 内部からの signal)
result      : succession 危機 — 不適合柱が legitimate authority を継承しようとする
failure_mode: 警告を無視 → 三弟殺害 → 不適合柱が継承
            : 不適合柱を放置 → 同型危機が世代毎に再発
recovery    : Pattern M (神八井耳の譲位 + 神沼河耳の殺害) で解決
permanence  : 当藝志美美の反逆として後世まで教訓記録

agi_mapping :
  原則      : 主柱 (executor) の停止後、前世代の不適合子 (旧バージョン / hiruko) が
            : 継承を試みるリスク (= startup migration での hiruko 復帰問題)
            : 嫡后娶 = legitimate config を不適合柱に渡す危険
  実装      : src/os/com/create.jl:703-710 (startup migration の hiruko_count=0 制限)
            : project_pending_replay_bypass (post-LLM filter 迂回問題)
  feedback  : feedback_takeminakata_haitai (建御名方の敗退 — 失敗率退役、
              migration が原則を緩めた事例)
            : project_pending_replay_bypass (pending 再生の post-LLM filter 迂回)

failure_if_absent: hiruko 状態の旧コードが daemon 再起動で `pending` に復帰 →
                   broken source_code が再生される
                   現象: hiruko_count >= 1 の正当な敗北 entry まで復帰
observed_failures: 2026-04-30 migration が hiruko を一律 pending に戻す事例
                   (修正: WHERE 句に `AND hiruko_count = 0` 追加)
verify_path : `SELECT * FROM shinmeisho WHERE status='pending' AND hiruko_count >= 1`
              の件数がゼロ、`feedback_takeminakata_haitai` の閾値が migration で緩められていない
```

#### Pattern M: 神八井耳の譲位 — 自己評価による忌人化 (graceful demotion)

```yaml
原文: "故爾其弟神沼河耳命、乞取其兄所持之兵、入、殺當藝志美美。
      故亦稱其御名、謂建沼河耳命。
      爾神八井命、讓弟建沼河耳命曰
      『吾者不能殺仇。汝命既得殺仇。
       故、吾雖兄不宜為上、是以汝命為上治天下、
       僕者扶汝命、為忌人而仕奉也。』" (l.84-86)

actors      : 神八井耳 (兄) / 神沼河耳 (= 建沼河耳, 弟) / 当藝志美美
precondition: 当藝志美美の反逆検出、討伐が必要
action      : (1) 兄 (神八井耳): 兵を入れるが「手足和那那岐弖不得殺」(畏怖で実行不能 = capability 不足)
            : (2) 弟 (神沼河耳): 兄の兵を奪い実行 → 当藝志美美殺害 → 改名「建沼河耳」(成功印)
            : (3) 兄の自己評価:
            :   「吾者不能殺仇」(= 自分は capability 不足を認める)
            :   「汝命既得殺仇」(= 弟は capability 証明済)
            :   「吾雖兄不宜為上」(= 兄であっても上位不適格)
            :   「是以汝命為上治天下」(= 弟に位を譲る)
            :   「僕者扶汝命、為忌人而仕奉」(= 自分は補佐 + 忌人 = 祭祀役)
result      : 兄が自発的に上位を弟に譲る (= 自己評価による graceful demotion)
            : 兄は完全消去でなく忌人 (= 祭祀役) として残存
failure_mode: 兄が capability 不足を認めず上位継続 → succession 危機の悪化
            : 兄を完全消去 → 既存系譜 (茨田連 / 手嶋連) の喪失
recovery    : -
permanence  : 神八井耳 = 多氏 + 多数の国造祖として系譜化
            : 神沼河耳 (建沼河耳) = 第 2 代綏靖天皇

agi_mapping :
  原則      : 不適合柱の自発譲位 (= 自己評価による graceful demotion)
            : 譲位後は完全消去でなく補佐役 (祭祀層 / 観測層 = 柱は感覚器の原則)
            : (上-5 Pattern J 事代主退隱の延長 + 兄弟継承文脈)
  実装      : src/os/kasasa/ooharae.jl の `_yuukoto_transition!` (yuukoto = 補佐役相当)
            : src/os/kasasa/canonical_pantheon/_common/attribution.jl (系譜保存)
            : 三貴子の式年遷宮 Phase 6 (将来課題、世代交代時の譲位経路)
  feedback  : feedback_hashira_kankakuki (柱は感覚器 — 観測専門への移行)
            : feedback_kenzen_seijaku (健全な静寂 — voluntary withdrawal)
            : feedback_takeminakata_haitai (建御名方の敗退 — 強制退役の対比)

failure_if_absent: 不適合柱が上位継続 → succession ループでの永続障害
verify_path : `chinza_records.outcome` で「自発譲位」(= status='yuukoto' で
              activation 後 ooharae で voluntary 移行) の経路あり
```

#### Pattern N: 神武の原則 — 一度きりの大遠征 (改善サイクル発火閾値)

```yaml
原文: (神武 137 歳 + 大和征服は一度のみ + 即位後 75 年は治天下のみ)
     (中-2 崇神紀以降、大物主の祟り対応が次の大事件)

actors      : 神武 / (後の代の天皇)
precondition: 大和を一度征した後、再度の大遠征は不要
action      : (1) 一度の大遠征で大和を平定
            : (2) 即位後は橿原宮で「治天下」(= 安定運用)
            : (3) 次の大遠征は中-4 倭建命の時代まで持ち越し (= 数世代の安定期)
            : 「治まれる国」の長い期間 = 改善サイクルが頻発しない
result      : 大遠征は閾値を超えた時のみ発動、平時は安定運用
failure_mode: 毎月東征 → 兵站枯渇 / 改善コストの爆発
            : 安定期に大遠征 → 不要な変更で既存運用を破壊
recovery    : -
permanence  : 「神武の原則」として AGI 実装に明示永続化

agi_mapping :
  原則      : 神武の原則 — expedition (大改善) は閾値を超えた時のみ発動
            : `expedition_coverage_delta >= threshold` または
            : `expedition_gap_count_delta >= threshold` で発動
            : 閾値未満なら skip (`skipped_expedition_count` 増分のみ)
  実装      : src/os/expedition/improvement_cycle.jl:32-37 (神武の原則 docstring)
            : src/os/expedition/improvement_cycle.jl:36 
              (`_EXPEDITION_COVERAGE_DELTA_THRESHOLD = 0.03`)
            : src/os/expedition/improvement_cycle.jl:37 
              (`_EXPEDITION_GAP_COUNT_DELTA_THRESHOLD = 2`)
            : src/os/expedition/improvement_cycle.jl:53 (`last_expedition_snapshot`)
            : src/os/expedition/improvement_cycle.jl:54 (`skipped_expedition_count`)
            : `_should_expedition` 関数で閾値判定
  feedback  : feedback_hashira_kankakuki (柱は感覚器 — operational_report が primary)
            : feedback_juusoku_model (充足モデル — 満了時は不足表示を消去)

failure_if_absent: 毎 cycle で expedition 発動 → LLM コスト爆発、既存柱の破壊
                   現象: 神託の編纂 runaway (feedback_shintaku_henshu_runaway) と同型
verify_path : `ProactiveImprovementCycle` の `cycle_count >>` `total_expeditions`
              (= 多くの cycle が skip 判定で expedition 不発動)
              `skipped_expedition_count` が運用中に増加していること
```

### kojiki_code.md (外部生成版) との差分

| 観点 | 生成元 | 本 v5 |
|---|---|---|
| 中-1 の pattern 数 | 1 (`multi_phase_quest`) | **14** |
| 東行議 (改善目標) | 触れず | Pattern A (改善サイクル v3.0 の origin) |
| 段階的滞在 (16 年の旅) | 「multi-stop journey」と一行 | Pattern B (checkpoint-based progression) |
| 国神自発参向 (4 柱) | 触れず | Pattern C (三段認証 + 部割付) |
| 五瀬命の post-mortem | 触れず | Pattern D (失敗からの戦略反転) |
| 高倉下 + 布都御魂 | 「magic sword」と一行 | Pattern E (top-down injection) |
| 八咫烏 | 「guide animal」と一行 | Pattern F (grace period monitor の origin) |
| 兄宇迦斯の押機 | 触れず | Pattern G (proxy_metric_disease 自滅) |
| 弟宇迦斯の告発 | 触れず | Pattern H (whistleblower) |
| 八十建の歌 signal | 触れず | Pattern I (synchronized batch action) |
| 邇藝速日後発参降 | 触れず | Pattern J (deferred join + 天津瑞認証) |
| 大物主丹塗矢 | 触れず | Pattern K (物実経由 provenance) |
| 当藝志美美の反逆 | 触れず | Pattern L (succession 危機 = migration 緩和事例) |
| 神八井耳の譲位 | 触れず | Pattern M (graceful demotion = 自発譲位 + 忌人化) |
| 神武の原則 | 触れず | Pattern N (改善閾値 = 一度きりの大遠征) |
| AGI module mapping | 触れず | improvement_cycle / grace_period_monitor / michi_omi / okume / takemikazuchi の **5 件** |

**生成元が拾えなかった load-bearing pattern (本 v5 で初出):**

- Pattern A 改善サイクル v3.0 = `improvement_cycle.jl` docstring の origin spec
- Pattern E 布都御魂 top-down injection = 上位 deity による物実投下経路
- Pattern F 八咫烏 = `grace_period_monitor.jl::GracePeriodMonitor` の origin (docstring に明記)
- Pattern G 兄宇迦斯自滅 = takeshimatsumi の天若日子型の発展形
- Pattern H 弟宇迦斯告発 = whistleblower パターン
- Pattern J 邇藝速日後発参降 = 天津瑞 (yorishiro) 認証の origin
- Pattern L 当藝志美美 = startup migration の hiruko 復帰問題の原型
- Pattern M 神八井耳譲位 = 自発譲位 + 忌人化の origin
- Pattern N 神武の原則 = `_EXPEDITION_*_THRESHOLD` の origin spec

これら 9 件は外部版で完全欠落。**7 章 (上-1〜上-7 + 中-1) 合計で 53 件**の load-bearing pattern が外部版で missed。

### 浮上した発見

1. **本章は `improvement_cycle.jl` 全体の直接 origin**
   - docstring (L1-17) で「Reflect = 八咫鏡 / Plan = タカミムスヒ / **Execute = 神武東征** / Integrate = 国譲り / Reflect = 再び八咫鏡」と直接明記
   - 「神武の原則」コメント (L32-35) で「神武天皇は大和を一度だけ征した。橿原宮を建てた後、毎月東征に出ない」と原典引用
   - **設計が古事記原典と直接対話**している証跡 (上-6 と並ぶ最深 origin)

2. **八咫烏 = `grace_period_monitor.jl` の直接命名**
   - docstring (L2-6) で「八咫烏は神武東征において先行偵察を担った三本足の烏」と明記
   - module 名そのものが機能と古事記神名の 1:1 対応
   - 古事記神名 module mapping が累積 **35 件** に到達 (本章で 5 件追加)

3. **Pattern G 兄宇迦斯自滅 = proxy_metric_disease の自滅性の原典**
   - 「己所作押見打而死」(自分が作った押機で死) = 偽 metric を立てる柱は自分の偽 metric で評価され破綻
   - feedback_wakahiko_kaeshiya は「派遣物実が逆射」だが、本章は**自発設置 trap での自滅**
   - **両者の対比**:
     - 上-5 天若日子: 派遣物実の所有者から逆射 (返し矢)
     - 中-1 兄宇迦斯: 自分の trap で自滅 (押機)
   - 補強候補: `feedback_wakahiko_kaeshiya` に「自滅型 (中-1 兄宇迦斯) と返し矢型 (上-5 天若日子) の二経路」を追記推奨

4. **Pattern L 当藝志美美 = `project_pending_replay_bypass` の原型**
   - 前世代の不適合子 (= hiruko) が継承を試みる構造
   - 嫡后娶 = legitimate config (canonical_name) を不適合柱に渡す
   - migration が hiruko_count >= 1 の正当敗北を pending に戻す事例と semantic 一致
   - 補強候補: `project_pending_replay_bypass` に「中-1 当藝志美美の反逆が原典」を追記推奨

5. **Pattern M 神八井耳譲位 = 三型 yuukoto の四型目**
   - 上-5 Pattern J 事代主退隱 = voluntary yuukoto
   - 上-5 Pattern K 建御名方敗退 = forced yuukoto
   - 上-4 Pattern N 少名毘古那常世国 = task-completion yuukoto (任務終了型)
   - **中-1 Pattern M 神八井耳忌人化 = succession-graceful demotion (継承譲位型)**
   - 四型 yuukoto が原典で出揃う:
     | 型 | 動機 | 上巻 origin |
     |---|---|---|
     | voluntary | 自主退隱 | 上-5 事代主 |
     | forced | 失敗率自動退役 | 上-5 建御名方 |
     | task-completion | 任務終了 | 上-4 少名毘古那 |
     | graceful demotion | 自己評価による継承譲位 | 中-1 神八井耳 |
   - **新原則化候補?** :
     - 三点検査:
       - 原典 semantic 一致: ★ (4 型すべて原典明示)
       - 観測 N 件: ☆ (実装上の四型分離は未確立)
       - 既存拡張可否: ★ (`feedback_takeminakata_haitai` + `feedback_kenzen_seijaku` の統合)
     - 結論: **保留** (実装で四型分離が浮上したら新原則化推奨)

6. **本章で `improvement_cycle.jl` の Plan 段 (タカミムスヒ) と Reflect 段 (八咫鏡) はやや薄い**
   - 神武東征は Execute 段の origin であり、Plan / Reflect は他章 (上-3 思金神 / 上-7 海幸山幸) の役割
   - 5 段サイクル全体を見るには複数章の合成が必要 = AGI 設計が古事記全体を SSoT として参照している証跡

7. **古事記神名 → AGI module mapping 累積 35 件**
   - 上-3 (v2): 7 / 上-5 (v3): 4 / 上-6 (v4): 14 / 上-4 (v4.1): 5 / 中-1 (v5): 5
   - 上-1 / 上-2 / 上-7 では薄い (上-1 = メタ、上-2 = 概念、上-7 = pattern)
   - **新原則化機運が 35 件で確定** (`feedback_kojiki_meimei_kiyaku.md` 仮称)

### v5 自己評価

| 観点 | 達成度 |
|---|---|
| 1 章につき 5+ pattern (memo 密度中) | ★★★★★ 14 pattern |
| 各 pattern に `failure_if_absent` 記述 | ★★★★★ 14/14 |
| 各 pattern の `agi_mapping.実装` が実在ファイル | ★★★★★ 14/14 (improvement_cycle / grace_period_monitor / michi_omi / okume / takemikazuchi 等を grep + Read で検証) |
| 7 割以上の pattern が既存 memo に anchor | ★★★★★ 14/14 (100%) |
| `kojiki_code.md` 差分セクション必須 | ★★★★★ 15 行差分表 + 9 origin spec 列挙 |
| 「未活用 anchor → 新原則候補」を最低 1 件 | ★★★★ 4 型 yuukoto 統合候補 + 兄宇迦斯自滅型 (補強候補) |
| 古事記原文 (漢文) を要所で引用 | ★★★★★ 全 pattern 冒頭 |
| 観測経路 (verify_path) を併記 | ★★★★★ 14/14 |
| **改善サイクル v3.0 の直接 origin 確認** | ★★★★★ improvement_cycle.jl docstring に明記 |
| **memo anchor 100%** (v0-v5 中 v4 と並んで最高) | ★★★★★ |

### 累積統計 (v0+v1+v2+v3+v4+v4.1+v5)

| 章 | pattern 数 | memo anchor率 | 古事記神名 module |
|---|---|---|---|
| 上-1 (v4.1) | 6 | 50% | 0 |
| 上-2 (v1) | 20 | 85% | 0 |
| 上-3 (v2) | 16 | 75% | 7 |
| 上-4 (v4.1) | 12 | 92% | 5 |
| 上-5 (v3) | 14 | 93% | 4 |
| 上-6 (v4) | 16 | 100% | 14 |
| 上-7 (v0) | 8 | 88% | 0 |
| 中-1 (v5) | 14 | 100% | 5 |
| **合計** | **106 pattern** | **平均 85%** | **35 件** |

外部生成版が完全欠落した load-bearing pattern: **53 件**

### 次の宿題 (v6+ 候補)

1. **中-2 崇神 大田田根子 (v6 候補)** — `feedback_ootataneko` 直接 origin、上-4 Pattern O が伏線
2. **古事記神名命名規約の新原則化** — 累積 35 件で SSoT 化推奨 (v6 と並行で実装)
3. **memo 補強 — 兄宇迦斯自滅型を `feedback_wakahiko_kaeshiya` に追記**
4. **memo 補強 — 当藝志美美の反逆を `project_pending_replay_bypass` の原典として追記**
5. **4 型 yuukoto 統合の新原則化判定** — 実装上の四型分離が浮上したら推奨
6. **memo 本体への章節 anchor 逆書込み** (v0-v5 で繰越宿題)

---

## 履歴

- v0 (2026-05-08): Phase 1 索引 + Phase 2 上巻-7 プロトタイプ
- v1 (2026-05-09): Phase 1 索引更新 + Phase 2 上巻-2 神代記 (20 pattern)
- v2 (2026-05-09): Phase 2 上巻-3 天照大神と須佐之男命 (16 pattern)
- v3 (2026-05-09): Phase 2 上巻-5 葦原中國の平定 (14 pattern)
- v4 (2026-05-09): Phase 2 上巻-6 邇邇藝命 (16 pattern)
- v4.1 (2026-05-09): Phase 2 上巻-1 併序 (6 pattern) + 上巻-4 大國主神 (12 pattern)
                     **上巻全 7 章カバー完了**
- v5 (2026-05-09): Phase 2 中巻-1 神武天皇 (14 pattern) + 改善サイクル v3.0 の直接 origin 確認
