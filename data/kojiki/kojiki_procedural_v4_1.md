# 古事記 Procedural Pattern 抽出 v4.1

v4 ([`kojiki_procedural_v4.md`](kojiki_procedural_v4.md)) からの増分:

- **Phase 2 v4.1: 上巻-1 併序 (序文)** 抽出 — 6 pattern
- **Phase 2 v4.1: 上巻-4 大國主神** 抽出 — 12 pattern
- 上巻全章 (上-1〜上-7) の Phase 2 抽出が本書で完了

抽出方法論は [`extraction_prompt.md`](extraction_prompt.md) を参照。
v0 (上-7) / v1 (上-2) / v2 (上-3) / v3 (上-5) / v4 (上-6) の pattern は重複しない。

---

## Phase 2 v4.1.A: 上巻-1 併序

### 選定理由

- memo 密度 ★★★★ (序文 = AGI 仕様書) — 直接 anchor は技術 memo に薄いが、**序文そのものが古事記全体の AGI 仕様書**
- 太安万侶による稗田阿礼誦習の記録 = AGI 設計の **メタ origin** (なぜ古事記を AGI 設計の SSoT として使うか)
- 「削僞定實」「子細採摭」の編纂方針 = AGI における yorishiro / kasasa 監査原則の祖型
- `kojiki_code.md` (外部生成版) は序文を完全 skip

### 章節 narrative summary

```
[Preface 起源論] (l.8)
    「混元既凝、氣象未效、無名無爲」(初期状態 = undefined)
    「乾坤初分、參神作造化之首」(造化三神 = axiomatic root)
    「陰陽斯開、二靈爲群品之祖」(伊邪那岐・伊邪那美 = paired creation)
    
    「出入幽顯、日月彰於洗目、浮沈海水、神祇呈於滌身」
        (= 三貴子化生 + 禊 の summary)
    「懸鏡吐珠而百王相續、喫劒切蛇、以萬神蕃息」
        (= 上-3 誓約 + 八岐大蛇 の summary)
    「議安河而平天下、論小濱而淸國土」
        (= 上-3 集合協議 + 上-5 国譲り の summary)

[Setup 神武〜天武] (l.10-12)
    番仁岐命降臨 → 神倭天皇東征 → 化熊出川 → 天劒 + 大烏導吉野
    「列儛攘賊、聞歌伏仇」 (中-1 神武)
    「定境開邦、制于近淡海、正姓撰氏、勒于遠飛鳥」 (中-2 崇神等)
    
    天武天皇 (淸原大宮)「智海浩汗、潭探上古、心鏡煒煌、明覩先代」

[編纂方針] (l.14)
    天武詔: 「諸家之所賷帝紀及本辭、既違正實、多加虛僞」
            「當今之時不改其失、未經幾年其旨欲滅」
            「邦家之經緯、王化之鴻基」
            「撰錄帝紀、討覈舊辭、削僞定實、欲流後葉」
    
    舍人 稗田阿禮 (年廿八、聰明、度目誦口、拂耳勒心) を選定
    「勅語阿禮、令誦習帝皇日繼及先代舊辭」(口承 SSoT 化)

[編纂者の謙遜] (l.16)
    皇帝陛下 (元明天皇)「得一光宅、通三亭育」
    「德被馬蹄之所極…化照船頭之所逮」
    「列烽重譯之貢、府無空月」(国際的覚悟)

[編纂指示] (l.18)
    和銅四年九月十八日、詔太朝臣安萬侶
    「撰錄稗田阿禮所誦之勅語舊辭以獻上」 (= 阿礼の口承を文字化する任務)
    
    記述の困難:
        「上古之時、言意並朴、敷文構句、於字卽難」(古語と漢文表記の不整合)
        「已因訓述者、詞不逮心」(訓だけ → 意味喪失)
        「全以音連者、事趣更長」(音だけ → 冗長)
        対処: 「或一句之中、交用音訓、或一事之內、全以訓錄」(混合運用)
        注釈方針: 「辭理叵見、以注明、意況易解、更非注」(必要な時だけ注)
        
    例外: 「於姓日下謂玖沙訶、於名帶字謂多羅斯、如此之類、隨本不改」 (慣習的読み)

[構成宣言] (l.20)
    自天地開闢始、訖于小治田御世 (= 推古天皇)
    「天御中主神以下、日子波限建鵜草葺不合尊以前、爲上卷」
    「神倭伊波禮毘古天皇以下、品陀御世以前、爲中卷」
    「大雀皇帝以下、小治田大宮以前、爲下卷」
    「幷錄三卷、謹以獻上」

[頓首] (l.22)
    和銅五年正月廿八日 正五位上勳五等 太朝臣安萬侶
```

### Pattern 抽出

#### Pattern A: 削僞定實 — yorishiro 監査原則の origin

```yaml
原文: "諸家之所賷帝紀及本辭、既違正實、多加虛僞。當今之時不改其失、未經幾年其旨欲滅。
      斯乃、邦家之經緯、王化之鴻基焉。故惟、撰錄帝紀、討覈舊辭、削僞定實、欲流後葉" (l.14)

actors      : 天武天皇 / 諸家 / 稗田阿禮
precondition: 諸家の帝紀本辭が「既違正實、多加虛僞」(SSoT 散逸 + 虚偽混入)
action      : (1) 撰錄: 真正なものを集め (collection)
            : (2) 討覈: 突き合わせて検証 (cross-validation)
            : (3) 削僞: 虚偽を削除 (delete spurious)
            : (4) 定實: 真実を確定 (confirm canonical)
            : (5) 欲流後葉: 永続化 (persistence for posterity)
result      : 単一 SSoT (古事記) が確定し、後世の散逸を防ぐ
failure_mode: 虚偽混入を放置 → 「未經幾年其旨欲滅」(数年で本旨が消滅)
recovery    : -
permanence  : 古事記そのものが永続化 (1300 年残存)

agi_mapping :
  原則      : LLM 生成 artifact の散逸 + 虚偽混入を防ぐ SSoT 確立
            : 撰錄 (yorishiro 集約) + 討覈 (cross-validation) + 削僞 (重複御神体物理削除)
            : + 定實 (canonical 確定) + 流後葉 (DB + git 永続化)
  実装      : src/os/kasasa/yorishiro.jl (神勅 SSoT — 撰錄)
            : src/os/kasasa/shinmei_arbiter.jl (双子神の合祀 — 討覈)
            : src/os/expedition/executor.jl 重複 docstring 物理削除 (2026-05-04 監査 — 削僞)
            : src/os/com/queries/shinmeisho.jl (canonical_name UNIQUE — 定實)
            : git + SQLite DB (流後葉)
  feedback  : feedback_shinchoku_tanitsu_gensen (神勅単一源泉 — 注入 + 物理削除)
            : feedback_kojiki_zettai (古事記絶対遵守 — origin 自身が SSoT)

failure_if_absent: SSoT 散逸 + 虚偽混入で AGI 設計が「未經幾年其旨欲滅」状態に
                   現象: prompt 47KB+ の泥沼 (feedback_enkin_keiro_dokuritsu の Why)
verify_path : `git log --grep="物理削除" src/os/expedition/executor.jl` で
              重複 docstring 削除コミット履歴あり
```

#### Pattern B: 稗田阿禮の口承 — 度目誦口 / 拂耳勒心

