# 📐 Architecture Report

> تولید شده توسط `tools/analyze_architecture.py`  
> تاریخ: 2026-05-12 20:37:50  
---

## 📊 آمار کلی

| معیار | مقدار |
|-------|-------|
| فایل‌های Python | 848 |
| کلاس‌ها | 1723 |
| توابع سطح بالا | 396 |
| فایل‌های با خطا | 0 |
| مجموع خطوط کد | 105085 |

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
  │   ├── 📁 communication/
  │   │   ├── 📁 bindings/
  │   │   ├── 📁 common/
  │   │   │   ├── 📁 auth/
  │   │   │   ├── 📁 serialization/
  │   │   │   └── 📁 transport/
  │   │   ├── 📁 consumption/
  │   │   ├── 📁 exposure/
  │   │   └── 📁 messaging/
  │   │       └── 📁 adapters/
  │   ├── 📁 document/
  │   │   ├── 📁 chunking/
  │   │   ├── 📁 embedding/
  │   │   ├── 📁 ingestion/
  │   │   │   ├── 📁 services/
  │   │   │   ├── 📁 steps/
  │   │   │   └── 📁 utils/
  │   │   ├── 📁 model_tools/
  │   │   │   ├── 📁 format_converters/
  │   │   │   ├── 📁 model_standard_converters/
  │   │   │   └── 📁 report_generators/
  │   │   ├── 📁 models/
  │   │   ├── 📁 parsers/
  │   │   │   ├── 📁 cad_parser/
  │   │   │   ├── 📁 docx_parser/
  │   │   │   ├── 📁 drawingml/
  │   │   │   ├── 📁 dsdm_parsers/
  │   │   │   ├── 📁 msdm_parsers/
  │   │   │   ├── 📁 osdm_parsers/
  │   │   │   ├── 📁 pdf_parser/
  │   │   │   ├── 📁 pptx_parser/
  │   │   │   ├── 📁 spreadsheet_parser/
  │   │   │   │   └── 📁 xlsx/
  │   │   │   ├── 📁 ssdm_parsers/
  │   │   │   └── 📁 tsdm_parsers/
  │   │   ├── 📁 storage/
  │   │   ├── 📁 utils/
  │   │   └── 📁 writers/
  │   │       ├── 📁 cad_writer/
  │   │       ├── 📁 docx_writer/
  │   │       ├── 📁 dsdm_writers/
  │   │       ├── 📁 msdm_writers/
  │   │       ├── 📁 osdm_writers/
  │   │       ├── 📁 pdf_writer/
  │   │       ├── 📁 pptx_writer/
  │   │       ├── 📁 spreadsheet_writer/
  │   │       │   └── 📁 xlsx/
  │   │       ├── 📁 ssdm_writers/
  │   │       └── 📁 tsdm_writers/
  │   ├── 📁 interaction/
  │   │   └── 📁 backends/
  │   ├── 📁 orchestration/
  │   │   ├── 📁 api/
  │   │   ├── 📁 bpmn/
  │   │   ├── 📁 cep/
  │   │   ├── 📁 cmmn/
  │   │   ├── 📁 core/
  │   │   ├── 📁 deployment/
  │   │   ├── 📁 dmn/
  │   │   ├── 📁 expression/
  │   │   ├── 📁 integration/
  │   │   ├── 📁 monitoring/
  │   │   ├── 📁 multi_agent/
  │   │   ├── 📁 persistence/
  │   │   ├── 📁 runtime/
  │   │   ├── 📁 state_machine/
  │   │   ├── 📁 tests/
  │   │   │   ├── 📁 test_bpmn/
  │   │   │   ├── 📁 test_cep/
  │   │   │   ├── 📁 test_cmmn/
  │   │   │   ├── 📁 test_core/
  │   │   │   ├── 📁 test_dmn/
  │   │   │   ├── 📁 test_multi_agent/
  │   │   │   └── 📁 test_state_machine/
  │   │   ├── 📁 utils/
  │   │   └── 📁 validation/
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
  │   ├── 📁 storage/
  │   │   ├── 📁 cache/
  │   │   │   └── 📁 backends/
  │   │   ├── 📁 event_log/
  │   │   │   └── 📁 backends/
  │   │   ├── 📁 graph/
  │   │   │   └── 📁 backends/
  │   │   ├── 📁 key_value/
  │   │   │   └── 📁 backends/
  │   │   ├── 📁 object/
  │   │   │   └── 📁 backends/
  │   │   ├── 📁 relational/
  │   │   │   └── 📁 backends/
  │   │   ├── 📁 stream/
  │   │   │   └── 📁 backends/
  │   │   ├── 📁 timeseries/
  │   │   │   └── 📁 backends/
  │   │   └── 📁 vector/
  │   │       └── 📁 backends/
  │   └── 📁 tools/
  │       └── 📁 adapters/
  ├── 📁 migrations/
  ├── 📁 tests/
  │   └── 📁 agents/
  │       ├── 📁 agents_unit/
  │       └── 📁 interaction/
  │           ├── 📁 interaction_performance/
  │           └── 📁 interaction_unit/
  └── 📁 tools/
