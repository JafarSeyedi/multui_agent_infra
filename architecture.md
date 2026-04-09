# 📐 Architecture Report

> تولید شده توسط `tools/analyze_architecture.py`  
> تاریخ: 2026-04-10 00:33:07  
---

## 📊 آمار کلی

| معیار | مقدار |
|-------|-------|
| فایل‌های Python | 256 |
| کلاس‌ها | 507 |
| توابع سطح بالا | 81 |
| فایل‌های با خطا | 0 |

---

## 📂 ساختار فولدرها

```
📦 project/
  ├── 📁 agents/
  │   ├── 📁 buses/
  │   ├── 📁 content/
  │   └── 📁 orchestration/
  │       ├── 📁 backends/
  │       └── 📁 interaction/
  ├── 📁 config/
  │   └── 📁 models/
  │       ├── 📁 agent_io/
  │       ├── 📁 rag/
  │       └── 📁 system/
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
  │       └── 📁 orchestration/
  │           ├── 📁 interaction/
  │           │   ├── 📁 interaction_performance/
  │           │   └── 📁 interaction_unit/
  │           ├── 📁 orchestration_performance/
  │           └── 📁 orchestration_unit/
  └── 📁 tools/
```

---

## 🗂️ ساختار کامل (فولدرها + فایل‌ها)

```
📦 project/
  ├── 📁 agents/
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
  │   │   ├── 📄 __init__.py
  │   │   └── 📄 text_rewriter.py
  │   ├── 📁 orchestration/
  │   │   ├── 📁 backends/
  │   │   │   ├── 📄 __init__.py
  │   │   │   ├── 📄 autogen_backend.py
  │   │   │   ├── 📄 base_backend.py
  │   │   │   └── 📄 native_backend.py
  │   │   ├── 📁 interaction/
  │   │   │   ├── 📄 __init__.py
  │   │   │   ├── 📄 base_strategy.py
  │   │   │   ├── 📄 broadcast_strategy.py
  │   │   │   ├── 📄 conditional_strategy.py
  │   │   │   ├── 📄 dag_strategy.py
  │   │   │   ├── 📄 debate_strategy.py
  │   │   │   ├── 📄 ensemble_strategy.py
  │   │   │   ├── 📄 event_driven_strategy.py
  │   │   │   ├── 📄 group_chat_strategy.py
  │   │   │   ├── 📄 manager_strategy.py
  │   │   │   ├── 📄 memory_augmented_strategy.py
  │   │   │   ├── 📄 pipeline_strategy.py
  │   │   │   ├── 📄 round_robin_strategy.py
  │   │   │   ├── 📄 self_refine_strategy.py
  │   │   │   └── 📄 strategy_registry.py
  │   │   ├── 📄 __init__.py
  │   │   ├── 📄 models.py
  │   │   └── 📄 orchestrator_agent.py
  │   ├── 📄 __init__.py
  │   ├── 📄 agent_registry.py
  │   └── 📄 base_agent.py
  ├── 📁 config/
  │   ├── 📁 models/
  │   │   ├── 📁 agent_io/
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
  │   │   ├── 📁 rag/
  │   │   │   ├── 📄 __init__.py
  │   │   │   └── 📄 rag_models.py
  │   │   ├── 📁 system/
  │   │   │   ├── 📄 __init__.py
  │   │   │   ├── 📄 event_models.py
  │   │   │   ├── 📄 execution_models.py
  │   │   │   └── 📄 versioning_models.py
  │   │   └── 📄 __init__.py
  │   ├── 📄 __init__.py
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
  │   │   ├── 📁 orchestration/
  │   │   │   ├── 📁 interaction/
  │   │   │   │   ├── 📁 interaction_performance/
  │   │   │   │   │   ├── 📄 __init__.py
  │   │   │   │   │   ├── 📄 conftest_performance.py
  │   │   │   │   │   ├── 📄 test_broadcast_strategy_performance.py
  │   │   │   │   │   ├── 📄 test_conditional_strategy_performance.py
  │   │   │   │   │   ├── 📄 test_dag_strategy_performance.py
  │   │   │   │   │   ├── 📄 test_debate_strategy_performance.py
  │   │   │   │   │   ├── 📄 test_ensemble_strategy_performance.py
  │   │   │   │   │   ├── 📄 test_event_driven_strategy_performance.py
  │   │   │   │   │   ├── 📄 test_group_chat_strategy_performance.py
  │   │   │   │   │   ├── 📄 test_manager_strategy_performance.py
  │   │   │   │   │   ├── 📄 test_memory_augmented_strategy_performance.py
  │   │   │   │   │   ├── 📄 test_pipeline_strategy_performance.py
  │   │   │   │   │   └── 📄 test_self_refine_strategy_performance.py
  │   │   │   │   ├── 📁 interaction_unit/
  │   │   │   │   │   ├── 📄 __init__.py
  │   │   │   │   │   ├── 📄 conftest.py
  │   │   │   │   │   ├── 📄 test_broadcast_strategy.py
  │   │   │   │   │   ├── 📄 test_conditional_strategy.py
  │   │   │   │   │   ├── 📄 test_dag_strategy.py
  │   │   │   │   │   ├── 📄 test_debate_strategy.py
  │   │   │   │   │   ├── 📄 test_ensemble_strategy.py
  │   │   │   │   │   ├── 📄 test_event_driven_strategy.py
  │   │   │   │   │   ├── 📄 test_group_chat_strategy.py
  │   │   │   │   │   ├── 📄 test_manager_strategy.py
  │   │   │   │   │   ├── 📄 test_memory_augmented_strategy.py
  │   │   │   │   │   ├── 📄 test_pipeline_strategy.py
  │   │   │   │   │   └── 📄 test_self_refine_strategy.py
  │   │   │   │   └── 📄 __init__.py
  │   │   │   ├── 📁 orchestration_performance/
  │   │   │   │   ├── 📄 __init__.py
  │   │   │   │   ├── 📄 test_native_orchestration_backend_performance.py
  │   │   │   │   └── 📄 test_orchestrator_agent_performance.py
  │   │   │   ├── 📁 orchestration_unit/
  │   │   │   │   ├── 📄 __init__.py
  │   │   │   │   ├── 📄 test_autogen_orchestration_backend.py
  │   │   │   │   ├── 📄 test_models.py
  │   │   │   │   ├── 📄 test_native_orchestration_backend.py
  │   │   │   │   └── 📄 test_orchestrator_agent.py
  │   │   │   └── 📄 __init__.py
  │   │   └── 📄 __init__.py
  │   └── 📄 __init__.py
  └── 📁 tools/
      ├── 📄 __init__.py
      ├── 📄 analyze_architecture.py
      ├── 📄 code_auditor.py
      ├── 📄 convert_agents_to_jsons.py
      └── 📄 generate_inits.py
```

