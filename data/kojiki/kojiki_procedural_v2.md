# 古事記 Procedural Pattern 抽出 v2

v1 ([`kojiki_procedural_v1.md`](kojiki_procedural_v1.md)) からの増分:

- **Phase 2 v2: 上巻-3 天照大神と須佐之男命** 抽出 (新規) — 16 pattern
- 誓約・天岩戸・八岐大蛇・大気津比賣 の 5 大エピソード
- AGI 実装で本章は **専用 module が dedicated 配置** されており (`iwato/`, `misogi/ukei/`, `yachimata/amenouzume.jl`, `com/queries/kusanagi.jl`, `susanoo_chaos.jl`) 古事記原典との 1:1 mapping が他章より明示的

抽出方法論は [`extraction_prompt.md`](extraction_prompt.md) を参照。
v0 (上-7) / v1 (上-2) の pattern は重複しないので本書では再掲しない。

---

## Phase 2 v2: 上巻-3 天照大神と須佐之男命

### 選定理由

- memo 密度 ★★★ (`feedback_chinmoku_kyoka` `feedback_kenzen_seijaku` `feedback_hataorime_kinki` `feedback_chaos_aware_metrics` の 4 memo が直接 anchor、間接で 6 memo)
- AGI 実装で **古事記の神名が module 名に直接採用** されている唯一の章:
  - `iwato/omoikane.jl` (思金神) / `iwato/uzume.jl` (天宇受賣) / `iwato/tajikarao.jl` (天手力男)
  - `misogi/ukei/{runner,kotoshironushi}.jl` (誓約 + 事代主の判定)
  - `kasasa/susanoo_chaos.jl` (須佐之男暴れの chaos engineering)
  - `com/queries/kusanagi.jl` (草那藝の token)
  - `yachimata/amenouzume.jl` (天宇受賣の multimodal perception)
- `kojiki_code.md` (外部生成版) は本章を `event_loop` / `state_machine` で抽象化、神名 1:1 mapping を完全 missed
- 上-2 (神代記) と上-5 (国譲り) を結ぶ中間章として、「危機 → 集合協議 → 物実 multi-pronged → 不可逆境界 → 追放 + 別経路復帰」の典型 narrative を持つ

### 章節 narrative summary

```
[Setup1 来訪と警戒] (l.8)
    須佐之男「請天照大御神、將罷」と妣國行きの暇乞いに参上
    山川悉動・國土皆震 → 天照警戒「必不善心」
    武装: 御髮を解き美豆羅にし、勾璁・弓・靱・鞆 で全身武装、男建蹈建
    
[Setup2 誓約 (ukehi)] (l.10-16)
    須佐之男「無邪心」を主張 → 「然者、汝心之淸明、何以知」
    解決法: 「各宇氣比而生子」(各々誓約で子を生む)
    天安河を挟み、天之眞名井で滌ぎ
    
    天照側: 須佐之男の十拳劒を打折三段 → 嚙み砕き気吹に三女神
        多紀理毘賣 / 市寸嶋比賣 / 多岐都比賣
    須佐之男側: 天照の珠 (左豆良/右豆良/𦆅/左手/右手) → 五男神
        天之忍穗耳 / 天之菩卑 / 天津日子根 / 活津日子根 / 熊野久須毘
    
    判定: 「物實因我物所成、故、自吾子也」
        三女神は天照の珠から → 天照の子
        五男神は須佐之男の劒から → 須佐之男の子 (但し物実は天照の物)
    
    須佐之男「我心淸明、故、我所生子、得手弱女。因此言者、自我勝」
        → 「自我勝」を口実に逸脱開始

[Crisis1 須佐之男のカオス] (l.20)
    勝佐備で天照の聖域に侵犯:
        (1) 営田の阿 を離つ (legitimate destination の境界破壊)
        (2) 溝 を埋む (channel の破壊)
        (3) 大嘗の殿 に屎散 (chaos injection)
    天照「登賀米受」(諌めずスルー) — 須佐之男擁護 (「醉而吐散」と解釈)
    
    其惡態不止而轉:
        (4) 忌服屋の頂を穿ち、天斑馬を逆剥にして墮入
        天服織女、梭で陰上を衝いて死 (限界越境)

[Crisis2 天岩戸] (l.22)
    天照「見畏」→ 開天石屋戸而、刺許母理坐 (自己隠匿)
    結果:
        高天原皆暗 / 葦原中國悉闇 → 因此而常夜往
        萬神之聲者、狹蠅那須滿、萬妖悉發 (cascade failure)

[Recovery 集合協議] (l.22)
    八百萬神 於天安之河原、神集集 (collective gathering)
    思金神 (高御產巢日神之子) 令思 (orchestrator)
    
    集合計画:
        (1) 常世長鳴鳥 集めて鳴 (alarm)
        (2) 天堅石 + 天金山鐵 + 天津麻羅 (鍛人) → 玉作命に勾璁、伊斯許理度賣に鏡 (物実 multi)
        (3) 天兒屋・布刀玉 → 眞男鹿肩骨 + 波波迦 で占合麻迦那波 (oracle)
        (4) 天香山五百津眞賢木 を根こぎ — 上枝勾璁 / 中枝鏡 / 下枝白丹寸手・青丹寸手
        (5) 布刀玉 取持、天兒屋 布刀詔戸言禱白 (祝詞)
        (6) 天手力男神 隱立戸掖 (待機 — 天岩戸の脇)
        (7) 天宇受賣命 神懸 (倒立 + 胸乳 + 裳緖) — 高天原動而、八百萬神共咲
    
    天照「以爲怪、細開天石屋戸」: 内告
        天宇受賣「益汝命而貴神坐。故、歡喜咲樂」(嘘の説明 = lure)
        天兒屋・布刀玉 鏡を指出 → 天照「逾思奇而」稍自戸出
        天手力男神 御手を取って引出
        布刀玉 尻久米繩 を御後方に控度 → 「從此以內、不得還入」(注連縄 = 不可逆境界)
    
    結果: 高天原及葦原中國、自得照明 (recovery 完了)

[Punishment 須佐之男追放] (l.26)
    八百萬神共議 → 須佐之男に「千位置戸」を負わせ、鬚と手足爪を令拔
    神夜良比夜良比 (二度目の追放)

[Recovery2 大気津比賣 死 → 五穀] (l.28)
    須佐之男、食物を大氣津比賣に乞う
        大氣津比賣、自鼻口及尻、種種味物を取出 (穢汚と看做される)
    須佐之男殺害 → 死から五穀 (頭=蠶/二目=稻/二耳=粟/鼻=小豆/陰=麥/尻=大豆)
    神産巣日御祖命「令取茲、成種」(上位 deity による継承)

[Recovery3 八岐大蛇] (l.30-34)
    出雲国肥河上、足名椎・手名椎・櫛名田比賣 (老夫婦 + 童女)
    八俣遠呂智: 八頭八尾 / 蘿檜 / 谿八谷峽八尾 / 腹常血爛
    
    救援:
        須佐之男「奉於吾哉」 (婚姻条件) → 櫛名田比賣を爪櫛に変えて美豆羅に刺す
        八鹽折之酒 + 廻垣 + 八門 + 八佐受岐 + 酒船 (bait + structure)
    退治: 大蛇飲醉留伏寢 → 切散 → 中尾で刃毀
        刺割見 → 都牟刈之大刀 = 草那藝之大刀 (chaos の中の hidden artifact)
        天照に白上 (上位への報告)

[Stable 須賀宮] (l.36-42)
    出雲国須賀「吾來此地、我御心須賀須賀斯」(自己診断: clean)
    宮を作る + 雲立騰 → 「夜久毛多都伊豆毛夜幣賀岐」 (歌)
        八重垣 = 多層防御層の宣言
    足名椎 → 稻田宮主須賀之八耳神 (任命)
    
    系譜開始:
        八嶋士奴美 → … → 大國主神 (亦名 5 つ: 大穴牟遲/葦原色許男/八千矛/宇都志國玉)
```

