Here's the comprehensive `onboarding_workflow.json` for managing new team member onboarding, training, and integration:

## Mermaid Dependency Graph

```mermaid
graph TD
    subgraph "Phase 1: Initiation"
        A[initiate_onboarding]
        B[validate_onboarding_data]
        C[human_verify_details]
    end

    subgraph "Phase 2: Mentorship"
        D[assign_mentor]
        E[mentor_accept_assignment]
    end

    subgraph "Phase 3: Environment Setup"
        F[create_accounts]
        G[request_equipment]
        H[setup_development_environment]
        I[verify_environment]
    end

    subgraph "Phase 4: Training"
        J[create_training_plan]
        K[human_review_training_plan]
        L[schedule_training_sessions]
        M[deliver_training_module]
        N[assess_module_completion]
        O[provide_module_feedback]
        P{check_training_progress}
        Q[next_training_module]
        R[final_assessment]
    end

    subgraph "Phase 5: Evaluation"
        S[evaluate_final_assessment]
        T[human_review_assessment]
        U[assign_first_task]
        V[mentor_support_task]
        W[complete_first_task]
        X[review_first_task]
        Y[calculate_readiness_score]
        Z[human_readiness_review]
    end

    subgraph "Phase 6: Integration"
        AA[create_onboarding_report]
        AB[update_team_roster]
        AC[schedule_checkpoints]
        AD[collect_onboarding_feedback]
        AE[collect_mentor_feedback]
        AF[update_skill_registry]
        AG[generate_certificate]
        AH[notify_team]
        AI[archive_onboarding_data]
    end

    %% Dependencies
    A --> B --> C --> D
    D --> E --> F --> G --> H --> I
    
    I --> J --> K --> L --> M --> N --> O --> P
    
    P -- "false" --> Q --> M
    P -- "true" --> R --> S --> T --> U --> V --> W --> X --> Y --> Z
    
    Z --> AA
    Z --> AB --> AC
    Z --> AD
    Z --> AE
    Z --> AF --> AG --> AH --> AI
    
    AA --> AH
    
    %% Critical Path Highlighting
    linkStyle 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30 stroke:red,stroke-width:3px;
    
    %% Style definitions
    classDef phase1 fill:#e1f5fe
    classDef phase2 fill:#fff3e0
    classDef phase3 fill:#e8f5e9
    classDef phase4 fill:#fce4ec
    classDef phase5 fill:#f3e5f5
    classDef phase6 fill:#e0f2f1
    
    class A,B,C phase1
    class D,E phase2
    class F,G,H,I phase3
    class J,K,L,M,N,O,P,Q,R phase4
    class S,T,U,V,W,X,Y,Z phase5
    class AA,AB,AC,AD,AE,AF,AG,AH,AI phase6
```

## Key Features of Onboarding Workflow:

### 1. **Pre-Onboarding Phase**
- Data validation and verification
- Manager approval
- Resource allocation planning

### 2. **Mentorship Assignment**
- Smart mentor matching based on skills and availability
- Mentor acceptance workflow
- Mentoring guidelines and expectations

### 3. **Account & Environment Setup**
- Multi-system account creation
- Equipment provisioning
- Development environment configuration
- Access permission management

### 4. **Personalized Training**
- Role-specific training modules
- Experience level adaptation
- Interactive training delivery
- Module assessment with passing score (80%)
- Feedback collection per module

### 5. **Training Modules Structure**
| Module Type | Examples | Duration |
|-------------|----------|----------|
| Core | Project overview, coding standards | 2-3 days |
| Role-specific | API dev, DevOps, QA, Frontend | 5-7 days |
| Advanced