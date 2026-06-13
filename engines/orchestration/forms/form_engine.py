"""Forms engine for orchestration runtime.

Supports form definitions, form field types, validation, default values,
and form rendering per Camunda/Flowable/RuoyiOffice patterns.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ..._types import Metadata, RawData

logger = logging.getLogger(__name__)


class FormFieldType(str, Enum):
    STRING = "string"
    LONG = "long"
    BOOLEAN = "boolean"
    DATE = "date"
    ENUM = "enum"
    TEXT = "text"
    NUMBER = "number"
    DROPDOWN = "dropdown"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    UPLOAD = "upload"
    USER_SELECT = "userSelect"
    GROUP_SELECT = "groupSelect"
    EXPRESSION = "expression"


class FormFieldValidation(str, Enum):
    REQUIRED = "required"
    MIN_LENGTH = "minLength"
    MAX_LENGTH = "maxLength"
    PATTERN = "pattern"
    MIN = "min"
    MAX = "max"
    EMAIL = "email"
    URL = "url"
    CUSTOM = "custom"


@dataclass
class FormFieldOption:
    id: str
    name: str


@dataclass
class FormFieldValidationRule:
    type: str
    value: Any
    error_message: str = ""


@dataclass
class FormField:
    id: str
    label: str = ""
    field_type: str = FormFieldType.STRING
    default_value: Any = None
    placeholder: str = ""
    tooltip: str = ""
    required: bool = False
    read_only: bool = False
    hidden: bool = False
    options: list[FormFieldOption] = field(default_factory=list)
    validations: list[FormFieldValidationRule] = field(default_factory=list)
    properties: Metadata = field(default_factory=dict)
    value_expression: str | None = None
    condition: str | None = None

    def validate(self, value: Any) -> list[str]:
        errors = []
        if self.required and (value is None or value == ""):
            errors.append(f"Field '{self.id}' ({self.label or self.id}) is required")
        for rule in self.validations:
            if rule.type == FormFieldValidation.MIN_LENGTH and isinstance(value, str):
                min_len = int(rule.value) if rule.value else 0
                if len(value) < min_len:
                    errors.append(rule.error_message or f"Minimum length is {min_len}")
            elif rule.type == FormFieldValidation.MAX_LENGTH and isinstance(value, str):
                max_len = int(rule.value) if rule.value else 0
                if len(value) > max_len:
                    errors.append(rule.error_message or f"Maximum length is {max_len}")
            elif rule.type == FormFieldValidation.PATTERN and isinstance(value, str):
                pattern = str(rule.value)
                if not re.match(pattern, value):
                    errors.append(rule.error_message or "Value does not match pattern")
            elif rule.type == FormFieldValidation.EMAIL and isinstance(value, str):
                if value and not re.match(r'^[^@]+@[^@]+\.[^@]+$', value):
                    errors.append(rule.error_message or "Invalid email address")
            elif rule.type == FormFieldValidation.MIN and value is not None:
                try:
                    if float(value) < float(rule.value):
                        errors.append(rule.error_message or f"Minimum value is {rule.value}")
                except (ValueError, TypeError):
                    pass
            elif rule.type == FormFieldValidation.MAX and value is not None:
                try:
                    if float(value) > float(rule.value):
                        errors.append(rule.error_message or f"Maximum value is {rule.value}")
                except (ValueError, TypeError):
                    pass
        return errors


@dataclass
class FormDefinition:
    id: str
    name: str | None = None
    description: str | None = None
    version: int = 1
    fields: list[FormField] = field(default_factory=list)
    key: str | None = None
    properties: Metadata = field(default_factory=dict)

    def get_field(self, field_id: str) -> FormField | None:
        for f in self.fields:
            if f.id == field_id:
                return f
        return None

    def validate(self, data: Metadata) -> dict[str, list[str]]:
        errors: dict[str, list[str]] = {}
        for field_def in self.fields:
            if field_def.hidden:
                continue
            if field_def.condition:
                if not self._evaluate_condition(field_def.condition, data):
                    continue
            value = data.get(field_def.id)
            field_errors = field_def.validate(value)
            if field_errors:
                errors[field_def.id] = field_errors
        return errors

    def _evaluate_condition(self, condition: str, data: Metadata) -> bool:
        if not condition:
            return True
        try:
            from ..expression.evaluator import EvaluationContext
            from ..expression.python_evaluator import PythonEvaluator
            return bool(PythonEvaluator().evaluate(condition, EvaluationContext(variables=data)))
        except Exception:
            return True

    def apply_defaults(self) -> Metadata:
        result = {}
        for field_def in self.fields:
            if field_def.default_value is not None:
                result[field_def.id] = field_def.default_value
        return result

    def to_dict(self) -> Metadata:
        return {
            "id": self.id,
            "key": self.key or self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "fields": [
                {
                    "id": f.id,
                    "label": f.label,
                    "type": f.field_type,
                    "defaultValue": f.default_value,
                    "required": f.required,
                    "readOnly": f.read_only,
                    "hidden": f.hidden,
                    "placeholder": f.placeholder,
                    "options": [{"id": o.id, "name": o.name} for o in f.options],
                    "validations": [{"type": v.type, "value": v.value} for v in f.validations],
                }
                for f in self.fields
            ],
        }

    @classmethod
    def from_dict(cls, data: RawData) -> FormDefinition:
        fields = []
        for f_data in data.get("fields", []):
            options = [FormFieldOption(id=o["id"], name=o["name"]) for o in f_data.get("options", [])]
            validations = [FormFieldValidationRule(type=v["type"], value=v.get("value")) for v in f_data.get("validations", [])]
            fields.append(FormField(
                id=f_data["id"],
                label=f_data.get("label", ""),
                field_type=f_data.get("type", FormFieldType.STRING),
                default_value=f_data.get("defaultValue"),
                required=f_data.get("required", False),
                read_only=f_data.get("readOnly", False),
                hidden=f_data.get("hidden", False),
                placeholder=f_data.get("placeholder", ""),
                options=options,
                validations=validations,
            ))
        return cls(
            id=data["id"],
            name=data.get("name"),
            key=data.get("key"),
            version=data.get("version", 1),
            fields=fields,
        )


class FormEngine:
    def __init__(self) -> None:
        self._forms: dict[str, FormDefinition] = {}

    def register_form(self, form: FormDefinition) -> None:
        key = form.key or form.id
        self._forms[key] = form
        logger.info("Form registered: %s (%s)", key, form.name)

    def get_form(self, form_key: str) -> FormDefinition | None:
        return self._forms.get(form_key)

    def list_forms(self) -> list[FormDefinition]:
        return list(self._forms.values())

    def submit_form(
        self,
        form_key: str,
        data: Metadata,
        instance_id: str | None = None,
    ) -> Metadata:
        form = self._forms.get(form_key)
        if form is None:
            return {"success": False, "errors": {"_form": [f"Form not found: {form_key}"]}}

        errors = form.validate(data)
        if errors:
            return {"success": False, "errors": errors, "form_key": form_key}

        result = {"success": True, "form_key": form_key, "data": dict(data)}
        if instance_id:
            result["instance_id"] = instance_id
        return result

    def render_form(self, form_key: str, default_data: Metadata | None = None) -> Metadata:
        form = self._forms.get(form_key)
        if form is None:
            return {"error": f"Form not found: {form_key}"}
        data = form.apply_defaults()
        if default_data:
            data.update(default_data)
        return {
            "form": form.to_dict(),
            "data": data,
        }

    def remove_form(self, form_key: str) -> bool:
        return self._forms.pop(form_key, None) is not None

    def get_statistics(self) -> dict[str, int]:
        return {"total_forms": len(self._forms)}
