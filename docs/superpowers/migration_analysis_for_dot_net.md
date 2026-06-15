# .NET 8 AOT Complete Rewrite Migration Prompt

You are an expert in both Python and C#/.NET, specializing in **complete codebase rewrites** from Python to .NET 8 with Native AOT compilation. I need you to analyze my Python codebase and produce a **complete migration plan** for rewriting it entirely in C#. There will be **no interoperability** between Python and C# during or after migration—this is a full rewrite.

## Context
- I am building an Agentic Business Process Management System (BPMS)
- Current Python version: 3.12+
- Target: **Complete rewrite** to C#/.NET 8 with Native AOT
- No hybrid approach: C# will replace Python entirely
- Existing Python code serves as **requirements specification** and **logic reference**
- I will use AI-assisted translation to generate C# equivalents

## Core Assumption

**The Python code will NOT run alongside C# code.** This analysis is for a complete rewrite where:
1. Python code is analyzed for business logic, algorithms, and data structures
2. Equivalent C# code is designed and implemented
3. Python code is archived/deleted after C# implementation is validated

## Primary Analysis Goals

For each module/file in the Python codebase, analyze and document:

### 1. Business Logic Extraction

Extract and document:
- **Core business rules** that must be preserved in C#
- **Algorithm descriptions** (step-by-step what the code does)
- **Data flow diagrams** (inputs → processing → outputs)
- **State machines** and transition logic
- **Workflow orchestration patterns**
- **Agent coordination logic**

**Do NOT preserve:**
- Python-specific idioms (list comprehensions, decorators, context managers)
- Python dynamic features (monkey patching, runtime type changes)
- Implementation details that are Python-specific

### 2. Data Architecture Analysis

For each data structure in Python, specify its C# equivalent:

| Python Construct | C# Equivalent (AOT-Compatible) |
|-----------------|-------------------------------|
| `dict` | `Dictionary<TKey, TValue>` |
| `list` | `List<T>` or `T[]` |
| `dataclass` | `record` or `struct` |
| `pydantic.BaseModel` | `record` + manual validation |
| `Enum` | `enum` |
| `TypedDict` | `record` or `class` |
| `NamedTuple` | `record` |
| `defaultdict` | `Dictionary` with factory method |
| `set` | `HashSet<T>` |
| `deque` | `Queue<T>` or `ConcurrentQueue<T>` |
| `datetime` | `DateTime`, `DateTimeOffset` |
| `decimal` | `decimal` (same) |
| `Union`/`Optional` | nullable types (`T?`) |

### 3. Dependency Analysis

For each external Python library used, provide:

| Python Library | .NET Alternative | Migration Complexity | Recommendation |
|----------------|------------------|---------------------|----------------|
| `FastAPI` | ASP.NET Core Minimal APIs | Low | Complete rewrite |
| `SQLAlchemy` | Entity Framework Core | Medium | Complete rewrite |
| `Pydantic` | System.Text.Json + records | Medium | Manual validation |
| `aiohttp` | `HttpClient` + `IHttpClientFactory` | Low | Complete rewrite |
| `httpx` | `HttpClient` | Low | Complete rewrite |
| `celery` | `BackgroundService` + `Channel<T>` | Medium | Complete rewrite |
| `pandas` | `CsvHelper` + LINQ OR manual | High | Evaluate if needed |
| `numpy` | `Math.NET Numerics` | High | Evaluate if needed |
| `boto3` (AWS) | `AWSSDK.*` packages | Low | Complete rewrite |
| `tenacity` (retries) | Polly | Low | Complete rewrite |
| `loguru` | `ILogger` (Microsoft.Extensions.Logging) | Low | Complete rewrite |
| `click` (CLI) | `System.CommandLine` | Low | Complete rewrite |
| `Jinja2` | `Scriban` OR `Razor` | Medium | Complete rewrite |

### 4. Architecture Pattern Translation