---

## 🏛️ کلاس‌ها و وراثت

### جدول کامل کلاس‌ها

| فایل | کلاس | والدین | متدها |
|------|------|--------|-------|
| `agents/agent_registry.py` | `AgentRegistry` | `—` | `__init__, register, get, run` |
| `agents/base_agent.py` | `BaseAgent` | `Generic[TInput, TOutput]` | `__init__, run, run_sync, execute, _validate_input, _validate_output ...` |
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
| `agents/content/text_rewriter.py` | `TextRewriterAgent` | `BaseAgent` | `execute, _rewrite_text, _fallback_rewrite, _estimate_readability` |
| `agents/orchestration/backends/autogen_backend.py` | `AutoGenOrchestrationBackend` | `BaseOrchestrationBackend` | `__init__, _autogen_available, is_available, execute, _execute_with_autogen_group_chat` |
| `agents/orchestration/backends/base_backend.py` | `BaseOrchestrationBackend` | `ABC` | `execute` |
| `agents/orchestration/backends/native_backend.py` | `NativeOrchestrationBackend` | `BaseOrchestrationBackend` | `__init__, _build_strategy, execute` |
| `agents/orchestration/interaction/base_strategy.py` | `InteractionStrategy` | `ABC` | `__init__, execute, _emit` |
| `agents/orchestration/interaction/broadcast_strategy.py` | `BroadcastStrategy` | `InteractionStrategy` | `execute, _execute_task, _normalize_gather_results, _aggregate_outputs` |
| `agents/orchestration/interaction/conditional_strategy.py` | `ConditionalStrategy` | `InteractionStrategy` | `execute, _select_next_task` |
| `agents/orchestration/interaction/dag_strategy.py` | `DAGStrategy` | `InteractionStrategy` | `execute, _validate_dag, _execute_task, visit` |
| `agents/orchestration/interaction/debate_strategy.py` | `DebateStrategy` | `InteractionStrategy` | `execute` |
| `agents/orchestration/interaction/ensemble_strategy.py` | `EnsembleStrategy` | `InteractionStrategy` | `__init__, execute, _aggregate_votes, _publish_vote, _normalize_output` |
| `agents/orchestration/interaction/event_driven_strategy.py` | `EventDrivenStrategy` | `InteractionStrategy` | `execute, _build_event_map, _execute_listener, _extract_events` |
| `agents/orchestration/interaction/group_chat_strategy.py` | `GroupChatStrategy` | `InteractionStrategy` | `__init__, execute, _init_messages, _resolve_participants, _extract_message, _extract_context_update ...` |
| `agents/orchestration/interaction/manager_strategy.py` | `ManagerStrategy` | `InteractionStrategy` | `__init__, execute, _run_validation, _aggregate, _publish_turn_message, _normalize_output` |
| `agents/orchestration/interaction/memory_augmented_strategy.py` | `MemoryAugmentedStrategy` | `InteractionStrategy` | `__init__, execute, _prioritize_tasks, _publish_memory_update, _normalize_output` |
| `agents/orchestration/interaction/pipeline_strategy.py` | `PipelineStrategy` | `InteractionStrategy` | `execute, _execute_task` |
| `agents/orchestration/interaction/round_robin_strategy.py` | `RoundRobinStrategy` | `InteractionStrategy` | `__init__, execute, _normalize_output` |
| `agents/orchestration/interaction/self_refine_strategy.py` | `SelfRefineStrategy` | `InteractionStrategy` | `execute, _safe_execute, _extract_score` |
| `agents/orchestration/interaction/strategy_registry.py` | `InteractionStrategyRegistry` | `Generic[TStrategy]` | `__init__, register, unregister, get, require, list_scenarios ...` |
| `agents/orchestration/models.py` | `TaskDefinition` | `BaseModel` | `` |
| `agents/orchestration/models.py` | `OrchestrationRequest` | `BaseModel` | `` |
| `agents/orchestration/models.py` | `TaskResult` | `BaseModel` | `` |
| `agents/orchestration/models.py` | `OrchestrationResult` | `BaseModel` | `` |
| `agents/orchestration/models.py` | `AgentMessage` | `BaseModel` | `` |
| `agents/orchestration/models.py` | `PipelineStep` | `BaseModel` | `` |
| `agents/orchestration/models.py` | `AgentInteraction` | `BaseModel` | `` |
| `agents/orchestration/models.py` | `ConversationTurn` | `BaseModel` | `` |
| `agents/orchestration/orchestrator_agent.py` | `OrchestratorAgent` | `BaseAgent` | `__init__, run` |
| `config/models/agent_io/analytics_agents_31_40.py` | `StudentBehaviorAnalysisInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/analytics_agents_31_40.py` | `BehaviorPattern` | `BaseModel` | `` |
| `config/models/agent_io/analytics_agents_31_40.py` | `StudentBehaviorAnalysisOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/analytics_agents_31_40.py` | `EngagementDetectionInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/analytics_agents_31_40.py` | `EngagementDetectionOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/analytics_agents_31_40.py` | `MotivationAnalysisInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/analytics_agents_31_40.py` | `MotivationAnalysisOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/analytics_agents_31_40.py` | `DropoutRiskPredictionInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/analytics_agents_31_40.py` | `DropoutRiskPredictionOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/analytics_agents_31_40.py` | `StudyPatternMiningInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/analytics_agents_31_40.py` | `StudyPattern` | `BaseModel` | `` |
| `config/models/agent_io/analytics_agents_31_40.py` | `StudyPatternMiningOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/analytics_agents_31_40.py` | `PerformanceTrendAnalysisInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/analytics_agents_31_40.py` | `PerformanceTrend` | `BaseModel` | `` |
| `config/models/agent_io/analytics_agents_31_40.py` | `PerformanceTrendAnalysisOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/analytics_agents_31_40.py` | `LearningOutcomePredictionInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/analytics_agents_31_40.py` | `LearningOutcomePredictionOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/analytics_agents_31_40.py` | `ClassroomAnalyticsInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/analytics_agents_31_40.py` | `ClassroomAnalyticsOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/analytics_agents_31_40.py` | `CohortComparisonInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/analytics_agents_31_40.py` | `CohortComparisonOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/analytics_agents_31_40.py` | `TeacherDashboardAggregationInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/analytics_agents_31_40.py` | `TeacherDashboardAggregationOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/assessment_agents_21_30.py` | `QuizBuilderInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/assessment_agents_21_30.py` | `QuizQuestion` | `BaseModel` | `` |
| `config/models/agent_io/assessment_agents_21_30.py` | `QuizBuilderOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/assessment_agents_21_30.py` | `AnswerEvaluationInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/assessment_agents_21_30.py` | `AnswerEvaluationOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/assessment_agents_21_30.py` | `FeedbackGenerationInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/assessment_agents_21_30.py` | `FeedbackGenerationOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/assessment_agents_21_30.py` | `RubricGenerationInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/assessment_agents_21_30.py` | `RubricCriterion` | `BaseModel` | `` |
| `config/models/agent_io/assessment_agents_21_30.py` | `RubricGenerationOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/assessment_agents_21_30.py` | `MisconceptionAnalysisInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/assessment_agents_21_30.py` | `MisconceptionPattern` | `BaseModel` | `` |
| `config/models/agent_io/assessment_agents_21_30.py` | `MisconceptionAnalysisOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/assessment_agents_21_30.py` | `SkillMasteryInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/assessment_agents_21_30.py` | `SkillMasteryOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/assessment_agents_21_30.py` | `LearningGapInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/assessment_agents_21_30.py` | `LearningGap` | `BaseModel` | `` |
| `config/models/agent_io/assessment_agents_21_30.py` | `LearningGapOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/assessment_agents_21_30.py` | `KnowledgeGraphUpdateInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/assessment_agents_21_30.py` | `KnowledgeGraphUpdateOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/assessment_agents_21_30.py` | `ConceptDifficultyInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/assessment_agents_21_30.py` | `ConceptDifficultyOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/assessment_agents_21_30.py` | `CurriculumMappingInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/assessment_agents_21_30.py` | `CurriculumMapping` | `BaseModel` | `` |
| `config/models/agent_io/assessment_agents_21_30.py` | `CurriculumMappingOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/common.py` | `ConfidenceScore` | `BaseModel` | `` |
| `config/models/agent_io/common.py` | `ScoreRange` | `BaseModel` | `` |
| `config/models/agent_io/common.py` | `Evidence` | `BaseModel` | `` |
| `config/models/agent_io/common.py` | `ReasoningTrace` | `BaseModel` | `` |
| `config/models/agent_io/common.py` | `Recommendation` | `BaseModel` | `` |
| `config/models/agent_io/common.py` | `ActionSuggestion` | `BaseModel` | `` |
| `config/models/agent_io/common.py` | `ConceptReference` | `BaseModel` | `` |
| `config/models/agent_io/common.py` | `ResourceReference` | `BaseModel` | `` |
| `config/models/agent_io/common.py` | `DetectedIssue` | `BaseModel` | `` |
| `config/models/agent_io/common.py` | `Pattern` | `BaseModel` | `` |
| `config/models/agent_io/common.py` | `Prediction` | `BaseModel` | `` |
| `config/models/agent_io/common.py` | `TimeWindow` | `BaseModel` | `` |
| `config/models/agent_io/content_agents_1_8.py` | `TextRewriteInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/content_agents_1_8.py` | `RewriteChange` | `BaseModel` | `` |
| `config/models/agent_io/content_agents_1_8.py` | `TextRewriteOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/content_agents_1_8.py` | `ContentValidationInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/content_agents_1_8.py` | `ValidationIssue` | `BaseModel` | `` |
| `config/models/agent_io/content_agents_1_8.py` | `ContentValidationOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/content_agents_1_8.py` | `CitationGenerationInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/content_agents_1_8.py` | `CitationEntry` | `BaseModel` | `` |
| `config/models/agent_io/content_agents_1_8.py` | `CitationGenerationOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/content_agents_1_8.py` | `GlossaryBuilderInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/content_agents_1_8.py` | `GlossaryTerm` | `BaseModel` | `` |
| `config/models/agent_io/content_agents_1_8.py` | `GlossaryBuilderOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/content_agents_1_8.py` | `DynamicUpdateInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/content_agents_1_8.py` | `ContentUpdateSuggestion` | `BaseModel` | `` |
| `config/models/agent_io/content_agents_1_8.py` | `DynamicUpdateOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/content_agents_1_8.py` | `NarrativeBuilderInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/content_agents_1_8.py` | `NarrativeElement` | `BaseModel` | `` |
| `config/models/agent_io/content_agents_1_8.py` | `NarrativeBuilderOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/content_agents_1_8.py` | `StructuringInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/content_agents_1_8.py` | `LessonSection` | `BaseModel` | `` |
| `config/models/agent_io/content_agents_1_8.py` | `StructuringOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/content_agents_1_8.py` | `PrerequisiteInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/content_agents_1_8.py` | `PrerequisiteItem` | `BaseModel` | `` |
| `config/models/agent_io/content_agents_1_8.py` | `PrerequisiteOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/content_generation_agents_91_100.py` | `ExampleGeneratorInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/content_generation_agents_91_100.py` | `ExampleGeneratorOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/content_generation_agents_91_100.py` | `ExerciseCreatorInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/content_generation_agents_91_100.py` | `ExerciseCreatorOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/content_generation_agents_91_100.py` | `StoryLessonCreatorInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/content_generation_agents_91_100.py` | `StoryLessonCreatorOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/content_generation_agents_91_100.py` | `ConceptExplanationInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/content_generation_agents_91_100.py` | `ConceptExplanationOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/content_generation_agents_91_100.py` | `PracticeQuestionGeneratorInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/content_generation_agents_91_100.py` | `PracticeQuestionGeneratorOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/content_generation_agents_91_100.py` | `AdaptiveQuestionGeneratorInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/content_generation_agents_91_100.py` | `AdaptiveQuestionGeneratorOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/content_generation_agents_91_100.py` | `ExplanationRewriterInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/content_generation_agents_91_100.py` | `ExplanationRewriterOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/content_generation_agents_91_100.py` | `SummaryGeneratorInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/content_generation_agents_91_100.py` | `SummaryGeneratorOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/content_generation_agents_91_100.py` | `ContentSimplifierInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/content_generation_agents_91_100.py` | `ContentSimplifierOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/content_generation_agents_91_100.py` | `AssessmentQuestionGeneratorInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/content_generation_agents_91_100.py` | `AssessmentQuestionGeneratorOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `ConceptGraphBuilderInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `ConceptGraphBuilderOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `ConceptRelationExtractorInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `ConceptRelationExtractorOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `PrerequisiteInferenceInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `PrerequisiteInferenceOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `CurriculumPlannerInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `CurriculumPlannerOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `LessonSequencePlannerInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `LessonSequencePlannerOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `LearningPathGeneratorInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `LearningPathGeneratorOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `PersonalizedCurriculumInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `PersonalizedCurriculumOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `SkillGapCurriculumAdapterInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `SkillGapCurriculumAdapterOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `DifficultyBalancerInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `DifficultyBalancerOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `StudyStrategyPlannerInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `StudyStrategyPlannerOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `ReviewSchedulerInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `ReviewSchedulerOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `RemediationPlannerInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `RemediationPlannerOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `EnrichmentPlannerInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `EnrichmentPlannerOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `ConceptReinforcementInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `ConceptReinforcementOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `LongTermLearningPlannerInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/curriculum_agents_46_60.py` | `LongTermLearningPlannerOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/evaluation_agents_41_45.py` | `EvaluationCriterion` | `BaseModel` | `` |
| `config/models/agent_io/evaluation_agents_41_45.py` | `EvaluationScore` | `BaseModel` | `` |
| `config/models/agent_io/evaluation_agents_41_45.py` | `EvaluationIssue` | `BaseModel` | `` |
| `config/models/agent_io/evaluation_agents_41_45.py` | `AlignmentResult` | `BaseModel` | `` |
| `config/models/agent_io/evaluation_agents_41_45.py` | `ConsistencyError` | `BaseModel` | `` |
| `config/models/agent_io/evaluation_agents_41_45.py` | `CoverageGap` | `BaseModel` | `` |
| `config/models/agent_io/evaluation_agents_41_45.py` | `QuestionQualityEvaluationInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/evaluation_agents_41_45.py` | `QuestionQualityEvaluationOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/evaluation_agents_41_45.py` | `ExplanationQualityEvaluationInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/evaluation_agents_41_45.py` | `ExplanationQualityEvaluationOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/evaluation_agents_41_45.py` | `PedagogicalAlignmentInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/evaluation_agents_41_45.py` | `PedagogicalAlignmentOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/evaluation_agents_41_45.py` | `ConsistencyEvaluationInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/evaluation_agents_41_45.py` | `ConsistencyEvaluationOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/evaluation_agents_41_45.py` | `CurriculumCoverageInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/evaluation_agents_41_45.py` | `CurriculumCoverageOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/learning_objects.py` | `StudentProfile` | `BaseModel` | `` |
| `config/models/agent_io/learning_objects.py` | `InstructorProfile` | `BaseModel` | `` |
| `config/models/agent_io/learning_objects.py` | `VAKRStyle` | `str, Enum` | `` |
| `config/models/agent_io/learning_objects.py` | `PacePreference` | `str, Enum` | `` |
| `config/models/agent_io/learning_objects.py` | `AbstractionLevel` | `str, Enum` | `` |
| `config/models/agent_io/learning_objects.py` | `FeedbackPreference` | `str, Enum` | `` |
| `config/models/agent_io/learning_objects.py` | `LearningStyle` | `BaseModel` | `` |
| `config/models/agent_io/learning_objects.py` | `LearningObjective` | `BaseModel` | `` |
| `config/models/agent_io/learning_objects.py` | `Lesson` | `BaseModel` | `` |
| `config/models/agent_io/learning_objects.py` | `ConceptNode` | `BaseModel` | `` |
| `config/models/agent_io/learning_objects.py` | `GlossaryEntry` | `BaseModel` | `` |
| `config/models/agent_io/learning_objects.py` | `Question` | `BaseModel` | `` |
| `config/models/agent_io/learning_objects.py` | `StudentAnswer` | `BaseModel` | `` |
| `config/models/agent_io/learning_objects.py` | `AssessmentResult` | `BaseModel` | `` |
| `config/models/agent_io/learning_objects.py` | `Assignment` | `BaseModel` | `` |
| `config/models/agent_io/learning_objects.py` | `LearningEvent` | `BaseModel` | `` |
| `config/models/agent_io/learning_objects.py` | `SkillPerformance` | `BaseModel` | `` |
| `config/models/agent_io/learning_objects.py` | `LearningProgress` | `BaseModel` | `` |
| `config/models/agent_io/learning_objects.py` | `LearningResource` | `BaseModel` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `KnowledgeIngestionInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `KnowledgeIngestionOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `DocumentChunkingInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `DocumentChunkingOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `EmbeddingGeneratorInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `EmbeddingGeneratorOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `SemanticIndexerInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `SemanticIndexerOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `VectorSearchInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `VectorSearchOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `HybridRetrievalInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `HybridRetrievalOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `ContextBuilderInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `ContextBuilderOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `MemoryConsolidationInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `MemoryConsolidationOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `EpisodicMemoryInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `EpisodicMemoryOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `StudentKnowledgeMemoryInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `StudentKnowledgeMemoryOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `KnowledgeUpdaterInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `KnowledgeUpdaterOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `KnowledgeConflictResolverInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `KnowledgeConflictResolverOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `RetrievalRankerInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `RetrievalRankerOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `ContextRelevanceEvaluatorInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `ContextRelevanceEvaluatorOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `KnowledgeSummarizerInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/memory_agents_76_90.py` | `KnowledgeSummarizerOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/multimodal_agents_101_110.py` | `TextToSpeechInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/multimodal_agents_101_110.py` | `TextToSpeechOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/multimodal_agents_101_110.py` | `SpeechToTextInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/multimodal_agents_101_110.py` | `SpeechToTextOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/multimodal_agents_101_110.py` | `VisualIllustrationInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/multimodal_agents_101_110.py` | `VisualIllustrationOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/multimodal_agents_101_110.py` | `BoardDrawingInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/multimodal_agents_101_110.py` | `BoardDrawingOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/multimodal_agents_101_110.py` | `EmotionAnalysisInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/multimodal_agents_101_110.py` | `EmotionAnalysisOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/multimodal_agents_101_110.py` | `EngagementDetectorInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/multimodal_agents_101_110.py` | `EngagementDetectorOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/multimodal_agents_101_110.py` | `VisualFeedbackInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/multimodal_agents_101_110.py` | `VisualFeedbackOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/multimodal_agents_101_110.py` | `GestureRecognitionInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/multimodal_agents_101_110.py` | `GestureRecognitionOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/multimodal_agents_101_110.py` | `AudioFeedbackInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/multimodal_agents_101_110.py` | `AudioFeedbackOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/multimodal_agents_101_110.py` | `InteractiveLessonOrchestratorInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/multimodal_agents_101_110.py` | `InteractiveLessonOrchestratorOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `LearningSessionPlannerInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `LearningSessionPlannerOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `AgentWorkflowPlannerInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `AgentWorkflowPlannerOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `TaskDecomposerInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `TaskDecomposerOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `AgentSelectorInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `AgentSelectorOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `ContextManagerInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `ContextManagerOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `WorkflowStateTrackerInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `WorkflowStateTrackerOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `FailureRecoveryInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `FailureRecoveryOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `RetryStrategyInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `RetryStrategyOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `ShortTermMemoryInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `ShortTermMemoryOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `LongTermMemoryInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `LongTermMemoryOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `WorkflowOptimizerInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `WorkflowOptimizerOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `CostEfficiencyAnalyzerInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `CostEfficiencyAnalyzerOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `AgentPerformanceMonitorInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `AgentPerformanceMonitorOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `SystemHealthEvaluatorInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/orchestration_agents_61_75.py` | `SystemHealthEvaluatorOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/personalization_agents_15_20.py` | `DialogueTutorInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/personalization_agents_15_20.py` | `TutorResponse` | `BaseModel` | `` |
| `config/models/agent_io/personalization_agents_15_20.py` | `DialogueTutorOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/personalization_agents_15_20.py` | `StyleAdaptationInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/personalization_agents_15_20.py` | `AdaptedContent` | `BaseModel` | `` |
| `config/models/agent_io/personalization_agents_15_20.py` | `StyleAdaptationOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/personalization_agents_15_20.py` | `ProgressAnalysisInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/personalization_agents_15_20.py` | `ProgressAnalysisOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/personalization_agents_15_20.py` | `LearningPathCreationInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/personalization_agents_15_20.py` | `LearningStep` | `BaseModel` | `` |
| `config/models/agent_io/personalization_agents_15_20.py` | `LearningPathCreationOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/personalization_agents_15_20.py` | `ResourceRecommendationInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/personalization_agents_15_20.py` | `RecommendedResource` | `BaseModel` | `` |
| `config/models/agent_io/personalization_agents_15_20.py` | `ResourceRecommendationOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/personalization_agents_15_20.py` | `InteractionStyleAnalysisInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/personalization_agents_15_20.py` | `InteractionPattern` | `BaseModel` | `` |
| `config/models/agent_io/personalization_agents_15_20.py` | `InteractionStyleAnalysisOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/teaching_agents_9_14.py` | `QuestionRefineInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/teaching_agents_9_14.py` | `QuestionRefineOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/teaching_agents_9_14.py` | `QuestionGenerationInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/teaching_agents_9_14.py` | `QuestionGenerationOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/teaching_agents_9_14.py` | `HintGenerationInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/teaching_agents_9_14.py` | `HintGenerationOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/teaching_agents_9_14.py` | `ExplanationGenerationInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/teaching_agents_9_14.py` | `ExplanationGenerationOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/teaching_agents_9_14.py` | `DifficultyAdaptationInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/teaching_agents_9_14.py` | `DifficultyAdaptationOutput` | `OrchestrationResult` | `` |
| `config/models/agent_io/teaching_agents_9_14.py` | `MisconceptionDetectionInput` | `OrchestrationRequest` | `` |
| `config/models/agent_io/teaching_agents_9_14.py` | `Misconception` | `OrchestrationResult` | `` |
| `config/models/agent_io/teaching_agents_9_14.py` | `MisconceptionDetectionOutput` | `OrchestrationResult` | `` |
| `config/models/rag/rag_models.py` | `Document` | `BaseModel` | `` |
| `config/models/rag/rag_models.py` | `DocumentChunk` | `BaseModel` | `` |
| `config/models/rag/rag_models.py` | `RetrievedDocument` | `BaseModel` | `` |
| `config/models/system/event_models.py` | `PipelineEvent` | `BaseModel` | `` |
| `config/models/system/event_models.py` | `StudentStateEvent` | `BaseModel` | `` |
| `config/models/system/event_models.py` | `RuntimeErrorLog` | `BaseModel` | `` |
| `config/models/system/event_models.py` | `MemorySnapshot` | `BaseModel` | `` |
| `config/models/system/event_models.py` | `SystemEvent` | `BaseModel` | `` |
| `config/models/system/execution_models.py` | `AgentExecutionRecord` | `BaseModel` | `` |
| `config/models/system/execution_models.py` | `TaskExecutionRecord` | `BaseModel` | `` |
| `config/models/system/execution_models.py` | `WorkflowExecutionRecord` | `BaseModel` | `` |
| `config/models/system/versioning_models.py` | `ContentVersion` | `BaseModel` | `` |
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
| `tests/agents/agents_unit/test_agent_registry.py` | `SimpleInput` | `OrchestrationRequest` | `` |
| `tests/agents/agents_unit/test_agent_registry.py` | `SimpleOutput` | `OrchestrationResult` | `` |
| `tests/agents/agents_unit/test_agent_registry.py` | `SimpleAgent` | `BaseAgent` | `execute` |
| `tests/agents/agents_unit/test_base_agent.py` | `InputModel` | `OrchestrationRequest` | `` |
| `tests/agents/agents_unit/test_base_agent.py` | `OutputModel` | `OrchestrationResult` | `` |
| `tests/agents/agents_unit/test_base_agent.py` | `EchoAgent` | `BaseAgent[InputModel, OutputModel]` | `execute` |
| `tests/agents/agents_unit/test_base_agent.py` | `FailingAgent` | `EchoAgent` | `execute` |
| `tests/agents/orchestration/interaction/interaction_unit/conftest.py` | `TestAgent` | `—` | `__init__, execute` |
| `tests/agents/orchestration/interaction/interaction_unit/conftest.py` | `TestRegistry` | `—` | `__init__, register, execute` |
| `tests/agents/orchestration/interaction/interaction_unit/conftest.py` | `DummyMessageBus` | `MessageBus` | `__init__, publish, subscribe, unsubscribe` |
| `tests/agents/orchestration/orchestration_performance/test_native_orchestration_backend_performance.py` | `DummyOutput` | `—` | `__init__, model_dump` |
| `tests/agents/orchestration/orchestration_performance/test_native_orchestration_backend_performance.py` | `SimpleRegistry` | `—` | `execute` |
| `tests/agents/orchestration/orchestration_performance/test_orchestrator_agent_performance.py` | `DummyBackend` | `BaseOrchestrationBackend` | `__init__, execute, model_dump` |
| `tests/agents/orchestration/orchestration_performance/test_orchestrator_agent_performance.py` | `Result` | `OrchestrationResult` | `model_dump` |
| `tests/agents/orchestration/orchestration_unit/test_autogen_orchestration_backend.py` | `DummyRegistry` | `—` | `execute` |
| `tests/agents/orchestration/orchestration_unit/test_autogen_orchestration_backend.py` | `DummyMessageBus` | `MessageBus` | `publish, subscribe, unsubscribe` |
| `tests/agents/orchestration/orchestration_unit/test_autogen_orchestration_backend.py` | `DummyResult` | `—` | `__init__, execute` |
| `tests/agents/orchestration/orchestration_unit/test_autogen_orchestration_backend.py` | `SimpleRequest` | `—` | `__init__` |
| `tests/agents/orchestration/orchestration_unit/test_native_orchestration_backend.py` | `DummyOutput` | `—` | `__init__, model_dump` |
| `tests/agents/orchestration/orchestration_unit/test_native_orchestration_backend.py` | `DummyRegistry` | `—` | `__init__, execute` |
| `tests/agents/orchestration/orchestration_unit/test_native_orchestration_backend.py` | `DummyMessageBus` | `MessageBus` | `__init__, publish, subscribe, unsubscribe` |
| `tests/agents/orchestration/orchestration_unit/test_orchestrator_agent.py` | `DummyBackend` | `BaseOrchestrationBackend` | `__init__, execute, model_dump` |
| `tests/agents/orchestration/orchestration_unit/test_orchestrator_agent.py` | `Result` | `OrchestrationResult` | `model_dump` |
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
ABC  →  MessageBus
MessageBus  →  DurableMessageBus
MessageBus  →  InMemoryMessageBus
MessageBus  →  KafkaMessageBus
MessageBus  →  PriorityMessageBus
MessageBus  →  RabbitMQMessageBus
MessageBus  →  RedisMessageBus
MessageBus  →  RequestReplyBus
MessageBus  →  TopicMessageBus
BaseAgent  →  TextRewriterAgent
BaseOrchestrationBackend  →  AutoGenOrchestrationBackend
ABC  →  BaseOrchestrationBackend
BaseOrchestrationBackend  →  NativeOrchestrationBackend
ABC  →  InteractionStrategy
InteractionStrategy  →  BroadcastStrategy
InteractionStrategy  →  ConditionalStrategy
InteractionStrategy  →  DAGStrategy
InteractionStrategy  →  DebateStrategy
InteractionStrategy  →  EnsembleStrategy
InteractionStrategy  →  EventDrivenStrategy
InteractionStrategy  →  GroupChatStrategy
InteractionStrategy  →  ManagerStrategy
InteractionStrategy  →  MemoryAugmentedStrategy
InteractionStrategy  →  PipelineStrategy
InteractionStrategy  →  RoundRobinStrategy
InteractionStrategy  →  SelfRefineStrategy
Generic[TStrategy]  →  InteractionStrategyRegistry
BaseModel  →  TaskDefinition
BaseModel  →  OrchestrationRequest
BaseModel  →  TaskResult
BaseModel  →  OrchestrationResult
BaseModel  →  AgentMessage
BaseModel  →  PipelineStep
BaseModel  →  AgentInteraction
BaseModel  →  ConversationTurn
BaseAgent  →  OrchestratorAgent
OrchestrationRequest  →  StudentBehaviorAnalysisInput
BaseModel  →  BehaviorPattern
OrchestrationResult  →  StudentBehaviorAnalysisOutput
OrchestrationRequest  →  EngagementDetectionInput
OrchestrationResult  →  EngagementDetectionOutput
OrchestrationRequest  →  MotivationAnalysisInput
OrchestrationResult  →  MotivationAnalysisOutput
OrchestrationRequest  →  DropoutRiskPredictionInput
OrchestrationResult  →  DropoutRiskPredictionOutput
OrchestrationRequest  →  StudyPatternMiningInput
BaseModel  →  StudyPattern
OrchestrationResult  →  StudyPatternMiningOutput
OrchestrationRequest  →  PerformanceTrendAnalysisInput
BaseModel  →  PerformanceTrend
OrchestrationResult  →  PerformanceTrendAnalysisOutput
OrchestrationRequest  →  LearningOutcomePredictionInput
OrchestrationResult  →  LearningOutcomePredictionOutput
OrchestrationRequest  →  ClassroomAnalyticsInput
OrchestrationResult  →  ClassroomAnalyticsOutput
OrchestrationRequest  →  CohortComparisonInput
OrchestrationResult  →  CohortComparisonOutput
OrchestrationRequest  →  TeacherDashboardAggregationInput
OrchestrationResult  →  TeacherDashboardAggregationOutput
OrchestrationRequest  →  QuizBuilderInput
BaseModel  →  QuizQuestion
OrchestrationResult  →  QuizBuilderOutput
OrchestrationRequest  →  AnswerEvaluationInput
OrchestrationResult  →  AnswerEvaluationOutput
OrchestrationRequest  →  FeedbackGenerationInput
OrchestrationResult  →  FeedbackGenerationOutput
OrchestrationRequest  →  RubricGenerationInput
BaseModel  →  RubricCriterion
OrchestrationResult  →  RubricGenerationOutput
OrchestrationRequest  →  MisconceptionAnalysisInput
BaseModel  →  MisconceptionPattern
OrchestrationResult  →  MisconceptionAnalysisOutput
OrchestrationRequest  →  SkillMasteryInput
OrchestrationResult  →  SkillMasteryOutput
OrchestrationRequest  →  LearningGapInput
BaseModel  →  LearningGap
OrchestrationResult  →  LearningGapOutput
OrchestrationRequest  →  KnowledgeGraphUpdateInput
OrchestrationResult  →  KnowledgeGraphUpdateOutput
OrchestrationRequest  →  ConceptDifficultyInput
OrchestrationResult  →  ConceptDifficultyOutput
OrchestrationRequest  →  CurriculumMappingInput
BaseModel  →  CurriculumMapping
OrchestrationResult  →  CurriculumMappingOutput
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
OrchestrationRequest  →  TextRewriteInput
BaseModel  →  RewriteChange
OrchestrationResult  →  TextRewriteOutput
OrchestrationRequest  →  ContentValidationInput
BaseModel  →  ValidationIssue
OrchestrationResult  →  ContentValidationOutput
OrchestrationRequest  →  CitationGenerationInput
BaseModel  →  CitationEntry
OrchestrationResult  →  CitationGenerationOutput
OrchestrationRequest  →  GlossaryBuilderInput
BaseModel  →  GlossaryTerm
OrchestrationResult  →  GlossaryBuilderOutput
OrchestrationRequest  →  DynamicUpdateInput
BaseModel  →  ContentUpdateSuggestion
OrchestrationResult  →  DynamicUpdateOutput
OrchestrationRequest  →  NarrativeBuilderInput
BaseModel  →  NarrativeElement
OrchestrationResult  →  NarrativeBuilderOutput
OrchestrationRequest  →  StructuringInput
BaseModel  →  LessonSection
OrchestrationResult  →  StructuringOutput
OrchestrationRequest  →  PrerequisiteInput
BaseModel  →  PrerequisiteItem
OrchestrationResult  →  PrerequisiteOutput
OrchestrationRequest  →  ExampleGeneratorInput
OrchestrationResult  →  ExampleGeneratorOutput
OrchestrationRequest  →  ExerciseCreatorInput
OrchestrationResult  →  ExerciseCreatorOutput
OrchestrationRequest  →  StoryLessonCreatorInput
OrchestrationResult  →  StoryLessonCreatorOutput
OrchestrationRequest  →  ConceptExplanationInput
OrchestrationResult  →  ConceptExplanationOutput
OrchestrationRequest  →  PracticeQuestionGeneratorInput
OrchestrationResult  →  PracticeQuestionGeneratorOutput
OrchestrationRequest  →  AdaptiveQuestionGeneratorInput
OrchestrationResult  →  AdaptiveQuestionGeneratorOutput
OrchestrationRequest  →  ExplanationRewriterInput
OrchestrationResult  →  ExplanationRewriterOutput
OrchestrationRequest  →  SummaryGeneratorInput
OrchestrationResult  →  SummaryGeneratorOutput
OrchestrationRequest  →  ContentSimplifierInput
OrchestrationResult  →  ContentSimplifierOutput
OrchestrationRequest  →  AssessmentQuestionGeneratorInput
OrchestrationResult  →  AssessmentQuestionGeneratorOutput
OrchestrationRequest  →  ConceptGraphBuilderInput
OrchestrationResult  →  ConceptGraphBuilderOutput
OrchestrationRequest  →  ConceptRelationExtractorInput
OrchestrationResult  →  ConceptRelationExtractorOutput
OrchestrationRequest  →  PrerequisiteInferenceInput
OrchestrationResult  →  PrerequisiteInferenceOutput
OrchestrationRequest  →  CurriculumPlannerInput
OrchestrationResult  →  CurriculumPlannerOutput
OrchestrationRequest  →  LessonSequencePlannerInput
OrchestrationResult  →  LessonSequencePlannerOutput
OrchestrationRequest  →  LearningPathGeneratorInput
OrchestrationResult  →  LearningPathGeneratorOutput
OrchestrationRequest  →  PersonalizedCurriculumInput
OrchestrationResult  →  PersonalizedCurriculumOutput
OrchestrationRequest  →  SkillGapCurriculumAdapterInput
OrchestrationResult  →  SkillGapCurriculumAdapterOutput
OrchestrationRequest  →  DifficultyBalancerInput
OrchestrationResult  →  DifficultyBalancerOutput
OrchestrationRequest  →  StudyStrategyPlannerInput
OrchestrationResult  →  StudyStrategyPlannerOutput
OrchestrationRequest  →  ReviewSchedulerInput
OrchestrationResult  →  ReviewSchedulerOutput
OrchestrationRequest  →  RemediationPlannerInput
OrchestrationResult  →  RemediationPlannerOutput
OrchestrationRequest  →  EnrichmentPlannerInput
OrchestrationResult  →  EnrichmentPlannerOutput
OrchestrationRequest  →  ConceptReinforcementInput
OrchestrationResult  →  ConceptReinforcementOutput
OrchestrationRequest  →  LongTermLearningPlannerInput
OrchestrationResult  →  LongTermLearningPlannerOutput
BaseModel  →  EvaluationCriterion
BaseModel  →  EvaluationScore
BaseModel  →  EvaluationIssue
BaseModel  →  AlignmentResult
BaseModel  →  ConsistencyError
BaseModel  →  CoverageGap
OrchestrationRequest  →  QuestionQualityEvaluationInput
OrchestrationResult  →  QuestionQualityEvaluationOutput
OrchestrationRequest  →  ExplanationQualityEvaluationInput
OrchestrationResult  →  ExplanationQualityEvaluationOutput
OrchestrationRequest  →  PedagogicalAlignmentInput
OrchestrationResult  →  PedagogicalAlignmentOutput
OrchestrationRequest  →  ConsistencyEvaluationInput
OrchestrationResult  →  ConsistencyEvaluationOutput
OrchestrationRequest  →  CurriculumCoverageInput
OrchestrationResult  →  CurriculumCoverageOutput
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
OrchestrationRequest  →  KnowledgeIngestionInput
OrchestrationResult  →  KnowledgeIngestionOutput
OrchestrationRequest  →  DocumentChunkingInput
OrchestrationResult  →  DocumentChunkingOutput
OrchestrationRequest  →  EmbeddingGeneratorInput
OrchestrationResult  →  EmbeddingGeneratorOutput
OrchestrationRequest  →  SemanticIndexerInput
OrchestrationResult  →  SemanticIndexerOutput
OrchestrationRequest  →  VectorSearchInput
OrchestrationResult  →  VectorSearchOutput
OrchestrationRequest  →  HybridRetrievalInput
OrchestrationResult  →  HybridRetrievalOutput
OrchestrationRequest  →  ContextBuilderInput
OrchestrationResult  →  ContextBuilderOutput
OrchestrationRequest  →  MemoryConsolidationInput
OrchestrationResult  →  MemoryConsolidationOutput
OrchestrationRequest  →  EpisodicMemoryInput
OrchestrationResult  →  EpisodicMemoryOutput
OrchestrationRequest  →  StudentKnowledgeMemoryInput
OrchestrationResult  →  StudentKnowledgeMemoryOutput
OrchestrationRequest  →  KnowledgeUpdaterInput
OrchestrationResult  →  KnowledgeUpdaterOutput
OrchestrationRequest  →  KnowledgeConflictResolverInput
OrchestrationResult  →  KnowledgeConflictResolverOutput
OrchestrationRequest  →  RetrievalRankerInput
OrchestrationResult  →  RetrievalRankerOutput
OrchestrationRequest  →  ContextRelevanceEvaluatorInput
OrchestrationResult  →  ContextRelevanceEvaluatorOutput
OrchestrationRequest  →  KnowledgeSummarizerInput
OrchestrationResult  →  KnowledgeSummarizerOutput
OrchestrationRequest  →  TextToSpeechInput
OrchestrationResult  →  TextToSpeechOutput
OrchestrationRequest  →  SpeechToTextInput
OrchestrationResult  →  SpeechToTextOutput
OrchestrationRequest  →  VisualIllustrationInput
OrchestrationResult  →  VisualIllustrationOutput
OrchestrationRequest  →  BoardDrawingInput
OrchestrationResult  →  BoardDrawingOutput
OrchestrationRequest  →  EmotionAnalysisInput
OrchestrationResult  →  EmotionAnalysisOutput
OrchestrationRequest  →  EngagementDetectorInput
OrchestrationResult  →  EngagementDetectorOutput
OrchestrationRequest  →  VisualFeedbackInput
OrchestrationResult  →  VisualFeedbackOutput
OrchestrationRequest  →  GestureRecognitionInput
OrchestrationResult  →  GestureRecognitionOutput
OrchestrationRequest  →  AudioFeedbackInput
OrchestrationResult  →  AudioFeedbackOutput
OrchestrationRequest  →  InteractiveLessonOrchestratorInput
OrchestrationResult  →  InteractiveLessonOrchestratorOutput
OrchestrationRequest  →  LearningSessionPlannerInput
OrchestrationResult  →  LearningSessionPlannerOutput
OrchestrationRequest  →  AgentWorkflowPlannerInput
OrchestrationResult  →  AgentWorkflowPlannerOutput
OrchestrationRequest  →  TaskDecomposerInput
OrchestrationResult  →  TaskDecomposerOutput
OrchestrationRequest  →  AgentSelectorInput
OrchestrationResult  →  AgentSelectorOutput
OrchestrationRequest  →  ContextManagerInput
OrchestrationResult  →  ContextManagerOutput
OrchestrationRequest  →  WorkflowStateTrackerInput
OrchestrationResult  →  WorkflowStateTrackerOutput
OrchestrationRequest  →  FailureRecoveryInput
OrchestrationResult  →  FailureRecoveryOutput
OrchestrationRequest  →  RetryStrategyInput
OrchestrationResult  →  RetryStrategyOutput
OrchestrationRequest  →  ShortTermMemoryInput
OrchestrationResult  →  ShortTermMemoryOutput
OrchestrationRequest  →  LongTermMemoryInput
OrchestrationResult  →  LongTermMemoryOutput
OrchestrationRequest  →  WorkflowOptimizerInput
OrchestrationResult  →  WorkflowOptimizerOutput
OrchestrationRequest  →  CostEfficiencyAnalyzerInput
OrchestrationResult  →  CostEfficiencyAnalyzerOutput
OrchestrationRequest  →  AgentPerformanceMonitorInput
OrchestrationResult  →  AgentPerformanceMonitorOutput
OrchestrationRequest  →  SystemHealthEvaluatorInput
OrchestrationResult  →  SystemHealthEvaluatorOutput
OrchestrationRequest  →  DialogueTutorInput
BaseModel  →  TutorResponse
OrchestrationResult  →  DialogueTutorOutput
OrchestrationRequest  →  StyleAdaptationInput
BaseModel  →  AdaptedContent
OrchestrationResult  →  StyleAdaptationOutput
OrchestrationRequest  →  ProgressAnalysisInput
OrchestrationResult  →  ProgressAnalysisOutput
OrchestrationRequest  →  LearningPathCreationInput
BaseModel  →  LearningStep
OrchestrationResult  →  LearningPathCreationOutput
OrchestrationRequest  →  ResourceRecommendationInput
BaseModel  →  RecommendedResource
OrchestrationResult  →  ResourceRecommendationOutput
OrchestrationRequest  →  InteractionStyleAnalysisInput
BaseModel  →  InteractionPattern
OrchestrationResult  →  InteractionStyleAnalysisOutput
OrchestrationRequest  →  QuestionRefineInput
OrchestrationResult  →  QuestionRefineOutput
OrchestrationRequest  →  QuestionGenerationInput
OrchestrationResult  →  QuestionGenerationOutput
OrchestrationRequest  →  HintGenerationInput
OrchestrationResult  →  HintGenerationOutput
OrchestrationRequest  →  ExplanationGenerationInput
OrchestrationResult  →  ExplanationGenerationOutput
OrchestrationRequest  →  DifficultyAdaptationInput
OrchestrationResult  →  DifficultyAdaptationOutput
OrchestrationRequest  →  MisconceptionDetectionInput
OrchestrationResult  →  Misconception
OrchestrationResult  →  MisconceptionDetectionOutput
BaseModel  →  Document
BaseModel  →  DocumentChunk
BaseModel  →  RetrievedDocument
BaseModel  →  PipelineEvent
BaseModel  →  StudentStateEvent
BaseModel  →  RuntimeErrorLog
BaseModel  →  MemorySnapshot
BaseModel  →  SystemEvent
BaseModel  →  AgentExecutionRecord
BaseModel  →  TaskExecutionRecord
BaseModel  →  WorkflowExecutionRecord
BaseModel  →  ContentVersion
BaseCompressor  →  EmbeddingCompressor
BaseCompressor  →  LLMCompressor
BaseModel  →  GraphNode
BaseModel  →  GraphEdge
ABC  →  BaseLLM
Protocol  →  AsyncLLM
BaseLLM  →  OllamaLLM
BaseLLM  →  OpenAILLM
BaseModel  →  RetrievalPlan
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
OrchestrationRequest  →  SimpleInput
OrchestrationResult  →  SimpleOutput
BaseAgent  →  SimpleAgent
OrchestrationRequest  →  InputModel
OrchestrationResult  →  OutputModel
BaseAgent[InputModel, OutputModel]  →  EchoAgent
EchoAgent  →  FailingAgent
MessageBus  →  DummyMessageBus
BaseOrchestrationBackend  →  DummyBackend
OrchestrationResult  →  Result
MessageBus  →  DummyMessageBus
MessageBus  →  DummyMessageBus
BaseOrchestrationBackend  →  DummyBackend
OrchestrationResult  →  Result
```

---

### کلاس‌های Abstract / Interface

- **`MessageBus`** (`agents/buses/base.py`)
  - متدها: `publish`, `subscribe`, `unsubscribe`, `start`, `stop`
- **`BaseOrchestrationBackend`** (`agents/orchestration/backends/base_backend.py`)
  - متدها: `execute`
- **`InteractionStrategy`** (`agents/orchestration/interaction/base_strategy.py`)
  - متدها: `__init__`, `execute`, `_emit`
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
- `VectorService` در `rag/vector_service.py`

---

## 📝 یادداشت

این گزارش به صورت **استاتیک** (تحلیل AST) تولید شده است.  
برای تحلیل runtime و dependency injection، ابزار تکمیلی لازم است.
