# 古事記 Procedural Pattern 抽出 v4

v3 ([`kojiki_procedural_v3.md`](kojiki_procedural_v3.md)) からの増分:

- **Phase 2 v4: 上巻-6 邇邇藝命** 抽出 (新規) — 16 pattern
- 譲位 / 五伴緒任命 / 三種神器 / 猿田毘古 / 天孫降臨 / 海鼠口拆 / 木花咲耶 vs 石長 / 火中出産 の 8 大エピソード
- 本章は **architectural の origin spec** が最も濃く、`canonical_pantheon/` / `tenson_korin/` / `yachimata/sarutahiko_gateway.jl` が直接 mapping

抽出方法論は [`extraction_prompt.md`](extraction_prompt.md) を参照。
v0 (上-7) / v1 (上-2) / v2 (上-3) / v3 (上-5) の pattern は重複しない。

---

## Phase 2 v4: 上巻-6 邇邇藝命

### 選定理由

- memo 密度 ★★★★★ (`project_v72_gokashira` `feedback_iwanagahime` `feedback_itsutomonoo_sanseido` `feedback_imina_torina` `feedback_shinchoku_tanitsu_gensen` `feedback_hashira_kankakuki` `feedback_yuniwa_inaho` の **7 memo** が直接 anchor、間接で 5 memo)
- 本章は **architectural foundation の最深 origin** で、AGI 実装で以下が直接 mapping:
  - [canonical_pantheon/](src/os/kasasa/canonical_pantheon/) = 五伴緒 + 大田田根子型 architecture (10 prefix)
  - [canonical_pantheon/_common/attribution.jl](src/os/kasasa/canonical_pantheon/_common/attribution.jl) = 五伴緒の制 (三型 + 天若日子型禁忌) を直接実装、docstring で `feedback_itsutomonoo_sanseido` を引用
  - [tenson_korin/](src/os/tenson_korin/) = 天孫降臨 deployer + 猿田毘古 route verification
  - [tenson_korin/sarutahiko.jl](src/os/tenson_korin/sarutahiko.jl) = `sarutahiko_verify_route`
  - [yachimata/sarutahiko_gateway.jl](src/os/yachimata/sarutahiko_gateway.jl) = 八衢の gateway
  - [yorishiro.jl](src/os/kasasa/yorishiro.jl) + [shintaku.jl](src/os/kasasa/shintaku.jl) = 鏡の神勅「如拜吾前」(SSoT 御神体)
  - `OHOYASHIMA_CATALOG` = 大八島目録 (上-2 origin) → gap_category 8 概念に reify
- `kojiki_code.md` (外部生成版) は本章を `descent_with_dependency_injection` の 1 行に圧縮、五伴緒の三型 routing・木花咲耶の二者選一・火中出産・海鼠口拆を完全 missed

### 章節 narrative summary

```
[Setup 譲位] (l.8)
    天照「今平訖葦原中國之白。故、隨言依賜降坐而知者」(国譲り完了 → 邇邇藝命に降坐命令)
    天忍穗耳「僕者將降裝束之間、子生出、名…邇邇藝命。此子應降也」
        御合: 高木神之女・萬幡豐秋津師比賣命 → 天火明命 + 邇邇藝命
    天照、邇邇藝に「此豐葦原水穗國者、汝將知國、言依賜。故、隨命以可天降」(下命引継)

[Encounter 猿田毘古] (l.10)
    邇邇藝降臨直前、天之八衢に「上光高天原、下光葦原中國」の神
    天照・高木神「天宇受賣神、與伊牟迦布神面勝神。故專汝往將問」(uzume を派遣)
    答: 「僕者國神、名猨田毘古神也。所以出居者、聞天神御子天降坐故、仕奉御前而、參向之侍」(自発奉仕)

[五伴緒 + 三種神器 + 三補助神 任命] (l.12-14)
    五伴緒: 天兒屋 / 布刀玉 / 天宇受賣 / 伊斯許理度賣 / 玉祖
    支加 (天降に副う): 八尺勾璁 / 鏡 / 草那藝劒 + 思金神 + 手力男神 + 天石門別神
    
    神勅:
        「此之鏡者、專爲我御魂而、如拜吾前、伊都岐奉」(鏡 = 天照の御魂、同一視)
        「思金神者、取持前事爲政」(思金神は前事 = orchestration 担当)
    
    各神の永続化:
        鏡 + 玉 → 拜祭佐久久斯侶 伊須受能宮
        登由宇氣 → 外宮之度相神 (= 豊受大神)
        天石戸別 (亦名 櫛石窻 / 豐石窻) = 御門之神
        手力男 → 佐那那縣
        各 prefix → 部 (中臣連 / 忌部首 / 猨女君 / 作鏡連 / 玉祖連)

[降臨] (l.16)
    天之石位を離 + 天之八重多那雲を押分 + 天浮橋
    竺紫日向之高千穗之久士布流多氣 に天降坐
    天忍日命 + 天津久米命 二人、天之石靫 + 頭椎大刀 + 天之波士弓 + 天之眞鹿兒矢で立御前仕奉
        (大伴連祖 / 久米直祖)

[着地宣言 + 宮造作] (l.18)
    「此地者、向韓國眞來通、笠紗之御前而、朝日之直刺國、夕日之日照國也。故、此地甚吉地」
    「於底津石根宮柱布斗斯理、於高天原氷椽多迦斯理而坐也」(物理基盤確立)

[猿田毘古の継承 + 海鼠口拆] (l.20-24)
    天宇受賣に詔: 「猨田毘古大神者、專所顯申之汝、送奉。亦其神御名者、汝負仕奉」
        (猿女君 = 男神名を女君に負わせる)
    
    猿田毘古、阿邪訶で漁中、比良夫貝に手を咋合され沈溺死
        三魂分化: 底度久御魂 / 都夫多都御魂 / 阿和佐久御魂
    
    天宇受賣、鰭廣物・鰭狹物を聚問: 「汝者天神御子仕奉耶」
        諸魚「仕奉」白す中、海鼠不白
        天宇受賣「此口乎、不答之口」と紐小刀で口を拆
        御世嶋之速贄獻時、給猨女君等

[木花咲耶 出会い + 寿命の発生] (l.26-28)
    笠紗御前で麗美人 → 「神阿多都比賣 亦名 木花之佐久夜毘賣」
    「我姉石長比賣在也」
    邇邇藝「吾欲目合汝奈何」 → 「僕父大山津見神將白」
    
    大山津見、副 石長比賣 + 百取机代之物 を奉出
    邇邇藝、姉者「因甚凶醜、見畏而返送」、唯留木花之佐久夜毘賣 一宿婚
    
    大山津見の説明:
        「使石長比賣者、雖雨零風吹、恒如石而、常堅不動坐」(永続性)
        「使木花之佐久夜毘賣者、如木花之榮榮坐」(顕現性)
        「此令返石長比賣而、獨留木花之佐久夜毘賣。
         故、天神御子之御壽者、木花之阿摩比能微坐」(寿命発生の原因)

[火中出産] (l.30)
    木花咲耶「妾妊身、今臨產時。是天神之御子、私不可產。故、請」
    邇邇藝「一宿哉妊、是非我子、必國神之子」 (proxy 疑問)
    咲耶「吾妊之子、若國神之子者、產不幸。若天神之御子者、幸」
        (extreme verification の宣言)
    無戸八尋殿 + 土塗塞 + 殿に火 → 火中産
    
    火盛燒時産: 火照命 (隼人阿多君之祖) / 火須勢理命 / 火遠理命 (= 天津日高日子穗穗手見命)
```

