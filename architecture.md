# 📐 Architecture Report

> تولید شده توسط `tools/analyze_architecture.py`  
> تاریخ: 2026-04-21 22:04:53  
---

## 📊 آمار کلی

| معیار | مقدار |
|-------|-------|
| فایل‌های Python | 526 |
| کلاس‌ها | 2002 |
| توابع سطح بالا | 257 |
| فایل‌های با خطا | 3 |
| مجموع خطوط کد | 159494 |

---

## 📂 ساختار فولدرها

```
📦 project/
  ├── 📁 config/
  ├── 📁 engines/
  │   ├── 📁 agents/
  │   │   ├── 📁 base_agents/
  │   │   │   └── 📁 base_research_agent/
  │   │   └── 📁 content/
  │   │       └── 📁 models/
  │   ├── 📁 buses/
  │   ├── 📁 document/
  │   │   ├── 📁 chunking/
  │   │   ├── 📁 embedding/
  │   │   ├── 📁 ingestion/
  │   │   │   ├── 📁 services/
  │   │   │   ├── 📁 steps/
  │   │   │   └── 📁 utils/
  │   │   ├── 📁 models/
  │   │   ├── 📁 parsers/
  │   │   │   ├── 📁 cad_parser/
  │   │   │   ├── 📁 docx_parser/
  │   │   │   └── 📁 pdf_parser/
  │   │   ├── 📁 storage/
  │   │   ├── 📁 utils/
  │   │   └── 📁 writers/
  │   │       ├── 📁 cad_writer/
  │   │       ├── 📁 docx_writer/
  │   │       └── 📁 pdf_writer/
  │   ├── 📁 interaction/
  │   │   └── 📁 backends/
  │   ├── 📁 orchestration/
  │   ├── 📁 rag/
  │   │   ├── 📁 agentic/
  │   │   ├── 📁 compression/
  │   │   ├── 📁 evidence/
  │   │   ├── 📁 explain/
  │   │   ├── 📁 graph/
  │   │   ├── 📁 learning/
  │   │   ├── 📁 llm/
  │   │   ├── 📁 planner/
  │   │   ├── 📁 reflection/
  │   │   ├── 📁 reranking/
  │   │   ├── 📁 research/
  │   │   │   ├── 📁 autonomous/
  │   │   │   ├── 📁 dashboard/
  │   │   │   ├── 📁 evaluation/
  │   │   │   ├── 📁 graph/
  │   │   │   ├── 📁 guardrails/
  │   │   │   ├── 📁 improvement/
  │   │   │   ├── 📁 memory/
  │   │   │   │   └── 📁 reasoning/
  │   │   │   ├── 📁 observability/
  │   │   │   └── 📁 summarization/
  │   │   ├── 📁 retrieval/
  │   │   ├── 📁 services/
  │   │   └── 📁 trainer/
  │   └── 📁 storage/
  │       ├── 📁 cache/
  │       │   └── 📁 backends/
  │       ├── 📁 event_log/
  │       │   └── 📁 backends/
  │       ├── 📁 graph/
  │       │   └── 📁 backends/
  │       ├── 📁 key_value/
  │       │   └── 📁 backends/
  │       ├── 📁 object/
  │       │   └── 📁 backends/
  │       ├── 📁 relational/
  │       │   └── 📁 backends/
  │       ├── 📁 stream/
  │       │   └── 📁 backends/
  │       ├── 📁 timeseries/
  │       │   └── 📁 backends/
  │       └── 📁 vector/
  │           └── 📁 backends/
  ├── 📁 migrations/
  ├── 📁 tests/
  │   └── 📁 agents/
  │       ├── 📁 agents_unit/
  │       └── 📁 interaction/
  │           ├── 📁 interaction_performance/
  │           └── 📁 interaction_unit/
  └── 📁 tools/
      └── 📁 ai/
          ├── 📁 analysis/
          │   ├── 📁 chunkers/
          │   ├── 📁 encoders/
          │   ├── 📁 indexers/
          │   └── 📁 scanners/
          ├── 📁 entry_points/
          ├── 📁 generation/
          │   ├── 📁 generators/
          │   ├── 📁 planners/
          │   └── 📁 refiners/
          ├── 📁 orchestration/
          │   ├── 📁 analytics/
          │   ├── 📁 co_evolution/
          │   ├── 📁 human_task/
          │   └── 📁 session/
          ├── 📁 planning/
          ├── 📁 quality/
          │   ├── 📁 debuggers/
          │   ├── 📁 documenters/
          │   ├── 📁 testers/
          │   └── 📁 validators/
          └── 📁 shared/
```

---

## 🗂️ ساختار کامل (فولدرها + فایل‌ها + تعداد خطوط)

```
📦 project/
  ├── 📁 config/
  │   └── 📄 settings.py [22 lines]
  ├── 📁 engines/
  │   ├── 📁 agents/
  │   │   ├── 📁 base_agents/
  │   │   │   ├── 📁 base_research_agent/
  │   │   │   │   ├── 📄 metadata.py [0 lines]
  │   │   │   │   ├── 📄 prompts.py [0 lines]
  │   │   │   │   └── 📄 rag_config.py [0 lines]
  │   │   │   ├── 📄 __init__.py [2 lines]
  │   │   │   ├── 📄 base_agent.py [117 lines]
  │   │   │   └── 📄 interaction_agent.py [30 lines]
  │   │   ├── 📁 content/
  │   │   │   ├── 📁 models/
  │   │   │   │   ├── 📄 __init__.py [13 lines]
  │   │   │   │   ├── 📄 analytics_agents_31_40.py [284 lines]
  │   │   │   │   ├── 📄 assessment_agents_21_30.py [327 lines]
  │   │   │   │   ├── 📄 common.py [159 lines]
  │   │   │   │   ├── 📄 content_agents_1_8.py [236 lines]
  │   │   │   │   ├── 📄 content_generation_agents_91_100.py [139 lines]
  │   │   │   │   ├── 📄 curriculum_agents_46_60.py [270 lines]
  │   │   │   │   ├── 📄 evaluation_agents_41_45.py [186 lines]
  │   │   │   │   ├── 📄 learning_objects.py [244 lines]
  │   │   │   │   ├── 📄 memory_agents_76_90.py [252 lines]
  │   │   │   │   ├── 📄 multimodal_agents_101_110.py [132 lines]
  │   │   │   │   ├── 📄 orchestration_agents_61_75.py [270 lines]
  │   │   │   │   ├── 📄 personalization_agents_15_20.py [97 lines]
  │   │   │   │   └── 📄 teaching_agents_9_14.py [82 lines]
  │   │   │   ├── 📄 __init__.py [1 lines]
  │   │   │   └── 📄 text_rewriter.py [76 lines]
  │   │   ├── 📄 __init__.py [2 lines]
  │   │   ├── 📄 agent_registry.py [35 lines]
  │   │   └── 📄 models.py [62 lines]
  │   ├── 📁 buses/
  │   │   ├── 📄 __init__.py [9 lines]
  │   │   ├── 📄 base_message_bus.py [36 lines]
  │   │   ├── 📄 durable_message_bus.py [55 lines]
  │   │   ├── 📄 in_memory_message_bus.py [46 lines]
  │   │   ├── 📄 kafka_bus.py [70 lines]
  │   │   ├── 📄 priority_message_bus.py [70 lines]
  │   │   ├── 📄 rabbitmq_bus.py [65 lines]
  │   │   ├── 📄 redis_pub_sub_bus.py [67 lines]
  │   │   ├── 📄 request_reply_bus.py [40 lines]
  │   │   └── 📄 topic_message_bus.py [40 lines]
  │   ├── 📁 document/
  │   │   ├── 📁 chunking/
  │   │   │   ├── 📄 __init__.py [3 lines]
  │   │   │   ├── 📄 base.py [21 lines]
  │   │   │   ├── 📄 models.py [20 lines]
  │   │   │   └── 📄 recursive_chunker.py [106 lines]
  │   │   ├── 📁 embedding/
  │   │   │   ├── 📄 __init__.py [2 lines]
  │   │   │   ├── 📄 base.py [16 lines]
  │   │   │   └── 📄 service.py [53 lines]
  │   │   ├── 📁 ingestion/
  │   │   │   ├── 📁 services/
  │   │   │   │   ├── 📄 __init__.py [4 lines]
  │   │   │   │   ├── 📄 async_ingest_service.py [70 lines]
  │   │   │   │   ├── 📄 batch_ingest_service.py [62 lines]
  │   │   │   │   ├── 📄 ingestion_scheduler.py [70 lines]
  │   │   │   │   └── 📄 upload_service.py [49 lines]
  │   │   │   ├── 📁 steps/
  │   │   │   │   ├── 📄 __init__.py [5 lines]
  │   │   │   │   ├── 📄 step_chunk.py [30 lines]
  │   │   │   │   ├── 📄 step_embed.py [50 lines]
  │   │   │   │   ├── 📄 step_extract.py [38 lines]
  │   │   │   │   ├── 📄 step_parse.py [36 lines]
  │   │   │   │   └── 📄 step_store.py [46 lines]
  │   │   │   ├── 📁 utils/
  │   │   │   │   ├── 📄 __init__.py [4 lines]
  │   │   │   │   ├── 📄 file_signature.py [30 lines]
  │   │   │   │   ├── 📄 hashing.py [34 lines]
  │   │   │   │   ├── 📄 retry_policy.py [47 lines]
  │   │   │   │   └── 📄 timing.py [48 lines]
  │   │   │   ├── 📄 __init__.py [9 lines]
  │   │   │   ├── 📄 ingestion_context.py [175 lines]
  │   │   │   ├── 📄 ingestion_errors.py [104 lines]
  │   │   │   ├── 📄 ingestion_models.py [163 lines]
  │   │   │   ├── 📄 ingestion_pipeline.py [75 lines]
  │   │   │   ├── 📄 ingestion_runner.py [170 lines]
  │   │   │   ├── 📄 ingestion_service.py [172 lines]
  │   │   │   ├── 📄 ingestion_utils.py [28 lines]
  │   │   │   ├── 📄 ingestion_validator.py [52 lines]
  │   │   │   └── 📄 workflow_registry.py [29 lines]
  │   │   ├── 📁 models/
  │   │   │   ├── 📄 __init__.py [13 lines]
  │   │   │   ├── 📄 base.py [170 lines]
  │   │   │   ├── 📄 chunked_binary_payload.py [23 lines]
  │   │   │   ├── 📄 csdm_core.py [700 lines]
  │   │   │   ├── 📄 csdm_entities.py [654 lines]
  │   │   │   ├── 📄 csdm_tables.py [661 lines]
  │   │   │   ├── 📄 document_registry.py [267 lines]
  │   │   │   ├── 📄 dsdm_models.py [524 lines]
  │   │   │   ├── 📄 esdm_models.py [1376 lines]
  │   │   │   ├── 📄 exceptions.py [65 lines]
  │   │   │   ├── 📄 media_detection.py [176 lines]
  │   │   │   ├── 📄 media_types.py [338 lines]
  │   │   │   ├── 📄 standard.py [122 lines]
  │   │   │   └── 📄 usdm_models.py [574 lines]
  │   │   ├── 📁 parsers/
  │   │   │   ├── 📁 cad_parser/
  │   │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   │   ├── 📄 csdm_loader.py [641 lines]
  │   │   │   │   ├── 📄 csdm_parser.py [74 lines]
  │   │   │   │   ├── 📄 csdm_relationships.py [281 lines]
  │   │   │   │   └── 📄 oda_bridge.py [273 lines]
  │   │   │   ├── 📁 docx_parser/
  │   │   │   │   ├── 📄 __init__.py [7 lines]
  │   │   │   │   ├── 📄 docx_extractor.py [2154 lines]
  │   │   │   │   ├── 📄 docx_image_extractor.py [544 lines]
  │   │   │   │   ├── 📄 docx_math_parser.py [922 lines]
  │   │   │   │   ├── 📄 docx_models.py [730 lines]
  │   │   │   │   ├── ⚠️ docx_parser.py [1866 lines]
  │   │   │   │   ├── 📄 docx_style_parser.py [118 lines]
  │   │   │   │   ├── 📄 docx_table_parser.py [44 lines]
  │   │   │   │   └── 📄 docx_utils.py [3590 lines]
  │   │   │   ├── 📁 pdf_parser/
  │   │   │   │   ├── 📄 __init__.py [7 lines]
  │   │   │   │   ├── 📄 content_extractor.py [1049 lines]
  │   │   │   │   ├── 📄 font_handler.py [928 lines]
  │   │   │   │   ├── 📄 layout_analyzer.py [396 lines]
  │   │   │   │   ├── 📄 metadata_extractor.py [1523 lines]
  │   │   │   │   ├── 📄 pdf_objects.py [1145 lines]
  │   │   │   │   ├── 📄 structure_parser.py [516 lines]
  │   │   │   │   └── 📄 utils.py [1145 lines]
  │   │   │   ├── 📄 __init__.py [9 lines]
  │   │   │   ├── 📄 base.py [87 lines]
  │   │   │   ├── 📄 binary_parser.py [374 lines]
  │   │   │   ├── 📄 cad_parser.py [133 lines]
  │   │   │   ├── 📄 csv_parser.py [535 lines]
  │   │   │   ├── 📄 docx_parser.py [218 lines]
  │   │   │   ├── 📄 excel_parser.py [307 lines]
  │   │   │   ├── 📄 excel_parser0-notvalid.py [1487 lines]
  │   │   │   ├── 📄 html_parser.py [816 lines]
  │   │   │   ├── 📄 json_parser.py [155 lines]
  │   │   │   ├── 📄 latex_parser.py [841 lines]
  │   │   │   ├── 📄 markdown_parser.py [439 lines]
  │   │   │   ├── 📄 pdf_parser.py [513 lines]
  │   │   │   ├── 📄 xml_parser.py [439 lines]
  │   │   │   └── 📄 yaml_parser.py [190 lines]
  │   │   ├── 📁 storage/
  │   │   │   ├── 📄 __init__.py [3 lines]
  │   │   │   ├── 📄 chunk_store.py [123 lines]
  │   │   │   ├── 📄 document_store.py [140 lines]
  │   │   │   └── 📄 metadata_store.py [38 lines]
  │   │   ├── 📁 utils/
  │   │   │   ├── 📄 __init__.py [2 lines]
  │   │   │   ├── 📄 binary_codec.py [100 lines]
  │   │   │   ├── 📄 docx_utils.py [0 lines]
  │   │   │   ├── 📄 ooxml_constants.py [0 lines]
  │   │   │   ├── 📄 streaming_binary_codec.py [46 lines]
  │   │   │   ├── 📄 xml_parser.py [0 lines]
  │   │   │   └── 📄 zip_handler.py [0 lines]
  │   │   ├── 📁 writers/
  │   │   │   ├── 📁 cad_writer/
  │   │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   │   ├── 📄 acis_writer.py [91 lines]
  │   │   │   │   ├── 📄 base_context.py [77 lines]
  │   │   │   │   ├── 📄 block_writer.py [124 lines]
  │   │   │   │   ├── 📄 cad_writer.py [129 lines]
  │   │   │   │   ├── 📄 dwg_builder.py [177 lines]
  │   │   │   │   ├── 📄 entity_writer.py [360 lines]
  │   │   │   │   ├── 📄 finalizer.py [138 lines]
  │   │   │   │   ├── 📄 non_graphical_writer.py [259 lines]
  │   │   │   │   ├── 📄 reactor_writer.py [67 lines]
  │   │   │   │   ├── 📄 table_writer.py [310 lines]
  │   │   │   │   └── 📄 xdata_writer.py [81 lines]
  │   │   │   ├── 📁 docx_writer/
  │   │   │   │   ├── 📄 docx_builder.py [0 lines]
  │   │   │   │   ├── 📄 docx_image_handler.py [0 lines]
  │   │   │   │   ├── 📄 docx_math_writer.py [0 lines]
  │   │   │   │   ├── 📄 docx_style_builder.py [0 lines]
  │   │   │   │   ├── 📄 docx_table_builder.py [0 lines]
  │   │   │   │   └── 📄 docx_writer.py [0 lines]
  │   │   │   ├── 📁 pdf_writer/
  │   │   │   │   ├── 📄 __init__.py [10 lines]
  │   │   │   │   ├── 📄 annotation_writer.py [580 lines]
  │   │   │   │   ├── 📄 content_writer.py [302 lines]
  │   │   │   │   ├── 📄 encryption.py [941 lines]
  │   │   │   │   ├── 📄 font_manager.py [1503 lines]
  │   │   │   │   ├── 📄 init.py [24 lines]
  │   │   │   │   ├── 📄 layout_builder.py [224 lines]
  │   │   │   │   ├── 📄 metadata_writer.py [407 lines]
  │   │   │   │   ├── 📄 optimizer.py [1255 lines]
  │   │   │   │   ├── 📄 outline_builder.py [274 lines]
  │   │   │   │   ├── 📄 pdf_objects.py [500 lines]
  │   │   │   │   └── 📄 utils.py [438 lines]
  │   │   │   ├── 📄 __init__.py [7 lines]
  │   │   │   ├── 📄 base.py [60 lines]
  │   │   │   ├── 📄 binary_writer.py [281 lines]
  │   │   │   ├── 📄 cad_writer.py [269 lines]
  │   │   │   ├── 📄 csv_writer.py [298 lines]
  │   │   │   ├── 📄 docx_writer.py [306 lines]
  │   │   │   ├── 📄 excel_writer.py [1660 lines]
  │   │   │   ├── ⚠️ html_writer.py [279 lines]
  │   │   │   ├── 📄 json_writer.py [188 lines]
  │   │   │   ├── 📄 latex_writer.py [636 lines]
  │   │   │   ├── ⚠️ markdown_writer.py [289 lines]
  │   │   │   ├── 📄 pdf_writer.py [831 lines]
  │   │   │   ├── 📄 xml_writer.py [262 lines]
  │   │   │   └── 📄 yaml_writer.py [224 lines]
  │   │   └── 📄 __init__.py [0 lines]
  │   ├── 📁 interaction/
  │   │   ├── 📁 backends/
  │   │   │   ├── 📄 __init__.py [3 lines]
  │   │   │   ├── 📄 autogen_backend.py [181 lines]
  │   │   │   ├── 📄 base_backend.py [7 lines]
  │   │   │   └── 📄 native_backend.py [77 lines]
  │   │   ├── 📄 __init__.py [10 lines]
  │   │   ├── 📄 base_strategy.py [112 lines]
  │   │   ├── 📄 broadcast_strategy.py [142 lines]
  │   │   ├── 📄 coordinator_strategy.py [162 lines]
  │   │   ├── 📄 debate_strategy.py [125 lines]
  │   │   ├── 📄 ensemble_strategy.py [171 lines]
  │   │   ├── 📄 group_chat_strategy.py [268 lines]
  │   │   ├── 📄 interaction_models.py [52 lines]
  │   │   ├── 📄 round_robin_strategy.py [142 lines]
  │   │   ├── 📄 self_refine_strategy.py [148 lines]
  │   │   └── 📄 strategy_registry.py [62 lines]
  │   ├── 📁 orchestration/
  │   │   ├── 📄 __init__.py [0 lines]
  │   │   ├── 📄 base_workflow_model.py [0 lines]
  │   │   ├── 📄 bpmn2_model.py [0 lines]
  │   │   ├── 📄 dag_model.py [0 lines]
  │   │   ├── 📄 event_driven_model.py [0 lines]
  │   │   ├── 📄 petri_net_model.py [0 lines]
  │   │   └── 📄 state_machine_model.py [0 lines]
  │   ├── 📁 rag/
  │   │   ├── 📁 agentic/
  │   │   │   ├── 📄 __init__.py [6 lines]
  │   │   │   ├── 📄 agent_v2.py [64 lines]
  │   │   │   ├── 📄 evidence_tracker.py [13 lines]
  │   │   │   ├── 📄 multihop_reasoner.py [18 lines]
  │   │   │   ├── 📄 query_decomposer.py [18 lines]
  │   │   │   ├── 📄 retrieval_agent.py [49 lines]
  │   │   │   └── 📄 uncertainty.py [25 lines]
  │   │   ├── 📁 compression/
  │   │   │   ├── 📄 __init__.py [3 lines]
  │   │   │   ├── 📄 base.py [12 lines]
  │   │   │   ├── 📄 embedding_compressor.py [55 lines]
  │   │   │   └── 📄 llm_compressor.py [42 lines]
  │   │   ├── 📁 evidence/
  │   │   │   ├── 📄 __init__.py [1 lines]
  │   │   │   └── 📄 evidence_clusterer.py [40 lines]
  │   │   ├── 📁 explain/
  │   │   │   ├── 📄 __init__.py [1 lines]
  │   │   │   └── 📄 retrieval_explainer.py [35 lines]
  │   │   ├── 📁 graph/
  │   │   │   ├── 📄 __init__.py [4 lines]
  │   │   │   ├── 📄 graph_builder.py [37 lines]
  │   │   │   ├── 📄 graph_models.py [17 lines]
  │   │   │   ├── 📄 graph_retriever.py [44 lines]
  │   │   │   └── 📄 graph_store.py [28 lines]
  │   │   ├── 📁 learning/
  │   │   │   ├── 📄 __init__.py [1 lines]
  │   │   │   └── 📄 retrieval_policy.py [39 lines]
  │   │   ├── 📁 llm/
  │   │   │   ├── 📄 __init__.py [5 lines]
  │   │   │   ├── 📄 base_llm.py [13 lines]
  │   │   │   ├── 📄 llm_factory.py [13 lines]
  │   │   │   ├── 📄 llm_protocols.py [9 lines]
  │   │   │   ├── 📄 ollama_llm.py [47 lines]
  │   │   │   └── 📄 openai_llm.py [36 lines]
  │   │   ├── 📁 planner/
  │   │   │   ├── 📄 __init__.py [2 lines]
  │   │   │   ├── 📄 adaptive_planner.py [52 lines]
  │   │   │   └── 📄 retrieval_plan.py [12 lines]
  │   │   ├── 📁 reflection/
  │   │   │   ├── 📄 __init__.py [2 lines]
  │   │   │   ├── 📄 reflection_critic.py [26 lines]
  │   │   │   └── 📄 reflection_loop.py [73 lines]
  │   │   ├── 📁 reranking/
  │   │   │   ├── 📄 __init__.py [2 lines]
  │   │   │   ├── 📄 base_reranker.py [11 lines]
  │   │   │   └── 📄 reranker.py [34 lines]
  │   │   ├── 📁 research/
  │   │   │   ├── 📁 autonomous/
  │   │   │   │   ├── 📄 __init__.py [4 lines]
  │   │   │   │   ├── 📄 coverage_scorer.py [45 lines]
  │   │   │   │   ├── 📄 gap_detector.py [48 lines]
  │   │   │   │   ├── 📄 query_generator.py [37 lines]
  │   │   │   │   └── 📄 research_loop.py [54 lines]
  │   │   │   ├── 📁 dashboard/
  │   │   │   │   ├── 📄 __init__.py [3 lines]
  │   │   │   │   ├── 📄 api_server.py [58 lines]
  │   │   │   │   ├── 📄 schema.py [51 lines]
  │   │   │   │   └── 📄 websocket_stream.py [38 lines]
  │   │   │   ├── 📁 evaluation/
  │   │   │   │   ├── 📄 __init__.py [9 lines]
  │   │   │   │   ├── 📄 citation_evaluator.py [17 lines]
  │   │   │   │   ├── 📄 completeness_evaluator.py [14 lines]
  │   │   │   │   ├── 📄 coverage_scorer.py [13 lines]
  │   │   │   │   ├── 📄 evaluation_controller.py [58 lines]
  │   │   │   │   ├── 📄 hallucination_detector.py [16 lines]
  │   │   │   │   ├── 📄 improvement_engine.py [31 lines]
  │   │   │   │   ├── 📄 reasoning_evaluator.py [13 lines]
  │   │   │   │   ├── 📄 retrieval_evaluator.py [27 lines]
  │   │   │   │   └── 📄 schema.py [28 lines]
  │   │   │   ├── 📁 graph/
  │   │   │   │   ├── 📄 __init__.py [8 lines]
  │   │   │   │   ├── 📄 entity_extractor.py [81 lines]
  │   │   │   │   ├── 📄 graph_aware_planner.py [33 lines]
  │   │   │   │   ├── 📄 graph_canonicalizer.py [21 lines]
  │   │   │   │   ├── 📄 graph_index.py [79 lines]
  │   │   │   │   ├── 📄 graph_persistence.py [64 lines]
  │   │   │   │   ├── 📄 graph_traverser.py [8 lines]
  │   │   │   │   ├── 📄 relation_builder.py [115 lines]
  │   │   │   │   └── 📄 relation_ranker.py [31 lines]
  │   │   │   ├── 📁 guardrails/
  │   │   │   │   ├── 📄 __init__.py [1 lines]
  │   │   │   │   └── 📄 hallucination_guard.py [13 lines]
  │   │   │   ├── 📁 improvement/
  │   │   │   │   ├── 📄 __init__.py [1 lines]
  │   │   │   │   └── 📄 feedback_controller.py [32 lines]
  │   │   │   ├── 📁 memory/
  │   │   │   │   ├── 📁 reasoning/
  │   │   │   │   │   ├── 📄 __init__.py [7 lines]
  │   │   │   │   │   ├── 📄 event_types.py [29 lines]
  │   │   │   │   │   ├── 📄 reasoning_event.py [31 lines]
  │   │   │   │   │   ├── 📄 reasoning_exporter.py [38 lines]
  │   │   │   │   │   ├── 📄 reasoning_memory.py [303 lines]
  │   │   │   │   │   ├── 📄 reasoning_node.py [51 lines]
  │   │   │   │   │   ├── 📄 reasoning_recorder.py [60 lines]
  │   │   │   │   │   └── 📄 reasoning_tree.py [53 lines]
  │   │   │   │   ├── 📄 __init__.py [5 lines]
  │   │   │   │   ├── 📄 memory_controller.py [49 lines]
  │   │   │   │   ├── 📄 memory_retriever.py [38 lines]
  │   │   │   │   ├── 📄 memory_store.py [39 lines]
  │   │   │   │   ├── 📄 reasoning_memory.py [153 lines]
  │   │   │   │   └── 📄 temporal_graph.py [32 lines]
  │   │   │   ├── 📁 observability/
  │   │   │   │   ├── 📄 __init__.py [9 lines]
  │   │   │   │   ├── 📄 failure_analyzer.py [16 lines]
  │   │   │   │   ├── 📄 graph_visualizer.py [13 lines]
  │   │   │   │   ├── 📄 memory_usage_tracker.py [20 lines]
  │   │   │   │   ├── 📄 metrics_store.py [18 lines]
  │   │   │   │   ├── 📄 observability_controller.py [31 lines]
  │   │   │   │   ├── 📄 retrieval_heatmap.py [20 lines]
  │   │   │   │   ├── 📄 telemetry.py [24 lines]
  │   │   │   │   ├── 📄 token_tracker.py [20 lines]
  │   │   │   │   └── 📄 trace_collector.py [23 lines]
  │   │   │   ├── 📁 summarization/
  │   │   │   │   ├── 📄 __init__.py [3 lines]
  │   │   │   │   ├── 📄 base_summarizer.py [19 lines]
  │   │   │   │   ├── 📄 research_summarizer.py [90 lines]
  │   │   │   │   └── 📄 section_summarizer.py [67 lines]
  │   │   │   ├── 📄 __init__.py [4 lines]
  │   │   │   ├── 📄 answer_planner.py [105 lines]
  │   │   │   ├── 📄 base_research_agent.py [10 lines]
  │   │   │   ├── 📄 citation_manager.py [82 lines]
  │   │   │   └── 📄 research_agent.py [148 lines]
  │   │   ├── 📁 retrieval/
  │   │   │   ├── 📄 __init__.py [12 lines]
  │   │   │   ├── 📄 base_retriever.py [11 lines]
  │   │   │   ├── 📄 bm25_retriever.py [89 lines]
  │   │   │   ├── 📄 hybrid_retriever.py [102 lines]
  │   │   │   ├── 📄 hybrid_retriever_plus.py [156 lines]
  │   │   │   ├── 📄 hybrid_retriever_super.py [186 lines]
  │   │   │   ├── 📄 keyword_retriever.py [39 lines]
  │   │   │   ├── 📄 retrieval_feedback_buffer.py [34 lines]
  │   │   │   ├── 📄 retriever_result.py [14 lines]
  │   │   │   ├── 📄 retriever_trainer.py [48 lines]
  │   │   │   ├── 📄 topk_optimizer.py [20 lines]
  │   │   │   ├── 📄 vector_retriever.py [54 lines]
  │   │   │   └── 📄 weight_manager.py [27 lines]
  │   │   ├── 📁 services/
  │   │   │   ├── 📄 __init__.py [3 lines]
  │   │   │   ├── 📄 chunking.py [65 lines]
  │   │   │   ├── 📄 embedding.py [61 lines]
  │   │   │   └── 📄 query_rewriter.py [28 lines]
  │   │   ├── 📁 trainer/
  │   │   │   ├── 📄 __init__.py [3 lines]
  │   │   │   ├── 📄 base_trainer.py [9 lines]
  │   │   │   ├── 📄 fusion_trainer.py [37 lines]
  │   │   │   └── 📄 reranker_trainer.py [23 lines]
  │   │   ├── 📄 __init__.py [2 lines]
  │   │   ├── 📄 rag_models.py [24 lines]
  │   │   └── 📄 vector_service.py [206 lines]
  │   ├── 📁 storage/
  │   │   ├── 📁 cache/
  │   │   │   ├── 📁 backends/
  │   │   │   │   ├── 📄 __init__.py [2 lines]
  │   │   │   │   ├── 📄 memory_adapter.py [54 lines]
  │   │   │   │   └── 📄 redis_adapter.py [69 lines]
  │   │   │   ├── 📄 __init__.py [1 lines]
  │   │   │   └── 📄 base.py [37 lines]
  │   │   ├── 📁 event_log/
  │   │   │   ├── 📁 backends/
  │   │   │   │   ├── 📄 __init__.py [2 lines]
  │   │   │   │   ├── 📄 rsyslog.py [63 lines]
  │   │   │   │   └── 📄 sql_event_log.py [49 lines]
  │   │   │   ├── 📄 __init__.py [1 lines]
  │   │   │   └── 📄 base.py [35 lines]
  │   │   ├── 📁 graph/
  │   │   │   ├── 📁 backends/
  │   │   │   │   ├── 📄 __init__.py [1 lines]
  │   │   │   │   └── 📄 neo4j_adapter.py [100 lines]
  │   │   │   ├── 📄 __init__.py [1 lines]
  │   │   │   └── 📄 base.py [34 lines]
  │   │   ├── 📁 key_value/
  │   │   │   ├── 📁 backends/
  │   │   │   │   ├── 📄 __init__.py [2 lines]
  │   │   │   │   ├── 📄 memory_adapter.py [41 lines]
  │   │   │   │   └── 📄 redis_adapter.py [186 lines]
  │   │   │   ├── 📄 __init__.py [1 lines]
  │   │   │   └── 📄 base.py [38 lines]
  │   │   ├── 📁 object/
  │   │   │   ├── 📁 backends/
  │   │   │   │   ├── 📄 __init__.py [3 lines]
  │   │   │   │   ├── 📄 filesystem_adapter.py [53 lines]
  │   │   │   │   ├── 📄 minio_adapter.py [141 lines]
  │   │   │   │   └── 📄 s3_adapter.py [103 lines]
  │   │   │   ├── 📄 __init__.py [1 lines]
  │   │   │   └── 📄 base.py [46 lines]
  │   │   ├── 📁 relational/
  │   │   │   ├── 📁 backends/
  │   │   │   │   ├── 📄 __init__.py [4 lines]
  │   │   │   │   ├── 📄 mysql_adapter.py [7 lines]
  │   │   │   │   ├── 📄 postgres_adapter.py [85 lines]
  │   │   │   │   ├── 📄 sql_server_adapter.py [7 lines]
  │   │   │   │   └── 📄 sqlite_adapter.py [61 lines]
  │   │   │   ├── 📄 __init__.py [1 lines]
  │   │   │   └── 📄 base.py [102 lines]
  │   │   ├── 📁 stream/
  │   │   │   ├── 📁 backends/
  │   │   │   │   ├── 📄 __init__.py [2 lines]
  │   │   │   │   ├── 📄 kafka_adapter.py [70 lines]
  │   │   │   │   └── 📄 redis_stream_adapter.py [236 lines]
  │   │   │   ├── 📄 __init__.py [1 lines]
  │   │   │   └── 📄 base.py [35 lines]
  │   │   ├── 📁 timeseries/
  │   │   │   ├── 📁 backends/
  │   │   │   │   ├── 📄 __init__.py [1 lines]
  │   │   │   │   └── 📄 influx_adapter.py [110 lines]
  │   │   │   ├── 📄 __init__.py [1 lines]
  │   │   │   └── 📄 base.py [37 lines]
  │   │   ├── 📁 vector/
  │   │   │   ├── 📁 backends/
  │   │   │   │   ├── 📄 __init__.py [6 lines]
  │   │   │   │   ├── 📄 chroma_adapter.py [125 lines]
  │   │   │   │   ├── 📄 faiss_adapter.py [181 lines]
  │   │   │   │   ├── 📄 memory_adapter.py [110 lines]
  │   │   │   │   ├── 📄 pinecone_adapter.py [178 lines]
  │   │   │   │   ├── 📄 qdrant_adapter.py [218 lines]
  │   │   │   │   └── 📄 weaviate_adapter.py [144 lines]
  │   │   │   ├── 📄 __init__.py [3 lines]
  │   │   │   ├── 📄 base.py [109 lines]
  │   │   │   ├── 📄 embedding_utils.py [12 lines]
  │   │   │   └── 📄 index_config.py [16 lines]
  │   │   ├── 📄 __init__.py [1 lines]
  │   │   └── 📄 base_storage.py [39 lines]
  │   └── 📄 __init__.py [0 lines]
  ├── 📁 migrations/
  │   ├── 📄 __init__.py [1 lines]
  │   └── 📄 env.py [78 lines]
  ├── 📁 tests/
  │   ├── 📁 agents/
  │   │   ├── 📁 agents_unit/
  │   │   │   ├── 📄 __init__.py [3 lines]
  │   │   │   ├── 📄 test_agent_registry.py [59 lines]
  │   │   │   ├── 📄 test_base_agent.py [87 lines]
  │   │   │   └── 📄 test_message_bus.py [49 lines]
  │   │   ├── 📁 interaction/
  │   │   │   ├── 📁 interaction_performance/
  │   │   │   │   ├── 📄 __init__.py [9 lines]
  │   │   │   │   ├── 📄 conftest_performance.py [14 lines]
  │   │   │   │   ├── 📄 test_broadcast_strategy_performance.py [32 lines]
  │   │   │   │   ├── 📄 test_coordinator_strategy_performance.py [31 lines]
  │   │   │   │   ├── 📄 test_debate_strategy_performance.py [31 lines]
  │   │   │   │   ├── 📄 test_ensemble_strategy_performance.py [30 lines]
  │   │   │   │   ├── 📄 test_group_chat_strategy_performance.py [28 lines]
  │   │   │   │   ├── 📄 test_interaction_agent_performance.py [40 lines]
  │   │   │   │   ├── 📄 test_native_interaction_backend_performance.py [41 lines]
  │   │   │   │   └── 📄 test_self_refine_strategy_performance.py [36 lines]
  │   │   │   ├── 📁 interaction_unit/
  │   │   │   │   ├── 📄 __init__.py [11 lines]
  │   │   │   │   ├── 📄 conftest.py [64 lines]
  │   │   │   │   ├── 📄 test_autogen_interaction_backend.py [73 lines]
  │   │   │   │   ├── 📄 test_broadcast_strategy.py [48 lines]
  │   │   │   │   ├── 📄 test_coordinator_strategy.py [67 lines]
  │   │   │   │   ├── 📄 test_debate_strategy.py [47 lines]
  │   │   │   │   ├── 📄 test_ensemble_strategy.py [47 lines]
  │   │   │   │   ├── 📄 test_group_chat_strategy.py [35 lines]
  │   │   │   │   ├── 📄 test_interaction_agent.py [49 lines]
  │   │   │   │   ├── 📄 test_models.py [31 lines]
  │   │   │   │   ├── 📄 test_native_interaction_backend.py [141 lines]
  │   │   │   │   └── 📄 test_self_refine_strategy.py [51 lines]
  │   │   │   └── 📄 __init__.py [0 lines]
  │   │   └── 📄 __init__.py [0 lines]
  │   └── 📄 __init__.py [0 lines]
  └── 📁 tools/
      ├── 📁 ai/
      │   ├── 📁 analysis/
      │   │   ├── 📁 chunkers/
      │   │   │   ├── 📄 __init__.py [3 lines]
      │   │   │   ├── 📄 code_chunker.py [1169 lines]
      │   │   │   ├── 📄 doc_chunker.py [1345 lines]
      │   │   │   └── 📄 semantic_chunker.py [1290 lines]
      │   │   ├── 📁 encoders/
      │   │   │   ├── 📄 __init__.py [3 lines]
      │   │   │   ├── 📄 batch_encoder.py [1166 lines]
      │   │   │   ├── 📄 embedding_store.py [1261 lines]
      │   │   │   └── 📄 ollama_encoder.py [1030 lines]
      │   │   ├── 📁 indexers/
      │   │   │   ├── 📄 __init__.py [2 lines]
      │   │   │   ├── 📄 code_indexer.py [1126 lines]
      │   │   │   └── 📄 doc_indexer.py [1237 lines]
      │   │   └── 📁 scanners/
      │   │       ├── 📄 __init__.py [4 lines]
      │   │       ├── 📄 api_surface_extractor.py [1377 lines]
      │   │       ├── 📄 ast_analyzer.py [1253 lines]
      │   │       ├── 📄 import_graph.py [1230 lines]
      │   │       └── 📄 project_scanner.py [1452 lines]
      │   ├── 📁 entry_points/
      │   │   ├── 📄 __init__.py [4 lines]
      │   │   ├── 📄 api_entry.py [966 lines]
      │   │   ├── 📄 base_entry_point.py [831 lines]
      │   │   ├── 📄 cli_entry.py [1547 lines]
      │   │   └── 📄 ide_plugin_entry.py [1267 lines]
      │   ├── 📁 generation/
      │   │   ├── 📁 generators/
      │   │   │   ├── 📄 __init__.py [6 lines]
      │   │   │   ├── 📄 class_generator.py [1185 lines]
      │   │   │   ├── 📄 docstring_generator.py [1336 lines]
      │   │   │   ├── 📄 function_generator.py [1296 lines]
      │   │   │   ├── 📄 module_generator.py [1124 lines]
      │   │   │   ├── 📄 performance_test_generator.py [1208 lines]
      │   │   │   └── 📄 test_generator.py [1133 lines]
      │   │   ├── 📁 planners/
      │   │   │   ├── 📄 __init__.py [5 lines]
      │   │   │   ├── 📄 contract_designer.py [1217 lines]
      │   │   │   ├── 📄 contract_generator.py [1166 lines]
      │   │   │   ├── 📄 dependency_planner.py [1221 lines]
      │   │   │   ├── 📄 module_architect.py [1341 lines]
      │   │   │   └── 📄 skeleton_generator.py [1323 lines]
      │   │   └── 📁 refiners/
      │   │       ├── 📄 __init__.py [6 lines]
      │   │       ├── 📄 base_refiner.py [96 lines]
      │   │       ├── 📄 feedback_loop.py [1143 lines]
      │   │       ├── 📄 functionality_preserver.py [318 lines]
      │   │       ├── 📄 impact_analyzer.py [1252 lines]
      │   │       ├── 📄 iterative_refiner.py [875 lines]
      │   │       └── 📄 scope_manager.py [302 lines]
      │   ├── 📁 orchestration/
      │   │   ├── 📁 analytics/
      │   │   │   ├── 📄 __init__.py [5 lines]
      │   │   │   ├── 📄 bottleneck_detector.py [764 lines]
      │   │   │   ├── 📄 performance_tracker.py [779 lines]
      │   │   │   ├── 📄 report_generator.py [842 lines]
      │   │   │   ├── 📄 skill_gap_analyzer.py [859 lines]
      │   │   │   └── 📄 workflow_metrics_collector.py [779 lines]
      │   │   ├── 📁 co_evolution/
      │   │   │   ├── 📄 __init__.py [5 lines]
      │   │   │   ├── 📄 co_evolution_engine.py [1016 lines]
      │   │   │   ├── 📄 config_updater.py [957 lines]
      │   │   │   ├── 📄 doc_updater.py [670 lines]
      │   │   │   ├── 📄 example_updater.py [836 lines]
      │   │   │   └── 📄 test_updater.py [885 lines]
      │   │   ├── 📁 human_task/
      │   │   │   ├── 📄 __init__.py [5 lines]
      │   │   │   ├── 📄 assignment_engine.py [802 lines]
      │   │   │   ├── 📄 feedback_collector.py [871 lines]
      │   │   │   ├── 📄 skill_registry.py [899 lines]
      │   │   │   ├── 📄 work_item_types.py [230 lines]
      │   │   │   └── 📄 work_queue.py [746 lines]
      │   │   ├── 📁 session/
      │   │   │   ├── 📄 __init__.py [3 lines]
      │   │   │   ├── 📄 session_manager.py [830 lines]
      │   │   │   ├── 📄 session_persistence.py [804 lines]
      │   │   │   └── 📄 session_types.py [630 lines]
      │   │   ├── 📄 __init__.py [8 lines]
      │   │   ├── 📄 agent_registry.py [870 lines]
      │   │   ├── 📄 base_orchestrator.py [811 lines]
      │   │   ├── 📄 context_manager.py [984 lines]
      │   │   ├── 📄 event_bus.py [802 lines]
      │   │   ├── 📄 pipeline_builder.py [1200 lines]
      │   │   ├── 📄 pipeline_executer.py [1145 lines]
      │   │   ├── 📄 workflow_engine.py [1080 lines]
      │   │   └── 📄 workflow_executor.py [681 lines]
      │   ├── 📁 planning/
      │   │   ├── 📄 __init__.py [5 lines]
      │   │   ├── 📄 arch_ideator.py [307 lines]
      │   │   ├── 📄 arch_implementor.py [414 lines]
      │   │   ├── 📄 dependency_analyzer.py [1177 lines]
      │   │   ├── 📄 progress_tracker.py [977 lines]
      │   │   └── 📄 task_decomposer.py [1272 lines]
      │   ├── 📁 quality/
      │   │   ├── 📁 debuggers/
      │   │   │   ├── 📄 __init__.py [3 lines]
      │   │   │   ├── 📄 error_analyzer.py [1518 lines]
      │   │   │   ├── 📄 runtime_inspector.py [1529 lines]
      │   │   │   └── 📄 stack_trace_parser.py [1232 lines]
      │   │   ├── 📁 documenters/
      │   │   │   ├── 📄 api_doc_generator.py [1083 lines]
      │   │   │   ├── 📄 architecture_doc.py [1132 lines]
      │   │   │   └── 📄 changelog_generator.py [893 lines]
      │   │   ├── 📁 testers/
      │   │   │   ├── 📄 __init__.py [3 lines]
      │   │   │   ├── 📄 coverage_analyzer.py [1596 lines]
      │   │   │   ├── 📄 mutation_tester.py [1370 lines]
      │   │   │   └── 📄 test_runner.py [1359 lines]
      │   │   └── 📁 validators/
      │   │       ├── 📄 __init__.py [14 lines]
      │   │       ├── 📄 api_consistency.py [892 lines]
      │   │       ├── 📄 architecture_validator.py [1090 lines]
      │   │       ├── 📄 compatibility_validator.py [1209 lines]
      │   │       ├── 📄 complexity_validator.py [1250 lines]
      │   │       ├── 📄 coverage_validator.py [1047 lines]
      │   │       ├── 📄 dependency_validator.py [1305 lines]
      │   │       ├── 📄 docstring_validator.py [1193 lines]
      │   │       ├── 📄 import_validator.py [1057 lines]
      │   │       ├── 📄 mypy_validator.py [929 lines]
      │   │       ├── 📄 naming_spellcheck_validator.py [1136 lines]
      │   │       ├── 📄 performance_validator.py [1349 lines]
      │   │       ├── 📄 pytest_validator.py [1160 lines]
      │   │       ├── 📄 ruff_validator.py [1711 lines]
      │   │       └── 📄 security_validator.py [1329 lines]
      │   └── 📁 shared/
      │       ├── 📄 __init__.py [6 lines]
      │       ├── 📄 config.py [1040 lines]
      │       ├── 📄 file_utils.py [886 lines]
      │       ├── 📄 git_utils.py [1329 lines]
      │       ├── 📄 llm_client.py [1024 lines]
      │       ├── 📄 logger.py [671 lines]
      │       └── 📄 state_manager.py [1484 lines]
      ├── 📄 __init__.py [4 lines]
      ├── 📄 analyze_architecture.py [435 lines]
      ├── 📄 clean_pycache.py [21 lines]
      ├── 📄 code_auditor.py [533 lines]
      └── 📄 generate_inits.py [113 lines]
```

---

## 🏛️ کلاس‌ها و وراثت

### جدول کامل کلاس‌ها

| فایل | کلاس | والدین | متدها |
|------|------|--------|-------|
| `engines/agents/agent_registry.py` | `AgentRegistry` | `—` | `__init__, register, get, run` |
| `engines/agents/base_agents/base_agent.py` | `BaseAgent` | `Generic[TInput, TOutput]` | `__init__, run, run_sync, execute, _validate_input, _validate_output ...` |
| `engines/agents/base_agents/interaction_agent.py` | `InteractionAgent` | `BaseAgent` | `__init__, run` |
| `engines/agents/content/models/analytics_agents_31_40.py` | `StudentBehaviorAnalysisInput` | `AgentInput` | `` |
| `engines/agents/content/models/analytics_agents_31_40.py` | `BehaviorPattern` | `BaseModel` | `` |
| `engines/agents/content/models/analytics_agents_31_40.py` | `StudentBehaviorAnalysisOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/analytics_agents_31_40.py` | `EngagementDetectionInput` | `AgentInput` | `` |
| `engines/agents/content/models/analytics_agents_31_40.py` | `EngagementDetectionOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/analytics_agents_31_40.py` | `MotivationAnalysisInput` | `AgentInput` | `` |
| `engines/agents/content/models/analytics_agents_31_40.py` | `MotivationAnalysisOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/analytics_agents_31_40.py` | `DropoutRiskPredictionInput` | `AgentInput` | `` |
| `engines/agents/content/models/analytics_agents_31_40.py` | `DropoutRiskPredictionOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/analytics_agents_31_40.py` | `StudyPatternMiningInput` | `AgentInput` | `` |
| `engines/agents/content/models/analytics_agents_31_40.py` | `StudyPattern` | `BaseModel` | `` |
| `engines/agents/content/models/analytics_agents_31_40.py` | `StudyPatternMiningOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/analytics_agents_31_40.py` | `PerformanceTrendAnalysisInput` | `AgentInput` | `` |
| `engines/agents/content/models/analytics_agents_31_40.py` | `PerformanceTrend` | `BaseModel` | `` |
| `engines/agents/content/models/analytics_agents_31_40.py` | `PerformanceTrendAnalysisOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/analytics_agents_31_40.py` | `LearningOutcomePredictionInput` | `AgentInput` | `` |
| `engines/agents/content/models/analytics_agents_31_40.py` | `LearningOutcomePredictionOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/analytics_agents_31_40.py` | `ClassroomAnalyticsInput` | `AgentInput` | `` |
| `engines/agents/content/models/analytics_agents_31_40.py` | `ClassroomAnalyticsOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/analytics_agents_31_40.py` | `CohortComparisonInput` | `AgentInput` | `` |
| `engines/agents/content/models/analytics_agents_31_40.py` | `CohortComparisonOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/analytics_agents_31_40.py` | `TeacherDashboardAggregationInput` | `AgentInput` | `` |
| `engines/agents/content/models/analytics_agents_31_40.py` | `TeacherDashboardAggregationOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/assessment_agents_21_30.py` | `QuizBuilderInput` | `AgentInput` | `` |
| `engines/agents/content/models/assessment_agents_21_30.py` | `QuizQuestion` | `BaseModel` | `` |
| `engines/agents/content/models/assessment_agents_21_30.py` | `QuizBuilderOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/assessment_agents_21_30.py` | `AnswerEvaluationInput` | `AgentInput` | `` |
| `engines/agents/content/models/assessment_agents_21_30.py` | `AnswerEvaluationOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/assessment_agents_21_30.py` | `FeedbackGenerationInput` | `AgentInput` | `` |
| `engines/agents/content/models/assessment_agents_21_30.py` | `FeedbackGenerationOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/assessment_agents_21_30.py` | `RubricGenerationInput` | `AgentInput` | `` |
| `engines/agents/content/models/assessment_agents_21_30.py` | `RubricCriterion` | `BaseModel` | `` |
| `engines/agents/content/models/assessment_agents_21_30.py` | `RubricGenerationOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/assessment_agents_21_30.py` | `MisconceptionAnalysisInput` | `AgentInput` | `` |
| `engines/agents/content/models/assessment_agents_21_30.py` | `MisconceptionPattern` | `BaseModel` | `` |
| `engines/agents/content/models/assessment_agents_21_30.py` | `MisconceptionAnalysisOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/assessment_agents_21_30.py` | `SkillMasteryInput` | `AgentInput` | `` |
| `engines/agents/content/models/assessment_agents_21_30.py` | `SkillMasteryOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/assessment_agents_21_30.py` | `LearningGapInput` | `AgentInput` | `` |
| `engines/agents/content/models/assessment_agents_21_30.py` | `LearningGap` | `BaseModel` | `` |
| `engines/agents/content/models/assessment_agents_21_30.py` | `LearningGapOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/assessment_agents_21_30.py` | `KnowledgeGraphUpdateInput` | `AgentInput` | `` |
| `engines/agents/content/models/assessment_agents_21_30.py` | `KnowledgeGraphUpdateOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/assessment_agents_21_30.py` | `ConceptDifficultyInput` | `AgentInput` | `` |
| `engines/agents/content/models/assessment_agents_21_30.py` | `ConceptDifficultyOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/assessment_agents_21_30.py` | `CurriculumMappingInput` | `AgentInput` | `` |
| `engines/agents/content/models/assessment_agents_21_30.py` | `CurriculumMapping` | `BaseModel` | `` |
| `engines/agents/content/models/assessment_agents_21_30.py` | `CurriculumMappingOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/common.py` | `ContentVersion` | `BaseModel` | `` |
| `engines/agents/content/models/common.py` | `ConfidenceScore` | `BaseModel` | `` |
| `engines/agents/content/models/common.py` | `ScoreRange` | `BaseModel` | `` |
| `engines/agents/content/models/common.py` | `Evidence` | `BaseModel` | `` |
| `engines/agents/content/models/common.py` | `ReasoningTrace` | `BaseModel` | `` |
| `engines/agents/content/models/common.py` | `Recommendation` | `BaseModel` | `` |
| `engines/agents/content/models/common.py` | `ActionSuggestion` | `BaseModel` | `` |
| `engines/agents/content/models/common.py` | `ConceptReference` | `BaseModel` | `` |
| `engines/agents/content/models/common.py` | `ResourceReference` | `BaseModel` | `` |
| `engines/agents/content/models/common.py` | `DetectedIssue` | `BaseModel` | `` |
| `engines/agents/content/models/common.py` | `Pattern` | `BaseModel` | `` |
| `engines/agents/content/models/common.py` | `Prediction` | `BaseModel` | `` |
| `engines/agents/content/models/common.py` | `TimeWindow` | `BaseModel` | `` |
| `engines/agents/content/models/content_agents_1_8.py` | `TextRewriteInput` | `AgentInput` | `` |
| `engines/agents/content/models/content_agents_1_8.py` | `RewriteChange` | `BaseModel` | `` |
| `engines/agents/content/models/content_agents_1_8.py` | `TextRewriteOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/content_agents_1_8.py` | `ContentValidationInput` | `AgentInput` | `` |
| `engines/agents/content/models/content_agents_1_8.py` | `ValidationIssue` | `BaseModel` | `` |
| `engines/agents/content/models/content_agents_1_8.py` | `ContentValidationOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/content_agents_1_8.py` | `CitationGenerationInput` | `AgentInput` | `` |
| `engines/agents/content/models/content_agents_1_8.py` | `CitationEntry` | `BaseModel` | `` |
| `engines/agents/content/models/content_agents_1_8.py` | `CitationGenerationOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/content_agents_1_8.py` | `GlossaryBuilderInput` | `AgentInput` | `` |
| `engines/agents/content/models/content_agents_1_8.py` | `GlossaryTerm` | `BaseModel` | `` |
| `engines/agents/content/models/content_agents_1_8.py` | `GlossaryBuilderOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/content_agents_1_8.py` | `DynamicUpdateInput` | `AgentInput` | `` |
| `engines/agents/content/models/content_agents_1_8.py` | `ContentUpdateSuggestion` | `BaseModel` | `` |
| `engines/agents/content/models/content_agents_1_8.py` | `DynamicUpdateOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/content_agents_1_8.py` | `NarrativeBuilderInput` | `AgentInput` | `` |
| `engines/agents/content/models/content_agents_1_8.py` | `NarrativeElement` | `BaseModel` | `` |
| `engines/agents/content/models/content_agents_1_8.py` | `NarrativeBuilderOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/content_agents_1_8.py` | `StructuringInput` | `AgentInput` | `` |
| `engines/agents/content/models/content_agents_1_8.py` | `LessonSection` | `BaseModel` | `` |
| `engines/agents/content/models/content_agents_1_8.py` | `StructuringOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/content_agents_1_8.py` | `PrerequisiteInput` | `AgentInput` | `` |
| `engines/agents/content/models/content_agents_1_8.py` | `PrerequisiteItem` | `BaseModel` | `` |
| `engines/agents/content/models/content_agents_1_8.py` | `PrerequisiteOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/content_generation_agents_91_100.py` | `ExampleGeneratorInput` | `AgentInput` | `` |
| `engines/agents/content/models/content_generation_agents_91_100.py` | `ExampleGeneratorOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/content_generation_agents_91_100.py` | `ExerciseCreatorInput` | `AgentInput` | `` |
| `engines/agents/content/models/content_generation_agents_91_100.py` | `ExerciseCreatorOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/content_generation_agents_91_100.py` | `StoryLessonCreatorInput` | `AgentInput` | `` |
| `engines/agents/content/models/content_generation_agents_91_100.py` | `StoryLessonCreatorOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/content_generation_agents_91_100.py` | `ConceptExplanationInput` | `AgentInput` | `` |
| `engines/agents/content/models/content_generation_agents_91_100.py` | `ConceptExplanationOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/content_generation_agents_91_100.py` | `PracticeQuestionGeneratorInput` | `AgentInput` | `` |
| `engines/agents/content/models/content_generation_agents_91_100.py` | `PracticeQuestionGeneratorOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/content_generation_agents_91_100.py` | `AdaptiveQuestionGeneratorInput` | `AgentInput` | `` |
| `engines/agents/content/models/content_generation_agents_91_100.py` | `AdaptiveQuestionGeneratorOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/content_generation_agents_91_100.py` | `ExplanationRewriterInput` | `AgentInput` | `` |
| `engines/agents/content/models/content_generation_agents_91_100.py` | `ExplanationRewriterOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/content_generation_agents_91_100.py` | `SummaryGeneratorInput` | `AgentInput` | `` |
| `engines/agents/content/models/content_generation_agents_91_100.py` | `SummaryGeneratorOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/content_generation_agents_91_100.py` | `ContentSimplifierInput` | `AgentInput` | `` |
| `engines/agents/content/models/content_generation_agents_91_100.py` | `ContentSimplifierOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/content_generation_agents_91_100.py` | `AssessmentQuestionGeneratorInput` | `AgentInput` | `` |
| `engines/agents/content/models/content_generation_agents_91_100.py` | `AssessmentQuestionGeneratorOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `ConceptGraphBuilderInput` | `AgentInput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `ConceptGraphBuilderOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `ConceptRelationExtractorInput` | `AgentInput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `ConceptRelationExtractorOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `PrerequisiteInferenceInput` | `AgentInput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `PrerequisiteInferenceOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `CurriculumPlannerInput` | `AgentInput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `CurriculumPlannerOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `LessonSequencePlannerInput` | `AgentInput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `LessonSequencePlannerOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `LearningPathGeneratorInput` | `AgentInput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `LearningPathGeneratorOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `PersonalizedCurriculumInput` | `AgentInput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `PersonalizedCurriculumOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `SkillGapCurriculumAdapterInput` | `AgentInput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `SkillGapCurriculumAdapterOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `DifficultyBalancerInput` | `AgentInput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `DifficultyBalancerOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `StudyStrategyPlannerInput` | `AgentInput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `StudyStrategyPlannerOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `ReviewSchedulerInput` | `AgentInput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `ReviewSchedulerOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `RemediationPlannerInput` | `AgentInput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `RemediationPlannerOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `EnrichmentPlannerInput` | `AgentInput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `EnrichmentPlannerOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `ConceptReinforcementInput` | `AgentInput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `ConceptReinforcementOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `LongTermLearningPlannerInput` | `AgentInput` | `` |
| `engines/agents/content/models/curriculum_agents_46_60.py` | `LongTermLearningPlannerOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/evaluation_agents_41_45.py` | `EvaluationCriterion` | `BaseModel` | `` |
| `engines/agents/content/models/evaluation_agents_41_45.py` | `EvaluationScore` | `BaseModel` | `` |
| `engines/agents/content/models/evaluation_agents_41_45.py` | `EvaluationIssue` | `BaseModel` | `` |
| `engines/agents/content/models/evaluation_agents_41_45.py` | `AlignmentResult` | `BaseModel` | `` |
| `engines/agents/content/models/evaluation_agents_41_45.py` | `ConsistencyError` | `BaseModel` | `` |
| `engines/agents/content/models/evaluation_agents_41_45.py` | `CoverageGap` | `BaseModel` | `` |
| `engines/agents/content/models/evaluation_agents_41_45.py` | `QuestionQualityEvaluationInput` | `AgentInput` | `` |
| `engines/agents/content/models/evaluation_agents_41_45.py` | `QuestionQualityEvaluationOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/evaluation_agents_41_45.py` | `ExplanationQualityEvaluationInput` | `AgentInput` | `` |
| `engines/agents/content/models/evaluation_agents_41_45.py` | `ExplanationQualityEvaluationOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/evaluation_agents_41_45.py` | `PedagogicalAlignmentInput` | `AgentInput` | `` |
| `engines/agents/content/models/evaluation_agents_41_45.py` | `PedagogicalAlignmentOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/evaluation_agents_41_45.py` | `ConsistencyEvaluationInput` | `AgentInput` | `` |
| `engines/agents/content/models/evaluation_agents_41_45.py` | `ConsistencyEvaluationOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/evaluation_agents_41_45.py` | `CurriculumCoverageInput` | `AgentInput` | `` |
| `engines/agents/content/models/evaluation_agents_41_45.py` | `CurriculumCoverageOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/learning_objects.py` | `StudentProfile` | `BaseModel` | `` |
| `engines/agents/content/models/learning_objects.py` | `InstructorProfile` | `BaseModel` | `` |
| `engines/agents/content/models/learning_objects.py` | `VAKRStyle` | `str, Enum` | `` |
| `engines/agents/content/models/learning_objects.py` | `PacePreference` | `str, Enum` | `` |
| `engines/agents/content/models/learning_objects.py` | `AbstractionLevel` | `str, Enum` | `` |
| `engines/agents/content/models/learning_objects.py` | `FeedbackPreference` | `str, Enum` | `` |
| `engines/agents/content/models/learning_objects.py` | `LearningStyle` | `BaseModel` | `` |
| `engines/agents/content/models/learning_objects.py` | `LearningObjective` | `BaseModel` | `` |
| `engines/agents/content/models/learning_objects.py` | `Lesson` | `BaseModel` | `` |
| `engines/agents/content/models/learning_objects.py` | `ConceptNode` | `BaseModel` | `` |
| `engines/agents/content/models/learning_objects.py` | `GlossaryEntry` | `BaseModel` | `` |
| `engines/agents/content/models/learning_objects.py` | `Question` | `BaseModel` | `` |
| `engines/agents/content/models/learning_objects.py` | `StudentAnswer` | `BaseModel` | `` |
| `engines/agents/content/models/learning_objects.py` | `AssessmentResult` | `BaseModel` | `` |
| `engines/agents/content/models/learning_objects.py` | `Assignment` | `BaseModel` | `` |
| `engines/agents/content/models/learning_objects.py` | `LearningEvent` | `BaseModel` | `` |
| `engines/agents/content/models/learning_objects.py` | `SkillPerformance` | `BaseModel` | `` |
| `engines/agents/content/models/learning_objects.py` | `LearningProgress` | `BaseModel` | `` |
| `engines/agents/content/models/learning_objects.py` | `LearningResource` | `BaseModel` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `KnowledgeIngestionInput` | `AgentInput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `KnowledgeIngestionOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `DocumentChunkingInput` | `AgentInput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `DocumentChunkingOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `EmbeddingGeneratorInput` | `AgentInput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `EmbeddingGeneratorOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `SemanticIndexerInput` | `AgentInput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `SemanticIndexerOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `VectorSearchInput` | `AgentInput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `VectorSearchOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `HybridRetrievalInput` | `AgentInput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `HybridRetrievalOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `ContextBuilderInput` | `AgentInput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `ContextBuilderOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `MemoryConsolidationInput` | `AgentInput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `MemoryConsolidationOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `EpisodicMemoryInput` | `AgentInput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `EpisodicMemoryOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `StudentKnowledgeMemoryInput` | `AgentInput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `StudentKnowledgeMemoryOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `KnowledgeUpdaterInput` | `AgentInput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `KnowledgeUpdaterOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `KnowledgeConflictResolverInput` | `AgentInput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `KnowledgeConflictResolverOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `RetrievalRankerInput` | `AgentInput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `RetrievalRankerOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `ContextRelevanceEvaluatorInput` | `AgentInput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `ContextRelevanceEvaluatorOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `KnowledgeSummarizerInput` | `AgentInput` | `` |
| `engines/agents/content/models/memory_agents_76_90.py` | `KnowledgeSummarizerOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/multimodal_agents_101_110.py` | `TextToSpeechInput` | `AgentInput` | `` |
| `engines/agents/content/models/multimodal_agents_101_110.py` | `TextToSpeechOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/multimodal_agents_101_110.py` | `SpeechToTextInput` | `AgentInput` | `` |
| `engines/agents/content/models/multimodal_agents_101_110.py` | `SpeechToTextOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/multimodal_agents_101_110.py` | `VisualIllustrationInput` | `AgentInput` | `` |
| `engines/agents/content/models/multimodal_agents_101_110.py` | `VisualIllustrationOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/multimodal_agents_101_110.py` | `BoardDrawingInput` | `AgentInput` | `` |
| `engines/agents/content/models/multimodal_agents_101_110.py` | `BoardDrawingOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/multimodal_agents_101_110.py` | `EmotionAnalysisInput` | `AgentInput` | `` |
| `engines/agents/content/models/multimodal_agents_101_110.py` | `EmotionAnalysisOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/multimodal_agents_101_110.py` | `EngagementDetectorInput` | `AgentInput` | `` |
| `engines/agents/content/models/multimodal_agents_101_110.py` | `EngagementDetectorOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/multimodal_agents_101_110.py` | `VisualFeedbackInput` | `AgentInput` | `` |
| `engines/agents/content/models/multimodal_agents_101_110.py` | `VisualFeedbackOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/multimodal_agents_101_110.py` | `GestureRecognitionInput` | `AgentInput` | `` |
| `engines/agents/content/models/multimodal_agents_101_110.py` | `GestureRecognitionOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/multimodal_agents_101_110.py` | `AudioFeedbackInput` | `AgentInput` | `` |
| `engines/agents/content/models/multimodal_agents_101_110.py` | `AudioFeedbackOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/multimodal_agents_101_110.py` | `InteractiveLessonOrchestratorInput` | `AgentInput` | `` |
| `engines/agents/content/models/multimodal_agents_101_110.py` | `InteractiveLessonOrchestratorOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `LearningSessionPlannerInput` | `AgentInput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `LearningSessionPlannerOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `AgentWorkflowPlannerInput` | `AgentInput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `AgentWorkflowPlannerOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `TaskDecomposerInput` | `AgentInput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `TaskDecomposerOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `AgentSelectorInput` | `AgentInput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `AgentSelectorOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `ContextManagerInput` | `AgentInput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `ContextManagerOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `WorkflowStateTrackerInput` | `AgentInput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `WorkflowStateTrackerOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `FailureRecoveryInput` | `AgentInput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `FailureRecoveryOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `RetryStrategyInput` | `AgentInput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `RetryStrategyOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `ShortTermMemoryInput` | `AgentInput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `ShortTermMemoryOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `LongTermMemoryInput` | `AgentInput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `LongTermMemoryOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `WorkflowOptimizerInput` | `AgentInput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `WorkflowOptimizerOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `CostEfficiencyAnalyzerInput` | `AgentInput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `CostEfficiencyAnalyzerOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `AgentPerformanceMonitorInput` | `AgentInput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `AgentPerformanceMonitorOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `SystemHealthEvaluatorInput` | `AgentInput` | `` |
| `engines/agents/content/models/orchestration_agents_61_75.py` | `SystemHealthEvaluatorOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/personalization_agents_15_20.py` | `DialogueTutorInput` | `AgentInput` | `` |
| `engines/agents/content/models/personalization_agents_15_20.py` | `TutorResponse` | `BaseModel` | `` |
| `engines/agents/content/models/personalization_agents_15_20.py` | `DialogueTutorOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/personalization_agents_15_20.py` | `StyleAdaptationInput` | `AgentInput` | `` |
| `engines/agents/content/models/personalization_agents_15_20.py` | `AdaptedContent` | `BaseModel` | `` |
| `engines/agents/content/models/personalization_agents_15_20.py` | `StyleAdaptationOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/personalization_agents_15_20.py` | `ProgressAnalysisInput` | `AgentInput` | `` |
| `engines/agents/content/models/personalization_agents_15_20.py` | `ProgressAnalysisOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/personalization_agents_15_20.py` | `LearningPathCreationInput` | `AgentInput` | `` |
| `engines/agents/content/models/personalization_agents_15_20.py` | `LearningStep` | `BaseModel` | `` |
| `engines/agents/content/models/personalization_agents_15_20.py` | `LearningPathCreationOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/personalization_agents_15_20.py` | `ResourceRecommendationInput` | `AgentInput` | `` |
| `engines/agents/content/models/personalization_agents_15_20.py` | `RecommendedResource` | `BaseModel` | `` |
| `engines/agents/content/models/personalization_agents_15_20.py` | `ResourceRecommendationOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/personalization_agents_15_20.py` | `InteractionStyleAnalysisInput` | `AgentInput` | `` |
| `engines/agents/content/models/personalization_agents_15_20.py` | `InteractionPattern` | `BaseModel` | `` |
| `engines/agents/content/models/personalization_agents_15_20.py` | `InteractionStyleAnalysisOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/teaching_agents_9_14.py` | `QuestionRefineInput` | `AgentInput` | `` |
| `engines/agents/content/models/teaching_agents_9_14.py` | `QuestionRefineOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/teaching_agents_9_14.py` | `QuestionGenerationInput` | `AgentInput` | `` |
| `engines/agents/content/models/teaching_agents_9_14.py` | `QuestionGenerationOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/teaching_agents_9_14.py` | `HintGenerationInput` | `AgentInput` | `` |
| `engines/agents/content/models/teaching_agents_9_14.py` | `HintGenerationOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/teaching_agents_9_14.py` | `ExplanationGenerationInput` | `AgentInput` | `` |
| `engines/agents/content/models/teaching_agents_9_14.py` | `ExplanationGenerationOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/teaching_agents_9_14.py` | `DifficultyAdaptationInput` | `AgentInput` | `` |
| `engines/agents/content/models/teaching_agents_9_14.py` | `DifficultyAdaptationOutput` | `AgentOutput` | `` |
| `engines/agents/content/models/teaching_agents_9_14.py` | `MisconceptionDetectionInput` | `AgentInput` | `` |
| `engines/agents/content/models/teaching_agents_9_14.py` | `Misconception` | `AgentOutput` | `` |
| `engines/agents/content/models/teaching_agents_9_14.py` | `MisconceptionDetectionOutput` | `AgentOutput` | `` |
| `engines/agents/content/text_rewriter.py` | `TextRewriterAgent` | `BaseAgent` | `__init__, execute, _rewrite_text, _fallback_rewrite, _estimate_readability` |
| `engines/agents/models.py` | `AgentInput` | `BaseModel` | `` |
| `engines/agents/models.py` | `AgentOutput` | `BaseModel` | `` |
| `engines/agents/models.py` | `AgentExecutionRecord` | `BaseModel` | `` |
| `engines/buses/base_message_bus.py` | `MessageBus` | `ABC` | `publish, subscribe, unsubscribe, start, stop` |
| `engines/buses/durable_message_bus.py` | `DurableMessageBus` | `MessageBus` | `__init__, subscribe, unsubscribe, publish, _consume` |
| `engines/buses/in_memory_message_bus.py` | `InMemoryMessageBus` | `MessageBus` | `__init__, subscribe, unsubscribe, publish` |
| `engines/buses/kafka_bus.py` | `KafkaMessageBus` | `MessageBus` | `__init__, start, stop, subscribe, unsubscribe, publish ...` |
| `engines/buses/priority_message_bus.py` | `PrioritizedMessage` | `—` | `` |
| `engines/buses/priority_message_bus.py` | `PriorityMessageBus` | `MessageBus` | `__init__, start, stop, subscribe, unsubscribe, publish ...` |
| `engines/buses/rabbitmq_bus.py` | `RabbitMQMessageBus` | `MessageBus` | `__init__, start, stop, subscribe, unsubscribe, publish ...` |
| `engines/buses/redis_pub_sub_bus.py` | `RedisMessageBus` | `MessageBus` | `__init__, start, stop, subscribe, unsubscribe, publish ...` |
| `engines/buses/request_reply_bus.py` | `RequestReplyBus` | `MessageBus` | `__init__, subscribe, unsubscribe, publish, request` |
| `engines/buses/topic_message_bus.py` | `TopicMessageBus` | `MessageBus` | `__init__, subscribe, unsubscribe, publish` |
| `engines/document/chunking/base.py` | `BaseChunker` | `ABC` | `chunk_document` |
| `engines/document/chunking/models.py` | `ChunkingConfig` | `BaseModel` | `` |
| `engines/document/chunking/models.py` | `ChunkingResult` | `BaseModel` | `` |
| `engines/document/chunking/recursive_chunker.py` | `RecursiveTextChunker` | `BaseChunker` | `chunk_document, _split_text, _hard_split, _merge_segments, _build_chunk` |
| `engines/document/embedding/base.py` | `EmbeddingProvider` | `ABC` | `embed_texts, embed_query` |
| `engines/document/embedding/service.py` | `HashEmbeddingProvider` | `EmbeddingProvider` | `__init__, embed_texts, _embed_single` |
| `engines/document/embedding/service.py` | `DocumentEmbeddingService` | `—` | `__init__, embed_chunks, _batched` |
| `engines/document/ingestion/ingestion_context.py` | `IngestionContext` | `BaseModel` | `create, build_asset_record, build_document_record` |
| `engines/document/ingestion/ingestion_context.py` | `Config` | `—` | `` |
| `engines/document/ingestion/ingestion_errors.py` | `IngestionError` | `Exception` | `__init__, to_dict` |
| `engines/document/ingestion/ingestion_errors.py` | `InvalidDocumentError` | `IngestionError` | `` |
| `engines/document/ingestion/ingestion_errors.py` | `UnsupportedMediaTypeError` | `IngestionError` | `__init__` |
| `engines/document/ingestion/ingestion_errors.py` | `ExtractionFailed` | `IngestionError` | `` |
| `engines/document/ingestion/ingestion_errors.py` | `ParseFailed` | `IngestionError` | `` |
| `engines/document/ingestion/ingestion_errors.py` | `ChunkingFailed` | `IngestionError` | `` |
| `engines/document/ingestion/ingestion_errors.py` | `EmbeddingFailed` | `IngestionError` | `` |
| `engines/document/ingestion/ingestion_errors.py` | `StorageFailed` | `IngestionError` | `` |
| `engines/document/ingestion/ingestion_errors.py` | `FinalizationFailed` | `IngestionError` | `` |
| `engines/document/ingestion/ingestion_errors.py` | `IngestionStepFailed` | `IngestionError` | `__init__` |
| `engines/document/ingestion/ingestion_models.py` | `DocumentAsset` | `—` | `` |
| `engines/document/ingestion/ingestion_models.py` | `DocumentRecord` | `BaseModel` | `` |
| `engines/document/ingestion/ingestion_models.py` | `ParsedDocument` | `—` | `` |
| `engines/document/ingestion/ingestion_models.py` | `ChunkRecord` | `BaseModel` | `` |
| `engines/document/ingestion/ingestion_models.py` | `IngestionStatus` | `str, Enum` | `` |
| `engines/document/ingestion/ingestion_models.py` | `StorageLocation` | `str, Enum` | `` |
| `engines/document/ingestion/ingestion_models.py` | `IngestionEvent` | `—` | `` |
| `engines/document/ingestion/ingestion_models.py` | `EmbeddingRecord` | `—` | `` |
| `engines/document/ingestion/ingestion_models.py` | `DocumentIngestionResult` | `BaseModel` | `add_event` |
| `engines/document/ingestion/ingestion_pipeline.py` | `IngestionPipeline` | `—` | `__init__, run` |
| `engines/document/ingestion/ingestion_runner.py` | `IngestionRunner` | `—` | `__init__, route, execute` |
| `engines/document/ingestion/ingestion_service.py` | `IngestionService` | `—` | `__init__, initialize_workflow_registry, initialize_document_registry, ingest` |
| `engines/document/ingestion/ingestion_utils.py` | `IngestionUtils` | `—` | `compute_sha256, guess_extension, make_object_key` |
| `engines/document/ingestion/ingestion_validator.py` | `IngestionValidator` | `—` | `validate_input` |
| `engines/document/ingestion/services/async_ingest_service.py` | `AsyncIngestService` | `—` | `__init__, process_message, _resolve_media_type` |
| `engines/document/ingestion/services/batch_ingest_service.py` | `BatchIngestService` | `—` | `__init__, ingest_sequential, ingest_parallel, handle` |
| `engines/document/ingestion/services/ingestion_scheduler.py` | `IngestionScheduler` | `—` | `__init__, ingest_folder, ingest_iterable, handle` |
| `engines/document/ingestion/services/upload_service.py` | `UploadService` | `—` | `__init__, ingest` |
| `engines/document/ingestion/utils/retry_policy.py` | `RetryPolicy` | `—` | `__init__, run` |
| `engines/document/ingestion/utils/timing.py` | `Stopwatch` | `—` | `__init__, start, stop, reset, read` |
| `engines/document/ingestion/workflow_registry.py` | `WorkflowRegistry` | `—` | `__init__, register, get` |
| `engines/document/models/base.py` | `ElementType` | `str, Enum` | `` |
| `engines/document/models/base.py` | `BinaryEncoding` | `str, Enum` | `` |
| `engines/document/models/base.py` | `CompressionMethod` | `str, Enum` | `` |
| `engines/document/models/base.py` | `BaseDocument` | `BaseModel` | `has_binary_content, has_text_content, content_size, get_effective_content` |
| `engines/document/models/base.py` | `BinaryPayload` | `BaseModel` | `has_content` |
| `engines/document/models/chunked_binary_payload.py` | `ChunkedBinaryPayload` | `BinaryPayload` | `compute_merkle_root` |
| `engines/document/models/csdm_core.py` | `CSDMHandle` | `—` | `new` |
| `engines/document/models/csdm_core.py` | `EntityType` | `str, Enum` | `` |
| `engines/document/models/csdm_core.py` | `XDataEntry` | `—` | `` |
| `engines/document/models/csdm_core.py` | `XDataContainer` | `—` | `add` |
| `engines/document/models/csdm_core.py` | `AddReactorsMixin` | `—` | `__init__, add_reactor, remove_reactor, add_xreactor, remove_xreactor` |
| `engines/document/models/csdm_core.py` | `ReactorLink` | `—` | `` |
| `engines/document/models/csdm_core.py` | `ReactorGraph` | `—` | `add` |
| `engines/document/models/csdm_core.py` | `CSDMObject` | `—` | `` |
| `engines/document/models/csdm_core.py` | `Vector3` | `—` | `` |
| `engines/document/models/csdm_core.py` | `Matrix4` | `—` | `__matmul__` |
| `engines/document/models/csdm_core.py` | `GeometryData` | `—` | `` |
| `engines/document/models/csdm_core.py` | `CSDMEntity` | `CSDMObject` | `` |
| `engines/document/models/csdm_core.py` | `EntityRegistry` | `—` | `register, create, get` |
| `engines/document/models/csdm_core.py` | `CSDMCustomObject` | `CSDMObject` | `` |
| `engines/document/models/csdm_core.py` | `CSDMHeader` | `—` | `` |
| `engines/document/models/csdm_core.py` | `CSDMMetadata` | `—` | `` |
| `engines/document/models/csdm_core.py` | `CSDMDictionaryEntry` | `—` | `` |
| `engines/document/models/csdm_core.py` | `CSDMDictionary` | `CSDMObject` | `add, get` |
| `engines/document/models/csdm_core.py` | `CSDMGroup` | `CSDMObject` | `` |
| `engines/document/models/csdm_core.py` | `PlotSettings` | `CSDMObject` | `` |
| `engines/document/models/csdm_core.py` | `CSDMLayout` | `CSDMObject` | `` |
| `engines/document/models/csdm_core.py` | `CSDMMaterial` | `CSDMObject` | `` |
| `engines/document/models/csdm_core.py` | `CSDMMLeaderStyle` | `CSDMObject` | `` |
| `engines/document/models/csdm_core.py` | `CSDMTableStyle` | `CSDMObject` | `` |
| `engines/document/models/csdm_core.py` | `CSDMImageDef` | `CSDMObject` | `` |
| `engines/document/models/csdm_core.py` | `CSDMUnderlayDef` | `CSDMObject` | `` |
| `engines/document/models/csdm_core.py` | `CSDMXref` | `CSDMObject` | `` |
| `engines/document/models/csdm_core.py` | `GeometryUnits` | `—` | `` |
| `engines/document/models/csdm_core.py` | `CSDMObjectTables` | `—` | `` |
| `engines/document/models/csdm_core.py` | `CSDMDocument` | `BaseDocument` | `register_object, find_by_handle, add_entity, add_object, add_block, add_xref` |
| `engines/document/models/csdm_core.py` | `AnnotationScale` | `—` | `` |
| `engines/document/models/csdm_core.py` | `AnnotationContext` | `—` | `add_scale, set_current_scale, get_ratio` |
| `engines/document/models/csdm_core.py` | `DimContext` | `—` | `get_dimscale` |
| `engines/document/models/csdm_core.py` | `ConstraintNode` | `—` | `` |
| `engines/document/models/csdm_core.py` | `ConstraintRelation` | `—` | `` |
| `engines/document/models/csdm_core.py` | `ConstraintGraph` | `—` | `add_node, add_relation` |
| `engines/document/models/csdm_core.py` | `BRepData` | `—` | `` |
| `engines/document/models/csdm_core.py` | `ACISInterface` | `—` | `extract_brep, attach_brep` |
| `engines/document/models/csdm_core.py` | `BodyEntity` | `CSDMEntity` | `` |
| `engines/document/models/csdm_core.py` | `Solid3DEntity` | `CSDMEntity` | `` |
| `engines/document/models/csdm_core.py` | `SurfaceEntity` | `CSDMEntity` | `` |
| `engines/document/models/csdm_entities.py` | `Vertex` | `—` | `` |
| `engines/document/models/csdm_entities.py` | `NormalVector` | `—` | `` |
| `engines/document/models/csdm_entities.py` | `Extrusion` | `—` | `` |
| `engines/document/models/csdm_entities.py` | `BaseEntity` | `CSDMObject, AddReactorsMixin` | `add_xdata, apply_transform` |
| `engines/document/models/csdm_entities.py` | `CurveEntity` | `BaseEntity` | `` |
| `engines/document/models/csdm_entities.py` | `SurfaceEntity` | `BaseEntity` | `` |
| `engines/document/models/csdm_entities.py` | `SolidEntity` | `BaseEntity` | `` |
| `engines/document/models/csdm_entities.py` | `TextBaseEntity` | `BaseEntity` | `` |
| `engines/document/models/csdm_entities.py` | `DimensionType` | `Enum` | `` |
| `engines/document/models/csdm_entities.py` | `DimensionBase` | `BaseEntity` | `` |
| `engines/document/models/csdm_entities.py` | `BlockRefBase` | `BaseEntity` | `` |
| `engines/document/models/csdm_entities.py` | `LineEntity` | `CurveEntity` | `` |
| `engines/document/models/csdm_entities.py` | `CircleEntity` | `CurveEntity` | `` |
| `engines/document/models/csdm_entities.py` | `ArcEntity` | `CurveEntity` | `` |
| `engines/document/models/csdm_entities.py` | `EllipseEntity` | `CurveEntity` | `` |
| `engines/document/models/csdm_entities.py` | `PolylineEntity` | `CurveEntity` | `` |
| `engines/document/models/csdm_entities.py` | `LWPolylineEntity` | `CurveEntity` | `` |
| `engines/document/models/csdm_entities.py` | `SplineEntity` | `CurveEntity` | `` |
| `engines/document/models/csdm_entities.py` | `RayEntity` | `CurveEntity` | `` |
| `engines/document/models/csdm_entities.py` | `XLineEntity` | `CurveEntity` | `` |
| `engines/document/models/csdm_entities.py` | `Solid2DEntity` | `CurveEntity` | `` |
| `engines/document/models/csdm_entities.py` | `Face3DEntity` | `CurveEntity` | `` |
| `engines/document/models/csdm_entities.py` | `TraceEntity` | `CurveEntity` | `` |
| `engines/document/models/csdm_entities.py` | `ShapeEntity` | `CurveEntity` | `` |
| `engines/document/models/csdm_entities.py` | `RegionEntity` | `SolidEntity` | `` |
| `engines/document/models/csdm_entities.py` | `BodyEntity` | `SolidEntity` | `` |
| `engines/document/models/csdm_entities.py` | `Solid3DEntity` | `SolidEntity` | `` |
| `engines/document/models/csdm_entities.py` | `SurfaceACISEntity` | `SurfaceEntity` | `` |
| `engines/document/models/csdm_entities.py` | `HatchLoop` | `—` | `` |
| `engines/document/models/csdm_entities.py` | `HatchEntity` | `BaseEntity` | `` |
| `engines/document/models/csdm_entities.py` | `TextEntity` | `TextBaseEntity` | `` |
| `engines/document/models/csdm_entities.py` | `MTextEntity` | `TextBaseEntity` | `` |
| `engines/document/models/csdm_entities.py` | `LeaderEntity` | `CurveEntity` | `` |
| `engines/document/models/csdm_entities.py` | `MLeaderEntity` | `BaseEntity` | `` |
| `engines/document/models/csdm_entities.py` | `DimensionEntity` | `DimensionBase` | `` |
| `engines/document/models/csdm_entities.py` | `BlockReference` | `BlockRefBase` | `` |
| `engines/document/models/csdm_entities.py` | `MInsertEntity` | `BlockRefBase` | `` |
| `engines/document/models/csdm_entities.py` | `AttributeEntity` | `TextBaseEntity` | `` |
| `engines/document/models/csdm_entities.py` | `AttributeDefEntity` | `TextBaseEntity` | `` |
| `engines/document/models/csdm_entities.py` | `ImageEntity` | `BaseEntity` | `` |
| `engines/document/models/csdm_entities.py` | `UnderlayEntity` | `BaseEntity` | `` |
| `engines/document/models/csdm_entities.py` | `WipeoutEntity` | `BaseEntity` | `` |
| `engines/document/models/csdm_entities.py` | `OLE2FrameEntity` | `BaseEntity` | `` |
| `engines/document/models/csdm_entities.py` | `PointEntity` | `BaseEntity` | `` |
| `engines/document/models/csdm_entities.py` | `MLineEntity` | `BaseEntity` | `` |
| `engines/document/models/csdm_entities.py` | `ToleranceEntity` | `BaseEntity` | `` |
| `engines/document/models/csdm_entities.py` | `FieldEntity` | `BaseEntity` | `` |
| `engines/document/models/csdm_entities.py` | `MLeaderTextContent` | `—` | `` |
| `engines/document/models/csdm_entities.py` | `MLeaderBlockContent` | `—` | `` |
| `engines/document/models/csdm_entities.py` | `MLeaderToleranceContent` | `—` | `` |
| `engines/document/models/csdm_entities.py` | `MLeaderContentEntity` | `BaseEntity` | `` |
| `engines/document/models/csdm_entities.py` | `CADTableCell` | `—` | `` |
| `engines/document/models/csdm_entities.py` | `CADTableRow` | `—` | `` |
| `engines/document/models/csdm_entities.py` | `TableEntity` | `BaseEntity` | `add_row` |
| `engines/document/models/csdm_entities.py` | `ConstraintType` | `—` | `` |
| `engines/document/models/csdm_entities.py` | `GeometricConstraintEntity` | `BaseEntity` | `` |
| `engines/document/models/csdm_entities.py` | `DimConstraintKind` | `—` | `` |
| `engines/document/models/csdm_entities.py` | `DimensionalConstraintEntity` | `BaseEntity` | `` |
| `engines/document/models/csdm_entities.py` | `DCFCustomEntity` | `BaseEntity` | `` |
| `engines/document/models/csdm_tables.py` | `TableEntry` | `CSDMObject` | `` |
| `engines/document/models/csdm_tables.py` | `LayerEntry` | `TableEntry` | `` |
| `engines/document/models/csdm_tables.py` | `LayerTable` | `CSDMObject` | `add` |
| `engines/document/models/csdm_tables.py` | `LinetypeSegment` | `—` | `` |
| `engines/document/models/csdm_tables.py` | `LinetypeEntry` | `TableEntry` | `` |
| `engines/document/models/csdm_tables.py` | `LinetypeTable` | `CSDMObject` | `add` |
| `engines/document/models/csdm_tables.py` | `TextStyleEntry` | `TableEntry` | `` |
| `engines/document/models/csdm_tables.py` | `TextStyleTable` | `CSDMObject` | `add` |
| `engines/document/models/csdm_tables.py` | `DimLUnit` | `Enum` | `` |
| `engines/document/models/csdm_tables.py` | `DimStyleEntry` | `TableEntry` | `` |
| `engines/document/models/csdm_tables.py` | `DimStyleTable` | `CSDMObject` | `add` |
| `engines/document/models/csdm_tables.py` | `UCSRecord` | `TableEntry` | `` |
| `engines/document/models/csdm_tables.py` | `UCSTable` | `CSDMObject` | `add` |
| `engines/document/models/csdm_tables.py` | `ViewRecord` | `TableEntry` | `` |
| `engines/document/models/csdm_tables.py` | `ViewTable` | `CSDMObject` | `add` |
| `engines/document/models/csdm_tables.py` | `VPortRecord` | `TableEntry` | `` |
| `engines/document/models/csdm_tables.py` | `VPortTable` | `CSDMObject` | `add` |
| `engines/document/models/csdm_tables.py` | `AppIDEntry` | `TableEntry` | `` |
| `engines/document/models/csdm_tables.py` | `AppIDTable` | `CSDMObject` | `add` |
| `engines/document/models/csdm_tables.py` | `BlockRecord` | `TableEntry` | `` |
| `engines/document/models/csdm_tables.py` | `BlockRecordTable` | `CSDMObject` | `add` |
| `engines/document/models/csdm_tables.py` | `PlotStyleEntry` | `TableEntry` | `` |
| `engines/document/models/csdm_tables.py` | `PlotStyleTable` | `CSDMObject` | `add` |
| `engines/document/models/csdm_tables.py` | `MaterialEntry` | `TableEntry` | `` |
| `engines/document/models/csdm_tables.py` | `MaterialTableDWG` | `CSDMObject` | `add` |
| `engines/document/models/csdm_tables.py` | `DimStyleOverride` | `—` | `` |
| `engines/document/models/csdm_tables.py` | `DimStyleOverrideTable` | `CSDMObject` | `set` |
| `engines/document/models/csdm_tables.py` | `MLineElement` | `—` | `` |
| `engines/document/models/csdm_tables.py` | `MLineStyle` | `TableEntry` | `` |
| `engines/document/models/csdm_tables.py` | `MLineStyleTable` | `CSDMObject` | `add` |
| `engines/document/models/csdm_tables.py` | `TableCellStyle` | `—` | `` |
| `engines/document/models/csdm_tables.py` | `CADTableStyle` | `TableEntry` | `` |
| `engines/document/models/csdm_tables.py` | `TableStyleTable` | `CSDMObject` | `add` |
| `engines/document/models/csdm_tables.py` | `MLeaderTextAlign` | `Enum` | `` |
| `engines/document/models/csdm_tables.py` | `MLeaderStyle` | `TableEntry` | `` |
| `engines/document/models/csdm_tables.py` | `MLeaderStyleTable` | `CSDMObject` | `add` |
| `engines/document/models/csdm_tables.py` | `LightType` | `Enum` | `` |
| `engines/document/models/csdm_tables.py` | `LightRecord` | `TableEntry` | `` |
| `engines/document/models/csdm_tables.py` | `LightTable` | `CSDMObject` | `add` |
| `engines/document/models/csdm_tables.py` | `RenderEnvironment` | `TableEntry` | `` |
| `engines/document/models/csdm_tables.py` | `RenderEnvironmentTable` | `CSDMObject` | `add` |
| `engines/document/models/csdm_tables.py` | `RenderSettings` | `TableEntry` | `` |
| `engines/document/models/csdm_tables.py` | `RenderSettingsTable` | `CSDMObject` | `add` |
| `engines/document/models/csdm_tables.py` | `UnderlayType` | `Enum` | `` |
| `engines/document/models/csdm_tables.py` | `UnderlayDefinition` | `TableEntry` | `` |
| `engines/document/models/csdm_tables.py` | `UnderlayTable` | `CSDMObject` | `add` |
| `engines/document/models/csdm_tables.py` | `RasterImageDef` | `TableEntry` | `` |
| `engines/document/models/csdm_tables.py` | `RasterImageTable` | `CSDMObject` | `add` |
| `engines/document/models/csdm_tables.py` | `PlotConfig` | `TableEntry` | `` |
| `engines/document/models/csdm_tables.py` | `PlotConfigTable` | `CSDMObject` | `add` |
| `engines/document/models/csdm_tables.py` | `OLEObject` | `TableEntry` | `` |
| `engines/document/models/csdm_tables.py` | `OLETable` | `CSDMObject` | `add` |
| `engines/document/models/csdm_tables.py` | `DataLink` | `TableEntry` | `` |
| `engines/document/models/csdm_tables.py` | `DataLinkTable` | `CSDMObject` | `add` |
| `engines/document/models/csdm_tables.py` | `DCFTableEntry` | `TableEntry` | `` |
| `engines/document/models/csdm_tables.py` | `DCFCustomTable` | `CSDMObject` | `add` |
| `engines/document/models/csdm_tables.py` | `CSDMTableCollection` | `—` | `create_defaults, register_dcf_table` |
| `engines/document/models/document_registry.py` | `DocumentRegistry` | `—` | `__init__, register_parser_plugin, register_writer_plugin, _detect_magic_mime, _fallback_mime_detection, resolve_media_type ...` |
| `engines/document/models/dsdm_models.py` | `DataNodeKind` | `str, Enum` | `` |
| `engines/document/models/dsdm_models.py` | `ScalarType` | `str, Enum` | `` |
| `engines/document/models/dsdm_models.py` | `DataValue` | `BaseModel` | `` |
| `engines/document/models/dsdm_models.py` | `DataSchemaReference` | `BaseModel` | `` |
| `engines/document/models/dsdm_models.py` | `DataDocumentCapabilities` | `BaseModel` | `` |
| `engines/document/models/dsdm_models.py` | `DataNode` | `BaseModel` | `is_leaf` |
| `engines/document/models/dsdm_models.py` | `DataDocument` | `BaseDocument` | `` |
| `engines/document/models/esdm_models.py` | `DocumentBaseModel` | `—` | `` |
| `engines/document/models/esdm_models.py` | `WorkbookProperties` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `Relationship` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `RelationshipCollection` | `DocumentBaseModel` | `add, find_by_type` |
| `engines/document/models/esdm_models.py` | `SharedStrings` | `DocumentBaseModel` | `get_index` |
| `engines/document/models/esdm_models.py` | `SheetDimensions` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `WorksheetProperties` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `Cell` | `DocumentBaseModel` | `coordinate, _col_to_letter` |
| `engines/document/models/esdm_models.py` | `Row` | `DocumentBaseModel` | `get_or_create_cell` |
| `engines/document/models/esdm_models.py` | `Column` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `CellRange` | `DocumentBaseModel` | `coord, _coord` |
| `engines/document/models/esdm_models.py` | `MergedCellRange` | `CellRange` | `` |
| `engines/document/models/esdm_models.py` | `NamedRange` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `Worksheet` | `DocumentBaseModel` | `get_row, get_cell, merge_cells` |
| `engines/document/models/esdm_models.py` | `Workbook` | `BaseDocument` | `add_sheet` |
| `engines/document/models/esdm_models.py` | `NumberFormat` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `NumberFormatCollection` | `DocumentBaseModel` | `add_custom_format, find` |
| `engines/document/models/esdm_models.py` | `FontUnderline` | `Enum` | `` |
| `engines/document/models/esdm_models.py` | `Font` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `FontCollection` | `DocumentBaseModel` | `register` |
| `engines/document/models/esdm_models.py` | `PatternType` | `Enum` | `` |
| `engines/document/models/esdm_models.py` | `PatternFill` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `GradientStop` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `GradientFill` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `Fill` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `FillCollection` | `DocumentBaseModel` | `register` |
| `engines/document/models/esdm_models.py` | `BorderStyle` | `Enum` | `` |
| `engines/document/models/esdm_models.py` | `BorderSide` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `Border` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `BorderCollection` | `DocumentBaseModel` | `register` |
| `engines/document/models/esdm_models.py` | `HorizontalAlign` | `Enum` | `` |
| `engines/document/models/esdm_models.py` | `VerticalAlign` | `Enum` | `` |
| `engines/document/models/esdm_models.py` | `Alignment` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `Protection` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `CellFormat` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `CellFormatCollection` | `DocumentBaseModel` | `register` |
| `engines/document/models/esdm_models.py` | `CellStyle` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `CellStyleCollection` | `DocumentBaseModel` | `register` |
| `engines/document/models/esdm_models.py` | `DifferentialFormat` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `DifferentialFormatCollection` | `DocumentBaseModel` | `register` |
| `engines/document/models/esdm_models.py` | `TableStyleElement` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `ExcelTableStyle` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `TableStyleCollection` | `DocumentBaseModel` | `register` |
| `engines/document/models/esdm_models.py` | `Stylesheet` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `DynamicFilterType` | `Enum` | `` |
| `engines/document/models/esdm_models.py` | `FilterOperator` | `Enum` | `` |
| `engines/document/models/esdm_models.py` | `CustomFilter` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `Filters` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `FilterColumn` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `AutoFilter` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `TableColumn` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `ExcelTableRow` | `DocumentBaseModel` | `get_value, set_value` |
| `engines/document/models/esdm_models.py` | `TableStyleInfo` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `Table` | `DocumentBaseModel` | `get_column_by_name, add_column, add_row` |
| `engines/document/models/esdm_models.py` | `TableCollection` | `DocumentBaseModel` | `add, find` |
| `engines/document/models/esdm_models.py` | `CFType` | `Enum` | `` |
| `engines/document/models/esdm_models.py` | `CFOperator` | `Enum` | `` |
| `engines/document/models/esdm_models.py` | `CFValueObject` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `ColorScale` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `DataBar` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `IconSetType` | `Enum` | `` |
| `engines/document/models/esdm_models.py` | `IconCriterion` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `IconSet` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `CFRule` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `ConditionalFormatting` | `DocumentBaseModel` | `add_rule` |
| `engines/document/models/esdm_models.py` | `ConditionalFormattingCollection` | `DocumentBaseModel` | `add, for_range` |
| `engines/document/models/esdm_models.py` | `FormulaTokenType` | `Enum` | `` |
| `engines/document/models/esdm_models.py` | `FormulaToken` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `FormulaAST` | `DocumentBaseModel` | `from_string, to_string` |
| `engines/document/models/esdm_models.py` | `SharedFormula` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `SharedFormulaCollection` | `DocumentBaseModel` | `add, get` |
| `engines/document/models/esdm_models.py` | `DefinedName` | `DocumentBaseModel` | `is_global` |
| `engines/document/models/esdm_models.py` | `DefinedNameCollection` | `DocumentBaseModel` | `add, find` |
| `engines/document/models/esdm_models.py` | `ExternalReference` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `ExternalLink` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `ExternalLinkCollection` | `DocumentBaseModel` | `add, get_by_id` |
| `engines/document/models/esdm_models.py` | `CellFormula` | `DocumentBaseModel` | `create, get` |
| `engines/document/models/esdm_models.py` | `DataValidationType` | `Enum` | `` |
| `engines/document/models/esdm_models.py` | `DataValidationOperator` | `Enum` | `` |
| `engines/document/models/esdm_models.py` | `DataValidationRule` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `DataValidation` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `DataValidationCollection` | `DocumentBaseModel` | `add` |
| `engines/document/models/esdm_models.py` | `Hyperlink` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `HyperlinkCollection` | `DocumentBaseModel` | `add` |
| `engines/document/models/esdm_models.py` | `Author` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `CommentTextRun` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `CommentText` | `DocumentBaseModel` | `from_string` |
| `engines/document/models/esdm_models.py` | `Comment` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `CommentCollection` | `DocumentBaseModel` | `add_author, add_comment` |
| `engines/document/models/esdm_models.py` | `ThreadedComment` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `ThreadedCommentCollection` | `DocumentBaseModel` | `add` |
| `engines/document/models/esdm_models.py` | `SheetProperties` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `SheetProtection` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `Orientation` | `Enum` | `` |
| `engines/document/models/esdm_models.py` | `PageMargins` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `PageSetup` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `CalcChainEntry` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `CalculationChain` | `DocumentBaseModel` | `add` |
| `engines/document/models/esdm_models.py` | `RichTextRun` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `RichText` | `DocumentBaseModel` | `from_string` |
| `engines/document/models/esdm_models.py` | `PivotField` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `PivotCacheReference` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `PivotCache` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `PivotTable` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `PivotCacheCollection` | `DocumentBaseModel` | `add` |
| `engines/document/models/esdm_models.py` | `PivotTableCollection` | `DocumentBaseModel` | `add` |
| `engines/document/models/exceptions.py` | `DocumentError` | `Exception` | `` |
| `engines/document/models/exceptions.py` | `DocumentParseError` | `DocumentError` | `` |
| `engines/document/models/exceptions.py` | `DocumentWriteError` | `DocumentError` | `` |
| `engines/document/models/exceptions.py` | `DocumentValidationError` | `DocumentError` | `` |
| `engines/document/models/exceptions.py` | `UnsupportedFormatError` | `DocumentError` | `__init__` |
| `engines/document/models/exceptions.py` | `BinaryEncodingError` | `DocumentError` | `` |
| `engines/document/models/exceptions.py` | `StreamingError` | `DocumentError` | `` |
| `engines/document/models/exceptions.py` | `RegistryError` | `DocumentError` | `` |
| `engines/document/models/exceptions.py` | `CompressionError` | `DocumentError` | `` |
| `engines/document/models/exceptions.py` | `SchemaValidationError` | `DocumentValidationError` | `` |
| `engines/document/models/exceptions.py` | `ContentDetectionError` | `DocumentError` | `` |
| `engines/document/models/media_types.py` | `DocumentFormat` | `str, Enum` | `` |
| `engines/document/models/media_types.py` | `MediaContentKind` | `str, Enum` | `` |
| `engines/document/models/media_types.py` | `MediaRawType` | `str, Enum` | `` |
| `engines/document/models/media_types.py` | `MediaType` | `BaseModel` | `` |
| `engines/document/models/media_types.py` | `MediaTypeRegistry` | `—` | `get_by_format, get_by_extension, get_by_mime, all` |
| `engines/document/models/standard.py` | `DocumentStandard` | `str, Enum` | `full_name, description` |
| `engines/document/models/standard.py` | `MediaCategory` | `str, Enum` | `` |
| `engines/document/models/usdm_models.py` | `USDMDcoument` | `BaseDocument` | `` |
| `engines/document/models/usdm_models.py` | `DocumentElement` | `—` | `` |
| `engines/document/models/usdm_models.py` | `Section` | `—` | `` |
| `engines/document/models/usdm_models.py` | `PageContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `LogicalElement` | `—` | `` |
| `engines/document/models/usdm_models.py` | `RichTextSpan` | `—` | `` |
| `engines/document/models/usdm_models.py` | `RichTextContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `ParagraphContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `HeadingContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `MathContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `CodeContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `ImageContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `ListItemContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `ListContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `TableCell` | `—` | `` |
| `engines/document/models/usdm_models.py` | `TableRow` | `—` | `` |
| `engines/document/models/usdm_models.py` | `TableContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `QuoteContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `BinaryContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `TextRun` | `—` | `` |
| `engines/document/models/usdm_models.py` | `ImageObject` | `—` | `` |
| `engines/document/models/usdm_models.py` | `VectorPath` | `—` | `` |
| `engines/document/models/usdm_models.py` | `AnnotationObject` | `—` | `` |
| `engines/document/models/usdm_models.py` | `Page` | `—` | `` |
| `engines/document/models/usdm_models.py` | `CharacterStyle` | `—` | `` |
| `engines/document/models/usdm_models.py` | `ParagraphStyle` | `—` | `` |
| `engines/document/models/usdm_models.py` | `TableStyle` | `—` | `` |
| `engines/document/models/usdm_models.py` | `ListStyle` | `—` | `` |
| `engines/document/models/usdm_models.py` | `StyleSheet` | `—` | `` |
| `engines/document/models/usdm_models.py` | `FormulaContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `LinkContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `CommentContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `PageBreakContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `LineBreakContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `ColumnBreakContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `PDFTextRun` | `—` | `` |
| `engines/document/models/usdm_models.py` | `PDFVectorPath` | `—` | `` |
| `engines/document/models/usdm_models.py` | `LaTeXEnvironmentContent` | `LogicalContent` | `` |
| `engines/document/models/usdm_models.py` | `LaTeXCommandContent` | `LogicalContent` | `` |
| `engines/document/models/usdm_models.py` | `SemanticHTMLContent` | `LogicalContent` | `` |
| `engines/document/models/usdm_models.py` | `CanvasContent` | `LogicalContent` | `` |
| `engines/document/models/usdm_models.py` | `DocumentMetadata` | `—` | `` |
| `engines/document/models/usdm_models.py` | `CrossReference` | `—` | `` |
| `engines/document/models/usdm_models.py` | `BibliographyEntry` | `—` | `` |
| `engines/document/models/usdm_models.py` | `ChangeTracking` | `—` | `` |
| `engines/document/models/usdm_models.py` | `Revision` | `—` | `` |
| `engines/document/models/usdm_models.py` | `PresentationHint` | `—` | `` |
| `engines/document/models/usdm_models.py` | `FormatPlugin` | `ABC` | `to_usdm, from_usdm` |
| `engines/document/models/usdm_models.py` | `TransformationRule` | `—` | `` |
| `engines/document/models/usdm_models.py` | `TransformationPipeline` | `—` | `__init__, add_rule` |
| `engines/document/models/usdm_models.py` | `ConversionQuality` | `—` | `` |
| `engines/document/models/usdm_models.py` | `BookmarkContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `FootnoteContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `EndnoteContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `EmbeddedObjectContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `OLEObjectContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `VideoContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `AudioContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `ShapeContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `DrawingContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `ChartContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `DataContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `SpreadsheetContent` | `—` | `` |
| `engines/document/parsers/base.py` | `ParseOptions` | `BaseModel` | `` |
| `engines/document/parsers/base.py` | `BaseDocumentParser` | `ABC` | `parse_bytes, parse_path, parse_stream, supports_extension, iter_supported_extensions` |
| `engines/document/parsers/binary_parser.py` | `BinaryParser` | `BaseDocumentParser` | `__init__, parse_bytes, parse_path, parse_stream, _detect_format, _parse_binary_data ...` |
| `engines/document/parsers/binary_parser.py` | `RestrictedUnpickler` | `pickle.Unpickler` | `find_class` |
| `engines/document/parsers/docx_parser/docx_extractor.py` | `DOCXExtractor` | `—` | `__init__, extract, extract_document_xml, extract_styles_xml, extract_numbering_xml, get_relationship_target ...` |
| `engines/document/parsers/docx_parser/docx_image_extractor.py` | `DOCXImageExtractor` | `—` | `__init__, extract_all_images, extract_image_by_rel_id, extract_image_by_path, extract_images_from_drawing_elements, get_image_metadata ...` |
| `engines/document/parsers/docx_parser/docx_math_parser.py` | `OMMLParser` | `—` | `__init__, _register_namespaces, parse_math_paragraph, parse_math, parse_math_from_xml, _parse_math_element ...` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXElementType` | `str, Enum` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `RunPropertyName` | `str, Enum` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `ParagraphAlignment` | `str, Enum` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `NumberingLevelSuffix` | `str, Enum` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `SectionType` | `str, Enum` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `VerticalAlignment` | `str, Enum` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `TextDirection` | `str, Enum` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXRunProperties` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXTextRun` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXDrawing` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXField` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXSymbol` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXBreak` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXTab` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXRunContent` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXParagraphProperties` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXParagraph` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXTableCellProperties` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXTableCell` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXTableRow` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXTableProperties` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXTableGrid` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXTable` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXStyleRunProperties` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXStyleParagraphProperties` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXStyleTableProperties` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXStyle` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXNumberingLevel` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXNumberingDefinition` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXNumberingInstance` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXHeaderFooter` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXPageSize` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXPageMargins` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXColumns` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXSection` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXComment` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXFootnoteEndnote` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXMathElement` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXMath` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXCoreProperties` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXExtendedProperties` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXCustomProperties` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXDocument` | `—` | `` |
| `engines/document/parsers/docx_parser/docx_style_parser.py` | `DocxStyleParser` | `—` | `__init__, parse_styles, _parse_style, _parse_run_properties, _parse_paragraph_properties, _parse_table_properties` |
| `engines/document/parsers/docx_parser/docx_table_parser.py` | `DocxTableParser` | `—` | `__init__, parse_table, parse_all_tables` |
| `engines/document/parsers/docx_parser/docx_utils.py` | `DocxStyleInfo` | `—` | `__post_init__` |
| `engines/document/parsers/docx_parser/docx_utils.py` | `DocxNumberingInfo` | `—` | `__post_init__` |
| `engines/document/parsers/docx_parser/docx_utils.py` | `DocxUtils` | `—` | `extract_text_style, extract_paragraph_style, extract_style_properties, extract_numbering_definition, extract_text_from_element, convert_omml_to_latex ...` |
| `engines/document/parsers/html_parser.py` | `HTMLDocumentParser` | `HTMLParser` | `__init__, _generate_id, _create_rich_text_span, _flush_current_text, handle_starttag, handle_endtag ...` |
| `engines/document/parsers/html_parser.py` | `HtmlParser` | `BaseDocumentParser` | `__init__, parse, parse_stream, get_supported_media_types, get_supported_extensions, _extract_math_from_html` |
| `engines/document/parsers/json_parser.py` | `JsonDocumentParser` | `BaseDocumentParser` | `__init__, parse_bytes, parse_path, get_supported_media_types, get_supported_extensions` |
| `engines/document/parsers/latex_parser.py` | `LatexParser` | `BaseDocumentParser` | `__init__, parse_bytes, parse_stream, _reset_parser_state, _generate_id, _extract_title ...` |
| `engines/document/parsers/markdown_parser.py` | `MarkdownTreeProcessor` | `Treeprocessor` | `__init__, run, _generate_id, _process_node, _extract_text, _process_list ...` |
| `engines/document/parsers/markdown_parser.py` | `MarkdownExtension` | `Extension` | `extendMarkdown` |
| `engines/document/parsers/markdown_parser.py` | `MarkdownParser` | `BaseDocumentParser` | `__init__, parse_bytes, parse_stream` |
| `engines/document/parsers/pdf_parser/content_extractor.py` | `ContentType` | `Enum` | `` |
| `engines/document/parsers/pdf_parser/content_extractor.py` | `ExtractedText` | `—` | `` |
| `engines/document/parsers/pdf_parser/content_extractor.py` | `ExtractedTable` | `—` | `to_dataframe, to_csv` |
| `engines/document/parsers/pdf_parser/content_extractor.py` | `ExtractedImage` | `—` | `__post_init__, save, to_pil_image` |
| `engines/document/parsers/pdf_parser/content_extractor.py` | `ExtractedLink` | `—` | `` |
| `engines/document/parsers/pdf_parser/content_extractor.py` | `ExtractedAnnotation` | `—` | `` |
| `engines/document/parsers/pdf_parser/content_extractor.py` | `ContentExtractionStats` | `—` | `to_dict` |
| `engines/document/parsers/pdf_parser/content_extractor.py` | `ContentExtractor` | `—` | `__init__, _setup_ocr, extract_all, extract_text, _extract_text_direct, _extract_text_with_ocr ...` |
| `engines/document/parsers/pdf_parser/font_handler.py` | `FontType` | `Enum` | `` |
| `engines/document/parsers/pdf_parser/font_handler.py` | `FontEncoding` | `Enum` | `` |
| `engines/document/parsers/pdf_parser/font_handler.py` | `FontLanguage` | `Enum` | `` |
| `engines/document/parsers/pdf_parser/font_handler.py` | `FontDescriptor` | `—` | `` |
| `engines/document/parsers/pdf_parser/font_handler.py` | `FontInfo` | `—` | `` |
| `engines/document/parsers/pdf_parser/font_handler.py` | `FontAnalysisResult` | `—` | `` |
| `engines/document/parsers/pdf_parser/font_handler.py` | `FontHandler` | `—` | `__init__, _init_farsi_mappings, extract_fonts_from_pdf, _extract_fonts_from_page, _parse_font_object, _parse_font_descriptor ...` |
| `engines/document/parsers/pdf_parser/layout_analyzer.py` | `LayoutBlock` | `—` | `` |
| `engines/document/parsers/pdf_parser/layout_analyzer.py` | `PageLayout` | `—` | `` |
| `engines/document/parsers/pdf_parser/layout_analyzer.py` | `LayoutAnalyzer` | `—` | `__init__, analyze_page, _extract_blocks, _classify_blocks, _detect_columns, _detect_regions ...` |
| `engines/document/parsers/pdf_parser/metadata_extractor.py` | `MetadataType` | `Enum` | `` |
| `engines/document/parsers/pdf_parser/metadata_extractor.py` | `PDFVersion` | `Enum` | `` |
| `engines/document/parsers/pdf_parser/metadata_extractor.py` | `PDFConformance` | `Enum` | `` |
| `engines/document/parsers/pdf_parser/metadata_extractor.py` | `PDFMetadata` | `—` | `to_dict, to_json, get_summary` |
| `engines/document/parsers/pdf_parser/metadata_extractor.py` | `PDFMetadataExtractor` | `—` | `__init__, extract_all, _extract_basic_metadata, _extract_with_pypdf2, _extract_with_pikepdf, _extract_with_pdfplumber ...` |
| `engines/document/parsers/pdf_parser/metadata_extractor.py` | `PDFMetadataError` | `Exception` | `` |
| `engines/document/parsers/pdf_parser/metadata_extractor.py` | `MetadataExtractor` | `—` | `extract_from_file, extract_from_bytes, extract_summary, validate_pdf, compare_metadata` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFObjectType` | `Enum` | `` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFColorSpace` | `Enum` | `` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFLineCapStyle` | `Enum` | `` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFLineJoinStyle` | `Enum` | `` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFTextRenderingMode` | `Enum` | `` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFError` | `Exception` | `` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFParseError` | `PDFError` | `` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFValidationError` | `PDFError` | `` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFObject` | `ABC` | `to_pdf, get_type, to_dict, __str__` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFBoolean` | `PDFObject` | `to_pdf, get_type, to_dict, __str__` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFInteger` | `PDFObject` | `to_pdf, get_type, to_dict, __str__` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFReal` | `PDFObject` | `to_pdf, get_type, to_dict, __str__` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFString` | `PDFObject` | `to_pdf, get_type, to_dict, __str__` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFName` | `PDFObject` | `to_pdf, get_type, to_dict, __str__` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFArray` | `PDFObject` | `to_pdf, get_type, to_dict, append, extend, __getitem__ ...` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFDictionary` | `PDFObject` | `to_pdf, get_type, to_dict, get, set, has_key ...` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFStream` | `PDFObject` | `to_pdf, get_type, to_dict, get_decoded_data, _decode_ascii_hex, _decode_ascii85 ...` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFNull` | `PDFObject` | `to_pdf, get_type, to_dict, __str__` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFReference` | `PDFObject` | `to_pdf, get_type, to_dict, __str__` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFIndirectObject` | `—` | `to_pdf, to_dict, __str__` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFXRefEntry` | `—` | `to_pdf, __str__` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFXRefTable` | `—` | `add_entry, to_pdf, _generate_subsections, __str__` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFTrailer` | `—` | `to_pdf, __str__` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFPage` | `PDFObject` | `to_pdf, get_type, to_dict, __str__` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFCatalog` | `PDFObject` | `to_pdf, get_type, to_dict, __str__` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFInfo` | `PDFObject` | `to_pdf, get_type, to_dict, _format_pdf_date, __str__` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFObjectFactory` | `—` | `create_from_value, parse_pdf_string` |
| `engines/document/parsers/pdf_parser/pdf_objects.py` | `PDFObjectSerializer` | `—` | `serialize, deserialize` |
| `engines/document/parsers/pdf_parser/structure_parser.py` | `StructuralElementType` | `Enum` | `` |
| `engines/document/parsers/pdf_parser/structure_parser.py` | `StructuralElement` | `—` | `` |
| `engines/document/parsers/pdf_parser/structure_parser.py` | `DocumentStructure` | `—` | `` |
| `engines/document/parsers/pdf_parser/structure_parser.py` | `StructureParser` | `—` | `__init__, parse_structure, _extract_toc, _analyze_page_structure, _extract_block_text, _extract_font_sizes ...` |
| `engines/document/parsers/pdf_parser/utils.py` | `TextDirection` | `Enum` | `` |
| `engines/document/parsers/pdf_parser/utils.py` | `Language` | `Enum` | `` |
| `engines/document/parsers/pdf_parser/utils.py` | `BoundingBox` | `—` | `width, height, area, center, intersects, contains ...` |
| `engines/document/parsers/pdf_parser/utils.py` | `TextUtils` | `—` | `detect_language, detect_text_direction, normalize_persian_text, reshape_arabic_text, calculate_text_similarity, extract_words ...` |
| `engines/document/parsers/pdf_parser/utils.py` | `ImageUtils` | `—` | `calculate_image_hash, image_to_base64, base64_to_image, resize_image, convert_image_format, extract_image_metadata` |
| `engines/document/parsers/pdf_parser/utils.py` | `FileUtils` | `—` | `safe_filename, get_file_hash, create_temp_file, read_file_chunks, get_file_info, format_file_size ...` |
| `engines/document/parsers/pdf_parser/utils.py` | `ValidationUtils` | `—` | `is_valid_pdf, is_valid_image, validate_bbox` |
| `engines/document/parsers/pdf_parser/utils.py` | `PerformanceUtils` | `—` | `timeit, memory_usage, profile_function, wrapper` |
| `engines/document/parsers/pdf_parser/utils.py` | `Logger` | `—` | `__init__, log, debug, info, warning, error` |
| `engines/document/parsers/pdf_parser.py` | `PDFParseOptions` | `—` | `` |
| `engines/document/parsers/pdf_parser.py` | `PDFParser` | `BaseParser` | `__init__, parse, _load_pdf, _merge_options, _extract_metadata, _parse_pdf_date ...` |
| `engines/document/parsers/xml_parser.py` | `XmlDocumentParser` | `BaseDocumentParser` | `__init__, parse_bytes, parse_path, _dom_to_dsdm, _handle_element_node, _handle_text_node ...` |
| `engines/document/parsers/yaml_parser.py` | `YamlDocumentParser` | `BaseDocumentParser` | `__init__, parse_bytes, parse_path, get_supported_media_types, get_supported_extensions` |
| `engines/document/storage/chunk_store.py` | `ChunkStore` | `—` | `__init__, _key, add_chunks, get_chunk, list_chunks_for_document, attach_embeddings ...` |
| `engines/document/storage/document_store.py` | `DocumentStore` | `—` | `__init__, _document_key, _chunk_key, add_document, add_chunks, get_document ...` |
| `engines/document/storage/metadata_store.py` | `MetadataStore` | `—` | `__init__, _key, put_metadata, get_metadata, delete_metadata` |
| `engines/document/utils/binary_codec.py` | `BinaryCodec` | `—` | `from_bytes, to_bytes` |
| `engines/document/utils/binary_codec.py` | `BinaryCodecAdvanced` | `—` | `encode, decode` |
| `engines/document/utils/streaming_binary_codec.py` | `StreamingBinaryCodec` | `—` | `chunk_file_to_payloads, payloads_to_file` |
| `engines/document/writers/base.py` | `WriteOptions` | `BaseModel` | `` |
| `engines/document/writers/base.py` | `BaseDocumentWriter` | `ABC` | `__init__, write_stream, write, write_to_file, get_supported_media_types, get_supported_extensions` |
| `engines/document/writers/binary_writer.py` | `BinaryWriter` | `BaseDocumentWriter` | `__init__, write_stream, write, write_to_file, _serialize_document, _determine_output_format ...` |
| `engines/document/writers/json_writer.py` | `JsonDocumentWriter` | `BaseDocumentWriter` | `__init__, write, _document_to_python, _json_default_serializer, write_to_file, get_supported_media_types ...` |
| `engines/document/writers/latex_writer.py` | `LatexWriter` | `BaseDocumentWriter` | `__init__, write, write_stream, write_to_file, get_supported_media_types, get_supported_extensions ...` |
| `engines/document/writers/pdf_writer/annotation_writer.py` | `AnnotationType` | `Enum` | `` |
| `engines/document/writers/pdf_writer/annotation_writer.py` | `AnnotationBorderStyle` | `Enum` | `` |
| `engines/document/writers/pdf_writer/annotation_writer.py` | `AnnotationFlag` | `Enum` | `` |
| `engines/document/writers/pdf_writer/annotation_writer.py` | `Annotation` | `—` | `to_dict` |
| `engines/document/writers/pdf_writer/annotation_writer.py` | `AnnotationWriter` | `—` | `__init__, _get_pdf_date, add_annotation, create_text_annotation, create_highlight_annotation, create_line_annotation ...` |
| `engines/document/writers/pdf_writer/content_writer.py` | `TextState` | `—` | `` |
| `engines/document/writers/pdf_writer/content_writer.py` | `ContentWriter` | `—` | `__init__, create_text_stream, _write_text_run, _encode_pdf_text, create_image_stream, create_vector_stream ...` |
| `engines/document/writers/pdf_writer/encryption.py` | `EncryptionAlgorithm` | `Enum` | `` |
| `engines/document/writers/pdf_writer/encryption.py` | `PermissionFlag` | `IntFlag` | `` |
| `engines/document/writers/pdf_writer/encryption.py` | `EncryptionOptions` | `—` | `__post_init__, _generate_owner_password` |
| `engines/document/writers/pdf_writer/encryption.py` | `PDFEncryptor` | `—` | `__init__, generate_encryption_key, _generate_key_revision_5, _generate_key_revision_4, _generate_key_revision_3, _generate_key_revision_2 ...` |
| `engines/document/writers/pdf_writer/encryption.py` | `PDFSecurityHandler` | `—` | `create_encryptor, generate_file_id, check_password_strength, get_supported_algorithms` |
| `engines/document/writers/pdf_writer/font_manager.py` | `FontStyle` | `Enum` | `` |
| `engines/document/writers/pdf_writer/font_manager.py` | `FontEncoding` | `Enum` | `` |
| `engines/document/writers/pdf_writer/font_manager.py` | `FontSubsetStrategy` | `Enum` | `` |
| `engines/document/writers/pdf_writer/font_manager.py` | `FontMetrics` | `—` | `` |
| `engines/document/writers/pdf_writer/font_manager.py` | `FontInfo` | `—` | `__post_init__, _extract_metrics_from_ttf, create_subset, get_font_data, get_encoding_name` |
| `engines/document/writers/pdf_writer/font_manager.py` | `FontManager` | `—` | `__init__, _get_default_font_directories, _register_standard_fonts, register_font_file, register_font_data, _extract_font_name ...` |
| `engines/document/writers/pdf_writer/layout_builder.py` | `PageLayout` | `—` | `content_width, content_height, column_width` |
| `engines/document/writers/pdf_writer/layout_builder.py` | `LayoutBuilder` | `—` | `__init__, create_page_layouts, _get_page_size, _estimate_content_volume, create_pdf_pages, calculate_text_position ...` |
| `engines/document/writers/pdf_writer/metadata_writer.py` | `XMPMetadata` | `—` | `` |
| `engines/document/writers/pdf_writer/metadata_writer.py` | `MetadataWriter` | `—` | `__init__, create_pdf_metadata, create_xmp_metadata, _get_title, _get_author, _get_subject ...` |
| `engines/document/writers/pdf_writer/optimizer.py` | `OptimizationLevel` | `Enum` | `` |
| `engines/document/writers/pdf_writer/optimizer.py` | `OptimizationOptions` | `—` | `` |
| `engines/document/writers/pdf_writer/optimizer.py` | `PDFOptimizer` | `—` | `__init__, optimize, _parse_pdf_structure, _apply_optimizations, _compress_streams, _optimize_images ...` |
| `engines/document/writers/pdf_writer/outline_builder.py` | `OutlineStyle` | `Enum` | `` |
| `engines/document/writers/pdf_writer/outline_builder.py` | `OutlineItem` | `—` | `to_dict` |
| `engines/document/writers/pdf_writer/outline_builder.py` | `OutlineBuilder` | `—` | `__init__, add_item, build_from_toc, _build_recursive, generate_outline_objects, _flatten_items ...` |
| `engines/document/writers/pdf_writer/pdf_objects.py` | `PDFObject` | `—` | `to_bytes, get_reference` |
| `engines/document/writers/pdf_writer/pdf_objects.py` | `PDFDictionary` | `PDFObject` | `to_bytes` |
| `engines/document/writers/pdf_writer/pdf_objects.py` | `PDFStream` | `PDFObject` | `to_bytes` |
| `engines/document/writers/pdf_writer/pdf_objects.py` | `PDFPage` | `PDFObject` | `to_bytes` |
| `engines/document/writers/pdf_writer/pdf_objects.py` | `PDFCatalog` | `PDFObject` | `to_bytes` |
| `engines/document/writers/pdf_writer/pdf_objects.py` | `PDFInfo` | `PDFObject` | `to_bytes, _format_pdf_date` |
| `engines/document/writers/pdf_writer/pdf_objects.py` | `PDFXRefEntry` | `—` | `to_bytes` |
| `engines/document/writers/pdf_writer/pdf_objects.py` | `PDFTrailer` | `—` | `to_bytes` |
| `engines/document/writers/pdf_writer/pdf_objects.py` | `PDFObjectFactory` | `—` | `__init__, create_dictionary, create_stream, create_page, create_catalog, create_info ...` |
| `engines/document/writers/pdf_writer/pdf_objects.py` | `PDFWriter` | `—` | `__init__, add_page, add_text, build_pdf, save` |
| `engines/document/writers/pdf_writer/utils.py` | `ColorConverter` | `—` | `hex_to_rgb, rgb_to_hex, cmyk_to_rgb, rgb_to_cmyk, parse_color` |
| `engines/document/writers/pdf_writer/utils.py` | `UnitConverter` | `—` | `to_points, from_points, convert, parse_measurement, normalize_measurement` |
| `engines/document/writers/pdf_writer/utils.py` | `ImageProcessor` | `—` | `__init__, process_image, _resize_image, extract_image_info, convert_to_base64, create_thumbnail` |
| `engines/document/writers/pdf_writer/utils.py` | `PDFColor` | `—` | `from_hex, from_rgb, from_cmyk, to_pdf_rgb, to_pdf_cmyk, to_pdf_gray ...` |
| `engines/document/writers/pdf_writer.py` | `PDFWriteOptions` | `WriteOptions` | `` |
| `engines/document/writers/pdf_writer.py` | `PDFWriter` | `BaseDocumentWriter` | `__init__, write_stream, write, write_to_file, get_supported_media_types, get_supported_extensions ...` |
| `engines/document/writers/xml_writer.py` | `XmlDocumentWriter` | `BaseDocumentWriter` | `__init__, write, write_to_file, _document_to_xml_string, _dsdm_to_element, _handle_xml_element ...` |
| `engines/document/writers/yaml_writer.py` | `YamlDocumentWriter` | `BaseDocumentWriter` | `__init__, write, _document_to_python, write_to_file, get_supported_media_types, get_supported_extensions ...` |
| `engines/document/writers/yaml_writer.py` | `CustomDumper` | `yaml.SafeDumper` | `datetime_representer, date_representer, bytes_representer, decimal_representer, datavalue_representer, datanode_representer` |
| `engines/interaction/backends/autogen_backend.py` | `AutoGenOrchestrationBackend` | `BaseOrchestrationBackend` | `__init__, _autogen_available, is_available, execute, _execute_with_autogen_group_chat` |
| `engines/interaction/backends/base_backend.py` | `BaseOrchestrationBackend` | `ABC` | `execute` |
| `engines/interaction/backends/native_backend.py` | `NativeOrchestrationBackend` | `BaseOrchestrationBackend` | `__init__, _build_strategy, execute` |
| `engines/interaction/base_strategy.py` | `InteractionStrategy` | `—` | `__init__, execute, _emit, _build_input, _run_agent` |
| `engines/interaction/broadcast_strategy.py` | `BroadcastStrategy` | `InteractionStrategy` | `execute, _execute_agent, _normalize_gather_results, _aggregate_outputs` |
| `engines/interaction/coordinator_strategy.py` | `CoordinatorStrategy` | `InteractionStrategy` | `__init__, execute, _run_validation, _aggregate, _publish_turn_message` |
| `engines/interaction/debate_strategy.py` | `DebateStrategy` | `InteractionStrategy` | `execute` |
| `engines/interaction/ensemble_strategy.py` | `EnsembleStrategy` | `InteractionStrategy` | `__init__, execute, _aggregate_votes, _publish_vote, _normalize_output` |
| `engines/interaction/group_chat_strategy.py` | `GroupChatStrategy` | `InteractionStrategy` | `__init__, execute, _init_messages, _resolve_participants, _extract_message, _extract_context_update ...` |
| `engines/interaction/interaction_models.py` | `InteractionRequest` | `BaseModel` | `` |
| `engines/interaction/interaction_models.py` | `InteractionResult` | `BaseModel` | `` |
| `engines/interaction/interaction_models.py` | `AgentMessage` | `BaseModel` | `` |
| `engines/interaction/round_robin_strategy.py` | `RoundRobinStrategy` | `InteractionStrategy` | `__init__, execute` |
| `engines/interaction/self_refine_strategy.py` | `SelfRefineStrategy` | `InteractionStrategy` | `execute, _extract_score` |
| `engines/interaction/strategy_registry.py` | `InteractionStrategyRegistry` | `Generic[TStrategy]` | `__init__, register, unregister, get, require, list_scenarios ...` |
| `engines/rag/agentic/agent_v2.py` | `RetrievalAgentV2` | `—` | `__init__, run` |
| `engines/rag/agentic/evidence_tracker.py` | `EvidenceTracker` | `—` | `__init__, add, needs_more` |
| `engines/rag/agentic/multihop_reasoner.py` | `MultiHopReasoner` | `—` | `__init__, generate_followup` |
| `engines/rag/agentic/query_decomposer.py` | `QueryDecomposer` | `—` | `__init__, decompose` |
| `engines/rag/agentic/retrieval_agent.py` | `RetrievalAgent` | `—` | `__init__, run` |
| `engines/rag/agentic/uncertainty.py` | `UncertaintyEstimator` | `—` | `__init__, score` |
| `engines/rag/compression/base.py` | `BaseCompressor` | `—` | `compress` |
| `engines/rag/compression/embedding_compressor.py` | `EmbeddingCompressor` | `BaseCompressor` | `__init__, compress` |
| `engines/rag/compression/llm_compressor.py` | `LLMCompressor` | `BaseCompressor` | `__init__, compress` |
| `engines/rag/evidence/evidence_clusterer.py` | `EvidenceClusterer` | `—` | `__init__, cluster` |
| `engines/rag/explain/retrieval_explainer.py` | `RetrievalExplainer` | `—` | `__init__, explain` |
| `engines/rag/graph/graph_builder.py` | `GraphBuilder` | `—` | `__init__, extract` |
| `engines/rag/graph/graph_models.py` | `GraphNode` | `BaseModel` | `` |
| `engines/rag/graph/graph_models.py` | `GraphEdge` | `BaseModel` | `` |
| `engines/rag/graph/graph_retriever.py` | `GraphRetriever` | `—` | `__init__, retrieve, search` |
| `engines/rag/graph/graph_store.py` | `MemoryGraphStore` | `—` | `__init__, add_node, add_edge, neighbors` |
| `engines/rag/learning/retrieval_policy.py` | `RetrievalPolicy` | `—` | `__init__, get_state, select, update` |
| `engines/rag/llm/base_llm.py` | `BaseLLM` | `ABC` | `ainvoke, astream` |
| `engines/rag/llm/llm_protocols.py` | `AsyncLLM` | `Protocol` | `ainvoke, astream` |
| `engines/rag/llm/ollama_llm.py` | `OllamaLLM` | `BaseLLM` | `__init__, ainvoke, _stream_impl, astream` |
| `engines/rag/llm/openai_llm.py` | `OpenAILLM` | `BaseLLM` | `__init__, ainvoke, _stream_impl, astream` |
| `engines/rag/planner/adaptive_planner.py` | `AdaptiveRetrievalPlanner` | `—` | `__init__, plan` |
| `engines/rag/planner/retrieval_plan.py` | `RetrievalPlan` | `BaseModel` | `` |
| `engines/rag/rag_models.py` | `Document` | `BaseModel` | `` |
| `engines/rag/rag_models.py` | `DocumentChunk` | `BaseModel` | `` |
| `engines/rag/rag_models.py` | `RetrievedDocument` | `BaseModel` | `` |
| `engines/rag/reflection/reflection_critic.py` | `RetrievalCritic` | `—` | `__init__, evaluate` |
| `engines/rag/reflection/reflection_loop.py` | `ReflectionLoop` | `—` | `__init__, improve_query, run` |
| `engines/rag/reranking/base_reranker.py` | `BaseReranker` | `ABC` | `rerank` |
| `engines/rag/reranking/reranker.py` | `Reranker` | `BaseReranker` | `rerank, _tokenize` |
| `engines/rag/research/answer_planner.py` | `LLMProtocol` | `Protocol` | `complete` |
| `engines/rag/research/answer_planner.py` | `LLMGenerateProtocol` | `Protocol` | `generate` |
| `engines/rag/research/answer_planner.py` | `LLMInvokeProtocol` | `Protocol` | `ainvoke` |
| `engines/rag/research/answer_planner.py` | `AnswerPlanner` | `—` | `__init__, create_plan, _llm_plan, _fallback_plan, _complete, _evidence_to_text` |
| `engines/rag/research/autonomous/coverage_scorer.py` | `EvidenceCoverageScorer` | `—` | `__init__, score, _complete, _to_text` |
| `engines/rag/research/autonomous/gap_detector.py` | `GapDetector` | `—` | `__init__, detect_gaps, _heuristic_gaps, _complete, _to_text` |
| `engines/rag/research/autonomous/query_generator.py` | `FollowUpQueryGenerator` | `—` | `__init__, generate, _complete, _heuristic_query` |
| `engines/rag/research/autonomous/research_loop.py` | `AutonomousResearchLoop` | `—` | `__init__, run` |
| `engines/rag/research/base_research_agent.py` | `BaseResearchAgent` | `ABC` | `run` |
| `engines/rag/research/citation_manager.py` | `Citation` | `—` | `` |
| `engines/rag/research/citation_manager.py` | `CitationManager` | `—` | `__init__, reset, register_source, build_reference_list` |
| `engines/rag/research/dashboard/schema.py` | `TokenUsage` | `BaseModel` | `` |
| `engines/rag/research/dashboard/schema.py` | `TokenBreakdownResponse` | `BaseModel` | `` |
| `engines/rag/research/dashboard/schema.py` | `RetrievalChunkStat` | `BaseModel` | `` |
| `engines/rag/research/dashboard/schema.py` | `RetrievalHeatmapResponse` | `BaseModel` | `` |
| `engines/rag/research/dashboard/schema.py` | `GraphPath` | `BaseModel` | `` |
| `engines/rag/research/dashboard/schema.py` | `GraphPathsResponse` | `BaseModel` | `` |
| `engines/rag/research/dashboard/schema.py` | `FailureEvent` | `BaseModel` | `` |
| `engines/rag/research/dashboard/schema.py` | `FailureResponse` | `BaseModel` | `` |
| `engines/rag/research/dashboard/schema.py` | `MemoryUsageResponse` | `BaseModel` | `` |
| `engines/rag/research/dashboard/schema.py` | `TelemetryEventResponse` | `BaseModel` | `` |
| `engines/rag/research/dashboard/websocket_stream.py` | `WebSocketStream` | `—` | `__init__, connect, disconnect, snapshot, stream_client` |
| `engines/rag/research/evaluation/citation_evaluator.py` | `CitationEvaluator` | `—` | `__init__, evaluate` |
| `engines/rag/research/evaluation/completeness_evaluator.py` | `CompletenessEvaluator` | `—` | `__init__, evaluate` |
| `engines/rag/research/evaluation/coverage_scorer.py` | `CoverageScorer` | `—` | `score` |
| `engines/rag/research/evaluation/evaluation_controller.py` | `EvaluationController` | `—` | `__init__, evaluate` |
| `engines/rag/research/evaluation/hallucination_detector.py` | `HallucinationDetector` | `—` | `__init__, detect` |
| `engines/rag/research/evaluation/improvement_engine.py` | `ImprovementEngine` | `—` | `suggest` |
| `engines/rag/research/evaluation/reasoning_evaluator.py` | `ReasoningEvaluator` | `—` | `__init__, evaluate` |
| `engines/rag/research/evaluation/retrieval_evaluator.py` | `RetrievalEvaluator` | `—` | `__init__, evaluate` |
| `engines/rag/research/evaluation/schema.py` | `Evidence` | `BaseModel` | `` |
| `engines/rag/research/evaluation/schema.py` | `ResearchAnswer` | `BaseModel` | `` |
| `engines/rag/research/evaluation/schema.py` | `EvaluationResult` | `BaseModel` | `` |
| `engines/rag/research/graph/entity_extractor.py` | `Entity` | `—` | `` |
| `engines/rag/research/graph/entity_extractor.py` | `EntityExtractor` | `—` | `__init__, extract, _llm_extract, _heuristic_extract, _deduplicate, _complete` |
| `engines/rag/research/graph/graph_aware_planner.py` | `GraphAwareAnswerPlanner` | `—` | `create_plan` |
| `engines/rag/research/graph/graph_canonicalizer.py` | `GraphCanonicalizer` | `—` | `canonicalize, normalize_entity` |
| `engines/rag/research/graph/graph_index.py` | `GraphNode` | `—` | `` |
| `engines/rag/research/graph/graph_index.py` | `GraphEdge` | `—` | `` |
| `engines/rag/research/graph/graph_index.py` | `GraphIndex` | `—` | `__init__, add_entities, add_relation, get_neighbors` |
| `engines/rag/research/graph/graph_persistence.py` | `GraphPersistence` | `—` | `__init__, _init_schema, save_node, save_edge` |
| `engines/rag/research/graph/graph_traverser.py` | `GraphTraverser` | `—` | `__init__, find_connections` |
| `engines/rag/research/graph/relation_builder.py` | `CandidateRelation` | `—` | `` |
| `engines/rag/research/graph/relation_builder.py` | `RelationBuilder` | `—` | `__init__, build_relations, _llm_relations, _pattern_relations, _cooccurrence_relations, _deduplicate ...` |
| `engines/rag/research/graph/relation_ranker.py` | `RelationRankingEngine` | `—` | `__init__, rank` |
| `engines/rag/research/guardrails/hallucination_guard.py` | `HallucinationGuard` | `—` | `__init__, enable_strict_mode, disable` |
| `engines/rag/research/improvement/feedback_controller.py` | `FeedbackController` | `—` | `__init__, apply_feedback` |
| `engines/rag/research/memory/memory_controller.py` | `MemoryController` | `—` | `__init__, record, recall, reasoning_trace, stats` |
| `engines/rag/research/memory/memory_retriever.py` | `MemoryRetriever` | `—` | `__init__, retrieve_similar, _token_overlap, _recency_weight` |
| `engines/rag/research/memory/memory_store.py` | `MemoryItem` | `—` | `` |
| `engines/rag/research/memory/memory_store.py` | `MemoryStore` | `—` | `__init__, add, all` |
| `engines/rag/research/memory/reasoning/event_types.py` | `ReasoningEventType` | `str, Enum` | `` |
| `engines/rag/research/memory/reasoning/reasoning_event.py` | `ReasoningEvent` | `—` | `to_dict` |
| `engines/rag/research/memory/reasoning/reasoning_exporter.py` | `ReasoningExporter` | `—` | `to_json, summary, walk` |
| `engines/rag/research/memory/reasoning/reasoning_memory.py` | `ReasoningLevel` | `str, Enum` | `` |
| `engines/rag/research/memory/reasoning/reasoning_memory.py` | `ReasoningPhase` | `str, Enum` | `` |
| `engines/rag/research/memory/reasoning/reasoning_memory.py` | `ReasoningMemory` | `—` | `__init__, start_session, end_session, start_group, end_group, log ...` |
| `engines/rag/research/memory/reasoning/reasoning_node.py` | `ReasoningNode` | `—` | `__init__, add_event, add_child, finish, mark_failed, to_dict` |
| `engines/rag/research/memory/reasoning/reasoning_recorder.py` | `ReasoningRecorder` | `—` | `__init__, start, end, rollback, event, export` |
| `engines/rag/research/memory/reasoning/reasoning_tree.py` | `ReasoningTree` | `—` | `__init__, start_group, end_group, rollback_group, to_dict` |
| `engines/rag/research/memory/reasoning_memory.py` | `ReasoningStep` | `—` | `__init__, to_dict` |
| `engines/rag/research/memory/reasoning_memory.py` | `ReasoningMemory` | `—` | `__init__, log, start_group, end_group, dump, summary ...` |
| `engines/rag/research/memory/temporal_graph.py` | `TemporalGraph` | `—` | `__init__, add_entity, add_relation, recent_relations` |
| `engines/rag/research/observability/failure_analyzer.py` | `FailureAnalyzer` | `—` | `__init__, record, recent` |
| `engines/rag/research/observability/graph_visualizer.py` | `GraphVisualizer` | `—` | `__init__, record_path, get_paths` |
| `engines/rag/research/observability/memory_usage_tracker.py` | `MemoryUsageTracker` | `—` | `current` |
| `engines/rag/research/observability/metrics_store.py` | `MetricsStore` | `—` | `__init__, snapshot` |
| `engines/rag/research/observability/observability_controller.py` | `ObservabilityController` | `—` | `__init__, track_research_session` |
| `engines/rag/research/observability/retrieval_heatmap.py` | `RetrievalHeatmap` | `—` | `__init__, record, top_chunks` |
| `engines/rag/research/observability/telemetry.py` | `TelemetryEvent` | `ABC` | `__init__, to_dict` |
| `engines/rag/research/observability/telemetry.py` | `Telemetry` | `ABC` | `__init__, emit` |
| `engines/rag/research/observability/token_tracker.py` | `TokenTracker` | `—` | `__init__, record, total, breakdown` |
| `engines/rag/research/observability/trace_collector.py` | `TraceCollector` | `—` | `__init__, collect, extend, get_recent, clear` |
| `engines/rag/research/research_agent.py` | `ResearchAgent` | `BaseResearchAgent` | `__init__, run, _compose_report, _to_evidence_item` |
| `engines/rag/research/summarization/base_summarizer.py` | `BaseSummarizer` | `ABC` | `summarize` |
| `engines/rag/research/summarization/research_summarizer.py` | `ResearchSummarizer` | `BaseSummarizer` | `__init__, summarize, build_prompt, enforce_citations, _fallback_summary` |
| `engines/rag/research/summarization/section_summarizer.py` | `SectionSummarizer` | `BaseSummarizer` | `__init__, summarize, _select_supporting_evidence` |
| `engines/rag/retrieval/base_retriever.py` | `BaseRetriever` | `ABC` | `search` |
| `engines/rag/retrieval/bm25_retriever.py` | `BM25KeywordRetriever` | `BaseRetriever` | `__init__, invalidate, _ensure_index, search, _tokenize` |
| `engines/rag/retrieval/hybrid_retriever.py` | `HybridRetriever` | `BaseRetriever` | `__init__, _rrf_merge, search` |
| `engines/rag/retrieval/hybrid_retriever_plus.py` | `HybridRetrieverPlus` | `BaseRetriever` | `__init__, _analyze_query, _semantic_keywords, _dynamic_rrf_from_llm, _normalize_scores, _cross_filter ...` |
| `engines/rag/retrieval/hybrid_retriever_super.py` | `FusionMLP` | `—` | `__init__, predict` |
| `engines/rag/retrieval/hybrid_retriever_super.py` | `HybridRetrieverSuper` | `BaseRetriever` | `__init__, attach_feedback_buffer, attach_trainer, collect_feedback, train_from_feedback, _normalize ...` |
| `engines/rag/retrieval/keyword_retriever.py` | `KeywordRetriever` | `BaseRetriever` | `__init__, search` |
| `engines/rag/retrieval/retrieval_feedback_buffer.py` | `RetrievalFeedbackBuffer` | `—` | `__init__, add, sample, __len__, get_all, clear` |
| `engines/rag/retrieval/retriever_result.py` | `RetrievalResult` | `—` | `` |
| `engines/rag/retrieval/retriever_trainer.py` | `RetrieverTrainer` | `—` | `__init__, train_step` |
| `engines/rag/retrieval/topk_optimizer.py` | `TopKOptimizer` | `—` | `__init__, choose, update` |
| `engines/rag/retrieval/vector_retriever.py` | `VectorRetriever` | `BaseRetriever` | `__init__, search, _result_to_chunk` |
| `engines/rag/retrieval/weight_manager.py` | `WeightManager` | `—` | `__init__, get, update, all` |
| `engines/rag/services/chunking.py` | `Chunker` | `—` | `__init__, create_chunks, _split_text` |
| `engines/rag/services/embedding.py` | `EmbeddingModel` | `—` | `__init__, embed, embed_one, _fallback_embed, _tokenize, _coerce_vector` |
| `engines/rag/services/query_rewriter.py` | `QueryRewriter` | `—` | `__init__, rewrite` |
| `engines/rag/trainer/base_trainer.py` | `BaseTrainer` | `ABC` | `train` |
| `engines/rag/trainer/fusion_trainer.py` | `FusionTrainer` | `BaseTrainer` | `__init__, ensure_optimizer, train_epoch, train` |
| `engines/rag/trainer/reranker_trainer.py` | `RerankerTrainer` | `BaseTrainer` | `__init__, train_step` |
| `engines/rag/vector_service.py` | `QueryResult` | `BaseModel` | `` |
| `engines/rag/vector_service.py` | `VectorService` | `—` | `__init__, retriever, register_feedback, raw_retrieve, _retrieve_one, query ...` |
| `engines/storage/base_storage.py` | `BaseStorage` | `ABC` | `__init__, is_connected, connect, disconnect, health, ensure_connected ...` |
| `engines/storage/cache/backends/memory_adapter.py` | `InMemoryCacheStorage` | `CacheStorage` | `__init__, connect, disconnect, health, _purge_expired, set ...` |
| `engines/storage/cache/backends/redis_adapter.py` | `RedisCacheStorage` | `CacheStorage` | `__init__, _key, connect, disconnect, health, set ...` |
| `engines/storage/cache/base.py` | `CacheStorage` | `BaseStorage, ABC` | `set, get, delete, exists, list_keys, invalidate ...` |
| `engines/storage/event_log/backends/rsyslog.py` | `RSyslogStorage` | `LogStorage` | `__init__, connect, disconnect, health, _send, log_agent_execution ...` |
| `engines/storage/event_log/backends/sql_event_log.py` | `SqlLogStorage` | `LogStorage` | `__init__, connect, disconnect, health, log_agent_execution, list_agent_logs ...` |
| `engines/storage/event_log/base.py` | `LogStorage` | `BaseStorage, ABC` | `log_agent_execution, list_agent_logs, get_agent_log, log_event, list_events, get_event` |
| `engines/storage/graph/backends/neo4j_adapter.py` | `Neo4jAdapter` | `GraphStorage` | `__init__, connect, disconnect, health, _run, add_node ...` |
| `engines/storage/graph/base.py` | `GraphStorage` | `BaseStorage, ABC` | `add_node, add_edge, query` |
| `engines/storage/key_value/backends/memory_adapter.py` | `InMemoryKeyValueStorage` | `KeyValueStorage` | `__init__, connect, disconnect, health, set, get ...` |
| `engines/storage/key_value/backends/redis_adapter.py` | `RedisManager` | `—` | `__init__, connect, disconnect, get_client` |
| `engines/storage/key_value/backends/redis_adapter.py` | `RedisStorageAdapter` | `KeyValueStorage` | `__init__, _get_key, connect, disconnect, health, _client ...` |
| `engines/storage/key_value/base.py` | `KeyValueStorage` | `BaseStorage, ABC` | `set, get, delete, exists, list_keys` |
| `engines/storage/object/backends/filesystem_adapter.py` | `LocalFileAdapter` | `ObjectStorage` | `__init__, connect, disconnect, health, _get_path, put ...` |
| `engines/storage/object/backends/minio_adapter.py` | `MinioAdapter` | `ObjectStorage` | `__init__, connect, disconnect, health, put, get ...` |
| `engines/storage/object/backends/s3_adapter.py` | `S3Adapter` | `ObjectStorage` | `__init__, connect, disconnect, health, put, get ...` |
| `engines/storage/object/base.py` | `ObjectStorage` | `BaseStorage, ABC` | `put, get, delete, exists, generate_url` |
| `engines/storage/relational/backends/mysql_adapter.py` | `MySQLStorageAdapter` | `PostgresStorageAdapter` | `` |
| `engines/storage/relational/backends/postgres_adapter.py` | `PostgresStorageAdapter` | `RelationalStorage` | `__init__, connect, disconnect, health, execute, fetch_one ...` |
| `engines/storage/relational/backends/sql_server_adapter.py` | `SQLServerStorageAdapter` | `PostgresStorageAdapter` | `` |
| `engines/storage/relational/backends/sqlite_adapter.py` | `SQLiteStorageAdapter` | `RelationalStorage` | `__init__, connect, disconnect, health, _normalize_params, execute ...` |
| `engines/storage/relational/base.py` | `SQLStorage` | `BaseStorage` | `__init__, connect, disconnect, health, save, load ...` |
| `engines/storage/relational/base.py` | `RelationalStorage` | `BaseStorage, ABC` | `execute, fetch_one, fetch_all` |
| `engines/storage/stream/backends/kafka_adapter.py` | `KafkaStreamAdapter` | `StreamStorage` | `__init__, connect, disconnect, health, publish, consume` |
| `engines/storage/stream/backends/redis_stream_adapter.py` | `RedisManagerStream` | `—` | `__init__, connect, disconnect, get_client` |
| `engines/storage/stream/backends/redis_stream_adapter.py` | `RedisStreamAdapter` | `StreamStorage` | `__init__, connect, disconnect, health, _client, publish ...` |
| `engines/storage/stream/base.py` | `StreamStorage` | `BaseStorage, ABC` | `publish, consume` |
| `engines/storage/timeseries/backends/influx_adapter.py` | `InfluxDBStorageAdapter` | `TimeSeriesStorage` | `__init__, connect, disconnect, health, write, query` |
| `engines/storage/timeseries/base.py` | `TimeSeriesStorage` | `BaseStorage, ABC` | `write, query` |
| `engines/storage/vector/backends/chroma_adapter.py` | `ChromaAdapter` | `VectorDBAdapter` | `__init__, _sanitize_metadata, _get_or_create_collection, create_index, upsert, batch_upsert ...` |
| `engines/storage/vector/backends/faiss_adapter.py` | `FaissAdapter` | `VectorDBAdapter` | `__init__, create_index, upsert, batch_upsert, query, delete` |
| `engines/storage/vector/backends/memory_adapter.py` | `InMemoryVectorStore` | `VectorDBAdapter` | `__init__, create_index, upsert, batch_upsert, query, delete` |
| `engines/storage/vector/backends/pinecone_adapter.py` | `PineconeAdapter` | `VectorDBAdapter` | `__init__, _initialize_connection, create_index, _require_index, upsert, batch_upsert ...` |
| `engines/storage/vector/backends/qdrant_adapter.py` | `QdrantAdapter` | `VectorDBAdapter` | `__init__, create_index, upsert, batch_upsert, query, delete` |
| `engines/storage/vector/backends/weaviate_adapter.py` | `WeaviateAdapter` | `VectorDBAdapter` | `__init__, _get_or_create_collection, create_index, upsert, batch_upsert, query ...` |
| `engines/storage/vector/base.py` | `VectorDBAdapter` | `ABC` | `create_index, upsert, batch_upsert, query, delete, search ...` |
| `engines/storage/vector/base.py` | `VectorStorage` | `BaseStorage, ABC` | `upsert, delete, query` |
| `engines/storage/vector/index_config.py` | `HNSWConfig` | `—` | `` |
| `engines/storage/vector/index_config.py` | `IVFConfig` | `—` | `` |
| `tests/agents/agents_unit/test_agent_registry.py` | `SimpleInput` | `AgentInput` | `` |
| `tests/agents/agents_unit/test_agent_registry.py` | `SimpleOutput` | `AgentOutput` | `` |
| `tests/agents/agents_unit/test_agent_registry.py` | `SimpleAgent` | `BaseAgent` | `execute` |
| `tests/agents/agents_unit/test_base_agent.py` | `InputModel` | `AgentInput` | `` |
| `tests/agents/agents_unit/test_base_agent.py` | `OutputModel` | `AgentOutput` | `` |
| `tests/agents/agents_unit/test_base_agent.py` | `EchoAgent` | `BaseAgent[InputModel, OutputModel]` | `execute` |
| `tests/agents/agents_unit/test_base_agent.py` | `FailingAgent` | `EchoAgent` | `execute` |
| `tests/agents/interaction/interaction_performance/test_interaction_agent_performance.py` | `DummyBackend` | `BaseOrchestrationBackend` | `__init__, execute, model_dump` |
| `tests/agents/interaction/interaction_performance/test_interaction_agent_performance.py` | `Result` | `InteractionResult` | `model_dump` |
| `tests/agents/interaction/interaction_performance/test_native_interaction_backend_performance.py` | `DummyOutput` | `—` | `__init__, model_dump` |
| `tests/agents/interaction/interaction_performance/test_native_interaction_backend_performance.py` | `SimpleRegistry` | `—` | `execute` |
| `tests/agents/interaction/interaction_unit/conftest.py` | `TestAgent` | `—` | `__init__, execute` |
| `tests/agents/interaction/interaction_unit/conftest.py` | `TestRegistry` | `—` | `__init__, register, execute` |
| `tests/agents/interaction/interaction_unit/conftest.py` | `DummyMessageBus1` | `MessageBus` | `__init__, publish, subscribe, unsubscribe` |
| `tests/agents/interaction/interaction_unit/test_autogen_interaction_backend.py` | `DummyRegistry1` | `—` | `execute` |
| `tests/agents/interaction/interaction_unit/test_autogen_interaction_backend.py` | `DummyMessageBus2` | `MessageBus` | `publish, subscribe, unsubscribe` |
| `tests/agents/interaction/interaction_unit/test_autogen_interaction_backend.py` | `DummyResult` | `—` | `__init__, execute` |
| `tests/agents/interaction/interaction_unit/test_autogen_interaction_backend.py` | `SimpleRequest` | `—` | `__init__` |
| `tests/agents/interaction/interaction_unit/test_interaction_agent.py` | `DummyBackend` | `BaseOrchestrationBackend` | `__init__, execute, model_dump` |
| `tests/agents/interaction/interaction_unit/test_interaction_agent.py` | `Result` | `InteractionResult` | `model_dump` |
| `tests/agents/interaction/interaction_unit/test_native_interaction_backend.py` | `DummyOutput` | `—` | `__init__, model_dump` |
| `tests/agents/interaction/interaction_unit/test_native_interaction_backend.py` | `DummyRegistry2` | `—` | `__init__, execute` |
| `tests/agents/interaction/interaction_unit/test_native_interaction_backend.py` | `DummyMessageBus` | `MessageBus` | `__init__, publish, subscribe, unsubscribe` |
| `tools/ai/analysis/chunkers/code_chunker.py` | `ChunkType` | `str, Enum` | `` |
| `tools/ai/analysis/chunkers/code_chunker.py` | `ChunkGranularity` | `str, Enum` | `` |
| `tools/ai/analysis/chunkers/code_chunker.py` | `Language` | `str, Enum` | `` |
| `tools/ai/analysis/chunkers/code_chunker.py` | `CodeChunk` | `—` | `__post_init__` |
| `tools/ai/analysis/chunkers/code_chunker.py` | `ChunkingResult` | `—` | `` |
| `tools/ai/analysis/chunkers/code_chunker.py` | `ChunkingConfig` | `—` | `` |
| `tools/ai/analysis/chunkers/code_chunker.py` | `CodeChunkVisitor` | `ast.NodeVisitor` | `__init__, visit_Module, visit_Import, visit_ImportFrom, visit_ClassDef, visit_FunctionDef ...` |
| `tools/ai/analysis/chunkers/code_chunker.py` | `CodeChunker` | `—` | `__init__, chunk_file, chunk_directory, chunk_symbols, merge_chunks, split_large_chunks ...` |
| `tools/ai/analysis/chunkers/doc_chunker.py` | `DocChunkType` | `str, Enum` | `` |
| `tools/ai/analysis/chunkers/doc_chunker.py` | `DocFormat` | `str, Enum` | `` |
| `tools/ai/analysis/chunkers/doc_chunker.py` | `DocSection` | `str, Enum` | `` |
| `tools/ai/analysis/chunkers/doc_chunker.py` | `DocChunk` | `—` | `__post_init__` |
| `tools/ai/analysis/chunkers/doc_chunker.py` | `DocStructure` | `—` | `` |
| `tools/ai/analysis/chunkers/doc_chunker.py` | `DocChunkingResult` | `—` | `` |
| `tools/ai/analysis/chunkers/doc_chunker.py` | `DocChunkingConfig` | `—` | `` |
| `tools/ai/analysis/chunkers/doc_chunker.py` | `MarkdownParser` | `—` | `__init__, parse, _parse_frontmatter, _parse_table_row, _create_chunk, _detect_sections ...` |
| `tools/ai/analysis/chunkers/doc_chunker.py` | `DocstringParser` | `—` | `__init__, parse_docstring, _parse_google_style, _section_to_chunk_type` |
| `tools/ai/analysis/chunkers/doc_chunker.py` | `DocChunker` | `—` | `__init__, chunk_file, chunk_docstring, chunk_directory, merge_chunks, _chunk_rst ...` |
| `tools/ai/analysis/chunkers/semantic_chunker.py` | `SemanticChunkType` | `str, Enum` | `` |
| `tools/ai/analysis/chunkers/semantic_chunker.py` | `ChunkingStrategy` | `str, Enum` | `` |
| `tools/ai/analysis/chunkers/semantic_chunker.py` | `SimilarityMetric` | `str, Enum` | `` |
| `tools/ai/analysis/chunkers/semantic_chunker.py` | `SemanticChunk` | `—` | `__post_init__` |
| `tools/ai/analysis/chunkers/semantic_chunker.py` | `TopicSegment` | `—` | `` |
| `tools/ai/analysis/chunkers/semantic_chunker.py` | `DiscourseMarker` | `—` | `` |
| `tools/ai/analysis/chunkers/semantic_chunker.py` | `SemanticChunkingResult` | `—` | `` |
| `tools/ai/analysis/chunkers/semantic_chunker.py` | `SemanticChunkingConfig` | `—` | `` |
| `tools/ai/analysis/chunkers/semantic_chunker.py` | `DiscourseMarkerDetector` | `—` | `__init__, detect, get_boundary_scores` |
| `tools/ai/analysis/chunkers/semantic_chunker.py` | `TopicSegmenter` | `—` | `__init__, segment, _cosine_similarity, _extract_keywords, _generate_topic_name` |
| `tools/ai/analysis/chunkers/semantic_chunker.py` | `SemanticChunker` | `—` | `__init__, chunk, chunk_documents, merge_related_chunks, _similarity_based_chunking, _llm_based_chunking ...` |
| `tools/ai/analysis/encoders/batch_encoder.py` | `BatchPriority` | `int, Enum` | `` |
| `tools/ai/analysis/encoders/batch_encoder.py` | `BatchStatus` | `str, Enum` | `` |
| `tools/ai/analysis/encoders/batch_encoder.py` | `CheckpointStrategy` | `str, Enum` | `` |
| `tools/ai/analysis/encoders/batch_encoder.py` | `BatchJob` | `—` | `__post_init__, update_progress, to_dict` |
| `tools/ai/analysis/encoders/batch_encoder.py` | `BatchConfig` | `—` | `` |
| `tools/ai/analysis/encoders/batch_encoder.py` | `JobQueue` | `—` | `__init__, put, get, peek, remove, get_job ...` |
| `tools/ai/analysis/encoders/batch_encoder.py` | `CheckpointManager` | `—` | `__init__, save_checkpoint, load_checkpoint, delete_checkpoint, list_checkpoints` |
| `tools/ai/analysis/encoders/batch_encoder.py` | `MetricsCollector` | `—` | `__init__, record_job_start, record_job_completion, record_batch, get_summary, reset` |
| `tools/ai/analysis/encoders/batch_encoder.py` | `BatchEncoder` | `—` | `__init__, _load_state, _save_state, _deserialize_job, submit, _generate_job_id ...` |
| `tools/ai/analysis/encoders/batch_encoder.py` | `RateLimiter` | `—` | `__init__, acquire, _refill` |
| `tools/ai/analysis/encoders/embedding_store.py` | `CollectionType` | `str, Enum` | `` |
| `tools/ai/analysis/encoders/embedding_store.py` | `DistanceMetric` | `str, Enum` | `` |
| `tools/ai/analysis/encoders/embedding_store.py` | `IndexType` | `str, Enum` | `` |
| `tools/ai/analysis/encoders/embedding_store.py` | `StoreConfig` | `—` | `` |
| `tools/ai/analysis/encoders/embedding_store.py` | `StoredDocument` | `—` | `__post_init__` |
| `tools/ai/analysis/encoders/embedding_store.py` | `SearchResult` | `—` | `to_dict` |
| `tools/ai/analysis/encoders/embedding_store.py` | `CollectionInfo` | `—` | `` |
| `tools/ai/analysis/encoders/embedding_store.py` | `BatchOperationResult` | `—` | `` |
| `tools/ai/analysis/encoders/embedding_store.py` | `OllamaEmbeddingFunction` | `EmbeddingFunction` | `__init__, __call__` |
| `tools/ai/analysis/encoders/embedding_store.py` | `CollectionManager` | `—` | `__init__, create_collection, get_collection, get_or_create_collection, list_collections, delete_collection ...` |
| `tools/ai/analysis/encoders/embedding_store.py` | `EmbeddingStore` | `—` | `__init__, _create_client, _initialize_default_collections, _get_collection_name, _compute_document_id, _distance_to_similarity ...` |
| `tools/ai/analysis/encoders/ollama_encoder.py` | `EmbeddingModel` | `str, Enum` | `` |
| `tools/ai/analysis/encoders/ollama_encoder.py` | `EncodingStatus` | `str, Enum` | `` |
| `tools/ai/analysis/encoders/ollama_encoder.py` | `PoolingStrategy` | `str, Enum` | `` |
| `tools/ai/analysis/encoders/ollama_encoder.py` | `EncodingRequest` | `—` | `` |
| `tools/ai/analysis/encoders/ollama_encoder.py` | `EncodingResult` | `—` | `` |
| `tools/ai/analysis/encoders/ollama_encoder.py` | `BatchEncodingResult` | `—` | `` |
| `tools/ai/analysis/encoders/ollama_encoder.py` | `ModelInfo` | `—` | `` |
| `tools/ai/analysis/encoders/ollama_encoder.py` | `EncoderConfig` | `—` | `` |
| `tools/ai/analysis/encoders/ollama_encoder.py` | `EmbeddingCache` | `—` | `__init__, _load, save, get, set, clear ...` |
| `tools/ai/analysis/encoders/ollama_encoder.py` | `OllamaClient` | `—` | `__init__, _create_session, get_available_models, embed, embed_batch, check_health ...` |
| `tools/ai/analysis/encoders/ollama_encoder.py` | `OllamaEncoder` | `—` | `__init__, _ensure_models, _get_cache, _compute_content_hash, _preprocess_text, _normalize_embedding ...` |
| `tools/ai/analysis/indexers/code_indexer.py` | `IndexStatus` | `str, Enum` | `` |
| `tools/ai/analysis/indexers/code_indexer.py` | `SymbolType` | `str, Enum` | `` |
| `tools/ai/analysis/indexers/code_indexer.py` | `IndexingConfig` | `—` | `` |
| `tools/ai/analysis/indexers/code_indexer.py` | `IndexingResult` | `—` | `` |
| `tools/ai/analysis/indexers/code_indexer.py` | `FileIndexState` | `—` | `` |
| `tools/ai/analysis/indexers/code_indexer.py` | `CodeSearchResult` | `—` | `to_dict` |
| `tools/ai/analysis/indexers/code_indexer.py` | `CodeIndexer` | `—` | `__init__, _load_state, _save_state, index, _filter_files, _index_file ...` |
| `tools/ai/analysis/indexers/doc_indexer.py` | `DocIndexStatus` | `str, Enum` | `` |
| `tools/ai/analysis/indexers/doc_indexer.py` | `DocType` | `str, Enum` | `` |
| `tools/ai/analysis/indexers/doc_indexer.py` | `DocIndexingConfig` | `—` | `` |
| `tools/ai/analysis/indexers/doc_indexer.py` | `DocIndexingResult` | `—` | `` |
| `tools/ai/analysis/indexers/doc_indexer.py` | `DocFileState` | `—` | `` |
| `tools/ai/analysis/indexers/doc_indexer.py` | `DocSearchResult` | `—` | `to_dict` |
| `tools/ai/analysis/indexers/doc_indexer.py` | `DocCollection` | `—` | `` |
| `tools/ai/analysis/indexers/doc_indexer.py` | `DocIndexer` | `—` | `__init__, _load_state, _save_state, _initialize_collections, _find_documentation_files, _should_include_file ...` |
| `tools/ai/analysis/scanners/api_surface_extractor.py` | `APIVisibility` | `str, Enum` | `` |
| `tools/ai/analysis/scanners/api_surface_extractor.py` | `APIElementType` | `str, Enum` | `` |
| `tools/ai/analysis/scanners/api_surface_extractor.py` | `DeprecationStatus` | `str, Enum` | `` |
| `tools/ai/analysis/scanners/api_surface_extractor.py` | `StabilityLevel` | `str, Enum` | `` |
| `tools/ai/analysis/scanners/api_surface_extractor.py` | `Parameter` | `—` | `` |
| `tools/ai/analysis/scanners/api_surface_extractor.py` | `APIElement` | `—` | `` |
| `tools/ai/analysis/scanners/api_surface_extractor.py` | `APIModule` | `—` | `` |
| `tools/ai/analysis/scanners/api_surface_extractor.py` | `APIPackage` | `—` | `` |
| `tools/ai/analysis/scanners/api_surface_extractor.py` | `APISurface` | `—` | `` |
| `tools/ai/analysis/scanners/api_surface_extractor.py` | `APIExtractorConfig` | `—` | `` |
| `tools/ai/analysis/scanners/api_surface_extractor.py` | `APIElementExtractor` | `ast.NodeVisitor` | `__init__, visit_Module, visit_Import, visit_ImportFrom, _is_public, _get_visibility ...` |
| `tools/ai/analysis/scanners/api_surface_extractor.py` | `APISurfaceExtractor` | `—` | `__init__, extract, _detect_project_name, _find_packages, _should_include_package, _extract_package ...` |
| `tools/ai/analysis/scanners/ast_analyzer.py` | `NodeType` | `str, Enum` | `` |
| `tools/ai/analysis/scanners/ast_analyzer.py` | `ComplexityType` | `str, Enum` | `` |
| `tools/ai/analysis/scanners/ast_analyzer.py` | `CodeSmell` | `str, Enum` | `` |
| `tools/ai/analysis/scanners/ast_analyzer.py` | `ASTMetrics` | `—` | `` |
| `tools/ai/analysis/scanners/ast_analyzer.py` | `ASTAnalysisResult` | `—` | `` |
| `tools/ai/analysis/scanners/ast_analyzer.py` | `ASTAnalyzerConfig` | `—` | `` |
| `tools/ai/analysis/scanners/ast_analyzer.py` | `MetricsVisitor` | `ast.NodeVisitor` | `__init__, _create_metrics, _push_metrics, _pop_metrics, _compute_lines_of_code, _count_comments ...` |
| `tools/ai/analysis/scanners/ast_analyzer.py` | `ImportExtractor` | `ast.NodeVisitor` | `__init__, visit_Import, visit_ImportFrom, visit_Assign` |
| `tools/ai/analysis/scanners/ast_analyzer.py` | `ASTAnalyzer` | `—` | `__init__, analyze_file, analyze_directory, _get_module_name, _compute_complexity_score, _compute_maintainability_score ...` |
| `tools/ai/analysis/scanners/import_graph.py` | `ImportType` | `str, Enum` | `` |
| `tools/ai/analysis/scanners/import_graph.py` | `DependencyType` | `str, Enum` | `` |
| `tools/ai/analysis/scanners/import_graph.py` | `GraphFormat` | `str, Enum` | `` |
| `tools/ai/analysis/scanners/import_graph.py` | `ImportEdge` | `—` | `id` |
| `tools/ai/analysis/scanners/import_graph.py` | `ModuleNode` | `—` | `` |
| `tools/ai/analysis/scanners/import_graph.py` | `ImportGraphConfig` | `—` | `` |
| `tools/ai/analysis/scanners/import_graph.py` | `ImportGraph` | `—` | `` |
| `tools/ai/analysis/scanners/import_graph.py` | `ImportExtractor` | `ast.NodeVisitor` | `__init__, visit_Import, visit_ImportFrom, visit_If, visit_Try, visit_Call ...` |
| `tools/ai/analysis/scanners/import_graph.py` | `ImportGraphAnalyzer` | `—` | `__init__, analyze, _find_python_modules, _should_include_file, _get_module_name, _add_module_node ...` |
| `tools/ai/analysis/scanners/project_scanner.py` | `ScanLevel` | `str, Enum` | `` |
| `tools/ai/analysis/scanners/project_scanner.py` | `SymbolType` | `str, Enum` | `` |
| `tools/ai/analysis/scanners/project_scanner.py` | `FileType` | `str, Enum` | `` |
| `tools/ai/analysis/scanners/project_scanner.py` | `ProjectType` | `str, Enum` | `` |
| `tools/ai/analysis/scanners/project_scanner.py` | `ScanConfig` | `—` | `` |
| `tools/ai/analysis/scanners/project_scanner.py` | `CodeSymbol` | `—` | `__post_init__` |
| `tools/ai/analysis/scanners/project_scanner.py` | `FileInfo` | `—` | `` |
| `tools/ai/analysis/scanners/project_scanner.py` | `ModuleInfo` | `—` | `` |
| `tools/ai/analysis/scanners/project_scanner.py` | `PackageInfo` | `—` | `` |
| `tools/ai/analysis/scanners/project_scanner.py` | `DependencyInfo` | `—` | `` |
| `tools/ai/analysis/scanners/project_scanner.py` | `ProjectGraph` | `—` | `` |
| `tools/ai/analysis/scanners/project_scanner.py` | `SymbolExtractor` | `ast.NodeVisitor` | `__init__, visit_Module, visit_Import, visit_ImportFrom, visit_ClassDef, visit_FunctionDef ...` |
| `tools/ai/analysis/scanners/project_scanner.py` | `DependencyExtractor` | `ast.NodeVisitor` | `__init__, visit_Import, visit_ImportFrom, visit_Call, visit_FunctionDef, visit_AsyncFunctionDef ...` |
| `tools/ai/analysis/scanners/project_scanner.py` | `ProjectScanner` | `—` | `__init__, scan, scan_incremental, _find_files, _should_include_file, _scan_file ...` |
| `tools/ai/entry_points/api_entry.py` | `HTTPMethod` | `str, Enum` | `` |
| `tools/ai/entry_points/api_entry.py` | `APIResponseStatus` | `str, Enum` | `` |
| `tools/ai/entry_points/api_entry.py` | `AuthMethod` | `str, Enum` | `` |
| `tools/ai/entry_points/api_entry.py` | `APIResponse` | `BaseModel` | `` |
| `tools/ai/entry_points/api_entry.py` | `WorkflowRequest` | `BaseModel` | `` |
| `tools/ai/entry_points/api_entry.py` | `WorkflowResponse` | `BaseModel` | `` |
| `tools/ai/entry_points/api_entry.py` | `AnalyzeRequest` | `BaseModel` | `` |
| `tools/ai/entry_points/api_entry.py` | `GenerateRequest` | `BaseModel` | `` |
| `tools/ai/entry_points/api_entry.py` | `ValidateRequest` | `BaseModel` | `` |
| `tools/ai/entry_points/api_entry.py` | `HealthResponse` | `BaseModel` | `` |
| `tools/ai/entry_points/api_entry.py` | `APIConfig` | `EntryPointConfig` | `` |
| `tools/ai/entry_points/api_entry.py` | `APIEntryPoint` | `BaseEntryPoint` | `__init__, _get_default_config, setup, _setup_middleware, _setup_routes, _setup_authentication ...` |
| `tools/ai/entry_points/base_entry_point.py` | `EntryPointType` | `str, Enum` | `` |
| `tools/ai/entry_points/base_entry_point.py` | `ExecutionMode` | `str, Enum` | `` |
| `tools/ai/entry_points/base_entry_point.py` | `ExitCode` | `int, Enum` | `` |
| `tools/ai/entry_points/base_entry_point.py` | `EntryPointContext` | `—` | `get_duration_seconds` |
| `tools/ai/entry_points/base_entry_point.py` | `EntryPointResult` | `—` | `` |
| `tools/ai/entry_points/base_entry_point.py` | `EntryPointConfig` | `—` | `` |
| `tools/ai/entry_points/base_entry_point.py` | `SignalHandler` | `—` | `__init__, setup, _handle_signal, restore, is_shutdown_requested` |
| `tools/ai/entry_points/base_entry_point.py` | `BaseEntryPoint` | `ABC` | `__init__, _get_default_config, run, run_async, _execute_with_retry, _execute_async_with_retry ...` |
| `tools/ai/entry_points/base_entry_point.py` | `ExampleEntryPoint` | `BaseEntryPoint` | `_get_default_config, parse_arguments, execute` |
| `tools/ai/entry_points/cli_entry.py` | `OutputFormat` | `str, Enum` | `` |
| `tools/ai/entry_points/cli_entry.py` | `CLIConfig` | `EntryPointConfig` | `` |
| `tools/ai/entry_points/cli_entry.py` | `CLIEntryPoint` | `BaseEntryPoint` | `__init__, _get_default_config, _register_commands, parse_arguments, _create_main_parser, _add_subcommands ...` |
| `tools/ai/entry_points/ide_plugin_entry.py` | `ProtocolType` | `str, Enum` | `` |
| `tools/ai/entry_points/ide_plugin_entry.py` | `MessageType` | `str, Enum` | `` |
| `tools/ai/entry_points/ide_plugin_entry.py` | `CommandScope` | `str, Enum` | `` |
| `tools/ai/entry_points/ide_plugin_entry.py` | `IDEMessage` | `BaseModel` | `` |
| `tools/ai/entry_points/ide_plugin_entry.py` | `IDERequest` | `BaseModel` | `` |
| `tools/ai/entry_points/ide_plugin_entry.py` | `IDEResponse` | `BaseModel` | `` |
| `tools/ai/entry_points/ide_plugin_entry.py` | `Diagnostic` | `BaseModel` | `` |
| `tools/ai/entry_points/ide_plugin_entry.py` | `CodeAction` | `BaseModel` | `` |
| `tools/ai/entry_points/ide_plugin_entry.py` | `IDEPluginConfig` | `EntryPointConfig` | `` |
| `tools/ai/entry_points/ide_plugin_entry.py` | `IDEPluginEntryPoint` | `BaseEntryPoint` | `__init__, _get_default_config, _register_handlers, _handle_initialize, _handle_initialized, _handle_shutdown ...` |
| `tools/ai/generation/generators/class_generator.py` | `ClassType` | `str, Enum` | `` |
| `tools/ai/generation/generators/class_generator.py` | `MethodType` | `str, Enum` | `` |
| `tools/ai/generation/generators/class_generator.py` | `Visibility` | `str, Enum` | `` |
| `tools/ai/generation/generators/class_generator.py` | `FieldSpec` | `—` | `` |
| `tools/ai/generation/generators/class_generator.py` | `MethodSpec` | `—` | `` |
| `tools/ai/generation/generators/class_generator.py` | `PropertySpec` | `—` | `` |
| `tools/ai/generation/generators/class_generator.py` | `ClassSpec` | `—` | `` |
| `tools/ai/generation/generators/class_generator.py` | `GeneratedClass` | `—` | `` |
| `tools/ai/generation/generators/class_generator.py` | `ClassGeneratorConfig` | `—` | `` |
| `tools/ai/generation/generators/class_generator.py` | `ClassCodeGenerator` | `—` | `__init__, generate, _generate_imports, _generate_typing_imports, _extract_typing_types, _generate_decorators ...` |
| `tools/ai/generation/generators/class_generator.py` | `ClassGenerator` | `—` | `__init__, generate, generate_from_description, _parse_description, generate_multiple, generate_module ...` |
| `tools/ai/generation/generators/docstring_generator.py` | `DocstringStyle` | `str, Enum` | `` |
| `tools/ai/generation/generators/docstring_generator.py` | `DocstringSection` | `str, Enum` | `` |
| `tools/ai/generation/generators/docstring_generator.py` | `DocstringQuality` | `str, Enum` | `` |
| `tools/ai/generation/generators/docstring_generator.py` | `ParameterInfo` | `—` | `` |
| `tools/ai/generation/generators/docstring_generator.py` | `ReturnInfo` | `—` | `` |
| `tools/ai/generation/generators/docstring_generator.py` | `ExceptionInfo` | `—` | `` |
| `tools/ai/generation/generators/docstring_generator.py` | `FunctionContext` | `—` | `` |
| `tools/ai/generation/generators/docstring_generator.py` | `ClassContext` | `—` | `` |
| `tools/ai/generation/generators/docstring_generator.py` | `ModuleContext` | `—` | `` |
| `tools/ai/generation/generators/docstring_generator.py` | `GeneratedDocstring` | `—` | `` |
| `tools/ai/generation/generators/docstring_generator.py` | `DocstringGeneratorConfig` | `—` | `` |
| `tools/ai/generation/generators/docstring_generator.py` | `ContextExtractor` | `ast.NodeVisitor` | `__init__, extract_function_context, extract_class_context, _extract_decorators, _extract_bases, _extract_parameters ...` |
| `tools/ai/generation/generators/docstring_generator.py` | `DocstringFormatter` | `—` | `__init__, format_function, format_class, format_module, _format_google_function, _format_numpy_function ...` |
| `tools/ai/generation/generators/docstring_generator.py` | `DocstringGenerator` | `—` | `__init__, generate_for_function, generate_for_class, generate_for_module, _generate_with_llm, _generate_class_with_llm ...` |
| `tools/ai/generation/generators/function_generator.py` | `FunctionType` | `str, Enum` | `` |
| `tools/ai/generation/generators/function_generator.py` | `ReturnStrategy` | `str, Enum` | `` |
| `tools/ai/generation/generators/function_generator.py` | `ErrorHandling` | `str, Enum` | `` |
| `tools/ai/generation/generators/function_generator.py` | `Complexity` | `str, Enum` | `` |
| `tools/ai/generation/generators/function_generator.py` | `ParameterSpec` | `—` | `` |
| `tools/ai/generation/generators/function_generator.py` | `ReturnSpec` | `—` | `` |
| `tools/ai/generation/generators/function_generator.py` | `ExceptionSpec` | `—` | `` |
| `tools/ai/generation/generators/function_generator.py` | `DecoratorSpec` | `—` | `` |
| `tools/ai/generation/generators/function_generator.py` | `FunctionBodySpec` | `—` | `` |
| `tools/ai/generation/generators/function_generator.py` | `FunctionSpec` | `—` | `` |
| `tools/ai/generation/generators/function_generator.py` | `GeneratedFunction` | `—` | `` |
| `tools/ai/generation/generators/function_generator.py` | `FunctionGeneratorConfig` | `—` | `` |
| `tools/ai/generation/generators/function_generator.py` | `FunctionCodeGenerator` | `—` | `__init__, generate, _generate_imports, _generate_decorators, _generate_signature, _generate_parameters ...` |
| `tools/ai/generation/generators/function_generator.py` | `FunctionGenerator` | `—` | `__init__, generate, generate_from_description, _parse_description, _generate_test, generate_multiple ...` |
| `tools/ai/generation/generators/module_generator.py` | `ModuleType` | `str, Enum` | `` |
| `tools/ai/generation/generators/module_generator.py` | `ModuleTemplate` | `str, Enum` | `` |
| `tools/ai/generation/generators/module_generator.py` | `ConstantSpec` | `—` | `` |
| `tools/ai/generation/generators/module_generator.py` | `ImportSpec` | `—` | `` |
| `tools/ai/generation/generators/module_generator.py` | `TypeAliasSpec` | `—` | `` |
| `tools/ai/generation/generators/module_generator.py` | `ModuleSpec` | `—` | `` |
| `tools/ai/generation/generators/module_generator.py` | `GeneratedModule` | `—` | `` |
| `tools/ai/generation/generators/module_generator.py` | `ModuleGeneratorConfig` | `—` | `` |
| `tools/ai/generation/generators/module_generator.py` | `ModuleCodeGenerator` | `—` | `__init__, generate, _generate_module_docstring, _generate_imports, _get_stdlib_modules, _needs_typing_imports ...` |
| `tools/ai/generation/generators/module_generator.py` | `ModuleGenerator` | `—` | `__init__, generate, generate_from_description, _parse_description, _get_module_path, _generate_test_file ...` |
| `tools/ai/generation/generators/performance_test_generator.py` | `PerformanceTestType` | `str, Enum` | `` |
| `tools/ai/generation/generators/performance_test_generator.py` | `MetricsType` | `str, Enum` | `` |
| `tools/ai/generation/generators/performance_test_generator.py` | `LoadPattern` | `str, Enum` | `` |
| `tools/ai/generation/generators/performance_test_generator.py` | `AssertionType` | `str, Enum` | `` |
| `tools/ai/generation/generators/performance_test_generator.py` | `PerformanceMetric` | `—` | `` |
| `tools/ai/generation/generators/performance_test_generator.py` | `LoadProfile` | `—` | `` |
| `tools/ai/generation/generators/performance_test_generator.py` | `PerformanceAssertion` | `—` | `` |
| `tools/ai/generation/generators/performance_test_generator.py` | `ResourceLimit` | `—` | `` |
| `tools/ai/generation/generators/performance_test_generator.py` | `PerformanceTestSpec` | `—` | `` |
| `tools/ai/generation/generators/performance_test_generator.py` | `GeneratedPerformanceTest` | `—` | `` |
| `tools/ai/generation/generators/performance_test_generator.py` | `PerformanceTestGeneratorConfig` | `—` | `` |
| `tools/ai/generation/generators/performance_test_generator.py` | `PerformanceTestCodeGenerator` | `—` | `__init__, generate, _generate_module_docstring, _generate_imports, _generate_constants, _generate_metrics_collector ...` |
| `tools/ai/generation/generators/performance_test_generator.py` | `StressTestGenerator` | `—` | `__init__, generate_stress_test, generate_endurance_test, generate_spike_test, generate_scalability_test` |
| `tools/ai/generation/generators/performance_test_generator.py` | `PerformanceTestGenerator` | `—` | `__init__, generate, generate_from_function, generate_from_description, _parse_description, _estimate_duration ...` |
| `tools/ai/generation/generators/test_generator.py` | `TestFramework` | `str, Enum` | `` |
| `tools/ai/generation/generators/test_generator.py` | `TestType` | `str, Enum` | `` |
| `tools/ai/generation/generators/test_generator.py` | `MockStrategy` | `str, Enum` | `` |
| `tools/ai/generation/generators/test_generator.py` | `AssertionStyle` | `str, Enum` | `` |
| `tools/ai/generation/generators/test_generator.py` | `TestCase` | `—` | `` |
| `tools/ai/generation/generators/test_generator.py` | `FixtureSpec` | `—` | `` |
| `tools/ai/generation/generators/test_generator.py` | `MockSpec` | `—` | `` |
| `tools/ai/generation/generators/test_generator.py` | `TestClassSpec` | `—` | `` |
| `tools/ai/generation/generators/test_generator.py` | `TestModuleSpec` | `—` | `` |
| `tools/ai/generation/generators/test_generator.py` | `GeneratedTest` | `—` | `` |
| `tools/ai/generation/generators/test_generator.py` | `TestGeneratorConfig` | `—` | `` |
| `tools/ai/generation/generators/test_generator.py` | `TestTargetAnalyzer` | `ast.NodeVisitor` | `__init__, analyze_file, visit_Import, visit_ImportFrom, visit_ClassDef, visit_FunctionDef ...` |
| `tools/ai/generation/generators/test_generator.py` | `TestCodeGenerator` | `—` | `__init__, generate, _generate_module_docstring, _generate_imports, _generate_fixtures, _generate_test_class ...` |
| `tools/ai/generation/generators/test_generator.py` | `TestGenerator` | `—` | `__init__, generate, generate_from_file, generate_from_description, _build_spec_from_analysis, _generate_test_cases_for_function ...` |
| `tools/ai/generation/planners/contract_designer.py` | `DesignPrinciple` | `str, Enum` | `` |
| `tools/ai/generation/planners/contract_designer.py` | `ParameterKind` | `str, Enum` | `` |
| `tools/ai/generation/planners/contract_designer.py` | `ReturnStyle` | `str, Enum` | `` |
| `tools/ai/generation/planners/contract_designer.py` | `ErrorStrategy` | `str, Enum` | `` |
| `tools/ai/generation/planners/contract_designer.py` | `ParameterDesign` | `—` | `` |
| `tools/ai/generation/planners/contract_designer.py` | `ReturnDesign` | `—` | `` |
| `tools/ai/generation/planners/contract_designer.py` | `ExceptionDesign` | `—` | `` |
| `tools/ai/generation/planners/contract_designer.py` | `MethodDesign` | `—` | `` |
| `tools/ai/generation/planners/contract_designer.py` | `PropertyDesign` | `—` | `` |
| `tools/ai/generation/planners/contract_designer.py` | `ConstantDesign` | `—` | `` |
| `tools/ai/generation/planners/contract_designer.py` | `TypeAliasDesign` | `—` | `` |
| `tools/ai/generation/planners/contract_designer.py` | `ContractDesign` | `—` | `` |
| `tools/ai/generation/planners/contract_designer.py` | `ContractSignature` | `—` | `` |
| `tools/ai/generation/planners/contract_designer.py` | `ContractDesignerConfig` | `—` | `` |
| `tools/ai/generation/planners/contract_designer.py` | `ContractDesignerEngine` | `—` | `__init__, design, _apply_requirements, _enforce_principles, _has_single_responsibility, _is_explicit ...` |
| `tools/ai/generation/planners/contract_designer.py` | `SignatureGenerator` | `—` | `__init__, generate_signature, _generate_module_docstring, _generate_imports, _generate_property, _generate_method ...` |
| `tools/ai/generation/planners/contract_designer.py` | `ContractDesigner` | `—` | `__init__, design, design_from_description, design_from_existing, _enhance_with_llm, _generate_contract ...` |
| `tools/ai/generation/planners/contract_generator.py` | `ContractType` | `str, Enum` | `` |
| `tools/ai/generation/planners/contract_generator.py` | `ParameterKind` | `str, Enum` | `` |
| `tools/ai/generation/planners/contract_generator.py` | `ContractVisibility` | `str, Enum` | `` |
| `tools/ai/generation/planners/contract_generator.py` | `ErrorHandling` | `str, Enum` | `` |
| `tools/ai/generation/planners/contract_generator.py` | `ParameterSpec` | `—` | `` |
| `tools/ai/generation/planners/contract_generator.py` | `ReturnSpec` | `—` | `` |
| `tools/ai/generation/planners/contract_generator.py` | `ExceptionSpec` | `—` | `` |
| `tools/ai/generation/planners/contract_generator.py` | `MethodSpec` | `—` | `` |
| `tools/ai/generation/planners/contract_generator.py` | `PropertySpec` | `—` | `` |
| `tools/ai/generation/planners/contract_generator.py` | `FieldSpec` | `—` | `` |
| `tools/ai/generation/planners/contract_generator.py` | `TypeVarSpec` | `—` | `` |
| `tools/ai/generation/planners/contract_generator.py` | `ContractSpec` | `—` | `` |
| `tools/ai/generation/planners/contract_generator.py` | `GeneratedContract` | `—` | `` |
| `tools/ai/generation/planners/contract_generator.py` | `ContractGeneratorConfig` | `—` | `` |
| `tools/ai/generation/planners/contract_generator.py` | `ContractCodeGenerator` | `—` | `__init__, generate, _generate_module_docstring, _generate_imports, _collect_typing_imports, _generate_type_vars ...` |
| `tools/ai/generation/planners/contract_generator.py` | `ContractGenerator` | `—` | `__init__, generate, generate_from_description, _parse_description, create_service_contract, create_repository_contract ...` |
| `tools/ai/generation/planners/dependency_planner.py` | `DependencyType` | `str, Enum` | `` |
| `tools/ai/generation/planners/dependency_planner.py` | `DependencyDirection` | `str, Enum` | `` |
| `tools/ai/generation/planners/dependency_planner.py` | `LayerType` | `str, Enum` | `` |
| `tools/ai/generation/planners/dependency_planner.py` | `DependencyRule` | `str, Enum` | `` |
| `tools/ai/generation/planners/dependency_planner.py` | `ComponentSpec` | `—` | `` |
| `tools/ai/generation/planners/dependency_planner.py` | `DependencyEdge` | `—` | `` |
| `tools/ai/generation/planners/dependency_planner.py` | `LayerDefinition` | `—` | `` |
| `tools/ai/generation/planners/dependency_planner.py` | `DependencyRule_` | `—` | `` |
| `tools/ai/generation/planners/dependency_planner.py` | `ImportPlan` | `—` | `` |
| `tools/ai/generation/planners/dependency_planner.py` | `GenerationOrder` | `—` | `` |
| `tools/ai/generation/planners/dependency_planner.py` | `DependencyPlan` | `—` | `` |
| `tools/ai/generation/planners/dependency_planner.py` | `DependencyPlannerConfig` | `—` | `` |
| `tools/ai/generation/planners/dependency_planner.py` | `DependencyGraphBuilder` | `—` | `__init__, add_component, add_dependency, _determine_direction, _generate_import_statement, build ...` |
| `tools/ai/generation/planners/dependency_planner.py` | `GenerationOrderCalculator` | `—` | `__init__, calculate, _find_circular_groups, _resolve_circular, _extract_cycle, strongconnect ...` |
| `tools/ai/generation/planners/dependency_planner.py` | `ImportPlanner` | `—` | `__init__, plan_imports, _generate_import, _is_stdlib, _is_third_party` |
| `tools/ai/generation/planners/dependency_planner.py` | `RuleValidator` | `—` | `__init__, validate, _matches_pattern, _get_layer_definition` |
| `tools/ai/generation/planners/dependency_planner.py` | `DependencyPlanner` | `—` | `__init__, plan, plan_from_specs, _validate_against_existing, _check_validity, _generate_issues ...` |
| `tools/ai/generation/planners/module_architect.py` | `ModuleType` | `str, Enum` | `` |
| `tools/ai/generation/planners/module_architect.py` | `ArchitecturePattern` | `str, Enum` | `` |
| `tools/ai/generation/planners/module_architect.py` | `Visibility` | `str, Enum` | `` |
| `tools/ai/generation/planners/module_architect.py` | `ComponentRole` | `str, Enum` | `` |
| `tools/ai/generation/planners/module_architect.py` | `FileSpec` | `—` | `` |
| `tools/ai/generation/planners/module_architect.py` | `ComponentSpec` | `—` | `` |
| `tools/ai/generation/planners/module_architect.py` | `DirectorySpec` | `—` | `` |
| `tools/ai/generation/planners/module_architect.py` | `LayerSpec` | `—` | `` |
| `tools/ai/generation/planners/module_architect.py` | `ModuleArchitecture` | `—` | `` |
| `tools/ai/generation/planners/module_architect.py` | `ModuleArchitectConfig` | `—` | `` |
| `tools/ai/generation/planners/module_architect.py` | `StructurePlanner` | `—` | `__init__, plan_structure, _plan_layered, _plan_clean, _plan_hexagonal, _plan_ddd ...` |
| `tools/ai/generation/planners/module_architect.py` | `ModuleArchitect` | `—` | `__init__, design, design_from_description, design_from_existing, _design_interface_for_component, _calculate_dependencies ...` |
| `tools/ai/generation/planners/skeleton_generator.py` | `StubType` | `str, Enum` | `` |
| `tools/ai/generation/planners/skeleton_generator.py` | `ImplementationHint` | `str, Enum` | `` |
| `tools/ai/generation/planners/skeleton_generator.py` | `StubConfig` | `—` | `` |
| `tools/ai/generation/planners/skeleton_generator.py` | `ClassStub` | `—` | `` |
| `tools/ai/generation/planners/skeleton_generator.py` | `MethodStub` | `—` | `` |
| `tools/ai/generation/planners/skeleton_generator.py` | `PropertyStub` | `—` | `` |
| `tools/ai/generation/planners/skeleton_generator.py` | `ParameterStub` | `—` | `` |
| `tools/ai/generation/planners/skeleton_generator.py` | `VariableStub` | `—` | `` |
| `tools/ai/generation/planners/skeleton_generator.py` | `FunctionStub` | `—` | `` |
| `tools/ai/generation/planners/skeleton_generator.py` | `ConstantStub` | `—` | `` |
| `tools/ai/generation/planners/skeleton_generator.py` | `TypeAliasStub` | `—` | `` |
| `tools/ai/generation/planners/skeleton_generator.py` | `ImportStub` | `—` | `` |
| `tools/ai/generation/planners/skeleton_generator.py` | `ModuleStub` | `—` | `` |
| `tools/ai/generation/planners/skeleton_generator.py` | `SkeletonGenerationResult` | `—` | `` |
| `tools/ai/generation/planners/skeleton_generator.py` | `SkeletonGeneratorConfig` | `—` | `` |
| `tools/ai/generation/planners/skeleton_generator.py` | `StubCodeGenerator` | `—` | `__init__, generate_module, _generate_imports, _is_stdlib, _format_import, _generate_constant ...` |
| `tools/ai/generation/planners/skeleton_generator.py` | `SkeletonGenerator` | `—` | `__init__, generate_from_architecture, generate_from_interface, _architecture_to_stubs, _component_to_class_stub, _interface_to_stubs ...` |
| `tools/ai/generation/refiners/base_refiner.py` | `RefinementScope` | `str, Enum` | `` |
| `tools/ai/generation/refiners/base_refiner.py` | `ChangeType` | `str, Enum` | `` |
| `tools/ai/generation/refiners/base_refiner.py` | `RefinementContext` | `—` | `` |
| `tools/ai/generation/refiners/base_refiner.py` | `RefinementResult` | `—` | `` |
| `tools/ai/generation/refiners/base_refiner.py` | `BaseRefiner` | `ABC` | `__init__, refine, can_handle, get_priority` |
| `tools/ai/generation/refiners/base_refiner.py` | `SafetyCheck` | `ABC` | `check` |
| `tools/ai/generation/refiners/feedback_loop.py` | `FeedbackType` | `str, Enum` | `` |
| `tools/ai/generation/refiners/feedback_loop.py` | `FeedbackSeverity` | `str, Enum` | `` |
| `tools/ai/generation/refiners/feedback_loop.py` | `LearningMode` | `str, Enum` | `` |
| `tools/ai/generation/refiners/feedback_loop.py` | `PatternType` | `str, Enum` | `` |
| `tools/ai/generation/refiners/feedback_loop.py` | `FeedbackItem` | `—` | `__post_init__, _generate_id` |
| `tools/ai/generation/refiners/feedback_loop.py` | `LearnedPattern` | `—` | `__post_init__` |
| `tools/ai/generation/refiners/feedback_loop.py` | `FeedbackSession` | `—` | `` |
| `tools/ai/generation/refiners/feedback_loop.py` | `FeedbackLoopConfig` | `—` | `` |
| `tools/ai/generation/refiners/feedback_loop.py` | `FeedbackStorage` | `—` | `__init__, _init_database, save_feedback, get_feedback, get_feedback_by_type, get_feedback_by_pattern ...` |
| `tools/ai/generation/refiners/feedback_loop.py` | `PatternLearner` | `—` | `__init__, learn_from_feedback, _group_similar_feedback, _generate_signature, _normalize_error_message, _normalize_code_snippet ...` |
| `tools/ai/generation/refiners/feedback_loop.py` | `FeedbackLoop` | `—` | `__init__, start_session, end_session, _generate_session_id, add_feedback, add_validation_errors ...` |
| `tools/ai/generation/refiners/functionality_preserver.py` | `FunctionalitySignature` | `—` | `to_dict` |
| `tools/ai/generation/refiners/functionality_preserver.py` | `FunctionalityPreserver` | `SafetyCheck` | `__init__, check, _extract_signatures, _check_public_api, _check_exceptions, _check_side_effects ...` |
| `tools/ai/generation/refiners/functionality_preserver.py` | `SignatureVisitor` | `ast.NodeVisitor` | `visit_FunctionDef, visit_AsyncFunctionDef, visit_ClassDef, _extract_function_signature, _extract_class_signature, _extract_raises ...` |
| `tools/ai/generation/refiners/impact_analyzer.py` | `ImpactSeverity` | `str, Enum` | `` |
| `tools/ai/generation/refiners/impact_analyzer.py` | `ImpactType` | `str, Enum` | `` |
| `tools/ai/generation/refiners/impact_analyzer.py` | `ChangeCategory` | `str, Enum` | `` |
| `tools/ai/generation/refiners/impact_analyzer.py` | `ChangeInfo` | `—` | `` |
| `tools/ai/generation/refiners/impact_analyzer.py` | `ImpactedArtifact` | `—` | `` |
| `tools/ai/generation/refiners/impact_analyzer.py` | `BreakingChange` | `—` | `` |
| `tools/ai/generation/refiners/impact_analyzer.py` | `ImpactAnalysisResult` | `—` | `` |
| `tools/ai/generation/refiners/impact_analyzer.py` | `ImpactAnalyzerConfig` | `—` | `` |
| `tools/ai/generation/refiners/impact_analyzer.py` | `ChangeDetector` | `—` | `__init__, detect_changes, _detect_code_changes, _detect_line_changes, _detect_git_changes, _extract_symbols ...` |
| `tools/ai/generation/refiners/impact_analyzer.py` | `ImpactCalculator` | `—` | `__init__, calculate_impact, _build_reverse_dependency_graph, _calculate_change_impact, _file_to_module, _module_to_file ...` |
| `tools/ai/generation/refiners/impact_analyzer.py` | `ImpactAnalyzer` | `—` | `__init__, analyze, analyze_git_diff, analyze_refinement, _meets_severity_threshold, _save_analysis ...` |
| `tools/ai/generation/refiners/impact_analyzer.py` | `SymbolVisitor` | `ast.NodeVisitor` | `__init__, visit_ClassDef, visit_FunctionDef, visit_AsyncFunctionDef, _extract_function_info` |
| `tools/ai/generation/refiners/iterative_refiner.py` | `RefinementStrategy` | `str, Enum` | `` |
| `tools/ai/generation/refiners/iterative_refiner.py` | `ErrorCategory` | `str, Enum` | `` |
| `tools/ai/generation/refiners/iterative_refiner.py` | `RefinementPhase` | `str, Enum` | `` |
| `tools/ai/generation/refiners/iterative_refiner.py` | `ValidationError` | `—` | `` |
| `tools/ai/generation/refiners/iterative_refiner.py` | `RefinementStep` | `—` | `` |
| `tools/ai/generation/refiners/iterative_refiner.py` | `RefinementSession` | `—` | `` |
| `tools/ai/generation/refiners/iterative_refiner.py` | `RefinerConfig` | `—` | `` |
| `tools/ai/generation/refiners/iterative_refiner.py` | `ErrorParser` | `—` | `parse_mypy_output, parse_ruff_output` |
| `tools/ai/generation/refiners/iterative_refiner.py` | `CodeAnalyzer` | `—` | `__init__, analyze_syntax, analyze_complexity, analyze_docstrings, calculate_quality_score, __init__ ...` |
| `tools/ai/generation/refiners/iterative_refiner.py` | `AIRefiner` | `—` | `__init__, refine, _build_refinement_prompt, _extract_code` |
| `tools/ai/generation/refiners/iterative_refiner.py` | `AutoFixer` | `—` | `fix_trailing_whitespace, fix_missing_newline, apply_all_fixes` |
| `tools/ai/generation/refiners/iterative_refiner.py` | `IterativeRefiner` | `—` | `__init__, refine, refine_class, refine_function, refine_module, refine_test ...` |
| `tools/ai/generation/refiners/iterative_refiner.py` | `ComplexityVisitor` | `ast.NodeVisitor` | `__init__, visit_If, visit_While, visit_For, visit_ExceptHandler` |
| `tools/ai/generation/refiners/scope_manager.py` | `ScopeBoundary` | `—` | `` |
| `tools/ai/generation/refiners/scope_manager.py` | `ScopeManager` | `SafetyCheck` | `__init__, _load_project_boundaries, check, _extract_symbols, _check_conflicts, _check_encapsulation ...` |
| `tools/ai/generation/refiners/scope_manager.py` | `SymbolVisitor` | `ast.NodeVisitor` | `__init__, visit_ClassDef, visit_FunctionDef, visit_Assign` |
| `tools/ai/generation/refiners/scope_manager.py` | `ImportVisitor` | `ast.NodeVisitor` | `visit_Import, visit_ImportFrom` |
| `tools/ai/orchestration/agent_registry.py` | `AgentStatus` | `Enum` | `` |
| `tools/ai/orchestration/agent_registry.py` | `AgentType` | `Enum` | `` |
| `tools/ai/orchestration/agent_registry.py` | `Capability` | `Enum` | `` |
| `tools/ai/orchestration/agent_registry.py` | `AgentCapability` | `—` | `to_dict, from_dict` |
| `tools/ai/orchestration/agent_registry.py` | `AgentInfo` | `—` | `to_dict, from_dict` |
| `tools/ai/orchestration/agent_registry.py` | `AgentHeartbeat` | `—` | `to_dict` |
| `tools/ai/orchestration/agent_registry.py` | `AgentQuery` | `—` | `` |
| `tools/ai/orchestration/agent_registry.py` | `AgentRegistry` | `—` | `__init__, _load_data, _save_data, _start_health_monitor, _check_agent_health, _update_agent_scores ...` |
| `tools/ai/orchestration/analytics/bottleneck_detector.py` | `BottleneckType` | `Enum` | `` |
| `tools/ai/orchestration/analytics/bottleneck_detector.py` | `Severity` | `Enum` | `` |
| `tools/ai/orchestration/analytics/bottleneck_detector.py` | `Bottleneck` | `—` | `to_dict` |
| `tools/ai/orchestration/analytics/bottleneck_detector.py` | `TaskMetrics` | `—` | `total_time, to_dict` |
| `tools/ai/orchestration/analytics/bottleneck_detector.py` | `AgentMetrics` | `—` | `utilization, to_dict` |
| `tools/ai/orchestration/analytics/bottleneck_detector.py` | `BottleneckDetector` | `—` | `__init__, _load_thresholds, register_task, start_task, complete_task, register_agent ...` |
| `tools/ai/orchestration/analytics/performance_tracker.py` | `MetricType` | `Enum` | `` |
| `tools/ai/orchestration/analytics/performance_tracker.py` | `Aggregation` | `Enum` | `` |
| `tools/ai/orchestration/analytics/performance_tracker.py` | `MetricPoint` | `—` | `to_dict` |
| `tools/ai/orchestration/analytics/performance_tracker.py` | `MetricDefinition` | `—` | `to_dict` |
| `tools/ai/orchestration/analytics/performance_tracker.py` | `MetricSnapshot` | `—` | `to_dict` |
| `tools/ai/orchestration/analytics/performance_tracker.py` | `PerformanceAlert` | `—` | `to_dict` |
| `tools/ai/orchestration/analytics/performance_tracker.py` | `RollingWindow` | `—` | `__init__, add, _cleanup, get_values, get_values_in_range, clear ...` |
| `tools/ai/orchestration/analytics/performance_tracker.py` | `PerformanceTracker` | `—` | `__init__, _register_default_metrics, _start_monitoring, _collect_system_metrics, _cleanup_old_data, _check_alerts ...` |
| `tools/ai/orchestration/analytics/report_generator.py` | `ReportFormat` | `Enum` | `` |
| `tools/ai/orchestration/analytics/report_generator.py` | `ReportType` | `Enum` | `` |
| `tools/ai/orchestration/analytics/report_generator.py` | `ReportConfig` | `—` | `to_dict` |
| `tools/ai/orchestration/analytics/report_generator.py` | `Report` | `—` | `to_dict` |
| `tools/ai/orchestration/analytics/report_generator.py` | `ReportGenerator` | `—` | `__init__, generate_report, _generate_performance_report, _generate_bottleneck_report, _generate_skill_gap_report, _generate_workflow_report ...` |
| `tools/ai/orchestration/analytics/skill_gap_analyzer.py` | `SkillLevel` | `Enum` | `__str__, from_string` |
| `tools/ai/orchestration/analytics/skill_gap_analyzer.py` | `SkillCategory` | `Enum` | `` |
| `tools/ai/orchestration/analytics/skill_gap_analyzer.py` | `GapSeverity` | `Enum` | `` |
| `tools/ai/orchestration/analytics/skill_gap_analyzer.py` | `Skill` | `—` | `to_dict, from_dict` |
| `tools/ai/orchestration/analytics/skill_gap_analyzer.py` | `HumanExpert` | `—` | `to_dict, from_dict` |
| `tools/ai/orchestration/analytics/skill_gap_analyzer.py` | `SkillRequirement` | `—` | `to_dict, from_dict` |
| `tools/ai/orchestration/analytics/skill_gap_analyzer.py` | `SkillGap` | `—` | `to_dict` |
| `tools/ai/orchestration/analytics/skill_gap_analyzer.py` | `SkillGapReport` | `—` | `to_dict` |
| `tools/ai/orchestration/analytics/skill_gap_analyzer.py` | `SkillGapAnalyzer` | `—` | `__init__, _load_data, _save_data, _initialize_skill_taxonomy, register_expert, unregister_expert ...` |
| `tools/ai/orchestration/analytics/workflow_metrics_collector.py` | `WorkflowStatus` | `Enum` | `` |
| `tools/ai/orchestration/analytics/workflow_metrics_collector.py` | `StepStatus` | `Enum` | `` |
| `tools/ai/orchestration/analytics/workflow_metrics_collector.py` | `WorkflowMetrics` | `—` | `duration_seconds, success_rate, to_dict` |
| `tools/ai/orchestration/analytics/workflow_metrics_collector.py` | `StepMetrics` | `—` | `execution_time, to_dict` |
| `tools/ai/orchestration/analytics/workflow_metrics_collector.py` | `ThroughputMetric` | `—` | `to_dict` |
| `tools/ai/orchestration/analytics/workflow_metrics_collector.py` | `ResourceMetric` | `—` | `to_dict` |
| `tools/ai/orchestration/analytics/workflow_metrics_collector.py` | `WorkflowMetricsCollector` | `—` | `__init__, _load_data, _dict_to_workflow_metrics, _dict_to_step_metrics, _dict_to_throughput_metric, _dict_to_resource_metric ...` |
| `tools/ai/orchestration/base_orchestrator.py` | `OrchestrationStatus` | `Enum` | `` |
| `tools/ai/orchestration/base_orchestrator.py` | `TaskPriority` | `Enum` | `` |
| `tools/ai/orchestration/base_orchestrator.py` | `OrchestrationConfig` | `—` | `to_dict` |
| `tools/ai/orchestration/base_orchestrator.py` | `Task` | `—` | `to_dict, from_dict` |
| `tools/ai/orchestration/base_orchestrator.py` | `BaseOrchestrator` | `ABC` | `__init__, _register_as_agent, _setup_event_handlers, _start_scheduler, _process_task_queue, _submit_task ...` |
| `tools/ai/orchestration/co_evolution/co_evolution_engine.py` | `EvolutionType` | `Enum` | `` |
| `tools/ai/orchestration/co_evolution/co_evolution_engine.py` | `EvolutionSeverity` | `Enum` | `` |
| `tools/ai/orchestration/co_evolution/co_evolution_engine.py` | `CodeElement` | `—` | `to_dict` |
| `tools/ai/orchestration/co_evolution/co_evolution_engine.py` | `EvolutionOperation` | `—` | `to_dict` |
| `tools/ai/orchestration/co_evolution/co_evolution_engine.py` | `EvolutionPlan` | `—` | `to_dict` |
| `tools/ai/orchestration/co_evolution/co_evolution_engine.py` | `CoEvolutionEngine` | `—` | `__init__, _load_data, _save_data, _register_default_watch_dirs, add_watch_directory, scan_codebase ...` |
| `tools/ai/orchestration/co_evolution/config_updater.py` | `ConfigFormat` | `Enum` | `` |
| `tools/ai/orchestration/co_evolution/config_updater.py` | `ChangeType` | `Enum` | `` |
| `tools/ai/orchestration/co_evolution/config_updater.py` | `ConfigEntry` | `—` | `to_dict, from_dict` |
| `tools/ai/orchestration/co_evolution/config_updater.py` | `ConfigChange` | `—` | `to_dict, _serialize_value` |
| `tools/ai/orchestration/co_evolution/config_updater.py` | `ConfigMigration` | `—` | `` |
| `tools/ai/orchestration/co_evolution/config_updater.py` | `ConfigUpdater` | `—` | `__init__, _load_registry, _save_registry, _initialize_default_entries, register_config_file, scan_and_update ...` |
| `tools/ai/orchestration/co_evolution/doc_updater.py` | `DocType` | `Enum` | `` |
| `tools/ai/orchestration/co_evolution/doc_updater.py` | `UpdateTrigger` | `Enum` | `` |
| `tools/ai/orchestration/co_evolution/doc_updater.py` | `DocSection` | `—` | `` |
| `tools/ai/orchestration/co_evolution/doc_updater.py` | `DocUpdate` | `—` | `to_dict` |
| `tools/ai/orchestration/co_evolution/doc_updater.py` | `APIDocEntry` | `—` | `to_dict` |
| `tools/ai/orchestration/co_evolution/doc_updater.py` | `DocUpdater` | `—` | `__init__, _load_data, _save_data, _initialize_templates, _get_readme_template, _get_changelog_template ...` |
| `tools/ai/orchestration/co_evolution/example_updater.py` | `ExampleType` | `Enum` | `` |
| `tools/ai/orchestration/co_evolution/example_updater.py` | `ExampleStatus` | `Enum` | `` |
| `tools/ai/orchestration/co_evolution/example_updater.py` | `CodeExample` | `—` | `to_dict, from_dict` |
| `tools/ai/orchestration/co_evolution/example_updater.py` | `APIChange` | `—` | `` |
| `tools/ai/orchestration/co_evolution/example_updater.py` | `ExampleUpdate` | `—` | `to_dict` |
| `tools/ai/orchestration/co_evolution/example_updater.py` | `ExampleUpdater` | `—` | `__init__, _load_data, _save_data, _register_default_example_dirs, add_example_directory, scan_examples ...` |
| `tools/ai/orchestration/co_evolution/test_updater.py` | `TestType` | `Enum` | `` |
| `tools/ai/orchestration/co_evolution/test_updater.py` | `TestStatus` | `Enum` | `` |
| `tools/ai/orchestration/co_evolution/test_updater.py` | `TestCase` | `—` | `to_dict, from_dict` |
| `tools/ai/orchestration/co_evolution/test_updater.py` | `CodeChange` | `—` | `` |
| `tools/ai/orchestration/co_evolution/test_updater.py` | `TestUpdate` | `—` | `to_dict` |
| `tools/ai/orchestration/co_evolution/test_updater.py` | `TestUpdater` | `—` | `__init__, _load_data, _save_data, _register_default_test_dirs, add_test_directory, scan_tests ...` |
| `tools/ai/orchestration/context_manager.py` | `ContextScope` | `Enum` | `` |
| `tools/ai/orchestration/context_manager.py` | `AccessMode` | `Enum` | `` |
| `tools/ai/orchestration/context_manager.py` | `VariableType` | `Enum` | `` |
| `tools/ai/orchestration/context_manager.py` | `ContextVariable` | `—` | `to_dict, _serialize_value, from_dict` |
| `tools/ai/orchestration/context_manager.py` | `ContextSchema` | `—` | `to_dict, from_dict` |
| `tools/ai/orchestration/context_manager.py` | `WorkflowContext` | `—` | `to_dict, from_dict` |
| `tools/ai/orchestration/context_manager.py` | `TaskContext` | `—` | `to_dict, from_dict` |
| `tools/ai/orchestration/context_manager.py` | `ContextChange` | `—` | `to_dict` |
| `tools/ai/orchestration/context_manager.py` | `ContextManager` | `—` | `__init__, _register_default_schemas, _load_data, _save_data, create_context, create_task_context ...` |
| `tools/ai/orchestration/event_bus.py` | `EventType` | `Enum` | `` |
| `tools/ai/orchestration/event_bus.py` | `EventPriority` | `Enum` | `` |
| `tools/ai/orchestration/event_bus.py` | `DeliveryMode` | `Enum` | `` |
| `tools/ai/orchestration/event_bus.py` | `Event` | `—` | `to_dict, from_dict` |
| `tools/ai/orchestration/event_bus.py` | `Subscription` | `—` | `matches` |
| `tools/ai/orchestration/event_bus.py` | `EventEnvelope` | `—` | `to_dict` |
| `tools/ai/orchestration/event_bus.py` | `EventBus` | `—` | `__init__, _load_data, _save_data, _start_processing, _deliver_event, publish ...` |
| `tools/ai/orchestration/human_task/assignment_engine.py` | `AssignmentStrategy` | `Enum` | `` |
| `tools/ai/orchestration/human_task/assignment_engine.py` | `AssignmentStatus` | `Enum` | `` |
| `tools/ai/orchestration/human_task/assignment_engine.py` | `HumanResource` | `—` | `current_load, is_available, to_dict, from_dict` |
| `tools/ai/orchestration/human_task/assignment_engine.py` | `HumanTask` | `—` | `to_dict, from_dict` |
| `tools/ai/orchestration/human_task/assignment_engine.py` | `Assignment` | `—` | `to_dict` |
| `tools/ai/orchestration/human_task/assignment_engine.py` | `AssignmentEngine` | `—` | `__init__, _load_data, _save_data, _start_workers, _process_assignments, _assign_task ...` |
| `tools/ai/orchestration/human_task/feedback_collector.py` | `FeedbackType` | `Enum` | `` |
| `tools/ai/orchestration/human_task/feedback_collector.py` | `FeedbackSeverity` | `Enum` | `` |
| `tools/ai/orchestration/human_task/feedback_collector.py` | `FeedbackStatus` | `Enum` | `` |
| `tools/ai/orchestration/human_task/feedback_collector.py` | `Feedback` | `—` | `to_dict, from_dict` |
| `tools/ai/orchestration/human_task/feedback_collector.py` | `FeedbackSummary` | `—` | `to_dict` |
| `tools/ai/orchestration/human_task/feedback_collector.py` | `HumanSatisfactionMetric` | `—` | `to_dict` |
| `tools/ai/orchestration/human_task/feedback_collector.py` | `FeedbackCollector` | `—` | `__init__, _load_data, _save_data, submit_feedback, _needs_escalation, submit_task_feedback ...` |
| `tools/ai/orchestration/human_task/skill_registry.py` | `SkillCategory` | `Enum` | `` |
| `tools/ai/orchestration/human_task/skill_registry.py` | `SkillType` | `Enum` | `__init__, display_name, from_id, get_by_category` |
| `tools/ai/orchestration/human_task/skill_registry.py` | `ProficiencyLevel` | `Enum` | `__str__, from_string` |
| `tools/ai/orchestration/human_task/skill_registry.py` | `SkillValidationStatus` | `Enum` | `` |
| `tools/ai/orchestration/human_task/skill_registry.py` | `SkillDefinition` | `—` | `from_skill_type, to_dict, from_dict` |
| `tools/ai/orchestration/human_task/skill_registry.py` | `HumanSkill` | `—` | `to_dict, from_dict` |
| `tools/ai/orchestration/human_task/skill_registry.py` | `SkillProficiencyMatrix` | `—` | `get_proficiency, get_skill_score, to_dict, from_dict` |
| `tools/ai/orchestration/human_task/skill_registry.py` | `SkillRegistry` | `—` | `__init__, _load_data, _save_data, _initialize_default_skills_from_enum, get_skill_type, get_skills_by_type_category ...` |
| `tools/ai/orchestration/human_task/work_item_types.py` | `WorkItemType` | `Enum` | `id, display_name, description, required_skills, default_priority, requires_approval ...` |
| `tools/ai/orchestration/human_task/work_queue.py` | `QueueType` | `Enum` | `` |
| `tools/ai/orchestration/human_task/work_queue.py` | `WorkItemStatus` | `Enum` | `` |
| `tools/ai/orchestration/human_task/work_queue.py` | `WorkItemPriority` | `Enum` | `` |
| `tools/ai/orchestration/human_task/work_queue.py` | `WorkItem` | `—` | `age_seconds, wait_time_seconds, processing_time_seconds, is_expired, to_dict, from_dict` |
| `tools/ai/orchestration/human_task/work_queue.py` | `QueueMetrics` | `—` | `to_dict` |
| `tools/ai/orchestration/human_task/work_queue.py` | `WorkQueue` | `—` | `__init__, _initialize_queues, _load_data, _save_data, _start_workers, _push_to_queue ...` |
| `tools/ai/orchestration/pipeline_builder.py` | `StageType` | `Enum` | `` |
| `tools/ai/orchestration/pipeline_builder.py` | `ExecutionStrategy` | `Enum` | `` |
| `tools/ai/orchestration/pipeline_builder.py` | `FailurePolicy` | `Enum` | `` |
| `tools/ai/orchestration/pipeline_builder.py` | `StageConfig` | `—` | `to_dict` |
| `tools/ai/orchestration/pipeline_builder.py` | `PipelineDefinition` | `—` | `to_dict` |
| `tools/ai/orchestration/pipeline_builder.py` | `PipelineExecution` | `—` | `to_dict` |
| `tools/ai/orchestration/pipeline_builder.py` | `PipelineBuilder` | `—` | `__init__, _register_default_handlers, add_task, add_workflow, add_parallel, add_conditional ...` |
| `tools/ai/orchestration/pipeline_executer.py` | `ExecutionStatus` | `Enum` | `` |
| `tools/ai/orchestration/pipeline_executer.py` | `StageExecutionStatus` | `Enum` | `` |
| `tools/ai/orchestration/pipeline_executer.py` | `StageExecution` | `—` | `to_dict` |
| `tools/ai/orchestration/pipeline_executer.py` | `PipelineExecution` | `—` | `progress, total_duration, to_dict` |
| `tools/ai/orchestration/pipeline_executer.py` | `PipelineExecutor` | `—` | `__init__, _register_default_handlers, _load_executions, _save_executions, _deserialize_execution, execute ...` |
| `tools/ai/orchestration/session/session_manager.py` | `SessionType` | `Enum` | `` |
| `tools/ai/orchestration/session/session_manager.py` | `SessionStatus` | `Enum` | `` |
| `tools/ai/orchestration/session/session_manager.py` | `SessionAuthLevel` | `Enum` | `` |
| `tools/ai/orchestration/session/session_manager.py` | `SessionContext` | `—` | `to_dict, from_dict` |
| `tools/ai/orchestration/session/session_manager.py` | `Session` | `—` | `is_expired, idle_minutes, to_dict, from_dict` |
| `tools/ai/orchestration/session/session_manager.py` | `SessionActivity` | `—` | `to_dict` |
| `tools/ai/orchestration/session/session_manager.py` | `SessionManager` | `—` | `__init__, _load_data, _save_data, _start_cleanup_worker, _cleanup_expired_sessions, _cleanup_old_activities ...` |
| `tools/ai/orchestration/session/session_persistence.py` | `PersistenceBackend` | `Enum` | `` |
| `tools/ai/orchestration/session/session_persistence.py` | `PersistenceConfig` | `—` | `to_dict` |
| `tools/ai/orchestration/session/session_persistence.py` | `SessionSnapshot` | `—` | `to_dict, from_dict` |
| `tools/ai/orchestration/session/session_persistence.py` | `SessionArchive` | `—` | `to_dict, from_dict` |
| `tools/ai/orchestration/session/session_persistence.py` | `SessionPersistence` | `—` | `__init__, _load_metadata, _save_metadata, _start_workers, _auto_save_all_sessions, save_session_state ...` |
| `tools/ai/orchestration/session/session_types.py` | `SessionCapability` | `Enum` | `` |
| `tools/ai/orchestration/session/session_types.py` | `SessionIntegration` | `Enum` | `` |
| `tools/ai/orchestration/session/session_types.py` | `SessionTypeConfig` | `—` | `to_dict` |
| `tools/ai/orchestration/session/session_types.py` | `SessionTypeRegistry` | `—` | `__new__, _initialize, _register_default_configs, _register_upgrade_paths, register_config, get_config ...` |
| `tools/ai/orchestration/session/session_types.py` | `SessionTypeMetadata` | `—` | `get_type_description, get_icon, get_color, get_priority, get_rate_limit_headers, is_interactive ...` |
| `tools/ai/orchestration/session/session_types.py` | `SessionTypeConverter` | `—` | `get_compatible_types, get_downgrade_path, estimate_conversion_cost` |
| `tools/ai/orchestration/session/session_types.py` | `SessionTypeValidator` | `—` | `validate_session_data, get_required_fields, get_optional_fields` |
| `tools/ai/orchestration/workflow_engine.py` | `WorkflowStatus` | `Enum` | `` |
| `tools/ai/orchestration/workflow_engine.py` | `TaskStatus` | `Enum` | `` |
| `tools/ai/orchestration/workflow_engine.py` | `TaskType` | `Enum` | `` |
| `tools/ai/orchestration/workflow_engine.py` | `TaskDefinition` | `—` | `to_dict, from_dict` |
| `tools/ai/orchestration/workflow_engine.py` | `WorkflowDefinition` | `—` | `to_dict, from_dict` |
| `tools/ai/orchestration/workflow_engine.py` | `WorkflowExecution` | `—` | `to_dict, from_dict` |
| `tools/ai/orchestration/workflow_engine.py` | `WorkflowEngine` | `—` | `__init__, _load_workflows, _save_workflows, register_workflow, _validate_workflow, unregister_workflow ...` |
| `tools/ai/orchestration/workflow_executor.py` | `WorkflowExecutor` | `—` | `__init__, _init_analysis_components, _init_generation_components, _init_quality_components, _register_components, load_definition ...` |
| `tools/ai/planning/arch_ideator.py` | `ArchitectureThought` | `—` | `` |
| `tools/ai/planning/arch_ideator.py` | `ArchitectureDocument` | `—` | `` |
| `tools/ai/planning/arch_ideator.py` | `ArchitectureIdeator` | `—` | `__init__, load_or_create_document, add_thought, _get_ai_feedback, refine_architecture, generate_mermaid_diagram ...` |
| `tools/ai/planning/arch_implementor.py` | `ModuleTask` | `—` | `` |
| `tools/ai/planning/arch_implementor.py` | `ModulePlan` | `—` | `` |
| `tools/ai/planning/arch_implementor.py` | `ArchitectureImplementor` | `—` | `__init__, load_architecture, create_directory_structure, _resolve_module_path, _generate_init_content, _generate_module_init ...` |
| `tools/ai/planning/dependency_analyzer.py` | `DependencyType` | `str, Enum` | `` |
| `tools/ai/planning/dependency_analyzer.py` | `Severity` | `str, Enum` | `` |
| `tools/ai/planning/dependency_analyzer.py` | `IssueType` | `str, Enum` | `` |
| `tools/ai/planning/dependency_analyzer.py` | `DependencyEdge` | `—` | `` |
| `tools/ai/planning/dependency_analyzer.py` | `ModuleMetrics` | `—` | `` |
| `tools/ai/planning/dependency_analyzer.py` | `DependencyIssue` | `—` | `` |
| `tools/ai/planning/dependency_analyzer.py` | `DependencyGraph` | `—` | `` |
| `tools/ai/planning/dependency_analyzer.py` | `OptimizationSuggestion` | `—` | `` |
| `tools/ai/planning/dependency_analyzer.py` | `DependencyAnalyzer` | `—` | `__init__, analyze, _build_from_project_graph, _scan_and_build, _should_skip, _get_module_name ...` |
| `tools/ai/planning/progress_tracker.py` | `TaskStatus` | `str, Enum` | `` |
| `tools/ai/planning/progress_tracker.py` | `EpicStatus` | `str, Enum` | `` |
| `tools/ai/planning/progress_tracker.py` | `Priority` | `str, Enum` | `` |
| `tools/ai/planning/progress_tracker.py` | `HealthStatus` | `str, Enum` | `` |
| `tools/ai/planning/progress_tracker.py` | `Task` | `—` | `is_overdue, progress_percentage` |
| `tools/ai/planning/progress_tracker.py` | `Epic` | `—` | `calculate_progress, is_overdue` |
| `tools/ai/planning/progress_tracker.py` | `Module` | `—` | `calculate_progress` |
| `tools/ai/planning/progress_tracker.py` | `Milestone` | `—` | `is_overdue` |
| `tools/ai/planning/progress_tracker.py` | `DailySnapshot` | `—` | `` |
| `tools/ai/planning/progress_tracker.py` | `ProgressReport` | `—` | `` |
| `tools/ai/planning/progress_tracker.py` | `ProgressTracker` | `—` | `__init__, _load_state, _save_state, _serialize_task, _deserialize_task, _serialize_epic ...` |
| `tools/ai/planning/task_decomposer.py` | `TaskComplexity` | `str, Enum` | `` |
| `tools/ai/planning/task_decomposer.py` | `TaskCategory` | `str, Enum` | `` |
| `tools/ai/planning/task_decomposer.py` | `DependencyType` | `str, Enum` | `` |
| `tools/ai/planning/task_decomposer.py` | `TaskTemplate` | `—` | `` |
| `tools/ai/planning/task_decomposer.py` | `DecompositionRule` | `—` | `` |
| `tools/ai/planning/task_decomposer.py` | `TaskDependency` | `—` | `` |
| `tools/ai/planning/task_decomposer.py` | `DecompositionResult` | `—` | `` |
| `tools/ai/planning/task_decomposer.py` | `WorkBreakdownStructure` | `—` | `` |
| `tools/ai/planning/task_decomposer.py` | `WBSNode` | `—` | `` |
| `tools/ai/planning/task_decomposer.py` | `TaskDecomposer` | `—` | `__init__, _load_templates, _save_templates, _get_default_templates, _load_rules, _save_rules ...` |
| `tools/ai/quality/debuggers/error_analyzer.py` | `ErrorCategory` | `str, Enum` | `` |
| `tools/ai/quality/debuggers/error_analyzer.py` | `ErrorSeverity` | `str, Enum` | `` |
| `tools/ai/quality/debuggers/error_analyzer.py` | `RootCauseType` | `str, Enum` | `` |
| `tools/ai/quality/debuggers/error_analyzer.py` | `ConfidenceLevel` | `str, Enum` | `` |
| `tools/ai/quality/debuggers/error_analyzer.py` | `StackFrame` | `—` | `` |
| `tools/ai/quality/debuggers/error_analyzer.py` | `ErrorInfo` | `—` | `` |
| `tools/ai/quality/debuggers/error_analyzer.py` | `RootCause` | `—` | `` |
| `tools/ai/quality/debuggers/error_analyzer.py` | `FixSuggestion` | `—` | `` |
| `tools/ai/quality/debuggers/error_analyzer.py` | `ErrorAnalysisReport` | `—` | `` |
| `tools/ai/quality/debuggers/error_analyzer.py` | `ErrorAnalyzerConfig` | `—` | `` |
| `tools/ai/quality/debuggers/error_analyzer.py` | `ErrorParser` | `—` | `__init__, parse_exception, parse_traceback, parse_syntax_error, _categorize_error, _determine_severity ...` |
| `tools/ai/quality/debuggers/error_analyzer.py` | `RootCauseAnalyzer` | `—` | `__init__, analyze, _analyze_import_error, _analyze_name_error, _analyze_attribute_error, _analyze_type_error ...` |
| `tools/ai/quality/debuggers/error_analyzer.py` | `FixSuggestionGenerator` | `—` | `__init__, generate, _is_auto_fixable, _estimate_effort, _suggest_import_fixes, _suggest_name_fixes ...` |
| `tools/ai/quality/debuggers/error_analyzer.py` | `ErrorAnalyzer` | `—` | `__init__, analyze, analyze_current_exception, _load_error_history, _save_error_history, _find_similar_errors ...` |
| `tools/ai/quality/debuggers/runtime_inspector.py` | `VariableScope` | `str, Enum` | `` |
| `tools/ai/quality/debuggers/runtime_inspector.py` | `VariableState` | `str, Enum` | `` |
| `tools/ai/quality/debuggers/runtime_inspector.py` | `ExecutionState` | `str, Enum` | `` |
| `tools/ai/quality/debuggers/runtime_inspector.py` | `TraceEvent` | `str, Enum` | `` |
| `tools/ai/quality/debuggers/runtime_inspector.py` | `VariableInfo` | `—` | `__post_init__, _estimate_size` |
| `tools/ai/quality/debuggers/runtime_inspector.py` | `CallFrame` | `—` | `` |
| `tools/ai/quality/debuggers/runtime_inspector.py` | `Breakpoint` | `—` | `` |
| `tools/ai/quality/debuggers/runtime_inspector.py` | `Watchpoint` | `—` | `` |
| `tools/ai/quality/debuggers/runtime_inspector.py` | `TraceEvent_` | `—` | `` |
| `tools/ai/quality/debuggers/runtime_inspector.py` | `RuntimeSnapshot` | `—` | `` |
| `tools/ai/quality/debuggers/runtime_inspector.py` | `RuntimeInspectionReport` | `—` | `` |
| `tools/ai/quality/debuggers/runtime_inspector.py` | `RuntimeInspectorConfig` | `—` | `` |
| `tools/ai/quality/debuggers/runtime_inspector.py` | `VariableInspector` | `—` | `__init__, inspect_frame, _should_inspect_variable, _create_variable_info, _format_value, _format_value_recursive ...` |
| `tools/ai/quality/debuggers/runtime_inspector.py` | `TraceCollector` | `—` | `__init__, start, stop, _trace_callback, _map_event_type, _create_call_frame ...` |
| `tools/ai/quality/debuggers/runtime_inspector.py` | `BreakpointManager` | `—` | `__init__, add_breakpoint, remove_breakpoint, add_watchpoint, remove_watchpoint, check_breakpoint ...` |
| `tools/ai/quality/debuggers/runtime_inspector.py` | `SnapshotManager` | `—` | `__init__, take_snapshot, get_snapshots, compare_snapshots` |
| `tools/ai/quality/debuggers/runtime_inspector.py` | `RuntimeInspector` | `—` | `__init__, start, stop, pause, resume, inspect ...` |
| `tools/ai/quality/debuggers/runtime_inspector.py` | `InspectContext` | `—` | `__init__, __enter__, __exit__` |
| `tools/ai/quality/debuggers/stack_trace_parser.py` | `FrameType` | `str, Enum` | `` |
| `tools/ai/quality/debuggers/stack_trace_parser.py` | `ErrorCategory` | `str, Enum` | `` |
| `tools/ai/quality/debuggers/stack_trace_parser.py` | `Severity` | `str, Enum` | `` |
| `tools/ai/quality/debuggers/stack_trace_parser.py` | `StackFrame` | `—` | `` |
| `tools/ai/quality/debuggers/stack_trace_parser.py` | `StackTrace` | `—` | `` |
| `tools/ai/quality/debuggers/stack_trace_parser.py` | `CodeSnippet` | `—` | `` |
| `tools/ai/quality/debuggers/stack_trace_parser.py` | `StackTraceAnalysis` | `—` | `` |
| `tools/ai/quality/debuggers/stack_trace_parser.py` | `StackTraceParserConfig` | `—` | `` |
| `tools/ai/quality/debuggers/stack_trace_parser.py` | `StackTraceParser` | `—` | `__init__, _compile_patterns, parse, parse_exception, _determine_frame_type, _categorize_error ...` |
| `tools/ai/quality/debuggers/stack_trace_parser.py` | `StackTraceAnalyzer` | `—` | `__init__, analyze, _find_root_cause, _extract_error_snippet, _extract_related_snippets, _analyze_imports ...` |
| `tools/ai/quality/debuggers/stack_trace_parser.py` | `StackTraceParserTool` | `—` | `__init__, analyze, analyze_file, export_analysis, close` |
| `tools/ai/quality/documenters/api_doc_generator.py` | `APIFramework` | `Enum` | `` |
| `tools/ai/quality/documenters/api_doc_generator.py` | `HttpMethod` | `Enum` | `` |
| `tools/ai/quality/documenters/api_doc_generator.py` | `AuthType` | `Enum` | `` |
| `tools/ai/quality/documenters/api_doc_generator.py` | `APIEndpoint` | `—` | `to_dict` |
| `tools/ai/quality/documenters/api_doc_generator.py` | `GraphQLSchema` | `—` | `to_dict` |
| `tools/ai/quality/documenters/api_doc_generator.py` | `DataModel` | `—` | `to_dict` |
| `tools/ai/quality/documenters/api_doc_generator.py` | `APIDocGenerator` | `—` | `__init__, generate, _detect_framework, _search_in_files, _scan_endpoints, _scan_fastapi_endpoints ...` |
| `tools/ai/quality/documenters/architecture_doc.py` | `DiagramFormat` | `Enum` | `` |
| `tools/ai/quality/documenters/architecture_doc.py` | `ArchitectureLevel` | `Enum` | `` |
| `tools/ai/quality/documenters/architecture_doc.py` | `DocumentationStyle` | `Enum` | `` |
| `tools/ai/quality/documenters/architecture_doc.py` | `Component` | `—` | `` |
| `tools/ai/quality/documenters/architecture_doc.py` | `DataFlow` | `—` | `` |
| `tools/ai/quality/documenters/architecture_doc.py` | `ArchitectureDecision` | `—` | `` |
| `tools/ai/quality/documenters/architecture_doc.py` | `ArchitectureDocGenerator` | `—` | `__init__, generate, _analyze_codebase, _analyze_file, _get_decorator_name, _get_return_annotation ...` |
| `tools/ai/quality/documenters/changelog_generator.py` | `ChangeType` | `Enum` | `` |
| `tools/ai/quality/documenters/changelog_generator.py` | `VersionBump` | `Enum` | `` |
| `tools/ai/quality/documenters/changelog_generator.py` | `Commit` | `—` | `to_dict` |
| `tools/ai/quality/documenters/changelog_generator.py` | `Release` | `—` | `changes_by_type, has_breaking_changes, to_dict` |
| `tools/ai/quality/documenters/changelog_generator.py` | `ChangelogConfig` | `—` | `to_dict` |
| `tools/ai/quality/documenters/changelog_generator.py` | `ChangelogGenerator` | `—` | `__init__, generate, _fetch_git_history, _parse_conventional_commits, _detect_versions, _group_commits_by_release ...` |
| `tools/ai/quality/testers/coverage_analyzer.py` | `CoverageLevel` | `str, Enum` | `` |
| `tools/ai/quality/testers/coverage_analyzer.py` | `CoverageType` | `str, Enum` | `` |
| `tools/ai/quality/testers/coverage_analyzer.py` | `GapSeverity` | `str, Enum` | `` |
| `tools/ai/quality/testers/coverage_analyzer.py` | `GapCategory` | `str, Enum` | `` |
| `tools/ai/quality/testers/coverage_analyzer.py` | `CoverageMetric` | `—` | `` |
| `tools/ai/quality/testers/coverage_analyzer.py` | `FileCoverage` | `—` | `` |
| `tools/ai/quality/testers/coverage_analyzer.py` | `ModuleCoverage` | `—` | `` |
| `tools/ai/quality/testers/coverage_analyzer.py` | `CoverageGap` | `—` | `` |
| `tools/ai/quality/testers/coverage_analyzer.py` | `TestRecommendation` | `—` | `` |
| `tools/ai/quality/testers/coverage_analyzer.py` | `CoverageReport` | `—` | `` |
| `tools/ai/quality/testers/coverage_analyzer.py` | `CoverageAnalyzerConfig` | `—` | `` |
| `tools/ai/quality/testers/coverage_analyzer.py` | `CoverageParser` | `—` | `__init__, parse, _run_coverage, _parse_coverage_json, _parse_coverage_xml, _parse_lcov ...` |
| `tools/ai/quality/testers/coverage_analyzer.py` | `GapDetector` | `—` | `__init__, detect_gaps, _file_to_module, _is_uncovered_function, _is_uncovered_class, _create_function_gap ...` |
| `tools/ai/quality/testers/coverage_analyzer.py` | `RecommendationGenerator` | `—` | `__init__, generate, _create_file_recommendation, _generate_test_template` |
| `tools/ai/quality/testers/coverage_analyzer.py` | `CoverageAnalyzer` | `—` | `__init__, analyze, _calculate_overall_metrics, _get_coverage_level, _build_module_coverages, _create_coverage_metrics ...` |
| `tools/ai/quality/testers/mutation_tester.py` | `MutationOperator` | `str, Enum` | `` |
| `tools/ai/quality/testers/mutation_tester.py` | `MutationStatus` | `str, Enum` | `` |
| `tools/ai/quality/testers/mutation_tester.py` | `MutationCategory` | `str, Enum` | `` |
| `tools/ai/quality/testers/mutation_tester.py` | `Mutation` | `—` | `` |
| `tools/ai/quality/testers/mutation_tester.py` | `MutationResult` | `—` | `` |
| `tools/ai/quality/testers/mutation_tester.py` | `TestCoverage` | `—` | `` |
| `tools/ai/quality/testers/mutation_tester.py` | `MutationReport` | `—` | `` |
| `tools/ai/quality/testers/mutation_tester.py` | `MutationTesterConfig` | `—` | `` |
| `tools/ai/quality/testers/mutation_tester.py` | `MutationGenerator` | `ast.NodeTransformer` | `__init__, generate, _create_mutation, _get_category, visit_FunctionDef, visit_ClassDef ...` |
| `tools/ai/quality/testers/mutation_tester.py` | `MutationExecutor` | `—` | `__init__, check_test_suite_passing, _build_test_command, execute_mutation, _apply_mutation, execute_mutations ...` |
| `tools/ai/quality/testers/mutation_tester.py` | `MutationTester` | `—` | `__init__, test, _create_empty_report, _find_source_files, _should_ignore, _generate_mutations ...` |
| `tools/ai/quality/testers/test_runner.py` | `TestStatus` | `str, Enum` | `` |
| `tools/ai/quality/testers/test_runner.py` | `TestFramework` | `str, Enum` | `` |
| `tools/ai/quality/testers/test_runner.py` | `TestSelectionStrategy` | `str, Enum` | `` |
| `tools/ai/quality/testers/test_runner.py` | `ExecutionMode` | `str, Enum` | `` |
| `tools/ai/quality/testers/test_runner.py` | `FailureCategory` | `str, Enum` | `` |
| `tools/ai/quality/testers/test_runner.py` | `TestCase` | `—` | `` |
| `tools/ai/quality/testers/test_runner.py` | `TestSuite` | `—` | `total` |
| `tools/ai/quality/testers/test_runner.py` | `TestRun` | `—` | `pass_rate, is_success` |
| `tools/ai/quality/testers/test_runner.py` | `TestFailureAnalysis` | `—` | `` |
| `tools/ai/quality/testers/test_runner.py` | `TestReport` | `—` | `` |
| `tools/ai/quality/testers/test_runner.py` | `TestRunnerConfig` | `—` | `` |
| `tools/ai/quality/testers/test_runner.py` | `TestDiscovery` | `—` | `__init__, discover, _discover_pytest, _discover_unittest, _discover_generic, _should_ignore` |
| `tools/ai/quality/testers/test_runner.py` | `TestSelector` | `—` | `__init__, select, _select_changed, _select_affected, _select_failed, _select_by_tag ...` |
| `tools/ai/quality/testers/test_runner.py` | `TestExecutor` | `—` | `__init__, execute, _execute_pytest, _execute_unittest, _execute_generic, _parse_pytest_output ...` |
| `tools/ai/quality/testers/test_runner.py` | `FailureAnalyzer` | `—` | `__init__, analyze, _analyze_failure, _generate_fix_suggestions` |
| `tools/ai/quality/testers/test_runner.py` | `FlakyDetector` | `—` | `__init__, detect` |
| `tools/ai/quality/testers/test_runner.py` | `TestRunner` | `—` | `__init__, run, run_specific, run_changed, run_affected, run_failed ...` |
| `tools/ai/quality/validators/api_consistency.py` | `ChangeType` | `str, Enum` | `` |
| `tools/ai/quality/validators/api_consistency.py` | `SemVerImpact` | `str, Enum` | `` |
| `tools/ai/quality/validators/api_consistency.py` | `CompatibilityStatus` | `str, Enum` | `` |
| `tools/ai/quality/validators/api_consistency.py` | `APIChange` | `—` | `` |
| `tools/ai/quality/validators/api_consistency.py` | `APICompatibilityReport` | `—` | `` |
| `tools/ai/quality/validators/api_consistency.py` | `APIValidatorConfig` | `—` | `` |
| `tools/ai/quality/validators/api_consistency.py` | `APIComparator` | `—` | `__init__, compare, _should_ignore, _compare_elements, _compare_signatures, _compare_bases` |
| `tools/ai/quality/validators/api_consistency.py` | `APIConsistencyValidator` | `—` | `__init__, validate, validate_string, validate_module, _get_module_code, _deserialize_elements ...` |
| `tools/ai/quality/validators/architecture_validator.py` | `LayerType` | `str, Enum` | `` |
| `tools/ai/quality/validators/architecture_validator.py` | `DependencyRule` | `str, Enum` | `` |
| `tools/ai/quality/validators/architecture_validator.py` | `RuleSeverity` | `str, Enum` | `` |
| `tools/ai/quality/validators/architecture_validator.py` | `PatternType` | `str, Enum` | `` |
| `tools/ai/quality/validators/architecture_validator.py` | `LayerDefinition` | `—` | `` |
| `tools/ai/quality/validators/architecture_validator.py` | `ArchitectureRule` | `—` | `` |
| `tools/ai/quality/validators/architecture_validator.py` | `RuleViolation` | `—` | `` |
| `tools/ai/quality/validators/architecture_validator.py` | `ArchitectureMetrics` | `—` | `` |
| `tools/ai/quality/validators/architecture_validator.py` | `ArchitectureValidationReport` | `—` | `` |
| `tools/ai/quality/validators/architecture_validator.py` | `ArchitectureValidatorConfig` | `—` | `` |
| `tools/ai/quality/validators/architecture_validator.py` | `ArchitecturePatterns` | `—` | `clean_architecture, hexagonal_architecture, layered_architecture, ddd_architecture` |
| `tools/ai/quality/validators/architecture_validator.py` | `LayerDetector` | `—` | `__init__, _compile_patterns, _pattern_to_regex, detect_layer, get_layer_definition` |
| `tools/ai/quality/validators/architecture_validator.py` | `RuleValidator` | `—` | `__init__, validate_dependency, _matches_pattern` |
| `tools/ai/quality/validators/architecture_validator.py` | `ArchitectureValidator` | `—` | `__init__, _load_pattern, validate, _find_import_line, _detect_circular_dependencies, _calculate_metrics ...` |
| `tools/ai/quality/validators/compatibility_validator.py` | `CompatibilityStatus` | `str, Enum` | `` |
| `tools/ai/quality/validators/compatibility_validator.py` | `PythonVersion` | `str, Enum` | `` |
| `tools/ai/quality/validators/compatibility_validator.py` | `IssueSeverity` | `str, Enum` | `` |
| `tools/ai/quality/validators/compatibility_validator.py` | `FeatureCategory` | `str, Enum` | `` |
| `tools/ai/quality/validators/compatibility_validator.py` | `PythonFeatureRegistry` | `—` | `get_minimum_version, get_category, get_all_features` |
| `tools/ai/quality/validators/compatibility_validator.py` | `VersionConstraint` | `—` | `` |
| `tools/ai/quality/validators/compatibility_validator.py` | `CompatibilityIssue` | `—` | `` |
| `tools/ai/quality/validators/compatibility_validator.py` | `DependencyInfo` | `—` | `` |
| `tools/ai/quality/validators/compatibility_validator.py` | `PythonVersionInfo` | `—` | `` |
| `tools/ai/quality/validators/compatibility_validator.py` | `CompatibilityReport` | `—` | `` |
| `tools/ai/quality/validators/compatibility_validator.py` | `CompatibilityValidatorConfig` | `—` | `` |
| `tools/ai/quality/validators/compatibility_validator.py` | `SyntaxFeatureDetector` | `ast.NodeVisitor` | `__init__, detect, visit_Match, visit_MatchAs, visit_MatchOr, visit_NamedExpr ...` |
| `tools/ai/quality/validators/compatibility_validator.py` | `DependencyAnalyzer` | `—` | `__init__, _load_installed_packages, analyze_requirements, analyze_pyproject, analyze_setup_py, _analyze_dependency ...` |
| `tools/ai/quality/validators/compatibility_validator.py` | `CompatibilityValidator` | `—` | `__init__, validate, _detect_project_name, _detect_project_version, _get_python_requires, _validate_python_version ...` |
| `tools/ai/quality/validators/compatibility_validator.py` | `ImportVisitor` | `ast.NodeVisitor` | `visit_Import, visit_ImportFrom, _check_import` |
| `tools/ai/quality/validators/complexity_validator.py` | `ComplexityMetric` | `str, Enum` | `` |
| `tools/ai/quality/validators/complexity_validator.py` | `Severity` | `str, Enum` | `` |
| `tools/ai/quality/validators/complexity_validator.py` | `Scope` | `str, Enum` | `` |
| `tools/ai/quality/validators/complexity_validator.py` | `ComplexityThreshold` | `—` | `` |
| `tools/ai/quality/validators/complexity_validator.py` | `ComplexityViolation` | `—` | `` |
| `tools/ai/quality/validators/complexity_validator.py` | `ComplexityMetrics` | `—` | `` |
| `tools/ai/quality/validators/complexity_validator.py` | `ComplexityReport` | `—` | `` |
| `tools/ai/quality/validators/complexity_validator.py` | `ComplexityValidatorConfig` | `—` | `` |
| `tools/ai/quality/validators/complexity_validator.py` | `ComplexityAnalyzer` | `ast.NodeVisitor` | `__init__, analyze, _create_module_metrics, _module_name, visit_ClassDef, visit_FunctionDef ...` |
| `tools/ai/quality/validators/complexity_validator.py` | `ComplexityValidator` | `—` | `__init__, validate, _analyze_file, _check_thresholds, _get_suggestion, _calculate_project_metrics ...` |
| `tools/ai/quality/validators/coverage_validator.py` | `CoverageType` | `str, Enum` | `` |
| `tools/ai/quality/validators/coverage_validator.py` | `CoverageFormat` | `str, Enum` | `` |
| `tools/ai/quality/validators/coverage_validator.py` | `Severity` | `str, Enum` | `` |
| `tools/ai/quality/validators/coverage_validator.py` | `CoverageThreshold` | `—` | `` |
| `tools/ai/quality/validators/coverage_validator.py` | `CoverageViolation` | `—` | `` |
| `tools/ai/quality/validators/coverage_validator.py` | `FileCoverage` | `—` | `` |
| `tools/ai/quality/validators/coverage_validator.py` | `ModuleCoverage` | `—` | `` |
| `tools/ai/quality/validators/coverage_validator.py` | `CoverageReport` | `—` | `` |
| `tools/ai/quality/validators/coverage_validator.py` | `CoverageValidatorConfig` | `—` | `` |
| `tools/ai/quality/validators/coverage_validator.py` | `CoverageParser` | `—` | `parse_coverage_json, parse_coverage_xml, parse_lcov, run_pytest_cov` |
| `tools/ai/quality/validators/coverage_validator.py` | `CoverageValidator` | `—` | `__init__, validate, _get_coverage_data, _calculate_overall_metrics, _build_module_coverages, _check_thresholds ...` |
| `tools/ai/quality/validators/dependency_validator.py` | `DependencySource` | `str, Enum` | `` |
| `tools/ai/quality/validators/dependency_validator.py` | `DependencyType` | `str, Enum` | `` |
| `tools/ai/quality/validators/dependency_validator.py` | `Severity` | `str, Enum` | `` |
| `tools/ai/quality/validators/dependency_validator.py` | `VulnerabilitySeverity` | `str, Enum` | `` |
| `tools/ai/quality/validators/dependency_validator.py` | `LicenseCompatibility` | `str, Enum` | `` |
| `tools/ai/quality/validators/dependency_validator.py` | `Vulnerability` | `—` | `` |
| `tools/ai/quality/validators/dependency_validator.py` | `LicenseInfo` | `—` | `` |
| `tools/ai/quality/validators/dependency_validator.py` | `DependencyInfo` | `—` | `` |
| `tools/ai/quality/validators/dependency_validator.py` | `DependencyIssue` | `—` | `` |
| `tools/ai/quality/validators/dependency_validator.py` | `LicenseViolation` | `—` | `` |
| `tools/ai/quality/validators/dependency_validator.py` | `DependencyReport` | `—` | `` |
| `tools/ai/quality/validators/dependency_validator.py` | `DependencyValidatorConfig` | `—` | `` |
| `tools/ai/quality/validators/dependency_validator.py` | `DependencyParser` | `—` | `__init__, parse_all, parse_requirements, parse_pyproject, parse_poetry_lock, parse_pipfile_lock ...` |
| `tools/ai/quality/validators/dependency_validator.py` | `VulnerabilityChecker` | `—` | `__init__, check_package, _map_safety_severity` |
| `tools/ai/quality/validators/dependency_validator.py` | `LicenseChecker` | `—` | `__init__, check_license, _analyze_license` |
| `tools/ai/quality/validators/dependency_validator.py` | `DependencyValidator` | `—` | `__init__, validate, _enrich_with_installed_versions, _enrich_with_pypi_info, _get_pypi_info, _check_dependency_issues ...` |
| `tools/ai/quality/validators/docstring_validator.py` | `DocstringStyle` | `str, Enum` | `` |
| `tools/ai/quality/validators/docstring_validator.py` | `DocstringSection` | `str, Enum` | `` |
| `tools/ai/quality/validators/docstring_validator.py` | `Severity` | `str, Enum` | `` |
| `tools/ai/quality/validators/docstring_validator.py` | `EntityType` | `str, Enum` | `` |
| `tools/ai/quality/validators/docstring_validator.py` | `DocstringIssue` | `—` | `` |
| `tools/ai/quality/validators/docstring_validator.py` | `DocstringMetrics` | `—` | `` |
| `tools/ai/quality/validators/docstring_validator.py` | `DocstringReport` | `—` | `` |
| `tools/ai/quality/validators/docstring_validator.py` | `DocstringValidatorConfig` | `—` | `` |
| `tools/ai/quality/validators/docstring_validator.py` | `DocstringParser` | `—` | `__init__, analyze, _detect_style, _parse_sections, _parse_google_style, _parse_numpy_style ...` |
| `tools/ai/quality/validators/docstring_validator.py` | `DocstringValidator` | `—` | `__init__, validate, _validate_file, _calculate_overall_score, _calculate_overall_grade, _should_ignore ...` |
| `tools/ai/quality/validators/docstring_validator.py` | `DocstringVisitor` | `ast.NodeVisitor` | `__init__, visit_Module, visit_ClassDef, visit_FunctionDef, visit_AsyncFunctionDef, _visit_function ...` |
| `tools/ai/quality/validators/import_validator.py` | `ImportType` | `str, Enum` | `` |
| `tools/ai/quality/validators/import_validator.py` | `Severity` | `str, Enum` | `` |
| `tools/ai/quality/validators/import_validator.py` | `ImportGroup` | `str, Enum` | `` |
| `tools/ai/quality/validators/import_validator.py` | `ImportStatement` | `—` | `` |
| `tools/ai/quality/validators/import_validator.py` | `ImportIssue` | `—` | `` |
| `tools/ai/quality/validators/import_validator.py` | `ModuleImports` | `—` | `` |
| `tools/ai/quality/validators/import_validator.py` | `ImportReport` | `—` | `` |
| `tools/ai/quality/validators/import_validator.py` | `ImportValidatorConfig` | `—` | `` |
| `tools/ai/quality/validators/import_validator.py` | `ImportParser` | `—` | `__init__, parse_file, _get_stdlib_modules, classify_import` |
| `tools/ai/quality/validators/import_validator.py` | `ImportVisitor` | `ast.NodeVisitor` | `__init__, visit_Module, _collect_used_names, visit_Import, visit_ImportFrom, visit_If ...` |
| `tools/ai/quality/validators/import_validator.py` | `ImportValidator` | `—` | `__init__, validate, _aggregate_statistics, _detect_circular_dependencies, _calculate_overall_score, _calculate_grade ...` |
| `tools/ai/quality/validators/import_validator.py` | `NameCollector` | `ast.NodeVisitor` | `__init__, visit_Name, visit_Attribute` |
| `tools/ai/quality/validators/mypy_validator.py` | `MypyErrorCode` | `str, Enum` | `` |
| `tools/ai/quality/validators/mypy_validator.py` | `Severity` | `str, Enum` | `` |
| `tools/ai/quality/validators/mypy_validator.py` | `MypyErrorCategory` | `str, Enum` | `` |
| `tools/ai/quality/validators/mypy_validator.py` | `MypyError` | `—` | `__str__` |
| `tools/ai/quality/validators/mypy_validator.py` | `TypeCoverageInfo` | `—` | `` |
| `tools/ai/quality/validators/mypy_validator.py` | `MypyReport` | `—` | `` |
| `tools/ai/quality/validators/mypy_validator.py` | `MypyValidatorConfig` | `—` | `` |
| `tools/ai/quality/validators/mypy_validator.py` | `MypyOutputParser` | `—` | `parse, parse_json, parse_coverage, _parse_line, _parse_error_code` |
| `tools/ai/quality/validators/mypy_validator.py` | `MypyValidator` | `—` | `__init__, validate, validate_string, validate_string_return_output, _run_mypy, _run_mypy_on_file ...` |
| `tools/ai/quality/validators/naming_spellcheck_validator.py` | `NamingConvention` | `str, Enum` | `` |
| `tools/ai/quality/validators/naming_spellcheck_validator.py` | `EntityType` | `str, Enum` | `` |
| `tools/ai/quality/validators/naming_spellcheck_validator.py` | `Severity` | `str, Enum` | `` |
| `tools/ai/quality/validators/naming_spellcheck_validator.py` | `SpellcheckLanguage` | `str, Enum` | `` |
| `tools/ai/quality/validators/naming_spellcheck_validator.py` | `NamingRule` | `—` | `` |
| `tools/ai/quality/validators/naming_spellcheck_validator.py` | `NamingViolation` | `—` | `` |
| `tools/ai/quality/validators/naming_spellcheck_validator.py` | `SpellingViolation` | `—` | `` |
| `tools/ai/quality/validators/naming_spellcheck_validator.py` | `NamingSpellcheckReport` | `—` | `` |
| `tools/ai/quality/validators/naming_spellcheck_validator.py` | `NamingSpellcheckConfig` | `—` | `` |
| `tools/ai/quality/validators/naming_spellcheck_validator.py` | `NamingValidator` | `ast.NodeVisitor` | `__init__, validate, visit_Module, visit_ClassDef, _is_exception_class, visit_FunctionDef ...` |
| `tools/ai/quality/validators/naming_spellcheck_validator.py` | `SpellcheckValidator` | `ast.NodeVisitor` | `__init__, validate, visit_FunctionDef, visit_ClassDef, visit_Assign, visit_Constant ...` |
| `tools/ai/quality/validators/naming_spellcheck_validator.py` | `NamingSpellcheckValidator` | `—` | `__init__, validate, _check_banned_names, _should_ignore, _calculate_overall_score, _calculate_grade ...` |
| `tools/ai/quality/validators/performance_validator.py` | `PerformanceIssueType` | `str, Enum` | `` |
| `tools/ai/quality/validators/performance_validator.py` | `Severity` | `str, Enum` | `` |
| `tools/ai/quality/validators/performance_validator.py` | `ComplexityClass` | `str, Enum` | `` |
| `tools/ai/quality/validators/performance_validator.py` | `ComplexityAnalysis` | `—` | `` |
| `tools/ai/quality/validators/performance_validator.py` | `ProfileResult` | `—` | `` |
| `tools/ai/quality/validators/performance_validator.py` | `MemoryProfile` | `—` | `` |
| `tools/ai/quality/validators/performance_validator.py` | `BenchmarkResult` | `—` | `` |
| `tools/ai/quality/validators/performance_validator.py` | `PerformanceIssue` | `—` | `` |
| `tools/ai/quality/validators/performance_validator.py` | `PerformanceReport` | `—` | `` |
| `tools/ai/quality/validators/performance_validator.py` | `PerformanceValidatorConfig` | `—` | `` |
| `tools/ai/quality/validators/performance_validator.py` | `ComplexityAnalyzer` | `ast.NodeVisitor` | `__init__, analyze_file, visit_FunctionDef, visit_AsyncFunctionDef, visit_For, visit_While ...` |
| `tools/ai/quality/validators/performance_validator.py` | `PerformanceIssueDetector` | `ast.NodeVisitor` | `__init__, analyze_file, visit_FunctionDef, visit_For, visit_While, visit_BinOp ...` |
| `tools/ai/quality/validators/performance_validator.py` | `CodeProfiler` | `—` | `__init__, profile_file` |
| `tools/ai/quality/validators/performance_validator.py` | `MemoryProfiler` | `—` | `__init__, profile_file` |
| `tools/ai/quality/validators/performance_validator.py` | `Benchmarker` | `—` | `__init__, benchmark_function` |
| `tools/ai/quality/validators/performance_validator.py` | `PerformanceValidator` | `—` | `__init__, validate, _is_complexity_problematic, _should_ignore, _calculate_overall_score, _calculate_grade ...` |
| `tools/ai/quality/validators/pytest_validator.py` | `TestStatus` | `str, Enum` | `` |
| `tools/ai/quality/validators/pytest_validator.py` | `TestOutcome` | `str, Enum` | `` |
| `tools/ai/quality/validators/pytest_validator.py` | `Severity` | `str, Enum` | `` |
| `tools/ai/quality/validators/pytest_validator.py` | `TestCase` | `—` | `` |
| `tools/ai/quality/validators/pytest_validator.py` | `TestFile` | `—` | `` |
| `tools/ai/quality/validators/pytest_validator.py` | `TestSuite` | `—` | `` |
| `tools/ai/quality/validators/pytest_validator.py` | `TestIssue` | `—` | `` |
| `tools/ai/quality/validators/pytest_validator.py` | `PytestReport` | `—` | `` |
| `tools/ai/quality/validators/pytest_validator.py` | `PytestValidatorConfig` | `—` | `` |
| `tools/ai/quality/validators/pytest_validator.py` | `PytestOutputParser` | `—` | `parse_junit_xml, parse_json_report, parse_text_output` |
| `tools/ai/quality/validators/pytest_validator.py` | `PytestValidator` | `—` | `__init__, validate, validate_file, _run_pytest, _run_coverage, _detect_flaky_tests ...` |
| `tools/ai/quality/validators/ruff_validator.py` | `RuffRuleCategory` | `str, Enum` | `` |
| `tools/ai/quality/validators/ruff_validator.py` | `Severity` | `str, Enum` | `` |
| `tools/ai/quality/validators/ruff_validator.py` | `FixAvailability` | `str, Enum` | `` |
| `tools/ai/quality/validators/ruff_validator.py` | `RuffViolation` | `—` | `__str__` |
| `tools/ai/quality/validators/ruff_validator.py` | `FileViolations` | `—` | `` |
| `tools/ai/quality/validators/ruff_validator.py` | `RuffReport` | `—` | `` |
| `tools/ai/quality/validators/ruff_validator.py` | `RuffValidatorConfig` | `—` | `` |
| `tools/ai/quality/validators/ruff_validator.py` | `RuleCategoryMapper` | `—` | `get_category` |
| `tools/ai/quality/validators/ruff_validator.py` | `RuffOutputParser` | `—` | `parse, parse_json, _parse_line, _parse_fix_availability` |
| `tools/ai/quality/validators/ruff_validator.py` | `RuffValidator` | `—` | `__init__, validate, validate_string, validate_string_return_output, fix, _run_ruff ...` |
| `tools/ai/quality/validators/security_validator.py` | `SecuritySeverity` | `str, Enum` | `` |
| `tools/ai/quality/validators/security_validator.py` | `VulnerabilityType` | `str, Enum` | `` |
| `tools/ai/quality/validators/security_validator.py` | `SecurityCategory` | `str, Enum` | `` |
| `tools/ai/quality/validators/security_validator.py` | `Confidence` | `str, Enum` | `` |
| `tools/ai/quality/validators/security_validator.py` | `SecurityIssue` | `—` | `` |
| `tools/ai/quality/validators/security_validator.py` | `SecretFinding` | `—` | `` |
| `tools/ai/quality/validators/security_validator.py` | `DependencyVulnerability` | `—` | `` |
| `tools/ai/quality/validators/security_validator.py` | `SecurityReport` | `—` | `` |
| `tools/ai/quality/validators/security_validator.py` | `SecurityValidatorConfig` | `—` | `` |
| `tools/ai/quality/validators/security_validator.py` | `SecretDetector` | `—` | `__init__, _compile_patterns, scan_file, _should_ignore_line, _calculate_entropy` |
| `tools/ai/quality/validators/security_validator.py` | `SecurityVisitor` | `ast.NodeVisitor` | `__init__, visit_Import, visit_ImportFrom, visit_FunctionDef, visit_Call, visit_Assign ...` |
| `tools/ai/quality/validators/security_validator.py` | `DependencyScanner` | `—` | `__init__, scan, _scan_pip_audit, _scan_safety, _map_severity` |
| `tools/ai/quality/validators/security_validator.py` | `SecurityValidator` | `—` | `__init__, validate, _update_severity_stats, _should_ignore, _calculate_overall_score, _calculate_grade ...` |
| `tools/ai/shared/config.py` | `ConfigFormat` | `str, Enum` | `` |
| `tools/ai/shared/config.py` | `LogLevel` | `str, Enum` | `` |
| `tools/ai/shared/config.py` | `Environment` | `str, Enum` | `` |
| `tools/ai/shared/config.py` | `LLMProvider` | `str, Enum` | `` |
| `tools/ai/shared/config.py` | `LoggingConfig` | `—` | `` |
| `tools/ai/shared/config.py` | `LLMConfig` | `—` | `` |
| `tools/ai/shared/config.py` | `OllamaConfig` | `—` | `` |
| `tools/ai/shared/config.py` | `VectorStoreConfig` | `—` | `` |
| `tools/ai/shared/config.py` | `StateConfig` | `—` | `` |
| `tools/ai/shared/config.py` | `GitConfig` | `—` | `` |
| `tools/ai/shared/config.py` | `AnalysisConfig` | `—` | `` |
| `tools/ai/shared/config.py` | `GenerationConfig` | `—` | `` |
| `tools/ai/shared/config.py` | `ValidationConfig` | `—` | `` |
| `tools/ai/shared/config.py` | `TestingConfig` | `—` | `` |
| `tools/ai/shared/config.py` | `EntryPointConfig` | `—` | `` |
| `tools/ai/shared/config.py` | `OrchestrationConfig` | `—` | `` |
| `tools/ai/shared/config.py` | `MetricsConfig` | `—` | `` |
| `tools/ai/shared/config.py` | `SecurityConfig` | `—` | `` |
| `tools/ai/shared/config.py` | `ExperimentalConfig` | `—` | `` |
| `tools/ai/shared/config.py` | `Config` | `—` | `__post_init__, load, load_from_dict, _detect_format, _load_from_default_locations, _load_json ...` |
| `tools/ai/shared/file_utils.py` | `FileWatcher` | `—` | `__init__, take_snapshot, get_changes` |
| `tools/ai/shared/file_utils.py` | `FileLock` | `—` | `__init__, acquire, release, __enter__, __exit__` |
| `tools/ai/shared/git_utils.py` | `GitStatus` | `str, Enum` | `` |
| `tools/ai/shared/git_utils.py` | `ChangeType` | `str, Enum` | `` |
| `tools/ai/shared/git_utils.py` | `MergeStrategy` | `str, Enum` | `` |
| `tools/ai/shared/git_utils.py` | `CommitType` | `str, Enum` | `` |
| `tools/ai/shared/git_utils.py` | `GitFileStatus` | `—` | `` |
| `tools/ai/shared/git_utils.py` | `GitCommit` | `—` | `` |
| `tools/ai/shared/git_utils.py` | `GitBranch` | `—` | `` |
| `tools/ai/shared/git_utils.py` | `GitTag` | `—` | `` |
| `tools/ai/shared/git_utils.py` | `GitRemote` | `—` | `` |
| `tools/ai/shared/git_utils.py` | `GitDiff` | `—` | `` |
| `tools/ai/shared/git_utils.py` | `GitStash` | `—` | `` |
| `tools/ai/shared/git_utils.py` | `GitUtils` | `—` | `__init__, is_repo, git_dir, init, get_config, set_config ...` |
| `tools/ai/shared/llm_client.py` | `MessageRole` | `str, Enum` | `` |
| `tools/ai/shared/llm_client.py` | `ResponseFormat` | `str, Enum` | `` |
| `tools/ai/shared/llm_client.py` | `FinishReason` | `str, Enum` | `` |
| `tools/ai/shared/llm_client.py` | `Message` | `—` | `` |
| `tools/ai/shared/llm_client.py` | `LLMResponse` | `—` | `` |
| `tools/ai/shared/llm_client.py` | `StreamingChunk` | `—` | `` |
| `tools/ai/shared/llm_client.py` | `Tool` | `—` | `` |
| `tools/ai/shared/llm_client.py` | `LLMConfig` | `—` | `` |
| `tools/ai/shared/llm_client.py` | `BaseLLMClient` | `—` | `__init__, _create_session, session, _get_cache_key, _load_cache, _save_cache ...` |
| `tools/ai/shared/llm_client.py` | `DeepSeekClient` | `BaseLLMClient` | `__init__, complete, complete_json, _extract_json, chat, stream ...` |
| `tools/ai/shared/llm_client.py` | `OllamaClient` | `BaseLLMClient` | `__init__, complete, complete_json, chat, stream, _format_messages` |
| `tools/ai/shared/llm_client.py` | `OpenAIClient` | `BaseLLMClient` | `__init__, complete, complete_json, chat, stream, _format_messages` |
| `tools/ai/shared/llm_client.py` | `LLMClient` | `—` | `__init__, _init_client, complete, complete_json, chat, stream ...` |
| `tools/ai/shared/logger.py` | `LogFormat` | `str, Enum` | `` |
| `tools/ai/shared/logger.py` | `LogDestination` | `str, Enum` | `` |
| `tools/ai/shared/logger.py` | `LoggerConfig` | `—` | `` |
| `tools/ai/shared/logger.py` | `LogEntry` | `—` | `` |
| `tools/ai/shared/logger.py` | `ConsoleFormatter` | `logging.Formatter` | `__init__, format` |
| `tools/ai/shared/logger.py` | `JSONFormatter` | `logging.Formatter` | `__init__, format, _redact` |
| `tools/ai/shared/logger.py` | `DetailedFormatter` | `logging.Formatter` | `__init__` |
| `tools/ai/shared/logger.py` | `BufferedHandler` | `logging.Handler` | `__init__, emit, flush, close` |
| `tools/ai/shared/logger.py` | `LoggerManager` | `—` | `__new__, __init__, _configure, _get_logging_level, _create_console_handler, _create_file_handler ...` |
| `tools/ai/shared/logger.py` | `LogContext` | `—` | `__init__, __enter__, __exit__, add` |
| `tools/ai/shared/logger.py` | `ContextFilter` | `logging.Filter` | `__init__, filter` |
| `tools/ai/shared/state_manager.py` | `StorageBackend` | `str, Enum` | `` |
| `tools/ai/shared/state_manager.py` | `CompressionType` | `str, Enum` | `` |
| `tools/ai/shared/state_manager.py` | `EncryptionType` | `str, Enum` | `` |
| `tools/ai/shared/state_manager.py` | `StateScope` | `str, Enum` | `` |
| `tools/ai/shared/state_manager.py` | `StateEntry` | `—` | `is_expired, touch` |
| `tools/ai/shared/state_manager.py` | `StateSnapshot` | `—` | `` |
| `tools/ai/shared/state_manager.py` | `StateConfig` | `—` | `` |
| `tools/ai/shared/state_manager.py` | `StorageBackendBase` | `—` | `__init__, load, save, close` |
| `tools/ai/shared/state_manager.py` | `JSONStorageBackend` | `StorageBackendBase` | `__init__, load, save` |
| `tools/ai/shared/state_manager.py` | `SQLiteStorageBackend` | `StorageBackendBase` | `__init__, _init_db, _get_connection, load, save, close` |
| `tools/ai/shared/state_manager.py` | `MemoryStorageBackend` | `StorageBackendBase` | `__init__, load, save` |
| `tools/ai/shared/state_manager.py` | `StateManager` | `—` | `__init__, _create_backend, _load, _ensure_loaded, _schedule_save, _auto_save ...` |
| `tools/ai/shared/state_manager.py` | `StateNamespace` | `—` | `__init__, _key, get, set, delete, exists ...` |
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
BaseAgent  →  InteractionAgent
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
BaseModel  →  AgentInput
BaseModel  →  AgentOutput
BaseModel  →  AgentExecutionRecord
ABC  →  MessageBus
MessageBus  →  DurableMessageBus
MessageBus  →  InMemoryMessageBus
MessageBus  →  KafkaMessageBus
MessageBus  →  PriorityMessageBus
MessageBus  →  RabbitMQMessageBus
MessageBus  →  RedisMessageBus
MessageBus  →  RequestReplyBus
MessageBus  →  TopicMessageBus
ABC  →  BaseChunker
BaseModel  →  ChunkingConfig
BaseModel  →  ChunkingResult
BaseChunker  →  RecursiveTextChunker
ABC  →  EmbeddingProvider
EmbeddingProvider  →  HashEmbeddingProvider
BaseModel  →  IngestionContext
Exception  →  IngestionError
IngestionError  →  InvalidDocumentError
IngestionError  →  UnsupportedMediaTypeError
IngestionError  →  ExtractionFailed
IngestionError  →  ParseFailed
IngestionError  →  ChunkingFailed
IngestionError  →  EmbeddingFailed
IngestionError  →  StorageFailed
IngestionError  →  FinalizationFailed
IngestionError  →  IngestionStepFailed
BaseModel  →  DocumentRecord
BaseModel  →  ChunkRecord
str  →  IngestionStatus
Enum  →  IngestionStatus
str  →  StorageLocation
Enum  →  StorageLocation
BaseModel  →  DocumentIngestionResult
str  →  ElementType
Enum  →  ElementType
str  →  BinaryEncoding
Enum  →  BinaryEncoding
str  →  CompressionMethod
Enum  →  CompressionMethod
BaseModel  →  BaseDocument
BaseModel  →  BinaryPayload
BinaryPayload  →  ChunkedBinaryPayload
str  →  EntityType
Enum  →  EntityType
CSDMObject  →  CSDMEntity
CSDMObject  →  CSDMCustomObject
CSDMObject  →  CSDMDictionary
CSDMObject  →  CSDMGroup
CSDMObject  →  PlotSettings
CSDMObject  →  CSDMLayout
CSDMObject  →  CSDMMaterial
CSDMObject  →  CSDMMLeaderStyle
CSDMObject  →  CSDMTableStyle
CSDMObject  →  CSDMImageDef
CSDMObject  →  CSDMUnderlayDef
CSDMObject  →  CSDMXref
BaseDocument  →  CSDMDocument
CSDMEntity  →  BodyEntity
CSDMEntity  →  Solid3DEntity
CSDMEntity  →  SurfaceEntity
CSDMObject  →  BaseEntity
AddReactorsMixin  →  BaseEntity
BaseEntity  →  CurveEntity
BaseEntity  →  SurfaceEntity
BaseEntity  →  SolidEntity
BaseEntity  →  TextBaseEntity
Enum  →  DimensionType
BaseEntity  →  DimensionBase
BaseEntity  →  BlockRefBase
CurveEntity  →  LineEntity
CurveEntity  →  CircleEntity
CurveEntity  →  ArcEntity
CurveEntity  →  EllipseEntity
CurveEntity  →  PolylineEntity
CurveEntity  →  LWPolylineEntity
CurveEntity  →  SplineEntity
CurveEntity  →  RayEntity
CurveEntity  →  XLineEntity
CurveEntity  →  Solid2DEntity
CurveEntity  →  Face3DEntity
CurveEntity  →  TraceEntity
CurveEntity  →  ShapeEntity
SolidEntity  →  RegionEntity
SolidEntity  →  BodyEntity
SolidEntity  →  Solid3DEntity
SurfaceEntity  →  SurfaceACISEntity
BaseEntity  →  HatchEntity
TextBaseEntity  →  TextEntity
TextBaseEntity  →  MTextEntity
CurveEntity  →  LeaderEntity
BaseEntity  →  MLeaderEntity
DimensionBase  →  DimensionEntity
BlockRefBase  →  BlockReference
BlockRefBase  →  MInsertEntity
TextBaseEntity  →  AttributeEntity
TextBaseEntity  →  AttributeDefEntity
BaseEntity  →  ImageEntity
BaseEntity  →  UnderlayEntity
BaseEntity  →  WipeoutEntity
BaseEntity  →  OLE2FrameEntity
BaseEntity  →  PointEntity
BaseEntity  →  MLineEntity
BaseEntity  →  ToleranceEntity
BaseEntity  →  FieldEntity
BaseEntity  →  MLeaderContentEntity
BaseEntity  →  TableEntity
BaseEntity  →  GeometricConstraintEntity
BaseEntity  →  DimensionalConstraintEntity
BaseEntity  →  DCFCustomEntity
CSDMObject  →  TableEntry
TableEntry  →  LayerEntry
CSDMObject  →  LayerTable
TableEntry  →  LinetypeEntry
CSDMObject  →  LinetypeTable
TableEntry  →  TextStyleEntry
CSDMObject  →  TextStyleTable
Enum  →  DimLUnit
TableEntry  →  DimStyleEntry
CSDMObject  →  DimStyleTable
TableEntry  →  UCSRecord
CSDMObject  →  UCSTable
TableEntry  →  ViewRecord
CSDMObject  →  ViewTable
TableEntry  →  VPortRecord
CSDMObject  →  VPortTable
TableEntry  →  AppIDEntry
CSDMObject  →  AppIDTable
TableEntry  →  BlockRecord
CSDMObject  →  BlockRecordTable
TableEntry  →  PlotStyleEntry
CSDMObject  →  PlotStyleTable
TableEntry  →  MaterialEntry
CSDMObject  →  MaterialTableDWG
CSDMObject  →  DimStyleOverrideTable
TableEntry  →  MLineStyle
CSDMObject  →  MLineStyleTable
TableEntry  →  CADTableStyle
CSDMObject  →  TableStyleTable
Enum  →  MLeaderTextAlign
TableEntry  →  MLeaderStyle
CSDMObject  →  MLeaderStyleTable
Enum  →  LightType
TableEntry  →  LightRecord
CSDMObject  →  LightTable
TableEntry  →  RenderEnvironment
CSDMObject  →  RenderEnvironmentTable
TableEntry  →  RenderSettings
CSDMObject  →  RenderSettingsTable
Enum  →  UnderlayType
TableEntry  →  UnderlayDefinition
CSDMObject  →  UnderlayTable
TableEntry  →  RasterImageDef
CSDMObject  →  RasterImageTable
TableEntry  →  PlotConfig
CSDMObject  →  PlotConfigTable
TableEntry  →  OLEObject
CSDMObject  →  OLETable
TableEntry  →  DataLink
CSDMObject  →  DataLinkTable
TableEntry  →  DCFTableEntry
CSDMObject  →  DCFCustomTable
str  →  DataNodeKind
Enum  →  DataNodeKind
str  →  ScalarType
Enum  →  ScalarType
BaseModel  →  DataValue
BaseModel  →  DataSchemaReference
BaseModel  →  DataDocumentCapabilities
BaseModel  →  DataNode
BaseDocument  →  DataDocument
DocumentBaseModel  →  WorkbookProperties
DocumentBaseModel  →  Relationship
DocumentBaseModel  →  RelationshipCollection
DocumentBaseModel  →  SharedStrings
DocumentBaseModel  →  SheetDimensions
DocumentBaseModel  →  WorksheetProperties
DocumentBaseModel  →  Cell
DocumentBaseModel  →  Row
DocumentBaseModel  →  Column
DocumentBaseModel  →  CellRange
CellRange  →  MergedCellRange
DocumentBaseModel  →  NamedRange
DocumentBaseModel  →  Worksheet
BaseDocument  →  Workbook
DocumentBaseModel  →  NumberFormat
DocumentBaseModel  →  NumberFormatCollection
Enum  →  FontUnderline
DocumentBaseModel  →  Font
DocumentBaseModel  →  FontCollection
Enum  →  PatternType
DocumentBaseModel  →  PatternFill
DocumentBaseModel  →  GradientStop
DocumentBaseModel  →  GradientFill
DocumentBaseModel  →  Fill
DocumentBaseModel  →  FillCollection
Enum  →  BorderStyle
DocumentBaseModel  →  BorderSide
DocumentBaseModel  →  Border
DocumentBaseModel  →  BorderCollection
Enum  →  HorizontalAlign
Enum  →  VerticalAlign
DocumentBaseModel  →  Alignment
DocumentBaseModel  →  Protection
DocumentBaseModel  →  CellFormat
DocumentBaseModel  →  CellFormatCollection
DocumentBaseModel  →  CellStyle
DocumentBaseModel  →  CellStyleCollection
DocumentBaseModel  →  DifferentialFormat
DocumentBaseModel  →  DifferentialFormatCollection
DocumentBaseModel  →  TableStyleElement
DocumentBaseModel  →  ExcelTableStyle
DocumentBaseModel  →  TableStyleCollection
DocumentBaseModel  →  Stylesheet
Enum  →  DynamicFilterType
Enum  →  FilterOperator
DocumentBaseModel  →  CustomFilter
DocumentBaseModel  →  Filters
DocumentBaseModel  →  FilterColumn
DocumentBaseModel  →  AutoFilter
DocumentBaseModel  →  TableColumn
DocumentBaseModel  →  ExcelTableRow
DocumentBaseModel  →  TableStyleInfo
DocumentBaseModel  →  Table
DocumentBaseModel  →  TableCollection
Enum  →  CFType
Enum  →  CFOperator
DocumentBaseModel  →  CFValueObject
DocumentBaseModel  →  ColorScale
DocumentBaseModel  →  DataBar
Enum  →  IconSetType
DocumentBaseModel  →  IconCriterion
DocumentBaseModel  →  IconSet
DocumentBaseModel  →  CFRule
DocumentBaseModel  →  ConditionalFormatting
DocumentBaseModel  →  ConditionalFormattingCollection
Enum  →  FormulaTokenType
DocumentBaseModel  →  FormulaToken
DocumentBaseModel  →  FormulaAST
DocumentBaseModel  →  SharedFormula
DocumentBaseModel  →  SharedFormulaCollection
DocumentBaseModel  →  DefinedName
DocumentBaseModel  →  DefinedNameCollection
DocumentBaseModel  →  ExternalReference
DocumentBaseModel  →  ExternalLink
DocumentBaseModel  →  ExternalLinkCollection
DocumentBaseModel  →  CellFormula
Enum  →  DataValidationType
Enum  →  DataValidationOperator
DocumentBaseModel  →  DataValidationRule
DocumentBaseModel  →  DataValidation
DocumentBaseModel  →  DataValidationCollection
DocumentBaseModel  →  Hyperlink
DocumentBaseModel  →  HyperlinkCollection
DocumentBaseModel  →  Author
DocumentBaseModel  →  CommentTextRun
DocumentBaseModel  →  CommentText
DocumentBaseModel  →  Comment
DocumentBaseModel  →  CommentCollection
DocumentBaseModel  →  ThreadedComment
DocumentBaseModel  →  ThreadedCommentCollection
DocumentBaseModel  →  SheetProperties
DocumentBaseModel  →  SheetProtection
Enum  →  Orientation
DocumentBaseModel  →  PageMargins
DocumentBaseModel  →  PageSetup
DocumentBaseModel  →  CalcChainEntry
DocumentBaseModel  →  CalculationChain
DocumentBaseModel  →  RichTextRun
DocumentBaseModel  →  RichText
DocumentBaseModel  →  PivotField
DocumentBaseModel  →  PivotCacheReference
DocumentBaseModel  →  PivotCache
DocumentBaseModel  →  PivotTable
DocumentBaseModel  →  PivotCacheCollection
DocumentBaseModel  →  PivotTableCollection
Exception  →  DocumentError
DocumentError  →  DocumentParseError
DocumentError  →  DocumentWriteError
DocumentError  →  DocumentValidationError
DocumentError  →  UnsupportedFormatError
DocumentError  →  BinaryEncodingError
DocumentError  →  StreamingError
DocumentError  →  RegistryError
DocumentError  →  CompressionError
DocumentValidationError  →  SchemaValidationError
DocumentError  →  ContentDetectionError
str  →  DocumentFormat
Enum  →  DocumentFormat
str  →  MediaContentKind
Enum  →  MediaContentKind
str  →  MediaRawType
Enum  →  MediaRawType
BaseModel  →  MediaType
str  →  DocumentStandard
Enum  →  DocumentStandard
str  →  MediaCategory
Enum  →  MediaCategory
BaseDocument  →  USDMDcoument
LogicalContent  →  LaTeXEnvironmentContent
LogicalContent  →  LaTeXCommandContent
LogicalContent  →  SemanticHTMLContent
LogicalContent  →  CanvasContent
ABC  →  FormatPlugin
BaseModel  →  ParseOptions
ABC  →  BaseDocumentParser
BaseDocumentParser  →  BinaryParser
pickle.Unpickler  →  RestrictedUnpickler
str  →  DOCXElementType
Enum  →  DOCXElementType
str  →  RunPropertyName
Enum  →  RunPropertyName
str  →  ParagraphAlignment
Enum  →  ParagraphAlignment
str  →  NumberingLevelSuffix
Enum  →  NumberingLevelSuffix
str  →  SectionType
Enum  →  SectionType
str  →  VerticalAlignment
Enum  →  VerticalAlignment
str  →  TextDirection
Enum  →  TextDirection
HTMLParser  →  HTMLDocumentParser
BaseDocumentParser  →  HtmlParser
BaseDocumentParser  →  JsonDocumentParser
BaseDocumentParser  →  LatexParser
Treeprocessor  →  MarkdownTreeProcessor
Extension  →  MarkdownExtension
BaseDocumentParser  →  MarkdownParser
Enum  →  ContentType
Enum  →  FontType
Enum  →  FontEncoding
Enum  →  FontLanguage
Enum  →  MetadataType
Enum  →  PDFVersion
Enum  →  PDFConformance
Exception  →  PDFMetadataError
Enum  →  PDFObjectType
Enum  →  PDFColorSpace
Enum  →  PDFLineCapStyle
Enum  →  PDFLineJoinStyle
Enum  →  PDFTextRenderingMode
Exception  →  PDFError
PDFError  →  PDFParseError
PDFError  →  PDFValidationError
ABC  →  PDFObject
PDFObject  →  PDFBoolean
PDFObject  →  PDFInteger
PDFObject  →  PDFReal
PDFObject  →  PDFString
PDFObject  →  PDFName
PDFObject  →  PDFArray
PDFObject  →  PDFDictionary
PDFObject  →  PDFStream
PDFObject  →  PDFNull
PDFObject  →  PDFReference
PDFObject  →  PDFPage
PDFObject  →  PDFCatalog
PDFObject  →  PDFInfo
Enum  →  StructuralElementType
Enum  →  TextDirection
Enum  →  Language
BaseParser  →  PDFParser
BaseDocumentParser  →  XmlDocumentParser
BaseDocumentParser  →  YamlDocumentParser
BaseModel  →  WriteOptions
ABC  →  BaseDocumentWriter
BaseDocumentWriter  →  BinaryWriter
BaseDocumentWriter  →  JsonDocumentWriter
BaseDocumentWriter  →  LatexWriter
Enum  →  AnnotationType
Enum  →  AnnotationBorderStyle
Enum  →  AnnotationFlag
Enum  →  EncryptionAlgorithm
IntFlag  →  PermissionFlag
Enum  →  FontStyle
Enum  →  FontEncoding
Enum  →  FontSubsetStrategy
Enum  →  OptimizationLevel
Enum  →  OutlineStyle
PDFObject  →  PDFDictionary
PDFObject  →  PDFStream
PDFObject  →  PDFPage
PDFObject  →  PDFCatalog
PDFObject  →  PDFInfo
WriteOptions  →  PDFWriteOptions
BaseDocumentWriter  →  PDFWriter
BaseDocumentWriter  →  XmlDocumentWriter
BaseDocumentWriter  →  YamlDocumentWriter
yaml.SafeDumper  →  CustomDumper
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
ABC  →  BaseStorage
CacheStorage  →  InMemoryCacheStorage
CacheStorage  →  RedisCacheStorage
BaseStorage  →  CacheStorage
ABC  →  CacheStorage
LogStorage  →  RSyslogStorage
LogStorage  →  SqlLogStorage
BaseStorage  →  LogStorage
ABC  →  LogStorage
GraphStorage  →  Neo4jAdapter
BaseStorage  →  GraphStorage
ABC  →  GraphStorage
KeyValueStorage  →  InMemoryKeyValueStorage
KeyValueStorage  →  RedisStorageAdapter
BaseStorage  →  KeyValueStorage
ABC  →  KeyValueStorage
ObjectStorage  →  LocalFileAdapter
ObjectStorage  →  MinioAdapter
ObjectStorage  →  S3Adapter
BaseStorage  →  ObjectStorage
ABC  →  ObjectStorage
PostgresStorageAdapter  →  MySQLStorageAdapter
RelationalStorage  →  PostgresStorageAdapter
PostgresStorageAdapter  →  SQLServerStorageAdapter
RelationalStorage  →  SQLiteStorageAdapter
BaseStorage  →  SQLStorage
BaseStorage  →  RelationalStorage
ABC  →  RelationalStorage
StreamStorage  →  KafkaStreamAdapter
StreamStorage  →  RedisStreamAdapter
BaseStorage  →  StreamStorage
ABC  →  StreamStorage
TimeSeriesStorage  →  InfluxDBStorageAdapter
BaseStorage  →  TimeSeriesStorage
ABC  →  TimeSeriesStorage
VectorDBAdapter  →  ChromaAdapter
VectorDBAdapter  →  FaissAdapter
VectorDBAdapter  →  InMemoryVectorStore
VectorDBAdapter  →  PineconeAdapter
VectorDBAdapter  →  QdrantAdapter
VectorDBAdapter  →  WeaviateAdapter
ABC  →  VectorDBAdapter
BaseStorage  →  VectorStorage
ABC  →  VectorStorage
AgentInput  →  SimpleInput
AgentOutput  →  SimpleOutput
BaseAgent  →  SimpleAgent
AgentInput  →  InputModel
AgentOutput  →  OutputModel
BaseAgent[InputModel, OutputModel]  →  EchoAgent
EchoAgent  →  FailingAgent
BaseOrchestrationBackend  →  DummyBackend
InteractionResult  →  Result
MessageBus  →  DummyMessageBus1
MessageBus  →  DummyMessageBus2
BaseOrchestrationBackend  →  DummyBackend
InteractionResult  →  Result
MessageBus  →  DummyMessageBus
str  →  ChunkType
Enum  →  ChunkType
str  →  ChunkGranularity
Enum  →  ChunkGranularity
str  →  Language
Enum  →  Language
ast.NodeVisitor  →  CodeChunkVisitor
str  →  DocChunkType
Enum  →  DocChunkType
str  →  DocFormat
Enum  →  DocFormat
str  →  DocSection
Enum  →  DocSection
str  →  SemanticChunkType
Enum  →  SemanticChunkType
str  →  ChunkingStrategy
Enum  →  ChunkingStrategy
str  →  SimilarityMetric
Enum  →  SimilarityMetric
int  →  BatchPriority
Enum  →  BatchPriority
str  →  BatchStatus
Enum  →  BatchStatus
str  →  CheckpointStrategy
Enum  →  CheckpointStrategy
str  →  CollectionType
Enum  →  CollectionType
str  →  DistanceMetric
Enum  →  DistanceMetric
str  →  IndexType
Enum  →  IndexType
EmbeddingFunction  →  OllamaEmbeddingFunction
str  →  EmbeddingModel
Enum  →  EmbeddingModel
str  →  EncodingStatus
Enum  →  EncodingStatus
str  →  PoolingStrategy
Enum  →  PoolingStrategy
str  →  IndexStatus
Enum  →  IndexStatus
str  →  SymbolType
Enum  →  SymbolType
str  →  DocIndexStatus
Enum  →  DocIndexStatus
str  →  DocType
Enum  →  DocType
str  →  APIVisibility
Enum  →  APIVisibility
str  →  APIElementType
Enum  →  APIElementType
str  →  DeprecationStatus
Enum  →  DeprecationStatus
str  →  StabilityLevel
Enum  →  StabilityLevel
ast.NodeVisitor  →  APIElementExtractor
str  →  NodeType
Enum  →  NodeType
str  →  ComplexityType
Enum  →  ComplexityType
str  →  CodeSmell
Enum  →  CodeSmell
ast.NodeVisitor  →  MetricsVisitor
ast.NodeVisitor  →  ImportExtractor
str  →  ImportType
Enum  →  ImportType
str  →  DependencyType
Enum  →  DependencyType
str  →  GraphFormat
Enum  →  GraphFormat
ast.NodeVisitor  →  ImportExtractor
str  →  ScanLevel
Enum  →  ScanLevel
str  →  SymbolType
Enum  →  SymbolType
str  →  FileType
Enum  →  FileType
str  →  ProjectType
Enum  →  ProjectType
ast.NodeVisitor  →  SymbolExtractor
ast.NodeVisitor  →  DependencyExtractor
str  →  HTTPMethod
Enum  →  HTTPMethod
str  →  APIResponseStatus
Enum  →  APIResponseStatus
str  →  AuthMethod
Enum  →  AuthMethod
BaseModel  →  APIResponse
BaseModel  →  WorkflowRequest
BaseModel  →  WorkflowResponse
BaseModel  →  AnalyzeRequest
BaseModel  →  GenerateRequest
BaseModel  →  ValidateRequest
BaseModel  →  HealthResponse
EntryPointConfig  →  APIConfig
BaseEntryPoint  →  APIEntryPoint
str  →  EntryPointType
Enum  →  EntryPointType
str  →  ExecutionMode
Enum  →  ExecutionMode
int  →  ExitCode
Enum  →  ExitCode
ABC  →  BaseEntryPoint
BaseEntryPoint  →  ExampleEntryPoint
str  →  OutputFormat
Enum  →  OutputFormat
EntryPointConfig  →  CLIConfig
BaseEntryPoint  →  CLIEntryPoint
str  →  ProtocolType
Enum  →  ProtocolType
str  →  MessageType
Enum  →  MessageType
str  →  CommandScope
Enum  →  CommandScope
BaseModel  →  IDEMessage
BaseModel  →  IDERequest
BaseModel  →  IDEResponse
BaseModel  →  Diagnostic
BaseModel  →  CodeAction
EntryPointConfig  →  IDEPluginConfig
BaseEntryPoint  →  IDEPluginEntryPoint
str  →  ClassType
Enum  →  ClassType
str  →  MethodType
Enum  →  MethodType
str  →  Visibility
Enum  →  Visibility
str  →  DocstringStyle
Enum  →  DocstringStyle
str  →  DocstringSection
Enum  →  DocstringSection
str  →  DocstringQuality
Enum  →  DocstringQuality
ast.NodeVisitor  →  ContextExtractor
str  →  FunctionType
Enum  →  FunctionType
str  →  ReturnStrategy
Enum  →  ReturnStrategy
str  →  ErrorHandling
Enum  →  ErrorHandling
str  →  Complexity
Enum  →  Complexity
str  →  ModuleType
Enum  →  ModuleType
str  →  ModuleTemplate
Enum  →  ModuleTemplate
str  →  PerformanceTestType
Enum  →  PerformanceTestType
str  →  MetricsType
Enum  →  MetricsType
str  →  LoadPattern
Enum  →  LoadPattern
str  →  AssertionType
Enum  →  AssertionType
str  →  TestFramework
Enum  →  TestFramework
str  →  TestType
Enum  →  TestType
str  →  MockStrategy
Enum  →  MockStrategy
str  →  AssertionStyle
Enum  →  AssertionStyle
ast.NodeVisitor  →  TestTargetAnalyzer
str  →  DesignPrinciple
Enum  →  DesignPrinciple
str  →  ParameterKind
Enum  →  ParameterKind
str  →  ReturnStyle
Enum  →  ReturnStyle
str  →  ErrorStrategy
Enum  →  ErrorStrategy
str  →  ContractType
Enum  →  ContractType
str  →  ParameterKind
Enum  →  ParameterKind
str  →  ContractVisibility
Enum  →  ContractVisibility
str  →  ErrorHandling
Enum  →  ErrorHandling
str  →  DependencyType
Enum  →  DependencyType
str  →  DependencyDirection
Enum  →  DependencyDirection
str  →  LayerType
Enum  →  LayerType
str  →  DependencyRule
Enum  →  DependencyRule
str  →  ModuleType
Enum  →  ModuleType
str  →  ArchitecturePattern
Enum  →  ArchitecturePattern
str  →  Visibility
Enum  →  Visibility
str  →  ComponentRole
Enum  →  ComponentRole
str  →  StubType
Enum  →  StubType
str  →  ImplementationHint
Enum  →  ImplementationHint
str  →  RefinementScope
Enum  →  RefinementScope
str  →  ChangeType
Enum  →  ChangeType
ABC  →  BaseRefiner
ABC  →  SafetyCheck
str  →  FeedbackType
Enum  →  FeedbackType
str  →  FeedbackSeverity
Enum  →  FeedbackSeverity
str  →  LearningMode
Enum  →  LearningMode
str  →  PatternType
Enum  →  PatternType
SafetyCheck  →  FunctionalityPreserver
ast.NodeVisitor  →  SignatureVisitor
str  →  ImpactSeverity
Enum  →  ImpactSeverity
str  →  ImpactType
Enum  →  ImpactType
str  →  ChangeCategory
Enum  →  ChangeCategory
ast.NodeVisitor  →  SymbolVisitor
str  →  RefinementStrategy
Enum  →  RefinementStrategy
str  →  ErrorCategory
Enum  →  ErrorCategory
str  →  RefinementPhase
Enum  →  RefinementPhase
ast.NodeVisitor  →  ComplexityVisitor
SafetyCheck  →  ScopeManager
ast.NodeVisitor  →  SymbolVisitor
ast.NodeVisitor  →  ImportVisitor
Enum  →  AgentStatus
Enum  →  AgentType
Enum  →  Capability
Enum  →  BottleneckType
Enum  →  Severity
Enum  →  MetricType
Enum  →  Aggregation
Enum  →  ReportFormat
Enum  →  ReportType
Enum  →  SkillLevel
Enum  →  SkillCategory
Enum  →  GapSeverity
Enum  →  WorkflowStatus
Enum  →  StepStatus
Enum  →  OrchestrationStatus
Enum  →  TaskPriority
ABC  →  BaseOrchestrator
Enum  →  EvolutionType
Enum  →  EvolutionSeverity
Enum  →  ConfigFormat
Enum  →  ChangeType
Enum  →  DocType
Enum  →  UpdateTrigger
Enum  →  ExampleType
Enum  →  ExampleStatus
Enum  →  TestType
Enum  →  TestStatus
Enum  →  ContextScope
Enum  →  AccessMode
Enum  →  VariableType
Enum  →  EventType
Enum  →  EventPriority
Enum  →  DeliveryMode
Enum  →  AssignmentStrategy
Enum  →  AssignmentStatus
Enum  →  FeedbackType
Enum  →  FeedbackSeverity
Enum  →  FeedbackStatus
Enum  →  SkillCategory
Enum  →  SkillType
Enum  →  ProficiencyLevel
Enum  →  SkillValidationStatus
Enum  →  WorkItemType
Enum  →  QueueType
Enum  →  WorkItemStatus
Enum  →  WorkItemPriority
Enum  →  StageType
Enum  →  ExecutionStrategy
Enum  →  FailurePolicy
Enum  →  ExecutionStatus
Enum  →  StageExecutionStatus
Enum  →  SessionType
Enum  →  SessionStatus
Enum  →  SessionAuthLevel
Enum  →  PersistenceBackend
Enum  →  SessionCapability
Enum  →  SessionIntegration
Enum  →  WorkflowStatus
Enum  →  TaskStatus
Enum  →  TaskType
str  →  DependencyType
Enum  →  DependencyType
str  →  Severity
Enum  →  Severity
str  →  IssueType
Enum  →  IssueType
str  →  TaskStatus
Enum  →  TaskStatus
str  →  EpicStatus
Enum  →  EpicStatus
str  →  Priority
Enum  →  Priority
str  →  HealthStatus
Enum  →  HealthStatus
str  →  TaskComplexity
Enum  →  TaskComplexity
str  →  TaskCategory
Enum  →  TaskCategory
str  →  DependencyType
Enum  →  DependencyType
str  →  ErrorCategory
Enum  →  ErrorCategory
str  →  ErrorSeverity
Enum  →  ErrorSeverity
str  →  RootCauseType
Enum  →  RootCauseType
str  →  ConfidenceLevel
Enum  →  ConfidenceLevel
str  →  VariableScope
Enum  →  VariableScope
str  →  VariableState
Enum  →  VariableState
str  →  ExecutionState
Enum  →  ExecutionState
str  →  TraceEvent
Enum  →  TraceEvent
str  →  FrameType
Enum  →  FrameType
str  →  ErrorCategory
Enum  →  ErrorCategory
str  →  Severity
Enum  →  Severity
Enum  →  APIFramework
Enum  →  HttpMethod
Enum  →  AuthType
Enum  →  DiagramFormat
Enum  →  ArchitectureLevel
Enum  →  DocumentationStyle
Enum  →  ChangeType
Enum  →  VersionBump
str  →  CoverageLevel
Enum  →  CoverageLevel
str  →  CoverageType
Enum  →  CoverageType
str  →  GapSeverity
Enum  →  GapSeverity
str  →  GapCategory
Enum  →  GapCategory
str  →  MutationOperator
Enum  →  MutationOperator
str  →  MutationStatus
Enum  →  MutationStatus
str  →  MutationCategory
Enum  →  MutationCategory
ast.NodeTransformer  →  MutationGenerator
str  →  TestStatus
Enum  →  TestStatus
str  →  TestFramework
Enum  →  TestFramework
str  →  TestSelectionStrategy
Enum  →  TestSelectionStrategy
str  →  ExecutionMode
Enum  →  ExecutionMode
str  →  FailureCategory
Enum  →  FailureCategory
str  →  ChangeType
Enum  →  ChangeType
str  →  SemVerImpact
Enum  →  SemVerImpact
str  →  CompatibilityStatus
Enum  →  CompatibilityStatus
str  →  LayerType
Enum  →  LayerType
str  →  DependencyRule
Enum  →  DependencyRule
str  →  RuleSeverity
Enum  →  RuleSeverity
str  →  PatternType
Enum  →  PatternType
str  →  CompatibilityStatus
Enum  →  CompatibilityStatus
str  →  PythonVersion
Enum  →  PythonVersion
str  →  IssueSeverity
Enum  →  IssueSeverity
str  →  FeatureCategory
Enum  →  FeatureCategory
ast.NodeVisitor  →  SyntaxFeatureDetector
ast.NodeVisitor  →  ImportVisitor
str  →  ComplexityMetric
Enum  →  ComplexityMetric
str  →  Severity
Enum  →  Severity
str  →  Scope
Enum  →  Scope
ast.NodeVisitor  →  ComplexityAnalyzer
str  →  CoverageType
Enum  →  CoverageType
str  →  CoverageFormat
Enum  →  CoverageFormat
str  →  Severity
Enum  →  Severity
str  →  DependencySource
Enum  →  DependencySource
str  →  DependencyType
Enum  →  DependencyType
str  →  Severity
Enum  →  Severity
str  →  VulnerabilitySeverity
Enum  →  VulnerabilitySeverity
str  →  LicenseCompatibility
Enum  →  LicenseCompatibility
str  →  DocstringStyle
Enum  →  DocstringStyle
str  →  DocstringSection
Enum  →  DocstringSection
str  →  Severity
Enum  →  Severity
str  →  EntityType
Enum  →  EntityType
ast.NodeVisitor  →  DocstringVisitor
str  →  ImportType
Enum  →  ImportType
str  →  Severity
Enum  →  Severity
str  →  ImportGroup
Enum  →  ImportGroup
ast.NodeVisitor  →  ImportVisitor
ast.NodeVisitor  →  NameCollector
str  →  MypyErrorCode
Enum  →  MypyErrorCode
str  →  Severity
Enum  →  Severity
str  →  MypyErrorCategory
Enum  →  MypyErrorCategory
str  →  NamingConvention
Enum  →  NamingConvention
str  →  EntityType
Enum  →  EntityType
str  →  Severity
Enum  →  Severity
str  →  SpellcheckLanguage
Enum  →  SpellcheckLanguage
ast.NodeVisitor  →  NamingValidator
ast.NodeVisitor  →  SpellcheckValidator
str  →  PerformanceIssueType
Enum  →  PerformanceIssueType
str  →  Severity
Enum  →  Severity
str  →  ComplexityClass
Enum  →  ComplexityClass
ast.NodeVisitor  →  ComplexityAnalyzer
ast.NodeVisitor  →  PerformanceIssueDetector
str  →  TestStatus
Enum  →  TestStatus
str  →  TestOutcome
Enum  →  TestOutcome
str  →  Severity
Enum  →  Severity
str  →  RuffRuleCategory
Enum  →  RuffRuleCategory
str  →  Severity
Enum  →  Severity
str  →  FixAvailability
Enum  →  FixAvailability
str  →  SecuritySeverity
Enum  →  SecuritySeverity
str  →  VulnerabilityType
Enum  →  VulnerabilityType
str  →  SecurityCategory
Enum  →  SecurityCategory
str  →  Confidence
Enum  →  Confidence
ast.NodeVisitor  →  SecurityVisitor
str  →  ConfigFormat
Enum  →  ConfigFormat
str  →  LogLevel
Enum  →  LogLevel
str  →  Environment
Enum  →  Environment
str  →  LLMProvider
Enum  →  LLMProvider
str  →  GitStatus
Enum  →  GitStatus
str  →  ChangeType
Enum  →  ChangeType
str  →  MergeStrategy
Enum  →  MergeStrategy
str  →  CommitType
Enum  →  CommitType
str  →  MessageRole
Enum  →  MessageRole
str  →  ResponseFormat
Enum  →  ResponseFormat
str  →  FinishReason
Enum  →  FinishReason
BaseLLMClient  →  DeepSeekClient
BaseLLMClient  →  OllamaClient
BaseLLMClient  →  OpenAIClient
str  →  LogFormat
Enum  →  LogFormat
str  →  LogDestination
Enum  →  LogDestination
logging.Formatter  →  ConsoleFormatter
logging.Formatter  →  JSONFormatter
logging.Formatter  →  DetailedFormatter
logging.Handler  →  BufferedHandler
logging.Filter  →  ContextFilter
str  →  StorageBackend
Enum  →  StorageBackend
str  →  CompressionType
Enum  →  CompressionType
str  →  EncryptionType
Enum  →  EncryptionType
str  →  StateScope
Enum  →  StateScope
StorageBackendBase  →  JSONStorageBackend
StorageBackendBase  →  SQLiteStorageBackend
StorageBackendBase  →  MemoryStorageBackend
```

---

### کلاس‌های Abstract / Interface

- **`MessageBus`** (`engines/buses/base_message_bus.py`)
  - متدها: `publish`, `subscribe`, `unsubscribe`, `start`, `stop`
- **`BaseChunker`** (`engines/document/chunking/base.py`)
  - متدها: `chunk_document`
- **`EmbeddingProvider`** (`engines/document/embedding/base.py`)
  - متدها: `embed_texts`, `embed_query`
- **`FormatPlugin`** (`engines/document/models/usdm_models.py`)
  - متدها: `to_usdm`, `from_usdm`
- **`BaseDocumentParser`** (`engines/document/parsers/base.py`)
  - متدها: `parse_bytes`, `parse_path`, `parse_stream`, `supports_extension`, `iter_supported_extensions`
- **`PDFObject`** (`engines/document/parsers/pdf_parser/pdf_objects.py`)
  - متدها: `to_pdf`, `get_type`, `to_dict`, `__str__`
- **`BaseDocumentWriter`** (`engines/document/writers/base.py`)
  - متدها: `__init__`, `write_stream`, `write`, `write_to_file`, `get_supported_media_types`, `get_supported_extensions`
- **`BaseOrchestrationBackend`** (`engines/interaction/backends/base_backend.py`)
  - متدها: `execute`
- **`BaseLLM`** (`engines/rag/llm/base_llm.py`)
  - متدها: `ainvoke`, `astream`
- **`BaseReranker`** (`engines/rag/reranking/base_reranker.py`)
  - متدها: `rerank`
- **`BaseResearchAgent`** (`engines/rag/research/base_research_agent.py`)
  - متدها: `run`
- **`TelemetryEvent`** (`engines/rag/research/observability/telemetry.py`)
  - متدها: `__init__`, `to_dict`
- **`Telemetry`** (`engines/rag/research/observability/telemetry.py`)
  - متدها: `__init__`, `emit`
- **`BaseSummarizer`** (`engines/rag/research/summarization/base_summarizer.py`)
  - متدها: `summarize`
- **`BaseRetriever`** (`engines/rag/retrieval/base_retriever.py`)
  - متدها: `search`
- **`BaseTrainer`** (`engines/rag/trainer/base_trainer.py`)
  - متدها: `train`
- **`BaseStorage`** (`engines/storage/base_storage.py`)
  - متدها: `__init__`, `is_connected`, `connect`, `disconnect`, `health`, `ensure_connected`, `__aenter__`, `__aexit__`
- **`CacheStorage`** (`engines/storage/cache/base.py`)
  - متدها: `set`, `get`, `delete`, `exists`, `list_keys`, `invalidate`, `clear`
- **`LogStorage`** (`engines/storage/event_log/base.py`)
  - متدها: `log_agent_execution`, `list_agent_logs`, `get_agent_log`, `log_event`, `list_events`, `get_event`
- **`GraphStorage`** (`engines/storage/graph/base.py`)
  - متدها: `add_node`, `add_edge`, `query`
- **`KeyValueStorage`** (`engines/storage/key_value/base.py`)
  - متدها: `set`, `get`, `delete`, `exists`, `list_keys`
- **`ObjectStorage`** (`engines/storage/object/base.py`)
  - متدها: `put`, `get`, `delete`, `exists`, `generate_url`
- **`RelationalStorage`** (`engines/storage/relational/base.py`)
  - متدها: `execute`, `fetch_one`, `fetch_all`
- **`StreamStorage`** (`engines/storage/stream/base.py`)
  - متدها: `publish`, `consume`
- **`TimeSeriesStorage`** (`engines/storage/timeseries/base.py`)
  - متدها: `write`, `query`
- **`VectorDBAdapter`** (`engines/storage/vector/base.py`)
  - متدها: `create_index`, `upsert`, `batch_upsert`, `query`, `delete`, `search`, `add_embeddings`, `delete_embeddings`
- **`VectorStorage`** (`engines/storage/vector/base.py`)
  - متدها: `upsert`, `delete`, `query`
- **`BaseEntryPoint`** (`tools/ai/entry_points/base_entry_point.py`)
  - متدها: `__init__`, `_get_default_config`, `run`, `run_async`, `_execute_with_retry`, `_execute_async_with_retry`, `execute`, `parse_arguments`, `_create_argument_parser`, `load_configuration`, `setup`, `setup_async`, `validate`, `execute_async`, `teardown`, `teardown_async`, `shutdown`, `shutdown_async`, `_setup_logging`, `_on_shutdown_signal`, `create_workflow_context`, `run_workflow`, `run_workflow_async`, `get_metrics`, `health_check`, `request_shutdown`, `is_shutdown_requested`, `create_success_result`, `create_error_result`, `main`
- **`BaseRefiner`** (`tools/ai/generation/refiners/base_refiner.py`)
  - متدها: `__init__`, `refine`, `can_handle`, `get_priority`
- **`SafetyCheck`** (`tools/ai/generation/refiners/base_refiner.py`)
  - متدها: `check`
- **`BaseOrchestrator`** (`tools/ai/orchestration/base_orchestrator.py`)
  - متدها: `__init__`, `_register_as_agent`, `_setup_event_handlers`, `_start_scheduler`, `_process_task_queue`, `_submit_task`, `_select_agent_for_task`, `_execute_task`, `_complete_task`, `submit_task`, `start_workflow`, `_schedule_workflow_tasks`, `get_task_status`, `get_workflow_status`, `cancel_task`, `cancel_workflow`, `_check_stalled_tasks`, `_update_health`, `_handle_task_completed_event`, `_handle_task_failed_event`, `_handle_workflow_completed_event`, `_handle_workflow_failed_event`, `_handle_agent_status_event`, `_reassign_agent_tasks`, `_load_state`, `_save_state`, `on_task_complete`, `on_workflow_complete`, `on_error`, `_notify_task_complete`, `_notify_task_failed`, `_notify_workflow_complete`, `_notify_workflow_failed`, `get_metrics`, `pause`, `resume`, `stop`, `get_capabilities`, `handle_custom_event`, `scheduler_loop`

---

## 🔍 تحلیل مشکلات احتمالی

### ⚠️ خطاهای Parse
- `engines/document/parsers/docx_parser/docx_parser.py`: SyntaxError: '(' was never closed (docx_parser.py, line 1393)
- `engines/document/writers/html_writer.py`: SyntaxError: unexpected indent (html_writer.py, line 1)
- `engines/document/writers/markdown_writer.py`: SyntaxError: unterminated f-string literal (detected at line 199) (markdown_writer.py, line 199)

### 🔴 کلاس‌های بزرگ (بیش از ۱۵ متد — نشانه نقض SRP)
- `DOCXExtractor` در `engines/document/parsers/docx_parser/docx_extractor.py` — 64 متد
- `DOCXImageExtractor` در `engines/document/parsers/docx_parser/docx_image_extractor.py` — 18 متد
- `OMMLParser` در `engines/document/parsers/docx_parser/docx_math_parser.py` — 28 متد
- `DocxUtils` در `engines/document/parsers/docx_parser/docx_utils.py` — 36 متد
- `HTMLDocumentParser` در `engines/document/parsers/html_parser.py` — 30 متد
- `LatexParser` در `engines/document/parsers/latex_parser.py` — 35 متد
- `ContentExtractor` در `engines/document/parsers/pdf_parser/content_extractor.py` — 27 متد
- `FontHandler` در `engines/document/parsers/pdf_parser/font_handler.py` — 20 متد
- `PDFMetadataExtractor` در `engines/document/parsers/pdf_parser/metadata_extractor.py` — 23 متد
- `PDFParser` در `engines/document/parsers/pdf_parser.py` — 18 متد
- `LatexWriter` در `engines/document/writers/latex_writer.py` — 24 متد
- `AnnotationWriter` در `engines/document/writers/pdf_writer/annotation_writer.py` — 27 متد
- `PDFEncryptor` در `engines/document/writers/pdf_writer/encryption.py` — 30 متد
- `FontManager` در `engines/document/writers/pdf_writer/font_manager.py` — 31 متد
- `MetadataWriter` در `engines/document/writers/pdf_writer/metadata_writer.py` — 18 متد
- `PDFOptimizer` در `engines/document/writers/pdf_writer/optimizer.py` — 33 متد
- `OutlineBuilder` در `engines/document/writers/pdf_writer/outline_builder.py` — 17 متد
- `PDFWriter` در `engines/document/writers/pdf_writer.py` — 28 متد
- `CodeChunkVisitor` در `tools/ai/analysis/chunkers/code_chunker.py` — 18 متد
- `CodeChunker` در `tools/ai/analysis/chunkers/code_chunker.py` — 26 متد
- `DocChunker` در `tools/ai/analysis/chunkers/doc_chunker.py` — 22 متد
- `SemanticChunker` در `tools/ai/analysis/chunkers/semantic_chunker.py` — 28 متد
- `BatchEncoder` در `tools/ai/analysis/encoders/batch_encoder.py` — 27 متد
- `EmbeddingStore` در `tools/ai/analysis/encoders/embedding_store.py` — 31 متد
- `OllamaEncoder` در `tools/ai/analysis/encoders/ollama_encoder.py` — 29 متد
- `CodeIndexer` در `tools/ai/analysis/indexers/code_indexer.py` — 24 متد
- `DocIndexer` در `tools/ai/analysis/indexers/doc_indexer.py` — 31 متد
- `APIElementExtractor` در `tools/ai/analysis/scanners/api_surface_extractor.py` — 18 متد
- `APISurfaceExtractor` در `tools/ai/analysis/scanners/api_surface_extractor.py` — 20 متد
- `MetricsVisitor` در `tools/ai/analysis/scanners/ast_analyzer.py` — 28 متد
- `ASTAnalyzer` در `tools/ai/analysis/scanners/ast_analyzer.py` — 17 متد
- `ImportGraphAnalyzer` در `tools/ai/analysis/scanners/import_graph.py` — 36 متد
- `SymbolExtractor` در `tools/ai/analysis/scanners/project_scanner.py` — 17 متد
- `ProjectScanner` در `tools/ai/analysis/scanners/project_scanner.py` — 27 متد
- `APIEntryPoint` در `tools/ai/entry_points/api_entry.py` — 45 متد
- `BaseEntryPoint` در `tools/ai/entry_points/base_entry_point.py` — 30 متد
- `CLIEntryPoint` در `tools/ai/entry_points/cli_entry.py` — 87 متد
- `IDEPluginEntryPoint` در `tools/ai/entry_points/ide_plugin_entry.py` — 47 متد
- `ClassCodeGenerator` در `tools/ai/generation/generators/class_generator.py` — 16 متد
- `DocstringFormatter` در `tools/ai/generation/generators/docstring_generator.py` — 17 متد
- `DocstringGenerator` در `tools/ai/generation/generators/docstring_generator.py` — 20 متد
- `ModuleGenerator` در `tools/ai/generation/generators/module_generator.py` — 21 متد
- `TestGenerator` در `tools/ai/generation/generators/test_generator.py` — 17 متد
- `ContractCodeGenerator` در `tools/ai/generation/planners/contract_generator.py` — 18 متد
- `ModuleArchitect` در `tools/ai/generation/planners/module_architect.py` — 23 متد
- `StubCodeGenerator` در `tools/ai/generation/planners/skeleton_generator.py` — 16 متد
- `SkeletonGenerator` در `tools/ai/generation/planners/skeleton_generator.py` — 17 متد
- `FeedbackLoop` در `tools/ai/generation/refiners/feedback_loop.py` — 22 متد
- `FunctionalityPreserver` در `tools/ai/generation/refiners/functionality_preserver.py` — 17 متد
- `ChangeDetector` در `tools/ai/generation/refiners/impact_analyzer.py` — 16 متد
- `ImpactCalculator` در `tools/ai/generation/refiners/impact_analyzer.py` — 26 متد
- `ScopeManager` در `tools/ai/generation/refiners/scope_manager.py` — 18 متد
- `AgentRegistry` در `tools/ai/orchestration/agent_registry.py` — 32 متد
- `BottleneckDetector` در `tools/ai/orchestration/analytics/bottleneck_detector.py` — 21 متد
- `PerformanceTracker` در `tools/ai/orchestration/analytics/performance_tracker.py` — 30 متد
- `ReportGenerator` در `tools/ai/orchestration/analytics/report_generator.py` — 29 متد
- `SkillGapAnalyzer` در `tools/ai/orchestration/analytics/skill_gap_analyzer.py` — 29 متد
- `WorkflowMetricsCollector` در `tools/ai/orchestration/analytics/workflow_metrics_collector.py` — 33 متد
- `BaseOrchestrator` در `tools/ai/orchestration/base_orchestrator.py` — 40 متد
- `CoEvolutionEngine` در `tools/ai/orchestration/co_evolution/co_evolution_engine.py` — 35 متد
- `ConfigUpdater` در `tools/ai/orchestration/co_evolution/config_updater.py` — 32 متد
- `DocUpdater` در `tools/ai/orchestration/co_evolution/doc_updater.py` — 29 متد
- `ExampleUpdater` در `tools/ai/orchestration/co_evolution/example_updater.py` — 27 متد
- `TestUpdater` در `tools/ai/orchestration/co_evolution/test_updater.py` — 29 متد
- `ContextManager` در `tools/ai/orchestration/context_manager.py` — 27 متد
- `EventBus` در `tools/ai/orchestration/event_bus.py` — 33 متد
- `AssignmentEngine` در `tools/ai/orchestration/human_task/assignment_engine.py` — 27 متد
- `FeedbackCollector` در `tools/ai/orchestration/human_task/feedback_collector.py` — 31 متد
- `SkillRegistry` در `tools/ai/orchestration/human_task/skill_registry.py` — 31 متد
- `WorkQueue` در `tools/ai/orchestration/human_task/work_queue.py` — 30 متد
- `PipelineBuilder` در `tools/ai/orchestration/pipeline_builder.py` — 49 متد
- `PipelineExecutor` در `tools/ai/orchestration/pipeline_executer.py` — 46 متد
- `SessionManager` در `tools/ai/orchestration/session/session_manager.py` — 38 متد
- `SessionPersistence` در `tools/ai/orchestration/session/session_persistence.py` — 26 متد
- `WorkflowEngine` در `tools/ai/orchestration/workflow_engine.py` — 47 متد
- `WorkflowExecutor` در `tools/ai/orchestration/workflow_executor.py` — 21 متد
- `DependencyAnalyzer` در `tools/ai/planning/dependency_analyzer.py` — 32 متد
- `ProgressTracker` در `tools/ai/planning/progress_tracker.py` — 35 متد
- `TaskDecomposer` در `tools/ai/planning/task_decomposer.py` — 31 متد
- `RootCauseAnalyzer` در `tools/ai/quality/debuggers/error_analyzer.py` — 20 متد
- `RuntimeInspector` در `tools/ai/quality/debuggers/runtime_inspector.py` — 30 متد
- `APIDocGenerator` در `tools/ai/quality/documenters/api_doc_generator.py` — 26 متد
- `ArchitectureDocGenerator` در `tools/ai/quality/documenters/architecture_doc.py` — 42 متد
- `GapDetector` در `tools/ai/quality/testers/coverage_analyzer.py` — 17 متد
- `MutationTester` در `tools/ai/quality/testers/mutation_tester.py` — 18 متد
- `TestRunner` در `tools/ai/quality/testers/test_runner.py` — 22 متد
- `SyntaxFeatureDetector` در `tools/ai/quality/validators/compatibility_validator.py` — 21 متد
- `CompatibilityValidator` در `tools/ai/quality/validators/compatibility_validator.py` — 19 متد
- `ComplexityAnalyzer` در `tools/ai/quality/validators/complexity_validator.py` — 29 متد
- `ComplexityValidator` در `tools/ai/quality/validators/complexity_validator.py` — 16 متد
- `CoverageValidator` در `tools/ai/quality/validators/coverage_validator.py` — 17 متد
- `DependencyValidator` در `tools/ai/quality/validators/dependency_validator.py` — 18 متد
- `ImportVisitor` در `tools/ai/quality/validators/import_validator.py` — 16 متد
- `MypyValidator` در `tools/ai/quality/validators/mypy_validator.py` — 16 متد
- `ComplexityAnalyzer` در `tools/ai/quality/validators/performance_validator.py` — 18 متد
- `PytestValidator` در `tools/ai/quality/validators/pytest_validator.py` — 17 متد
- `RuffValidator` در `tools/ai/quality/validators/ruff_validator.py` — 17 متد
- `SecurityVisitor` در `tools/ai/quality/validators/security_validator.py` — 20 متد
- `Config` در `tools/ai/shared/config.py` — 34 متد
- `GitUtils` در `tools/ai/shared/git_utils.py` — 60 متد
- `LoggerManager` در `tools/ai/shared/logger.py` — 16 متد
- `StateManager` در `tools/ai/shared/state_manager.py` — 40 متد

### 🟡 فایل‌های خالی یا فقط شامل import
- `config/settings.py` [22 lines]
- `engines/agents/base_agents/base_research_agent/metadata.py` [0 lines]
- `engines/agents/base_agents/base_research_agent/prompts.py` [0 lines]
- `engines/agents/base_agents/base_research_agent/rag_config.py` [0 lines]
- `engines/document/parsers/cad_parser/csdm_loader.py` [641 lines]
- `engines/document/parsers/cad_parser/csdm_parser.py` [74 lines]
- `engines/document/parsers/cad_parser/csdm_relationships.py` [281 lines]
- `engines/document/parsers/cad_parser/oda_bridge.py` [273 lines]
- `engines/document/parsers/cad_parser.py` [133 lines]
- `engines/document/parsers/csv_parser.py` [535 lines]
- `engines/document/parsers/docx_parser.py` [218 lines]
- `engines/document/parsers/excel_parser.py` [307 lines]
- `engines/document/parsers/excel_parser0-notvalid.py` [1487 lines]
- `engines/document/utils/docx_utils.py` [0 lines]
- `engines/document/utils/ooxml_constants.py` [0 lines]
- `engines/document/utils/xml_parser.py` [0 lines]
- `engines/document/utils/zip_handler.py` [0 lines]
- `engines/document/writers/cad_writer/acis_writer.py` [91 lines]
- `engines/document/writers/cad_writer/base_context.py` [77 lines]
- `engines/document/writers/cad_writer/block_writer.py` [124 lines]
- `engines/document/writers/cad_writer/cad_writer.py` [129 lines]
- `engines/document/writers/cad_writer/dwg_builder.py` [177 lines]
- `engines/document/writers/cad_writer/entity_writer.py` [360 lines]
- `engines/document/writers/cad_writer/finalizer.py` [138 lines]
- `engines/document/writers/cad_writer/non_graphical_writer.py` [259 lines]
- `engines/document/writers/cad_writer/reactor_writer.py` [67 lines]
- `engines/document/writers/cad_writer/table_writer.py` [310 lines]
- `engines/document/writers/cad_writer/xdata_writer.py` [81 lines]
- `engines/document/writers/cad_writer.py` [269 lines]
- `engines/document/writers/csv_writer.py` [298 lines]
- `engines/document/writers/docx_writer/docx_builder.py` [0 lines]
- `engines/document/writers/docx_writer/docx_image_handler.py` [0 lines]
- `engines/document/writers/docx_writer/docx_math_writer.py` [0 lines]
- `engines/document/writers/docx_writer/docx_style_builder.py` [0 lines]
- `engines/document/writers/docx_writer/docx_table_builder.py` [0 lines]
- `engines/document/writers/docx_writer/docx_writer.py` [0 lines]
- `engines/document/writers/docx_writer.py` [306 lines]
- `engines/document/writers/excel_writer.py` [1660 lines]
- `engines/document/writers/pdf_writer/init.py` [24 lines]
- `engines/orchestration/base_workflow_model.py` [0 lines]
- `engines/orchestration/bpmn2_model.py` [0 lines]
- `engines/orchestration/dag_model.py` [0 lines]
- `engines/orchestration/event_driven_model.py` [0 lines]
- `engines/orchestration/petri_net_model.py` [0 lines]
- `engines/orchestration/state_machine_model.py` [0 lines]

### 🟠 کلاس‌های بدون Base Class (احتمال عدم رعایت interface مشترک)
- `DocumentEmbeddingService` در `engines/document/embedding/service.py`
- `IngestionService` در `engines/document/ingestion/ingestion_service.py`
- `AsyncIngestService` در `engines/document/ingestion/services/async_ingest_service.py`
- `BatchIngestService` در `engines/document/ingestion/services/batch_ingest_service.py`
- `UploadService` در `engines/document/ingestion/services/upload_service.py`
- `FontHandler` در `engines/document/parsers/pdf_parser/font_handler.py`
- `PDFSecurityHandler` در `engines/document/writers/pdf_writer/encryption.py`
- `InteractionStrategy` در `engines/interaction/base_strategy.py`
- `VectorService` در `engines/rag/vector_service.py`
- `SignalHandler` در `tools/ai/entry_points/base_entry_point.py`
- `EventBus` در `tools/ai/orchestration/event_bus.py`
- `StorageBackendBase` در `tools/ai/shared/state_manager.py`

---

## 📝 یادداشت

این گزارش به صورت **استاتیک** (تحلیل AST) تولید شده است.  
برای تحلیل runtime و dependency injection، ابزار تکمیلی لازم است.