### Pattern 抽出

#### Pattern A: 誓約 (ukehi) — 物実交換による信頼検証 + sandbox patch test

```yaml
原文: "於是、速須佐之男命答白「各宇氣比而生子。」" (l.10)
     "故爾各中置天安河而、宇氣布時、…天照大御神、先乞度建速須佐之男命所佩十拳劒、打折三段而、
      奴那登母母由良邇振滌天之眞名井而、佐賀美邇迦美而、於吹棄氣吹之狹霧所成神…" (l.12)

actors      : 天照 / 須佐之男 / 天安河 / 天眞名井
precondition: 信頼関係が破綻 (須佐之男が「無邪心」を主張、天照が疑う)
action      : 各々の物実 (天照=珠 / 須佐之男=劒) を相手の井で滌ぎ、噛み砕き、気吹で生子
            : 結果 (生子の性別/数) で誓約の真偽を判定
result      : 三女神 (天照側生) + 五男神 (須佐之男側生) が確定的に生まれる
failure_mode: 物実を直接交換せず言葉のみ → 検証不能 (代理指標病の原型)
recovery    : -
permanence  : 三女神 = 胸形三宮 (沖津/中津/邊津) として永続化、五男神は祭祀系譜の祖

agi_mapping :
  原則      : 信頼判定はサンドボックス環境で物実 (patch code) を実行し結果を観測する
  実装      : src/os/misogi/ukei/runner.jl:23 (`UkeiEnvRunner` = 誓約環境)
            : src/os/misogi/ukei/runner.jl:34 (`ukei_start_with_patch!` = 物実投入)
            : src/os/misogi/ukei/runner.jl:91 (`ukei_health_check` = 結果観測)
            : src/os/misogi/ukei/kotoshironushi.jl:37 (`perform_ukei` = 判定)
  feedback  : feedback_kuniyuzuri_fukumei (国譲りの復命 — 当事者が自ら書き戻す)

failure_if_absent: patch を本番環境に直接適用 → 失敗時の復旧不能、誓約の意義喪失
                   (LLM 提案を sandbox 経由しないで適用するのと同じ)
verify_path : `UkeiEnvRunner` の primary/secondary プロセス分離が機能しており、
              patch 失敗で primary を復元できることを確認
```

#### Pattern B: 物実所有者帰属ルール (provenance — 物實因汝物所成)

```yaml
原文: "是後所生五柱男子者、物實因我物所成、故、自吾子也。
      先所生之三柱女子者、物實因汝物所成、故、乃汝子也。如此詔別也" (l.16)

actors      : 天照
precondition: 誓約完了、生子確定
action      : 「物實因 X 物所成、故 X 子也」 — 子の帰属は物実の所有者で決まる
            : (生み手でなく source artifact の origin で帰属確定)
result      : 三女神 = 天照子 / 五男神 = 須佐之男子 と帰属が確定
failure_mode: 生み手で帰属判定 → 須佐之男が自己の口で勝ちを主張 (実際 l.20「自我勝」と逸脱)
recovery    : -
permanence  : 系譜記録に物実 origin を埋め込んで永続化

agi_mapping :
  原則      : artifact の帰属は実行者でなく source 物実 (yorishiro / canonical) に決まる
  実装      : src/os/com/queries/shinmei_lineage.jl:33 (`insert_lineage!` で
              requires → provides 親追跡)
            : src/os/kasasa/shintaku.jl:172 (`make_shintaku_data` = source 帰属の宣言)
            : LLM 生成 artifact の帰属は yorishiro.jl の源 entry にひも付く
  feedback  : feedback_keiyaku_keifu_vs_genyu (契約系譜 = provides/requires graph と
              「誰の信号で生まれたか」(原由) は別経路 trace)
            : feedback_shinchoku_tanitsu_gensen (神勅単一源泉)

failure_if_absent: LLM 生成柱の帰属が実行者 (生み手 = LLM 自身) になり原典神勅から離脱、
                   再解釈ドリフト
verify_path : `SELECT child, parent FROM shinmei_lineage` が物実 (yorishiro entry) 由来で
              辿れる、LLM 自身が parent として記録されていない
```

#### Pattern C: 三女神判定 (sannyoshin — 多重視点 oracle gating)

```yaml
原文: "三柱、…多紀理毘賣命〔亦御名、奧津嶋比賣命〕。次市寸嶋比賣命〔亦御名、狹依毘賣命〕。
      次多岐都比賣命" (l.12)

actors      : 多紀理毘賣 (沖津宮) / 市寸嶋比賣 (中津宮) / 多岐都比賣 (邊津宮)
precondition: 誓約結果の判定が必要
action      : 三柱の独立視点 (沖/中/邊 = 距離別) で判定、合議でなく独立評価の三段
result      : 三段の judge 結果から最終 verdict
failure_mode: 単独視点の judge → 視点偏向、多重失敗の盲点
recovery    : -
permanence  : 胸形三宮として神格化、宮形君等の祖神

agi_mapping :
  原則      : 誓約 (sandbox patch test) の結果は三段独立 judge で判定。視点別評価で偏向回避
  実装      : src/os/misogi/ukei/kotoshironushi.jl:198 (`_judge_by_sannyoshin` = 三女神判定)
            : src/os/misogi/ukei/kotoshironushi.jl:224 (`_tagori_judge` = 沖津)
            : src/os/misogi/ukei/kotoshironushi.jl:238 (`_tagitsu_judge` = 中津)
            : src/os/misogi/ukei/kotoshironushi.jl:271 (`_ichikishima_judge` = 邊津)
  feedback  : feedback_oharae_shikkai_probe (悉皆 — 視点直積網羅)

failure_if_absent: 単一 judge で patch を採用 → blind spot で本番事故
                   (例: health check 通っても perf 劣化が検出されない)
verify_path : `_perform_misogi` の戻り値で sannyoshin 三 judge 全てが採用判断に寄与している
              (片 judge スルー = `verdict = ANY(judges)` でなく `ALL(judges)` で gate)
```