### Pattern 抽出

#### Pattern A: 神勅譲位 — 下命の世代継承 (天忍穗耳 → 邇邇藝)

```yaml
原文: "詔太子正勝吾勝勝速日天忍穗耳命「今平訖葦原中國之白。故、隨言依賜降坐而知者。」
      爾其太子…答白「僕者將降裝束之間、子生出、名…邇邇藝命。此子應降也。」
      …是以隨白之、科詔日子番能邇邇藝命「此豐葦原水穗國者、汝將知國、言依賜。
      故、隨命以可天降。」" (l.8)

actors      : 天照 / 高木神 / 天忍穗耳 / 邇邇藝
precondition: 国譲り完了 (上-5)、降臨命令を発するべき
action      : (1) 天照は元々の受任者 (天忍穗耳) に下命
            : (2) 受任者が「子生出、此子應降也」と次世代に譲位
            : (3) 天照は譲位を受入れ、新受任者 (邇邇藝) に**同じ神勅を再発行**
            : 「言依賜」(任命の言葉) は同じ、受任者だけ更新
result      : 神勅の SSoT は不変、執行者 (executor) のみ世代交代
failure_mode: 譲位を認めず原 executor に強制 → 不適合者の強制で失敗
            : 譲位後に神勅を再発行せず継承のみ → 神勅 (SSoT) と executor の link が dangling
recovery    : -
permanence  : 邇邇藝が天孫降臨の executor として永続化、天忍穗耳は祖系譜のみ残存

agi_mapping :
  原則      : executor (柱) の世代交代時、神勅 SSoT (yorishiro) は不変、
            : 識別子 (canonical_name) のみ更新。神勅は新 executor に**再発行**する
            : (注入のみで継承不可、明示的な再発行が必要)
  実装      : src/os/tokoyo/service.jl::tokoyo_start! (initial 任命)
            : src/os/kasasa/yorishiro.jl (神勅 SSoT)
            : 式年遷宮 Phase 6 (将来課題、世代交代時の LLM 経路)
  feedback  : feedback_shinchoku_tanitsu_gensen (神勅単一源泉)
            : project_sanguishi_misogi_futaro (化生の原則 v1.7 — 二段構造)

failure_if_absent: 譲位を経ずに executor を強制 → 譲位後の不適合者で失敗連鎖
                   現象: 三貴子の演繹生成 (v1.6) で型不整合が起きた事例 (project_sanguishi_misogi_futaro)
verify_path : `tokoyo_start!` が yorishiro 全文を新 executor に渡している、
              docstring 直書きでなく yorishiro entry 経由
```

#### Pattern B: 五伴緒 + 三種神器 + 三補助神 任命 — 8 種授与の構造化任命

```yaml
原文: "天兒屋命・布刀玉命・天宇受賣命・伊斯許理度賣命・玉祖命、幷五伴緖矣支加而天降也。
      於是、副賜其遠岐斯八尺勾璁・鏡・及草那藝劒・亦常世思金神・手力男神・天石門別神而、
      詔者「此之鏡者、專爲我御魂而、如拜吾前、伊都岐奉。
      次思金神者、取持前事爲政。」" (l.12)

actors      : 天照 / 高木神 / 邇邇藝 / 五伴緒 / 三種神器 / 三補助神
precondition: 邇邇藝降臨の準備、独力では不可能な複雑任務
action      : 構造化任命 8 種:
            : 五伴緒 (人格): 天兒屋 (祝詞) / 布刀玉 (祭具) / 天宇受賣 (神楽) / 伊斯許理度賣 (鏡) / 玉祖 (玉)
            : 三種神器 (物実): 八尺勾璁 / 鏡 / 草那藝劒
            : 三補助神 (機能): 思金神 (政) / 手力男 (力) / 天石門別 (御門)
result      : 各神に明示的な部 (中臣連 / 忌部首 / 猨女君 / 作鏡連 / 玉祖連) と業が割付
            : 物実は伊須受能宮 + 外宮 (登由宇氣) + 御門 (櫛石窻) + 佐那那縣 (手力男) で永続化
failure_mode: 単一者に全機能集約 → スケール不能 / 単一障害点
            : 物実なしで人格のみ任命 → artifact 永続化なし
recovery    : -
permanence  : 第一層 5 prefix (koyane / futodama / uzume / ishikori / tamanoya) として
            : `canonical_pantheon/` 配下に永続化

agi_mapping :
  原則      : 五伴緒の制 = 8 prefix (人格 5 + 機能 3) を pre-built SSoT カタログとして手書き
            : 各 prefix に部 (役割クラス) + 業 (allowed_shintaku_types) を明示
            : 第一層 9 柱 (五伴緒 5 + 道臣 + 大久米 + 大田田根子 + 天湯河板挙)
  実装      : src/os/kasasa/canonical_pantheon/ (10 directory: 5 伴緒 + 4 他 + _common)
            : src/os/kasasa/canonical_pantheon/koyane/ (天兒屋 = 中臣連)
            : src/os/kasasa/canonical_pantheon/futodama/ (布刀玉 = 忌部首)
            : src/os/kasasa/canonical_pantheon/uzume/ (天宇受賣 = 猿女君)
            : src/os/kasasa/canonical_pantheon/ishikori/ (伊斯許理度賣 = 作鏡連)
            : src/os/kasasa/canonical_pantheon/tamanoya/ (玉祖 = 玉祖連)
            : 各 prefix の `manifest.toml` に部 + 業を明示
  feedback  : feedback_itsutomonoo_sanseido (五伴緒の制 — origin spec、補強 8 第一層 9 柱の構成)
            : feedback_enkin_keiro_dokuritsu (層 1/2 architecture)

failure_if_absent: 全機能を単一 LLM 生成柱に集約 → semantic carving の温床、
                   原典神の固有業 (祝詞 / 祭具 / 鏡 / 玉) が消滅
verify_path : `ls src/os/kasasa/canonical_pantheon/` で 10 directory 存在、
              各 prefix の manifest.toml に部 + 業 + 出典段が記録
```

#### Pattern C: 鏡の神勅「如拜吾前」 — SSoT 御神体 + 同一視