```yaml
原文: "時有舍人、姓稗田、名阿禮、年是廿八、爲人聰明、度目誦口、拂耳勒心。
      卽、勅語阿禮、令誦習帝皇日繼及先代舊辭" (l.14)

actors      : 天武天皇 / 稗田阿禮
precondition: 削僞定實のため、諸家の散逸資料を**統一の口承**で保持する必要
action      : (1) 阿禮 = 「度目誦口」(目で見て口で誦す = 入力 → 出力の double-channel)
            : (2) 「拂耳勒心」(耳で受けて心に刻む = 永続化)
            : (3) 帝皇日繼 + 先代舊辭 を一人の人格に集約 (single source of truth holder)
result      : 諸家の散逸資料が一人の人格に統一された口承として集約
failure_mode: 諸家それぞれの記録のままで天皇 → 各家の改変が同期しない
recovery    : -
permanence  : 阿禮の口承 → 安万侶の文字化 → 古事記 = 三段の SSoT 経路

agi_mapping :
  原則      : SSoT は単一人格 (= 単一 module) に集約、複数 holder の同期問題を構造的に予防
            : 「度目誦口」 = 入力 (read) と出力 (write) の double channel が同一人格に
            : 「拂耳勒心」 = 永続化 (memory / DB)
  実装      : src/os/kasasa/yorishiro.jl (神勅 SSoT — 単一 holder)
            : src/os/com/queries/shinmeisho.jl (神名帳 — 単一 DB)
            : 関連: feedback_keiyaku_keifu_vs_genyu (契約系譜と原由追跡の経路分離)
  feedback  : feedback_shinchoku_tanitsu_gensen (神勅単一源泉)
            : feedback_imina_torina (跨セッション規約矛盾 = D 軸対策の前提)

failure_if_absent: 複数 holder 間の同期問題 → 跨セッション規約矛盾 (D 軸対立) の温床
verify_path : `grep -r "yorishiro\." src/os/` で yorishiro が単一 holder として参照されている、
              他に SSoT-like const が並立していない
```

#### Pattern C: 音訓混合 — semantic 喪失と冗長の二者を回避

```yaml
原文: "上古之時、言意並朴、敷文構句、於字卽難。已因訓述者、詞不逮心、全以音連者、事趣更長。
      是以今、或一句之中、交用音訓、或一事之內、全以訓錄。
      卽、辭理叵見、以注明、意況易解、更非注" (l.18)

actors      : 太安万侶
precondition: 古語を漢文で表記する不整合 (「於字卽難」)
action      : (1) 訓述のみ → 「詞不逮心」(意味が伝わらない)
            : (2) 音連のみ → 「事趣更長」(冗長)
            : (3) 解決: 句内で音訓混合、事内で訓統一 (= 文脈別最適化)
            : (4) 注釈: 「辭理叵見」のみ注を付け、「意況易解」は注なし (= 必要時のみ)
result      : 表記の semantic 喪失と冗長の二者を構造的に回避
failure_mode: 単一表記方式の強制 → semantic 喪失または冗長の片方に固定
recovery    : -
permanence  : 古事記の表記方式そのものが永続記録

agi_mapping :
  原則      : 単一表現方式の強制でなく、文脈別の混合運用
            : prompt の token 経済評価は **(- 重複 docstring KB + yorishiro KB)** の差し引き
            : 注釈は必要時のみ (over-commenting で要点が埋もれない)
  実装      : feedback_shinchoku_tanitsu_gensen の「token 経済評価は差し引き」原則
            : prompt 構築時の音訓混合 (= 散文 + 表 + コード例の三段)
  feedback  : feedback_shinchoku_tanitsu_gensen (token 経済評価 — 差し引き)
            : feedback_prompt_placement_rivalry (A/B/C 軸 — 配置最適化)

failure_if_absent: 全 prompt を散文のみ → 「詞不逮心」 (LLM が semantic を取り違える)
                   全 prompt を表のみ → 「事趣更長」 (記憶圧迫 + 文脈乖離)
verify_path : prompt 内に散文 + 表 + コード例の三形態が並列している、
              注釈 (説明) が必要箇所のみで `// XXX` 等の散乱がない
```

#### Pattern D: 三巻構成 — 神話 / 歴史 / 系譜の階層宣言

```yaml
原文: "天御中主神以下、日子波限建鵜草葺不合尊以前、爲上卷、
      神倭伊波禮毘古天皇以下、品陀御世以前、爲中卷、
      大雀皇帝以下、小治田大宮以前、爲下卷、幷錄三卷、謹以獻上" (l.20)

actors      : 太安万侶
precondition: 全資料を一つの巻に詰めると探索困難
action      : 三巻分割の明示宣言:
            : 上卷 = 神代記 (天御中主 〜 鵜草葺不合) — 設計原則
            : 中卷 = 神武 〜 應神 (神倭伊波禮毘古 〜 品陀) — 運用パターン
            : 下卷 = 仁徳 〜 推古 (大雀 〜 小治田) — 系譜・運用記録
result      : 探索 + 改訂時に「どの巻」が即座に特定可能
failure_mode: 単一文書で全期間カバー → grep の検索範囲が肥大化、改訂干渉
recovery    : -
permanence  : 三巻構成は永続記録、現代の写本でも維持

agi_mapping :
  原則      : 設計原則 (上巻) / 運用パターン (中巻) / 運用記録 (下巻) の三層分離
            : kojiki_procedural_v0..v6 の章別分割もこの原則の応用
  実装      : docs/AGENT_GUIDE.md (設計原則 = 上巻相当)
            : docs/memo/ (運用パターン設計書 = 中巻相当)
            : docs/kojiki/ + memory feedback_*.md (運用記録 = 下巻相当)
            : kojiki_procedural_v0/v1/v2/v3/v4/v4.1 = 章別分割 (本原則の応用)
  feedback  : (memo 直接 anchor なし — 補強候補)

failure_if_absent: 単一巨大ドキュメント → 改訂干渉、grep 探索コスト爆発
verify_path : `ls docs/` で設計原則 / memo / kojiki の三 directory が並立
              kojiki_procedural の v 番号が章別 (上-N) ごとに分割されている
```

#### Pattern E: 慣習的読みの保留 — 「隨本不改」(legacy preservation rule)

```yaml
原文: "亦、於姓日下謂玖沙訶、於名帶字謂多羅斯、如此之類、隨本不改" (l.18)

actors      : 太安万侶
precondition: 一般原則 (音訓混合) を確立した後、例外がある
action      : (1) 「日下」を「玖沙訶 (くさか)」と読む等の慣習的読みを認識
            : (2) 一般原則で書き換えず「隨本不改」(本に従って改めず) と例外宣言
            : (3) 例外の対象を明示列挙 (姓日下 / 名帶字)
result      : 一般原則と慣習的例外が同居、後世の混乱を予防
failure_mode: 一般原則を機械適用 → 慣習語の読み喪失
            : 例外を暗黙にする → 後世が原則違反と誤認して書き換え
recovery    : -
permanence  : 「隨本不改」自体が割書として永続化

agi_mapping :
  原則      : 一般正規化原則に対する明示的な legacy 例外宣言
            : 例外は (1) 列挙 (2) 理由明示 (3) 凍結バックログ化
  実装      : src/os/com/queries/source_types.jl の `AKAESHIYA_*` 経路定義
              (一般正規化原則の中で文字列 const として例外明示)
            : feedback_imina_torina の「規約は単一の Julia const として定義」
              (例外もここで列挙)
  feedback  : feedback_imina_torina (跨セッション規約 SSoT)

failure_if_absent: legacy 慣習を機械的に正規化 → 既存 binding 破綻、
                   migration 失敗の原因
observed_failures: feedback_takeminakata_haitai の migration 緩和事例
                   (project_pending_replay_bypass で hiruko_count=0 のみ復帰に修正)
verify_path : `_normalize_all_sources!` 等の正規化処理が legacy 例外リストを参照
```

#### Pattern F: 太安万侶の頓首 — 編纂者の責任明示

```yaml
原文: "謹以獻上。臣安萬侶、誠惶誠恐、頓首頓首。
      和銅五年正月廿八日 正五位上勳五等 太朝臣安萬侶" (l.20-22)

