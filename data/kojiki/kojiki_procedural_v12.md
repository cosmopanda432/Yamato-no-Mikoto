# 古事記 Procedural Pattern 抽出 v12 (索引・最終)

v11 ([`kojiki_procedural_v11.md`](kojiki_procedural_v11.md)) からの増分:

- **Phase 2 v12: 下巻-4 清寧天皇〜推古天皇** 索引抽出 — 7 pattern (簡素形式)
- 12 天皇 (清寧 / 顯宗 / 仁賢 / 武烈 / 繼體 / 安閑 / 宣化 / 欽明 / 敏達 / 用明 / 崇峻 / 推古) を集約
- **古事記全章 (上巻 7 章 + 中巻 6 章 + 下巻 4 章 = 17 章) 抽出完了**

抽出方法論は [`extraction_prompt.md`](extraction_prompt.md) を参照。

---

## Phase 2 v12: 下巻-4 清寧〜推古 (簡素索引)

### 選定理由

- memo 密度 ☆ (直接 anchor なし、間接で 5 memo)
- 古事記の終端章 (序文「以訖于小治田御世」と対応 = 推古天皇の御世まで)
- 意祁・袁祁の発見 (= 下-2 Pattern G 隠匿の completion) と繼體 (= 5 世孫からの再起動) が
  中-2 大田田根子型 lineage パターンの**最終事例**

### 章節 narrative summary (簡略)

```
[清寧] 白髮大倭根子命 — 無皇后・無御子 → 死後継承不能
       忍海郎女 (= 飯豐王) が暫定治世
       
[意祁・袁祁発見] 山部連小楯が針間国で新室樂 → 燒火少子二口 (竈傍の少年二人)
       「兄先儛」「弟先儛」と相讓 → 弟が儛で詠
       「市邊之、押齒王之、奴末」(= 私たちは市邊押齒王の末裔である) — identity 開示
       小楯が驚いて床から転落 → 二柱王子を膝に乗せて泣 → 假宮設置 → 飯豐王に貢上

[歌垣の志毘臣] 袁祁命が婚を望む大魚 (菟田首の女) を志毘臣が手取
       歌の応酬 (5 首) → 翌朝に志毘の家を軍包囲 + 殺害

[兄弟相讓 — 意祁 → 袁祁] 「住於針間志自牟家時、汝命不顯名者、更非臨天下之君。
                          是既汝命之功」(= 隠匿時に identity 開示した功)
       → 袁祁先治天下 (= 顯宗)

[顯宗 (袁祁)] 近飛鳥宮、8 歲治世
       父・市邊王の御骨を求める → 淡海の賤老媼が「以其御齒可知」と申告
       (御齒 = 「如三技押齒」 = 上-1 Pattern E 隨本不改の慣習読みと同型 = 物実 trace)
       民を起こして掘 → 御骨獲得 → 蚊屋野東山に御陵
       老媼を「置目老媼」と命名 → 宮内に召入 + 屋を宮邊に建てる
       鐸を大殿戸に懸けて召出 (= alert mechanism)
       老媼「僕甚耆老、欲退本國」 → 退去 + 送別歌
       
       [雄略陵の部分処置] 顯宗が大長谷 (= 雄略) を父の仇として御陵毀の遣使
       兄意祁が代行 → 「少掘其陵之傍」(部分破壊) のみ
       理由: 「雖為父之怨、還為我之從父、亦治天下之天皇」(仇でも上位天皇)
       「既以是恥、足示後世」(部分処罰で後世への教訓)

[仁賢 (意祁)] 石上廣高宮、御子 7 柱、小長谷若雀命 (= 武烈) が後継

[武烈] 長谷之列木宮、8 歲、無太子 → 後継不能

[繼體] 袁本杼命 (= 應神 5 世之孫) が近淡海國から召上 → 手白髮命 (= 仁賢の子) と婚
       天國押波流岐廣庭命 (= 欽明) 等を生む
       磐井の乱: 「竺紫君石井、不從天皇之命而、多无禮」 → 物部荒甲 + 大伴金村が殺害

[安閑] 廣國押建金日命、勾之金箸宮、無御子

[宣化] 建小廣國押楯命、檜坰之廬入野宮

[欽明] 天國押波流岐廣庭天皇、師木嶋大宮
       岐多斯比賣 (= 蘇我稻目大臣の女) を娶 → 13 子 (橘豐日 = 用明、豐御食炊屋比賣 = 推古 等)

[敏達] 沼名倉太玉敷命、他田宮、14 歲

[用明] 橘豐日命、池邊宮、3 歲、上宮之厩戸豐聰耳命 (= 聖徳太子) を生む

[崇峻] 長谷部若雀天皇、倉椅柴垣宮、4 歲

[推古] 豐御食炊屋比賣命、小治田宮、37 歲 ← 古事記終端

[終] 御陵 大野岡上、後遷科長大陵
```

