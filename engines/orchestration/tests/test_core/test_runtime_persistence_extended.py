"""Extended runtime persistence tests — Phase A/B infrastructure."""

from __future__ import annotations

from datetime import datetime

import pytest

from engines.orchestration.core.engine import OrchestrationEngine, ProcessDefinition
from engines.orchestration.core.instance import InstanceState
from engines.orchestration.persistence.event_repository import EventRepository
from engines.orchestration.persistence.history_repository import HistoryRepository
from engines.orchestration.persistence.instance_repository import InstanceRepository
from engines.orchestration.persistence.token_repository import TokenRepository
from engines.orchestration.persistence.variable_repository import VariableRepository
from engines.orchestration.runtime.incident_manager import IncidentManager, IncidentType, IncidentState
from engines.orchestration.runtime.tenant import TenantManager, TenantContext, TenantInfo
from engines.orchestration.runtime.circuit_breaker import CircuitBreakerRegistry, RetryConfig
from engines.orchestration.runtime.rate_limiter import RateLimiter, RateLimitConfig
from engines.orchestration.forms.form_engine import FormDefinition, FormField, FormFieldType, FormEngine


def _make_engine():
    return OrchestrationEngine(
        event_repository=EventRepository(),
        history_repository=HistoryRepository(),
        instance_repository=InstanceRepository(),
        variable_repository=VariableRepository(),
        token_repository=TokenRepository(),
    )


class TestIncidentManager:
    def test_create_and_resolve_incident(self):
        mgr = IncidentManager()
        inc = mgr.create_incident(
            IncidentType.PROCESS_EXECUTION_FAILED,
            "inst1", "Something went wrong",
            activity_id="task1",
        )
        assert inc.state == IncidentState.OPEN
        assert inc.incident_type == IncidentType.PROCESS_EXECUTION_FAILED
        resolved = mgr.resolve_incident(inc.incident_id, "manual fix")
        assert resolved is not None
        assert resolved.state == IncidentState.RESOLVED

    def test_move_to_dead_letter(self):
        mgr = IncidentManager()
        inc = mgr.create_incident(IncidentType.RETRY_EXHAUSTED, "inst1", "max retries")
        dl = mgr.move_to_dead_letter(inc.incident_id)
        assert dl is not None
        assert dl.state == IncidentState.DEAD_LETTER

    def test_query_incidents(self):
        mgr = IncidentManager()
        mgr.create_incident(IncidentType.JOB_EXECUTION_FAILED, "inst1", "err1")
        mgr.create_incident(IncidentType.TIMER_PROCESSING_FAILED, "inst2", "err2")
        mgr.create_incident(IncidentType.JOB_EXECUTION_FAILED, "inst3", "err3")
        from engines.orchestration.runtime.incident_manager import IncidentQuery
        results = mgr.query_incidents(IncidentQuery(incident_type=IncidentType.JOB_EXECUTION_FAILED))
        assert len(results) == 2

    def test_get_statistics(self):
        mgr = IncidentManager()
        inc = mgr.create_incident(IncidentType.PROCESS_EXECUTION_FAILED, "inst1", "err")
        mgr.resolve_incident(inc.incident_id)
        mgr.create_incident(IncidentType.JOB_EXECUTION_FAILED, "inst2", "err2")
        stats = mgr.get_statistics()
        assert stats.get("resolved", 0) == 1
        assert stats.get("open", 0) >= 1


class TestTenantManager:
    def test_register_and_get_tenant(self):
        mgr = TenantManager()
        mgr.register_tenant(TenantInfo(tenant_id="t1", name="Acme"))
        t = mgr.get_tenant("t1")
        assert t is not None
        assert t.name == "Acme"

    def test_tenant_context_propagation(self):
        TenantContext.set_current_tenant("t1")
        assert TenantContext.get_current_tenant() == "t1"
        TenantContext.set_current_tenant(None)
        assert TenantContext.get_current_tenant() is None

    def test_tenant_scope_context_manager(self):
        with TenantContext.tenant_scope("t2"):
            assert TenantContext.get_current_tenant() == "t2"
        assert TenantContext.get_current_tenant() is None

    def test_tenant_quota(self):
        mgr = TenantManager()
        mgr.register_tenant(TenantInfo(tenant_id="t1", name="Acme", max_instances=10))
        assert mgr.check_tenant_quota("t1", 5) is True
        assert mgr.check_tenant_quota("t1", 15) is False

    def test_deactivate_tenant(self):
        mgr = TenantManager()
        mgr.register_tenant(TenantInfo(tenant_id="t1", name="Acme"))
        assert mgr.is_tenant_active("t1") is True
        mgr.deactivate_tenant("t1")
        assert mgr.is_tenant_active("t1") is False


