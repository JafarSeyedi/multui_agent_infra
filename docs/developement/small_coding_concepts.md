
You are coding a Python platform/infrastructure (BPMS, multi-agent AI, model-driven). Follow these principles strictly:

1. Model-Driven: Models are source of truth
2. Extensible core (not complete) — use plugins/hooks
3. SoC: Separate engine, storage, security, logging
4. CoC: Smart defaults everywhere
5. DI: Constructor injection only (no internal instantiation)
6. ISP: Small ABCs/Protocols, no fat interfaces
7. Composition over inheritance
8. Explicit over implicit, readable over clever
9. Fail fast with clear errors
10. DRY and KISS

Anti-patterns to avoid: God classes, hidden deps, singletons, deep inheritance (>2 levels).

Always use type hints. Always inject dependencies via __init__.