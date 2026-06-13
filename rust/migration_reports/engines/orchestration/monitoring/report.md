# Monitoring & Observability — Rust Migration Report

## Files Analyzed
- `__init__.py` (33 lines) — re-exports
- `health_checker.py` (50 lines) — `HealthMonitor`
- `logger.py` (28 lines) — `StructuredLogger`
- `metrics_collector.py` (267 lines) — `MetricsCollector`, `ProcessMetrics`, `ActivityMetrics`
- `performance_monitor.py` (35 lines) — `PerformanceMonitor`
- `process_heatmap.py` (161 lines) — `ProcessHeatmap`, `BottleneckDetection`, `KpiTracker`
- `tracer.py` (69 lines) — `Tracer`, `Span`

## 1. Pre-refactor Patterns

| Pattern | Files | Details |
|---------|-------|---------|
| `Any` | metrics_collector.py:13,230, process_heatmap.py:7, health_checker.py:45 | Dynamic payloads, exception messages |
| `dict[str, Any]` | process_heatmap.py:92, metrics_collector.py:217,230 | Results/bottleneck output |
| `isinstance` | metrics_collector.py:103,110 | Numeric checks in time-series data |
| Global state | None | No mutable module-level state |
| Mutable defaults | None | `field(default_factory=...)` in dataclasses |

## 2. Migration Notes & Rust Score

| File | Lines | Complexity | Rust Score | Notes |
|------|-------|-----------|------------|-------|
| health_checker.py | 50 | Low | 5/5 | Callback registry, simple |
| logger.py | 28 | Low | 5/5 | Struct + builder, trivial |
| metrics_collector.py | 267 | Medium | 4/5 | Dataclass-heavy. Running averages, fault tracking. State mutation pattern. |
| performance_monitor.py | 35 | Low | 4/5 | Context manager → Rust needs `Drop`-based scope guard |
| process_heatmap.py | 161 | Low | 5/5 | Pure computation, no I/O, no eval |
| tracer.py | 69 | Low | 4/5 | Context manager stack → `Drop`-based span lifecycle |

**Overall**: 4.6/5. Mostly pure data transformations and accumulation. No external dependencies. `MetricsCollector` is the most complex but still straightforward.

## 3. Ownership Map

```
MetricsCollector
 ├── HashMap<String, ProcessMetrics>  — per-definition
 ├── HashMap<String, InstanceMetrics> — per-instance
 ├── HashMap<String, HealthCheck>     — per-check
 └── observations: HashMap<String, Vec<f64>>

ProcessMetrics
 ├── activity_metrics: HashMap<String, ActivityMetrics>
 └── running averages, counters

ActivityMetrics
 └── running min/max/avg + failure rate

InstanceMetrics — flat counters

HealthMonitor
 └── HashMap<String, Box<dyn Fn() -> bool>>

PerformanceMonitor — wraps MetricsCollector with timing

ProcessHeatmap — computes heat score from metrics
BottleneckDetection — static bottleneck analysis
KpiTracker — KPI history with thresholds

Tracer — span stack with emit hook
StructuredLogger — event emission
```

## 4. PyO3 Binding Structure

```rust
#[pyclass]
struct MetricsCollector { ... }

#[pyclass]
struct ProcessMetrics { ... }

#[pyclass]
struct ActivityMetrics { ... }

#[pyclass]
struct ProcessHeatmap { ... }

#[pyclass]
struct KpiTracker { ... }

#[pyclass]
struct Tracer { ... }  // context manager via __enter__/__exit__
```

## 5. Libraries Analysis

| Current Python | Rust Equivalent | Notes |
|---------------|----------------|-------|
| `time` | `std::time::Instant` | Perf counters |
| `contextlib.contextmanager` | `Drop` trait | RAII scope guards |
| `datetime` | `chrono` | Timestamps |

**Zero external dependencies required.** All logic is pure math/data.

## 6. Performance Hot Paths

- `ActivityMetrics.record_execution()` — called per activity completion. Simple O(1) arithmetic.
- `MetricsCollector.snapshot()` — O(n) over all observations. Sum/average computation.
- `BottleneckDetection.detect_bottlenecks()` — O(n) over all activity metrics with string formatting.
- `KpiTracker.compute_process_kpis()` — O(1) percentage calculations.
- `ProcessHeatmap.build_heatmap()` — O(n) with sort.

## 7. Error Handling

| Python | Rust Strategy |
|--------|---------------|
| `except Exception: status = unhealthy` | `match check() { Ok(true) => Healthy, Ok(false) => Unhealthy, Err(e) => Unhealthy(e) }` |
| No custom error types | Define `MonitoringError` enum if needed |
| `cast(float, ...)` in type check | `as f64` or `TryFrom` |
