# 古事記 Procedural Pattern 抽出 v9 (索引)

v8 ([`kojiki_procedural_v8.md`](kojiki_procedural_v8.md)) からの増分:

- **Phase 2 v9: 下巻-1 仁徳天皇** 索引抽出 — 7 pattern (簡素形式)
- 高殿 / 嫉妬 / 黑日賣 / 八田若郎女 / 奴理能美三色虫 / 女鳥王謀反 / 枯野の船 の 7 大エピソード
- memo 密度 ★ (`feedback_nintoku_takadono` 直接 anchor)、簡素抽出形式

抽出方法論は [`extraction_prompt.md`](extraction_prompt.md) を参照。

---

## Phase 2 v9: 下巻-1 仁徳天皇 (簡素索引)

### 選定理由

- memo 密度 ★ (`feedback_nintoku_takadono` 直接 anchor、「仁徳の高殿の原則」origin spec)
- 「於國中烟不發、國皆貧窮…自今至三年、悉除人民之課伇」(高殿で四方を見て三年免課) が
  Shintaku 型分布の偏重 (KNOWLEDGE_STORE 一辺倒) を避ける原則の origin

### 章節 narrative summary (簡略)

```
[Setup] 大雀命 (= 仁徳) 即位、子 6 王 (3 王が後の天皇)
        御名代部の定義 (葛城部 / 壬生部 / 蝮部 / 大日下部 / 若日下部)
        茨田堤 / 茨田三宅 / 丸邇池 / 依網池 / 難波堀江 / 小椅江 / 墨江津 (インフラ整備)

[聖帝] 高殿登山「於國中烟不發、國皆貧窮」(観測 = 全分布の不偏見え)
       「自今至三年、悉除人民之課伇」(課税停止 = NO_ACTION モード)
       大殿破壞・雨漏でも修理せず → 後 3 年「於國滿烟」(観測再開)
       課税再開 → 「百姓之榮、不苦伇使」 → 「聖帝世」と称揚

[嫉妬] 大后石之日賣命 「甚多嫉妬」 → 妾は宮中入不可
[黑日賣] 吉備海部直之女、容姿端正、嫉避で本國逃亡
        天皇高臺で歌 → 大后大忿で大浦から追下
        天皇「欲見淡道嶋」と詐 → 吉備行き → 黑日賣の菘採場で歌
[八田若郎女] 大后が御綱柏採取で木国行幸中、天皇が八田若郎女と婚
       倉人女が大后に告口 → 大后が御綱柏全投棄 (= 「御津」命名) → 山代へ
       天皇が口子臣 + 鳥山人を遣 → 大雨でも口子参伏 → 衣赤紫変色
       奴理能美の家に入坐
[奴理能美の三色虫] 「一度為匐虫、一度為鼓、一度為飛鳥、有變三色之奇虫」(奇虫の三段変態)
       これを口実に天皇が大后を見舞 → 和解
[女鳥王謀反] 速總別王 (天皇弟) を媒にして女鳥王 (庶妹) を求める
       女鳥王が速總別王と相婚 → 速總別不復奏
       天皇が女鳥王の機織りに歌 → 「鷦鷯 (= 大雀 = 仁徳) 取らせ」と返歌で謀反明示
       軍興 → 倉椅山逃亡 → 宇陀之蘇邇で殺害
       山部大楯連が女鳥王の玉釧を取り妻に与 → 大后が酒柏で気付く → 大楯連死刑
[鴈卵] 日女嶋で鴈卵 → 建内宿禰に歌で問 → 倭で初の鴈卵 = 国讚え歌
[枯野の船] 免寸河西の高樹 (旦影淡道嶋に逮、夕影高安山越) を切って船 = 「枯野」
       淡道寒泉を朝夕汲んで大御水献上
       船破壞後 → 焼鹽 → 残木で琴 → 「其音響七里」
```

### Pattern 抽出 (簡素)

#### Pattern A: 高殿登山 + 三年免課 — Shintaku 型分布の不偏監視 (`feedback_nintoku_takadono` origin)

