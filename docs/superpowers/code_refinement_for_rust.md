# Rust Migration Preparation Prompt

You are an expert in both Python and Rust, specializing in safe, incremental migration strategies. I need you to analyze and refactor my Python codebase to make it "Rust-ready" - meaning the code can be cleanly and safely migrated to Rust using PyO3, with minimal friction.

## Context
- I am building an Agentic Business Process Management System (BPMS)
- Current Python version: 3.12+
- Target: Incremental migration of performance-critical paths to Rust
- Migration tool: PyO3 + maturin
- I will use AI-assisted translation after this refactoring

## Primary Goals

### 1. Type System Preparation
- Add complete type hints to ALL functions and methods
- Replace `Dict[str, Any]` with concrete dataclasses or TypedDict
- Replace `Union` and `Optional` with `|` syntax (Python 3.10+)
- Use `TypeAlias` for complex type definitions
- Mark pure functions with `@staticmethod` or module-level functions
- Identify and document ownership semantics (who owns/mutates each data structure)

### 2. Data Structure Modernization
- Replace mutable dictionaries with `dataclass` or `pydantic.BaseModel`
- Replace nested conditionals with pattern matching (Python 3.10+ `match`)
- Use `enum.Enum` or `enum.StrEnum` for all constants and state values
- Make immutable data structures with `@dataclass(frozen=True)`
- Replace inheritance with composition where possible
- Eliminate monkey patching and dynamic attribute assignment

### 3. Error Handling Restructuring
- Replace bare `except:` with specific exception types
- Create a proper exception hierarchy for domain errors
- Convert functions that return `None` on error to raise exceptions
- Identify functions where returning `Result` type (Rust pattern) would be beneficial
- Remove exception swallowing and silent failures

### 4. Ownership and Mutability Documentation
- Add comments indicating function ownership:
  - `# Takes ownership of: x, y`
  - `# Borrows immutably: config`
  - `# Borrows mutably: state`
  - `# Returns new owned value`
- Mark functions with side effects clearly with `# SIDE EFFECTS: modifies database` (in the reports outputs not just in the code)
- Separate pure functions from impure functions into different modules

### 5. Performance Hot Path Identification
- Flag functions that are called >1000x per second with `# HOT_PATH`(report in the reports outputs not just in the code)
- Identify CPU-bound functions (calculations, validation, state transitions) (report in the reports outputs not just in the code)
- Identify allocation-heavy functions (frequent list/dict creation) (report in the reports outputs not just in the code)
- Mark functions that would benefit from zero-copy operations (report in the reports outputs not just in the code)

### 6. Dependency Decoupling
- Remove circular imports (essential for Rust migration)
- Move I/O operations to the boundaries (not deep in business logic)
- Replace global state with explicit dependency injection
- Abstract external services behind clear interfaces

### 7. PyO3-Specific Preparation
- Ensure all Python functions exposed to Rust have:
  - No default arguments (or document default values explicitly)
  - All parameters type-hinted
  - Return type explicitly stated
- Mark functions that should become Rust with `# RUST_CANDIDATE` (report in the reports outputs not just in the code)
- Mark functions that must stay in Python with `# PYTHON_ONLY` (report in the reports outputs not just in the code)
- Identify which Python exceptions should map to Rust error types (report in the reports outputs not just in the code)

## Output Requirements

For EACH module/file, provide:

1. **Pre-refactor analysis**: List of Rust-migration blockers found
2. **Refactored code**: Complete rewritten module (the root folder is rust and the subfolders must be matched with the current folder structure (rust/engines,rust/engines/orchestration, ...))
3. **Migration notes**: Which functions are good Rust candidates (priority 1-5)
4. **Ownership map**: Table showing who owns each data structure
5. **Suggested PyO3 binding structure**: How the Rust API should look
6. **Libraries analysis** rust library alterantives, libraries that do not have alternatives, how to use pyo3 to use python libraries in rust code.
7. A report for each module containg all above requested reports: (report in the reports outputs not just in the code)
8. all other ooutput artifacts must be in rust/migration_reports folder

## Code to Analyze

all the project