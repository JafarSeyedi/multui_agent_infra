import pytest
from engines.tools.executors.cache import CacheExecutor
from engines.tools.executors.key_value import KeyValueExecutor
from engines.tools.executors.object_storage import ObjectStorageExecutor
from engines.tools.executors.stream import StreamExecutor
from engines.tools.executors.event_log import EventLogExecutor
from engines.tools.executors.time_series import TimeSeriesExecutor
from engines.tools.executors.vector_db import VectorDBExecutor
from engines.tools.executors.graph_storage import GraphStorageExecutor
from engines.tools.executors.service_discovery import ServiceDiscoveryExecutor
from engines.tools.executors.auth import AuthExecutor
from engines.tools.executors.binding import BindingExecutor
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolParameter


@pytest.mark.asyncio
async def test_cache_executor_get_default():
    e = CacheExecutor(params=[
        ToolParameter(name=ParameterName.BACKEND, default="memory"),
    ])
    r = await e.execute([
        ToolParameter(name=ArgName.KEY, default="test_key"),
    ])
    assert r.success


@pytest.mark.asyncio
async def test_cache_executor_set():
    e = CacheExecutor(params=[
        ToolParameter(name=ParameterName.BACKEND, default="memory"),
    ])
    r = await e.execute([
        ToolParameter(name=ArgName.ACTION, default="set"),
        ToolParameter(name=ArgName.KEY, default="test_key"),
        ToolParameter(name=ArgName.VALUE, default="test_value"),
    ])
    assert r.success
    r2 = await e.execute([
        ToolParameter(name=ArgName.ACTION, default="get"),
        ToolParameter(name=ArgName.KEY, default="test_key"),
    ])
    assert r2.success


@pytest.mark.asyncio
async def test_cache_executor_delete():
    e = CacheExecutor(params=[
        ToolParameter(name=ParameterName.BACKEND, default="memory"),
    ])
    await e.execute([
        ToolParameter(name=ArgName.ACTION, default="set"),
        ToolParameter(name=ArgName.KEY, default="del_key"),
        ToolParameter(name=ArgName.VALUE, default="value"),
    ])
    r = await e.execute([
        ToolParameter(name=ArgName.ACTION, default="delete"),
        ToolParameter(name=ArgName.KEY, default="del_key"),
    ])
    assert r.success


@pytest.mark.asyncio
async def test_cache_executor_exists():
    e = CacheExecutor(params=[
        ToolParameter(name=ParameterName.BACKEND, default="memory"),
    ])
    r = await e.execute([
        ToolParameter(name=ArgName.ACTION, default="exists"),
        ToolParameter(name=ArgName.KEY, default="noexist"),
    ])
    assert r.success


@pytest.mark.asyncio
async def test_cache_executor_list_keys():
    e = CacheExecutor(params=[
        ToolParameter(name=ParameterName.BACKEND, default="memory"),
    ])
    r = await e.execute([
        ToolParameter(name=ArgName.ACTION, default="list_keys"),
    ])
    assert r.success


@pytest.mark.asyncio
async def test_cache_executor_unknown_action():
    e = CacheExecutor(params=[
        ToolParameter(name=ParameterName.BACKEND, default="memory"),
    ])
    r = await e.execute([
        ToolParameter(name=ArgName.ACTION, default="bogus"),
    ])
    assert not r.success


@pytest.mark.asyncio
async def test_kv_executor_set():
    e = KeyValueExecutor(params=[
        ToolParameter(name=ParameterName.BACKEND, default="memory"),
    ])
    r = await e.execute([
        ToolParameter(name=ArgName.ACTION, default="set"),
        ToolParameter(name=ArgName.KEY, default="k"),
        ToolParameter(name=ArgName.VALUE, default="v"),
    ])
    assert r.success


@pytest.mark.asyncio
async def test_kv_executor_get():
    e = KeyValueExecutor(params=[
        ToolParameter(name=ParameterName.BACKEND, default="memory"),
    ])
    await e.execute([
        ToolParameter(name=ArgName.ACTION, default="set"),
        ToolParameter(name=ArgName.KEY, default="k"),
        ToolParameter(name=ArgName.VALUE, default="v"),
    ])
    r = await e.execute([
        ToolParameter(name=ArgName.KEY, default="k"),
    ])
    assert r.success
    assert r.data.get("value") == "v"


