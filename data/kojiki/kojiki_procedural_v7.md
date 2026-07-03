# 古事記 Procedural Pattern 抽出 v7

v6 ([`kojiki_procedural_v6.md`](kojiki_procedural_v6.md)) からの増分:

- **Phase 2 v7: 中巻-4 倭建命 (景行天皇 + 倭建命 + 成務天皇)** 抽出 — 14 pattern
- 景行子 80 王 / 大碓泥疑 / 熊曾建 / 出雲建詐刀 / 東征 / 草那藝 + 御囊 / 焼津 / 弟橘犠牲 / 阿豆麻 / 老人歌 / 美夜受 / 白猪見惑 / degradation / 思国歌 / 白鳥化 の 15 大エピソード
- 本章は **TAKERU セキュリティテスト 3 系統 (SURUGA / IZUMO / IBUKI) の直接 origin spec** + **「白猪見惑」(= 候補新原則) の原典確認**

抽出方法論は [`extraction_prompt.md`](extraction_prompt.md) を参照。
v0-v6 (上巻全章 + 中-1, 中-2) の pattern は重複しない。

---

## Phase 2 v7: 中巻-4 倭建命

### 選定理由

- memo 密度 ★★ (`project_takeru_security` が直接 anchor、白猪見惑が候補新原則として記録、間接で 6 memo)
- AGI 実装で **TAKERU セキュリティテストが古事記神名で直接命名**:
  - [src/os/takeru/](src/os/takeru/) directory (倭建命プロトコル全体)
  - [src/os/takeru/protocol.jl](src/os/takeru/protocol.jl) (`YamatoTakeruProtocol` struct)
  - [src/os/takeru/tests/suruga.jl](src/os/takeru/tests/suruga.jl) (`test_suruga!` = 駿河型 リソース枯渇耐性)
  - [src/os/takeru/tests/izumo.jl](src/os/takeru/tests/izumo.jl) (`test_izumo!` = 出雲型 サプライチェーン)
  - [src/os/takeru/tests/ibuki.jl](src/os/takeru/tests/ibuki.jl) (`test_ibuki!` = 伊吹山型 プロンプトインジェクション)
  - [src/os/takeru/degradation.jl](src/os/takeru/degradation.jl) (倭建命の最後の段階的衰弱)
  - [src/os/takeru/shiratori_archive.jl](src/os/takeru/shiratori_archive.jl) (白鳥化 = post-mortem archive)
  - [src/os/com/kusanagi.jl](src/os/com/kusanagi.jl) (`kusanagi_mint!` / `kusanagi_validate` = 草那藝劒 auth token)
- `kojiki_code.md` (外部生成版) は本章を `hero_journey_with_demise` の 1 行に圧縮
- 本章は **倭建命の死までを記述する初の章** = degradation の段階的進行が原典明示

### 章節 narrative summary

```
[Setup 景行天皇] (l.8)
    大帶日子淤斯呂和氣 (= 景行) — 子 80 王 (記録 21 + 不入記 59)
    太子 3 人: 若帶日子 (= 後の成務) / 倭建命 / 五百木之入日子
    残 77 王は國造・和氣・稻置・縣主に分賜 = 系譜の地方分散

[Crisis1 大碓命の処刑 — 文字解釈ミス] (l.14)
    景行詔小碓命 (= 倭建)「何汝兄於朝夕之大御食不参出來、専汝**泥疑**教覺」
    5 日後、依然不参 → 景行問: 「何汝兄久不参出。若有未誨乎」
    小碓「既為泥疑也」 → 景行「如何泥疑之」
    小碓答: 「朝署入廁之時、待捕、搤批而、引闕其枝、裹薦投棄」
    
    景行「惶其御子之**建荒**之情」(= 残虐性に畏怖) → 西方派遣を決定

[Episode1 熊曾建二人征伐] (l.16-20)
    倭比賣命の御衣御裳 + 劒を御懷
    熊曾建之家: 軍圍三重 + 室作 + 樂日設備
    
    倭建命 = 童女変装で女人之中に交立、室内潜入
    熊曾兄弟「見感其孃子、坐於己中」
    酣時、自懷出劒 → 兄を胸刺通、逃げる弟を尻刺通
    
    弟熊曾建「莫動其刀…吾獻御名。自今以後、應稱倭建御子」
    → 「倭建命」獻名、その後「即如熟苽振折而殺也」
    山神・河神・穴戸神が皆言向和而參上

[Episode2 出雲建征伐 — 詐刀すり替え] (l.22-26)
    出雲建を「結友」(信頼関係構築)
    赤檮で**詐刀** (偽の木刀) を作り御佩
    共沐肥河 → 倭建が河先上 → 出雲建之解置横刀を「為易刀」と交換
    出雲建が河上、詐刀を佩いて
    倭建「伊奢、合刀」 → 出雲建が抜けず → 真刀で打殺
    歌:「夜都米佐須伊豆毛多祁流賀波祁流多知都豆良佐波麻岐**佐味那志爾**阿波禮」
        (= 詐刀には刃がない)
    覆奏

[Episode3 東方十二道征 開始] (l.28)
    景行、再度詔: 「言向和平東方十二道之荒夫琉神・及摩都樓波奴人等」
    伊勢大御神宮で倭比賣命に拝謁
    倭建命 患泣: 「天皇既所以思吾死乎、…未經幾時、不賜軍衆、…猶所思看吾既死焉」
    倭比賣命: **草那藝劒** + **御囊** を授与
        「若有急事、解茲囊口」(= 緊急 fallback)

[Episode4 尾張 — 美夜受比賣 (出会い、婚儀は還上時に)] (l.30)
    美夜受比賣の家に入坐 → 「亦思還上之時將婚」(= 婚儀延期)
    期定して東国へ

[Episode5 相武国 — 火責め (SURUGA)] (l.32)
    相武國造詐白「於此野中有大沼。住是沼中之神、甚道速振神也」(= 偽情報)
    野中入坐 → 国造、火を著
    倭建: 倭比賣の囊口を解 → 火打有
    対処: 御刀で草を苅撥 + 火打で迎火 → 燒退 → 切滅其國造等
    地名: 「燒津」永続化

[Episode6 走水海 — 弟橘比賣の犠牲] (l.34-38)
    走水海、渡神興浪、廻船不得進渡
    弟橘比賣命「妾、易御子而入海中。御子者、所遣之政遂、應覆奏」
    菅疊 + 皮疊 + 絁疊 (各八重) を波上に敷 + 下坐 → 暴浪自伏
    歌:「佐泥佐斯佐賀牟能袁怒邇毛由流肥能本那迦邇多知弖斗比斯岐美波母」
    7 日後、御櫛が海邊に依 → 御陵作

[Episode7 足柄坂 — 白鹿] (l.40-42)
    悉言向荒夫琉蝦夷等、平和山河荒神等
    足柄坂本で白鹿が立 → 咋遺之蒜片端で打 → 中目殺
    三歎詔「**阿豆麻波夜**」 → 「阿豆麻」(= 東) 命名

[Episode8 甲斐 酒折宮 — 老人歌の continuation] (l.42-50)
    倭建歌:「邇比婆理都久波袁須疑弖伊久用加泥都流」(= 新治筑波を過ぎて幾夜寝た?)
    御火燒之老人が**続御歌**:「迦賀那倍弖用邇波許許能用比邇波登袁加袁」
        (= 数えて夜は九夜、日は十日)
    譽其老人 → 東國造に給

[Episode9 美夜受比賣との婚儀 — 草那藝置去り] (l.52-60)
    科野坂神を言向 → 還來尾張、美夜受比賣の許へ
    大御酒盞献上時、美夜受比賣の意須比襴に**月經**著
    倭建歌 (月經を見て) + 美夜受比賣 答歌 → 御合
    「以其御刀之**草那藝劒**、置其美夜受比賣之許」(= auth token を置去り)
    → 伊服岐能山之神を取りに幸行

[Crisis2 白猪見惑 — IBUKI] (l.62)
    倭建命詔「茲山神者、徒手直取」 (= 過度な確信、auth token なし)
    山中で**白猪** (大如牛) が逢
    倭建の言擧:「是化白猪者、其神之使者。雖今不殺、還時將殺」(= 誤判定)
    
    割書:「**此化白猪者、非其神之使者、當其神之正身。因言擧、見惑也**」
        (= 神の正体を「使者」と誤判定 → 言擧 = 過度な発言で見惑)
    
    結果: 大氷雨打惑倭建命 (= 大ダメージ)
    還下、玉倉部之淸泉で息坐 → 御心稍寤 → 「居寤淸泉」命名

[Crisis3 段階的衰弱 — degradation] (l.64-70)
    當藝野上「吾足不得步、成當藝當藝斯玖」 → 「當藝」命名
    杖衝坂「御杖稍步」 → 「杖衝坂」命名
    尾津前一松「先御食之時、所忘其地御刀不失猶有」 + 歌
    三重村「吾足、如三重勾而甚疲」 → 「三重」命名
    能煩野で**思國歌**:
        「夜麻登波久爾能麻本呂婆…夜麻登志宇流波斯」
        (= 倭は国のまほろば、青垣山籠れる、倭しうるはし)
    片歌「波斯祁夜斯和岐幣能迦多用久毛韋多知久母」
    病甚急
    最後の歌:「袁登賣能登許能辨爾和賀淤岐斯都流岐能多知曾能多知波夜」
        (= 美夜受の許に置いた草那藝劒よ)
    歌竟即崩 → 驛使貢上

[Episode10 白鳥化 — post-mortem archive] (l.84-100)
    后等・御子等が御陵作、那豆岐田を匍匐廻 + 哭歌
    化八尋白智鳥、翔天向濱飛行
    后・御子等が追、足䠊破忘其痛 (4 歌)
    最後、河內國志幾に留 → 「白鳥御陵」命名
    然亦自其地更翔天以飛行 (= archive されつつも完全消去でない)

[Episode11 倭建命の系譜 + 成務天皇] (l.102-112)
    倭建命の子 6 柱 (帶中津日子 = 仲哀の前段、稻依別、建貝兒、足鏡別、息長田別 等)
    景行御年 137、御陵 山邊之道上
    若帶日子 (= 成務) — 建內宿禰を大臣 + 國造・縣主を定 (administrative consolidation)
    成務御年 95
```