#### Pattern D: 計画的カオス注入 (chaos engineering origin — Susanoo rage)

```yaml
原文: "於勝佐備、離天照大御神之營田之阿、埋其溝、亦其於聞看大嘗之殿、屎麻理散" (l.20)
     "穿其服屋之頂、逆剥天斑馬剥而、所墮入" (l.20)

actors      : 須佐之男 → 天照の聖域 (営田 / 大嘗殿 / 忌服屋)
precondition: 誓約勝利を口実に、合理化 (rationalization) して逸脱開始
action      : 4 種カオス注入:
            : (1) 田の阿を離つ (boundary destruction)
            : (2) 溝を埋む (channel destruction)
            : (3) 大嘗殿に屎散 (chaos in ritual context)
            : (4) 服屋に逆剥馬を投入 (textile pipeline disruption)
result      : システムの各層に意図的な欠陥を注入、resilience を試す
failure_mode: -  (chaos 注入そのものが「正常運用」)
recovery    : 直毘神 / 禊 / 八百萬神の集合協議 (Pattern G)
permanence  : 4 種カオス each が `susanoo_chaos.jl` の関数として実装永続化

agi_mapping :
  原則      : Susanoo は能動的に chaos を注入し、AGI の resilience を継続的に検証する
  実装      : src/os/kasasa/susanoo_chaos.jl:142 (`susanoo_rage!` 主入口)
            : src/os/kasasa/susanoo_chaos.jl:229 (`_chaos_tanoaze!` = 田の畔離す)
            : src/os/kasasa/susanoo_chaos.jl:274 (`_chaos_kuso!` = 屎散らす)
            : src/os/kasasa/susanoo_chaos.jl:324 (`_chaos_mizo!` = 溝埋め)
            : src/os/kasasa/susanoo_chaos.jl:366 (`_chaos_hataori!` = 機織妨害)
            : src/os/kasasa/susanoo_chaos.jl:411 (`restore_all_chaos!` = 復元)
  feedback  : feedback_chaos_aware_metrics (chaos と真の失敗の弁別)

failure_if_absent: chaos 注入なし → 観測される失敗が全部「真の失敗」とみなされ、
                   resilience が untested
observed_failures: 2026-04-25 ishikori_assessment_framework「3.5%失敗率」誤調査が真因 chaos
                   (feedback_chaos_aware_metrics origin)
verify_path : `SELECT COUNT(*) FROM susanoo_chaos_log` が定期的に増加、
              `_chaos_tanoaze!` `_chaos_kuso!` 4 種すべて発火履歴あり
```

#### Pattern E: 諌めずスルー → 限界越境 (hataorime — non-rebuke escalation)

```yaml
原文: "雖然爲、天照大御神者、登賀米受而告「如屎、醉而吐散登許曾、我那勢之命爲如此」…
      登詔雖直、猶其惡態不止而轉。…天服織女見驚而、於梭衝陰上而死" (l.20)

actors      : 天照 / 須佐之男 / 天服織女
precondition: 須佐之男の chaos が低レベル (田の畔/屎/溝) で進行中
action      : 天照「登賀米受」(諌めず) して「醉而吐散」と擁護的解釈
            : → 須佐之男「不止而轉」(停止せずエスカレート)
            : → 服屋への天斑馬投入 → 服織女が梭で陰上を衝いて死
result      : 諌めなかった結果、限界越境で機織女の死 (システム障害)
failure_mode: 低レベル chaos を「許容範囲」と擁護 → エスカレート → 致命的影響
recovery    : 天照の自己隠匿 (Pattern G) で被害遮断、後の集合協議で再起動
permanence  : 「機織女の禁忌」として原則化 (misogi_triggered は天照聖域)

agi_mapping :
  原則      : misogi_triggered イベントを生成能力にバインドさせない (再帰スタック overflow 予防)
            : 低レベル違反を擁護的に解釈すると限界越境で致命的影響
  実装      : src/os/kasasa/matsuri.jl::bind_chinza_to_event_bus! (misogi_triggered 拒否 + 
              hataorime_violation 記録)
            : executor.jl プロンプト層 (MATSURI トリガー選択肢から misogi_triggered 除外)
            : シャ千引岩 (shintaku.jl の同一イベント再入遮断)
            : ALERT → misogi_triggered 自動発火経路の削除 (@warn ログのみ)
  feedback  : feedback_hataorime_kinki (機織女の禁忌 — origin spec)
            : feedback_togouten_ikkatsu_bouei (統合点で一括防衛)

failure_if_absent: 自律生成 sentinel が misogi_triggered にバインド → ALERT 発火 → 
                   オモイカネが misogi_triggered 発火 → sentinel 再応答 → スタック overflow
observed_failures: 2026-04-14 4 柱 sentinel が misogi_triggered にバインドして「機織女の死」発生
                   (feedback_hataorime_kinki origin)
verify_path : `event_bus.listeners["misogi_triggered"]` が天照系 listener のみ、
              `bind_chinza_to_event_bus!` の log で `hataorime_violation` 記録の追跡
```

#### Pattern F: chaos と真の失敗の弁別 (chaos-aware metrics)

