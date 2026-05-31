"""Conversation execution engine.

Executes BPMN conversation definitions with participant coordination,
sub-conversation expansion, call conversation resolution, and link traversal.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ....document.models.osdm_models import (
    Conversation,
    SubConversation,
    CallConversation,
    GlobalConversation,
    ConversationLink,
    ConversationNode,
    ConversationAssociation,
    Participant,
)


logger = logging.getLogger(__name__)


@dataclass
class ConversationExecutionContext:
    conversation_id: str
    participants: list[str] = field(default_factory=list)
    links: list[dict[str, Any]] = field(default_factory=list)
    active_nodes: list[str] = field(default_factory=list)
    status: str = "active"


class ConversationExecutor:
    """Executes BPMN conversation definitions."""

    def __init__(self, orchestration_engine: Any | None = None) -> None:
        self._engine = orchestration_engine
        self._contexts: dict[str, ConversationExecutionContext] = {}

    def create_context(
        self,
        conversation_id: str,
        conversation: Conversation | None = None,
    ) -> ConversationExecutionContext:
        ctx = ConversationExecutionContext(conversation_id=conversation_id)
        if conversation:
            if hasattr(conversation, 'participants'):
                for p in conversation.participants if conversation.participants else []:
                    pid = p.id if hasattr(p, 'id') else str(p)
                    ctx.participants.append(pid)
        self._contexts[conversation_id] = ctx
        return ctx

    def get_context(self, conversation_id: str) -> ConversationExecutionContext | None:
        return self._contexts.get(conversation_id)

    async def expand_sub_conversation(
        self,
        sub_conv: SubConversation,
        context: ConversationExecutionContext,
    ) -> list[dict[str, Any]]:
        results = []
        nodes = getattr(sub_conv, 'nodes', {})
        for node_id, node in nodes.items():
            results.append({
                "node_id": node_id,
                "type": node.__class__.__name__,
                "expanded_from": sub_conv.id,
                "conversation_id": context.conversation_id,
            })
        return results

    async def resolve_call_conversation(
        self,
        call_conv: CallConversation,
        context: ConversationExecutionContext,
    ) -> dict[str, Any]:
        called_ref = getattr(call_conv, 'called_conversation_ref', None)
        result: dict[str, Any] = {
            "call_id": call_conv.id,
            "called_ref": called_ref,
            "status": "resolved",
        }
        if called_ref and self._engine:
            called_def = self._engine.definitions.get(called_ref)
            result["definition_found"] = called_def is not None
        return result

    async def traverse_conversation_link(
        self,
        link: ConversationLink,
        context: ConversationExecutionContext,
    ) -> dict[str, Any]:
        source_ref = getattr(link, 'source_ref', None)
        target_ref = getattr(link, 'target_ref', None)
        name = getattr(link, 'name', None)
        link_info = {
            "link_id": link.id,
            "name": name,
            "conversation_id": context.conversation_id,
        }
        if source_ref:
            link_info["source"] = source_ref.id if hasattr(source_ref, 'id') else str(source_ref)
        if target_ref:
            link_info["target"] = target_ref.id if hasattr(target_ref, 'id') else str(target_ref)
        return link_info

    async def resolve_global_conversation(
        self,
        global_conv: GlobalConversation,
        context: ConversationExecutionContext,
    ) -> dict[str, Any]:
        collaboration_ref = getattr(global_conv, 'collaboration_ref', None)
        return {
            "global_conv_id": global_conv.id,
            "collaboration_ref": str(collaboration_ref) if collaboration_ref else None,
            "conversation_id": context.conversation_id,
            "status": "resolved",
        }

    async def resolve_conversation_association(
        self,
        association: ConversationAssociation,
        context: ConversationExecutionContext,
    ) -> dict[str, Any]:
        conversation_ref = getattr(association, 'conversation_ref', None)
        source_ref = getattr(association, 'source_ref', None)
        target_ref = getattr(association, 'target_ref', None)
        return {
            "association_id": association.id,
            "conversation_ref": str(conversation_ref) if conversation_ref else None,
            "source_ref": str(source_ref) if source_ref else None,
            "target_ref": str(target_ref) if target_ref else None,
        }

    def get_statistics(self) -> dict[str, Any]:
        return {
            "total_conversations": len(self._contexts),
            "total_participants": sum(len(ctx.participants) for ctx in self._contexts.values()),
        }