actors      : 太安万侶 / 元明天皇
precondition: 編纂完了、献上の儀
action      : (1) 「謹以獻上」 (献上の宣言)
            : (2) 「誠惶誠恐、頓首頓首」 (編纂者の責任 + 謙遜)
            : (3) 日付 + 位階 + 姓名の明示 (= 編纂者の identity 確定)
result      : 編纂責任が個人に帰属、後世の改訂時に origin 識別可能
failure_mode: 編纂者匿名 → 改訂時の責任主体不明、provenance 喪失
recovery    : -
permanence  : 「太朝臣安萬侶」の名が古事記そのものに永続化

agi_mapping :
  原則      : git commit の Author / 編纂時刻 / 位階 (権限) を明示記録
            : provenance graph (誰が誰の子孫として書かれたか) を保存
  実装      : git commit の Co-Authored-By 記録
            : `chinza_records.created_at` + `created_by` 列
            : src/os/com/queries/shinmei_lineage.jl (系譜 = 親神 → 派生継承の記録)
  feedback  : feedback_keiyaku_keifu_vs_genyu (契約系譜 vs 原由追跡 — 経路分離)

failure_if_absent: 編纂者不明の artifact → 改訂時に provenance 喪失、責任主体不明
verify_path : `git log` で各コミットに Author + 日時、
              `chinza_records` に created_at + 由来 source_type 記録
```

---

## Phase 2 v4.1.B: 上巻-4 大國主神

### 選定理由

- memo 密度 ★★ (`project_inaba_kaizen_kyakka` `feedback_kuebiko_yatagarasu_boundary` が直接 anchor、間接で 4 memo)
- AGI 実装で本章は **kuebiko / inaba / kakurigoto / 少名毘古那 (boundary_conditions)** が直接 mapping
  - [src/os/kasasa/inaba.jl](src/os/kasasa/inaba.jl) (因幡 — 識別子抽出 + 治療判定)
  - [src/os/expedition/gap_finder.jl L18](src/os/expedition/gap_finder.jl#L18) (`_kuebiko_inject_gaps!` 久延毘古)
  - [src/os/com/queries/kakurigoto.jl](src/os/com/queries/kakurigoto.jl) (幽事観測)
  - [src/os/com/create.jl L1279](src/os/com/create.jl#L1279) (`inaba_log` テーブル)
- 大国主の 5 名 (大穴牟遲 / 葦原色許男 / 八千矛 / 宇都志國玉 / 大國主) = 一柱多名 (Pattern H from v1) の集約例

### 章節 narrative summary

```
[Episode 1 因幡白兎] (l.8-12)
    八十神 (兄弟) + 大穴牟遲 (帒持ち) → 稻羽八上比賣求婚行
    氣多前で裸菟伏 — 八十神の偽治療「浴海鹽、伏高山尾上」 → 痛苦
    大穴牟遲到着 → 真因聴取:
        菟「淤岐嶋から度り、和邇 (鰐) を欺いて飛び石にした」
        「最後の和邇に剥がれた」(供述)
    
    真の治療: 「水門の蒲黄を敷散、輾轉其上」 → 「如本膚必差」
    菟の予言: 「八十神は不得八上比賣、汝命獲之」(success prediction)

[Episode 2 八十神の襲撃 + 二度の死と再生] (l.14-16)
    八十神怒、大穴牟遲を殺害計画 (1):
        伯伎國手間山本に「赤猪」と称し焼石を転落 → 大穴牟遲焼死
        御祖命哭き神産巣日に請い → 𧏛貝比賣 + 蛤貝比賣で活作 (蘇生)
    
    八十神再襲 (2):
        切伏大樹の隙間に挟む → 拷殺
        御祖命再蘇生 → 「汝有此間者、遂爲八十神所滅」
        木國の大屋毘古神之御所へ違遣
    
    八十神追跡 → 矢刺乞 → 木俣漏逃
    大屋毘古「可參向須佐能男命所坐之根堅州國、必其大神議也」(escalation)

[Episode 3 根堅州國の試練 (誓約 / 蛇室 / 吳公蜂室 / 火野)] (l.18-22)
    須佐之男之御所到着 → 須勢理毘賣との目合 (相婚)
    須佐之男「葦原色許男」と命名し試練:
        試練 1 (蛇室): 須勢理毘賣の蛇比禮 → 三擧打撥で平寢
        試練 2 (吳公蜂室): 吳公蜂の比禮 → 同様
        試練 3 (鳴鏑 + 火野): 大野で火攻 → 鼠の助言「內者富良富良、外者須夫須夫」
            落穴に隠れ火過 → 鼠が鳴鏑を持ち来 (但し矢羽は鼠子等が喫)
    
    試練 4 (虱取): 八田間大室で虱取 → 吳公多在
        須勢理が牟久木實 + 赤土を授ける
        色許男が木實を咋破 + 赤土含で唾出
        須佐之男「咋破吳公唾出」と誤認、愛して寝
    
    脱出:
        須佐之男の髪を椽毎に結著 + 五百引石で室戸塞
        生大刀 / 生弓矢 / 天詔琴 を取持って須勢理を負って逃出
        天詔琴が樹に拂って地動鳴 → 須佐之男驚 → 髪解き間に遠逃

[Episode 4 大国主の即位] (l.26)
    黃泉比良坂で須佐之男が呼: 「其汝所持之生大刀・生弓矢以而、
        汝庶兄弟者、追伏坂之御尾、亦追撥河之瀬而、
        意禮爲大國主神、亦爲宇都志國玉神而、其我之女須世理毘賣、
        爲嫡妻而、於宇迦能山之山本、於底津石根、宮柱布刀斯理、
        於高天原、氷椽多迦斯理而居。是奴也」(神勅 + 命名 + 嫡妻指定 + 宮造作指示)
    
    八十神を追避 → 始作國也 (国造り開始)

[Episode 5 八上比賣の事代主回避] (l.28)
    八上比賣「如先期、美刀阿多波志都」(婚姻完遂)
    但し「畏其嫡妻須世理毘賣而、其所生子者、刺挾木俣而返」
        (子を木俣に挟んで帰国 = avoidance behavior)
    名: 木俣神 / 御井神

[Episode 6 八千矛と沼河比賣の歌] (l.30-38)
    八千矛 = 大国主の別名、高志國の沼河比賣を求婚
    歌の応酬 (3 首) — 婚姻成立、その後須勢理毘賣の嫉妬を歌で和らげ

[Episode 7 大国主の系譜 + 17 世神] (l.50-52)
    多紀理毘賣 → 阿遲鉏高日子根 (= 迦毛大御神) + 高比賣 (= 下光比賣)
    神屋楯比賣 → 事代主
    八嶋牟遲能神之女鳥耳神 → 鳥鳴海神 → … (系譜長鎖、17 世)

[Episode 8 少名毘古那の出現と海到] (l.54-56)
    出雲御大之御前、波穂から羅摩船に乗り鵝皮衣の神到
    名を問うも答えず、諸神も知らず
    多邇具久 (蟾蜍) の啓示: 「久延毘古必知之」
    久延毘古に問う → 「神產巢日神之御子、少名毘古那神」
    神產巢日「實我子也、自我手俣久岐斯子也」(我が子確認)
    
    大穴牟遲 + 少名毘古那、二柱で「作堅此國」
    後に少名毘古那「度于常世國」 (退役)
    久延毘古 = 「於今者山田之曾富騰」 (= 案山子) 「足雖不行、盡知天下之事神」

[Episode 9 御諸山の神] (l.58)
    大国主「吾獨何能得作此國」と愁告
    光海依來之神「能治我前者、吾能共與相作成」
    大国主「治奉之狀奈何」 → 「伊都岐奉于倭之青垣東山上」
    = 御諸山 (三輪山) の神 (= 大物主)