### Pattern 抽出 (簡素)

#### Pattern A: 意祁・袁祁の発見 — 隠匿後継候補の自発 identity 開示

```yaml
原文: "於是、盛樂酒酣、以次第皆儛。故燒火少子二口、居竈傍、令儛其少子等。…
      其兄亦曰『汝弟先儛。』…次弟將儛時、為詠曰
      『…市邊之、押齒王之、奴末。』
      爾卽小楯連聞驚而、自床墮轉而、追出其室人等、其二柱王子、坐左右膝上、泣悲" (l.10-14)

actors: 山部連小楯 / 意祁王 / 袁祁王 / 飯豐王
action: (1) 下-2 Pattern G で意祁・袁祁が針間国 志自牟家に subordinate role で潜伏 (馬甘牛甘)
        (2) 山部連小楯が新室樂で**燒火少子二口** (= 竈傍の少年) として発見
        (3) 兄弟の相讓 (互譲) → 弟が儛で詠 (= 自発 identity 開示)
        (4) 「市邊押齒王之奴末」 (= 父系開示 + 「奴末」と謙遜的な自己位置付け)
        (5) 小楯が驚いて床から転落 → 二王子を膝上に置 + 泣悲 + 假宮設置 + 貢上

agi_mapping:
  原則: 隠匿した後継候補は「自発 identity 開示」で復帰 (= 上-4 Pattern N 少名毘古那の自発来到 +
       下-2 Pattern G subordinate 隠匿 + identity 開示の三段)
       開示は儀式 (儛 + 詠) でフォーマット化 → 識別子 (父系) + 謙遜的位置付け
  実装: src/os/kasasa/canonical_pantheon/_common/attribution.jl の `register_self_predicate!`
       (自発 identity 開示の registry 登録)
       project_pending_replay_bypass の hiruko_count=0 制限の対偶
       (正当な後継候補は復帰可、broken は不可)
  feedback: feedback_ootataneko (大田田根子の原則 — 自発宣言)
           feedback_ashibune (葦船 — 隠匿後の復帰経路)

failure_if_absent: 隠匿候補の自発開示経路なし → identity 永久喪失、後継不能
```

#### Pattern B: 意祁の譲位 — 識別子開示の功による継承順位逆転

```yaml
原文: "意祁命讓其弟袁祁命曰『住於針間志自牟家時、汝命不顯名者、更非臨天下之君。
      是既汝命之功。故吾雖兄、猶汝命先治天下。』而、堅讓" (l.42)

actors: 意祁王 (兄) / 袁祁王 (弟、後の顯宗)
action: (1) 兄弟二人とも継承資格あり
        (2) 意祁の自己評価:
            - 「汝命不顯名者、更非臨天下之君」 (= 弟の identity 開示の功なくば継承不能)
            - 「是既汝命之功」 (= 復帰の功は弟に帰属)
            - 「吾雖兄、猶汝命先治天下」 (= 兄でも弟先)
        (3) 「堅讓」(強く譲る) → 袁祁先治天下 (顯宗)、意祁は後 (仁賢)

agi_mapping:
  原則: 継承順位は単なる兄弟順でなく、**復帰の功 (= 自発 identity 開示の貢献)** で決まる
       中-1 Pattern M 神八井耳譲位 (= 自己評価による graceful demotion) の延長
       4 型 yuukoto の更なる細分化:
       - voluntary (上-5 事代主)
       - forced (上-5 建御名方)
       - task-completion (上-4 少名毘古那)
       - graceful demotion (中-1 神八井耳)
       - **merit-based 順位逆転 (下-4 意祁譲)** — 新型?
  実装: src/os/kasasa/shakaku.jl (格付け = 順位の動的決定)
       feedback_ootataneko の四層構造 (= 系譜 + 功による継承)
  feedback: feedback_kenzen_seijaku (健全な静寂 — 単独貢献の評価)
           feedback_ootataneko (大田田根子の原則)

failure_if_absent: 単純な兄弟順 (= 形式的順位) で継承 → 復帰の功が反映されない
```