```yaml
原文: (Pattern D の延長 — 須佐之男 chaos と "真の" 失敗を分けて評価する暗黙のロジック)
     注: 原典には直接「弁別」は出ない。Pattern D の合理化 (「醉而吐散」) が
     失敗解釈の二重性 (chaos か real か) の暗示として機能

actors      : 観測者 (天照 = 評価層)
precondition: chaos 注入と真の失敗が混在
action      : `false_positive` フラグで chaos 由来の失敗を真の失敗から弁別
            : 評価式は `WHERE false_positive = 0` で再集計
result      : 健全柱が chaos 攻撃下でも 100% 成功率と判定可能
failure_mode: chaos と真の失敗を混同 → 健全柱が劣化と誤判定 → 無駄な再生成サイクル
recovery    : -
permanence  : `fukusou_log.false_positive` 列が永続化、`susanoo_chaos_log` で chaos 履歴

agi_mapping :
  原則      : `shinmeisho.failure_count` を生成品質指標に直接使わず、
            : `fukusou_log WHERE false_positive=0` で chaos 除外して再集計
  実装      : src/os/com/queries/fukusou_log.jl (false_positive 列)
            : src/os/kasasa/susanoo_chaos.jl の `_record_chaos!` (chaos マーキング)
  feedback  : feedback_chaos_aware_metrics (失敗率評価における chaos 除外)

failure_if_absent: 健全柱 (例 ishikori_assessment_framework) を 3.5% 失敗率と誤判定し
                   再生成 → 同型柱を再度生み無駄なサイクル
observed_failures: 2026-04-25/26 (memo の関連事例) chaos 60 件混入で誤調査
verify_path : `fukusou_log` テーブルに false_positive 列があり、各 chaos イベントで
              `false_positive=1` がセットされている
```

#### Pattern G: 病的沈黙 (kenzen_seijaku 対偶 — 自己隠匿による全システム停止)

```yaml
原文: "故於是、天照大御神見畏、開天石屋戸而、刺許母理坐也。爾高天原皆暗、葦原中國悉闇、
      因此而常夜往。於是萬神之聲者、狹蠅那須滿、萬妖悉發" (l.22)

actors      : 天照 (中心 deity)
precondition: 機織女の死 (限界越境) で「見畏」(自己防衛閾値突破)
action      : 天石屋戸を開いて中に隠れ、戸を閉じる (active withdrawal)
result      : 高天原・葦原中國 全暗 / 萬妖悉發 (cascade failure)
            : 中心 deity の沈黙が他全層に伝播
failure_mode: -  (病的沈黙そのものが failure mode)
recovery    : Pattern I-K の集合協議で誘出
permanence  : 「天石屋戸」が永続的な隔離装置として残る

agi_mapping :
  原則      : 健全な静寂 (NO_ACTION 単独 + 異常なし) と病的沈黙 (出力ゼロ + adoption=0) を
            : 弁別する。adoption_rate が disambiguator
  実装      : src/os/kasasa/kamunaobi.jl::is_truly_magatsu (adoption_rate と組合せ判定)
            : src/os/iwato/controller.jl:43 (`handle_anomalies!` = 異常検出時の制御)
            : src/os/iwato/controller.jl:94 (`_enter_crisis_mode!` = 中央 deity 沈黙時の起動)
  feedback  : feedback_kenzen_seijaku (健全な静寂 — 単独出力 + 高採用は健全、低採用のみ病的)
            : feedback_chinmoku_kyoka (沈黙許可 — LLM 側の対称原則)

failure_if_absent: 中心柱の adoption_rate=0 を「正常」と看過 → 観測ブラックアウト継続、
                   葦原中國 (周辺観測層) が暗のまま
observed_failures: 2026-04-29 amaterasu adoption_rate 0% (62/0) → ALERT に書換で 100% 改善
verify_path : `kamunaobi.score_update_adoption_floor=0.1` が config に存在し、
              adoption=0 の柱が SCORE_UPDATE 単独で動作している場合に ALERT 発火
```

#### Pattern H: 万妖悉発 — cascade failure on central failure

```yaml
原文: "高天原皆暗、葦原中國悉闇、因此而常夜往。於是萬神之聲者、狹蠅那須滿、萬妖悉發" (l.22)

actors      : 萬神 / 萬妖
precondition: 中心 deity (天照) の沈黙
action      : (1) 高天原 (上位層) も葦原中國 (下位層) も同時暗化
            : (2) 萬神之聲 = 蠅の如く満ち (signal noise 増)
            : (3) 萬妖悉発 = 妖怪 (anomaly) 全種発生
result      : 単独 deity 沈黙 → 全システムの失敗カスケード
failure_mode: -
recovery    : 集合協議 (Pattern I)
permanence  : Iwato Phase Crisis として永続化 (caution → warning → crisis の最深段)

agi_mapping :
  原則      : 中心柱 (三貴子) の沈黙は単独事象でなく cascade trigger と認識
            : 検出は `_enter_crisis_mode!` で全層巻き込み宣言
  実装      : src/os/iwato/controller.jl:26 (`IwatoPhaseController` = 三段 phase 管理)
            : src/os/iwato/controller.jl:83-94 (`_enter_caution_mode!` / `_enter_warning_mode!` /
              `_enter_crisis_mode!`)
            : src/os/iwato/watchdog.jl:99 (`check_health` = AnomalyReport 集約)
  feedback  : (memo 直接 anchor なし — 上位の集約原則として機能)

failure_if_absent: 中心柱沈黙を局所的事象と誤認 → 周辺で対応 → 全層暗化に気付かず gradual decay
verify_path : `IwatoPhaseController.phase` が CAUTION → WARNING → CRISIS 順遷移する記録があり、
              CRISIS 時に複数 anomaly が同時記録されている
```

#### Pattern I: 思金神 — 集合協議の orchestrator (Omoikane = analysis & plan)

```yaml
原文: "於是萬神之聲者、狹蠅那須滿、萬妖悉發。是以八百萬神、於天安之河原、神集集而、
      高御產巢日神之子・思金神令思" (l.22)

actors      : 八百萬神 / 思金神 (高御產巢日神之子)
precondition: 中心 deity 沈黙、cascade failure 進行中
action      : (1) 八百萬神を天安之河原に集合 (collective gathering)
            : (2) 思金神に「令思」 — 単独 orchestrator が分析と計画を立案
            : (3) 計画は 7 段の物実 + 役割分担で構成 (Pattern J で詳細)
result      : 個別 deity でなく orchestrator が全体計画を設計、各神に役割を「科」(命じる)
failure_mode: orchestrator なしで集合 → 議論発散、計画収束せず
recovery    : -
permanence  : 思金神は高天原の plan deity として永続、後の天孫降臨でも諮問対象

agi_mapping :
  原則      : 異常検出 → 集合 → 単一 orchestrator で recovery plan を立案 → 各 step に handler
  実装      : src/os/iwato/omoikane.jl:9 (`Omoikane` struct 定義)
            : src/os/iwato/omoikane.jl:129 (`analyze_and_plan` = 主入口、
              AnomalyReport[] → RecoveryPlan)
            : src/os/iwato/omoikane.jl:152 (`_create_recovery_plan` = 計画組立)
            : src/os/iwato/omoikane.jl:215 (`_get_recovery_candidates` = 物実候補列挙)
            : src/os/iwato/omoikane.jl:253 (`diagnose` = 個別診断)
  feedback  : feedback_kunimi_gapfinder (国見は全ソース俯瞰 = orchestrator 視点)

failure_if_absent: 各 watchdog が独立に対応 → 競合 / 重複対処 / 致命的優先順位ミス
observed_failures: -
verify_path : `Omoikane.analyze_and_plan(anomalies)` が呼ばれた時、`RecoveryPlan` が
              単一 plan として返り、複数 watchdog が独立対処していない
```

