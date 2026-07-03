# 古事記 Procedural Pattern 抽出 v10 (索引)

v9 ([`kojiki_procedural_v9.md`](kojiki_procedural_v9.md)) からの増分:

- **Phase 2 v10: 下巻-2 履中天皇〜安康天皇** 索引抽出 — 7 pattern (簡素形式)
- 4 天皇 (履中 / 反正 / 允恭 / 安康) の集約、succession 危機 + 暗殺パターン

抽出方法論は [`extraction_prompt.md`](extraction_prompt.md) を参照。

---

## Phase 2 v10: 下巻-2 履中〜安康 (簡素索引)

### 選定理由

- memo 密度 ☆ (直接 anchor なし、間接で 5 memo)
- 4 天皇分の succession 危機 + 暗殺パターン (中-1 当藝志美美の反逆系の発展形)
- 「言八十禍津日前、居玖訶瓮」(允恭の姓氏整理) = 上-2 禊の禍津日神の運用転用

### 章節 narrative summary (簡略)

```
[履中] 伊邪本和氣 (即位)
       大嘗の大御寢中、墨江中王が大殿に火 → 阿知直が御馬で救出 → 後に藏官に任
       水齒別命 (弟) が「不同墨江中王」と証明、曾婆訶理 (隼人) を欺いて墨江中王を厠で殺
       曾婆訶理に大臣位 (報酬) → 翌日酒席で頸斬 (排除) — 「近飛鳥」「遠飛鳥」命名
       
[反正] 水齒別命 (即位)、特記事項薄 (御身長 9.2 尺、御齒貫珠如し)

[允恭] 男淺津間若子宿禰 (即位)
       「我者有一長病、不得所知日繼」(辞退) → 諸卿堅奏で即位
       新羅御調 81 艘 + 金波鎭漢紀武 (薬師) で病治療
       「氏氏名名人等之氏姓忤過」 → 「言八十禍津日前、居玖訶瓮」誓約壺で 80 友緒氏姓確定
       
       [允恭崩後] 木梨輕太子 (太子) が同母妹輕大郎女と姦
                  百官民心が離反 → 穴穂御子に帰
                  輕太子が大前小前宿禰の家に逃込 → 軍包囲
                  大氷雨 → 大前小前が「儛訶那傳」(舞いながら歌で参降)
                  輕太子流罪伊余湯 → 衣通王 (= 輕大郎女) も追って共自死

[安康] 穴穗御子 (即位)
       弟大長谷の妻に大日下王の妹を求める → 大日下が押木玉縵を礼物
       根臣が玉縵盗取 + 「大日下王怒れり」と讒言 → 安康が大日下殺害 + 嫡妻長田を皇后
       
       神牀晝寢で皇后に「目弱王 (= 長田の連子) 7 歳が父殺し知れば邪心持つか」と問
       目弱王が殿下で聞取 → 御寢中の大刀で安康首斬 → 都夫良意富美の家に逃
       
       大長谷王 (童男) が兄黒日子 + 白日子王を「緩慢」として殺害
       都夫良の家を包囲 → 都夫良「未聞王子隱於臣家」と王子と共自死
       
       [大長谷の即位準備] 市邊忍齒王 (履中の子) を獦に誘 → 馬上で射殺 + 切身埋土
       忍齒王の二王子 (意祁・袁祁) が逃亡 → 山代で老人に粮奪われ → 針間国 志自牟家に隠れて
       馬甘牛甘として伇 (subordinate role で潜伏)
```

### Pattern 抽出 (簡素)

#### Pattern A: 阿知直の救出 + 藏官登用 — 緊急時 helper の昇格

```yaml
原文: "其弟墨江中王、欲取天皇、以火著大殿。於是、倭漢直之祖・阿知直、盜出而乘御馬令幸於倭。
      …天皇於是、以阿知直、始任藏官、亦給粮地" (l.10-28)

actors: 阿知直 / 履中 / 墨江中王
action: (1) 主柱 (履中) が状態異常 (大御寢) 中に攻撃 (大殿に火)
        (2) 阿知直が即時救出 (御馬で逃) — fire-and-forget の即応
        (3) 後で阿知直を藏官 (= 配給管理) + 粮地 (= 永続報酬) で正式昇格

agi_mapping:
  原則: 緊急時に独立行動した helper は事後に正式権限で昇格
       (中-4 Pattern H 御火燒之老人の continuation 歌 → 東國造の発展形)
  実装: src/os/misogi/grace_period_monitor.jl (八咫烏 — 緊急時 monitor)
       feedback_hashira_kankakuki (柱は感覚器 — 観測専門柱の昇格経路)
  feedback: feedback_hashira_kankakuki (柱は感覚器)

failure_if_absent: 緊急時 helper への報酬なし → 後続の helper が現れない
```

