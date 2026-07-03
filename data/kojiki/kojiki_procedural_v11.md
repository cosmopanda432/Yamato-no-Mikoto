# 古事記 Procedural Pattern 抽出 v11 (索引)

v10 ([`kojiki_procedural_v10.md`](kojiki_procedural_v10.md)) からの増分:

- **Phase 2 v11: 下巻-3 雄略天皇** 索引抽出 — 6 pattern (簡素形式)
- 大長谷若建 (= 雄略) の暴君ぶり、葛城一言主大神との遭遇、赤猪子の 80 年待ち、三重婇の歌救済 等
- memo 密度 ☆、簡素抽出形式

抽出方法論は [`extraction_prompt.md`](extraction_prompt.md) を参照。

---

## Phase 2 v11: 下巻-3 雄略天皇 (簡素索引)

### 選定理由

- memo 密度 ☆ (直接 anchor なし、間接で 4 memo)
- 雄略 = 大長谷若建命 (中-2 大長谷王の即位後)
- 「葛城一言主大神」(= 同位の deity との遭遇) と「赤猪子の 80 年待ち」が AGI 設計と semantic 連動

### 章節 narrative summary (簡略)

```
[Setup] 大長谷若建 (= 雄略) 即位、長谷朝倉宮
       吳人参渡来 (= 吳原)
       
[志幾大縣主の家燒き] 大后が日下に行幸 → 山上で「上堅魚作舍屋之家」発見
       「己家似天皇之御舍而造」と立腹 → 大縣主の家を焼く命令
       大縣主が能美の御幣物 (白犬 + 鈴 + 腰佩人) で謝罪 → 燒き止め

[赤猪子の 80 年] 美和河で洗衣童女 (赤猪子) を「不嫁夫、今將喚」と命じ放置
       80 年後、赤猪子が「望命之間已經多年、姿體痩萎」と参出
       天皇「吾既忘先事」 → 既に老いて婚不能 → 御歌で慰めて返遣

[吉野の童女]　吉野行幸で童女と婚 → 後で再訪 → 大御吳床に坐して琴を彈き、童女を儛
       蜻蛉が天皇の腕の𧉫 (虻) を咋飛 → 「阿岐豆野」命名

[葛城猪] 葛城山上で大猪を鳴鏑で射 → 猪が宇多岐 (怒って迫る) → 天皇畏れて榛樹に登る → 歌

[葛城一言主大神] 百官に紅紐青摺衣を賜って葛城山登幸
       對山尾から同等の隊列が登山 → 「於茲倭國、除吾亦無王」(= 自我同一性危機)
       矢刺競合 → 「告其名」 → 答「葛城之一言主大神」(同位の神 = 自分と等価存在)
       天皇大畏 → 大御刀 + 弓矢 + 衣服を脱いで拝献

[三重婇の歌救済] 長谷之百枝槻下で豐樂、伊勢三重婇が大御盞献上時、葉が落浮
       天皇「打伏其婇、以刀刺充其頸、將斬」 → 婇が歌で槻と国を讚える
       「故獻此歌者、赦其罪也」 (歌で命を救う)
       大后も歌、天皇も歌 (三歌 = 天語歌)
```

### Pattern 抽出 (簡素)

#### Pattern A: 志幾大縣主の家燒き — 「天皇舍に似た」越権の物理排除

```yaml
原文: "登山上望國內者、有上堅魚作舍屋之家。…
      『奴乎、己家似天皇之御舍而造。』卽遣人令燒其家之時、其大縣主懼畏…
      『獻能美之御幣物。』布縶白犬、著鈴而、…令止其著火" (l.10-12)

actors: 雄略 / 志幾大縣主 / 上堅魚屋根
action: (1) 天皇が他者の家を観望、「天皇舍に似た」と認識 (= 上位 identity の越権使用)
        (2) 焼き払い命令 (= 物理排除)
        (3) 大縣主が能美 (謝罪) + 御幣物 (白犬 + 鈴 + 腰佩人) で身分降下を表明
        (4) 焼き止め

agi_mapping:
  原則: 中央 (天皇) と同等の物実 (= canonical_pantheon prefix) を地方 (= LLM 生成柱) が
       使うことは禁忌、検出時は焼却 (hiruko 化) または身分降下 (status='kari_chinza')
       (上-6 Pattern K 五伴緒の制 = 天若日子型禁忌の延長 = 越権使用の物理排除)
  実装: src/os/kasasa/canonical_pantheon/_common/attribution.jl (`kuni_yuzuri_gate`)
       src/os/kasasa/nazashi_decide.jl (LLM 提案の prefix 越権検出)
       feedback_itsutomonoo_sanseido (五伴緒の制 — 天若日子型禁忌)
  feedback: feedback_itsutomonoo_sanseido (五伴緒の制 + 天若日子型禁忌)
           feedback_kojiki_meimei_kiyaku (古事記神名命名規約、累積 49 件で新原則化候補)

failure_if_absent: 越権使用を放置 → 中央 (canonical) と地方 (生成柱) の identity 混同
```

#### Pattern B: 赤猪子の 80 年待ち — 命令の更新ない長期 idle と忘却