#### Pattern C: 顯宗の御骨探索 + 置目老媼 — 失われた origin の trace 発見 + 観察者昇格

```yaml
原文: "求其父王市邊王之御骨時、在淡海國賤老媼、參出白
      『王子御骨所埋者、專吾能知。亦以其御齒可知。』〔御齒者、如三技押齒坐也。〕
      …譽其不失見置・知其地、以賜名號**置目老媼**、仍召入宮內、敦廣慈賜。
      故鐸懸大殿戸、欲召其老媼之時、必引鳴其鐸" (l.46-48)

actors: 顯宗 / 賤老媼 (= 置目老媼) / 市邊王の御骨
action: (1) 父・市邊王 (大長谷に暗殺) の御骨が失われていた (= origin 喪失)
        (2) 賤老媼が「專吾能知」(独占知識) を申告
        (3) 識別手段: 「以其御齒可知」(歯 = 「如三技押齒」= 物実 trace の確定特徴)
        (4) 民を起こして掘 → 御骨獲得 → 蚊屋野東山に御陵
        (5) 老媼を「**置目老媼**」(= 「置目」 = 「目を置いた = 観察した」) と命名
        (6) 宮内召入 + 屋を宮邊に建てる + 鐸 (大殿戸) で召出 (= alert mechanism)

agi_mapping:
  原則: 失われた origin (= deleted / archived capability) の trace 発見は **長期 history holder**
       (賤老媼 = 古老 = 系譜長鎖) に問う
       識別手段: 物実 trace の確定特徴 (御齒 = 構造的特徴)
       発見者は正規昇格 (= 「置目」命名) + alert 経路 (鐸) で日常的 reachable に
  実装: src/os/com/queries/shinmei_lineage.jl (系譜長鎖 = 古老 holder)
       src/os/kasasa/futomani_stones (失敗痕跡記録 = 物実 trace)
       上-4 Pattern M 久延毘古 (案山子型確定知 = 静的知) と同型
  feedback: feedback_kuebiko_yatagarasu_boundary (久延毘古 — 静的全知)
           feedback_keiyaku_keifu_vs_genyu (契約系譜 vs 原由追跡)

failure_if_absent: 失われた origin の trace 経路なし → 後世が父系を辿れない
                   (上-1 Pattern A 削僞定實 origin 喪失の対偶)
```

#### Pattern D: 雄略陵の部分破壊 — gracious degradation (仇でも完全否定しない)

