# 📐 Architecture Report

> تولید شده توسط `tools/analyze_architecture.py`  
> تاریخ: 2026-04-11 00:25:51  
---

## 📊 آمار کلی

| معیار | مقدار |
|-------|-------|
| فایل‌های Python | 233 |
| کلاس‌ها | 492 |
| توابع سطح بالا | 63 |
| فایل‌های با خطا | 0 |

---

## 📂 ساختار فولدرها

```
📦 project/
  ├── 📁 agents/
  │   ├── 📁 base_agents/
  │   ├── 📁 buses/
  │   ├── 📁 content/
  │   │   └── 📁 models/
  │   └── 📁 interaction/
  │       └── 📁 backends/
  ├── 📁 config/
  ├── 📁 migrations/
  ├── 📁 rag/
  │   ├── 📁 agentic/
  │   ├── 📁 compression/
  │   ├── 📁 evidence/
  │   ├── 📁 explain/
  │   ├── 📁 graph/
  │   ├── 📁 learning/
  │   ├── 📁 llm/
  │   ├── 📁 planner/
  │   ├── 📁 reflection/
  │   ├── 📁 reranking/
  │   ├── 📁 research/
  │   │   ├── 📁 autonomous/
  │   │   ├── 📁 dashboard/
  │   │   ├── 📁 evaluation/
  │   │   ├── 📁 graph/
  │   │   ├── 📁 guardrails/
  │   │   ├── 📁 improvement/
  │   │   ├── 📁 memory/
  │   │   │   └── 📁 reasoning/
  │   │   ├── 📁 observability/
  │   │   └── 📁 summarization/
  │   ├── 📁 retrieval/
  │   ├── 📁 services/
  │   └── 📁 trainer/
  ├── 📁 storage/
  │   ├── 📁 backends/
  │   │   └── 📁 redis/
  │   └── 📁 vector/
  │       └── 📁 backends/
  ├── 📁 tests/
  │   └── 📁 agents/
  │       ├── 📁 agents_unit/
  │       ├── 📁 interaction/
  │       │   ├── 📁 interaction_performance/
  │       │   └── 📁 interaction_unit/
  │       └── 📁 orchestration/
  │           ├── 📁 orchestration_performance/
  │           └── 📁 orchestration_unit/
  └── 📁 tools/
```

---

## 🗂️ ساختار کامل (فولدرها + فایل‌ها)

```
📦 project/
  ├── 📁 agents/
  │   ├── 📁 base_agents/
  │   │   ├── 📄 __init__.py
  │   │   ├── 📄 agent_registry.py
  │   │   ├── 📄 base_agent.py
  │   │   ├── 📄 models.py
  │   │   └── 📄 interaction_agent.py
  │   ├── 📁 buses/
  │   │   ├── 📄 __init__.py
  │   │   ├── 📄 base.py
  │   │   ├── 📄 durable_message_bus.py
  │   │   ├── 📄 in_memory_message_bus.py
  │   │   ├── 📄 kafka_bus.py
  │   │   ├── 📄 priority_message_bus.py
  │   │   ├── 📄 rabbitmq_bus.py
  │   │   ├── 📄 redis_pub_sub_bus.py
  │   │   ├── 📄 request_reply_bus.py
  │   │   └── 📄 topic_message_bus.py
  │   ├── 📁 content/
  │   │   ├── 📁 models/
  │   │   │   ├── 📄 __init__.py
  │   │   │   ├── 📄 analytics_agents_31_40.py
  │   │   │   ├── 📄 assessment_agents_21_30.py
  │   │   │   ├── 📄 common.py
  │   │   │   ├── 📄 content_agents_1_8.py
  │   │   │   ├── 📄 content_generation_agents_91_100.py
  │   │   │   ├── 📄 curriculum_agents_46_60.py
  │   │   │   ├── 📄 evaluation_agents_41_45.py
  │   │   │   ├── 📄 learning_objects.py
  │   │   │   ├── 📄 memory_agents_76_90.py
  │   │   │   ├── 📄 multimodal_agents_101_110.py
  │   │   │   ├── 📄 orchestration_agents_61_75.py
  │   │   │   ├── 📄 personalization_agents_15_20.py
  │   │   │   └── 📄 teaching_agents_9_14.py
  │   │   ├── 📄 __init__.py
  │   │   └── 📄 text_rewriter.py
  │   └── 📁 interaction/
  │       ├── 📁 backends/
  │       │   ├── 📄 __init__.py
  │       │   ├── 📄 autogen_backend.py
  │       │   ├── 📄 base_backend.py
  │       │   └── 📄 native_backend.py
  │       ├── 📄 __init__.py
  │       ├── 📄 base_strategy.py
  │       ├── 📄 broadcast_strategy.py
  │       ├── 📄 coordinator_strategy.py
  │       ├── 📄 debate_strategy.py
  │       ├── 📄 ensemble_strategy.py
  │       ├── 📄 group_chat_strategy.py
  │       ├── 📄 interaction_models.py
  │       ├── 📄 round_robin_strategy.py
  │       ├── 📄 self_refine_strategy.py
  │       └── 📄 strategy_registry.py
  ├── 📁 config/
  │   └── 📄 settings.py
  ├── 📁 migrations/
  │   ├── 📄 __init__.py
  │   └── 📄 env.py
  ├── 📁 rag/
  │   ├── 📁 agentic/
  │   │   ├── 📄 __init__.py
  │   │   ├── 📄 agent_v2.py
  │   │   ├── 📄 evidence_tracker.py
  │   │   ├── 📄 multihop_reasoner.py
  │   │   ├── 📄 query_decomposer.py
  │   │   ├── 📄 retrieval_agent.py
  │   │   └── 📄 uncertainty.py
  │   ├── 📁 compression/
  │   │   ├── 📄 __init__.py
  │   │   ├── 📄 base.py
  │   │   ├── 📄 embedding_compressor.py
  │   │   └── 📄 llm_compressor.py
  │   ├── 📁 evidence/
  │   │   ├── 📄 __init__.py
  │   │   └── 📄 evidence_clusterer.py
  │   ├── 📁 explain/
  │   │   ├── 📄 __init__.py
  │   │   └── 📄 retrieval_explainer.py
  │   ├── 📁 graph/
  │   │   ├── 📄 __init__.py
  │   │   ├── 📄 graph_builder.py
  │   │   ├── 📄 graph_models.py
  │   │   ├── 📄 graph_retriever.py
  │   │   └── 📄 graph_store.py
  │   ├── 📁 learning/
  │   │   ├── 📄 __init__.py
  │   │   └── 📄 retrieval_policy.py
  │   ├── 📁 llm/
  │   │   ├── 📄 __init__.py
  │   │   ├── 📄 base_llm.py
  │   │   ├── 📄 llm_factory.py
  │   │   ├── 📄 llm_protocols.py
  │   │   ├── 📄 ollama_llm.py
  │   │   └── 📄 openai_llm.py
  │   ├── 📁 planner/
  │   │   ├── 📄 __init__.py
  │   │   ├── 📄 adaptive_planner.py
  │   │   └── 📄 retrieval_plan.py
  │   ├── 📁 reflection/
  │   │   ├── 📄 __init__.py
  │   │   ├── 📄 reflection_critic.py
  │   │   └── 📄 reflection_loop.py
  │   ├── 📁 reranking/
  │   │   ├── 📄 __init__.py
  │   │   ├── 📄 base_reranker.py
  │   │   └── 📄 reranker.py
  │   ├── 📁 research/
  │   │   ├── 📁 autonomous/
  │   │   │   ├── 📄 __init__.py
  │   │   │   ├── 📄 coverage_scorer.py
  │   │   │   ├── 📄 gap_detector.py
  │   │   │   ├── 📄 query_generator.py
  │   │   │   └── 📄 research_loop.py
  │   │   ├── 📁 dashboard/
  │   │   │   ├── 📄 __init__.py
  │   │   │   ├── 📄 api_server.py
  │   │   │   ├── 📄 schema.py
  │   │   │   └── 📄 websocket_stream.py
  │   │   ├── 📁 evaluation/
  │   │   │   ├── 📄 __init__.py
  │   │   │   ├── 📄 citation_evaluator.py
  │   │   │   ├── 📄 completeness_evaluator.py
  │   │   │   ├── 📄 coverage_scorer.py
  │   │   │   ├── 📄 evaluation_controller.py
  │   │   │   ├── 📄 hallucination_detector.py
  │   │   │   ├── 📄 improvement_engine.py
  │   │   │   ├── 📄 reasoning_evaluator.py
  │   │   │   ├── 📄 retrieval_evaluator.py
  │   │   │   └── 📄 schema.py
  │   │   ├── 📁 graph/
  │   │   │   ├── 📄 __init__.py
  │   │   │   ├── 📄 entity_extractor.py
  │   │   │   ├── 📄 graph_aware_planner.py
  │   │   │   ├── 📄 graph_canonicalizer.py
  │   │   │   ├── 📄 graph_index.py
  │   │   │   ├── 📄 graph_persistence.py
  │   │   │   ├── 📄 graph_traverser.py
  │   │   │   ├── 📄 relation_builder.py
  │   │   │   └── 📄 relation_ranker.py
  │   │   ├── 📁 guardrails/
  │   │   │   ├── 📄 __init__.py
  │   │   │   └── 📄 hallucination_guard.py
  │   │   ├── 📁 improvement/
  │   │   │   ├── 📄 __init__.py
  │   │   │   └── 📄 feedback_controller.py
  │   │   ├── 📁 memory/
  │   │   │   ├── 📁 reasoning/
  │   │   │   │   ├── 📄 __init__.py
  │   │   │   │   ├── 📄 event_types.py
  │   │   │   │   ├── 📄 reasoning_event.py
  │   │   │   │   ├── 📄 reasoning_exporter.py
  │   │   │   │   ├── 📄 reasoning_memory.py
  │   │   │   │   ├── 📄 reasoning_node.py
  │   │   │   │   ├── 📄 reasoning_recorder.py
  │   │   │   │   └── 📄 reasoning_tree.py
  │   │   │   ├── 📄 __init__.py
  │   │   │   ├── 📄 memory_controller.py
  │   │   │   ├── 📄 memory_retriever.py
  │   │   │   ├── 📄 memory_store.py
  │   │   │   ├── 📄 reasoning_memory.py
  │   │   │   └── 📄 temporal_graph.py
  │   │   ├── 📁 observability/
  │   │   │   ├── 📄 __init__.py
  │   │   │   ├── 📄 failure_analyzer.py
  │   │   │   ├── 📄 graph_visualizer.py
  │   │   │   ├── 📄 memory_usage_tracker.py
  │   │   │   ├── 📄 metrics_store.py
  │   │   │   ├── 📄 observability_controller.py
  │   │   │   ├── 📄 retrieval_heatmap.py
  │   │   │   ├── 📄 telemetry.py
  │   │   │   ├── 📄 token_tracker.py
  │   │   │   └── 📄 trace_collector.py
  │   │   ├── 📁 summarization/
  │   │   │   ├── 📄 __init__.py
  │   │   │   ├── 📄 base_summarizer.py
  │   │   │   ├── 📄 research_summarizer.py
  │   │   │   └── 📄 section_summarizer.py
  │   │   ├── 📄 __init__.py
  │   │   ├── 📄 answer_planner.py
  │   │   ├── 📄 base_research_agent.py
  │   │   ├── 📄 citation_manager.py
  │   │   └── 📄 research_agent.py
  │   ├── 📁 retrieval/
  │   │   ├── 📄 __init__.py
  │   │   ├── 📄 base_retriever.py
  │   │   ├── 📄 bm25_retriever.py
  │   │   ├── 📄 hybrid_retriever.py
  │   │   ├── 📄 hybrid_retriever_plus.py
  │   │   ├── 📄 hybrid_retriever_super.py
  │   │   ├── 📄 keyword_retriever.py
  │   │   ├── 📄 retrieval_feedback_buffer.py
  │   │   ├── 📄 retriever_result.py
  │   │   ├── 📄 retriever_trainer.py
  │   │   ├── 📄 topk_optimizer.py
  │   │   ├── 📄 vector_retriever.py
  │   │   └── 📄 weight_manager.py
  │   ├── 📁 services/
  │   │   ├── 📄 __init__.py
  │   │   ├── 📄 chunking.py
  │   │   ├── 📄 embedding.py
  │   │   └── 📄 query_rewriter.py
  │   ├── 📁 trainer/
  │   │   ├── 📄 __init__.py
  │   │   ├── 📄 base_trainer.py
  │   │   ├── 📄 fusion_trainer.py
  │   │   └── 📄 reranker_trainer.py
  │   ├── 📄 __init__.py
  │   ├── 📄 rag_models.py
  │   └── 📄 vector_service.py
  ├── 📁 storage/
  │   ├── 📁 backends/
  │   │   ├── 📁 redis/
  │   │   │   ├── 📄 __init__.py
  │   │   │   ├── 📄 connection.py
  │   │   │   ├── 📄 storage_adapter.py
  │   │   │   └── 📄 stream_adapter.py
  │   │   ├── 📄 __init__.py
  │   │   ├── 📄 file_adapter.py
  │   │   └── 📄 sql_storage.py
  │   ├── 📁 vector/
  │   │   ├── 📁 backends/
  │   │   │   ├── 📄 __init__.py
  │   │   │   ├── 📄 chroma_adapter.py
  │   │   │   ├── 📄 faiss_adapter.py
  │   │   │   ├── 📄 memory_adapter.py
  │   │   │   ├── 📄 pinecone_adapter.py
  │   │   │   ├── 📄 qdrant_adapter.py
  │   │   │   └── 📄 weaviate_adapter.py
  │   │   ├── 📄 __init__.py
  │   │   ├── 📄 base.py
  │   │   ├── 📄 embedding_utils.py
  │   │   └── 📄 index_config.py
  │   ├── 📄 __init__.py
  │   ├── 📄 base_storage.py
  │   ├── 📄 document_store.py
  │   └── 📄 log_storage.py
  ├── 📁 tests/
  │   ├── 📁 agents/
  │   │   ├── 📁 agents_unit/
  │   │   │   ├── 📄 __init__.py
  │   │   │   ├── 📄 test_agent_registry.py
  │   │   │   ├── 📄 test_base_agent.py
  │   │   │   └── 📄 test_message_bus.py
  │   │   ├── 📁 interaction/
  │   │   │   ├── 📁 interaction_performance/
  │   │   │   │   ├── 📄 __init__.py
  │   │   │   │   ├── 📄 conftest_performance.py
  │   │   │   │   ├── 📄 test_broadcast_strategy_performance.py
  │   │   │   │   ├── 📄 test_coordinator_strategy_performance.py
  │   │   │   │   ├── 📄 test_debate_strategy_performance.py
  │   │   │   │   ├── 📄 test_ensemble_strategy_performance.py
  │   │   │   │   ├── 📄 test_group_chat_strategy_performance.py
  │   │   │   │   └── 📄 test_self_refine_strategy_performance.py
  │   │   │   ├── 📁 interaction_unit/
  │   │   │   │   ├── 📄 __init__.py
  │   │   │   │   ├── 📄 conftest.py
  │   │   │   │   ├── 📄 test_broadcast_strategy.py
  │   │   │   │   ├── 📄 test_coordinator_strategy.py
  │   │   │   │   ├── 📄 test_debate_strategy.py
  │   │   │   │   ├── 📄 test_ensemble_strategy.py
  │   │   │   │   ├── 📄 test_group_chat_strategy.py
  │   │   │   │   └── 📄 test_self_refine_strategy.py
  │   │   │   └── 📄 __init__.py
  │   │   ├── 📁 orchestration/
  │   │   │   ├── 📁 orchestration_performance/
  │   │   │   │   ├── 📄 __init__.py
  │   │   │   │   ├── 📄 test_native_orchestration_backend_performance.py
  │   │   │   │   └── 📄 test_interaction_agent_performance.py
  │   │   │   ├── 📁 orchestration_unit/
  │   │   │   │   ├── 📄 __init__.py
  │   │   │   │   ├── 📄 test_autogen_orchestration_backend.py
  │   │   │   │   ├── 📄 test_models.py
  │   │   │   │   ├── 📄 test_native_orchestration_backend.py
  │   │   │   │   └── 📄 test_interaction_agent.py
  │   │   │   └── 📄 __init__.py
  │   │   └── 📄 __init__.py
  │   └── 📄 __init__.py
  └── 📁 tools/
      ├── 📄 __init__.py
      ├── 📄 analyze_architecture.py
      ├── 📄 code_auditor.py
      └── 📄 generate_inits.py
```

