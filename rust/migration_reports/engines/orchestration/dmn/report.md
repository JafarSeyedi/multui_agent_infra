# DMN Engine — Rust Migration Analysis

**Source:** `engines/orchestration/dmn/`  
**Files analyzed:** 9 Python files (2,193 total lines)  
**Score:** 4–5 (pure computation — excellent Rust candidate)

---

## 1. Pre-refactor Analysis

### `Any` / `dict[str, Any]` Proliferation

The type system originates from `engines/_types.py` where **every type alias** is `Any` or `dict[str, Any]`:

| Alias | Definition | Used where |
|-------|-----------|------------|
| `FeelContext` | `dict[str, Any]` | Every evaluate() signature |
| `DmnValue` | `Any` | Every return type |
| `Metadata` | `dict[str, Any]` | Output values, cache |
| `RawData` | `dict[str, Any]` | Table input, rules |
| `VariableValue` | `Any` | Context values |

**25+ functions** use these aliases. A Rust enum (`DmnValue`) should replace `Any`:

```rust
enum DmnValue {
    String(String),
    Number(f64),
    Bool(bool),
    Null,
    List(Vec<DmnValue>),
    Context(HashMap<String, DmnValue>),
    Date(String),
    Time(String),
    Duration(DurationParts),
    Range(Box<RangeValue>),
}
```

### `isinstance` Chains (5 sites)

| File | Line | Pattern |
|------|------|---------|
| `feel_engine.py` | 595 | `isinstance(node, tuple)` — AST node dispatch |
| `feel_engine.py` | 616–619 | `isinstance(base, dict)` / `hasattr` — path eval |
| `feel_engine.py` | 625–628 | `isinstance(collection, list)` — filter eval |
| `feel_engine.py` | 724, 737, 778 | `isinstance(collection, list)` — for/quantified/filter |
| `hit_policy_handler.py` | 125–132 | `isinstance(out, dict)` / `isinstance(out, (int, float))` — numeric extraction |
| `literal_expression_eval.py` | 84 | `isinstance(result, caster)` — type coercion guard |

**Strategy:** Replace with Rust enum pattern matching (`match value { ... }`). The isinstance pattern in `_eval_instance_of` (line 684–691) is a `type_map` dict + `isinstance` — translate to a `match` on type-of-value.

### Dispatch Dicts (4 sites)

| File | Lines | Pattern |
|------|-------|---------|
| `feel_engine.py:558–592` | `_OP_HANDLERS` — 28 entries | `dict[str, str]` mapping op -> method name |
| `hit_policy_handler.py:92–105` | `_HIT_POLICY_HANDLERS` — 11 entries | `dict[HitPolicy, Callable]` |
| `decision_executor.py:69–74` | `_BODY_EXTRACTORS` — 4 entries | `dict[type, Callable]` |
| `decision_executor.py:86–94` | `_BOXED_EXPRESSION_HANDLERS` — 7 entries | `dict[type, lambda]` |

**Strategy:** Use `match` statements. `_OP_HANDLERS` becomes `match op { "literal" => self.eval_literal(node), ... }`. Hit policy handlers become a method on `HitPolicy` enum or a function array indexed by policy variant.

### FEEL Expression Evaluation (feel_engine.py, 874 lines — 40% of total)

The **largest and most complex file**. A hand-written recursive-descent parser + tree-walking evaluator.

**Parser:** `FEELParser._tokenize()` builds tokens via character-by-character scanning (132 lines). `_parse_*` methods implement recursive descent with 17 grammar rules.

**Evaluator:** `FEELParser._eval_ast()` dispatches via `_OP_HANDLERS` dict. 28 handler methods, each matching one AST node type.

**Key for Rust:** This is a textbook `nom` or `pest` / `logos` parser target. The AST is already tuple-based `("op", left, right)`, which maps directly to a Rust enum:

```rust
enum FeelExpr {
    Literal(DmnValue),
    Var(String),
    Path(Box<FeelExpr>, String),
    Filter(Box<FeelExpr>, Box<FeelExpr>),
    Or(Box<FeelExpr>, Box<FeelExpr>),
    And(Box<FeelExpr>, Box<FeelExpr>),
    Not(Box<FeelExpr>),
    Eq(Box<FeelExpr>, Box<FeelExpr>),
    Neq(Box<FeelExpr>, Box<FeelExpr>),
    // ... etc
}
```

