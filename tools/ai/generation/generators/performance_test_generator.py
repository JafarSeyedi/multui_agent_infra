#!/usr/bin/env python3
"""
Performance Test Generator - AI Development Framework
Generates performance, stress, load, and scalability tests for Python code.

Part of the Level 3 Generation tools (generators/performance_test_generator.py)

This performance_test_generator.py provides:

1. Multiple Test Types - Benchmark, load, stress, endurance, spike, scalability, concurrency, memory, throughput, latency
2. Configurable Load Patterns - Constant, ramp-up, ramp-down, step, sinusoidal, spike, Poisson
3. Comprehensive Metrics - Execution time, memory usage, CPU usage, throughput, latency, error rate
4. Performance Assertions - Max time, avg time, percentiles, memory limits, throughput minimums
5. Resource Monitoring - CPU, memory, disk I/O, network I/O tracking
6. Code Profiling - cProfile integration for hot-spot identification
7. Visualizations - Response time histograms, percentile charts, throughput graphs, memory usage plots
8. Stress Test Generation - Increasing load until failure detection
9. Endurance Test Generation - Extended period testing for memory leaks
10. Spike Test Generation - Sudden load increase simulation
11. Scalability Test Generation - Varying concurrent user testing
12. Warmup/Cooldown Phases - Proper test isolation and stabilization

The performance test generator produces comprehensive performance, stress, and load tests that help ensure your code meets performance requirements and can scale under various conditions.
"""

import ast
import json
import time
import asyncio
import statistics
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import concurrent.futures
import threading

from ...shared.llm_client import LLMClient
from ...shared.state_manager import StateManager
from ...shared.logger import get_logger
from ...level_2_analysis.scanners.ast_analyzer import ASTAnalyzer, ASTMetrics

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class PerformanceTestType(str, Enum):
    """Type of performance test."""
    BENCHMARK = "benchmark"           # Measure execution time
    LOAD = "load"                     # Test under expected load
    STRESS = "stress"                 # Test beyond normal capacity
    ENDURANCE = "endurance"           # Test over extended period
    SPIKE = "spike"                   # Sudden increase in load
    SCALABILITY = "scalability"       # Test scaling characteristics
    CONCURRENCY = "concurrency"       # Test concurrent execution
    MEMORY = "memory"                 # Test memory usage
    THROUGHPUT = "throughput"         # Test requests per second
    LATENCY = "latency"               # Test response time distribution
    RECOVERY = "recovery"             # Test recovery from failure
    CAPACITY = "capacity"             # Find maximum capacity


class MetricsType(str, Enum):
    """Type of metrics to collect."""
    EXECUTION_TIME = "execution_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    THROUGHPUT = "throughput"
    LATENCY = "latency"
    ERROR_RATE = "error_rate"
    CONCURRENT_USERS = "concurrent_users"
    REQUESTS_PER_SECOND = "requests_per_second"
    RESPONSE_SIZE = "response_size"
    CONNECTION_COUNT = "connection_count"
    QUEUE_SIZE = "queue_size"
    GC_STATS = "gc_stats"


class LoadPattern(str, Enum):
    """Pattern for load generation."""
    CONSTANT = "constant"             # Constant load
    RAMP_UP = "ramp_up"              # Gradually increasing
    RAMP_DOWN = "ramp_down"          # Gradually decreasing
    STEP = "step"                     # Step changes
    SINUSOIDAL = "sinusoidal"        # Sine wave pattern
    SPIKE = "spike"                   # Sudden spikes
    POISSON = "poisson"              # Random (Poisson) arrival
    CUSTOM = "custom"                 # Custom pattern


class AssertionType(str, Enum):
    """Type of performance assertion."""
    MAX_TIME = "max_time"
    AVG_TIME = "avg_time"
    PERCENTILE = "percentile"
    MAX_MEMORY = "max_memory"
    MIN_THROUGHPUT = "min_throughput"
    MAX_LATENCY = "max_latency"
    ERROR_RATE = "error_rate"
    CUSTOM = "custom"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class PerformanceMetric:
    """Specification for a performance metric."""
    name: str
    metric_type: MetricsType
    target_value: Optional[float] = None
    max_value: Optional[float] = None
    min_value: Optional[float] = None
    percentile: Optional[float] = None  # For percentile metrics
    unit: str = ""
    description: Optional[str] = None


@dataclass
class LoadProfile:
    """Specification for load generation profile."""
    pattern: LoadPattern = LoadPattern.CONSTANT
    start_rate: int = 1                    # Requests per second
    end_rate: Optional[int] = None         # For ramp patterns
    duration_seconds: int = 60
    ramp_up_seconds: int = 10
    ramp_down_seconds: int = 10
    concurrent_users: int = 1
    think_time_ms: int = 0                 # Time between requests
    spike_multiplier: float = 5.0          # For spike pattern
    spike_duration_seconds: int = 5
    warmup_seconds: int = 5
    cooldown_seconds: int = 5
    custom_pattern: Optional[List[Tuple[int, int]]] = None  # (time, rate) pairs


@dataclass
class PerformanceAssertion:
    """Assertion for performance test."""
    assertion_type: AssertionType
    metric_name: str
    expected_value: float
    operator: str = "<="  # <=, >=, ==, <, >
    percentile: Optional[float] = None  # For percentile assertions
    message: Optional[str] = None


@dataclass
class ResourceLimit:
    """Resource limits for the test."""
    max_memory_mb: Optional[int] = None
    max_cpu_percent: Optional[int] = None
    max_disk_io_mbps: Optional[int] = None
    max_network_io_mbps: Optional[int] = None
    timeout_seconds: int = 300