---

## 🏛️ کلاس‌ها و وراثت

### جدول کامل کلاس‌ها

| فایل | کلاس | والدین | متدها |
|------|------|--------|-------|
| `agents/base_agents/agent_registry.py` | `AgentRegistry` | `—` | `__init__, register, get, run` |
| `agents/base_agents/base_agent.py` | `BaseAgent` | `Generic[TInput, TOutput]` | `__init__, run, run_sync, execute, _validate_input, _validate_output ...` |
| `agents/base_agents/models.py` | `AgentInput` | `BaseModel` | `` |
| `agents/base_agents/models.py` | `AgentOutput` | `BaseModel` | `` |
| `agents/base_agents/models.py` | `AgentExecutionRecord` | `BaseModel` | `` |
| `agents/base_agents/interaction_agent.py` | `InteractionAgent` | `BaseAgent` | `__init__, run` |
| `agents/buses/base.py` | `MessageBus` | `ABC` | `publish, subscribe, unsubscribe, start, stop` |
| `agents/buses/durable_message_bus.py` | `DurableMessageBus` | `MessageBus` | `__init__, subscribe, unsubscribe, publish, _consume` |
| `agents/buses/in_memory_message_bus.py` | `InMemoryMessageBus` | `MessageBus` | `__init__, subscribe, unsubscribe, publish` |
| `agents/buses/kafka_bus.py` | `KafkaMessageBus` | `MessageBus` | `__init__, start, stop, subscribe, unsubscribe, publish ...` |
| `agents/buses/priority_message_bus.py` | `PrioritizedMessage` | `—` | `` |
| `agents/buses/priority_message_bus.py` | `PriorityMessageBus` | `MessageBus` | `__init__, start, stop, subscribe, unsubscribe, publish ...` |
| `agents/buses/rabbitmq_bus.py` | `RabbitMQMessageBus` | `MessageBus` | `__init__, start, stop, subscribe, unsubscribe, publish ...` |
| `agents/buses/redis_pub_sub_bus.py` | `RedisMessageBus` | `MessageBus` | `__init__, start, stop, subscribe, unsubscribe, publish ...` |
| `agents/buses/request_reply_bus.py` | `RequestReplyBus` | `MessageBus` | `__init__, subscribe, unsubscribe, publish, request` |
| `agents/buses/topic_message_bus.py` | `TopicMessageBus` | `MessageBus` | `__init__, subscribe, unsubscribe, publish` |
| `agents/content/models/analytics_agents_31_40.py` | `StudentBehaviorAnalysisInput` | `AgentInput` | `` |
| `agents/content/models/analytics_agents_31_40.py` | `BehaviorPattern` | `BaseModel` | `` |
| `agents/content/models/analytics_agents_31_40.py` | `StudentBehaviorAnalysisOutput` | `AgentOutput` | `` |
| `agents/content/models/analytics_agents_31_40.py` | `EngagementDetectionInput` | `AgentInput` | `` |
| `agents/content/models/analytics_agents_31_40.py` | `EngagementDetectionOutput` | `AgentOutput` | `` |
| `agents/content/models/analytics_agents_31_40.py` | `MotivationAnalysisInput` | `AgentInput` | `` |
| `agents/content/models/analytics_agents_31_40.py` | `MotivationAnalysisOutput` | `AgentOutput` | `` |
| `agents/content/models/analytics_agents_31_40.py` | `DropoutRiskPredictionInput` | `AgentInput` | `` |
| `agents/content/models/analytics_agents_31_40.py` | `DropoutRiskPredictionOutput` | `AgentOutput` | `` |
| `agents/content/models/analytics_agents_31_40.py` | `StudyPatternMiningInput` | `AgentInput` | `` |
| `agents/content/models/analytics_agents_31_40.py` | `StudyPattern` | `BaseModel` | `` |
| `agents/content/models/analytics_agents_31_40.py` | `StudyPatternMiningOutput` | `AgentOutput` | `` |
| `agents/content/models/analytics_agents_31_40.py` | `PerformanceTrendAnalysisInput` | `AgentInput` | `` |
| `agents/content/models/analytics_agents_31_40.py` | `PerformanceTrend` | `BaseModel` | `` |
| `agents/content/models/analytics_agents_31_40.py` | `PerformanceTrendAnalysisOutput` | `AgentOutput` | `` |
| `agents/content/models/analytics_agents_31_40.py` | `LearningOutcomePredictionInput` | `AgentInput` | `` |
| `agents/content/models/analytics_agents_31_40.py` | `LearningOutcomePredictionOutput` | `AgentOutput` | `` |
| `agents/content/models/analytics_agents_31_40.py` | `ClassroomAnalyticsInput` | `AgentInput` | `` |
| `agents/content/models/analytics_agents_31_40.py` | `ClassroomAnalyticsOutput` | `AgentOutput` | `` |
| `agents/content/models/analytics_agents_31_40.py` | `CohortComparisonInput` | `AgentInput` | `` |
| `agents/content/models/analytics_agents_31_40.py` | `CohortComparisonOutput` | `AgentOutput` | `` |
| `agents/content/models/analytics_agents_31_40.py` | `TeacherDashboardAggregationInput` | `AgentInput` | `` |
| `agents/content/models/analytics_agents_31_40.py` | `TeacherDashboardAggregationOutput` | `AgentOutput` | `` |
| `agents/content/models/assessment_agents_21_30.py` | `QuizBuilderInput` | `AgentInput` | `` |
| `agents/content/models/assessment_agents_21_30.py` | `QuizQuestion` | `BaseModel` | `` |
| `agents/content/models/assessment_agents_21_30.py` | `QuizBuilderOutput` | `AgentOutput` | `` |
| `agents/content/models/assessment_agents_21_30.py` | `AnswerEvaluationInput` | `AgentInput` | `` |
| `agents/content/models/assessment_agents_21_30.py` | `AnswerEvaluationOutput` | `AgentOutput` | `` |
| `agents/content/models/assessment_agents_21_30.py` | `FeedbackGenerationInput` | `AgentInput` | `` |
| `agents/content/models/assessment_agents_21_30.py` | `FeedbackGenerationOutput` | `AgentOutput` | `` |
| `agents/content/models/assessment_agents_21_30.py` | `RubricGenerationInput` | `AgentInput` | `` |
| `agents/content/models/assessment_agents_21_30.py` | `RubricCriterion` | `BaseModel` | `` |
| `agents/content/models/assessment_agents_21_30.py` | `RubricGenerationOutput` | `AgentOutput` | `` |
| `agents/content/models/assessment_agents_21_30.py` | `MisconceptionAnalysisInput` | `AgentInput` | `` |
| `agents/content/models/assessment_agents_21_30.py` | `MisconceptionPattern` | `BaseModel` | `` |
| `agents/content/models/assessment_agents_21_30.py` | `MisconceptionAnalysisOutput` | `AgentOutput` | `` |
| `agents/content/models/assessment_agents_21_30.py` | `SkillMasteryInput` | `AgentInput` | `` |
| `agents/content/models/assessment_agents_21_30.py` | `SkillMasteryOutput` | `AgentOutput` | `` |
| `agents/content/models/assessment_agents_21_30.py` | `LearningGapInput` | `AgentInput` | `` |
| `agents/content/models/assessment_agents_21_30.py` | `LearningGap` | `BaseModel` | `` |
| `agents/content/models/assessment_agents_21_30.py` | `LearningGapOutput` | `AgentOutput` | `` |
| `agents/content/models/assessment_agents_21_30.py` | `KnowledgeGraphUpdateInput` | `AgentInput` | `` |
| `agents/content/models/assessment_agents_21_30.py` | `KnowledgeGraphUpdateOutput` | `AgentOutput` | `` |
| `agents/content/models/assessment_agents_21_30.py` | `ConceptDifficultyInput` | `AgentInput` | `` |
| `agents/content/models/assessment_agents_21_30.py` | `ConceptDifficultyOutput` | `AgentOutput` | `` |
| `agents/content/models/assessment_agents_21_30.py` | `CurriculumMappingInput` | `AgentInput` | `` |
| `agents/content/models/assessment_agents_21_30.py` | `CurriculumMapping` | `BaseModel` | `` |
| `agents/content/models/assessment_agents_21_30.py` | `CurriculumMappingOutput` | `AgentOutput` | `` |
| `agents/content/models/common.py` | `ContentVersion` | `BaseModel` | `` |
| `agents/content/models/common.py` | `ConfidenceScore` | `BaseModel` | `` |
| `agents/content/models/common.py` | `ScoreRange` | `BaseModel` | `` |
| `agents/content/models/common.py` | `Evidence` | `BaseModel` | `` |
| `agents/content/models/common.py` | `ReasoningTrace` | `BaseModel` | `` |
| `agents/content/models/common.py` | `Recommendation` | `BaseModel` | `` |
| `agents/content/models/common.py` | `ActionSuggestion` | `BaseModel` | `` |
| `agents/content/models/common.py` | `ConceptReference` | `BaseModel` | `` |
| `agents/content/models/common.py` | `ResourceReference` | `BaseModel` | `` |
| `agents/content/models/common.py` | `DetectedIssue` | `BaseModel` | `` |
| `agents/content/models/common.py` | `Pattern` | `BaseModel` | `` |
| `agents/content/models/common.py` | `Prediction` | `BaseModel` | `` |
| `agents/content/models/common.py` | `TimeWindow` | `BaseModel` | `` |
| `agents/content/models/content_agents_1_8.py` | `TextRewriteInput` | `AgentInput` | `` |
| `agents/content/models/content_agents_1_8.py` | `RewriteChange` | `BaseModel` | `` |
| `agents/content/models/content_agents_1_8.py` | `TextRewriteOutput` | `AgentOutput` | `` |
| `agents/content/models/content_agents_1_8.py` | `ContentValidationInput` | `AgentInput` | `` |
| `agents/content/models/content_agents_1_8.py` | `ValidationIssue` | `BaseModel` | `` |
| `agents/content/models/content_agents_1_8.py` | `ContentValidationOutput` | `AgentOutput` | `` |
| `agents/content/models/content_agents_1_8.py` | `CitationGenerationInput` | `AgentInput` | `` |
| `agents/content/models/content_agents_1_8.py` | `CitationEntry` | `BaseModel` | `` |
| `agents/content/models/content_agents_1_8.py` | `CitationGenerationOutput` | `AgentOutput` | `` |
| `agents/content/models/content_agents_1_8.py` | `GlossaryBuilderInput` | `AgentInput` | `` |
| `agents/content/models/content_agents_1_8.py` | `GlossaryTerm` | `BaseModel` | `` |
| `agents/content/models/content_agents_1_8.py` | `GlossaryBuilderOutput` | `AgentOutput` | `` |
| `agents/content/models/content_agents_1_8.py` | `DynamicUpdateInput` | `AgentInput` | `` |
| `agents/content/models/content_agents_1_8.py` | `ContentUpdateSuggestion` | `BaseModel` | `` |
| `agents/content/models/content_agents_1_8.py` | `DynamicUpdateOutput` | `AgentOutput` | `` |
| `agents/content/models/content_agents_1_8.py` | `NarrativeBuilderInput` | `AgentInput` | `` |
| `agents/content/models/content_agents_1_8.py` | `NarrativeElement` | `BaseModel` | `` |
| `agents/content/models/content_agents_1_8.py` | `NarrativeBuilderOutput` | `AgentOutput` | `` |
| `agents/content/models/content_agents_1_8.py` | `StructuringInput` | `AgentInput` | `` |
| `agents/content/models/content_agents_1_8.py` | `LessonSection` | `BaseModel` | `` |
| `agents/content/models/content_agents_1_8.py` | `StructuringOutput` | `AgentOutput` | `` |
| `agents/content/models/content_agents_1_8.py` | `PrerequisiteInput` | `AgentInput` | `` |
| `agents/content/models/content_agents_1_8.py` | `PrerequisiteItem` | `BaseModel` | `` |
| `agents/content/models/content_agents_1_8.py` | `PrerequisiteOutput` | `AgentOutput` | `` |
| `agents/content/models/content_generation_agents_91_100.py` | `ExampleGeneratorInput` | `AgentInput` | `` |
| `agents/content/models/content_generation_agents_91_100.py` | `ExampleGeneratorOutput` | `AgentOutput` | `` |
| `agents/content/models/content_generation_agents_91_100.py` | `ExerciseCreatorInput` | `AgentInput` | `` |
| `agents/content/models/content_generation_agents_91_100.py` | `ExerciseCreatorOutput` | `AgentOutput` | `` |
| `agents/content/models/content_generation_agents_91_100.py` | `StoryLessonCreatorInput` | `AgentInput` | `` |
| `agents/content/models/content_generation_agents_91_100.py` | `StoryLessonCreatorOutput` | `AgentOutput` | `` |
| `agents/content/models/content_generation_agents_91_100.py` | `ConceptExplanationInput` | `AgentInput` | `` |
| `agents/content/models/content_generation_agents_91_100.py` | `ConceptExplanationOutput` | `AgentOutput` | `` |
| `agents/content/models/content_generation_agents_91_100.py` | `PracticeQuestionGeneratorInput` | `AgentInput` | `` |
| `agents/content/models/content_generation_agents_91_100.py` | `PracticeQuestionGeneratorOutput` | `AgentOutput` | `` |
| `agents/content/models/content_generation_agents_91_100.py` | `AdaptiveQuestionGeneratorInput` | `AgentInput` | `` |
| `agents/content/models/content_generation_agents_91_100.py` | `AdaptiveQuestionGeneratorOutput` | `AgentOutput` | `` |
| `agents/content/models/content_generation_agents_91_100.py` | `ExplanationRewriterInput` | `AgentInput` | `` |
| `agents/content/models/content_generation_agents_91_100.py` | `ExplanationRewriterOutput` | `AgentOutput` | `` |
| `agents/content/models/content_generation_agents_91_100.py` | `SummaryGeneratorInput` | `AgentInput` | `` |
| `agents/content/models/content_generation_agents_91_100.py` | `SummaryGeneratorOutput` | `AgentOutput` | `` |
| `agents/content/models/content_generation_agents_91_100.py` | `ContentSimplifierInput` | `AgentInput` | `` |
| `agents/content/models/content_generation_agents_91_100.py` | `ContentSimplifierOutput` | `AgentOutput` | `` |
| `agents/content/models/content_generation_agents_91_100.py` | `AssessmentQuestionGeneratorInput` | `AgentInput` | `` |
| `agents/content/models/content_generation_agents_91_100.py` | `AssessmentQuestionGeneratorOutput` | `AgentOutput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `ConceptGraphBuilderInput` | `AgentInput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `ConceptGraphBuilderOutput` | `AgentOutput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `ConceptRelationExtractorInput` | `AgentInput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `ConceptRelationExtractorOutput` | `AgentOutput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `PrerequisiteInferenceInput` | `AgentInput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `PrerequisiteInferenceOutput` | `AgentOutput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `CurriculumPlannerInput` | `AgentInput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `CurriculumPlannerOutput` | `AgentOutput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `LessonSequencePlannerInput` | `AgentInput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `LessonSequencePlannerOutput` | `AgentOutput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `LearningPathGeneratorInput` | `AgentInput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `LearningPathGeneratorOutput` | `AgentOutput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `PersonalizedCurriculumInput` | `AgentInput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `PersonalizedCurriculumOutput` | `AgentOutput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `SkillGapCurriculumAdapterInput` | `AgentInput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `SkillGapCurriculumAdapterOutput` | `AgentOutput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `DifficultyBalancerInput` | `AgentInput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `DifficultyBalancerOutput` | `AgentOutput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `StudyStrategyPlannerInput` | `AgentInput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `StudyStrategyPlannerOutput` | `AgentOutput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `ReviewSchedulerInput` | `AgentInput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `ReviewSchedulerOutput` | `AgentOutput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `RemediationPlannerInput` | `AgentInput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `RemediationPlannerOutput` | `AgentOutput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `EnrichmentPlannerInput` | `AgentInput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `EnrichmentPlannerOutput` | `AgentOutput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `ConceptReinforcementInput` | `AgentInput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `ConceptReinforcementOutput` | `AgentOutput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `LongTermLearningPlannerInput` | `AgentInput` | `` |
| `agents/content/models/curriculum_agents_46_60.py` | `LongTermLearningPlannerOutput` | `AgentOutput` | `` |
| `agents/content/models/evaluation_agents_41_45.py` | `EvaluationCriterion` | `BaseModel` | `` |
| `agents/content/models/evaluation_agents_41_45.py` | `EvaluationScore` | `BaseModel` | `` |
| `agents/content/models/evaluation_agents_41_45.py` | `EvaluationIssue` | `BaseModel` | `` |
| `agents/content/models/evaluation_agents_41_45.py` | `AlignmentResult` | `BaseModel` | `` |
| `agents/content/models/evaluation_agents_41_45.py` | `ConsistencyError` | `BaseModel` | `` |
| `agents/content/models/evaluation_agents_41_45.py` | `CoverageGap` | `BaseModel` | `` |
| `agents/content/models/evaluation_agents_41_45.py` | `QuestionQualityEvaluationInput` | `AgentInput` | `` |
| `agents/content/models/evaluation_agents_41_45.py` | `QuestionQualityEvaluationOutput` | `AgentOutput` | `` |
| `agents/content/models/evaluation_agents_41_45.py` | `ExplanationQualityEvaluationInput` | `AgentInput` | `` |
| `agents/content/models/evaluation_agents_41_45.py` | `ExplanationQualityEvaluationOutput` | `AgentOutput` | `` |
| `agents/content/models/evaluation_agents_41_45.py` | `PedagogicalAlignmentInput` | `AgentInput` | `` |
| `agents/content/models/evaluation_agents_41_45.py` | `PedagogicalAlignmentOutput` | `AgentOutput` | `` |
| `agents/content/models/evaluation_agents_41_45.py` | `ConsistencyEvaluationInput` | `AgentInput` | `` |
| `agents/content/models/evaluation_agents_41_45.py` | `ConsistencyEvaluationOutput` | `AgentOutput` | `` |
| `agents/content/models/evaluation_agents_41_45.py` | `CurriculumCoverageInput` | `AgentInput` | `` |
| `agents/content/models/evaluation_agents_41_45.py` | `CurriculumCoverageOutput` | `AgentOutput` | `` |
| `agents/content/models/learning_objects.py` | `StudentProfile` | `BaseModel` | `` |
| `agents/content/models/learning_objects.py` | `InstructorProfile` | `BaseModel` | `` |
| `agents/content/models/learning_objects.py` | `VAKRStyle` | `str, Enum` | `` |
| `agents/content/models/learning_objects.py` | `PacePreference` | `str, Enum` | `` |
| `agents/content/models/learning_objects.py` | `AbstractionLevel` | `str, Enum` | `` |
| `agents/content/models/learning_objects.py` | `FeedbackPreference` | `str, Enum` | `` |
| `agents/content/models/learning_objects.py` | `LearningStyle` | `BaseModel` | `` |
| `agents/content/models/learning_objects.py` | `LearningObjective` | `BaseModel` | `` |
| `agents/content/models/learning_objects.py` | `Lesson` | `BaseModel` | `` |
| `agents/content/models/learning_objects.py` | `ConceptNode` | `BaseModel` | `` |
| `agents/content/models/learning_objects.py` | `GlossaryEntry` | `BaseModel` | `` |
| `agents/content/models/learning_objects.py` | `Question` | `BaseModel` | `` |
| `agents/content/models/learning_objects.py` | `StudentAnswer` | `BaseModel` | `` |
| `agents/content/models/learning_objects.py` | `AssessmentResult` | `BaseModel` | `` |
| `agents/content/models/learning_objects.py` | `Assignment` | `BaseModel` | `` |
| `agents/content/models/learning_objects.py` | `LearningEvent` | `BaseModel` | `` |
| `agents/content/models/learning_objects.py` | `SkillPerformance` | `BaseModel` | `` |
| `agents/content/models/learning_objects.py` | `LearningProgress` | `BaseModel` | `` |
| `agents/content/models/learning_objects.py` | `LearningResource` | `BaseModel` | `` |
| `agents/content/models/memory_agents_76_90.py` | `KnowledgeIngestionInput` | `AgentInput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `KnowledgeIngestionOutput` | `AgentOutput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `DocumentChunkingInput` | `AgentInput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `DocumentChunkingOutput` | `AgentOutput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `EmbeddingGeneratorInput` | `AgentInput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `EmbeddingGeneratorOutput` | `AgentOutput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `SemanticIndexerInput` | `AgentInput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `SemanticIndexerOutput` | `AgentOutput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `VectorSearchInput` | `AgentInput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `VectorSearchOutput` | `AgentOutput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `HybridRetrievalInput` | `AgentInput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `HybridRetrievalOutput` | `AgentOutput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `ContextBuilderInput` | `AgentInput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `ContextBuilderOutput` | `AgentOutput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `MemoryConsolidationInput` | `AgentInput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `MemoryConsolidationOutput` | `AgentOutput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `EpisodicMemoryInput` | `AgentInput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `EpisodicMemoryOutput` | `AgentOutput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `StudentKnowledgeMemoryInput` | `AgentInput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `StudentKnowledgeMemoryOutput` | `AgentOutput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `KnowledgeUpdaterInput` | `AgentInput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `KnowledgeUpdaterOutput` | `AgentOutput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `KnowledgeConflictResolverInput` | `AgentInput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `KnowledgeConflictResolverOutput` | `AgentOutput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `RetrievalRankerInput` | `AgentInput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `RetrievalRankerOutput` | `AgentOutput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `ContextRelevanceEvaluatorInput` | `AgentInput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `ContextRelevanceEvaluatorOutput` | `AgentOutput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `KnowledgeSummarizerInput` | `AgentInput` | `` |
| `agents/content/models/memory_agents_76_90.py` | `KnowledgeSummarizerOutput` | `AgentOutput` | `` |
| `agents/content/models/multimodal_agents_101_110.py` | `TextToSpeechInput` | `AgentInput` | `` |
| `agents/content/models/multimodal_agents_101_110.py` | `TextToSpeechOutput` | `AgentOutput` | `` |
| `agents/content/models/multimodal_agents_101_110.py` | `SpeechToTextInput` | `AgentInput` | `` |
| `agents/content/models/multimodal_agents_101_110.py` | `SpeechToTextOutput` | `AgentOutput` | `` |
| `agents/content/models/multimodal_agents_101_110.py` | `VisualIllustrationInput` | `AgentInput` | `` |
| `agents/content/models/multimodal_agents_101_110.py` | `VisualIllustrationOutput` | `AgentOutput` | `` |
| `agents/content/models/multimodal_agents_101_110.py` | `BoardDrawingInput` | `AgentInput` | `` |
| `agents/content/models/multimodal_agents_101_110.py` | `BoardDrawingOutput` | `AgentOutput` | `` |
| `agents/content/models/multimodal_agents_101_110.py` | `EmotionAnalysisInput` | `AgentInput` | `` |
| `agents/content/models/multimodal_agents_101_110.py` | `EmotionAnalysisOutput` | `AgentOutput` | `` |
| `agents/content/models/multimodal_agents_101_110.py` | `EngagementDetectorInput` | `AgentInput` | `` |
| `agents/content/models/multimodal_agents_101_110.py` | `EngagementDetectorOutput` | `AgentOutput` | `` |
| `agents/content/models/multimodal_agents_101_110.py` | `VisualFeedbackInput` | `AgentInput` | `` |
| `agents/content/models/multimodal_agents_101_110.py` | `VisualFeedbackOutput` | `AgentOutput` | `` |
| `agents/content/models/multimodal_agents_101_110.py` | `GestureRecognitionInput` | `AgentInput` | `` |
| `agents/content/models/multimodal_agents_101_110.py` | `GestureRecognitionOutput` | `AgentOutput` | `` |
| `agents/content/models/multimodal_agents_101_110.py` | `AudioFeedbackInput` | `AgentInput` | `` |
| `agents/content/models/multimodal_agents_101_110.py` | `AudioFeedbackOutput` | `AgentOutput` | `` |
| `agents/content/models/multimodal_agents_101_110.py` | `InteractiveLessonOrchestratorInput` | `AgentInput` | `` |
| `agents/content/models/multimodal_agents_101_110.py` | `InteractiveLessonOrchestratorOutput` | `AgentOutput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `LearningSessionPlannerInput` | `AgentInput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `LearningSessionPlannerOutput` | `AgentOutput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `AgentWorkflowPlannerInput` | `AgentInput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `AgentWorkflowPlannerOutput` | `AgentOutput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `TaskDecomposerInput` | `AgentInput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `TaskDecomposerOutput` | `AgentOutput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `AgentSelectorInput` | `AgentInput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `AgentSelectorOutput` | `AgentOutput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `ContextManagerInput` | `AgentInput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `ContextManagerOutput` | `AgentOutput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `WorkflowStateTrackerInput` | `AgentInput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `WorkflowStateTrackerOutput` | `AgentOutput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `FailureRecoveryInput` | `AgentInput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `FailureRecoveryOutput` | `AgentOutput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `RetryStrategyInput` | `AgentInput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `RetryStrategyOutput` | `AgentOutput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `ShortTermMemoryInput` | `AgentInput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `ShortTermMemoryOutput` | `AgentOutput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `LongTermMemoryInput` | `AgentInput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `LongTermMemoryOutput` | `AgentOutput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `WorkflowOptimizerInput` | `AgentInput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `WorkflowOptimizerOutput` | `AgentOutput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `CostEfficiencyAnalyzerInput` | `AgentInput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `CostEfficiencyAnalyzerOutput` | `AgentOutput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `AgentPerformanceMonitorInput` | `AgentInput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `AgentPerformanceMonitorOutput` | `AgentOutput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `SystemHealthEvaluatorInput` | `AgentInput` | `` |
| `agents/content/models/orchestration_agents_61_75.py` | `SystemHealthEvaluatorOutput` | `AgentOutput` | `` |
| `agents/content/models/personalization_agents_15_20.py` | `DialogueTutorInput` | `AgentInput` | `` |
| `agents/content/models/personalization_agents_15_20.py` | `TutorResponse` | `BaseModel` | `` |
| `agents/content/models/personalization_agents_15_20.py` | `DialogueTutorOutput` | `AgentOutput` | `` |
| `agents/content/models/personalization_agents_15_20.py` | `StyleAdaptationInput` | `AgentInput` | `` |
| `agents/content/models/personalization_agents_15_20.py` | `AdaptedContent` | `BaseModel` | `` |
| `agents/content/models/personalization_agents_15_20.py` | `StyleAdaptationOutput` | `AgentOutput` | `` |
| `agents/content/models/personalization_agents_15_20.py` | `ProgressAnalysisInput` | `AgentInput` | `` |
| `agents/content/models/personalization_agents_15_20.py` | `ProgressAnalysisOutput` | `AgentOutput` | `` |
| `agents/content/models/personalization_agents_15_20.py` | `LearningPathCreationInput` | `AgentInput` | `` |
| `agents/content/models/personalization_agents_15_20.py` | `LearningStep` | `BaseModel` | `` |
| `agents/content/models/personalization_agents_15_20.py` | `LearningPathCreationOutput` | `AgentOutput` | `` |
| `agents/content/models/personalization_agents_15_20.py` | `ResourceRecommendationInput` | `AgentInput` | `` |
| `agents/content/models/personalization_agents_15_20.py` | `RecommendedResource` | `BaseModel` | `` |
| `agents/content/models/personalization_agents_15_20.py` | `ResourceRecommendationOutput` | `AgentOutput` | `` |
| `agents/content/models/personalization_agents_15_20.py` | `InteractionStyleAnalysisInput` | `AgentInput` | `` |
| `agents/content/models/personalization_agents_15_20.py` | `InteractionPattern` | `BaseModel` | `` |
| `agents/content/models/personalization_agents_15_20.py` | `InteractionStyleAnalysisOutput` | `AgentOutput` | `` |
| `agents/content/models/teaching_agents_9_14.py` | `QuestionRefineInput` | `AgentInput` | `` |
| `agents/content/models/teaching_agents_9_14.py` | `QuestionRefineOutput` | `AgentOutput` | `` |
| `agents/content/models/teaching_agents_9_14.py` | `QuestionGenerationInput` | `AgentInput` | `` |
| `agents/content/models/teaching_agents_9_14.py` | `QuestionGenerationOutput` | `AgentOutput` | `` |
| `agents/content/models/teaching_agents_9_14.py` | `HintGenerationInput` | `AgentInput` | `` |
| `agents/content/models/teaching_agents_9_14.py` | `HintGenerationOutput` | `AgentOutput` | `` |
| `agents/content/models/teaching_agents_9_14.py` | `ExplanationGenerationInput` | `AgentInput` | `` |
| `agents/content/models/teaching_agents_9_14.py` | `ExplanationGenerationOutput` | `AgentOutput` | `` |
| `agents/content/models/teaching_agents_9_14.py` | `DifficultyAdaptationInput` | `AgentInput` | `` |
| `agents/content/models/teaching_agents_9_14.py` | `DifficultyAdaptationOutput` | `AgentOutput` | `` |
| `agents/content/models/teaching_agents_9_14.py` | `MisconceptionDetectionInput` | `AgentInput` | `` |
| `agents/content/models/teaching_agents_9_14.py` | `Misconception` | `AgentOutput` | `` |
| `agents/content/models/teaching_agents_9_14.py` | `MisconceptionDetectionOutput` | `AgentOutput` | `` |
| `agents/content/text_rewriter.py` | `TextRewriterAgent` | `BaseAgent` | `__init__, execute, _rewrite_text, _fallback_rewrite, _estimate_readability` |
| `agents/interaction/backends/autogen_backend.py` | `AutoGenOrchestrationBackend` | `BaseOrchestrationBackend` | `__init__, _autogen_available, is_available, execute, _execute_with_autogen_group_chat` |
| `agents/interaction/backends/base_backend.py` | `BaseOrchestrationBackend` | `ABC` | `execute` |
| `agents/interaction/backends/native_backend.py` | `NativeOrchestrationBackend` | `BaseOrchestrationBackend` | `__init__, _build_strategy, execute` |
| `agents/interaction/base_strategy.py` | `InteractionStrategy` | `—` | `__init__, execute, _emit, _build_input, _run_agent` |
| `agents/interaction/broadcast_strategy.py` | `BroadcastStrategy` | `InteractionStrategy` | `execute, _execute_agent, _normalize_gather_results, _aggregate_outputs` |
| `agents/interaction/coordinator_strategy.py` | `CoordinatorStrategy` | `InteractionStrategy` | `__init__, execute, _run_validation, _aggregate, _publish_turn_message` |
| `agents/interaction/debate_strategy.py` | `DebateStrategy` | `InteractionStrategy` | `execute` |
| `agents/interaction/ensemble_strategy.py` | `EnsembleStrategy` | `InteractionStrategy` | `__init__, execute, _aggregate_votes, _publish_vote, _normalize_output` |
| `agents/interaction/group_chat_strategy.py` | `GroupChatStrategy` | `InteractionStrategy` | `__init__, execute, _init_messages, _resolve_participants, _extract_message, _extract_context_update ...` |
| `agents/interaction/interaction_models.py` | `InteractionRequest` | `BaseModel` | `` |
| `agents/interaction/interaction_models.py` | `InteractionResult` | `BaseModel` | `` |
| `agents/interaction/interaction_models.py` | `AgentMessage` | `BaseModel` | `` |
| `agents/interaction/round_robin_strategy.py` | `RoundRobinStrategy` | `InteractionStrategy` | `__init__, execute` |
| `agents/interaction/self_refine_strategy.py` | `SelfRefineStrategy` | `InteractionStrategy` | `execute, _extract_score` |
| `agents/interaction/strategy_registry.py` | `InteractionStrategyRegistry` | `Generic[TStrategy]` | `__init__, register, unregister, get, require, list_scenarios ...` |
| `rag/agentic/agent_v2.py` | `RetrievalAgentV2` | `—` | `__init__, run` |
| `rag/agentic/evidence_tracker.py` | `EvidenceTracker` | `—` | `__init__, add, needs_more` |
| `rag/agentic/multihop_reasoner.py` | `MultiHopReasoner` | `—` | `__init__, generate_followup` |
| `rag/agentic/query_decomposer.py` | `QueryDecomposer` | `—` | `__init__, decompose` |
| `rag/agentic/retrieval_agent.py` | `RetrievalAgent` | `—` | `__init__, run` |
| `rag/agentic/uncertainty.py` | `UncertaintyEstimator` | `—` | `__init__, score` |
| `rag/compression/base.py` | `BaseCompressor` | `—` | `compress` |
| `rag/compression/embedding_compressor.py` | `EmbeddingCompressor` | `BaseCompressor` | `__init__, compress` |
| `rag/compression/llm_compressor.py` | `LLMCompressor` | `BaseCompressor` | `__init__, compress` |
| `rag/evidence/evidence_clusterer.py` | `EvidenceClusterer` | `—` | `__init__, cluster` |
| `rag/explain/retrieval_explainer.py` | `RetrievalExplainer` | `—` | `__init__, explain` |
| `rag/graph/graph_builder.py` | `GraphBuilder` | `—` | `__init__, extract` |
| `rag/graph/graph_models.py` | `GraphNode` | `BaseModel` | `` |
| `rag/graph/graph_models.py` | `GraphEdge` | `BaseModel` | `` |
| `rag/graph/graph_retriever.py` | `GraphRetriever` | `—` | `__init__, retrieve, search` |
| `rag/graph/graph_store.py` | `MemoryGraphStore` | `—` | `__init__, add_node, add_edge, neighbors` |
| `rag/learning/retrieval_policy.py` | `RetrievalPolicy` | `—` | `__init__, get_state, select, update` |
| `rag/llm/base_llm.py` | `BaseLLM` | `ABC` | `ainvoke, astream` |
| `rag/llm/llm_protocols.py` | `AsyncLLM` | `Protocol` | `ainvoke, astream` |
| `rag/llm/ollama_llm.py` | `OllamaLLM` | `BaseLLM` | `__init__, ainvoke, _stream_impl, astream` |
| `rag/llm/openai_llm.py` | `OpenAILLM` | `BaseLLM` | `__init__, ainvoke, _stream_impl, astream` |
| `rag/planner/adaptive_planner.py` | `AdaptiveRetrievalPlanner` | `—` | `__init__, plan` |
| `rag/planner/retrieval_plan.py` | `RetrievalPlan` | `BaseModel` | `` |
| `rag/rag_models.py` | `Document` | `BaseModel` | `` |
| `rag/rag_models.py` | `DocumentChunk` | `BaseModel` | `` |
| `rag/rag_models.py` | `RetrievedDocument` | `BaseModel` | `` |
| `rag/reflection/reflection_critic.py` | `RetrievalCritic` | `—` | `__init__, evaluate` |
| `rag/reflection/reflection_loop.py` | `ReflectionLoop` | `—` | `__init__, improve_query, run` |
| `rag/reranking/base_reranker.py` | `BaseReranker` | `ABC` | `rerank` |
| `rag/reranking/reranker.py` | `Reranker` | `BaseReranker` | `rerank, _tokenize` |
| `rag/research/answer_planner.py` | `LLMProtocol` | `Protocol` | `complete` |
| `rag/research/answer_planner.py` | `LLMGenerateProtocol` | `Protocol` | `generate` |
| `rag/research/answer_planner.py` | `LLMInvokeProtocol` | `Protocol` | `ainvoke` |
| `rag/research/answer_planner.py` | `AnswerPlanner` | `—` | `__init__, create_plan, _llm_plan, _fallback_plan, _complete, _evidence_to_text` |
| `rag/research/autonomous/coverage_scorer.py` | `EvidenceCoverageScorer` | `—` | `__init__, score, _complete, _to_text` |
| `rag/research/autonomous/gap_detector.py` | `GapDetector` | `—` | `__init__, detect_gaps, _heuristic_gaps, _complete, _to_text` |
| `rag/research/autonomous/query_generator.py` | `FollowUpQueryGenerator` | `—` | `__init__, generate, _complete, _heuristic_query` |
| `rag/research/autonomous/research_loop.py` | `AutonomousResearchLoop` | `—` | `__init__, run` |
| `rag/research/base_research_agent.py` | `BaseResearchAgent` | `ABC` | `run` |
| `rag/research/citation_manager.py` | `Citation` | `—` | `` |
| `rag/research/citation_manager.py` | `CitationManager` | `—` | `__init__, reset, register_source, build_reference_list` |
| `rag/research/dashboard/schema.py` | `TokenUsage` | `BaseModel` | `` |
| `rag/research/dashboard/schema.py` | `TokenBreakdownResponse` | `BaseModel` | `` |
| `rag/research/dashboard/schema.py` | `RetrievalChunkStat` | `BaseModel` | `` |
| `rag/research/dashboard/schema.py` | `RetrievalHeatmapResponse` | `BaseModel` | `` |
| `rag/research/dashboard/schema.py` | `GraphPath` | `BaseModel` | `` |
| `rag/research/dashboard/schema.py` | `GraphPathsResponse` | `BaseModel` | `` |
| `rag/research/dashboard/schema.py` | `FailureEvent` | `BaseModel` | `` |
| `rag/research/dashboard/schema.py` | `FailureResponse` | `BaseModel` | `` |
| `rag/research/dashboard/schema.py` | `MemoryUsageResponse` | `BaseModel` | `` |
| `rag/research/dashboard/schema.py` | `TelemetryEventResponse` | `BaseModel` | `` |
| `rag/research/dashboard/websocket_stream.py` | `WebSocketStream` | `—` | `__init__, connect, disconnect, snapshot, stream_client` |
| `rag/research/evaluation/citation_evaluator.py` | `CitationEvaluator` | `—` | `__init__, evaluate` |
| `rag/research/evaluation/completeness_evaluator.py` | `CompletenessEvaluator` | `—` | `__init__, evaluate` |
| `rag/research/evaluation/coverage_scorer.py` | `CoverageScorer` | `—` | `score` |
| `rag/research/evaluation/evaluation_controller.py` | `EvaluationController` | `—` | `__init__, evaluate` |
| `rag/research/evaluation/hallucination_detector.py` | `HallucinationDetector` | `—` | `__init__, detect` |
| `rag/research/evaluation/improvement_engine.py` | `ImprovementEngine` | `—` | `suggest` |
| `rag/research/evaluation/reasoning_evaluator.py` | `ReasoningEvaluator` | `—` | `__init__, evaluate` |
| `rag/research/evaluation/retrieval_evaluator.py` | `RetrievalEvaluator` | `—` | `__init__, evaluate` |
| `rag/research/evaluation/schema.py` | `Evidence` | `BaseModel` | `` |
| `rag/research/evaluation/schema.py` | `ResearchAnswer` | `BaseModel` | `` |
| `rag/research/evaluation/schema.py` | `EvaluationResult` | `BaseModel` | `` |
| `rag/research/graph/entity_extractor.py` | `Entity` | `—` | `` |
| `rag/research/graph/entity_extractor.py` | `EntityExtractor` | `—` | `__init__, extract, _llm_extract, _heuristic_extract, _deduplicate, _complete` |
| `rag/research/graph/graph_aware_planner.py` | `GraphAwareAnswerPlanner` | `—` | `create_plan` |
| `rag/research/graph/graph_canonicalizer.py` | `GraphCanonicalizer` | `—` | `canonicalize, normalize_entity` |
| `rag/research/graph/graph_index.py` | `GraphNode` | `—` | `` |
| `rag/research/graph/graph_index.py` | `GraphEdge` | `—` | `` |
| `rag/research/graph/graph_index.py` | `GraphIndex` | `—` | `__init__, add_entities, add_relation, get_neighbors` |
| `rag/research/graph/graph_persistence.py` | `GraphPersistence` | `—` | `__init__, _init_schema, save_node, save_edge` |
| `rag/research/graph/graph_traverser.py` | `GraphTraverser` | `—` | `__init__, find_connections` |
| `rag/research/graph/relation_builder.py` | `CandidateRelation` | `—` | `` |
| `rag/research/graph/relation_builder.py` | `RelationBuilder` | `—` | `__init__, build_relations, _llm_relations, _pattern_relations, _cooccurrence_relations, _deduplicate ...` |
| `rag/research/graph/relation_ranker.py` | `RelationRankingEngine` | `—` | `__init__, rank` |
| `rag/research/guardrails/hallucination_guard.py` | `HallucinationGuard` | `—` | `__init__, enable_strict_mode, disable` |
| `rag/research/improvement/feedback_controller.py` | `FeedbackController` | `—` | `__init__, apply_feedback` |
| `rag/research/memory/memory_controller.py` | `MemoryController` | `—` | `__init__, record, recall, reasoning_trace, stats` |
| `rag/research/memory/memory_retriever.py` | `MemoryRetriever` | `—` | `__init__, retrieve_similar, _token_overlap, _recency_weight` |
| `rag/research/memory/memory_store.py` | `MemoryItem` | `—` | `` |
| `rag/research/memory/memory_store.py` | `MemoryStore` | `—` | `__init__, add, all` |
| `rag/research/memory/reasoning/event_types.py` | `ReasoningEventType` | `str, Enum` | `` |
| `rag/research/memory/reasoning/reasoning_event.py` | `ReasoningEvent` | `—` | `to_dict` |
| `rag/research/memory/reasoning/reasoning_exporter.py` | `ReasoningExporter` | `—` | `to_json, summary, walk` |
| `rag/research/memory/reasoning/reasoning_memory.py` | `ReasoningLevel` | `str, Enum` | `` |
| `rag/research/memory/reasoning/reasoning_memory.py` | `ReasoningPhase` | `str, Enum` | `` |
| `rag/research/memory/reasoning/reasoning_memory.py` | `ReasoningMemory` | `—` | `__init__, start_session, end_session, start_group, end_group, log ...` |
| `rag/research/memory/reasoning/reasoning_node.py` | `ReasoningNode` | `—` | `__init__, add_event, add_child, finish, mark_failed, to_dict` |
| `rag/research/memory/reasoning/reasoning_recorder.py` | `ReasoningRecorder` | `—` | `__init__, start, end, rollback, event, export` |
| `rag/research/memory/reasoning/reasoning_tree.py` | `ReasoningTree` | `—` | `__init__, start_group, end_group, rollback_group, to_dict` |
| `rag/research/memory/reasoning_memory.py` | `ReasoningStep` | `—` | `__init__, to_dict` |
| `rag/research/memory/reasoning_memory.py` | `ReasoningMemory` | `—` | `__init__, log, start_group, end_group, dump, summary ...` |
| `rag/research/memory/temporal_graph.py` | `TemporalGraph` | `—` | `__init__, add_entity, add_relation, recent_relations` |
| `rag/research/observability/failure_analyzer.py` | `FailureAnalyzer` | `—` | `__init__, record, recent` |
| `rag/research/observability/graph_visualizer.py` | `GraphVisualizer` | `—` | `__init__, record_path, get_paths` |
| `rag/research/observability/memory_usage_tracker.py` | `MemoryUsageTracker` | `—` | `current` |
| `rag/research/observability/metrics_store.py` | `MetricsStore` | `—` | `__init__, snapshot` |
| `rag/research/observability/observability_controller.py` | `ObservabilityController` | `—` | `__init__, track_research_session` |
| `rag/research/observability/retrieval_heatmap.py` | `RetrievalHeatmap` | `—` | `__init__, record, top_chunks` |
| `rag/research/observability/telemetry.py` | `TelemetryEvent` | `ABC` | `__init__, to_dict` |
| `rag/research/observability/telemetry.py` | `Telemetry` | `ABC` | `__init__, emit` |
| `rag/research/observability/token_tracker.py` | `TokenTracker` | `—` | `__init__, record, total, breakdown` |
| `rag/research/observability/trace_collector.py` | `TraceCollector` | `—` | `__init__, collect, extend, get_recent, clear` |
| `rag/research/research_agent.py` | `ResearchAgent` | `BaseResearchAgent` | `__init__, run, _compose_report, _to_evidence_item` |
| `rag/research/summarization/base_summarizer.py` | `BaseSummarizer` | `ABC` | `summarize` |
| `rag/research/summarization/research_summarizer.py` | `ResearchSummarizer` | `BaseSummarizer` | `__init__, summarize, build_prompt, enforce_citations, _fallback_summary` |
| `rag/research/summarization/section_summarizer.py` | `SectionSummarizer` | `BaseSummarizer` | `__init__, summarize, _select_supporting_evidence` |
| `rag/retrieval/base_retriever.py` | `BaseRetriever` | `ABC` | `search` |
| `rag/retrieval/bm25_retriever.py` | `BM25KeywordRetriever` | `BaseRetriever` | `__init__, invalidate, _ensure_index, search, _tokenize` |
| `rag/retrieval/hybrid_retriever.py` | `HybridRetriever` | `BaseRetriever` | `__init__, _rrf_merge, search` |
| `rag/retrieval/hybrid_retriever_plus.py` | `HybridRetrieverPlus` | `BaseRetriever` | `__init__, _analyze_query, _semantic_keywords, _dynamic_rrf_from_llm, _normalize_scores, _cross_filter ...` |
| `rag/retrieval/hybrid_retriever_super.py` | `FusionMLP` | `—` | `__init__, predict` |
| `rag/retrieval/hybrid_retriever_super.py` | `HybridRetrieverSuper` | `BaseRetriever` | `__init__, attach_feedback_buffer, attach_trainer, collect_feedback, train_from_feedback, _normalize ...` |
| `rag/retrieval/keyword_retriever.py` | `KeywordRetriever` | `BaseRetriever` | `__init__, search` |
| `rag/retrieval/retrieval_feedback_buffer.py` | `RetrievalFeedbackBuffer` | `—` | `__init__, add, sample, __len__, get_all, clear` |
| `rag/retrieval/retriever_result.py` | `RetrievalResult` | `—` | `` |
| `rag/retrieval/retriever_trainer.py` | `RetrieverTrainer` | `—` | `__init__, train_step` |
| `rag/retrieval/topk_optimizer.py` | `TopKOptimizer` | `—` | `__init__, choose, update` |
| `rag/retrieval/vector_retriever.py` | `VectorRetriever` | `BaseRetriever` | `__init__, search, _result_to_chunk` |
| `rag/retrieval/weight_manager.py` | `WeightManager` | `—` | `__init__, get, update, all` |
| `rag/services/chunking.py` | `Chunker` | `—` | `__init__, create_chunks, _split_text` |
| `rag/services/embedding.py` | `EmbeddingModel` | `—` | `__init__, embed, embed_one, _fallback_embed, _tokenize, _coerce_vector` |
| `rag/services/query_rewriter.py` | `QueryRewriter` | `—` | `__init__, rewrite` |
| `rag/trainer/base_trainer.py` | `BaseTrainer` | `ABC` | `train` |
| `rag/trainer/fusion_trainer.py` | `FusionTrainer` | `BaseTrainer` | `__init__, ensure_optimizer, train_epoch, train` |
| `rag/trainer/reranker_trainer.py` | `RerankerTrainer` | `BaseTrainer` | `__init__, train_step` |
| `rag/vector_service.py` | `QueryResult` | `BaseModel` | `` |
| `rag/vector_service.py` | `VectorService` | `—` | `__init__, retriever, register_feedback, raw_retrieve, _retrieve_one, query ...` |
| `storage/backends/file_adapter.py` | `LocalFileAdapter` | `StorageAdapter` | `__init__, _get_path, save, load, delete, list_keys` |
| `storage/backends/redis/connection.py` | `RedisManager` | `—` | `__init__, connect, get_client` |
| `storage/backends/redis/storage_adapter.py` | `RedisStorageAdapter` | `StorageAdapter` | `__init__, _get_key, _client, save, load, delete ...` |
| `storage/backends/redis/stream_adapter.py` | `RedisStreamAdapter` | `—` | `__init__, _client, add_event, read_group` |
| `storage/backends/sql_storage.py` | `SQLStorage` | `StorageAdapter` | `__init__, _ensure_initialized, save, load, delete, list_keys` |
| `storage/base_storage.py` | `StorageAdapter` | `ABC` | `save, load, delete, list_keys` |
| `storage/base_storage.py` | `BaseStorage` | `ABC` | `add, get, delete` |
| `storage/document_store.py` | `DocumentStore` | `BaseStorage` | `__init__, add_document, add_chunks, get_document, get_chunk, get_chunks_by_doc ...` |
| `storage/log_storage.py` | `LogStorage` | `BaseStorage` | `__init__, log_agent_execution, list_agent_logs, get_agent_log, log_event, list_events ...` |
| `storage/vector/backends/chroma_adapter.py` | `ChromaAdapter` | `VectorDBAdapter` | `__init__, _sanitize_metadata, _get_or_create_collection, create_index, upsert, batch_upsert ...` |
| `storage/vector/backends/faiss_adapter.py` | `FaissAdapter` | `VectorDBAdapter` | `__init__, create_index, upsert, batch_upsert, query, delete` |
| `storage/vector/backends/memory_adapter.py` | `InMemoryVectorStore` | `VectorDBAdapter` | `__init__, create_index, upsert, batch_upsert, query, delete` |
| `storage/vector/backends/pinecone_adapter.py` | `PineconeAdapter` | `VectorDBAdapter` | `__init__, _initialize_connection, create_index, _require_index, upsert, batch_upsert ...` |
| `storage/vector/backends/qdrant_adapter.py` | `QdrantAdapter` | `VectorDBAdapter` | `__init__, create_index, upsert, batch_upsert, query, delete` |
| `storage/vector/backends/weaviate_adapter.py` | `WeaviateAdapter` | `VectorDBAdapter` | `__init__, _get_or_create_collection, create_index, upsert, batch_upsert, query ...` |
| `storage/vector/base.py` | `VectorDBAdapter` | `ABC` | `create_index, upsert, batch_upsert, query, delete, search ...` |
| `storage/vector/index_config.py` | `HNSWConfig` | `—` | `` |
| `storage/vector/index_config.py` | `IVFConfig` | `—` | `` |
| `tests/agents/agents_unit/test_agent_registry.py` | `SimpleInput` | `AgentInput` | `` |
| `tests/agents/agents_unit/test_agent_registry.py` | `SimpleOutput` | `AgentOutput` | `` |
| `tests/agents/agents_unit/test_agent_registry.py` | `SimpleAgent` | `BaseAgent` | `execute` |
| `tests/agents/agents_unit/test_base_agent.py` | `InputModel` | `AgentInput` | `` |
| `tests/agents/agents_unit/test_base_agent.py` | `OutputModel` | `AgentOutput` | `` |
| `tests/agents/agents_unit/test_base_agent.py` | `EchoAgent` | `BaseAgent[InputModel, OutputModel]` | `execute` |
| `tests/agents/agents_unit/test_base_agent.py` | `FailingAgent` | `EchoAgent` | `execute` |
| `tests/agents/interaction/interaction_unit/conftest.py` | `TestAgent` | `—` | `__init__, execute` |
| `tests/agents/interaction/interaction_unit/conftest.py` | `TestRegistry` | `—` | `__init__, register, execute` |
| `tests/agents/interaction/interaction_unit/conftest.py` | `DummyMessageBus1` | `MessageBus` | `__init__, publish, subscribe, unsubscribe` |
| `tests/agents/orchestration/orchestration_performance/test_native_orchestration_backend_performance.py` | `DummyOutput` | `—` | `__init__, model_dump` |
| `tests/agents/orchestration/orchestration_performance/test_native_orchestration_backend_performance.py` | `SimpleRegistry` | `—` | `execute` |
| `tests/agents/orchestration/orchestration_performance/test_interaction_agent_performance.py` | `DummyBackend` | `BaseOrchestrationBackend` | `__init__, execute, model_dump` |
| `tests/agents/orchestration/orchestration_performance/test_interaction_agent_performance.py` | `Result` | `InteractionResult` | `model_dump` |
| `tests/agents/orchestration/orchestration_unit/test_autogen_orchestration_backend.py` | `DummyRegistry1` | `—` | `execute` |
| `tests/agents/orchestration/orchestration_unit/test_autogen_orchestration_backend.py` | `DummyMessageBus2` | `MessageBus` | `publish, subscribe, unsubscribe` |
| `tests/agents/orchestration/orchestration_unit/test_autogen_orchestration_backend.py` | `DummyResult` | `—` | `__init__, execute` |
| `tests/agents/orchestration/orchestration_unit/test_autogen_orchestration_backend.py` | `SimpleRequest` | `—` | `__init__` |
| `tests/agents/orchestration/orchestration_unit/test_native_orchestration_backend.py` | `DummyOutput` | `—` | `__init__, model_dump` |
| `tests/agents/orchestration/orchestration_unit/test_native_orchestration_backend.py` | `DummyRegistry2` | `—` | `__init__, execute` |
| `tests/agents/orchestration/orchestration_unit/test_native_orchestration_backend.py` | `DummyMessageBus` | `MessageBus` | `__init__, publish, subscribe, unsubscribe` |
| `tests/agents/orchestration/orchestration_unit/test_interaction_agent.py` | `DummyBackend` | `BaseOrchestrationBackend` | `__init__, execute, model_dump` |
| `tests/agents/orchestration/orchestration_unit/test_interaction_agent.py` | `Result` | `InteractionResult` | `model_dump` |
| `tools/analyze_architecture.py` | `ClassInfo` | `—` | `` |
| `tools/analyze_architecture.py` | `FileInfo` | `—` | `` |
| `tools/analyze_architecture.py` | `ASTParser` | `—` | `parse, _extract, _parse_class, _is_top_level, _name` |
| `tools/analyze_architecture.py` | `ProjectCollector` | `—` | `__init__, collect, _iter_python_files` |
| `tools/analyze_architecture.py` | `ArchitectureAnalyzer` | `—` | `__init__, folder_structure, folder_tree, classes_table, inheritance_map, abstract_classes ...` |
| `tools/analyze_architecture.py` | `MarkdownRenderer` | `—` | `__init__, render` |
| `tools/code_auditor.py` | `MockPosition` | `—` | `__init__` |
| `tools/code_auditor.py` | `MockRange` | `—` | `__init__` |
| `tools/code_auditor.py` | `MockLocation` | `—` | `__init__` |
| `tools/code_auditor.py` | `MockDiagnostic` | `—` | `__init__` |
| `tools/code_auditor.py` | `MockDiagnosticSeverity` | `—` | `` |
| `tools/code_auditor.py` | `Issue` | `—` | `__str__` |
| `tools/code_auditor.py` | `CodeAuditor` | `—` | `__init__, _iter_files, _check_syntax, _get_params, _is_intentionally_empty, _assign_to_stmt ...` |