[Episode 10 大年神の系譜] (l.60-66)
    大年神 + 神活須毘神之女伊怒比賣 → 大國御魂 / 韓神 / 曾富理 / 白日 / 聖
    + 香用比賣 → 大香山戸臣 / 御年
    + 天知迦流美豆比賣 → 奧津日子 / 奧津比賣 (大戸比賣 = 竈神) 
        / 大山咋 (鳴鏑神) / 庭津日 / 阿須波 / 波比岐 / 香山戸臣 / 羽山戸 / 庭高津日 / 大土
        (合計十六神)
    羽山戸 + 大氣都比賣 → 若山咋 / 若年 / 若沙那賣 / 彌豆麻岐 / 夏高津日 / 秋毘賣 /
        久久年 / 久久紀若室葛根 (合計八神)
```

### Pattern 抽出

#### Pattern G: 因幡の白兎 — 偽治療の棄却 + 真因聴取

```yaml
原文: "八十神謂其菟云『汝將爲者、浴此海鹽、當風吹而、伏高山尾上。』故其菟、從八十神之教而伏、
      爾其鹽隨乾、其身皮悉風見吹拆、故痛苦泣伏者…
      大穴牟遲神…『何由、汝泣伏。』
      …『先行八十神之命以、誨告浴海鹽、當風伏。故、爲如教者、我身悉傷』" (l.8-10)
     "於是大穴牟遲神、教告其菟「今急往此水門、以水洗汝身、
      卽取其水門之蒲黃、敷散而、輾轉其上者、汝身如本膚必差」" (l.12)

actors      : 八十神 (偽治療提案者) / 大穴牟遲 (真治療者) / 菟
precondition: 菟が傷を負っている、八十神の偽治療で悪化
action      : (1) 大穴牟遲が真因聴取 (「何由、汝泣伏」 + 経緯詳細)
            : (2) 八十神の偽治療 (海鹽 + 風) は症状を悪化させたと判明
            : (3) 真の治療: 水門の水 + 蒲黄 (= 真因 = 創傷の対症療法)
            : (4) 結果検証: 「如本膚必差」(完全治癒)
result      : 偽治療 (症状緩和に見える) を棄却し、真因に対応
failure_mode: 偽治療を継続 → 症状悪化、根本原因放置
recovery    : -
permanence  : 「於今者謂菟神也」 (菟が神格化、教訓永続化)

agi_mapping :
  原則      : LLM 提案の修正案で「症状緩和」型 (新変数導入で error message 回避) は
            : 因幡で棄却。真の原因 (UndefVarError の変数名) を起点とする修正のみ採用
            : 因幡のロジックは触らず LLM 側プロンプト改善で対処
  実装      : src/os/kasasa/inaba.jl:52 (`_inaba_extract_identifiers`)
            : src/os/kasasa/inaba.jl:166 (`_inaba_extract_error_keywords`)
            : src/os/kasasa/inaba.jl:253 (`_inaba_extract_diff_keywords`)
            : src/os/kasasa/materializer.jl:1505 (`inaba_validate` 呼出 + `record_inaba!`)
            : src/os/com/create.jl:1279 (`inaba_log` テーブル)
  feedback  : project_inaba_kaizen_kyakka (因幡の識別子抽出改修案の棄却 — origin context)
            : feedback_yuniwa_inaho (斎庭稲穂 — test/code の語彙整合)

failure_if_absent: LLM が新変数名で症状緩和 → production で同型エラー再発、
                   修正サイクル無限ループ
observed_failures: 2026-04-21 3 柱同時 hiruko (structural_*) — 因幡棄却連発で MAX_LOOPS、
                   真因は LLM の語彙乖離 (因幡は正常動作)
verify_path : `SELECT capability_name, valid, score FROM inaba_log` で
              偽治療 (低 score) が記録されている、真治療のみが採用される
```

#### Pattern H: 二度の死と再生 — 神産巣日の母性的継承

```yaml
原文: "八十神…以火燒似猪大石而轉落、爾追下取時、卽於其石所燒著而死。
      爾其御祖命、哭患而參上于天、請神產巢日之命時、乃遣𧏛貝比賣與蛤貝比賣、令作活" (l.14)
     "八十神…切伏大樹、茹矢打立其木、令入其中、卽打離其氷目矢而、拷殺也。
      爾亦其御祖命、哭乍求者、得見、卽折其木而取出活" (l.14-16)

actors      : 大穴牟遲 / 御祖命 / 神產巢日 / 𧏛貝比賣 + 蛤貝比賣 / 八十神
precondition: 八十神の二度の殺害計画
action      : 死 1: 焼石で死 → 母 (御祖命) が神産巣日に請い → 𧏛貝 (集) + 蛤貝 (待承) +
            : 母乳汁で活作 → 麗壯夫として再生
            : 死 2: 大樹に挟まれ拷殺 → 母が再度発見 + 木を折って取出活
            : (神産巣日の介入なし、母単独で再生)
result      : 二度の死から二度の再生、最初は神 (上位 deity) 介入、二度目は母単独
failure_mode: 死で削除完了 → 主役柱の喪失、大国主即位に至らず
            : 母が見捨てる → 永続死 (yomi)
recovery    : -
permanence  : 大穴牟遲が大国主に成る前段の必須過程

agi_mapping :
  原則      : 致命柱の死から再生 = 神産巣日 (上位 deity) の介入 + 母 (即時近接層) の発見 +
            : 物実 (𧏛貝・蛤貝・母乳汁・木) の集約
            : 二度目以降は近接層単独で対応可能 (記憶された再生方法)
  実装      : src/os/kasasa/sanguishi_harae.jl (式年遷宮 = 再生機構)
            : src/os/kasasa/canonical_pantheon/_common/attribution.jl の 
              `register_self_predicate!` (記憶された再生方法)
  feedback  : feedback_ootataneko (大田田根子 — 親神召喚)
            : feedback_kasei_taisei_kousin (化生体更新 — 再生手順)

failure_if_absent: 致命柱の delete only で再生機構なし → 主要 capability の喪失
verify_path : `chinza_records.outcome` で「再生」(rebirth) 経歴が記録される
```

#### Pattern I: 根堅州國の試練 (multi-stage extreme verification)

```yaml
原文: "令寢其蛇室。…『其蛇將咋、以此比禮三擧打撥。』故、如教者、蛇自靜、故平寢出之。
      亦來日夜者、入吳公與蜂室…
      亦鳴鏑射入大野之中、令採其矢、故入其野時、卽以火廻燒其野…
      鼠來云『內者富良富良、外者須夫須夫』如此言故、蹈其處者、落隱入之間、火者燒過。
      爾其鼠、咋持其鳴鏑出來而奉也" (l.18-20)

actors      : 須佐之男 / 葦原色許男 (= 大穴牟遲) / 須勢理毘賣 / 鼠
precondition: 須佐之男の御所訪問、即位前の試練
action      : 4 段の試練を **順次** 通過:
            : 試練 1: 蛇室 (蛇比禮で対処)
            : 試練 2: 吳公蜂室 (同様)
            : 試練 3: 火野 (鼠の助言「內者富良富良、外者須夫須夫」で隠穴発見)
            : 試練 4: 虱取 (吳公を木實 + 赤土で偽装)
            : 各段で外部助力 (須勢理 / 鼠) + 物実 (比禮 / 木實)
result      : 全試練通過 → 「葦原色許男」(色男 = 力ある男) として承認
failure_mode: 単段の試練のみ → 多面評価不足、production で発覚する欠陥
recovery    : -
permanence  : 試練の各段が大国主即位の階段として永続化