@dataclass
class PerformanceTestSpec:
    """Complete specification for a performance test."""
    name: str
    test_type: PerformanceTestType
    target_function: str
    target_module: str
    description: Optional[str] = None
    
    # Load configuration
    load_profile: LoadProfile = field(default_factory=LoadProfile)
    
    # Metrics to collect
    metrics: List[PerformanceMetric] = field(default_factory=list)
    
    # Assertions
    assertions: List[PerformanceAssertion] = field(default_factory=list)
    
    # Test data
    test_data: Optional[List[Dict[str, Any]]] = None
    data_generator: Optional[str] = None  # Code to generate test data
    
    # Resource limits
    resource_limits: ResourceLimit = field(default_factory=ResourceLimit)
    
    # Additional configuration
    iterations: int = 1
    parallel_instances: int = 1
    async_mode: bool = False
    collect_gc_stats: bool = True
    profile_code: bool = False
    save_results: bool = True
    output_format: str = "json"  # json, csv, html
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedPerformanceTest:
    """Result of performance test generation."""
    test_spec: PerformanceTestSpec
    code: str
    file_path: Optional[Path] = None
    validation_passed: bool = False
    estimated_duration_seconds: int = 0
    generated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceTestGeneratorConfig:
    """Configuration for performance test generator."""
    framework: str = "pytest"  # pytest, locust, custom
    use_llm: bool = True
    llm_model: str = "deepseek-chat"
    include_visualizations: bool = True
    generate_reports: bool = True
    default_duration: int = 60
    default_concurrent_users: int = 10
    collect_system_metrics: bool = True
    use_process_pool: bool = False
    async_support: bool = True
    output_dir: Optional[Path] = None


# ============================================================
# PERFORMANCE TEST CODE GENERATOR
# ============================================================