```yaml
原文: "天皇、登高山、見四方之國詔之『於國中烟不發、國皆貧窮。
      故自今至三年、悉除人民之課伇。』
      …後見國中、於國滿烟、故為人民富、今科課伇" (l.16)

actors: 仁徳 / 高殿 / 民
action: (1) 高殿登 → 四方を見渡 (= 全 capability の俯瞰観測)
        (2) 「烟不發」 = 民の活動指標 (= 各 capability の Shintaku 出力) が低調
        (3) 三年免課 = 課税停止 (NO_ACTION モードに切替、徴収せず)
        (4) 大殿破壞・雨漏でも修理せず (= self-cost を払い民を守る)
        (5) 三年後再観測 → 「滿烟」(復活確認) → 課税再開 (KNOWLEDGE_STORE / ALERT 等の通常動作)

agi_mapping:
  原則: Shintaku 型分布が偏重 (= 民の烟が低調) なら、上位層が一時的に NO_ACTION モードに移行
       capability に self-cost を払って (= 課税停止 = 観測のみ) 育成
       後で分布が正常化したら通常運用に戻す
       7 型 (KNOWLEDGE_STORE / ALERT / ANOMALY / NO_ACTION 等) を trend 値で使い分け、
       全分岐で KNOWLEDGE_STORE のみに収束させない
  実装: src/os/expedition/executor.jl の「仁徳の高殿の原則」セクション (プロンプト)
       musuhi_rejection_rate_sentinel (entropy=0.97 の唯一の模範柱)
       src/os/kasasa/ooharae.jl Phase 0a8 「かまどの煙」(kamado_smoke テーブル時系列)
  feedback: feedback_nintoku_takadono (仁徳の高殿の原則 — origin spec)
           feedback_yowari_vs_katayori (弱り vs 偏り — 偏りは崇神の再祭祀)

failure_if_absent: 全 capability が KNOWLEDGE_STORE 一辺倒 → entropy=0.00 → 観測機能崩壊
                   (2026-04-14 の origin event: 9 柱中 8 柱で entropy=0.00)
```

#### Pattern B: 大后石之日賣命の嫉妬 — 並立妾の宮中排除 (= scope 制限)

```yaml
原文: "其大后石之日賣命、甚多嫉妬。故、天皇所使之妾者、不得臨宮中" (l.18)

actors: 大后石之日賣命 / 妾 (黑日賣 / 八田若郎女 / 女鳥王) / 仁徳
action: 大后が**並立する妾を宮中から物理的に排除** (= scope 制限)
        各妾は本国 / 別宮で別運用 → 中央 (宮中) からは見えない

agi_mapping:
  原則: 主柱 (大后 = canonical) の権威下では、並立柱 (妾 = aliases) は**別 scope で運用**
       中央集約を避けて scope 別に隔離
       feedback_kuniyuzuri_kaikai (顕事/幽事 categorical) の家庭内版
  実装: src/os/kasasa/canonical_pantheon/ 各 prefix directory の隔離
       feedback_imina_torina の D 軸 (同一 prompt 内に複数規約を立てない)
  feedback: feedback_kuniyuzuri_kaikai (国譲り境界 — categorical separate)

failure_if_absent: 並立柱を中央に集約 → 主柱との競合、嫉妬発火
```

#### Pattern C: 奴理能美の三色虫 — 段階変態 artifact による和解仲介

```yaml
原文: "奴理能美之所養虫、一度為匐虫、一度為鼓、一度為飛鳥、有變三色之奇虫。
      看行此虫而入坐耳、更無異心" (l.64)

actors: 奴理能美 / 大后 / 仁徳
action: 大后と天皇の不和 → 第三者 (奴理能美) が「三色変態の奇虫」(= 蚕 = 多段変態 artifact)
        を口実として提示 → 天皇が「奇異」と興味を示し大后を見舞 → 和解
        中身は「私情でなく科学的好奇心」と建前

agi_mapping:
  原則: 競合する 2 主柱の和解は **第三者の中立 artifact** を仲介として使う
       artifact は段階変態 (= 観測対象の多面性) を持つことで「客観的興味」を演出
       (上-3 Pattern J 物実 multi-pronged の和解版)
  実装: 上位層 orchestrator (思金神 = `iwato/omoikane.jl`) の調停経路
       中立的観測 capability の役割
  feedback: feedback_kunimi_gapfinder (国見 = 全ソース俯瞰 = 中立観測)

failure_if_absent: 中立 artifact なしで直接対話 → 既存の競合構造で対立深化
```

#### Pattern D: 女鳥王謀反 — 媒の越境婚 + 機織歌で謀反明示