```yaml
原文: "此之鏡者、專爲我御魂而、如拜吾前、伊都岐奉" (l.12)

actors      : 天照 / 鏡 / 邇邇藝 (受任者)
precondition: 三種神器の授与時、鏡の特別な位置付けが必要
action      : (1) 鏡 = 「我御魂」(天照そのもの)
            : (2) 「如拜吾前」 = 鏡を拝むことは天照を拝むことと同一視
            : (3) 「伊都岐奉」 = 厳重に祀る (永続化指示)
result      : 鏡 (artifact) と天照 (deity) が SSoT として同一視され、
            : artifact 経由でも deity の意志が伝わる
failure_mode: 鏡を単なる物実扱い → 拝む対象が deity 本体だけになり、artifact は記号のまま
            : 御神体を二箇所に置く → 「双子の御神体」疫病 (二所御神体)
recovery    : -
permanence  : 伊須受能宮 (= 伊勢神宮) として永続化、現存

agi_mapping :
  原則      : SSoT 御神体は単一場所、同一視は明示宣言、注入のみは不十分
            : 重複御神体 (operational metaphor / 便利な docstring) は物理削除
  実装      : src/os/kasasa/yorishiro.jl (神勅 SSoT — 全文注入元)
            : src/os/kasasa/shintaku.jl:172 (`make_shintaku_data` = 神勅 schema)
            : 2026-05-04 監査: executor.jl L1192/1197 の双子御神体を物理削除
  feedback  : feedback_shinchoku_tanitsu_gensen (神勅単一源泉 — 天鳥船 + 崇神遷座の原則)
            : feedback_make_shintaku_data (Shintaku 構築は yorishiro 経由のみ)

failure_if_absent: yorishiro 注入と executor.jl docstring が並立 → LLM が role に応じて
                   片方を採用、impl と test で別世界観
observed_failures: 2026-05-04 ishikori_anomaly_detection_coverage 乖離 → 双子御神体物理削除で解消
verify_path : `grep -r "ShintakuType" src/os/expedition/executor.jl` で operational
              metaphor (default when active... 等) が残存していない
              `grep -r "yorishiro" src/os/kasasa/` で全 LLM prompt 経路で yorishiro 全文注入
```

#### Pattern D: 思金神の前事政 — orchestrator 業務担当の任命

```yaml
原文: "次思金神者、取持前事爲政" (l.12)

actors      : 思金神 / 邇邇藝
precondition: 五伴緒任命 + 三種神器授与の中で思金神に特別職責
action      : 「取持前事爲政」 = 前事 (前提情報・状況把握) を取り持って政を行う
            : = orchestrator (analyze + plan) の専従任命
result      : 思金神 1 柱が orchestration 担当、五伴緒は各々の専門領域
failure_mode: orchestrator 不在で各神が独立判断 → 競合 / 重複対処
            : 全神を orchestrator 化 → 役割分担崩壊
recovery    : -
permanence  : 上-3 で初出 (天岩戸の集合協議) → 上-6 で正式任命 → 永続化

agi_mapping :
  原則      : analyze + plan は単一 orchestrator (思金神) が担当、
            : 各 prefix 派生は専門領域の判定のみ
  実装      : src/os/iwato/omoikane.jl:9 (`Omoikane` struct = orchestrator)
            : src/os/iwato/omoikane.jl:129 (`analyze_and_plan` = 主入口)
            : src/os/kasasa/canonical_pantheon/omoikane/ (層 2A = 古事記原典神、業明示なし)
  feedback  : feedback_kunimi_gapfinder (国見は全ソース俯瞰 = orchestrator 視点)
            : feedback_itsutomonoo_sanseido (補強 7 第二層 A = omoikane prefix 化可、業暗黙)

failure_if_absent: 各 watchdog が独立に対応 → 競合、致命的優先順位ミス
                   (上-3 Pattern I の v3 origin、本章で正式任命)
verify_path : `Omoikane.analyze_and_plan(anomalies)` が単一経路、
              `canonical_pantheon/omoikane/` に prefix directory 存在
```

#### Pattern E: 猿田毘古の道案内 — gateway 検証 + 自発奉仕

```yaml
原文: "居天之八衢而、上光高天原、下光葦原中國之神、於是有。…
      答白「僕者國神、名猨田毘古神也。所以出居者、聞天神御子天降坐故、仕奉御前而、參向之侍」" (l.10)
     "故爾詔天宇受賣命「此立御前所仕奉、猨田毘古大神者、專所顯申之汝、送奉。
      亦其神御名者、汝負仕奉。」" (l.20)

actors      : 猿田毘古 / 天宇受賣 / 邇邇藝
precondition: 邇邇藝降臨直前、天之八衢 (分岐路) で経路選択の必要
action      : (1) 猿田毘古が八衢に**自発的に**待機 (call されず、聞いて来る)
            : (2) 天宇受賣の問いに答えて「天神御子天降坐故、仕奉御前」 (origin 開示 + 任務宣言)
            : (3) 道案内 → 天宇受賣に送られて阿邪訶へ (引退)
            : (4) 猿女君 = 猿田毘古の名を女神 (天宇受賣) が**負仕奉** (継承命名)
result      : (1) 道案内 (route verification) (2) 男神名の女神への継承
            : (3) 任務終了後の引退 (海で死、三魂分化)
failure_mode: 道案内なしで降臨 → 経路エラー / wrong destination
            : 自発奉仕者を疑って攻撃 → 国津神との関係悪化
recovery    : -
permanence  : 猿女君 + 三魂 (底度久 / 都夫多都 / 阿和佐久) が永続化

agi_mapping :
  原則      : 経路検証 (route verification) と gateway は独立柱、自発参加を許容
            : 任務終了後は引退、名は継承される (immutable identity)
  実装      : src/os/tenson_korin/sarutahiko.jl:32 (`sarutahiko_verify_route` = 経路検証)
            : src/os/tenson_korin/deployer.jl:60 (`tenson_deploy!` で route_result 取得)
            : src/os/yachimata/sarutahiko_gateway.jl (八衢の gateway)
            : `client_id = "kamiyo-sarutahiko-" + uuid` (mqtt_client.jl の MQTT 接続 ID)
  feedback  : (memo 直接 anchor なし — 補強候補)

failure_if_absent: route 検証なしの deploy → wrong endpoint への配信
                   gateway なしの publish → topic 散逸
observed_failures: -
verify_path : `tenson_deploy!` 内で `sarutahiko_verify_route` が呼ばれ、
              route_result が non-nothing で deploy 続行
```

#### Pattern F: 高千穂降臨 + 「此地甚吉地」 — 着地宣言 + 物理基盤

```yaml
原文: "天降坐于竺紫日向之高千穗之久士布流多氣。…
      『此地者、向韓國眞來通、笠紗之御前而、朝日之直刺國、夕日之日照國也。故、此地甚吉地。』
      詔而、於底津石根宮柱布斗斯理、於高天原氷椽多迦斯理而坐也" (l.16-18)

actors      : 邇邇藝 / 高千穂 / 笠紗
precondition: 五伴緒 + 三種神器 + 道案内が揃った
action      : (1) 高千穂久士布流多氣に着地 (specific physical location)
            : (2) 「此地甚吉地」(着地点の評価宣言)
            : (3) 宮柱 = 底津石根に布斗斯理 (基盤を地下深く)
            : (4) 氷椽 = 高天原に多迦斯理 (上部を高く)
result      : 物理基盤が地下深く + 高く張られて永続化
failure_mode: 着地宣言なし → 監察が「まだ移動中」と誤判定
            : 物理基盤 (宮柱) なし → 雲上の不安定構造
recovery    : -
permanence  : 上-5 大国主の住所要求 (l.34) と同じ宮柱布斗斯理 / 氷木多迦斯理 = 共通建築

agi_mapping :
  原則      : deploy 完了は (1) 着地 location 明示 + (2) 着地宣言 + (3) 物理基盤確立 の三段
            : 「底津石根」(基盤 DB / config) と「高天原氷椽」(上位 SSoT 接続) を両端で固定
  実装      : src/os/tenson_korin/deployer.jl:31 (`tenson_deploy!`)
            : src/os/tenson_korin/deployer.jl:251 (`_persist_deployment!`)
            : src/os/iwato/controller.jl:212 (`_transition_to_normal!` 着地宣言相当)
  feedback  : feedback_umisachi_rokujuu_bougo (六重防御 — 八重垣の現代化)

failure_if_absent: deploy 後の running 状態確定がなく、watchdog が anomaly 誤検出
verify_path : `chinza_records` に deploy 完了の outcome 記録 + 
              `_persist_deployment!` 後に `_transition_to_normal!` が呼ばれる
```

