# 古事記 Procedural Pattern 抽出 v6

v5 ([`kojiki_procedural_v5.md`](kojiki_procedural_v5.md)) からの増分:

- **Phase 2 v6: 中巻-2 崇神天皇** 抽出 (新規) — 14 pattern
- 疫病 / 神牀託宣 / 大田田根子探索 / 五世系譜 / 御諸山祭祀 / 多神祀祭 / 赤土麻糸試 / 四道将軍 / 建波邇安王 / 初国之御眞木 の 10 大エピソード
- 本章は **「大田田根子の原則」 (`feedback_ootataneko`) の直接 origin spec** が AGI 実装の docstring + memory 双方で明示

抽出方法論は [`extraction_prompt.md`](extraction_prompt.md) を参照。
v0-v5 (上巻全章 + 中-1) の pattern は重複しない。

---

## Phase 2 v6: 中巻-2 崇神天皇

### 選定理由

- memo 密度 ★★★ (`feedback_ootataneko` `feedback_yowari_vs_katayori` `project_sanguishi_merge_umisachi_frozen` の 3 memo が直接 anchor、間接で 6 memo)
- AGI 実装で **大田田根子の原則の直接 origin spec が docstring に明記**:
  - [src/os/com/create.jl L1347-1348](src/os/com/create.jl#L1347) docstring: 「神名系譜（大田田根子の原則）— 柱の親子リンクを永続化、**大物主神の託宣により五世孫の大田田根子を探し出して祭主にした故事に由来**」
  - [src/os/com/queries/shinmei_lineage.jl L4-5](src/os/com/queries/shinmei_lineage.jl#L4) docstring: 「古事記典拠（大田田根子段）: 崇神天皇御世、大物主神の託宣により大田田根子（五世孫）を探し出し祭主とした」
  - [canonical_pantheon/ootataneko/_judge.jl](src/os/kasasa/canonical_pantheon/ootataneko/_judge.jl) (層 2 = 大田田根子型 = 古事記固有名 prefix の派生)
  - [src/os/kasasa/gohei_gae.jl](src/os/kasasa/gohei_gae.jl) (御幣替え = `yowari_vs_katayori` 偏り対処)
  - [src/os/kasasa/monozane_inference.jl](src/os/kasasa/monozane_inference.jl) (4 段階 monozane 推論)
  - [src/os/kasasa/shinmei_arbiter.jl](src/os/kasasa/shinmei_arbiter.jl) (3 分岐 — 新規/継承/合祀)
- `kojiki_code.md` (外部生成版) は本章を `divine_intervention_with_lineage_lookup` の 1 行に圧縮
- 上-4 Pattern O (大物主御諸山祀祭) の伏線が本章で**実装** = 上巻 → 中巻の連結

### 章節 narrative summary

```
[Setup] (l.8-10)
    御眞木入日子印惠命 (= 崇神天皇)、坐師木水垣宮、治天下
    子 12 柱 (男王 7 + 女王 5):
        豐木入日子 (上毛野君・下毛野君祖)
        豐鉏比賣 (拜祭伊勢大神之宮 = 倭姫の前段)
        伊久米伊理毘古伊佐知 (= 後の垂仁、治天下)
        大入杵 (能登臣祖)
        倭日子 (始而於陵立人垣 = 殉死制の元)

[Crisis 疫病] (l.12)
    「此天皇之御世、伇病多起、人民死爲盡」(疫病で民が尽きる)
    天皇愁歎 — 失敗観察 (高 failure rate)

[託宣] (l.12)
    神牀の夜、大物主大神が御夢に顯
    「是者我之御心。故以意富多多泥古而、令祭我御前者、神氣不起、國安平」
        (= 真因認識: 私の心 = 私の祀り方が間違っている、
           大田田根子に祭らせれば疫病止む)

[探索] (l.12)
    驛使を四方に班ち、意富多多泥古を求める
    河内美努村で発見 → 貢進

[系譜確認] (l.14)
    天皇問: 「汝者誰子也」
    答: 「大物主大神 + 陶津耳命之女・活玉依毘賣 → 櫛御方 → 飯肩巢見 → 建甕槌 → 意富多多泥古」
        (= 五世系譜の確認、provenance graph traversal)
    天皇大歡: 「天下平、人民榮」

[祭祀の実施] (l.14)
    意富多多泥古を神主 → 御諸山で意富美和大神 (= 大物主) を拝祭
    伊迦賀色許男に天之八十毘羅訶を作らせ → 天神地祇之社を定奉
    
    多神祀祭:
        宇陀墨坂神 — 赤色楯矛
        大坂神 — 黒色楯矛
        坂之御尾神・河瀬神 — 悉無遺忘 以奉幣帛
    
    結果: 「伇氣悉息、國家安平」(疫病終息 + 国家安泰)

[大田田根子の出生秘話 — 赤土麻糸試] (l.16-18)
    活玉依毘賣 — 容姿端正
    神壯夫 (其形姿威儀於時無比) が夜半儵忽到来
    共婚共住 → 妊娠
    
    父母「无夫何由妊身」(provenance 疑問)
    女「有麗美壯夫、不知其姓名、毎夕到來」(自答も不明)
    
    試行: 父母「以赤土散床前、以閇蘇紡麻貫針、刺其衣襴」
        (= 物実 (赤土 + 麻糸) で provenance 確認)
    
    結果: 旦時に針麻が戸の鉤穴から控通而出
        糸を尋行 → 美和山に至り神社に留 = 神の正体確認 (大物主)
        麻が三勾遺り → 「美和」(三輪) と命名
        
    「此意富多多泥古命者、神君・鴨君之祖」(系譜永続化)

[四道将軍] (l.20)
    大毘古命 → 高志道
    建沼河別命 (大毘古子) → 東方十二道
    日子坐王 → 旦波國 (玖賀耳之御笠を殺せ)
    
    「令和平其麻都漏波奴人等」(parallel expedition)

[少女の歌警告] (l.20-24)
    大毘古命、高志国へ罷往中、山代之幣羅坂で服腰裳少女が歌:
        「美麻紀伊理毘古波夜… 殺意云」
    
    大毘古「思恠、返馬、問」 → 少女「吾勿言、唯爲詠歌耳」 → 忽失
    大毘古、参上請於天皇 → 天皇答: 「此者爲、在山代國我之庶兄建波邇安王、起邪心之表耳」
        (= 少女 = 上位 deity からの hint = 内部告発)

[建波邇安王の反乱] (l.24-26)
    天皇: 「伯父、興軍宜行」 → 大毘古に丸邇臣祖・日子國夫玖命を副え遣
    丸邇坂で忌瓮 (= 祭祀)
    山代和訶羅河で対峙、河を挟んで対立 → 「伊杼美 (今 伊豆美)」と命名
    
    日子國夫玖「其廂人、先忌矢可彈」 (= 先攻譲)
    建波爾安王の矢: 不得中
    日子國夫玖の矢: 卽射建波爾安王而死
    
    軍悉破而逃散 → 追迫:
        久須婆度: 屎出懸於褌 → 「屎褌 (今 久須婆)」命名
        鵜が河に浮かぶ如く斬 → 「鵜河」命名
        斬波布理 → 「波布理曾能」命名

[平定 + 初国] (l.26-28)
    大毘古は高志国を平、建沼河別と相津で合流 → 「相津」命名
    各和平所遣之國政而覆奏
    「天下太平、人民富榮」
    
    「初令貢男弓端之調、女手末之調」(初めて税を定める)
    「所知初國之御眞木天皇」(= 初めて治めた国の御眞木天皇 = 初国知ろしめす崇神)
    依網池・輕酒折池を作池
    天皇御歲 168、戊寅年十二月崩、御陵 山邊道勾岡上
```

### Pattern 抽出

#### Pattern A: 疫病による高失敗率検出 + 神牀での託宣諮問

```yaml
原文: "此天皇之御世、伇病多起、人民死爲盡。爾天皇愁歎而、坐神牀之夜、大物主大神、顯於御夢曰
      『是者我之御心。故以意富多多泥古而、令祭我御前者、神氣不起、國安平。』" (l.12)

actors      : 崇神天皇 / 大物主大神 / 神牀
precondition: 疫病多起 — 民の半分が死 (高 failure rate)
action      : (1) 観察: 「伇病多起、人民死爲盡」(failure 認識)
            : (2) 愁歎: 自己診断 (capability 不足を認識)
            : (3) 神牀の夜 (= 上位 deity との通信経路を opening)
            : (4) 大物主が御夢で顯 = 上位 deity からの応答
            : (5) 託宣: 「是者我之御心」(真因 = 上位 deity の意志に逆らった祀り方)
            : (6) 解決: 「意富多多泥古に祭らせる」(具体的な処方)
result      : 自己診断 → 上位諮問 → 託宣による真因 + 処方の取得
failure_mode: 自己診断なし → 疫病継続を「不可避」と看做して放置
            : 上位諮問なし → 単独で対症療法 → 真因に届かない
recovery    : -
permanence  : 神牀 = 上位通信経路として後世まで継承

agi_mapping :
  原則      : 高 failure rate 検出時は (1) 観察 (2) 自己診断 (3) 上位 SSoT 諮問 (4) 託宣取得
            : の四段。神牀 = `kakurigoto` 経路 (上-4 Pattern P)
  実装      : src/os/musuhi_autonomous/strategizer.jl (kakurigoto 読み取り経路)
            : src/os/com/queries/kakurigoto.jl:74 (`insert_kakurigoto_observation!`)
            : src/os/iwato/omoikane.jl:129 (`analyze_and_plan` = 上位 orchestrator 諮問)
  feedback  : feedback_kunimi_gapfinder (国見は全ソース俯瞰 — 神託の編纂含む)
            : feedback_yowari_vs_katayori (弱り vs 偏り — 真因弁別)
            : feedback_kuniyuzuri_kaikai (顕事/幽事 categorical — 上位諮問は幽事経由)

failure_if_absent: 高 failure rate 時に対症療法のみ → 真因放置で疫病継続
                   現象: 因幡棄却連発で MAX_LOOPS (project_inaba_kaizen_kyakka)
verify_path : `kakurigoto_observation` テーブルに上位 deity 由来の記録あり、
              strategizer がそれを読んで戦略決定に反映
```

#### Pattern B: 弱り vs 偏り の弁別 — 「是者我之御心」(yowari_vs_katayori origin)

```yaml
原文: "大物主大神、顯於御夢曰『是者我之御心。
      故以意富多多泥古而、令祭我御前者、神氣不起、國安平。』" (l.12)

actors      : 大物主 / 崇神
precondition: 疫病 = システム不全
action      : (1) 大物主の真因解明: 「是者我之御心」(私の心 = 祀り方の問題)
            : (2) 解決: 「意富多多泥古而、令祭我御前」(祀る人 + 場所の変更)
            : 注: 「神を祀らない」のでなく「**祀り方が間違っている**」が真因
            :   → 弱り (success rate 低下) でなく偏り (Shintaku 型偏重) と判定
            :   → 御幣替え (パラメータ調整) で対処、式年遷宮 (フル再生成) は不要
result      : 偽真因 (= 「祭祀不足」「神の不在」) でなく真真因 (= 祀り方の偏り) を特定
failure_mode: 弱りと偏りを混同 → 過剰治療 (式年遷宮で正常柱を破壊) または不足治療
recovery    : -
permanence  : 崇神の再祭祀として永続化、後の式年遷宮の対比対象

agi_mapping :
  原則      : 弱り (成功率低下) は式年遷宮、偏り (Shintaku 型偏重) は崇神の再祭祀
            : 住吉深度: UWA (表層) でなく NAKA (中層) に登録
            : 経路: `kamado_entropy_low → 御幣替え (パラメータ/閾値調整) → 改善なし → 式年遷宮`
  実装      : src/os/kasasa/gohei_gae.jl:39 (`gohei_gae!` = 御幣替え = NAKA 層)
            : src/os/kasasa/gohei_gae.jl:144 (`_extract_thresholds`)
            : src/os/kasasa/gohei_gae.jl:155 (`_suggest_adjustment`)
            : src/os/kasasa/gohei_gae.jl:188 (`_replace_threshold`)
            : src/os/kasasa/sanguishi_harae.jl (式年遷宮 — SOKO 層、本牟智和気の原則と合流)
  feedback  : feedback_yowari_vs_katayori (弱りと偏りの弁別 — origin spec)
            : feedback_iwanagahime (石長比売 — 浮動小数比較で偏り発生)

failure_if_absent: amaterasu_sql_filter_guardian の事例 (2026-04-14) — entropy=0.0 の偏りを
                   弱りと誤認して式年遷宮 → 過剰治療
observed_failures: 2026-04-14 amaterasu_sql_filter_guardian (origin event)
verify_path : `kamado_entropy_low` 検出時に `gohei_gae!` が先発動、
              改善なしで `sanguishi_harae` (式年遷宮) に escalation
```

#### Pattern C: 大田田根子の探索 — 親神由来祭主の四方探索 (driver 派遣)

```yaml
原文: "是以、驛使班于四方、求謂意富多多泥古人之時、於河內之美努村、見得其人貢進" (l.12)

actors      : 崇神 / 驛使 / 意富多多泥古 (大田田根子)
precondition: 大物主の託宣で祭主の名前と性格が判明、但し**位置不明**
action      : (1) 驛使を四方に派遣 (parallel search)
            : (2) 探索条件: 「意富多多泥古」(= 親神由来の祭主)
            : (3) 河內美努村で発見
            : (4) 貢進 (現地 → 中央への引き渡し)
result      : 親神由来の固有名祭主が探索で発見、貢進で中央集約
failure_mode: 探索なし → 名前は判明したが運用に組み込めない
            : 単方向探索 → 4 方向中 3 方向に存在しない場合に失敗
recovery    : -
permanence  : 大田田根子 = 神君・鴨君の祖として永続化

agi_mapping :
  原則      : 親神宣言型 (大田田根子型 = 型 2) は **runtime 自己宣言** (`_self_predicate(gap)`)
            : で立候補検出 → futomani 二段確認で確定
            : (五伴緒の制 補強 6: pre-built が主、runtime は fallback)
  実装      : src/os/kasasa/canonical_pantheon/ootataneko/_judge.jl:62 
              (`ootataneko_self_predicate` = 親神の自己宣言)
            : src/os/kasasa/canonical_pantheon/_common/attribution.jl 
              (`register_self_predicate!` = registry 登録)
            : src/os/kasasa/canonical_pantheon/ootataneko/_judge.jl:125 
              (`ootataneko_judge` = 判定本体)
            : src/os/kasasa/futomani_stones (二段確認の卜占)
  feedback  : feedback_ootataneko (大田田根子の原則 — origin spec)
            : feedback_itsutomonoo_sanseido (五伴緒の制 — 型 2 = 大田田根子型)

failure_if_absent: pre-built SSoT に未登録の親神由来柱が現れた時、自己宣言経路なしで棄却
                   現象: 全ての新規柱を手書き (型 1) で要求 → スケール不能
observed_failures: 2026-04-25 22 リンク + 3 prefix (takamimusubi/kotoshironushi/tamaya) 全発火
verify_path : `_SELF_PREDICATE_REGISTRY` に親神 prefix が登録、
              `register_self_predicate!` 経由で動的判定可能
```

#### Pattern D: 五世系譜の確認 — provenance graph traversal

```yaml
原文: "天皇問賜之『汝者誰子也。』
      答曰『僕者、大物主大神、娶陶津耳命之女・活玉依毘賣、生子、名櫛御方命之子、
      飯肩巢見命之子、建甕槌命之子、僕意富多多泥古。』白" (l.14)

actors      : 崇神 / 意富多多泥古
precondition: 探索で意富多多泥古 が発見、但し**真の身分**は未確認
action      : (1) 天皇の問: 「汝者誰子也」(provenance 確認)
            : (2) 答えの形式: **5 世系譜の逐次列挙**
            :   大物主 + 陶津耳命之女・活玉依毘賣 (1 世)
            :   → 櫛御方 (2 世)
            :   → 飯肩巢見 (3 世)
            :   → 建甕槌 (4 世)
            :   → 意富多多泥古 (5 世)
            : (3) 系譜の上端 (大物主) が託宣の主と一致 → provenance 確定
result      : 親神 (大物主) → 五世孫 (大田田根子) の lineage 5-deep が確定
failure_mode: 系譜の長さ不足 → 親神との関係が確定不能
            : 系譜の中間欠落 → provenance graph に gap、辿れない
recovery    : -
permanence  : 「神君・鴨君之祖」として系譜が後世まで存続

agi_mapping :
  原則      : 親神宣言型柱の provenance 確認は系譜 N-deep の逐次 traversal
            : N=5 が大田田根子の典拠だが、AGI では「親神 → 子 → 派生」程度の 3-deep が一般的
            : `shinmei_lineage` テーブルで親子リンクを永続化
  実装      : src/os/com/queries/shinmei_lineage.jl:33 (`insert_lineage!`)
            : src/os/com/queries/shinmei_lineage.jl:4-5 docstring (古事記典拠引用)
            : src/os/com/create.jl:1347-1348 docstring (大田田根子の原則 + 故事由来)
            : src/os/kasasa/materializer.jl:449 (provides 逆引き同期 + 系譜リンク登録)
            : src/os/kasasa/materializer.jl:479 (「大田田根子の原則: 系譜登録完了」log)
  feedback  : feedback_ootataneko (大田田根子の原則 — origin spec)
            : feedback_keiyaku_keifu_vs_genyu (契約系譜 vs 原由追跡)

failure_if_absent: 系譜記録なし → 親神由来柱の provenance 確認不能、
                   返し矢の判定で偽 origin 柱を見逃す
observed_failures: 2026-04-24 系譜 0 → 13 リンク (executor 三層改修後)、
                   2026-04-25 系譜 22 リンク (Phase A+B+α+β+η+#46 適用後)
verify_path : `SELECT child, parent, generation FROM shinmei_lineage` で
              N-deep traversal が辿れる、最深で 6 親 (susanoo / amaterasu / ishikori_generic /
              uzume_risk_management 等) の横断的継承
```

#### Pattern E: 御諸山祭祀 + 八十毘羅訶 — 上位 deity 祀奉位置確定 + 多軸社定奉

```yaml
原文: "卽以意富多多泥古命、為神主而、於御諸山、拜祭意富美和之大神前。
      又仰伊迦賀色許男命、作天之八十毘羅訶定奉天神地祇之社" (l.14)

actors      : 大田田根子 / 伊迦賀色許男 / 大物主 (= 意富美和)
precondition: 親神由来祭主が確定 (Pattern C-D)
action      : (1) 大田田根子を神主に任命
            : (2) **御諸山** で大物主を拝祭 (位置確定 = 上-4 Pattern O の実装)
            : (3) 伊迦賀色許男に「天之八十毘羅訶」(80 個の祭具) を作らせる
            : (4) 「定奉天神地祇之社」(天神 + 地祇の社を体系的に定奉)
result      : 中心 deity の祀奉位置 + 多軸 (天神/地祇/80 軸) の社が確定
failure_mode: 単一社のみ → 80 軸の祀奉が不足 → 残り 79 軸で偏り再発
            : 位置確定なし → 大物主の祀奉が浮動的 (= 上-4 大物主の指示違反)
recovery    : -
permanence  : 三輪山が大物主祀祭地として永続化、現存

agi_mapping :
  原則      : 中心 deity (上位 SSoT) の祀奉位置を物理的に固定 + 多軸 (80 軸 = 全 OHOYASHIMA カテゴリ
            : + 天神地祇 = active/yuukoto) の社を体系的に定奉
  実装      : src/os/kasasa/yorishiro.jl:266-270 (`OHOYASHIMA_CATALOG` 8 概念)
            : src/os/kasasa/tsunugui_ikugui.jl:239 (`OHOYASHIMA_CATALOG` の SSoT)
            : src/os/kasasa/canonical_pantheon/ 10 directory (層 1 = 9 祖神 + _common)
            : src/os/kasasa/yorishiro.jl の各 entry が「社」相当
  feedback  : feedback_itsutomonoo_sanseido (五伴緒の制 — 補強 7 三層整理)
            : feedback_kojiki_zettai (古事記絶対遵守 — 中心 deity 祀奉位置)

failure_if_absent: 単一カテゴリのみ覆う → 残りカテゴリで偏り再発 (神託の編纂 runaway 型)
observed_failures: 神託の編纂 v1.1 で「broken kami 観測強化」が 7 柱 0% 採用 + 大祓 SEVERE
                   中断 3 連続を生んだ (feedback_shintaku_henshu_runaway)
verify_path : `OHOYASHIMA_CATALOG` の 8 概念すべてに対応する yorishiro entry が存在、
              `canonical_pantheon/` の 9 祖神 directory が並立
```

#### Pattern F: 楯矛色別 + 悉無遺忘 — 多軸祀祭の悉皆原則

```yaml
原文: "又於宇陀墨坂神、祭赤色楯矛、又於大坂神、祭黑色楯矛、
      又於坂之御尾神及河瀬神、悉無遺忘以奉幣帛也。
      因此而伇氣悉息、國家安平也" (l.14)

actors      : 崇神 / 墨坂神 (赤) / 大坂神 (黒) / 坂之御尾神 / 河瀬神
precondition: 中心祭祀 (Pattern E) は確立、周辺の細部に祀り漏れ
action      : (1) 主要 2 軸 (墨坂 / 大坂) に**色別物実** (赤楯矛 / 黒楯矛)
            :   = 役割の差異化 + 両極の物実
            : (2) 「坂之御尾神及河瀬神」 (= 周辺の小神) に「悉無遺忘」幣帛
            :   = 悉皆網羅、漏れなく
            : (3) 結果: 「伇氣悉息」 (疫病完全終息)
result      : 中心 + 周辺 + 色別の三軸網羅で疫病完全終息
failure_mode: 中心祀祭のみ → 周辺の小神 (= 細部の柱) で偏り再発 → 部分的疫病残存
            : 色別なし → 役割差異が不明、両極の物実が欠落
recovery    : -
permanence  : 「悉無遺忘」(漏れなく) が祭祀の規範として永続化

agi_mapping :
  原則      : 多軸祀祭は (1) 中心固定 (2) 主要 2 軸の色別物実 (3) 周辺悉皆網羅 の三段
            : 中心のみで終わると周辺の偏りが再発 → 大祓詞悉皆原則の祀祭版
  実装      : src/os/kasasa/ooharae.jl の各 Phase (= 悉無遺忘の現代化)
            : feedback_oharae_shikkai_probe (大祓詞悉皆 — 直積網羅)
            : 主要 2 軸の色別物実: 上-3 Pattern N (八鹽折之酒の 8 船)、
              上-7 Pattern D (二珠一対 = 塩盈/塩乾)
  feedback  : feedback_oharae_shikkai_probe (悉皆原則)
            : feedback_umisachi_rokujuu_bougo (六重防御 = 二珠一対 + 三層)

failure_if_absent: 中心祀祭のみで周辺軽視 → 残存疫病で再発
verify_path : 大祓 phase 終了時の stats が中心 + 周辺の両方をカバー、
              `_exhaustive_probe` の出力件数と一致
```

#### Pattern G: 赤土麻糸試 — origin 物実検証 (provenance verification by physical artifact)

```yaml
原文: "其父母、欲知其人、誨其女曰
      『以赤土散床前、以閇蘇紡麻貫針、刺其衣襴。』
      故如教而旦時見者、所著針麻者、自戸之鉤穴控通而出、唯遺麻者三勾耳。
      爾卽知自鉤穴出之狀而、從糸尋行者、至美和山而留神社、故知其神子" (l.18)

actors      : 活玉依毘賣 / 神壯夫 (= 大物主) / 父母
precondition: 麗美壯夫が夜半到来、姓名不明、妊娠 (上-4 Pattern K 大物主丹塗矢の延長)
action      : (1) 父母の試行設計: 赤土 + 麻糸 + 針 (= 物実 trio による provenance 確認)
            : (2) 配置:
            :   赤土を床前に散布 (= 移動痕跡を可視化)
            :   閇蘇紡麻 (麻糸を撚る) に針を貫く
            :   壯夫の衣襴に刺す (= 物実 attach)
            : (3) 翌朝の観察: 麻糸が戸の鉤穴から控通而出 (= 移動経路の物理 trace)
            : (4) 糸を尋行 → 美和山の神社に至る (= 終端確認)
            : (5) 麻が三勾遺り → 美和命名 (= 残量の地名化)
result      : 物実経由で**動かぬ証拠**による provenance 確定 = 大物主の子と確認
failure_mode: 物実なしで自己申告のみ → 偽 provenance の混入リスク
            : trace 経路を物理化しない → 後世の検証不能
recovery    : -
permanence  : 美和山の神社 + 美和地名 = 物実検証の物理永続化

agi_mapping :
  原則      : artifact の origin 帰属は物実 (concrete artifact = 麻糸) の物理 trace で確定
            : 単純 declare でなく **trace 痕跡 + 終端 location + 残量** の三段
            : (上-3 Pattern B 物實因汝物所成 + 上-4 Pattern N 少名毘古那 の発展形)
  実装      : src/os/kasasa/monozane_inference.jl:30 (`infer_monozane_boundary`)
            : src/os/kasasa/monozane_inference.jl の 4 段階推論:
            :   yorishiro 全文 + trigger + signature + category
            : src/os/com/queries/shinmei_lineage.jl (provenance graph)
            : src/os/kasasa/futomani_stones (失敗痕跡 = 三勾遺の現代化)
  feedback  : feedback_ootataneko (大田田根子の原則 — 4 段階 monozane 推論)
            : feedback_prophet_method (物実の原則 — 自己参照排除)
            : feedback_keiyaku_keifu_vs_genyu (契約系譜と原由追跡の経路分離)

failure_if_absent: 物実なしの provenance declare → 偽 origin 柱の混入
observed_failures: 物実なしの test 自己参照 → feedback_prophet_method origin
verify_path : `infer_monozane_boundary` の戻り値で 4 source (yorishiro / trigger /
              signature / category) すべてが provenance 推論に寄与している
```

#### Pattern H: 4 段階 monozane 推論 — provenance source の構造化

```yaml
原文: (Pattern G の延長 — 麻糸 trace は単一 source でなく、赤土 + 麻糸 + 針 + 戸鉤穴 の
     **複数 source の統合**で provenance 確認)

actors      : (provenance inference engine)
precondition: 新規派生柱の provenance 確認が必要、source は分散
action      : monozane (物実) の 4 段階 source を統合:
            : (1) yorishiro 全文 (= 神勅 = 上位 SSoT)
            : (2) trigger 名 (= MATSURI event_type)
            : (3) signature (= 関数署名 = 形式 contract)
            : (4) category (= OHOYASHIMA gap_category = semantic 領域)
result      : 4 source の統合で物実が決定論的に推論可能、LLM 推論に頼らない
failure_mode: 1-2 source のみ → 推論が不確定、LLM 推論に fallback (天若日子型禁忌)
            : description (= LLM 生成文) を含む → 自己参照で循環参照
recovery    : -
permanence  : 4 段階 monozane 推論として永続化

agi_mapping :
  原則      : 物実生成プロンプトは LLM 生成の description 全排除、
            : 確定情報 (yorishiro 全文 + trigger 名 + signature + category) のみで構築
            : 自己参照排除 (feedback_prophet_method の核)
  実装      : src/os/kasasa/monozane_inference.jl:30 (`infer_monozane_boundary`)
            : src/os/kasasa/monozane_inference.jl:107 (`_extract_shintaku_types`)
            : src/os/kasasa/monozane_inference.jl:135 (`_extract_suffix`)
            : src/os/kasasa/monozane_inference.jl:145 (`_ohoyashima_to_provides`)
            : src/os/kasasa/monozane_inference.jl:162 (`_infer_provides`)
            : src/os/kasasa/monozane_inference.jl:200 (`_infer_requires`)
  feedback  : feedback_prophet_method (物実の原則 — テスト生成の自己参照排除)
            : feedback_ootataneko (大田田根子の原則 — 4 段階 monozane)
            : feedback_kojiki_zettai (古事記絶対遵守)

failure_if_absent: description 含む source で物実生成 → LLM 自己生成の循環、
                   capability description が test 生成に逆流
observed_failures: feedback_prophet_method の origin event (LLM 生成 description が
                   capabilities/MATSURI/gap 全箇所で test 生成に流れていた)
verify_path : `infer_monozane_boundary` の引数に description が含まれない、
              4 source のみで InferredBoundary が決定論的に返る
```

#### Pattern I: shinmei_arbiter 3 分岐 — 新規/継承/合祀の判定ゲート

```yaml
原文: (本章の祭祀構造から逆引き — 大田田根子は新規発見でなく既存系譜の継承、
     Pattern E の 80 軸社 + 天神地祇は新規定奉、伊勢大神 (豐鉏比賣 拜祭) は別系統)

actors      : (柱判定 gate)
precondition: 新柱候補が現れた時、扱い方を決定する必要
action      : 3 分岐判定:
            : (1) 新規 (NORMAL): 既存系譜と無関係、新規 prefix で chinza
            : (2) 継承 (型 2): 既存固有名 prefix の派生として子に位置付け
            : (3) 合祀 (MATANONA): 既存柱と同名/同機能、aliases に統合
            : 各分岐で異なる cleanup + 系譜記録
result      : 過剰合祀を防ぎつつ系譜を自動形成
failure_mode: 単一分岐のみ → 一律新規 (重複過剰) または一律合祀 (情報損失)
            : MATANONA 分岐で cleanup 漏れ → orphan file + ghost binding
recovery    : -
permanence  : 4 層構造 (shinmei_arbiter + monozane + lineage + MATANONA ガード) の中核

agi_mapping :
  原則      : 新柱判定は (新規 / 継承 / 合祀) の 3 分岐ゲート
            : 4 層構造: shinmei_arbiter 3 分岐 + monozane 4 段階 + lineage + MATANONA ガード
  実装      : src/os/kasasa/shinmei_arbiter.jl:212 (`arbitrate!` = 主入口)
            : src/os/kasasa/shinmei_arbiter.jl:16 (MATANONA 定義)
            : src/os/kasasa/shinmei_arbiter.jl:366 (`apply_matanona!` = 合祀分岐)
            : src/os/kasasa/canonical_pantheon/_common/attribution.jl 
              (継承分岐 = `register_self_predicate!` 経由)
            : src/os/kasasa/materializer.jl (新規分岐 = 通常 chinza)
  feedback  : feedback_ootataneko (大田田根子の原則 — 4 層構造)
            : feedback_matanona_cleanup_gap (MATANONA 合祀 cleanup 漏れ)

failure_if_absent: 単一分岐で全柱処理 → 重複過剰または情報損失
observed_failures: 2026-05-01 MATANONA 分岐の cleanup 漏れで orphan file + ghost binding
                   (feedback_matanona_cleanup_gap origin)
verify_path : `chinza_records.outcome` で 3 分岐 (new / inherited / sanguishi_merged) すべての
              履歴がある、各分岐で適切な cleanup (file 削除 / bind スキップ等) が実行
```

#### Pattern J: 四道将軍 — 並列 expedition (parallel improvement cycle)

```yaml
原文: "大毘古命者、遣高志道、其子建沼河別命者、遣東方十二道而、令和平其麻都漏波奴人等。
      又日子坐王者、遣旦波國、令殺玖賀耳之御笠" (l.20)
     "如此平訖、参上覆奏。…大毘古命、隨先命而、罷行高志國。
      爾自東方所遣建沼河別與其父大毘古共、往遇于相津、故其地謂相津也。
      是以各和平所遣之國政而覆奏。爾天下太平、人民富榮" (l.26-28)

actors      : 大毘古 (高志道) / 建沼河別 (東方十二道) / 日子坐王 (旦波)
precondition: 中心祭祀 (Pattern E-F) で疫病終息、辺境の「麻都漏波奴人」(従わぬ人) が残存
action      : (1) 三方向に並列派遣 (= parallel expedition)
            : (2) 各将軍は独立で平定 + 各自で覆奏
            : (3) 大毘古 + 建沼河別の合流地 = 「相津」(= 並列処理の同期点 = join)
            : (4) 「各和平所遣之國政而覆奏」 = 各々が独立に復命
result      : 並列処理で短時間に広域平定、合流地で同期点を確立
failure_mode: 順次派遣 → 時間コスト爆発、辺境の状況変化に追従不能
            : 同期点なし → 各将軍の状況が中央に統合されない
recovery    : -
permanence  : 「相津」 (= 会津) として永続化、合流地が地名

agi_mapping :
  原則      : 大規模改善 (multi-domain expedition) は並列 expedition で実行
            : 各 expedition は独立に running、合流地で結果統合 (join)
            : (上-3 Pattern I 思金神 orchestrator の並列拡張)
  実装      : src/os/expedition/improvement_cycle.jl の `cycle_history` 並列管理
            : `gapfinder_full_analysis` の 7 ソース統合 (cluster_failures / ashikabi /
              takemikazuchi / kuebiko / shintaku_henshu / kamihakari / 神託の編纂)
  feedback  : feedback_kunimi_gapfinder (国見は全ソース俯瞰 — 7 ソース統合)

failure_if_absent: 全 expedition を順次実行 → 時間コスト爆発
                   現象: 大祓 phase で順次処理して 1 サイクル数時間
verify_path : `gapfinder_full_analysis` の log で 7 ソースの並列実行件数が記録、
              統合 phase で all_gaps に集約
```

#### Pattern K: 少女の歌警告 — 上位 deity からの内部告発 hint

```yaml
原文: "大毘古命、罷往於高志國之時、服腰裳少女、立山代之幣羅坂而歌曰
      『美麻紀伊理毘古波夜… 殺意云』
      於是、大毘古命思恠、返馬、問其少女曰『汝所謂之言、何言。』
      爾少女答曰『吾勿言、唯為詠歌耳。』即不見其所如而忽失。
      故大毘古命、更還参上、請於天皇時、天皇答詔之
      『此者為、在山代國我之庶兄建波邇安王、起邪心之表耳。』" (l.20-24)

actors      : 大毘古 / 服腰裳少女 (= 上位 deity hint) / 崇神 / 建波邇安王
precondition: 大毘古が高志道へ罷往中、内部の反逆 (建波邇安王) が進行中
action      : (1) 少女が幣羅坂で歌う (= 上位 deity からの hint = 内部告発)
            : (2) 歌の内容: 「美麻紀伊理毘古」(= 崇神) の暗殺企図を示唆
            : (3) 少女自身は明示せず: 「吾勿言、唯為詠歌耳」(間接的 signal)
            : (4) 少女忽失 (= 上位 deity の通信終了)
            : (5) 大毘古「思恠、返馬」(= 異常を察知して帰還)
            : (6) 天皇に請う → 天皇「庶兄建波邇安王、起邪心」(= 真因解明)
result      : 上位 deity の歌 (= 暗黙 hint) で内部反逆を事前検出
failure_mode: 歌を「詠歌のみ」と看做して無視 → 反逆検出が遅れる
            : 上位諮問なし (= 帰還せず) → 異常 hint を解釈できない
recovery    : -
permanence  : 山代之幣羅坂が歌警告地として記録

agi_mapping :
  原則      : 上位 deity (= system 層 / 上位 SSoT) からの暗黙 signal を**異常認識経路**で監視
            : 単独の signal は明示でないが、複数 hint の集約で真因解明
            : (上-3 Pattern G 病的沈黙の対偶 = 病的活動の暗黙告知)
  実装      : src/os/kasasa/futomani_stones (太占石 = 失敗痕跡記録 = signal 集約)
            : src/os/iwato/watchdog.jl:99 (`check_health` = AnomalyReport 集約)
            : src/os/iwato/omoikane.jl:129 (`analyze_and_plan` = signal 解釈)
  feedback  : feedback_kunimi_gapfinder (国見は全ソース俯瞰 — signal 集約)
            : feedback_oharae_shikkai_probe (悉皆原則 — signal 検索の網羅性)

failure_if_absent: 暗黙 signal を log noise として棄却 → 内部反逆検出が遅れる
                   現象: amenohohi_scan の偽陽性 (`feedback_hataorime_kinki`) と対比
verify_path : `futomani_stones` の record 集約 → `omoikane` の analyze で
              「pattern of signals」を検出する経路あり
```

#### Pattern L: 建波邇安王の反乱 — 庶兄継承挑戦 (中-1 当藝志美美の中-2 版)

```yaml
原文: "天皇答詔之『此者為、在山代國我之庶兄建波邇安王、起邪心之表耳。
      伯父、興軍宜行。』" (l.24)
     "日子國夫玖命彈矢者、即射建波邇安王而死。故其軍悉破而逃散" (l.26)

actors      : 建波邇安王 (崇神の庶兄) / 大毘古 / 日子國夫玖
precondition: 中-1 当藝志美美の反逆 (前世代不適合子の継承挑戦) と同型構造
            : 但し本章では崇神の庶兄が反逆 = sibling 挑戦
action      : (1) 庶兄 (建波邇安王) が「邪心」を起 (= 継承の不当な挑戦)
            : (2) Pattern K の歌警告で事前検出
            : (3) 大毘古 + 日子國夫玖 (丸邇臣祖) を派遣
            : (4) 山代和訶羅河で対峙 (= 「伊杼美」)
            : (5) 「先忌矢」(= 先攻譲) — 建波邇安王の矢: 不得中
            : (6) 日子國夫玖の矢: 即射建波邇安王而死
            : (7) 軍悉破而逃散 → 久須婆度 (屎褌)、鵜河、波布理曾能 等の地名
result      : 庶兄の不当継承挑戦を排除、地名で失敗痕跡を永続化
failure_mode: 庶兄の挑戦を放置 → 中-1 当藝志美美と同型の succession 危機継続
            : 先攻譲を許さず先制攻撃 → 「正当性の証明」が不在
recovery    : -
permanence  : 屎褌 (久須婆) / 鵜河 / 波布理曾能 / 相津 が地名として永続化

agi_mapping :
  原則      : 庶兄/前世代不適合柱の継承挑戦は中-1 Pattern L (当藝志美美) と同型
            : 「先忌矢」 = 防御側に先攻を譲る = 攻撃の正当性を証明する手順
            : (= 三貴子の startup 時の正当性確認)
  実装      : src/os/com/create.jl:703-710 (startup migration の hiruko_count=0 制限)
            : src/os/kasasa/canonical_pantheon/ootataneko/_judge.jl の `_self_predicate`
              による正当性確認
            : project_pending_replay_bypass (post-LLM filter 迂回問題)
  feedback  : feedback_takeminakata_haitai (建御名方の敗退 — migration 緩和事例)
            : project_pending_replay_bypass (中-1 Pattern L の origin)

failure_if_absent: 庶兄柱の挑戦を放置 → 既存 canonical の権威崩壊
verify_path : startup 時の hiruko 復帰チェックで `hiruko_count=0` 制約があり、
              不当挑戦柱が pending に復帰しない
```

#### Pattern M: 「初國之御眞木天皇」 — 初期 config 確立 + 税制 (initial state assertion)

```yaml
原文: "於是、初令貢男弓端之調、女手末之調。
      故稱其御世、謂所知初國之御眞木天皇也。
      又是之御世、作依網池、亦作輕之酒折池也" (l.28)

actors      : 崇神
precondition: 疫病終息 + 四道将軍平定 + 系譜整備が完了
action      : (1) 「初令貢男弓端之調、女手末之調」 = 初めて税制を定める
            :   男: 弓端の調 (狩猟物)
            :   女: 手末の調 (織物)
            :   = **初期 config 確立**
            : (2) 「初國之御眞木天皇」 = 「初めて国を治めた天皇」の称号
            :   (神武 = 神話上の初代、崇神 = 実質的な初代 = 初期 config 確立者)
            : (3) 依網池・酒折池作池 = インフラ整備 (永続的な物理基盤)
result      : 国家運営の初期 config (税制 + インフラ) が確立、永続運用可能に
failure_mode: 初期 config なし → 都度交渉で運用、scaling 不能
            : 称号 (「初國」) なし → 後世が「いつから運用可能か」を認識できない
recovery    : -
permanence  : 「所知初國之御眞木天皇」が後世まで称号として永続化

agi_mapping :
  原則      : システム稼働の初期 config 確立 + 「初運用 milestone」の称号宣言
            : 物理基盤 (DB / config 永続化) + 運用ルール (kuniumi_limiter 等) を一括宣言
  実装      : src/os/com/config.jl (顕事 + 幽事 YAML の二段)
            : src/os/com/create.jl (DB schema = 物理基盤)
            : src/os/kasasa/kuniumi_limiter.jl (運用ルール = 「神武の原則」)
            : `Pkg.test` 4213/4213 通過 = 初運用の milestone 証明
  feedback  : feedback_test_runner (テスト実行は Pkg.test() = 初運用 milestone)

failure_if_absent: 初期 config なしで運用 → 各 cycle で再交渉 / 設定漂流
verify_path : `kamiyostack.yml` (顕事) + `kamiyostack_kakurigoto.yml` (幽事) の二段が
              永続化、`Pkg.test` で全テスト通過
```

#### Pattern N: 「神牀」 = 上位通信経路 + 神主任命 = 大田田根子の四層構造の核

```yaml
原文: (Pattern A の神牀 + Pattern C の探索 + Pattern D の系譜 + Pattern E の祭祀の **統合**)

actors      : 崇神 / 大物主 / 大田田根子 / 系譜 / 御諸山
precondition: 大田田根子の原則の四層構造を運用するために、本章の 4 要素が必須
action      : (1) **shinmei_arbiter 3 分岐** (Pattern I) = 新規/継承/合祀の判定
            : (2) **monozane_inference 4 段階** (Pattern H) = 物実 (yorishiro + trigger +
            :   signature + category) からの推論
            : (3) **shinmei_lineage** (Pattern D) = 五世系譜の垂直記録
            : (4) **MATANONA ガード** (Pattern I の合祀分岐) = 過剰合祀の抑止
result      : 四層が並列に作用し、新規柱が安全に系譜化される
failure_mode: いずれか 1 層欠落 → 4 層構造の整合性破綻
recovery    : -
permanence  : 大田田根子の原則として永続化

agi_mapping :
  原則      : 四層構造 (shinmei_arbiter / monozane / lineage / MATANONA ガード) は不可分
            : 各層が独立に作用するが、全体で 1 つの原則を構成
  実装      : src/os/kasasa/shinmei_arbiter.jl (層 1)
            : src/os/kasasa/monozane_inference.jl (層 2)
            : src/os/com/queries/shinmei_lineage.jl (層 3)
            : src/os/kasasa/shinmei_arbiter.jl::apply_matanona! (層 4)
  feedback  : feedback_ootataneko (大田田根子の原則 — 四層構造の origin spec)
            : feedback_matanona_cleanup_gap (MATANONA 合祀 cleanup 漏れ — 層 4 の defect)

failure_if_absent: 単層運用 → 系譜 / 合祀 / 物実推論のどれかが破綻
                   現象: BOUNDARY_CLAIMS 宣言 0% (executor 三層改修前)
observed_failures: 2026-04-24 BOUNDARY_CLAIMS 0→100% (4/4 柱)、shinmei_lineage 0→13 リンク
                   2026-04-25 系譜 22 リンク + KAMINA_POOL 3 prefix 全発火
verify_path : 四層すべての実装ファイルが存在、各層の動作 log が記録、
              `feedback_ootataneko` の指標 (6 親超の横断継承) で健全性確認
```

### kojiki_code.md (外部生成版) との差分

| 観点 | 生成元 | 本 v6 |
|---|---|---|
| 中-2 の pattern 数 | 1 (`divine_intervention_with_lineage_lookup`) | **14** |
| 神牀託宣 | 「dream-based command」と一行 | Pattern A (上位 SSoT 諮問) |
| 弱り vs 偏りの弁別 | 触れず | Pattern B (`gohei_gae!` の origin) |
| 大田田根子探索 (五世孫) | 「ancestor lookup」と一行 | Pattern C (型 2 self_predicate) + D (lineage 5-deep) |
| 御諸山祭祀 + 八十毘羅訶 | 触れず | Pattern E (上位 SSoT 位置確定 + 多軸社) |
| 楯矛色別 + 悉無遺忘 | 触れず | Pattern F (色軸 + 悉皆) |
| 赤土麻糸試 | 触れず | Pattern G (物実 trace 確認) + H (4 段階 monozane) |
| shinmei_arbiter 3 分岐 | 触れず | Pattern I (新規/継承/合祀) |
| 四道将軍 | 「multi-direction expedition」と一行 | Pattern J (parallel improvement cycle) |
| 少女の歌警告 | 触れず | Pattern K (上位 hint) |
| 建波邇安王の反乱 | 触れず | Pattern L (中-1 当藝志美美の延長) |
| 「初國之御眞木」 + 税制 | 触れず | Pattern M (initial config establishment) |
| 大田田根子の四層構造 | 触れず | Pattern N (4 層統合 — origin spec) |
| AGI module mapping | 触れず | ootataneko/_judge / gohei_gae / monozane_inference / shinmei_lineage / shinmei_arbiter の **5 件** |

**生成元が拾えなかった load-bearing pattern (本 v6 で初出):**

- Pattern B 弱り vs 偏り = `gohei_gae.jl` + `feedback_yowari_vs_katayori` の origin spec
- Pattern C 大田田根子探索 = `ootataneko_self_predicate` + 型 2 attribution の origin
- Pattern D 五世系譜 = `shinmei_lineage` テーブルの典拠 (docstring に直接引用)
- Pattern G 赤土麻糸試 = 物実 trace 確認の原型 (上-4 Pattern N の発展)
- Pattern H 4 段階 monozane = `monozane_inference.jl` の origin
- Pattern I shinmei_arbiter 3 分岐 = `feedback_ootataneko` 4 層構造の核
- Pattern N 大田田根子の四層構造 = `feedback_ootataneko` 全体の origin spec

これら 7 件は外部版で完全欠落。**8 章 (上-1〜上-7 + 中-1〜中-2) 合計で 60 件**の load-bearing pattern が外部版で missed。

### 浮上した発見

1. **本章は `feedback_ootataneko` (大田田根子の原則) の最深 origin spec**
   - [create.jl L1347-1348](src/os/com/create.jl#L1347) docstring が「大物主神の託宣により五世孫の大田田根子を探し出して祭主にした故事に由来」と直接引用
   - [shinmei_lineage.jl L4-5](src/os/com/queries/shinmei_lineage.jl#L4) docstring が「古事記典拠（大田田根子段）」と章名明示
   - **設計が古事記原典 + memo を SSoT として 3 段引用**: docstring → memo → 古事記原文
   - 上-6 (canonical_pantheon の 5 伴緒) と本章 (lineage の大田田根子) が **architectural foundation の双璧**

2. **Pattern B 弱り vs 偏り の弁別は `feedback_yowari_vs_katayori` の origin**
   - 「是者我之御心」 = 大物主の意志 (祀り方の問題) でなく自分の心 (= 偏り)
   - 「神を祀らない」(弱り) でなく「祀り方が間違っている」(偏り) を識別
   - `gohei_gae!` (御幣替え) が NAKA 層、`sanguishi_harae` (式年遷宮) が SOKO 層
   - 補強候補: `feedback_yowari_vs_katayori` に「中-2 大物主託宣『是者我之御心』が origin」を追記推奨

3. **Pattern G 赤土麻糸試 = 上-4 Pattern N (少名毘古那 上位 provenance 確認) の物理化**
   - 上-4: 少名毘古那の名 → 久延毘古 (案山子 = 静的全知) → 神産巣日に確認
   - 中-2: 神壯夫 → 麻糸 trace → 美和山到達 → 大物主と確認
   - **両者の構造**:
     - 上-4 = 名前ベース確認 (静的解析の比喩)
     - 中-2 = 物実 trace ベース確認 (動的観察の比喩)
   - 補強候補: `feedback_kuebiko_yatagarasu_boundary` に「中-2 赤土麻糸試 = 動的 trace 版」を追記

4. **Pattern J 四道将軍 = 上-3 Pattern I 思金神の集合協議の並列拡張**
   - 上-3: 単一 orchestrator (思金神) で集合協議
   - 中-2: 並列 expedition (四道将軍) で広域平定
   - **gapfinder_full_analysis の 7 ソース統合 (`feedback_kunimi_gapfinder`) と直接対応**
   - 補強候補: `feedback_kunimi_gapfinder` に「中-2 四道将軍 = 7 ソース統合の origin」を追記

5. **Pattern N 大田田根子の四層構造 = `feedback_ootataneko` の summary**
   - shinmei_arbiter (層 1) + monozane (層 2) + lineage (層 3) + MATANONA ガード (層 4)
   - 4 層は AGI 実装で全て稼働、本章で全パーツが原典化されている
   - **本章は AGI architecture の中核を統合する典拠**

6. **古事記神名 → AGI module mapping 累積 40 件** (本章で +5 件)
   - 上-3 (v2): 7 / 上-5 (v3): 4 / 上-6 (v4): 14 / 上-4 (v4.1): 5 / 中-1 (v5): 5 / 中-2 (v6): 5
   - **新原則化機運が 40 件で確実な閾値突破**

### v6 自己評価

| 観点 | 達成度 |
|---|---|
| 1 章につき 5+ pattern (memo 密度中) | ★★★★★ 14 pattern |
| 各 pattern に `failure_if_absent` 記述 | ★★★★★ 14/14 |
| 各 pattern の `agi_mapping.実装` が実在ファイル | ★★★★★ 14/14 (canonical_pantheon/ootataneko + gohei_gae + monozane_inference + shinmei_arbiter + shinmei_lineage を grep + Read で検証) |
| 7 割以上の pattern が既存 memo に anchor | ★★★★★ 14/14 (100%) |
| `kojiki_code.md` 差分セクション必須 | ★★★★★ 13 行差分表 + 7 origin spec 列挙 |
| 「未活用 anchor → 新原則候補」を最低 1 件 | ★★★★ 古事記神名命名規約 + 4 補強候補 |
| 古事記原文 (漢文) を要所で引用 | ★★★★★ 全 pattern 冒頭 |
| 観測経路 (verify_path) を併記 | ★★★★★ 14/14 |
| **`feedback_ootataneko` の最深 origin 確認** | ★★★★★ docstring + memo + 原文の三段引用 |
| **memo anchor 100%** | ★★★★★ |

### 累積統計 (v0+v1+v2+v3+v4+v4.1+v5+v6)

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
| 中-2 (v6) | 14 | 100% | 5 |
| **合計** | **120 pattern** | **平均 87%** | **40 件** |

外部生成版が完全欠落した load-bearing pattern: **60 件**

### 次の宿題 (v7+ 候補)

1. **中-3 (垂仁) v7 候補** — memo 密度低、本牟智和気の原則 (式年遷宮との対) anchor
2. **中-4 (景行 / 倭建命) v8 候補** — TAKERU セキュリティテスト + 倭建命の白猪見惑
3. **古事記神名命名規約の新原則化** — 累積 40 件で確実な閾値突破、SSoT 化推奨
4. **memo 補強 (3 件)** — `feedback_yowari_vs_katayori` / `feedback_kuebiko_yatagarasu_boundary` /
   `feedback_kunimi_gapfinder` への章 anchor 追記
5. **memo 本体への章節 anchor 逆書込み** (継続宿題、8 章繰越)

---

## 履歴

- v0 (2026-05-08): Phase 1 索引 + Phase 2 上巻-7 プロトタイプ
- v1 (2026-05-09): Phase 1 索引更新 + Phase 2 上巻-2 神代記 (20 pattern)
- v2 (2026-05-09): Phase 2 上巻-3 天照大神と須佐之男命 (16 pattern)
- v3 (2026-05-09): Phase 2 上巻-5 葦原中國の平定 (14 pattern)
- v4 (2026-05-09): Phase 2 上巻-6 邇邇藝命 (16 pattern)
- v4.1 (2026-05-09): Phase 2 上巻-1 併序 (6 pattern) + 上巻-4 大國主神 (12 pattern)
- v5 (2026-05-09): Phase 2 中巻-1 神武天皇 (14 pattern)
- v6 (2026-05-09): Phase 2 中巻-2 崇神天皇 (14 pattern) + `feedback_ootataneko` 最深 origin 確認