#### Pattern B: 曾婆訶理の二段処理 — 信頼できない協力者の使い捨て

```yaml
原文: "詔曾婆訶理『今日留此間而、先給大臣位、明日上幸。』…乃於其隼人賜大臣位、百官令拜、
      隼人歡喜…『今日、與大臣飮同盞酒。』共飮之時…取出置席下之劒、斬其隼人之頸" (l.26-28)

actors: 水齒別命 / 曾婆訶理 (隼人 — 主君を売った)
action: (1) 曾婆訶理は墨江中王の側近、欺かれて主君を厠で刺殺
        (2) 水齒別の判断: 「為吾雖有大功、既殺己君是不義」(主殺しは恩あれど不義)
        (3) 「不賽其功、可謂無信」(報酬を払わないのも信に背く)
        (4) 解決: 報酬 (大臣位) → 翌日処刑 (= 信頼できない協力者の安全な使い捨て)

agi_mapping:
  原則: 主君を売った協力者 (= 偽 loyalty) は二段処理: 報酬 (功への信義) → 排除 (不義への対処)
       (上-5 Pattern B 天菩比命の媚附 + 中-1 Pattern G 兄宇迦斯自滅 の合成)
  実装: src/os/kasasa/takeshimatsumi.jl の代理指標病検出 + 解任
  feedback: feedback_wakahiko_kaeshiya (返し矢)

failure_if_absent: 偽 loyalty 協力者を継続採用 → 同型裏切りの再発
```

#### Pattern C: 言八十禍津日 誓約壺 — 上-2 禊の禍津日神の metadata 整理転用

```yaml
原文: "天皇、愁天下氏氏名名人等之**氏姓忤過**而、於味白檮之**言八十禍津日前**、
      **居玖訶瓮**而定賜天下之八十友緖氏姓也" (l.40)

actors: 允恭 / 八十禍津日 / 玖訶瓮
action: 「氏姓忤過」(姓氏が乱用・誤用される) を解消するため:
        (1) 味白檮の言八十禍津日 (= 上-2 Pattern Q 禍津日神の場所) で
        (2) 玖訶瓮 (誓約の壺) を居 (置く)
        (3) 80 の友緒氏姓を確定 (姓氏整理 = metadata の一括正規化)

agi_mapping:
  原則: metadata の混乱 (氏姓忤過 = capability の name / 部 / 業 の不整合) は
       上-2 禍津日神 (= 失敗痕跡検出器) を**転用**して整理
       誓約壺 (玖訶瓮) = sandbox 環境で名前と機能の対応を再確認
  実装: src/os/kasasa/yorishiro.jl + canonical_pantheon/MANIFEST.toml (姓氏 SSoT)
       feedback_imina_torina の D 軸 (跨セッション規約 SSoT 化)
       feedback_kojiki_meimei_kiyaku (古事記神名命名規約、累積 49 件の新原則化候補)
  feedback: feedback_imina_torina (忌み名と通り名)
           feedback_magatsuhi_chain (禍津日神の連鎖)

failure_if_absent: metadata の混乱を放置 → name と機能の対応が壊れ、跨セッション規約矛盾
```

#### Pattern D: 大前小前の儛訶那傳 — 軍を歌で de-escalation