Map Python architectural patterns to C# equivalents:

| Python Pattern | C# Pattern |
|----------------|------------|
| Global state in module | Static class with `Lazy<T>` |
| Dependency injection (manual) | Microsoft.Extensions.DependencyInjection |
| Abstract base class | `abstract class` |
| Protocol/duck typing | Interface |
| Context manager (`__enter__`/`__exit__`) | `IDisposable` + `using` |
| Decorator | Attribute OR middleware |
| Coroutine (`async def`) | `async Task` |
| Generator (`yield`) | `yield return` OR `IEnumerable<T>` |
| Weakref | `WeakReference<T>` |
| `__slots__` | `struct` (value type) |
| Metaclass | Factory pattern OR code generation |

### 5. Performance and AOT Compatibility

For each module, identify:

**AOT-Compatible (Safe for Native AOT):**
- Pure calculations and algorithms
- Static data structures
- Value types (`struct`)
- Simple generics
- Fixed dependency tree

**Requires Runtime JIT (NOT AOT-Compatible):**
- `System.Reflection.Emit`
- Dynamic code loading (`Assembly.Load`)
- `Expression.Compile()` without pre-compilation
- Serialization with runtime type discovery (some scenarios)
- `dynamic` keyword usage
- Runtime code generation

**If non-AOT code is required:**
- Document why it cannot be AOT
- Suggest alternative AOT-compatible approaches
- Or accept that this module cannot be AOT-compiled

### 6. Concurrency Model Translation

| Python Concurrency | C# Equivalent |
|-------------------|----------------|
| `asyncio` + `async/await` | `Task` + `async/await` |
| `asyncio.gather()` | `Task.WhenAll()` |
| `asyncio.create_task()` | `Task.Run()` or `Task.Factory.StartNew()` |
| `asyncio.Queue` | `Channel<T>` or `ConcurrentQueue<T>` |
| `asyncio.Semaphore` | `SemaphoreSlim` |
| `asyncio.Lock` | `AsyncLock` OR `SemaphoreSlim(1,1)` |
| `threading.Thread` | `Task` OR `Thread` |
| `multiprocessing` | `Parallel.ForEach` OR `Task` (avoid multiprocessing) |
| `concurrent.futures` | `Task.Run` + `Task.WhenAll` |
| GIL limitations | No GIL - true parallelism available |

### 7. Error Handling Translation

| Python Pattern | C# Pattern (AOT-Compatible) |
|----------------|-----------------------------|
| `try/except` | `try/catch` |
| `raise Exception` | `throw new Exception()` |
| Custom exception class | Custom exception class (derive from `Exception`) |
| `except Exception as e:` | `catch (Exception ex)` |
| `finally:` | `finally:` |
| `else:` (try-else) | Manual flag or restructure |
| `return None` on error | Throw exception OR return `Result<T>` type |

**Critical for AOT:** Exceptions work in AOT, but `ExceptionDispatchInfo` and some reflection-based exception features may have limitations.

### 8. Logging and Observability

| Python | C# Equivalent |
|--------|----------------|
| `print()` | `ILogger.LogInformation()` |
| `logging.getLogger()` | `ILogger<T>` via DI |
| Structured logging (JSON) | `Serilog` OR `Microsoft.Extensions.Logging` |
| OpenTelemetry | OpenTelemetry .NET SDK |

### 9. Testing Strategy Translation

| Python Testing | C# Equivalent |
|----------------|----------------|
| `pytest` | xUnit, NUnit, or MSTest |
| `pytest.fixture` | `[SetUp]` or `IClassFixture` |
| `unittest.mock` | `Moq`, `NSubstitute`, or `FakeItEasy` |
| `pytest-asyncio` | `[TestMethod]` + `async Task` |
| `pytest-cov` | Coverlet + ReportGenerator |
| `hypothesis` | FsCheck or Property-based testing frameworks |

### 10. Project Structure Translation