```

---

## 🗂️ ساختار کامل (فولدرها + فایل‌ها + تعداد خطوط)

```
📦 project/
  ├── 📁 config/
  │   ├── 📄 __init__.py [13 lines]
  │   └── 📄 settings.py [21 lines]
  ├── 📁 engines/
  │   ├── 📁 agents/
  │   │   ├── 📁 base_agents/
  │   │   │   ├── 📁 base_research_agent/
  │   │   │   │   ├── 📄 metadata.py [0 lines]
  │   │   │   │   ├── 📄 prompts.py [0 lines]
  │   │   │   │   └── 📄 rag_config.py [0 lines]
  │   │   │   ├── 📄 __init__.py [8 lines]
  │   │   │   ├── 📄 base_agent.py [121 lines]
  │   │   │   └── 📄 interaction_agent.py [32 lines]
  │   │   ├── 📁 content/
  │   │   │   ├── 📁 models/
  │   │   │   │   ├── 📄 __init__.py [306 lines]
  │   │   │   │   ├── 📄 analytics_agents_31_40.py [283 lines]
  │   │   │   │   ├── 📄 assessment_agents_21_30.py [331 lines]
  │   │   │   │   ├── 📄 common.py [159 lines]
  │   │   │   │   ├── 📄 content_agents_1_8.py [238 lines]
  │   │   │   │   ├── 📄 content_generation_agents_91_100.py [141 lines]
  │   │   │   │   ├── 📄 curriculum_agents_46_60.py [269 lines]
  │   │   │   │   ├── 📄 evaluation_agents_41_45.py [187 lines]
  │   │   │   │   ├── 📄 learning_objects.py [245 lines]
  │   │   │   │   ├── 📄 memory_agents_76_90.py [252 lines]
  │   │   │   │   ├── 📄 multimodal_agents_101_110.py [132 lines]
  │   │   │   │   ├── 📄 orchestration_agents_61_75.py [270 lines]
  │   │   │   │   ├── 📄 personalization_agents_15_20.py [100 lines]
  │   │   │   │   └── 📄 teaching_agents_9_14.py [83 lines]
  │   │   │   ├── 📄 __init__.py [5 lines]
  │   │   │   └── 📄 text_rewriter.py [78 lines]
  │   │   ├── 📄 __init__.py [10 lines]
  │   │   ├── 📄 agent_registry.py [34 lines]
  │   │   └── 📄 models.py [64 lines]
  │   ├── 📁 buses/
  │   │   ├── 📄 __init__.py [31 lines]
  │   │   ├── 📄 base_message_bus.py [39 lines]
  │   │   ├── 📄 durable_message_bus.py [54 lines]
  │   │   ├── 📄 in_memory_message_bus.py [46 lines]
  │   │   ├── 📄 kafka_bus.py [72 lines]
  │   │   ├── 📄 priority_message_bus.py [72 lines]
  │   │   ├── 📄 rabbitmq_bus.py [71 lines]
  │   │   ├── 📄 redis_pub_sub_bus.py [68 lines]
  │   │   ├── 📄 request_reply_bus.py [39 lines]
  │   │   └── 📄 topic_message_bus.py [40 lines]
  │   ├── 📁 communication/
  │   │   ├── 📁 bindings/
  │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   ├── 📄 binding_parser.py [0 lines]
  │   │   │   ├── 📄 binding_writer.py [0 lines]
  │   │   │   └── 📄 mcp_binding_writer.py [0 lines]
  │   │   ├── 📁 common/
  │   │   │   ├── 📁 auth/
  │   │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   │   ├── 📄 api_key.py [0 lines]
  │   │   │   │   ├── 📄 auth_manager.py [0 lines]
  │   │   │   │   ├── 📄 jwt.py [0 lines]
  │   │   │   │   ├── 📄 mtls.py [0 lines]
  │   │   │   │   └── 📄 oauth2.py [0 lines]
  │   │   │   ├── 📁 serialization/
  │   │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   │   ├── 📄 avro_serializer.py [0 lines]
  │   │   │   │   ├── 📄 json_serializer.py [0 lines]
  │   │   │   │   └── 📄 protobuf_serializer.py [0 lines]
  │   │   │   ├── 📁 transport/
  │   │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   │   ├── 📄 amqp_client.py [0 lines]
  │   │   │   │   ├── 📄 base.py [0 lines]
  │   │   │   │   ├── 📄 grpc_client.py [0 lines]
  │   │   │   │   ├── 📄 http_client.py [0 lines]
  │   │   │   │   ├── 📄 kafka_client.py [0 lines]
  │   │   │   │   └── 📄 mcp_adapter.py [0 lines]
  │   │   │   └── 📄 __init__.py [0 lines]
  │   │   ├── 📁 consumption/
  │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   ├── 📄 binding_loader.py [0 lines]
  │   │   │   ├── 📄 circuit_breaker.py [0 lines]
  │   │   │   ├── 📄 client_generator.py [0 lines]
  │   │   │   ├── 📄 mcp_binding_loader.py [0 lines]
  │   │   │   ├── 📄 mcp_client_adapter.py [0 lines]
  │   │   │   └── 📄 service_discovery.py [0 lines]
  │   │   ├── 📁 exposure/
  │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   ├── 📄 docker_compose_writer.py [0 lines]
  │   │   │   ├── 📄 gateway_config_writer.py [0 lines]
  │   │   │   ├── 📄 kubernetes_manifest_writer.py [0 lines]
  │   │   │   ├── 📄 mcp_server_writer.py [0 lines]
  │   │   │   └── 📄 server_builder.py [0 lines]
  │   │   ├── 📁 messaging/
  │   │   │   ├── 📁 adapters/
  │   │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   │   ├── 📄 amqp_adapter.py [0 lines]
  │   │   │   │   ├── 📄 kafka_adapter.py [0 lines]
  │   │   │   │   └── 📄 nats_adapter.py [0 lines]
  │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   ├── 📄 channel_manager.py [0 lines]
  │   │   │   ├── 📄 message_binding_parser.py [0 lines]
  │   │   │   └── 📄 message_binding_writer.py [0 lines]
  │   │   └── 📄 __init__.py [0 lines]
  │   ├── 📁 document/
  │   │   ├── 📁 chunking/
  │   │   │   ├── 📄 __init__.py [12 lines]
  │   │   │   ├── 📄 base.py [20 lines]
  │   │   │   ├── 📄 models.py [19 lines]
  │   │   │   └── 📄 recursive_chunker.py [105 lines]
  │   │   ├── 📁 embedding/
  │   │   │   ├── 📄 __init__.py [9 lines]
  │   │   │   ├── 📄 base.py [17 lines]
  │   │   │   └── 📄 service.py [53 lines]
  │   │   ├── 📁 ingestion/
  │   │   │   ├── 📁 services/
  │   │   │   │   ├── 📄 __init__.py [14 lines]
  │   │   │   │   ├── 📄 async_ingest_service.py [70 lines]
  │   │   │   │   ├── 📄 batch_ingest_service.py [60 lines]
  │   │   │   │   ├── 📄 ingestion_scheduler.py [68 lines]
  │   │   │   │   └── 📄 upload_service.py [50 lines]
  │   │   │   ├── 📁 steps/
  │   │   │   │   ├── 📄 __init__.py [17 lines]
  │   │   │   │   ├── 📄 step_chunk.py [29 lines]
  │   │   │   │   ├── 📄 step_embed.py [50 lines]
  │   │   │   │   ├── 📄 step_extract.py [37 lines]
  │   │   │   │   ├── 📄 step_parse.py [33 lines]
  │   │   │   │   └── 📄 step_store.py [46 lines]
  │   │   │   ├── 📁 utils/
  │   │   │   │   ├── 📄 __init__.py [17 lines]
  │   │   │   │   ├── 📄 file_signature.py [28 lines]
  │   │   │   │   ├── 📄 hashing.py [32 lines]
  │   │   │   │   ├── 📄 retry_policy.py [46 lines]
  │   │   │   │   └── 📄 timing.py [46 lines]
  │   │   │   ├── 📄 __init__.py [46 lines]
  │   │   │   ├── 📄 ingestion_context.py [172 lines]
  │   │   │   ├── 📄 ingestion_errors.py [96 lines]
  │   │   │   ├── 📄 ingestion_models.py [164 lines]
  │   │   │   ├── 📄 ingestion_pipeline.py [73 lines]
  │   │   │   ├── 📄 ingestion_runner.py [161 lines]
  │   │   │   ├── 📄 ingestion_service.py [163 lines]
  │   │   │   ├── 📄 ingestion_utils.py [26 lines]
  │   │   │   ├── 📄 ingestion_validator.py [50 lines]
  │   │   │   └── 📄 workflow_registry.py [27 lines]
  │   │   ├── 📁 model_tools/
  │   │   │   ├── 📁 format_converters/
  │   │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   │   ├── 📄 converter_base.py [0 lines]
  │   │   │   │   ├── 📄 docx_to_pdf.py [0 lines]
  │   │   │   │   ├── 📄 docx_to_pptx.py [0 lines]
  │   │   │   │   ├── 📄 generic_converter.py [0 lines]
  │   │   │   │   ├── 📄 json_to_docx.py [0 lines]
  │   │   │   │   ├── 📄 json_to_pdf.py [0 lines]
  │   │   │   │   ├── 📄 markdown_to_docx.py [0 lines]
  │   │   │   │   ├── 📄 markdown_to_pdf.py [0 lines]
  │   │   │   │   ├── 📄 pdf_to_docx.py [0 lines]
  │   │   │   │   ├── 📄 ppt_to_docx.py [0 lines]
  │   │   │   │   ├── 📄 ppt_to_pdf.py [0 lines]
  │   │   │   │   ├── 📄 xlsx_to_docx.py [0 lines]
  │   │   │   │   ├── 📄 xlsx_to_pdf.py [0 lines]
  │   │   │   │   └── 📄 xlsx_to_ppt.py [0 lines]
  │   │   │   ├── 📁 model_standard_converters/
  │   │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   │   ├── 📄 csdm_to_usdm_adapter.py [0 lines]
  │   │   │   │   ├── 📄 esdm_to_usdm_adapter.py [0 lines]
  │   │   │   │   ├── 📄 psdm_to_usdm_adapter.py [0 lines]
  │   │   │   │   └── 📄 usdm_to_pdf_adapter.py [0 lines]
  │   │   │   ├── 📁 report_generators/
  │   │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   │   ├── 📄 data_aggregated_list_report_generator.py [0 lines]
  │   │   │   │   ├── 📄 data_aggregated_list_with_content_report_generator.py [0 lines]
  │   │   │   │   ├── 📄 data_aggregated_list_with_related_list_report_generator.py [0 lines]
  │   │   │   │   ├── 📄 data_aggregated_list_with_sub_list_report_generator.py [0 lines]
  │   │   │   │   ├── 📄 data_aggregated_page_report_generator.py [0 lines]
  │   │   │   │   ├── 📄 data_aggregated_page_with_related_list_report_generator.py [0 lines]
  │   │   │   │   ├── 📄 data_aggregated_page_with_sub_list_report_generator.py [0 lines]
  │   │   │   │   ├── 📄 data_simple_list_report_generator.py [0 lines]
  │   │   │   │   ├── 📄 data_simple_list_with_content_report_generator.py [0 lines]
  │   │   │   │   ├── 📄 data_simple_list_with_related_list_report_generator.py [0 lines]
  │   │   │   │   ├── 📄 data_simple_page_report_generator.py [0 lines]
  │   │   │   │   ├── 📄 data_simple_page_with_related_list_report_generator.py [0 lines]
  │   │   │   │   ├── 📄 schema_report_generator.py [0 lines]
  │   │   │   │   └── 📄 service_report_generator.py [0 lines]
  │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   ├── 📄 configuration.py [0 lines]
  │   │   │   ├── 📄 diff_engine.py [0 lines]
  │   │   │   └── 📄 diff_sql_writer.py [0 lines]
  │   │   ├── 📁 models/
  │   │   │   ├── 📄 __init__.py [783 lines]
  │   │   │   ├── 📄 base.py [174 lines]
  │   │   │   ├── 📄 chunked_binary_payload.py [24 lines]
  │   │   │   ├── 📄 csdm_core.py [698 lines]
  │   │   │   ├── 📄 csdm_entities.py [649 lines]
  │   │   │   ├── 📄 csdm_tables.py [658 lines]
  │   │   │   ├── 📄 document_registry.py [263 lines]
  │   │   │   ├── 📄 dsdm_models.py [208 lines]
  │   │   │   ├── 📄 esdm_models.py [990 lines]
  │   │   │   ├── 📄 exceptions.py [54 lines]
  │   │   │   ├── 📄 media_detection.py [508 lines]
  │   │   │   ├── 📄 media_types.py [880 lines]
  │   │   │   ├── 📄 msdm_capabilities.py [147 lines]
  │   │   │   ├── 📄 msdm_models.py [360 lines]
  │   │   │   ├── 📄 msdm_registry.py [455 lines]
  │   │   │   ├── 📄 osdm_models.py [1560 lines]
  │   │   │   ├── 📄 psdm_models.py [282 lines]
  │   │   │   ├── 📄 ssdm_capabilities.py [99 lines]
  │   │   │   ├── 📄 ssdm_models.py [747 lines]
  │   │   │   ├── 📄 ssdm_registry.py [186 lines]
  │   │   │   ├── 📄 standard.py [148 lines]
  │   │   │   ├── 📄 tsdm_models.py [252 lines]
  │   │   │   └── 📄 usdm_models.py [716 lines]
  │   │   ├── 📁 parsers/
  │   │   │   ├── 📁 cad_parser/
  │   │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   │   ├── 📄 csdm_loader.py [580 lines]
  │   │   │   │   ├── 📄 csdm_parser.py [60 lines]
  │   │   │   │   ├── 📄 csdm_relationships.py [240 lines]
  │   │   │   │   └── 📄 oda_bridge.py [238 lines]
  │   │   │   ├── 📁 docx_parser/
  │   │   │   │   ├── 📄 __init__.py [88 lines]
  │   │   │   │   ├── 📄 docx_chart_extractor.py [122 lines]
  │   │   │   │   ├── 📄 docx_diagram_extractor.py [114 lines]
  │   │   │   │   ├── 📄 docx_extractor.py [2275 lines]
  │   │   │   │   ├── 📄 docx_image_extractor.py [531 lines]
  │   │   │   │   ├── 📄 docx_math_parser.py [915 lines]
  │   │   │   │   ├── 📄 docx_models.py [747 lines]
  │   │   │   │   ├── 📄 docx_parser.py [1966 lines]
  │   │   │   │   ├── 📄 docx_shape_extractor.py [106 lines]
  │   │   │   │   ├── 📄 docx_style_parser.py [128 lines]
  │   │   │   │   ├── 📄 docx_table_parser.py [35 lines]
  │   │   │   │   └── 📄 docx_utils.py [3588 lines]
  │   │   │   ├── 📁 drawingml/
  │   │   │   │   ├── 📄 __init__.py [15 lines]
  │   │   │   │   ├── 📄 chart_ref_parser.py [109 lines]
  │   │   │   │   ├── 📄 diagram_parser.py [132 lines]
  │   │   │   │   ├── 📄 image_parser.py [122 lines]
  │   │   │   │   └── 📄 shape_parser.py [331 lines]
  │   │   │   ├── 📁 dsdm_parsers/
  │   │   │   │   ├── 📄 __init__.py [54 lines]
  │   │   │   │   ├── 📄 base_dsdm_parser.py [205 lines]
  │   │   │   │   ├── 📄 binary_parser.py [22 lines]
  │   │   │   │   ├── 📄 bson_parser.py [24 lines]
  │   │   │   │   ├── 📄 cassandra_parser.py [78 lines]
  │   │   │   │   ├── 📄 cbor_parser.py [18 lines]
  │   │   │   │   ├── 📄 csv_tsv_parser.py [132 lines]
  │   │   │   │   ├── 📄 dsdm_utils.py [314 lines]
  │   │   │   │   ├── 📄 json_parser.py [18 lines]
  │   │   │   │   ├── 📄 mongodb_parser.py [141 lines]
  │   │   │   │   ├── 📄 msgpack_parser.py [18 lines]
  │   │   │   │   ├── 📄 pickle_parser.py [20 lines]
  │   │   │   │   ├── 📄 protobuf_parser.py [35 lines]
  │   │   │   │   ├── 📄 redis_parser.py [82 lines]
  │   │   │   │   ├── 📄 sql_parser.py [165 lines]
  │   │   │   │   ├── 📄 xml_parser.py [50 lines]
  │   │   │   │   └── 📄 yaml_parser.py [16 lines]
  │   │   │   ├── 📁 msdm_parsers/
  │   │   │   │   ├── 📄 __init__.py [120 lines]
  │   │   │   │   ├── 📄 base_msdm_parser.py [137 lines]
  │   │   │   │   ├── 📄 cql_parser.py [551 lines]
  │   │   │   │   ├── 📄 elasticsearch_mapping_parser.py [252 lines]
  │   │   │   │   ├── 📄 erd_parser.py [298 lines]
  │   │   │   │   ├── 📄 graphql_schema_parser.py [602 lines]
  │   │   │   │   ├── 📄 influxdb_schema_parser.py [318 lines]
  │   │   │   │   ├── 📄 json_schema_parser.py [405 lines]
  │   │   │   │   ├── 📄 mongodb_schema_parser.py [478 lines]
  │   │   │   │   ├── 📄 neo4j_schema_parser.py [220 lines]
  │   │   │   │   ├── 📄 owl_parser.py [268 lines]
  │   │   │   │   ├── 📄 plantuml_parser.py [383 lines]
  │   │   │   │   ├── 📄 proto_msdm_parser.py [402 lines]
  │   │   │   │   ├── 📄 python_model_parser.py [296 lines]
  │   │   │   │   ├── 📄 sql_ddl_parser.py [524 lines]
  │   │   │   │   ├── 📄 thrift_idl_parser.py [278 lines]
  │   │   │   │   ├── 📄 typescript_interface_parser.py [639 lines]
  │   │   │   │   ├── 📄 uml_xmi_parser.py [372 lines]
  │   │   │   │   └── 📄 xsd_parser.py [343 lines]
  │   │   │   ├── 📁 osdm_parsers/
  │   │   │   │   ├── 📄 __init__.py [58 lines]
  │   │   │   │   ├── 📄 base_osdm_parser.py [91 lines]
  │   │   │   │   ├── 📄 bpmn_xml_parser.py [1441 lines]
  │   │   │   │   ├── 📄 cep_parser.py [119 lines]
  │   │   │   │   ├── 📄 cmmn_xml_parser.py [394 lines]
  │   │   │   │   ├── 📄 dmn_xml_parser.py [255 lines]
  │   │   │   │   ├── 📄 epc_parser.py [200 lines]
  │   │   │   │   ├── 📄 graphml_xml_parser.py [159 lines]
  │   │   │   │   ├── 📄 pnml_xml_parser.py [171 lines]
  │   │   │   │   ├── 📄 prefect_dag_parser.py [182 lines]
  │   │   │   │   ├── 📄 scxml_parser.py [311 lines]
  │   │   │   │   ├── 📄 uml_state_machine_parser.py [247 lines]
  │   │   │   │   └── 📄 xpd_parser.py [337 lines]
  │   │   │   ├── 📁 pdf_parser/
  │   │   │   │   ├── 📄 __init__.py [93 lines]
  │   │   │   │   ├── 📄 content_extractor.py [1049 lines]
  │   │   │   │   ├── 📄 font_handler.py [923 lines]
  │   │   │   │   ├── 📄 layout_analyzer.py [398 lines]
  │   │   │   │   ├── 📄 metadata_extractor.py [1533 lines]
  │   │   │   │   ├── 📄 pdf_objects.py [1219 lines]
  │   │   │   │   ├── 📄 structure_parser.py [518 lines]
  │   │   │   │   └── 📄 utils.py [1145 lines]
  │   │   │   ├── 📁 pptx_parser/
  │   │   │   │   ├── 📄 __init__.py [50 lines]
  │   │   │   │   ├── 📄 animation_parser.py [191 lines]
  │   │   │   │   ├── 📄 comments_parser.py [40 lines]
  │   │   │   │   ├── 📄 constants.py [106 lines]
  │   │   │   │   ├── 📄 master_parser.py [185 lines]
  │   │   │   │   ├── 📄 media_parser.py [117 lines]
  │   │   │   │   ├── 📄 notes_parser.py [83 lines]
  │   │   │   │   ├── 📄 ole_parser.py [45 lines]
  │   │   │   │   ├── 📄 parser.py [403 lines]
  │   │   │   │   ├── 📄 relationship_utils.py [127 lines]
  │   │   │   │   ├── 📄 shape_parser.py [106 lines]
  │   │   │   │   ├── 📄 slide_builder.py [297 lines]
  │   │   │   │   ├── 📄 table_parser.py [138 lines]
  │   │   │   │   ├── 📄 theme_parser.py [170 lines]
  │   │   │   │   └── 📄 utils.py [62 lines]
  │   │   │   ├── 📁 spreadsheet_parser/
  │   │   │   │   ├── 📁 xlsx/
  │   │   │   │   │   ├── 📄 __init__.py [77 lines]
  │   │   │   │   │   ├── 📄 charts_builder.py [122 lines]
  │   │   │   │   │   ├── 📄 constants.py [233 lines]
  │   │   │   │   │   ├── 📄 drawings_builder.py [270 lines]
  │   │   │   │   │   ├── 📄 formulas_builder.py [94 lines]
  │   │   │   │   │   ├── 📄 namespaces.py [16 lines]
  │   │   │   │   │   ├── 📄 parser.py [317 lines]
  │   │   │   │   │   ├── 📄 pivot_builder.py [70 lines]
  │   │   │   │   │   ├── 📄 relationships_builder.py [113 lines]
  │   │   │   │   │   ├── 📄 shared_strings_builder.py [0 lines]
  │   │   │   │   │   ├── 📄 styles_builder.py [366 lines]
  │   │   │   │   │   ├── 📄 tables_builder.py [236 lines]
  │   │   │   │   │   ├── 📄 utils.py [113 lines]
  │   │   │   │   │   ├── 📄 vba_builder.py [123 lines]
  │   │   │   │   │   ├── 📄 workbook_builder.py [240 lines]
  │   │   │   │   │   └── 📄 worksheet_builder.py [460 lines]
  │   │   │   │   ├── 📄 __init__.py [19 lines]
  │   │   │   │   ├── 📄 base_spreadsheet_parser.py [89 lines]
  │   │   │   │   ├── 📄 binary_parser.py [130 lines]
  │   │   │   │   ├── 📄 delimited_parser.py [117 lines]
  │   │   │   │   └── 📄 fixed_width_parser.py [131 lines]
  │   │   │   ├── 📁 ssdm_parsers/
  │   │   │   │   ├── 📄 __init__.py [47 lines]
  │   │   │   │   ├── 📄 asyncapi_parser.py [379 lines]
  │   │   │   │   ├── 📄 base_ssdm_parser.py [91 lines]
  │   │   │   │   ├── 📄 graphql_service_parser.py [724 lines]
  │   │   │   │   ├── 📄 mcp_parser.py [362 lines]
  │   │   │   │   ├── 📄 openapi_parser.py [553 lines]
  │   │   │   │   ├── 📄 proto_service_parser.py [654 lines]
  │   │   │   │   ├── 📄 python_service_parser.py [464 lines]
  │   │   │   │   ├── 📄 wsdl_parser.py [286 lines]
  │   │   │   │   └── 📄 yang_parser.py [660 lines]
  │   │   │   ├── 📁 tsdm_parsers/
  │   │   │   │   ├── 📄 __init__.py [9 lines]
  │   │   │   │   ├── 📄 base_tsdm_parser.py [39 lines]
  │   │   │   │   └── 📄 tsdm_json_parser.py [230 lines]
  │   │   │   ├── 📄 __init__.py [18 lines]
  │   │   │   ├── 📄 base.py [90 lines]
  │   │   │   ├── 📄 html_parser.py [738 lines]
  │   │   │   ├── 📄 latex_parser.py [835 lines]
  │   │   │   └── 📄 markdown_parser.py [433 lines]
  │   │   ├── 📁 storage/
  │   │   │   ├── 📄 __init__.py [11 lines]
  │   │   │   ├── 📄 chunk_store.py [121 lines]
  │   │   │   ├── 📄 document_store.py [141 lines]
  │   │   │   └── 📄 metadata_store.py [38 lines]
  │   │   ├── 📁 utils/
  │   │   │   ├── 📄 __init__.py [9 lines]
  │   │   │   ├── 📄 binary_codec.py [100 lines]
  │   │   │   ├── 📄 docx_utils.py [0 lines]
  │   │   │   ├── 📄 ooxml_constants.py [0 lines]
  │   │   │   ├── 📄 streaming_binary_codec.py [46 lines]
  │   │   │   └── 📄 xml_parser.py [0 lines]
  │   │   ├── 📁 writers/
  │   │   │   ├── 📁 cad_writer/
  │   │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   │   ├── 📄 acis_writer.py [71 lines]
  │   │   │   │   ├── 📄 base_context.py [59 lines]
  │   │   │   │   ├── 📄 block_writer.py [99 lines]
  │   │   │   │   ├── 📄 cad_writer.py [104 lines]
  │   │   │   │   ├── 📄 dwg_builder.py [146 lines]
  │   │   │   │   ├── 📄 entity_writer.py [297 lines]
  │   │   │   │   ├── 📄 finalizer.py [115 lines]
  │   │   │   │   ├── 📄 non_graphical_writer.py [212 lines]
  │   │   │   │   ├── 📄 reactor_writer.py [53 lines]
  │   │   │   │   ├── 📄 table_writer.py [245 lines]
  │   │   │   │   └── 📄 xdata_writer.py [62 lines]
  │   │   │   ├── 📁 docx_writer/
  │   │   │   │   ├── 📄 docx_builder.py [0 lines]
  │   │   │   │   ├── 📄 docx_image_handler.py [0 lines]
  │   │   │   │   ├── 📄 docx_math_writer.py [0 lines]
  │   │   │   │   ├── 📄 docx_style_builder.py [0 lines]
  │   │   │   │   ├── 📄 docx_table_builder.py [0 lines]
  │   │   │   │   └── 📄 docx_writer.py [0 lines]
  │   │   │   ├── 📁 dsdm_writers/
  │   │   │   │   ├── 📄 __init__.py [49 lines]
  │   │   │   │   ├── 📄 base_dsdm_writer.py [102 lines]
  │   │   │   │   ├── 📄 binary_writer.py [51 lines]
  │   │   │   │   ├── 📄 bson_writer.py [33 lines]
  │   │   │   │   ├── 📄 cassandra_writer.py [50 lines]
  │   │   │   │   ├── 📄 cbor_writer.py [24 lines]
  │   │   │   │   ├── 📄 csv_tsv_writer.py [90 lines]
  │   │   │   │   ├── 📄 json_writer.py [25 lines]
  │   │   │   │   ├── 📄 mongodb_writer.py [65 lines]
  │   │   │   │   ├── 📄 msgpack_writer.py [28 lines]
  │   │   │   │   ├── 📄 pickle_writer.py [30 lines]
  │   │   │   │   ├── 📄 protobuf_writer.py [45 lines]
  │   │   │   │   ├── 📄 redis_writer.py [57 lines]
  │   │   │   │   ├── 📄 sql_writer.py [119 lines]
  │   │   │   │   ├── 📄 xml_writer.py [134 lines]
  │   │   │   │   └── 📄 yaml_writer.py [24 lines]
  │   │   │   ├── 📁 msdm_writers/
  │   │   │   │   ├── 📄 __init__.py [76 lines]
  │   │   │   │   ├── 📄 base_msdm_writer.py [180 lines]
  │   │   │   │   ├── 📄 cql_writer.py [431 lines]
  │   │   │   │   ├── 📄 elasticsearch_mapping_writer.py [322 lines]
  │   │   │   │   ├── 📄 erd_writer.py [220 lines]
  │   │   │   │   ├── 📄 graphql_schema_writer.py [309 lines]
  │   │   │   │   ├── 📄 influxdb_schema_writer.py [264 lines]
  │   │   │   │   ├── 📄 json_schema_writer.py [297 lines]
  │   │   │   │   ├── 📄 mongodb_schema_writer.py [332 lines]
  │   │   │   │   ├── 📄 neo4j_schema_writer.py [170 lines]
  │   │   │   │   ├── 📄 owl_writer.py [170 lines]
  │   │   │   │   ├── 📄 plantuml_writer.py [242 lines]
  │   │   │   │   ├── 📄 proto_msdm_writer.py [271 lines]
  │   │   │   │   ├── 📄 python_model_writer.py [342 lines]
  │   │   │   │   ├── 📄 sql_ddl_writer.py [313 lines]
  │   │   │   │   ├── 📄 thrift_idl_writer.py [263 lines]
  │   │   │   │   ├── 📄 typescript_interface_writer.py [283 lines]
  │   │   │   │   ├── 📄 uml_xmi_writer.py [276 lines]
  │   │   │   │   └── 📄 xsd_writer.py [260 lines]
  │   │   │   ├── 📁 osdm_writers/
  │   │   │   │   ├── 📄 __init__.py [59 lines]
  │   │   │   │   ├── 📄 base_osdm_writer.py [166 lines]
  │   │   │   │   ├── 📄 bpmn_xml_writer.py [802 lines]
  │   │   │   │   ├── 📄 cep_writer.py [80 lines]
  │   │   │   │   ├── 📄 cmmn_xml_writer.py [217 lines]
  │   │   │   │   ├── 📄 dmn_xml_writer.py [201 lines]
  │   │   │   │   ├── 📄 epc_writer.py [129 lines]
  │   │   │   │   ├── 📄 graphml_xml_writer.py [134 lines]
  │   │   │   │   ├── 📄 pnml_xml_writer.py [143 lines]
  │   │   │   │   ├── 📄 prefect_dag_writer.py [186 lines]
  │   │   │   │   ├── 📄 scxml_writer.py [251 lines]
  │   │   │   │   ├── 📄 uml_state_machine_writer.py [175 lines]
  │   │   │   │   └── 📄 xpd_writer.py [172 lines]
  │   │   │   ├── 📁 pdf_writer/
  │   │   │   │   ├── 📄 __init__.py [64 lines]
  │   │   │   │   ├── 📄 annotation_writer.py [581 lines]
  │   │   │   │   ├── 📄 content_writer.py [313 lines]
  │   │   │   │   ├── 📄 encryption.py [966 lines]
  │   │   │   │   ├── 📄 font_manager.py [1498 lines]
  │   │   │   │   ├── 📄 init.py [28 lines]
  │   │   │   │   ├── 📄 layout_builder.py [223 lines]
  │   │   │   │   ├── 📄 metadata_writer.py [413 lines]
  │   │   │   │   ├── 📄 optimizer.py [1257 lines]
  │   │   │   │   ├── 📄 outline_builder.py [275 lines]
  │   │   │   │   ├── 📄 pdf_objects.py [500 lines]
  │   │   │   │   └── 📄 utils.py [437 lines]
  │   │   │   ├── 📁 pptx_writer/
  │   │   │   │   ├── 📄 __init__.py [70 lines]
  │   │   │   │   ├── 📄 animation_writer.py [94 lines]
  │   │   │   │   ├── 📄 charts_writer.py [73 lines]
  │   │   │   │   ├── 📄 comments_writer.py [32 lines]
  │   │   │   │   ├── 📄 constants.py [74 lines]
  │   │   │   │   ├── 📄 diagram_writer.py [108 lines]
  │   │   │   │   ├── 📄 master_writer.py [88 lines]
  │   │   │   │   ├── 📄 media_writer.py [76 lines]
  │   │   │   │   ├── 📄 notes_writer.py [59 lines]
  │   │   │   │   ├── 📄 ole_writer.py [47 lines]
  │   │   │   │   ├── 📄 relationship_utils.py [86 lines]
  │   │   │   │   ├── 📄 shape_writer.py [172 lines]
  │   │   │   │   ├── 📄 slide_writer.py [204 lines]
  │   │   │   │   ├── 📄 style_writer.py [141 lines]
  │   │   │   │   ├── 📄 table_writer.py [71 lines]
  │   │   │   │   ├── 📄 theme_writer.py [119 lines]
  │   │   │   │   ├── 📄 utils.py [31 lines]
  │   │   │   │   └── 📄 writer.py [467 lines]
  │   │   │   ├── 📁 spreadsheet_writer/
  │   │   │   │   ├── 📁 xlsx/
  │   │   │   │   │   ├── 📄 __init__.py [47 lines]
  │   │   │   │   │   ├── 📄 conditional_formatting_writer.py [181 lines]
  │   │   │   │   │   ├── 📄 const.py [7 lines]
  │   │   │   │   │   ├── 📄 data_validation_writer.py [116 lines]
  │   │   │   │   │   ├── 📄 drawing_writer.py [423 lines]
  │   │   │   │   │   ├── 📄 extra_writers.py [187 lines]
  │   │   │   │   │   ├── 📄 pivot_writer.py [231 lines]
  │   │   │   │   │   ├── 📄 shared_strings_writer.py [48 lines]
  │   │   │   │   │   ├── 📄 styles_writer.py [277 lines]
  │   │   │   │   │   ├── 📄 table_writer.py [103 lines]
  │   │   │   │   │   ├── 📄 vba_writer.py [39 lines]
  │   │   │   │   │   ├── 📄 workbook_writer.py [61 lines]
  │   │   │   │   │   ├── 📄 worksheet_writer.py [310 lines]
  │   │   │   │   │   ├── 📄 xlsx_writer.py [199 lines]
  │   │   │   │   │   └── 📄 zip_packager.py [53 lines]
  │   │   │   │   ├── 📄 __init__.py [13 lines]
  │   │   │   │   ├── 📄 base.py [312 lines]
  │   │   │   │   ├── 📄 csv_writer.py [152 lines]
  │   │   │   │   └── 📄 esdm_writer.py [143 lines]
  │   │   │   ├── 📁 ssdm_writers/
  │   │   │   │   ├── 📄 __init__.py [36 lines]
  │   │   │   │   ├── 📄 asyncapi_writer.py [221 lines]
  │   │   │   │   ├── 📄 base_ssdm_writer.py [151 lines]
  │   │   │   │   ├── 📄 graphql_service_writer.py [313 lines]
  │   │   │   │   ├── 📄 mcp_writer.py [179 lines]
  │   │   │   │   ├── 📄 openapi_writer.py [345 lines]
  │   │   │   │   ├── 📄 proto_service_writer.py [181 lines]
  │   │   │   │   ├── 📄 python_service_writer.py [232 lines]
  │   │   │   │   ├── 📄 wsdl_writer.py [248 lines]
  │   │   │   │   └── 📄 yang_writer.py [384 lines]
  │   │   │   ├── 📁 tsdm_writers/
  │   │   │   │   ├── 📄 __init__.py [8 lines]
  │   │   │   │   ├── 📄 base_tsdm_writer.py [13 lines]
  │   │   │   │   └── 📄 tsdm_json_writer.py [209 lines]
  │   │   │   ├── 📄 __init__.py [25 lines]
  │   │   │   ├── 📄 base.py [61 lines]
  │   │   │   ├── 📄 drawingml_helpers.py [231 lines]
  │   │   │   ├── 📄 html_writer.py [223 lines]
  │   │   │   ├── 📄 latex_writer.py [636 lines]
  │   │   │   └── 📄 markdown_writer.py [286 lines]
  │   │   └── 📄 __init__.py [0 lines]
  │   ├── 📁 interaction/
  │   │   ├── 📁 backends/
  │   │   │   ├── 📄 __init__.py [11 lines]
  │   │   │   ├── 📄 autogen_backend.py [177 lines]
  │   │   │   ├── 📄 base_backend.py [10 lines]
  │   │   │   └── 📄 native_backend.py [73 lines]
  │   │   ├── 📄 __init__.py [34 lines]
  │   │   ├── 📄 base_strategy.py [113 lines]
  │   │   ├── 📄 broadcast_strategy.py [142 lines]
  │   │   ├── 📄 coordinator_strategy.py [160 lines]
  │   │   ├── 📄 debate_strategy.py [123 lines]
  │   │   ├── 📄 ensemble_strategy.py [168 lines]
  │   │   ├── 📄 group_chat_strategy.py [266 lines]
  │   │   ├── 📄 interaction_models.py [56 lines]
  │   │   ├── 📄 round_robin_strategy.py [140 lines]
  │   │   ├── 📄 self_refine_strategy.py [146 lines]
  │   │   └── 📄 strategy_registry.py [64 lines]
  │   ├── 📁 orchestration/
  │   │   ├── 📁 api/
  │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   ├── 📄 admin_api.py [0 lines]
  │   │   │   ├── 📄 deployment_api.py [0 lines]
  │   │   │   ├── 📄 engine_api.py [0 lines]
  │   │   │   ├── 📄 instance_api.py [0 lines]
  │   │   │   ├── 📄 process_api.py [0 lines]
  │   │   │   └── 📄 task_api.py [0 lines]
  │   │   ├── 📁 bpmn/
  │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   ├── 📄 activity_handler.py [0 lines]
  │   │   │   ├── 📄 adhoc_handler.py [0 lines]
  │   │   │   ├── 📄 choreography_handler.py [0 lines]
  │   │   │   ├── 📄 collaboration_handler.py [0 lines]
  │   │   │   ├── 📄 data_object_handler.py [0 lines]
  │   │   │   ├── 📄 engine.py [0 lines]
  │   │   │   ├── 📄 event_handler.py [0 lines]
  │   │   │   ├── 📄 gateway_handler.py [0 lines]
  │   │   │   ├── 📄 global_task_handler.py [0 lines]
  │   │   │   ├── 📄 loop_handler.py [0 lines]
  │   │   │   ├── 📄 process_executor.py [0 lines]
  │   │   │   ├── 📄 sequence_flow.py [0 lines]
  │   │   │   └── 📄 transaction_handler.py [0 lines]
  │   │   ├── 📁 cep/
  │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   ├── 📄 aggregator.py [0 lines]
  │   │   │   ├── 📄 engine.py [0 lines]
  │   │   │   ├── 📄 event_store.py [0 lines]
  │   │   │   ├── 📄 pattern_matcher.py [0 lines]
  │   │   │   ├── 📄 rule_evaluator.py [0 lines]
  │   │   │   ├── 📄 stream_processor.py [0 lines]
  │   │   │   └── 📄 window_manager.py [0 lines]
  │   │   ├── 📁 cmmn/
  │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   ├── 📄 case_executor.py [0 lines]
  │   │   │   ├── 📄 case_file_manager.py [0 lines]
  │   │   │   ├── 📄 discretionary_handler.py [0 lines]
  │   │   │   ├── 📄 engine.py [0 lines]
  │   │   │   ├── 📄 milestone_handler.py [0 lines]
  │   │   │   ├── 📄 planning_table_handler.py [0 lines]
  │   │   │   ├── 📄 sentry_evaluator.py [0 lines]
  │   │   │   ├── 📄 stage_handler.py [0 lines]
  │   │   │   └── 📄 task_handler.py [0 lines]
  │   │   ├── 📁 core/
  │   │   │   ├── 📄 __init__.py [61 lines]
  │   │   │   ├── 📄 context.py [398 lines]
  │   │   │   ├── 📄 correlation.py [459 lines]
  │   │   │   ├── 📄 engine.py [590 lines]
  │   │   │   ├── 📄 event_bus.py [397 lines]
  │   │   │   ├── 📄 instance.py [418 lines]
  │   │   │   ├── 📄 scheduler.py [396 lines]
  │   │   │   ├── 📄 token.py [443 lines]
  │   │   │   └── 📄 transaction.py [503 lines]
  │   │   ├── 📁 deployment/
  │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   ├── 📄 deployer.py [0 lines]
  │   │   │   ├── 📄 migration_handler.py [0 lines]
  │   │   │   ├── 📄 tenant_manager.py [0 lines]
  │   │   │   └── 📄 version_manager.py [0 lines]
  │   │   ├── 📁 dmn/
  │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   ├── 📄 decision_executor.py [0 lines]
  │   │   │   ├── 📄 decision_table_evaluator.py [0 lines]
  │   │   │   ├── 📄 engine.py [0 lines]
  │   │   │   ├── 📄 feel_engine.py [0 lines]
  │   │   │   ├── 📄 hit_policy_handler.py [0 lines]
  │   │   │   ├── 📄 invocation_handler.py [0 lines]
  │   │   │   └── 📄 literal_expression_eval.py [0 lines]
  │   │   ├── 📁 expression/
  │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   ├── 📄 context_builder.py [0 lines]
  │   │   │   ├── 📄 evaluator.py [0 lines]
  │   │   │   ├── 📄 feel_evaluator.py [0 lines]
  │   │   │   ├── 📄 javascript_evaluator.py [0 lines]
  │   │   │   ├── 📄 juel_evaluator.py [0 lines]
  │   │   │   └── 📄 python_evaluator.py [0 lines]
  │   │   ├── 📁 integration/
  │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   ├── 📄 business_rule_adapter.py [0 lines]
  │   │   │   ├── 📄 connector_registry.py [0 lines]
  │   │   │   ├── 📄 data_mapper.py [0 lines]
  │   │   │   ├── 📄 message_adapter.py [0 lines]
  │   │   │   ├── 📄 script_executor.py [0 lines]
  │   │   │   ├── 📄 service_invoker.py [0 lines]
  │   │   │   └── 📄 user_task_adapter.py [0 lines]
  │   │   ├── 📁 monitoring/
  │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   ├── 📄 health_checker.py [0 lines]
  │   │   │   ├── 📄 logger.py [0 lines]
  │   │   │   ├── 📄 metrics_collector.py [0 lines]
  │   │   │   ├── 📄 performance_monitor.py [0 lines]
  │   │   │   └── 📄 tracer.py [0 lines]
  │   │   ├── 📁 multi_agent/
  │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   ├── 📄 agent_executor.py [0 lines]
  │   │   │   ├── 📄 coordination_handler.py [0 lines]
  │   │   │   ├── 📄 engine.py [0 lines]
  │   │   │   ├── 📄 interaction_handler.py [0 lines]
  │   │   │   ├── 📄 message_router.py [0 lines]
  │   │   │   ├── 📄 negotiation_handler.py [0 lines]
  │   │   │   └── 📄 protocol_handler.py [0 lines]
  │   │   ├── 📁 persistence/
  │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   ├── 📄 definition_repository.py [0 lines]
  │   │   │   ├── 📄 event_repository.py [0 lines]
  │   │   │   ├── 📄 history_repository.py [0 lines]
  │   │   │   ├── 📄 instance_repository.py [0 lines]
  │   │   │   ├── 📄 repository.py [0 lines]
  │   │   │   └── 📄 variable_repository.py [0 lines]
  │   │   ├── 📁 runtime/
  │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   ├── 📄 compensation.py [0 lines]
  │   │   │   ├── 📄 error_handler.py [0 lines]
  │   │   │   ├── 📄 executor.py [0 lines]
  │   │   │   ├── 📄 resource_manager.py [0 lines]
  │   │   │   ├── 📄 state_manager.py [0 lines]
  │   │   │   ├── 📄 timer_manager.py [0 lines]
  │   │   │   └── 📄 variable_manager.py [0 lines]
  │   │   ├── 📁 state_machine/
  │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   ├── 📄 action_executor.py [0 lines]
  │   │   │   ├── 📄 engine.py [0 lines]
  │   │   │   ├── 📄 guard_evaluator.py [0 lines]
  │   │   │   ├── 📄 hierarchical_handler.py [0 lines]
  │   │   │   ├── 📄 history_manager.py [0 lines]
  │   │   │   ├── 📄 parallel_state_handler.py [0 lines]
  │   │   │   ├── 📄 state_executor.py [0 lines]
  │   │   │   └── 📄 transition_handler.py [0 lines]
  │   │   ├── 📁 tests/
  │   │   │   ├── 📁 test_bpmn/
  │   │   │   │   └── 📄 __init__.py [0 lines]
  │   │   │   ├── 📁 test_cep/
  │   │   │   │   └── 📄 __init__.py [0 lines]
  │   │   │   ├── 📁 test_cmmn/
  │   │   │   │   └── 📄 __init__.py [0 lines]
  │   │   │   ├── 📁 test_core/
  │   │   │   │   └── 📄 __init__.py [0 lines]
  │   │   │   ├── 📁 test_dmn/
  │   │   │   │   └── 📄 __init__.py [0 lines]
  │   │   │   ├── 📁 test_multi_agent/
  │   │   │   │   └── 📄 __init__.py [0 lines]
  │   │   │   ├── 📁 test_state_machine/
  │   │   │   │   └── 📄 __init__.py [0 lines]
  │   │   │   └── 📄 __init__.py [0 lines]
  │   │   ├── 📁 utils/
  │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   ├── 📄 graph_utils.py [0 lines]
  │   │   │   ├── 📄 id_generator.py [0 lines]
  │   │   │   ├── 📄 json_parser.py [0 lines]
  │   │   │   ├── 📄 time_utils.py [0 lines]
  │   │   │   ├── 📄 type_converter.py [0 lines]
  │   │   │   └── 📄 xml_parser.py [0 lines]
  │   │   ├── 📁 validation/
  │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   ├── 📄 bpmn_validator.py [0 lines]
  │   │   │   ├── 📄 cmmn_validator.py [0 lines]
  │   │   │   ├── 📄 dmn_validator.py [0 lines]
  │   │   │   ├── 📄 semantic_validator.py [0 lines]
  │   │   │   ├── 📄 state_machine_validator.py [0 lines]
  │   │   │   └── 📄 validator.py [0 lines]
  │   │   └── 📄 __init__.py [0 lines]
  │   ├── 📁 rag/
  │   │   ├── 📁 agentic/
  │   │   │   ├── 📄 __init__.py [20 lines]
  │   │   │   ├── 📄 agent_v2.py [64 lines]
  │   │   │   ├── 📄 evidence_tracker.py [13 lines]
  │   │   │   ├── 📄 multihop_reasoner.py [18 lines]
  │   │   │   ├── 📄 query_decomposer.py [16 lines]
  │   │   │   ├── 📄 retrieval_agent.py [49 lines]
  │   │   │   └── 📄 uncertainty.py [23 lines]
  │   │   ├── 📁 compression/
  │   │   │   ├── 📄 __init__.py [11 lines]
  │   │   │   ├── 📄 base.py [11 lines]
  │   │   │   ├── 📄 embedding_compressor.py [54 lines]
  │   │   │   └── 📄 llm_compressor.py [41 lines]
  │   │   ├── 📁 evidence/
  │   │   │   ├── 📄 __init__.py [5 lines]
  │   │   │   └── 📄 evidence_clusterer.py [39 lines]
  │   │   ├── 📁 explain/
  │   │   │   ├── 📄 __init__.py [5 lines]
  │   │   │   └── 📄 retrieval_explainer.py [34 lines]
  │   │   ├── 📁 graph/
  │   │   │   ├── 📄 __init__.py [15 lines]
  │   │   │   ├── 📄 graph_builder.py [38 lines]
  │   │   │   ├── 📄 graph_models.py [16 lines]
  │   │   │   ├── 📄 graph_retriever.py [44 lines]
  │   │   │   └── 📄 graph_store.py [28 lines]
  │   │   ├── 📁 learning/
  │   │   │   ├── 📄 __init__.py [5 lines]
  │   │   │   └── 📄 retrieval_policy.py [39 lines]
  │   │   ├── 📁 llm/
  │   │   │   ├── 📄 __init__.py [14 lines]
  │   │   │   ├── 📄 base_llm.py [14 lines]
  │   │   │   ├── 📄 llm_factory.py [13 lines]
  │   │   │   ├── 📄 llm_protocols.py [11 lines]
  │   │   │   ├── 📄 ollama_llm.py [48 lines]
  │   │   │   └── 📄 openai_llm.py [37 lines]
  │   │   ├── 📁 planner/
  │   │   │   ├── 📄 __init__.py [8 lines]
  │   │   │   ├── 📄 adaptive_planner.py [52 lines]
  │   │   │   └── 📄 retrieval_plan.py [12 lines]
  │   │   ├── 📁 reflection/
  │   │   │   ├── 📄 __init__.py [8 lines]
  │   │   │   ├── 📄 reflection_critic.py [26 lines]
  │   │   │   └── 📄 reflection_loop.py [72 lines]
  │   │   ├── 📁 reranking/
  │   │   │   ├── 📄 __init__.py [8 lines]
  │   │   │   ├── 📄 base_reranker.py [13 lines]
  │   │   │   └── 📄 reranker.py [34 lines]
  │   │   ├── 📁 research/
  │   │   │   ├── 📁 autonomous/
  │   │   │   │   ├── 📄 __init__.py [14 lines]
  │   │   │   │   ├── 📄 coverage_scorer.py [45 lines]
  │   │   │   │   ├── 📄 gap_detector.py [48 lines]
  │   │   │   │   ├── 📄 query_generator.py [38 lines]
  │   │   │   │   └── 📄 research_loop.py [54 lines]
  │   │   │   ├── 📁 dashboard/
  │   │   │   │   ├── 📄 __init__.py [17 lines]
  │   │   │   │   ├── 📄 api_server.py [58 lines]
  │   │   │   │   ├── 📄 schema.py [50 lines]
  │   │   │   │   └── 📄 websocket_stream.py [37 lines]
  │   │   │   ├── 📁 evaluation/
  │   │   │   │   ├── 📄 __init__.py [31 lines]
  │   │   │   │   ├── 📄 citation_evaluator.py [17 lines]
  │   │   │   │   ├── 📄 completeness_evaluator.py [14 lines]
  │   │   │   │   ├── 📄 coverage_scorer.py [13 lines]
  │   │   │   │   ├── 📄 evaluation_controller.py [58 lines]
  │   │   │   │   ├── 📄 hallucination_detector.py [16 lines]
  │   │   │   │   ├── 📄 improvement_engine.py [31 lines]
  │   │   │   │   ├── 📄 reasoning_evaluator.py [13 lines]
  │   │   │   │   ├── 📄 retrieval_evaluator.py [27 lines]
  │   │   │   │   └── 📄 schema.py [27 lines]
  │   │   │   ├── 📁 graph/
  │   │   │   │   ├── 📄 __init__.py [30 lines]
  │   │   │   │   ├── 📄 entity_extractor.py [82 lines]
  │   │   │   │   ├── 📄 graph_aware_planner.py [33 lines]
  │   │   │   │   ├── 📄 graph_canonicalizer.py [20 lines]
  │   │   │   │   ├── 📄 graph_index.py [82 lines]
  │   │   │   │   ├── 📄 graph_persistence.py [63 lines]
  │   │   │   │   ├── 📄 graph_traverser.py [8 lines]
  │   │   │   │   ├── 📄 relation_builder.py [115 lines]
  │   │   │   │   └── 📄 relation_ranker.py [30 lines]
  │   │   │   ├── 📁 guardrails/
  │   │   │   │   ├── 📄 __init__.py [5 lines]
  │   │   │   │   └── 📄 hallucination_guard.py [13 lines]
  │   │   │   ├── 📁 improvement/
  │   │   │   │   ├── 📄 __init__.py [5 lines]
  │   │   │   │   └── 📄 feedback_controller.py [32 lines]
  │   │   │   ├── 📁 memory/
  │   │   │   │   ├── 📁 reasoning/
  │   │   │   │   │   ├── 📄 __init__.py [25 lines]
  │   │   │   │   │   ├── 📄 event_types.py [28 lines]
  │   │   │   │   │   ├── 📄 reasoning_event.py [32 lines]
  │   │   │   │   │   ├── 📄 reasoning_exporter.py [35 lines]
  │   │   │   │   │   ├── 📄 reasoning_memory.py [303 lines]
  │   │   │   │   │   ├── 📄 reasoning_node.py [49 lines]
  │   │   │   │   │   ├── 📄 reasoning_recorder.py [59 lines]
  │   │   │   │   │   └── 📄 reasoning_tree.py [51 lines]
  │   │   │   │   ├── 📄 __init__.py [19 lines]
  │   │   │   │   ├── 📄 memory_controller.py [49 lines]
  │   │   │   │   ├── 📄 memory_retriever.py [39 lines]
  │   │   │   │   ├── 📄 memory_store.py [38 lines]
  │   │   │   │   ├── 📄 reasoning_memory.py [150 lines]
  │   │   │   │   └── 📄 temporal_graph.py [31 lines]
  │   │   │   ├── 📁 observability/
  │   │   │   │   ├── 📄 __init__.py [30 lines]
  │   │   │   │   ├── 📄 failure_analyzer.py [16 lines]
  │   │   │   │   ├── 📄 graph_visualizer.py [13 lines]
  │   │   │   │   ├── 📄 memory_usage_tracker.py [17 lines]
  │   │   │   │   ├── 📄 metrics_store.py [18 lines]
  │   │   │   │   ├── 📄 observability_controller.py [31 lines]
  │   │   │   │   ├── 📄 retrieval_heatmap.py [20 lines]
  │   │   │   │   ├── 📄 telemetry.py [24 lines]
  │   │   │   │   ├── 📄 token_tracker.py [20 lines]
  │   │   │   │   └── 📄 trace_collector.py [24 lines]
  │   │   │   ├── 📁 summarization/
  │   │   │   │   ├── 📄 __init__.py [11 lines]
  │   │   │   │   ├── 📄 base_summarizer.py [21 lines]
  │   │   │   │   ├── 📄 research_summarizer.py [90 lines]
  │   │   │   │   └── 📄 section_summarizer.py [66 lines]
  │   │   │   ├── 📄 __init__.py [18 lines]
  │   │   │   ├── 📄 answer_planner.py [107 lines]
  │   │   │   ├── 📄 base_research_agent.py [11 lines]
  │   │   │   ├── 📄 citation_manager.py [80 lines]
  │   │   │   └── 📄 research_agent.py [149 lines]
  │   │   ├── 📁 retrieval/
  │   │   │   ├── 📄 __init__.py [39 lines]
  │   │   │   ├── 📄 base_retriever.py [13 lines]
  │   │   │   ├── 📄 bm25_retriever.py [88 lines]
  │   │   │   ├── 📄 hybrid_retriever.py [102 lines]
  │   │   │   ├── 📄 hybrid_retriever_plus.py [157 lines]
  │   │   │   ├── 📄 hybrid_retriever_super.py [185 lines]
  │   │   │   ├── 📄 keyword_retriever.py [35 lines]
  │   │   │   ├── 📄 retrieval_feedback_buffer.py [34 lines]
  │   │   │   ├── 📄 retriever_result.py [15 lines]
  │   │   │   ├── 📄 retriever_trainer.py [48 lines]
  │   │   │   ├── 📄 topk_optimizer.py [20 lines]
  │   │   │   ├── 📄 vector_retriever.py [53 lines]
  │   │   │   └── 📄 weight_manager.py [27 lines]
  │   │   ├── 📁 services/
  │   │   │   ├── 📄 __init__.py [11 lines]
  │   │   │   ├── 📄 chunking.py [64 lines]
  │   │   │   ├── 📄 embedding.py [62 lines]
  │   │   │   └── 📄 query_rewriter.py [28 lines]
  │   │   ├── 📁 trainer/
  │   │   │   ├── 📄 __init__.py [11 lines]
  │   │   │   ├── 📄 base_trainer.py [10 lines]
  │   │   │   ├── 📄 fusion_trainer.py [38 lines]
  │   │   │   └── 📄 reranker_trainer.py [24 lines]
  │   │   ├── 📄 __init__.py [11 lines]
  │   │   ├── 📄 rag_models.py [23 lines]
  │   │   └── 📄 vector_service.py [207 lines]
  │   ├── 📁 storage/
  │   │   ├── 📁 cache/
  │   │   │   ├── 📁 backends/
  │   │   │   │   ├── 📄 __init__.py [8 lines]
  │   │   │   │   ├── 📄 memory_adapter.py [54 lines]
  │   │   │   │   └── 📄 redis_adapter.py [69 lines]
  │   │   │   ├── 📄 __init__.py [5 lines]
  │   │   │   └── 📄 base.py [38 lines]
  │   │   ├── 📁 event_log/
  │   │   │   ├── 📁 backends/
  │   │   │   │   ├── 📄 __init__.py [8 lines]
  │   │   │   │   ├── 📄 rsyslog.py [62 lines]
  │   │   │   │   └── 📄 sql_event_log.py [47 lines]
  │   │   │   ├── 📄 __init__.py [5 lines]
  │   │   │   └── 📄 base.py [35 lines]
  │   │   ├── 📁 graph/
  │   │   │   ├── 📁 backends/
  │   │   │   │   ├── 📄 __init__.py [5 lines]
  │   │   │   │   └── 📄 neo4j_adapter.py [101 lines]
  │   │   │   ├── 📄 __init__.py [5 lines]
  │   │   │   └── 📄 base.py [33 lines]
  │   │   ├── 📁 key_value/
  │   │   │   ├── 📁 backends/
  │   │   │   │   ├── 📄 __init__.py [9 lines]
  │   │   │   │   ├── 📄 memory_adapter.py [41 lines]
  │   │   │   │   └── 📄 redis_adapter.py [190 lines]
  │   │   │   ├── 📄 __init__.py [5 lines]
  │   │   │   └── 📄 base.py [38 lines]
  │   │   ├── 📁 object/
  │   │   │   ├── 📁 backends/
  │   │   │   │   ├── 📄 __init__.py [11 lines]
  │   │   │   │   ├── 📄 filesystem_adapter.py [52 lines]
  │   │   │   │   ├── 📄 minio_adapter.py [141 lines]
  │   │   │   │   └── 📄 s3_adapter.py [102 lines]
  │   │   │   ├── 📄 __init__.py [5 lines]
  │   │   │   └── 📄 base.py [43 lines]
  │   │   ├── 📁 relational/
  │   │   │   ├── 📁 backends/
  │   │   │   │   ├── 📄 __init__.py [14 lines]
  │   │   │   │   ├── 📄 mysql_adapter.py [7 lines]
  │   │   │   │   ├── 📄 postgres_adapter.py [86 lines]
  │   │   │   │   ├── 📄 sql_server_adapter.py [7 lines]
  │   │   │   │   └── 📄 sqlite_adapter.py [63 lines]
  │   │   │   ├── 📄 __init__.py [6 lines]
  │   │   │   └── 📄 base.py [103 lines]
  │   │   ├── 📁 stream/
  │   │   │   ├── 📁 backends/
  │   │   │   │   ├── 📄 __init__.py [9 lines]
  │   │   │   │   ├── 📄 kafka_adapter.py [70 lines]
  │   │   │   │   └── 📄 redis_stream_adapter.py [241 lines]
  │   │   │   ├── 📄 __init__.py [5 lines]
  │   │   │   └── 📄 base.py [33 lines]
  │   │   ├── 📁 timeseries/
  │   │   │   ├── 📁 backends/
  │   │   │   │   ├── 📄 __init__.py [5 lines]
  │   │   │   │   └── 📄 influx_adapter.py [110 lines]
  │   │   │   ├── 📄 __init__.py [5 lines]
  │   │   │   └── 📄 base.py [36 lines]
  │   │   ├── 📁 vector/
  │   │   │   ├── 📁 backends/
  │   │   │   │   ├── 📄 __init__.py [20 lines]
  │   │   │   │   ├── 📄 chroma_adapter.py [125 lines]
  │   │   │   │   ├── 📄 faiss_adapter.py [181 lines]
  │   │   │   │   ├── 📄 memory_adapter.py [109 lines]
  │   │   │   │   ├── 📄 pinecone_adapter.py [180 lines]
  │   │   │   │   ├── 📄 qdrant_adapter.py [219 lines]
  │   │   │   │   └── 📄 weaviate_adapter.py [143 lines]
  │   │   │   ├── 📄 __init__.py [13 lines]
  │   │   │   ├── 📄 base.py [107 lines]
  │   │   │   ├── 📄 embedding_utils.py [12 lines]
  │   │   │   └── 📄 index_config.py [16 lines]
  │   │   ├── 📄 __init__.py [5 lines]
  │   │   └── 📄 base_storage.py [39 lines]
  │   ├── 📁 tools/
  │   │   ├── 📁 adapters/
  │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   ├── 📄 ai_model_executor.py [0 lines]
  │   │   │   ├── 📄 cli_executor.py [0 lines]
  │   │   │   ├── 📄 composite_executor.py [0 lines]
  │   │   │   ├── 📄 db_query_executor.py [0 lines]
  │   │   │   ├── 📄 file_executor.py [0 lines]
  │   │   │   ├── 📄 grpc_tool_executor.py [0 lines]
  │   │   │   ├── 📄 http_service_executor.py [0 lines]
  │   │   │   ├── 📄 http_tool_executor.py [0 lines]
  │   │   │   ├── 📄 mcp_tool_executor.py [0 lines]
  │   │   │   ├── 📄 message_bus_executor.py [0 lines]
  │   │   │   ├── 📄 mib_snmp_executor.py [0 lines]
  │   │   │   ├── 📄 python_function_executor.py [0 lines]
  │   │   │   ├── 📄 tcp_socket_executor.py [0 lines]
  │   │   │   └── 📄 yang_netconf_executor.py [0 lines]
  │   │   ├── 📄 __init__.py [0 lines]
  │   │   ├── 📄 base_executor.py [0 lines]
  │   │   ├── 📄 parameter_mapper.py [0 lines]
  │   │   └── 📄 tool_registry.py [0 lines]
  │   └── 📄 __init__.py [0 lines]
  ├── 📁 migrations/
  │   ├── 📄 __init__.py [6 lines]
  │   └── 📄 env.py [78 lines]
  ├── 📁 tests/
  │   ├── 📁 agents/
  │   │   ├── 📁 agents_unit/
  │   │   │   ├── 📄 __init__.py [14 lines]
  │   │   │   ├── 📄 test_agent_registry.py [60 lines]
  │   │   │   ├── 📄 test_base_agent.py [87 lines]
  │   │   │   └── 📄 test_message_bus.py [49 lines]
  │   │   ├── 📁 interaction/
  │   │   │   ├── 📁 interaction_performance/
  │   │   │   │   ├── 📄 __init__.py [15 lines]
  │   │   │   │   ├── 📄 conftest_performance.py [15 lines]
  │   │   │   │   ├── 📄 test_broadcast_strategy_performance.py [31 lines]
  │   │   │   │   ├── 📄 test_coordinator_strategy_performance.py [30 lines]
  │   │   │   │   ├── 📄 test_debate_strategy_performance.py [30 lines]
  │   │   │   │   ├── 📄 test_ensemble_strategy_performance.py [30 lines]
  │   │   │   │   ├── 📄 test_group_chat_strategy_performance.py [27 lines]
  │   │   │   │   ├── 📄 test_interaction_agent_performance.py [41 lines]
  │   │   │   │   ├── 📄 test_native_interaction_backend_performance.py [37 lines]
  │   │   │   │   └── 📄 test_self_refine_strategy_performance.py [35 lines]
  │   │   │   ├── 📁 interaction_unit/
  │   │   │   │   ├── 📄 __init__.py [26 lines]
  │   │   │   │   ├── 📄 conftest.py [66 lines]
  │   │   │   │   ├── 📄 test_autogen_interaction_backend.py [73 lines]
  │   │   │   │   ├── 📄 test_broadcast_strategy.py [47 lines]
  │   │   │   │   ├── 📄 test_coordinator_strategy.py [67 lines]
  │   │   │   │   ├── 📄 test_debate_strategy.py [46 lines]
  │   │   │   │   ├── 📄 test_ensemble_strategy.py [47 lines]
  │   │   │   │   ├── 📄 test_group_chat_strategy.py [34 lines]
  │   │   │   │   ├── 📄 test_interaction_agent.py [50 lines]
  │   │   │   │   ├── 📄 test_models.py [31 lines]
  │   │   │   │   ├── 📄 test_native_interaction_backend.py [142 lines]
  │   │   │   │   └── 📄 test_self_refine_strategy.py [50 lines]
  │   │   │   └── 📄 __init__.py [0 lines]
  │   │   └── 📄 __init__.py [0 lines]
  │   └── 📄 __init__.py [0 lines]
  └── 📁 tools/
      ├── 📄 __init__.py [131 lines]
      ├── 📄 ai_fixer.py [372 lines]
      ├── 📄 analyze_architecture.py [434 lines]
      ├── 📄 clean_pycache.py [21 lines]
      ├── 📄 code_auditor.py [537 lines]
      ├── 📄 count_mypy_errors.py [38 lines]
      ├── 📄 generate_inits.py [250 lines]
      ├── 📄 mypy_batcher.py [99 lines]
      ├── 📄 restore_py_modules.py [96 lines]
      ├── 📄 test_ai.py [23 lines]
      └── 📄 upgrade.py [2044 lines]
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
| `engines/document/models/csdm_entities.py` | `CadConstraintType` | `Enum` | `` |
| `engines/document/models/csdm_entities.py` | `GeometricConstraintEntity` | `BaseEntity` | `` |
| `engines/document/models/csdm_entities.py` | `DimConstraintKind` | `Enum` | `` |
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
| `engines/document/models/dsdm_models.py` | `DataValue` | `BaseModel` | `` |
| `engines/document/models/dsdm_models.py` | `DataSchemaReference` | `BaseModel` | `` |
| `engines/document/models/dsdm_models.py` | `DataDocumentCapabilities` | `BaseModel` | `` |
| `engines/document/models/dsdm_models.py` | `SchemaBinding` | `BaseModel` | `check_one_binding` |
| `engines/document/models/dsdm_models.py` | `DataNode` | `BaseModel` | `is_leaf` |
| `engines/document/models/dsdm_models.py` | `DataDocument` | `BaseDocument` | `validate_against_schema, _validate_node, _check_attribute_constraints, infer_msdm, _entity_from_node, _attribute_from_child ...` |
| `engines/document/models/esdm_models.py` | `ESDMDocument` | `BaseDocument` | `` |
| `engines/document/models/esdm_models.py` | `DocumentBaseModel` | `—` | `` |
| `engines/document/models/esdm_models.py` | `WorkbookProperties` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `ExcelRelationship` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `RelationshipCollection` | `DocumentBaseModel` | `add, find_by_type` |
| `engines/document/models/esdm_models.py` | `SharedStrings` | `DocumentBaseModel` | `get_index` |
| `engines/document/models/esdm_models.py` | `CellFormula` | `DocumentBaseModel` | `create, get` |
| `engines/document/models/esdm_models.py` | `Cell` | `DocumentBaseModel` | `coordinate, _col_to_letter` |
| `engines/document/models/esdm_models.py` | `Row` | `DocumentBaseModel` | `get_or_create_cell` |
| `engines/document/models/esdm_models.py` | `Column` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `CellRange` | `DocumentBaseModel` | `coord, _coord` |
| `engines/document/models/esdm_models.py` | `MergedCellRange` | `CellRange` | `` |
| `engines/document/models/esdm_models.py` | `NamedRange` | `DocumentBaseModel` | `` |
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
| `engines/document/models/esdm_models.py` | `CellStyle` | `CharacterStyle` | `` |
| `engines/document/models/esdm_models.py` | `DifferentialFormat` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `TableStyleElement` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `ExcelTableStyle` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `SpreadsheetStyleSheet` | `StyleSheet` | `` |
| `engines/document/models/esdm_models.py` | `DynamicFilterType` | `Enum` | `` |
| `engines/document/models/esdm_models.py` | `FilterOperator` | `Enum` | `` |
| `engines/document/models/esdm_models.py` | `CustomFilter` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `Filters` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `FilterColumn` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `AutoFilter` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `TableColumn` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `ExcelTableRow` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `TableStyleInfo` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `Table` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `CFType` | `Enum` | `` |
| `engines/document/models/esdm_models.py` | `CFOperator` | `Enum` | `` |
| `engines/document/models/esdm_models.py` | `CFValueObject` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `ColorScale` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `DataBar` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `IconSetType` | `Enum` | `` |
| `engines/document/models/esdm_models.py` | `IconCriterion` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `IconSet` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `CFRule` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `ConditionalFormatting` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `FormulaTokenType` | `Enum` | `` |
| `engines/document/models/esdm_models.py` | `FormulaToken` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `FormulaAST` | `DocumentBaseModel` | `from_string, to_string` |
| `engines/document/models/esdm_models.py` | `SharedFormula` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `DefinedName` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `ExternalReference` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `ExternalLink` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `DataValidationType` | `Enum` | `` |
| `engines/document/models/esdm_models.py` | `DataValidationOperator` | `Enum` | `` |
| `engines/document/models/esdm_models.py` | `DataValidationRule` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `DataValidation` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `Hyperlink` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `Author` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `CommentTextRun` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `CommentText` | `DocumentBaseModel` | `from_string` |
| `engines/document/models/esdm_models.py` | `Comment` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `CommentCollection` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `ThreadedComment` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `SheetProperties` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `SheetProtection` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `Orientation` | `Enum` | `` |
| `engines/document/models/esdm_models.py` | `PageMargins` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `PageSetup` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `SheetDimensions` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `CalcChainEntry` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `CalculationChain` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `PivotField` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `PivotCacheReference` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `PivotCache` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `PivotTable` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `Worksheet` | `DocumentBaseModel` | `get_row, get_cell, merge_cells` |
| `engines/document/models/esdm_models.py` | `Workbook` | `DocumentBaseModel` | `add_sheet, get_sheet_by_name` |
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
| `engines/document/models/msdm_capabilities.py` | `ScalarSupport` | `str, Enum` | `` |
| `engines/document/models/msdm_capabilities.py` | `CompositeSupport` | `str, Enum` | `` |
| `engines/document/models/msdm_capabilities.py` | `ConstraintCapability` | `str, Enum` | `` |
| `engines/document/models/msdm_capabilities.py` | `IndexCapability` | `str, Enum` | `` |
| `engines/document/models/msdm_capabilities.py` | `NestingDepth` | `str, Enum` | `` |
| `engines/document/models/msdm_capabilities.py` | `InheritanceSupport` | `str, Enum` | `` |
| `engines/document/models/msdm_capabilities.py` | `RelationshipModel` | `str, Enum` | `` |
| `engines/document/models/msdm_capabilities.py` | `AnnotationSupport` | `str, Enum` | `` |
| `engines/document/models/msdm_capabilities.py` | `TimeSeriesSupport` | `Flag` | `` |
| `engines/document/models/msdm_capabilities.py` | `NamespaceSupport` | `str, Enum` | `` |
| `engines/document/models/msdm_capabilities.py` | `EnumCapability` | `Flag` | `` |
| `engines/document/models/msdm_capabilities.py` | `MSDM_FormatCapability` | `—` | `` |
| `engines/document/models/msdm_models.py` | `EntityKind` | `str, Enum` | `` |
| `engines/document/models/msdm_models.py` | `Cardinality` | `str, Enum` | `` |
| `engines/document/models/msdm_models.py` | `ConstraintType` | `str, Enum` | `` |
| `engines/document/models/msdm_models.py` | `ScalarType` | `str, Enum` | `` |
| `engines/document/models/msdm_models.py` | `IndexMethod` | `str, Enum` | `` |
| `engines/document/models/msdm_models.py` | `CompositionType` | `str, Enum` | `` |
| `engines/document/models/msdm_models.py` | `VersionStatus` | `str, Enum` | `` |
| `engines/document/models/msdm_models.py` | `VisibilityKind` | `str, Enum` | `` |
| `engines/document/models/msdm_models.py` | `DataType` | `—` | `` |
| `engines/document/models/msdm_models.py` | `Annotation` | `—` | `` |
| `engines/document/models/msdm_models.py` | `Constraint` | `—` | `` |
| `engines/document/models/msdm_models.py` | `Index` | `—` | `` |
| `engines/document/models/msdm_models.py` | `Attribute` | `—` | `` |
| `engines/document/models/msdm_models.py` | `Namespace` | `—` | `` |
| `engines/document/models/msdm_models.py` | `EntityComposition` | `—` | `` |
| `engines/document/models/msdm_models.py` | `Entity` | `—` | `` |
| `engines/document/models/msdm_models.py` | `EntityRelationship` | `—` | `` |
| `engines/document/models/msdm_models.py` | `MSDMDocument` | `BaseDocument` | `` |
| `engines/document/models/osdm_models.py` | `ParticipantBandKind` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `MessageVisibleKind` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `AlignmentKind` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `TransactionMethod` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `TimerCalculationType` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `TimeReference` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `DurationResolution` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `EscapeType` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `CorrelationPropertyType` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `CaseFileMultiplicity` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `EventListenerType` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `ActivityType` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `TaskType` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `SubProcessType` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `GatewayType` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `EventType` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `LoopType` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `MultiInstanceBehavior` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `AdHocOrdering` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `ScriptLanguage` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `CallActivityType` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `ProcessType` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `GatewayDirection` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `AssociationDirection` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `EventBasedGatewayType` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `ItemKind` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `TimerEventType` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `RelationshipDirection` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `CEPOperator` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `WorkflowStateType` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `ResourceParameterType` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `ResourceRoleType` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `PotentialOwnerType` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `InteractionNodeType` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `EventDefinitionType` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `ChoreographyLoopType` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `DecisionLogicType` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `PseudoStateKind` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `InteractionStrategy` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `BaseElement` | `—` | `` |
| `engines/document/models/osdm_models.py` | `RootElement` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `StateNode` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `Transition` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `ExtensionAttributeDefinition` | `—` | `` |
| `engines/document/models/osdm_models.py` | `ExtensionDefinition` | `—` | `` |
| `engines/document/models/osdm_models.py` | `ExtensionAttributeValue` | `—` | `` |
| `engines/document/models/osdm_models.py` | `Extension` | `—` | `` |
| `engines/document/models/osdm_models.py` | `Bounds` | `—` | `` |
| `engines/document/models/osdm_models.py` | `Locator` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `DiagramElement` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `Edge` | `DiagramElement` | `` |
| `engines/document/models/osdm_models.py` | `Shape` | `DiagramElement` | `` |
| `engines/document/models/osdm_models.py` | `BPMNDiagram` | `—` | `` |
| `engines/document/models/osdm_models.py` | `BPMNPlane` | `DiagramElement` | `` |
| `engines/document/models/osdm_models.py` | `BPMNShape` | `Shape` | `` |
| `engines/document/models/osdm_models.py` | `BPMNEdge` | `Edge` | `` |
| `engines/document/models/osdm_models.py` | `BPMNLabel` | `—` | `` |
| `engines/document/models/osdm_models.py` | `BpmnExpression` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `FormalExpression` | `BpmnExpression` | `` |
| `engines/document/models/osdm_models.py` | `ItemDefinition` | `RootElement` | `` |
| `engines/document/models/osdm_models.py` | `Resource` | `RootElement` | `` |
| `engines/document/models/osdm_models.py` | `ResourceParameter` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `ResourceAssignmentExpression` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `ResourceParameterBinding` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `ResourceRole` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `HumanPerformer` | `ResourceRole` | `` |
| `engines/document/models/osdm_models.py` | `Performer` | `HumanPerformer` | `` |
| `engines/document/models/osdm_models.py` | `PotentialOwner` | `HumanPerformer` | `` |
| `engines/document/models/osdm_models.py` | `FlowElement` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `FlowNode` | `FlowElement` | `` |
| `engines/document/models/osdm_models.py` | `Activity` | `FlowNode` | `` |
| `engines/document/models/osdm_models.py` | `Task` | `Activity` | `` |
| `engines/document/models/osdm_models.py` | `ServiceTask` | `Task` | `` |
| `engines/document/models/osdm_models.py` | `SendTask` | `Task` | `` |
| `engines/document/models/osdm_models.py` | `ReceiveTask` | `Task` | `` |
| `engines/document/models/osdm_models.py` | `UserTask` | `Task` | `` |
| `engines/document/models/osdm_models.py` | `ManualTask` | `Task` | `` |
| `engines/document/models/osdm_models.py` | `Script` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `ScriptTask` | `Task` | `` |
| `engines/document/models/osdm_models.py` | `BusinessRuleTask` | `Task` | `` |
| `engines/document/models/osdm_models.py` | `CallActivity` | `Activity` | `` |
| `engines/document/models/osdm_models.py` | `SubProcess` | `Activity` | `` |
| `engines/document/models/osdm_models.py` | `TransactionSubProcess` | `SubProcess` | `` |
| `engines/document/models/osdm_models.py` | `AdHocSubProcess` | `SubProcess` | `` |
| `engines/document/models/osdm_models.py` | `GlobalTask` | `RootElement` | `` |
| `engines/document/models/osdm_models.py` | `GlobalUserTask` | `GlobalTask` | `` |
| `engines/document/models/osdm_models.py` | `GlobalScriptTask` | `GlobalTask` | `` |
| `engines/document/models/osdm_models.py` | `GlobalManualTask` | `GlobalTask` | `` |
| `engines/document/models/osdm_models.py` | `GlobalBusinessRuleTask` | `GlobalTask` | `` |
| `engines/document/models/osdm_models.py` | `Rendering` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `RenderingForm` | `Rendering` | `` |
| `engines/document/models/osdm_models.py` | `LoopCharacteristics` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `StandardLoopCharacteristics` | `LoopCharacteristics` | `` |
| `engines/document/models/osdm_models.py` | `MultiInstanceLoopCharacteristics` | `LoopCharacteristics` | `` |
| `engines/document/models/osdm_models.py` | `ComplexBehaviorDefinition` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `InputOutputSpecification` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `DataInput` | `—` | `` |
| `engines/document/models/osdm_models.py` | `DataOutput` | `—` | `` |
| `engines/document/models/osdm_models.py` | `InputSet` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `OutputSet` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `DataInputRef` | `—` | `` |
| `engines/document/models/osdm_models.py` | `DataOutputRef` | `—` | `` |
| `engines/document/models/osdm_models.py` | `InputOutputBinding` | `—` | `` |
| `engines/document/models/osdm_models.py` | `Event` | `FlowNode` | `` |
| `engines/document/models/osdm_models.py` | `CatchEvent` | `Event` | `` |
| `engines/document/models/osdm_models.py` | `ThrowEvent` | `Event` | `` |
| `engines/document/models/osdm_models.py` | `StartEvent` | `CatchEvent` | `` |
| `engines/document/models/osdm_models.py` | `EndEvent` | `ThrowEvent` | `` |
| `engines/document/models/osdm_models.py` | `IntermediateCatchEvent` | `CatchEvent` | `` |
| `engines/document/models/osdm_models.py` | `IntermediateThrowEvent` | `ThrowEvent` | `` |
| `engines/document/models/osdm_models.py` | `BoundaryEvent` | `CatchEvent` | `` |
| `engines/document/models/osdm_models.py` | `ImplicitThrowEvent` | `ThrowEvent` | `` |
| `engines/document/models/osdm_models.py` | `EventDefinition` | `RootElement` | `` |
| `engines/document/models/osdm_models.py` | `MessageEventDefinition` | `EventDefinition` | `` |
| `engines/document/models/osdm_models.py` | `TimerEventDefinition` | `EventDefinition` | `` |
| `engines/document/models/osdm_models.py` | `SignalEventDefinition` | `EventDefinition` | `` |
| `engines/document/models/osdm_models.py` | `ErrorEventDefinition` | `EventDefinition` | `` |
| `engines/document/models/osdm_models.py` | `EscalationEventDefinition` | `EventDefinition` | `` |
| `engines/document/models/osdm_models.py` | `CompensateEventDefinition` | `EventDefinition` | `` |
| `engines/document/models/osdm_models.py` | `ConditionalEventDefinition` | `EventDefinition` | `` |
| `engines/document/models/osdm_models.py` | `LinkEventDefinition` | `EventDefinition` | `` |
| `engines/document/models/osdm_models.py` | `CancelEventDefinition` | `EventDefinition` | `` |
| `engines/document/models/osdm_models.py` | `TerminateEventDefinition` | `EventDefinition` | `` |
| `engines/document/models/osdm_models.py` | `DueTimeDuration` | `—` | `` |
| `engines/document/models/osdm_models.py` | `DataFlowElement` | `FlowElement` | `` |
| `engines/document/models/osdm_models.py` | `DataObject` | `DataFlowElement` | `` |
| `engines/document/models/osdm_models.py` | `DataObjectReference` | `DataFlowElement` | `` |
| `engines/document/models/osdm_models.py` | `DataStore` | `RootElement` | `` |
| `engines/document/models/osdm_models.py` | `DataStoreReference` | `DataFlowElement` | `` |
| `engines/document/models/osdm_models.py` | `DataState` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `DataElement` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `Property` | `DataElement` | `` |
| `engines/document/models/osdm_models.py` | `DataAssociation` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `DataInputAssociation` | `DataAssociation` | `` |
| `engines/document/models/osdm_models.py` | `DataOutputAssociation` | `DataAssociation` | `` |
| `engines/document/models/osdm_models.py` | `Assignment` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `SequenceFlow` | `FlowElement` | `` |
| `engines/document/models/osdm_models.py` | `MessageFlow` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `Gateway` | `FlowNode` | `` |
| `engines/document/models/osdm_models.py` | `ExclusiveGateway` | `Gateway` | `` |
| `engines/document/models/osdm_models.py` | `InclusiveGateway` | `Gateway` | `` |
| `engines/document/models/osdm_models.py` | `ParallelGateway` | `Gateway` | `` |
| `engines/document/models/osdm_models.py` | `EventBasedGateway` | `Gateway` | `` |
| `engines/document/models/osdm_models.py` | `ComplexGateway` | `Gateway` | `` |
| `engines/document/models/osdm_models.py` | `Lane` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `LaneSet` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `Process` | `RootElement` | `` |
| `engines/document/models/osdm_models.py` | `Collaboration` | `RootElement` | `` |
| `engines/document/models/osdm_models.py` | `Artifact` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `Association` | `Artifact` | `` |
| `engines/document/models/osdm_models.py` | `Group` | `Artifact` | `` |
| `engines/document/models/osdm_models.py` | `TextAnnotation` | `Artifact` | `` |
| `engines/document/models/osdm_models.py` | `Auditing` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `Monitoring` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `Interface` | `RootElement` | `` |
| `engines/document/models/osdm_models.py` | `Operation` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `EndPoint` | `RootElement` | `` |
| `engines/document/models/osdm_models.py` | `Message` | `RootElement` | `` |
| `engines/document/models/osdm_models.py` | `Signal` | `RootElement` | `` |
| `engines/document/models/osdm_models.py` | `Error` | `RootElement` | `` |
| `engines/document/models/osdm_models.py` | `Escalation` | `RootElement` | `` |
| `engines/document/models/osdm_models.py` | `CorrelationKey` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `CorrelationProperty` | `RootElement` | `` |
| `engines/document/models/osdm_models.py` | `CorrelationPropertyRetrievalExpression` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `CorrelationSubscription` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `CorrelationPropertyBinding` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `Category` | `RootElement` | `` |
| `engines/document/models/osdm_models.py` | `CategoryValue` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `InteractionNode` | `—` | `` |
| `engines/document/models/osdm_models.py` | `MessageFlowAssociation` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `Participant` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `ParticipantMultiplicity` | `—` | `` |
| `engines/document/models/osdm_models.py` | `ParticipantAssociation` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `PartnerEntity` | `RootElement` | `` |
| `engines/document/models/osdm_models.py` | `PartnerRole` | `RootElement` | `` |
| `engines/document/models/osdm_models.py` | `ConversationNode` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `Conversation` | `ConversationNode` | `` |
| `engines/document/models/osdm_models.py` | `CallConversation` | `ConversationNode` | `` |
| `engines/document/models/osdm_models.py` | `GlobalConversation` | `ConversationNode` | `` |
| `engines/document/models/osdm_models.py` | `SubConversation` | `ConversationNode` | `` |
| `engines/document/models/osdm_models.py` | `ConversationAssociation` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `ConversationLink` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `ChoreographyActivity` | `FlowNode` | `` |
| `engines/document/models/osdm_models.py` | `ChoreographyTask` | `ChoreographyActivity` | `` |
| `engines/document/models/osdm_models.py` | `CallChoreography` | `ChoreographyActivity` | `` |
| `engines/document/models/osdm_models.py` | `SubChoreography` | `ChoreographyActivity` | `` |
| `engines/document/models/osdm_models.py` | `Choreography` | `Collaboration` | `` |
| `engines/document/models/osdm_models.py` | `GlobalChoreographyTask` | `Choreography` | `` |
| `engines/document/models/osdm_models.py` | `PlanItem` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `DiscretionaryItem` | `PlanItem` | `` |
| `engines/document/models/osdm_models.py` | `CaseFileItem` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `CaseTask` | `Activity` | `` |
| `engines/document/models/osdm_models.py` | `ProcessTask` | `Activity` | `` |
| `engines/document/models/osdm_models.py` | `HumanTask` | `Activity` | `` |
| `engines/document/models/osdm_models.py` | `ApplicabilityRule` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `EntryCriterion` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `ExitCriterion` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `Stage` | `FlowNode` | `` |
| `engines/document/models/osdm_models.py` | `Milestone` | `FlowNode` | `` |
| `engines/document/models/osdm_models.py` | `EventListener` | `FlowNode` | `` |
| `engines/document/models/osdm_models.py` | `Sentry` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `CMMNDefinition` | `—` | `` |
| `engines/document/models/osdm_models.py` | `InformationRequirement` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `KnowledgeRequirement` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `AuthorityRequirement` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `DecisionService` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `Decision` | `FlowNode` | `` |
| `engines/document/models/osdm_models.py` | `BusinessKnowledgeModel` | `FlowNode` | `` |
| `engines/document/models/osdm_models.py` | `InputData` | `FlowNode` | `` |
| `engines/document/models/osdm_models.py` | `KnowledgeSource` | `FlowNode` | `` |
| `engines/document/models/osdm_models.py` | `DMNDefinition` | `—` | `` |
| `engines/document/models/osdm_models.py` | `ErrorHandlingOperator` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `RetryBackoffRate` | `float, Enum` | `` |
| `engines/document/models/osdm_models.py` | `CloudResourceBinding` | `—` | `` |
| `engines/document/models/osdm_models.py` | `ErrorHandlingConfig` | `—` | `` |
| `engines/document/models/osdm_models.py` | `RetryConfig` | `—` | `` |
| `engines/document/models/osdm_models.py` | `TimeoutConfig` | `—` | `` |
| `engines/document/models/osdm_models.py` | `State` | `StateNode` | `` |
| `engines/document/models/osdm_models.py` | `StateTransition` | `Transition` | `` |
| `engines/document/models/osdm_models.py` | `StateInvoke` | `—` | `` |
| `engines/document/models/osdm_models.py` | `StateMachineRegion` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `StateMachineModel` | `—` | `` |
| `engines/document/models/osdm_models.py` | `PseudoState` | `StateNode` | `` |
| `engines/document/models/osdm_models.py` | `Place` | `State` | `` |
| `engines/document/models/osdm_models.py` | `PnTransition` | `Transition` | `` |
| `engines/document/models/osdm_models.py` | `Arc` | `Transition` | `` |
| `engines/document/models/osdm_models.py` | `EventStream` | `—` | `` |
| `engines/document/models/osdm_models.py` | `CEPRule` | `—` | `` |
| `engines/document/models/osdm_models.py` | `CEPDefinition` | `—` | `` |
| `engines/document/models/osdm_models.py` | `InteractionProtocol` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `InteractionModel` | `—` | `` |
| `engines/document/models/osdm_models.py` | `BaseOSDMDocument` | `BaseDocument` | `` |
| `engines/document/models/osdm_models.py` | `BPMNDocument` | `BaseOSDMDocument` | `` |
| `engines/document/models/osdm_models.py` | `CMMNDocument` | `BaseOSDMDocument` | `` |
| `engines/document/models/osdm_models.py` | `StateMachineDocument` | `BaseOSDMDocument` | `` |
| `engines/document/models/osdm_models.py` | `DMNDocument` | `BaseOSDMDocument` | `` |
| `engines/document/models/osdm_models.py` | `CEPDocument` | `BaseOSDMDocument` | `` |
| `engines/document/models/osdm_models.py` | `MultiAgentInteractionDocument` | `BaseOSDMDocument` | `` |
| `engines/document/models/osdm_models.py` | `OSDMModel` | `—` | `` |
| `engines/document/models/osdm_models.py` | `SentryExpression` | `FormalExpression` | `` |
| `engines/document/models/osdm_models.py` | `DecisionTable` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `ActionList` | `BaseElement` | `` |
| `engines/document/models/psdm_models.py` | `PlaceholderType` | `str, Enum` | `` |
| `engines/document/models/psdm_models.py` | `TransitionType` | `str, Enum` | `` |
| `engines/document/models/psdm_models.py` | `AnimationType` | `str, Enum` | `` |
| `engines/document/models/psdm_models.py` | `TriggerType` | `str, Enum` | `` |
| `engines/document/models/psdm_models.py` | `ShowType` | `str, Enum` | `` |
| `engines/document/models/psdm_models.py` | `Placeholder` | `—` | `` |
| `engines/document/models/psdm_models.py` | `SlideLayout` | `—` | `` |
| `engines/document/models/psdm_models.py` | `SlideMaster` | `—` | `` |
| `engines/document/models/psdm_models.py` | `PresentationTransition` | `—` | `` |
| `engines/document/models/psdm_models.py` | `Animation` | `—` | `` |
| `engines/document/models/psdm_models.py` | `MediaReference` | `—` | `` |
| `engines/document/models/psdm_models.py` | `NotesSlide` | `—` | `` |
| `engines/document/models/psdm_models.py` | `SlideComment` | `—` | `` |
| `engines/document/models/psdm_models.py` | `Slide` | `—` | `` |
| `engines/document/models/psdm_models.py` | `PresentationProperties` | `—` | `` |
| `engines/document/models/psdm_models.py` | `Theme` | `—` | `` |
| `engines/document/models/psdm_models.py` | `HyperlinkAction` | `—` | `` |
| `engines/document/models/psdm_models.py` | `GroupShapeContent` | `—` | `` |
| `engines/document/models/psdm_models.py` | `ConnectorContent` | `—` | `` |
| `engines/document/models/psdm_models.py` | `PresentationSection` | `—` | `` |
| `engines/document/models/psdm_models.py` | `PSDMDocument` | `BaseDocument` | `` |
| `engines/document/models/ssdm_capabilities.py` | `ParameterNesting` | `str, Enum` | `` |
| `engines/document/models/ssdm_capabilities.py` | `BodyMediaType` | `str, Enum` | `` |
| `engines/document/models/ssdm_capabilities.py` | `SecurityFeature` | `str, Enum` | `` |
| `engines/document/models/ssdm_capabilities.py` | `TransportBinding` | `str, Enum` | `` |
| `engines/document/models/ssdm_capabilities.py` | `SchemaKind` | `str, Enum` | `` |
| `engines/document/models/ssdm_capabilities.py` | `OperationModel` | `str, Enum` | `` |
| `engines/document/models/ssdm_capabilities.py` | `FormatCapability` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `HttpMethod` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `ParameterLocation` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `AuthMethod` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `OAuth2Flow` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `ApiKeyLocation` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `OperationType` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `Transport` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `ValueSource` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `RetryPolicy` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `PortProtocol` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `HealthProbeType` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `PerformedBy` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `DiscoveryBackend` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `ServiceType` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `MeshRuleType` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `MessageFormat` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `SubscriptionType` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `InternalComponentType` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `CoordinationProtocol` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `ContactInfo` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `LicenseInfo` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `Server` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `Parameter` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `RequestBody` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `Link` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `Response` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `YangMetadata` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `ServiceOperation` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `SSDMDocument` | `BaseDocument` | `` |
| `engines/document/models/ssdm_models.py` | `SecurityRequirement` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `JWTValidation` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `AuthConfig` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `SlaPolicy` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `RateLimit` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `CORSConfig` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `GatewayRule` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `PortMapping` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `HTTPGetProbe` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `TCPSocketProbe` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `ExecProbe` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `GRPCProbe` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `HealthCheck` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `DiscoveryConfig` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `MeshRule` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `IngressRule` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `LoadBalancerConfig` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `ServiceExposure` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `DeploymentDescriptor` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `MessageBinding` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `ServiceBinding` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `MCPToolBinding` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `MCPResourceBinding` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `MCPPromptBinding` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `MCPNorthBoundBinding` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `ParameterMapping` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `ResponseMapping` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `InternalServiceBinding` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `NorthBoundBinding` | `ServiceBinding` | `` |
| `engines/document/models/ssdm_models.py` | `MCPClientToolBinding` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `MCPSouthBoundBinding` | `—` | `to_service_binding` |
| `engines/document/models/standard.py` | `DocumentStandard` | `str, Enum` | `full_name, description` |
| `engines/document/models/standard.py` | `MediaCategory` | `str, Enum` | `` |
| `engines/document/models/tsdm_models.py` | `ToolKind` | `str, Enum` | `` |
| `engines/document/models/tsdm_models.py` | `ParameterSource` | `str, Enum` | `` |
| `engines/document/models/tsdm_models.py` | `ParameterType` | `str, Enum` | `` |
| `engines/document/models/tsdm_models.py` | `LoadBalanceStrategy` | `str, Enum` | `` |
| `engines/document/models/tsdm_models.py` | `SnmpVersion` | `str, Enum` | `` |
| `engines/document/models/tsdm_models.py` | `NetconfProtocol` | `str, Enum` | `` |
| `engines/document/models/tsdm_models.py` | `ToolParameter` | `—` | `` |
| `engines/document/models/tsdm_models.py` | `ToolOutput` | `—` | `` |
| `engines/document/models/tsdm_models.py` | `Tool` | `—` | `` |
| `engines/document/models/tsdm_models.py` | `DbQueryTool` | `Tool` | `` |
| `engines/document/models/tsdm_models.py` | `DbStatementTool` | `Tool` | `` |
| `engines/document/models/tsdm_models.py` | `HttpServiceTool` | `Tool` | `` |
| `engines/document/models/tsdm_models.py` | `GrpcServiceTool` | `Tool` | `` |
| `engines/document/models/tsdm_models.py` | `GraphQLTool` | `Tool` | `` |
| `engines/document/models/tsdm_models.py` | `TcpSocketTool` | `Tool` | `` |
| `engines/document/models/tsdm_models.py` | `MessageBusTool` | `Tool` | `` |
| `engines/document/models/tsdm_models.py` | `CliTool` | `Tool` | `` |
| `engines/document/models/tsdm_models.py` | `PythonFunctionTool` | `Tool` | `` |
| `engines/document/models/tsdm_models.py` | `MCPTool` | `Tool` | `` |
| `engines/document/models/tsdm_models.py` | `YangNetconfTool` | `Tool` | `` |
| `engines/document/models/tsdm_models.py` | `MibSnmpTool` | `Tool` | `` |
| `engines/document/models/tsdm_models.py` | `FileReadTool` | `Tool` | `` |
| `engines/document/models/tsdm_models.py` | `FileWriteTool` | `Tool` | `` |
| `engines/document/models/tsdm_models.py` | `AiModelTool` | `Tool` | `` |
| `engines/document/models/tsdm_models.py` | `CompositeTool` | `Tool` | `` |
| `engines/document/models/tsdm_models.py` | `TSDMDocument` | `BaseDocument` | `` |
| `engines/document/models/usdm_models.py` | `USDMDocument` | `BaseDocument` | `` |
| `engines/document/models/usdm_models.py` | `DocumentElement` | `—` | `` |
| `engines/document/models/usdm_models.py` | `Section` | `—` | `` |
| `engines/document/models/usdm_models.py` | `PageContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `LogicalElement` | `—` | `_meta` |
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
| `engines/document/models/usdm_models.py` | `LaTeXEnvironmentContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `LaTeXCommandContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `SemanticHTMLContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `CanvasOperation` | `—` | `` |
| `engines/document/models/usdm_models.py` | `PDFInfo` | `—` | `` |
| `engines/document/models/usdm_models.py` | `DOCXProperties` | `—` | `` |
| `engines/document/models/usdm_models.py` | `Change` | `—` | `` |
| `engines/document/models/usdm_models.py` | `CanvasContent` | `—` | `` |
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
| `engines/document/models/usdm_models.py` | `ChartSeriesContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `ChartAxisContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `ChartContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `DataContent` | `—` | `` |
| `engines/document/models/usdm_models.py` | `SpreadsheetContent` | `—` | `` |
| `engines/document/parsers/base.py` | `ParseOptions` | `BaseModel` | `` |
| `engines/document/parsers/base.py` | `BaseDocumentParser` | `ABC` | `parse_bytes, parse_path, parse_stream, supports_extension, iter_supported_extensions` |
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
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXDiagram` | `—` | `__init__` |
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
| `engines/document/parsers/docx_parser/docx_parser.py` | `DOCXParser` | `—` | `__init__, _reset, _generate_element_id, _convert_table, _merge_consecutive_lists, parse ...` |
| `engines/document/parsers/docx_parser/docx_style_parser.py` | `DocxStyleParser` | `—` | `__init__, parse_styles, _parse_style, _parse_run_properties, _parse_paragraph_properties, _parse_table_properties` |
| `engines/document/parsers/docx_parser/docx_table_parser.py` | `DocxTableParser` | `—` | `__init__, parse_table, parse_all_tables` |
| `engines/document/parsers/docx_parser/docx_utils.py` | `DocxStyleInfo` | `—` | `__post_init__` |
| `engines/document/parsers/docx_parser/docx_utils.py` | `DocxNumberingInfo` | `—` | `__post_init__` |
| `engines/document/parsers/docx_parser/docx_utils.py` | `DocxUtils` | `—` | `extract_text_style, extract_paragraph_style, extract_style_properties, extract_numbering_definition, extract_text_from_element, convert_omml_to_latex ...` |
| `engines/document/parsers/drawingml/diagram_parser.py` | `DiagramNode` | `—` | `__init__` |
| `engines/document/parsers/dsdm_parsers/base_dsdm_parser.py` | `DSDMParseOptions` | `ParseOptions` | `` |
| `engines/document/parsers/dsdm_parsers/base_dsdm_parser.py` | `BaseDSDMParser` | `BaseDocumentParser` | `parse_bytes, _parse_to_datanode, _detect_media_type, _bind_schema, _bind_node, _coerce_default_value ...` |
| `engines/document/parsers/dsdm_parsers/binary_parser.py` | `BinaryParser` | `BaseDSDMParser` | `_parse_to_datanode, _detect_media_type` |
| `engines/document/parsers/dsdm_parsers/bson_parser.py` | `BSONParser` | `BinaryParser` | `_parse_to_datanode, _detect_media_type` |
| `engines/document/parsers/dsdm_parsers/cassandra_parser.py` | `CassandraParser` | `BaseDSDMParser` | `fetch_from_cassandra, _coerce_cassandra_value` |
| `engines/document/parsers/dsdm_parsers/cbor_parser.py` | `CBORParser` | `BinaryParser` | `_parse_to_datanode, _detect_media_type` |
| `engines/document/parsers/dsdm_parsers/csv_tsv_parser.py` | `CSVTSVParser` | `BaseDSDMParser` | `_parse_to_datanode, _coerce_value, _detect_media_type` |
| `engines/document/parsers/dsdm_parsers/json_parser.py` | `JSONParser` | `BaseDSDMParser` | `_parse_to_datanode, _detect_media_type` |
| `engines/document/parsers/dsdm_parsers/mongodb_parser.py` | `MongoDBParser` | `BSONParser` | `fetch_collection, _coerce_mongo_value, _mongo_field_to_node` |
| `engines/document/parsers/dsdm_parsers/msgpack_parser.py` | `MsgPackParser` | `BinaryParser` | `_parse_to_datanode, _detect_media_type` |
| `engines/document/parsers/dsdm_parsers/pickle_parser.py` | `PickleParser` | `BinaryParser` | `_parse_to_datanode, _detect_media_type` |
| `engines/document/parsers/dsdm_parsers/protobuf_parser.py` | `ProtobufParser` | `BaseDSDMParser` | `_parse_to_datanode, _detect_media_type` |
| `engines/document/parsers/dsdm_parsers/redis_parser.py` | `RedisParser` | `BaseDSDMParser` | `_parse_to_datanode, _detect_media_type, fetch_from_redis, _coerce_redis_value` |
| `engines/document/parsers/dsdm_parsers/sql_parser.py` | `AsyncDBConnection` | `Protocol` | `execute` |
| `engines/document/parsers/dsdm_parsers/sql_parser.py` | `SQLDataParser` | `BaseDSDMParser` | `_parse_to_datanode, _detect_media_type, fetch_from_database, _build_tree_from_rows, _coerce_value_from_db, _parse_default` |
| `engines/document/parsers/dsdm_parsers/xml_parser.py` | `XMLParser` | `BaseDSDMParser` | `_parse_to_datanode, _elem_to_datanode, _detect_media_type` |
| `engines/document/parsers/dsdm_parsers/yaml_parser.py` | `YAMLParser` | `BaseDSDMParser` | `_parse_to_datanode, _detect_media_type` |
| `engines/document/parsers/html_parser.py` | `HTMLDocumentParser` | `HTMLParser` | `__init__, _generate_id, _create_rich_text_span, _flush_current_text, handle_starttag, handle_endtag ...` |
| `engines/document/parsers/html_parser.py` | `HtmlParser` | `BaseDocumentParser` | `parse_bytes, parse_text, parse_stream, get_supported_media_types, get_supported_extensions, _extract_math_from_html` |
| `engines/document/parsers/latex_parser.py` | `LatexParser` | `BaseDocumentParser` | `__init__, parse_bytes, parse_stream, _reset_parser_state, _generate_id, _extract_title ...` |
| `engines/document/parsers/markdown_parser.py` | `MarkdownTreeProcessor` | `Treeprocessor` | `__init__, run, _generate_id, _process_node, _extract_text, _process_list ...` |
| `engines/document/parsers/markdown_parser.py` | `MarkdownExtension` | `Extension` | `extendMarkdown` |
| `engines/document/parsers/markdown_parser.py` | `MarkdownParser` | `BaseDocumentParser` | `__init__, parse_bytes, parse_stream` |
| `engines/document/parsers/msdm_parsers/base_msdm_parser.py` | `BaseMSDMParser` | `BaseDocumentParser` | `__init__, parse_bytes, parse_path, parse_stream, _parse_to_msdm, resolve_references ...` |
| `engines/document/parsers/msdm_parsers/cql_parser.py` | `CQLParser` | `BaseMSDMParser` | `_parse_to_msdm, _strip_comments, _process_statement, _parse_create_table, _parse_create_type, _parse_create_index ...` |
| `engines/document/parsers/msdm_parsers/elasticsearch_mapping_parser.py` | `ElasticsearchMappingParser` | `BaseMSDMParser` | `_parse_to_msdm, _store_settings, _parse_mappings, _parse_field, _flatten` |
| `engines/document/parsers/msdm_parsers/erd_parser.py` | `ERDParser` | `BaseMSDMParser` | `_parse_to_msdm, _parse_json, _parse_json_entity, _parse_json_attribute, _parse_json_relationship, _parse_xml ...` |
| `engines/document/parsers/msdm_parsers/graphql_schema_parser.py` | `TokenType` | `Enum` | `` |
| `engines/document/parsers/msdm_parsers/graphql_schema_parser.py` | `GraphQLSchemaParser` | `BaseMSDMParser` | `_parse_to_msdm, _peek, _advance, _skip_comments, _expect, _expect_name ...` |
| `engines/document/parsers/msdm_parsers/influxdb_schema_parser.py` | `InfluxDBSchemaParser` | `BaseMSDMParser` | `_parse_to_msdm, _strip_comments, _split_statements, _process_statement, _parse_create_measurement, _parse_measurement_fields ...` |
| `engines/document/parsers/msdm_parsers/json_schema_parser.py` | `JsonSchemaParser` | `BaseMSDMParser` | `_parse_to_msdm, _process_schema, _parse_attribute, _type_to_datatype, _resolve_refs, _store_definitions ...` |
| `engines/document/parsers/msdm_parsers/mongodb_schema_parser.py` | `MongoDBSchemaParser` | `BaseMSDMParser` | `_parse_to_msdm, _try_json, _parse_validator, _process_validator_object, _parse_validator_field, _bson_type_to_datatype ...` |
| `engines/document/parsers/msdm_parsers/neo4j_schema_parser.py` | `Neo4jSchemaParser` | `BaseMSDMParser` | `_parse_to_msdm, _strip_comments, _process_statement, _add_prop, _build_entities` |
| `engines/document/parsers/msdm_parsers/owl_parser.py` | `OWLParser` | `BaseMSDMParser` | `_parse_to_msdm, _collect_entities, _collect_properties, _local_name, _get_child_text, _store_ref_annotation ...` |
| `engines/document/parsers/msdm_parsers/plantuml_parser.py` | `PlantUMLParser` | `BaseMSDMParser` | `_parse_to_msdm, _finalize_class_block, _parse_type_string, _parse_relationship_line, _to_card` |
| `engines/document/parsers/msdm_parsers/proto_msdm_parser.py` | `ProtoParser` | `BaseMSDMParser` | `_parse_to_msdm, _tokenize, _peek, _advance, _strip_comments, _parse_top_level ...` |
| `engines/document/parsers/msdm_parsers/python_model_parser.py` | `PythonModelParser` | `BaseMSDMParser` | `_parse_to_msdm, _process_class, _process_enum, _extract_fields, _annotation_to_datatype, _ast_to_datatype ...` |
| `engines/document/parsers/msdm_parsers/sql_ddl_parser.py` | `SqlDDLParser` | `BaseMSDMParser` | `_parse_to_msdm, _strip_sql_comments, _split_statements, _parse_create_table, _parse_column_definition, _sql_type_to_datatype ...` |
| `engines/document/parsers/msdm_parsers/thrift_idl_parser.py` | `ThriftIDLParser` | `BaseMSDMParser` | `_parse_to_msdm, _process_file_directives, _parse_typedef, _parse_enum, _parse_struct, _split_field_lines ...` |
| `engines/document/parsers/msdm_parsers/typescript_interface_parser.py` | `_Token` | `—` | `__init__` |
| `engines/document/parsers/msdm_parsers/typescript_interface_parser.py` | `TypeScriptInterfaceParser` | `BaseMSDMParser` | `_parse_to_msdm, _peek, _peek_value, _peek_kind, _advance, _expect ...` |
| `engines/document/parsers/msdm_parsers/uml_xmi_parser.py` | `UMLXmiParser` | `BaseMSDMParser` | `_parse_to_msdm, _collect_elements, _collect_enum_literals, _parse_class, _is_association_end, _parse_attribute ...` |
| `engines/document/parsers/msdm_parsers/xsd_parser.py` | `XSDParser` | `BaseMSDMParser` | `_parse_to_msdm, _parse_complex_type, _process_complex_content, _process_base_type, _process_compositor_or_attrs, _process_compositor ...` |
| `engines/document/parsers/osdm_parsers/base_osdm_parser.py` | `BaseOSDMParser` | `BaseDocumentParser` | `__init__, parse_bytes, parse_path, parse_stream, _parse_to_document, _detect_version` |
| `engines/document/parsers/osdm_parsers/bpmn_xml_parser.py` | `BPMNXMLParser` | `BaseOSDMParser` | `__init__, _map_enum, _map_gateway_type, _map_gateway_direction, _map_process_type, _map_association_direction ...` |
| `engines/document/parsers/osdm_parsers/cep_parser.py` | `CEPParser` | `BaseOSDMParser` | `_parse_to_document, _parse_definition, _parse_stream, _parse_rule` |
| `engines/document/parsers/osdm_parsers/cmmn_xml_parser.py` | `CMMNXMLParser` | `BaseOSDMParser` | `_parse_to_document, _parse_case, _parse_stage, _parse_flow_element, _parse_milestone, _parse_event_listener ...` |
| `engines/document/parsers/osdm_parsers/dmn_xml_parser.py` | `DMNXMLParser` | `BaseOSDMParser` | `_parse_to_document, _parse_definitions, _parse_decision, _resolve_decision_requirements, _parse_information_requirement, _parse_knowledge_requirement ...` |
| `engines/document/parsers/osdm_parsers/epc_parser.py` | `EPCParser` | `BaseOSDMParser` | `_parse_to_document, _parse_epc, _parse_event, _parse_function, _parse_connector, _parse_arc ...` |
| `engines/document/parsers/osdm_parsers/graphml_xml_parser.py` | `GraphMLXMLParser` | `BaseOSDMParser` | `_parse_to_document, _parse_graph, _parse_node, _parse_edge, _parse_port` |
| `engines/document/parsers/osdm_parsers/pnml_xml_parser.py` | `PNMLXMLParser` | `BaseOSDMParser` | `_parse_to_document, _parse_net, _parse_page, _parse_place, _parse_transition, _parse_arc ...` |
| `engines/document/parsers/osdm_parsers/prefect_dag_parser.py` | `PrefectDAGParser` | `BaseOSDMParser` | `_parse_to_document, _find_flows, _is_decorator_name, _build_state_machine, _build_state_machine_from_tasks, _find_tasks ...` |
| `engines/document/parsers/osdm_parsers/scxml_parser.py` | `SCXMLParser` | `BaseOSDMParser` | `_parse_to_document, _parse_scxml, _parse_state_or_parallel, _add_to_region, _parse_transition, _parse_on_entry_exit ...` |
| `engines/document/parsers/osdm_parsers/uml_state_machine_parser.py` | `UMLStateMachineParser` | `BaseOSDMParser` | `_parse_to_document, _parse_state_machine, _parse_region, _parse_state, _parse_activity, _parse_final_state ...` |
| `engines/document/parsers/osdm_parsers/xpd_parser.py` | `XPDLParser` | `BaseOSDMParser` | `_parse_to_document, _parse_workflow_process_first_pass, _parse_activity_first_pass, _parse_transition_first_pass, _parse_association_first_pass, _parse_artifact_first_pass ...` |
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
| `engines/document/parsers/pptx_parser/parser.py` | `PPTXParser` | `BaseDocumentParser` | `parse_bytes, parse_path, parse_stream, _parse_to_psdm, _parse_sections, _map_sections_to_slides ...` |
| `engines/document/parsers/spreadsheet_parser/base_spreadsheet_parser.py` | `BaseSpreadsheetParser` | `BaseDocumentParser` | `parse_bytes, parse_path, parse_stream, _parse_to_workbook` |
| `engines/document/parsers/spreadsheet_parser/binary_parser.py` | `ColumnarBinaryParser` | `BaseSpreadsheetParser` | `_parse_to_workbook, _convert_arrow_value, _read_table, _get_sheet_name` |
| `engines/document/parsers/spreadsheet_parser/binary_parser.py` | `ParquetParser` | `ColumnarBinaryParser` | `_read_table` |
| `engines/document/parsers/spreadsheet_parser/binary_parser.py` | `ArrowIPCParser` | `ColumnarBinaryParser` | `_read_table` |
| `engines/document/parsers/spreadsheet_parser/binary_parser.py` | `FeatherParser` | `ColumnarBinaryParser` | `_read_table` |
| `engines/document/parsers/spreadsheet_parser/delimited_parser.py` | `DelimitedParser` | `BaseSpreadsheetParser` | `_parse_to_workbook, _get_sheet_name` |
| `engines/document/parsers/spreadsheet_parser/delimited_parser.py` | `CSVParser` | `DelimitedParser` | `` |
| `engines/document/parsers/spreadsheet_parser/delimited_parser.py` | `TSVParser` | `DelimitedParser` | `` |
| `engines/document/parsers/spreadsheet_parser/fixed_width_parser.py` | `FixedWidthParser` | `BaseSpreadsheetParser` | `_parse_to_workbook, _slice_line, _get_sheet_name` |
| `engines/document/parsers/spreadsheet_parser/xlsx/parser.py` | `XLSXParser` | `BaseSpreadsheetParser` | `_parse_to_workbook, _load_xml, _load_relationships, _load_sheet_relationships, _resolve_sheets, _find_sheet_relationship ...` |
| `engines/document/parsers/ssdm_parsers/asyncapi_parser.py` | `AsyncAPIParser` | `BaseSSDMParser` | `_parse_to_document, _parse_contact, _parse_license, _parse_servers, _parse_security_schemes, _parse_channel ...` |
| `engines/document/parsers/ssdm_parsers/base_ssdm_parser.py` | `BaseSSDMParser` | `BaseDocumentParser` | `__init__, parse_bytes, parse_path, parse_stream, _parse_to_document, _detect_version` |
| `engines/document/parsers/ssdm_parsers/graphql_service_parser.py` | `_TokenType` | `—` | `` |
| `engines/document/parsers/ssdm_parsers/graphql_service_parser.py` | `_Token` | `—` | `` |
| `engines/document/parsers/ssdm_parsers/graphql_service_parser.py` | `_GraphQLScanner` | `—` | `__init__, peek, next, _next_token, _skip_whitespace_and_comments, _scan_number ...` |
| `engines/document/parsers/ssdm_parsers/graphql_service_parser.py` | `_GraphQLField` | `—` | `__init__` |
| `engines/document/parsers/ssdm_parsers/graphql_service_parser.py` | `_GraphQLType` | `—` | `__init__` |
| `engines/document/parsers/ssdm_parsers/graphql_service_parser.py` | `_GraphQLSchema` | `—` | `__init__` |
| `engines/document/parsers/ssdm_parsers/graphql_service_parser.py` | `_GraphQLParser` | `—` | `__init__, parse, _match, _advance, _peek, _parse_schema_definition ...` |
| `engines/document/parsers/ssdm_parsers/graphql_service_parser.py` | `GraphQLServiceParser` | `BaseSSDMParser` | `_parse_to_document, _convert_type_to_entity, _map_gql_type_to_datatype, _fields_to_operations` |
| `engines/document/parsers/ssdm_parsers/mcp_parser.py` | `MCPParser` | `BaseSSDMParser` | `_parse_to_document, _parse_mcp_binding, _parse_auth, _parse_internal_binding, _parse_tool_binding, _parse_resource_binding ...` |
| `engines/document/parsers/ssdm_parsers/openapi_parser.py` | `OpenAPIV3Parser` | `BaseSSDMParser` | `_parse_to_document, _parse_contact, _parse_license, _parse_servers, _parse_security_schemes, _parse_paths ...` |
| `engines/document/parsers/ssdm_parsers/proto_service_parser.py` | `ProtoToken` | `—` | `__init__` |
| `engines/document/parsers/ssdm_parsers/proto_service_parser.py` | `ProtoLexer` | `—` | `__init__, next_token, _skip_whitespace_and_comments, _scan_string, _scan_number` |
| `engines/document/parsers/ssdm_parsers/proto_service_parser.py` | `ProtoType` | `—` | `__init__` |
| `engines/document/parsers/ssdm_parsers/proto_service_parser.py` | `FieldDescriptor` | `—` | `__init__` |
| `engines/document/parsers/ssdm_parsers/proto_service_parser.py` | `MessageDef` | `—` | `__init__` |
| `engines/document/parsers/ssdm_parsers/proto_service_parser.py` | `EnumDef` | `—` | `__init__` |
| `engines/document/parsers/ssdm_parsers/proto_service_parser.py` | `ServiceMethod` | `—` | `__init__` |
| `engines/document/parsers/ssdm_parsers/proto_service_parser.py` | `ServiceDef` | `—` | `__init__` |
| `engines/document/parsers/ssdm_parsers/proto_service_parser.py` | `ProtoFile` | `—` | `__init__` |
| `engines/document/parsers/ssdm_parsers/proto_service_parser.py` | `ProtoParser` | `—` | `__init__, _eat, parse, _parse_syntax, _parse_package, _parse_message ...` |
| `engines/document/parsers/ssdm_parsers/proto_service_parser.py` | `ProtoServiceParser` | `BaseSSDMParser` | `_parse_to_document, _message_to_entity, _field_to_attribute, _enum_to_entity, _method_to_operation, _proto_type_to_datatype ...` |
| `engines/document/parsers/ssdm_parsers/python_service_parser.py` | `PythonServiceParser` | `BaseSSDMParser` | `_parse_to_document, _find_app_instance, _collect_pydantic_models, _pydantic_class_to_entity, _parse_routes, _is_route_decorator ...` |
| `engines/document/parsers/ssdm_parsers/wsdl_parser.py` | `WSDLParser` | `BaseSSDMParser` | `_parse_to_document, _parse_xsd_schema, _xsd_type_to_datatype, _parts_to_parameters, _parts_to_body_entity, _get_child_text` |
| `engines/document/parsers/ssdm_parsers/yang_parser.py` | `_Token` | `—` | `__init__` |
| `engines/document/parsers/ssdm_parsers/yang_parser.py` | `YANGParser` | `BaseSSDMParser` | `_parse_to_document, _peek, _peek_value, _peek_kind, _advance, _expect ...` |
| `engines/document/parsers/tsdm_parsers/base_tsdm_parser.py` | `BaseTSDMParser` | `BaseDocumentParser` | `parse_bytes, parse_path, parse_stream, _parse_to_tsdm` |
| `engines/document/parsers/tsdm_parsers/tsdm_json_parser.py` | `TsdmJsonParser` | `BaseTSDMParser` | `_parse_to_tsdm, _parse_tool, _parse_parameters, _parse_outputs` |
| `engines/document/storage/chunk_store.py` | `ChunkStore` | `—` | `__init__, _key, add_chunks, get_chunk, list_chunks_for_document, attach_embeddings ...` |
| `engines/document/storage/document_store.py` | `DocumentStore` | `—` | `__init__, _document_key, _chunk_key, add_document, add_chunks, get_document ...` |
| `engines/document/storage/metadata_store.py` | `MetadataStore` | `—` | `__init__, _key, put_metadata, get_metadata, delete_metadata` |
| `engines/document/utils/binary_codec.py` | `BinaryCodec` | `—` | `from_bytes, to_bytes` |
| `engines/document/utils/binary_codec.py` | `BinaryCodecAdvanced` | `—` | `encode, decode` |
| `engines/document/utils/streaming_binary_codec.py` | `StreamingBinaryCodec` | `—` | `chunk_file_to_payloads, payloads_to_file` |
| `engines/document/writers/base.py` | `WriteOptions` | `BaseModel` | `` |
| `engines/document/writers/base.py` | `BaseDocumentWriter` | `ABC` | `__init__, write_stream, write, write_to_file, get_supported_media_types, get_supported_extensions` |
| `engines/document/writers/dsdm_writers/base_dsdm_writer.py` | `DSDMWriteOptions` | `WriteOptions` | `` |
| `engines/document/writers/dsdm_writers/base_dsdm_writer.py` | `BaseDSDMWriter` | `BaseDocumentWriter` | `__init__, write, write_stream, write_to_file, _serialise_root, _serialise_node ...` |
| `engines/document/writers/dsdm_writers/binary_writer.py` | `BinaryWriter` | `BaseDSDMWriter` | `get_supported_media_types, get_supported_extensions, _serialise_root, _serialise_node` |
| `engines/document/writers/dsdm_writers/bson_writer.py` | `BSONWriter` | `BaseDSDMWriter` | `get_supported_media_types, get_supported_extensions, _serialise_root, _serialise_node` |
| `engines/document/writers/dsdm_writers/cassandra_writer.py` | `CassandraWriter` | `BaseDSDMWriter` | `get_supported_media_types, get_supported_extensions, _serialise_root, _serialise_node, write_to_cassandra` |
| `engines/document/writers/dsdm_writers/cbor_writer.py` | `CBORWriter` | `BaseDSDMWriter` | `get_supported_media_types, get_supported_extensions, _serialise_root, _serialise_node` |
| `engines/document/writers/dsdm_writers/csv_tsv_writer.py` | `CSVTSVWriter` | `BaseDSDMWriter` | `get_supported_media_types, get_supported_extensions, _serialise_root, _serialise_node, _format_cell` |
| `engines/document/writers/dsdm_writers/json_writer.py` | `JSONWriter` | `BaseDSDMWriter` | `get_supported_media_types, get_supported_extensions, _serialise_root, _serialise_node` |
| `engines/document/writers/dsdm_writers/mongodb_writer.py` | `MongoDBWriter` | `BaseDSDMWriter` | `get_supported_media_types, get_supported_extensions, _serialise_root, _serialise_node, write_to_collection, _convert_to_mongo_documents ...` |
| `engines/document/writers/dsdm_writers/msgpack_writer.py` | `MsgPackWriter` | `BaseDSDMWriter` | `get_supported_media_types, get_supported_extensions, _serialise_root, _serialise_node` |
| `engines/document/writers/dsdm_writers/pickle_writer.py` | `PickleWriter` | `BaseDSDMWriter` | `get_supported_media_types, get_supported_extensions, _serialise_root, _serialise_node` |
| `engines/document/writers/dsdm_writers/protobuf_writer.py` | `ProtobufWriter` | `BaseDSDMWriter` | `get_supported_media_types, get_supported_extensions, _serialise_root, _serialise_node` |
| `engines/document/writers/dsdm_writers/redis_writer.py` | `RedisWriter` | `BaseDSDMWriter` | `get_supported_media_types, get_supported_extensions, _serialise_root, _serialise_node, write_to_redis, _extract_redis_value` |
| `engines/document/writers/dsdm_writers/sql_writer.py` | `AsyncSQLConnection` | `Protocol` | `execute, executemany` |
| `engines/document/writers/dsdm_writers/sql_writer.py` | `SQLDataWriter` | `BaseDSDMWriter` | `get_supported_media_types, get_supported_extensions, _serialise_root, _serialise_node, write_to_database, _generate_upsert_sql ...` |
| `engines/document/writers/dsdm_writers/xml_writer.py` | `XMLWriter` | `BaseDSDMWriter` | `get_supported_media_types, get_supported_extensions, _serialise_root, _serialise_node, _node_to_xml, _native_xml_element ...` |
| `engines/document/writers/dsdm_writers/yaml_writer.py` | `YAMLWriter` | `BaseDSDMWriter` | `get_supported_media_types, get_supported_extensions, _serialise_root, _serialise_node` |
| `engines/document/writers/latex_writer.py` | `LatexWriter` | `BaseDocumentWriter` | `__init__, write, write_stream, write_to_file, get_supported_media_types, get_supported_extensions ...` |
| `engines/document/writers/markdown_writer.py` | `MarkdownWriter` | `BaseDocumentWriter` | `__init__, write, write_stream, write_to_file, get_supported_media_types, get_supported_extensions ...` |
| `engines/document/writers/msdm_writers/base_msdm_writer.py` | `WriteTarget` | `str, Enum` | `` |
| `engines/document/writers/msdm_writers/base_msdm_writer.py` | `SoftDeleteStrategy` | `str, Enum` | `` |
| `engines/document/writers/msdm_writers/base_msdm_writer.py` | `ConnectionConfig` | `BaseModel` | `` |
| `engines/document/writers/msdm_writers/base_msdm_writer.py` | `BaseMSDMWriter` | `BaseDocumentWriter` | `__init__, write_stream, write, write_to_file, apply_to_database, _write_design ...` |
| `engines/document/writers/msdm_writers/cql_writer.py` | `CQLWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_create_table, _write_create_type ...` |
| `engines/document/writers/msdm_writers/elasticsearch_mapping_writer.py` | `ElasticsearchMappingWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _build_index_definition, _attribute_to_es_field ...` |
| `engines/document/writers/msdm_writers/erd_writer.py` | `ERDWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _build_json, _entity_to_json ...` |
| `engines/document/writers/msdm_writers/graphql_schema_writer.py` | `GraphQLSchemaWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _is_scalar_type, _is_enum_type ...` |
| `engines/document/writers/msdm_writers/influxdb_schema_writer.py` | `InfluxDBSchemaWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_measurement, _is_implicit_timestamp ...` |
| `engines/document/writers/msdm_writers/json_schema_writer.py` | `JsonSchemaWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _entity_to_schema, _attribute_to_property_schema ...` |
| `engines/document/writers/msdm_writers/mongodb_schema_writer.py` | `MongoDBSchemaWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _build_validator_schema, _entity_to_json_schema ...` |
| `engines/document/writers/msdm_writers/neo4j_schema_writer.py` | `Neo4jSchemaWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_node_constraints, _write_edge_constraints ...` |
| `engines/document/writers/msdm_writers/owl_writer.py` | `OWLWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _base_uri, _entity_to_uri ...` |
| `engines/document/writers/msdm_writers/plantuml_writer.py` | `PlantUMLWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _entity_to_block, _field_to_plantuml ...` |
| `engines/document/writers/msdm_writers/proto_msdm_writer.py` | `ProtoWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_entity, _is_enum_entity ...` |
| `engines/document/writers/msdm_writers/python_model_writer.py` | `TargetStyle` | `str, Enum` | `` |
| `engines/document/writers/msdm_writers/python_model_writer.py` | `PythonModelWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _is_enum_entity, _build_enum ...` |
| `engines/document/writers/msdm_writers/sql_ddl_writer.py` | `SqlDDLWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _build_create_table, _column_definition ...` |
| `engines/document/writers/msdm_writers/thrift_idl_writer.py` | `ThriftIDLWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _is_typedef, _is_enum ...` |
| `engines/document/writers/msdm_writers/typescript_interface_writer.py` | `TypeScriptInterfaceWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _entity_to_declaration, _is_enum ...` |
| `engines/document/writers/msdm_writers/uml_xmi_writer.py` | `UMLXmiWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _new_id, _existing_or_new_id ...` |
| `engines/document/writers/msdm_writers/xsd_writer.py` | `XSDWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _entity_to_schema_item, _is_simple_entity ...` |
| `engines/document/writers/osdm_writers/base_osdm_writer.py` | `VersionStrategy` | `str, Enum` | `` |
| `engines/document/writers/osdm_writers/base_osdm_writer.py` | `VersionIncrement` | `str, Enum` | `` |
| `engines/document/writers/osdm_writers/base_osdm_writer.py` | `OSDMWriteOptions` | `WriteOptions` | `` |
| `engines/document/writers/osdm_writers/base_osdm_writer.py` | `BaseOSDMWriter` | `BaseDocumentWriter` | `__init__, write_stream, write, write_to_file, _write_design, get_supported_media_types ...` |
| `engines/document/writers/osdm_writers/bpmn_xml_writer.py` | `BPMNXMLWriter` | `BaseOSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _obj_id, _add_bpmn_element ...` |
| `engines/document/writers/osdm_writers/cep_writer.py` | `CEPWriter` | `BaseOSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _definition_to_dict, _stream_to_dict ...` |
| `engines/document/writers/osdm_writers/cmmn_xml_writer.py` | `CMMNXMLWriter` | `BaseOSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _obj_id, _add_cmmn_element ...` |
| `engines/document/writers/osdm_writers/dmn_xml_writer.py` | `DMNXMLWriter` | `BaseOSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _new_id, _obj_id ...` |
| `engines/document/writers/osdm_writers/epc_writer.py` | `EPCWriter` | `BaseOSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_process, _write_organisational_units ...` |
| `engines/document/writers/osdm_writers/graphml_xml_writer.py` | `GraphMLXMLWriter` | `BaseOSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _define_attributes, _write_graph ...` |
| `engines/document/writers/osdm_writers/pnml_xml_writer.py` | `PNMLXMLWriter` | `BaseOSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_net, _write_page ...` |
| `engines/document/writers/osdm_writers/prefect_dag_writer.py` | `PrefectDAGWriter` | `BaseOSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_header, _write_flow_definition ...` |
| `engines/document/writers/osdm_writers/scxml_writer.py` | `SCXMLWriter` | `BaseOSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_scxml_body, _resolve_initial_state ...` |
| `engines/document/writers/osdm_writers/uml_state_machine_writer.py` | `UMLStateMachineWriter` | `BaseOSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _new_id, _add_uml_element ...` |
| `engines/document/writers/osdm_writers/xpd_writer.py` | `XPDLWriter` | `BaseOSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_participant, _write_workflow_process ...` |
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
| `engines/document/writers/pptx_writer/writer.py` | `PPTXWriter` | `BaseDocumentWriter` | `__init__, write_stream, write, write_to_file, get_supported_media_types, get_supported_extensions ...` |
| `engines/document/writers/spreadsheet_writer/base.py` | `ESDMWriteOptions` | `WriteOptions` | `` |
| `engines/document/writers/spreadsheet_writer/base.py` | `ESDMBaseWriter` | `BaseDocumentWriter` | `__init__, write_stream, write, write_to_file, _add_shared_string, _get_shared_strings_xml ...` |
| `engines/document/writers/spreadsheet_writer/csv_writer.py` | `CSVWriter` | `ESDMBaseWriter` | `__init__, write_stream, write, write_to_file, _write_csv, _get_max_columns ...` |
| `engines/document/writers/spreadsheet_writer/csv_writer.py` | `TSVWriter` | `CSVWriter` | `__init__, get_supported_media_types, get_supported_extensions` |
| `engines/document/writers/spreadsheet_writer/esdm_writer.py` | `ESDMWriter` | `—` | `__init__, write_stream, write, write_to_file, _write_csv, _determine_format` |
| `engines/document/writers/spreadsheet_writer/xlsx/conditional_formatting_writer.py` | `ConditionalFormattingWriter` | `—` | `__init__, write, _write_rule, _get_cf_type, _get_cf_operator, _write_color_scale ...` |
| `engines/document/writers/spreadsheet_writer/xlsx/data_validation_writer.py` | `DataValidationWriter` | `—` | `__init__, write, _write_data_validation, _get_validation_type, _get_validation_operator` |
| `engines/document/writers/spreadsheet_writer/xlsx/drawing_writer.py` | `DrawingsWriter` | `—` | `__init__, write_drawing, _process_image, _process_chart, _build_chart_xml, _process_shape ...` |
| `engines/document/writers/spreadsheet_writer/xlsx/extra_writers.py` | `ContentTypesWriter` | `—` | `__init__, write` |
| `engines/document/writers/spreadsheet_writer/xlsx/extra_writers.py` | `RelationshipsWriter` | `—` | `__init__, write_root_rels, write_worksheet_rels` |
| `engines/document/writers/spreadsheet_writer/xlsx/extra_writers.py` | `CommentWriter` | `—` | `__init__, write_legacy_comments_vml, write_threaded_comments_xml` |
| `engines/document/writers/spreadsheet_writer/xlsx/extra_writers.py` | `HyperlinkWriter` | `—` | `__init__, write_hyperlinks_and_rels` |
| `engines/document/writers/spreadsheet_writer/xlsx/pivot_writer.py` | `PivotWriter` | `—` | `__init__, write, _write_pivot_cache_definition, _write_pivot_table` |
| `engines/document/writers/spreadsheet_writer/xlsx/shared_strings_writer.py` | `SharedStringsWriter` | `—` | `__init__, write` |
| `engines/document/writers/spreadsheet_writer/xlsx/styles_writer.py` | `StylesWriter` | `—` | `__init__, write, _write_number_formats, _write_fonts, _write_fills, _write_borders ...` |
| `engines/document/writers/spreadsheet_writer/xlsx/table_writer.py` | `TableWriter` | `—` | `__init__, write, _calculate_ref_from_rows, _col_letter` |
| `engines/document/writers/spreadsheet_writer/xlsx/vba_writer.py` | `VBAWriter` | `—` | `__init__, write` |
| `engines/document/writers/spreadsheet_writer/xlsx/workbook_writer.py` | `WorkbookWriter` | `—` | `__init__, write` |
| `engines/document/writers/spreadsheet_writer/xlsx/worksheet_writer.py` | `WorksheetWriter` | `—` | `__init__, write, _write_cell, _write_run_properties, _format_cell_value, _get_sheet_dimension ...` |
| `engines/document/writers/spreadsheet_writer/xlsx/xlsx_writer.py` | `XLSXWriter` | `ESDMBaseWriter` | `__init__, write_stream, write, write_to_file, _build_xlsx, _write_workbook_xml ...` |
| `engines/document/writers/spreadsheet_writer/xlsx/zip_packager.py` | `ZipPackager` | `—` | `__init__, pack, _add_extra_parts, _add_image_binaries` |
| `engines/document/writers/ssdm_writers/asyncapi_writer.py` | `AsyncAPIWriter` | `BaseSSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _build_info, _build_servers ...` |
| `engines/document/writers/ssdm_writers/base_ssdm_writer.py` | `VersionStrategy` | `str, Enum` | `` |
| `engines/document/writers/ssdm_writers/base_ssdm_writer.py` | `VersionIncrement` | `str, Enum` | `` |
| `engines/document/writers/ssdm_writers/base_ssdm_writer.py` | `SSDMWriteOptions` | `WriteOptions` | `` |
| `engines/document/writers/ssdm_writers/base_ssdm_writer.py` | `BaseSSDMWriter` | `BaseDocumentWriter` | `__init__, write_stream, write, write_to_file, _write_design, get_supported_media_types ...` |
| `engines/document/writers/ssdm_writers/graphql_service_writer.py` | `GraphQLServiceWriter` | `BaseSSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _get_annotation, _has_annotation ...` |
| `engines/document/writers/ssdm_writers/mcp_writer.py` | `MCPWriter` | `BaseSSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _build_input_schema, _build_output_schema ...` |
| `engines/document/writers/ssdm_writers/openapi_writer.py` | `OpenAPIWriter` | `BaseSSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _build_info, _build_servers ...` |
| `engines/document/writers/ssdm_writers/proto_service_writer.py` | `ProtoServiceWriter` | `BaseSSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _prepare_operation_messages, _param_to_proto_type ...` |
| `engines/document/writers/ssdm_writers/python_service_writer.py` | `PythonServiceWriter` | `BaseSSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_pydantic_model, _write_route ...` |
| `engines/document/writers/ssdm_writers/wsdl_writer.py` | `WSDLWriter` | `BaseSSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_types, _write_xsd_entity ...` |
| `engines/document/writers/ssdm_writers/yang_writer.py` | `YANGWriter` | `BaseDocumentWriter` | `__init__, write_stream, write, write_to_file, get_supported_media_types, get_supported_extensions ...` |
| `engines/document/writers/tsdm_writers/base_tsdm_writer.py` | `BaseTSDMWriter` | `BaseDocumentWriter` | `_write_design` |
| `engines/document/writers/tsdm_writers/tsdm_json_writer.py` | `TsdmJsonWriter` | `BaseTSDMWriter` | `_write_design, _tool_to_dict, _param_to_dict, _output_to_dict` |
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
| `engines/orchestration/core/context.py` | `ContextScope` | `Enum` | `` |
| `engines/orchestration/core/context.py` | `VariableScope` | `Enum` | `` |
| `engines/orchestration/core/context.py` | `Variable` | `—` | `` |
| `engines/orchestration/core/context.py` | `ExecutionContext` | `—` | `__init__, set_variable, get_variable, get_variable_object, has_variable, remove_variable ...` |
| `engines/orchestration/core/context.py` | `ContextManager` | `—` | `__init__, create_context, get_context, destroy_context, cleanup_inactive_contexts, get_statistics ...` |
| `engines/orchestration/core/correlation.py` | `CorrelationKey` | `—` | `__hash__, __eq__` |
| `engines/orchestration/core/correlation.py` | `CorrelationKeySet` | `—` | `add_key, matches, to_dict, __hash__, __eq__` |
| `engines/orchestration/core/correlation.py` | `Message` | `—` | `` |
| `engines/orchestration/core/correlation.py` | `MessageSubscription` | `—` | `` |
| `engines/orchestration/core/correlation.py` | `EventSubscription` | `—` | `` |
| `engines/orchestration/core/correlation.py` | `CorrelationEngine` | `—` | `__init__, subscribe_message, unsubscribe_message, subscribe_event, unsubscribe_event, correlate_message ...` |
| `engines/orchestration/core/engine.py` | `EngineState` | `Enum` | `` |
| `engines/orchestration/core/engine.py` | `DeploymentMode` | `Enum` | `` |
| `engines/orchestration/core/engine.py` | `EngineConfig` | `—` | `` |
| `engines/orchestration/core/engine.py` | `ProcessDefinition` | `—` | `` |
| `engines/orchestration/core/engine.py` | `Deployment` | `—` | `` |
| `engines/orchestration/core/engine.py` | `OrchestrationEngine` | `—` | `__init__, start, stop, pause, resume, register_engine_handler ...` |
| `engines/orchestration/core/event_bus.py` | `EventType` | `Enum` | `` |
| `engines/orchestration/core/event_bus.py` | `EventPriority` | `Enum` | `` |
| `engines/orchestration/core/event_bus.py` | `Event` | `—` | `to_dict` |
| `engines/orchestration/core/event_bus.py` | `Subscription` | `—` | `` |
| `engines/orchestration/core/event_bus.py` | `EventBus` | `—` | `__init__, start, stop, subscribe, unsubscribe, publish ...` |
| `engines/orchestration/core/instance.py` | `InstanceState` | `Enum` | `` |
| `engines/orchestration/core/instance.py` | `InstanceType` | `Enum` | `` |
| `engines/orchestration/core/instance.py` | `IncidentInfo` | `—` | `` |
| `engines/orchestration/core/instance.py` | `ActivityInstance` | `—` | `` |
| `engines/orchestration/core/instance.py` | `ProcessInstance` | `—` | `__init__, set_variable, get_variable, has_variable, remove_variable, set_variables ...` |
| `engines/orchestration/core/instance.py` | `InstanceManager` | `—` | `__init__, add_instance, get_instance, remove_instance, find_by_business_key, find_by_definition ...` |
| `engines/orchestration/core/scheduler.py` | `ScheduleType` | `Enum` | `` |
| `engines/orchestration/core/scheduler.py` | `TaskState` | `Enum` | `` |
| `engines/orchestration/core/scheduler.py` | `ScheduledTask` | `—` | `__lt__` |
| `engines/orchestration/core/scheduler.py` | `Scheduler` | `—` | `__init__, start, stop, pause, resume, schedule_once ...` |
| `engines/orchestration/core/token.py` | `TokenState` | `Enum` | `` |
| `engines/orchestration/core/token.py` | `TokenType` | `Enum` | `` |
| `engines/orchestration/core/token.py` | `TokenSnapshot` | `—` | `` |
| `engines/orchestration/core/token.py` | `Token` | `—` | `__init__, move_to, wait, resume, complete, terminate ...` |
| `engines/orchestration/core/token.py` | `TokenManager` | `—` | `__init__, create_token, get_token, remove_token, get_instance_tokens, get_active_tokens ...` |
| `engines/orchestration/core/transaction.py` | `TransactionState` | `Enum` | `` |
| `engines/orchestration/core/transaction.py` | `IsolationLevel` | `Enum` | `` |
| `engines/orchestration/core/transaction.py` | `TransactionParticipant` | `—` | `` |
| `engines/orchestration/core/transaction.py` | `CompensationAction` | `—` | `` |
| `engines/orchestration/core/transaction.py` | `TransactionScope` | `—` | `__init__, add_participant, add_compensation, prepare, commit, rollback ...` |
| `engines/orchestration/core/transaction.py` | `TransactionManager` | `—` | `__init__, begin_transaction, get_transaction, commit_transaction, rollback_transaction, transaction ...` |
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
| `tools/upgrade.py` | `CyclePolicy` | `Enum` | `` |
| `tools/upgrade.py` | `PipelineConfig` | `—` | `__post_init__` |
| `tools/upgrade.py` | `ToolResult` | `NamedTuple` | `` |
| `tools/upgrade.py` | `StageOutcome` | `Enum` | `` |
| `tools/upgrade.py` | `StageRecord` | `—` | `` |
| `tools/upgrade.py` | `HintSource` | `Enum` | `` |
| `tools/upgrade.py` | `HintKind` | `Enum` | `` |
| `tools/upgrade.py` | `TypeHint` | `—` | `__post_init__` |
| `tools/upgrade.py` | `FunctionLocation` | `—` | `` |
| `tools/upgrade.py` | `SymbolIndex` | `—` | `__init__, build` |
| `tools/upgrade.py` | `_SymbolCollector` | `cst.CSTVisitor` | `__init__, visit_ClassDef, leave_ClassDef, visit_FunctionDef` |
| `tools/upgrade.py` | `MypyError` | `—` | `__init__, __hash__` |
| `tools/upgrade.py` | `MypyErrorParser` | `—` | `parse` |
| `tools/upgrade.py` | `ConvergenceTracker` | `—` | `__init__, update, should_stop` |
| `tools/upgrade.py` | `ReturnTypeCollector` | `cst.CSTVisitor` | `__init__, visit_Return, consolidate` |
| `tools/upgrade.py` | `OptionalAssignmentDetector` | `cst.CSTVisitor` | `__init__, _is_none_check, visit_If, visit_IfExp` |
| `tools/upgrade.py` | `IsInstanceUnionDetector` | `cst.CSTVisitor` | `__init__, visit_If, _process_instance_check, _type_to_str` |
| `tools/upgrade.py` | `ParamUsageInferer` | `cst.CSTVisitor` | `__init__, visit_Call, _literal_type` |
| `tools/upgrade.py` | `TypeHintMerger` | `—` | `__init__, merge, _select_best` |
| `tools/upgrade.py` | `AnnotationInjector` | `cst.CSTTransformer` | `__init__, leave_FunctionDef, _parse_annotation` |
| `tools/upgrade.py` | `ExternalToolRunner` | `—` | `run_pyright, run_pytype, run_mypy` |
| `tools/upgrade.py` | `PyrightHintExtractor` | `—` | `extract` |
| `tools/upgrade.py` | `PytypeHintExtractor` | `—` | `extract` |
| `tools/upgrade.py` | `LibCSTInferencer` | `—` | `infer_file, __init__, visit_FunctionDef` |
| `tools/upgrade.py` | `ImportGraph` | `—` | `__init__, add_edge, build_from_project, find_cycles, _path_to_module, dfs` |
| `tools/upgrade.py` | `APISurfaceAnalyser` | `—` | `dump_api, load_api_dump, _get_public_symbols_all, _path_to_module, detect_breaking_changes, detect_signature_changes ...` |
| `tools/upgrade.py` | `RollbackManager` | `—` | `__init__, snapshot_project, rollback_stage, rollback_file` |
| `tools/upgrade.py` | `FixStrategy` | `Enum` | `` |
| `tools/upgrade.py` | `MypyErrorFixer` | `cst.CSTTransformer` | `__init__, _pos, _get_error_for_node, _parse_annotation, _is_none_literal, _wrap_async_return ...` |
| `tools/upgrade.py` | `RuffDiagnostic` | `—` | `` |
| `tools/upgrade.py` | `RuffErrorFixer` | `cst.CSTTransformer` | `__init__, _pos, _get_diag, leave_If, leave_Try, leave_SimpleStatementLine ...` |
| `tools/upgrade.py` | `PipelineSupervisor` | `—` | `__init__, log, add_stage, save_report, run_stage, _maybe_write_file ...` |
| `tools/upgrade.py` | `FunctionCollector` | `cst.CSTVisitor` | `__init__, visit_FunctionDef` |

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
Enum  →  CadConstraintType
BaseEntity  →  GeometricConstraintEntity
Enum  →  DimConstraintKind
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
BaseModel  →  DataValue
BaseModel  →  DataSchemaReference
BaseModel  →  DataDocumentCapabilities
BaseModel  →  SchemaBinding
BaseModel  →  DataNode
BaseDocument  →  DataDocument
BaseDocument  →  ESDMDocument
DocumentBaseModel  →  WorkbookProperties
DocumentBaseModel  →  ExcelRelationship
DocumentBaseModel  →  RelationshipCollection
DocumentBaseModel  →  SharedStrings
DocumentBaseModel  →  CellFormula
DocumentBaseModel  →  Cell
DocumentBaseModel  →  Row
DocumentBaseModel  →  Column
DocumentBaseModel  →  CellRange
CellRange  →  MergedCellRange
DocumentBaseModel  →  NamedRange
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
CharacterStyle  →  CellStyle
DocumentBaseModel  →  DifferentialFormat
DocumentBaseModel  →  TableStyleElement
DocumentBaseModel  →  ExcelTableStyle
StyleSheet  →  SpreadsheetStyleSheet
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
Enum  →  FormulaTokenType
DocumentBaseModel  →  FormulaToken
DocumentBaseModel  →  FormulaAST
DocumentBaseModel  →  SharedFormula
DocumentBaseModel  →  DefinedName
DocumentBaseModel  →  ExternalReference
DocumentBaseModel  →  ExternalLink
Enum  →  DataValidationType
Enum  →  DataValidationOperator
DocumentBaseModel  →  DataValidationRule
DocumentBaseModel  →  DataValidation
DocumentBaseModel  →  Hyperlink
DocumentBaseModel  →  Author
DocumentBaseModel  →  CommentTextRun
DocumentBaseModel  →  CommentText
DocumentBaseModel  →  Comment
DocumentBaseModel  →  CommentCollection
DocumentBaseModel  →  ThreadedComment
DocumentBaseModel  →  SheetProperties
DocumentBaseModel  →  SheetProtection
Enum  →  Orientation
DocumentBaseModel  →  PageMargins
DocumentBaseModel  →  PageSetup
DocumentBaseModel  →  SheetDimensions
DocumentBaseModel  →  CalcChainEntry
DocumentBaseModel  →  CalculationChain
DocumentBaseModel  →  PivotField
DocumentBaseModel  →  PivotCacheReference
DocumentBaseModel  →  PivotCache
DocumentBaseModel  →  PivotTable
DocumentBaseModel  →  Worksheet
DocumentBaseModel  →  Workbook
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
str  →  ScalarSupport
Enum  →  ScalarSupport
str  →  CompositeSupport
Enum  →  CompositeSupport
str  →  ConstraintCapability
Enum  →  ConstraintCapability
str  →  IndexCapability
Enum  →  IndexCapability
str  →  NestingDepth
Enum  →  NestingDepth
str  →  InheritanceSupport
Enum  →  InheritanceSupport
str  →  RelationshipModel
Enum  →  RelationshipModel
str  →  AnnotationSupport
Enum  →  AnnotationSupport
Flag  →  TimeSeriesSupport
str  →  NamespaceSupport
Enum  →  NamespaceSupport
Flag  →  EnumCapability
str  →  EntityKind
Enum  →  EntityKind
str  →  Cardinality
Enum  →  Cardinality
str  →  ConstraintType
Enum  →  ConstraintType
str  →  ScalarType
Enum  →  ScalarType
str  →  IndexMethod
Enum  →  IndexMethod
str  →  CompositionType
Enum  →  CompositionType
str  →  VersionStatus
Enum  →  VersionStatus
str  →  VisibilityKind
Enum  →  VisibilityKind
BaseDocument  →  MSDMDocument
str  →  ParticipantBandKind
Enum  →  ParticipantBandKind
str  →  MessageVisibleKind
Enum  →  MessageVisibleKind
str  →  AlignmentKind
Enum  →  AlignmentKind
str  →  TransactionMethod
Enum  →  TransactionMethod
str  →  TimerCalculationType
Enum  →  TimerCalculationType
str  →  TimeReference
Enum  →  TimeReference
str  →  DurationResolution
Enum  →  DurationResolution
str  →  EscapeType
Enum  →  EscapeType
str  →  CorrelationPropertyType
Enum  →  CorrelationPropertyType
str  →  CaseFileMultiplicity
Enum  →  CaseFileMultiplicity
str  →  EventListenerType
Enum  →  EventListenerType
str  →  ActivityType
Enum  →  ActivityType
str  →  TaskType
Enum  →  TaskType
str  →  SubProcessType
Enum  →  SubProcessType
str  →  GatewayType
Enum  →  GatewayType
str  →  EventType
Enum  →  EventType
str  →  LoopType
Enum  →  LoopType
str  →  MultiInstanceBehavior
Enum  →  MultiInstanceBehavior
str  →  AdHocOrdering
Enum  →  AdHocOrdering
str  →  ScriptLanguage
Enum  →  ScriptLanguage
str  →  CallActivityType
Enum  →  CallActivityType
str  →  ProcessType
Enum  →  ProcessType
str  →  GatewayDirection
Enum  →  GatewayDirection
str  →  AssociationDirection
Enum  →  AssociationDirection
str  →  EventBasedGatewayType
Enum  →  EventBasedGatewayType
str  →  ItemKind
Enum  →  ItemKind
str  →  TimerEventType
Enum  →  TimerEventType
str  →  RelationshipDirection
Enum  →  RelationshipDirection
str  →  CEPOperator
Enum  →  CEPOperator
str  →  WorkflowStateType
Enum  →  WorkflowStateType
str  →  ResourceParameterType
Enum  →  ResourceParameterType
str  →  ResourceRoleType
Enum  →  ResourceRoleType
str  →  PotentialOwnerType
Enum  →  PotentialOwnerType
str  →  InteractionNodeType
Enum  →  InteractionNodeType
str  →  EventDefinitionType
Enum  →  EventDefinitionType
str  →  ChoreographyLoopType
Enum  →  ChoreographyLoopType
str  →  DecisionLogicType
Enum  →  DecisionLogicType
str  →  PseudoStateKind
Enum  →  PseudoStateKind
str  →  InteractionStrategy
Enum  →  InteractionStrategy
BaseElement  →  RootElement
BaseElement  →  StateNode
BaseElement  →  Transition
BaseElement  →  Locator
BaseElement  →  DiagramElement
DiagramElement  →  Edge
DiagramElement  →  Shape
DiagramElement  →  BPMNPlane
Shape  →  BPMNShape
Edge  →  BPMNEdge
BaseElement  →  BpmnExpression
BpmnExpression  →  FormalExpression
RootElement  →  ItemDefinition
RootElement  →  Resource
BaseElement  →  ResourceParameter
BaseElement  →  ResourceAssignmentExpression
BaseElement  →  ResourceParameterBinding
BaseElement  →  ResourceRole
ResourceRole  →  HumanPerformer
HumanPerformer  →  Performer
HumanPerformer  →  PotentialOwner
BaseElement  →  FlowElement
FlowElement  →  FlowNode
FlowNode  →  Activity
Activity  →  Task
Task  →  ServiceTask
Task  →  SendTask
Task  →  ReceiveTask
Task  →  UserTask
Task  →  ManualTask
BaseElement  →  Script
Task  →  ScriptTask
Task  →  BusinessRuleTask
Activity  →  CallActivity
Activity  →  SubProcess
SubProcess  →  TransactionSubProcess
SubProcess  →  AdHocSubProcess
RootElement  →  GlobalTask
GlobalTask  →  GlobalUserTask
GlobalTask  →  GlobalScriptTask
GlobalTask  →  GlobalManualTask
GlobalTask  →  GlobalBusinessRuleTask
BaseElement  →  Rendering
Rendering  →  RenderingForm
BaseElement  →  LoopCharacteristics
LoopCharacteristics  →  StandardLoopCharacteristics
LoopCharacteristics  →  MultiInstanceLoopCharacteristics
BaseElement  →  ComplexBehaviorDefinition
BaseElement  →  InputOutputSpecification
BaseElement  →  InputSet
BaseElement  →  OutputSet
FlowNode  →  Event
Event  →  CatchEvent
Event  →  ThrowEvent
CatchEvent  →  StartEvent
ThrowEvent  →  EndEvent
CatchEvent  →  IntermediateCatchEvent
ThrowEvent  →  IntermediateThrowEvent
CatchEvent  →  BoundaryEvent
ThrowEvent  →  ImplicitThrowEvent
RootElement  →  EventDefinition
EventDefinition  →  MessageEventDefinition
EventDefinition  →  TimerEventDefinition
EventDefinition  →  SignalEventDefinition
EventDefinition  →  ErrorEventDefinition
EventDefinition  →  EscalationEventDefinition
EventDefinition  →  CompensateEventDefinition
EventDefinition  →  ConditionalEventDefinition
EventDefinition  →  LinkEventDefinition
EventDefinition  →  CancelEventDefinition
EventDefinition  →  TerminateEventDefinition
FlowElement  →  DataFlowElement
DataFlowElement  →  DataObject
DataFlowElement  →  DataObjectReference
RootElement  →  DataStore
DataFlowElement  →  DataStoreReference
BaseElement  →  DataState
BaseElement  →  DataElement
DataElement  →  Property
BaseElement  →  DataAssociation
DataAssociation  →  DataInputAssociation
DataAssociation  →  DataOutputAssociation
BaseElement  →  Assignment
FlowElement  →  SequenceFlow
BaseElement  →  MessageFlow
FlowNode  →  Gateway
Gateway  →  ExclusiveGateway
Gateway  →  InclusiveGateway
Gateway  →  ParallelGateway
Gateway  →  EventBasedGateway
Gateway  →  ComplexGateway
BaseElement  →  Lane
BaseElement  →  LaneSet
RootElement  →  Process
RootElement  →  Collaboration
BaseElement  →  Artifact
Artifact  →  Association
Artifact  →  Group
Artifact  →  TextAnnotation
BaseElement  →  Auditing
BaseElement  →  Monitoring
RootElement  →  Interface
BaseElement  →  Operation
RootElement  →  EndPoint
RootElement  →  Message
RootElement  →  Signal
RootElement  →  Error
RootElement  →  Escalation
BaseElement  →  CorrelationKey
RootElement  →  CorrelationProperty
BaseElement  →  CorrelationPropertyRetrievalExpression
BaseElement  →  CorrelationSubscription
BaseElement  →  CorrelationPropertyBinding
RootElement  →  Category
BaseElement  →  CategoryValue
BaseElement  →  MessageFlowAssociation
BaseElement  →  Participant
BaseElement  →  ParticipantAssociation
RootElement  →  PartnerEntity
RootElement  →  PartnerRole
BaseElement  →  ConversationNode
ConversationNode  →  Conversation
ConversationNode  →  CallConversation
ConversationNode  →  GlobalConversation
ConversationNode  →  SubConversation
BaseElement  →  ConversationAssociation
BaseElement  →  ConversationLink
FlowNode  →  ChoreographyActivity
ChoreographyActivity  →  ChoreographyTask
ChoreographyActivity  →  CallChoreography
ChoreographyActivity  →  SubChoreography
Collaboration  →  Choreography
Choreography  →  GlobalChoreographyTask
BaseElement  →  PlanItem
PlanItem  →  DiscretionaryItem
BaseElement  →  CaseFileItem
Activity  →  CaseTask
Activity  →  ProcessTask
Activity  →  HumanTask
BaseElement  →  ApplicabilityRule
BaseElement  →  EntryCriterion
BaseElement  →  ExitCriterion
FlowNode  →  Stage
FlowNode  →  Milestone
FlowNode  →  EventListener
BaseElement  →  Sentry
BaseElement  →  InformationRequirement
BaseElement  →  KnowledgeRequirement
BaseElement  →  AuthorityRequirement
BaseElement  →  DecisionService
FlowNode  →  Decision
FlowNode  →  BusinessKnowledgeModel
FlowNode  →  InputData
FlowNode  →  KnowledgeSource
str  →  ErrorHandlingOperator
Enum  →  ErrorHandlingOperator
float  →  RetryBackoffRate
Enum  →  RetryBackoffRate
StateNode  →  State
Transition  →  StateTransition
BaseElement  →  StateMachineRegion
StateNode  →  PseudoState
State  →  Place
Transition  →  PnTransition
Transition  →  Arc
BaseElement  →  InteractionProtocol
BaseDocument  →  BaseOSDMDocument
BaseOSDMDocument  →  BPMNDocument
BaseOSDMDocument  →  CMMNDocument
BaseOSDMDocument  →  StateMachineDocument
BaseOSDMDocument  →  DMNDocument
BaseOSDMDocument  →  CEPDocument
BaseOSDMDocument  →  MultiAgentInteractionDocument
FormalExpression  →  SentryExpression
BaseElement  →  DecisionTable
BaseElement  →  ActionList
str  →  PlaceholderType
Enum  →  PlaceholderType
str  →  TransitionType
Enum  →  TransitionType
str  →  AnimationType
Enum  →  AnimationType
str  →  TriggerType
Enum  →  TriggerType
str  →  ShowType
Enum  →  ShowType
BaseDocument  →  PSDMDocument
str  →  ParameterNesting
Enum  →  ParameterNesting
str  →  BodyMediaType
Enum  →  BodyMediaType
str  →  SecurityFeature
Enum  →  SecurityFeature
str  →  TransportBinding
Enum  →  TransportBinding
str  →  SchemaKind
Enum  →  SchemaKind
str  →  OperationModel
Enum  →  OperationModel
str  →  HttpMethod
Enum  →  HttpMethod
str  →  ParameterLocation
Enum  →  ParameterLocation
str  →  AuthMethod
Enum  →  AuthMethod
str  →  OAuth2Flow
Enum  →  OAuth2Flow
str  →  ApiKeyLocation
Enum  →  ApiKeyLocation
str  →  OperationType
Enum  →  OperationType
str  →  Transport
Enum  →  Transport
str  →  ValueSource
Enum  →  ValueSource
str  →  RetryPolicy
Enum  →  RetryPolicy
str  →  PortProtocol
Enum  →  PortProtocol
str  →  HealthProbeType
Enum  →  HealthProbeType
str  →  PerformedBy
Enum  →  PerformedBy
str  →  DiscoveryBackend
Enum  →  DiscoveryBackend
str  →  ServiceType
Enum  →  ServiceType
str  →  MeshRuleType
Enum  →  MeshRuleType
str  →  MessageFormat
Enum  →  MessageFormat
str  →  SubscriptionType
Enum  →  SubscriptionType
str  →  InternalComponentType
Enum  →  InternalComponentType
str  →  CoordinationProtocol
Enum  →  CoordinationProtocol
BaseDocument  →  SSDMDocument
ServiceBinding  →  NorthBoundBinding
str  →  DocumentStandard
Enum  →  DocumentStandard
str  →  MediaCategory
Enum  →  MediaCategory
str  →  ToolKind
Enum  →  ToolKind
str  →  ParameterSource
Enum  →  ParameterSource
str  →  ParameterType
Enum  →  ParameterType
str  →  LoadBalanceStrategy
Enum  →  LoadBalanceStrategy
str  →  SnmpVersion
Enum  →  SnmpVersion
str  →  NetconfProtocol
Enum  →  NetconfProtocol
Tool  →  DbQueryTool
Tool  →  DbStatementTool
Tool  →  HttpServiceTool
Tool  →  GrpcServiceTool
Tool  →  GraphQLTool
Tool  →  TcpSocketTool
Tool  →  MessageBusTool
Tool  →  CliTool
Tool  →  PythonFunctionTool
Tool  →  MCPTool
Tool  →  YangNetconfTool
Tool  →  MibSnmpTool
Tool  →  FileReadTool
Tool  →  FileWriteTool
Tool  →  AiModelTool
Tool  →  CompositeTool
BaseDocument  →  TSDMDocument
BaseDocument  →  USDMDocument
ABC  →  FormatPlugin
BaseModel  →  ParseOptions
ABC  →  BaseDocumentParser
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
ParseOptions  →  DSDMParseOptions
BaseDocumentParser  →  BaseDSDMParser
BaseDSDMParser  →  BinaryParser
BinaryParser  →  BSONParser
BaseDSDMParser  →  CassandraParser
BinaryParser  →  CBORParser
BaseDSDMParser  →  CSVTSVParser
BaseDSDMParser  →  JSONParser
BSONParser  →  MongoDBParser
BinaryParser  →  MsgPackParser
BinaryParser  →  PickleParser
BaseDSDMParser  →  ProtobufParser
BaseDSDMParser  →  RedisParser
Protocol  →  AsyncDBConnection
BaseDSDMParser  →  SQLDataParser
BaseDSDMParser  →  XMLParser
BaseDSDMParser  →  YAMLParser
HTMLParser  →  HTMLDocumentParser
BaseDocumentParser  →  HtmlParser
BaseDocumentParser  →  LatexParser
Treeprocessor  →  MarkdownTreeProcessor
Extension  →  MarkdownExtension
BaseDocumentParser  →  MarkdownParser
BaseDocumentParser  →  BaseMSDMParser
BaseMSDMParser  →  CQLParser
BaseMSDMParser  →  ElasticsearchMappingParser
BaseMSDMParser  →  ERDParser
Enum  →  TokenType
BaseMSDMParser  →  GraphQLSchemaParser
BaseMSDMParser  →  InfluxDBSchemaParser
BaseMSDMParser  →  JsonSchemaParser
BaseMSDMParser  →  MongoDBSchemaParser
BaseMSDMParser  →  Neo4jSchemaParser
BaseMSDMParser  →  OWLParser
BaseMSDMParser  →  PlantUMLParser
BaseMSDMParser  →  ProtoParser
BaseMSDMParser  →  PythonModelParser
BaseMSDMParser  →  SqlDDLParser
BaseMSDMParser  →  ThriftIDLParser
BaseMSDMParser  →  TypeScriptInterfaceParser
BaseMSDMParser  →  UMLXmiParser
BaseMSDMParser  →  XSDParser
BaseDocumentParser  →  BaseOSDMParser
BaseOSDMParser  →  BPMNXMLParser
BaseOSDMParser  →  CEPParser
BaseOSDMParser  →  CMMNXMLParser
BaseOSDMParser  →  DMNXMLParser
BaseOSDMParser  →  EPCParser
BaseOSDMParser  →  GraphMLXMLParser
BaseOSDMParser  →  PNMLXMLParser
BaseOSDMParser  →  PrefectDAGParser
BaseOSDMParser  →  SCXMLParser
BaseOSDMParser  →  UMLStateMachineParser
BaseOSDMParser  →  XPDLParser
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
BaseDocumentParser  →  PPTXParser
BaseDocumentParser  →  BaseSpreadsheetParser
BaseSpreadsheetParser  →  ColumnarBinaryParser
ColumnarBinaryParser  →  ParquetParser
ColumnarBinaryParser  →  ArrowIPCParser
ColumnarBinaryParser  →  FeatherParser
BaseSpreadsheetParser  →  DelimitedParser
DelimitedParser  →  CSVParser
DelimitedParser  →  TSVParser
BaseSpreadsheetParser  →  FixedWidthParser
BaseSpreadsheetParser  →  XLSXParser
BaseSSDMParser  →  AsyncAPIParser
BaseDocumentParser  →  BaseSSDMParser
BaseSSDMParser  →  GraphQLServiceParser
BaseSSDMParser  →  MCPParser
BaseSSDMParser  →  OpenAPIV3Parser
BaseSSDMParser  →  ProtoServiceParser
BaseSSDMParser  →  PythonServiceParser
BaseSSDMParser  →  WSDLParser
BaseSSDMParser  →  YANGParser
BaseDocumentParser  →  BaseTSDMParser
BaseTSDMParser  →  TsdmJsonParser
BaseModel  →  WriteOptions
ABC  →  BaseDocumentWriter
WriteOptions  →  DSDMWriteOptions
BaseDocumentWriter  →  BaseDSDMWriter
BaseDSDMWriter  →  BinaryWriter
BaseDSDMWriter  →  BSONWriter
BaseDSDMWriter  →  CassandraWriter
BaseDSDMWriter  →  CBORWriter
BaseDSDMWriter  →  CSVTSVWriter
BaseDSDMWriter  →  JSONWriter
BaseDSDMWriter  →  MongoDBWriter
BaseDSDMWriter  →  MsgPackWriter
BaseDSDMWriter  →  PickleWriter
BaseDSDMWriter  →  ProtobufWriter
BaseDSDMWriter  →  RedisWriter
Protocol  →  AsyncSQLConnection
BaseDSDMWriter  →  SQLDataWriter
BaseDSDMWriter  →  XMLWriter
BaseDSDMWriter  →  YAMLWriter
BaseDocumentWriter  →  LatexWriter
BaseDocumentWriter  →  MarkdownWriter
str  →  WriteTarget
Enum  →  WriteTarget
str  →  SoftDeleteStrategy
Enum  →  SoftDeleteStrategy
BaseModel  →  ConnectionConfig
BaseDocumentWriter  →  BaseMSDMWriter
BaseMSDMWriter  →  CQLWriter
BaseMSDMWriter  →  ElasticsearchMappingWriter
BaseMSDMWriter  →  ERDWriter
BaseMSDMWriter  →  GraphQLSchemaWriter
BaseMSDMWriter  →  InfluxDBSchemaWriter
BaseMSDMWriter  →  JsonSchemaWriter
BaseMSDMWriter  →  MongoDBSchemaWriter
BaseMSDMWriter  →  Neo4jSchemaWriter
BaseMSDMWriter  →  OWLWriter
BaseMSDMWriter  →  PlantUMLWriter
BaseMSDMWriter  →  ProtoWriter
str  →  TargetStyle
Enum  →  TargetStyle
BaseMSDMWriter  →  PythonModelWriter
BaseMSDMWriter  →  SqlDDLWriter
BaseMSDMWriter  →  ThriftIDLWriter
BaseMSDMWriter  →  TypeScriptInterfaceWriter
BaseMSDMWriter  →  UMLXmiWriter
BaseMSDMWriter  →  XSDWriter
str  →  VersionStrategy
Enum  →  VersionStrategy
str  →  VersionIncrement
Enum  →  VersionIncrement
WriteOptions  →  OSDMWriteOptions
BaseDocumentWriter  →  BaseOSDMWriter
BaseOSDMWriter  →  BPMNXMLWriter
BaseOSDMWriter  →  CEPWriter
BaseOSDMWriter  →  CMMNXMLWriter
BaseOSDMWriter  →  DMNXMLWriter
BaseOSDMWriter  →  EPCWriter
BaseOSDMWriter  →  GraphMLXMLWriter
BaseOSDMWriter  →  PNMLXMLWriter
BaseOSDMWriter  →  PrefectDAGWriter
BaseOSDMWriter  →  SCXMLWriter
BaseOSDMWriter  →  UMLStateMachineWriter
BaseOSDMWriter  →  XPDLWriter
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
BaseDocumentWriter  →  PPTXWriter
WriteOptions  →  ESDMWriteOptions
BaseDocumentWriter  →  ESDMBaseWriter
ESDMBaseWriter  →  CSVWriter
CSVWriter  →  TSVWriter
ESDMBaseWriter  →  XLSXWriter
BaseSSDMWriter  →  AsyncAPIWriter
str  →  VersionStrategy
Enum  →  VersionStrategy
str  →  VersionIncrement
Enum  →  VersionIncrement
WriteOptions  →  SSDMWriteOptions
BaseDocumentWriter  →  BaseSSDMWriter
BaseSSDMWriter  →  GraphQLServiceWriter
BaseSSDMWriter  →  MCPWriter
BaseSSDMWriter  →  OpenAPIWriter
BaseSSDMWriter  →  ProtoServiceWriter
BaseSSDMWriter  →  PythonServiceWriter
BaseSSDMWriter  →  WSDLWriter
BaseDocumentWriter  →  YANGWriter
BaseDocumentWriter  →  BaseTSDMWriter
BaseTSDMWriter  →  TsdmJsonWriter
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
Enum  →  ContextScope
Enum  →  VariableScope
Enum  →  EngineState
Enum  →  DeploymentMode
Enum  →  EventType
Enum  →  EventPriority
Enum  →  InstanceState
Enum  →  InstanceType
Enum  →  ScheduleType
Enum  →  TaskState
Enum  →  TokenState
Enum  →  TokenType
Enum  →  TransactionState
Enum  →  IsolationLevel
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
Enum  →  CyclePolicy
NamedTuple  →  ToolResult
Enum  →  StageOutcome
Enum  →  HintSource
Enum  →  HintKind
cst.CSTVisitor  →  _SymbolCollector
cst.CSTVisitor  →  ReturnTypeCollector
cst.CSTVisitor  →  OptionalAssignmentDetector
cst.CSTVisitor  →  IsInstanceUnionDetector
cst.CSTVisitor  →  ParamUsageInferer
cst.CSTTransformer  →  AnnotationInjector
Enum  →  FixStrategy
cst.CSTTransformer  →  MypyErrorFixer
cst.CSTTransformer  →  RuffErrorFixer
cst.CSTVisitor  →  FunctionCollector
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

