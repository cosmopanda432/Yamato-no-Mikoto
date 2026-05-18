"""
稗田阿礼 (Hieda-no-Are) コンテキスト注入システム

=== 五層アーキテクチャでの役割 ===

Layer 4 → Layer 3 の「通信プロトコル」として機能。
外部データソース（海原・常世）からデータを取得し、
推論ランタイム（葦原中国）に注入する。

役割:
├── 外部データの取得 (Fetch)
├── コンテキストへの変換 (Tokenize & Embed)
├── 関連性フィルタリング
└── Layer 3 への注入 (Prompt Injection)

=== 従来の役割（互換性維持） ===

古事記編纂における稗田阿礼の役割:
  - 帝紀・旧辞をすべて暗記（誦習）する記憶装置
  - 太安万侶（文章生成）に対して、定義を正確に唱え続ける

66Mモデル（太安万侶）の外部に「阿礼」を置き、
生成された定義を記憶し、各Phase開始時にREPL形式で誦習する。

Architecture:
    HiedaNoAre (メインクラス)
    ├── JuliaDefinitionParser  — テキストから定義を抽出
    ├── AreMemory              — Phase横断の定義記憶
    ├── ShoujuFormatter        — REPL形式の誦習プロンプト整形
    └── fetch_and_contextualize — 五層統合用API
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set


# ---------------------------------------------------------------------------
# 定義の種類
# ---------------------------------------------------------------------------

class DefinitionKind(Enum):
    """Julia 定義の種類"""
    STRUCT = "struct"
    MUTABLE_STRUCT = "mutable_struct"
    ABSTRACT_TYPE = "abstract_type"
    PRIMITIVE_TYPE = "primitive_type"
    CONST = "const"
    FUNCTION_SIGNATURE = "function_signature"


# 優先度 (小さいほど高優先)
_KIND_PRIORITY = {
    DefinitionKind.STRUCT: 0,
    DefinitionKind.MUTABLE_STRUCT: 0,
    DefinitionKind.ABSTRACT_TYPE: 1,
    DefinitionKind.PRIMITIVE_TYPE: 1,
    DefinitionKind.FUNCTION_SIGNATURE: 2,
    DefinitionKind.CONST: 3,
}


@dataclass
class JuliaDefinition:
    """抽出された Julia 定義"""
    kind: DefinitionKind
    name: str
    source: str
    phase: int

    @property
    def priority(self) -> int:
        return _KIND_PRIORITY.get(self.kind, 99)


# ---------------------------------------------------------------------------
# 定義パーサー
# ---------------------------------------------------------------------------

class JuliaDefinitionParser:
    """
    生成テキストから Julia 定義を正規表現で抽出

    REPL出力 (julia> プレフィックス) にも対応。
    部分的な定義にも耐性を持つ。
    """

    # struct / mutable struct ... end
    _RE_STRUCT = re.compile(
        r'((?:mutable\s+)?struct\s+(\w+)(?:\{[^}]*\})?'
        r'(?:\s*<:\s*[\w{}.]+)?'
        r'.*?end)',
        re.DOTALL,
    )

    # abstract type Name end / abstract type Name <: Parent end
    _RE_ABSTRACT = re.compile(
        r'(abstract\s+type\s+(\w+)(?:\s*<:\s*\w+)?\s*end)'
    )

    # primitive type Name <bits> end
    _RE_PRIMITIVE = re.compile(
        r'(primitive\s+type\s+(\w+)\s+\d+\s*end)'
    )

    # const NAME = ...
    _RE_CONST = re.compile(
        r'(const\s+(\w+)\s*=\s*[^\n]+)'
    )

    # function name(...) — 署名行のみ
    _RE_FUNC_SIG = re.compile(
        r'(function\s+(\w+)(?:\{[^}]*\})?\s*\([^)]*\)'
        r'(?:\s*::\s*[\w{}.]+)?'
        r'(?:\s*where\s*\{[^}]*\})?)'
    )

    def _strip_repl_prompts(self, text: str) -> str:
        """julia> プレフィックスを除去"""
        lines = text.split('\n')
        cleaned = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('julia>'):
                cleaned.append(stripped[6:].strip())
            else:
                cleaned.append(line)
        return '\n'.join(cleaned)

    def parse(self, text: str, phase: int) -> List[JuliaDefinition]:
        """テキストから Julia 定義を抽出"""
        clean = self._strip_repl_prompts(text)
        defs: List[JuliaDefinition] = []
        seen_names: Set[str] = set()

        # struct / mutable struct
        for m in self._RE_STRUCT.finditer(clean):
            name = m.group(2)
            if name not in seen_names:
                kind = (DefinitionKind.MUTABLE_STRUCT
                        if m.group(1).strip().startswith('mutable')
                        else DefinitionKind.STRUCT)
                defs.append(JuliaDefinition(
                    kind=kind, name=name, source=m.group(1).strip(), phase=phase,
                ))
                seen_names.add(name)

        # abstract type
        for m in self._RE_ABSTRACT.finditer(clean):
            name = m.group(2)
            if name not in seen_names:
                defs.append(JuliaDefinition(
                    kind=DefinitionKind.ABSTRACT_TYPE,
                    name=name, source=m.group(1).strip(), phase=phase,
                ))
                seen_names.add(name)

        # primitive type
        for m in self._RE_PRIMITIVE.finditer(clean):
            name = m.group(2)
            if name not in seen_names:
                defs.append(JuliaDefinition(
                    kind=DefinitionKind.PRIMITIVE_TYPE,
                    name=name, source=m.group(1).strip(), phase=phase,
                ))
                seen_names.add(name)

        # const
        for m in self._RE_CONST.finditer(clean):
            name = m.group(2)
            if name not in seen_names:
                defs.append(JuliaDefinition(
                    kind=DefinitionKind.CONST,
                    name=name, source=m.group(1).strip(), phase=phase,
                ))
                seen_names.add(name)

        # function signature
        for m in self._RE_FUNC_SIG.finditer(clean):
            name = m.group(2)
            if name not in seen_names:
                defs.append(JuliaDefinition(
                    kind=DefinitionKind.FUNCTION_SIGNATURE,
                    name=name, source=m.group(1).strip(), phase=phase,
                ))
                seen_names.add(name)

        return defs


# ---------------------------------------------------------------------------
# 記憶ストア
# ---------------------------------------------------------------------------

@dataclass
class AreMemory:
    """
    稗田阿礼の記憶 — Phase横断の定義記憶

    名前でデデュプし、同名の定義は後の Phase のもので上書き。
    """
    definitions: List[JuliaDefinition] = field(default_factory=list)
    _by_name: Dict[str, JuliaDefinition] = field(default_factory=dict)

    def memorize(self, new_defs: List[JuliaDefinition]):
        """定義を記憶（同名は上書き）"""
        for d in new_defs:
            self._by_name[d.name] = d
        self.definitions = list(self._by_name.values())

    def recall(self, phases: Optional[List[int]] = None) -> List[JuliaDefinition]:
        """指定 Phase の定義を優先度順で返す"""
        if phases is None:
            defs = self.definitions
        else:
            phase_set = set(phases)
            defs = [d for d in self.definitions if d.phase in phase_set]
        return sorted(defs, key=lambda d: d.priority)

    def clear(self):
        """リセット"""
        self.definitions.clear()
        self._by_name.clear()


# ---------------------------------------------------------------------------
# 誦習フォーマッター
# ---------------------------------------------------------------------------

class ShoujuFormatter:
    """
    誦習（しょうじゅう）フォーマッター

    定義を REPL 形式のコンテキストに変換する。
    MoE モデルは REPL データで訓練されているため、
    「julia>」プロンプト形式で再注入する。

    訓練データ形式 (kuniumi_repl_gen.py の format_repl に準拠):
        julia> struct Point2D
            x::Float64
            y::Float64
        end

        julia> function distance(p1::Point2D, p2::Point2D)
    """

    REPL_PROMPT = "julia> "

    def _format_single(self, defn: JuliaDefinition) -> str:
        """単一の定義を REPL 形式に整形"""
        lines = defn.source.split('\n')
        parts = []
        for i, line in enumerate(lines):
            if i == 0:
                parts.append(f"{self.REPL_PROMPT}{line}")
            else:
                parts.append(line)
        return '\n'.join(parts)

    def format_recitation(
        self,
        definitions: List[JuliaDefinition],
        tokenizer=None,
        max_tokens_hint: int = 512,
    ) -> str:
        """
        定義を REPL 誦習プロンプトに整形

        優先度順に追加し、トークン予算を超えたら打ち切り。
        tokenizer が渡された場合は正確なトークン数を計算、
        なければ単語数で概算する。
        """
        sorted_defs = sorted(definitions, key=lambda d: d.priority)

        parts: List[str] = []
        estimated_tokens = 0

        for defn in sorted_defs:
            formatted = self._format_single(defn)

            if tokenizer is not None:
                est = len(tokenizer.encode(formatted, add_special_tokens=False))
            else:
                est = len(formatted.split())

            if estimated_tokens + est > max_tokens_hint and parts:
                break
            parts.append(formatted)
            estimated_tokens += est

        return '\n\n'.join(parts)


# ---------------------------------------------------------------------------
# 稗田阿礼 メインクラス
# ---------------------------------------------------------------------------

class HiedaNoAre:
    """
    稗田阿礼 — 外部コンテキスト管理器

    古事記を口伝した稗田阿礼のように、
    生成された定義を記憶し、各Phase開始時に誦習する。

    Args:
        tokenizer: JuliaTokenizer (トークン数計算用、Noneでも動作)
        max_context_tokens: 誦習に使う最大トークン数
    """

    def __init__(
        self,
        tokenizer=None,
        max_context_tokens: int = 512,
    ):
        self.tokenizer = tokenizer
        self.max_context_tokens = max_context_tokens
        self.memory = AreMemory()
        self.parser = JuliaDefinitionParser()
        self.formatter = ShoujuFormatter()

    def memorize_output(self, text: str, phase: int) -> List[JuliaDefinition]:
        """Phase の生成結果を記憶"""
        definitions = self.parser.parse(text, phase)
        self.memory.memorize(definitions)
        return definitions

    def memorize_prompt(self, text: str) -> List[JuliaDefinition]:
        """ユーザープロンプト中の定義を記憶 (phase=-1)"""
        definitions = self.parser.parse(text, phase=-1)
        self.memory.memorize(definitions)
        return definitions

    def build_recitation(
        self,
        target_phase: int,
        generation_prompt: str = "",
    ) -> str:
        """
        target_phase 用の誦習プロンプトを構築

        Phase 0 (IZANAGI): 誦習なし — ユーザープロンプトのみ
        Phase 1 (IZANAMI): Phase 0 の struct/type 定義を誦習
        Phase 2 (KAMIYUMI): Phase 0+1 の全定義を誦習
        """
        if target_phase == 0:
            return generation_prompt

        # 誦習対象のPhaseを決定
        recall_phases = list(range(target_phase))
        # ユーザープロンプト由来 (phase=-1) も含める
        recall_phases.append(-1)

        definitions = self.memory.recall(phases=recall_phases)

        if not definitions:
            return generation_prompt

        recitation = self.formatter.format_recitation(
            definitions,
            tokenizer=self.tokenizer,
            max_tokens_hint=self.max_context_tokens,
        )

        if generation_prompt:
            return recitation + "\n\n" + generation_prompt
        return recitation

    def reset(self):
        """新しい生成セッション用にリセット"""
        self.memory.clear()

    def get_kotonodama(self, boost: float = 10.0) -> Optional["KotonodamaProcessor"]:
        """
        記憶された定義名から言霊プロセッサを生成

        阿礼が記憶した構造体名・関数名をブースト対象にする。
        """
        if not self.tokenizer or not self.memory.definitions:
            return None
        names = [d.name for d in self.memory.definitions]
        return KotonodamaProcessor(self.tokenizer, names, boost=boost)

    def get_contextual_kotonodama(
        self, boost: float = 20.0, ban: float = 50.0,
    ) -> Optional["ContextualKotonodamaProcessor"]:
        """
        記憶された定義名から文脈依存型言霊プロセッサを生成

        各定義名をBPEトークン列に分解し、隣接トークン間のルールを自動構築。
        例: "Point2D" = [P(52), o(83), int(1007), 2(22), D(40)]

        "int"(1007)の後に"2"(22)が来るべき箇所で:
          - "2"(22) を +boost
          - 他の数字トークンを -ban (Point3D等への変異を防止)

        Returns:
            ContextualKotonodamaProcessor or None
        """
        if not self.tokenizer or not self.memory.definitions:
            return None

        # 数字トークンのID (0-9) を取得
        digit_ids = {}
        for digit in "0123456789":
            ids = self.tokenizer.encode(digit, add_special_tokens=False)
            if ids:
                digit_ids[digit] = ids[0]

        rules: List[KotonodamaRule] = []
        seen_rules: Set[tuple] = set()  # 重複防止

        for defn in self.memory.definitions:
            token_ids = self.tokenizer.encode(defn.name, add_special_tokens=False)
            if len(token_ids) < 2:
                continue

            # 隣接トークンペアをスキャンして数字トークンを検出
            for i in range(1, len(token_ids)):
                current_id = token_ids[i]
                prev_id = token_ids[i - 1]

                # current_id が数字トークンの場合、ルールを構築
                current_digit = None
                for d, did in digit_ids.items():
                    if did == current_id:
                        current_digit = d
                        break

                if current_digit is not None:
                    rule_key = (prev_id, current_id)
                    if rule_key in seen_rules:
                        continue
                    seen_rules.add(rule_key)

                    # この数字以外の数字をバン対象に
                    ban_ids = set()
                    for d, did in digit_ids.items():
                        if did != current_id:
                            ban_ids.add(did)

                    rules.append(KotonodamaRule(
                        trigger_token_ids={prev_id},
                        boost_token_ids={current_id},
                        ban_token_ids=ban_ids,
                        boost_val=boost,
                        ban_val=ban,
                    ))

        if not rules:
            return None

        return ContextualKotonodamaProcessor(rules=rules)

    # =========================================================================
    # 五層アーキテクチャ統合API
    # =========================================================================

    def fetch_and_contextualize(self, query: dict) -> dict:
        """
        Layer 4 → Layer 3 ブリッジ: 外部データの取得とコンテキスト化

        天御柱オーケストレータの「左旋」フェーズで呼び出される。
        クエリから関連する外部コンテキストを構築し、
        推論ランタイムに注入可能な形式で返す。

        Parameters:
            query: 推論リクエスト
                - prompt: str (必須)
                - constraints: dict (オプション)
                - session_context: dict (オプション、過去セッション情報)

        Returns:
            dict: コンテキスト化されたデータ
                - recitation: str (誦習プロンプト)
                - kotonodama: KotonodamaProcessor (言霊プロセッサ)
                - definitions: List[JuliaDefinition] (抽出された定義)
                - source: str ("hieda_no_are")
        """
        prompt = query.get("prompt", "")
        session_context = query.get("session_context", {})

        # 1. プロンプトから定義を抽出・記憶
        prompt_definitions = self.memorize_prompt(prompt)

        # 2. セッションコンテキストから過去の定義を取り込み
        past_definitions: List[JuliaDefinition] = []
        if session_context:
            past_output = session_context.get("previous_output", "")
            if past_output:
                past_definitions = self.memorize_output(past_output, phase=-2)

        # 3. 誦習プロンプトを構築
        all_definitions = self.memory.recall()
        recitation = ""
        if all_definitions:
            recitation = self.formatter.format_recitation(
                all_definitions,
                tokenizer=self.tokenizer,
                max_tokens_hint=self.max_context_tokens,
            )

        # 4. 言霊プロセッサを取得
        kotonodama = self.get_contextual_kotonodama()

        return {
            "recitation": recitation,
            "kotonodama": kotonodama,
            "definitions": all_definitions,
            "prompt_definitions": prompt_definitions,
            "past_definitions": past_definitions,
            "source": "hieda_no_are",
        }

    def get_layer4_status(self) -> dict:
        """
        Layer 4 (海原・常世) の現在のステータスを取得

        Returns:
            dict: ステータス情報
                - memory_count: int (記憶している定義数)
                - definition_names: List[str] (定義名リスト)
                - has_tokenizer: bool
        """
        return {
            "memory_count": len(self.memory.definitions),
            "definition_names": [d.name for d in self.memory.definitions],
            "has_tokenizer": self.tokenizer is not None,
            "max_context_tokens": self.max_context_tokens,
        }


# ---------------------------------------------------------------------------
# 言霊 (Kotonodama) — Logitsブーストプロセッサ
# ---------------------------------------------------------------------------

class KotonodamaProcessor:
    """
    言霊（ことのだま）— 生成時のLogitsブースト

    阿礼が記憶した定義名（構造体名、関数名等）を構成するサブワードの
    logitsスコアをブーストし、訓練データの強いpriorに対抗する。

    例: "Point2D" が ["P", "o", "int", "2", "D"] にトークン化される場合、
    これら全てのトークンIDのスコアを +boost する。

    Args:
        tokenizer: JuliaTokenizer
        target_words: ブースト対象の単語リスト
        boost: スコア加算量 (デフォルト 10.0)
    """

    def __init__(self, tokenizer, target_words: List[str], boost: float = 10.0):
        self.boost = boost
        self.target_ids: Set[int] = set()

        for word in target_words:
            ids = tokenizer.encode(word, add_special_tokens=False)
            self.target_ids.update(ids)

    def apply(self, logits: "torch.Tensor", last_token_id: Optional[int] = None) -> "torch.Tensor":
        """
        logits [batch, vocab_size] にブーストを適用

        生成ループ内で temperature 適用後、サンプリング前に呼ぶ。
        """
        for tid in self.target_ids:
            if tid < logits.size(-1):
                logits[:, tid] += self.boost
        return logits


# ---------------------------------------------------------------------------
# 文脈依存型・言霊 (Contextual Kotonodama) — トリガーベースLogitsプロセッサ
# ---------------------------------------------------------------------------

@dataclass
class KotonodamaRule:
    """
    文脈依存型言霊ルール

    trigger_token_ids のいずれかが直前トークンの場合に発動。
    boost_token_ids のlogitsを +boost_val、
    ban_token_ids のlogitsを -ban_val する。
    """
    trigger_token_ids: Set[int]
    boost_token_ids: Set[int]
    ban_token_ids: Set[int]
    boost_val: float = 20.0
    ban_val: float = 50.0


class ContextualKotonodamaProcessor:
    """
    文脈依存型・言霊（ことのだま）— トリガーベースLogitsプロセッサ

    直前トークンを確認し、特定の文脈でのみブースト/バンを行う。
    BPEサブワードの副作用（数値リテラルへの干渉）を防止する。

    例: "Point2D" = [P(52), o(83), int(1007), 2(22), D(40)]
        "Point3D" = [P(52), o(83), int(1007), 3(23), D(40)]

    ルール: 直前が "int"(1007) → "2"(22)をブースト、"3"(23)をバン
    → "2.0" や "3.14" 等の数値リテラルには干渉しない
      (これらは "int" の直後には出現しないため)

    Args:
        rules: KotonodamaRule のリスト
    """

    def __init__(self, rules: List[KotonodamaRule]):
        self.rules = rules

    def apply(self, logits: "torch.Tensor", last_token_id: Optional[int] = None) -> "torch.Tensor":
        """
        logits [batch, vocab_size] に文脈依存ブースト/バンを適用

        Args:
            logits: [batch, vocab_size] のlogitsテンソル
            last_token_id: 直前に生成されたトークンID (Noneなら何もしない)
        """
        if last_token_id is None:
            return logits

        vocab_size = logits.size(-1)

        for rule in self.rules:
            if last_token_id in rule.trigger_token_ids:
                for tid in rule.boost_token_ids:
                    if tid < vocab_size:
                        logits[:, tid] += rule.boost_val
                for tid in rule.ban_token_ids:
                    if tid < vocab_size:
                        logits[:, tid] -= rule.ban_val

        return logits