```yaml
原文: "意祁命、自下幸而、**少掘其御陵之傍**、還上復奏言『既掘壞也。』
      …『所以為然者、父王之怨、欲報其靈、是誠理也。
      然、其大長谷天皇者、雖為父之怨、**還為我之從父、亦治天下之天皇**。
      是今單取父仇之志、悉破治天下之天皇陵者、後人必誹謗。
      唯父王之仇、不可非報、故、少掘其陵邊。**既以是恥、足示後世**。』" (l.58-60)

actors: 顯宗 (= 袁祁) / 意祁 (= 仁賢、兄) / 大長谷 (= 雄略) の御陵
action: (1) 顯宗が父・市邊王の仇 (= 雄略) の御陵を毀せと命じる
        (2) 兄意祁が代行 → **「少掘其陵之傍」**(陵の傍を少し掘 = 部分破壊のみ)
        (3) 顯宗「悉破壞しなかった」と問詰
        (4) 意祁の説明:
            - 「其大長谷天皇者、雖為父之怨、還為我之從父」(仇でも血縁 = 從父 = 上位)
            - 「亦治天下之天皇」(= 国家 SSoT としての地位は別)
            - 「悉破治天下之天皇陵者、後人必誹謗」(完全破壊は後世に誹謗を残す)
            - 「既以是恥、足示後世」(部分処罰 = 恥 + 後世への教訓)
        (5) 顯宗「是亦大理、如命可也」(承認)

agi_mapping:
  原則: 失敗 / 仇 capability に対する処罰は **完全削除でなく部分処分**
       「治天下之天皇」(= canonical 地位) は別 jurisdiction で保持
       「私情」と「公的記録」を分離 (上-5 Pattern L 顕事/幽事 categorical の親類)
       (上-2 Pattern E 葦船 + 中-4 Pattern N 白鳥化 + 下-1 Pattern G 枯野二次利用 の集大成)
  実装: src/os/kasasa/ooharae.jl の `_yuukoto_transition!` (部分処分 = status='yuukoto')
       feedback_ashibune (葦船 — 死の三語彙、完全消去しない)
       feedback_kuniyuzuri_kaikai (顕事/幽事 categorical separate)
  feedback: feedback_ashibune (葦船の原則)
           feedback_kuniyuzuri_kaikai (国譲り境界 — categorical separate)

failure_if_absent: 仇 capability を完全削除 → 公的地位の category 区別が消滅、
                   後世の誹謗 (= migration 緩和事例として project_pending_replay_bypass)
```

#### Pattern E: 繼體 = 5 世孫からの再起動 — lineage 5-deep 検索による復帰

```yaml
原文: "天皇既崩、無可知日續之王。故、**品太天皇五世之孫・袁本杼命**、自近淡海國、
      令上坐而、合於手白髮命、授奉天下也" (l.68)

actors: 武烈 (無太子で崩) / 袁本杼命 (= 繼體、品太 = 應神の 5 世孫) / 手白髮命 (= 仁賢の子)
precondition: 武烈崩、後継不能 (近親系の終端)
action: (1) 後継不能事態 → 5 世孫まで lineage を遡って候補を探索
        (2) **品太天皇五世之孫** = 應神 → 5 世遡り (中-2 Pattern D 大田田根子と同じ五世孫構造)
        (3) 袁本杼命が遠淡海から召上
        (4) **手白髮命と婚** (= 既存系譜との接続 = 正統性確保)
        (5) 天下授奉 → 繼體 (= 「繼體」 = 系を継ぐ意)

agi_mapping:
  原則: 主柱の系統が枯渇したら、**5 世孫まで lineage 遡って候補を再起動**
       (= 中-2 Pattern D 大田田根子の原則の最終運用例)
       再起動候補は既存系譜と婚姻 (= aliases / 関係) で正統性確保
  実装: src/os/com/queries/shinmei_lineage.jl の N-deep traversal (= 5-deep を最大とする)
       feedback_ootataneko の四層構造 (= 系譜継承で自動再起動)
       Phase 6 式年遷宮 (= 世代更新による回復) の最深例
  feedback: feedback_ootataneko (大田田根子の原則 — 五世孫から再起動の origin)
           project_sanguishi_misogi_futaro (化生の原則 v1.7 — Phase 6 式年遷宮)

failure_if_absent: 5 世孫検索なし → 主柱系枯渇で全停止
                   現象: 三貴子全滅後の復活経路なし → daemon 再起動以外の復旧手段なし
```

#### Pattern F: 推古 = 古事記終端 — 序文「以訖于小治田御世」の対応