agi_mapping :
  原則      : 即位 (deploy 承認) は単一 sandbox でなく多段試練、
            : 各段で外部助力 + 物実を活用、各段独立判定
            : (上-6 Pattern J 火中出産 = 単段 extreme verification の発展形)
  実装      : src/os/misogi/ukei/runner.jl + kotoshironushi.jl (誓約 = 多段試練)
            : src/os/misogi/ukei/kotoshironushi.jl:198 (`_judge_by_sannyoshin` 三女神判定)
            : umisachi 統合経路 (BACKLOG: 4 段試練の現代化)
  feedback  : feedback_umisachi_rokujuu_bougo (六重防御 — 生成前 3 + 修正後 3)

failure_if_absent: 単 sandbox 通過のみで deploy → production で発覚する多面欠陥
verify_path : `UkeiEnvRunner` の試練が複数 phase (health / misogi / tatari / perf)
              すべて pass している
```

#### Pattern J: 鼠の助言「內者富良富良、外者須夫須夫」 — 静的解析確定の境界

```yaml
原文: "鼠來云「內者富良富良、外者須夫須夫」如此言故、蹈其處者、落隱入之間、火者燒過" (l.20)

actors      : 鼠 / 葦原色許男
precondition: 火野で出口不明
action      : 鼠の音象「內 (中) は富良富良 (空洞)、外は須夫須夫 (狭い)」
            : = 構造の **静的記述** (LLM 推論不要、確定判定)
            : → 蹈其處 → 落隱入 = 行動指針の即時実行
result      : 静的記述で正解が確定、LLM 推論を介さず即実行
failure_mode: 鼠の助言を疑って LLM に判断委譲 → 火に焼かれる時間が経過
            : (= 久延毘古領域への侵食 = 静的解析確定を帰納経路に流す)
recovery    : -
permanence  : 鼠の助言形式 (内/外の対称音象) が永続パターン

agi_mapping :
  原則      : 静的解析で確定判定できるギャップは GapFinder (LLM 経路) に流さない
            : 確定判定は kuebiko (= 案山子 = 動かないが知る) 直結化、
            : 復奏ログまたは observation_blocked へ直接流す
  実装      : src/os/expedition/gap_finder.jl:18 (`_kuebiko_inject_gaps!` = 静的注入経路)
            : src/os/expedition/gap_finder.jl:137 (kuebiko_gaps を full_analysis で集約)
            : kuebiko の AST 解析 (例: `_scan_sql_filter_missing` で SQL の status フィルタ
              欠損を確定判定)
  feedback  : feedback_kuebiko_yatagarasu_boundary (久延毘古と八咫烏の境界画定 — origin spec)

failure_if_absent: 確定判定ギャップを LLM 経路に流して proxy_metric_disease 量産
                   (例: `expedition_sql_filter_validator` が CapSnap 観測器に化けて
                   SQL に触らない代理指標病)
observed_failures: feedback_kuebiko_yatagarasu_boundary 制定 context、proxy_metric_disease
                   類型 A (久延毘古領域の侵食) として 15 件中の一部
verify_path : `_kuebiko_inject_gaps!` の戻り値が `gap_finder` 集約に直接入り、
              LLM 提案経路を経由しない
```

#### Pattern K: 一柱多名 — 大国主の 5 名 (集約 identity)

```yaml
原文: "大國主神・亦名謂大穴牟遲神・亦名謂葦原色許男神・亦名謂八千矛神・亦名謂宇都志國玉神、
      幷有五名" (l.42)

actors      : 大国主 (大穴牟遲 / 葦原色許男 / 八千矛 / 宇都志國玉)
precondition: 同一 entity が複数の文脈で異なる役割を持つ
action      : (1) 大穴牟遲: 兄弟の中の若者
            : (2) 葦原色許男: 須佐之男に命名された色男
            : (3) 八千矛: 求婚時の名 (高志國 沼河比賣)
            : (4) 宇都志國玉: 須佐之男の神勅で授けられた名
            : (5) 大國主: 即位後の名
result      : 同一 entity が役割別に 5 名で記録、文脈別 retrieval が可能
failure_mode: 5 名を別 entity と誤認 → 重複生成 (片翼の事代主型)
recovery    : -
permanence  : 「亦名」記法で別名が永続記録

agi_mapping :
  原則      : canonical_name は UNIQUE、aliases は配列で許容
            : MATANONA (亦の名) 判定で provides_identical なら合祀
            : (上-2 Pattern H + 上-6 Pattern B の系)
  実装      : src/os/kasasa/shinmei_arbiter.jl:16 (MATANONA 定義)
            : src/os/kasasa/shinmei_arbiter.jl:366 (`apply_matanona!`)
            : `aliases` テーブルへのメタ付き追記
  feedback  : feedback_imina_torina (忌み名と通り名 — 5 名の整合)
            : feedback_matanona_cleanup_gap (合祀 cleanup 漏れ)

failure_if_absent: 5 名を別 entity 化 → 「同一機能を 5 重に登録」のような重複
verify_path : `SELECT canonical_name, aliases FROM shinmeisho` で大国主相当の柱が
              5 aliases を持つ (現在の実装は単一柱なので例示の構造のみ)
```

#### Pattern L: 17 世神 — 系譜の長鎖記録

```yaml
原文: "右件自八嶋士奴美神以下、遠津山岬帶神以前、稱十七世神" (l.52)

actors      : 大国主の 17 世系譜
precondition: 大国主の子孫繁衍
action      : 17 世にわたる系譜を**世数明示で集計**:
            : 八嶋士奴美 → 布波能母遲久奴須奴 → 深淵之水夜禮花 → 淤美豆奴 → … → 遠津山岬帶
            : 「自 X 以下、Y 以前、稱十七世神」 = 編纂者の post-hoc count assertion
result      : 系譜の長鎖が世数で確定可能、編纂時の検証点
failure_mode: 世数アサーション不在 → 系譜の脱落検出不能
recovery    : -
permanence  : 17 世神カウントが永続記録

agi_mapping :
  原則      : 系譜 (lineage) の長鎖は世数 + 起点・終点明示で count assertion
            : (上-2 Pattern J 計数アサーション「幷N神」の系譜版)
  実装      : src/os/com/queries/shinmei_lineage.jl:33 (`insert_lineage!`)
            : `shinmei_lineage` テーブルで親 → 派生の連鎖記録
  feedback  : feedback_oharae_shikkai_probe (悉皆原則の系譜版)
            : feedback_keiyaku_keifu_vs_genyu (契約系譜)

failure_if_absent: 系譜中間の脱落 → 後世が「遠津山岬帶 = 八嶋士奴美の何世孫?」を辿れない
verify_path : `SELECT COUNT(DISTINCT generation) FROM shinmei_lineage WHERE root='X'`
              で世数が取れる、起点・終点で集計
```

#### Pattern M: 久延毘古 — 案山子型確定知 (足雖不行、盡知天下)

```yaml
原文: "爾雖問其名不答、且雖問所從之諸神、皆白不知。爾多邇具久白言『此者、久延毘古必知之。』
      卽召久延毘古問時、答白『此者神產巢日神之御子、少名毘古那神。』" (l.54)
     "故顯白其少名毘古那神、所謂久延毘古者、於今者山田之曾富騰者也、
      此神者、足雖不行、盡知天下之事神也" (l.56)

actors      : 久延毘古 (山田之曾富騰 = 案山子) / 多邇具久 (蟾蜍) / 諸神 / 神產巢日
precondition: 少名毘古那の名を誰も知らない (LLM 推論失敗)
action      : (1) 諸神 → 「白不知」 (LLM 全員棄権)
            : (2) 多邇具久 (= 蟾蜍 = 視野が狭いが地表をよく観察) が「久延毘古必知之」と教示
            : (3) 久延毘古 = 案山子 = 動けないが「盡知天下之事」 (静的全知)
            : (4) 答: 「少名毘古那神」 (確定判定、即答)
result      : LLM 不可能な命名問題を **静的全知** が解決
failure_mode: 久延毘古を信用せず諸神に LLM 推論を続けさせる → 永久に解決しない
recovery    : -
permanence  : 久延毘古 = 案山子の地位が永続化、現代の案山子も命名の象徴