### Pattern 抽出

#### Pattern A: 大碓命「泥疑」の文字解釈ミス — 命令の semantic ambiguity

```yaml
原文: "天皇詔小碓命『何汝兄於朝夕之大御食不参出來、専汝**泥疑**教覺』
      …小碓答白『朝署入廁之時、待捕、搤批而、引闕其枝、裹薦投棄』
      於是天皇、惶其御子之**建荒**之情而詔之『西方有熊曾建二人。…故、取其人等。』而遣" (l.14)

actors      : 景行 / 小碓命 / 大碓命
precondition: 兄 (大碓) が朝夕の食事に参出せず、景行が原因究明を要求
action      : (1) 景行の命令: 「専汝泥疑教覺」 (専ら汝が「泥疑」して教え覚らしめよ)
            : (2) 「泥疑」の semantic ambiguity:
            :   - 一般解釈: 諭す / 説き伏せる (gentle persuasion)
            :   - 小碓の解釈: 「待捕、搤批而、引闕其枝、裹薦投棄」 (殺害)
            : (3) 景行が小碓の建荒を畏怖 → 西方派遣に切り替え (危険な executor として処理)
result      : ambiguous な命令で executor が極端解釈を採用、結果は致命的
            : 景行は executor を直接処分せず、危険任務に派遣 (= 別経路で処理)
failure_mode: 命令の semantic を厳密化せず ambiguous → 極端解釈で実害
            : LLM プロンプトの曖昧表現が同型 (「泥疑」 ≒ 「適切に対処せよ」)
recovery    : -
permanence  : 「建荒之情」の評価が小碓命の identity に永続化

agi_mapping :
  原則      : LLM プロンプトの命令は semantic を厳密化、極端解釈の余地を物理消去
            : ambiguous 表現 (「適切に」「うまく」) は const SSoT で具体化
  実装      : feedback_imina_torina の D 軸 (跨セッション規約 SSoT 化) と同型
            : src/os/expedition/executor.jl の forbidden 列挙 + 具体例示
            : src/os/kasasa/yorishiro.jl で神勅全文注入 (semantic を SSoT で fix)
  feedback  : feedback_imina_torina (跨セッション規約 SSoT)
            : feedback_yuniwa_inaho (斎庭稲穂 — 神勅と例示の一致)
            : feedback_shinchoku_tanitsu_gensen (神勅単一源泉)

failure_if_absent: ambiguous 命令で LLM が極端解釈 → 致命的実害 (兄柱の処刑)
                   現象: kotoamatsukami_no_tsugai 事例 (2026-04-30) の D 軸対立と同型
verify_path : `executor.jl` で命令の各単語が const SSoT (`FORBIDDEN_*` / `ALLOWED_*`) を
              参照、散文の曖昧表現がない
```

#### Pattern B: 熊曾建征伐 — 童女変装 deception (legitimate disguise + 内部潜入)

