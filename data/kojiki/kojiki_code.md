これは深い問い。古事記には少なくとも 6 種類の processing pattern が procedural に書かれている。注釈ではなく本文 (主文) のロジック構造そのものが code として読める。

1. Try-Catch-Retry with RCA — 国生み第 1 試行 (上巻 -2)
最も衝撃的な例。これは literal な 構造化例外処理 + root cause analysis + retry:

原文の流れ

[Step 1] 約竟廻時、伊邪那美命、先言「阿那邇夜志愛袁登古袁。」
         後伊邪那岐命言「阿那邇夜志愛袁登賣袁。」
         → 妻 (Female) が先に発言、夫 (Male) が後に発言

[Step 2] 各言竟之後、告其妹曰「女人先言、不良。」
         → // WARN: female-first ordering is invalid

[Step 3] 雖然、久美度邇興而生子、水蛭子、
         → // ATTEMPT 1: returned defective output (water-leech child)

[Step 4] 此子者入葦船而流去。次生淡嶋、是亦不入子之例。
         → // REJECTED: discarded both invalid outputs (excluded from child list)

[Step 5] 於是、二柱神議云「今吾所生之子、不良。猶宜白天神之御所。」
         → try { ... } catch (BadOutput e) {
             escalate_to_parent_service();
         }

[Step 6] 卽共參上、請天神之命、爾天神之命以、布斗麻邇爾ト相而詔之
         「因女先言而不良、亦還降改言。」
         → // RCA from oracle: ROOT CAUSE = "female spoke first"
         //                    FIX = "go back and redo speech order"

[Step 7] 故爾反降、更往廻其天之御柱如先
         → // REDO: re-execute same loop body with fix applied

[Step 8] 於是伊邪那岐命先言「阿那邇夜志愛袁登賣袁。」
         後妹伊邪那美命言「阿那邇夜志愛袁登古袁。」
         → // ATTEMPT 2: male-first this time

[Step 9] 如此言竟而御合生子、淡道之穗之狹別嶋。
         → // SUCCESS: returned valid output (Awaji island)
Pattern 抽象化

def country_generation():
    while True:
        result = perform_ritual(speaker_order)
        if not is_valid(result):
            log_rejected(result)
            cause = oracle_consultation()  # divination = RPC call
            speaker_order = apply_fix(cause)
            continue  # retry
        return result
これは現代 software engineering の retry-with-backoff + RCA + structured exception handling と同型。1300 年前にこのパターンが書かれている。

2. Procedural Object Creation — 神産み sequence

次生神名、大事忍男神、
次生石土毘古神、
次生石巢比賣神、
次生大戸日別神、
次生天之吹男神、
次生大屋毘古神、
次生風木津別之忍男神、
次生海神・名大綿津見神、
次生水戸神・名速秋津日子神、
次妹速秋津比賣神。
Pattern

deities = []
for spec in deity_specs:
    deity = Deity(
        name=spec.name,
        domain=spec.domain,  # 海/水/風/火/etc
        parent=current_parent,
    )
    deities.append(deity)
# 自動集計: 自大事忍男神至秋津比賣神、幷十神 (annotation)
assert len(deities) == 10
これはシーケンシャル object instantiation with auto-aggregation。割書の 「自X至Y、幷Z神」 は assertion または post-hoc validation。

3. State Transformation Function — 禊 (上巻 -2 末)
イザナギ が黄泉から戻って身を清める transformation function:


[INPUT]  defiled state (黄泉から帰還)

[PROCESS]
  ├ 御杖を投げる → 衝立船戸神 を生成
  ├ 御帶を投げる → 道之長乳齒神 を生成
  ├ 御囊を投げる → 時量師神 を生成
  ├ ...
  ├ 御衣を投げる → 和豆良比能宇斯能神 を生成
  ├ 左目を洗う  → 天照大御神 を生成   ★ 太陽
  ├ 右目を洗う  → 月讀命 を生成       ★ 月
  └ 鼻を洗う    → 須佐之男命 を生成   ★ 嵐

[OUTPUT] clean state + spawned deities (side effects)
Pattern

def purification(initial_state):
    spawned = []
    for body_part in [杖, 帶, 囊, ..., 左目, 右目, 鼻]:
        new_deity = wash(body_part)  # input → output mapping
        spawned.append(new_deity)
    return CleanState(initial_state), spawned
