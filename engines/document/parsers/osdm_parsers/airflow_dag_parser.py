# engines/document/parsers/osdm_parsers/airflow_dag_parser.py
"""
Airflow DAG Parser – converts an Airflow Python DAG file into a
StateMachineDocument (unified OSDM model).
- Schedule → TimerEventDefinition on StateMachineModel
- Tasks → Script in state.do_actions (raw assignment + callable body)
- Dependencies → StateTransition
"""

from __future__ import annotations
import ast
import re
from pathlib import Path
from typing import Optional, Dict, Any, List

from .base_osdm_parser import BaseOSDMParser
from ..base import ParseOptions
from ...models.osdm_models import (
    BaseOSDMDocument,
    StateMachineDocument,
    StateMachineModel,
    StateMachineRegion,
    State,
    StateTransition,
    Script,
    ScriptLanguage,
    TimerEventDefinition,
    TimerEventType,
    FormalExpression,
)
from ...models.base import BaseDocument


class AirflowDAGParser(BaseOSDMParser):
    """Parser for Apache Airflow DAG files (.py)."""

    name = "airflow_dag"
    supported_extensions = (".py",)

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> BaseOSDMDocument:
        source = data.decode(options.encoding or "utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax: {e}")

        dag_infos = self._find_dag_definitions(tree)
        if not dag_infos:
            return StateMachineDocument()

        doc = StateMachineDocument()
        for dag_info in dag_infos:
            sm = self._build_state_machine(dag_info, tree)
            doc.state_machines.append(sm)
        return doc

    # ── DAG detection and info extraction (unchanged) ──────────────
    def _find_dag_definitions(self, tree: ast.AST) -> List[dict]:
        dag_infos = []
        for node in ast.walk(tree):
            if isinstance(node, ast.With) and self._is_dag_context(node):
                dag_info = self._extract_dag_info_from_with(node)
                if dag_info:
                    dag_infos.append(dag_info)
            elif isinstance(node, ast.Assign):
                if isinstance(node.value, ast.Call) and self._is_dag_call(node.value):
                    dag_info = self._extract_dag_info_from_assign(node)
                    if dag_info:
                        dag_infos.append(dag_info)
        if not dag_infos:
            dag_info = self._infer_dag_from_file(tree)
            if dag_info:
                dag_infos.append(dag_info)
        return dag_infos

    def _is_dag_context(self, node: ast.With) -> bool:
        if len(node.items) != 1:
            return False
        ctx = node.items[0]
        if ctx.context_expr and isinstance(ctx.context_expr, ast.Call):
            return self._is_dag_call(ctx.context_expr)
        return False

    def _is_dag_call(self, call: ast.Call) -> bool:
        if isinstance(call.func, ast.Name) and call.func.id == "DAG":
            return True
        if isinstance(call.func, ast.Attribute) and call.func.attr == "DAG":
            return True
        return False

    def _extract_dag_info_from_with(self, node: ast.With) -> Optional[dict]:
        call = node.items[0].context_expr
        dag_id = self._get_call_kwarg(call, "dag_id")
        schedule = self._get_call_kwarg(call, "schedule_interval")
        start_date = self._get_call_kwarg(call, "start_date")
        tasks, deps = [], []
        self._collect_tasks_and_deps(node.body, tasks, deps)
        return {
            "dag_id": dag_id,
            "schedule": schedule,
            "start_date": start_date,
            "tasks": tasks,
            "deps": deps,
        }

    def _extract_dag_info_from_assign(self, node: ast.Assign) -> Optional[dict]:
        call = node.value
        dag_id = self._get_call_kwarg(call, "dag_id")
        schedule = self._get_call_kwarg(call, "schedule_interval")
        start_date = self._get_call_kwarg(call, "start_date")
        return {
            "dag_id": dag_id,
            "schedule": schedule,
            "start_date": start_date,
            "tasks": [],
            "deps": [],
        }

    def _infer_dag_from_file(self, tree: ast.AST) -> Optional[dict]:
        tasks, deps = [], []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and self._is_task_assign(node):
                tasks.append(node)
            elif self._is_dependency_expr(node):
                deps.append(node)
        if tasks or deps:
            return {"dag_id": "inferred_dag", "schedule": None, "start_date": None, "tasks": tasks, "deps": deps}
        return None

    def _collect_tasks_and_deps(self, body, tasks, deps) -> None:
        for stmt in body:
            if isinstance(stmt, ast.Assign) and self._is_task_assign(stmt):
                tasks.append(stmt)
            elif self._is_dependency_expr(stmt):
                deps.append(stmt)
            elif isinstance(stmt, (ast.For, ast.While)):
                self._handle_dynamic_tasks(stmt, tasks)

    def _is_task_assign(self, node: ast.Assign) -> bool:
        if not isinstance(node.value, ast.Call):
            return False
        func = node.value.func
        operator_names = {"PythonOperator", "BashOperator", "DummyOperator", "BranchPythonOperator",
                          "ShortCircuitOperator", "PythonVirtualenvOperator", "ExternalPythonOperator"}
        if isinstance(func, ast.Name) and func.id in operator_names:
            return True
        if isinstance(func, ast.Attribute) and func.attr in operator_names:
            return True
        return False

    def _is_dependency_expr(self, node) -> bool:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.BinOp):
            return isinstance(node.value.op, (ast.RShift, ast.LShift))
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            if isinstance(call.func, ast.Attribute) and call.func.attr in ("set_downstream", "set_upstream"):
                return True
        return False

    def _handle_dynamic_tasks(self, loop_node, tasks: List) -> None:
        for inner in ast.iter_child_nodes(loop_node):
            if isinstance(inner, ast.Assign) and self._is_task_assign(inner):
                tasks.append(inner)

    def _get_call_kwarg(self, call: ast.Call, arg_name: str) -> Optional[str]:
        for kw in call.keywords:
            if kw.arg == arg_name:
                return ast.unparse(kw.value) if kw.value else None
        return None

    # ── Schedule → TimerEventDefinition (rich parsing) ────────────
    def _parse_schedule(self, schedule: Optional[str]) -> Optional[TimerEventDefinition]:
        if not schedule:
            return None
        schedule = schedule.strip("'\"")
        if schedule == "None":
            return None

        # Cron expression detection
        if re.match(r'^\s*(\*|[\d\-,/]+)\s+(\*|[\d\-,/]+)\s+(\*|[\d\-,/]+)\s+(\*|[\d\-,/]+)\s+(\*|[\d\-,/]+)', schedule):
            return TimerEventDefinition(
                timer_type=TimerEventType.CYCLE,
                time_cycle=FormalExpression(body=schedule),
            )
        # timedelta
        match = re.match(
            r'^timedelta\s*\(\s*(?:days\s*=\s*(\d+)\s*,\s*)?(?:hours\s*=\s*(\d+)\s*,\s*)?(?:minutes\s*=\s*(\d+)\s*,\s*)?(?:seconds\s*=\s*(\d+)\s*)?\)$',
            schedule)
        if match:
            days, hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
            total_seconds = days * 86400 + hours * 3600 + minutes * 60 + seconds
            return TimerEventDefinition(
                timer_type=TimerEventType.DURATION,
                time_duration=FormalExpression(body=str(total_seconds)),
            )
        # plain number (seconds)
        if schedule.isdigit():
            return TimerEventDefinition(
                timer_type=TimerEventType.DURATION,
                time_duration=FormalExpression(body=schedule),
            )
        # predefined schedules like '@daily', '@hourly', etc.
        if schedule.startswith('@'):
            return TimerEventDefinition(
                timer_type=TimerEventType.CYCLE,
                time_cycle=FormalExpression(body=schedule),
            )
        # fallback
        return TimerEventDefinition(
            timer_type=TimerEventType.DURATION,
            time_duration=FormalExpression(body=schedule),
        )

    # ── Build StateMachineModel ────────────────────────────────────
    def _build_state_machine(self, dag_info: dict, tree: ast.AST) -> StateMachineModel:
        sm = StateMachineModel(
            id=dag_info.get("dag_id", "airflow_dag"),
            name=dag_info.get("dag_id", "airflow_dag"),
        )
        sm.timer_trigger = self._parse_schedule(dag_info.get("schedule"))
        if dag_info.get("start_date"):
            sm.start_date = dag_info["start_date"].strip("'\"")

        top_region = StateMachineRegion()
        sm.top_region = top_region

        task_map: Dict[str, State] = {}
        for task_assign in dag_info.get("tasks", []):
            state = self._task_to_state(task_assign)
            if state:
                top_region.states.append(state)
                task_name = task_assign.targets[0].id if isinstance(task_assign.targets[0], ast.Name) else "unknown"
                task_map[task_name] = state

        for dep in dag_info.get("deps", []):
            trans = self._dependency_to_transition(dep, task_map)
            if trans:
                top_region.transitions.append(trans)

        if top_region.states:
            top_region.initial_state = top_region.states[0]

        return sm

    def _task_to_state(self, assign: ast.Assign) -> Optional[State]:
        if not isinstance(assign.targets[0], ast.Name):
            return None
        task_id = assign.targets[0].id
        call = assign.value
        task_type = call.func.id if isinstance(call.func, ast.Name) else call.func.attr if isinstance(call.func, ast.Attribute) else "Operator"

        state = State(id=task_id, name=task_id, airflow_operator=task_type)

        # Store the raw assignment as a Script for exact round‑trip
        raw_script = Script(script_body=ast.unparse(assign), script_language=ScriptLanguage.PYTHON)
        state.do_actions.append(raw_script)

        # For PythonOperator, also extract the callable function body if available
        if task_type == "PythonOperator":
            python_callable = self._get_kwarg_string(call, "python_callable")
            if python_callable:
                func_body = self._find_function_body(python_callable, assign)
                if func_body:
                    callable_script = Script(script_body=func_body, script_language=ScriptLanguage.PYTHON)
                    # Keep it separate from the raw assignment; mark it with a special identifier? We'll keep it as a second do_action
                    state.do_actions.append(callable_script)
        return state

    def _dependency_to_transition(self, dep_node, task_map: Dict[str, State]) -> Optional[StateTransition]:
        if isinstance(dep_node, ast.Expr) and isinstance(dep_node.value, ast.BinOp):
            left = dep_node.value.left
            right = dep_node.value.right
            if isinstance(left, ast.Name) and isinstance(right, ast.Name):
                source = task_map.get(left.id)
                target = task_map.get(right.id)
                if source and target:
                    trans_id = f"{left.id}_to_{right.id}"
                    return StateTransition(id=trans_id, source=source, target=target)
        if isinstance(dep_node, ast.Expr) and isinstance(dep_node.value, ast.Call):
            call = dep_node.value
            if isinstance(call.func, ast.Attribute) and call.func.attr == "set_downstream":
                obj = call.func.value
                if isinstance(obj, ast.Name) and obj.id in task_map:
                    source = task_map[obj.id]
                    for arg in call.args:
                        if isinstance(arg, ast.Name) and arg.id in task_map:
                            target = task_map[arg.id]
                            trans_id = f"{source.id}_to_{target.id}"
                            return StateTransition(id=trans_id, source=source, target=target)
        return None

    def _get_kwarg_string(self, call: ast.Call, arg_name: str) -> Optional[str]:
        for kw in call.keywords:
            if kw.arg == arg_name:
                if isinstance(kw.value, ast.Name):
                    return kw.value.id
                elif isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    return kw.value.value
        return None

    def _find_function_body(self, func_name: str, node: ast.AST) -> Optional[str]:
        if not hasattr(self, '_source_tree'):
            return None
        for n in ast.walk(self._source_tree):
            if isinstance(n, ast.FunctionDef) and n.name == func_name:
                return ast.unparse(n)
        return None

    async def parse_bytes(self, data: bytes, document_id: str, source_name: str,
                          metadata: Optional[Dict[str, Any]] = None,
                          options: Optional[ParseOptions] = None) -> BaseDocument:
        source = data.decode(options.encoding or "utf-8") if options else data.decode("utf-8")
        try:
            self._source_tree = ast.parse(source)
        except SyntaxError:
            self._source_tree = None
        return await super().parse_bytes(data, document_id, source_name, metadata, options)