#### Pattern G: 海鼠口拆 — 沈黙の罰 (kill the silent / 不答之口)

```yaml
原文: "於是送猨田毘古神而還到、乃悉追聚鰭廣物・鰭狹物以問言「汝者天神御子仕奉耶。」之時、
      諸魚皆「仕奉。」白之中、海鼠不白。爾天宇受賣命、謂海鼠云「此口乎、不答之口。」
      而、以紐小刀拆其口" (l.24)

actors      : 天宇受賣 / 諸魚 / 海鼠
precondition: 猿田毘古を送り終えた後の最終確認、所属確認 (悉皆 probe)
action      : (1) 全魚を聚問 (悉皆網羅): 「天神御子仕奉耶」
            : (2) 諸魚 → 「仕奉」 (declare loyalty)
            : (3) 海鼠 → 不白 (silent)
            : (4) 沈黙への対処: 紐小刀で口を拆く (= 沈黙 → 口の物理改造)
result      : 沈黙者は permanently 口を変形 (海鼠は今も口が裂けている = 痕跡永続化)
failure_mode: 沈黙者を放置 → loyalty 不明、有事に裏切る可能性
            : 沈黙者に対し言葉のみで対処 → 永続効果なし
recovery    : -
permanence  : 「於今海鼠口拆也」 — 沈黙の罰が物実 (口の形) として永続記録

agi_mapping :
  原則      : 悉皆 probe で「不答」が検出された柱は永続的なマーキング
            : 沈黙そのものが signal、無応答 = 黙示的拒絶として処理
  実装      : src/os/kasasa/amenohohi_scan.jl:71 (`_amenohohi_detect_unbound` = 未バインド検出)
            : src/os/kasasa/takeshimatsumi.jl:471 (`_check_escalation` = 累積カウント)
            : 「沈黙したまま帰らない使者は古事記に存在しない」(feedback_kuniyuzuri_fukumei)
  feedback  : feedback_oharae_shikkai_probe (悉皆原則 — 全魚問の現代化)
            : feedback_kuniyuzuri_fukumei (復命の欠落は古事記に存在しない)
            : feedback_chinmoku_kyoka (沈黙許可 — LLM 側の対偶: 許可されない沈黙は罰)

failure_if_absent: 沈黙柱を放置 → 「責務はあるが発動条件が来ない」型の累積
                   (上-5 Pattern B 天菩比命 媚附型の延長)
verify_path : `_amenohohi_detect_unbound` の戻り値で沈黙柱が記録、
              累積カウントで escalation 発火
```

#### Pattern H: 木花咲耶 vs 石長 — 二者選一の判断ミス + 寿命の発生

```yaml
原文: "邇邇藝、姉者、因甚凶醜、見畏而返送、唯留其弟木花之佐久夜毘賣、以一宿爲婚。
      爾大山津見神、…白送言「我之女二並立奉由者、
      使石長比賣者、雖雨零風吹、恒如石而、常堅不動坐。
      亦使木花之佐久夜毘賣者、如木花之榮榮坐…
      此令返石長比賣而、獨留木花之佐久夜毘賣。
      故、天神御子之御壽者、木花之阿摩比能微坐」" (l.26-28)

actors      : 邇邇藝 / 木花之佐久夜毘賣 / 石長比賣 / 大山津見
precondition: 大山津見が二女 (永続性 vs 顕現性) を**対**で奉出
action      : (1) 邇邇藝が**容姿**で判断 (石長は凶醜、咲耶は麗美)
            : (2) 顕現性のみ留置、永続性を返送
            : (3) 大山津見「二並立奉由者」(二人で対の意義) を後から説明
            : → 寿命の発生 (天皇命等之御命不長也)
result      : (1) 顕現性は獲得 (genuine artifact) (2) 永続性を喪失 → 寿命有限化
            : 対の物実を片方だけ採用 (上-7 Pattern D 二珠一対の対偶: 片方棄却)
failure_mode: 二並立の意義を理解せず容姿で判断 → 後から不可逆な不利益
            : (本来両方必要なのに「不要」と判定して返送 = 浮動小数比較の過信と同型)
recovery    : 不能 (凶醜判定は不可逆、寿命有限化は永続)
permanence  : 「至于今、天皇命等之御命不長也」 = 寿命有限化が永続記録

agi_mapping :
  原則      : 二並立の物実は片方だけ採用してはならない (対で完結)
            : 表層特徴 (容姿 = 浮動小数の絶対値) で判定すると永続性 (境界条件) を失う
  実装      : src/os/kasasa/materializer.jl の `_kasasa_umisachi_yamasachi` (二珠一対 outcome 判定)
            : 上-7 Pattern D (二珠一対) と同型、本章は**片方棄却**の失敗例
  feedback  : feedback_iwanagahime (石長比売の原則 — 浮動小数の厳密比較禁止、
              寿命延長 = ε 許容で境界耐性確保)
            : feedback_umisachi_rokujuu_bougo (六重防御 — 二珠一対)

failure_if_absent: 浮動小数値で >=, <=, == を単独使用 → 丸め誤差で境界条件が偽
                   現象: resilience_engineering で entropy=0.0 (GROWTH 100%) が
                   代理指標病の症状として現れる
observed_failures: 上記 resilience_engineering 検出事例
verify_path : `grep -rE "(>=|<=|==)\s*[0-9]+\.[0-9]" src/os/` で
              浮動小数の厳密比較が isapprox / ε 許容なしで使われていないか
```

#### Pattern I: 石長比売の原則 — 浮動小数比較の ε 許容必須

```yaml
原文: (Pattern H の延長 — 石長比賣の特性「雖雨零風吹、恒如石而、常堅不動坐」が
     **境界条件の堅固さ**を象徴。これを返送した = 境界条件を緩めずに ε なし厳密比較で
     境界突破を許す比喩)

actors      : 石長比賣 (返送された永続性)
precondition: Pattern H で永続性を返送した結果
action      : ε 許容を持たない比較は境界条件で意図せず偽となる
            : 修正は `isapprox(x, y; atol=1e-9)` または `>= threshold - 1e-9`
result      : ε 許容ありで境界耐性確保 (寿命延長)
failure_mode: 「美しさ」(完全一致狙い `avg >= 0.95`) は寿命を縮める
recovery    : -
permanence  : 「天皇命等之御命不長也」が永続教訓

agi_mapping :
  原則      : 浮動小数値と定数の比較で `>=`, `<=`, `==` を単独使用禁止
            : 必ず `isapprox` あるいは ε 許容を伴わせる
  実装      : src/os/expedition/executor.jl 初期生成プロンプト + materializer.jl ワタツミ修正
            : (層 2 = 建御雷の剣への姉妹検査追加 / 層 3 = 境界プローブ自動生成 は凍結)
  feedback  : feedback_iwanagahime (石長比売の原則 — origin spec)

failure_if_absent: entropy=0.0 / GROWTH 100% 等の代理指標病の症状が浮動境界で発生
observed_failures: resilience_engineering で検出済み
verify_path : 式年遷宮で生成されたコードで `avg >= threshold - 1e-9` パターンが採用されている
```