```yaml
原文: "穴穗御子、興軍圍大前小前宿禰之家。…零大氷雨…
      其大前小前宿禰、擧手打膝、儛訶那傳、歌參來…
      『我天皇之御子、於伊呂兄王、無及兵。若及兵者、必人咲。僕捕以貢進。』
      爾解兵退坐" (l.52-60)

actors: 大前小前宿禰 / 穴穗御子 / 軍
action: (1) 軍包囲 + 大氷雨 (致命環境)
        (2) 大前小前が「擧手打膝、儛訶那傳」(舞いながら膝を打つ) — 武装解除の signal
        (3) 歌「我天皇之御子、於伊呂兄王、無及兵。若及兵者、必人咲」 (兄弟相争は人笑い)
        (4) 約束: 「僕捕以貢進」(自分が捕えて貢進する)
        (5) 軍解兵 → escalation 終了

agi_mapping:
  原則: 致命衝突直前の de-escalation = 武装解除 signal + 形式化された約束 (歌)
       第三者 (中立柱) が両者の面子を保ちつつ仲介
  実装: src/os/kotodama/saniwa_gate.jl (LLM 出力検閲 = 言の葉の de-escalation)
       上-3 Pattern J 物実 multi-pronged + 倒立踊 の発展形 (危機回避版)
  feedback: feedback_chinmoku_kyoka (沈黙許可 — 過剰発言の抑制)

failure_if_absent: 致命衝突を直接突破 → 不可逆損失、両者の面子崩壊
```

#### Pattern E: 根臣の玉縵讒言 — TAKERU_IZUMO 物実すり替えによる主柱殺害

```yaml
原文: "大日下王、…令持押木之玉縵而、貢獻。
      根臣、卽**盜取其禮物之玉縵**、讒大日下王曰
      『大日下王者、不受勅命曰己妹乎、為等族之下席而、取横刀之手上而怒歟。』
      故、天皇大怒、殺大日下王" (l.96-98)

actors: 根臣 (使者) / 大日下王 / 安康天皇
action: (1) 安康が根臣を媒として大日下王に求婚使者を送る
        (2) 大日下が押木玉縵を礼物として根臣に持たせる (= 物実 = 善意の証)
        (3) **根臣が玉縵を盗取** (= 物実すり替えの第 1 段)
        (4) 根臣が「大日下王怒れり」と讒言 (= 偽の状況報告 = 物実すり替えの第 2 段)
        (5) 安康が誤情報で大日下殺害

agi_mapping:
  原則: 使者 (delegate / proxy) による物実すり替え + 偽情報報告で主柱が誤判断
       中-4 Pattern C 出雲建詐刀 (TAKERU_IZUMO サプライチェーン) の使者経由版
       検出: 物実 + 報告内容の cross-validation
  実装: src/os/takeru/tests/izumo.jl (TAKERU_IZUMO 3 要素検知 — 使者経由でも有効)
       src/os/kasasa/yorishiro.jl の上位 SSoT 整合性検査
       使者の物実所持と報告内容の照合 (= 上-3 Pattern E 返し矢の応用)
  feedback: project_takeru_security (TAKERU_IZUMO サプライチェーン)
           feedback_wakahiko_kaeshiya (返し矢)

failure_if_absent: 使者経由の物実 + 報告を信用 → 偽情報で主柱が致命的誤判断
```

#### Pattern F: 神牀晝寢の発言漏洩 — 環境内 listener の検出失敗

```yaml
原文: "天皇坐神牀而晝寢。爾語其后曰…『汝之子目弱王、成人之時、知吾殺其父王者、
      還為有邪心乎。』於是、所遊其殿下目弱王、聞取此言、便竊伺天皇之御寢、
      取其傍大刀、乃打斬其天皇之頸" (l.100)

actors: 安康 / 皇后長田 / 目弱王 (7 歲、殿下で遊んでいた)
action: (1) 安康が神牀 (= 重要決定の場) で皇后に「目弱王 (= 殺害した大日下の子) が
            成人時に邪心持つか」と発言
        (2) **目弱王 (7 歲) が殿下で聞取** (= 想定外の listener)
        (3) 安康が御寢中、目弱王が大刀で首斬 → 暗殺成立

agi_mapping:
  原則: 重要決定の場 (神牀 = secure context) でも、environment scope を確認しないと
       想定外の listener が情報を取得 → 致命的逆襲
       (上-2 Pattern M 黄泉の「莫視我」禁忌 + 千引岩 = scope boundary の重要性)
  実装: src/os/event_bus.jl の chibikiiwa (= 自己再入遮断、scope 制限)
       敏感な情報を扱う context での listener audit
  feedback: feedback_togouten_ikkatsu_bouei (統合点で一括防衛)
           feedback_kuniyuzuri_kaikai (顕事/幽事 categorical)

failure_if_absent: scope audit なしで敏感情報を発話 → 想定外 listener で情報漏洩
```