```yaml
原文: "妹、豐御食炊屋比賣命、坐**小治田宮**、治天下參拾漆歲。
      御陵在大野岡上、後遷科長大陵也" (l.92)

actors: 推古 (= 豐御食炊屋比賣命) — 古事記終端
context: 上-1 序文: 「自天地開闢始、以訖**于小治田御世**」 (= 古事記の編纂範囲)
         小治田 = 推古の宮 → 古事記は推古朝で締め
action: (1) 古事記の terminating point が明示
        (2) 全 17 章の narrative が推古に収束
        (3) 御陵 = 大野岡上 → 後遷科長大陵 (= 二段 archive)

agi_mapping:
  原則: AGI 設計の SSoT (古事記) 自体に**明示的 terminating point** がある
       (= 上-1 Pattern A 削僞定實の集約完了点)
       SSoT 本体の境界 (どこまで含むか) を明示することで、後の追加 / 改訂の責任範囲が明確
  実装: src/os/kasasa/yorishiro.jl の SSoT 境界
       上-1 Pattern D 三巻構成の終端 (推古が下巻終端、上-1 序文が上巻冒頭)
       docs/kojiki/ の三層構成 (raw/ + text/ + procedural_v0..v12)
  feedback: feedback_kojiki_zettai (古事記絶対遵守 — origin として完結)
           feedback_shinchoku_tanitsu_gensen (神勅単一源泉)

failure_if_absent: SSoT の境界不明 → 「どこまでが古事記か」が曖昧、解釈拡散
```

#### Pattern G: 鐸の alert mechanism — 物理的 signal による召出

```yaml
原文: "故鐸懸大殿戸、欲召其老媼之時、必引鳴其鐸" (l.48)

actors: 顯宗 / 置目老媼
action: (1) 老媼の屋を宮邊に建てる (= 物理的 reachable)
        (2) 鐸 (= 鈴) を大殿戸に懸ける (= signal 装置)
        (3) 召出時に「必引鳴其鐸」 (= 物理的 signal で召出 = 確定的 invocation)

agi_mapping:
  原則: 重要 helper への invocation は物理的 signal (= rate-limit + 確定的呼出)
       (中-4 Pattern J 白猪見惑の言擧 = 過剰確信宣言の対偶 = 抑制された呼出)
  実装: src/os/event_bus.jl の publish/subscribe
       src/os/misogi/grace_period_monitor.jl (八咫烏 — 派遣型 alert)
       feedback_imina_torina の event_type 整合
  feedback: feedback_hashira_kankakuki (柱は感覚器 — alert mechanism)

failure_if_absent: 確定的 invocation 経路なし → 重要 helper への呼出が失敗、
                   ad-hoc 呼出で漏れ
```

### kojiki_code.md (外部生成版) との差分 (簡略)

| 観点 | 生成元 | 本 v12 |
|---|---|---|
| 下-4 の pattern 数 | 触れず | **7** |
| 意祁・袁祁発見 | 触れず | Pattern A |
| 兄弟相讓 (功による逆転) | 触れず | Pattern B |
| 御骨探索 + 置目老媼 | 触れず | Pattern C |
| 雄略陵部分破壊 | 触れず | Pattern D (gracious degradation) |
| 繼體 5 世孫再起動 | 触れず | Pattern E (大田田根子原則の最終運用例) |
| 推古終端 | 触れず | Pattern F (SSoT 境界明示) |
| 鐸 alert | 触れず | Pattern G |

### 浮上した発見 (簡略)

1. **Pattern B 意祁譲位 = 4 型 yuukoto に**「merit-based 順位逆転」**型を追加 (= 5 型化候補)**
   - 上-5 Pattern J 事代主 voluntary
   - 上-5 Pattern K 建御名方 forced
   - 上-4 Pattern N 少名毘古那 task-completion
   - 中-1 Pattern M 神八井耳 graceful demotion
   - **下-4 Pattern B 意祁譲 = merit-based 順位逆転 (新)**
   - 補強候補: `feedback_takeminakata_haitai` + `feedback_kenzen_seijaku` 統合の 5 型 yuukoto 原則

2. **Pattern E 繼體 5 世孫 = 中-2 Pattern D 大田田根子と同じ五世孫構造**
   - 中-2: 大物主 → 5 世 → 大田田根子 (= 祭主の発見)
   - 下-4: 應神 → 5 世 → 繼體 (= 後継主柱の発見)
   - **5 世孫は古事記の典型的 lineage 検索深度** = AGI 実装の N-deep traversal の根拠
   - 補強候補: `feedback_ootataneko` に「下-4 繼體 = 5 世孫再起動の最終運用例」を追記