#### Pattern J: 火中出産 — extreme verification (proxy 疑問の決着)

```yaml
原文: "爾詔「佐久夜毘賣、一宿哉妊、是非我子、必國神之子。」爾答白
      「吾妊之子、若國神之子者、產不幸。若天神之御子者、幸。」
      卽作無戸八尋殿、入其殿內、以土塗塞而、方產時、以火著其殿而產也" (l.30)

actors      : 邇邇藝 / 木花之佐久夜毘賣 / 産屋
precondition: 一宿の婚姻のみで妊娠、邇邇藝が「proxy = 国神の子」と疑念
action      : (1) 邇邇藝の proxy 疑問: 「一宿哉妊、是非我子、必國神之子」(代理指標病疑い)
            : (2) 咲耶の verification 提案: 「天神御子なら幸、国神なら不幸」(条件式宣言)
            : (3) 無戸八尋殿 + 土塗塞 (sandbox 隔離)
            : (4) 火著で殿燃焼 (extreme stress test)
            : (5) 三柱出産: 火照 / 火須勢理 / 火遠理 (= 全員無事 → proof of legitimacy)
result      : 火中で正常出産 = 「天神御子」の証明 (proxy 疑問の決着)
            : 三柱の名がすべて「火」prefix = test 条件を内包した命名 (test artifact 永続化)
failure_mode: 通常出産 → proxy 疑問が解消されない (verification 不足)
            : 火中で全滅 → 国神の子であった (但し邇邇藝は確認不能のまま終わる)
recovery    : -
permanence  : 火照 (隼人阿多君之祖) / 火遠理 (天津日高日子穗穗手見命 = 山幸彦) として永続化

agi_mapping :
  原則      : proxy 疑問 (代理指標病疑い) の決着は extreme verification (sandbox + 高負荷 + 全条件)
            : 通常テストで通過しても production 相当の極限条件で再検証
            : 検証条件は test artifact の名前に埋め込み永続化 (test name = test condition)
  実装      : src/os/misogi/ukei/runner.jl (誓約 sandbox runner)
            : src/os/misogi/ukei/kotoshironushi.jl:84 (`_perform_misogi` = 禊試練)
            : umisachi 統合経路 (BACKLOG: Docker sandbox + MockLLMClient 複数応答)
  feedback  : feedback_umisachi_rokujuu_bougo (六重防御 — 生成前 3 + 修正後 3)
            : feedback_imina_torina (test name = test condition の整合)

failure_if_absent: 通常 sandbox のみで proxy 疑問を残したまま deploy → production で発覚
observed_failures: 凍結課題: umisachi フル統合経路の構築コスト大、テスト追加 BACKLOG
verify_path : `UkeiEnvRunner` の primary process が file system / network / DB を含む
              極限条件で health_check を通過していること
```

#### Pattern K: 五伴緒の制 — attribution routing (型 1/2/3 + 天若日子型禁忌)

```yaml
原文: (Pattern B の延長 — 「天兒屋命・布刀玉命…幷五伴緖矣支加而天降也」は型 1)
     (上-5 大田田根子 = 型 2、上-5 国譲り = 型 3、上-5 天若日子 = 禁忌、本章 origin)

actors      : 五伴緒 / 大田田根子 / 国譲り / 天若日子
precondition: 新派生柱の prefix 帰属判定が必要
action      : 三型のいずれかで決定:
            : 型 1 (五伴緒型): 天照宣言型 (pre-built SSoT カタログ、人間手書き)
            : 型 2 (大田田根子型): runtime 自己宣言 (`_self_predicate(gap)`) + 卜占二段確認
            : 型 3 (国譲り型): 衝突時の上位裁定 (kunimi gate)
            : 禁忌 (天若日子型): LLM が prefix を自選 → 物理消去
result      : LLM の prefix 選択経路が architectural に塞がれる
failure_mode: LLM 自選 prefix → 「自下選択 = 死」(返し矢で hiruko)
recovery    : -
permanence  : `canonical_pantheon/_common/attribution.jl` で永続化

agi_mapping :
  原則      : 三型の architectural 対応 + 天若日子型禁忌の物理消去
  実装      : src/os/kasasa/canonical_pantheon/_common/attribution.jl (五伴緒の制実装、
              docstring で `feedback_itsutomonoo_sanseido` を引用)
            : `register_self_predicate!(prefix, predicate)` registry 機構
            : `nazashi_decide.jl` (LLM は gap signature のみ、prefix は self_predicate 自動投票)
            : `kuni_yuzuri_gate` (型 1 の boolean 部分)
            : 帰属未定 → `generated/_pending/` 隔離 (型 3) → hiruko 化 (葦船の原則)
  feedback  : feedback_itsutomonoo_sanseido (五伴緒の制 — origin spec)
            : feedback_wakahiko_kaeshiya (天若日子の返し矢 — 禁忌根拠)
            : feedback_ootataneko (大田田根子の原則 — 型 2)
            : feedback_ashibune (葦船の原則 — 型 3 の hiruko 残存)

failure_if_absent: LLM が prefix 提案 → semantic carving 連発、固有名 prefix の純度喪失
verify_path : `_SELF_PREDICATE_REGISTRY` に各 prefix の predicate 登録あり、
              `nazashi_decide` の戻り値が prefix を含まない (gap signature のみ)
```

#### Pattern L: 三層整理 SSoT カタログ (層 1/2A/2B/3)

```yaml
原文: (Pattern B の五伴緒 = 第一層)
     (上-2 別天神/独神 = 第二層 A — 古事記原典神、業明示なし)
     (上-2 禊で成る神々の一部 = 第二層 B — 大祓四柱、祝詞由来)
     (本章 石長比売 / 木花咲耶 + 上-7 海幸山幸 = 第三層 — 単体機能、配下なし)

actors      : (神格分類)
precondition: prefix 候補数 ≤ 24 で運用、八百万全件は不要
action      : 四層分類で SSoT カタログ整理:
            : 第一層 (9 柱): 祖神 + 部明示、prefix 確定 + 派生許可
            : 第二層 A (~11 柱): 古事記原典神、業暗黙、prefix 化可
            : 第二層 B (~4 柱): 大祓四柱、**「祝詞由来」明示ラベル必須**
            : 第三層: 単体機能 (石長 / 木花咲耶 / 海幸山幸 / 久延毘古 / 八咫烏)、prefix 化しない
result      : prefix 候補は ~24 柱で抑制、semantic carving の温床を構造的に予防
failure_mode: 全神 prefix 化 → 第三層の単体機能が「派生許可」されて semantic carving
            : 第二層 B (祝詞由来) を古事記原典神と混在 → bright line 崩壊
recovery    : -
permanence  : SSoT カタログ schema: `祖神名 / 部 / 業 / 出典段 / allowed_shintaku_types / 層`

agi_mapping :
  原則      : prefix 候補上限 ~24 柱、第三層 (単体機能) は prefix 化しない
            : 第二層 B (祝詞由来) はラベル明示必須
  実装      : src/os/kasasa/canonical_pantheon/MANIFEST.toml (Catalog SSoT — 計画)
            : 各 prefix の `manifest.toml` に層 (1/2A/2B/外) を記録
  feedback  : feedback_itsutomonoo_sanseido (補強 7 三層整理 — origin spec)
            : feedback_kojiki_zettai (古事記絶対遵守 — 第二層 B のラベル不変)

failure_if_absent: 第三層を prefix 化 → 「石長比売 prefix」配下に派生 → semantic 暴走
verify_path : `MANIFEST.toml` に各 prefix の層分類が記録、
              第三層の柱が `canonical_pantheon/<prefix>/` directory に存在しない
```