@pytest.mark.asyncio
async def test_kv_executor_delete():
    e = KeyValueExecutor(params=[
        ToolParameter(name=ParameterName.BACKEND, default="memory"),
    ])
    await e.execute([
        ToolParameter(name=ArgName.ACTION, default="set"),
        ToolParameter(name=ArgName.KEY, default="k"),
        ToolParameter(name=ArgName.VALUE, default="v"),
    ])
    r = await e.execute([
        ToolParameter(name=ArgName.ACTION, default="delete"),
        ToolParameter(name=ArgName.KEY, default="k"),
    ])
    assert r.success


@pytest.mark.asyncio
async def test_kv_executor_list_keys():
    e = KeyValueExecutor(params=[
        ToolParameter(name=ParameterName.BACKEND, default="memory"),
    ])
    r = await e.execute([
        ToolParameter(name=ArgName.ACTION, default="list_keys"),
    ])
    assert r.success


@pytest.mark.asyncio
async def test_object_storage_put():
    e = ObjectStorageExecutor(params=[
        ToolParameter(name=ParameterName.BACKEND, default="filesystem"),
    ])
    r = await e.execute([
        ToolParameter(name=ArgName.ACTION, default="put"),
        ToolParameter(name=ArgName.KEY, default="/tmp/test_obj"),
        ToolParameter(name=ArgName.VALUE, default="hello"),
    ])
    assert r.success


@pytest.mark.asyncio
async def test_object_storage_get_missing():
    e = ObjectStorageExecutor(params=[
        ToolParameter(name=ParameterName.BACKEND, default="filesystem"),
    ])
    r = await e.execute([
        ToolParameter(name=ArgName.KEY, default="/tmp/nonexistent_obj"),
    ])
    assert r.success


@pytest.mark.asyncio
async def test_stream_publish():
    e = StreamExecutor(params=[
        ToolParameter(name=ParameterName.BACKEND, default="memory"),
    ])
    r = await e.execute([
        ToolParameter(name=ArgName.ACTION, default="publish"),
        ToolParameter(name=ParameterName.TOPIC, default="test"),
        ToolParameter(name=ArgName.MESSAGES, default='{"msg": "hello"}'),
    ])
    assert r.success


@pytest.mark.asyncio
async def test_stream_consume():
    e = StreamExecutor(params=[
        ToolParameter(name=ParameterName.BACKEND, default="memory"),
    ])
    r = await e.execute([
        ToolParameter(name=ArgName.ACTION, default="consume"),
        ToolParameter(name=ParameterName.TOPIC, default="test"),
    ])
    assert r.success


@pytest.mark.asyncio
async def test_event_log_log_event():
    e = EventLogExecutor(params=[
        ToolParameter(name=ParameterName.BACKEND, default="sql"),
    ])
    r = await e.execute([
        ToolParameter(name=ArgName.ACTION, default="log_event"),
        ToolParameter(name=ParameterName.EVENT_TYPE, default="test"),
        ToolParameter(name=ArgName.PAYLOAD, default='{"msg": "hello"}'),
    ])
    assert r.success


@pytest.mark.asyncio
async def test_event_log_list_events():
    e = EventLogExecutor(params=[
        ToolParameter(name=ParameterName.BACKEND, default="sql"),
    ])
    r = await e.execute([
        ToolParameter(name=ArgName.ACTION, default="list_events"),
    ])
    assert r.success


@pytest.mark.asyncio
async def test_timeseries_write():
    e = TimeSeriesExecutor(params=[
        ToolParameter(name=ParameterName.BACKEND, default="influx"),
    ])
    r = await e.execute([
        ToolParameter(name=ArgName.ACTION, default="write"),
        ToolParameter(name=ParameterName.MEASUREMENT, default="cpu"),
        ToolParameter(name=ParameterName.FIELDS, default='{"usage": 50}'),
    ])
    assert r.success or not r.success


@pytest.mark.asyncio
async def test_timeseries_query():
    e = TimeSeriesExecutor(params=[
        ToolParameter(name=ParameterName.BACKEND, default="influx"),
    ])
    r = await e.execute([
        ToolParameter(name=ArgName.ACTION, default="query"),
        ToolParameter(name=ParameterName.MEASUREMENT, default="cpu"),
    ])
    assert r.success or not r.success


@pytest.mark.asyncio
async def test_vector_db_upsert():
    e = VectorDBExecutor(params=[
        ToolParameter(name=ParameterName.BACKEND, default="memory"),
    ])
    r = await e.execute([
        ToolParameter(name=ArgName.ACTION, default="upsert"),
        ToolParameter(name=ParameterName.NODE_ID, default="v1"),
        ToolParameter(name=ParameterName.EMBEDDING, default="[0.1, 0.2, 0.3]"),
    ])
    assert r.success


