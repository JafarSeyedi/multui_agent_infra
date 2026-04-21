# engines/document/ingestion/utils/timing.py

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Optional


@contextmanager
def time_block(label: str):
    """
    Usage:
        with time_block("fetching"):
            fetch_data()
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        end = time.perf_counter()
        duration = (end - start) * 1000.0
        print(f"[timing] {label}: {duration:.2f} ms")


class Stopwatch:
    """
    Programmatic stopwatch for more complex pipelines.
    """

    def __init__(self) -> None:
        self.start_time: Optional[float] = None
        self.elapsed_ms: float = 0.0

    def start(self):
        self.start_time = time.perf_counter()

    def stop(self):
        if self.start_time is not None:
            self.elapsed_ms += (time.perf_counter() - self.start_time) * 1000.0
            self.start_time = None

    def reset(self):
        self.start_time = None
        self.elapsed_ms = 0.0

    def read(self) -> float:
        return self.elapsed_ms