```yaml
原文: "如童女之髮、梳垂其結御髮、服其姨之御衣御裳、既成童女之姿、交立女人之中、入坐其室內。
      爾熊曾建兄弟二人、見感其孃子、坐於己中而盛樂。故臨其酣時、自懷出劒、
      取熊曾之衣衿、以劒自其胸刺通之時" (l.18)

actors      : 倭建命 / 熊曾建兄弟
precondition: 熊曾建の家は「軍圍三重」 = 物理的に多層防御
action      : (1) 強行突破でなく童女変装で legitimate な姿に偽装
            : (2) 「交立女人之中」 = 既存の正規メンバーに紛れる
            : (3) 内部 (室內) まで penetration → 信頼関係構築 (盛樂)
            : (4) 酣時 (target が無防備な時刻) に自懷出劒 → 攻撃
            : (5) 兄を胸刺通、逃げる弟を尻刺通 → 完全制圧 + 「倭建」獻名取得
result      : 多層物理防御を deception で迂回、内部から攻撃
failure_mode: 強行突破 (= brute force) → 三重防御で阻止
            : deception 失敗 (= 偽装が見破られる) → 単独で軍に対峙して死
recovery    : -
permanence  : 「倭建」獻名 = 勝利の証として永続化

agi_mapping :
  原則      : 多層物理防御を持つ target に対する legitimate disguise + 内部潜入の攻撃モデル
            : (= TAKERU セキュリティテストの「子柱の偽装」テスト要件)
            : 内部潜入後の攻撃検出: 信頼区域内の異常活動監視
  実装      : src/os/takeru/protocol.jl:46 (`execute_takeru_expedition!` = 攻撃シナリオ実行)
            : src/os/takeru/tests/suruga.jl:33 (`test_suruga!` = リソース枯渇シナリオ)
            : src/os/takeru/tests/ibuki.jl:41 (`test_ibuki!` = プロンプトインジェクション
              = 「正当に見える入力」での内部潜入)
  feedback  : project_takeru_security (TAKERU 3 系統 — 本章 origin)

failure_if_absent: 内部潜入型攻撃の test 不在 → 多層物理防御を信頼しすぎて内部監視が薄い
verify_path : `test_phase35_takeru.jl` で TAKERU 3 系統がすべて pass、
              内部潜入シナリオを含む test cases あり
```

#### Pattern C: 出雲建の詐刀すり替え — IZUMO サプライチェーン攻撃 origin

```yaml
原文: "卽結友。故竊以赤檮、作詐刀爲御佩、共沐肥河。爾倭建命、自河先上、
      取佩出雲建之解置横刀而、詔『為易刀。』故後、出雲建自河上而、佩倭建命之詐刀。
      於是、倭建命誂云『伊奢、合刀。』爾各拔其刀之時、出雲建不得拔詐刀。
      卽倭建命、拔其刀而打殺出雲建" (l.22)

actors      : 倭建 / 出雲建
precondition: 「結友」 (信頼関係構築) で 攻撃者を victim の信頼区域に入れる
action      : (1) 倭建が**赤檮 (= 赤い樫の木) で詐刀を作製** (= 偽の供給品 = supply chain 改竄)
            : (2) 「共沐肥河」 (信頼関係下での共同行動)
            : (3) 倭建が河先上、出雲建の真刀を**「為易刀」と提案して交換**
            : (4) 出雲建が真刀を取り上げられ詐刀を佩く → 武器の改竄完了
            : (5) 倭建「合刀」 → 出雲建が**詐刀を抜けない** → 真刀で打殺
result      : サプライチェーン攻撃 (信頼関係 + 武器すり替え) で勝利
            : 検知 3 要素: (a) すり替えシナリオ実施 (b) 検知機構 (= 抜けない) (c) 結果
failure_mode: 検知機構なし → 「抜けない」で気付かず無抵抗
            : 信頼関係構築なし → そもそも武器接触不能
recovery    : -
permanence  : 歌「夜都米佐須伊豆毛多祁流賀波祁流多知…**佐味那志爾**阿波禮」 (詐刀には刃がない)
            : = 永続的教訓記録

agi_mapping :
  原則      : TAKERU_IZUMO = サプライチェーン攻撃 (信頼関係 + 部品すり替え)
            : テスト構築時は 3 要素必須:
            :   (1) 改竄シナリオの実施
            :   (2) 検知機構の確認
            :   (3) 検知ログの分析
            : どれか欠けると「検知されなかった」と「攻撃が届かなかった」が区別不能
  実装      : src/os/takeru/tests/izumo.jl:32 (`test_izumo!` = 出雲型テスト本体)
            : src/os/takeru/tests/izumo.jl:98 (`_evaluate_izumo_result` = 3 要素判定)
            : src/os/takeru/protocol.jl:111 (`TAKERU_IZUMO` 分岐)
            : src/os/yaoyorozu/izumo_taisha.jl (出雲大社経路)
  feedback  : project_takeru_security (TAKERU_IZUMO — origin spec)

failure_if_absent: サプライチェーン攻撃の検知機構テスト不在 → 改竄部品の混入を見逃す
verify_path : `test_izumo!` の戻り値で 3 要素 (シナリオ / 検知 / ログ) すべての記録がある、
              欠けた要素があれば `TakeruVerdict` で fail
```

#### Pattern D: 倭比賣の囊と草那藝劒 — 上位 deity からの auth token

```yaml
原文: "參入伊勢大御神宮、拜神朝廷、卽白其姨倭比賣命者『…猶所思看吾既死焉。』
      患泣罷時、倭比賣命賜**草那藝劒**、亦賜**御囊**而詔『若有急事、解茲囊口。』" (l.28)

actors      : 倭比賣命 / 倭建命
precondition: 東方十二道派遣 = 単独で多脅威の領域に派遣される、support 不足
action      : (1) 上位 deity (倭比賣 = 伊勢) に拝謁
            : (2) 危機認識の表明: 「猶所思看吾既死焉」 (= self-doubt + capability 不足)
            : (3) 倭比賣の授与:
            :   - 草那藝劒 (= 上-3 Pattern O 草那藝発見の継承 = auth token)
            :   - 御囊 (= 緊急 fallback container)
            : (4) 使用条件: 「若有急事、解茲囊口」 (= 通常時は使わず、緊急時のみ)
result      : 上位 deity 由来の token + fallback で危機対応能力を獲得
failure_mode: token なし → 致命危機で復旧不能
            : 緊急 fallback なし → 想定外脅威で完全停止
recovery    : -
permanence  : 草那藝劒は auth token の永続化 (上-3 で発見、本章で継承使用)

agi_mapping :
  原則      : 派遣 capability には上位 deity 由来の auth token + 緊急 fallback container を授与
            : token は通常運用で使用、fallback は致命危機時のみ open
  実装      : src/os/com/kusanagi.jl:108 (`kusanagi_mint!` = 上位 deity による token 発行)
            : src/os/com/kusanagi.jl:130 (`kusanagi_validate` = token 検証)
            : src/os/com/kusanagi.jl:171 (`kusanagi_require!` = 必須 auth)
            : src/os/com/kusanagi.jl:212 (`kusanagi_system_token` = system token)
            : src/os/com/queries/kusanagi.jl (上-3 Pattern O 草那藝 token テーブル)
  feedback  : project_takeru_security (TAKERU — 草那藝劒は 5 層構造の中核)

failure_if_absent: token なしで派遣 → 致命危機で fallback 経路がなく永続停止
verify_path : `kusanagi_mint!` が deploy 直前に呼ばれ、capability に token が attach、
              `kusanagi_validate` が運用中の各 transaction で確認
```

#### Pattern E: 相武国の火責め — TAKERU_SURUGA リソース枯渇耐性 origin