---

### نقشه وراثت

```
Generic[TInput, TOutput]  →  BaseAgent
BaseModel  →  AgentInput
BaseModel  →  AgentOutput
BaseModel  →  AgentExecutionRecord
BaseAgent  →  InteractionAgent
ABC  →  MessageBus
MessageBus  →  DurableMessageBus
MessageBus  →  InMemoryMessageBus
MessageBus  →  KafkaMessageBus
MessageBus  →  PriorityMessageBus
MessageBus  →  RabbitMQMessageBus
MessageBus  →  RedisMessageBus
MessageBus  →  RequestReplyBus
MessageBus  →  TopicMessageBus
AgentInput  →  StudentBehaviorAnalysisInput
BaseModel  →  BehaviorPattern
AgentOutput  →  StudentBehaviorAnalysisOutput
AgentInput  →  EngagementDetectionInput
AgentOutput  →  EngagementDetectionOutput
AgentInput  →  MotivationAnalysisInput
AgentOutput  →  MotivationAnalysisOutput
AgentInput  →  DropoutRiskPredictionInput
AgentOutput  →  DropoutRiskPredictionOutput
AgentInput  →  StudyPatternMiningInput
BaseModel  →  StudyPattern
AgentOutput  →  StudyPatternMiningOutput
AgentInput  →  PerformanceTrendAnalysisInput
BaseModel  →  PerformanceTrend
AgentOutput  →  PerformanceTrendAnalysisOutput
AgentInput  →  LearningOutcomePredictionInput
AgentOutput  →  LearningOutcomePredictionOutput
AgentInput  →  ClassroomAnalyticsInput
AgentOutput  →  ClassroomAnalyticsOutput
AgentInput  →  CohortComparisonInput
AgentOutput  →  CohortComparisonOutput
AgentInput  →  TeacherDashboardAggregationInput
AgentOutput  →  TeacherDashboardAggregationOutput
AgentInput  →  QuizBuilderInput
BaseModel  →  QuizQuestion
AgentOutput  →  QuizBuilderOutput
AgentInput  →  AnswerEvaluationInput
AgentOutput  →  AnswerEvaluationOutput
AgentInput  →  FeedbackGenerationInput
AgentOutput  →  FeedbackGenerationOutput
AgentInput  →  RubricGenerationInput
BaseModel  →  RubricCriterion
AgentOutput  →  RubricGenerationOutput
AgentInput  →  MisconceptionAnalysisInput
BaseModel  →  MisconceptionPattern
AgentOutput  →  MisconceptionAnalysisOutput
AgentInput  →  SkillMasteryInput
AgentOutput  →  SkillMasteryOutput
AgentInput  →  LearningGapInput
BaseModel  →  LearningGap
AgentOutput  →  LearningGapOutput
AgentInput  →  KnowledgeGraphUpdateInput
AgentOutput  →  KnowledgeGraphUpdateOutput
AgentInput  →  ConceptDifficultyInput
AgentOutput  →  ConceptDifficultyOutput
AgentInput  →  CurriculumMappingInput
BaseModel  →  CurriculumMapping
AgentOutput  →  CurriculumMappingOutput
BaseModel  →  ContentVersion
BaseModel  →  ConfidenceScore
BaseModel  →  ScoreRange
BaseModel  →  Evidence
BaseModel  →  ReasoningTrace
BaseModel  →  Recommendation
BaseModel  →  ActionSuggestion
BaseModel  →  ConceptReference
BaseModel  →  ResourceReference
BaseModel  →  DetectedIssue
BaseModel  →  Pattern
BaseModel  →  Prediction
BaseModel  →  TimeWindow
AgentInput  →  TextRewriteInput
BaseModel  →  RewriteChange
AgentOutput  →  TextRewriteOutput
AgentInput  →  ContentValidationInput
BaseModel  →  ValidationIssue
AgentOutput  →  ContentValidationOutput
AgentInput  →  CitationGenerationInput
BaseModel  →  CitationEntry
AgentOutput  →  CitationGenerationOutput
AgentInput  →  GlossaryBuilderInput
BaseModel  →  GlossaryTerm
AgentOutput  →  GlossaryBuilderOutput
AgentInput  →  DynamicUpdateInput
BaseModel  →  ContentUpdateSuggestion
AgentOutput  →  DynamicUpdateOutput
AgentInput  →  NarrativeBuilderInput
BaseModel  →  NarrativeElement
AgentOutput  →  NarrativeBuilderOutput
AgentInput  →  StructuringInput
BaseModel  →  LessonSection
AgentOutput  →  StructuringOutput
AgentInput  →  PrerequisiteInput
BaseModel  →  PrerequisiteItem
AgentOutput  →  PrerequisiteOutput
AgentInput  →  ExampleGeneratorInput
AgentOutput  →  ExampleGeneratorOutput
AgentInput  →  ExerciseCreatorInput
AgentOutput  →  ExerciseCreatorOutput
AgentInput  →  StoryLessonCreatorInput
AgentOutput  →  StoryLessonCreatorOutput
AgentInput  →  ConceptExplanationInput
AgentOutput  →  ConceptExplanationOutput
AgentInput  →  PracticeQuestionGeneratorInput
AgentOutput  →  PracticeQuestionGeneratorOutput
AgentInput  →  AdaptiveQuestionGeneratorInput
AgentOutput  →  AdaptiveQuestionGeneratorOutput
AgentInput  →  ExplanationRewriterInput
AgentOutput  →  ExplanationRewriterOutput
AgentInput  →  SummaryGeneratorInput
AgentOutput  →  SummaryGeneratorOutput
AgentInput  →  ContentSimplifierInput
AgentOutput  →  ContentSimplifierOutput
AgentInput  →  AssessmentQuestionGeneratorInput
AgentOutput  →  AssessmentQuestionGeneratorOutput
AgentInput  →  ConceptGraphBuilderInput
AgentOutput  →  ConceptGraphBuilderOutput
AgentInput  →  ConceptRelationExtractorInput
AgentOutput  →  ConceptRelationExtractorOutput
AgentInput  →  PrerequisiteInferenceInput
AgentOutput  →  PrerequisiteInferenceOutput
AgentInput  →  CurriculumPlannerInput
AgentOutput  →  CurriculumPlannerOutput
AgentInput  →  LessonSequencePlannerInput
AgentOutput  →  LessonSequencePlannerOutput
AgentInput  →  LearningPathGeneratorInput
AgentOutput  →  LearningPathGeneratorOutput
AgentInput  →  PersonalizedCurriculumInput
AgentOutput  →  PersonalizedCurriculumOutput
AgentInput  →  SkillGapCurriculumAdapterInput
AgentOutput  →  SkillGapCurriculumAdapterOutput
AgentInput  →  DifficultyBalancerInput
AgentOutput  →  DifficultyBalancerOutput
AgentInput  →  StudyStrategyPlannerInput
AgentOutput  →  StudyStrategyPlannerOutput
AgentInput  →  ReviewSchedulerInput
AgentOutput  →  ReviewSchedulerOutput
AgentInput  →  RemediationPlannerInput
AgentOutput  →  RemediationPlannerOutput
AgentInput  →  EnrichmentPlannerInput
AgentOutput  →  EnrichmentPlannerOutput
AgentInput  →  ConceptReinforcementInput
AgentOutput  →  ConceptReinforcementOutput
AgentInput  →  LongTermLearningPlannerInput
AgentOutput  →  LongTermLearningPlannerOutput
BaseModel  →  EvaluationCriterion
BaseModel  →  EvaluationScore
BaseModel  →  EvaluationIssue
BaseModel  →  AlignmentResult
BaseModel  →  ConsistencyError
BaseModel  →  CoverageGap
AgentInput  →  QuestionQualityEvaluationInput
AgentOutput  →  QuestionQualityEvaluationOutput
AgentInput  →  ExplanationQualityEvaluationInput
AgentOutput  →  ExplanationQualityEvaluationOutput
AgentInput  →  PedagogicalAlignmentInput
AgentOutput  →  PedagogicalAlignmentOutput
AgentInput  →  ConsistencyEvaluationInput
AgentOutput  →  ConsistencyEvaluationOutput
AgentInput  →  CurriculumCoverageInput
AgentOutput  →  CurriculumCoverageOutput
BaseModel  →  StudentProfile
BaseModel  →  InstructorProfile
str  →  VAKRStyle
Enum  →  VAKRStyle
str  →  PacePreference
Enum  →  PacePreference
str  →  AbstractionLevel
Enum  →  AbstractionLevel
str  →  FeedbackPreference
Enum  →  FeedbackPreference
BaseModel  →  LearningStyle
BaseModel  →  LearningObjective
BaseModel  →  Lesson
BaseModel  →  ConceptNode
BaseModel  →  GlossaryEntry
BaseModel  →  Question
BaseModel  →  StudentAnswer
BaseModel  →  AssessmentResult
BaseModel  →  Assignment
BaseModel  →  LearningEvent
BaseModel  →  SkillPerformance
BaseModel  →  LearningProgress
BaseModel  →  LearningResource
AgentInput  →  KnowledgeIngestionInput
AgentOutput  →  KnowledgeIngestionOutput
AgentInput  →  DocumentChunkingInput
AgentOutput  →  DocumentChunkingOutput
AgentInput  →  EmbeddingGeneratorInput
AgentOutput  →  EmbeddingGeneratorOutput
AgentInput  →  SemanticIndexerInput
AgentOutput  →  SemanticIndexerOutput
AgentInput  →  VectorSearchInput
AgentOutput  →  VectorSearchOutput
AgentInput  →  HybridRetrievalInput
AgentOutput  →  HybridRetrievalOutput
AgentInput  →  ContextBuilderInput
AgentOutput  →  ContextBuilderOutput
AgentInput  →  MemoryConsolidationInput
AgentOutput  →  MemoryConsolidationOutput
AgentInput  →  EpisodicMemoryInput
AgentOutput  →  EpisodicMemoryOutput
AgentInput  →  StudentKnowledgeMemoryInput
AgentOutput  →  StudentKnowledgeMemoryOutput
AgentInput  →  KnowledgeUpdaterInput
AgentOutput  →  KnowledgeUpdaterOutput
AgentInput  →  KnowledgeConflictResolverInput
AgentOutput  →  KnowledgeConflictResolverOutput
AgentInput  →  RetrievalRankerInput
AgentOutput  →  RetrievalRankerOutput
AgentInput  →  ContextRelevanceEvaluatorInput
AgentOutput  →  ContextRelevanceEvaluatorOutput
AgentInput  →  KnowledgeSummarizerInput
AgentOutput  →  KnowledgeSummarizerOutput
AgentInput  →  TextToSpeechInput
AgentOutput  →  TextToSpeechOutput
AgentInput  →  SpeechToTextInput
AgentOutput  →  SpeechToTextOutput
AgentInput  →  VisualIllustrationInput
AgentOutput  →  VisualIllustrationOutput
AgentInput  →  BoardDrawingInput
AgentOutput  →  BoardDrawingOutput
AgentInput  →  EmotionAnalysisInput
AgentOutput  →  EmotionAnalysisOutput
AgentInput  →  EngagementDetectorInput
AgentOutput  →  EngagementDetectorOutput
AgentInput  →  VisualFeedbackInput
AgentOutput  →  VisualFeedbackOutput
AgentInput  →  GestureRecognitionInput
AgentOutput  →  GestureRecognitionOutput
AgentInput  →  AudioFeedbackInput
AgentOutput  →  AudioFeedbackOutput
AgentInput  →  InteractiveLessonOrchestratorInput
AgentOutput  →  InteractiveLessonOrchestratorOutput
AgentInput  →  LearningSessionPlannerInput
AgentOutput  →  LearningSessionPlannerOutput
AgentInput  →  AgentWorkflowPlannerInput
AgentOutput  →  AgentWorkflowPlannerOutput
AgentInput  →  TaskDecomposerInput
AgentOutput  →  TaskDecomposerOutput
AgentInput  →  AgentSelectorInput
AgentOutput  →  AgentSelectorOutput
AgentInput  →  ContextManagerInput
AgentOutput  →  ContextManagerOutput
AgentInput  →  WorkflowStateTrackerInput
AgentOutput  →  WorkflowStateTrackerOutput
AgentInput  →  FailureRecoveryInput
AgentOutput  →  FailureRecoveryOutput
AgentInput  →  RetryStrategyInput
AgentOutput  →  RetryStrategyOutput
AgentInput  →  ShortTermMemoryInput
AgentOutput  →  ShortTermMemoryOutput
AgentInput  →  LongTermMemoryInput
AgentOutput  →  LongTermMemoryOutput
AgentInput  →  WorkflowOptimizerInput
AgentOutput  →  WorkflowOptimizerOutput
AgentInput  →  CostEfficiencyAnalyzerInput
AgentOutput  →  CostEfficiencyAnalyzerOutput
AgentInput  →  AgentPerformanceMonitorInput
AgentOutput  →  AgentPerformanceMonitorOutput
AgentInput  →  SystemHealthEvaluatorInput
AgentOutput  →  SystemHealthEvaluatorOutput
AgentInput  →  DialogueTutorInput
BaseModel  →  TutorResponse
AgentOutput  →  DialogueTutorOutput
AgentInput  →  StyleAdaptationInput
BaseModel  →  AdaptedContent
AgentOutput  →  StyleAdaptationOutput
AgentInput  →  ProgressAnalysisInput
AgentOutput  →  ProgressAnalysisOutput
AgentInput  →  LearningPathCreationInput
BaseModel  →  LearningStep
AgentOutput  →  LearningPathCreationOutput
AgentInput  →  ResourceRecommendationInput
BaseModel  →  RecommendedResource
AgentOutput  →  ResourceRecommendationOutput
AgentInput  →  InteractionStyleAnalysisInput
BaseModel  →  InteractionPattern
AgentOutput  →  InteractionStyleAnalysisOutput
AgentInput  →  QuestionRefineInput
AgentOutput  →  QuestionRefineOutput
AgentInput  →  QuestionGenerationInput
AgentOutput  →  QuestionGenerationOutput
AgentInput  →  HintGenerationInput
AgentOutput  →  HintGenerationOutput
AgentInput  →  ExplanationGenerationInput
AgentOutput  →  ExplanationGenerationOutput
AgentInput  →  DifficultyAdaptationInput
AgentOutput  →  DifficultyAdaptationOutput
AgentInput  →  MisconceptionDetectionInput
AgentOutput  →  Misconception
AgentOutput  →  MisconceptionDetectionOutput
BaseAgent  →  TextRewriterAgent
BaseOrchestrationBackend  →  AutoGenOrchestrationBackend
ABC  →  BaseOrchestrationBackend
BaseOrchestrationBackend  →  NativeOrchestrationBackend
InteractionStrategy  →  BroadcastStrategy
InteractionStrategy  →  CoordinatorStrategy
InteractionStrategy  →  DebateStrategy
InteractionStrategy  →  EnsembleStrategy
InteractionStrategy  →  GroupChatStrategy
BaseModel  →  InteractionRequest
BaseModel  →  InteractionResult
BaseModel  →  AgentMessage
InteractionStrategy  →  RoundRobinStrategy
InteractionStrategy  →  SelfRefineStrategy
Generic[TStrategy]  →  InteractionStrategyRegistry
BaseCompressor  →  EmbeddingCompressor
BaseCompressor  →  LLMCompressor
BaseModel  →  GraphNode
BaseModel  →  GraphEdge
ABC  →  BaseLLM
Protocol  →  AsyncLLM
BaseLLM  →  OllamaLLM
BaseLLM  →  OpenAILLM
BaseModel  →  RetrievalPlan
BaseModel  →  Document
BaseModel  →  DocumentChunk
BaseModel  →  RetrievedDocument
ABC  →  BaseReranker
BaseReranker  →  Reranker
Protocol  →  LLMProtocol
Protocol  →  LLMGenerateProtocol
Protocol  →  LLMInvokeProtocol
ABC  →  BaseResearchAgent
BaseModel  →  TokenUsage
BaseModel  →  TokenBreakdownResponse
BaseModel  →  RetrievalChunkStat
BaseModel  →  RetrievalHeatmapResponse
BaseModel  →  GraphPath
BaseModel  →  GraphPathsResponse
BaseModel  →  FailureEvent
BaseModel  →  FailureResponse
BaseModel  →  MemoryUsageResponse
BaseModel  →  TelemetryEventResponse
BaseModel  →  Evidence
BaseModel  →  ResearchAnswer
BaseModel  →  EvaluationResult
str  →  ReasoningEventType
Enum  →  ReasoningEventType
str  →  ReasoningLevel
Enum  →  ReasoningLevel
str  →  ReasoningPhase
Enum  →  ReasoningPhase
ABC  →  TelemetryEvent
ABC  →  Telemetry
BaseResearchAgent  →  ResearchAgent
ABC  →  BaseSummarizer
BaseSummarizer  →  ResearchSummarizer
BaseSummarizer  →  SectionSummarizer
ABC  →  BaseRetriever
BaseRetriever  →  BM25KeywordRetriever
BaseRetriever  →  HybridRetriever
BaseRetriever  →  HybridRetrieverPlus
BaseRetriever  →  HybridRetrieverSuper
BaseRetriever  →  KeywordRetriever
BaseRetriever  →  VectorRetriever
ABC  →  BaseTrainer
BaseTrainer  →  FusionTrainer
BaseTrainer  →  RerankerTrainer
BaseModel  →  QueryResult
StorageAdapter  →  LocalFileAdapter
StorageAdapter  →  RedisStorageAdapter
StorageAdapter  →  SQLStorage
ABC  →  StorageAdapter
ABC  →  BaseStorage
BaseStorage  →  DocumentStore
BaseStorage  →  LogStorage
VectorDBAdapter  →  ChromaAdapter
VectorDBAdapter  →  FaissAdapter
VectorDBAdapter  →  InMemoryVectorStore
VectorDBAdapter  →  PineconeAdapter
VectorDBAdapter  →  QdrantAdapter
VectorDBAdapter  →  WeaviateAdapter
ABC  →  VectorDBAdapter
AgentInput  →  SimpleInput
AgentOutput  →  SimpleOutput
BaseAgent  →  SimpleAgent
AgentInput  →  InputModel
AgentOutput  →  OutputModel
BaseAgent[InputModel, OutputModel]  →  EchoAgent
EchoAgent  →  FailingAgent
MessageBus  →  DummyMessageBus1
BaseOrchestrationBackend  →  DummyBackend
InteractionResult  →  Result
MessageBus  →  DummyMessageBus2
MessageBus  →  DummyMessageBus
BaseOrchestrationBackend  →  DummyBackend
InteractionResult  →  Result
```