これは input parameters (body parts) から deterministic outputs (specific deities) への pure function with side effects = まさに modern function definition。特に 三貴子 (天照・月讀・須佐之男) の生成は specific input → specific output mapping でhash table lookup や dispatch table に近い。

4. RPC / Oracle Call — 占い (ト)

天神之命以、布斗麻邇爾ト相而詔之
「天神が布斗麻邇 (太占) で占って詔した」

Pattern

# Remote procedure call to higher authority
result = oracle.consult(
    method="布斗麻邇",  # divination method
    question=current_problem,
)
return result.diagnosis  # cause analysis
これは Remote Procedure Call + diagnostic service。AGI でいうと higher-level reasoning service への delegation (例: tool use, expert system call)。

5. Recursive Descent — 神統譜

A 神 → 生 B, C, D
B 神 → 生 E, F
C 神 → 生 G, H, I
E 神 → 生 J, K
...
Pattern

def generate_descendants(parent_deity, depth=0):
    children = parent_deity.spawn()
    for child in children:
        yield child
        yield from generate_descendants(child, depth+1)  # recursive
= recursive descent generator。再帰的子孫生成。

6. State Machine — 須佐之男命 vs 八岐大蛇 (上巻 -3)

[State 1: 出会い]
  須佐之男 + 老夫婦 (足名椎・手名椎) → 状況把握
  
[State 2: 計画]
  「八鹽折之酒 + 8 桶 + 8 門の垣 + 8 棚」を準備指示
  
[State 3: 待機]
  大蛇出現 → 各頭が酒桶に頭を入れる
  
[State 4: 攻撃]
  大蛇が酔って眠った → 切断
  
[State 5: 戦利品]
  尾から十拳剣 (天叢雲剣) 取得
  
[State 6: 報告]
  天照大御神に献上
Pattern

class YamataNoOrochiBattle(StateMachine):
    states = [Encounter, Planning, Waiting, Attack, Loot, Report]
    
    def transition(self, state, event):
        if state == Waiting and event == DragonAppears:
            self.intoxicate()  # side effect
            return Attack
7. ★ 最も novel: Conditional Compilation directive
序文の有名な一節:


是以今、或一句之中、交用音訓、或一事之內、全以訓錄。
卽、辭理叵見、以注明、意況易解、更非注。
「ある句の中では音と訓を混用、ある事の内では全部訓で書く。意味が見にくい場合は注を付けて明らかに、分かりやすい場合は注を付けない」

Pattern

# Conditional compilation / output formatting
def render_chunk(chunk):
    if chunk.is_unclear:
        return chunk.text + annotate(chunk)  # add comment
    return chunk.text  # no comment

def encode_chunk(chunk):
    if chunk.context == 'mixed':
        return mix(phonetic, semantic)
    elif chunk.context == 'unified':
        return semantic_only(chunk)
これは literal な conditional compilation directive。Modern macro system の concept。

統合 — 古事記が implementing している全体プログラム

[main]
  initialize_substrate()  ← 混元既凝
  
  spawn_root_deities()  ← 造化三神 + 別天神五柱 + 神世七代
    
  while not all_creation_done:
    try:
      country = country_generation()  ← 国生み (with retry/RCA)
    except BadOutput as e:
      cause = oracle.consult()
      apply_fix(cause)
      continue
    
    for deity in deity_generation_sequence:  ← 神産み for loop
      spawn(deity)
      
    if state.is_defiled():  ← 黄泉訪問
      clean_state, spawned = purification(state)  ← 禊 transformation
      
    handle_conflict()  ← 須佐之男 vs 大蛇 state machine
    
  process_genealogy_recursive(root)  ← 天皇系譜 recursive descent
= 古事記全体が「宇宙生成 + 維持 + 観測者継承」の procedural な実装記述

AGI 実装への含意
古事記の処理	AGI 設計パターン
国生み try/catch/retry	self-correcting agent loop with RCA
神産み for sequence	sequential object instantiation
禊 transformation	state cleaning + side-effect tracking
占い RPC	tool use / external reasoning service call
神統譜 recursive	knowledge graph descent
須佐之男 state machine	task planning + execution state
「辭理叵見以注明」	selective explanation policy