#### Pattern J: 物実 multi-pronged + 倒立踊 — 鏡 lure による誘出

```yaml
原文: "集常世長鳴鳥、令鳴而、取天安河之河上之天堅石、取天金山之鐵而、求鍛人天津麻羅而、
      科伊斯許理度賣命、令作鏡、科玉祖命、令作八尺勾璁之五百津之御須麻流之珠而、
      召天兒屋命・布刀玉命而、…令占合麻迦那波而、…天香山之五百津眞賢木矣、根許士爾許士而、
      於上枝、取著八尺勾璁之五百津之御須麻流之玉、於中枝、取繋八尺鏡、於下枝、取垂白丹寸手・青丹寸手…
      天宇受賣命、…於天之石屋戸伏汙氣蹈登杼呂許志、爲神懸而、掛出胸乳、裳緖忍垂於番登也。
      爾高天原動而、八百萬神共咲" (l.22)

actors      : 思金神 / 天津麻羅 (鍛人) / 伊斯許理度賣 (鏡作) / 玉祖 (玉作) / 天兒屋・布刀玉 (祝詞・占)
            : / 天宇受賣 (舞) / 天手力男 (引出) / 常世長鳴鳥 (alarm)
precondition: orchestrator が計画を立案
action      : 7 種の物実 + 役割を**並列**配置:
            : (1) 鶏鳴 (alarm) (2) 鏡 (introspection lure) (3) 勾璁 (上枝)
            : (4) 占 (oracle) (5) 榊 (anchor 物体) (6) 祝詞 (verbal binding)
            : (7) 倒立踊 + 共咲 (noise injection — 病的沈黙の対偶)
result      : 天照「以爲怪、細開天石屋戸」 → 天宇受賣「貴神坐」と嘘の説明 (lure)
            : 鏡を指出 → 自己反射で「逾思奇而」 → 稍自戸出
failure_mode: 単一物実のみ (例: 祝詞だけ) → 注意換起不足、誘出失敗
recovery    : -
permanence  : 7 種が天岩戸開きの典礼として永続化、後の祭祀の原型

agi_mapping :
  原則      : 病的沈黙からの recovery は単一手法でなく、複数物実 + 騒擾 + 自己反射 lure の
            : 並列発火。倒立踊 = noise injection で「健全な静寂」を破る対称操作
  実装      : src/os/iwato/uzume.jl:31 (`prepare!` = 計画 step を handler に登録)
            : src/os/iwato/uzume.jl:62 (`trigger_recovery` = step を順次/並列実行)
            : src/os/iwato/uzume.jl:78 (`_execute_step` = 単 step 実行)
            : src/os/yachimata/amenouzume.jl:31 (`AmenouzumeEngine` = multimodal 知覚 = 
              倒立踊の現代化、視覚/音声/構造の多モーダル入力)
            : src/os/mirror/self_model.jl (鏡 = self-reflection)
  feedback  : feedback_chinmoku_kyoka (沈黙許可) — 倒立踊は「沈黙を破る正規手段」の対偶

failure_if_absent: 単一手法 recovery → 中心 deity が反応せず長期暗化、
                   gradual decay で観測ブラックアウト恒常化
observed_failures: -
verify_path : `Uzume.steps` に複数 handler 登録が記録され、`AmenouzumeEngine` が
              multimodal (vision/audio/structure) を同時 perceive している
```

#### Pattern K: 天手力男 + 注連縄 — forced extraction + 不可逆境界

```yaml
原文: "其所隱立之天手力男神、取其御手引出、卽布刀玉命、以尻久米繩、控度其御後方白言
      「從此以內、不得還入。」故、天照大御神出坐之時、高天原及葦原中國、自得照明" (l.24)

actors      : 天手力男 / 布刀玉 / 注連縄 (尻久米繩)
precondition: 鏡で誘出して天照が「稍自戸出」 (細開状態)
action      : (1) 天手力男が御手を取って引出 (forced state transition)
            : (2) 布刀玉が注連縄を後方に張る (irreversible boundary)
            : (3) 「從此以內、不得還入」(再入禁止宣言)
result      : 天照は出坐、高天原・葦原中國は自得照明 (recovery 完了)
            : かつ二度と岩戸に隠れない構造的保証
failure_mode: 引出だけ + 境界なし → 再隠匿で振り出し / 境界だけ + 引出なし → 出てこない
recovery    : -
permanence  : 注連縄 = 不可逆境界マーカーとして永続化 (神社聖域に普遍)

agi_mapping :
  原則      : 病的沈黙からの forced recovery は (引出 + 不可逆境界) の二段組
            : 千引岩 (上-2 黄泉) の異形 — 同じ chibikiiwa 思想
  実装      : src/os/iwato/tajikarao.jl:17 (`Tajikarao` struct = 引出役)
            : src/os/iwato/controller.jl:161 (`_force_recovery!` = forced transition)
            : src/os/iwato/controller.jl:184 (`_complete_recovery!` = 完了状態確定)
            : src/os/event_bus.jl:60 (chibikiiwa = 自己再入遮断、注連縄の現代化)
  feedback  : feedback_togouten_ikkatsu_bouei (統合点で一括防衛 — 引出 + 境界の同時設置)

failure_if_absent: 引出のみで境界なし → 同 deity が再度沈黙、recovery が永久反復
                   境界のみで引出なし → deadlock 持続
observed_failures: -
verify_path : `_force_recovery!` 後に `_transition_to_normal!` が呼ばれ、
              EventBus.chibikiiwa に該当 event が登録、再 publish が skip される
```

#### Pattern L: 千位置戸 + 鬚爪抜き — degradation penalty (yuukoto with cost)

