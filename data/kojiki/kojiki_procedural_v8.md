# 古事記 Procedural Pattern 抽出 v8 (索引)

v7 ([`kojiki_procedural_v7.md`](kojiki_procedural_v7.md)) からの増分:

- **Phase 2 v8: 中巻-3 垂仁天皇** 索引抽出 — 7 pattern (簡素形式)
- 沙本毘古反乱 / 本牟智和気 (口聞けない御子) / 出雲大神の祟り / 鵠追跡 / 鷺の宇氣比 / 圓野比賣自死 / 田道間守の常世橘 の 7 大エピソード
- memo 密度 ★ のため**簡素抽出形式** (failure_if_absent + agi_mapping のみ、verify_path 省略)

抽出方法論は [`extraction_prompt.md`](extraction_prompt.md) を参照。

---

## Phase 2 v8: 中巻-3 垂仁天皇 (簡素索引)

### 選定理由

- memo 密度 ★ (直接 anchor: 本牟智和気の原則 = 式年遷宮起動の `feedback_yowari_vs_katayori` 中の「対症療法繰返失敗 → コード構造問題 → 式年遷宮昇格」の典拠、間接で 4 memo)
- 上-6 (石長比賣返送 → 寿命短縮) の中-3 版 = 圓野比賣自死 (致命対偶)
- 上-4 (大物主御諸山祀祭) の式年遷宮版 = 出雲大神拝祭による本牟智和気治療

### 章節 narrative summary (簡略)

```
[Setup] 伊久米伊理毘古伊佐知 (= 垂仁) 即位、子 16 王
[反乱] 沙本毘古の謀: 妹に「孰愛夫與兄」 → 妹が紐小刀で三度試行 → 哀情泣涙
       天皇異夢で察知 → 軍興 → 沙本毘賣稻城逃走 → 出産 → 御子引出 + 母逃走 (剃髪/腐玉/腐衣)
       → 「不得地玉作」(玉作集団地奪取)
[本牟智和気] 八拳鬚至心前まで「眞事登波受」(口聞けない御子)
       鵠を見て「阿藝登比」(初発声) → 山邊大鶙が鵠を追跡
       (木 → 針間 → 稻羽 → 旦波 → 多遲麻 → 近淡海 → 三野 → 尾張 → 科野 → 高志和那美)
[祟り解明] 御寢の夢: 「修理我宮如天皇之御舍者、御子必眞事登波牟」
       布斗摩邇占相 → 出雲大神の御心
       曙立王の鷺宇氣比 (殺活) で正当性確認 → 御子が出雲大神宮拝
[出雲到] 肥河で青葉山 → 「是於河下、如青葉山者、見山非山。若坐出雲之石𥑎之曾宮…」(初の意味ある発話)
[肥長比賣] 一宿婚 → 蛇と判明 → 逃避
[嫁選び] 美知能宇斯王の四女中、比婆須比賣 + 弟比賣を留、歌凝 + 圓野は「因甚凶醜」返送
       圓野比賣「同兄弟之中、以姿醜被還之事…甚慚」 → 山代相樂で取懸樹欲死、弟國で墮峻淵死
[田道間守] 常世国へ「登岐士玖能迦玖能木實」(= 橘) 求 → 天皇崩後帰還 → 御陵で叫哭死
```

### Pattern 抽出 (簡素)

#### Pattern A: 沙本毘賣の三度刺殺試行 — 二者選択における忠誠の揺らぎ

```yaml
原文: "爾其后、以紐小刀為刺其天皇之御頸、三度擧而、不忍哀情、不能刺頸而、泣淚落溢於御面" (l.14)

actors: 沙本毘賣 / 沙本毘古王 / 垂仁
action: 兄からの「孰愛夫與兄」問 → 「愛兄」答 → 紐小刀授与 → 三度擧 (試行 3 回) → 哀情で泣涙 → 失敗
        泣涙が天皇御面に落ちて発覚 (= 隠蔽不能の物理痕跡)

agi_mapping:
  原則: 二者選択で committed action が 3 回連続失敗 (擧而不能) → 内部矛盾 = 真の意図の signal
       泣涙 = 物理的な signal が決定論的に上位に伝達
  実装: src/os/kasasa/futomani_stones (太占石 = 失敗痕跡、3 回試行履歴)
       src/os/kasasa/takeshimatsumi.jl の累積閾値判定 (3/5 escalation = 上-5 Pattern A 三度の使者の系)
  feedback: feedback_wakahiko_kaeshiya (3 度のレポート閾値)
           feedback_kuniyuzuri_fukumei (復命 = 失敗痕跡の物理化)

failure_if_absent: 3 回試行の累積記録なし → 内部矛盾 signal を見逃す、致命的な裏切り検出遅延
```