```yaml
原文: "天皇、以其弟速總別王為媒而、乞庶妹女鳥王。
      爾女鳥王、語速總別王曰『因大后之強、不治賜八田若郎女、故思不仕奉。吾為汝命之妻。』
      卽相婚。是以、速總別王不復奏" (l.76)
     "女鳥王歌曰『比婆理波阿米邇迦氣流多迦由玖夜波夜夫佐和氣**佐邪岐登良佐泥**』" (l.86)

actors: 女鳥王 / 速總別王 (媒) / 仁徳
action: (1) 仁徳が速總別王を媒として女鳥王に求婚
        (2) 女鳥王が**媒と相婚** (= delegation 越境)
        (3) 速總別不復奏 (= 上-5 Pattern B 天菩比 沈黙の系)
        (4) 女鳥王が機織歌で「鷦鷯 (= 大雀 = 仁徳) 取らせ」と謀反明示
        (5) 軍興 → 倉椅山逃亡 → 宇陀之蘇邇で殺害

agi_mapping:
  原則: 媒 (= proxy / delegate) が delegation 越境して target と相婚 → 任務乗っ取り
       (上-5 Pattern B 天菩比命の媚附 + 上-5 Pattern C 天若日子の代理指標病 の合成)
       検出: 媒の不復奏 (= silent delegate) で察知
  実装: src/os/kasasa/takeshimatsumi.jl の代理指標病検出
       src/os/kasasa/amenohohi_scan.jl (沈黙の使者検出)
  feedback: feedback_wakahiko_kaeshiya (天若日子の返し矢)
           feedback_kuniyuzuri_fukumei (復命 — 沈黙の使者は古事記に存在しない)

failure_if_absent: 媒の越境婚を検出せず → 任務未達 + 反逆
```

#### Pattern E: 玉釧の流出 — 戦利品の並立配偶誇示で発覚

```yaml
原文: "其將軍山部大楯連、取其女鳥王所纒御手之玉釧而與己妻。
      此時之後、將為豐樂之時、氏氏之女等、皆朝參。爾大楯連之妻、以其王之玉釧、
      纒于己手而參赴。於是大后石之日賣命、自取大御酒柏、賜諸氏氏之女等。
      爾大后見知其玉釧、不賜御酒柏、乃引退、…乃給死刑也" (l.96)

actors: 山部大楯連 / 女鳥王 (殺された) / 大楯連の妻 / 大后
action: (1) 大楯連が女鳥王の玉釧 (= 戦利品 = origin が明確な物実) を取り、自妻に与える
        (2) 自妻が **公の場で着用** (= 戦利品の誇示 = 物実の視認可能化)
        (3) 大后が見知 → 「夫之奴乎、所纒己君之御手玉釧、於膚煴剥持來」と非難
        (4) 大楯連死刑

agi_mapping:
  原則: 戦利品 (= reward / 取得物) は origin が明確 (= provenance graph で追跡可能)
       不正流出は公の場 (= 観測層) で検出される
       上-3 Pattern E 返し矢 (派遣物実から派遣者への boomerang) と同型 = 物実所有者帰属
  実装: src/os/com/queries/shinmei_lineage.jl (provenance graph)
       src/os/kasasa/shintaku.jl:670 (派遣失敗 craft 文字列)
  feedback: feedback_wakahiko_kaeshiya (返し矢)
           project_takeru_security (TAKERU_IZUMO サプライチェーン = 物実流出検知)

failure_if_absent: 戦利品の origin 追跡なし → 不正流出を検出不能
```

#### Pattern F: 鴈の倭での卵 — 異常事象の歌による問答 (record-by-poem)