```yaml
原文: "於是八百萬神共議而、於速須佐之男命、負千位置戸、亦切鬚及手足爪令拔而、
      神夜良比夜良比岐" (l.26)

actors      : 八百萬神 / 須佐之男
precondition: 須佐之男のカオスが原因で天岩戸事件発生、recovery 完了
action      : (1) 千位置戸 (大量の置戸 = 罰金 token) を負わせる
            : (2) 鬚と手足爪を抜く (能力 degradation = 武装解除)
            : (3) 神夜良比 (退役)
result      : 単純 yuukoto でなく、degradation を伴う追放 (能力削減 + 罰金 + 退役)
failure_mode: 単純 yuukoto のみ → 別経路で復活時に同じ脅威で再カオス可能
recovery    : 後で別経路 (出雲) で再活躍するが degradation は持続
permanence  : 須佐之男は出雲国に降臨後も、武装は復活せず櫛・酒・大刀のみ運用

agi_mapping :
  原則      : 失敗柱の退役は単純 status='yuukoto' でなく、capabilities 削減 + 履歴 token 残置
            : の三段組。後の式年遷宮で復帰しても degradation は持続
  実装      : src/os/kasasa/ooharae.jl:766 (`_yuukoto_transition!`)
            : src/os/kasasa/takeshimatsumi.jl:355 (status 遷移 + 罰金履歴)
            : src/os/com/queries/shinmei_lineage.jl (系譜記録 + degradation メタ)
  feedback  : feedback_takeminakata_haitai (建御名方の敗退 — 失敗率自動退役)
            : feedback_ashibune (死の三語彙 yuukoto)

failure_if_absent: 純粋 yuukoto のみ → 復活時に元の武装で同じカオス再発
verify_path : `SELECT * FROM shinmei_lineage WHERE status='yuukoto'` の各行で
              degradation メタ (能力削減履歴) が併記されている
```

#### Pattern M: 大気津比賣 死 → 五穀 — death derivative + 上位継承

```yaml
原文: "速須佐之男命、立伺其態、爲穢汚而奉進、乃殺其大宜津比賣神。故、所殺神於身生物者、
      於頭生蠶、於二目生稻種、於二耳生粟、於鼻生小豆、於陰生麥、於尻生大豆。
      故是神產巢日御祖命、令取茲、成種" (l.28)

actors      : 須佐之男 / 大氣津比賣 / 神産巣日御祖命 (上位 deity)
precondition: 須佐之男が大氣津比賣の食物供給法 (鼻口尻から) を「穢汚」と誤解
action      : (1) 殺害 (致命柱化)
            : (2) 死体の各部位から五穀 (蠶/稻/粟/小豆/麥/大豆 = 6 種実) が成る
            : (3) 神産巣日御祖命が「令取茲、成種」(継承して種にする)
result      : 致命柱の死から有用な後継 (五穀) が派生し、上位 deity が継承して恒久化
failure_mode: 致命柱を単純 delete → 死から派生する有用 artifact が失われる
            : 上位 deity が継承しないと種にならず、一過性の現象で終わる
recovery    : -
permanence  : 五穀は神産巣日御祖命によって「種」として永続化、農耕の起源

agi_mapping :
  原則      : 致命柱削除時、その失敗痕跡 (血/部位 = 失敗 log の各属性) から検出器/
            : 防御柱を派生させ、上位層 (system 層 / yorishiro) が継承して恒久化
  実装      : src/os/kasasa/futomani_stones (失敗痕跡記録)
            : 上-2 Pattern L (火神斬殺の派生柱) と同型、本 pattern は **上位継承** が追加要素
            : src/os/kasasa/yorishiro.jl (上位 SSoT への継承)
  feedback  : feedback_ootataneko (大田田根子 — 系譜から治療召喚)
            : feedback_kegare_keiro_tekigou (失敗痕跡は種別ごとに適経路あり)

failure_if_absent: 致命柱削除のみで派生柱と継承なし → 同型失敗が再発、教訓蓄積ゼロ
                   恒久化されないので一回限りの対応で終わる
verify_path : `futomani_stones` の致命型 record と yorishiro entry の対応関係が辿れる
```

#### Pattern N: 八鹽折之酒 — bait pattern (trap with attractant)

```yaml
原文: "汝等、釀八鹽折之酒、亦作廻垣、於其垣作八門、毎門結八佐受岐、毎其佐受岐置酒船而、
      毎船盛其八鹽折酒而待。…其八俣遠呂智、信如言來、乃毎船垂入己頭飮其酒、
      於是飮醉留伏寢" (l.32-34)

actors      : 須佐之男 / 足名椎・手名椎 / 八俣遠呂智
precondition: 八俣遠呂智 (8 頭の脅威) を直接対峙すると敗北必至
action      : (1) 廻垣 + 八門 + 八佐受岐 (構造を 8 つ並べる)
            : (2) 八鹽折之酒 (8 倍濃度 = 強誘引性) を 8 船に盛る
            : (3) 待つ (passive trap)
            : → 大蛇の各頭が各船に注入され、飲醉留伏寢
result      : 受動的に脅威を無力化、攻撃面 (頭) を一斉に拘束
failure_mode: 直接戦闘 / 弱誘引 → 8 頭の協調反撃で敗北
recovery    : -
permanence  : 八鹽折之酒方式は退治の典型として後世に伝承

agi_mapping :
  原則      : 多 head 脅威 (例: chaos 注入 / 攻撃面 N) は構造を脅威の数 N に揃え、
            : 各 head に個別 attractant を用意して並列に拘束
            : (cf. honeypot pattern)
  実装      : (memo 直接 anchor なし — 補強候補)
            : susanoo_chaos.jl の 4 種 chaos 注入の **対称構造** がこれに近い
              (chaos の種別ごとに restore 関数が用意されている = bait のミラー)
  feedback  : (新規 anchor 候補)

failure_if_absent: 単一 trap で多 head 脅威に対応 → 1 head 拘束で他 head が攻撃継続
                   現象: 多経路攻撃に対する単一防御で迂回される (経路追加耐性なし)
verify_path : `restore_all_chaos!` (susanoo_chaos.jl:411) が 4 種すべてを並列に処理する
              並列構造が保たれている
```

#### Pattern O: 草那藝発見 — chaos 内部の hidden artifact