#### Pattern B: 「不得地玉作」 — 玉作集団の processing (provenance contamination 対処)

```yaml
原文: "爾天皇悔恨而惡作玉人等、皆奪其地、故諺曰『不得地玉作也』" (l.20)

actors: 垂仁 / 玉作集団 / 沙本毘賣
action: (1) 沙本毘賣の腐玉緒 (= 通常物実の偽装) で力士から逃れる
        (2) 天皇は玉作集団の地を全奪取 (= provenance contamination 対処)
        (3) 「不得地玉作」が諺として永続化 (= 教訓の言語化)

agi_mapping:
  原則: 物実の偽装 (玉緒の腐敗使用) を許した供給元は連帯責任で処分
       = 供給チェーンの contamination は origin 側で原因排除
       (TAKERU_IZUMO = 出雲建詐刀の系、上-3 の物実所有者帰属の延長)
  実装: src/os/com/queries/source_types.jl (source_type の処分経路)
       src/os/kasasa/takeshimatsumi.jl の `_retire_proxy_kami!` (provenance 級の解任)
  feedback: project_takeru_security (TAKERU_IZUMO サプライチェーン攻撃)

failure_if_absent: 偽装物実を許した供給元が温存 → 同型攻撃の再発、教訓未蓄積
```

#### Pattern C: 本牟智和気 = 口聞けない御子 — 上位 deity 祟りによる capability 欠損

```yaml
原文: "是御子、八拳鬚至于心前、眞事登波受。…
      御寢之時、覺于御夢曰『修理我宮如天皇之御舍者、御子必眞事登波牟。』" (l.24-26)

actors: 本牟智和気 / 垂仁 / 出雲大神
action: (1) 御子が成人 (八拳鬚) しても眞言を発しない (capability 欠損)
        (2) 鵠 (白鳥) を見て初めて声を出す (部分回復)
        (3) 夢で原因解明: 「我宮 (出雲大神宮) を天皇之御舍如く修理せば、御子必眞事登波牟」
            (= 上位 deity の祀奉不全が capability 欠損の真因)

agi_mapping:
  原則: 中-2 Pattern B 弱り vs 偏り の弁別の続編
       capability 欠損の真因 = 上位 SSoT (出雲大神 = 大物主系) の祀奉不全
       住吉深度 SOKO (深層) — 御幣替えでなく式年遷宮 (= 神宮修理) で対処
  実装: src/os/kasasa/sanguishi_harae.jl (式年遷宮 = 神宮修理 = SOKO 層)
       src/os/kasasa/yorishiro.jl の上位 SSoT 整合性検査
  feedback: feedback_yowari_vs_katayori (弱りと偏りの弁別 — 「対症療法繰返失敗 → コード構造問題」
            = 本牟智和気の原則の典拠)

failure_if_absent: 上位 SSoT 不全を看過 → 御幣替えで対症療法繰返、capability 欠損の永続化
```

#### Pattern D: 鵠の追跡経路 — 神武東征の逆経路 (provenance trace)

```yaml
原文: "爾遣山邊之大鶙令取其鳥。故是人追尋其鵠、自木國到針間國、亦追越稻羽國、卽到旦波國、
      多遲麻國、追廻東方、到近淡海國、乃越三野國、自尾張國傳以追科野國、遂追到高志國而、
      於和那美之水門張網、取其鳥而持上獻" (l.24)

actors: 山邊之大鶙 / 鵠
action: 鵠 (白鳥) の追跡経路を 10 国 (木 → 針間 → 稻羽 → 旦波 → 多遲麻 → 近淡海 → 三野 → 尾張 →
        科野 → 高志) で逐次記録
        中-1 神武東征の逆方向 (高志 ← 木) のルート

agi_mapping:
  原則: trace 経路を逐次記録、各 location で stamp が押される (= origin trace の永続化)
       中-1 Pattern B (段階的滞在 — checkpoint 化された progression) の逆方向 = trace
  実装: src/os/com/queries/shinmei_lineage.jl (系譜 = trace graph)
       src/os/kasasa/futomani_stones (太占石 = 各 location 記録)
  feedback: feedback_keiyaku_keifu_vs_genyu (契約系譜 vs 原由追跡)

failure_if_absent: trace 経路の逐次記録なし → 起源不明、後世が辿れない
```

