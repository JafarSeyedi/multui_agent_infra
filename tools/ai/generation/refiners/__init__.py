from .base_refiner import RefinementScope, ChangeType, RefinementContext, RefinementResult, BaseRefiner, SafetyCheck
from .feedback_loop import FeedbackType, FeedbackSeverity, LearningMode, PatternType, FeedbackItem, LearnedPattern, FeedbackSession, FeedbackLoopConfig, FeedbackStorage, PatternLearner, FeedbackLoop, main
from .functionality_preserver import FunctionalitySignature, FunctionalityPreserver
from .impact_analyzer import ImpactSeverity, ImpactType, ChangeCategory, ChangeInfo, ImpactedArtifact, BreakingChange, ImpactAnalysisResult, ImpactAnalyzerConfig, ChangeDetector, ImpactCalculator, ImpactAnalyzer, main
from .iterative_refiner import RefinementStrategy, ErrorCategory, RefinementPhase, ValidationError, RefinementStep, RefinementSession, RefinerConfig, ErrorParser, CodeAnalyzer, AIRefiner, AutoFixer, IterativeRefiner, main
from .scope_manager import ScopeBoundary, ScopeManager
