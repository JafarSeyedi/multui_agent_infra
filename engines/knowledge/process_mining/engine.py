from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from engines.knowledge.ml_mining.models import MiningModelType
from engines.knowledge.process_mining.models import (
    ClusteringConfig,
    MiningProcessDefinition,
    ProcessMiningDefinitionDocument,
)
from engines.document.models.lsdm_models import EventLogDocument, LogAttribute
from engines.document.models.media_types import MEDIA_TYPES
from engines.orchestration.dmn.models.dmn_models import (
    DMNDefinition,
    DMNDocument,
    Decision,
    DecisionRule,
    DecisionTable,
    DecisionLogicType,
    InputClause,
    LiteralExpression,
    OutputClause,
    UnaryTests,
)
from engines.document.models.standard import DocumentStandard
from engines.knowledge.process_mining.models.parsers.jprm_parser import JprmParser
from engines.knowledge.process_mining.models.parsers.yprm_parser import YprmParser
from engines.knowledge.ml_mining.engine import MlMiningEngine


_PARSERS: dict[str, type[JprmParser | YprmParser]] = {
    "jprm": JprmParser,
    "yprm": YprmParser,
}

_DMN_MEDIA_TYPE = MEDIA_TYPES["dmn_xml"]


def _get_attribute_value(event: LogAttribute | dict[str, Any], key: str) -> str | None:
    if isinstance(event, dict):
        return str(event.get(key, "")) or None
    return event.value if event.key == key else None


def _extract_event_features(
    events: list[LogAttribute] | list[dict[str, Any]],
    feature_keys: list[str],
) -> dict[str, str]:
    features: dict[str, str] = {}
    for attr in events:
        if isinstance(attr, LogAttribute):
            key = attr.key
            value = attr.value
        else:
            key = str(attr.get("key", ""))
            value = str(attr.get("value", ""))
        if key in feature_keys:
            features[key] = value
    return features