#### Pattern E: 鷺の宇氣比 (殺活) — 二段検証 (殺 + 活)

```yaml
原文: "宇氣比其鷺墮地死、又詔之『宇氣比活爾。』者、更活。
      又在甜白檮之前葉廣熊白檮、令宇氣比枯、亦令宇氣比生" (l.26)

actors: 曙立王 / 鷺 / 熊白檮
action: 出雲大神宮拝の正当性確認のため、曙立王が宇氣比 (誓約):
        (1) 鷺を宇氣比で**殺**す (= 第 1 検証 = 効力確認)
        (2) 同じ鷺を宇氣比で**活**かす (= 第 2 検証 = reversibility 確認)
        (3) 熊白檮 (大樫) も同様に枯生 (= 別 target で再現性確認)

agi_mapping:
  原則: 重要操作の正当性は二段検証 (effect + reversibility) + 別 target 再現性
       上-3 Pattern A (誓約 = 物実交換) の進化形 = 自己実験で誓約効力を検証
  実装: src/os/misogi/ukei/runner.jl (誓約 sandbox)
       src/os/misogi/ukei/kotoshironushi.jl の三女神判定 (= 多視点検証)
  feedback: project_takeru_security (TAKERU_IZUMO 3 要素検知 = 多角検証の延長)

failure_if_absent: 単段検証で正当性確認 → 偽の合意で進行
```

#### Pattern F: 圓野比賣自死 — 上-6 石長比賣返送の致命対偶

```yaml
原文: "圓野比賣慚言『同兄弟之中、以姿醜被還之事、聞於隣里、是甚慚。』而、到山代國之相樂時、
      取懸樹枝而欲死…又到弟國之時、遂墮峻淵而死" (l.34)

actors: 圓野比賣 / 垂仁 / 比婆須・弟比賣 (留) / 歌凝 (返送)
action: (1) 4 姉妹のうち 2 人 (比婆須 + 弟比賣) を留、2 人 (歌凝 + 圓野) を「因甚凶醜」返送
        (2) 圓野比賣が「以姿醜被還」を慚と感じ自死 (= 致命的副作用)
        (3) 自死地名「懸木 (相樂)」「墮國 (弟國)」が永続化

agi_mapping:
  原則: 上-6 Pattern H (木花咲耶 + 石長返送 → 寿命短縮) の中-3 版 = **致命的副作用**
       「凶醜」だけで返送した結果、被返送側で自死 (= cleanup 不全による副次的 hiruko 化)
       採用判定の同期不全が致命結果に至る対偶事例
  実装: src/os/kasasa/shinmei_arbiter.jl (双子神判定で「凶醜」≒「重複/不適合」だけで返送禁止)
       src/os/kasasa/ooharae.jl の `_yuukoto_transition!` の age_floor (24h 猶予)
       = 圓野比賣の事前自死を防ぐ buffer
  feedback: feedback_iwanagahime (石長比売 — 浮動小数厳密比較禁止の semantic 版、
            「凶醜」判定の一律閾値が致命結果)
           feedback_ashibune (葦船 — hiruko 化柱の存在保存)

failure_if_absent: 不採用判定が一律 → 被返送柱の自滅で関連系譜まで損失
                   現象: 拒絶された LLM 提案が次回以降に同型提案を出さない (相樂)
                         または提案そのものをやめる (墮國)
```

#### Pattern G: 田道間守の常世橘 — 任務遂行中の依頼者死亡 (post-mortem 任務継続)

