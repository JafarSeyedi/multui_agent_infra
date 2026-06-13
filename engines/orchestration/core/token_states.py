"""State pattern for Token lifecycle.

Each state encapsulates valid transitions for a Token,
replacing the enum + conditional guard pattern.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .token import Token

logger = logging.getLogger(__name__)


class TokenState(ABC):
    """Base class for token states."""

    @abstractmethod
    def wait(self, token: Token, reason: str) -> None: ...
    @abstractmethod
    def resume(self, token: Token) -> None: ...
    @abstractmethod
    def complete(self, token: Token) -> None: ...
    @abstractmethod
    def terminate(self, token: Token) -> None: ...
    @abstractmethod
    def merge(self, token: Token) -> None: ...


class _ActiveTokenState(TokenState):
    def wait(self, token: Token, reason: str) -> None:
        from .token import TokenStateEnum
        token.set_state(TokenStateEnum.WAITING, _WaitingTokenState())
        import datetime
        token.waiting_for = reason
        token.wait_start_time = datetime.datetime.utcnow()
        token.updated_at = datetime.datetime.utcnow()
        logger.debug("Token %s waiting: %s", token.token_id, reason)

    def resume(self, token: Token) -> None:
        logger.warning("Token %s not in waiting state", token.token_id)

    def complete(self, token: Token) -> None:
        from .token import TokenStateEnum
        token.set_state(TokenStateEnum.COMPLETED, _CompletedTokenState())
        import datetime
        token.completed_at = datetime.datetime.utcnow()
        token.updated_at = datetime.datetime.utcnow()
        logger.debug("Token %s completed", token.token_id)

    def terminate(self, token: Token) -> None:
        from .token import TokenStateEnum
        token.set_state(TokenStateEnum.TERMINATED, _TerminatedTokenState())
        import datetime
        token.completed_at = datetime.datetime.utcnow()
        token.updated_at = datetime.datetime.utcnow()
        logger.debug("Token %s terminated", token.token_id)

    def merge(self, token: Token) -> None:
        from .token import TokenStateEnum
        token.set_state(TokenStateEnum.MERGED, _MergedTokenState())
        import datetime
        token.completed_at = datetime.datetime.utcnow()
        token.updated_at = datetime.datetime.utcnow()
        logger.debug("Token %s merged", token.token_id)


class _WaitingTokenState(TokenState):
    def wait(self, token: Token, reason: str) -> None:
        logger.warning("Token %s already waiting", token.token_id)

    def resume(self, token: Token) -> None:
        from .token import TokenStateEnum
        token.set_state(TokenStateEnum.ACTIVE, _ActiveTokenState())
        token.waiting_for = None
        token.wait_start_time = None
        import datetime
        token.updated_at = datetime.datetime.utcnow()
        logger.debug("Token %s resumed", token.token_id)

    def complete(self, token: Token) -> None:
        from .token import TokenStateEnum
        token.set_state(TokenStateEnum.COMPLETED, _CompletedTokenState())
        import datetime
        token.completed_at = datetime.datetime.utcnow()
        token.updated_at = datetime.datetime.utcnow()
        logger.debug("Token %s completed (from waiting)", token.token_id)

    def terminate(self, token: Token) -> None:
        from .token import TokenStateEnum
        token.set_state(TokenStateEnum.TERMINATED, _TerminatedTokenState())
        import datetime
        token.completed_at = datetime.datetime.utcnow()
        token.updated_at = datetime.datetime.utcnow()
        logger.debug("Token %s terminated (from waiting)", token.token_id)

    def merge(self, token: Token) -> None:
        from .token import TokenStateEnum
        token.set_state(TokenStateEnum.MERGED, _MergedTokenState())
        import datetime
        token.completed_at = datetime.datetime.utcnow()
        token.updated_at = datetime.datetime.utcnow()
        logger.debug("Token %s merged (from waiting)", token.token_id)


class _CompletedTokenState(TokenState):
    def wait(self, token: Token, reason: str) -> None:
        raise RuntimeError(f"Cannot wait on completed token {token.token_id}")

    def resume(self, token: Token) -> None:
        raise RuntimeError(f"Cannot resume completed token {token.token_id}")

    def complete(self, token: Token) -> None:
        logger.warning("Token %s already completed", token.token_id)

    def terminate(self, token: Token) -> None:
        raise RuntimeError(f"Cannot terminate completed token {token.token_id}")

    def merge(self, token: Token) -> None:
        raise RuntimeError(f"Cannot merge completed token {token.token_id}")


class _TerminatedTokenState(TokenState):
    def wait(self, token: Token, reason: str) -> None:
        raise RuntimeError(f"Cannot wait on terminated token {token.token_id}")

    def resume(self, token: Token) -> None:
        raise RuntimeError(f"Cannot resume terminated token {token.token_id}")

    def complete(self, token: Token) -> None:
        raise RuntimeError(f"Cannot complete terminated token {token.token_id}")

    def terminate(self, token: Token) -> None:
        logger.warning("Token %s already terminated", token.token_id)

    def merge(self, token: Token) -> None:
        raise RuntimeError(f"Cannot merge terminated token {token.token_id}")


class _MergedTokenState(TokenState):
    def wait(self, token: Token, reason: str) -> None:
        raise RuntimeError(f"Cannot wait on merged token {token.token_id}")

    def resume(self, token: Token) -> None:
        raise RuntimeError(f"Cannot resume merged token {token.token_id}")

    def complete(self, token: Token) -> None:
        raise RuntimeError(f"Cannot complete merged token {token.token_id}")

    def terminate(self, token: Token) -> None:
        raise RuntimeError(f"Cannot terminate merged token {token.token_id}")

    def merge(self, token: Token) -> None:
        logger.warning("Token %s already merged", token.token_id)


# State registry
_STATE_MAP: dict[str, TokenState] = {}

def token_state_for(enum_value: str) -> TokenState:
    """Get the token state instance for a given TokenStateEnum value."""
    global _STATE_MAP
    if not _STATE_MAP:
        from .token import TokenStateEnum
        _STATE_MAP = {
            TokenStateEnum.ACTIVE.value: _ActiveTokenState(),
            TokenStateEnum.WAITING.value: _WaitingTokenState(),
            TokenStateEnum.COMPLETED.value: _CompletedTokenState(),
            TokenStateEnum.TERMINATED.value: _TerminatedTokenState(),
            TokenStateEnum.MERGED.value: _MergedTokenState(),
        }
    return _STATE_MAP[enum_value]
