"""
Transaction Management

Manages transactional boundaries for process execution.
Supports ACID properties, compensation, and distributed transactions.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any
from collections.abc import Callable
from enum import Enum
from dataclasses import dataclass, field
from uuid import uuid4
from contextlib import asynccontextmanager

from .transaction_states import (
    ActiveState as _ActiveTxState,
    CommittedState as _CommittedTxState,
    FailedState as _FailedTxState,
    PreparedState as _PreparedTxState,
    RollingBackState as _RollingBackTxState,
    TransactionState as _TransactionStateABC,
)


logger = logging.getLogger(__name__)


class TransactionState(Enum):
    """Transaction states"""
    ACTIVE = "active"
    PREPARING = "preparing"
    PREPARED = "prepared"
    COMMITTING = "committing"
    COMMITTED = "committed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class IsolationLevel(Enum):
    """Transaction isolation levels"""
    READ_UNCOMMITTED = "read_uncommitted"
    READ_COMMITTED = "read_committed"
    REPEATABLE_READ = "repeatable_read"
    SERIALIZABLE = "serializable"


@dataclass
class TransactionParticipant:
    """Participant in a distributed transaction"""
    participant_id: str
    name: str
    prepare_handler: Callable | None = None
    commit_handler: Callable | None = None
    rollback_handler: Callable | None = None
    is_prepared: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CompensationAction:
    """Compensation action for transaction rollback"""
    action_id: str
    name: str
    handler: Callable
    order: int = 0  # Execution order (higher = later)
    executed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class TransactionScope:
    """
    Transaction scope for coordinating transactional operations.
    
    Supports:
    - ACID transaction semantics
    - Two-phase commit for distributed transactions
    - Compensation-based rollback
    - Nested transactions (savepoints)
    """
    
    def __init__(
        self,
        transaction_id: str,
        isolation_level: IsolationLevel = IsolationLevel.READ_COMMITTED,
        parent: TransactionScope | None = None
    ) -> None:
        self.transaction_id = transaction_id
        self.isolation_level = isolation_level
        self.parent = parent
        self._lifecycle_state: _TransactionStateABC = _ActiveTxState()

        # Timing
        self.start_time = datetime.utcnow()
        self.end_time: datetime | None = None
        
        # Participants (for distributed transactions)
        self.participants: dict[str, TransactionParticipant] = {}
        
        # Compensation actions
        self.compensation_actions: list[CompensationAction] = []
        
        # Transaction log
        self.log: list[dict[str, Any]] = []

        # Metadata
        self.metadata: dict[str, Any] = {}

        # Nested transactions (savepoints)
        self.savepoints: dict[str, TransactionScope] = {}

    @property
    def state(self) -> TransactionState:
        name = self._lifecycle_state.name
        for s in TransactionState:
            if s.value == name:
                return s
        return TransactionState.FAILED
    
    def add_participant(
        self,
        name: str,
        prepare_handler: Callable | None = None,
        commit_handler: Callable | None = None,
        rollback_handler: Callable | None = None,
        participant_id: str | None = None
    ) -> str:
        """Add a participant to the transaction"""
        if participant_id is None:
            participant_id = str(uuid4())
        
        participant = TransactionParticipant(
            participant_id=participant_id,
            name=name,
            prepare_handler=prepare_handler,
            commit_handler=commit_handler,
            rollback_handler=rollback_handler
        )
        
        self.participants[participant_id] = participant
        self._log("participant_added", {"participant_id": participant_id, "name": name})
        
        logger.debug(f"Added participant '{name}' to transaction {self.transaction_id}")
        return participant_id
    
    def add_compensation(
        self,
        name: str,
        handler: Callable,
        order: int = 0,
        action_id: str | None = None
    ) -> str:
        """Add a compensation action"""
        if action_id is None:
            action_id = str(uuid4())
        
        action = CompensationAction(
            action_id=action_id,
            name=name,
            handler=handler,
            order=order
        )
        
        self.compensation_actions.append(action)
        self._log("compensation_added", {"action_id": action_id, "name": name})
        
        logger.debug(f"Added compensation '{name}' to transaction {self.transaction_id}")
        return action_id
    
    async def prepare(self) -> bool:
        return await self._lifecycle_state.prepare(self)

    async def _do_prepare(self) -> bool:
        self._log("prepare_started", {})
        try:
            for participant in self.participants.values():
                if participant.prepare_handler:
                    if asyncio.iscoroutinefunction(participant.prepare_handler):
                        result = await participant.prepare_handler(self)
                    else:
                        result = participant.prepare_handler(self)
                    if not result:
                        logger.warning(f"Participant '{participant.name}' failed to prepare")
                        return False
                participant.is_prepared = True
            self._log("prepare_completed", {})
            logger.info(f"Transaction {self.transaction_id} prepared successfully")
            return True
        except Exception as e:
            self._log("prepare_failed", {"error": str(e)})
            logger.error(f"Transaction {self.transaction_id} prepare failed: {e}")
            return False
    
    async def commit(self) -> bool:
        return await self._lifecycle_state.commit(self)

    async def _do_commit(self) -> bool:
        self._log("commit_started", {})
        try:
            for participant in self.participants.values():
                if participant.commit_handler:
                    if asyncio.iscoroutinefunction(participant.commit_handler):
                        await participant.commit_handler(self)
                    else:
                        participant.commit_handler(self)
            self.end_time = datetime.utcnow()
            self._log("commit_completed", {})
            logger.info(f"Transaction {self.transaction_id} committed successfully")
            return True
        except Exception as e:
            self._log("commit_failed", {"error": str(e)})
            logger.error(f"Transaction {self.transaction_id} commit failed: {e}")
            await self.rollback()
            return False
    
    async def rollback(self) -> bool:
        return await self._lifecycle_state.rollback(self)

    async def _do_rollback(self) -> bool:
        self._log("rollback_started", {})
        try:
            for participant in self.participants.values():
                if participant.rollback_handler:
                    try:
                        if asyncio.iscoroutinefunction(participant.rollback_handler):
                            await participant.rollback_handler(self)
                        else:
                            participant.rollback_handler(self)
                    except Exception as e:
                        logger.error(f"Error rolling back participant '{participant.name}': {e}")
            sorted_actions = sorted(self.compensation_actions, key=lambda a: a.order, reverse=True)
            for action in sorted_actions:
                if not action.executed:
                    try:
                        if asyncio.iscoroutinefunction(action.handler):
                            await action.handler(self)
                        else:
                            action.handler(self)
                        action.executed = True
                        self._log("compensation_executed", {"action_id": action.action_id})
                    except Exception as e:
                        logger.error(f"Error executing compensation '{action.name}': {e}")
            self.end_time = datetime.utcnow()
            self._log("rollback_completed", {})
            logger.info(f"Transaction {self.transaction_id} rolled back successfully")
            return True
        except Exception as e:
            self._log("rollback_failed", {"error": str(e)})
            logger.error(f"Transaction {self.transaction_id} rollback failed: {e}")
            return False
    
    def create_savepoint(self, name: str) -> TransactionScope:
        """Create a nested transaction (savepoint)"""
        savepoint_id = f"{self.transaction_id}:{name}"
        savepoint = TransactionScope(
            transaction_id=savepoint_id,
            isolation_level=self.isolation_level,
            parent=self
        )
        
        self.savepoints[name] = savepoint
        self._log("savepoint_created", {"name": name})
        
        logger.debug(f"Created savepoint '{name}' in transaction {self.transaction_id}")
        return savepoint
    
    async def rollback_to_savepoint(self, name: str) -> bool:
        """Rollback to a savepoint"""
        savepoint = self.savepoints.get(name)
        if not savepoint:
            logger.warning(f"Savepoint '{name}' not found")
            return False
        
        result = await savepoint.rollback()
        self._log("savepoint_rollback", {"name": name, "success": result})
        
        return result
    
    def _log(self, event: str, data: dict[str, Any]) -> None:
        """Add entry to transaction log"""
        self.log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "data": data
        })
    
    def get_duration_ms(self) -> int | None:
        """Get transaction duration in milliseconds"""
        if self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() * 1000)
        return None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert transaction to dictionary"""
        return {
            "transaction_id": self.transaction_id,
            "state": self.state.value,
            "isolation_level": self.isolation_level.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.get_duration_ms(),
            "participants": len(self.participants),
            "compensation_actions": len(self.compensation_actions),
            "savepoints": len(self.savepoints),
            "metadata": self.metadata
        }