---

## 🔍 تحلیل مشکلات احتمالی


### 🔴 کلاس‌های بزرگ (بیش از ۱۵ متد — نشانه نقض SRP)
- `DOCXExtractor` در `engines/document/parsers/docx_parser/docx_extractor.py` — 68 متد
- `DOCXImageExtractor` در `engines/document/parsers/docx_parser/docx_image_extractor.py` — 18 متد
- `OMMLParser` در `engines/document/parsers/docx_parser/docx_math_parser.py` — 28 متد
- `DOCXParser` در `engines/document/parsers/docx_parser/docx_parser.py` — 61 متد
- `DocxUtils` در `engines/document/parsers/docx_parser/docx_utils.py` — 36 متد
- `HTMLDocumentParser` در `engines/document/parsers/html_parser.py` — 31 متد
- `LatexParser` در `engines/document/parsers/latex_parser.py` — 35 متد
- `GraphQLSchemaParser` در `engines/document/parsers/msdm_parsers/graphql_schema_parser.py` — 21 متد
- `ProtoParser` در `engines/document/parsers/msdm_parsers/proto_msdm_parser.py` — 18 متد
- `TypeScriptInterfaceParser` در `engines/document/parsers/msdm_parsers/typescript_interface_parser.py` — 22 متد
- `BPMNXMLParser` در `engines/document/parsers/osdm_parsers/bpmn_xml_parser.py` — 69 متد
- `CMMNXMLParser` در `engines/document/parsers/osdm_parsers/cmmn_xml_parser.py` — 19 متد
- `ContentExtractor` در `engines/document/parsers/pdf_parser/content_extractor.py` — 27 متد
- `FontHandler` در `engines/document/parsers/pdf_parser/font_handler.py` — 20 متد
- `PDFMetadataExtractor` در `engines/document/parsers/pdf_parser/metadata_extractor.py` — 24 متد
- `_GraphQLParser` در `engines/document/parsers/ssdm_parsers/graphql_service_parser.py` — 19 متد
- `OpenAPIV3Parser` در `engines/document/parsers/ssdm_parsers/openapi_parser.py` — 16 متد
- `ProtoParser` در `engines/document/parsers/ssdm_parsers/proto_service_parser.py` — 17 متد
- `PythonServiceParser` در `engines/document/parsers/ssdm_parsers/python_service_parser.py` — 18 متد
- `YANGParser` در `engines/document/parsers/ssdm_parsers/yang_parser.py` — 25 متد
- `LatexWriter` در `engines/document/writers/latex_writer.py` — 24 متد
- `MarkdownWriter` در `engines/document/writers/markdown_writer.py` — 19 متد
- `CQLWriter` در `engines/document/writers/msdm_writers/cql_writer.py` — 23 متد
- `GraphQLSchemaWriter` در `engines/document/writers/msdm_writers/graphql_schema_writer.py` — 21 متد
- `ProtoWriter` در `engines/document/writers/msdm_writers/proto_msdm_writer.py` — 20 متد
- `SqlDDLWriter` در `engines/document/writers/msdm_writers/sql_ddl_writer.py` — 22 متد
- `TypeScriptInterfaceWriter` در `engines/document/writers/msdm_writers/typescript_interface_writer.py` — 16 متد
- `XSDWriter` در `engines/document/writers/msdm_writers/xsd_writer.py` — 16 متد
- `BPMNXMLWriter` در `engines/document/writers/osdm_writers/bpmn_xml_writer.py` — 61 متد
- `CMMNXMLWriter` در `engines/document/writers/osdm_writers/cmmn_xml_writer.py` — 22 متد
- `DMNXMLWriter` در `engines/document/writers/osdm_writers/dmn_xml_writer.py` — 21 متد
- `AnnotationWriter` در `engines/document/writers/pdf_writer/annotation_writer.py` — 27 متد
- `PDFEncryptor` در `engines/document/writers/pdf_writer/encryption.py` — 30 متد
- `FontManager` در `engines/document/writers/pdf_writer/font_manager.py` — 31 متد
- `MetadataWriter` در `engines/document/writers/pdf_writer/metadata_writer.py` — 18 متد
- `PDFOptimizer` در `engines/document/writers/pdf_writer/optimizer.py` — 33 متد
- `OutlineBuilder` در `engines/document/writers/pdf_writer/outline_builder.py` — 17 متد
- `PPTXWriter` در `engines/document/writers/pptx_writer/writer.py` — 19 متد
- `ESDMBaseWriter` در `engines/document/writers/spreadsheet_writer/base.py` — 19 متد
- `GraphQLServiceWriter` در `engines/document/writers/ssdm_writers/graphql_service_writer.py` — 21 متد
- `OpenAPIWriter` در `engines/document/writers/ssdm_writers/openapi_writer.py` — 16 متد
- `YANGWriter` در `engines/document/writers/ssdm_writers/yang_writer.py` — 22 متد
- `ExecutionContext` در `engines/orchestration/core/context.py` — 16 متد
- `OrchestrationEngine` در `engines/orchestration/core/engine.py` — 20 متد
- `ProcessInstance` در `engines/orchestration/core/instance.py` — 26 متد
- `Scheduler` در `engines/orchestration/core/scheduler.py` — 20 متد
- `Token` در `engines/orchestration/core/token.py` — 18 متد
- `MypyErrorFixer` در `tools/upgrade.py` — 19 متد
- `RuffErrorFixer` در `tools/upgrade.py` — 24 متد
- `PipelineSupervisor` در `tools/upgrade.py` — 25 متد

