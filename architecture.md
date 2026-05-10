# 📐 Architecture Report

> تولید شده توسط `tools/analyze_architecture.py`  
> تاریخ: 2026-04-30 21:57:16  
---

## 📊 آمار کلی

| معیار | مقدار |
|-------|-------|
| فایل‌های Python | 717 |
| کلاس‌ها | 1682 |
| توابع سطح بالا | 369 |
| فایل‌های با خطا | 2 |
| مجموع خطوط کد | 106363 |

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
  │   │   │   ├── 📄 __init__.py [20 lines]
  │   │   │   ├── 📄 base.py [171 lines]
  │   │   │   ├── 📄 chunked_binary_payload.py [23 lines]
  │   │   │   ├── 📄 csdm_core.py [700 lines]
  │   │   │   ├── 📄 csdm_entities.py [654 lines]
  │   │   │   ├── 📄 csdm_tables.py [661 lines]
  │   │   │   ├── 📄 document_registry.py [267 lines]
  │   │   │   ├── 📄 dsdm_models.py [524 lines]
  │   │   │   ├── 📄 esdm_models.py [996 lines]
  │   │   │   ├── 📄 exceptions.py [65 lines]
  │   │   │   ├── 📄 media_detection.py [545 lines]
  │   │   │   ├── 📄 media_types.py [978 lines]
  │   │   │   ├── 📄 msdm_capabilities.py [144 lines]
  │   │   │   ├── 📄 msdm_models.py [356 lines]
  │   │   │   ├── 📄 msdm_registry.py [483 lines]
  │   │   │   ├── 📄 osdm_models.py [1471 lines]
  │   │   │   ├── 📄 psdm_models.py [289 lines]
  │   │   │   ├── 📄 ssdm_capabilities.py [98 lines]
  │   │   │   ├── 📄 ssdm_models.py [855 lines]
  │   │   │   ├── 📄 ssdm_registry.py [323 lines]
  │   │   │   ├── 📄 standard.py [151 lines]
  │   │   │   ├── 📄 tsdm_models.py [259 lines]
  │   │   │   └── 📄 usdm_models.py [700 lines]
  │   │   ├── 📁 parsers/
  │   │   │   ├── 📁 cad_parser/
  │   │   │   │   ├── 📄 __init__.py [0 lines]
  │   │   │   │   ├── 📄 csdm_loader.py [641 lines]
  │   │   │   │   ├── 📄 csdm_parser.py [74 lines]
  │   │   │   │   ├── 📄 csdm_relationships.py [281 lines]
  │   │   │   │   └── 📄 oda_bridge.py [273 lines]
  │   │   │   ├── 📁 docx_parser/
  │   │   │   │   ├── 📄 __init__.py [11 lines]
  │   │   │   │   ├── 📄 docx_chart_extractor.py [126 lines]
  │   │   │   │   ├── 📄 docx_diagram_extractor.py [110 lines]
  │   │   │   │   ├── 📄 docx_extractor.py [2285 lines]
  │   │   │   │   ├── 📄 docx_image_extractor.py [532 lines]
  │   │   │   │   ├── 📄 docx_math_parser.py [922 lines]
  │   │   │   │   ├── 📄 docx_models.py [742 lines]
  │   │   │   │   ├── 📄 docx_parser.py [1980 lines]
  │   │   │   │   ├── 📄 docx_shape_extractor.py [102 lines]
  │   │   │   │   ├── 📄 docx_style_parser.py [130 lines]
  │   │   │   │   ├── 📄 docx_table_parser.py [44 lines]
  │   │   │   │   └── 📄 docx_utils.py [3593 lines]
  │   │   │   ├── 📁 drawingml/
  │   │   │   │   ├── 📄 __init__.py [4 lines]
  │   │   │   │   ├── 📄 chart_ref_parser.py [105 lines]
  │   │   │   │   ├── 📄 diagram_parser.py [126 lines]
  │   │   │   │   ├── 📄 image_parser.py [123 lines]
  │   │   │   │   └── 📄 shape_parser.py [333 lines]
  │   │   │   ├── 📁 msdm_parsers/
  │   │   │   │   ├── 📄 __init__.py [20 lines]
  │   │   │   │   ├── 📄 avro_schema_parser.py [353 lines]
  │   │   │   │   ├── 📄 base_msdm_parser.py [71 lines]
  │   │   │   │   ├── 📄 cql_parser.py [544 lines]
  │   │   │   │   ├── 📄 cue_parser.py [378 lines]
  │   │   │   │   ├── 📄 elasticsearch_mapping_parser.py [252 lines]
  │   │   │   │   ├── 📄 erd_parser.py [307 lines]
  │   │   │   │   ├── 📄 graphql_schema_parser.py [566 lines]
  │   │   │   │   ├── 📄 influxdb_schema_parser.py [319 lines]
  │   │   │   │   ├── 📄 json_schema_parser.py [404 lines]
  │   │   │   │   ├── 📄 mongodb_schema_parser.py [472 lines]
  │   │   │   │   ├── 📄 neo4j_schema_parser.py [266 lines]
  │   │   │   │   ├── 📄 owl_parser.py [310 lines]
  │   │   │   │   ├── 📄 plantuml_parser.py [382 lines]
  │   │   │   │   ├── 📄 proto_msdm_parser.py [463 lines]
  │   │   │   │   ├── 📄 python_model_parser.py [354 lines]
  │   │   │   │   ├── 📄 sql_ddl_parser.py [519 lines]
  │   │   │   │   ├── 📄 thrift_idl_parser.py [277 lines]
  │   │   │   │   ├── 📄 typescript_interface_parser.py [586 lines]
  │   │   │   │   ├── 📄 uml_xmi_parser.py [453 lines]
  │   │   │   │   └── 📄 xsd_parser.py [409 lines]
  │   │   │   ├── 📁 osdm_parsers/
  │   │   │   │   ├── 📄 __init__.py [17 lines]
  │   │   │   │   ├── 📄 airflow_dag_parser.py [319 lines]
  │   │   │   │   ├── 📄 aws_step_functions_parser.py [228 lines]
  │   │   │   │   ├── 📄 azure_logic_apps_parser.py [225 lines]
  │   │   │   │   ├── 📄 base_osdm_parser.py [106 lines]
  │   │   │   │   ├── 📄 bpmn_xml_parser.py [910 lines]
  │   │   │   │   ├── 📄 cep_parser.py [125 lines]
  │   │   │   │   ├── 📄 cmmn_xml_parser.py [302 lines]
  │   │   │   │   ├── 📄 cncf_serverless_workflow_parser.py [254 lines]
  │   │   │   │   ├── 📄 dmn_xml_parser.py [249 lines]
  │   │   │   │   ├── 📄 epc_parser.py [206 lines]
  │   │   │   │   ├── 📄 graphml_xml_parser.py [162 lines]
  │   │   │   │   ├── 📄 pnml_xml_parser.py [187 lines]
  │   │   │   │   ├── 📄 prefect_dag_parser.py [195 lines]
  │   │   │   │   ├── 📄 scxml_parser.py [279 lines]
  │   │   │   │   ├── 📄 uml_state_machine_parser.py [228 lines]
  │   │   │   │   ├── 📄 xpd_parser.py [289 lines]
  │   │   │   │   └── 📄 yawl_parser.py [193 lines]
  │   │   │   ├── 📁 pdf_parser/
  │   │   │   │   ├── 📄 __init__.py [7 lines]
  │   │   │   │   ├── 📄 content_extractor.py [1050 lines]
  │   │   │   │   ├── 📄 font_handler.py [931 lines]
  │   │   │   │   ├── 📄 layout_analyzer.py [397 lines]
  │   │   │   │   ├── 📄 metadata_extractor.py [1534 lines]
  │   │   │   │   ├── 📄 pdf_objects.py [1227 lines]
  │   │   │   │   ├── 📄 structure_parser.py [516 lines]
  │   │   │   │   └── 📄 utils.py [1147 lines]
  │   │   │   ├── 📁 pptx_parser/
  │   │   │   │   ├── 📄 __init__.py [13 lines]
  │   │   │   │   ├── 📄 animation_parser.py [192 lines]
  │   │   │   │   ├── 📄 comments_parser.py [41 lines]
  │   │   │   │   ├── 📄 constants.py [108 lines]
  │   │   │   │   ├── 📄 master_parser.py [189 lines]
  │   │   │   │   ├── 📄 media_parser.py [104 lines]
  │   │   │   │   ├── 📄 notes_parser.py [127 lines]
  │   │   │   │   ├── 📄 ole_parser.py [46 lines]
  │   │   │   │   ├── 📄 parser.py [403 lines]
  │   │   │   │   ├── 📄 relationship_utils.py [128 lines]
  │   │   │   │   ├── 📄 shape_parser.py [96 lines]
  │   │   │   │   ├── 📄 slide_builder.py [292 lines]
  │   │   │   │   ├── 📄 table_parser.py [140 lines]
  │   │   │   │   ├── 📄 theme_parser.py [159 lines]
  │   │   │   │   └── 📄 utils.py [62 lines]
  │   │   │   ├── 📁 spreadsheet_parser/
  │   │   │   │   ├── 📁 xlsx/
  │   │   │   │   │   ├── 📄 __init__.py [12 lines]
  │   │   │   │   │   ├── 📄 charts_builder.py [120 lines]
  │   │   │   │   │   ├── 📄 constants.py [245 lines]
  │   │   │   │   │   ├── 📄 drawings_builder.py [267 lines]
  │   │   │   │   │   ├── 📄 formulas_builder.py [88 lines]
  │   │   │   │   │   ├── 📄 namespaces.py [16 lines]
  │   │   │   │   │   ├── 📄 parser.py [308 lines]
  │   │   │   │   │   ├── 📄 pivot_builder.py [70 lines]
  │   │   │   │   │   ├── 📄 relationships_builder.py [109 lines]
  │   │   │   │   │   ├── 📄 shared_strings_builder.py [0 lines]
  │   │   │   │   │   ├── 📄 styles_builder.py [368 lines]
  │   │   │   │   │   ├── 📄 tables_builder.py [215 lines]
  │   │   │   │   │   ├── 📄 utils.py [106 lines]
  │   │   │   │   │   ├── 📄 vba_builder.py [124 lines]
  │   │   │   │   │   ├── 📄 workbook_builder.py [255 lines]
  │   │   │   │   │   └── 📄 worksheet_builder.py [439 lines]
  │   │   │   │   ├── 📄 __init__.py [4 lines]
  │   │   │   │   ├── 📄 base_spreadsheet_parser.py [86 lines]
  │   │   │   │   ├── 📄 binary_parser.py [128 lines]
  │   │   │   │   ├── 📄 delimited_parser.py [116 lines]
  │   │   │   │   └── 📄 fixed_width_parser.py [131 lines]
  │   │   │   ├── 📁 ssdm_parsers/
  │   │   │   │   ├── 📄 __init__.py [9 lines]
  │   │   │   │   ├── 📄 apib_parser.py [621 lines]
  │   │   │   │   ├── 📄 asyncapi_parser.py [384 lines]
  │   │   │   │   ├── 📄 base_ssdm_parser.py [97 lines]
  │   │   │   │   ├── 📄 cddl_parser.py [514 lines]
  │   │   │   │   ├── 📄 graphql_service_parser.py [713 lines]
  │   │   │   │   ├── 📄 mcp_parser.py [364 lines]
  │   │   │   │   ├── 📄 mib_parser.py [584 lines]
  │   │   │   │   ├── 📄 openapi_parser.py [657 lines]
  │   │   │   │   ├── 📄 postman_collection_parser.py [210 lines]
  │   │   │   │   ├── 📄 proto_service_parser.py [539 lines]
  │   │   │   │   ├── 📄 python_service_parser.py [365 lines]
  │   │   │   │   ├── 📄 raml_parser.py [308 lines]
  │   │   │   │   ├── 📄 webidl_parser.py [447 lines]
  │   │   │   │   ├── 📄 wsdl_parser.py [246 lines]
  │   │   │   │   └── 📄 yang_parser.py [448 lines]
  │   │   │   ├── 📁 tsdm_parsers/
  │   │   │   │   ├── 📄 __init__.py [2 lines]
  │   │   │   │   ├── 📄 base_tsdm_parser.py [37 lines]
  │   │   │   │   └── 📄 tsdm_json_parser.py [205 lines]
  │   │   │   ├── 📄 __init__.py [8 lines]
  │   │   │   ├── 📄 base.py [87 lines]
  │   │   │   ├── 📄 binary_parser.py [374 lines]
  │   │   │   ├── 📄 cad_parser.py [133 lines]
  │   │   │   ├── 📄 html_parser.py [742 lines]
  │   │   │   ├── 📄 json_parser.py [155 lines]
  │   │   │   ├── 📄 latex_parser.py [841 lines]
  │   │   │   ├── 📄 markdown_parser.py [439 lines]
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
  │   │   │   ├── 📁 msdm_writers/
  │   │   │   │   ├── 📄 __init__.py [19 lines]
  │   │   │   │   ├── 📄 avro_schema_writer.py [399 lines]
  │   │   │   │   ├── 📄 base_msdm_writer.py [177 lines]
  │   │   │   │   ├── 📄 cql_writer.py [497 lines]
  │   │   │   │   ├── 📄 cue_writer.py [218 lines]
  │   │   │   │   ├── 📄 elasticsearch_mapping_writer.py [290 lines]
  │   │   │   │   ├── 📄 erd_writer.py [209 lines]
  │   │   │   │   ├── 📄 graphql_schema_writer.py [315 lines]
  │   │   │   │   ├── ⚠️ influxdb_schema_writer.py [324 lines]
  │   │   │   │   ├── 📄 json_schema_writer.py [299 lines]
  │   │   │   │   ├── 📄 mongodb_schema_writer.py [354 lines]
  │   │   │   │   ├── 📄 neo4j_schema_writer.py [200 lines]
  │   │   │   │   ├── 📄 owl_writer.py [197 lines]
  │   │   │   │   ├── 📄 plantuml_writer.py [246 lines]
  │   │   │   │   ├── 📄 proto_writer.py [291 lines]
  │   │   │   │   ├── 📄 python_model_writer.py [391 lines]
  │   │   │   │   ├── 📄 sql_ddl_writer.py [370 lines]
  │   │   │   │   ├── 📄 thrift_idl_writer.py [264 lines]
  │   │   │   │   ├── 📄 typescript_interface_writer.py [288 lines]
  │   │   │   │   ├── 📄 uml_xmi_writer.py [350 lines]
  │   │   │   │   └── 📄 xsd_writer.py [324 lines]
  │   │   │   ├── 📁 osdm_writers/
  │   │   │   │   ├── 📄 __init__.py [16 lines]
  │   │   │   │   ├── 📄 airflow_dag_writer.py [192 lines]
  │   │   │   │   ├── ⚠️ aws_step_functions_writer.py [188 lines]
  │   │   │   │   ├── 📄 azure_logic_apps_writer.py [183 lines]
  │   │   │   │   ├── 📄 base_osdm_writer.py [166 lines]
  │   │   │   │   ├── 📄 bpmn_xml_writer.py [842 lines]
  │   │   │   │   ├── 📄 cep_writer.py [88 lines]
  │   │   │   │   ├── 📄 cmmn_xml_writer.py [217 lines]
  │   │   │   │   ├── 📄 cncf_serverless_workflow_writer.py [165 lines]
  │   │   │   │   ├── 📄 dmn_xml_writer.py [222 lines]
  │   │   │   │   ├── 📄 epc_writer.py [136 lines]
  │   │   │   │   ├── 📄 graphml_xml_writer.py [181 lines]
  │   │   │   │   ├── 📄 pnml_xml_writer.py [191 lines]
  │   │   │   │   ├── 📄 prefect_dag_writer.py [189 lines]
  │   │   │   │   ├── 📄 scxml_writer.py [245 lines]
  │   │   │   │   ├── 📄 uml_state_machine_writer.py [204 lines]
  │   │   │   │   ├── 📄 xpd_writer.py [186 lines]
  │   │   │   │   └── 📄 yawl_writer.py [147 lines]
  │   │   │   ├── 📁 pdf_writer/
  │   │   │   │   ├── 📄 __init__.py [10 lines]
  │   │   │   │   ├── 📄 annotation_writer.py [582 lines]
  │   │   │   │   ├── 📄 content_writer.py [314 lines]
  │   │   │   │   ├── 📄 encryption.py [965 lines]
  │   │   │   │   ├── 📄 font_manager.py [1504 lines]
  │   │   │   │   ├── 📄 init.py [24 lines]
  │   │   │   │   ├── 📄 layout_builder.py [224 lines]
  │   │   │   │   ├── 📄 metadata_writer.py [412 lines]
  │   │   │   │   ├── 📄 optimizer.py [1259 lines]
  │   │   │   │   ├── 📄 outline_builder.py [275 lines]
  │   │   │   │   ├── 📄 pdf_objects.py [502 lines]
  │   │   │   │   └── 📄 utils.py [439 lines]
  │   │   │   ├── 📁 pptx_writer/
  │   │   │   │   ├── 📄 __init__.py [15 lines]
  │   │   │   │   ├── 📄 animation_writer.py [90 lines]
  │   │   │   │   ├── 📄 comments_writer.py [32 lines]
  │   │   │   │   ├── 📄 constants.py [76 lines]
  │   │   │   │   ├── 📄 diagram_writer.py [105 lines]
  │   │   │   │   ├── 📄 master_writer.py [88 lines]
  │   │   │   │   ├── 📄 media_writer.py [76 lines]
  │   │   │   │   ├── 📄 notes_writer.py [59 lines]
  │   │   │   │   ├── 📄 ole_writer.py [48 lines]
  │   │   │   │   ├── 📄 relationship_utils.py [85 lines]
  │   │   │   │   ├── 📄 shape_writer.py [163 lines]
  │   │   │   │   ├── 📄 slide_writer.py [198 lines]
  │   │   │   │   ├── 📄 style_writer.py [138 lines]
  │   │   │   │   ├── 📄 table_writer.py [69 lines]
  │   │   │   │   ├── 📄 theme_writer.py [116 lines]
  │   │   │   │   ├── 📄 utils.py [30 lines]
  │   │   │   │   └── 📄 writer.py [463 lines]
  │   │   │   ├── 📁 spreadsheet_writer/
  │   │   │   │   ├── 📁 xlsx/
  │   │   │   │   │   ├── 📄 __init__.py [13 lines]
  │   │   │   │   │   ├── 📄 conditional_formatting_writer.py [182 lines]
  │   │   │   │   │   ├── 📄 const.py [7 lines]
  │   │   │   │   │   ├── 📄 data_validation_writer.py [117 lines]
  │   │   │   │   │   ├── 📄 drawing_writer.py [426 lines]
  │   │   │   │   │   ├── 📄 extra_writers.py [189 lines]
  │   │   │   │   │   ├── 📄 pivot_writer.py [231 lines]
  │   │   │   │   │   ├── 📄 shared_strings_writer.py [48 lines]
  │   │   │   │   │   ├── 📄 styles_writer.py [277 lines]
  │   │   │   │   │   ├── 📄 table_writer.py [103 lines]
  │   │   │   │   │   ├── 📄 vba_writer.py [39 lines]
  │   │   │   │   │   ├── 📄 workbook_writer.py [61 lines]
  │   │   │   │   │   ├── 📄 worksheet_writer.py [310 lines]
  │   │   │   │   │   ├── 📄 xlsx_writer.py [189 lines]
  │   │   │   │   │   └── 📄 zip_packager.py [51 lines]
  │   │   │   │   ├── 📄 __init__.py [3 lines]
  │   │   │   │   ├── 📄 base.py [316 lines]
  │   │   │   │   ├── 📄 csv_writer.py [142 lines]
  │   │   │   │   └── 📄 esdm_writer.py [136 lines]
  │   │   │   ├── 📁 ssdm_writers/
  │   │   │   │   ├── 📄 __init__.py [15 lines]
  │   │   │   │   ├── 📄 apib_writer.py [211 lines]
  │   │   │   │   ├── 📄 asyncapi_writer.py [204 lines]
  │   │   │   │   ├── 📄 base_ssdm_writer.py [151 lines]
  │   │   │   │   ├── 📄 cddl_writer.py [152 lines]
  │   │   │   │   ├── 📄 graphql_service_writer.py [338 lines]
  │   │   │   │   ├── 📄 mcp_writer.py [187 lines]
  │   │   │   │   ├── 📄 mib_writer.py [80 lines]
  │   │   │   │   ├── 📄 openapi_writer.py [307 lines]
  │   │   │   │   ├── 📄 postman_collection_writer.py [192 lines]
  │   │   │   │   ├── 📄 proto_service_writer.py [185 lines]
  │   │   │   │   ├── 📄 python_service_writer.py [242 lines]
  │   │   │   │   ├── 📄 raml_writer.py [287 lines]
  │   │   │   │   ├── 📄 webidl_writer.py [139 lines]
  │   │   │   │   ├── 📄 wsdl_writer.py [252 lines]
  │   │   │   │   └── 📄 yang_writer.py [253 lines]
  │   │   │   ├── 📁 tsdm_writers/
  │   │   │   │   ├── 📄 __init__.py [2 lines]
  │   │   │   │   ├── 📄 base_tsdm_writer.py [12 lines]
  │   │   │   │   └── 📄 tsdm_json_writer.py [67 lines]
  │   │   │   ├── 📄 __init__.py [8 lines]
  │   │   │   ├── 📄 base.py [60 lines]
  │   │   │   ├── 📄 binary_writer.py [281 lines]
  │   │   │   ├── 📄 cad_writer.py [269 lines]
  │   │   │   ├── 📄 csv_writer.py [298 lines]
  │   │   │   ├── 📄 docx_writer.py [306 lines]
  │   │   │   ├── 📄 drawingml_helpers.py [230 lines]
  │   │   │   ├── 📄 excel_writer.py [1660 lines]
  │   │   │   ├── 📄 html_writer.py [279 lines]
  │   │   │   ├── 📄 json_writer.py [188 lines]
  │   │   │   ├── 📄 latex_writer.py [640 lines]
  │   │   │   ├── 📄 markdown_writer.py [290 lines]
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
  │   │   │   │   ├── 📄 memory_usage_tracker.py [16 lines]
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
| `engines/document/models/esdm_models.py` | `ESDMDocument` | `BaseDocument` | `` |
| `engines/document/models/esdm_models.py` | `DocumentBaseModel` | `—` | `` |
| `engines/document/models/esdm_models.py` | `WorkbookProperties` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `Relationship` | `DocumentBaseModel` | `` |
| `engines/document/models/esdm_models.py` | `RelationshipCollection` | `DocumentBaseModel` | `add, find_by_type` |
| `engines/document/models/esdm_models.py` | `SharedStrings` | `DocumentBaseModel` | `get_index` |
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
| `engines/document/models/esdm_models.py` | `CellFormula` | `DocumentBaseModel` | `create, get` |
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
| `engines/document/models/msdm_models.py` | `XSDFacet` | `str, Enum` | `` |
| `engines/document/models/msdm_models.py` | `ProtobufOption` | `str, Enum` | `` |
| `engines/document/models/msdm_models.py` | `AvroLogicalType` | `str, Enum` | `` |
| `engines/document/models/msdm_models.py` | `GraphQLDirective` | `str, Enum` | `` |
| `engines/document/models/msdm_models.py` | `DataType` | `—` | `` |
| `engines/document/models/msdm_models.py` | `Annotation` | `—` | `` |
| `engines/document/models/msdm_models.py` | `Constraint` | `—` | `` |
| `engines/document/models/msdm_models.py` | `Index` | `—` | `` |
| `engines/document/models/msdm_models.py` | `Attribute` | `—` | `` |
| `engines/document/models/msdm_models.py` | `Entity` | `—` | `` |
| `engines/document/models/msdm_models.py` | `EntityComposition` | `—` | `` |
| `engines/document/models/msdm_models.py` | `Relationship` | `—` | `` |
| `engines/document/models/msdm_models.py` | `MSDMDocument` | `BaseDocument` | `` |
| `engines/document/models/osdm_models.py` | `YAWLJoinType` | `str, Enum` | `` |
| `engines/document/models/osdm_models.py` | `YAWLSplitType` | `str, Enum` | `` |
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
| `engines/document/models/osdm_models.py` | `SentryExpression` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `DecisionTable` | `BaseElement` | `` |
| `engines/document/models/osdm_models.py` | `ActionList` | `BaseElement` | `` |
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
| `engines/document/models/osdm_models.py` | `YAWLTaskDecorator` | `BaseElement` | `` |
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
| `engines/document/models/psdm_models.py` | `PlaceholderType` | `str, Enum` | `` |
| `engines/document/models/psdm_models.py` | `TransitionType` | `str, Enum` | `` |
| `engines/document/models/psdm_models.py` | `AnimationType` | `str, Enum` | `` |
| `engines/document/models/psdm_models.py` | `TriggerType` | `str, Enum` | `` |
| `engines/document/models/psdm_models.py` | `ShowType` | `str, Enum` | `` |
| `engines/document/models/psdm_models.py` | `Placeholder` | `—` | `` |
| `engines/document/models/psdm_models.py` | `SlideLayout` | `—` | `` |
| `engines/document/models/psdm_models.py` | `SlideMaster` | `—` | `` |
| `engines/document/models/psdm_models.py` | `Transition` | `—` | `` |
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
| `engines/document/models/psdm_models.py` | `Section` | `—` | `` |
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
| `engines/document/models/ssdm_models.py` | `SecurityType` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `OAuth2Flow` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `ApiKeyLocation` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `OperationType` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `YangStatement` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `SnmpAccess` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `SnmpStatus` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `ContactInfo` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `LicenseInfo` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `Server` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `SecurityScheme` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `OAuth2FlowInfo` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `Parameter` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `RequestBody` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `Link` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `Response` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `Operation` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `YangType` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `YangLeaf` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `YangContainer` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `MibObjectType` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `MibModule` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `GraphQLService` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `AsyncAPIInfo` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `SSDMDocument ` | `BaseDocument` | `` |
| `engines/document/models/ssdm_models.py` | `Transport` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `AuthMethod` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `ApiKeyLocation` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `ValueSource` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `OAuth2Flow` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `RetryPolicy` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `PortProtocol` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `HealthProbeType` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `PerformedBy` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `DiscoveryBackend` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `ServiceType` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `JWTValidation` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `AuthConfig` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `SlAPolicy` | `—` | `` |
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
| `engines/document/models/ssdm_models.py` | `MeshRuleType` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `MeshRule` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `IngressRule` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `LoadBalancerConfig` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `ServiceExposure` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `DeploymentDescriptor` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `MessageFormat` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `SubscriptionType` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `MessageBinding` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `ServiceBinding` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `MCPToolBinding` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `MCPResourceBinding` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `MCPPromptBinding` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `MCPNorthBoundBinding` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `InternalComponentType` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `CoordinationProtocol` | `str, Enum` | `` |
| `engines/document/models/ssdm_models.py` | `ParameterMapping` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `ResponseMapping` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `InternalServiceBinding` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `NorthBoundBinding` | `ServiceBinding` | `` |
| `engines/document/models/ssdm_models.py` | `MCPClientToolBinding` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `MCPSouthBoundBinding` | `—` | `` |
| `engines/document/models/ssdm_models.py` | `MCPSouthBoundBinding` | `—` | `to_service_binding` |
| `engines/document/models/standard.py` | `DocumentStandard` | `str, Enum` | `full_name, description` |
| `engines/document/models/standard.py` | `MediaCategory` | `str, Enum` | `` |
| `engines/document/models/tsdm_models.py` | `ToolKind` | `str, Enum` | `` |
| `engines/document/models/tsdm_models.py` | `ParameterSource` | `str, Enum` | `` |
| `engines/document/models/tsdm_models.py` | `ParameterType` | `str, Enum` | `` |
| `engines/document/models/tsdm_models.py` | `HttpMethod` | `str, Enum` | `` |
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
| `engines/document/parsers/docx_parser/docx_models.py` | `DOCXDiagram` | `—` | `` |
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
| `engines/document/parsers/html_parser.py` | `HTMLDocumentParser` | `HTMLParser` | `__init__, _generate_id, _create_rich_text_span, _flush_current_text, handle_starttag, handle_endtag ...` |
| `engines/document/parsers/html_parser.py` | `HtmlParser` | `BaseDocumentParser` | `parse_bytes, parse_text, parse_stream, get_supported_media_types, get_supported_extensions, _extract_math_from_html` |
| `engines/document/parsers/json_parser.py` | `JsonDocumentParser` | `BaseDocumentParser` | `__init__, parse_bytes, parse_path, get_supported_media_types, get_supported_extensions` |
| `engines/document/parsers/latex_parser.py` | `LatexParser` | `BaseDocumentParser` | `__init__, parse_bytes, parse_stream, _reset_parser_state, _generate_id, _extract_title ...` |
| `engines/document/parsers/markdown_parser.py` | `MarkdownTreeProcessor` | `Treeprocessor` | `__init__, run, _generate_id, _process_node, _extract_text, _process_list ...` |
| `engines/document/parsers/markdown_parser.py` | `MarkdownExtension` | `Extension` | `extendMarkdown` |
| `engines/document/parsers/markdown_parser.py` | `MarkdownParser` | `BaseDocumentParser` | `__init__, parse_bytes, parse_stream` |
| `engines/document/parsers/msdm_parsers/avro_schema_parser.py` | `AvroSchemaParser` | `BaseMSDMParser` | `_parse_to_msdm, _process_schema_entry, _parse_record, _parse_enum, _parse_fixed, _parse_field ...` |
| `engines/document/parsers/msdm_parsers/base_msdm_parser.py` | `BaseMSDMParser` | `BaseDocumentParser` | `__init__, parse_bytes, parse_path, parse_stream, _parse_to_msdm` |
| `engines/document/parsers/msdm_parsers/cql_parser.py` | `CQLParser` | `BaseMSDMParser` | `_parse_to_msdm, _strip_comments, _process_statement, _parse_create_table, _parse_create_type, _parse_create_index ...` |
| `engines/document/parsers/msdm_parsers/cue_parser.py` | `CueParser` | `BaseMSDMParser` | `_parse_to_msdm, _strip_comments, _parse_cue_text, _tokenize, _peek, _advance ...` |
| `engines/document/parsers/msdm_parsers/elasticsearch_mapping_parser.py` | `ElasticsearchMappingParser` | `BaseMSDMParser` | `_parse_to_msdm, _store_settings, _parse_mappings, _parse_field, _flatten` |
| `engines/document/parsers/msdm_parsers/erd_parser.py` | `ERDParser` | `BaseMSDMParser` | `_parse_to_msdm, _parse_json, _parse_json_entity, _parse_json_attribute, _parse_json_relationship, _parse_xml ...` |
| `engines/document/parsers/msdm_parsers/graphql_schema_parser.py` | `TokenType` | `Enum` | `` |
| `engines/document/parsers/msdm_parsers/graphql_schema_parser.py` | `GraphQLSchemaParser` | `BaseMSDMParser` | `_parse_to_msdm, _peek, _advance, _skip_comments, _parse_definition, _parse_description ...` |
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
| `engines/document/parsers/msdm_parsers/typescript_interface_parser.py` | `Token` | `—` | `__init__` |
| `engines/document/parsers/msdm_parsers/typescript_interface_parser.py` | `TypeScriptInterfaceParser` | `BaseMSDMParser` | `_parse_to_msdm, _peek, _advance, _match, _expect, _parse_declaration ...` |
| `engines/document/parsers/msdm_parsers/uml_xmi_parser.py` | `UMLXmiParser` | `BaseMSDMParser` | `_parse_to_msdm, _collect_elements, _parse_class, _is_association_end, _parse_attribute, _parse_operation ...` |
| `engines/document/parsers/msdm_parsers/xsd_parser.py` | `XSDParser` | `BaseMSDMParser` | `_parse_to_msdm, _parse_complex_type, _process_complex_content, _process_base_type, _process_compositor_or_attrs, _process_compositor ...` |
| `engines/document/parsers/osdm_parsers/airflow_dag_parser.py` | `AirflowDAGParser` | `BaseOSDMParser` | `_parse_to_document, _find_dag_definitions, _is_dag_context, _is_dag_call, _extract_dag_info_from_with, _extract_dag_info_from_assign ...` |
| `engines/document/parsers/osdm_parsers/aws_step_functions_parser.py` | `AWSStepFunctionsParser` | `BaseOSDMParser` | `_parse_to_document, _build_state_machine, _parse_state, _choice_to_expression` |
| `engines/document/parsers/osdm_parsers/azure_logic_apps_parser.py` | `AzureLogicAppsParser` | `BaseOSDMParser` | `_parse_to_document, _build_state_machine, _parse_triggers, _parse_action, _parse_iso8601_duration` |
| `engines/document/parsers/osdm_parsers/base_osdm_parser.py` | `BaseOSDMParser` | `BaseDocumentParser` | `__init__, parse_bytes, parse_path, parse_stream, _parse_to_document, _detect_version ...` |
| `engines/document/parsers/osdm_parsers/bpmn_xml_parser.py` | `BPMNXMLParser` | `BaseOSDMParser` | `_parse_to_document, _parse_process, _parse_flow_element, _parse_task, _parse_activity_common, _parse_sub_process ...` |
| `engines/document/parsers/osdm_parsers/cep_parser.py` | `CEPParser` | `BaseOSDMParser` | `_parse_to_document, _parse_definition, _parse_stream, _parse_rule` |
| `engines/document/parsers/osdm_parsers/cmmn_xml_parser.py` | `CMMNXMLParser` | `BaseOSDMParser` | `_parse_to_document, _parse_case, _parse_stage, _parse_flow_element, _parse_milestone, _parse_event_listener ...` |
| `engines/document/parsers/osdm_parsers/cncf_serverless_workflow_parser.py` | `CNCFServerlessWorkflowParser` | `BaseOSDMParser` | `_parse_to_document, _build_state_machine, _parse_state, _parse_iso8601_duration` |
| `engines/document/parsers/osdm_parsers/dmn_xml_parser.py` | `DMNXMLParser` | `BaseOSDMParser` | `_parse_to_document, _parse_definitions, _parse_decision, _resolve_decision_requirements, _parse_information_requirement, _parse_knowledge_requirement ...` |
| `engines/document/parsers/osdm_parsers/epc_parser.py` | `EPCParser` | `BaseOSDMParser` | `_parse_to_document, _parse_epc, _parse_event, _parse_function, _parse_connector, _parse_arc ...` |
| `engines/document/parsers/osdm_parsers/graphml_xml_parser.py` | `GraphMLXMLParser` | `BaseOSDMParser` | `_parse_to_document, _parse_graph, _parse_node, _parse_edge, _parse_port` |
| `engines/document/parsers/osdm_parsers/pnml_xml_parser.py` | `PNMLXMLParser` | `BaseOSDMParser` | `_parse_to_document, _parse_net, _parse_page, _parse_place, _parse_transition, _parse_arc ...` |
| `engines/document/parsers/osdm_parsers/prefect_dag_parser.py` | `PrefectDAGParser` | `BaseOSDMParser` | `_parse_to_document, _find_flows, _is_decorator_name, _build_state_machine, _build_state_machine_from_tasks, _find_tasks ...` |
| `engines/document/parsers/osdm_parsers/scxml_parser.py` | `SCXMLParser` | `BaseOSDMParser` | `_parse_to_document, _parse_scxml, _parse_state_or_parallel, _add_to_region, _parse_transition, _parse_on_entry_exit ...` |
| `engines/document/parsers/osdm_parsers/uml_state_machine_parser.py` | `UMLStateMachineParser` | `BaseOSDMParser` | `_parse_to_document, _parse_state_machine, _parse_region, _parse_state, _parse_activity, _parse_final_state ...` |
| `engines/document/parsers/osdm_parsers/xpd_parser.py` | `XPDLParser` | `BaseOSDMParser` | `_parse_to_document, _parse_workflow_process, _parse_activity, _parse_transition, _parse_lane, _parse_data_field ...` |
| `engines/document/parsers/osdm_parsers/yawl_parser.py` | `YAWLParser` | `BaseOSDMParser` | `_parse_to_document, _parse_specification_and_net, _parse_condition, _parse_task, _parse_arc, _parse_cancellation_set ...` |
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
| `engines/document/parsers/ssdm_parsers/apib_parser.py` | `APIBlueprintTokenizer` | `—` | `__init__, eof, current, peek, advance, next_non_empty ...` |
| `engines/document/parsers/ssdm_parsers/apib_parser.py` | `APIBObject` | `—` | `to_dict` |
| `engines/document/parsers/ssdm_parsers/apib_parser.py` | `APIBMetadata` | `APIBObject` | `__init__` |
| `engines/document/parsers/ssdm_parsers/apib_parser.py` | `APIBParameter` | `APIBObject` | `__init__` |
| `engines/document/parsers/ssdm_parsers/apib_parser.py` | `APIBBody` | `APIBObject` | `__init__` |
| `engines/document/parsers/ssdm_parsers/apib_parser.py` | `APIBAction` | `APIBObject` | `__init__` |
| `engines/document/parsers/ssdm_parsers/apib_parser.py` | `APIBResource` | `APIBObject` | `__init__` |
| `engines/document/parsers/ssdm_parsers/apib_parser.py` | `APIBGroup` | `APIBObject` | `__init__` |
| `engines/document/parsers/ssdm_parsers/apib_parser.py` | `APIBlueprintParser` | `—` | `__init__, parse, _skip_blank, _parse_metadata, _parse_group, _parse_resource ...` |
| `engines/document/parsers/ssdm_parsers/apib_parser.py` | `APIBlueprintToSSDMParser` | `BaseSSDMParser` | `_parse_to_document, _build_servers, _action_to_operation, _object_to_entity` |
| `engines/document/parsers/ssdm_parsers/asyncapi_parser.py` | `AsyncAPIParser` | `BaseSSDMParser` | `_parse_to_document, _parse_contact, _parse_license, _parse_servers, _parse_security_schemes, _parse_channel ...` |
| `engines/document/parsers/ssdm_parsers/base_ssdm_parser.py` | `BaseSSDMParser` | `BaseDocumentParser` | `__init__, parse_bytes, parse_path, parse_stream, _parse_to_document, _detect_version ...` |
| `engines/document/parsers/ssdm_parsers/cddl_parser.py` | `CDDLTokenType` | `—` | `` |
| `engines/document/parsers/ssdm_parsers/cddl_parser.py` | `CDDLToken` | `—` | `` |
| `engines/document/parsers/ssdm_parsers/cddl_parser.py` | `CDDLLexer` | `—` | `__init__, _skip_spaces_and_comments, _make_token, next_token` |
| `engines/document/parsers/ssdm_parsers/cddl_parser.py` | `CDDLType` | `—` | `__init__, __repr__` |
| `engines/document/parsers/ssdm_parsers/cddl_parser.py` | `CDDLParser` | `—` | `__init__, _eat, _skip_newlines, parse, _parse_type, _parse_choice ...` |
| `engines/document/parsers/ssdm_parsers/cddl_parser.py` | `CDDLServiceParser` | `BaseSSDMParser` | `_parse_to_document, _cddl_to_entity, _type_to_string, _primitive_to_type_string` |
| `engines/document/parsers/ssdm_parsers/graphql_service_parser.py` | `TokenType` | `—` | `` |
| `engines/document/parsers/ssdm_parsers/graphql_service_parser.py` | `Token` | `—` | `` |
| `engines/document/parsers/ssdm_parsers/graphql_service_parser.py` | `GraphQLScanner` | `—` | `__init__, peek, next, _next_token, _skip_whitespace_and_comments, _scan_number ...` |
| `engines/document/parsers/ssdm_parsers/graphql_service_parser.py` | `GraphQLField` | `—` | `__init__` |
| `engines/document/parsers/ssdm_parsers/graphql_service_parser.py` | `GraphQLType` | `—` | `__init__` |
| `engines/document/parsers/ssdm_parsers/graphql_service_parser.py` | `GraphQLSchema` | `—` | `__init__` |
| `engines/document/parsers/ssdm_parsers/graphql_service_parser.py` | `GraphQLParser` | `—` | `__init__, parse, _match, _advance, _peek, _parse_schema_definition ...` |
| `engines/document/parsers/ssdm_parsers/graphql_service_parser.py` | `GraphQLServiceParser` | `BaseSSDMParser` | `_parse_to_document, _convert_type_to_entity, _map_gql_type_to_string, _fields_to_operations` |
| `engines/document/parsers/ssdm_parsers/mcp_parser.py` | `MCPParser` | `BaseSSDMParser` | `_parse_to_document, _parse_mcp_binding, _parse_auth, _parse_internal_binding, _parse_tool_binding, _parse_resource_binding ...` |
| `engines/document/parsers/ssdm_parsers/mib_parser.py` | `MIBLexer` | `—` | `__init__, eof, current_line, advance, skip_blank_and_comments, peek_after_blanks ...` |
| `engines/document/parsers/ssdm_parsers/mib_parser.py` | `OIDNode` | `—` | `__init__, add_child, get_full_oid` |
| `engines/document/parsers/ssdm_parsers/mib_parser.py` | `MIBDef` | `—` | `__init__` |
| `engines/document/parsers/ssdm_parsers/mib_parser.py` | `MIBDocParser` | `—` | `__init__, _parse, _parse_imports, _parse_module_identity, _set_module_field, _parse_object_type ...` |
| `engines/document/parsers/ssdm_parsers/mib_parser.py` | `MIBParser` | `BaseSSDMParser` | `_parse_to_document, _map_access, _make_get_operation, _make_set_operation, _make_notification_operation` |
| `engines/document/parsers/ssdm_parsers/openapi_parser.py` | `OpenAPIV3Parser` | `BaseSSDMParser` | `_parse_to_document, _parse_contact, _parse_license, _parse_servers, _parse_security_schemes, _parse_reusable_parameters ...` |
| `engines/document/parsers/ssdm_parsers/postman_collection_parser.py` | `PostmanCollectionParser` | `BaseSSDMParser` | `_parse_to_document, _process_item, _parse_request, _infer_entity_from_json, _infer_datatype` |
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
| `engines/document/parsers/ssdm_parsers/proto_service_parser.py` | `ProtoServiceParser` | `BaseSSDMParser` | `_parse_to_document, _message_to_entity, _field_to_attribute, _enum_to_entity, _method_to_operation` |
| `engines/document/parsers/ssdm_parsers/python_service_parser.py` | `PythonServiceParser` | `BaseSSDMParser` | `_parse_to_document, _find_app_instance, _collect_pydantic_models, _pydantic_class_to_entity, _parse_routes, _is_route_decorator ...` |
| `engines/document/parsers/ssdm_parsers/raml_parser.py` | `RAMLParser` | `BaseSSDMParser` | `_parse_to_document, _parse_resource, _parse_method, _parse_parameter, _parse_raml_type, _raml_prop_to_datatype ...` |
| `engines/document/parsers/ssdm_parsers/webidl_parser.py` | `Token` | `—` | `__init__` |
| `engines/document/parsers/ssdm_parsers/webidl_parser.py` | `WebIDLParser` | `BaseSSDMParser` | `_parse_to_document, _peek, _advance, _expect, _match, _parse_definition ...` |
| `engines/document/parsers/ssdm_parsers/wsdl_parser.py` | `WSDLParser` | `BaseSSDMParser` | `_parse_to_document, _parse_xsd_schema, _xsd_type_to_datatype, _parts_to_parameters, _parts_to_body_entity, _get_child_text` |
| `engines/document/parsers/ssdm_parsers/yang_parser.py` | `Token` | `—` | `__init__` |
| `engines/document/parsers/ssdm_parsers/yang_parser.py` | `YANGParser` | `BaseSSDMParser` | `_parse_to_document, _peek, _advance, _match, _expect, _parse_module ...` |
| `engines/document/parsers/tsdm_parsers/base_tsdm_parser.py` | `BaseTSDMParser` | `BaseDocumentParser` | `parse_bytes, parse_path, parse_stream, _parse_to_tsdm` |
| `engines/document/parsers/tsdm_parsers/tsdm_json_parser.py` | `TsdmJsonParser` | `BaseTSDMParser` | `_parse_to_tsdm, _parse_tool, _parse_parameters, _parse_outputs` |
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
| `engines/document/writers/markdown_writer.py` | `MarkdownWriter` | `BaseDocumentWriter` | `__init__, write, write_stream, write_to_file, get_supported_media_types, get_supported_extensions ...` |
| `engines/document/writers/msdm_writers/avro_schema_writer.py` | `AvroSchemaWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _entity_to_avro, _is_enum_entity ...` |
| `engines/document/writers/msdm_writers/base_msdm_writer.py` | `WriteTarget` | `str, Enum` | `` |
| `engines/document/writers/msdm_writers/base_msdm_writer.py` | `SoftDeleteStrategy` | `str, Enum` | `` |
| `engines/document/writers/msdm_writers/base_msdm_writer.py` | `ConnectionConfig` | `BaseModel` | `` |
| `engines/document/writers/msdm_writers/base_msdm_writer.py` | `BaseMSDMWriter` | `BaseDocumentWriter` | `__init__, write_stream, write, write_to_file, apply_to_database, _write_design ...` |
| `engines/document/writers/msdm_writers/cql_writer.py` | `CQLWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_create_table, _write_create_type ...` |
| `engines/document/writers/msdm_writers/cue_writer.py` | `CUEWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _entity_to_cue, _attribute_to_cue ...` |
| `engines/document/writers/msdm_writers/elasticsearch_mapping_writer.py` | `ElasticsearchMappingWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _build_index_definition, _attribute_to_es_field ...` |
| `engines/document/writers/msdm_writers/erd_writer.py` | `ERDWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _build_json, _entity_to_json ...` |
| `engines/document/writers/msdm_writers/graphql_schema_writer.py` | `GraphQLSchemaWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _is_scalar_type, _is_enum_type ...` |
| `engines/document/writers/msdm_writers/json_schema_writer.py` | `JsonSchemaWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _entity_to_schema, _attribute_to_property_schema ...` |
| `engines/document/writers/msdm_writers/mongodb_schema_writer.py` | `MongoDBSchemaWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _build_validator_schema, _entity_to_json_schema ...` |
| `engines/document/writers/msdm_writers/neo4j_schema_writer.py` | `Neo4jSchemaWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_node_constraints, _write_edge_constraints ...` |
| `engines/document/writers/msdm_writers/owl_writer.py` | `OWLWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _base_uri, _entity_to_uri ...` |
| `engines/document/writers/msdm_writers/plantuml_writer.py` | `PlantUMLWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _entity_to_block, _field_to_plantuml ...` |
| `engines/document/writers/msdm_writers/proto_writer.py` | `ProtoWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_entity, _is_enum_entity ...` |
| `engines/document/writers/msdm_writers/python_model_writer.py` | `TargetStyle` | `str, Enum` | `` |
| `engines/document/writers/msdm_writers/python_model_writer.py` | `PythonModelWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _is_enum_entity, _build_enum ...` |
| `engines/document/writers/msdm_writers/sql_ddl_writer.py` | `SqlDDLWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _build_create_table, _column_definition ...` |
| `engines/document/writers/msdm_writers/thrift_idl_writer.py` | `ThriftIDLWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _is_typedef, _is_enum ...` |
| `engines/document/writers/msdm_writers/typescript_interface_writer.py` | `TypeScriptInterfaceWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _entity_to_declaration, _is_enum ...` |
| `engines/document/writers/msdm_writers/uml_xmi_writer.py` | `UMLXmiWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _new_id, _existing_or_new_id ...` |
| `engines/document/writers/msdm_writers/xsd_writer.py` | `XSDWriter` | `BaseMSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _entity_to_schema_item, _is_simple_entity ...` |
| `engines/document/writers/osdm_writers/airflow_dag_writer.py` | `AirflowDAGWriter` | `BaseOSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_header, _write_dag_definition ...` |
| `engines/document/writers/osdm_writers/azure_logic_apps_writer.py` | `AzureLogicAppsWriter` | `BaseOSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _build_workflow, _collect_states ...` |
| `engines/document/writers/osdm_writers/base_osdm_writer.py` | `VersionStrategy` | `str, Enum` | `` |
| `engines/document/writers/osdm_writers/base_osdm_writer.py` | `VersionIncrement` | `str, Enum` | `` |
| `engines/document/writers/osdm_writers/base_osdm_writer.py` | `OSDMWriteOptions` | `WriteOptions` | `` |
| `engines/document/writers/osdm_writers/base_osdm_writer.py` | `BaseOSDMWriter` | `BaseDocumentWriter` | `__init__, write_stream, write, write_to_file, _write_design, get_supported_media_types ...` |
| `engines/document/writers/osdm_writers/bpmn_xml_writer.py` | `BPMNXMLWriter` | `BaseOSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _obj_id, _add_bpmn_element ...` |
| `engines/document/writers/osdm_writers/cep_writer.py` | `CEPWriter` | `BaseOSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _definition_to_dict, _stream_to_dict ...` |
| `engines/document/writers/osdm_writers/cmmn_xml_writer.py` | `CMMNXMLWriter` | `BaseOSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _obj_id, _add_cmmn_element ...` |
| `engines/document/writers/osdm_writers/cncf_serverless_workflow_writer.py` | `CNCFServerlessWorkflowWriter` | `BaseOSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _build_workflow, _resolve_initial_state ...` |
| `engines/document/writers/osdm_writers/dmn_xml_writer.py` | `DMNXMLWriter` | `BaseOSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _new_id, _obj_id ...` |
| `engines/document/writers/osdm_writers/epc_writer.py` | `EPCWriter` | `BaseOSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_process, _write_organisational_units ...` |
| `engines/document/writers/osdm_writers/graphml_xml_writer.py` | `GraphMLXMLWriter` | `BaseOSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _define_attributes, _write_graph ...` |
| `engines/document/writers/osdm_writers/pnml_xml_writer.py` | `PNMLXMLWriter` | `BaseOSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _is_petri_net, _get_annotation ...` |
| `engines/document/writers/osdm_writers/prefect_dag_writer.py` | `PrefectDAGWriter` | `BaseOSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_header, _write_flow_definition ...` |
| `engines/document/writers/osdm_writers/scxml_writer.py` | `SCXMLWriter` | `BaseOSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_scxml_body, _resolve_initial_state ...` |
| `engines/document/writers/osdm_writers/uml_state_machine_writer.py` | `UMLStateMachineWriter` | `BaseOSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _new_id, _add_uml_element ...` |
| `engines/document/writers/osdm_writers/xpd_writer.py` | `XPDLWriter` | `BaseOSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_participant, _write_workflow_process ...` |
| `engines/document/writers/osdm_writers/yawl_writer.py` | `YAWLWriter` | `BaseOSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_specification, _write_net ...` |
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
| `engines/document/writers/ssdm_writers/apib_writer.py` | `APIBlueprintWriter` | `BaseSSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_parameter, _write_body ...` |
| `engines/document/writers/ssdm_writers/asyncapi_writer.py` | `AsyncAPIWriter` | `BaseSSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _build_info, _build_servers ...` |
| `engines/document/writers/ssdm_writers/base_ssdm_writer.py` | `VersionStrategy` | `str, Enum` | `` |
| `engines/document/writers/ssdm_writers/base_ssdm_writer.py` | `VersionIncrement` | `str, Enum` | `` |
| `engines/document/writers/ssdm_writers/base_ssdm_writer.py` | `SSDMWriteOptions` | `WriteOptions` | `` |
| `engines/document/writers/ssdm_writers/base_ssdm_writer.py` | `BaseSSDMWriter` | `BaseDocumentWriter` | `__init__, write_stream, write, write_to_file, _write_design, get_supported_media_types ...` |
| `engines/document/writers/ssdm_writers/cddl_writer.py` | `CDDLWriter` | `BaseSSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_entity, _write_operation ...` |
| `engines/document/writers/ssdm_writers/graphql_service_writer.py` | `GraphQLServiceWriter` | `BaseSSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _is_scalar_type, _is_enum_type ...` |
| `engines/document/writers/ssdm_writers/mcp_writer.py` | `MCPWriter` | `BaseSSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _build_input_schema, _build_output_schema ...` |
| `engines/document/writers/ssdm_writers/mib_writer.py` | `MIBWriter` | `BaseSSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_object, _quote` |
| `engines/document/writers/ssdm_writers/openapi_writer.py` | `OpenAPIWriter` | `BaseSSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _build_info, _build_servers ...` |
| `engines/document/writers/ssdm_writers/postman_collection_writer.py` | `PostmanCollectionWriter` | `BaseSSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _build_request_item, _entity_to_json_example ...` |
| `engines/document/writers/ssdm_writers/proto_service_writer.py` | `ProtoServiceWriter` | `BaseSSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _prepare_operation_messages, _param_to_proto_type ...` |
| `engines/document/writers/ssdm_writers/python_service_writer.py` | `PythonServiceWriter` | `BaseSSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_pydantic_model, _write_route ...` |
| `engines/document/writers/ssdm_writers/raml_writer.py` | `RAMLWriter` | `BaseSSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _build_resources, _set_nested_resource ...` |
| `engines/document/writers/ssdm_writers/webidl_writer.py` | `WebIDLWriter` | `BaseSSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_dictionary, _write_operation ...` |
| `engines/document/writers/ssdm_writers/wsdl_writer.py` | `WSDLWriter` | `BaseSSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_types, _write_xsd_entity ...` |
| `engines/document/writers/ssdm_writers/yang_writer.py` | `YANGWriter` | `BaseSSDMWriter` | `__init__, _write_design, get_supported_media_types, get_supported_extensions, _write_module, _write_description ...` |
| `engines/document/writers/tsdm_writers/base_tsdm_writer.py` | `BaseTSDMWriter` | `BaseDocumentWriter` | `_write_design` |
| `engines/document/writers/tsdm_writers/tsdm_json_writer.py` | `TsdmJsonWriter` | `BaseTSDMWriter` | `_write_design, _tool_to_dict, _param_to_dict, _output_to_dict` |
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
BaseDocument  →  ESDMDocument
DocumentBaseModel  →  WorkbookProperties
DocumentBaseModel  →  Relationship
DocumentBaseModel  →  RelationshipCollection
DocumentBaseModel  →  SharedStrings
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
DocumentBaseModel  →  CellFormula
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
str  →  XSDFacet
Enum  →  XSDFacet
str  →  ProtobufOption
Enum  →  ProtobufOption
str  →  AvroLogicalType
Enum  →  AvroLogicalType
str  →  GraphQLDirective
Enum  →  GraphQLDirective
BaseDocument  →  MSDMDocument
str  →  YAWLJoinType
Enum  →  YAWLJoinType
str  →  YAWLSplitType
Enum  →  YAWLSplitType
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
BaseElement  →  SentryExpression
BaseElement  →  DecisionTable
BaseElement  →  ActionList
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
BaseElement  →  YAWLTaskDecorator
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
str  →  SecurityType
Enum  →  SecurityType
str  →  OAuth2Flow
Enum  →  OAuth2Flow
str  →  ApiKeyLocation
Enum  →  ApiKeyLocation
str  →  OperationType
Enum  →  OperationType
str  →  YangStatement
Enum  →  YangStatement
str  →  SnmpAccess
Enum  →  SnmpAccess
str  →  SnmpStatus
Enum  →  SnmpStatus
BaseDocument  →  SSDMDocument 
str  →  Transport
Enum  →  Transport
str  →  AuthMethod
Enum  →  AuthMethod
str  →  ApiKeyLocation
Enum  →  ApiKeyLocation
str  →  ValueSource
Enum  →  ValueSource
str  →  OAuth2Flow
Enum  →  OAuth2Flow
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
str  →  HttpMethod
Enum  →  HttpMethod
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
BaseMSDMParser  →  AvroSchemaParser
BaseDocumentParser  →  BaseMSDMParser
BaseMSDMParser  →  CQLParser
BaseMSDMParser  →  CueParser
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
BaseOSDMParser  →  AirflowDAGParser
BaseOSDMParser  →  AWSStepFunctionsParser
BaseOSDMParser  →  AzureLogicAppsParser
BaseDocumentParser  →  BaseOSDMParser
BaseOSDMParser  →  BPMNXMLParser
BaseOSDMParser  →  CEPParser
BaseOSDMParser  →  CMMNXMLParser
BaseOSDMParser  →  CNCFServerlessWorkflowParser
BaseOSDMParser  →  DMNXMLParser
BaseOSDMParser  →  EPCParser
BaseOSDMParser  →  GraphMLXMLParser
BaseOSDMParser  →  PNMLXMLParser
BaseOSDMParser  →  PrefectDAGParser
BaseOSDMParser  →  SCXMLParser
BaseOSDMParser  →  UMLStateMachineParser
BaseOSDMParser  →  XPDLParser
BaseOSDMParser  →  YAWLParser
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
APIBObject  →  APIBMetadata
APIBObject  →  APIBParameter
APIBObject  →  APIBBody
APIBObject  →  APIBAction
APIBObject  →  APIBResource
APIBObject  →  APIBGroup
BaseSSDMParser  →  APIBlueprintToSSDMParser
BaseSSDMParser  →  AsyncAPIParser
BaseDocumentParser  →  BaseSSDMParser
BaseSSDMParser  →  CDDLServiceParser
BaseSSDMParser  →  GraphQLServiceParser
BaseSSDMParser  →  MCPParser
BaseSSDMParser  →  MIBParser
BaseSSDMParser  →  OpenAPIV3Parser
BaseSSDMParser  →  PostmanCollectionParser
BaseSSDMParser  →  ProtoServiceParser
BaseSSDMParser  →  PythonServiceParser
BaseSSDMParser  →  RAMLParser
BaseSSDMParser  →  WebIDLParser
BaseSSDMParser  →  WSDLParser
BaseSSDMParser  →  YANGParser
BaseDocumentParser  →  BaseTSDMParser
BaseTSDMParser  →  TsdmJsonParser
BaseDocumentParser  →  XmlDocumentParser
BaseDocumentParser  →  YamlDocumentParser
BaseModel  →  WriteOptions
ABC  →  BaseDocumentWriter
BaseDocumentWriter  →  BinaryWriter
BaseDocumentWriter  →  JsonDocumentWriter
BaseDocumentWriter  →  LatexWriter
BaseDocumentWriter  →  MarkdownWriter
BaseMSDMWriter  →  AvroSchemaWriter
str  →  WriteTarget
Enum  →  WriteTarget
str  →  SoftDeleteStrategy
Enum  →  SoftDeleteStrategy
BaseModel  →  ConnectionConfig
BaseDocumentWriter  →  BaseMSDMWriter
BaseMSDMWriter  →  CQLWriter
BaseMSDMWriter  →  CUEWriter
BaseMSDMWriter  →  ElasticsearchMappingWriter
BaseMSDMWriter  →  ERDWriter
BaseMSDMWriter  →  GraphQLSchemaWriter
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
BaseOSDMWriter  →  AirflowDAGWriter
BaseOSDMWriter  →  AzureLogicAppsWriter
str  →  VersionStrategy
Enum  →  VersionStrategy
str  →  VersionIncrement
Enum  →  VersionIncrement
WriteOptions  →  OSDMWriteOptions
BaseDocumentWriter  →  BaseOSDMWriter
BaseOSDMWriter  →  BPMNXMLWriter
BaseOSDMWriter  →  CEPWriter
BaseOSDMWriter  →  CMMNXMLWriter
BaseOSDMWriter  →  CNCFServerlessWorkflowWriter
BaseOSDMWriter  →  DMNXMLWriter
BaseOSDMWriter  →  EPCWriter
BaseOSDMWriter  →  GraphMLXMLWriter
BaseOSDMWriter  →  PNMLXMLWriter
BaseOSDMWriter  →  PrefectDAGWriter
BaseOSDMWriter  →  SCXMLWriter
BaseOSDMWriter  →  UMLStateMachineWriter
BaseOSDMWriter  →  XPDLWriter
BaseOSDMWriter  →  YAWLWriter
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
BaseSSDMWriter  →  APIBlueprintWriter
BaseSSDMWriter  →  AsyncAPIWriter
str  →  VersionStrategy
Enum  →  VersionStrategy
str  →  VersionIncrement
Enum  →  VersionIncrement
WriteOptions  →  SSDMWriteOptions
BaseDocumentWriter  →  BaseSSDMWriter
BaseSSDMWriter  →  CDDLWriter
BaseSSDMWriter  →  GraphQLServiceWriter
BaseSSDMWriter  →  MCPWriter
BaseSSDMWriter  →  MIBWriter
BaseSSDMWriter  →  OpenAPIWriter
BaseSSDMWriter  →  PostmanCollectionWriter
BaseSSDMWriter  →  ProtoServiceWriter
BaseSSDMWriter  →  PythonServiceWriter
BaseSSDMWriter  →  RAMLWriter
BaseSSDMWriter  →  WebIDLWriter
BaseSSDMWriter  →  WSDLWriter
BaseSSDMWriter  →  YANGWriter
BaseDocumentWriter  →  BaseTSDMWriter
BaseTSDMWriter  →  TsdmJsonWriter
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