### `eval()` Usage — SECURITY CRITICAL (3 sites)

| File | Line | Context |
|------|------|---------|
| `decision_table_evaluator.py` | 173 | `eval(out_text.strip(), {"__builtins__": {}}, context)` — rule output |
| `decision_table_evaluator.py` | 195 | `eval(text, {"__builtins__": {}}, {})` — list check |
| `decision_table_evaluator.py` | 210, 228 | `float()` conversion in bound parsing |
| `decision_executor.py` | 250, 266 | `eval(test, ...)` — OSDM rule matching |
| `decision_executor.py` | 311, 327 | `eval(test, ...)` — dict-based rule matching |
| `expression/python_evaluator.py` | 35 | `eval(expression, _SAFE_GLOBALS, context)` — generic expression |

**Impact:** `eval()` is used for DMN rule entry matching. In Rust this becomes a direct FEEL expression evaluation — no eval needed. The `PythonEvaluator` fallback in `literal_expression_eval.py:58–61` is a separate concern; Rust migration eliminates the Python pathway entirely.

---

## 2. Migration Notes

### DMN Decision Tables

`DecisionTableEvaluator` (252 lines) and inline evaluation in `DecisionExecutor._evaluate_decision_table` (60 lines) and `_evaluate_osdm_decision_table` (55 lines) contain **duplicated rule-matching logic**.

Three separate rule-match loops exist:
1. `DecisionTableEvaluator._match_rules` (lines 147–186)
2. `DecisionExecutor._evaluate_decision_table` (lines 301–330)
3. `DecisionExecutor._evaluate_osdm_decision_table` (lines 241–269)

**Strategy:** Unify into a single `evaluate_table(table, context) -> Vec<Match>` in Rust. The three implementations differ slightly in data-access patterns but share the same algorithm: iterate rules → test each input entry → collect outputs.

### FEEL Engine — Highest Value Target

The FEEL engine is:
- **Self-contained:** No external deps beyond `re` and `datetime` (both easily replaced in Rust)
- **Pure computation:** No I/O, no async, no database
- **Hot path:** Called per cell in every decision table evaluation
- **Line-dominant:** 874 lines, 40% of total

**Rust replacement:** Use `logos` for tokenization + `nom` for parsing → evaluate against `HashMap<String, DmnValue>` context. The `builtins` (56 functions, lines 811–861) become a `HashMap<&str, fn(Vec<&DmnValue>) -> DmnValue>`.

### Hit Policies — Trivial Migration

`hit_policy_handler.py` (160 lines) is a pure function dispatch. The `HitPolicy` enum (10 variants) plus 11 handler functions (all 10–15 lines, pure list processing). No `Any` issues — `list[RawData]` input, `DmnValue | None` output. Direct 1:1 Rust translation.

---

## 3. Ownership Map

```
DMNEngine (engine.py)
  └── DecisionExecutor (decision_executor.py)
        ├── DecisionTableEvaluator (decision_table_evaluator.py)
        │     ├── InputClause, OutputClause, DecisionRule (dataclasses)
        │     └── hit_policy_handler.py::apply_hit_policy
        │           └── _HIT_POLICY_HANDLERS dispatch table
        ├── LiteralExpressionEvaluator (literal_expression_eval.py)
        │     ├── FEELEngine
        │     └── PythonEvaluator (fallback)
        ├── InvocationHandler (invocation_handler.py)
        │     └── FEELEngine
        ├── HitPolicyHandler (hit_policy_handler.py)
        └── FEELEngine (feel_engine.py)
              ├── FEELParser (tokenizer + recursive descent)
              └── builtins registry (56 functions)
  └── DmnDecisionServiceExecutor (decision_requirements_graph.py)
        └── DecisionRequirementsGraph (topological sort)
```

**Decision → DecisionTable → Rule → hit policy evaluation** is the core chain.  
`DecisionExecutor` is the central orchestrator; `FEELEngine` is the leaf dependency used everywhere.

---

## 4. PyO3 Binding Structure

### Recommended architecture:

```
dmn-engine (Rust crate)
├── lib.rs              # PyO3 bindings
├── feel/
│   ├── mod.rs          # FEELEngine, FEELError
│   ├── parser.rs       # FEELParser (tokenizer + recursive descent)
│   ├── ast.rs          # FeelExpr enum
│   ├── eval.rs         # AST evaluator (+ 56 builtins)
│   └── token.rs        # Token, TokenType enums
├── table/
│   ├── mod.rs          # DecisionTableEvaluator
│   ├── rule.rs         # DecisionRule, input/output entry matching
│   └── clause.rs       # InputClause, OutputClause
├── hit_policy.rs       # HitPolicy enum + handlers
├── invocation.rs       # InvocationHandler
├── drg.rs              # DecisionRequirementsGraph
├── literal.rs          # LiteralExpressionEvaluator
└── types.rs            # DmnValue, FeelContext, etc.
```

### PyO3 exposure priority:

1. **`FEELEngine`** — `#[pyclass]` with `evaluate(expression: &str, context: HashMap<String, PyObject>) -> PyResult<PyObject>`. Huge win: expression parsing + evaluation in Rust.
2. **`DecisionTableEvaluator`** — Pure computation, no Python fallback needed.
3. **`HitPolicyHandler`** — Trivial.
4. **`DecisionRequirementsGraph`** — Graph algorithms benefit from Rust performance.

### Python callers that need updating:

| File | Call site |
|------|-----------|
| `engine.py:51` | `await self.executor.evaluate(...)` — async wrapper needed |
| `decision_executor.py:107` | `async evaluate(...)` — DecisionExecutor entry point |
| `decision_executor.py:174` | `async evaluate_osdm(...)` — OSDM path |
| `decision_executor.py:345` | `evaluate_context(...)` — uses FEELEngine |
| `decision_executor.py:360` | `evaluate_relation(...)` — uses FEELEngine |
| `invocation_handler.py:44` | `async invoke(...)` — uses FEELEngine |

The `DecisionExecutor` is async (uses `orchestration_engine.event_bus.publish`), so the PyO3 binding needs `pyo3-asyncio` for the top-level evaluate, or restructure so the synchronous core (FEEL, table eval, hit policy) is pure Rust and only the top-level orchestrator remains Python.

---

## 5. Libraries Analysis

### Python stdlib only (no external dependencies in DMN layer):

| Module | Usage | Rust replacement |
|--------|-------|-----------------|
| `re` | `feel_engine.py:790` — duration ISO parsing | `regex` crate or hand-parser |
| `datetime` | `feel_engine.py:810–847` — date/time builtins | `chrono` crate |
| `math` | `feel_engine.py:811–815` — ceil/floor/sqrt | `f64` methods |
| `enum` | TokenType, HitPolicy enums | native `enum` |
| `dataclasses` | 8+ dataclasses | `struct` |
| `logging` | across all files | `log` crate |
| `typing` | type hints | n/a |
| `eval()` | Python expression evaluation | **eliminated** — FEEL-only |

### OSDM model dependency:

`decision_executor.py` and `decision_requirements_graph.py` import from `document.models.osdm_models`. These are typed dataclasses (`Decision`, `DecisionTable`, etc.). For a pure Rust rewrite, these need Rust equivalents. For incremental migration, PyO3 can accept the Python objects and access their fields via `.getattr()`.

### Cross-module dependencies:

- `hit_policy_handler.py` — independent (only imports `_types`)
- `feel_engine.py` — independent (imports `_types` + `expression/evaluator.py`)
- `literal_expression_eval.py` — depends on `FEELEngine` + `PythonEvaluator`
- `decision_table_evaluator.py` — depends on `hit_policy_handler`
- `invocation_handler.py` — depends on `FEELEngine`
- `decision_executor.py` — depends on everything above + OSDM models
- `decision_requirements_graph.py` — depends on OSDM models
- `engine.py` — depends on `DecisionExecutor` + `DmnDecisionServiceExecutor`

---

## 6. Performance Hot Paths

### 1. Decision table rule matching (DECISION_TABLE_EVALUATOR + DECISION_EXECUTOR)

Three implementations of the same loop, each O(n*m) where n=rules, m=input entries:

```python
# decision_table_evaluator.py:155 — per rule
for rule in table.rules:
    for i, entry_text in enumerate(rule.input_entries):
        if not self._test_input_entry(entry_text, input_values[i], context):
            break
```

