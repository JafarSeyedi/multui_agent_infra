# agents/orchestration/interaction/strategy_registry.py
from __future__ import annotations

from threading import RLock
from typing import Dict, Generic, Iterable, List, Optional, TypeVar

from .base_strategy import InteractionStrategy

TStrategy = TypeVar("TStrategy", bound=InteractionStrategy)


class InteractionStrategyRegistry(Generic[TStrategy]):
    """
    نگهبان استراتژی‌های تعامل. برای جلوگیری از ثبت همزمان‌ی استراتژی‌های یکسان
    و ارائه‌ی قابلیت‌های کمکی مثل فهرست‌برداری و حذفِ ایمن طراحی شده است.
    """

    def __init__(self) -> None:
        self._strategies: Dict[str, TStrategy] = {}
        self._lock = RLock()

    def register(self, strategy: TStrategy, *, replace: bool = False) -> TStrategy:
        """
        یک استراتژی جدید ثبت می‌کند. در صورت تکراری بودن و
        replace=False خطا می‌دهد؛ در غیر این صورت جایگزین می‌کند.
        """
        scenario = strategy.scenario_name
        with self._lock:
            if scenario in self._strategies and not replace:
                raise ValueError(f"Strategy for scenario '{scenario}' already registered.")
            self._strategies[scenario] = strategy
        return strategy

    def unregister(self, scenario: str) -> None:
        """استراتژی با نام سناریو مشخص را حذف می‌کند (اگر وجود داشت)."""
        with self._lock:
            self._strategies.pop(scenario, None)

    def get(self, scenario: str) -> Optional[TStrategy]:
        """استراتژی را بدون خطا دادن برمی‌گرداند (اگر ثبت شده باشد)."""
        with self._lock:
            return self._strategies.get(scenario)

    def require(self, scenario: str) -> TStrategy:
        """
        استراتژی را برمی‌گرداند یا اگر وجود نداشت، خطای معنی‌داری می‌اندازد.
        برای زمانی که حضور استراتژی الزامی است بسیار مفید است.
        """
        strategy = self.get(scenario)
        if strategy is None:
            raise KeyError(f"No interaction strategy registered for scenario '{scenario}'.")
        return strategy

    def list_scenarios(self) -> List[str]:
        """تمام سناریوهای ثبت‌شده را برمی‌گرداند."""
        with self._lock:
            return list(self._strategies.keys())

    def all_strategies(self) -> Iterable[TStrategy]:
        """دایره‌المعارف همهٔ استراتژی‌ها برای بررسی یا تست."""
        with self._lock:
            return list(self._strategies.values())