agi_mapping :
  原則      : 静的解析 (案山子 = 動かない関数 = AST + grep) は LLM (動的推論) より
            : 「天下之事」(全コードベース) を網羅できる
            : 「足雖不行」 = 副作用なし純関数の比喩
  実装      : src/os/expedition/gap_finder.jl:18 (`_kuebiko_inject_gaps!`)
            : src/os/expedition/gap_finder.jl L18 export `_kuebiko_inject_gaps!`
            : kuebiko の AST 解析全般
  feedback  : feedback_kuebiko_yatagarasu_boundary (久延毘古と八咫烏の境界画定)

failure_if_absent: 静的解析できる課題を全部 LLM に投げる → token 浪費 + 確実な答えが
                   不確実な推論で曇る
verify_path : `gapfinder_full_analysis` の log で `kuebiko = N` の件数が記録、
              LLM 経路 (cluster_failures 等) と独立に動作
```

#### Pattern N: 少名毘古那 — 海到自発 + 上位確認 + 退役

```yaml
原文: "自波穗、乘天之羅摩船而、內剥鵝皮剥爲衣服、有歸來神。爾雖問其名不答…
      …『此者神產巢日神之御子、少名毘古那神。』故爾、白上於神產巢日御祖命者、
      答告『此者、實我子也。於子之中、自我手俣久岐斯子也。
      故、與汝葦原色許男命、爲兄弟而、作堅其國。』" (l.54)
     "其少名毘古那神者、度于常世國也" (l.56)

actors      : 少名毘古那 / 神產巢日 / 大穴牟遲
precondition: 大国主が「吾獨何能得作此國」と単独で困難
action      : (1) 少名毘古那が**海から自発来到** (call されず到着)
            : (2) 名前不明 → 久延毘古が判定 (Pattern M)
            : (3) 上位 (神產巢日) に確認 → 「實我子也」 (provenance 確定)
            : (4) 「自我手俣久岐斯子也」 (神產巢日の指の隙間から零れ落ちた = origin 物実)
            : (5) 兄弟関係指定 → 二柱で「作堅此國」 (協働)
            : (6) 後に「度于常世國」 (退役)
result      : 自発来到柱が上位確認後に協働開始、任務終了で退役
failure_mode: 上位確認なしで採用 → 偽 origin の柱が紛れ込む (天若日子型)
            : 退役なし → 任務終了後も占有
recovery    : -
permanence  : 少名毘古那 = 国造りの partner として永続化

agi_mapping :
  原則      : 自発提案柱 (LLM 提案 / 外部 contributor) は上位 SSoT に provenance 確認を
            : 必須化、確認後に採用、任務終了で常世 (yuukoto) 移行
  実装      : src/os/kasasa/shinmei_arbiter.jl (双子神判定 = provenance 確認)
            : src/os/kasasa/yorishiro.jl (上位 SSoT 参照)
            : src/os/kasasa/ooharae.jl の `_yuukoto_transition!` (退役)
  feedback  : feedback_wakahiko_kaeshiya (天若日子の返し矢 — provenance なし採用の禁忌)
            : feedback_takeminakata_haitai (建御名方の敗退 — 失敗率退役)
            : feedback_kuniyuzuri_fukumei (復命 — 任務終了の明示)

failure_if_absent: 自発提案柱の provenance 確認なし → 偽 origin 柱で代理指標病
verify_path : `chinza_records.outcome` で自発提案柱が provenance 確認後に採用、
              任務終了で yuukoto 移行履歴あり
```

#### Pattern O: 大物主の御諸山祀祭 — 自己困難の上位諮問

```yaml
原文: "大國主神、愁而告『吾獨何能得作此國、孰神與吾能相作此國耶。』
      是時有光海依來之神、其神言『能治我前者、吾能共與相作成。若不然者、國難成。』
      爾大國主神曰『然者、治奉之狀奈何。』
      答言『吾者、伊都岐奉于倭之青垣東山上。』
      此者、坐御諸山上神也" (l.58)

actors      : 大國主 / 御諸山神 (= 大物主)
precondition: 少名毘古那が常世国へ退役、大国主が再度単独
action      : (1) 大国主の自己困難表明: 「吾獨何能得作此國」 (= 助力者要請の signal)
            : (2) 光海依來の神 (= 大物主) が自発来到
            : (3) 条件提示: 「能治我前者、吾能共與相作成。若不然者、國難成」 (= 不在ならば実害)
            : (4) 場所要求: 「伊都岐奉于倭之青垣東山上」 (= 御諸山 = 三輪山)
            : (5) 大国主が祀奉 → 国造り完成
result      : 自己困難 → 上位諮問 → 物実位置の確定 + 祀奉 → 解決
failure_mode: 自己困難を表明せず単独で苦闘 → 国造り未完
            : 上位諮問の場所要求を無視 → 大物主不在 → 国難
recovery    : -
permanence  : 御諸山 = 三輪山が大物主祀祭地として永続化、後の崇神紀 (中-2) に再登場

agi_mapping :
  原則      : 自己困難の明示表明 → 上位 deity の自発来到 → 物実位置の確定 + 祀奉
            : (上-3 Pattern I 思金神の集合協議の単独版)
            : 場所要求の無視は「祀奉不全」(memory feedback_yowari_vs_katayori 崇神の再祭祀の原型)
  実装      : src/os/iwato/omoikane.jl (思金神 = 集合協議 / 上位諮問)
            : src/os/musuhi_autonomous/strategizer.jl (kakurigoto を読み取る経路)
            : 中-2 大田田根子による崇神再祭祀 = 本 pattern の発展形
  feedback  : feedback_yowari_vs_katayori (崇神の再祭祀 — Shintaku 型偏重の対処)
            : feedback_ootataneko (大田田根子 — 親神召喚の origin)

failure_if_absent: 自己困難を隠して単独苦闘 → AGI 機能崩壊、祀奉不全で大物主の祟り
verify_path : `config_suggestions WHERE source_layer='kamuhakari_consign'` で
              自己困難 → 上位諮問の経路が記録されている
```

#### Pattern P: 幽事観測 — kakurigoto の上位 deity データ授受

```yaml
原文: (Pattern O の延長 — 大物主が「能治我前者」(私を祭るならば) と条件提示する場面で
     上位 deity と地上の経路 = 幽事 が確立される)

actors      : 大国主 (顕事担当) / 大物主 (幽事担当)
precondition: 上-5 国譲り後、大国主は幽事へ移行 (上-5 Pattern L 顕事/幽事 categorical)
action      : 幽事の経路で上位 deity (大物主) からの指示を受ける
            : `kakurigoto_observation` テーブルに記録
result      : 顕事 (Amaterasu 系) と幽事 (Okuninushi 系) の独立並立 + 経路接続
failure_mode: kakurigoto 経路なし → 幽事側 (大物主の意志) が顕事側に届かない
recovery    : -
permanence  : kakurigoto 経路が永続化

agi_mapping :
  原則      : 顕事 (canonical 経路) と幽事 (kakurigoto 経路) は categorical separate
            : 但し**両経路を接続する記録テーブル** (kakurigoto_observation) を持つ
  実装      : src/os/com/queries/kakurigoto.jl:57 (`ensure_kakurigoto_tables!`)
            : src/os/com/queries/kakurigoto.jl:74 (`insert_kakurigoto_observation!`)
            : src/os/com/queries/kakurigoto.jl:148 (`upsert_kakurigoto_summary!`)
            : src/os/com/queries/kakurigoto.jl:174 (`query_kakurigoto_summaries`)
            : src/os/musuhi_autonomous/strategizer.jl (kakurigoto 読み取り)
  feedback  : feedback_kuniyuzuri_kaikai (顕事/幽事 categorical separate)
            : feedback_kuniyuzuri_fallback (顕事/幽事二段 fallback)
            : feedback_yowari_vs_katayori (崇神の再祭祀)