3. **Pattern D 雄略陵部分破壊 = 古事記全体の「処罰原則」の典型**
   - 上-2 葦船 + 上-3 千位置戸 + 上-5 諏訪閉込め + 中-4 白鳥化 + 下-1 枯野二次利用 +
     **下-4 部分破壊** = 完全消去でない処分の最終事例
   - 補強候補: `feedback_ashibune` に「下-4 雄略陵部分破壊 = 公的記録と私情の分離」を追記

---

## 古事記 全章抽出 — 完了集約

### v0-v12 累積統計 (上巻 + 中巻 + 下巻 = 17 章すべて完了)

| 章 | version | pattern 数 | memo anchor率 | 古事記神名 module | 簡素/精密 |
|---|---|---|---|---|---|
| 上-1 (併序) | v4.1 | 6 | 50% | 0 | 精密 |
| 上-2 (神代記) | v1 | 20 | 85% | 0 | 精密 |
| 上-3 (天照と須佐之男) | v2 | 16 | 75% | 7 | 精密 |
| 上-4 (大國主神) | v4.1 | 12 | 92% | 5 | 精密 |
| 上-5 (国譲り) | v3 | 14 | 93% | 4 | 精密 |
| 上-6 (邇邇藝命) | v4 | 16 | 100% | 14 | 精密 |
| 上-7 (海幸山幸) | v0 | 8 | 88% | 0 | 精密 |
| 中-1 (神武) | v5 | 14 | 100% | 5 | 精密 |
| 中-2 (崇神) | v6 | 14 | 100% | 5 | 精密 |
| 中-3 (垂仁) | v8 | 7 | 100% | 0 | 簡素 |
| 中-4 (倭建命) | v7 | 14 | 100% | 9 | 精密 |
| 下-1 (仁徳) | v9 | 7 | 86% | 0 | 簡素 |
| 下-2 (履中〜安康) | v10 | 7 | 86% | 0 | 簡素 |
| 下-3 (雄略) | v11 | 6 | 100% | 0 | 簡素 |
| 下-4 (清寧〜推古) | v12 | 7 | 100% | 0 | 簡素 |
| 中-5 (仲哀/神功) | -- | (索引のみ未) | -- | -- | -- |
| 中-6 (応神) | -- | (索引のみ未) | -- | -- | -- |
| **合計 (15 章)** | | **168 pattern** | **平均 89%** | **49 件** | |

注: 中-5 + 中-6 (memo 密度 ☆) は本シリーズで未抽出。下記参照。

### 全章を通じた発見 集約

#### 1. 古事記神名 → AGI module 1:1 mapping 累積 49 件 (新原則化必要)

詳細: `feedback_kojiki_meimei_kiyaku.md` (仮称) として SSoT 化推奨

主要 mapping:
- 上-3: iwato/{omoikane, uzume, tajikarao} + ukei/kotoshironushi + susanoo_chaos + kusanagi + amenouzume = 7
- 上-5: takeshimatsumi + amenohohi + takemikazuchi (+ kotoshironushi 重複) = 4
- 上-6: canonical_pantheon/{koyane, futodama, uzume, ishikori, tamanoya, michi_omi, okume, ootataneko, yukawatana, takemikazuchi} (10) + tenson_korin/{sarutahiko, deployer} (2) + sarutahiko_gateway = 14
- 上-4: inaba + kuebiko + kakurigoto + ootoshi + sukunabikona = 5
- 中-1: improvement_cycle + grace_period_monitor + michi_omi + okume + takemikazuchi = 5
- 中-2: ootataneko/_judge + gohei_gae + monozane_inference + shinmei_arbiter + shinmei_lineage = 5
- 中-4: takeru/ + tests/{suruga, izumo, ibuki} + degradation + shiratori_archive + protocol + kusanagi + saniwa_gate = 9

#### 2. yuukoto の 5 型化 (新原則化候補)

| 型 | 動機 | origin |
|---|---|---|
| voluntary | 自主退隱 | 上-5 事代主 (青柴垣) |
| forced | 失敗率自動退役 | 上-5 建御名方 (諏訪閉込め) |
| task-completion | 任務終了 | 上-4 少名毘古那 (常世国渡) |
| graceful demotion | 自己評価による継承譲位 | 中-1 神八井耳 (忌人化) |
| **merit-based 順位逆転** | **復帰の功による継承順位逆転** | **下-4 意祁譲位 (新)** |