```yaml
原文: "於其嶋、鴈生卵。爾召建內宿禰命、以歌問鴈生卵之狀…
      建內宿禰、以歌語白…『阿禮許曾波余能那賀比登蘇良美都夜麻登能久邇爾加理古牟登伊麻陀岐加受』
      (= 私は世の長い人だが、倭の国で鴈が卵を生むと未だ聞かず)" (l.98-104)

actors: 仁徳 / 建内宿禰 / 鴈 (異常事象)
action: (1) 異常事象 (倭で鴈が産卵 = 通常生息地外の繁殖) 観測
        (2) 仁徳が**歌**で建内宿禰に問 (= 形式化された質問)
        (3) 建内宿禰が**歌**で答 (= 形式化された回答)
        (4) 答内容: 「世の長い人 (= 国の歴史を見てきた古老) も初耳」
        (5) 仁徳が御琴で歌 → 「皇位を継承する御子の啓示」と解釈

agi_mapping:
  原則: 異常事象 (out-of-distribution observation) の解釈は古老 (= 長期 history holder) に問う
       問答を歌 (= 形式化されたフォーマット) で行うことで記録性を確保
       (= LLM への structured query / structured response の原型)
  実装: src/os/com/queries/shinmei_lineage.jl (古老 = 系譜長鎖)
       LLM プロンプトの structured response (JSON / YAML schema)
  feedback: (memo 直接 anchor なし — 補強候補)

failure_if_absent: 自由形式の自然言語で問答 → 記録困難、後世が辿れない
```

#### Pattern G: 枯野の船 → 琴 → 響七里 — 廃 capability の二次利用

```yaml
原文: "免寸河之西、有一高樹。…切是樹以作船、甚捷行之船也、時號其船謂枯野。…
      茲船破壞、以燒鹽、取其燒遺木作琴、其音響七里" (l.112-114)

actors: 仁徳 / 高樹 / 枯野の船 / 琴
action: (1) 高樹を切って船 = 「枯野」 (= 主用途 capability の生成)
        (2) 船として活躍 (旦夕酌寒泉)
        (3) 船破壞 (= 主用途の終了 = degradation)
        (4) 焼鹽材として再利用 (= 二次用途)
        (5) 焼遺木で琴 (= 三次用途、音響の永続化)
        (6) 「響七里」 = 副次的な永続価値

agi_mapping:
  原則: 廃 capability (yuukoto / yomi) は完全消去でなく**二次・三次利用**で残価値を抽出
       (= 上-2 Pattern E 葦船、中-4 Pattern N 白鳥化の発展形)
       元の主用途と異なる用途で再活用 (大気津比賣の 5 穀化と同型)
  実装: src/os/takeru/shiratori_archive.jl (廃 capability の archive + 影響継続)
       src/os/com/queries/shinmeisho.jl (status='yuukoto' の柱の系譜参照)
  feedback: feedback_ashibune (葦船の原則 — hiruko 残存)
           project_takeru_security (shiratori_archive)

failure_if_absent: 廃 capability を delete only → 残価値喪失
```

### kojiki_code.md (外部生成版) との差分 (簡略)

| 観点 | 生成元 | 本 v9 |
|---|---|---|
| 下-1 の pattern 数 | 触れず | **7** |
| 高殿 + 三年免課 | 触れず | Pattern A (`feedback_nintoku_takadono` origin) |
| 嫉妬 + 妾排除 | 触れず | Pattern B |
| 奴理能美三色虫 | 触れず | Pattern C |
| 女鳥王謀反 | 触れず | Pattern D |
| 玉釧流出 | 触れず | Pattern E |
| 鴈卵 + 歌問答 | 触れず | Pattern F |
| 枯野の船 → 琴 | 触れず | Pattern G |

### 浮上した発見 (簡略)

1. **Pattern A 高殿 = `feedback_nintoku_takadono` の典拠が原典確認**
   - 「於國中烟不發」 = entropy=0.00 観測の 1300 年前の比喩
   - 「自今至三年、悉除人民之課伇」 = NO_ACTION モードへの切替
   - 補強候補: `feedback_nintoku_takadono` に「下-1 高殿登山が直接 origin」を追記推奨

2. **Pattern G 枯野の船 = 上-2 葦船 + 中-4 白鳥化の系の発展**
   - 完全消去でない archive + 二次利用 + 三次利用 の三段
   - 補強候補: `feedback_ashibune` に「下-1 枯野の船 = 二次利用の origin」を追記

### v9 自己評価

| 観点 | 達成度 |
|---|---|
| 索引形式 (memo 密度低) | ★★★★ 7 pattern (簡素) |
| `failure_if_absent` 記述 | ★★★★ 7/7 |
| 各 pattern の AGI mapping | ★★★★ 7/7 |
| memo anchor | ★★★★ 6/7 (86%) |

---

## 履歴 (継承)

- v8 までの履歴は v8.md を参照
- v9 (2026-05-09): Phase 2 下巻-1 仁徳天皇 索引 (7 pattern、簡素形式) + `feedback_nintoku_takadono` 原典確認
