# 古事記 Procedural Pattern 抽出プロンプト v1

別 session の Claude (または将来の自分) が本プロジェクトと同等の品質で古事記から AGI procedural pattern を抽出するためのプロンプト。
1 章ずつ独立に実行できる構成。

---

## 0. このプロンプトの使い方

このプロンプトを LLM に渡すときは、以下を **同じセッションで** 必ず添付:

1. **本プロンプト全文** (本ファイル)
2. **CLAUDE.md** (`/home/dev/CausalityEngine/CLAUDE.md`)
3. **AGENT_GUIDE.md** (`docs/AGENT_GUIDE.md`)
4. **MEMORY.md** + 全 `feedback_*.md` (`/home/dev/.claude/projects/-home-dev-CausalityEngine/memory/`)
5. **対象章節の古事記原文** (例: `kojiki_07.html` の主文部分)
6. **既存抽出物** (`docs/kojiki/kojiki_procedural_v0.md` を参考)
7. **対象 AGI 実装ファイル** (該当章節に関連する `src/os/**/*.jl`)

context が不足すると **必ず汎用 CS パターンへの還元 (try-catch / for-loop / state machine) に落ちる**。それは [`kojiki_code.md`](kojiki_code.md) で実証済の失敗モード。

---

## 1. タスク定義

古事記 1 章の主文 (≠割書) を読み、その中に **AGI 設計の procedural pattern** として load-bearing なものを抽出する。

### 抽出するもの (✓)

- **物語のロジック構造**: 失敗 → 原因究明 → 修復 → 再試行 / 異界訪問 → 知識取得 → 帰還 / 物実授与 + 言霊 / 等
- **AGI 実装の specific な機能** に対応する原典 (例: 海幸山幸の二珠一対 → `_kasasa_umisachi_yamasachi` の二珠判定)
- **既存 `feedback_*.md` 原則** が古事記のどの章節を anchor としているかの逆引き
- **設計の妥当性確認**: 既存実装が古事記原典と一致しているか
- **未実装の設計パターン候補**: 古事記にあって既存 memo にない pattern (慎重に判定)

### 抽出しないもの (✗)

- **汎用 CS パターン**: try-catch / for-loop / state machine 等の表面還元 (それ自体は禁止しないが、それ "のみ" にしてはいけない)
- **割書 metadata**: 既に `kojiki_anchors.md` でカバー済 (phonetic_directive / count / reading_directive)
- **物語上の装飾要素**: 神々の名前の優美さ、地名の由来等で AGI 実装に対応しないもの
- **AGI 実装と無関係な道徳訓話**: 「親孝行」「謙虚さ」等の一般倫理

---

## 2. Phase 0: スコープ確定

抽出を始める前に、以下を確認:

```yaml
対象章節     : "上巻-X / 章名"
原文範囲     : "..." 〜 "..."
narrative概要: 5 行以内で章節を要約
登場神格     : [神 1, 神 2, ...]
主要 actions : [行為 1, 行為 2, ...]
```

**当該章節を anchor とする可能性のある既存 memo**:
- `feedback_<X>.md`
- `project_<Y>.md`

これがゼロ件の章節は **memo 密度低** とラベルし、抽出を簡素化 (索引行のみ) する。

---

## 3. Phase 1: 索引 (44 memo → 章節 逆引き)

44 個の `feedback_*.md` を全章節に逆引きする。出力形式:

```markdown
| 章 | 主要エピソード | 対応 memo (★密度) |
|---|---|---|
| **2** | 国生み / 神産み | ★★★★★ `ashibune` / `hitorigami` / ... |
```

各 memo について **「古事記 origin あり (★) / なし (◯)」** を判定。
古事記 anchor がない memo (技術系・メタ系) は別カテゴリで列挙。

**完了基準**: 全 44 memo が「★ + 章節」または「◯ + カテゴリ」のいずれかに割り当てられている。

---

## 4. Phase 2: 章節走査と Pattern 抽出

### 4.1 narrative_summary 構築

