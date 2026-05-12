"""
Token-based Execution Tracking

Implements token-based execution semantics for BPMN and other flow-based
orchestration standards. Tokens represent execution flow through the process.
"""

import logging
from datetime import datetime
from typing import Any, Set
from enum import Enum
from dataclasses import dataclass, field
from uuid import uuid4


logger = logging.getLogger(__name__)


class TokenState(Enum):
    """Token states"""
    ACTIVE = "active"  # Token is active and can move
    WAITING = "waiting"  # Token is waiting (e.g., at gateway)
    COMPLETED = "completed"  # Token reached end event
    TERMINATED = "terminated"  # Token was terminated
    MERGED = "merged"  # Token was merged with another


class TokenType(Enum):
    """Token types"""
    PROCESS = "process"  # Main process token
    SUBPROCESS = "subprocess"  # Subprocess token
    PARALLEL = "parallel"  # Parallel execution token
    EVENT = "event"  # Event-triggered token
    COMPENSATION = "compensation"  # Compensation token


@dataclass
class TokenSnapshot:
    """Snapshot of token state at a point in time"""
    timestamp: datetime
    element_id: str
    element_type: str
    state: TokenState
    variables: dict[str, Any]


class Token:
    """
    Represents an execution token in a process.
    
    Tokens move through the process following sequence flows, splitting
    at parallel gateways and merging at join points.
    """
    
    def __init__(
        self,
        token_id: str,
        instance_id: str,
        parent_token_id: str | None = None,
        token_type: TokenType = TokenType.PROCESS,
        current_element_id: str | None = None
    ) -> None:
        self.token_id = token_id
        self.instance_id = instance_id
        self.parent_token_id = parent_token_id
        self.token_type = token_type
        self.state = TokenState.ACTIVE
        
        # Position tracking
        self.current_element_id = current_element_id
        self.current_element_type: str | None = None
        self.previous_element_id: str | None = None
        
        # Timing
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.completed_at: datetime | None = None
        
        # Execution history
        self.execution_path: list[str] = []
        self.snapshots: list[TokenSnapshot] = []
        
        # Child tokens (for parallel execution)
        self.child_token_ids: list[str] = []
        
        # Metadata
        self.metadata: dict[str, Any] = {}
        
        # Waiting state
        self.waiting_for: str | None = None  # What the token is waiting for
        self.wait_start_time: datetime | None = None
        
        logger.debug(f"Created token: {token_id} for instance {instance_id}")
    
    def move_to(self, element_id: str, element_type: str) -> None:
        """Move token to a new element"""
        self.previous_element_id = self.current_element_id
        self.current_element_id = element_id
        self.current_element_type = element_type
        self.updated_at = datetime.utcnow()
        
        # Track execution path
        if element_id not in self.execution_path:
            self.execution_path.append(element_id)
        
        logger.debug(f"Token {self.token_id} moved to {element_id} ({element_type})")
    
    def wait(self, reason: str) -> None:
        """Put token in waiting state"""
        self.state = TokenState.WAITING
        self.waiting_for = reason
        self.wait_start_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        logger.debug(f"Token {self.token_id} waiting: {reason}")
    
    def resume(self) -> None:
        """Resume token from waiting state"""
        if self.state != TokenState.WAITING:
            logger.warning(f"Token {self.token_id} not in waiting state")
            return
        
        self.state = TokenState.ACTIVE
        self.waiting_for = None
        self.wait_start_time = None
        self.updated_at = datetime.utcnow()
        
        logger.debug(f"Token {self.token_id} resumed")
    
    def complete(self) -> None:
        """Mark token as completed"""
        self.state = TokenState.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        logger.debug(f"Token {self.token_id} completed")
    
    def terminate(self) -> None:
        """Terminate the token"""
        self.state = TokenState.TERMINATED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        logger.debug(f"Token {self.token_id} terminated")
    
    def merge(self) -> None:
        """Mark token as merged"""
        self.state = TokenState.MERGED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        logger.debug(f"Token {self.token_id} merged")
    
    def add_child_token(self, child_token_id: str) -> None:
        """Add a child token (for parallel execution)"""
        if child_token_id not in self.child_token_ids:
            self.child_token_ids.append(child_token_id)
    
    def create_snapshot(self, variables: dict[str, Any] | None = None) -> TokenSnapshot:
        """Create a snapshot of current token state"""
        snapshot = TokenSnapshot(
            timestamp=datetime.utcnow(),
            element_id=self.current_element_id or "",
            element_type=self.current_element_type or "",
            state=self.state,
            variables=variables or {}
        )
        
        self.snapshots.append(snapshot)
        return snapshot
    
    def get_wait_duration_ms(self) -> int | None:
        """Get duration of current wait in milliseconds"""
        if self.wait_start_time:
            delta = datetime.utcnow() - self.wait_start_time
            return int(delta.total_seconds() * 1000)
        return None
    
    def get_lifetime_ms(self) -> int:
        """Get token lifetime in milliseconds"""
        end_time = self.completed_at or datetime.utcnow()
        delta = end_time - self.created_at
        return int(delta.total_seconds() * 1000)
    
    def is_active(self) -> bool:
        """Check if token is active"""
        return self.state == TokenState.ACTIVE
    
    def is_waiting(self) -> bool:
        """Check if token is waiting"""
        return self.state == TokenState.WAITING
    
    def is_completed(self) -> bool:
        """Check if token is completed"""
        return self.state in (TokenState.COMPLETED, TokenState.TERMINATED, TokenState.MERGED)
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value"""
        return self.metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata value"""
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> dict[str, Any]:
        """Convert token to dictionary representation"""
        return {
            "token_id": self.token_id,
            "instance_id": self.instance_id,
            "parent_token_id": self.parent_token_id,
            "token_type": self.token_type.value,
            "state": self.state.value,
            "current_element_id": self.current_element_id,
            "current_element_type": self.current_element_type,
            "previous_element_id": self.previous_element_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "execution_path": self.execution_path,
            "child_tokens": len(self.child_token_ids),
            "waiting_for": self.waiting_for,
            "wait_duration_ms": self.get_wait_duration_ms(),
            "lifetime_ms": self.get_lifetime_ms(),
            "metadata": self.metadata
        }
    
    def __repr__(self) -> str:
        return (
            f"Token(id={self.token_id}, instance={self.instance_id}, "
            f"state={self.state.value}, element={self.current_element_id})"
        )


