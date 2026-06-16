# engines/ui_backend/models/parsers/ui_parser.py
from __future__ import annotations

from ..ui_backend_models import UIAction


def parse_ui_action(data: dict) -> UIAction:
    return UIAction(
        action=data.get("action", ""),
        payload=data.get("payload", {}),
    )
