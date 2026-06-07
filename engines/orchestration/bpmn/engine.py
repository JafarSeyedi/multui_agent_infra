"""BPMN 2.0 orchestration engine implementation."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Optional

from ..core.context import ContextManager, ContextScope
from ..core.engine import OrchestrationEngine, ProcessDefinition
from ..core.instance import InstanceState, ProcessInstance
from ..runtime.state_manager import StateManager
from .process_executor import BPMNProcessExecutor
from .choreography_executor import ChoreographyExecutor
from .conversation_executor import ConversationExecutor
from .pool_lane_executor import PoolLaneExecutor

# OSDM BPMN model imports
from ...document.parsers.osdm_parsers.bpmn_xml_parser import BPMNXMLParser
from ...document.models.osdm_models import (
    BPMNDocument, Process, FlowElement, FlowNode, Activity, SequenceFlow,
    Event, Gateway, EventType, Choreography, Collaboration,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BPMNExecutionError(RuntimeError):
    """Raised when BPMN runtime cannot execute a definition."""


class BPMNEngine:
    """Engine adapter used by :class:`OrchestrationEngine` via `engine_handlers`."""

    def __init__(
        self,
        orchestration_engine: OrchestrationEngine,
        *,
        state_manager: StateManager | None = None,
    ) -> None:
        self.orchestration_engine = orchestration_engine
        self.context_manager = ContextManager()
        self.state_manager = state_manager or orchestration_engine.state_manager
        self.executor = BPMNProcessExecutor(
            engine=self,
            orchestration_engine=orchestration_engine,
            state_manager=self.state_manager,
            context_manager=self.context_manager,
        )
        self.choreography_executor = ChoreographyExecutor(orchestration_engine=orchestration_engine)
        self.conversation_executor = ConversationExecutor(orchestration_engine=orchestration_engine)
        self.pool_lane_executor = PoolLaneExecutor()
        # Parser for converting BPMN XML to OSDM model objects
        self._bpmn_parser = BPMNXMLParser()
        # Cache for parsed BPMN documents to avoid reparsing
        self._parsed_documents: Dict[str, BPMNDocument] = {}

    def _convert_flow_elements_to_activities_and_flows(self, flow_elements: Dict[str, FlowElement]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Convert OSDM flow elements to activities and flows lists for the process executor.
        
        Args:
            flow_elements: Dictionary mapping element IDs to FlowElement objects
            
        Returns:
            Tuple of (activities_list, flows_list)
        """
        activities = []
        flows = []
        
        for element_id, element in flow_elements.items():
            # Handle different types of flow elements
            if isinstance(element, Activity):
                # Convert Activity to dict format expected by executor
                activity_dict = {
                    "id": element.id,
                    "name": getattr(element, 'name', None) or element.id,
                    "type": getattr(element.activity_type, 'value', str(element.activity_type)) if hasattr(element, 'activity_type') else "task",
                    # Add other relevant activity properties
                }
                
                # Add loop characteristics if present
                if hasattr(element, 'loop_characteristics') and element.loop_characteristics:
                    loop_char = element.loop_characteristics
                    activity_dict["loop_characteristics"] = {
                        "type": getattr(loop_char, '__class__.__name__', str(type(loop_char))),
                        # Add specific loop characteristic properties as needed
                    }
                
                # Add IO specification if present
                if hasattr(element, 'io_specification') and element.io_specification:
                    io_spec = element.io_specification
                    activity_dict["io_specification"] = {
                        "data_inputs": [{"id": di.id, "name": getattr(di, 'name', None)} for di in getattr(io_spec, 'data_inputs', [])],
                        "data_outputs": [{"id": do.id, "name": getattr(do, 'name', None)} for do in getattr(io_spec, 'data_outputs', [])],
                        "data_associations": [
                            {
                                "id": da.id,
                                "source_ref": getattr(da, 'source_ref', None),
                                "target_ref": getattr(da, 'target_ref', None),
                                "transformation": getattr(da, 'transformation', None)
                            } for da in getattr(io_spec, 'data_associations', [])
                        ]
                    }
                
                activities.append(activity_dict)
                
            elif isinstance(element, SequenceFlow):
                flow_dict = {
                    "id": element.id,
                    "source": element.source_ref_id or (element.source_ref.id if element.source_ref else None),
                    "target": element.target_ref_id or (element.target_ref.id if element.target_ref else None),
                    "sourceRef": element.source_ref_id or (element.source_ref.id if element.source_ref else None),
                    "targetRef": element.target_ref_id or (element.target_ref.id if element.target_ref else None),
                }
                
                if element.condition_expression:
                    cond_expr = element.condition_expression
                    flow_dict["condition"] = cond_expr.body if cond_expr.body else str(cond_expr)
                    flow_dict["conditionExpression"] = flow_dict["condition"]
                
                flows.append(flow_dict)
                
            # Handle other flow element types as needed (events, gateways, etc.)
            elif isinstance(element, (Event, Gateway)):
                # For now, treat events and gateways as activities for simplicity
                # In a more sophisticated implementation, they would be handled differently
                activity_dict = {
                    "id": element.id,
                    "name": getattr(element, 'name', None) or element.id,
                    "type": getattr(element, '__class__.__name__', 'unknown').replace('Event', '').replace('Gateway', '').lower() or "task",
                }
                activities.append(activity_dict)

        return activities, flows

    async def _get_bpmn_document(self, definition: ProcessDefinition) -> BPMNDocument:
        """
        Get or parse the BPMN document for a process definition.
        
        Args:
            definition: The process definition containing BPMN XML
            
        Returns:
            Parsed BPMNDocument object
        """
        # Check if we have already parsed and cached this document
        if definition.id in self._parsed_documents:
            return self._parsed_documents[definition.id]
        
        # Parse the BPMN XML to get the OSDM model
        # The definition_xml field contains the raw BPMN XML string
        bpmn_xml = definition.definition_xml.encode('utf-8')
        from ...document.parsers.base import ParseOptions
        
        parse_options = ParseOptions()
        bpmn_document = await self._bpmn_parser.parse_bytes(
            bpmn_xml,
            document_id=definition.id,
            source_name=definition.resource_name or "unknown",
            options=parse_options
        )
        
        if not isinstance(bpmn_document, BPMNDocument):
            raise BPMNExecutionError(
                f"Parser returned {type(bpmn_document).__name__}, expected BPMNDocument"
            )
        
        self._parsed_documents[definition.id] = bpmn_document
        
        return bpmn_document

    async def _get_process_from_document(self, bpmn_document: BPMNDocument, definition: ProcessDefinition) -> Process:
        """
        Extract the Process object from a BPMN document that matches the definition.
        
        Args:
            bpmn_document: The parsed BPMN document
            definition: The process definition to match
            
        Returns:
            The Process object that matches the definition
            
        Raises:
            BPMNExecutionError: If no matching process is found
        """
        # Find the process that matches the definition key or ID
        for process in bpmn_document.processes:
            # Match by definition key (from the BPMN model) or by ID
            if (process.id == definition.key or 
                process.id == definition.id or
                getattr(process, 'name', None) == definition.name):
                return process
        
        # If no exact match, return the first executable process
        for process in bpmn_document.processes:
            if getattr(process, 'is_executable', False):
                return process
        
        # If still no match, raise an error
        if bpmn_document.processes:
            raise BPMNExecutionError(
                f"No executable process found in BPMN document for definition {definition.key}"
            )
        else:
            raise BPMNExecutionError(
                f"No processes found in BPMN document for definition {definition.key}"
            )

    async def execute_instance(self, instance: ProcessInstance, definition: ProcessDefinition) -> None:
        context_id = instance.id
        
        # Get the parsed BPMN document and extract the process
        bpmn_document = await self._get_bpmn_document(definition)
        process = await self._get_process_from_document(bpmn_document, definition)
        
        logger.info("BPMN engine executing instance %s for process %s", instance.id, process.id)
        
        # Convert the OSDM process to the format expected by the executor
        activities, flows = self._convert_flow_elements_to_activities_and_flows(
            getattr(process, 'flow_elements', {})
        )
        
        # Find the start node (look for start events)
        start_node = None
        for element in getattr(process, 'flow_elements', {}).values():
            if isinstance(element, Event) and getattr(element, 'event_type', None) == EventType.START:
                start_node = element.id
                break
        
        # If no start event found, look for any element with a start-like type
        if not start_node:
            for element_id, element in getattr(process, 'flow_elements', {}).items():
                if hasattr(element, 'type') and str(getattr(element, 'type', '')).lower() in {'start', 'startevent', 'startEvent'}:
                    start_node = element_id
                    break
        
        definition_payload = {
            "id": process.id,
            "activities": activities,
            "flows": flows,
            "start_event_id": start_node,
        }
        
        self.context_manager.create_context(ContextScope.PROCESS, context_id)
        logger.info("BPMN engine executing instance %s", instance.id)

        await self.state_manager.set_persisted(
            context_id,
            "running",
            data={"definition_key": definition.key, "definition_id": definition.id},
        )
        try:
            outcome = await self.executor.execute(instance, definition_payload)
        except Exception as exc:
            await self.orchestration_engine.update_instance_state(instance.id, InstanceState.FAILED, reason=str(exc))
            await self.state_manager.set_persisted(
                context_id,
                "failed",
                data={"definition_key": definition.key, "definition_id": definition.id, "error": str(exc)},
            )
            raise

        if outcome.completed:
            await self.orchestration_engine.update_instance_state(instance.id, InstanceState.COMPLETED)
            await self.state_manager.set_persisted(
                context_id,
                "completed",
                data={"definition_key": definition.key, "definition_id": definition.id},
            )
            return

        final_state = "waiting" if outcome.waiting else (instance.state.value if hasattr(instance.state, "value") else str(instance.state))
        await self.state_manager.set_persisted(
            context_id,
            final_state,
            data={"definition_key": definition.key, "definition_id": definition.id, "current_node": outcome.current_node},
        )
        logger.debug("BPMN instance paused in state for %s: %s", instance.id, final_state)