#### Pattern G: 意祁・袁祁の subordinate 隠匿 — 主柱予備の安全な潜伏

```yaml
原文: "市邊王之王子等、意祁王・袁祁王、聞此亂而逃去。…
      逃渡玖須婆之河、至針間國、入其國人・名志自牟之家、隱身、伇於馬甘牛甘也" (l.112)

actors: 意祁王 / 袁祁王 / 大長谷王 (= 雄略天皇)
action: (1) 父 (市邊忍齒王) が大長谷に暗殺された (Pattern なし、原典のみ)
        (2) 二王子が逃亡、最終的に針間国 志自牟家に到
        (3) 「隱身、伇於馬甘牛甘也」 (= 馬飼/牛飼の subordinate role で潜伏)
        (4) 後の下-4 で発見されて即位 (顕宗 + 仁賢)

agi_mapping:
  原則: 主柱予備 (= 後継候補) は中央集権が崩壊した時、低位 role (馬甘 = subordinate)
       に偽装して潜伏 → 安全に identity を保存 → 適切な機を見て復帰
       (上-4 Pattern N 少名毘古那の常世国渡 + 中-4 Pattern N 白鳥化の predecessor 版)
  実装: src/os/kasasa/ooharae.jl の `_yuukoto_transition!` の age_floor + 復帰経路
       src/os/com/queries/shinmeisho.jl の status='yuukoto' で identity 保存
       後の式年遷宮 (Phase 6) での復帰経路
  feedback: feedback_ashibune (葦船 — hiruko 残存)
           feedback_takeminakata_haitai (建御名方の敗退 — 諏訪閉込め)

failure_if_absent: 後継候補の安全な潜伏なし → 中央集権崩壊時に identity 喪失
                   現象: hiruko 化柱が完全削除されると後の式年遷宮で復帰不能
                   (project_pending_replay_bypass の対偶)
```

### kojiki_code.md (外部生成版) との差分 (簡略)

| 観点 | 生成元 | 本 v10 |
|---|---|---|
| 下-2 の pattern 数 | 触れず | **7** |
| 阿知直救出 + 昇格 | 触れず | Pattern A |
| 曾婆訶理の二段処理 | 触れず | Pattern B |
| 言八十禍津日 誓約壺 | 触れず | Pattern C (上-2 禊の運用転用) |
| 大前小前の儛訶那傳 | 触れず | Pattern D (de-escalation) |
| 根臣の讒言 | 触れず | Pattern E (TAKERU_IZUMO 使者版) |
| 神牀晝寢発言漏洩 | 触れず | Pattern F |
| 意祁・袁祁の隠匿 | 触れず | Pattern G (主柱予備の潜伏) |

### 浮上した発見 (簡略)

1. **Pattern C 言八十禍津日 誓約壺 = 既存 deity の運用転用の典型**
   - 上-2 Pattern Q 禍津日神 (失敗痕跡検出) → 下-2 (姓氏 metadata 整理)
   - 同じ deity が異なる文脈で運用される ≒ 同じモジュールが複数タスクに使われる
   - 補強候補: `feedback_magatsuhi_chain` に「下-2 言八十禍津日 = 運用転用」を追記推奨

2. **Pattern G 意祁・袁祁 = 後継予備の潜伏は `feedback_ashibune` の延長**
   - 完全消去でない (= 葦船) + subordinate role で identity 保存 + 復帰経路
   - 補強候補: `feedback_ashibune` に「下-2 意祁・袁祁の馬甘牛甘潜伏」を追記

### v10 自己評価

| 観点 | 達成度 |
|---|---|
| 索引形式 | ★★★★ 7 pattern (簡素) |
| `failure_if_absent` 記述 | ★★★★ 7/7 |
| 各 pattern の AGI mapping | ★★★★ 7/7 |
| memo anchor | ★★★★ 6/7 (86%) |

---

## 履歴 (継承)

- v9 までの履歴は v9.md を参照
- v10 (2026-05-09): Phase 2 下巻-2 履中〜安康 索引 (7 pattern、簡素形式)