### ⚠️ خطاهای Parse
- `engines/document/writers/msdm_writers/influxdb_schema_writer.py`: SyntaxError: invalid syntax (influxdb_schema_writer.py, line 271)
- `engines/document/writers/osdm_writers/aws_step_functions_writer.py`: SyntaxError: invalid syntax (aws_step_functions_writer.py, line 18)

### 🔴 کلاس‌های بزرگ (بیش از ۱۵ متد — نشانه نقض SRP)
- `DOCXExtractor` در `engines/document/parsers/docx_parser/docx_extractor.py` — 68 متد
- `DOCXImageExtractor` در `engines/document/parsers/docx_parser/docx_image_extractor.py` — 18 متد
- `OMMLParser` در `engines/document/parsers/docx_parser/docx_math_parser.py` — 28 متد
- `DOCXParser` در `engines/document/parsers/docx_parser/docx_parser.py` — 61 متد
- `DocxUtils` در `engines/document/parsers/docx_parser/docx_utils.py` — 36 متد
- `HTMLDocumentParser` در `engines/document/parsers/html_parser.py` — 31 متد
- `LatexParser` در `engines/document/parsers/latex_parser.py` — 35 متد
- `CueParser` در `engines/document/parsers/msdm_parsers/cue_parser.py` — 17 متد
- `GraphQLSchemaParser` در `engines/document/parsers/msdm_parsers/graphql_schema_parser.py` — 21 متد
- `ProtoParser` در `engines/document/parsers/msdm_parsers/proto_msdm_parser.py` — 18 متد
- `TypeScriptInterfaceParser` در `engines/document/parsers/msdm_parsers/typescript_interface_parser.py` — 17 متد
- `AirflowDAGParser` در `engines/document/parsers/osdm_parsers/airflow_dag_parser.py` — 19 متد
- `BPMNXMLParser` در `engines/document/parsers/osdm_parsers/bpmn_xml_parser.py` — 55 متد
- `CMMNXMLParser` در `engines/document/parsers/osdm_parsers/cmmn_xml_parser.py` — 17 متد
- `ContentExtractor` در `engines/document/parsers/pdf_parser/content_extractor.py` — 27 متد
- `FontHandler` در `engines/document/parsers/pdf_parser/font_handler.py` — 20 متد
- `PDFMetadataExtractor` در `engines/document/parsers/pdf_parser/metadata_extractor.py` — 24 متد
- `APIBlueprintParser` در `engines/document/parsers/ssdm_parsers/apib_parser.py` — 16 متد
- `GraphQLParser` در `engines/document/parsers/ssdm_parsers/graphql_service_parser.py` — 19 متد
- `MIBDocParser` در `engines/document/parsers/ssdm_parsers/mib_parser.py` — 16 متد
- `OpenAPIV3Parser` در `engines/document/parsers/ssdm_parsers/openapi_parser.py` — 25 متد
- `ProtoParser` در `engines/document/parsers/ssdm_parsers/proto_service_parser.py` — 17 متد
- `PythonServiceParser` در `engines/document/parsers/ssdm_parsers/python_service_parser.py` — 17 متد
- `WebIDLParser` در `engines/document/parsers/ssdm_parsers/webidl_parser.py` — 20 متد
- `YANGParser` در `engines/document/parsers/ssdm_parsers/yang_parser.py` — 23 متد
- `LatexWriter` در `engines/document/writers/latex_writer.py` — 24 متد
- `MarkdownWriter` در `engines/document/writers/markdown_writer.py` — 19 متد
- `AvroSchemaWriter` در `engines/document/writers/msdm_writers/avro_schema_writer.py` — 16 متد
- `CQLWriter` در `engines/document/writers/msdm_writers/cql_writer.py` — 23 متد
- `GraphQLSchemaWriter` در `engines/document/writers/msdm_writers/graphql_schema_writer.py` — 21 متد
- `ProtoWriter` در `engines/document/writers/msdm_writers/proto_writer.py` — 16 متد
- `SqlDDLWriter` در `engines/document/writers/msdm_writers/sql_ddl_writer.py` — 20 متد
- `TypeScriptInterfaceWriter` در `engines/document/writers/msdm_writers/typescript_interface_writer.py` — 16 متد
- `XSDWriter` در `engines/document/writers/msdm_writers/xsd_writer.py` — 16 متد
- `BPMNXMLWriter` در `engines/document/writers/osdm_writers/bpmn_xml_writer.py` — 63 متد
- `CMMNXMLWriter` در `engines/document/writers/osdm_writers/cmmn_xml_writer.py` — 22 متد
- `DMNXMLWriter` در `engines/document/writers/osdm_writers/dmn_xml_writer.py` — 20 متد
- `AnnotationWriter` در `engines/document/writers/pdf_writer/annotation_writer.py` — 27 متد
- `PDFEncryptor` در `engines/document/writers/pdf_writer/encryption.py` — 30 متد
- `FontManager` در `engines/document/writers/pdf_writer/font_manager.py` — 31 متد
- `MetadataWriter` در `engines/document/writers/pdf_writer/metadata_writer.py` — 18 متد
- `PDFOptimizer` در `engines/document/writers/pdf_writer/optimizer.py` — 33 متد
- `OutlineBuilder` در `engines/document/writers/pdf_writer/outline_builder.py` — 17 متد
- `PPTXWriter` در `engines/document/writers/pptx_writer/writer.py` — 19 متد
- `ESDMBaseWriter` در `engines/document/writers/spreadsheet_writer/base.py` — 19 متد
- `GraphQLServiceWriter` در `engines/document/writers/ssdm_writers/graphql_service_writer.py` — 24 متد
- `OpenAPIWriter` در `engines/document/writers/ssdm_writers/openapi_writer.py` — 16 متد
- `YANGWriter` در `engines/document/writers/ssdm_writers/yang_writer.py` — 20 متد

