# analysis_workflow.json

Here's the comprehensive `analysis_workflow.json` for systematic code analysis, metrics collection, and insight generation:

## Mermaid Dependency Graph

```mermaid
graph TD
    subgraph "Phase 1: Discovery"
        A[initialize_analysis]
        B[scan_project_structure]
        C[discover_files]
    end

    subgraph "Phase 2: Core Analysis"
        D[analyze_code_metrics]
        E[run_static_analysis]
        F[analyze_import_graph]
        G[analyze_dependencies]
        H[analyze_test_coverage]
        I[analyze_security]
        J[analyze_performance]
        K[analyze_documentation]
    end

    subgraph "Phase 3: Advanced Analysis"
        L[identify_code_smells]
        M[find_complexity_hotspots]
        N[identify_architectural_issues]
        O[analyze_evolution_trends]
        P[compare_with_benchmarks]
    end

    subgraph "Phase 4: Synthesis"
        Q[calculate_quality_scores]
        R[calculate_tech_debt]
        S[generate_recommendations]
        T[generate_visualizations]
    end

    subgraph "Phase 5: Output"
        U[generate_analysis_report]
        V[export_analysis_data]
        W[store_results]
        X[create_ci_report]
        Y[notify_stakeholders]
        Z[archive_analysis]
    end

    %% Phase 1 Dependencies
    A --> B --> C

    %% Phase 2 Dependencies
    C --> D
    C --> E
    C --> F
    C --> G
    C --> H
    C --> I
    C --> J
    C --> K

    %% Phase 3 Dependencies
    D --> L
    D --> M
    D --> N
    F --> N
    Q --> O
    Q --> P

    %% Phase 4 Dependencies
    D --> Q
    E --> Q
    H --> Q
    I --> Q
    J --> Q
    K --> Q
    L --> Q
    
    L --> R
    M --> R
    E --> R
    I --> R
    H --> R
    
    Q --> S
    R --> S
    
    F --> T
    M --> T
    H --> T
    O --> T

    %% Phase 5 Dependencies
    S --> U
    R --> U
    P --> U
    T --> U
    
    U --> V --> W
    Q --> X
    W --> Y
    X --> Y
    Y --> Z

    %% Critical Path Highlighting
    linkStyle 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200 stroke:red,stroke-width:3px;
    
    %% Style definitions
    classDef phase1 fill:#e1f5fe
    classDef phase2 fill:#fff3e0
    classDef phase3 fill:#e8f5e9
    classDef phase4 fill:#fce4ec
    classDef phase5 fill:#f3e5f5
    
    class A,B,C phase1
    class D,E,F,G,H,I,J,K phase2
    class L,M,N,O,P phase3
    class Q,R,S,T phase4
    class U,V,W,X,Y,Z phase5
```

## Key Features of Analysis Workflow:

### 1. **Comprehensive Metrics Collection**

| Metric Category | Specific Metrics | Tool |
|-----------------|-----------------|------|
| Code Metrics | LOC, Complexity, Maintainability | complexity_validator |
| Quality | Style violations, Best practices | ruff_validator |
| Dependencies | Import graph, Cycles | import_graph |
| Security | Vulnerabilities, Secrets | security_validator |
| Performance | Bottlenecks, Algorithms | performance_validator |
| Documentation | Docstring coverage | docstring_validator |
| Testing | Coverage, Gaps | coverage_analyzer |

### 2. **Quality Scoring Formula**

```javascript
quality_score = (
    complexity_score * 0.15 +
    static_analysis_score * 0.15 +
    test_coverage_score * 0.20 +
    security_score * 0.20 +
    performance_score * 0.10 +
    documentation_score * 0.10 +
    code_smells_score * 0.10
) * 100

health_score = (quality_score + maintainability_score) / 2
```

### 3. **Technical Debt Calculation**

```javascript
tech_debt_hours = 
    code_smells * 0.5 +
    complexity_issues * 2 +
    static_issues * 0.25 +
    security_issues * 4 +
    coverage_gaps * 1

debt_ratio = (tech_debt_hours / total_development_hours) * 100
```