class ProcessMiningEngine:
    def __init__(self) -> None:
        self._ml_engine = MlMiningEngine()

    def load(
        self, path: str | Path,
        document_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ProcessMiningDefinitionDocument:
        p = Path(path)
        ext = p.suffix.lstrip(".").lower()
        parser_cls = _PARSERS.get(ext)
        if parser_cls is None:
            raise ValueError(f"Unsupported process mining format: {ext}")
        parser = parser_cls()
        import asyncio
        doc = asyncio.run(
            parser.parse_path(
                str(p),
                document_id or p.stem,
                metadata=metadata,
            )
        )
        return doc

    def loads(
        self, content: str, fmt: str = "jprm",
        document_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> ProcessMiningDefinitionDocument:
        parser_cls = _PARSERS.get(fmt)
        if parser_cls is None:
            raise ValueError(f"Unsupported process mining format: {fmt}")
        parser = parser_cls()
        import asyncio
        doc = asyncio.run(
            parser.parse_bytes(
                content.encode("utf-8"),
                document_id,
                source_name=f"inline.{fmt}",
                metadata=metadata,
            )
        )
        return doc

    def discover_process_model(
        self,
        doc: ProcessMiningDefinitionDocument,
        event_log: EventLogDocument,
        activity_key: str = "concept:name",
    ) -> ProcessMiningDefinitionDocument:
        for pid, pdef in doc.processes.items():
            pdef.mining_name = pdef.mining_name or f"discovered_{pid}"
        return doc

    def analyze_decision_points(
        self,
        doc: ProcessMiningDefinitionDocument,
        event_log: EventLogDocument,
        activity_key: str = "concept:name",
    ) -> DMNDocument:
        dmn_def = DMNDefinition(id="decision_mining", name="Decision Mining Analysis")

        for pid, pdef in doc.processes.items():
            for dpid, dp in pdef.decision_points.items():
                rules: list[DecisionRule] = []
                input_columns: set[str] = set()

                trace_data: list[dict[str, str]] = []
                trace_labels: list[str] = []

                for trace in event_log.traces:
                    evt_attrs: list[dict[str, Any]] = []
                    for ea in trace.events:
                        if isinstance(ea, LogAttribute):
                            evt_attrs.append({"key": ea.key, "value": ea.value})
                        else:
                            evt_attrs.append(ea)
                    attrs = _extract_event_features(evt_attrs, [activity_key])
                    activity = attrs.get(activity_key, "")
                    if activity:
                        trace_data.append(attrs)
                        trace_labels.append(activity)

                if trace_data:
                    combined: dict[str, list[str]] = defaultdict(list)
                    for td in trace_data:
                        for k, v in td.items():
                            combined[k].append(v)
                    for k in combined:
                        if k != activity_key:
                            input_columns.add(k)

                    seen_rules: set[str] = set()
                    for td, label in zip(trace_data, trace_labels):
                        input_values = [td.get(col, "") for col in sorted(input_columns)]
                        rule_key = "|".join(input_values)
                        if rule_key not in seen_rules:
                            seen_rules.add(rule_key)
                            rid = f"rule_{len(rules)}"
                            rule = DecisionRule(
                                id=rid,
                                input_entries=[
                                    UnaryTests(id=f"uit_{rid}_{i}", body=f'= "{v}"') if v else UnaryTests(id=f"uit_{rid}_{i}", body="-")
                                    for i, v in enumerate(input_values)
                                ],
                                output_entries=[
                                    LiteralExpression(id=f"ole_{rid}", body=label),
                                ],
                            )
                            rules.append(rule)

                dt_id = f"dt_{dpid}"
                decision = Decision(
                    id=dpid,
                    name=f"Decision_{dpid}",
                    logic=DecisionLogicType.DECISION_TABLE,
                    table_data=DecisionTable(
                        id=dt_id,
                        hit_policy="UNIQUE",
                        inputs=[
                            InputClause(
                                id=f"ic_{dt_id}_{i}",
                                input_expression=LiteralExpression(id=f"ie_{dt_id}_{i}", body=col),
                            )
                            for i, col in enumerate(sorted(input_columns))
                        ],
                        outputs=[
                            OutputClause(id=f"oc_{dt_id}", name=activity_key),
                        ],
                        rules=rules,
                    ),
                )
                dmn_def.decisions.append(decision)

        return DMNDocument(
            title=f"Decision Mining: {doc.title}",
            document_id=f"{doc.document_id}_dmn",
            kind=DocumentStandard.OSDM,
            dmn_definitions=[dmn_def],
            media_type=_DMN_MEDIA_TYPE,
        )

    def analyze_catch_events(
        self,
        doc: ProcessMiningDefinitionDocument,
        event_log: EventLogDocument,
    ) -> DMNDocument:
        dmn_def = DMNDefinition(id="event_mining", name="Catch Event Mining Analysis")

        for pid, pdef in doc.processes.items():
            for cid, ce in pdef.catch_event_definitions.items():
                rules: list[DecisionRule] = []
                cluster_assignments: dict[int, list[dict[str, str]]] = defaultdict(list)
                for i, ev in enumerate(event_log.events):
                    evt_attrs: list[dict[str, Any]] = []
                    for ea in ev.attributes:
                        evt_attrs.append({"key": ea.key, "value": ea.value})
                    attrs = _extract_event_features(evt_attrs, [a.key for a in ev.attributes])
                    cluster_id = hash(frozenset(attrs.items())) % max(len(event_log.events), 1)
                    cluster_assignments[cluster_id].append(attrs)

                for cluster_id, members in cluster_assignments.items():
                    cluster_name = f"cluster_{cluster_id}"
                    for member in members[:3]:
                        rid = f"cerule_{len(rules)}"
                        input_str = ", ".join(f"{k}={v}" for k, v in member.items())
                        rule = DecisionRule(
                            id=rid,
                            input_entries=[UnaryTests(id=f"ceuit_{rid}", body=f'= "{cluster_name}"')],
                            output_entries=[
                                LiteralExpression(id=f"ceole_{rid}", body=input_str),
                            ],
                        )
                        rules.append(rule)

                dt_id = f"dt_{cid}"
                decision = Decision(
                    id=cid,
                    name=f"CatchEvent_{cid}",
                    logic=DecisionLogicType.DECISION_TABLE,
                    table_data=DecisionTable(
                        id=dt_id,
                        hit_policy="COLLECT",
                        inputs=[
                            InputClause(
                                id=f"ic_{dt_id}",
                                input_expression=LiteralExpression(id=f"ie_{dt_id}", body="cluster"),
                            )
                        ],
                        outputs=[
                            OutputClause(id=f"oc_{dt_id}", name="event_pattern"),
                        ],
                        rules=rules,
                    ),
                )
                dmn_def.decisions.append(decision)

        return DMNDocument(
            title=f"Event Mining: {doc.title}",
            document_id=f"{doc.document_id}_event",
            kind=DocumentStandard.OSDM,
            dmn_definitions=[dmn_def],
            media_type=_DMN_MEDIA_TYPE,
        )

    def to_dmn(
        self,
        doc: ProcessMiningDefinitionDocument,
        decision_point_id: str | None = None,
        activity_key: str = "concept:name",
    ) -> DMNDocument:
        dmn_def = DMNDefinition(id="process_dmn", name="Process Mining DMN Export")

        for pid, pdef in doc.processes.items():
            for dpid, dp in pdef.decision_points.items():
                if decision_point_id is not None and dpid != decision_point_id:
                    continue
                dt_id = f"dt_{dpid}"
                decision = Decision(
                    id=dpid,
                    name=f"Decision_{dpid}",
                    logic=DecisionLogicType.DECISION_TABLE,
                    table_data=DecisionTable(
                        id=dt_id,
                        hit_policy="UNIQUE",
                        inputs=[
                            InputClause(
                                id=f"ic_{dt_id}",
                                input_expression=LiteralExpression(id=f"ie_{dt_id}", body=activity_key),
                            )
                        ],
                        outputs=[
                            OutputClause(id=f"oc_{dt_id}", name="next_activity"),
                        ],
                        rules=[],
                    ),
                )
                dmn_def.decisions.append(decision)

        return DMNDocument(
            title=f"DMN Export: {doc.title}",
            document_id=f"{doc.document_id}_dmn_export",
            kind=DocumentStandard.OSDM,
            dmn_definitions=[dmn_def],
            media_type=_DMN_MEDIA_TYPE,
        )

    def validate(
        self, doc: ProcessMiningDefinitionDocument,
    ) -> list[str]:
        errors: list[str] = []
        for pid, pdef in doc.processes.items():
            if not pdef.id:
                errors.append(f"Process '{pid}' has no id")
            for dpid in pdef.decision_points:
                if not dpid:
                    errors.append(f"Decision point in process '{pid}' has empty id")
            for cid in pdef.catch_event_definitions:
                if not cid:
                    errors.append(f"Catch event definition in process '{pid}' has empty id")
        return errors

    def get_statistics(
        self, doc: ProcessMiningDefinitionDocument,
    ) -> dict[str, Any]:
        total_dps = sum(
            len(pdef.decision_points) for pdef in doc.processes.values()
        )
        total_ceds = sum(
            len(pdef.catch_event_definitions) for pdef in doc.processes.values()
        )
        return {
            "num_processes": len(doc.processes),
            "num_decision_points": total_dps,
            "num_catch_event_definitions": total_ceds,
            "has_default_clustering": doc.default_clustering_config is not None,
            "processes": [
                {
                    "id": pid,
                    "decision_points": list(pdef.decision_points.keys()),
                    "catch_event_definitions": list(pdef.catch_event_definitions.keys()),
                }
                for pid, pdef in doc.processes.items()
            ],
        }