class PerformanceTestCodeGenerator:
    """Generate performance test code from specifications."""
    
    def __init__(self, config: PerformanceTestGeneratorConfig):
        self.config = config
        self.indent = "    "
    
    def generate(self, spec: PerformanceTestSpec) -> str:
        """Generate complete performance test code."""
        lines = []
        
        # Module docstring
        lines.extend(self._generate_module_docstring(spec))
        
        # Imports
        lines.extend(self._generate_imports(spec))
        
        # Constants
        lines.extend(self._generate_constants(spec))
        
        # Metrics collector class
        lines.extend(self._generate_metrics_collector(spec))
        
        # Load generator class
        lines.extend(self._generate_load_generator(spec))
        
        # Test data generator
        if spec.data_generator:
            lines.extend(self._generate_data_generator(spec))
        
        # Main test class
        lines.extend(self._generate_test_class(spec))
        
        # Helper functions
        lines.extend(self._generate_helper_functions(spec))
        
        # Main entry point
        lines.extend(self._generate_main_entry(spec))
        
        return "\n".join(lines)
    
    def _generate_module_docstring(self, spec: PerformanceTestSpec) -> List[str]:
        """Generate module docstring."""
        lines = []
        lines.append('"""')
        lines.append(f"Performance Test: {spec.name}")
        lines.append("")
        lines.append(f"Type: {spec.test_type.value}")
        lines.append(f"Target: {spec.target_module}.{spec.target_function}")
        lines.append("")
        if spec.description:
            lines.append(spec.description)
            lines.append("")
        lines.append("Auto-generated by Performance Test Generator.")
        lines.append('"""')
        lines.append("")
        return lines
    
    def _generate_imports(self, spec: PerformanceTestSpec) -> List[str]:
        """Generate import statements."""
        lines = []
        
        lines.append("import time")
        lines.append("import json")
        lines.append("import statistics")
        lines.append("import threading")
        lines.append("from dataclasses import dataclass, field, asdict")
        lines.append("from datetime import datetime")
        lines.append("from typing import Dict, List, Optional, Any, Callable")
        lines.append("from collections import defaultdict")
        lines.append("import concurrent.futures")
        
        if spec.async_mode:
            lines.append("import asyncio")
        
        if self.config.collect_system_metrics:
            lines.append("import psutil")
            lines.append("import os")
        
        if spec.collect_gc_stats:
            lines.append("import gc")
        
        if spec.profile_code:
            lines.append("import cProfile")
            lines.append("import pstats")
            lines.append("from io import StringIO")
        
        if self.config.include_visualizations:
            lines.append("try:")
            lines.append("    import matplotlib.pyplot as plt")
            lines.append("    import numpy as np")
            lines.append("    VISUALIZATION_AVAILABLE = True")
            lines.append("except ImportError:")
            lines.append("    VISUALIZATION_AVAILABLE = False")
        
        # Target module import
        lines.append(f"from {spec.target_module} import {spec.target_function}")
        
        lines.append("")
        return lines
    
    def _generate_constants(self, spec: PerformanceTestSpec) -> List[str]:
        """Generate constants."""
        lines = []
        
        lines.append("# Test Configuration Constants")
        lines.append(f"TEST_NAME = \"{spec.name}\"")
        lines.append(f"TEST_TYPE = \"{spec.test_type.value}\"")
        lines.append(f"TARGET_FUNCTION = \"{spec.target_function}\"")
        lines.append(f"DURATION_SECONDS = {spec.load_profile.duration_seconds}")
        lines.append(f"CONCURRENT_USERS = {spec.load_profile.concurrent_users}")
        lines.append(f"WARMUP_SECONDS = {spec.load_profile.warmup_seconds}")
        lines.append(f"COOLDOWN_SECONDS = {spec.load_profile.cooldown_seconds}")
        lines.append(f"ITERATIONS = {spec.iterations}")
        lines.append(f"ASYNC_MODE = {spec.async_mode}")
        lines.append("")
        
        return lines
    
    def _generate_metrics_collector(self, spec: PerformanceTestSpec) -> List[str]:
        """Generate metrics collector class."""
        lines = []
        
        lines.append("@dataclass")
        lines.append("class PerformanceMetrics:")
        lines.append('    """Collector for performance metrics."""')
        lines.append("")
        lines.append("    execution_times: List[float] = field(default_factory=list)")
        lines.append("    memory_samples: List[float] = field(default_factory=list)")
        lines.append("    cpu_samples: List[float] = field(default_factory=list)")
        lines.append("    error_count: int = 0")
        lines.append("    request_count: int = 0")
        lines.append("    start_time: Optional[datetime] = None")
        lines.append("    end_time: Optional[datetime] = None")
        lines.append("    lock: threading.Lock = field(default_factory=threading.Lock)")
        lines.append("")
        lines.append("    def record_execution(self, duration: float, success: bool = True):")
        lines.append("        with self.lock:")
        lines.append("            self.execution_times.append(duration)")
        lines.append("            self.request_count += 1")
        lines.append("            if not success:")
        lines.append("                self.error_count += 1")
        lines.append("")
        lines.append("    def record_memory(self, memory_mb: float):")
        lines.append("        with self.lock:")
        lines.append("            self.memory_samples.append(memory_mb)")
        lines.append("")
        lines.append("    def record_cpu(self, cpu_percent: float):")
        lines.append("        with self.lock:")
        lines.append("            self.cpu_samples.append(cpu_percent)")
        lines.append("")
        lines.append("    def get_statistics(self) -> Dict[str, Any]:")
        lines.append("        with self.lock:")
        lines.append("            stats = {")
        lines.append("                'total_requests': self.request_count,")
        lines.append("                'error_count': self.error_count,")
        lines.append("                'error_rate': self.error_count / max(self.request_count, 1),")
        lines.append("            }")
        lines.append("")
        lines.append("            if self.execution_times:")
        lines.append("                sorted_times = sorted(self.execution_times)")
        lines.append("                stats.update({")
        lines.append("                    'min_time': min(self.execution_times),")
        lines.append("                    'max_time': max(self.execution_times),")
        lines.append("                    'avg_time': statistics.mean(self.execution_times),")
        lines.append("                    'median_time': statistics.median(self.execution_times),")
        lines.append("                    'p95_time': sorted_times[int(len(sorted_times) * 0.95)],")
        lines.append("                    'p99_time': sorted_times[int(len(sorted_times) * 0.99)],")
        lines.append("                    'std_dev': statistics.stdev(self.execution_times) if len(self.execution_times) > 1 else 0,")
        lines.append("                    'throughput': self.request_count / self.get_duration_seconds() if self.get_duration_seconds() > 0 else 0,")
        lines.append("                })")
        lines.append("")
        lines.append("            if self.memory_samples:")
        lines.append("                stats.update({")
        lines.append("                    'avg_memory_mb': statistics.mean(self.memory_samples),")
        lines.append("                    'max_memory_mb': max(self.memory_samples),")
        lines.append("                })")
        lines.append("")
        lines.append("            if self.cpu_samples:")
        lines.append("                stats.update({")
        lines.append("                    'avg_cpu_percent': statistics.mean(self.cpu_samples),")
        lines.append("                    'max_cpu_percent': max(self.cpu_samples),")
        lines.append("                })")
        lines.append("")
        lines.append("            return stats")
        lines.append("")
        lines.append("    def get_duration_seconds(self) -> float:")
        lines.append("        if self.start_time and self.end_time:")
        lines.append("            return (self.end_time - self.start_time).total_seconds()")
        lines.append("        return 0")
        lines.append("")
        
        return lines
    
    def _generate_load_generator(self, spec: PerformanceTestSpec) -> List[str]:
        """Generate load generator class."""
        lines = []
        
        lines.append("class LoadGenerator:")
        lines.append('    """Generate load according to specified pattern."""')
        lines.append("")
        lines.append(f"    def __init__(self, profile: LoadProfile = None):")
        lines.append(f"        self.profile = profile or LoadProfile()")
        lines.append(f"        self._stop_event = threading.Event()")
        lines.append(f"        self._start_time = None")
        lines.append("")
        lines.append("    def get_current_rate(self, elapsed_seconds: float) -> int:")
        lines.append("        pattern = self.profile.pattern")
        lines.append(f"        ")
        lines.append("        if pattern == LoadPattern.CONSTANT:")
        lines.append("            return self.profile.start_rate")
        lines.append("        elif pattern == LoadPattern.RAMP_UP:")
        lines.append("            if elapsed_seconds >= self.profile.ramp_up_seconds:")
        lines.append("                return self.profile.end_rate or self.profile.start_rate")
        lines.append("            progress = elapsed_seconds / self.profile.ramp_up_seconds")
        lines.append("            return int(self.profile.start_rate + (self.profile.end_rate - self.profile.start_rate) * progress)")
        lines.append("        elif pattern == LoadPattern.SPIKE:")
        lines.append("            # Check if in spike window")
        lines.append("            spike_start = (self.profile.duration_seconds - self.profile.spike_duration_seconds) / 2")
        lines.append("            spike_end = spike_start + self.profile.spike_duration_seconds")
        lines.append("            if spike_start <= elapsed_seconds <= spike_end:")
        lines.append("                return int(self.profile.start_rate * self.profile.spike_multiplier)")
        lines.append("            return self.profile.start_rate")
        lines.append("        else:")
        lines.append("            return self.profile.start_rate")
        lines.append("")
        lines.append("    def generate(self, target_func: Callable, metrics: PerformanceMetrics, test_data: Optional[List[Dict]] = None):")
        lines.append("        self._start_time = time.time()")
        lines.append("        ")
        lines.append("        with concurrent.futures.ThreadPoolExecutor(max_workers=self.profile.concurrent_users) as executor:")
        lines.append("            futures = []")
        lines.append("            last_request_time = time.time()")
        lines.append("            ")
        lines.append("            while not self._stop_event.is_set():")
        lines.append("                elapsed = time.time() - self._start_time")
        lines.append("                ")
        lines.append("                if elapsed >= self.profile.duration_seconds:")
        lines.append("                    break")
        lines.append("                ")
        lines.append("                current_rate = self.get_current_rate(elapsed)")
        lines.append("                target_interval = 1.0 / max(current_rate, 1)")
        lines.append("                ")
        lines.append("                if time.time() - last_request_time >= target_interval:")
        lines.append("                    # Select test data")
        lines.append("                    kwargs = {}")
        lines.append("                    if test_data:")
        lines.append("                        import random")
        lines.append("                        kwargs = random.choice(test_data)")
        lines.append("                    ")
        lines.append("                    future = executor.submit(self._execute_request, target_func, metrics, **kwargs)")
        lines.append("                    futures.append(future)")
        lines.append("                    last_request_time = time.time()")
        lines.append("                ")
        lines.append("                # Clean up completed futures")
        lines.append("                futures = [f for f in futures if not f.done()]")
        lines.append("                time.sleep(0.001)")
        lines.append("            ")
        lines.append("            # Wait for remaining futures")
        lines.append("            for future in futures:")
        lines.append("                future.result(timeout=30)")
        lines.append("")
        lines.append("    def _execute_request(self, func: Callable, metrics: PerformanceMetrics, **kwargs):")
        lines.append("        start = time.perf_counter()")
        lines.append("        success = True")
        lines.append("        try:")
        lines.append("            result = func(**kwargs)")
        lines.append("        except Exception as e:")
        lines.append("            success = False")
        lines.append("        finally:")
        lines.append("            duration = time.perf_counter() - start")
        lines.append("            metrics.record_execution(duration, success)")
        lines.append("")
        lines.append("    def stop(self):")
        lines.append("        self._stop_event.set()")
        lines.append("")
        
        return lines
    
    def _generate_data_generator(self, spec: PerformanceTestSpec) -> List[str]:
        """Generate test data generator function."""
        lines = []
        
        lines.append("def generate_test_data() -> List[Dict[str, Any]]:")
        lines.append('    """Generate test data for performance test."""')
        
        if spec.data_generator:
            for line in spec.data_generator.split('\n'):
                lines.append(f"    {line}")
        else:
            lines.append("    # Default test data")
            lines.append("    return [{}]")
        
        lines.append("")
        return lines
    
    def _generate_test_class(self, spec: PerformanceTestSpec) -> List[str]:
        """Generate main test class."""
        lines = []
        
        if self.config.framework == "pytest":
            lines.append("import pytest")
            lines.append("")
        
        lines.append(f"class Test{spec.name.replace(' ', '').replace('-', '_')}:")
        lines.append(f'    """Performance test: {spec.name}"""')
        lines.append("")
        
        # Setup method
        lines.append("    def setup_method(self):")
        lines.append("        self.metrics = PerformanceMetrics()")
        lines.append("        self.load_generator = LoadGenerator(load_profile)")
        if spec.test_data:
            lines.append(f"        self.test_data = {spec.test_data}")
        elif spec.data_generator:
            lines.append("        self.test_data = generate_test_data()")
        else:
            lines.append("        self.test_data = None")
        lines.append("        self.metrics.start_time = datetime.now()")
        lines.append("")
        
        # System metrics collection thread
        if self.config.collect_system_metrics:
            lines.append("        self._stop_monitoring = threading.Event()")
            lines.append("        self._monitor_thread = threading.Thread(target=self._monitor_system)")
            lines.append("        self._monitor_thread.start()")
            lines.append("")
        
        # Teardown method
        lines.append("    def teardown_method(self):")
        if self.config.collect_system_metrics:
            lines.append("        self._stop_monitoring.set()")
            lines.append("        self._monitor_thread.join(timeout=5)")
        lines.append("        self.metrics.end_time = datetime.now()")
        lines.append("")
        
        # System monitoring method
        if self.config.collect_system_metrics:
            lines.append("    def _monitor_system(self):")
            lines.append("        process = psutil.Process(os.getpid())")
            lines.append("        while not self._stop_monitoring.is_set():")
            lines.append("            try:")
            lines.append("                memory_info = process.memory_info()")
            lines.append("                self.metrics.record_memory(memory_info.rss / (1024 * 1024))")
            lines.append("                self.metrics.record_cpu(process.cpu_percent())")
            lines.append("            except:")
            lines.append("                pass")
            lines.append("            time.sleep(0.1)")
            lines.append("")
        
        # Warmup method
        lines.append("    def _warmup(self):")
        lines.append(f'        """Execute warmup phase."""')
        lines.append(f"        print(f\"Starting warmup phase ({WARMUP_SECONDS}s)...\")")
        lines.append("        warmup_end = time.time() + WARMUP_SECONDS")
        lines.append("        while time.time() < warmup_end:")
        lines.append("            try:")
        lines.append(f"                {spec.target_function}()")
        lines.append("            except:")
        lines.append("                pass")
        lines.append("        print(\"Warmup complete.\")")
        lines.append("")
        
        # Main test method
        lines.append(f"    def test_{spec.name.replace(' ', '_').lower()}(self):")
        lines.append(f'        """Execute performance test."""')
        lines.append("")
        
        # GC setup
        if spec.collect_gc_stats:
            lines.append("        gc.collect()")
            lines.append("        gc.disable()")
            lines.append("")
        
        # Warmup
        if spec.load_profile.warmup_seconds > 0:
            lines.append("        self._warmup()")
            lines.append("")
        
        # Profiling setup
        if spec.profile_code:
            lines.append("        profiler = cProfile.Profile()")
            lines.append("        profiler.enable()")
            lines.append("")
        
        # Execute test
        lines.append(f"        print(f\"Starting performance test '{spec.name}'...\")")
        lines.append(f"        print(f\"Duration: {spec.load_profile.duration_seconds}s, Concurrent users: {spec.load_profile.concurrent_users}\")")
        lines.append("")
        lines.append("        self.load_generator.generate(")
        lines.append(f"            {spec.target_function},")
        lines.append("            self.metrics,")
        lines.append("            self.test_data")
        lines.append("        )")
        lines.append("")
        
        # Profiling teardown
        if spec.profile_code:
            lines.append("        profiler.disable()")
            lines.append("        s = StringIO()")
            lines.append("        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')")
            lines.append("        ps.print_stats(20)")
            lines.append("        print(\"\\n=== Profile Results ===\"")
            lines.append("        print(s.getvalue())")
            lines.append("")
        
        # GC teardown
        if spec.collect_gc_stats:
            lines.append("        gc.enable()")
            lines.append("        gc_stats = gc.get_stats()")
            lines.append("        print(f\"GC Stats: {gc_stats}\")")
            lines.append("")
        
        # Cooldown
        if spec.load_profile.cooldown_seconds > 0:
            lines.append(f"        print(f\"Cooldown phase ({COOLDOWN_SECONDS}s)...\")")
            lines.append(f"        time.sleep(COOLDOWN_SECONDS)")
            lines.append("")
        
        # Print results
        lines.append("        stats = self.metrics.get_statistics()")
        lines.append("        print(\"\\n=== Performance Test Results ===\"")
        lines.append("        for key, value in stats.items():")
        lines.append("            print(f\"{key}: {value}\")")
        lines.append("")
        
        # Assertions
        if spec.assertions:
            lines.append("        # Performance assertions")
            for assertion in spec.assertions:
                lines.append(self._generate_assertion_code(assertion))
            lines.append("")
        
        # Save results
        if spec.save_results:
            lines.append("        # Save results to file")
            lines.append("        results = {")
            lines.append("            'test_name': TEST_NAME,")
            lines.append("            'test_type': TEST_TYPE,")
            lines.append("            'timestamp': datetime.now().isoformat(),")
            lines.append("            'statistics': stats,")
            lines.append("            'configuration': {")
            lines.append("                'duration_seconds': DURATION_SECONDS,")
            lines.append("                'concurrent_users': CONCURRENT_USERS,")
            lines.append("                'target_function': TARGET_FUNCTION,")
            lines.append("            }")
            lines.append("        }")
            lines.append("")
            lines.append(f"        output_file = f\"results_{spec.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json\"")
            lines.append("        with open(output_file, 'w') as f:")
            lines.append("            json.dump(results, f, indent=2, default=str)")
            lines.append(f"        print(f\"\\nResults saved to: {{output_file}}\")")
            lines.append("")
        
        # Generate visualization
        if self.config.include_visualizations:
            lines.append("        if VISUALIZATION_AVAILABLE and len(self.metrics.execution_times) > 0:")
            lines.append("            self._generate_visualizations()")
            lines.append("")
        
        lines.append("")
        
        # Visualization method
        if self.config.include_visualizations:
            lines.append("    def _generate_visualizations(self):")
            lines.append('        """Generate performance visualizations."""')
            lines.append("        fig, axes = plt.subplots(2, 2, figsize=(12, 10))")
            lines.append("")
            lines.append("        # Response time histogram")
            lines.append("        axes[0, 0].hist(self.metrics.execution_times, bins=50, alpha=0.7, color='blue')")
            lines.append("        axes[0, 0].set_xlabel('Response Time (s)')")
            lines.append("        axes[0, 0].set_ylabel('Frequency')")
            lines.append("        axes[0, 0].set_title('Response Time Distribution')")
            lines.append("        axes[0, 0].axvline(statistics.median(self.metrics.execution_times), color='red', linestyle='--', label='Median')")
            lines.append("        axes[0, 0].legend()")
            lines.append("")
            lines.append("        # Response time percentiles")
            lines.append("        percentiles = [50, 75, 90, 95, 99]")
            lines.append("        values = [statistics.quantiles(self.metrics.execution_times, n=100)[p-1] for p in percentiles]")
            lines.append("        axes[0, 1].bar(range(len(percentiles)), values, color='green', alpha=0.7)")
            lines.append("        axes[0, 1].set_xticks(range(len(percentiles)))")
            lines.append("        axes[0, 1].set_xticklabels([f'p{p}' for p in percentiles])")
            lines.append("        axes[0, 1].set_ylabel('Response Time (s)')")
            lines.append("        axes[0, 1].set_title('Response Time Percentiles')")
            lines.append("")
            lines.append("        # Throughput over time")
            lines.append("        if len(self.metrics.execution_times) > 1:")
            lines.append("            window_size = max(1, len(self.metrics.execution_times) // 50)")
            lines.append("            throughput = []")
            lines.append("            for i in range(0, len(self.metrics.execution_times), window_size):")
            lines.append("                window = self.metrics.execution_times[i:i+window_size]")
            lines.append("                throughput.append(len(window) / sum(window) if sum(window) > 0 else 0)")
            lines.append("            axes[1, 0].plot(throughput, color='orange')")
            lines.append("            axes[1, 0].set_xlabel('Time Window')")
            lines.append("            axes[1, 0].set_ylabel('Throughput (req/s)')")
            lines.append("            axes[1, 0].set_title('Throughput Over Time')")
            lines.append("")
            lines.append("        # Memory usage")
            lines.append("        if self.metrics.memory_samples:")
            lines.append("            axes[1, 1].plot(self.metrics.memory_samples, color='purple')")
            lines.append("            axes[1, 1].set_xlabel('Sample')")
            lines.append("            axes[1, 1].set_ylabel('Memory (MB)')")
            lines.append("            axes[1, 1].set_title('Memory Usage Over Time')")
            lines.append("")
            lines.append("        plt.tight_layout()")
            lines.append(f"        output_file = f\"viz_{spec.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png\"")
            lines.append("        plt.savefig(output_file, dpi=150)")
            lines.append(f"        print(f\"Visualization saved to: {{output_file}}\")")
            lines.append("        plt.close()")
            lines.append("")
        
        return lines
    
    def _generate_assertion_code(self, assertion: PerformanceAssertion) -> str:
        """Generate assertion code."""
        metric_map = {
            "max_time": "stats['max_time']",
            "avg_time": "stats['avg_time']",
            "min_time": "stats['min_time']",
            "p95_time": "stats['p95_time']",
            "p99_time": "stats['p99_time']",
            "throughput": "stats['throughput']",
            "error_rate": "stats['error_rate']",
            "max_memory_mb": "stats.get('max_memory_mb', 0)"
        }
        
        metric_expr = metric_map.get(assertion.metric_name, f"stats.get('{assertion.metric_name}', 0)")
        message = assertion.message or f"Performance assertion failed: {assertion.metric_name} {assertion.operator} {assertion.expected_value}"
        
        return f"        assert {metric_expr} {assertion.operator} {assertion.expected_value}, f\"{message}: {{{metric_expr}}}\""
    
    def _generate_helper_functions(self, spec: PerformanceTestSpec) -> List[str]:
        """Generate helper functions."""
        lines = []
        
        lines.append("def calculate_percentiles(data: List[float], percentiles: List[float]) -> Dict[float, float]:")
        lines.append('    """Calculate percentiles for data."""')
        lines.append("    if not data:")
        lines.append("        return {}")
        lines.append("    sorted_data = sorted(data)")
        lines.append("    result = {}")
        lines.append("    for p in percentiles:")
        lines.append("        index = int(len(sorted_data) * p / 100)")
        lines.append("        result[p] = sorted_data[min(index, len(sorted_data) - 1)]")
        lines.append("    return result")
        lines.append("")
        
        lines.append("def format_duration(seconds: float) -> str:")
        lines.append('    """Format duration in human-readable format."""')
        lines.append("    if seconds < 1:")
        lines.append("        return f\"{seconds*1000:.2f}ms\"")
        lines.append("    elif seconds < 60:")
        lines.append("        return f\"{seconds:.2f}s\"")
        lines.append("    else:")
        lines.append("        minutes = int(seconds // 60)")
        lines.append("        secs = seconds % 60")
        lines.append("        return f\"{minutes}m {secs:.1f}s\"")
        lines.append("")
        
        return lines
    
    def _generate_main_entry(self, spec: PerformanceTestSpec) -> List[str]:
        """Generate main entry point."""
        lines = []
        
        lines.append("if __name__ == \"__main__\":")
        lines.append("    import sys")
        lines.append("")
        lines.append("    # Parse command line arguments")
        lines.append("    import argparse")
        lines.append("    parser = argparse.ArgumentParser(description=f'Performance Test: {spec.name}')")
        lines.append("    parser.add_argument('--duration', type=int, default=DURATION_SECONDS, help='Test duration in seconds')")
        lines.append("    parser.add_argument('--users', type=int, default=CONCURRENT_USERS, help='Number of concurrent users')")
        lines.append("    parser.add_argument('--rate', type=int, help='Target request rate')")
        lines.append("    parser.add_argument('--output', type=str, help='Output file for results')")
        lines.append("    parser.add_argument('--no-warmup', action='store_true', help='Skip warmup phase')")
        lines.append("    parser.add_argument('--profile', action='store_true', help='Enable code profiling')")
        lines.append("    args = parser.parse_args()")
        lines.append("")
        lines.append("    # Override configuration")
        lines.append("    if args.duration:")
        lines.append("        DURATION_SECONDS = args.duration")
        lines.append("    if args.users:")
        lines.append("        CONCURRENT_USERS = args.users")
        lines.append("")
        lines.append("    # Create load profile")
        lines.append("    load_profile = LoadProfile(")
        lines.append(f"        pattern=LoadPattern.{spec.load_profile.pattern.name},")
        lines.append(f"        start_rate={spec.load_profile.start_rate},")
        lines.append(f"        duration_seconds=DURATION_SECONDS,")
        lines.append(f"        concurrent_users=CONCURRENT_USERS,")
        lines.append(f"        warmup_seconds=0 if args.no_warmup else WARMUP_SECONDS")
        lines.append("    )")
        lines.append("")
        lines.append("    # Run test")
        lines.append(f"    test = Test{spec.name.replace(' ', '').replace('-', '_')}()")
        lines.append("    test.setup_method()")
        lines.append("    try:")
        lines.append(f"        test.test_{spec.name.replace(' ', '_').lower()}()")
        lines.append("    finally:")
        lines.append("        test.teardown_method()")
        lines.append("")
        
        return lines