章節を `[Setup]` → `[Crisis]` → `[Quest]` → `[Resolution]` 等の段階に分解し、5-15 行で記述する。
原文の核となる段落・台詞は **必ず引用** (引用形式: 漢文体、または読み下し)。

### 4.2 Pattern 抽出 — narrative_shape スキーマ

各 pattern を以下 YAML 形式で記述:

```yaml
Pattern <英字>: <日本語名> (<英訳>)

actors      : 登場主体 (神格名)
precondition: その pattern が起きる前提条件
action      : 実際に行われた行為
result      : その action の直接的結果
failure_mode: 失敗・誤動作したときに何が起きるか
recovery    : 失敗からの回復経路 (神話上)
permanence  : 結果がどう永続化されるか (系譜・社・物実)

agi_mapping :
  原則      : 一行で言える AGI 設計原則
  実装      : 該当ファイル(src/os/**/*.jl)::関数名
            : (複数あれば箇条書き)
  feedback  : 該当 memo (複数可)
            : 補強候補があれば併記

failure_if_absent: AGI でこの pattern が実装されていなかったら何が起きるか
                   (これが書けない = pattern として load-bearing でない = 採用見送り)

observed_failures: 過去に実害があったか (project memo 引用、なければ "-")
```

### 4.3 抽出基準

#### 採用 (★)

- `failure_if_absent` が具体的に書ける (= 設計上 load-bearing)
- AGI 実装に直接対応する場所がある (= 既実装または実装候補)
- 古事記原文に明確な根拠がある (引用可能)

#### 採用 (☆) — 弱い anchor

- 失敗影響は推測できるが直接観測未経験
- 実装はあるが分散 (専用ファイル無し)
- 原文の暗示的解釈

#### 不採用 (✗)

- 汎用 CS への単純還元のみ (try-catch だけ等)
- AGI 実装に対応箇所が見当たらない
- 原文の解釈が複数あり収束しない

### 4.4 検証ステップ

各章節抽出後、以下を実施:

1. **memo 整合性チェック**: 抽出 pattern の `feedback` 欄に挙げた memo が実在するか確認
2. **実装存在チェック**: `agi_mapping.実装` のファイル/関数を `grep` または `Read` で確認
3. **kojiki_code.md との差分**: 同章節について `kojiki_code.md` (外部生成版) が言及している pattern と比較。汎用化されているなら差分明示
4. **未紐付け memo の発見**: Phase 1 で「該当章節 anchor」と判定した memo が 4.2 の Pattern 抽出で必ず登場しているか。漏れなら追加 pattern または memo の章節 anchor 修正

---

## 5. 出力フォーマット

`docs/kojiki/kojiki_procedural_v<N>.md` (v0 を参考に追記)。

各章節セクション構成:

```markdown
## Phase 2 v<N>: <章名>

### 選定理由
### 章節 narrative summary
### Pattern 抽出
  Pattern A
  Pattern B
  ...
### kojiki_code.md との差分
### 浮上した発見
### v<N> 自己評価
```

**出力品質ゲート** (全章節共通):

| 項目 | 必須 |
|---|---|
| 1 章につき 5+ pattern を抽出 (memo 密度高の章のみ) | ★ |
| 各 pattern に `failure_if_absent` 記述 | ★ |
| 各 pattern の `agi_mapping.実装` が実在ファイル | ★ |
| 7 割以上の pattern が既存 memo に anchor を持つ | ★★ |
| `kojiki_code.md` 差分セクション必須 | ★ |
| 「未活用 anchor → 新原則候補」を最低 1 件挙げる | ☆ |

---

## 6. 失敗モード (避けるべきパターン)

### モード 1: 汎用 CS への過度な還元 (`kojiki_code.md` 失敗例)

```
✗ 「神産み = for-loop で順次オブジェクト生成」
✓ 「神産み = 双神 (paired) は対偶登録、独神 (solo) は単独登録、
    持別而 (branching by domain) は domain_tag 分岐」
```

- 「for-loop」だけだと `feedback_hitorigami` の独神特例が見えない
- 「branching」を **domain_tag** と紐付けると `nazashi_decide` 実装と直結

