"""Parallel state handler for state machine.

Supports orthogonal regions and join/termination behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...core.instance import ProcessInstance


@dataclass
class RegionState:
    region_id: str
    states: list[str] = field(default_factory=list)
    current_state: str | None = None
    is_active: bool = False
    is_completed: bool = False
    initial_state: str | None = None


class ParallelStateHandler:
    def __init__(self) -> None:
        self._regions: dict[str, RegionState] = {}

    def register_region(self, region: RegionState) -> None:
        self._regions[region.region_id] = region

    def activate_region(self, region_id: str, instance: ProcessInstance | None = None) -> None:
        region = self._regions.get(region_id)
        if region:
            region.is_active = True
            if region.initial_state:
                region.current_state = region.initial_state

    def deactivate_region(self, region_id: str) -> None:
        region = self._regions.get(region_id)
        if region:
            region.is_active = False

    def complete_region(self, region_id: str, final_state: str | None = None) -> None:
        region = self._regions.get(region_id)
        if region:
            region.is_active = False
            region.is_completed = True
            if final_state:
                region.current_state = final_state

    def are_all_regions_complete(self) -> bool:
        return all(r.is_completed for r in self._regions.values() if r.is_active)

    def check_join(self, target_state: str, incoming_regions: list[str]) -> bool:
        for region_id in incoming_regions:
            region = self._regions.get(region_id)
            if region and not region.is_completed:
                return False
        return True

    def get_active_regions(self) -> list[str]:
        return [r_id for r_id, r in self._regions.items() if r.is_active]

    def get_completed_regions(self) -> list[str]:
        return [r_id for r_id, r in self._regions.items() if r.is_completed]

    def is_region_complete(self, region_id: str) -> bool:
        region = self._regions.get(region_id)
        return region is not None and region.is_completed