### 🟡 فایل‌های خالی یا فقط شامل import
- `config/settings.py` [22 lines]
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
- `engines/document/parsers/cad_parser/csdm_loader.py` [641 lines]
- `engines/document/parsers/cad_parser/csdm_parser.py` [74 lines]
- `engines/document/parsers/cad_parser/csdm_relationships.py` [281 lines]
- `engines/document/parsers/cad_parser/oda_bridge.py` [273 lines]
- `engines/document/parsers/cad_parser.py` [133 lines]
- `engines/document/parsers/pptx_parser/constants.py` [108 lines]
- `engines/document/parsers/spreadsheet_parser/xlsx/constants.py` [245 lines]
- `engines/document/parsers/spreadsheet_parser/xlsx/namespaces.py` [16 lines]
- `engines/document/parsers/spreadsheet_parser/xlsx/shared_strings_builder.py` [0 lines]
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
- `engines/document/writers/html_writer.py` [279 lines]
- `engines/document/writers/pdf_writer/init.py` [24 lines]
- `engines/document/writers/pptx_writer/constants.py` [76 lines]
- `engines/document/writers/spreadsheet_writer/xlsx/const.py` [7 lines]
- `engines/orchestration/base_workflow_model.py` [0 lines]
- `engines/orchestration/bpmn2_model.py` [0 lines]
- `engines/orchestration/dag_model.py` [0 lines]
- `engines/orchestration/event_driven_model.py` [0 lines]
- `engines/orchestration/petri_net_model.py` [0 lines]
- `engines/orchestration/state_machine_model.py` [0 lines]
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