### 🟡 فایل‌های خالی یا فقط شامل import
- `config/settings.py` [21 lines]
- `engines/agents/base_agents/base_research_agent/metadata.py` [0 lines]
- `engines/agents/base_agents/base_research_agent/prompts.py` [0 lines]
- `engines/agents/base_agents/base_research_agent/rag_config.py` [0 lines]
- `engines/communication/bindings/binding_parser.py` [0 lines]
- `engines/communication/bindings/binding_writer.py` [0 lines]
- `engines/communication/bindings/mcp_binding_writer.py` [0 lines]
- `engines/communication/common/auth/api_key.py` [0 lines]
- `engines/communication/common/auth/auth_manager.py` [0 lines]
- `engines/communication/common/auth/jwt.py` [0 lines]
- `engines/communication/common/auth/mtls.py` [0 lines]
- `engines/communication/common/auth/oauth2.py` [0 lines]
- `engines/communication/common/serialization/avro_serializer.py` [0 lines]
- `engines/communication/common/serialization/json_serializer.py` [0 lines]
- `engines/communication/common/serialization/protobuf_serializer.py` [0 lines]
- `engines/communication/common/transport/amqp_client.py` [0 lines]
- `engines/communication/common/transport/base.py` [0 lines]
- `engines/communication/common/transport/grpc_client.py` [0 lines]
- `engines/communication/common/transport/http_client.py` [0 lines]
- `engines/communication/common/transport/kafka_client.py` [0 lines]
- `engines/communication/common/transport/mcp_adapter.py` [0 lines]
- `engines/communication/consumption/binding_loader.py` [0 lines]
- `engines/communication/consumption/circuit_breaker.py` [0 lines]
- `engines/communication/consumption/client_generator.py` [0 lines]
- `engines/communication/consumption/mcp_binding_loader.py` [0 lines]
- `engines/communication/consumption/mcp_client_adapter.py` [0 lines]
- `engines/communication/consumption/service_discovery.py` [0 lines]
- `engines/communication/exposure/docker_compose_writer.py` [0 lines]
- `engines/communication/exposure/gateway_config_writer.py` [0 lines]
- `engines/communication/exposure/kubernetes_manifest_writer.py` [0 lines]
- `engines/communication/exposure/mcp_server_writer.py` [0 lines]
- `engines/communication/exposure/server_builder.py` [0 lines]
- `engines/communication/messaging/adapters/amqp_adapter.py` [0 lines]
- `engines/communication/messaging/adapters/kafka_adapter.py` [0 lines]
- `engines/communication/messaging/adapters/nats_adapter.py` [0 lines]
- `engines/communication/messaging/channel_manager.py` [0 lines]
- `engines/communication/messaging/message_binding_parser.py` [0 lines]
- `engines/communication/messaging/message_binding_writer.py` [0 lines]
- `engines/document/model_tools/configuration.py` [0 lines]
- `engines/document/model_tools/diff_engine.py` [0 lines]
- `engines/document/model_tools/diff_sql_writer.py` [0 lines]
- `engines/document/model_tools/format_converters/converter_base.py` [0 lines]
- `engines/document/model_tools/format_converters/docx_to_pdf.py` [0 lines]
- `engines/document/model_tools/format_converters/docx_to_pptx.py` [0 lines]
- `engines/document/model_tools/format_converters/generic_converter.py` [0 lines]
- `engines/document/model_tools/format_converters/json_to_docx.py` [0 lines]
- `engines/document/model_tools/format_converters/json_to_pdf.py` [0 lines]
- `engines/document/model_tools/format_converters/markdown_to_docx.py` [0 lines]
- `engines/document/model_tools/format_converters/markdown_to_pdf.py` [0 lines]
- `engines/document/model_tools/format_converters/pdf_to_docx.py` [0 lines]
- `engines/document/model_tools/format_converters/ppt_to_docx.py` [0 lines]
- `engines/document/model_tools/format_converters/ppt_to_pdf.py` [0 lines]
- `engines/document/model_tools/format_converters/xlsx_to_docx.py` [0 lines]
- `engines/document/model_tools/format_converters/xlsx_to_pdf.py` [0 lines]
- `engines/document/model_tools/format_converters/xlsx_to_ppt.py` [0 lines]
- `engines/document/model_tools/model_standard_converters/csdm_to_usdm_adapter.py` [0 lines]
- `engines/document/model_tools/model_standard_converters/esdm_to_usdm_adapter.py` [0 lines]
- `engines/document/model_tools/model_standard_converters/psdm_to_usdm_adapter.py` [0 lines]
- `engines/document/model_tools/model_standard_converters/usdm_to_pdf_adapter.py` [0 lines]
- `engines/document/model_tools/report_generators/data_aggregated_list_report_generator.py` [0 lines]
- `engines/document/model_tools/report_generators/data_aggregated_list_with_content_report_generator.py` [0 lines]
- `engines/document/model_tools/report_generators/data_aggregated_list_with_related_list_report_generator.py` [0 lines]
- `engines/document/model_tools/report_generators/data_aggregated_list_with_sub_list_report_generator.py` [0 lines]
- `engines/document/model_tools/report_generators/data_aggregated_page_report_generator.py` [0 lines]
- `engines/document/model_tools/report_generators/data_aggregated_page_with_related_list_report_generator.py` [0 lines]
- `engines/document/model_tools/report_generators/data_aggregated_page_with_sub_list_report_generator.py` [0 lines]
- `engines/document/model_tools/report_generators/data_simple_list_report_generator.py` [0 lines]
- `engines/document/model_tools/report_generators/data_simple_list_with_content_report_generator.py` [0 lines]
- `engines/document/model_tools/report_generators/data_simple_list_with_related_list_report_generator.py` [0 lines]
- `engines/document/model_tools/report_generators/data_simple_page_report_generator.py` [0 lines]
- `engines/document/model_tools/report_generators/data_simple_page_with_related_list_report_generator.py` [0 lines]
- `engines/document/model_tools/report_generators/schema_report_generator.py` [0 lines]
- `engines/document/model_tools/report_generators/service_report_generator.py` [0 lines]
- `engines/document/parsers/cad_parser/csdm_loader.py` [580 lines]
- `engines/document/parsers/cad_parser/csdm_parser.py` [60 lines]
- `engines/document/parsers/cad_parser/csdm_relationships.py` [240 lines]
- `engines/document/parsers/cad_parser/oda_bridge.py` [238 lines]
- `engines/document/parsers/pptx_parser/constants.py` [106 lines]
- `engines/document/parsers/spreadsheet_parser/xlsx/constants.py` [233 lines]
- `engines/document/parsers/spreadsheet_parser/xlsx/namespaces.py` [16 lines]
- `engines/document/parsers/spreadsheet_parser/xlsx/shared_strings_builder.py` [0 lines]
- `engines/document/utils/docx_utils.py` [0 lines]
- `engines/document/utils/ooxml_constants.py` [0 lines]
- `engines/document/utils/xml_parser.py` [0 lines]
- `engines/document/writers/cad_writer/acis_writer.py` [71 lines]
- `engines/document/writers/cad_writer/base_context.py` [59 lines]
- `engines/document/writers/cad_writer/block_writer.py` [99 lines]
- `engines/document/writers/cad_writer/cad_writer.py` [104 lines]
- `engines/document/writers/cad_writer/dwg_builder.py` [146 lines]
- `engines/document/writers/cad_writer/entity_writer.py` [297 lines]
- `engines/document/writers/cad_writer/finalizer.py` [115 lines]
- `engines/document/writers/cad_writer/non_graphical_writer.py` [212 lines]
- `engines/document/writers/cad_writer/reactor_writer.py` [53 lines]
- `engines/document/writers/cad_writer/table_writer.py` [245 lines]
- `engines/document/writers/cad_writer/xdata_writer.py` [62 lines]
- `engines/document/writers/docx_writer/docx_builder.py` [0 lines]
- `engines/document/writers/docx_writer/docx_image_handler.py` [0 lines]
- `engines/document/writers/docx_writer/docx_math_writer.py` [0 lines]
- `engines/document/writers/docx_writer/docx_style_builder.py` [0 lines]
- `engines/document/writers/docx_writer/docx_table_builder.py` [0 lines]
- `engines/document/writers/docx_writer/docx_writer.py` [0 lines]
- `engines/document/writers/html_writer.py` [223 lines]
- `engines/document/writers/pdf_writer/init.py` [28 lines]
- `engines/document/writers/pptx_writer/constants.py` [74 lines]
- `engines/document/writers/spreadsheet_writer/xlsx/const.py` [7 lines]
- `engines/orchestration/api/admin_api.py` [0 lines]
- `engines/orchestration/api/deployment_api.py` [0 lines]
- `engines/orchestration/api/engine_api.py` [0 lines]
- `engines/orchestration/api/instance_api.py` [0 lines]
- `engines/orchestration/api/process_api.py` [0 lines]
- `engines/orchestration/api/task_api.py` [0 lines]
- `engines/orchestration/bpmn/activity_handler.py` [0 lines]
- `engines/orchestration/bpmn/adhoc_handler.py` [0 lines]
- `engines/orchestration/bpmn/choreography_handler.py` [0 lines]
- `engines/orchestration/bpmn/collaboration_handler.py` [0 lines]
- `engines/orchestration/bpmn/data_object_handler.py` [0 lines]
- `engines/orchestration/bpmn/engine.py` [0 lines]
- `engines/orchestration/bpmn/event_handler.py` [0 lines]
- `engines/orchestration/bpmn/gateway_handler.py` [0 lines]
- `engines/orchestration/bpmn/global_task_handler.py` [0 lines]
- `engines/orchestration/bpmn/loop_handler.py` [0 lines]
- `engines/orchestration/bpmn/process_executor.py` [0 lines]
- `engines/orchestration/bpmn/sequence_flow.py` [0 lines]
- `engines/orchestration/bpmn/transaction_handler.py` [0 lines]
- `engines/orchestration/cep/aggregator.py` [0 lines]
- `engines/orchestration/cep/engine.py` [0 lines]
- `engines/orchestration/cep/event_store.py` [0 lines]
- `engines/orchestration/cep/pattern_matcher.py` [0 lines]
- `engines/orchestration/cep/rule_evaluator.py` [0 lines]
- `engines/orchestration/cep/stream_processor.py` [0 lines]
- `engines/orchestration/cep/window_manager.py` [0 lines]
- `engines/orchestration/cmmn/case_executor.py` [0 lines]
- `engines/orchestration/cmmn/case_file_manager.py` [0 lines]
- `engines/orchestration/cmmn/discretionary_handler.py` [0 lines]
- `engines/orchestration/cmmn/engine.py` [0 lines]
- `engines/orchestration/cmmn/milestone_handler.py` [0 lines]
- `engines/orchestration/cmmn/planning_table_handler.py` [0 lines]
- `engines/orchestration/cmmn/sentry_evaluator.py` [0 lines]
- `engines/orchestration/cmmn/stage_handler.py` [0 lines]
- `engines/orchestration/cmmn/task_handler.py` [0 lines]
- `engines/orchestration/deployment/deployer.py` [0 lines]
- `engines/orchestration/deployment/migration_handler.py` [0 lines]
- `engines/orchestration/deployment/tenant_manager.py` [0 lines]
- `engines/orchestration/deployment/version_manager.py` [0 lines]
- `engines/orchestration/dmn/decision_executor.py` [0 lines]
- `engines/orchestration/dmn/decision_table_evaluator.py` [0 lines]
- `engines/orchestration/dmn/engine.py` [0 lines]
- `engines/orchestration/dmn/feel_engine.py` [0 lines]
- `engines/orchestration/dmn/hit_policy_handler.py` [0 lines]
- `engines/orchestration/dmn/invocation_handler.py` [0 lines]
- `engines/orchestration/dmn/literal_expression_eval.py` [0 lines]
- `engines/orchestration/expression/context_builder.py` [0 lines]
- `engines/orchestration/expression/evaluator.py` [0 lines]
- `engines/orchestration/expression/feel_evaluator.py` [0 lines]
- `engines/orchestration/expression/javascript_evaluator.py` [0 lines]
- `engines/orchestration/expression/juel_evaluator.py` [0 lines]
- `engines/orchestration/expression/python_evaluator.py` [0 lines]
- `engines/orchestration/integration/business_rule_adapter.py` [0 lines]
- `engines/orchestration/integration/connector_registry.py` [0 lines]
- `engines/orchestration/integration/data_mapper.py` [0 lines]
- `engines/orchestration/integration/message_adapter.py` [0 lines]
- `engines/orchestration/integration/script_executor.py` [0 lines]
- `engines/orchestration/integration/service_invoker.py` [0 lines]
- `engines/orchestration/integration/user_task_adapter.py` [0 lines]
- `engines/orchestration/monitoring/health_checker.py` [0 lines]
- `engines/orchestration/monitoring/logger.py` [0 lines]
- `engines/orchestration/monitoring/metrics_collector.py` [0 lines]
- `engines/orchestration/monitoring/performance_monitor.py` [0 lines]
- `engines/orchestration/monitoring/tracer.py` [0 lines]
- `engines/orchestration/multi_agent/agent_executor.py` [0 lines]
- `engines/orchestration/multi_agent/coordination_handler.py` [0 lines]
- `engines/orchestration/multi_agent/engine.py` [0 lines]
- `engines/orchestration/multi_agent/interaction_handler.py` [0 lines]
- `engines/orchestration/multi_agent/message_router.py` [0 lines]
- `engines/orchestration/multi_agent/negotiation_handler.py` [0 lines]
- `engines/orchestration/multi_agent/protocol_handler.py` [0 lines]
- `engines/orchestration/persistence/definition_repository.py` [0 lines]
- `engines/orchestration/persistence/event_repository.py` [0 lines]
- `engines/orchestration/persistence/history_repository.py` [0 lines]
- `engines/orchestration/persistence/instance_repository.py` [0 lines]
- `engines/orchestration/persistence/repository.py` [0 lines]
- `engines/orchestration/persistence/variable_repository.py` [0 lines]
- `engines/orchestration/runtime/compensation.py` [0 lines]
- `engines/orchestration/runtime/error_handler.py` [0 lines]
- `engines/orchestration/runtime/executor.py` [0 lines]
- `engines/orchestration/runtime/resource_manager.py` [0 lines]
- `engines/orchestration/runtime/state_manager.py` [0 lines]
- `engines/orchestration/runtime/timer_manager.py` [0 lines]
- `engines/orchestration/runtime/variable_manager.py` [0 lines]
- `engines/orchestration/state_machine/action_executor.py` [0 lines]
- `engines/orchestration/state_machine/engine.py` [0 lines]
- `engines/orchestration/state_machine/guard_evaluator.py` [0 lines]
- `engines/orchestration/state_machine/hierarchical_handler.py` [0 lines]
- `engines/orchestration/state_machine/history_manager.py` [0 lines]
- `engines/orchestration/state_machine/parallel_state_handler.py` [0 lines]
- `engines/orchestration/state_machine/state_executor.py` [0 lines]
- `engines/orchestration/state_machine/transition_handler.py` [0 lines]
- `engines/orchestration/utils/graph_utils.py` [0 lines]
- `engines/orchestration/utils/id_generator.py` [0 lines]
- `engines/orchestration/utils/json_parser.py` [0 lines]
- `engines/orchestration/utils/time_utils.py` [0 lines]
- `engines/orchestration/utils/type_converter.py` [0 lines]
- `engines/orchestration/utils/xml_parser.py` [0 lines]
- `engines/orchestration/validation/bpmn_validator.py` [0 lines]
- `engines/orchestration/validation/cmmn_validator.py` [0 lines]
- `engines/orchestration/validation/dmn_validator.py` [0 lines]
- `engines/orchestration/validation/semantic_validator.py` [0 lines]
- `engines/orchestration/validation/state_machine_validator.py` [0 lines]
- `engines/orchestration/validation/validator.py` [0 lines]
- `engines/tools/adapters/ai_model_executor.py` [0 lines]
- `engines/tools/adapters/cli_executor.py` [0 lines]
- `engines/tools/adapters/composite_executor.py` [0 lines]
- `engines/tools/adapters/db_query_executor.py` [0 lines]
- `engines/tools/adapters/file_executor.py` [0 lines]
- `engines/tools/adapters/grpc_tool_executor.py` [0 lines]
- `engines/tools/adapters/http_service_executor.py` [0 lines]
- `engines/tools/adapters/http_tool_executor.py` [0 lines]
- `engines/tools/adapters/mcp_tool_executor.py` [0 lines]
- `engines/tools/adapters/message_bus_executor.py` [0 lines]
- `engines/tools/adapters/mib_snmp_executor.py` [0 lines]
- `engines/tools/adapters/python_function_executor.py` [0 lines]
- `engines/tools/adapters/tcp_socket_executor.py` [0 lines]
- `engines/tools/adapters/yang_netconf_executor.py` [0 lines]
- `engines/tools/base_executor.py` [0 lines]
- `engines/tools/parameter_mapper.py` [0 lines]
- `engines/tools/tool_registry.py` [0 lines]
- `tools/mypy_batcher.py` [99 lines]
- `tools/test_ai.py` [23 lines]

