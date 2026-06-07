"""Execution history persistence with time-series aggregation and audit trail reconstruction."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple

from .runtime_records import AUDIT_RECORD
from .repository import PersistentRuntimeRepository


class HistoryRepository(PersistentRuntimeRepository):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            record_type=AUDIT_RECORD,
            key_prefix="orchestration:history:",
            measurement="orchestration_history",
            **kwargs,
        )

    def append(self, instance_id: str, data: dict[str, Any]) -> None:
        payload = dict(data)
        payload.setdefault("instance_id", instance_id)
        payload.setdefault("created_at", datetime.utcnow().isoformat())
        super().save(f"{instance_id}:{payload['created_at']}", payload)

    async def append_persisted(self, instance_id: str, data: dict[str, Any]) -> dict[str, Any]:
        payload = dict(data)
        payload.setdefault("instance_id", instance_id)
        payload.setdefault("created_at", datetime.utcnow().isoformat())
        payload.setdefault("action", payload.get("action", "history.append"))
        key = f"{instance_id}:{payload['created_at']}"
        return await self.save_persisted(key, payload)

    def query(self, instance_id: str) -> list[dict[str, Any]]:
        """Get history records for an instance, ordered by timestamp (oldest first)."""
        rows = self.list(predicate=lambda row: row.get("instance_id") == instance_id)
        return sorted(rows, key=lambda item: item.get("created_at", ""))

    def query_time_series_aggregation(
        self, 
        instance_id: str, 
        metric: str, 
        aggregation: str = "count",
        interval: str = "hour"
    ) -> list[dict[str, Any]]:
        """
        Perform time-series aggregation on history records for metrics.
        
        Args:
            instance_id: The instance ID to filter records
            metric: The metric to aggregate (e.g., 'action', 'activity_id')
            aggregation: The aggregation function ('count', 'sum', 'avg', 'min', 'max')
            interval: The time interval for grouping ('minute', 'hour', 'day')
            
        Returns:
            List of dictionaries with time buckets and aggregated values
        """
        # Get all records for the instance
        records = self.query(instance_id)
        
        # Group by time interval
        grouped_records: Dict[str, List[Dict[str, Any]]] = {}
        
        for record in records:
            created_at_str = record.get("created_at", "")
            if not created_at_str:
                continue
                
            try:
                # Parse the timestamp
                dt = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                
                # Format the time bucket based on interval
                if interval == "minute":
                    time_bucket = dt.strftime("%Y-%m-%d %H:%M")
                elif interval == "hour":
                    time_bucket = dt.strftime("%Y-%m-%d %H:00")
                elif interval == "day":
                    time_bucket = dt.strftime("%Y-%m-%d")
                else:
                    # Default to hour
                    time_bucket = dt.strftime("%Y-%m-%d %H:00")
                    
                if time_bucket not in grouped_records:
                    grouped_records[time_bucket] = []
                grouped_records[time_bucket].append(record)
            except ValueError:
                # Skip records with invalid timestamps
                continue
        
        # Perform aggregation for each time bucket
        results = []
        for time_bucket, bucket_records in sorted(grouped_records.items()):
            aggregated_value: int | float = 0
            if aggregation == "count":
                aggregated_value = len(bucket_records)
            elif aggregation == "sum":
                values = []
                for record in bucket_records:
                    value = record.get(metric)
                    if isinstance(value, (int, float)):
                        values.append(value)
                aggregated_value = sum(values) if values else 0
            elif aggregation == "avg":
                values_avg = []
                for record in bucket_records:
                    value = record.get(metric)
                    if isinstance(value, (int, float)):
                        values_avg.append(value)
                aggregated_value = sum(values_avg) / len(values_avg) if values_avg else 0
            elif aggregation == "min":
                values_min = []
                for record in bucket_records:
                    value = record.get(metric)
                    if isinstance(value, (int, float)):
                        values_min.append(value)
                aggregated_value = min(values_min) if values_min else 0
            elif aggregation == "max":
                values_max = []
                for record in bucket_records:
                    value = record.get(metric)
                    if isinstance(value, (int, float)):
                        values_max.append(value)
                aggregated_value = max(values_max) if values_max else 0
            else:
                aggregated_value = len(bucket_records)

            results.append({
                "time_bucket": time_bucket,
                "metric": metric,
                "aggregation": aggregation,
                "value": aggregated_value,
                "record_count": len(bucket_records)
            })
            
        return results

    def reconstruct_audit_trail(self, instance_id: str) -> list[dict[str, Any]]:
        """
        Reconstruct the complete audit trail for an instance.
        
        Returns a chronological list of audit events that shows the sequence
        of activities, state changes, and actions performed on the instance.
        """
        # Get all history records for the instance
        records = self.query(instance_id)
        
        # Enhance each record with additional context for reconstruction
        audit_trail = []
        for record in records:
            # Create a reconstructed audit entry
            audit_entry = {
                "timestamp": record.get("created_at"),
                "instance_id": record.get("instance_id"),
                "activity_id": record.get("activity_id"),
                "action": record.get("action"),
                "description": self._generate_audit_description(record),
                "payload": record.get("payload", {}),
                "metadata": {
                    "record_id": record.get("record_id"),
                    "record_type": record.get("record_type")
                }
            }
            audit_trail.append(audit_entry)
            
        return audit_trail

    def reconstruct_audit_trail_by_activity(self, instance_id: str) -> Dict[str, List[dict[str, Any]]]:
        """
        Reconstruct the audit trail grouped by activity.
        
        Returns a dictionary where keys are activity IDs and values are lists
        of audit events for each activity, providing a detailed view of
        what happened in each activity.
        """
        # Get the full audit trail
        audit_trail = self.reconstruct_audit_trail(instance_id)
        
        # Group by activity ID
        grouped_trail: Dict[str, List[dict[str, Any]]] = {}
        for entry in audit_trail:
            activity_id = entry.get("activity_id", "unknown")
            if activity_id not in grouped_trail:
                grouped_trail[activity_id] = []
            grouped_trail[activity_id].append(entry)
            
        return grouped_trail

    def get_instance_transitions(self, instance_id: str) -> list[dict[str, Any]]:
        """
        Get state transitions for an instance from the audit trail.
        
        Returns a list of state changes that shows how the instance progressed
        through different states over time.
        """
        # Get the full audit trail
        audit_trail = self.reconstruct_audit_trail(instance_id)
        
        # Filter for state transition actions (this would be customized based on
        # what actions represent state transitions in your system)
        transitions = []
        for entry in audit_trail:
            action = entry.get("action", "")
            # Common state transition actions - customize as needed
            if any(state_action in action.lower() for state_action in 
                   ["start", "complete", "suspend", "resume", "cancel", "terminate"]):
                transitions.append(entry)
                
        return transitions

    def _generate_audit_description(self, record: dict[str, Any]) -> str:
        """Generate a human-readable description of an audit record."""
        activity_id = record.get("activity_id", "Unknown Activity")
        action = record.get("action", "Unknown Action")
        
        # Create a descriptive message based on the action
        action_descriptions = {
            "process.start": f"Process started for activity {activity_id}",
            "process.complete": f"Process completed for activity {activity_id}",
            "task.assign": f"Task assigned: {activity_id}",
            "task.complete": f"Task completed: {activity_id}",
            "state.enter": f"Entered state: {activity_id}",
            "state.exit": f"Exited state: {activity_id}",
            "transition.take": f"Transition taken: {activity_id}",
        }
        
        # Return specific description if available, otherwise generic
        return action_descriptions.get(action, f"{action} on {activity_id}")