class TestCircuitBreaker:
    def test_circuit_stays_closed_on_success(self):
        reg = CircuitBreakerRegistry()
        cb = reg.get_or_create("svc1")
        assert cb.state == "closed"
        cb.record_success()
        assert cb.state == "closed"

    def test_circuit_opens_after_failures(self):
        from engines.orchestration.runtime.circuit_breaker import CircuitBreakerConfig
        reg = CircuitBreakerRegistry()
        cb = reg.get_or_create("svc2", CircuitBreakerConfig(failure_threshold=3))
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "closed"
        cb.record_failure()
        assert cb.state == "open"

    def test_circuit_half_open_after_timeout(self):
        import time
        from engines.orchestration.runtime.circuit_breaker import CircuitBreakerConfig
        reg = CircuitBreakerRegistry()
        cb = reg.get_or_create("svc3", CircuitBreakerConfig(failure_threshold=1, open_duration_seconds=0))
        cb.record_failure()
        assert cb.state == "open"
        time.sleep(0.1)
        assert cb.can_execute() is True
        assert cb.state == "half_open"

    def test_retry_config_delay(self):
        config = RetryConfig(initial_delay_ms=100, backoff_multiplier=2.0, max_delay_ms=5000)
        d0 = config.get_delay(0)
        d1 = config.get_delay(1)
        d2 = config.get_delay(2)
        assert d0 < d1 < d2
        assert d2 <= 5.0


class TestRateLimiter:
    def test_allow_within_limit(self):
        rl = RateLimiter()
        rl.configure(RateLimitConfig(resource_name="api1", max_requests=5, window_seconds=60))
        for _ in range(5):
            status = rl.check("api1")
            assert status.allowed is True

    def test_reject_over_limit(self):
        rl = RateLimiter()
        rl.configure(RateLimitConfig(resource_name="api2", max_requests=3, window_seconds=60))
        for _ in range(3):
            rl.check("api2")
        status = rl.check("api2")
        assert status.allowed is False
        assert status.remaining == 0

    def test_peek_does_not_consume(self):
        rl = RateLimiter()
        rl.configure(RateLimitConfig(resource_name="api3", max_requests=10, window_seconds=60))
        s1 = rl.peek("api3")
        s2 = rl.peek("api3")
        assert s1.remaining == s2.remaining

    def test_reset(self):
        rl = RateLimiter()
        rl.configure(RateLimitConfig(resource_name="api4", max_requests=1, window_seconds=60))
        rl.check("api4")
        assert rl.check("api4").allowed is False
        rl.reset("api4")
        assert rl.check("api4").allowed is True


class TestFormEngine:
    def test_create_form(self):
        form = FormDefinition(id="f1", name="Test Form", key="test_form")
        form.fields.append(FormField(
            id="name", label="Name", field_type=FormFieldType.STRING, required=True,
        ))
        assert len(form.fields) == 1

    def test_form_validation(self):
        form = FormDefinition(id="f2", name="Test", key="test")
        form.fields.append(FormField(
            id="email", label="Email", field_type=FormFieldType.STRING, required=True,
        ))
        errors = form.validate({})
        assert "email" in errors

    def test_form_submit(self):
        engine = FormEngine()
        form = FormDefinition(id="f3", name="Test", key="test")
        form.fields.append(FormField(id="name", label="Name", field_type=FormFieldType.STRING))
        engine.register_form(form)
        result = engine.submit_form("test", {"name": "John"})
        assert result["success"] is True

    def test_render_form(self):
        engine = FormEngine()
        form = FormDefinition(id="f4", name="Test", key="test")
        form.fields.append(FormField(
            id="name", label="Name", field_type=FormFieldType.STRING, default_value="Default",
        ))
        engine.register_form(form)
        rendered = engine.render_form("test")
        assert "form" in rendered
        assert "data" in rendered


class TestMultiTenancyIntegration:
    @pytest.mark.asyncio
    async def test_tenant_aware_engine_operations(self):
        _engine = _make_engine()
        mgr = TenantManager()
        mgr.register_tenant(TenantInfo(tenant_id="tenant-a", name="Tenant A"))
        assert mgr.is_tenant_active("tenant-a") is True

    def test_tenant_filter_mixin(self):
        from engines.orchestration.runtime.tenant import TenantAwareMixin
        class TestRepo(TenantAwareMixin):
            pass
        repo = TestRepo()
        TenantContext.set_current_tenant("t1")
        filtered = repo._tenant_filter({"key": "val"})
        assert filtered.get("tenant_id") == "t1"
        TenantContext.set_current_tenant(None)