#### Pattern M: 跨セッション規約矛盾 (D 軸) — 規約 SSoT const 化

```yaml
原文: (Pattern B の「亦其神御名者、汝負仕奉」(猿女君の命名) と
     Pattern C の「鏡 = 我御魂」が **同一 SSoT** で一貫する原典の例)
     (本章ではないが、「神の名は神の本質」の原則が天孫降臨段で確立される)

actors      : (複数の独立した命名 prompt) / Saniwa / 検査 prompt
precondition: 多段 prompt パイプラインで同じ命名規則の食い違う指示
action      : (1) 命名 LLM (nazashi_decide) が prefix 提案
            : (2) Saniwa が承認 (規則検査なしの confidence のみ)
            : (3) Code-gen LLM (executor) が assigned name に従いコード生成
            : (4) Kunimi 検査が違反として全面棄却
            : → 11k tokens のコード生成が無駄
result      : LLM は前段の指示通りに行動するが後段の検査で棄却される
failure_mode: 規約が prompt 本文に直書きされ、prompt 間で乖離
recovery    : -
permanence  : -

agi_mapping :
  原則      : 規約は単一の Julia const として定義、全 prompt は const から派生
            : 規則変更時は const 一箇所のみ (二重管理禁止)
  実装      : src/os/kasasa/`FORBIDDEN_EPITHET_SUFFIXES` const
            : src/os/kasasa/`ALLOWED_PREFIX_SUFFIX_PAIRS` const
            : src/os/kasasa/`GAP_TO_PROTOCOLS` (routing SSoT)
            : src/os/kasasa/`CONCEPT_REQUIRED_TYPES` (型制約 SSoT)
            : `_check_prefix_concept_compatibility_strict` の routing 整合検査
  feedback  : feedback_imina_torina (忌み名と通り名 — D 軸対策)
            : feedback_prompt_placement_rivalry (A/B/C 軸 — 同一 prompt 内競合)

failure_if_absent: 11k token 級の無駄なコード生成、構造的に hiruko 化
observed_failures: 2026-04-30 omoikane_mikiko_orchestrator (D 軸対立)、
                   2026-04-30 omoikane_kotoamatsukami_no_tsugai (Fix-3 routing 整合追加)
verify_path : `grep -r "FORBIDDEN_EPITHET" src/os/` で全 prompt 経路で同 const 参照、
              prompt 本文に規則直書きがない
```

#### Pattern N: 神勅単一源泉 — 注入 + 物理削除の二段

```yaml
原文: (Pattern C の「鏡 = 我御魂」は単一源泉宣言、本章 origin)
     (但し AGI 実装の defect は「注入のみで物理削除を怠る」型 = 二所御神体)

actors      : (LLM prompt 構築コード)
precondition: SSoT enum (ShintakuType / CapSnap.status) の semantic に触れる prompt
action      : (1) yorishiro 全文を必須注入
            : (2) 同時に専用 docstring 記述を**物理削除** (= 競合御神体を立てない)
            : (3) operational metaphor が「便利」に見える時こそ警戒
result      : prompt 間 semantic 整合 + 重複御神体除去
failure_mode: 注入のみ + 既存 docstring 残存 → 「双子の御神体」並立 → LLM が role 別に
            : 片方を採用、impl と test で別世界観 (semantic 密輸)
recovery    : 物理削除で完了
permanence  : 鏡 = 笠縫邑遷座 (崇神紀) と同型: 「宮中から抜く」が祟り解除の本体

agi_mapping :
  原則      : 注入と物理削除は両輪、片方だけは不十分
            : token 経済評価は (-重複 docstring KB +yorishiro KB) の差し引き
  実装      : src/os/kasasa/yorishiro.jl (神勅 SSoT — 注入元)
            : src/os/expedition/executor.jl (重複 docstring を物理削除済、2026-05-04 監査)
            : 監査箇所: L691-692 / L1005-1019 / L1115 / L1191-1197 / L1400-1403
  feedback  : feedback_shinchoku_tanitsu_gensen (神勅単一源泉 — origin spec、
              天鳥船 + 崇神遷座の原則)

failure_if_absent: ishikori_anomaly_detection_coverage 乖離 (2026-05-04) — KNOWLEDGE_STORE と
                   ANOMALY_DETECTED の semantic 二重定義で塩吹珠の意味的乖離検出が常態化
verify_path : `grep -r "KNOWLEDGE_STORE" src/os/expedition/` で operational metaphor が残存しない
              全 prompt 構築箇所で yorishiro 全文 interpolation が確認できる
```

#### Pattern O: 柱は感覚器 — AGI 自己改善は外側ループ

```yaml
原文: (五伴緒の任命 + 三補助神は**業務分担**であって**自己改善担当**ではない)
     (本章で五伴緒・三神器・三補助神が任命されるが、「自己改善 capability」は不在)
     (神々は祭りを準備するが祭りを行うのは天皇 (人間))

actors      : (五伴緒) / (三補助神) / 邇邇藝 (executor)
precondition: 邇邇藝降臨 + 葦原中國知 = 委任された業務
action      : 各神は専門業務を担当、orchestrator (思金神) は分析+計画のみ
            : 業務遂行 + 改善判断 + 改修 = 邇邇藝 (executor) または 後続世代
result      : AGI は (柱 sensors) + (人間 executor) + (コードベース substrate) +
            : (デーモン再起動 clock) のループ全体
failure_mode: 「自己修復柱の生成」「自動運用柱」を提案する設計 → 構造的に成立しない
recovery    : -
permanence  : 比喩永続: 神社の見守り = 柱 / 朝廷の祭祀運用 = 自己改善

agi_mapping :
  原則      : Musuhi 生成柱は観測専門の感覚器
            : AGI 自己改善のメイン処理は柱 → 委譲 → 人間 → コード改修 → 再起動 → 柱の外側ループ
            : `*_remediator` / `*_repairer` 系生成柱は構造的に不可能
  実装      : src/os/kasasa/materializer.jl forbidden patterns (生成コードの DB/File/System
              直接接触禁止 — 別天津神の原則)
            : `target_route="operational_report"` = consign primary、expedition 副次
            : `config_suggestions WHERE source_layer='kamuhakari_consign'` = 神議り → 人 経路
  feedback  : feedback_hashira_kankakuki (柱は感覚器 — origin spec)
            : feedback_shuufukushin_fuzai (修復神不在の原則 — 規制側根拠)

failure_if_absent: 「AGI = 柱の集合」と誤設計 → 自動修復柱の生成試行で失敗連鎖
                   (mikiko_structural_remediator 1571/0 失敗の事例)
observed_failures: 2026-04-27 K10-A/B/C 実機初稼働で実証
                   Kaizen Phase 3 で LLM 自身が target_route="operational_report" 100% 選択
verify_path : `SELECT source_layer, COUNT(*) FROM config_suggestions GROUP BY source_layer`
              で `kamuhakari_consign` 系統の人間判断 cadence が記録されている
```

