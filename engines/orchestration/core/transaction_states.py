"""State pattern — transaction state transitions for ITransactionScope."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ._context_protocols import ITransactionScope


class TransactionState(ABC):
    """Base transaction state."""

    @abstractmethod
    async def prepare(self, tx: ITransactionScope) -> bool:
        ...

    @abstractmethod
    async def commit(self, tx: ITransactionScope) -> bool:
        ...

    @abstractmethod
    async def rollback(self, tx: ITransactionScope) -> bool:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...


class ActiveState(TransactionState):
    async def prepare(self, tx: ITransactionScope) -> bool:
        tx._lifecycle_state = PreparingState()
        result = await tx._do_prepare()
        tx._lifecycle_state = PreparedState() if result else FailedState()
        return result

    async def commit(self, tx: ITransactionScope) -> bool:
        return await self.prepare(tx) and await tx._lifecycle_state.commit(tx)

    async def rollback(self, tx: ITransactionScope) -> bool:
        tx._lifecycle_state = RollingBackState()
        result = await tx._do_rollback()
        tx._lifecycle_state = RolledBackState() if result else FailedState()
        return result

    @property
    def name(self) -> str:
        return "active"


class PreparingState(TransactionState):
    async def prepare(self, tx: ITransactionScope) -> bool:
        return await self._transition_from_preparing(tx)

    async def commit(self, tx: ITransactionScope) -> bool:
        raise RuntimeError("Cannot commit while preparing")

    async def rollback(self, tx: ITransactionScope) -> bool:
        return await ActiveState().rollback(tx)

    async def _transition_from_preparing(self, tx: ITransactionScope) -> bool:
        result = await tx._do_prepare()
        tx._lifecycle_state = PreparedState() if result else FailedState()
        return result

    @property
    def name(self) -> str:
        return "preparing"


class PreparedState(TransactionState):
    async def prepare(self, tx: ITransactionScope) -> bool:
        return True

    async def commit(self, tx: ITransactionScope) -> bool:
        tx._lifecycle_state = CommittingState()
        result = await tx._do_commit()
        tx._lifecycle_state = CommittedState() if result else FailedState()
        if result is False:
            await ActiveState().rollback(tx)
        return result

    async def rollback(self, tx: ITransactionScope) -> bool:
        return await ActiveState().rollback(tx)

    @property
    def name(self) -> str:
        return "prepared"


class CommittingState(TransactionState):
    async def prepare(self, tx: ITransactionScope) -> bool:
        raise RuntimeError("Cannot prepare while committing")

    async def commit(self, tx: ITransactionScope) -> bool:
        return True

    async def rollback(self, tx: ITransactionScope) -> bool:
        return await ActiveState().rollback(tx)

    @property
    def name(self) -> str:
        return "committing"


class CommittedState(TransactionState):
    async def prepare(self, tx: ITransactionScope) -> bool:
        raise RuntimeError("Cannot prepare a committed transaction")

    async def commit(self, tx: ITransactionScope) -> bool:
        return True

    async def rollback(self, tx: ITransactionScope) -> bool:
        return False

    @property
    def name(self) -> str:
        return "committed"


class RollingBackState(TransactionState):
    async def prepare(self, tx: ITransactionScope) -> bool:
        raise RuntimeError("Cannot prepare while rolling back")

    async def commit(self, tx: ITransactionScope) -> bool:
        raise RuntimeError("Cannot commit while rolling back")

    async def rollback(self, tx: ITransactionScope) -> bool:
        return True

    @property
    def name(self) -> str:
        return "rolling_back"


class RolledBackState(TransactionState):
    async def prepare(self, tx: ITransactionScope) -> bool:
        raise RuntimeError("Cannot prepare a rolled-back transaction")

    async def commit(self, tx: ITransactionScope) -> bool:
        raise RuntimeError("Cannot commit a rolled-back transaction")

    async def rollback(self, tx: ITransactionScope) -> bool:
        return False

    @property
    def name(self) -> str:
        return "rolled_back"


class FailedState(TransactionState):
    async def prepare(self, tx: ITransactionScope) -> bool:
        tx._lifecycle_state = PreparingState()
        result = await tx._do_prepare()
        tx._lifecycle_state = PreparedState() if result else self
        return result

    async def commit(self, tx: ITransactionScope) -> bool:
        return await ActiveState().rollback(tx)

    async def rollback(self, tx: ITransactionScope) -> bool:
        return await ActiveState().rollback(tx)

    @property
    def name(self) -> str:
        return "failed"