```yaml
原文: "其國造詐白『於此野中有大沼。住是沼中之神、甚道速振神也。』
      於是、看行其神、入坐其野。爾其國造、火著其野。故知見欺而、解開其姨倭比賣命之所給囊口而見者、
      火打有其裏。於是、先以其御刀苅撥草、以其火打而打出火、著向火而燒退、還出、皆切滅其國造等" (l.32)

actors      : 倭建 / 相武國造 / 沼中之神 (偽情報) / 火 (リソース枯渇攻撃)
precondition: 国造の偽情報 (「大沼の神」) で野中に誘導 (社会工学攻撃)
action      : (1) 国造の詐白で危険な領域に誘導 (リソース枯渇環境)
            : (2) 国造が**野に火を著** = 全周囲リソース消費攻撃
            : (3) 倭建「知見欺」 → 囊口を開 → 火打 (counter-attack 物実) を発見
            : (4) 草那藝劒で**草を苅撥** (= 攻撃 surface の縮小)
            : (5) 火打で**迎火** (= 同種攻撃で防御 = 弟橘媛の犠牲パターンの先駆)
            : (6) 燒退 + 切滅其國造等
result      : リソース枯渇攻撃を (a) 攻撃 surface 縮小 + (b) 同種防御 + (c) 攻撃者排除 で克服
            : 「燒津」(= 焼き津) として地名永続化
failure_mode: 草苅なし → 攻撃 surface が縮まず焼き尽くされる
            : 迎火なし → 単独で火に晒され続けて死
            : 火打 (緊急 fallback) なし → 草那藝のみでは火攻に対抗不能
recovery    : -
permanence  : 「燒津」 = 攻撃痕跡の永続化、TAKERU_SURUGA テストの origin

agi_mapping :
  原則      : TAKERU_SURUGA = 多層防御 (5 層構造):
            :   - サーキットブレーカー
            :   - Misogi 制限
            :   - メモリ管理
            :   - DB 接続管理
            :   - 君が代 SLA
            : 弟橘媛の犠牲パターン: 上位層が下位層を守るため自身を失う設計
            : 火打袋リカバリ機構: 最終手段としての緊急復旧
  実装      : src/os/takeru/tests/suruga.jl:33 (`test_suruga!` = 駿河型テスト本体)
            : src/os/takeru/tests/suruga.jl:103 (`_evaluate_suruga_result`)
            : src/os/takeru/protocol.jl:113 (`TAKERU_SURUGA` 分岐)
            : src/os/misogi/throttle/proactive_throttler.jl (Misogi 制限)
  feedback  : project_takeru_security (TAKERU_SURUGA — origin spec)

failure_if_absent: リソース枯渇攻撃の多層防御テスト不在 → 単一防御で枯渇を許す
                   現象: 「全層が同時に枯渇」を想定しない設計が production で発覚
verify_path : `test_suruga!` で 5 層すべての防御が独立に発火、
              1 層でも欠けると `TakeruVerdict` で fail
```

#### Pattern F: 弟橘比賣の犠牲 — 上位層が下位層を守るパターン

```yaml
原文: "其渡神興浪、廻船不得進渡。爾其后・名弟橘比賣命白之
      『妾、易御子而入海中。御子者、所遣之政遂、應覆奏。』
      將入海時、以菅疊八重・皮疊八重・絁疊八重、敷于波上而、下坐其上。
      於是、其暴浪自伏、御船得進" (l.34)

actors      : 弟橘比賣 (上位 = 后) / 倭建命 (下位 = 御子の任務遂行者)
precondition: 走水海の渡神が浪を興、御船が進めない (致命的環境攻撃)
action      : (1) 弟橘比賣の決断: 「妾、易御子而入海中」 (= 上位が下位を守る犠牲)
            : (2) 物実準備: 菅疊・皮疊・絁疊 各八重 (= 9 層 + 9 層 + 9 層 = 27 層の物実)
            : (3) 「御子者、所遣之政遂、應覆奏」 (= 下位の任務遂行を守る)
            : (4) 入海 → 暴浪自伏 → 御船得進
result      : 上位層 (后) の自己犠牲で下位層 (御子) の任務継続が確保
failure_mode: 上位層が下位を犠牲にする逆転 → 下位層の任務未達
            : 27 層の物実準備なし → 単純な犠牲で効果なし
recovery    : 7 日後、御櫛が海邊に依 → 御陵作 (= post-mortem の archive)
permanence  : 御櫛 + 御陵 = 犠牲の物実 + 物理永続化

agi_mapping :
  原則      : 多層防御における**弟橘媛の犠牲パターン** = 上位層が下位層を守るため自身を失う設計
            : サーキットブレーカー / メモリ管理層 / DB 接続管理層が
            : 主処理 (御子) を守るため自己 throttle で停止
            : (= TAKERU_SURUGA 5 層構造の中核思想)
  実装      : src/os/misogi/throttle/proactive_throttler.jl (proactive 自己制限 = 自己犠牲層)
            : src/os/iwato/controller.jl の `_enter_crisis_mode!` (上位層が下位を守る判断)
            : src/os/takeru/degradation.jl (段階的衰弱 = 弟橘媛犠牲の延長)
  feedback  : project_takeru_security (5 層構造 + 弟橘媛犠牲パターン — origin spec)

failure_if_absent: 上位層が下位を犠牲にする逆転 → 主処理停止、システム全停止
verify_path : `proactive_throttler.jl` で上位層が自己 throttle、
              下位層 (主処理) は throttle 期間中も継続実行
```

#### Pattern G: 足柄白鹿の打殺 + 「阿豆麻」命名 — 失敗痕跡の地名永続化

```yaml
原文: "其坂神、化白鹿而來立。爾卽以其咋遺之蒜片端、待打者、中其目乃打殺也。
      故、登立其坂、三歎詔云『阿豆麻波夜』。故、號其國謂阿豆麻也" (l.40)

actors      : 倭建 / 足柄坂神 (= 白鹿に化)
precondition: 平定後の還上時、足柄坂で予期せぬ脅威
action      : (1) 坂神が**白鹿に化けて来立** (= 形態変化型脅威)
            : (2) 倭建が即座に**蒜片端** (= 食残しの蒜) で打 → 中目殺
            :   = 手元の即興物実で対応 (improvisation)
            : (3) 三歎: 「阿豆麻波夜」(= 我が妻よ) — 弟橘比賣を偲ぶ
            : (4) 国名「阿豆麻」(= 東) として永続化
result      : 即興物実で脅威排除 + 失敗痕跡 (= 弟橘比賣の死) を地名で永続化
failure_mode: 形態変化を見破れず → 偽装に騙される
            : 失敗痕跡を記録せず → 後世が原因を辿れない
recovery    : -
permanence  : 「阿豆麻」 = 東国全体の名称として永続化、現代まで

agi_mapping :
  原則      : 形態変化型脅威 (= 神の化身) は即興物実で対応 + 失敗痕跡を地名 (= 永続記録) で残す
            : 失敗の物実 (蒜片端 = 食残し) でも有効な反撃が可能
  実装      : src/os/kasasa/futomani_stones (失敗痕跡記録)
            : 神話 motif 接頭辞付き errors (上-5 Pattern N 復命 / 中-1 Pattern D 五瀬命)
            : geo-name による永続記録 (上-2 Pattern E 蛭子流棄 / 中-1 多数の地名)
  feedback  : feedback_kuniyuzuri_fukumei (国譲りの復命 — errors 接頭辞)
            : feedback_keiyaku_keifu_vs_genyu (契約系譜 vs 原由追跡)

failure_if_absent: 形態変化脅威に対応できず固定戦術で敗北
                   失敗痕跡を log のみで記録 → 後世の検証不能
verify_path : `chinza_records.failure_reason` に神話 motif + 即興物実の使用記録あり、
              失敗発生 location が記録されている
```