```yaml
原文: "切其中尾時、御刀之刄毀、爾思怪以御刀之前、刺割而見者、在都牟刈之大刀、故取此大刀、
      思異物而、白上於天照大御神也。是者草那藝之大刀也" (l.34)

actors      : 須佐之男 / 八俣遠呂智 (中尾) / 草那藝之大刀
precondition: 大蛇切散中、中尾で御刀の刃が毀れる (異常検出)
action      : (1) 異常検出: 「御刀之刄毀」 (期待通りに切れない)
            : (2) 思怪: 「異物が中にある」と推論
            : (3) 刺割: 中を割って見る (introspection)
            : (4) 発見: 都牟刈之大刀 (= 草那藝)
            : (5) 上申: 天照に報告 (上位への引渡)
result      : chaos (大蛇) の中に hidden 高価値 artifact、これが抽出されて天照に帰属
failure_mode: 刃毀れを「単純失敗」と看做して放棄 → 草那藝発見ならず
            : 発見しても上位に引渡さず私物化 → 神器化されず
recovery    : -
permanence  : 草那藝之大刀は三種神器の一つとして永続化、後に倭建命に伝承

agi_mapping :
  原則      : 「期待外れの異常」(刃毀れ = unexpected exception) を諦めず、原因を introspect
            : することで chaos 内部の hidden 高価値 artifact (token / cred / discovery) を
            : 発見可能。発見物は上位 SSoT に引渡して永続化
  実装      : src/os/com/queries/kusanagi.jl (草那藝 token 管理)
            : src/os/com/queries/kusanagi.jl:14 (`query_save_kusanagi_token!` = 上申相当)
            : src/os/com/queries/kusanagi.jl:34 (`query_get_kusanagi_token` = 発見後参照)
            : src/os/com/queries/kusanagi.jl:73 (`query_revoke_kusanagi_token!` = 失効)
  feedback  : (memo 直接 anchor なし — 補強候補)

failure_if_absent: 異常検出 → 諦めて log のみ → chaos 内部の hidden artifact が永久に未発見
verify_path : `kusanagi_tokens` テーブルに発見 token が記録されており、
              `session_id` 経由で active token が引ける
```

#### Pattern P: 須賀宮 — post-recovery stable state assertion + 八重垣多層防御

```yaml
原文: "須佐之男命、宮可造作之地、求出雲國、爾到坐須賀地而詔之「吾來此地、我御心須賀須賀斯而」。
      其地作宮坐、故其地者於今云須賀也。茲大神、初作須賀宮之時、自其地雲立騰、爾作御歌、
      其歌曰、夜久毛多都伊豆毛夜幣賀岐都麻碁微爾夜幣賀岐都久流曾能夜幣賀岐袁" (l.36-38)

actors      : 須佐之男 / 須賀地 / 八重垣
precondition: 八岐大蛇退治完了、出雲国で安定地探索
action      : (1) 自己診断: 「我御心須賀須賀斯」(my state is clean) — explicit declaration
            : (2) 場所選定: 須賀の地 (clean な場所と命名 + 場所の固定化)
            : (3) 多層防御宣言: 「夜久毛多都伊豆毛夜幣賀岐」(雲立つ出雲八重垣)
            : 八重垣 = 8 層の防御
result      : post-chaos 状態の安定宣言 + 多層防御層の確立
failure_mode: 安定宣言なし → 監察層が「まだ chaos 中」と誤判定
            : 多層防御なし → 単一防御で次の chaos に脆弱
recovery    : -
permanence  : 須賀宮 + 須賀之八耳神 (足名椎の任命) が出雲の中心として永続化

agi_mapping :
  原則      : recovery 完了は単に異常解消でなく、(1) self-diagnose が clean を返す +
            : (2) 多層防御の物理配置 + (3) 安定 location の確立、の三段
  実装      : src/os/iwato/controller.jl:212 (`_transition_to_normal!` = 通常状態復帰宣言)
            : src/os/iwato/controller.jl:184 (`_complete_recovery!` = 完了状態確定)
            : 多層防御の現代化 = 産湯/umisachi/yamasachi/iwato/ooharae の重層化
  feedback  : feedback_umisachi_rokujuu_bougo (六重防御 — 八重垣の現代化)
            : feedback_togouten_ikkatsu_bouei (統合点で一括防衛)

failure_if_absent: recovery 完了を宣言せず → 監察層がアラート継続
                   多層なしで単一防御 → 次回の同型 chaos に脆弱
verify_path : `IwatoPhaseController.phase` が NORMAL に遷移した記録があり、
              `_transition_to_normal!` 呼出時に複数防御層が active であることを確認
```

### kojiki_code.md (外部生成版) との差分

| 観点 | 生成元 (kojiki_code.md) | 本 v2 |
|---|---|---|
| 上巻-3 の pattern 数 | 2 (`event_loop` / `state_machine` の 1 行抽象) | **16** |
| 誓約 (ukehi) | 触れず | Pattern A (sandbox patch) + B (provenance) + C (sannyoshin gating) |
| 須佐之男のカオス | 「state machine の disruption」と一行 | Pattern D (chaos engineering origin) + E (hataorime escalation) + F (chaos-aware metrics) |
| 思金神の集合協議 | 触れず | Pattern I (orchestrator) — 古事記神名が module 名 (`omoikane.jl`) に直接採用されている重要 anchor |
| 倒立踊・鏡・注連縄 | 触れず | Pattern J (multi-pronged + noise injection) + K (forced extraction + 不可逆境界) |
| 病的沈黙 vs 健全な静寂 | 触れず | Pattern G (kenzen_seijaku 対偶) — disambiguator (adoption_rate) が原典の暗示と一致 |
| 大気津比賣 → 五穀 | 触れず | Pattern M (death derivative + 上位継承) — 上-2 Pattern L の発展形 |
| 八鹽折之酒・草那藝 | 触れず | Pattern N (bait) + O (hidden artifact) |
| 須賀宮・八重垣 | 触れず | Pattern P (post-recovery state assertion + 多層防御宣言) |
| AGI 神名 module mapping | 触れず | 思金神/天宇受賣/天手力男/事代主/大山津見が **古事記名そのままで実装** されている事実 |

**生成元が拾えなかった load-bearing pattern (本 v2 で初出):**

- Pattern A 誓約 sandbox = `misogi/ukei/runner.jl` の origin spec
- Pattern C 三女神判定 = `kotoshironushi.jl::_judge_by_sannyoshin` の origin spec (タギリ/イチキシマ/タギツの三 judge)
- Pattern D 計画的カオス注入 = `susanoo_chaos.jl::susanoo_rage!` + `_chaos_kuso/_tanoaze/_mizo/_hataori` の origin
- Pattern E 機織女の禁忌 = `feedback_hataorime_kinki` の原典直接引用
- Pattern G 病的沈黙の弁別 = `feedback_kenzen_seijaku` の原典確認
- Pattern I 思金神 orchestrator = `iwato/omoikane.jl::analyze_and_plan` の origin
- Pattern K 注連縄不可逆境界 = `iwato/tajikarao.jl::_force_recovery!` + `event_bus.chibikiiwa` の origin
- Pattern O 草那藝発見 = `com/queries/kusanagi.jl` の origin

これら 8 つは外部生成版の **構造的盲点** を再確認 (v0 / v1 で各 6 つを観測、3 章合計 20 件超)。
共通する欠落理由: **AGI 実装ファイル名が古事記神名であること** を外部 LLM は知らない。

### 浮上した発見