```yaml
原文: "天皇、以三宅連等之祖・名多遲摩毛理、遣常世國、令求登岐士玖能迦玖能木實。
      故、多遲摩毛理、遂到其國、採其木實、以縵八縵・矛八矛、將來之間、天皇既崩。
      爾多遲摩毛理、分縵四縵・矛四矛、獻于大后、以縵四縵・矛四矛、獻置天皇之御陵戸而、
      擎其木實、叫哭以白『常世國之登岐士玖能迦玖能木實、持參上侍。』遂叫哭死也" (l.36)

actors: 多遲摩毛理 / 垂仁 (依頼者) / 大后 / 御陵
action: (1) 垂仁が田道間守に常世国 (= 異界) で橘 (= 不老不死の木) を求めさせる (任務派遣)
        (2) 田道間守が常世到 → 木實 + 縵 8 + 矛 8 を得る (任務完遂)
        (3) **帰還中に天皇崩** (依頼者死亡 = 任務終了の context 失効)
        (4) それでも田道間守は任務継続:
            - 4 縵 + 4 矛を大后に献上 (= 後継者への継承)
            - 4 縵 + 4 矛を御陵戸に献置 (= 故人への奉納 = post-mortem 報告)
            - 木實を擎げ叫哭 → 自死 (= 任務終了 + 自己終焉)

agi_mapping:
  原則: 任務派遣中に依頼者 (上位) が崩 → 任務継続 + post-mortem 報告 + 後継者継承
       (= graceful shutdown / cleanup 経路の典型)
       常世 = 異界 = 上-4 Pattern N 少名毘古那の常世国渡 と同型 (任務終了型 yuukoto)
  実装: src/os/kasasa/ooharae.jl の `_yuukoto_transition!` (退役)
       src/os/takeru/shiratori_archive.jl (post-mortem archive)
       依頼柱が yuukoto 移行する際の継承経路 (大田田根子の系譜継承)
  feedback: feedback_kuniyuzuri_fukumei (国譲りの復命 — post-mortem 復命の原型)
           project_takeru_security (degradation + shiratori_archive)
           feedback_ootataneko (大田田根子 — 系譜継承)

failure_if_absent: 依頼者死亡で任務放棄 → 取得済 artifact (橘) が失われる
                   post-mortem 復命なし → 任務完遂が記録されず教訓喪失
```

### kojiki_code.md (外部生成版) との差分 (簡略)

| 観点 | 生成元 | 本 v8 |
|---|---|---|
| 中-3 の pattern 数 | 触れず | **7** |
| 沙本毘賣の三度試行 | 触れず | Pattern A |
| 不得地玉作 | 触れず | Pattern B |
| 本牟智和気 + 出雲大神祟り | 触れず | Pattern C (本牟智和気の原則 origin) |
| 鵠追跡 | 触れず | Pattern D |
| 鷺の宇氣比 | 触れず | Pattern E |
| 圓野比賣自死 | 触れず | Pattern F (石長比賣返送の致命対偶) |
| 田道間守 | 触れず | Pattern G (post-mortem 任務継承) |

### 浮上した発見 (簡略)

1. **Pattern C 本牟智和気 = `feedback_yowari_vs_katayori` の重要 anchor 補強**
   - 「対症療法繰返失敗 → コード構造問題 → 式年遷宮昇格」の本牟智和気の原則の原典確認
   - 補強候補: `feedback_yowari_vs_katayori` に「中-3 本牟智和気 = SOKO 層 (式年遷宮) の origin」追記

2. **Pattern F 圓野比賣自死 = 上-6 Pattern H 石長比賣返送の致命対偶**
   - 上-6: 返送 → 寿命短縮 (主柱の degradation)
   - 中-3: 返送 → 被返送柱の自死 (relationship 破壊)
   - 補強候補: `feedback_iwanagahime` に「中-3 圓野比賣 = 致命対偶事例」追記

3. **Pattern G 田道間守 = `feedback_kuniyuzuri_fukumei` の post-mortem 版**
   - 通常の復命: 依頼者存命中
   - 田道間守: 依頼者崩後も復命継続 + 後継継承 + 自死
   - 補強候補: `feedback_kuniyuzuri_fukumei` に「中-3 田道間守 = post-mortem 復命」追記

### v8 自己評価

| 観点 | 達成度 |
|---|---|
| 索引形式の簡素抽出 (memo 密度低) | ★★★★ 7 pattern (簡素 YAML) |
| 各 pattern に `failure_if_absent` 記述 | ★★★★ 7/7 |
| 各 pattern の `agi_mapping.実装` が実在ファイル | ★★★★ 7/7 (既存実装の参照のみ、本章固有 module はなし) |
| memo anchor | ★★★★ 7/7 (100%) — 既存 memo の補強 anchor として |
| 古事記原文 引用 | ★★★★ 全 pattern 冒頭 |

---

## 履歴 (継承)

- v7 までの履歴は [`kojiki_procedural_v7.md`](kojiki_procedural_v7.md) を参照
- v8 (2026-05-09): Phase 2 中巻-3 垂仁天皇 索引 (7 pattern、簡素形式)