class TransactionManager:
    """
    Manages transactions across the orchestration engine.
    
    Provides:
    - Transaction lifecycle management
    - Distributed transaction coordination
    - Compensation handling
    - Transaction isolation
    """
    
    def __init__(self) -> None:
        self.transactions: dict[str, TransactionScope] = {}
        self.active_transactions: set[str] = set()
        
        # Statistics
        self.total_committed = 0
        self.total_rolled_back = 0
        self.total_failed = 0
        
        logger.info("Transaction manager created")
    
    def begin_transaction(
        self,
        isolation_level: IsolationLevel = IsolationLevel.READ_COMMITTED,
        transaction_id: str | None = None
    ) -> TransactionScope:
        """Begin a new transaction"""
        if transaction_id is None:
            transaction_id = str(uuid4())
        
        transaction = TransactionScope(
            transaction_id=transaction_id,
            isolation_level=isolation_level
        )
        
        self.transactions[transaction_id] = transaction
        self.active_transactions.add(transaction_id)
        
        logger.info(f"Began transaction: {transaction_id}")
        return transaction
    
    def get_transaction(self, transaction_id: str) -> TransactionScope | None:
        """Get a transaction by ID"""
        return self.transactions.get(transaction_id)
    
    async def commit_transaction(self, transaction_id: str) -> bool:
        """Commit a transaction"""
        transaction = self.transactions.get(transaction_id)
        if not transaction:
            logger.warning(f"Transaction not found: {transaction_id}")
            return False
        
        result = await transaction.commit()
        
        if result:
            self.total_committed += 1
            self.active_transactions.discard(transaction_id)
        else:
            self.total_failed += 1
        
        return result
    
    async def rollback_transaction(self, transaction_id: str) -> bool:
        """Rollback a transaction"""
        transaction = self.transactions.get(transaction_id)
        if not transaction:
            logger.warning(f"Transaction not found: {transaction_id}")
            return False
        
        result = await transaction.rollback()
        
        if result:
            self.total_rolled_back += 1
            self.active_transactions.discard(transaction_id)
        else:
            self.total_failed += 1
        
        return result
    
    @asynccontextmanager
    async def transaction(
        self,
        isolation_level: IsolationLevel = IsolationLevel.READ_COMMITTED
    ):
        """
        Context manager for transactions.
        
        Usage:
            async with transaction_manager.transaction() as tx:
                # Do work
                tx.add_compensation(...)
        """
        transaction = self.begin_transaction(isolation_level)
        
        try:
            yield transaction
            await transaction.commit()
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            await transaction.rollback()
            raise
        finally:
            self.active_transactions.discard(transaction.transaction_id)
    
    def cleanup_completed_transactions(self, max_age_seconds: int = 3600) -> int:
        """Clean up old completed transactions"""
        now = datetime.utcnow()
        to_remove = []
        
        for tx_id, tx in self.transactions.items():
            if tx.state in (TransactionState.COMMITTED, TransactionState.ROLLED_BACK):
                if tx.end_time:
                    age = (now - tx.end_time).total_seconds()
                    if age > max_age_seconds:
                        to_remove.append(tx_id)
        
        for tx_id in to_remove:
            del self.transactions[tx_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} completed transactions")
        
        return len(to_remove)
    
    def get_statistics(self) -> dict[str, Any]:
        """Get transaction manager statistics"""
        state_counts: dict[str, int] = {}
        for tx in self.transactions.values():
            state = tx.state.value
            state_counts[state] = state_counts.get(state, 0) + 1
        
        return {
            "total_transactions": len(self.transactions),
            "active_transactions": len(self.active_transactions),
            "total_committed": self.total_committed,
            "total_rolled_back": self.total_rolled_back,
            "total_failed": self.total_failed,
            "state_distribution": state_counts
        }