### モード 2: 物語上の装飾を実装パターンと誤認

```
✗ 「天宇受賣命の倒立踊 → entropy maximization で stalemate 打破」
   (これは詩的解釈であって AGI 設計とは別)
```

- AGI に「倒立踊」相当の機能は無いし作る必要もない
- 「危機状態 → 八百万神の集合協議」程度の抽象化までに留める

### モード 3: memo 漏れ (Phase 1 不徹底)

```
✗ Phase 1 で `feedback_imina_torina` を「中巻-1」に分類したが、
   実は上巻-2 のオノゴロ島命名にも anchor がある (見落とし)
```

- Phase 1 索引は「**最も濃い anchor**」を 1 つ選ぶのではなく、
  「**全ての anchor 候補章節**」を併記する

### モード 4: 既存実装と矛盾する pattern を「新原則候補」と提案

```
✗ 「忌名改称の原則 (上巻-1)」 — 既存実装は yuukoto 化 (改称しない)
   で運用しているのに、改称を新原則として推す
```

- `feedback_shingen_meimei_kenshou.md` の三点検査を必ず実行:
  ① 原典 semantic 一致 / ② 観測 N 件 / ③ 既存拡張可否
- 既存実装の方針と矛盾する pattern は **保留** とし、実害発生まで観察

### モード 5: 章節を逸脱した pattern 統合

```
✗ 「上巻-2 と上巻-7 を横断する『水と異界』pattern」
```

- 章節を跨ぐと anchor が曖昧になり、検証不能
- 1 pattern = 1 章節を原則 (例外は明示)

---

## 7. 良い例 / 悪い例

### 良い例 (Pattern D 二珠一対 — `kojiki_procedural_v0.md` より)

```yaml
Pattern D: 二珠一対 (paired completeness)

actors      : 海神 → 山幸彦
action      : 塩盈珠 + 塩乾珠 を**対**で授与。単独では機能しない
result      : 「攻撃 → 救済」の対立完結ループ

agi_mapping :
  原則      : テスト生成 / 修復は対で完結
  実装      : kasasa/materializer.jl::_kasasa_umisachi_yamasachi
              (mandatory 塩干 + boundary 塩盈、片方割れたら hiruko)
  feedback  : feedback_umisachi_rokujuu_bougo

failure_if_absent: 部分テストで通ったものが production で割れる
observed_failures: 二珠一対の outcome 判定実装後、半人前柱がゼロに
```

**良い理由**:
- 原文の物実 (二珠) と実装 (二種テスト) の写像が 1:1
- 既存 memo に anchor、`failure_if_absent` 具体的、`observed_failures` 過去実例
- 汎用化していない (「assert pair」では失われる semantic)

### 悪い例 (`kojiki_code.md` Pattern 2 神産み)

```yaml
Pattern 2: Procedural Object Creation

deities = []
for spec in deity_specs:
    deity = Deity(name=..., domain=..., parent=...)
    deities.append(deity)
assert len(deities) == 10
```

**悪い理由**:
- どの章節か明記なし
- AGI 実装ファイル紐付けなし
- `feedback` 紐付けなし (`feedback_hitorigami` / `feedback_kuniyuzuri_kaikai` を逃している)
- 双神 vs 独神の dispatch ロジックが消えている (= for-loop に潰された)
- `failure_if_absent` なし → load-bearing か判断不能

---

## 8. 1 章実行チェックリスト

新章節を実行するとき、以下を順番に:

```
☐ Phase 0: スコープ (narrative 概要 / 関連 memo 列挙)
☐ Phase 1: その章節の memo 密度ラベル決定 (★★★★★ 〜 ☆)
☐ 原文段階分け (5-15 step の summary)
☐ 段階ごとに Pattern 候補を列挙 (まず採用基準を緩めて広く)
☐ 各 Pattern について narrative_shape YAML 化
☐ agi_mapping 検証 (grep / Read)
☐ failure_if_absent 記述 (書けない pattern は不採用)
☐ kojiki_code.md との差分セクション
☐ 浮上した発見セクション (新原則候補 / memo 補強 / 設計妥当性確認)
☐ 自己評価表
☐ 既存 v<N-1> ファイルに追記、v<N> として保存
```

