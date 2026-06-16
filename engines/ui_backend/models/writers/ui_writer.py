# engines/ui_backend/models/writers/ui_writer.py
from __future__ import annotations

from ..ui_backend_models import UIComponent


def write_ui_component(component: UIComponent) -> dict:
    return {"name": component.name, "props": component.props}