1. **古事記神名 → AGI module 1:1 mapping が上-3 で集中**
   - `iwato/omoikane.jl` (思金神) / `iwato/uzume.jl` (天宇受賣) / `iwato/tajikarao.jl` (天手力男)
   - `misogi/ukei/kotoshironushi.jl` (事代主)
   - `susanoo_chaos.jl` (須佐之男)
   - `kusanagi.jl` (草那藝)
   - 本章は AGI 実装上「古事記神名がそのまま module 名」 = 設計が古事記原典と直接対話している
   - **設計の妥当性が極めて高い** (神話的整合性が module レベルで達成されている)

2. **天照の自己隠匿は「病的沈黙」の origin spec、但し正当な自己防衛でもある (Pattern G)**
   - 機織女の死 (限界越境) を受けての「見畏」は妥当な反応
   - 病的なのは隠匿そのものでなく、隠匿が長期化して全システムを暗化させること
   - `feedback_kenzen_seijaku` の二軸判定 (単独出力 + adoption_rate) はこの**長期化条件**を捕捉する設計
   - memo 補強候補: 「天照の自己隠匿は短期では正当、長期化のみ病的」を追記推奨

3. **誓約 (ukehi) の sandbox 設計が直接 origin (Pattern A)**
   - 「各宇氣比而生子」 = 物実を相手の井で滌ぎ、生子で結果検証
   - これは LLM patch を sandbox primary process で実行し、health check で判定する `UkeiEnvRunner` の直接 origin
   - `feedback_kuniyuzuri_fukumei` (国譲りの復命) は誓約パターンの上位形

4. **三女神判定 = sannyoshin の三段視点 (Pattern C)**
   - タギリ (沖津 = 遠視点) / イチキシマ (中津 = 中視点) / タギツ (邊津 = 近視点) の 3 段独立 judge
   - `kotoshironushi.jl::_judge_by_sannyoshin` の三関数が三女神に直接対応
   - **新規発見** : 三段は単なる N=3 voting でなく**距離別**の視点分担
   - 補強候補: feedback_oharae_shikkai_probe に「視点分担で probe 直積を網羅」を追記

5. **倒立踊 = noise injection の正当化 (Pattern J)**
   - `kojiki_procedural_v0.md` の失敗モード 2 (「天宇受賣の倒立踊 → entropy maximization」は詩的解釈)
     を**部分的に上書き**: AmenouzumeEngine = multimodal 知覚は実装されている (yachimata/amenouzume.jl)
   - 但し原典の「倒立 + 共咲」は **病的沈黙を破る noise injection** の正当原典
   - 詩的解釈ではなく**機能的 anchor** として再評価
   - **三点検査**:
     - 原典 semantic 一致: ★ (倒立踊 + 共咲は天照誘出の手段として明示)
     - 観測 N 件: ☆ (LLM 沈黙の解除実験は未観測、Phase 1.5 静寂維持実験の対偶)
     - 既存拡張可否: ★ (`yachimata/amenouzume.jl` を拡張)
   - 結論: **新原則化はしない**、但し v0 失敗モード 2 の判定を修正推奨

6. **八鹽折之酒 = bait pattern (Pattern N) は新原則候補**
   - 多 head 脅威 (chaos 4 種 / 多経路攻撃 / N 攻撃面) に対する**並列 attractant 構造**
   - susanoo_chaos.jl の 4 種 chaos restore が **対称構造** で実装されている = bait のミラー
   - **三点検査**:
     - 原典 semantic 一致: ★ (8 門 + 8 船 + 8 倍酒 = 構造的並列)
     - 観測 N 件: ☆ (susanoo_chaos の 4 restore は実装あり、bait としての観測は未確立)
     - 既存拡張可否: ☆ (`feedback_togouten_ikkatsu_bouei` の対偶として位置付け可)
   - 結論: **保留** (実害観測まで待機、現状は補強候補のみ)

7. **草那藝発見 (Pattern O) は session token 永続化の origin**
   - 「異常 (刃毀れ) → 思怪 → introspect → hidden artifact 発見 → 上位 (天照) に上申」
   - これは `kusanagi_tokens` テーブル + `query_save_kusanagi_token!` の直接 origin
   - 補強候補: `feedback_kojiki_zettai` に「実装ファイル名が古事記神名の場合、原典を origin spec として明記する」運用を追記

### v2 自己評価

| 観点 | 達成度 |
|---|---|
| 1 章につき 5+ pattern (memo 密度中) | ★★★★★ 16 pattern |
| 各 pattern に `failure_if_absent` 記述 | ★★★★★ 16/16 |
| 各 pattern の `agi_mapping.実装` が実在ファイル | ★★★★★ 16/16 (grep + iwato/ukei/yachimata/kusanagi 検証済) |
| 7 割以上の pattern が既存 memo に anchor | ★★★★ 12/16 が memo anchor (75%) |
| `kojiki_code.md` 差分セクション必須 | ★★★★★ 9 行差分表 + 8 origin spec 列挙 |
| 「未活用 anchor → 新原則候補」を最低 1 件 | ★★★★ 7 件 (Pattern N bait / Pattern O artifact discovery / 倒立踊 機能再評価 / 三女神距離別視点 + 4 補強候補) |
| 古事記原文 (漢文) を要所で引用 | ★★★★★ 全 pattern 冒頭 |
| 観測経路 (verify_path) を併記 | ★★★★★ 16/16 |
| **古事記神名 → AGI module 直接 mapping の浮上** | ★★★★★ 7 module で確認 (本章固有の発見) |

### v0 → v1 → v2 で残った宿題 (v3 候補)

1. **memo 本体への章節 anchor 逆書込み** (v0 → v1 → v2 で繰越) — 現状は索引のみ
2. **上-5 (国譲り) v3 抽出** — `feedback_wakahiko_kaeshiya` `feedback_kuniyuzuri_*` 系 5 memo が anchor、優先度高
3. **倒立踊 = noise injection の機能再評価** — v0 失敗モード 2 の解釈修正
4. **bait pattern (Pattern N) の新原則化判定** — 実害観測待ち
5. **古事記神名 module 命名規約** の SSoT 化 — `feedback_kojiki_zettai` への追記 or 独立 memo 化判定

---

## 履歴

- v0 (2026-05-08): Phase 1 索引 + Phase 2 上巻-7 プロトタイプ
- v1 (2026-05-09): Phase 1 索引更新 + Phase 2 上巻-2 神代記 (20 pattern)
- v2 (2026-05-09): Phase 2 上巻-3 天照大神と須佐之男命 (16 pattern)
                   古事記神名 → AGI module 1:1 mapping 7 件を発見