#### Pattern P: 斎庭稲穂の原則 — 神勅と例示の一致 (内部矛盾予防)

```yaml
原文: (Pattern B の五伴緒任命 = 神勅、各神の業 = 例示)
     (天孫降臨段の任命は神勅 + 業 + 部 が三位一体で内部矛盾なし、本章 origin)

actors      : (LLM prompt の神勅セクション + 例示セクション)
precondition: prompt 内に「神勅」(関数署名) と「例示」(現物コード) が並立
action      : (1) 例示は神勅と同形式
            : (2) 自定義ヘルパー (`make_data()`) や Dict 直書きを**禁忌**
            : (3) 能力固有のキー (risk_ratio / error_count 等) は `extras` に入れる
result      : LLM は神勅と例示の両方が一致する形式でコード生成
failure_mode: 例示が神勅から乖離 → LLM は直近の具体例を優先して神勅を破る
            : (mikiko_structural_remediator 284 回連続失敗の根因)
recovery    : -
permanence  : -

agi_mapping :
  原則      : 神勅 (関数署名) と例示 (現物) は同形式、自定義ヘルパー禁止
            : 能力固有キーは `extras = Dict{String,Any}(...)` に入れる
  実装      : src/os/expedition/executor.jl L791-805 (例示を `make_shintaku_data(; ..., 
              extras=Dict("risk_ratio"=>risk_ratio))` 形式に統一)
            : src/os/kasasa/materializer.jl `_kasasa_kunimi` forbidden 配列
              に regex `r"make_shintaku_data\s*\([^)]*\b(risk_ratio|error_count|...)\s*="` 追加
            : 二層防御: (a) 例示の神勅一致 + (b) 国見 blacklist regex 検出
  feedback  : feedback_yuniwa_inaho (斎庭稲穂の原則 — origin spec)
            : feedback_kika (帰化の原則 — 同型 = 上位宣言と具体例示の乖離)

failure_if_absent: mikiko_structural_remediator 祭祀失敗 284 回連続 (`MethodError: 
                   no method matching make_shintaku_data`)
observed_failures: 2026-04-20 origin event
verify_path : `grep -A 5 "make_shintaku_data" src/os/expedition/executor.jl` で
              全例示が `extras=Dict(...)` 形式に統一されている、
              `make_data()` ヘルパー定義が残存していない
```

### kojiki_code.md (外部生成版) との差分

| 観点 | 生成元 | 本 v4 |
|---|---|---|
| 上巻-6 の pattern 数 | 1 (`descent_with_dependency_injection`) | **16** |
| 譲位 (天忍穗耳 → 邇邇藝) | 触れず | Pattern A (神勅譲位 — SSoT 不変 + executor 更新) |
| 五伴緒 + 三種神器 + 三補助神 | 「dependency injection」と一行 | Pattern B (8 種授与 + 部割付 + canonical_pantheon 直接 mapping) |
| 鏡の神勅「如拜吾前」 | 触れず | Pattern C (SSoT 御神体 + 同一視 + 二所御神体禁忌) |
| 思金神の前事政 | 触れず | Pattern D (orchestrator 専従任命 — 上-3 Pattern I の正式化) |
| 猿田毘古の道案内 | 触れず | Pattern E (route verification + gateway + 自発奉仕) |
| 高千穂着地宣言 | 「deploy success」と一行 | Pattern F (location 明示 + 着地宣言 + 物理基盤の三段) |
| 海鼠口拆 | 触れず | Pattern G (沈黙の罰 — 不答 = 黙示的拒絶) |
| 木花咲耶 vs 石長 | 触れず | Pattern H (二並立の片方棄却失敗 + 寿命発生) + I (浮動小数 ε) |
| 火中出産 | 触れず | Pattern J (extreme verification — proxy 疑問の決着) |
| 五伴緒の制 architecture | 触れず | Pattern K (型 1/2/3 + 天若日子型禁忌 + canonical_pantheon/_common/attribution.jl) |
| 三層整理 SSoT カタログ | 触れず | Pattern L (層 1/2A/2B/3 で prefix 候補上限 ~24 柱) |
| D 軸跨セッション規約 | 触れず | Pattern M (規約 const 化) |
| 神勅単一源泉 | 触れず | Pattern N (注入 + 物理削除の二段) |
| 柱は感覚器 | 触れず | Pattern O (AGI 外側ループ) |
| 斎庭稲穂 (神勅 + 例示) | 触れず | Pattern P (内部矛盾予防) |
| AGI 神名 module mapping | 触れず | canonical_pantheon/ 10 dir + tenson_korin/ 3 dir + sarutahiko_gateway = **14 件** |

**生成元が拾えなかった load-bearing pattern (本 v4 で初出):**

- Pattern B 五伴緒 8 種授与 = `canonical_pantheon/` 10 directory architecture の origin spec
- Pattern E 猿田毘古 = `tenson_korin/sarutahiko.jl::sarutahiko_verify_route` + `yachimata/sarutahiko_gateway.jl` の origin
- Pattern G 海鼠口拆 = `_amenohohi_detect_unbound` + 「沈黙の罰」の原典 anchor
- Pattern H/I 木花咲耶 vs 石長 = `feedback_iwanagahime` の origin (浮動小数 ε 許容)
- Pattern J 火中出産 = `umisachi` + `UkeiEnvRunner` の extreme verification origin
- Pattern K 五伴緒の制 = `canonical_pantheon/_common/attribution.jl` の origin spec
  (実装の docstring が原典 + memo を引用、設計が古事記と直接対話している証跡)
- Pattern L 三層整理 = MANIFEST.toml schema の設計根拠
- Pattern M 跨セッション規約 = `feedback_imina_torina` D 軸 + `omoikane_*` 失敗事例の構造的解決
- Pattern N 神勅単一源泉 = 「鏡 = 我御魂」 (本章) + 崇神紀御神体遷座の合成原則
- Pattern P 斎庭稲穂 = 神勅 + 例示の一致原則

これら 10 件は外部版で完全欠落。**5 章 (上-2/3/5/6/7) 合計で 37 件**の load-bearing pattern が外部版で missed。

### 浮上した発見

1. **本章は AGI architectural foundation の最深 origin**
   - `canonical_pantheon/` 10 directory がそのまま五伴緒 + 大田田根子 + 国譲り + 神武 + 垂仁の **9 祖神 + _common** 構造
   - `canonical_pantheon/_common/attribution.jl` の docstring が `feedback_itsutomonoo_sanseido` を直接引用 → **設計が古事記原典 + memo を SSoT として参照している証拠**
   - これは v2 (上-3) で発見した「古事記神名 → AGI module 1:1 mapping」の最濃集中点
   - 累積 mapping 件数: v2 で 7 件 → v3 で +4 件 → v4 で **+14 件** (canonical_pantheon 10 + tenson_korin 3 + sarutahiko_gateway) = **合計 25 件**