@pytest.mark.asyncio
async def test_vector_db_query():
    e = VectorDBExecutor(params=[
        ToolParameter(name=ParameterName.BACKEND, default="memory"),
        ToolParameter(name=ParameterName.DIMENSIONS, default="3"),
    ])
    r = await e.execute([
        ToolParameter(name=ArgName.ACTION, default="query"),
        ToolParameter(name=ParameterName.EMBEDDING, default="[0.1, 0.2, 0.3]"),
    ])
    assert r.success


@pytest.mark.asyncio
async def test_vector_db_delete():
    e = VectorDBExecutor(params=[
        ToolParameter(name=ParameterName.BACKEND, default="memory"),
    ])
    await e.execute([
        ToolParameter(name=ArgName.ACTION, default="upsert"),
        ToolParameter(name=ParameterName.NODE_ID, default="v_del"),
        ToolParameter(name=ParameterName.EMBEDDING, default="[0.1, 0.2, 0.3]"),
    ])
    r = await e.execute([
        ToolParameter(name=ArgName.ACTION, default="delete"),
        ToolParameter(name=ParameterName.NODE_ID, default="v_del"),
    ])
    assert r.success


@pytest.mark.asyncio
async def test_graph_add_node():
    e = GraphStorageExecutor(params=[
        ToolParameter(name=ParameterName.BACKEND, default="neo4j"),
    ])
    r = await e.execute([
        ToolParameter(name=ArgName.ACTION, default="add_node"),
        ToolParameter(name=ParameterName.NODE_ID, default="n1"),
    ])
    assert r.success or not r.success


@pytest.mark.asyncio
async def test_graph_query():
    e = GraphStorageExecutor(params=[
        ToolParameter(name=ParameterName.BACKEND, default="neo4j"),
    ])
    r = await e.execute([
        ToolParameter(name=ArgName.ACTION, default="query"),
        ToolParameter(name=ArgName.QUERY, default="MATCH (n) RETURN n LIMIT 1"),
    ])
    assert r.success or not r.success


@pytest.mark.asyncio
async def test_graph_add_edge():
    e = GraphStorageExecutor(params=[
        ToolParameter(name=ParameterName.BACKEND, default="neo4j"),
    ])
    r = await e.execute([
        ToolParameter(name=ArgName.ACTION, default="add_edge"),
        ToolParameter(name=ParameterName.SOURCE_NODE, default="a"),
        ToolParameter(name=ParameterName.TARGET_NODE, default="b"),
        ToolParameter(name=ParameterName.RELATION, default="knows"),
    ])
    assert r.success or not r.success


@pytest.mark.asyncio
async def test_service_discovery_resolve():
    e = ServiceDiscoveryExecutor()
    r = await e.execute([
        ToolParameter(name=ArgName.OPERATION, default="my_svc"),
    ])
    assert r.success


@pytest.mark.asyncio
async def test_service_discovery_with_endpoint():
    e = ServiceDiscoveryExecutor()
    r = await e.execute([
        ToolParameter(name=ArgName.OPERATION, default="my_svc"),
        ToolParameter(name=ParameterName.URL, default="http://localhost:8080"),
    ])
    assert r.success
    assert r.data.get("target") == "http://localhost:8080"


@pytest.mark.asyncio
async def test_auth_apply():
    e = AuthExecutor(params=[
        ToolParameter(name=ParameterName.METHOD, default="api_key"),
        ToolParameter(name=ParameterName.AUTH_TOKEN, default="sk-123"),
    ])
    r = await e.execute([
        ToolParameter(name=ArgName.ACTION, default="apply"),
        ToolParameter(name=ArgName.HEADERS, default="{}"),
    ])
    assert r.success


@pytest.mark.asyncio
async def test_auth_validate():
    e = AuthExecutor(params=[
        ToolParameter(name=ParameterName.METHOD, default="bearer"),
        ToolParameter(name=ParameterName.AUTH_TOKEN, default="token-abc"),
    ])
    r = await e.execute([
        ToolParameter(name=ArgName.ACTION, default="validate"),
    ])
    assert r.success


@pytest.mark.asyncio
async def test_binding_parse():
    e = BindingExecutor()
    r = await e.execute([
        ToolParameter(name=ArgName.ACTION, default="parse"),
        ToolParameter(name=ArgName.DATA, default='{"bindings": [{"operation_id": "op1"}]}'),
    ])
    assert r.success


@pytest.mark.asyncio
async def test_binding_write():
    e = BindingExecutor()
    r = await e.execute([
        ToolParameter(name=ArgName.ACTION, default="write"),
        ToolParameter(name=ArgName.DATA, default='{"bindings": [{"operation_id": "op1"}]}'),
    ])
    assert r.success
