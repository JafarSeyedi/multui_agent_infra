# code_review_workflow.json

Here's the comprehensive `code_review_workflow.json` for systematic code review with multiple reviewers, quality gates, and automated analysis:

## Mermaid Dependency Graph

```mermaid
graph TD
    subgraph "Phase 1: Request & Analysis"
        A[receive_code_review_request]
        B[fetch_code_changes]
        C[analyze_code_metrics]
        D[run_static_analysis]
        E[run_type_checking]
        F[analyze_test_coverage]
        G[run_security_scan]
        H[analyze_performance]
        I[analyze_dependencies]
    end

    subgraph "Phase 2: Scoring & Automation"
        J[calculate_overall_score]
        K[identify_critical_issues]
        L[generate_auto_review]
        M[determine_reviewers]
        N[assign_reviewers]
        O[schedule_review_deadline]
    end

    subgraph "Phase 3: Human Reviews"
        P[technical_review]
        Q[security_review]
        R[performance_review]
        S[architecture_review]
    end

    subgraph "Phase 4: Consolidation"
        T[consolidate_reviews]
        U{check_approval_status}
    end

    subgraph "Phase 5: Decision & Actions"
        V[request_changes]
        W[wait_for_updates]
        X[revalidate_updates]
        Y[approve_pr]
    end

    subgraph "Phase 6: Finalization"
        Z[generate_review_report]
        AA[post_report_to_pr]
        AB[update_ci_status]
        AC[notify_completion]
        AD[archive_review_data]
    end

    %% Phase 1 Dependencies
    A --> B
    B --> C
    B --> D
    B --> E
    B --> F
    B --> G
    B --> H
    B --> I

    %% Phase 2 Dependencies
    C --> J
    D --> J
    E --> J
    F --> J
    G --> J
    H --> J
    I --> J

    G --> K
    E --> K
    F --> K
    C --> K

    J --> L
    B --> M
    M --> N --> O
    L --> O

    %% Phase 3 Dependencies
    L --> P
    N --> P
    L --> Q
    N --> Q
    L --> R
    N --> R
    L --> S
    N --> S

    %% Phase 4 Dependencies
    P --> T
    Q --> T
    R --> T
    S --> T
    T --> U

    %% Phase 5 Dependencies
    U -- "changes_requested" --> V --> W --> X --> T
    U -- "approved" --> Y

    %% Phase 6 Dependencies
    Y --> Z
    V --> Z
    Z --> AA --> AB --> AC --> AD

    %% Critical Path Highlighting
    linkStyle 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90 stroke:red,stroke-width:3px;
    
    %% Style definitions
    classDef phase1 fill:#e1f5fe
    classDef phase2 fill:#fff3e0
    classDef phase3 fill:#e8f5e9
    classDef phase4 fill:#fce4ec
    classDef phase5 fill:#f3e5f5
    classDef phase6 fill:#ffe0b2
    
    class A,B,C,D,E,F,G,H,I phase1
    class J,K,L,M,N,O phase2
    class P,Q,R,S phase3
    class T,U phase4
    class V,W,X,Y phase5
    class Z,AA,AB,AC,AD phase6
```

## Key Features of Code Review Workflow:

### 1. **Comprehensive Automated Analysis**

| Analysis Type | Tool | Metrics |
|---------------|------|---------|
| Code Metrics | complexity_validator | Cyclomatic complexity, maintainability |
| Static Analysis | ruff_validator | Code style, best practices |
| Type Checking | mypy_validator | Type safety, return types |
| Test Coverage | coverage_analyzer | Line/branch coverage |
| Security | security_validator | Vulnerability detection |
| Performance | performance_validator | Algorithm efficiency |
| Dependencies | dependency_validator | Import cycles, violations |

### 2. **Quality Scoring Formula**

```javascript
overall_score = (
    complexity * 0.15 +
    static_analysis * 0.15 +
    type_checking * 0.10 +
    coverage * 0.15 +
    security * 0.20 +
    performance * 0.15 +
    dependencies * 0.10
) * 100

Passing Threshold: 75%
```

### 3. **Review Types & Assignees**

| Review Type | Focus Areas | Required Skills | Priority |
|-------------|-------------|-----------------|----------|
| Technical | Logic, implementation, tests | Code review, programming | High |
| Security | Vulnerabilities, secure coding | Security review | Critical |
| Performance | Efficiency, optimization | Performance engineering | Medium |
| Architecture | Patterns, structure | System design | High |

### 4. **Review Configuration**

```yaml
review_config:
  required_reviewers: 2
  min_approvals: 2
  review_timeout_hours: 48
  allow_self_approval: false
  require_ci_passed: true
```

### 5. **Automated Review Generation**
- LLM-powered review comments
- Inline suggestions
- Code improvement recommendations
- Pattern-based issue detection

### 6. **Critical Issues Detection**

| Severity | Examples | Action |
|----------|----------|--------|
| Critical | Security vulnerabilities, Type errors | Block merge |
| High | Test failures, Complexity violations | Required fix |
| Medium | Style issues, Optimization opportunities | Suggested fix |
| Low | Documentation, Minor improvements | Optional |

### 7. **Review Workflow States**

```
PENDING → ANALYSIS → AUTO_REVIEW → REVIEWER_ASSIGNMENT
                                    ↓
                            TECHNICAL_REVIEW
                            SECURITY_REVIEW
                            PERFORMANCE_REVIEW
                            ARCHITECTURE_REVIEW
                                    ↓
                            CONSOLIDATION
                                    ↓
                    ┌───────────────┴───────────────┐
                    ↓                               ↓
            APPROVED                    CHANGES_REQUESTED
                    ↓                               ↓
            MERGE_READY                     WAIT_FOR_UPDATES
                                                    ↓
                                            REVALIDATE
                                                    ↓
                                            (Loop to REVIEW)
```

### 8. **Action Items Categorization**
- **Required** (must fix before merge)
- **Recommended** (should fix)
- **Optional** (nice to have)
- **Question** (clarification needed)

### 9. **Git Integration**
- Auto-assign reviewers to PR
- Post review comments inline
- Update PR status (approved/changes requested)
- Block merge until approvals received

### 10. **Reporting Artifacts**

| Artifact | Format | Content |
|----------|--------|---------|
| Quality Report | HTML | Metrics, scores, recommendations |
| Review Summary | Markdown | PR comment with key findings |
| Action Items | List | Required and optional fixes |
| Archived Data | JSON | Complete review history |

### 11. **Notification Channels**
- Slack (real-time updates)
- Email (review assignments)
- Event Bus (system integration)
- PR Comments (GitHub/GitLab)

### 12. **Quality Gates**

| Gate | Requirement | Blocking |
|------|-------------|----------|
| CI Passed | All tests pass | Yes |
| Security Scan | No critical issues | Yes |
| Type Checking | No type errors | Yes |
| Coverage | ≥80% | No (warning) |
| Complexity | ≤10 per function | No (warning) |
| Reviewers | ≥2 approvals | Yes |

### 13. **Timeouts & Escalation**
- Initial review: 48 hours
- Change requests: 72 hours
- Escalation after timeout
- Automatic reminders

### 14. **Learning & Improvement**
- Track review patterns
- Identify common issues
- Improve automated suggestions
- Update review guidelines

### 15. **Success Criteria**

Code is approved when:
- All required reviewers approved
- No critical issues remain
- CI pipeline passes
- Quality score ≥ 75%
- All requested changes addressed

This workflow ensures thorough, consistent code review with automated analysis, multi-perspective human review, quality gates, and comprehensive tracking throughout the process.