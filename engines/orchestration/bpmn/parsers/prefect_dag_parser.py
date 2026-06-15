# engines/document/parsers/osdm_parsers/prefect_dag_parser.py
"""
Prefect DAG Parser – converts a Prefect Python flow file (.py) into a
StateMachineDocument (unified OSDM model).

All meaningful data is stored in typed fields:
- @flow → StateMachineModel
- @task → State with Script in do_actions (the full task definition)
- Task dependencies (calls between tasks) → StateTransition
- Scheduling (if found) → TimerEventDefinition on StateMachineModel
"""
from __future__ import annotations

import ast
import uuid
from pathlib import Path
from typing import Any

from engines.document.models.media_types import MEDIA_TYPES
from ..models.bpmn_models import Script, ScriptLanguage
from ...models.shared_models import BaseOSDMDocument
from ...state_machine.models.state_machine_models import (
    State, StateMachineDocument,
    StateMachineModel, StateMachineRegion, StateTransition
)
from engines.document.parsers.base import ParseOptions
from ...models.base_osdm_parser import BaseOSDMParser


class PrefectDAGParser(BaseOSDMParser):
    """Parser for Prefect DAG files (.py)."""

    name = "prefect_dag"
    supported_extensions = (".py",)

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> BaseOSDMDocument:
        source = data.decode(options.encoding or "utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax: {e}")

        doc = StateMachineDocument(
            document_id=Path(source_name).stem,
            title=Path(source_name).stem,
            media_type=MEDIA_TYPES.get("prefect_dag_py", MEDIA_TYPES["txt"])
        )
        doc.source_file = source_name

        # Find all @flow decorated functions
        flows = self._find_flows(tree)
        if not flows:
            # If no @flow, treat the whole file as a flow with inferred tasks
            sm = self._build_state_machine_from_tasks(tree, source_name)
            doc.state_machines.append(sm)
        else:
            for flow_def in flows:
                sm = self._build_state_machine(flow_def, tree)
                doc.state_machines.append(sm)

        return doc

    # ── Find @flow functions ─────────────────────────────────────
    def _find_flows(self, tree: ast.AST) -> list[ast.FunctionDef]:
        flows = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if self._is_decorator_name(decorator, "flow"):
                        flows.append(node)
                        break
        return flows

    def _is_decorator_name(self, node: ast.AST, name: str) -> bool:
        if isinstance(node, ast.Name) and node.id == name:
            return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == name:
            return True
        if isinstance(node, ast.Attribute) and node.attr == name:
            return True
        return False

    # ── Build StateMachine from a single @flow ───────────────────
    def _build_state_machine(self, flow_def: ast.FunctionDef, tree: ast.AST) -> StateMachineModel:
        sm = StateMachineModel(
            id=flow_def.name,
            name=flow_def.name,
        )
        top_region = StateMachineRegion(id=str(uuid.uuid4().hex))
        sm.top_region = top_region

        # Extract tasks defined inside the flow body, and also global tasks that are called by the flow.
        task_defs = self._find_tasks(tree)
        flow_body = flow_def.body

        # Resolve which tasks are called in the flow and in what order (dependencies).
        called_tasks = self._find_called_tasks_in_body(flow_body, task_defs)

        task_map: dict[str, State] = {}
        for task_name, task_func in called_tasks.items():
            state = self._task_to_state(task_func)
            top_region.states.append(state)
            task_map[task_name] = state

        # Determine dependencies by analyzing call order in the flow body.
        last_called: str | None = None
        for stmt in flow_body:
            for node in ast.walk(stmt):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    called_name = node.func.id
                    if called_name in task_map:
                        if last_called and last_called != called_name:
                            trans = StateTransition(
                                id=f"{last_called}_to_{called_name}",
                                source=task_map[last_called],
                                target=task_map[called_name],
                            )
                            top_region.transitions.append(trans)
                        last_called = called_name

        # Set initial state to first called task
        if top_region.states:
            top_region.initial_state = top_region.states[0]

        return sm

    # ── Fallback: build from tasks only (no @flow) ───────────────
    def _build_state_machine_from_tasks(self, tree: ast.AST, source_name: str) -> StateMachineModel:
        sm = StateMachineModel(
            id=Path(source_name).stem,
            name=Path(source_name).stem,
        )
        top_region = StateMachineRegion(id=str(uuid.uuid4().hex))
        sm.top_region = top_region

        task_defs = self._find_tasks(tree)
        task_map: dict[str, State] = {}
        for task_func in task_defs.values():
            state = self._task_to_state(task_func)
            top_region.states.append(state)
            task_map[task_func.name] = state

        if top_region.states:
            top_region.initial_state = top_region.states[0]

        return sm

    # ── Find @task functions globally ────────────────────────────
    def _find_tasks(self, tree: ast.AST) -> dict[str, ast.FunctionDef]:
        tasks = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if self._is_decorator_name(decorator, "task"):
                        tasks[node.name] = node
                        break
        return tasks

    # ── Find which tasks are called inside a flow body ──────────
    def _find_called_tasks_in_body(self, body: list[ast.stmt],
                                   task_defs: dict[str, ast.FunctionDef]) -> dict[str, ast.FunctionDef]:
        called = {}
        for stmt in body:
            for node in ast.walk(stmt):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    task_name = node.func.id
                    if task_name in task_defs:
                        called[task_name] = task_defs[task_name]
        return called

    # ── Convert a task function to State ─────────────────────────
    def _task_to_state(self, func_def: ast.FunctionDef) -> State:
        task_id = func_def.name
        state = State(id=task_id, name=task_id)
        # Store the entire function body as a Script
        script_body = ast.unparse(func_def)
        state.do_actions.append(Script(
            id=str(uuid.uuid4().hex),
            script_body=script_body,
            script_language=ScriptLanguage.PYTHON
        ))
        return state