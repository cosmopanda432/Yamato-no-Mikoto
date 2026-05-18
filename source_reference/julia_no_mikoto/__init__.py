"""
Julia-no-Mikoto: コード生成層（古事記アーキテクチャ）

古事記の神話構造をJulia言語の型システム・多重ディスパッチにマッピング。
yamatoLLM の3層アーキテクチャにおけるコード生成層を担う。

=== モデル内部層（layers.py）===
    第一章: 天地開闢層 (Genesis) - Embeddings
    第二章: 神世七代層 (SevenGenerations) - Transformer Blocks
    第三章: 国生み層 (Kuniumi) - Struct Generation
    第四章: 黄泉国層 (Yomi) - Type Instability Detection
    第五章: 禊層 (Misogi) - Output Heads

=== パイプライン層 ===
    造化三神: 横断プロセス (zoka_sanshin.py)
    天御柱: オーケストレータ (amenomihashira.py)
    葦原中国: 推論ランタイム (ashihara_runtime.py)
    稗田阿礼: 外部メモリ (hieda_no_are.py)
    黄泉比良坂: 評価ゲートウェイ (yomotsu_hirasaka.py)
"""

from .config import (
    KojikiConfig,
    TokenRole,
    TYPE_CATEGORIES,
    TYPE_ID_TO_NAME,
    TYPE_NAME_TO_ID,
    TYPE_SPECIFICITY,
    TYPE_DEPTH,
    DEFAULT_CONFIG,
    TrustLevel,
    VerdictType,
    FeedbackType,
    TrainingPriority,
    FiveLayerConfig,
    DEFAULT_FIVE_LAYER_CONFIG,
)

from .model import KojikiLM, create_model

from .layers import (
    GenesisLayer,
    AmenominakanushiPositionalEncoding,
    TakamimusubiTokenEmbedding,
    KamimusubiTypeHierarchyEmbedding,
    SevenGenerationsStack,
    SevenGenerationsBlock,
    KuninotokotachiSelfAttention,
    ToyokumoFeedForward,
    MultipleDispatchAttention,
    KuniumiLayer,
    YomiLayer,
    MisogiLayer,
    AmaterasuTokenHead,
    TsukuyomiTypeHead,
    SusanooErrorHead,
)

from .yata_kagami_attention import YataKagamiAttention
from .definition_detector import DefinitionDetector

from .moe import (
    KojikiMoE,
    create_moe_model,
    MoEBlock,
    MoEFeedForward,
    MoERouter,
)

from .training import (
    KojikiLoss,
    Trainer,
    create_optimizer,
    get_cosine_schedule_with_warmup,
    create_dummy_batch,
)

from .amenomihashira import (
    GenerationPhase,
    HirukoValidator,
    NaobiValidator,
    AmenomihashiraGenerator,
    AmenomihashiraResult,
    PhaseResult,
    HirukoReport,
    NaobiReport,
    AmeNoMihashira,
    PipelinePhase,
    PipelineResult,
)

from .hieda_no_are import (
    HiedaNoAre,
    JuliaDefinitionParser,
    ShoujuFormatter,
    AreMemory,
    JuliaDefinition,
    DefinitionKind,
    KotonodamaProcessor,
    ContextualKotonodamaProcessor,
    KotonodamaRule,
)

from .zoka_sanshin import (
    AmeNoMinakaNushi,
    TakamiMusubi,
    KamiMusubi,
    ForwardPassTicket,
    RepairTicket,
    TicketStatus,
)

from .yomi_evaluator import (
    YomiEvaluator,
    HirukoDetector,
    HirukoReport as YomiHirukoReport,
    EnmaGate,
    EnmaVerdict,
    YomiArchive,
    YomiRecord,
    Verdict,
)

from .yomotsu_hirasaka import (
    YomotsuHirasaka,
    AuditLogEntry,
)

from .layer4_unabara import (
    Layer4Gateway,
    Tokoyo,
    Unabara,
    Watatsumi,
    ExternalData,
)

from .ashihara_runtime import (
    AshiharaRuntime,
    GenerationResult,
    PipelineOutput,
)

from .takamagahara_feedback import (
    TakamagaharaFeedback,
    FeedbackPipeline,
    TrainingSignal,
    QualityTrendTracker,
    ErrorPatternAnalyzer,
)