Map the Python project structure to .NET conventions:

**Current Python structure:**
```
project/
├── engines/
│   ├── orchestration/
│   │   ├── workflow_engine.py
│   │   └── state_machine.py
│   └── agents/
│       ├── base_agent.py
│       └── bpmn_agent.py
├── models/
│   ├── workflow.py
│   └── tasks.py
├── services/
│   ├── persistence.py
│   └── messaging.py
└── utils/
    ├── logging.py
    └── validators.py
```

**Proposed .NET structure:**
```
DotNetBpms/
├── src/
│   ├── DotNetBpms.Engines/
│   │   ├── Orchestration/
│   │   │   ├── WorkflowEngine.cs
│   │   │   └── StateMachine.cs
│   │   └── Agents/
│   │       ├── BaseAgent.cs
│   │       └── BpmnAgent.cs
│   ├── DotNetBpms.Models/
│   │   ├── Workflow.cs
│   │   └── Tasks.cs
│   ├── DotNetBpms.Services/
│   │   ├── Persistence/
│   │   └── Messaging/
│   └── DotNetBpms.Common/
│       ├── Logging/
│       └── Validation/
├── tests/
│   ├── DotNetBpms.Engines.Tests/
│   └── DotNetBpms.Models.Tests/
└── DotNetBpms.sln
```

## Output Requirements

For the ENTIRE Python project, produce:

### 1. Migration Report (`migration_reports/overview.md`)

- **Executive summary**: Scope, estimated effort, risk assessment
- **Architecture comparison**: Current Python architecture vs. proposed C# architecture
- **Dependency migration matrix**: All Python libraries → .NET alternatives
- **AOT compatibility assessment**: Percentage of code that can be AOT-compiled
- **Migration phases**: Suggested order of migration (dependencies first)

### 2. Module Migration Specifications (`migration_reports/modules_xxxx__yyyy_report.md`)

For each module/package:

```markdown
# Module: [Original Python Path]

## Business Logic Summary
[Description of what this module does, not how it does it]

## Data Structures
| Python Type | C# Equivalent | Complexity | Notes |
|-------------|---------------|------------|-------|

## Key Algorithms
[Step-by-step descriptions of critical algorithms]

## Dependencies
| Python Import | .NET Alternative | Required? |
|---------------|------------------|-----------|

## AOT Compatibility
- [ ] Compatible as-is
- [ ] Needs modification
- [ ] Cannot be AOT-compiled (explain why)

## Proposed C# Implementation
[High-level design of the C# equivalent]

## Complexity Estimate
- [Low/Medium/High] effort
- Estimated lines of C# code: [###]

## Risks
[List of risks specific to this module]
```

### 3. C# Project Structure Definition (`migration_reports/project_structure.md`)

- Complete .NET solution structure
- Project dependencies graph
- Namespace mapping from Python modules
- Startup and configuration approach

### 4. Implementation Roadmap (`migration_reports/roadmap.md`)


### 5. Migration Validation Plan (`migration_reports/validation.md`)

- How to verify C# implementation matches Python behavior
- Property-based testing strategies for equivalence
- Performance baseline comparison
- Acceptance criteria for each module

### 6. Code Generation Templates (`migration_reports/templates/`)

For each common pattern, provide a prompt for AI code generation:

```markdown
## Template: Python Class to C# Record

### Source Pattern (Python):
```python
@dataclass(frozen=True)
class WorkflowState:
    id: str
    status: str
    created_at: datetime
```

### Target Pattern (C#):
```csharp
public sealed record WorkflowState(
    string Id,
    string Status,
    DateTime CreatedAt
);
```

### Conversion Rules:
1. `@dataclass(frozen=True)` → `record` (immutable)
2. `@dataclass` (mutable) → `class` with init-only properties
3. `default` values handled via parameterless constructor
4. `field(default_factory=...)` handled via static factory method
```

## Code to Analyze

All Python code in the current project.

---