### 🟠 کلاس‌های بدون Base Class (احتمال عدم رعایت interface مشترک)
- `DocumentEmbeddingService` در `engines/document/embedding/service.py`
- `IngestionService` در `engines/document/ingestion/ingestion_service.py`
- `AsyncIngestService` در `engines/document/ingestion/services/async_ingest_service.py`
- `BatchIngestService` در `engines/document/ingestion/services/batch_ingest_service.py`
- `UploadService` در `engines/document/ingestion/services/upload_service.py`
- `ServiceOperation` در `engines/document/models/ssdm_models.py`
- `ServiceExposure` در `engines/document/models/ssdm_models.py`
- `ServiceBinding` در `engines/document/models/ssdm_models.py`
- `InternalServiceBinding` در `engines/document/models/ssdm_models.py`
- `FontHandler` در `engines/document/parsers/pdf_parser/font_handler.py`
- `ServiceMethod` در `engines/document/parsers/ssdm_parsers/proto_service_parser.py`
- `ServiceDef` در `engines/document/parsers/ssdm_parsers/proto_service_parser.py`
- `PDFSecurityHandler` در `engines/document/writers/pdf_writer/encryption.py`
- `InteractionStrategy` در `engines/interaction/base_strategy.py`
- `EventBus` در `engines/orchestration/core/event_bus.py`
- `VectorService` در `engines/rag/vector_service.py`

---

## 📝 یادداشت

این گزارش به صورت **استاتیک** (تحلیل AST) تولید شده است.  
برای تحلیل runtime و dependency injection، ابزار تکمیلی لازم است.