class TokenManager:
    """
    Manages tokens across process instances.
    
    Handles token creation, lifecycle, splitting, and merging.
    """
    
    def __init__(self) -> None:
        self.tokens: dict[str, Token] = {}
        self.instance_tokens: dict[str, Set[str]] = {}  # instance_id -> token_ids
        self.element_tokens: dict[str, Set[str]] = {}  # element_id -> token_ids
    
    def create_token(
        self,
        instance_id: str,
        parent_token_id: str | None = None,
        token_type: TokenType = TokenType.PROCESS,
        current_element_id: str | None = None,
        token_id: str | None = None
    ) -> Token:
        """Create a new token"""
        if token_id is None:
            token_id = str(uuid4())
        
        token = Token(
            token_id=token_id,
            instance_id=instance_id,
            parent_token_id=parent_token_id,
            token_type=token_type,
            current_element_id=current_element_id
        )
        
        self.tokens[token_id] = token
        
        # Update indexes
        if instance_id not in self.instance_tokens:
            self.instance_tokens[instance_id] = set()
        self.instance_tokens[instance_id].add(token_id)
        
        if current_element_id:
            if current_element_id not in self.element_tokens:
                self.element_tokens[current_element_id] = set()
            self.element_tokens[current_element_id].add(token_id)
        
        # Register with parent token
        if parent_token_id:
            parent = self.tokens.get(parent_token_id)
            if parent:
                parent.add_child_token(token_id)
        
        logger.info(f"Created token {token_id} for instance {instance_id}")
        return token
    
    def get_token(self, token_id: str) -> Token | None:
        """Get a token by ID"""
        return self.tokens.get(token_id)
    
    def remove_token(self, token_id: str) -> bool:
        """Remove a token"""
        token = self.tokens.pop(token_id, None)
        if not token:
            return False
        
        # Update indexes
        if token.instance_id in self.instance_tokens:
            self.instance_tokens[token.instance_id].discard(token_id)
        
        if token.current_element_id and token.current_element_id in self.element_tokens:
            self.element_tokens[token.current_element_id].discard(token_id)
        
        return True
    
    def get_instance_tokens(self, instance_id: str) -> list[Token]:
        """Get all tokens for an instance"""
        token_ids = self.instance_tokens.get(instance_id, set())
        return [self.tokens[tid] for tid in token_ids if tid in self.tokens]
    
    def get_active_tokens(self, instance_id: str) -> list[Token]:
        """Get active tokens for an instance"""
        return [
            token for token in self.get_instance_tokens(instance_id)
            if token.is_active()
        ]
    
    def get_waiting_tokens(self, instance_id: str) -> list[Token]:
        """Get waiting tokens for an instance"""
        return [
            token for token in self.get_instance_tokens(instance_id)
            if token.is_waiting()
        ]
    
    def get_element_tokens(self, element_id: str) -> list[Token]:
        """Get all tokens at a specific element"""
        token_ids = self.element_tokens.get(element_id, set())
        return [self.tokens[tid] for tid in token_ids if tid in self.tokens]
    
    def split_token(
        self,
        parent_token_id: str,
        target_elements: list[str],
        token_type: TokenType = TokenType.PARALLEL
    ) -> list[Token]:
        """
        Split a token into multiple child tokens (for parallel gateways).
        
        Args:
            parent_token_id: ID of the token to split
            target_elements: list of element IDs for child tokens
            token_type: Type for child tokens
        
        Returns:
            list of created child tokens
        """
        parent_token = self.tokens.get(parent_token_id)
        if not parent_token:
            raise ValueError(f"Parent token not found: {parent_token_id}")
        
        # Create child tokens
        child_tokens = []
        for element_id in target_elements:
            child_token = self.create_token(
                instance_id=parent_token.instance_id,
                parent_token_id=parent_token_id,
                token_type=token_type,
                current_element_id=element_id
            )
            child_tokens.append(child_token)
        
        # Mark parent as waiting for children
        parent_token.wait(f"split_into_{len(child_tokens)}_tokens")
        
        logger.info(f"Split token {parent_token_id} into {len(child_tokens)} child tokens")
        return child_tokens
    
    def merge_tokens(
        self,
        token_ids: list[str],
        target_element_id: str,
        create_new_token: bool = True
    ) -> Token | None:
        """
        Merge multiple tokens into one (for join gateways).
        
        Args:
            token_ids: IDs of tokens to merge
            target_element_id: Element ID for merged token
            create_new_token: Whether to create a new token or reuse first
        
        Returns:
            Merged token or None
        """
        tokens = [self.tokens.get(tid) for tid in token_ids]
        tokens = [t for t in tokens if t is not None]
        
        if not tokens or len(tokens)==0 or tokens[0] is None:
            return None
        
        # Get instance ID from first token
        instance_id = tokens[0].instance_id
        
        # Mark all tokens as merged
        for token in tokens:
            if token is not None:
                token.merge()
        
        # Create or reuse token
        if create_new_token:
            merged_token = self.create_token(
                instance_id=instance_id,
                token_type=TokenType.PROCESS,
                current_element_id=target_element_id
            )
        elif tokens[0] is not None:
            merged_token = tokens[0]
            merged_token.state = TokenState.ACTIVE
            merged_token.move_to(target_element_id, "merged")
        
        logger.info(f"Merged {len(tokens)} tokens into {merged_token.token_id}")
        return merged_token
    
    def cleanup_completed_tokens(self, instance_id: str) -> int:
        """Clean up completed tokens for an instance"""
        tokens = self.get_instance_tokens(instance_id)
        completed = [t for t in tokens if t.is_completed()]
        
        for token in completed:
            self.remove_token(token.token_id)
        
        return len(completed)
    
    def get_statistics(self) -> dict[str, Any]:
        """Get token manager statistics"""
        state_counts: dict[str, int] = {}
        type_counts: dict[str, int] = {}
        
        for token in self.tokens.values():
            state = token.state.value
            state_counts[state] = state_counts.get(state, 0) + 1
            
            token_type = token.token_type.value
            type_counts[token_type] = type_counts.get(token_type, 0) + 1
        
        return {
            "total_tokens": len(self.tokens),
            "state_distribution": state_counts,
            "type_distribution": type_counts,
            "instances_with_tokens": len(self.instance_tokens),
            "elements_with_tokens": len(self.element_tokens)
        }