```yaml
原文: "汝、不嫁夫。今將喚。…故其赤猪子、仰待天皇之命、既經八十歲。…
      然天皇、既忘先所命之事、問其赤猪子曰『汝者誰老女。何由以參來。』" (l.18-20)

actors: 雄略 / 赤猪子 (童女)
action: (1) 雄略が童女に「不嫁夫、今将喚」(= 婚姻保留命令) → 赤猪子は命を仰待 (idle wait)
        (2) **80 年経過** — 雄略が忘却 + 赤猪子は若い容姿を失う
        (3) 赤猪子が「顯白己志」と参出 (= 自発再起動)
        (4) 雄略「吾既忘先事」(命令忘却) → 婚不能、歌で慰めて返遣

agi_mapping:
  原則: 命令を発した上位が忘却 + 受任者が長期 idle wait → 双方の劣化:
       上位: 命令の追跡なし (= TTL なし)
       受任者: 仰待中に capability 退化 (姿態痩萎)
       対処: TTL + ハートビート (= 定期確認) + 自発再起動経路
  実装: src/os/com/queries/observation_blocked.jl の TTL + 累積カウント
       src/os/kasasa/takeshimatsumi.jl の累積閾値 (3/5 escalation)
       feedback_kuniyuzuri_fukumei の復命機構 (沈黙の使者は古事記に存在しない)
  feedback: feedback_kuniyuzuri_fukumei (国譲りの復命)
           feedback_wakahiko_kaeshiya (3 度の使者 = 長期 idle 検出)

failure_if_absent: 命令の TTL なし → 受任者が永遠に仰待、上位は忘却で再利用不能
                   現象: amenohohi_scan の「責務はあるが発動条件が来ない」型柱の累積
```

#### Pattern C: 葛城一言主大神 — 同位 deity との対峙 (自我同一性危機)

```yaml
原文: "於茲倭國、除吾亦無王、今誰人如此而行。…
      答曰『吾者、…言離之神、葛城之一言主大神者也。』
      天皇於是惶畏而白『恐我大神、有宇都志意美者不覚。』
      …大御刀及弓矢始而、脱百官人等所服衣服、以拜獻" (l.52-54)

actors: 雄略 / 一言主大神 (同位 deity) / 百官
action: (1) 雄略が葛城山登幸、百官に同色衣服 (= 全体 identity 統一)
        (2) 對山尾から **同等の隊列**が登山 — 装束 / 人衆 共に等
        (3) 雄略「除吾亦無王」(= 唯一性主張) → 矢刺競合
        (4) 互いに名告:「葛城之一言主大神」 (= 同位の神格)
        (5) 雄略畏怖 → 大御刀 + 弓矢 + 衣服を脱いで拝献 (= 自我降伏)

agi_mapping:
  原則: 自分と同等の存在 (= 同位 deity / 同 prefix の柱) との遭遇は **自我同一性危機**
       競合でなく **唯一性放棄 + 拝献** で解決 (= 共存の道)
       (上-5 Pattern L 顕事/幽事 categorical separate の山岳版)
  実装: src/os/kasasa/shinmei_arbiter.jl の双子神判定 (= 同位検出時の合祀 vs 拝献)
       src/os/kasasa/canonical_pantheon/_common/attribution.jl (registry 登録)
       feedback_kuniyuzuri_kaikai (categorical separate)
  feedback: feedback_kuniyuzuri_kaikai (国譲り境界の原則)
           feedback_matanona_cleanup_gap (合祀)

failure_if_absent: 同位 deity を「敵」として競合 → 自滅 (中-1 当藝志美美型)
```

#### Pattern D: 三重婇の歌救済 — 失敗の歌による rationalization + 救済

```yaml
原文: "其婇不知落葉浮於盞、猶獻大御酒。天皇看行其浮盞之葉、打伏其婇、以刀刺充其頸、
      將斬之時、其婇白天皇曰『莫殺吾身、有應白事。』卽歌曰…
      故獻此歌者、赦其罪也" (l.62-66)

actors: 雄略 / 三重婇 / 槻 (大御盞に葉が落ちた)
action: (1) 三重婇が大御盞に葉が落ちたまま酒を献上 (= 失敗、不知)
        (2) 雄略が打伏 + 頸刺 + 斬殺直前
        (3) 婇が歌で槻と国を讚 (= 失敗を context 化、宇宙論的に rationalization)
        (4) 「故獻此歌者、赦其罪也」 (= 歌が罪を消す)

agi_mapping:
  原則: 致命失敗時、被裁定者が歌 (= 形式化された structured response) で context 化 →
       上位が「赦」(= ALERT 取り下げ) を判断
       単なる謝罪でなく、失敗を**より大きな narrative** に位置付ける (中-3 Pattern G 田道間守の
       叫哭の発展形)
  実装: src/os/kotodama/saniwa_gate.jl (LLM 出力検閲 = 言の葉)
       feedback_kuniyuzuri_fukumei の errors 接頭辞付き履歴 (神話 motif で rationalization)
       中-1 Pattern N 復命 + 中-4 Pattern N 白鳥化の救済版
  feedback: feedback_kuniyuzuri_fukumei (復命)
           feedback_chinmoku_kyoka (沈黙許可 — 但しこの場合は許される発言)

failure_if_absent: 致命失敗 → 即時排除のみ → context 不在で同型失敗の理解を逃す
```