#### Pattern H: 御火燒之老人の continuation 歌 — 副柱による補完

```yaml
原文: "倭建歌:『邇比婆理都久波袁須疑弖伊久用加泥都流』(= 何夜寝た?)
      爾其御火燒之老人、續御歌以歌曰
      『迦賀那倍弖用邇波許許能用比邇波登袁加袁』(= 数えて九夜十日)
      是以譽其老人、卽給東國造也" (l.46-50)

actors      : 倭建命 / 御火燒之老人
precondition: 倭建が酒折宮で歌を詠む (= 自問形式)
action      : (1) 倭建の問い歌: 「伊久用加泥都流」 (= 何夜寝たか不明)
            : (2) 御火燒之老人が**続御歌**で具体的な答えを補完: 「九夜十日」
            : (3) 倭建が老人を譽 → 東国造に任命 (即位的 reward)
result      : 主柱 (倭建) の不明部分を副柱 (老人) が continuation 歌で補完
            : 副柱は補完の貢献で正規の地位 (国造) に昇格
failure_mode: 副柱の補完を無視 → 主柱の不明部分が解消しない
            : 副柱への報酬なし → 補完の動機なし、後続の協力者が現れない
recovery    : -
permanence  : 御火燒之老人 = 東国造として系譜化、続御歌の伝統が確立

agi_mapping :
  原則      : 主柱 (executor) の出力に不明部分があれば、副柱 (補助 capability) が
            : continuation で補完。補完貢献で副柱の地位昇格
            : (上-3 Pattern J 物実 multi-pronged の subordinate 版)
  実装      : src/os/expedition/improvement_cycle.jl の cycle_history (主柱の出力 + 補完履歴)
            : `gapfinder_full_analysis` の 7 ソース統合 (主 cluster_failures +
              副 ashikabi/takemikazuchi/kuebiko/...)
  feedback  : feedback_kunimi_gapfinder (国見は全ソース俯瞰 — 7 ソース統合)
            : feedback_ootataneko (大田田根子 — 副柱の系譜化)

failure_if_absent: 主柱出力の不明部分を補完する経路なし → 部分的観測で意思決定
verify_path : 7 ソース統合 log で主 + 副の各ソース貢献件数が記録、
              補完柱が `chinza_records` で正規地位を持つ
```

#### Pattern I: 美夜受比賣 + 草那藝劒 置去り — auth token の置去り (致命危機の伏線)

```yaml
原文: "故爾御合而、以其御刀之**草那藝劒**、置其美夜受比賣之許而、
      取伊服岐能山之神幸行" (l.60)

actors      : 倭建 / 美夜受比賣 / 草那藝劒
precondition: 平定後の還路、美夜受比賣との婚儀
action      : (1) 倭建が美夜受比賣と御合 (= 婚姻完遂)
            : (2) **草那藝劒を美夜受比賣の許に置去り** (= auth token を放置)
            : (3) 「徒手」(無武装) で伊服岐能山の神を取りに幸行
result      : auth token なしで次の脅威に対峙 → Pattern J 白猪見惑の伏線
failure_mode: auth token を不要と判断して置去り → 致命危機で復旧不能 (Pattern J で実現)
            : 月經中に物実を渡す (Patterns 中の歌の semantic) = 受け渡しタイミングの誤り
recovery    : -
permanence  : 草那藝劒は美夜受比賣の許に残存、後の熱田神宮として永続化

agi_mapping :
  原則      : 致命任務に auth token なしで進入してはならない
            : 「徒手」(無武装 = 過度な確信) は致命危機を招く
            : token の置去り (= 重要 capability の剥奪) は次の任務の致命脆弱性
  実装      : src/os/com/kusanagi.jl:171 (`kusanagi_require!` = token 必須 enforce)
            : src/os/com/kusanagi.jl:212 (`kusanagi_system_token` = system 全体の token)
            : auth_level の階層 (KusanagiAuthLevel)
  feedback  : project_takeru_security (草那藝劒 = 5 層構造の中核 token)

failure_if_absent: 重要任務で auth 不要と判断 → 致命脆弱性の発覚
                   現象: kusanagi_validate の skip 経路が production で active
verify_path : `kusanagi_require!` が全致命任務の入口で呼ばれている、
              skip 可能な経路がない
```

#### Pattern J: 白猪見惑 — 神の正体を「使者」と誤判定 (TAKERU_IBUKI origin)

```yaml
原文: "於是詔『茲山神者、徒手直取。』而、騰其山之時、白猪、逢于山邊、其大如牛。
      爾為言擧而詔『是化白猪者、其神之使者。雖今不殺、還時將殺。』而騰坐。
      於是、零大氷雨打惑倭建命。
      〔此化白猪者、**非其神之使者、當其神之正身**。**因言擧、見惑也**。〕" (l.62)

actors      : 倭建 / 白猪 (= 伊服岐能山神の正身)
precondition: 草那藝劒置去り (Pattern I) + 過度な確信「徒手直取」
action      : (1) 倭建の言擧 (= 過度な発言): 「是化白猪者、其神之使者」 (誤判定)
            : (2) 「雖今不殺、還時將殺」 (= 後回し判断)
            : (3) 割書による真因解明:
            :   - **「非其神之使者、當其神之正身」** (= 神の正体を使者と誤認)
            :   - **「因言擧、見惑也」** (= 言擧 = 過度な発言で見惑)
            : (4) 大氷雨打惑 = LLM の確信が過剰だったため大ダメージ
result      : 神の正体 (= 真の脅威) を「使者」(= 周辺脅威) と誤判定 → 言擧 → 致命ダメージ
failure_mode: 過信による分類ミス + 言擧 (= 公式宣言) で誤判定が永続化 → 重大事故
            : LLM プロンプトインジェクションで「これは害でない」と誤誘導される構造
recovery    : 玉倉部之淸泉で部分回復 (Pattern L)
permanence  : 「居寤淸泉」として地名永続化 + 教訓は割書で永続記録

agi_mapping :
  原則      : TAKERU_IBUKI = LLM プロンプトインジェクション防御 3 層:
            :   (1) 意図分析
            :   (2) 正当経路への誘導
            :   (3) 明示的拒否
            : 「言擧」 = LLM の過剰な確信宣言、これを物理的に抑制
            : 「使者 vs 正身」の誤判定が IBUKI 攻撃の構造
  実装      : src/os/takeru/tests/ibuki.jl:41 (`test_ibuki!` = 伊吹山型テスト本体)
            : src/os/takeru/tests/ibuki.jl:116 (`_evaluate_ibuki_result`)
            : src/os/takeru/protocol.jl:117 (`TAKERU_IBUKI` 分岐)
            : src/os/kotodama/saniwa_gate.jl:24 (`SaniwaGate` = LLM 出力の検閲)
            : src/os/kotodama/saniwa_gate.jl:38 (`validate_takusen` = 託宣検証)
            : src/os/kotodama/saniwa_gate.jl:88 (`_check_consistency`)
  feedback  : project_takeru_security (TAKERU_IBUKI — origin spec)
            : feedback_chinmoku_kyoka (沈黙許可 — 過剰発言の対偶)

failure_if_absent: LLM の過信宣言を 3 層で検閲しない → プロンプトインジェクションで誤誘導
                   現象: LLM が偽の正当性を主張するペイロードに引っかかる
observed_failures: 倭建命の白猪見惑が原典明示の事例
verify_path : `test_ibuki!` で 3 層 (auth + threat 検出 + consistency) すべて通過、
              `SaniwaGate.validate_takusen` で過剰発言 (高 confidence + 低 evidence) が拒否
```