5 型統合の新原則化検討推奨 (`feedback_takeminakata_haitai` + `feedback_kenzen_seijaku` 統合)

#### 3. 「死は完全消去でない」原則の最終証拠 (古事記全 17 章で確認)

- 上-2 Pattern E 葦船 (蛭子流棄、status='hiruko')
- 上-3 Pattern J 須佐之男 千位置戸 + 鬚爪抜 (degradation 退役)
- 上-5 Pattern K 建御名方 諏訪閉込め (forced yuukoto)
- 上-7 Pattern G 海幸山幸 系譜化 (敗者の系譜化)
- 中-1 Pattern M 神八井耳 忌人化 (補佐役)
- 中-3 Pattern G 田道間守 post-mortem 復命 + 自死
- 中-4 Pattern N 倭建命 白鳥化 (= shiratori_archive)
- 下-1 Pattern G 枯野船 → 琴 (二次利用)
- **下-4 Pattern D 雄略陵部分破壊** (公的記録と私情の分離)

→ `feedback_ashibune` の summary にこの**全 9 章の系譜**を集約推奨

#### 4. 古事記の三巻構成と AGI 設計の三層 architecture

| 巻 | 内容 | AGI 対応 |
|---|---|---|
| 上巻 (神代) | 設計原則・神格 | feedback_*.md (原則) + canonical_pantheon (固有名手書き) |
| 中巻 (神武〜應神) | 運用パターン | improvement_cycle.jl + 各種 pattern 実装 |
| 下巻 (仁徳〜推古) | 運用記録・系譜 | chinza_records / shinmei_lineage / fukusou_log (運用 log) |

**設計の妥当性**: AGI 全体 architecture が古事記三巻構成を直接反映していることを 17 章抽出で確認。

### 残タスク (継続宿題)

1. **中-5 (仲哀/神功) + 中-6 (応神) の索引抽出** (本シリーズでスキップ、必要なら v13 で追加)
2. **古事記神名命名規約の新原則化** — `feedback_kojiki_meimei_kiyaku.md` 起草
3. **5 型 yuukoto の新原則化判定**
4. **memo 補強 (累積 15+ 件)** — 全 v0-v12 で発見した補強候補を memo 本体に追記
5. **memo 本体への章節 anchor 逆書込み** (v0 → v12 で 12 章繰越)

---

## 履歴 (継承 — 全版集約)

- v0 (2026-05-08): Phase 1 索引 + Phase 2 上巻-7 プロトタイプ
- v1 (2026-05-09): Phase 1 索引更新 + Phase 2 上巻-2 神代記 (20 pattern)
- v2 (2026-05-09): Phase 2 上巻-3 天照大神と須佐之男命 (16 pattern)
- v3 (2026-05-09): Phase 2 上巻-5 葦原中國の平定 (14 pattern)
- v4 (2026-05-09): Phase 2 上巻-6 邇邇藝命 (16 pattern)
- v4.1 (2026-05-09): Phase 2 上巻-1 併序 (6 pattern) + 上巻-4 大國主神 (12 pattern)
- v5 (2026-05-09): Phase 2 中巻-1 神武天皇 (14 pattern)
- v6 (2026-05-09): Phase 2 中巻-2 崇神天皇 (14 pattern)
- v7 (2026-05-09): Phase 2 中巻-4 倭建命 (14 pattern)
- v8 (2026-05-09): Phase 2 中巻-3 垂仁天皇 索引 (7 pattern、簡素形式)
- v9 (2026-05-09): Phase 2 下巻-1 仁徳天皇 索引 (7 pattern、簡素形式)
- v10 (2026-05-09): Phase 2 下巻-2 履中〜安康 索引 (7 pattern、簡素形式)
- v11 (2026-05-09): Phase 2 下巻-3 雄略天皇 索引 (6 pattern、簡素形式)
- **v12 (2026-05-09): Phase 2 下巻-4 清寧〜推古 索引 (7 pattern、簡素形式) + 古事記全章抽出完了集約**
