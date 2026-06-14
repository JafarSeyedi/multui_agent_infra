from __future__ import annotations

from datetime import datetime
from typing import Any

from ..models.bam_models import Dashboard


class DashboardManager:
    def __init__(self) -> None:
        self._dashboards: dict[str, Dashboard] = {}
        self._metric_values: dict[str, float] = {}

    def register(self, dashboard: Dashboard) -> None:
        self._dashboards[dashboard.dashboard_id] = dashboard

    def unregister(self, dashboard_id: str) -> None:
        self._dashboards.pop(dashboard_id, None)

    def get(self, dashboard_id: str) -> Dashboard | None:
        return self._dashboards.get(dashboard_id)

    def list_all(self) -> list[Dashboard]:
        return list(self._dashboards.values())

    def set_metric_value(self, metric_id: str, value: float) -> None:
        self._metric_values[metric_id] = value

    def resolve_widget(self, widget_id: str) -> dict[str, Any] | None:
        for dash in self._dashboards.values():
            for widget in dash.widgets:
                if widget.widget_id == widget_id:
                    data_source = widget.data_source
                    value = None
                    if data_source.startswith("metric:"):
                        metric_id = data_source.split(":", 1)[1]
                        value = self._metric_values.get(metric_id)
                    return {
                        "widget_id": widget.widget_id,
                        "type": widget.type,
                        "title": widget.title,
                        "value": value,
                        "data_source": data_source,
                    }
        return None

    def resolve_dashboard(self, dashboard_id: str) -> dict[str, Any] | None:
        dash = self._dashboards.get(dashboard_id)
        if dash is None:
            return None
        return {
            "dashboard_id": dash.dashboard_id,
            "name": dash.name,
            "widgets": [
                self.resolve_widget(w.widget_id) for w in dash.widgets
            ],
        }
