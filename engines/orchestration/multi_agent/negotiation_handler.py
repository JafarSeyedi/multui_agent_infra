"""Negotiation helper for agent agreements."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Proposal:
    proposal_id: str
    payload: dict


def evaluate_proposals(proposals: list[Proposal]) -> Proposal | None:
    return proposals[0] if proposals else None