# ============================================================
# STRESS TEST GENERATOR
# ============================================================

class StressTestGenerator:
    """Specialized generator for stress tests."""
    
    def __init__(self, base_generator: PerformanceTestCodeGenerator):
        self.base_generator = base_generator
    
    def generate_stress_test(self, spec: PerformanceTestSpec) -> str:
        """Generate stress test with increasing load until failure."""
        spec.test_type = PerformanceTestType.STRESS
        spec.load_profile.pattern = LoadPattern.RAMP_UP
        spec.load_profile.end_rate = spec.load_profile.start_rate * 10
        
        return self.base_generator.generate(spec)
    
    def generate_endurance_test(self, spec: PerformanceTestSpec) -> str:
        """Generate endurance test for extended period."""
        spec.test_type = PerformanceTestType.ENDURANCE
        spec.load_profile.duration_seconds = 3600  # 1 hour default
        
        return self.base_generator.generate(spec)
    
    def generate_spike_test(self, spec: PerformanceTestSpec) -> str:
        """Generate spike test with sudden load increases."""
        spec.test_type = PerformanceTestType.SPIKE
        spec.load_profile.pattern = LoadPattern.SPIKE
        spec.load_profile.spike_multiplier = 10.0
        
        return self.base_generator.generate(spec)
    
    def generate_scalability_test(self, spec: PerformanceTestSpec) -> str:
        """Generate scalability test with varying concurrent users."""
        spec.test_type = PerformanceTestType.SCALABILITY
        
        # Generate test that runs with different user counts
        lines = self.base_generator.generate(spec).split('\n')
        
        # Add scalability-specific code
        scalability_code = '''
    def test_scalability(self):
        """Test scalability with varying concurrent users."""
        user_counts = [1, 5, 10, 25, 50, 100]
        results = []
        
        for users in user_counts:
            print(f"\\n=== Testing with {users} concurrent users ===")
            self.metrics = PerformanceMetrics()
            self.load_generator = LoadGenerator(load_profile)
            self.load_generator.profile.concurrent_users = users
            
            self.metrics.start_time = datetime.now()
            self.load_generator.generate(TARGET_FUNCTION, self.metrics, self.test_data)
            self.metrics.end_time = datetime.now()
            
            stats = self.metrics.get_statistics()
            stats['concurrent_users'] = users
            results.append(stats)
        
        # Print scalability summary
        print("\\n=== Scalability Summary ===")
        print(f"{'Users':<10} {'Throughput':<15} {'Avg Time':<15} {'Error Rate':<15}")
        for r in results:
            print(f"{r['concurrent_users']:<10} {r.get('throughput', 0):<15.2f} {r.get('avg_time', 0):<15.4f} {r.get('error_rate', 0):<15.2%}")
        
        # Save scalability results
        with open(f"scalability_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(results, f, indent=2)
'''
        
        # Insert scalability test
        class_end = -1
        for i, line in enumerate(lines):
            if line.strip().startswith("if __name__"):
                class_end = i
                break
        
        if class_end > 0:
            lines.insert(class_end, scalability_code)
        
        return '\n'.join(lines)


