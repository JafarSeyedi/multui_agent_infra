from __future__ import annotations

from typing import Any, Generic, TypeVar

T = TypeVar("T")


class RingBuffer(Generic[T]):
    def __init__(self, capacity: int = 100000) -> None:
        if capacity <= 0:
            raise ValueError(f"RingBuffer capacity must be > 0, got {capacity}")
        self._capacity = capacity
        self._buffer: list[T] = []
        self._head = 0

    def push(self, item: T) -> None:
        if len(self._buffer) < self._capacity:
            self._buffer.append(item)
        else:
            self._buffer[self._head] = item
            self._head = (self._head + 1) % self._capacity

    def get_all(self) -> list[T]:
        if len(self._buffer) < self._capacity:
            return list(self._buffer)
        return self._buffer[self._head:] + self._buffer[:self._head]

    def clear(self) -> None:
        self._buffer.clear()
        self._head = 0

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def size(self) -> int:
        return len(self._buffer)