---

### کلاس‌های Abstract / Interface

- **`MessageBus`** (`agents/buses/base.py`)
  - متدها: `publish`, `subscribe`, `unsubscribe`, `start`, `stop`
- **`BaseOrchestrationBackend`** (`agents/interaction/backends/base_backend.py`)
  - متدها: `execute`
- **`BaseLLM`** (`rag/llm/base_llm.py`)
  - متدها: `ainvoke`, `astream`
- **`BaseReranker`** (`rag/reranking/base_reranker.py`)
  - متدها: `rerank`
- **`BaseResearchAgent`** (`rag/research/base_research_agent.py`)
  - متدها: `run`
- **`TelemetryEvent`** (`rag/research/observability/telemetry.py`)
  - متدها: `__init__`, `to_dict`
- **`Telemetry`** (`rag/research/observability/telemetry.py`)
  - متدها: `__init__`, `emit`
- **`BaseSummarizer`** (`rag/research/summarization/base_summarizer.py`)
  - متدها: `summarize`
- **`BaseRetriever`** (`rag/retrieval/base_retriever.py`)
  - متدها: `search`
- **`BaseTrainer`** (`rag/trainer/base_trainer.py`)
  - متدها: `train`
- **`StorageAdapter`** (`storage/base_storage.py`)
  - متدها: `save`, `load`, `delete`, `list_keys`
- **`BaseStorage`** (`storage/base_storage.py`)
  - متدها: `add`, `get`, `delete`
- **`VectorDBAdapter`** (`storage/vector/base.py`)
  - متدها: `create_index`, `upsert`, `batch_upsert`, `query`, `delete`, `search`, `add_embeddings`, `delete_embeddings`

---

## 🔍 تحلیل مشکلات احتمالی


### 🟡 فایل‌های خالی یا فقط شامل import
- `config/settings.py`

### 🟠 کلاس‌های بدون Base Class (احتمال عدم رعایت interface مشترک)
- `InteractionStrategy` در `agents/interaction/base_strategy.py`
- `VectorService` در `rag/vector_service.py`

---

## 📝 یادداشت

این گزارش به صورت **استاتیک** (تحلیل AST) تولید شده است.  
برای تحلیل runtime و dependency injection، ابزار تکمیلی لازم است.