### 4. **Analysis Depth Levels**

| Level | Scope | Time Estimate |
|-------|-------|---------------|
| Quick | Basic metrics only | 2-5 minutes |
| Standard | Full metrics + quality | 10-20 minutes |
| Comprehensive | All analyses + recommendations | 30-60 minutes |
| Deep | + Historical trends + Benchmarks | 1-2 hours |

### 5. **Code Smell Detection**

| Smell Type | Detection Method | Severity |
|------------|------------------|----------|
| Long Method | >50 lines | Medium |
| Large Class | >500 lines | High |
| Duplicate Code | AST comparison | Medium |
| Feature Envy | Method usage analysis | Low |
| Data Clumps | Parameter grouping | Low |
| Message Chains | Attribute access depth | Medium |

### 6. **Security Scan Rules**

```yaml
security_rules:
  critical:
    - sql_injection
    - command_injection
    - hardcoded_secrets
  high:
    - xss
    - path_traversal
    - weak_crypto
  medium:
    - log_injection
    - ssrf
    - xxe
  low:
    - insecure_deserialization
    - information_exposure
```

### 7. **Performance Patterns Detected**

| Pattern | Impact | Detection |
|---------|--------|-----------|
| N+1 Queries | High | ORM analysis |
| Inefficient Loops | Medium | Complexity analysis |
| Memory Leaks | High | Reference tracking |
| Blocking Calls | High | Async detection |
| Unoptimized Algorithms | Medium | Big-O analysis |

### 8. **Report Sections**

```
1. Executive Summary
   - Overall health score
   - Key findings
   - Critical issues
   
2. Quality Metrics
   - Code complexity
   - Maintainability
   - Documentation coverage
   
3. Security Assessment
   - Vulnerability summary
   - Critical findings
   - Recommendations
   
4. Performance Insights
   - Bottlenecks
   - Optimization opportunities
   
5. Dependency Analysis
   - Import graph
   - Circular dependencies
   - External dependencies
   
6. Technical Debt
   - Debt calculation
   - Interest estimation
   - Repayment plan
   
7. Recommendations
   - Critical fixes
   - Improvements
   - Best practices
```

### 9. **Visualization Outputs**

| Visualization | Format | Purpose |
|---------------|--------|---------|
| Dependency Graph | Mermaid/SVG | Module relationships |
| Complexity Heatmap | HTML | Hotspot identification |
| Coverage Map | HTML | Test gap visualization |
| Trend Charts | SVG | Historical analysis |

### 10. **Integration Points**

- **CI/CD**: Quality gates, badges
- **State Manager**: Result storage
- **Git**: Historical data
- **Notifications**: Slack, Email
- **Archiving**: Long-term storage

### 11. **Export Formats**

| Format | Use Case |
|--------|----------|
| JSON | API consumption |
| CSV | Spreadsheet analysis |
| HTML | Human-readable report |
| YAML | Configuration import |

### 12. **Benchmark Comparison**

```yaml
benchmark_categories:
  - industry_average
  - top_quartile
  - company_historical
  - open_source_reference
```

### 13. **Quality Thresholds**

| Metric | Excellent | Good | Poor |
|--------|-----------|------|------|
| Maintainability | >85 | 70-85 | <70 |
| Test Coverage | >90% | 80-90% | <80% |
| Complexity | <5 | 5-10 | >10 |
| Tech Debt Ratio | <5% | 5-20% | >20% |

### 14. **Analysis Workflow States**

```
INITIALIZED → DISCOVERY → ANALYSIS → SYNTHESIS → REPORTING → COMPLETED
     ↓           ↓          ↓          ↓           ↓
  VALIDATED   SCANNED   METRICS    SCORES      EXPORTED
```

### 15. **Performance Optimizations**
- Parallel file processing
- Incremental analysis
- Caching of results
- Streaming for large files
- Memory-efficient processing

This workflow provides comprehensive code analysis with actionable insights, quality metrics, security assessments, and performance recommendations to guide improvement efforts.