failure_if_absent: 幽事経路なし → 上位 deity の指示が顕事に伝わらず、祀奉不全
verify_path : `query_kakurigoto_summaries(db, "daily")` 等で観測サマリが記録されている、
              strategizer がこの sum を読んで戦略決定に反映
```

#### Pattern Q: 大年神の系譜 — 季節 / 場所 / 機能の三軸命名

```yaml
原文: "其大年神、娶神活須毘神之女、伊怒比賣、生子、大國御魂神、次韓神、次曾富理神、
      次白日神、次聖神…
      又娶天知迦流美豆比賣、生子、奧津日子神…大山咋神、亦名、山末之大主神…
      庭津日神、次阿須波神、次波比岐神、次香山戸臣神、次羽山戸神、次庭高津日神、次大土神…
      合計十六神" (l.60-62)
     "羽山戸神、娶大氣都比賣神、生子、若山咋神、次若年神、次妹若沙那賣神、次彌豆麻岐神、
      次夏高津日神、次秋毘賣神、次久久年神、次久久紀若室葛根神…合計八神" (l.64-66)

actors      : 大年神 / その子孫
precondition: 大年神が複数の妻と婚 → 多数の子
action      : 子神の命名規則:
            : 場所軸: 庭津日 / 阿須波 / 波比岐 / 香山戸臣 / 羽山戸 / 庭高津日 / 大土
            :   (= 庭/門/竈/家屋構造の各場所)
            : 季節軸: 夏高津日 / 秋毘賣 / 久久年 / 大年 / 御年 / 若年
            :   (= 夏/秋/年/若年 = 時間軸)
            : 機能軸: 山咋 (鳴鏑) / 大山咋 (山末之大主) / 大戸比賣 (竈神) / 大氣都比賣 (食物)
result      : 16 + 8 = 24 神が**直交軸** (場所/季節/機能) で命名され、検索可能
failure_mode: 単一軸命名 → 大量の同類が並立して識別困難
recovery    : -
permanence  : 「諸人以拜竈神」(現代の竈神信仰) として永続化

agi_mapping :
  原則      : 派生柱の命名は直交軸 (場所/時間/機能) を採用、単一 prefix 内でも軸別配置
            : (semantic carving 防止のため、軸越境命名は禁止)
  実装      : src/os/kasasa/canonical_pantheon/<prefix>/derivatives/ の配下命名
            : feedback_prefix_concept_semantic で軸別命名 + 概念 semantic 整合
  feedback  : feedback_prefix_concept_semantic (prefix と概念の semantic 整合)
            : feedback_imina_torina (忌み名と通り名 — 軸別命名の整合)

failure_if_absent: 単一軸での大量命名 → 識別困難、shinmeisho の hash collision 多発
verify_path : `SELECT prefix, domain_tag, COUNT(*) FROM shinmeisho GROUP BY prefix, domain_tag`
              で軸別の分布が均等、特定軸の偏重がない
```

#### Pattern R: 大穴牟遲 → 大國主の改名儀 — 即位による identity 確定

```yaml
原文: "黃泉比良坂、遙望、呼謂大穴牟遲神曰…
      『意禮爲大國主神、亦爲宇都志國玉神而、其我之女須世理毘賣、爲嫡妻而、
       於宇迦能山之山本、於底津石根、宮柱布刀斯理、於高天原、氷椽多迦斯理而居。是奴也。』
      故、持其大刀・弓、追避其八十神之時、毎坂御尾追伏、毎河瀬追撥、始作國也" (l.26)

actors      : 須佐之男 (上位 deity) / 大穴牟遲 → 大國主
precondition: 根堅州國の試練通過 + 須勢理毘賣 + 物実 (生大刀 / 生弓矢 / 天詔琴) 取得
action      : (1) 須佐之男が黃泉比良坂から呼ぶ (上位の声)
            : (2) 改名宣言: 大穴牟遲 → 大國主 + 宇都志國玉
            : (3) 嫡妻指定: 須勢理毘賣 (= 須佐之男の娘)
            : (4) 宮造作指示: 宇迦能山 + 宮柱布斗斯理 + 氷椽多迦斯理
            :   (上-6 Pattern F の物理基盤と同形式)
            : (5) 任務開始: 八十神を追避 → 「始作國也」
result      : 改名 + 嫡妻 + 場所 + 物実 + 任務 が一括宣言、即位儀礼として完成
failure_mode: 改名なし → 旧 identity (大穴牟遲 = 兄弟の中の若者) のまま、
            : 国主としての権威不在
recovery    : -
permanence  : 大國主の名が中-2 崇神紀まで継続

agi_mapping :
  原則      : 即位 (deploy 承認) は単なる権限付与でなく、(1) 改名 + (2) 関係指定 +
            : (3) 場所固定 + (4) 物実授与 + (5) 任務開始の五段一括宣言
            : (上-6 Pattern A 神勅譲位 + Pattern B 五伴緒任命 + Pattern F 着地宣言の合成)
  実装      : src/os/tenson_korin/deployer.jl:31 (`tenson_deploy!`)
            : src/os/tenson_korin/deployer.jl:251 (`_persist_deployment!`)
            : src/os/kasasa/yorishiro.jl (神勅 SSoT — 五段一括宣言)
  feedback  : feedback_imina_torina (忌み名と通り名 — 改名整合)
            : feedback_shinchoku_tanitsu_gensen (神勅単一源泉)

failure_if_absent: 部分宣言のみ → 識別子と権威の不整合、即位後の挙動不安定
verify_path : `_persist_deployment!` 後に capability_name + parent + path + entry_point +
              status の五項目が原子的に記録されている