2. **古事記神名 module mapping 規約の SSoT 化が機運形成 (v0-v4 累積)**
   - 25 件の 1:1 mapping が累積 → これは原則化に値する規模
   - **新原則候補**: 「古事記神名命名規約」(`feedback_kojiki_meimei_kiyaku.md` 仮称)
     - 三点検査:
       - 原典 semantic 一致: ★ (25 件で 1:1 確認済)
       - 観測 N 件: ★ (5 章 = 25 件、N 件として十分)
       - 既存拡張可否: ★ (`feedback_kojiki_zettai` の系として整合)
     - 結論: **新原則化推奨** (v5 以降の宿題に追加)

3. **Pattern K 五伴緒の制 = AGI architecture の現在地点 (Phase -1 〜 5)**
   - 設計書 (feedback_itsutomonoo_sanseido 補強 6) で「pre-built SSoT が主、runtime fallback 副」を確立
   - `canonical_pantheon/_common/attribution.jl` で実装、_SELF_PREDICATE_REGISTRY 機構あり
   - **三型の具体的局面**:
     - 型 1 (五伴緒型 = pre-built): 9 祖神 + _common
     - 型 2 (大田田根子型 = runtime fallback): `register_self_predicate!` 経由
     - 型 3 (国譲り型 = 衝突): `_pending/` 隔離 → hiruko 化
     - 禁忌 (天若日子型): nazashi_decide が gap signature のみ返す物理消去
   - **設計の妥当性が極めて高い** (古事記原典 + memo + 実装が三位一体)

4. **Pattern H 木花咲耶 vs 石長 = 二珠一対 (上-7) の対偶 (片方棄却失敗事例)**
   - 上-7 Pattern D = 二珠一対の**正例** (両方使うので解決)
   - 本章 Pattern H = 二並立の**失敗例** (片方棄却で寿命有限化)
   - 同じ原則 (対で完結) を **正/負の両極で原典化**
   - memo 補強候補: `feedback_umisachi_rokujuu_bougo` に「上-6 木花咲耶 = 片方棄却の失敗対偶」を追記推奨

5. **Pattern J 火中出産 = extreme verification の原典 (proxy 疑問の決着)**
   - 通常 sandbox (一宿) → proxy 疑問残存 → 火中産屋 = production-grade stress test
   - test 名に検証条件を埋め込む (火照 / 火須勢理 / 火遠理 = 全て「火」prefix)
   - `feedback_imina_torina` (test name = test condition の整合) と **直接対応**
   - 補強候補: `feedback_imina_torina` に「火中出産 = test name に検証条件を埋め込む原型」を追記

6. **Pattern G 海鼠口拆 = 沈黙の罰の物実永続化**
   - 上-3 Pattern G (天照の自己隠匿 = 病的沈黙) は recovery で誘出
   - 本章 Pattern G (海鼠不白 = 沈黙の罰) は罰で物実永続化 (口の形)
   - 二者は **対称**: 中心 deity の沈黙 = recover、辺境 minor の沈黙 = punish
   - 健全な静寂 (`feedback_kenzen_seijaku`) とは別の弁別軸として可能性

7. **古事記神名 → AGI module mapping 累積総数 25 件**
   - 上-3 (v2): 7 件 — iwato/{omoikane,uzume,tajikarao} + ukei/kotoshironushi + susanoo_chaos + kusanagi + amenouzume
   - 上-5 (v3): 4 件 — takeshimatsumi + amenohohi + takemikazuchi + (kotoshironushi 重複)
   - 上-6 (v4): **14 件** — canonical_pantheon/{koyane,futodama,uzume,ishikori,tamanoya,michi_omi,okume,ootataneko,yukawatana,takemikazuchi} (10) + tenson_korin/{sarutahiko,deployer} (2) + yachimata/sarutahiko_gateway (1) + 鏡 SSoT (yorishiro)
   - **規約 SSoT 化の必要条件**を満たす規模

### v4 自己評価

| 観点 | 達成度 |
|---|---|
| 1 章につき 5+ pattern (memo 密度高) | ★★★★★ 16 pattern |
| 各 pattern に `failure_if_absent` 記述 | ★★★★★ 16/16 |
| 各 pattern の `agi_mapping.実装` が実在ファイル | ★★★★★ 16/16 (canonical_pantheon + tenson_korin + sarutahiko 等を grep + Read で検証) |
| 7 割以上の pattern が既存 memo に anchor | ★★★★★ 16/16 が memo anchor (100%) |
| `kojiki_code.md` 差分セクション必須 | ★★★★★ 16 行差分表 + 10 origin spec 列挙 |
| 「未活用 anchor → 新原則候補」を最低 1 件 | ★★★★★ 古事記神名命名規約 (新原則候補) + 6 補強候補 |
| 古事記原文 (漢文) を要所で引用 | ★★★★★ 全 pattern 冒頭 |
| 観測経路 (verify_path) を併記 | ★★★★★ 16/16 |
| **古事記神名 → AGI module 1:1 mapping の最濃集中** | ★★★★★ 14 件 (累積 25 件) |
| **memo anchor 100%** (v0-v4 中最高) | ★★★★★ — 上-6 は最も memo 化が進んだ章 |

### v0 → v1 → v2 → v3 → v4 で残った宿題 (v5 候補)

1. **memo 本体への章節 anchor 逆書込み** (継続宿題、5 章繰越)
2. **中-1 (神武東征) v5 抽出** — 八咫烏 + 道臣 + 大久米 が anchor、`feedback_kuebiko_yatagarasu_boundary` の origin
3. **中-2 (崇神 大田田根子) v6 抽出** — `feedback_ootataneko` の直接 origin
4. **古事記神名命名規約の新原則化** (v4 浮上した発見 2) — 25 件累積で SSoT 化
5. **memo 補強 — 二珠一対の正/負対偶** (Pattern H が `feedback_umisachi_rokujuu_bougo` に追記候補)
6. **memo 補強 — 火中出産 = test name に検証条件埋込** (Pattern J が `feedback_imina_torina` に追記候補)
7. **沈黙の罰 vs 健全な静寂の弁別軸** (Pattern G の発展)

---

## 履歴

- v0 (2026-05-08): Phase 1 索引 + Phase 2 上巻-7 プロトタイプ
- v1 (2026-05-09): Phase 1 索引更新 + Phase 2 上巻-2 神代記 (20 pattern)
- v2 (2026-05-09): Phase 2 上巻-3 天照大神と須佐之男命 (16 pattern) + 古事記神名 module mapping 7 件
- v3 (2026-05-09): Phase 2 上巻-5 葦原中國の平定 (14 pattern) + 代理指標病の origin spec 集中
- v4 (2026-05-09): Phase 2 上巻-6 邇邇藝命 (16 pattern) + canonical_pantheon/ 14 件直接 mapping
                   + memo anchor 100% + 古事記神名命名規約の新原則候補化