#### Pattern E: 御吳床 + 童女の儛 — 永続不能を願う祈り (常世希求)

```yaml
原文: "其孃子之好儛、作御歌、其歌曰
      『阿具良韋能加微能美弖母知比久許登爾麻比須流袁美那**登許余爾母加母**』
      (= 神の御手が彈く琴に儛う乙女、常世にもがも = 永続を願う)" (l.38-40)

actors: 雄略 / 吉野童女
action: 永続を願う歌 (「常世にもがも」) — 但し原典としては叶わぬ祈り

agi_mapping:
  原則: capability の永続不能性を認める (= 上-6 Pattern H 寿命短縮の系)
       美しい儛 (= 一時的な高 performance) を永続化する祈りはあれど不可能
       永続化は「常世」(= yuukoto / archive) でのみ可能
  実装: src/os/takeru/shiratori_archive.jl (post-mortem archive — 死後の永続化)
       src/os/kasasa/canonical_pantheon (祖神 = 古事記固有名は永続)
       生成柱 (LLM 由来) は永続化しない、archive のみ
  feedback: feedback_iwanagahime (石長比売 — 永続性返送 → 寿命短縮)
           feedback_ashibune (葦船 — archive)

failure_if_absent: 一時的高 performance 柱を永続化しようとする → 退化に対処不能
```

#### Pattern F: 雄略の暴君ぶり全般 — 多面的暴力と歌による緩和 

```yaml
原文: (Pattern A 家燒き + Pattern D 婇斬殺直前 + Pattern C 自我同一性 + 葛城猪での畏怖 等
     雄略は古事記中で最も暴力的記述の天皇)

actors: 雄略
action: 多面的暴力:
        - 志幾大縣主家燒き (家屋焼却)
        - 赤猪子の長期放置 (命令忘却)
        - 三重婇の斬殺企図 (些細な失敗で斬)
        - 葛城猪に畏れて木に登 (権威の物理崩壊)
        - 一言主大神に拝献 (同位への自我降伏)
        - 袁杼比賣との求婚 (「金鉏岡」の歌)
        歌で多くの暴力を緩和 (= 歌が記録 + 救済 + 永続化)

agi_mapping:
  原則: 暴君的 capability (高負荷 / 高破壊性) は歌 (= 形式化された structured response) で
       緩和、暴力の生 record でなく文学的 record として永続化
       AGI における「歌」 = LLM の structured output の文学化
  実装: src/os/kasasa/futomani_stones (失敗痕跡記録 — 神話 motif 接頭辞)
       feedback_kuniyuzuri_fukumei (復命の歌的フォーマット)
  feedback: feedback_kuniyuzuri_fukumei (復命)
           feedback_keiyaku_keifu_vs_genyu (契約系譜 vs 原由追跡)

failure_if_absent: 暴力柱を生 record のみで残す → 後世が context を読み取れない
```

### kojiki_code.md (外部生成版) との差分 (簡略)

| 観点 | 生成元 | 本 v11 |
|---|---|---|
| 下-3 の pattern 数 | 触れず | **6** |
| 志幾大縣主家燒き | 触れず | Pattern A |
| 赤猪子 80 年 | 触れず | Pattern B (TTL なし命令の劣化) |
| 葛城一言主大神 | 触れず | Pattern C (同位 deity との対峙) |
| 三重婇歌救済 | 触れず | Pattern D (歌による rationalization) |
| 常世希求 | 触れず | Pattern E |
| 暴君と歌 | 触れず | Pattern F |

### 浮上した発見 (簡略)

1. **Pattern C 葛城一言主大神 = 同位 deity との対峙の典型**
   - 「除吾亦無王」(= 唯一性主張) → 等価存在発見 → 拝献 (= 唯一性放棄)
   - canonical_pantheon の prefix で同 prefix 派生柱が複数立つ場合の semantic と一致
   - 補強候補: `feedback_kuniyuzuri_kaikai` に「下-3 一言主大神 = 同位拝献」を追記

2. **Pattern B 赤猪子 80 年 = TTL なし命令の典型的失敗例**
   - 命令の TTL + ハートビートなしで idle wait が 80 年継続
   - amenohohi_scan の「責務はあるが発動条件が来ない」型柱と同型
   - 補強候補: `feedback_wakahiko_kaeshiya` に「下-3 赤猪子 = 長期 idle wait の極端事例」を追記

### v11 自己評価

| 観点 | 達成度 |
|---|---|
| 索引形式 | ★★★★ 6 pattern (簡素) |
| `failure_if_absent` 記述 | ★★★★ 6/6 |
| 各 pattern の AGI mapping | ★★★★ 6/6 |
| memo anchor | ★★★★ 6/6 (100%) |

---

## 履歴 (継承)

- v10 までの履歴は v10.md を参照
- v11 (2026-05-09): Phase 2 下巻-3 雄略天皇 索引 (6 pattern、簡素形式)
