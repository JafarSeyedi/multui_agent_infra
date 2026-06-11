import pytest
from datetime import datetime
from engines.orchestration.bam.dashboard.dashboard_manager import DashboardManager
from engines.document.models.bam_models import (
    Dashboard, DashboardWidget, BusinessMetric, KPI,
    MetricValue,
)


@pytest.mark.asyncio
async def test_dashboard_manager_register():
    mgr = DashboardManager()
    dash = Dashboard(
        dashboard_id="d1", name="Operations",
        widgets=[
            DashboardWidget(widget_id="w1", type="gauge", title="CPU", data_source="metric:cpu"),
            DashboardWidget(widget_id="w2", type="chart", title="Latency", data_source="metric:latency"),
        ],
    )
    mgr.register(dash)
    assert mgr.get("d1") is not None
    assert len(mgr.list_all()) == 1


@pytest.mark.asyncio
async def test_dashboard_manager_resolve_widget_data():
    mgr = DashboardManager()
    dash = Dashboard(
        dashboard_id="d1", name="Ops",
        widgets=[
            DashboardWidget(widget_id="w1", type="gauge", title="CPU", data_source="metric:cpu"),
        ],
    )
    mgr.register(dash)

    mgr.set_metric_value("cpu", 42.5)
    data = mgr.resolve_widget("w1")
    assert data is not None
    assert data["value"] == 42.5
    assert data["widget_id"] == "w1"