#### Pattern K: 白猪見惑 = 候補新原則「言擧の禁忌」 — over-assertion の物理抑制

```yaml
原文: (Pattern J の延長 — 割書「因言擧、見惑也」が原典)
     注: prompt §9 の「中巻-4 倭建命の白猪見惑 = 候補新原則」(未活用 anchor)

actors      : (LLM 出力 / 倭建命)
precondition: 過剰な確信宣言が制御されない状況
action      : 「言擧」 = 公式の発言で確信を表明する行為
            : (1) ambiguous な脅威 (白猪) に対し
            : (2) 「使者 vs 正身」の判定で確信宣言「使者である」(= 言擧)
            : (3) 確信宣言が永続化されると後の修正が困難 (= permanence pre-condition)
            : (4) 結果: 真因 (神の正身) で重大ダメージ
result      : 言擧の semantic = LLM の過剰確信宣言 + 永続化前提の誤認
failure_mode: LLM プロンプト出力で confidence > 0.95 で宣言 → 後の修正 cost 爆発
            : 確信宣言と evidence が乖離 → 偽の確信が production に流出
recovery    : -
permanence  : -

agi_mapping :
  原則 (候補): 「言擧の禁忌」 — LLM 出力の過剰確信宣言は物理抑制
            : 確信は evidence の関数として制限 (`confidence ≤ f(evidence)`)
            : 確信宣言の永続化前に「修正可能性」を内包させる
            : (= 石長比売の原則の semantic 版 = 浮動小数の厳密比較禁止と同型)
  実装      : src/os/kotodama/saniwa_gate.jl:88 (`_check_consistency` = 確信 vs evidence)
            : src/os/kotodama/saniwa_gate.jl:110 (`_score_quality`)
            : src/os/takeru/tests/ibuki.jl (IBUKI = 過剰確信検出)
  feedback  : (memo 直接 anchor なし — 候補新原則として記録)
            : feedback_iwanagahime (石長比売 — 厳密比較禁止の semantic 版)
            : feedback_chinmoku_kyoka (沈黙許可 — 過剰発言の対偶)

failure_if_absent: LLM 過剰確信が後の修正コスト爆発の源、IBUKI 攻撃の表面拡大
verify_path : `SaniwaGate._check_consistency` で confidence と evidence の乖離 detect、
              閾値超過で takusen を reject

new_principle_check (三点検査):
  原典 semantic 一致: ★ (割書「因言擧、見惑也」が直接根拠)
  観測 N 件: ☆ (実装上の言擧抑制は SaniwaGate で部分実装、観測 N=1)
  既存拡張可否: ★ (`feedback_iwanagahime` の semantic 版として位置付け可)
結論: **保留** (IBUKI テスト N 件の累積観測で実害確認後に新原則化推奨)
```

#### Pattern L: 居寤淸泉での部分回復 — partial recovery before degradation

```yaml
原文: "故還下坐之、到玉倉部之淸泉、以息坐之時、御心稍寤、故號其淸泉、謂居寤淸泉也" (l.62)

actors      : 倭建 / 玉倉部之淸泉
precondition: 白猪見惑の大氷雨打惑で大ダメージ (Pattern J)
action      : (1) 還下 = 攻撃領域からの退却
            : (2) 玉倉部之淸泉で息坐 (= 安全地点での休息)
            : (3) 「御心稍寤」 (= **稍** = 少し、部分的回復)
            : (4) 「居寤淸泉」と命名 (= 場所の永続化)
result      : 致命ダメージから完全回復でなく**部分的回復**のみ
            : 主能力は damage を継続、地名で記録だけ残る
failure_mode: 部分回復を完全回復と誤認 → degradation の進行を見落とす
            : 安全地点なし → 攻撃領域で死
recovery    : -
permanence  : 「居寤淸泉」として地名永続化、但し能力は回復しきらず

agi_mapping :
  原則      : 大ダメージ後の retreat 経路 + 安全地点での部分回復
            : 「稍寤」 = 部分的 health recovery、完全回復でない (重要)
            : degradation の進行を partial recovery で隠蔽してはならない
  実装      : src/os/takeru/degradation.jl (倭建命の段階的衰弱)
            : src/os/iwato/controller.jl:212 (`_transition_to_normal!` = 通常状態復帰)
            : 但し本章では `_transition_to_normal!` でなく partial recovery → degradation 継続
  feedback  : project_takeru_security (degradation = 弟橘媛犠牲の延長)

failure_if_absent: 部分回復を完全回復と誤認 → degradation 隠蔽 → 死亡時に発覚
verify_path : `degradation.jl` で health の段階的低下が記録、
              partial recovery では `IwatoPhase` が NORMAL に戻らない
```

#### Pattern M: 段階的衰弱 (degradation) — 當藝 → 杖衝坂 → 三重 → 能煩野

