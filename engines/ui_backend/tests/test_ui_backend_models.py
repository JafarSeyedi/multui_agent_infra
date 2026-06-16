# engines/ui_backend/tests/test_ui_backend_models.py
from engines.ui_backend.models.ui_backend_models import UIComponent, UIAction, Session
from engines.ui_backend.models.parsers.ui_parser import parse_ui_action
from engines.ui_backend.models.writers.ui_writer import write_ui_component


def test_ui_component():
    comp = UIComponent(name="Dialog", props={"title": "Confirm"})
    assert comp.name == "Dialog"


def test_ui_component_write():
    comp = UIComponent(name="Button", props={"label": "Submit"})
    data = write_ui_component(comp)
    assert data["name"] == "Button"


def test_ui_action_parse():
    data = {"action": "submit", "payload": {"form": "login"}}
    action = parse_ui_action(data)
    assert action.action == "submit"


def test_session():
    s = Session(session_id="s1", user_id="alice")
    assert s.user_id == "alice"
