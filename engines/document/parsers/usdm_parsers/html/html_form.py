# mypy: disable-error-code="attr-defined"

from __future__ import annotations

from typing import Any

from ....models.base import ElementType
from ....models.usdm_models import FormFieldContent
from .html_parser_constants import FORM_INPUT_TYPES
from .html_parser_utils import safe_int


class HTMLFormParser:
    """Mixin providing HTML form element parsing methods."""

    form_field_stack: list[dict[str, Any]]
    current_text: list[str]
    current_select: dict[str, Any] | None
    current_details: dict[str, Any] | None
    current_dialog: dict[str, Any] | None
    current_spans: list[Any]
    in_dialog: bool

    def _handle_form_start(self, attrs: dict[str, str]) -> None:
        self.form_field_stack.append({
            "action": attrs.get("action", ""),
            "method": attrs.get("method", "get"),
            "enctype": attrs.get("enctype", ""),
            "fields": [],
        })

    def _handle_form_end(self) -> None:
        if self.form_field_stack:
            self.form_field_stack.pop()

    def _handle_input(self, attrs: dict[str, str]) -> None:
        input_type = attrs.get("type", "text")
        if input_type not in FORM_INPUT_TYPES:
            input_type = "text"
        field = FormFieldContent(
            field_name=attrs.get("name", ""),
            field_type=input_type,
            value=attrs.get("value", ""),
            default_value=attrs.get("value", ""),
            placeholder=attrs.get("placeholder", ""),
            required=attrs.get("required") is not None,
            read_only=attrs.get("readonly") is not None,
            max_length=safe_int(attrs.get("maxlength")) if attrs.get("maxlength") else None,
            tooltip=attrs.get("title", ""),
        )
        element = self._create_logical_element(ElementType.FORM_FIELD, field, attrs)
        self._add_element(element)

    def _handle_textarea_start(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("in_textarea", True)
        self.current_text = []
        self.form_field_stack.append({
            "field_name": attrs.get("name", ""),
            "placeholder": attrs.get("placeholder"),
            "required": attrs.get("required") is not None,
            "read_only": attrs.get("readonly") is not None,
        })

    def _handle_textarea_end(self) -> None:
        text_value = "".join(self.current_text)
        self.current_text = []
        self._pop_style_attr("in_textarea")
        if self.form_field_stack:
            info = self.form_field_stack.pop()
            field = FormFieldContent(
                field_name=info.get("field_name", ""),
                field_type="textarea",
                value=text_value,
                placeholder=info.get("placeholder", ""),
                required=info.get("required", False),
                read_only=info.get("read_only", False),
            )
            element = self._create_logical_element(ElementType.FORM_FIELD, field)
            self._add_element(element)

    def _handle_select_start(self, attrs: dict[str, str]) -> None:
        self.current_select = {
            "field_name": attrs.get("name", ""),
            "multiple": attrs.get("multiple") is not None,
            "required": attrs.get("required") is not None,
            "options": [],
            "current_optgroup": None,
        }

    def _handle_select_end(self) -> None:
        if self.current_select:
            field = FormFieldContent(
                field_name=self.current_select["field_name"],
                field_type="select",
                options=[opt["value"] for opt in self.current_select["options"]],
                required=self.current_select["required"],
            )
            element = self._create_logical_element(ElementType.FORM_FIELD, field)
            self._add_element(element)
            self.current_select = None

    def _handle_optgroup_start(self, attrs: dict[str, str]) -> None:
        if self.current_select:
            self.current_select["current_optgroup"] = attrs.get("label", "")

    def _handle_optgroup_end(self) -> None:
        if self.current_select:
            self.current_select["current_optgroup"] = None

    def _handle_option_start(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("in_option", True)
        self.current_text = []
        if self.current_select:
            self.current_select["_current_option"] = {
                "value": attrs.get("value", ""),
                "selected": attrs.get("selected") is not None,
            }

    def _handle_option_end(self) -> None:
        option_text = "".join(self.current_text)
        self.current_text = []
        self._pop_style_attr("in_option")
        if self.current_select and self.current_select.get("_current_option"):
            opt = self.current_select["_current_option"]
            opt["value"] = opt["value"] or option_text
            self.current_select["options"].append(opt)
            self.current_select["_current_option"] = None

    def _handle_button_start(self, attrs: dict[str, str]) -> None:
        pass

    def _handle_button_end(self) -> None:
        self._flush_current_text()
        if self.current_spans:
            btn_text = "".join(s.text for s in self.current_spans)
            self.current_spans = []
            field = FormFieldContent(
                field_name="",
                field_type="button",
                value=btn_text,
            )
            element = self._create_logical_element(ElementType.FORM_FIELD, field)
            self._add_element(element)

    def _handle_fieldset_start(self, attrs: dict[str, str]) -> None:
        pass

    def _handle_fieldset_end(self) -> None:
        pass

    def _handle_progress(self, attrs: dict[str, str]) -> None:
        field = FormFieldContent(
            field_name="",
            field_type="progress",
            value=attrs.get("value", ""),
        )
        element = self._create_logical_element(ElementType.FORM_FIELD, field, attrs)
        self._add_element(element)

    def _handle_meter(self, attrs: dict[str, str]) -> None:
        field = FormFieldContent(
            field_name="",
            field_type="meter",
            value=attrs.get("value", ""),
        )
        element = self._create_logical_element(ElementType.FORM_FIELD, field, attrs)
        self._add_element(element)

    def _handle_details_start(self, attrs: dict[str, str]) -> None:
        self.current_details = {
            "open": attrs.get("open") is not None,
            "summary": None,
            "elements": [],
        }

    def _handle_details_end(self) -> None:
        self.current_details = None

    def _handle_dialog_start(self, attrs: dict[str, str]) -> None:
        self.in_dialog = True
        self.current_dialog = {
            "open": attrs.get("open") is not None,
            "elements": [],
        }

    def _handle_dialog_end(self) -> None:
        self.in_dialog = False
        self.current_dialog = None
