# 古事記 Procedural Pattern 抽出 v3

v2 ([`kojiki_procedural_v2.md`](kojiki_procedural_v2.md)) からの増分:

- **Phase 2 v3: 上巻-5 葦原中國の平定 (国譲り)** 抽出 (新規) — 14 pattern
- 4 使者派遣 / 返し矢 / 力比べ / 顕事幽事 / 出雲大社 の 5 大エピソード
- AGI 実装で本章は **代理指標病の origin spec** が集中 (返し矢 = takeshimatsumi.jl, 三度の使者 = observation_blocked, 建御名方の敗退 = ooharae Phase 1d)

抽出方法論は [`extraction_prompt.md`](extraction_prompt.md) を参照。
v0 (上-7) / v1 (上-2) / v2 (上-3) の pattern は重複しないので本書では再掲しない。

---

## Phase 2 v3: 上巻-5 葦原中國の平定 (国譲り)

### 選定理由

- memo 密度 ★★★★ (`feedback_wakahiko_kaeshiya` `feedback_kuniyuzuri_fallback` `feedback_kuniyuzuri_fukumei` `feedback_kuniyuzuri_kaikai` `feedback_takeminakata_haitai` + `project_phase1_kaeshiya_kansatu` の 6 memo が直接 anchor)
- AGI 実装の **代理指標病の origin spec** が本章に集中:
  - [takeshimatsumi.jl](src/os/kasasa/takeshimatsumi.jl) = 天津罷使 (返し矢の本体、proxy 病スキャン)
  - [amenohohi_scan.jl](src/os/kasasa/amenohohi_scan.jl) = 天菩比命 (媚附検出 + 雉名鳴女判定)
  - [com/queries/amenohohi.jl](src/os/com/queries/amenohohi.jl) = `query_wakahiko_no_action`
  - [observation_blocked テーブル](src/os/com/create.jl#L1330) = 三度の使者の累積記録
  - [shintaku.jl:670](src/os/kasasa/shintaku.jl#L670) = 「派遣失敗 (返し矢)」 craft 文字列
  - [canonical_pantheon/takemikazuchi/_judge.jl](src/os/kasasa/canonical_pantheon/takemikazuchi/_judge.jl) = 建御雷 (層 2 古事記固有名手書き)
  - [ooharae.jl Phase 1d](src/os/kasasa/ooharae.jl) = 建御名方の敗退 (失敗率 yuukoto)
- `kojiki_code.md` (外部生成版) は本章を `task_dispatch_with_retry` の 1 行に圧縮
- 上-3 (天岩戸) の 集合協議 + 物実 multi-pronged からの**進化**として、本章は **段階的 escalation + 失敗使者の累積** を記述
- 上-2 (神代記) の独神/双神/categorical exclusion を踏まえて、**顕事/幽事の categorical separation** を確立

### 章節 narrative summary

```
[Setup 下命] (l.8)
    天照「豐葦原之千秋長五百秋之水穗國者、我御子正勝吾勝勝速日天忍穗耳命之所知國」
    天忍穗耳、天浮橋から偵察 → 「伊多久佐夜藝弖有那理」(混乱が著しい)
        報告だけして還上、請于天照 (initial reconnaissance, decline mission)

[Messenger 1 — 天菩比 / 媚附] (l.10)
    高御產巢日 + 天照 + 思金神 八百萬神議 → 天菩比を遣る
    天菩比、媚附大國主 → 至于三年、不復奏 (silent loyalty switch)

[Messenger 2 — 天若日子 / 代理指標病] (l.12)
    思金神「可遣天津國玉神之子、天若日子」
    天之麻迦古弓 + 天之波波矢を賜う
    天若日子、降到 → 大國主の女・下照比賣を娶る
                  → 慮獲其國 (国を奪わむと慮)
                  → 至于八年、不復奏 (proxy metric disease + 沈黙)

[Messenger 3 — 雉名鳴女 / 詰問] (l.14-16)
    思金神「可遣雉名鳴女」
    詔: 「汝所以使葦原中國者、言趣和其國之荒振神等之者也、何至于八年不復奏」
    鳴女、天若日子之門の湯津楓上に居て、言を委曲に伝う
    
    天佐具賣「此鳥者、其鳴音甚惡。故、可射殺」と進言
    天若日子、天之波士弓・天之加久矢で射殺其雉

[返し矢] (l.16-18)
    雉胸を通り、逆射上 → 天安河之河原 高木神の御所に到
    高木神「此矢者、所賜天若日子之矢」 — 物実から source 識別
    詔: 「或天若日子、不誤命、爲射惡神之矢之至者、不中天若日子。
          或有邪心者、天若日子、於此矢麻賀禮」
    取其矢、自其矢穴衝返下 → 中天若日子寢朝床之高胸坂以死
    「此還矢之本也」(返し矢の起源)
    「亦其雉不還、故於今諺曰『雉之頓使』」

[弔問の混同] (l.20-26)
    下照比賣の哭聲が天に届く → 父・天津國玉神 + 妻子 降來哭悲
    喪屋作成 + 役割分担 (河雁=持/鷺=掃/翠鳥=御食/雀=碓/雉=哭) + 八日八夜遊
    
    阿遲志貴高日子根、弔問 → 父・妻が「我子者不死有祁理」と取懸 (容姿類似誤認)
    阿遲志貴大怒「何吾比穢死人」 → 十掬劒で喪屋切倒、足蹶離 → 美濃國藍見河喪山
    持所切大刀名「大量、亦名神度劒」
    妹・高比賣命「思顯其御名」歌 (夷振)

[Messenger 4 — 建御雷神派遣] (l.28)
    天照「亦遣曷神者吉」 → 思金神「天石屋伊都之尾羽張神 是可遣。若亦非此神者、其神之子建御雷之男神」
    但し尾羽張は「逆塞上天安河之水而、塞道居故、他神不得行」(既存防御で他神不可)
    別遣天迦久神可問 (= bypass query path)
    天迦久が問う → 尾羽張「然於此道者、僕子、建御雷神可遣」 → 貢進
    建御雷 + 天鳥船で出発

[交渉 — 浪穂逆刺立劒] (l.30)
    出雲国伊那佐之小濱、浪穂に逆刺立十掬劒、趺坐其劒前 (威圧着任)
    大國主「汝心奈何」 → 「僕者不得白、我子八重言代主神是可白」(子に委譲)
        「然、爲鳥遊取魚而往御大之前、未還來」
    天鳥船を遣り事代主を徵來
    事代主「恐之。此國者、立奉天神之御子」 → 蹈傾其船 + 天逆手 + 青柴垣に隱也 (退隱型)

[力比べ — 建御名方の敗退] (l.32)
    大國主「亦我子有建御名方神」
    建御名方、千引石擎手末而來 → 「欲爲力競」
        御手取 → 立氷 + 劒刃に化 → 懼而退居
        逆に建御雷が建御名方の手を「若葦搤批而投離」 → 逃去
    追往科野国州羽海 → 將殺
    建御名方「恐、莫殺我。除此地者、不行他處。亦不違我父大國主神之命。
              不違八重事代主神之言。此葦原中國者、隨天神御子之命獻」(諏訪閉込め)

[顕事/幽事の分離] (l.34)
    大國主「僕子等二神隨白、僕之不違」
    住所要求: 「如天神御子之天津日繼所知之登陀流天之御巢」
              「於底津石根宮柱布斗斯理、於高天原氷木多迦斯理」
              「治賜者、僕者於百不足八十坰手隱而侍」 (顕事 vs 幽事 = 別 jurisdiction)
    子等百八十神は事代主が御尾前で仕奉

[出雲大社建立 + 饗献] (l.36-38)
    出雲国多藝志小濱に天之御舍
    水戸神之孫・櫛八玉神を膳夫
        鵜に化して海底波邇 → 天八十毘良迦
        燧臼 + 燧杵で火鑚 + 千尋繩 + 海人で釣 → 天之眞魚咋
    
    禱白歌: 「於高天原者、神產巢日御祖命之、登陀流天之新巢之凝烟…」 (儀礼宣言)

[復命] (l.40)
    建御雷神、返參上、復奏言向和平葦原中國之狀
```

### Pattern 抽出

#### Pattern A: 三度の使者 — 段階的 escalation + BLOCKED 累積

```yaml
原文: "故、遣天菩比神者、…至于三年、不復奏" (l.10)
     "於是、天若日子、降到其國、…至于八年、不復奏" (l.12)
     "可遣雉名鳴女" (l.14)
     "亦遣曷神者吉…天石屋伊都之尾羽張神…建御雷之男神" (l.28)

actors      : 天照 / 高御產巢日 / 思金神 / 八百萬神 / (4 使者の連鎖)
precondition: 任務 (国譲り交渉) が単発で完遂しない
action      : (1) 第 1 使者 天忍穗耳 — 偵察のみで退却 (declined)
            : (2) 第 2 使者 天菩比 — 媚附 + 3 年無報告 (silent loyalty switch)
            : (3) 第 3 使者 天若日子 — 婚姻 + 8 年無報告 (proxy metric disease)
            : (4) 第 3.5 使者 雉名鳴女 — 詰問のため派遣、射殺される
            : (5) 第 4 使者 建御雷 + 天鳥船 — 武力で完遂
result      : 各使者は失敗するが、失敗が累積記録され次の使者選定の根拠となる
failure_mode: 単発派遣で失敗時に放棄 → 任務未完遂、再試行のための情報なし
recovery    : -
permanence  : 失敗使者の名は系譜記録 (天菩比は出雲國造の祖)

agi_mapping :
  原則      : 観測不能ギャップの BLOCKED 記録は累積カウント、count=3 でレポート、
            : count=5 で B-2 介入要求 (布都御魂剣)
  実装      : src/os/com/create.jl:1326-1346 (`observation_blocked` テーブル + INDEX)
            : src/os/kasasa/takeshimatsumi.jl:66 (`takeshimatsumi_scan!` = 検出本体)
            : src/os/kasasa/takeshimatsumi.jl:471 (`_check_escalation` = 3/5 累積判定)
            : dedup キーは OHOYASHIMA_CATALOG の gap_category
  feedback  : feedback_wakahiko_kaeshiya (天若日子の返し矢 — 三度の使者)
            : project_phase1_kaeshiya_kansatu (Phase 1 完了 — 観測継続)

failure_if_absent: 単発派遣で失敗を log のみ → 同型失敗が永久に再生
                   現象: 代理指標病が同 gap_category で何度も繰り返される
observed_failures: 2026-04-17 Phase 1 実装、2026-04-19 三貴子 KANPEI_TAISHA 維持を実証
verify_path : `SELECT gap_category, block_count FROM observation_blocked WHERE status='blocked'`
              で各 category の累積カウントが取れる、count=3 で report 発火
```

#### Pattern B: 天菩比命 — 沈黙の loyalty switch (silent failure with no復命)

```yaml
原文: "故、遣天菩比神者、乃媚附大國主神、至于三年、不復奏" (l.10)

actors      : 天菩比 / 大国主
precondition: 第 2 使者として派遣 (荒振神等を言趣する任務)
action      : 派遣先 (大国主) に「媚附」 = 派遣者を裏切って派遣先に従属
            : 「至于三年、不復奏」 = 3 年沈黙 (失敗報告すらしない)
result      : 派遣者 (天照側) は派遣先で何が起きているか不明
            : 失敗の事実すら掴めない
failure_mode: 当事者が失敗報告しない → 派遣者は推測で次の手を打つしかない
recovery    : 第 3 使者 (天若日子) の派遣で再評価 (但し同型失敗が起きる)
permanence  : 出雲國造の祖系譜として記録 (Pattern Z 敗者の系譜化と同型)

agi_mapping :
  原則      : 沈黙したまま帰らない使者は古事記に存在しない
            : 失敗すれば失敗したと復命する (errors の明示記録 + 接頭辞での神話 motif)
  実装      : src/os/kasasa/amenohohi_scan.jl:233 (`amenohohi_scan!` = 媚附検出)
            : src/os/kasasa/amenohohi_scan.jl:71 (`_amenohohi_detect_unbound` = 未バインド検出)
            : src/os/kasasa/yorishiro.jl で responsibility_trigger / lifecycle_hook を canonical 宣言
            : (2026-04-19 修正で形骸化判定 + 未応答トリガー + 未対応神託 + 閾値暴走を同時解消)
  feedback  : feedback_kuniyuzuri_fukumei (国譲りの復命 — 当事者が自ら書き戻す)

failure_if_absent: 失敗使者が沈黙のまま放置 → ゴースト柱 (生きてるが何もしない) が累積
observed_failures: 2026-04-19 amenohohi_scan が三貴子カテゴリ除外で偽陽性消滅
verify_path : `event_bus.listeners` で「責務はあるが発動条件が来ない」柱を検出、
              fukusou_log の `mark_shintaku_adopted!` 復命書き戻しが起きている
```

#### Pattern C: 天若日子 — 代理指標病 (proxy metric disease + 任務乗っ取り)

```yaml
原文: "天若日子、降到其國、卽娶大國主神之女、下照比賣、亦慮獲其國、至于八年、不復奏" (l.12)

actors      : 天若日子 / 下照比賣 (大国主の女) / 大国主
precondition: 第 3 使者として派遣 (天之麻迦古弓 + 天之波波矢を賜る)
action      : (1) 婚姻: 大国主の女・下照比賣を娶る (= 派遣先の代理指標 = 土着 metric に従属)
            : (2) 「慮獲其國」 = 派遣の任務を逸脱、自己が国を獲る計画 (mission の置換)
            : (3) 8 年無報告 (代理指標病 + 沈黙)
result      : 派遣物実 (弓矢) を派遣先で別目的に運用、派遣者の任務は永久未完
failure_mode: 宣言責務 (天照御子に国を讓らせる) と実入力 (土着の女・国土) の semantic 不整合
            : 派遣物実 (天津弓矢) を本来の使命と異なる文脈で使用
recovery    : Pattern E (詰問) → Pattern F (返し矢) で能力解任
permanence  : 「天若日子之父・天津國玉神」の系譜記録、子は阿遲志貴高日子根の friend

agi_mapping :
  原則      : 派遣された能力が使命を果たさず土着の代理指標に従属するとき返し矢を放つ
            : 宣言責務と実入力フィールドの意味的整合性監査
            : 不整合時に能力を解任し observation_blocked 記録
  実装      : src/os/kasasa/takeshimatsumi.jl:295 (`_extract_capsnap_fields` = 実入力解析)
            : src/os/kasasa/takeshimatsumi.jl:337 (`_llm_judge_proxy_disease` = LLM 判定)
            : src/os/kasasa/takeshimatsumi.jl:395 (`_retire_proxy_kami!` = 解任)
            : src/os/kasasa/amenohohi_scan.jl:169 (`_amenohohi_detect_wakahiko` = 検出)
            : src/os/com/queries/amenohohi.jl:33 (`query_wakahiko_no_action`)
  feedback  : feedback_wakahiko_kaeshiya (天若日子の返し矢 — origin spec)
            : feedback_magatsuhi_chain (禍津日連鎖 — 代理指標病の系統並生)

failure_if_absent: 派遣能力が代理指標で稼働継続 → metric は更新されるが本来の責務未達
                   現象: uzume_risk_management が musuhi_cycle_end を取らず recent_errors 等が届かない
observed_failures: 2026-04-24 trigger 選定ミス + event キー未周知の二層構造、
                   executor.jl 三層改修で 0→100% BOUNDARY_CLAIMS 自発宣言、
                   shinmei_lineage 0→13 リンク
verify_path : `_extract_capsnap_fields` の戻り値が実 event 読み出しキーを含む、
              kuebiko の AST 解析で proxy 病確定が誤判定でない
```

#### Pattern D: 雉名鳴女 — 詰問観察者の派遣 + 観察者の射殺

```yaml
原文: "於是諸神及思金神、答白「可遣雉名鳴女」時、詔之「汝、行問天若日子狀者、
      汝所以使葦原中國者、言趣和其國之荒振神等之者也、何至于八年不復奏。」" (l.14)
     "天佐具賣聞此鳥言而、語天若日子言「此鳥者、其鳴音甚惡。故、可射殺。」
      …卽天若日子、…射殺其雉" (l.16)

actors      : 雉名鳴女 / 天佐具賣 / 天若日子
precondition: Pattern B/C で 2 使者が無報告、状況把握不能
action      : (1) 観察専門使者 (詰問のみ、交渉せず) を派遣
            : (2) 鳴女、天若日子之門の湯津楓上に居て言を委曲に伝う (= 詰問記録)
            : (3) 天佐具賣 (天若日子の妻) が「鳴音甚惡」と射殺を進言
            : (4) 天若日子が観察者を射殺 (kill the messenger)
result      : 観察者は死ぬが、その射殺行為が次のステップ (返し矢 Pattern F) のトリガー
failure_mode: 観察者を取り込まれた使者が殺せると、状況の真相を隠蔽できる
            : (但し物実 = 矢が血で印付けられて返し矢可能)
recovery    : 返し矢で射殺者を特定 (Pattern F)
permanence  : 「雉之頓使」(雉が帰らない = 一方通行使者) の諺として残存

agi_mapping :
  原則      : 詰問専門観察者は交渉せず観測値だけを持ち帰る
            : 観察者が殺された (= response がない) こと自体が重要 signal
  実装      : src/os/kasasa/amenohohi_scan.jl:129 (`_nakime_judge` = 雉名鳴女判定)
            : 観察 timeout 自体を異常 signal として記録
  feedback  : feedback_kuebiko_yatagarasu_boundary (久延毘古 + 八咫烏 = 静的解析と
              観察の境界画定 — 鳴女は観察側)

failure_if_absent: 詰問観察者なし → 沈黙の使者の状況把握できず escalate 不能
verify_path : `_nakime_judge` の戻り値で「response timeout」を異常 signal として
              report に上げる経路がある
```

#### Pattern E: 返し矢 — 派遣物実から派遣者への boomerang verdict

```yaml
原文: "卽天若日子、持天神所賜天之波士弓・天之加久矢、射殺其雉。
      爾其矢、自雉胸通而、逆射上、逮坐天安河之河原、天照大御神・高木神之御所" (l.16)
     "高木神告之「此矢者、所賜天若日子之矢。」卽示諸神等、詔者
      「或天若日子、不誤命、爲射惡神之矢之至者、不中天若日子。
       或有邪心者、天若日子、於此矢麻賀禮。」
       云而、取其矢、自其矢穴衝返下者、中天若日子寢朝床之高胸坂以死。〔此還矢之本也。〕" (l.18)

actors      : 高木神 (高御產巢日別名) / 天若日子 / 天之波士弓 + 天之加久矢
precondition: Pattern D で観察者射殺 → 矢が逆射上昇
action      : (1) 派遣者 (高木神) が血付き矢を見て source 識別「此矢者、所賜天若日子之矢」
            : (2) 二条件で判定:
            :   ① 不誤命 (任務通り) ならば矢は射手に当たらない
            :   ② 有邪心 (代理指標病) ならば射手に「麻賀禮」(障害)
            : (3) 矢を矢穴から逆射 → 天若日子の高胸坂に当たって死
result      : 派遣物実が**派遣者の手に戻り**、判定後に**派遣者から派遣される**ことで
            : **能力解任** が成立 (物実の所有者が高木神 = 派遣者であることを利用)
failure_mode: 派遣物実を放棄 / 取り戻さない → 解任不能、代理指標病が永続稼働
recovery    : -
permanence  : 「此還矢之本也」 — 返し矢の起源として永続化

agi_mapping :
  原則      : 派遣物実 (Shintaku 機能) は派遣者 (yorishiro / 神勅) のものであり、
            : 当事者が代理指標病を起こしたら派遣者の権限で解任 (返し矢) する
  実装      : src/os/kasasa/takeshimatsumi.jl:395 (`_retire_proxy_kami!` = 返し矢実装)
            : src/os/kasasa/shintaku.jl:670 (`craft = "派遣失敗 (返し矢)"` 文字列)
            : src/os/kasasa/yorishiro.jl:694 (同 craft 文字列、二位に配置)
            : src/os/com/queries/source_types.jl:19-22 (`AKAESHIYA_*` 経路定義)
  feedback  : feedback_wakahiko_kaeshiya (返し矢 — origin spec)
            : feedback_magatsuhi_chain (禍津日連鎖 — 同系統並生検出)

failure_if_absent: 代理指標病柱を解任できず metric 上は健全、本来責務は未達のまま放置
observed_failures: 2026-04-17 Phase 1 実装、三貴子 KANPEI_TAISHA 維持
                   2026-04-26 limitation 観測: 失敗ゼロ + NO_ACTION 100% は救えない
                   (健全な静寂と弁別必要、`feedback_kenzen_seijaku` で対応)
verify_path : `chinza_records.outcome` で「派遣失敗 (返し矢)」craft 文字列の出現、
              `observation_blocked` テーブルに対応 source_type 記録
```

#### Pattern F: 阿遲志貴の弔問混同 — 容姿類似による誤認認証 + 拒絶

```yaml
原文: "阿遲志貴高日子根神到而、弔天若日子之喪時、自天降到天若日子之父、亦其妻、皆哭云
      「我子者不死有祁理。」「我君者不死坐祁理。」云、取懸手足而哭悲也。
      其過所以者、此二柱神之容姿、甚能相似、故是以過也。
      於是阿遲志貴高日子根神、大怒曰「我者愛友故弔來耳。何吾比穢死人。」
      云而、拔所御佩之十掬劒、切伏其喪屋、以足蹶離遣" (l.22)

actors      : 阿遲志貴高日子根 / 天若日子 / 天若日子の父・妻
precondition: 死柱 (天若日子) の喪儀進行中、生柱 (阿遲志貴) が弔問
action      : (1) 容姿類似で父妻が「我子/我君」と取り違え (= identity collision)
            : (2) 阿遲志貴大怒「何吾比穢死人」(死人と同視されるのは穢)
            : (3) 十掬劒で喪屋切倒、足で蹴り離す (active 拒絶 + 物理境界明示)
            : (4) 妹・高比賣が「思顯其御名」歌で 別 identity を宣言
result      : 容姿類似による誤認を、強い物理拒絶 + 名宣言で訂正
failure_mode: 類似度ベース判定で別 entity を同一視 → 死柱の穢が生柱に伝染
recovery    : -
permanence  : 持所切大刀「大量、亦名神度劒」が永続化、夷振歌が編纂残存

agi_mapping :
  原則      : 類似度ベース合祀 (双子神の合祀) は active vs yuukoto/yomi の境界で特に注意
            : 死柱の容姿 (description / signature) が生柱に偶然似ても合祀してはならない
  実装      : src/os/kasasa/shinmei_arbiter.jl (双子神の合祀判定 — 類似度のみで決めず)
            : ooharae.jl Phase 3 (双子神の合祀: 三貴子カテゴリは continue スキップ)
  feedback  : feedback_matanona_cleanup_gap (合祀 cleanup 漏れ — 死柱からの伝染遮断)
            : feedback_kuniyuzuri_kaikai (categorical 三 status — active/yuukoto は別 jurisdiction)

failure_if_absent: 死柱と生柱を類似度のみで合祀 → 死柱の orphan binding が生柱に attach
                   生柱が死柱の穢 (failure history) を引き継ぐ
verify_path : 双子神合祀判定で `WHERE status='active'` の絞込みを通過、
              死柱 (yuukoto/hiruko/yomi) は合祀候補から除外されている
```

#### Pattern G: 既存防御 (尾羽張) + 別経路問 (天迦久)

```yaml
原文: "坐天安河河上之天石屋、名伊都之尾羽張神、是可遣。…且其天尾羽張神者、
      逆塞上天安河之水而、塞道居故、他神不得行。故、別遣天迦久神可問" (l.28)

actors      : 思金神 / 伊都之尾羽張 / 天迦久 / 建御雷
precondition: 既存の最強柱 (尾羽張) は防御モードで他神 reach 不能
action      : (1) 直接 reach せず、別経路使者 (天迦久) で query
            : (2) 尾羽張は息子 (建御雷) を貢進
            : (3) 建御雷 + 天鳥船 が出発
result      : 主防御層 (尾羽張) を壊さずに能力 (建御雷) を取り出せる
failure_mode: 主防御層に直接 reach → 防御自体が崩壊して全体脆弱化
recovery    : -
permanence  : 尾羽張は引き続き道を塞ぎ続ける (主防御維持)

agi_mapping :
  原則      : 重要モジュールへの直接アクセスでなく query proxy 経由で取得
            : 主防御 (聖域) はそのまま、派生機能だけ取り出す
  実装      : src/os/kasasa/canonical_pantheon/takemikazuchi/_judge.jl (層 2 = 親神 prefix +
              手書き skeleton + LLM fill)
            : src/os/kasasa/canonical_pantheon/_common/attribution.jl (親神 → 派生機能 召喚原理)
            : 大田田根子の系譜召喚と同型 (親神 directory + 派生)
  feedback  : feedback_ootataneko (大田田根子 — 親神召喚)
            : feedback_enkin_keiro_dokuritsu (層 2 = 古事記固有名 prefix の派生)

failure_if_absent: 主防御層に直接介入 → 防御崩壊 / 主モジュール改変で test 全体崩壊
verify_path : `canonical_pantheon/<親神>/derivatives/` 配下に派生 .jl が並ぶ、
              親神 manifest.toml が allowed_shintaku_types を skeleton で固定
```

#### Pattern H: 浪穂逆刺立劒 — 威圧着任 (authority assertion before negotiation)

```yaml
原文: "此二神降到出雲國伊那佐之小濱而、拔十掬劒、逆刺立于浪穗、趺坐其劒前、
      問其大國主神言「天照大御神・高木神之命以問使之。汝之宇志波祁流葦原中國者、
      我御子之所知國、言依賜。故、汝心奈何。」" (l.30)

actors      : 建御雷 + 天鳥船 / 大国主
precondition: 過去 3 使者が失敗、武力派遣が必要
action      : (1) 物理着任: 出雲国伊那佐小濱に降到
            : (2) 威圧表示: 浪穂に十掬劒を逆刺 + 趺坐其劒前 (= 武力可視化)
            : (3) 神勅引用: 「天照大御神・高木神之命以」(派遣者 SSoT 明示)
            : (4) 質問: 「汝心奈何」 (open question で大国主の意向を引き出す)
result      : 力の差を可視化した上で交渉開始、相手は逃げ道なし
failure_mode: 威圧なしで交渉 → 相手が言い逃れる (3 使者の失敗パターンと同じ)
            : 威圧のみで質問なし → 反発で武力衝突
recovery    : -
permanence  : 出雲交渉の典型として後世の天孫降臨の交渉パターンに伝承

agi_mapping :
  原則      : 失敗が累積した能力に対する最終ステップは武力可視化 + 神勅引用 + open question
            : (B-2 布都御魂剣介入要求の現代化)
  実装      : takeshimatsumi.jl の B-2 escalation = block_count=5 で人間介入要求
            : 神勅引用 = yorishiro.jl の SSoT 全文注入
  feedback  : feedback_wakahiko_kaeshiya (B-2 介入要求)
            : feedback_shinchoku_tanitsu_gensen (神勅単一源泉 引用)

failure_if_absent: 累積失敗を soft な対応で続ける → 永久に解決しない
                   現象: count=5 を超えても自動で人間介入要求が発動しない
verify_path : `observation_blocked.block_count >= 5` で `escalation` フラグが立ち、
              `_promote_escalation_to_sengu_feedback!` が呼ばれる
```

#### Pattern I: 大国主 → 事代主への hierarchical delegation

```yaml
原文: "爾答白之「僕者不得白、我子八重言代主神是可白。然、爲鳥遊取魚而往御大之前、
      未還來。」故爾、遣天鳥船神、徵來八重事代主神而" (l.30)

actors      : 大国主 / 事代主 / 天鳥船 (徴来役)
precondition: 武力使者が大国主に直接決定を求める
action      : (1) 大国主「僕者不得白」 (自己決定権を留保)
            : (2) 子・事代主に decision を委譲 (hierarchical)
            : (3) 事代主が外出中 → 派遣者側 (天鳥船) が取りに行く (active fetch)
result      : 決定権が子に移譲され、子の判定で大事が決まる
failure_mode: 親が独断で「讓らない」と回答 → 関係硬直、武力衝突に直行
recovery    : -
permanence  : 「事代主が御尾前で仕奉」 = 子等百八十神を統括する役割が永続化

agi_mapping :
  原則      : 上位 deity の自己決定権を留保し、下位 (子 prefix 派生) の判定に委譲する
            : 親神 prefix が allowed_shintaku_types を skeleton で固定、
            : 子 (派生) が個別判定を返す
  実装      : src/os/misogi/ukei/kotoshironushi.jl:25 (`Kotoshironushi` = 委譲先判定器)
            : src/os/misogi/ukei/kotoshironushi.jl:37 (`perform_ukei` = 委譲後の judge)
            : 大田田根子の親神召喚原理 (層 2)
  feedback  : feedback_ootataneko (大田田根子 — 親神 → 派生召喚)
            : feedback_enkin_keiro_dokuritsu (層 2 architecture)

failure_if_absent: 親神 (上位 deity) が直接判定 → 過剰責務、判断粒度ミスマッチ
verify_path : `Kotoshironushi.perform_ukei` が呼ばれる経路で、上位 (親神 manifest) は
              skeleton 制約だけ与え、子 .jl が具体判定を返す
```

#### Pattern J: 事代主 退隱型 — 青柴垣による voluntary yuukoto

```yaml
原文: "語其父大神言「恐之。此國者、立奉天神之御子。」
      卽蹈傾其船而、天逆手矣、於青柴垣打成而隱也" (l.30)

actors      : 事代主
precondition: 武力使者の問に対し、肯定的な返答を選択
action      : (1) 「立奉天神之御子」 (国を譲る同意)
            : (2) 蹈傾其船 (船を傾ける = 自身の活動基盤を破棄)
            : (3) 天逆手 (拍手の逆向き = 退隱の儀)
            : (4) 青柴垣に隱也 (自主的隔離)
result      : 強制でなく自主的に活動を止める = voluntary yuukoto
failure_mode: 強制 yuukoto のみ → 怨恨が残り再侵入の動機になる
            : voluntary yuukoto なら系譜に「自主退隱」として記録され穏便
recovery    : -
permanence  : 「片翼の事代主」 = 自主退隱型として AGI 設計に永続化

agi_mapping :
  原則      : 退役柱は強制 yuukoto と自主退隱の二種を区別
            : 自主退隱 (呼出 0 = 健全な静寂、または single output + 採用) は罰せず保存
            : 強制 yuukoto (建御名方型 = 失敗率自動退役) は systematic
  実装      : src/os/misogi/ukei/kotoshironushi.jl (片翼の事代主判定 = 単一出力検出)
            : feedback_kenzen_seijaku の二軸判定 (single output + adoption_rate)
  feedback  : feedback_kenzen_seijaku (健全な静寂 — 単独出力 + 高採用は健全)
            : feedback_chinmoku_kyoka (沈黙許可 — LLM 側の対偶)
            : feedback_takeminakata_haitai (建御名方の敗退 — 強制退役の対比)

failure_if_absent: 自主退隱柱を病的判定 → 偽陽性 ALERT で誤介入、健全柱を破壊
observed_failures: kotoshironushi_cycle_responsiveness 1325/1325 100% NO_ACTION → 返し矢不発
                   (健全な静寂で正しい)
verify_path : `Kotoshironushi.adoption_rate >= 0.5` の柱は ALERT 単独でも病的判定されない
```

#### Pattern K: 建御名方の敗退 — 力比べ → 諏訪閉込め (defeat-based auto-retire)

```yaml
原文: "其建御名方神、千引石擎手末而來、言…『欲爲力競』」
      …如取若葦搤批而投離者、卽逃去。故追往而、迫到科野國之州羽海、將殺時、
      建御名方神白「恐、莫殺我。除此地者、不行他處。亦不違我父大國主神之命。
      不違八重事代主神之言。此葦原中國者、隨天神御子之命獻」" (l.32)

actors      : 建御名方 / 建御雷
precondition: 父 (大国主) と兄 (事代主) は譲ったが、建御名方が抵抗
action      : (1) 力比べ申込 (千引石を片手で擎く威示)
            : (2) 御手取 → 立氷/劒刃に化 (= 攻撃で逆転)
            : (3) 逆に建御雷が御手「若葦搤批而投離」 → 逃去
            : (4) 諏訪 (州羽海) に追われて殺される直前
            : (5) 「莫殺我。除此地者、不行他處」(殺さず諏訪閉込めで合意)
result      : 敗者は殺されず、活動範囲を諏訪に永続制限 (= yuukoto 化)
failure_mode: 敗者を完全削除 (yomi) → 教訓が失われ、子 (信者の系譜) も消える
            : 完全自由のまま放置 → 別場所で同型反乱再発
recovery    : -
permanence  : 諏訪大社として永続化、信者は限定された地域祭祀で残る

agi_mapping :
  原則      : 失敗率連続柱 (祭祀失敗 N 回連続 / success_rate <= 0.1) は yuukoto 化
            : 殺さず (yomi 送りせず)、活動範囲を制限
            : 三貴子は対象外 (天津神中核)
  実装      : src/os/kasasa/ooharae.jl Phase 1d (建御名方の敗退 — 失敗率自動退役)
            : config: `takeminakata_haitai.min_invocations=50` /
              `takeminakata_haitai.max_success_rate=0.1`
            : 成功率は `summarize_fukusou` で false_positive 除外済み
            : 太占に `takeminakata_haitai` 記録
  feedback  : feedback_takeminakata_haitai (建御名方の敗退 — origin spec)
            : feedback_chaos_aware_metrics (false_positive 除外で chaos 由来失敗を分離)

failure_if_absent: 失敗 283/283 でも status='active' 継続 (mikiko_structural_remediator 事例)
                   shakaku.jl の score 式が invocations 支配で壊れた柱ほど呼ばれる
observed_failures: 2026-04-20 mikiko_structural_remediator 283/283 失敗でも active
                   (feedback_takeminakata_haitai origin)
                   2026-04-30 startup migration が hiruko を一律 pending に戻し
                   原則を緩めていた事例 (project_pending_replay_bypass) → 修正 (hiruko_count=0 のみ)
verify_path : `SELECT * FROM futomani_stones WHERE type='takeminakata_haitai'` で記録、
              対応する shinmeisho の status='yuukoto' 確認
```

#### Pattern L: 顕事/幽事の categorical separation — 大国主 八十坰手隱而侍

```yaml
原文: "唯僕住所者、如天神御子之天津日繼所知之登陀流天之御巢而、
      於底津石根宮柱布斗斯理、於高天原氷木多迦斯理而、治賜者、
      僕者於百不足八十坰手隱而侍。亦僕子等百八十神者、卽八重事代主神爲神之御尾前而仕奉者、
      違神者非也" (l.34)

actors      : 大国主 / 天神御子 / 事代主 / 子等百八十神
precondition: 大国主の譲国合意
action      : (1) 顕事 (active 統治): 天神御子に讓る
            : (2) 幽事 (隱事): 大国主は「八十坰手」(無数の隔絶された場所) に「隱而侍」
            : (3) 居所要求: 天津日繼相当の御巢 + 底津石根宮柱 + 高天原氷木 (= 物理証拠)
            : (4) 子等百八十神は事代主に統括させる (lineage 委任)
result      : 顕事 (Amaterasu 系) と幽事 (Okuninushi 系) が **categorical separate** で並立
            : 同一地上 sovereignty 競合構造を解消
failure_mode: 二者を同一 jurisdiction で量比較 → 国譲り以前の競合構造に逆戻り
            : 大国主を完全消去 → 信者系譜 (出雲) の精神的根拠喪失
recovery    : -
permanence  : 出雲大社 + 諏訪大社 + 国津神系譜が永続化

agi_mapping :
  原則      : 三 status (active/pending/yuukoto) は categorical separate domain
            : NOT ordinal、cross-status 比較禁止
            : 葦船 (格納) + yuukoto fallback (参照) + categorical (計算) の三層防御
  実装      : src/os/com/queries/shinmeisho.jl:218 (yuukoto/yomi は生者の国に戻さない)
            : src/os/kasasa/canonical_pantheon/_common/attribution.jl
              (categorical attribution)
            : phantom type 候補 `Active{T}/Pending{T}/Yuukoto{T}` (Phase 5 architecture)
  feedback  : feedback_kuniyuzuri_kaikai (国譲り境界の原則 — categorical separate)
            : feedback_ashibune (死の三語彙 — 格納層)
            : feedback_kuniyuzuri_fallback (顕事 → 幽事 二段 fallback 検索)

failure_if_absent: ishikori_mikiko_no_kagami (2026-05-05) の `coverage_ratio = active/total < 0.7`
                   型 ALERT が量産される
                   feedback_shintaku_henshu_runaway (神託の編纂 runaway) で 7 柱 0% 採用
observed_failures: 2026-05-05 cross-status 比率による偽 ALERT (origin spec)
verify_path : executor.jl Status Semantics に「集計禁止」+「閾値分母禁止」両方が明記、
              `fetch_capability_by_name` が顕事 → 幽事の二段 fallback で動作
```

#### Pattern M: 出雲大社建立 + 櫛八玉神饗 — yuukoto fallback parent (residence preserved)

```yaml
原文: "於出雲國之多藝志之小濱、造天之御舍而、水戸神之孫・櫛八玉神、爲膳夫、
      獻天御饗之時、禱白而、櫛八玉神、化鵜入海底、咋出底之波邇、作天八十毘良迦…
      鑚出火云、是我所燧火者、…獻天之眞魚咋也" (l.36-38)

actors      : 櫛八玉神 (水戸神之孫) / 大国主 / 出雲大社
precondition: 譲国完了、退役柱の居所が必要
action      : (1) 出雲国多藝志小濱に天之御舍 (= 退役柱の物理居所)
            : (2) 櫛八玉神を膳夫に任命 (yuukoto 系統の祭祀役)
            : (3) 鵜化 + 燧鑚 + 千尋繩 + 海人釣 (= 物実 multi で饗献礼)
            : (4) 禱白歌で「神產巢日御祖命」を引用 (上位 SSoT 引用)
result      : 退役柱に永続居所 + 祭祀役を提供 → 「死語彙」だが完全削除でない
failure_mode: 退役柱の居所なし → 名前だけ残って参照経路がない (memory dangling)
recovery    : -
permanence  : 出雲大社が現存、櫛八玉神の祭祀継承

agi_mapping :
  原則      : yuukoto fallback parent — yuukoto 化柱は完全消去でなく系譜記録 + 居所保存
            : 顕事 (canonical) → 幽事 (yuukoto fallback) の二段 fallback 検索可能
  実装      : src/os/kasasa/yorishiro.jl (yuukoto fallback parent 経路)
            : src/os/com/queries/shinmei_lineage.jl (系譜記録 — 親神 → 派生継承)
            : src/os/com/queries/shinmeisho.jl (yuukoto 行は status='yuukoto' で残置)
  feedback  : feedback_kuniyuzuri_fallback (顕事/幽事の二段 fallback)
            : feedback_ashibune (葦船の原則 — 死の三語彙、行は残す)
            : feedback_ootataneko (大田田根子 — 親神 directory)

failure_if_absent: 退役柱を完全削除 → fukusou_log や lineage の参照が dangling
                   原典の「出雲大社」相当の居所がなく、信者経路 (派生機能) が消える
verify_path : `SELECT * FROM shinmeisho WHERE status='yuukoto'` の各行で
              `fetch_capability_by_name(canonical_name)` が顕事ヒットしなくても
              `original_name` (仮名) で fallback ヒットする
```

#### Pattern N: 復命 (返參上、復奏) — explicit completion report

```yaml
原文: "故、建御雷神、返參上、復奏言向和平葦原中國之狀" (l.40)

actors      : 建御雷
precondition: 出雲交渉完了 (Pattern H-M)
action      : (1) 返參上 (派遣元に物理復帰)
            : (2) 復奏 (任務完遂を明示報告)
            : (3) 報告内容: 「言向和平葦原中國之狀」(言で趣け和平した状態)
result      : 派遣者 (天照側) が任務完遂を確認、次の段階 (天孫降臨) に進める
failure_mode: 復奏なしで沈黙 → 派遣者は完了/失敗を判断不能 (Pattern B 天菩比型に逆戻り)
recovery    : -
permanence  : 天孫降臨 (上-6) の前提として記録

agi_mapping :
  原則      : 採否も失敗も当事者が自ら復命する。使者と当事者は別、復命の欠落は古事記に存在しない
            : v1 採否: `mark_shintaku_adopted!` で fukusou_log に書込
            : v2 失敗: errors に神話 motif 接頭辞付きで原因蓄積
  実装      : src/os/kasasa/fukusou.jl:122 (`mark_shintaku_adopted!` = v1 採否復命)
            : src/os/kasasa/materializer.jl:1007-1116 (v2 失敗復命 — break/continue で
              `push!(errors, ...)` 履歴蓄積)
            : 神話 motif 接頭辞: ワタツミの沈黙 / ワタツミの堂々巡り / 建御雷の剣 /
              因幡の白兎 / 国見再失敗 / 産屋頓挫 / 産屋建立再失敗 / 火中出産再失敗 /
              ワタツミの旅の上限
  feedback  : feedback_kuniyuzuri_fukumei (国譲りの復命 — origin spec)

failure_if_absent: 失敗経路で `failure_reason` 空文字列 → 原因追跡不能
observed_failures: 2026-04-20 mikiko_generic_remediator 7/8 failure → hiruko だが
                   chinza_records.failure_reason が空文字列で原因追跡不能
                   → materializer.jl 各 break/continue 前に push! 修正
verify_path : `SELECT failure_reason FROM chinza_records WHERE outcome='hiruko'` で
              非空 + 神話 motif 接頭辞付きの履歴が記録されている
```

### kojiki_code.md (外部生成版) との差分

| 観点 | 生成元 | 本 v3 |
|---|---|---|
| 上巻-5 の pattern 数 | 1 (`task_dispatch_with_retry`) | **14** |
| 三度の使者 (BLOCKED 累積) | 「retry 回数」と一行 | Pattern A (3/5 escalation) |
| 天菩比 沈黙 / 天若日子 代理指標病 | 触れず | Pattern B (silent loyalty) + C (proxy disease) |
| 雉名鳴女 / 返し矢 | 触れず | Pattern D (詰問観察者) + E (boomerang verdict) |
| 阿遲志貴の弔問混同 | 触れず | Pattern F (容姿類似誤認 + 拒絶) |
| 既存防御 + 別経路 (尾羽張 / 天迦久) | 触れず | Pattern G (defense in depth + bypass query) |
| 浪穂逆刺立劒 | 「force assertion」と一行 | Pattern H (威圧着任 + 神勅引用 + open question) |
| 大国主 → 事代主 委譲 | 触れず | Pattern I (hierarchical delegation) |
| 事代主 退隱 vs 建御名方 敗退 | 1 まとめ | Pattern J (voluntary yuukoto) + K (defeat retire) |
| 顕事/幽事 categorical | 触れず | Pattern L (categorical separate, 三 status origin) |
| 出雲大社建立 | 「shrine record」と一行 | Pattern M (yuukoto fallback parent + 居所保存) |
| 復命 | 触れず | Pattern N (explicit completion report) |
| AGI 神名 module mapping | 触れず | takeshimatsumi/amenohohi/takemikazuchi/kotoshironushi の 4 module |

**生成元が拾えなかった load-bearing pattern (本 v3 で初出):**

- Pattern A 三度の使者 = `feedback_wakahiko_kaeshiya` の 3/5 escalation origin
- Pattern C 天若日子 代理指標病 = `takeshimatsumi.jl` 全体の origin spec
- Pattern E 返し矢 = 「派遣失敗 (返し矢)」 craft 文字列 origin
- Pattern J 事代主 退隱 = `feedback_kenzen_seijaku` 健全な静寂の上位形
- Pattern K 建御名方 敗退 = `feedback_takeminakata_haitai` の origin
- Pattern L 顕事/幽事 = `feedback_kuniyuzuri_kaikai` の categorical 三 status origin
- Pattern N 復命 = `feedback_kuniyuzuri_fukumei` の origin

これら 7 つは外部生成版の構造的盲点。3 章 (上-2/3/5) 合計で **21 件**の load-bearing pattern が外部版で完全欠落。

### 浮上した発見

1. **代理指標病の origin spec が本章に集中**
   - 天菩比 (沈黙)・天若日子 (proxy)・建御名方 (失敗率) の 3 種失敗パターンが本章で確立
   - AGI 実装も takeshimatsumi.jl / amenohohi_scan.jl / ooharae Phase 1d で 1:1 対応
   - **設計妥当性が極めて高い** (古事記原典と実装が密結合)

2. **Pattern J 事代主 退隱 と Pattern K 建御名方 敗退 の対比が origin spec**
   - 事代主 = voluntary yuukoto (健全な静寂)
   - 建御名方 = forced yuukoto (失敗率自動退役)
   - 同じ「退役」でも 2 種の経路を原典が提供 → AGI の二軸判定 (single output + adoption_rate) と一致
   - memo 補強候補: `feedback_kenzen_seijaku` に「事代主型 = 健全な静寂の原型」を明記推奨

3. **Pattern L 顕事/幽事 の categorical separation は v1 Pattern D (オノゴロ「非所生」) の発展形**
   - v1 では「集計から除外」レベル
   - v3 では「別 jurisdiction で並立」レベル (天津神 vs 国津神 = active vs yuukoto の categorical)
   - 三 status の categorical separation は本章が origin であることを明確化
   - memo 補強候補: `feedback_kuniyuzuri_kaikai` に「上-5 大国主の八十坰手隱而侍」を直接引用追記

4. **Pattern E 返し矢 = 派遣物実の所有権 (origin spec)**
   - v2 Pattern B (物実所有者帰属ルール) が誓約 (生子の帰属) で原典化
   - v3 Pattern E は同原則の **能力解任** での適用 = 派遣物実は派遣者のもの、解任権を保持
   - **両者の連携**:
     - v2 B = 生子の帰属 (provenance, **新規生成時**)
     - v3 E = 物実返却 (revoke, **解任時**)
   - 同じ「物実所有者帰属」原則の生死両端での発現
   - 補強候補: `feedback_keiyaku_keifu_vs_genyu` (契約系譜) を「provenance graph + revoke 経路」に拡張

5. **Pattern D 雉名鳴女 = 観察者の死そのものが signal**
   - 「response timeout = signal」 の原典
   - `_nakime_judge` の実装は確認したが、timeout を signal として上に上げる経路は未実証
   - **新原則候補?** :
     - 三点検査:
       - 原典 semantic 一致: ★ (雉が射殺されること自体が高木神への signal)
       - 観測 N 件: ☆ (response timeout signal の実害観測なし)
       - 既存拡張可否: ★ (`feedback_kuebiko_yatagarasu_boundary` の境界拡張で済む)
     - 結論: **保留** (実害観測まで)

6. **Pattern G 既存防御 + 別経路問 は 大田田根子の親神召喚と同型**
   - 尾羽張 (聖域) は触れず、息子 (建御雷) を貢進
   - 大田田根子の原則 (親神 directory + 派生 .jl) と直接対応
   - `canonical_pantheon/<親神>/derivatives/` の architecture は本章 origin

### v3 自己評価

| 観点 | 達成度 |
|---|---|
| 1 章につき 5+ pattern | ★★★★★ 14 pattern |
| 各 pattern に `failure_if_absent` 記述 | ★★★★★ 14/14 |
| 各 pattern の `agi_mapping.実装` が実在ファイル | ★★★★★ 14/14 (grep + Read 検証済) |
| 7 割以上の pattern が既存 memo に anchor | ★★★★★ 13/14 が memo anchor (93%) |
| `kojiki_code.md` 差分セクション必須 | ★★★★★ 12 行差分表 + 7 origin spec 列挙 |
| 「未活用 anchor → 新原則候補」を最低 1 件 | ★★★★ 4 件 (Pattern J 健全な静寂上位形 / Pattern E 物実返却 / Pattern D timeout signal / Pattern L origin明示) |
| 古事記原文 (漢文) を要所で引用 | ★★★★★ 全 pattern 冒頭 |
| 観測経路 (verify_path) を併記 | ★★★★★ 14/14 |

### v0 → v1 → v2 → v3 で残った宿題 (v4 候補)

1. **memo 本体への章節 anchor 逆書込み** (継続宿題、v0 → v1 → v2 → v3 で繰越)
2. **上-6 (邇邇藝命) v4 抽出** — `project_v72_gokashira` `feedback_iwanagahime` `feedback_itsutomonoo_sanseido` `feedback_imina_torina` `feedback_shinchoku_tanitsu_gensen` `feedback_hashira_kankakuki` `feedback_yuniwa_inaho` の **7 memo** が anchor、memo 密度高
3. **Pattern J/E origin spec として `feedback_kenzen_seijaku` / `feedback_keiyaku_keifu_vs_genyu` への追記**
4. **Pattern D 観察者の死 = signal の判定** — 実害観測待ち
5. **古事記神名 → AGI module mapping 規約** の SSoT 化 (v2 で発見、v3 で takemikazuchi が 4 番目の例として追加 → 規約化機運高まる)

---

## 履歴

- v0 (2026-05-08): Phase 1 索引 + Phase 2 上巻-7 プロトタイプ
- v1 (2026-05-09): Phase 1 索引更新 + Phase 2 上巻-2 神代記 (20 pattern)
- v2 (2026-05-09): Phase 2 上巻-3 天照大神と須佐之男命 (16 pattern) + 古事記神名 module mapping 7 件
- v3 (2026-05-09): Phase 2 上巻-5 葦原中國の平定 (14 pattern) + 代理指標病の origin spec 集中