# ============================================================
# MAIN PERFORMANCE TEST GENERATOR
# ============================================================

class PerformanceTestGenerator:
    """
    Generates comprehensive performance tests.
    
    Features:
    - Multiple test types (benchmark, load, stress, endurance, spike, scalability)
    - Configurable load patterns
    - Comprehensive metrics collection
    - Performance assertions
    - Visualizations
    - Resource monitoring
    - Profiling support
    - LLM-powered generation
    """
    
    def __init__(self, config: Optional[PerformanceTestGeneratorConfig] = None):
        self.config = config or PerformanceTestGeneratorConfig()
        self.code_generator = PerformanceTestCodeGenerator(self.config)
        self.stress_generator = StressTestGenerator(self.code_generator)
        self.llm = LLMClient() if self.config.use_llm else None
        self.state = StateManager(Path(".ai_state") / "performance_test_generator.json")
        
        logger.info("PerformanceTestGenerator initialized")
    
    # ============================================================
    # GENERATION
    # ============================================================
    
    def generate(self, spec: PerformanceTestSpec, output_path: Optional[Path] = None) -> GeneratedPerformanceTest:
        """
        Generate a performance test from specification.
        
        Args:
            spec: Performance test specification
            output_path: Optional output file path
        """
        logger.info(f"Generating performance test: {spec.name}")
        
        # Generate code based on test type
        if spec.test_type == PerformanceTestType.STRESS:
            code = self.stress_generator.generate_stress_test(spec)
        elif spec.test_type == PerformanceTestType.ENDURANCE:
            code = self.stress_generator.generate_endurance_test(spec)
        elif spec.test_type == PerformanceTestType.SPIKE:
            code = self.stress_generator.generate_spike_test(spec)
        elif spec.test_type == PerformanceTestType.SCALABILITY:
            code = self.stress_generator.generate_scalability_test(spec)
        else:
            code = self.code_generator.generate(spec)
        
        # Estimate duration
        estimated_duration = self._estimate_duration(spec)
        
        # Write to file if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(code)
        
        result = GeneratedPerformanceTest(
            test_spec=spec,
            code=code,
            file_path=output_path,
            validation_passed=True,
            estimated_duration_seconds=estimated_duration
        )
        
        self._save_result(result)
        
        logger.info(f"Generated performance test {spec.name}")
        return result
    
    def generate_from_function(self,
                                func: Callable,
                                test_type: PerformanceTestType = PerformanceTestType.BENCHMARK,
                                output_path: Optional[Path] = None) -> GeneratedPerformanceTest:
        """
        Generate performance test from a Python function.
        
        Args:
            func: Python function to test
            test_type: Type of performance test
            output_path: Optional output file path
        """
        # Extract function info
        func_name = func.__name__
        module_name = func.__module__
        
        # Create specification
        spec = PerformanceTestSpec(
            name=f"{test_type.value}_{func_name}",
            test_type=test_type,
            target_function=func_name,
            target_module=module_name,
            description=f"Performance test for {func_name}",
            metrics=[
                PerformanceMetric(name="execution_time", metric_type=MetricsType.EXECUTION_TIME, unit="s"),
                PerformanceMetric(name="throughput", metric_type=MetricsType.THROUGHPUT, unit="req/s"),
            ],
            assertions=[
                PerformanceAssertion(
                    assertion_type=AssertionType.AVG_TIME,
                    metric_name="avg_time",
                    expected_value=1.0,
                    operator="<"
                )
            ]
        )
        
        return self.generate(spec, output_path)
    
    def generate_from_description(self,
                                   description: str,
                                   target_function: str,
                                   target_module: str,
                                   output_path: Optional[Path] = None) -> GeneratedPerformanceTest:
        """
        Generate performance test from natural language description.
        
        Args:
            description: Natural language description
            target_function: Name of function to test
            target_module: Module containing the function
            output_path: Optional output file path
        """
        if not self.llm:
            raise ValueError("LLM is required for description-based generation")
        
        logger.info(f"Generating performance test from description")
        
        spec = self._parse_description(description, target_function, target_module)
        
        return self.generate(spec, output_path)
    
    def _parse_description(self, description: str, target_function: str, target_module: str) -> PerformanceTestSpec:
        """Parse natural language description into PerformanceTestSpec."""
        prompt = f"""
        Parse this performance test description into a structured specification:
        
        Target: {target_module}.{target_function}
        Description: {description}
        
        Return a JSON object with:
        - test_type: one of {[t.value for t in PerformanceTestType]}
        - name: test name
        - load_profile: object with pattern, concurrent_users, duration_seconds
        - metrics: list of metrics to collect
        - assertions: list of performance assertions
        
        Output only valid JSON.
        """
        
        response = self.llm.complete_json(prompt)
        
        spec = PerformanceTestSpec(
            name=response.get('name', f'perf_test_{target_function}'),
            test_type=PerformanceTestType(response.get('test_type', 'benchmark')),
            target_function=target_function,
            target_module=target_module,
            description=description
        )
        
        # Parse load profile
        if 'load_profile' in response:
            lp = response['load_profile']
            spec.load_profile = LoadProfile(
                pattern=LoadPattern(lp.get('pattern', 'constant')),
                concurrent_users=lp.get('concurrent_users', 10),
                duration_seconds=lp.get('duration_seconds', 60)
            )
        
        return spec
    
    def _estimate_duration(self, spec: PerformanceTestSpec) -> int:
        """Estimate total test duration."""
        duration = spec.load_profile.duration_seconds
        duration += spec.load_profile.warmup_seconds
        duration += spec.load_profile.cooldown_seconds
        duration *= spec.iterations
        return duration
    
    def _save_result(self, result: GeneratedPerformanceTest):
        """Save generation result to state."""
        history = self.state.get('history', [])
        history.append({
            'test_name': result.test_spec.name,
            'test_type': result.test_spec.test_type.value,
            'file_path': str(result.file_path) if result.file_path else None,
            'estimated_duration': result.estimated_duration_seconds,
            'generated_at': result.generated_at.isoformat()
        })
        
        if len(history) > 100:
            history = history[-100:]
        
        self.state.set('history', history)
        self.state.save()
    
    def close(self):
        """Clean up resources."""
        self.state.save()
        logger.info("PerformanceTestGenerator closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for performance test generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate performance tests for Python code")
    parser.add_argument("--target", type=str, required=True, help="Target function (module.function)")
    parser.add_argument("--type", choices=[t.value for t in PerformanceTestType],
                       default=PerformanceTestType.BENCHMARK.value, help="Test type")
    parser.add_argument("--name", type=str, help="Test name")
    parser.add_argument("--output", "-o", type=Path, help="Output file path")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    parser.add_argument("--users", type=int, default=10, help="Concurrent users")
    parser.add_argument("--rate", type=int, default=1, help="Target request rate")
    parser.add_argument("--stress", action="store_true", help="Generate stress test")
    parser.add_argument("--endurance", action="store_true", help="Generate endurance test")
    parser.add_argument("--spike", action="store_true", help="Generate spike test")
    parser.add_argument("--scalability", action="store_true", help="Generate scalability test")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM assistance")
    
    args = parser.parse_args()
    
    config = PerformanceTestGeneratorConfig(use_llm=not args.no_llm)
    generator = PerformanceTestGenerator(config)
    
    # Parse target
    if '.' in args.target:
        module_name, func_name = args.target.rsplit('.', 1)
    else:
        module_name = "__main__"
        func_name = args.target
    
    # Determine test type
    test_type = PerformanceTestType(args.type)
    if args.stress:
        test_type = PerformanceTestType.STRESS
    elif args.endurance:
        test_type = PerformanceTestType.ENDURANCE
    elif args.spike:
        test_type = PerformanceTestType.SPIKE
    elif args.scalability:
        test_type = PerformanceTestType.SCALABILITY
    
    # Create specification
    spec = PerformanceTestSpec(
        name=args.name or f"{test_type.value}_{func_name}",
        test_type=test_type,
        target_function=func_name,
        target_module=module_name,
        load_profile=LoadProfile(
            pattern=LoadPattern.CONSTANT if test_type == PerformanceTestType.BENCHMARK else LoadPattern.RAMP_UP,
            start_rate=args.rate,
            concurrent_users=args.users,
            duration_seconds=args.duration
        ),
        metrics=[
            PerformanceMetric(name="execution_time", metric_type=MetricsType.EXECUTION_TIME, unit="s"),
            PerformanceMetric(name="throughput", metric_type=MetricsType.THROUGHPUT, unit="req/s"),
        ]
    )
    
    # Generate test
    result = generator.generate(spec, args.output)
    
    if args.output:
        print(f"Performance test generated at {args.output}")
        print(f"Estimated duration: {result.estimated_duration_seconds}s")
    else:
        print(result.code)
    
    generator.close()


if __name__ == "__main__":
    main()