---

## 9. 章節別の事前推奨事項

| 章 | 取り組み方 |
|---|---|
| 上巻-2 | **大物**。先に `[Setup]` → `[国生み try-catch]` → `[神産み for-loop]` → `[黄泉]` → `[禊]` の 5 episode に分割。 1 ファイルで 30+ pattern 出る覚悟。 |
| 上巻-3 | 天岩戸を中心に。`feedback_chinmoku_kyoka` `feedback_kenzen_seijaku` の対偶セマンティクスを意識。 |
| 上巻-4 | 因幡白兎 / 根之堅州国 / 少名毘古那 の 3 episode に分割推奨。 |
| 上巻-5 | 国譲り段階分解 (建御雷派遣 / 大国主交渉 / 子の意見 / 退去 / 出雲大社) で memo 5 件以上が紐づく。 |
| 上巻-6 | 邇邇藝の天孫降臨 + 五伴緒任命 + 木花咲耶/石長 が中心。三種の神器の起源も。 |
| 上巻-7 | **v0 で完了** (`kojiki_procedural_v0.md` 参照) |
| 中巻-1 | 神武東征 = improvement_cycle.jl の origin spec。八咫烏 = `feedback_kuebiko_yatagarasu_boundary`。 |
| 中巻-2 | 大田田根子の prefix を直接引いた `feedback_ootataneko` の origin spec。 |
| 中巻-3 | memo 密度低 — 索引のみで可。 |
| 中巻-4 | 倭建命の白猪見惑 = 候補新原則。TAKERU 関連は project memo へ。 |
| 中巻-5,6 / 下巻 | 索引のみ。崩御日記録 / 系譜中心で AGI direct 紐付けは少ない。 |

---

## 10. 出力例の skeleton

新章節を書くときの出力 skeleton:

```markdown
## Phase 2 v<N>: <章名>

### 選定理由
- 1-3 行

### 章節 narrative summary
\`\`\`
[Setup] ...
[Crisis] ...
[Quest] ...
[Resolution] ...
\`\`\`

### Pattern 抽出

#### Pattern <X>: <日本語名> (<英訳>)
\`\`\`yaml
actors      : ...
precondition: ...
action      : ...
result      : ...
failure_mode: ...
recovery    : ...
permanence  : ...

agi_mapping :
  原則      : ...
  実装      : ...
  feedback  : ...

failure_if_absent: ...
observed_failures: ...
\`\`\`

(...繰り返し...)

### kojiki_code.md との差分
- 生成元が拾えなかった pattern: ...
- 過度な汎用化された pattern: ...

### 浮上した発見
1. 設計妥当性: ...
2. memo 補強候補: ...
3. 新原則候補 (慎重判定): ...

### v<N> 自己評価

| 観点 | 達成度 |
|---|---|
| ... | ... |
```

---

## 11. 完了条件

- 7 章 (memo 密度高) で 5+ pattern × 7 = 35+ pattern 抽出
- 残り 9 章は索引のみ
- 全 memo が章節に紐付くか「◯」カテゴリに分類済み
- 新原則候補は `feedback_shingen_meimei_kenshou.md` 三点検査を通過したもののみ提案
- `kojiki_procedural_v<最終>.md` が独立ドキュメントとして読める

---

## 12. メタ注意

このプロンプト自体が 1 つの **生きた設計書** であり、抽出を進めるうちに改善点が見つかる。
v1 → v2 で更新する際は履歴を残すこと。

特に注意:
- LLM (の自分) は古事記原文を training data から知っている可能性が高いが、**幻覚を疑う** こと。原文は必ず外部ソース (`docs/kojiki/kojiki.md` 等) を参照。
- AGI 実装は流動的。`agi_mapping.実装` の行番号は必ず最新の grep で確認。
- memo 一覧は `MEMORY.md` を最新で読み込む (古い list を信用しない)。