### 🟠 کلاس‌های بدون Base Class (احتمال عدم رعایت interface مشترک)
- `DocumentEmbeddingService` در `engines/document/embedding/service.py`
- `IngestionService` در `engines/document/ingestion/ingestion_service.py`
- `AsyncIngestService` در `engines/document/ingestion/services/async_ingest_service.py`
- `BatchIngestService` در `engines/document/ingestion/services/batch_ingest_service.py`
- `UploadService` در `engines/document/ingestion/services/upload_service.py`
- `GraphQLService` در `engines/document/models/ssdm_models.py`
- `ServiceExposure` در `engines/document/models/ssdm_models.py`
- `ServiceBinding` در `engines/document/models/ssdm_models.py`
- `InternalServiceBinding` در `engines/document/models/ssdm_models.py`
- `FontHandler` در `engines/document/parsers/pdf_parser/font_handler.py`
- `ServiceMethod` در `engines/document/parsers/ssdm_parsers/proto_service_parser.py`
- `ServiceDef` در `engines/document/parsers/ssdm_parsers/proto_service_parser.py`
- `PDFSecurityHandler` در `engines/document/writers/pdf_writer/encryption.py`
- `InteractionStrategy` در `engines/interaction/base_strategy.py`
- `VectorService` در `engines/rag/vector_service.py`

---

## 📝 یادداشت

این گزارش به صورت **استاتیک** (تحلیل AST) تولید شده است.  
برای تحلیل runtime و dependency injection، ابزار تکمیلی لازم است.
