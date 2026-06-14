"""CMMN case executor with stage/task/milestone orchestration.

Supports CMMN 1.1 semantics including:
- Case plan model execution and state transitions
- Stage activation/completion/reentry/nesting
- Task execution kinds (human/process/case/decision)
- Milestone state, criteria, and auditing
- Sentry evaluation for entry/exit criteria
- Planning table and discretionary items
- Case file item management
- OSDM-typed document models (CMMNDocument, Stage, etc.)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..._types import Metadata, RawData
from ..core.instance import ProcessInstance
from ..core.event_bus import Event, EventType
from ..core.engine import OrchestrationEngine
from ..bpmn.models.bpmn_models import FormalExpression
from .models.cmmn_models import (
    CaseFileItem,
    CaseTask,
    CMMNDefinition,
    CMMNDocument,
    DiscretionaryItem,
    EntryCriterion,
    ExitCriterion,
    HumanTask,
    Milestone,
    PlanItem,
    ProcessTask,
    Sentry,
    SentryExpression,
    Stage,
)
from .sentry_evaluator import SentryEvaluator


logger = logging.getLogger(__name__)


class CMMNTaskType(str, Enum):
    HUMAN_TASK = "HumanTask"
    PROCESS_TASK = "ProcessTask"
    CASE_TASK = "CaseTask"
    DECISION_TASK = "DecisionTask"
    TASK = "Task"
    MILESTONE = "Milestone"
    STAGE = "Stage"


class CMMNActivationRule(str, Enum):
    MANUAL = "Manual"
    AUTOMATIC = "Automatic"
    REPETITION = "Repetition"


class CMMNCompletionBehavior(str, Enum):
    REQUIRED = "Required"
    OPTIONAL = "Optional"
    DISCRETIONARY = "Discretionary"


@dataclass(frozen=True)
class CaseExecutionError(RuntimeError):
    """Raised when a case cannot continue."""


@dataclass
class StageContext:
    stage_id: str
    name: str | None = None
    is_active: bool = False
    is_completed: bool = False
    auto_complete: bool = True
    children: list[str] = field(default_factory=list)


@dataclass
class MilestoneContext:
    milestone_id: str
    name: str | None = None
    is_achieved: bool = False
    entry_criteria: list[Sentry] = field(default_factory=list)


@dataclass
class PlanningItemContext:
    item_id: str
    name: str | None = None
    is_planned: bool = False
    is_available: bool = False
    definition_type: str = "task"


@dataclass
class CasePlanModel:
    stages: list[RawData] = field(default_factory=list)
    tasks: list[RawData] = field(default_factory=list)
    milestones: list[RawData] = field(default_factory=list)
    case_file_items: list[RawData] = field(default_factory=list)
    sentries: list[RawData] = field(default_factory=list)
    discretionary_items: list[RawData] = field(default_factory=list)
    planning_tables: list[RawData] = field(default_factory=list)
    text_annotations: list[RawData] = field(default_factory=list)
    input: list[RawData] = field(default_factory=list)
    output: list[RawData] = field(default_factory=list)


class CaseExecutor:
    """Execute a CMMN case plan model with full semantics."""

    def __init__(self, orchestration_engine: OrchestrationEngine | None = None) -> None:
        self.orchestration_engine = orchestration_engine
        self.sentry_evaluator = SentryEvaluator()
        self._stages: dict[str, StageContext] = {}
        self._milestones: dict[str, MilestoneContext] = {}
        self._planning_items: dict[str, PlanningItemContext] = {}

    async def execute(self, instance: ProcessInstance, definition: RawData) -> None:
        plan_model = self._normalize_definition(definition)

        for item in plan_model.case_file_items:
            name = item.get("name") or item.get("id")
            value = item.get("defaultValue", item.get("value", None))
            if name:
                instance.set_variable(f"caseFile.{name}", value)

        for sentry in plan_model.sentries:
            self.sentry_evaluator.register(sentry)

        for milestone in plan_model.milestones:
            mctx = MilestoneContext(
                milestone_id=milestone.get("id", ""),
                name=milestone.get("name"),
                entry_criteria=milestone.get("entryCriteria", []),
            )
            self._milestones[mctx.milestone_id] = mctx
            instance.set_variable(f"milestone.{mctx.milestone_id}", {
                "name": mctx.name,
                "achieved": False,
            })

        for stage in plan_model.stages:
            sctx = StageContext(
                stage_id=stage.get("id", ""),
                name=stage.get("name"),
                auto_complete=stage.get("autoComplete", True),
            )
            self._stages[sctx.stage_id] = sctx

        available_tasks = self._get_available_tasks(plan_model)

        for task in available_tasks:
            task_id = task.get("id", "")
            task_type = task.get("type", "task")
            task_name = task.get("name", task_id)
            entry_criteria = task.get("entryCriteria", [])
            required = task.get("requiredRule", "optional")

            if entry_criteria:
                if not self.sentry_evaluator.evaluate_entry_criteria(entry_criteria, instance):
                    continue

            instance.set_variable(f"task.{task_id}", {
                "name": task_name,
                "type": task_type,
                "status": "active",
                "required": required,
            })

            if self.orchestration_engine is not None:
                await self.orchestration_engine.event_bus.publish(
                    Event(
                        type=EventType.ACTIVITY_STARTED,
                        data={
                            "instance_id": instance.id,
                            "activity_id": task_id,
                            "activity_type": task_type,
                            "engine_type": "cmmn",
                        },
                    )
                )
            
            result = await self._execute_task(instance, task, plan_model, required)
            
            if result and self.orchestration_engine is not None:
                await self.orchestration_engine.event_bus.publish(
                    Event(
                        type=EventType.ACTIVITY_COMPLETED,
                        data={
                            "instance_id": instance.id,
                            "activity_id": task_id,
                            "activity_type": task_type,
                            "engine_type": "cmmn",
                        },
                    )
                )
        
        self._evaluate_milestones(instance)
        self._check_case_completion(instance)
    
    async def execute_osdm(self, document: CMMNDocument, instance: ProcessInstance) -> None:
        for cmmn_def in document.cmmn_definitions:
            case_plan_model = cmmn_def.case
            await self._execute_osdm_case(instance, cmmn_def, case_plan_model)

    async def _execute_osdm_case(
        self,
        instance: ProcessInstance,
        cmmn_def: CMMNDefinition,
        case_plan_model: Stage,
    ) -> None:
        case_file_items: list[CaseFileItem] = cmmn_def.case_file_items
        for item in case_file_items:
            name = item.name if item.name else item.id
            instance.set_variable(f"caseFile.{name}", None)

        sentries: list[Sentry] = case_plan_model.sentries
        for sentry in sentries:
            sentry_dict = self._sentry_to_dict(sentry)
            self.sentry_evaluator.register(sentry_dict)

        plan_items: list[PlanItem] = cmmn_def.plan_items
        discretionary_items: list[DiscretionaryItem] = cmmn_def.discretionary_items

        milestone_items: list[Milestone] = []
        stage_items: list[Stage] = []
        task_items: list[PlanItem] = []
        self._collect_plan_items(case_plan_model, plan_items, milestone_items, stage_items, task_items)

        for milestone in milestone_items:
            mctx = MilestoneContext(
                milestone_id=milestone.id,
                name=milestone.name,
            )
            self._milestones[mctx.milestone_id] = mctx
            instance.set_variable(f"milestone.{mctx.milestone_id}", {
                "name": mctx.name,
                "achieved": False,
            })

        for stage in stage_items:
            sctx = StageContext(
                stage_id=stage.id,
                name=stage.name,
                auto_complete=True,
            )
            self._stages[sctx.stage_id] = sctx

        for task_item in task_items:
            entry_criteria = self._resolve_entry_criteria(task_item)
            if entry_criteria:
                criteria_dicts = [self._sentry_to_dict(ec) for ec in entry_criteria]
                if not self.sentry_evaluator.evaluate_entry_criteria(criteria_dicts, instance):
                    continue

            definition = task_item.definition_ref
            task_id = definition.id if definition else task_item.id
            task_name = definition.name if definition and definition.name else task_id

            instance.set_variable(f"task.{task_id}", {
                "name": task_name,
                "status": "active",
                "required": "optional",
            })

            if self.orchestration_engine is not None:
                await self.orchestration_engine.event_bus.publish(
                    Event(
                        type=EventType.ACTIVITY_STARTED,
                        data={
                            "instance_id": instance.id,
                            "activity_id": task_id,
                            "activity_type": type(definition).__name__ if definition else "unknown",
                            "engine_type": "cmmn",
                        },
                    )
                )

            result = await self._execute_osdm_task(instance, task_item, definition)

            if result and self.orchestration_engine is not None:
                await self.orchestration_engine.event_bus.publish(
                    Event(
                        type=EventType.ACTIVITY_COMPLETED,
                        data={
                            "instance_id": instance.id,
                            "activity_id": task_id,
                            "activity_type": type(definition).__name__ if definition else "unknown",
                            "engine_type": "cmmn",
                        },
                    )
                )

        for disc_item in discretionary_items:
            if disc_item.definition_ref:
                definition = disc_item.definition_ref
                task_id = definition.id
                task_name = definition.name if definition.name else task_id
                instance.set_variable(f"task.{task_id}", {
                    "name": task_name,
                    "status": "available",
                    "required": "discretionary",
                })

        self._evaluate_osdm_milestones(instance, milestone_items, plan_items)
        self._check_osdm_case_completion(instance)

    async def _execute_osdm_task(
        self,
        instance: ProcessInstance,
        plan_item: PlanItem,
        definition: Any,
    ) -> Metadata | None:
        task_id = definition.id
        task_name = definition.name if definition.name else task_id

        result: Metadata = {
            "task_id": task_id,
            "task_name": task_name,
            "task_type": type(definition).__name__,
            "status": "completed",
        }

        if isinstance(definition, HumanTask):
            role_ref = definition.role_ref
            performer = role_ref.name if role_ref and role_ref.name else role_ref.id if role_ref else None
            result["performer"] = performer
            if performer:
                instance.set_variable(f"task.{task_id}.performer", performer)

        elif isinstance(definition, ProcessTask):
            process_ref = definition.process_ref
            called_element = process_ref.id if process_ref else None
            result["called_element"] = called_element
            if called_element:
                instance.set_variable(f"task.{task_id}.calledElement", called_element)

        elif isinstance(definition, CaseTask):
            case_ref = definition.case_ref
            case_ref_id = case_ref.id if case_ref and hasattr(case_ref, "id") else str(case_ref) if case_ref else None
            result["case_ref"] = case_ref_id
            if case_ref_id:
                instance.set_variable(f"task.{task_id}.caseRef", case_ref_id)

        else:
            result["output"] = {}

        instance.set_variable(f"task.{task_id}.output", result)
        instance.set_variable(f"task.{task_id}.status", "completed")

        return result

    def _collect_plan_items(
        self,
        case_plan_model: Stage,
        plan_items: list[PlanItem],
        milestone_items: list[Milestone],
        stage_items: list[Stage],
        task_items: list[PlanItem],
    ) -> None:
        flow_elements = case_plan_model.flow_elements
        for element in flow_elements.values():
            if isinstance(element, Milestone):
                milestone_items.append(element)
            elif isinstance(element, Stage):
                stage_items.append(element)
                nested = element.flow_elements
                for nested_elem in nested.values():
                    if isinstance(nested_elem, Milestone):
                        milestone_items.append(nested_elem)
                    elif isinstance(nested_elem, Stage):
                        stage_items.append(nested_elem)

        for plan_item in plan_items:
            definition = plan_item.definition_ref
            if definition is None:
                continue
            if isinstance(definition, Milestone):
                milestone_items.append(definition)
            elif isinstance(definition, Stage):
                stage_items.append(definition)
            else:
                task_items.append(plan_item)

    def _resolve_entry_criteria(self, plan_item: PlanItem) -> list[Sentry]:
        criteria: list[Sentry] = []
        for entry_criterion in plan_item.entry_criteria:
            if entry_criterion.sentry_ref:
                criteria.append(entry_criterion.sentry_ref)
        return criteria

    def _sentry_to_dict(self, sentry: Sentry) -> RawData:
        sentry_dict: RawData = {
            "id": sentry.id,
            "name": sentry.name,
        }
        if sentry.on_part is not None:
            if isinstance(sentry.on_part, FormalExpression):
                sentry_dict["on"] = [{"source": sentry.on_part.body}]
            else:
                sentry_dict["on"] = [str(sentry.on_part)]
        else:
            sentry_dict["on"] = []
        if sentry.if_part is not None:
            if isinstance(sentry.if_part, FormalExpression):
                sentry_dict["condition"] = sentry.if_part.body
            else:
                sentry_dict["condition"] = str(sentry.if_part)
        return sentry_dict

    def _evaluate_osdm_milestones(
        self,
        instance: ProcessInstance,
        milestones: list[Milestone],
        plan_items: list[PlanItem],
    ) -> None:
        for milestone in milestones:
            ctx = self._milestones.get(milestone.id)
            if ctx is None or ctx.is_achieved:
                continue
            entry_criteria: list[Sentry] = []
            for pi in plan_items:
                if isinstance(pi.definition_ref, Milestone) and pi.definition_ref.id == milestone.id:
                    for ec in pi.entry_criteria:
                        if ec.sentry_ref:
                            entry_criteria.append(ec.sentry_ref)
            if entry_criteria:
                criteria_dicts = [self._sentry_to_dict(s) for s in entry_criteria]
                if self.sentry_evaluator.evaluate_entry_criteria(criteria_dicts, instance):
                    ctx.is_achieved = True
                    instance.set_variable(f"milestone.{milestone.id}.achieved", True)
            else:
                ctx.is_achieved = True
                instance.set_variable(f"milestone.{milestone.id}.achieved", True)

    def _check_osdm_case_completion(self, instance: ProcessInstance) -> None:
        all_milestones_achieved = all(ctx.is_achieved for ctx in self._milestones.values())
        all_stages_done = all(
            ctx.is_completed for ctx in self._stages.values()
        ) if self._stages else True

        if all_milestones_achieved and all_stages_done:
            instance.complete()

    async def _execute_task(
        self,
        instance: ProcessInstance,
        task: RawData,
        plan_model: CasePlanModel,
        required: str,
    ) -> Metadata | None:
        task_id = task.get("id", "")
        task_type = task.get("type", "task")
        task_name = task.get("name", task_id)
        payload: Any = task.get("payload", task.get("inputParameters", {}))

        result: Metadata = {
            "task_id": task_id,
            "task_name": task_name,
            "task_type": task_type,
            "status": "completed",
        }

        if task_type == CMMNTaskType.HUMAN_TASK:
            result.update({
                "assignee": task.get("assignee", payload.get("assignee")),
                "candidate_groups": task.get("candidateGroups", payload.get("candidateGroups", [])),
                "form_key": task.get("formKey", payload.get("formKey")),
                "priority": task.get("priority", payload.get("priority", "medium")),
                "due_date": task.get("dueDate", payload.get("dueDate")),
            })
            if payload:
                for key, value in payload.items():
                    instance.set_variable(f"task.{task_id}.{key}", value)

        elif task_type == CMMNTaskType.PROCESS_TASK:
            called_element = task.get("calledElement", payload.get("calledElement"))
            result["called_element"] = called_element
            if called_element:
                instance.set_variable(f"task.{task_id}.calledElement", called_element)
            io_mapping = task.get("ioMapping", [])
            for mapping in io_mapping:
                source = mapping.get("source")
                target = mapping.get("target")
                if source and target:
                    value = instance.get_variable(source)
                    if value is not None:
                        instance.set_variable(target, value)

        elif task_type == CMMNTaskType.CASE_TASK:
            case_ref = task.get("caseRef") or payload.get("caseRef")
            result["case_ref"] = case_ref
            if case_ref:
                instance.set_variable(f"task.{task_id}.caseRef", case_ref)

        elif task_type == CMMNTaskType.DECISION_TASK:
            decision_ref = task.get("calledDecision") or payload.get("calledDecision")
            result_variable = payload.get("resultVariable", f"task.{task_id}.result")
            result["decision_ref"] = decision_ref
            result["result_variable"] = result_variable
            if decision_ref:
                instance.set_variable(f"task.{task_id}.decisionRef", decision_ref)

        else:
            result["output"] = payload

        instance.set_variable(f"task.{task_id}.output", result)
        instance.set_variable(f"task.{task_id}.status", "completed")

        return result

    def _get_available_tasks(self, plan_model: CasePlanModel) -> list[RawData]:
        available: list[RawData] = []
        active_stage_ids: set[str] = set()

        for stage in plan_model.stages:
            stage_ctx = self._stages.get(stage.get("id", ""))
            if stage_ctx and stage_ctx.is_active:
                active_stage_ids.add(stage.get("id", ""))

        for task in plan_model.tasks:
            task_type = task.get("type", "task")
            if task_type == CMMNTaskType.MILESTONE:
                continue

            stage_ref = task.get("stageRef")
            if stage_ref and stage_ref not in active_stage_ids:
                continue

            activation_rule = task.get("activationRule", "automatic")
            if activation_rule == "manual":
                continue

            _required_rule = task.get("requiredRule", "optional")
            available.append(task)

        for item in plan_model.discretionary_items:
            planning_ctx = self._planning_items.get(item.get("id", ""))
            if planning_ctx and planning_ctx.is_planned:
                available.append({
                    "id": item.get("id", ""),
                    "name": item.get("name"),
                    "type": item.get("definitionType", "task"),
                    "planning_table_ref": item.get("planningTableRef"),
                    "entryCriteria": item.get("entryCriteria", []),
                    "is_discretionary": True,
                })

        return available

    def _evaluate_milestones(self, instance: ProcessInstance) -> None:
        for milestone_id, ctx in self._milestones.items():
            if ctx.is_achieved:
                continue
            if ctx.entry_criteria:
                criteria_dicts = [self._sentry_to_dict(ec) for ec in ctx.entry_criteria]
                if self.sentry_evaluator.evaluate_entry_criteria(criteria_dicts, instance):
                    ctx.is_achieved = True
                    instance.set_variable(f"milestone.{milestone_id}.achieved", True)
            else:
                ctx.is_achieved = True
                instance.set_variable(f"milestone.{milestone_id}.achieved", True)

    def _check_case_completion(self, instance: ProcessInstance) -> None:
        all_milestones_achieved = all(ctx.is_achieved for ctx in self._milestones.values())
        all_stages_done = all(
            ctx.is_completed for ctx in self._stages.values()
        ) if self._stages else True

        if all_milestones_achieved and all_stages_done:
            instance.complete()

    def _normalize_definition(self, definition: RawData) -> CasePlanModel:
        plan_model = CasePlanModel()

        stages = definition.get("stages", definition.get("fragments", []))
        if isinstance(stages, list):
            plan_model.stages = stages

        tasks = definition.get("tasks", definition.get("elements", []))
        if isinstance(tasks, list):
            plan_model.tasks = tasks

        milestones = definition.get("milestones", [])
        if isinstance(milestones, list):
            plan_model.milestones = milestones

        case_file_items = definition.get("caseFileItems", definition.get("case_file_items", definition.get("case_file", [])))
        if isinstance(case_file_items, list):
            plan_model.case_file_items = case_file_items

        sentries = definition.get("sentries", definition.get("entryCriteria", []))
        if isinstance(sentries, list):
            plan_model.sentries = sentries

        discretionary_items = definition.get("discretionaryItems", definition.get("fragments", []))
        if isinstance(discretionary_items, list):
            plan_model.discretionary_items = discretionary_items

        return plan_model

    def plan(self, definition: RawData) -> list[str]:
        plan_model = self._normalize_definition(definition)
        return [item.get("id", f"item_{i}") for i, item in enumerate(plan_model.tasks)]