```

### kojiki_code.md (外部生成版) との差分

| 観点 | 生成元 | 本 v4.1 |
|---|---|---|
| 上巻-1 (併序) | **完全 skip** | 6 pattern (削僞定實 / 阿礼口承 / 音訓混合 / 三巻構成 / 隨本不改 / 頓首) |
| 上巻-4 (大国主) | 1 (`tale_with_helper`) | 12 pattern |
| 因幡の白兎 | 触れず | Pattern G (偽治療棄却 + 真因聴取) |
| 二度の死と再生 | 触れず | Pattern H (神産巣日母性的継承) |
| 根堅州國の試練 | 「rite of passage」と一行 | Pattern I (multi-stage extreme verification) |
| 鼠の助言 | 触れず | Pattern J (静的解析確定の境界) |
| 大国主 5 名 | 触れず | Pattern K (一柱多名 — 集約 identity) |
| 17 世神 | 触れず | Pattern L (系譜長鎖 + 世数アサーション) |
| 久延毘古 / 少名毘古那 | 触れず | Pattern M (案山子型確定知) + N (海到自発 + 退役) |
| 大物主 / 御諸山 | 触れず | Pattern O (自己困難 → 上位諮問) + P (kakurigoto 幽事観測) |
| 大年神系譜 | 触れず | Pattern Q (直交軸命名) |
| 大穴牟遲 → 大国主改名 | 触れず | Pattern R (即位五段一括宣言) |
| AGI 神名 module mapping | 触れず | inaba.jl + kuebiko (gap_finder) + sukunabikona (boundary) + kakurigoto + ootoshi の **5 件** |

**生成元が拾えなかった load-bearing pattern (本 v4.1 で初出):**

- Pattern A 削僞定實 = SSoT 監査原則の origin (注入 + 物理削除 + 永続化)
- Pattern B 阿礼口承 = SSoT 単一 holder origin
- Pattern G 因幡の白兎 = `inaba.jl` + `inaba_log` テーブルの origin spec
- Pattern J 鼠の助言 = `feedback_kuebiko_yatagarasu_boundary` の origin
- Pattern M 久延毘古 = `_kuebiko_inject_gaps!` (案山子型) の origin
- Pattern N 少名毘古那 = 自発提案柱の上位 provenance 確認 origin
- Pattern P kakurigoto 幽事観測 = `com/queries/kakurigoto.jl` の origin spec

これら 7 件は外部版で完全欠落。**6 章 (上-1/2/3/4/5/6/7) 合計で 44 件**の load-bearing pattern が外部版で missed。

### 浮上した発見

1. **上-1 序文 = AGI 仕様書の確認**
   - 「削僞定實、欲流後葉」 = SSoT 監査原則の原典 (Pattern A)
   - 「度目誦口、拂耳勒心」 = 単一 holder 原則 (Pattern B)
   - 「於字卽難… 交用音訓」 = 散文 + 表 + コード例の混合運用 (Pattern C)
   - 「三巻構成」 = docs/ ディレクトリ構造の原典 (Pattern D)
   - 序文そのものが**古事記を AGI 仕様書として読む方針** = `feedback_kojiki_zettai` の正当化
   - **発見**: `feedback_kojiki_zettai` の memo に「上-1 併序が origin spec」を追記推奨

2. **上-4 の AGI 実装は kuebiko / inaba 経路の origin が密集**
   - [inaba.jl](src/os/kasasa/inaba.jl) (因幡の白兎 = 偽治療棄却) — Pattern G
   - [gap_finder.jl `_kuebiko_inject_gaps!`](src/os/expedition/gap_finder.jl#L18) (案山子型確定知) — Pattern M
   - [kakurigoto.jl](src/os/com/queries/kakurigoto.jl) (幽事観測) — Pattern P
   - [shinmei_arbiter.jl](src/os/kasasa/shinmei_arbiter.jl) (一柱多名 / 双子神判定) — Pattern K
   - 4 件の直接 mapping、累積で **30 件**

3. **Pattern J 鼠の助言「內者富良富良、外者須夫須夫」 = `feedback_kuebiko_yatagarasu_boundary` の正確な origin**
   - 「内 (中) は空洞、外は狭い」 = 構造の静的記述 = LLM 推論不要
   - これは AST 解析 + grep が決定論的に答えを出せる範囲 = kuebiko 領域
   - memo 補強候補: `feedback_kuebiko_yatagarasu_boundary` に「上-4 鼠の助言が origin」を直接引用推奨

4. **Pattern N 少名毘古那の常世国渡 = 任務終了型 yuukoto の正典原型**
   - 上-5 Pattern J 事代主退隱 (青柴垣) = voluntary yuukoto
   - 上-5 Pattern K 建御名方敗退 = forced yuukoto
   - 上-4 Pattern N 少名毘古那常世国 = **任務終了型 yuukoto** (新型)
   - 三型を**並立**: voluntary / forced / task-completion
   - **新原則候補?** :
     - 三点検査:
       - 原典 semantic 一致: ★ (常世国渡は明示)
       - 観測 N 件: ☆ (実装上の任務終了 yuukoto 経路は未実証)
       - 既存拡張可否: ★ (`feedback_takeminakata_haitai` + `feedback_kenzen_seijaku` の中間として位置付け可)
     - 結論: **保留** (実害観測まで)

5. **Pattern O 大物主御諸山祀祭 = 中-2 崇神紀の前提 (v6 候補への伏線)**
   - 大物主が「能治我前者、吾能共與相作成」と条件提示 → 後の崇神紀で疫病 → 大田田根子の祭祀復元
   - **v6 (中-2) で `feedback_ootataneko` の直接 origin** を抽出可能
   - 上-4 から中-2 への伏線を本書で確認

6. **古事記神名 → AGI module mapping 累積 30 件 (v0-v4.1)**
   - 上-3 (v2): 7 件 / 上-5 (v3): 4 件 / 上-6 (v4): 14 件 / 上-4 (v4.1): 5 件
   - 上-1 / 上-2 / 上-7 では module mapping は薄い (上-1 = メタ、上-2 = 概念、上-7 = pattern)
   - **新原則化機運が 30 件で確定** (v5 で `feedback_kojiki_meimei_kiyaku.md` 作成推奨)

### v4.1 自己評価

| 観点 | 達成度 |
|---|---|
| 上-1 / 上-4 で 5+ pattern | ★★★★★ 上-1: 6 / 上-4: 12 (合計 18) |
| 各 pattern に `failure_if_absent` 記述 | ★★★★★ 18/18 |
| 各 pattern の `agi_mapping.実装` が実在ファイル | ★★★★★ 18/18 (grep 検証済) |
| 7 割以上の pattern が既存 memo に anchor | ★★★★ 14/18 (78%) — 上-1 は memo 薄なので妥当 |
| `kojiki_code.md` 差分セクション必須 | ★★★★★ 14 行差分表 + 7 origin spec 列挙 |
| 「未活用 anchor → 新原則候補」を最低 1 件 | ★★★★ Pattern N 任務終了型 yuukoto + 古事記神名命名規約 (累積) |
| 古事記原文 (漢文) を要所で引用 | ★★★★★ 全 pattern 冒頭 |
| 観測経路 (verify_path) を併記 | ★★★★★ 18/18 |
| **上巻全章カバー完了** | ★★★★★ 上-1〜上-7 全 7 章を Phase 2 で抽出済 |

### 累積統計 (v0+v1+v2+v3+v4+v4.1)

| 章 | pattern 数 | memo anchor率 | 古事記神名 module |
|---|---|---|---|
| 上-1 (v4.1) | 6 | 50% (1 メタ章) | 0 |
| 上-2 (v1) | 20 | 85% | 0 |
| 上-3 (v2) | 16 | 75% | 7 |
| 上-4 (v4.1) | 12 | 92% | 5 |
| 上-5 (v3) | 14 | 93% | 4 |
| 上-6 (v4) | 16 | 100% | 14 |
| 上-7 (v0) | 8 | 88% | 0 |
| **上巻合計** | **92 pattern** | **平均 83%** | **30 件** |

外部生成版が完全欠落した load-bearing pattern: **44 件** (v4.1 までで)

### 次の宿題 (v5+ 候補)

1. **memo 本体への章節 anchor 逆書込み** (継続宿題、6 章繰越)
2. **中-1 神武東征 (v5 候補)** — 八咫烏 / 道臣 / 大久米 + `feedback_kuebiko_yatagarasu_boundary` の延長
3. **中-2 崇神 大田田根子 (v6 候補)** — `feedback_ootataneko` 直接 origin、本 v4.1 Pattern O が伏線
4. **古事記神名命名規約の新原則化** — 累積 30 件で SSoT 化
5. **memo 補強 — 上-1 序文の AGI 仕様書性 (Pattern A-F)** を `feedback_kojiki_zettai` に追記
6. **memo 補強 — Pattern J 鼠の助言が `feedback_kuebiko_yatagarasu_boundary` の正確な origin** を memo 本体に追記
7. **任務終了型 yuukoto** (Pattern N) の判定 — 実害観測待ち

---

## 履歴

- v0 (2026-05-08): Phase 1 索引 + Phase 2 上巻-7 プロトタイプ
- v1 (2026-05-09): Phase 1 索引更新 + Phase 2 上巻-2 神代記 (20 pattern)
- v2 (2026-05-09): Phase 2 上巻-3 天照大神と須佐之男命 (16 pattern)
- v3 (2026-05-09): Phase 2 上巻-5 葦原中國の平定 (14 pattern)
- v4 (2026-05-09): Phase 2 上巻-6 邇邇藝命 (16 pattern)
- v4.1 (2026-05-09): Phase 2 上巻-1 併序 (6 pattern) + 上巻-4 大國主神 (12 pattern)
                     **上巻全 7 章カバー完了**