`_test_input_entry` (188 lines) has 7 branches: empty, list `[...]`, range `(...)`, `..` range, equality. Each branch may call `eval()` or `float()`.

**Rust win:** Single pass, no eval. FEEL expression parsing is a one-time cost per entry.

### 2. FEEL expression parsing (feel_engine.py:118–531)

`_tokenize()` is O(n) character scanning with 30+ character classes. The parser is recursive descent with 17 non-terminals. This runs for **every cell** in a decision table.

**Rust win:** `logos` tokenizer is zero-allocation. `nom` parser produces `FeelExpr` enums on the stack. Estimated 10–50x speedup.

### 3. FEEL expression evaluation (feel_engine.py:594–803)

`_eval_ast` dispatches via dict lookup + `getattr`. 28 handler methods, each evaluating AST nodes recursively. The hot path is comparison operators in rule matching.

### 4. Hit policy aggregation (hit_policy_handler.py)

Each handler processes `list[RawData]` (matched rules). `COLLECT`, `C_SUM`, `C_MIN`, `C_MAX`, `C_COUNT` are trivially fast. `UNIQUE` and `ANY` have single-pass checks. Not a bottleneck.

### 5. DRG topological sort (decision_requirements_graph.py:81–94)

Kahn's algorithm on small graphs (typically <100 nodes). Not a bottleneck.

---

## 7. Error Handling

### FEELError (feel_engine.py:36)
- Raised for: parse errors (25+ sites), unknown AST ops, unknown functions, division by zero, variable not found, type access errors
- **Migration:** Map to a Rust error enum:

```rust
#[derive(Debug, thiserror::Error)]
pub enum FeelError {
    #[error("Parse error at position {pos}: expected {expected}, got {actual}")]
    ParseError { pos: usize, expected: String, actual: String },
    #[error("Variable not found: {0}")]
    VarNotFound(String),
    #[error("Division by zero")]
    DivByZero,
    #[error("Unknown function: {0}")]
    UnknownFunction(String),
    #[error("Type error: {0}")]
    TypeError(String),
    #[error("Evaluation error: {0}")]
    EvalError(String),
}
```

### Expression evaluation errors (decision_table_evaluator.py:173–175, 194–199, 209–212)
- Wrapped in generic `try/except Exception` with fallback to text value
- **Migration:** Replace with `Result<DmnValue, FeelError>`. The fallback-to-string behavior is a design smell — Rust should make fallback explicit.

### DMNExecutionError (engine.py:26)
- Thin wrapper around RuntimeError
- **Migration:** Single error variant in engine-level enum

### Invocation errors (invocation_handler.py:83–84)
- Caught `Exception` from FEEL evaluation, logged as binding error, continued execution
- **Migration:** `Result` type with error collection pattern

### Catch-all patterns
- `decision_table_evaluator.py:174, 199, 211` — `except Exception: pass` in `_test_input_entry`
- `decision_executor.py:167` — `except Exception` wrapping entire decision evaluation
- `literal_expression_eval.py:55, 60` — `except Exception: pass` in cascade

These are the weakest part of the current code. Rust's `Result` type enforces explicit error handling — no silent swallows.

---

## Summary Data

| Metric | Value |
|--------|-------|
| Total Python LOC | 2,193 |
| Files | 9 |
| FEEL engine (flagship target) | 874 lines (40%) |
| `eval()` calls | 7 (3 files) |
| `isinstance` chains | 6 sites |
| Dispatch dicts | 4 |
| `try/except Exception` catch-alls | 7+ |
| Dataclass->struct candidates | 12+ |
| External dependencies (stdlib only) | `re`, `datetime`, `math`, `eval()` |
| Migration score | **4.5** — pure computation, no I/O, heavy CPU |

### Recommended migration order
1. **FEELEngine** (parser + evaluator) — highest value, self-contained
2. **HitPolicyHandler** — trivial, removes one dispatch dict
3. **DecisionTableEvaluator** — depends on FEEL, replaces `eval()` calls
4. **InvocationHandler** — depends on FEEL
5. **DecisionRequirementsGraph** — independent, small
6. **DecisionExecutor** — async coordinator, needs pyo3-asyncio
7. **DMNEngine** — top-level async entry point