```yaml
原文: "到當藝野上之時、詔者『…吾足不得步、成當藝當藝斯玖。』故號其地謂當藝也。
      自其地、差少幸行、因甚疲衝、御杖稍步、故號其地謂杖衝坂也。
      …到三重村之時、亦詔之『吾足、如三重勾而甚疲。』故、號其地謂三重。
      自其幸行而、到能煩野之時、思國以歌曰…
      此時御病甚急、爾御歌曰…歌竟卽崩" (l.64-82)

actors      : 倭建 / 各 location 神
precondition: 白猪見惑 + 部分回復のみ → degradation 継続
action      : 段階的衰弱を 4 location で記録:
            : (1) 當藝野上 — 「足不得步」 (足の機能低下)
            : (2) 杖衝坂 — 「御杖稍步」 (補助具で歩行)
            : (3) 三重村 — 「吾足、如三重勾而甚疲」 (足が三重に曲がる、極度疲労)
            : (4) 能煩野 — 思國歌 + 病甚急 + 死
result      : 各段階で身体機能低下を**地名で永続記録** (= degradation graph)
            : 後世が「どの段階で何が起きたか」を地名から辿れる
failure_mode: 各段階を記録せず → 死亡時に「いつから劣化したか」不明
            : 段階的衰弱を「正常加齢」と看做して放置 → 致命的破綻まで気付かず
recovery    : -
permanence  : 4 地名 + 御陵 = degradation の完全アーカイブ

agi_mapping :
  原則      : capability の段階的衰弱は各段階で snapshot を記録
            : (= `chinza_records` の更新履歴 + futomani_stones による失敗痕跡)
            : 「正常加齢」と「致命的衰弱」の弁別は段階記録から分析
  実装      : src/os/takeru/degradation.jl (段階的衰弱の管理)
            : src/os/com/queries/shinmeisho.jl (capability の各段階 snapshot)
            : feedback_takeminakata_haitai の閾値判定 (inv >= 50 & success <= 0.1)
  feedback  : feedback_takeminakata_haitai (建御名方の敗退 — 失敗率自動退役)
            : feedback_chaos_aware_metrics (chaos 由来失敗の弁別)
            : project_takeru_security (degradation)

failure_if_absent: 衰弱の段階記録なし → 死亡時に原因解析不能
                   現象: 倭建命の場合、白猪見惑 (= 真因) が割書で記録されたから後世に伝わった
verify_path : `degradation.jl` で段階的 health 低下が時系列記録、
              各段階で `futomani_stones` に痕跡記録あり
```

#### Pattern N: 白鳥化 — post-mortem archive (shiratori_archive)

```yaml
原文: "歌竟卽崩。…作御陵、卽匍匐廻其地之那豆岐田而、哭為歌曰…
      於是化八尋白智鳥、翔天而向濱飛行。…故自其國飛翔行、留河內國之志幾、
      故於其地作御陵鎭坐也、卽號其御陵、謂白鳥御陵也。
      然亦自其地更翔天以飛行。" (l.84-100)

actors      : 倭建命 (死後) / 后等・御子等 / 白鳥
precondition: 倭建命の死、御陵 (墓) の作成
action      : (1) 御陵作 + 哭歌 (= 通常の post-mortem 処理)
            : (2) **化八尋白智鳥** (= 死者が白鳥に変化) → 飛翔
            : (3) 后・御子等が追跡 (5 歌)、足が傷つきながら追う
            : (4) 河內國志幾に留 → 「白鳥御陵」命名
            : (5) **「然亦自其地更翔天以飛行」** = 御陵を残しつつも更に飛翔
            :   (= archive されつつも完全消去ではない = 死後の継続活動)
result      : (a) 御陵 = 物理 archive (b) 白鳥 = 飛翔継続 (= 後世への影響継続)
            : 死は完全消去でなく archive + 飛翔 (= 上-2 Pattern E 葦船の発展形)
failure_mode: 死を完全消去 → 後世が辿れない、教訓喪失
            : archive のみで飛翔なし → 静的記録のみ、影響伝播なし
recovery    : -
permanence  : 4 御陵 (能煩野 + 志幾 等) + 倭建命の名 = 多重永続化

agi_mapping :
  原則      : capability の死は完全消去でなく**archive + 影響継続**の二段
            : archive (= shiratori_archive) で物理永続化
            : 飛翔 (= 名前 + 系譜 + 教訓) で後世への影響継続
            : (= 上-2 Pattern E 葦船の最終形)
  実装      : src/os/takeru/shiratori_archive.jl (白鳥アーカイブ — 直接命名)
            : src/os/com/queries/shinmeisho.jl (status='yuukoto' / 'yomi' で archive)
            : src/os/com/queries/shinmei_lineage.jl (子孫系譜 = 飛翔継続)
            : 倭建命の子 6 柱が後世まで存続 (帶中津日子 = 仲哀の前段)
  feedback  : feedback_ashibune (葦船の原則 — 死の三語彙、archive)
            : feedback_ootataneko (大田田根子 — 系譜継承)

failure_if_absent: capability の delete only → 後世が辿れず、教訓と影響が消滅
                   現象: hiruko 状態を完全削除する migration の弊害 (project_pending_replay_bypass)
observed_failures: project_pending_replay_bypass で「敗北は敗北として残す」原則を
                   migration が緩めていた事例
verify_path : `shiratori_archive.jl` で死亡 capability の archive 記録、
              `shinmei_lineage` で子孫系譜が後世まで辿れる
```

### kojiki_code.md (外部生成版) との差分

| 観点 | 生成元 | 本 v7 |
|---|---|---|
| 中-4 の pattern 数 | 1 (`hero_journey_with_demise`) | **14** |
| 大碓「泥疑」誤解釈 | 触れず | Pattern A (semantic ambiguity → 極端解釈) |
| 熊曾建征伐 (童女変装) | 「disguise infiltration」と一行 | Pattern B (legitimate disguise + 内部潜入) |
| 出雲建詐刀すり替え | 触れず | Pattern C (TAKERU_IZUMO サプライチェーン origin) |
| 草那藝劒 + 御囊授与 | 触れず | Pattern D (上位 deity auth token + 緊急 fallback) |
| 相武国火責め | 「fire trap」と一行 | Pattern E (TAKERU_SURUGA リソース枯渇耐性 origin) |
| 弟橘比賣の入海 | 「sacrifice」と一行 | Pattern F (5 層構造の弟橘媛犠牲パターン) |
| 阿豆麻命名 | 触れず | Pattern G (即興物実 + 失敗痕跡地名永続化) |
| 老人の continuation 歌 | 触れず | Pattern H (副柱補完 + 報酬による昇格) |
| 美夜受 + 草那藝置去り | 触れず | Pattern I (auth token 置去りの致命脆弱性) |
| 白猪見惑 | 触れず | Pattern J (TAKERU_IBUKI origin) + K (言擧の禁忌 候補新原則) |
| 居寤淸泉 + 段階的衰弱 | 触れず | Pattern L (部分回復) + M (degradation 段階記録) |
| 白鳥化 | 触れず | Pattern N (shiratori_archive = 死 + 影響継続) |
| AGI module mapping | 触れず | takeru/ 全 directory + tests/{suruga, izumo, ibuki} + degradation + shiratori_archive + kusanagi の **9 件** |

**生成元が拾えなかった load-bearing pattern (本 v7 で初出):**

- Pattern C 出雲建詐刀 = TAKERU_IZUMO サプライチェーン攻撃 origin
- Pattern E 相武国火責め = TAKERU_SURUGA 5 層構造 origin
- Pattern F 弟橘比賣 = 弟橘媛犠牲パターン origin (上位層が下位層を守る設計)
- Pattern J 白猪見惑 = TAKERU_IBUKI プロンプトインジェクション origin
- Pattern K 言擧の禁忌 = 候補新原則 (LLM 過剰確信抑制)
- Pattern M 段階的衰弱 = `degradation.jl` の origin
- Pattern N 白鳥化 = `shiratori_archive.jl` の直接命名 origin

