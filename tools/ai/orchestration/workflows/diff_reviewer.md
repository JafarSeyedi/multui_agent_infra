# diff_reviewer.json
Here's the comprehensive `diff_reviewer.json` for intelligent code diff analysis, review, and integration:


## Mermaid Dependency Graph

```mermaid
graph TD
    subgraph "Phase 1: Diff Ingestion"
        A[receive_diff]
        B[parse_diff_structure]
        C[load_base_context]
        D[load_head_context]
    end

    subgraph "Phase 2: Analysis"
        E[analyze_syntax_changes]
        F[analyze_style_changes]
        G[analyze_complexity_change]
        H[analyze_dependency_impact]
        I[analyze_test_impact]
        J[calculate_coverage_impact]
        K[run_security_scan_diff]
        L[analyze_performance_impact]
        M[analyze_api_changes]
        N[analyze_documentation_impact]
    end

    subgraph "Phase 3: Risk Assessment"
        O[calculate_risk_score]
        P[generate_auto_review]
        Q[suggest_improvements]
        R[check_merge_readiness]
    end

    subgraph "Phase 4: Decision"
        S{ready_for_merge?}
        T[auto_approve]
        U[human_review_required]
        V[process_human_feedback]
        W{approved?}
        X[generate_change_requests]
    end

    subgraph "Phase 5: Execution"
        Y[post_review_comments]
        Z[update_pr_status]
        AA[generate_review_report]
        AB[notify_review_complete]
        AC[archive_review_data]
        AD[auto_merge_if_approved]
    end

    %% Phase 1 Dependencies
    A --> B
    B --> C
    B --> D

    %% Phase 2 Dependencies
    C --> E
    C --> F
    C --> G
    C --> H
    C --> I
    C --> J
    C --> K
    C --> L
    C --> M
    C --> N

    D --> E
    D --> F
    D --> G
    D --> H
    D --> I
    D --> J
    D --> K
    D --> L
    D --> M
    D --> N

    %% Phase 3 Dependencies
    E --> O
    F --> O
    G --> O
    H --> O
    I --> O
    J --> O
    K --> O
    L --> O
    M --> O
    N --> O

    O --> P
    P --> Q
    O --> R
    P --> R
    Q --> R

    %% Phase 4 Dependencies
    R --> S
    
    S -- "true (low risk)" --> T
    S -- "false (needs review)" --> U
    
    T --> Y
    
    U --> V
    V --> W
    
    W -- "approved" --> Y
    W -- "changes requested" --> X --> Y

    %% Phase 5 Dependencies
    Y --> Z
    Z --> AA
    AA --> AB
    AB --> AC
    Y --> AD

    %% Critical Path Highlighting
    linkStyle 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40 stroke:red,stroke-width:3px;
    
    %% Style definitions
    classDef phase1 fill:#e1f5fe
    classDef phase2 fill:#fff3e0
    classDef phase3 fill:#e8f5e9
    classDef phase4 fill:#fce4ec
    classDef phase5 fill:#f3e5f5
    
    class A,B,C,D phase1
    class E,F,G,H,I,J,K,L,M,N phase2
    class O,P,Q,R phase3
    class S,T,U,V,W,X phase4
    class Y,Z,AA,AB,AC,AD phase5
```

## Key Features of Diff Reviewer Workflow:

### 1. **Comprehensive Diff Analysis**
- File-level and line-level change detection
- Binary file detection
- Hunk parsing and metadata extraction
- Before/after context loading

### 2. **Multi-Dimensional Analysis**

| Analysis Type | Component | Focus Areas |
|---------------|-----------|-------------|
| Syntax | mypy_validator | Type errors, syntax correctness |
| Style | ruff_validator | Code style, formatting, best practices |
| Complexity | complexity_validator | Cyclomatic, cognitive complexity |
| Dependencies | dependency_validator | Import changes, circular deps |
| Tests | test_runner | Affected tests, new test needs |
| Coverage | coverage_analyzer | Coverage impact analysis |
| Security | security_validator | Vulnerability detection |
| Performance | performance_validator | Algorithm changes, regressions |
| API | api_surface_extractor | Breaking changes, compatibility |
| Documentation | docstring_validator | Docstring updates needed |

### 3. **Risk Scoring Algorithm**

```javascript
risk_score = (
    syntax_issues * 25 +
    critical_security_issues * 30 +
    breaking_changes * 20 +
    complexity_increase * 10 +
    coverage_decrease * 10 +
    performance_degradation * 5
) / 100

Risk Levels:
- 0-30: Low Risk (Auto-approve)
- 31-60: Medium Risk (Human review recommended)
- 61-100: High Risk (Required human review)
```

### 4. **Auto-Review Generation**
- LLM-powered review comments
- Inline code suggestions
- Constructive feedback formatting
- Context-aware recommendations

### 5. **Human Review Interface**

| Feature | Description |
|---------|-------------|
| Diff Visualization | Side-by-side comparison |
| Risk Assessment | Color-coded risk indicators |
| Auto Comments | Pre-populated review comments |
| Decision Options | Approve, Request Changes, Comment |
| Timeout | 12-24 hours based on risk |

### 6. **Merge Readiness Criteria**

Auto-merge allowed when:
- Risk score ≤ 30
- No critical security issues
- No syntax errors
- No breaking API changes
- Tests pass (if applicable)

### 7. **PR Integration**

| Action | Method |
|--------|--------|
| Post comments | Inline and summary comments |
| Update status | Success/Pending/Failure |
| Request changes | Block merge until resolved |
| Auto-merge | Squash merge with branch deletion |

### 8. **Review Outputs**

```yaml
Outputs:
  - Review comments (inline + summary)
  - Risk assessment report
  - Suggested improvements
  - Change requests (if needed)
  - Approval status
  - Merge decision
```

### 9. **Security Scan Rules**
- SQL Injection detection
- XSS vulnerability scanning
- Command injection patterns
- Hardcoded secret detection
- Weak cryptography identification
- Path traversal vulnerabilities

### 10. **Performance Impact Detection**
- Algorithm complexity changes (O(n) → O(n²))
- Database query pattern changes
- Memory usage implications
- Caching pattern modifications

### 11. **API Compatibility Check**
- Breaking change detection
- Deprecated API usage
- Parameter type changes
- Return type modifications
- Exception specification changes

### 12. **Test Impact Analysis**
- Identify affected tests
- Suggest new test cases
- Coverage impact prediction
- Regression risk assessment

### 13. **Documentation Impact**
- Detect docstring changes
- Identify undocumented functions
- Suggest documentation updates
- API documentation coverage

### 14. **Notification Channels**
- Slack (real-time updates)
- Event bus (system integration)
- PR comments (GitHub/GitLab)
- Email (for critical issues)

### 15. **Review Decision Flow**

```
Diff Received
    ↓
Auto Analysis
    ↓
Risk Score ≤ 30? 
    ↓ YES → Auto Approve → Auto Merge
    ↓ NO → Human Review Required
           ↓
        Human Decision
           ↓
    Approve → Merge
    Request Changes → Post Changes → Wait for Update
```

This workflow provides comprehensive, intelligent code review with appropriate automation for low-risk changes and thorough human oversight for complex or risky modifications.