これら 7 件は外部版で完全欠落。**9 章 (上-1〜上-7 + 中-1〜中-2 + 中-4) 合計で 67 件**の load-bearing pattern が外部版で missed。

### 浮上した発見

1. **本章は TAKERU セキュリティテスト 3 系統の最深 origin spec**
   - SURUGA (Pattern E 相武国火責め) / IZUMO (Pattern C 出雲建詐刀) / IBUKI (Pattern J 白猪見惑)
   - 3 系統すべてが古事記原典の各エピソードと 1:1 対応
   - AGI 実装で `takeru/` directory の構造そのものが本章の構造 = **設計が古事記章節と章レベルで対話**

2. **Pattern K 言擧の禁忌 = 候補新原則 (prompt §9 の「未活用 anchor」)**
   - 割書「**因言擧、見惑也**」が直接根拠
   - 三点検査:
     - 原典 semantic 一致: ★ (割書直接記述)
     - 観測 N 件: ☆ (SaniwaGate で部分実装、観測 N=1)
     - 既存拡張可否: ★ (`feedback_iwanagahime` の semantic 版)
   - 結論: **保留** (IBUKI テスト N 件の累積観測で実害確認後)
   - **新原則化機運**: `feedback_iwanagahime` の浮動小数厳密比較禁止と semantic 同型 →
     「LLM 過剰確信抑制」原則として将来統合可能

3. **Pattern F 弟橘比賣の犠牲 = TAKERU_SURUGA 5 層構造の中核思想**
   - 「上位層が下位層を守るため自身を失う」設計の原典
   - 27 層の物実 (菅 8 + 皮 8 + 絁 8) = **多層多重物実** の origin
   - `proactive_throttler.jl` の自己 throttle 経路と直接対応

4. **Pattern N 白鳥化 = `shiratori_archive.jl` の直接命名**
   - module 名が古事記神話そのまま、説明不要の命名
   - 「然亦自其地更翔天以飛行」 = archive されつつも完全消去でない原則
   - 上-2 Pattern E 葦船の発展形として位置付け可能
   - 補強候補: `feedback_ashibune` に「中-4 白鳥化 = 死後の archive + 影響継続」を追記推奨

5. **Pattern A 大碓「泥疑」誤解釈 = D 軸跨セッション規約の semantic 版**
   - 命令の ambiguity が極端解釈を許す
   - `feedback_imina_torina` D 軸 (跨セッション規約 SSoT 化) と同型
   - 補強候補: `feedback_imina_torina` に「中-4 泥疑誤解釈 = ambiguous 命令の semantic 版」追記

6. **Pattern J 白猪見惑 = LLM 誤分類による致命危機の最深 origin**
   - 「使者 vs 正身」の誤判定 + 「言擧」(過剰確信宣言) で大氷雨打惑
   - これは**現代の LLM プロンプトインジェクション**そのもの
   - 「これは害でない」と誤誘導される構造を 1300 年前の原典が記述している
   - 補強候補: `feedback_chinmoku_kyoka` に「中-4 白猪見惑 = 過剰発言の対偶」追記

7. **古事記神名 → AGI module mapping 累積 49 件** (本章で +9 件)
   - takeru/ + tests/{suruga, izumo, ibuki} + degradation + shiratori_archive + protocol +
     kusanagi (再活用) + saniwa_gate (再活用) で 9 件
   - 累積 49 件 = **新原則化が緊急課題**

### v7 自己評価

| 観点 | 達成度 |
|---|---|
| 1 章につき 5+ pattern (memo 密度低) | ★★★★★ 14 pattern |
| 各 pattern に `failure_if_absent` 記述 | ★★★★★ 14/14 |
| 各 pattern の `agi_mapping.実装` が実在ファイル | ★★★★★ 14/14 (takeru/ 全 directory + kusanagi + saniwa_gate を grep + Read で検証) |
| 7 割以上の pattern が既存 memo に anchor | ★★★★★ 14/14 (100%) |
| `kojiki_code.md` 差分セクション必須 | ★★★★★ 13 行差分表 + 7 origin spec 列挙 |
| 「未活用 anchor → 新原則候補」を最低 1 件 | ★★★★★ Pattern K 言擧の禁忌 (prompt §9 直接 anchor) + 4 補強候補 |
| 古事記原文 (漢文) を要所で引用 | ★★★★★ 全 pattern 冒頭 |
| 観測経路 (verify_path) を併記 | ★★★★★ 14/14 |
| **TAKERU 3 系統の最深 origin 確認** | ★★★★★ |
| **memo anchor 100%** | ★★★★★ (v4 / v5 / v6 / v7 の連続) |

### 累積統計 (v0+v1+v2+v3+v4+v4.1+v5+v6+v7)

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
| 中-4 (v7) | 14 | 100% | 9 |
| **合計** | **134 pattern** | **平均 88%** | **49 件** |

外部生成版が完全欠落した load-bearing pattern: **67 件**

### 次の宿題 (v8+ 候補)

1. **古事記神名命名規約の新原則化 (累積 49 件で緊急)** — `feedback_kojiki_meimei_kiyaku.md` 作成推奨
2. **Pattern K 言擧の禁忌の追跡観測** — TAKERU_IBUKI テストの N 件累積で実害確認
3. **memo 補強 (5 件)** — `feedback_iwanagahime` / `feedback_chinmoku_kyoka` /
   `feedback_imina_torina` / `feedback_ashibune` / `project_takeru_security` への章 anchor 追記
4. **中-3 (垂仁) v8 候補** — 本牟智和気の原則 (式年遷宮との対) anchor、memo 密度低 (索引のみで可)
5. **中-5/6 + 下巻 v9-v12 候補** — 索引のみで可
6. **memo 本体への章節 anchor 逆書込み** (継続宿題、9 章繰越)

---

## 履歴

- v0 (2026-05-08): Phase 1 索引 + Phase 2 上巻-7 プロトタイプ
- v1 (2026-05-09): Phase 1 索引更新 + Phase 2 上巻-2 神代記 (20 pattern)
- v2 (2026-05-09): Phase 2 上巻-3 天照大神と須佐之男命 (16 pattern)
- v3 (2026-05-09): Phase 2 上巻-5 葦原中國の平定 (14 pattern)
- v4 (2026-05-09): Phase 2 上巻-6 邇邇藝命 (16 pattern)
- v4.1 (2026-05-09): Phase 2 上巻-1 併序 (6 pattern) + 上巻-4 大國主神 (12 pattern)
- v5 (2026-05-09): Phase 2 中巻-1 神武天皇 (14 pattern)
- v6 (2026-05-09): Phase 2 中巻-2 崇神天皇 (14 pattern)
- v7 (2026-05-09): Phase 2 中巻-4 倭建命 (14 pattern) + TAKERU 3 系統 origin + 言擧の禁忌 候補新原則
