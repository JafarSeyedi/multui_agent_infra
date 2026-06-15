## Implementation Classification: Build vs. Integrate

The table below classifies each significant tool/component from the 65 domains into one of four types:

- **Infrastructure (I)**: External, pre‑existing infrastructure software (databases, message brokers, Kubernetes, cloud services). We deploy and configure them but do not modify their code. Configuration is done via their native models.
- **Library (L)**: Software library integrated into one of our custom engines (e.g., a parsing library, a client SDK). It becomes part of our codebase.
- **Service/Container (S)**: A pre‑built software component that we run as a service (Docker container, Pod) and integrate with via API or protocol. We may wrap it with a thin API but not re‑implement its core. Examples: Keycloak, Elasticsearch, Kong.
- **Engine to Develop (E)**: Core logic that we must build ourselves because it is model‑driven and unique to our platform. This includes our process engine, content processing engine, agent orchestration engine, MCP server gateway, etc. We own the code.

*Assumptions*: We choose best‑of‑breed open‑source or cloud services for infrastructure, and focus custom development on model‑driven engines that differentiate our platform.

| Domain | Domain Name | Component / Sub‑domain | Type | Notes |
|--------|-------------|------------------------|------|-------|
| 1 | Runtime Infrastructure & Orchestration | Kubernetes (K8s) | I | Platform infrastructure; we run clusters. |
|  |  | Container runtime (containerd, etc.) | I | Part of K8s nodes. |
| 2 | Service Discovery & Registry | Consul | S | Runs as a service; we integrate via API/DNS. |
|  |  | Agent Registry (custom) | E | Our registry for agents, built on top of Consul KV. |
| 3 | Inter‑Service Communication | OpenAPI/gRPC service generation | L | Code generation libraries (protoc, openapi-generator) used inside services. |
|  |  | Kafka client library | L | Integrated into our microservices. |
|  |  | Resilience4j / Polly | L | Integrated into service code for circuit breakers. |
| 4 | Service Mesh | Linkerd / Istio | I | Run as infrastructure; sidecar injection. |
| 5 | Northbound Exposure (API Gateway) | Kong | S | Runs as a service; we configure with declarative models. |
|  |  | Envoy (if used standalone) | S | Same as above. |
| 6 | Southbound Integration | Apache Camel | L | Embedded in our integration engine or run as standalone. We use its components. |
|  |  | Kafka Connect | S | Run as a service; we provide connector configs. |
| 7 | State & Caching | Redis | I | Infrastructure (Redis Cluster). |
|  |  | Hazelcast | L | Library embedded in our services for distributed state. |
| 8 | Configuration & Secrets Management | Vault | S | Run as a service; our engines use its API. |
|  |  | Consul KV | I | Part of Consul (above). |
| 9 | Event Streaming & Event‑Driven Architecture | Kafka / NATS | I | Infrastructure; we run clusters. |
|  |  | Confluent Schema Registry | S | Run as a service; integrates with Kafka. |
|  |  | Kafka Streams / Flink | L | Library used inside our stream processors. |
| 10 | Data Consistency & Distributed Transactions | Saga coordinator (our process engine) | E | We build the saga logic as part of the process engine. |
|  |  | Debezium (CDC) | S | Run as a service; connects to DB. |
| 11 | Observability | OpenTelemetry Collector | S | Run as a service (DaemonSet). |
|  |  | Prometheus / Grafana LGTM | I | Infrastructure; we configure dashboards. |
|  |  | LangSmith | S | SaaS/external service for LLM tracing. |
| 12 | Security | OPA | S | Run as a service; Rego policies are our model. |
|  |  | Keycloak | S | Identity provider service; configured via JSON/HCL. |
|  |  | cert‑manager | S | Run in K8s for certificate automation. |
| 13 | Agentic Systems & AI‑Native Integration | MCP server gateway | E | Custom gateway that routes and authorizes tool calls. |
|  |  | MCP tool servers (specific tools) | E | We develop tool wrappers (thin services that adapt existing APIs). |
|  |  | A2A message router | E | Build logic on top of Kafka; envelope handling. |
|  |  | Agent workflow engine | E | Built as part of our process engine (supports BPMN). |
|  |  | Multi‑agent strategy engine | E | Custom orchestration logic (LangGraph integration). |
|  |  | Skills engine | E | Registry and executor for skills, built by us. |
|  |  | Agent memory service | E | Thin service wrapping Redis/Vector DB; we develop API. |
|  |  | Code execution sandbox | E | We build using gVisor library and expose as MCP tool. |
| 14 | UI Backend & Frontend Development | Next.js / Remix | S | Framework; we run as a Node.js service. BFF logic custom code. |
|  |  | Storybook, Figma | I | Design tools (external); Figma is SaaS. |
|  |  | Formily | L | Library integrated into our frontend. |
|  |  | Nx / Turborepo | L | Build tooling (Node packages). |
| 15 | Load Balancing & Traffic Routing | HAProxy / Nginx | I | Infrastructure; we configure. |
|  |  | Cloudflare / Route53 | I | External services. |
| 16 | Data Persistence & Storage | PostgreSQL, MongoDB, Neo4j, etc. | I | Run as databases (infrastructure). |
|  |  | pgvector | L | PostgreSQL extension (infra). |
|  |  | Qdrant | S | Vector DB service. |
|  |  | MinIO / S3 | I | Object storage; S3 is cloud service. |
| 17 | Business Process & Workflow Orchestration | **Our Process Engine (BPMN, CMMN, DMN)** | **E** | Core engine; we develop completely. |
|  |  | Camunda (if used) | S | May be used as a library or standalone; in our case, we build our own but can embed. |
|  |  | Scripting sandbox (GraalVM/gVisor) | L/E | We integrate libraries and build the sandbox engine. |
|  |  | Human task UI integration | E | We build the integration with our UI Backend and Formily. |
|  |  | BAM dashboards | I | Uses Grafana (infrastructure). |
| 18 | Knowledge & Analytics | Apache Superset | S | Run as a service; we configure dashboards. |
|  |  | dbt | L | Data transformation tool; we run as CLI. |
|  |  | MLflow | S | Model registry; run as service. |
|  |  | RAG pipeline orchestrator | E | Custom engine that coordinates ingestion, retrieval, and LLM calls. |
| 19 | Tool Integration & Abstraction | MCP servers (generic) | E | We develop the servers and registry. |
|  |  | Apache Camel (as adapter) | L | Used in tool adapters; we embed. |
| 20 | Content Processing & Document Abstraction | Pandoc, Apache Tika | L | Libraries integrated into our content engine. |
|  |  | LibreOffice (headless) | S | Run as a service (container) for conversions. |
|  |  | Whisper / Tesseract | L/S | ASR/OCR; we either embed models or call as service. |
|  |  | Canonical model engine | E | Core document abstraction engine we build. |
| 21 | Developer Experience & Platform Engineering | Backstage | S | Run as a service; we configure plugins and templates. |
|  |  | Crossplane | S | Run in K8s; we define XRDs. |
| 22 | CI/CD | GitHub Actions / Jenkins | I | External CI services; we provide pipeline YAML. |
|  |  | Argo CD | S | GitOps tool; run in K8s. |
| 23 | Testing | k6, Playwright, Pact | L/S | Testing tools; we run as part of CI or as libraries. |
| 24 | IAM | Keycloak | S | Identity provider service. |
|  |  | OPA | S | Policy engine service. |
|  |  | Casbin | L | Embedded library if needed. |
| 25 | Compliance & Audit | Vanta / Drata | I | External SaaS for compliance automation. |
|  |  | OPA (policies) | S | Already covered. |
| 26 | Cost Management | Kubecost | S | Run in K8s as service. |
|  |  | Infracost | L | CLI tool integrated into CI. |
| 27 | Disaster Recovery | Velero | S | Run as a service in K8s. |
|  |  | Cloud‑native backup | I | AWS Backup, etc. |
| 28 | API Lifecycle | Spectral | L | Linter library; integrated into CI. |
|  |  | Stoplight / SwaggerHub | I | External SaaS or tools. |
| 29 | Multi‑Tenancy | PostgreSQL RLS | I | Database feature; we configure via SQL. |
|  |  | Kong (tenant routing) | S | We configure plugins. |
| 30 | Edge Computing | K3s, KubeEdge | I | Edge infrastructure. |
|  |  | WasmEdge | L/I | Edge runtime; we deploy. |
| 31 | Service Versioning | Confluent Schema Registry | S | Infrastructure. |
|  |  | Apicurio | S | Alternative schema registry. |
| 32 | High Availability | etcd | I | Infrastructure. |
| 33 | Data Privacy | Google Cloud DLP | I | External service. |
|  |  | Vault Transform | E | Part of Vault; configuration is our model. |
| 34 | Data Pipelines | Airflow | S | Run as service. |
|  |  | dbt | L | We run as CLI; models are YAML/SQL. |
|  |  | Debezium | S | Service for CDC. |
| 35 | Digital Twins | Azure Digital Twins | I | Cloud service. |
|  |  | Eclipse Ditto | S | Open‑source, run as service. |
| 36 | Scheduling | Kubernetes CronJob | I | Built‑in. |
|  |  | Temporal | S | Run as service if we adopt it; otherwise our process engine. |
| 37 | Notifications | Novu / Courier | S | Run as service or SaaS. |
|  |  | SendGrid | I | External email API. |
| 38 | Localization | Crowdin | I | SaaS translation management. |
|  |  | FormatJS | L | Library for frontend i18n. |
| 39 | Licensing | LaunchDarkly | S | Feature flag service. |
|  |  | Stripe Billing | I | Payment/subscription API. |
| 40 | Search | Elasticsearch / OpenSearch | I | Infrastructure. |
| 41 | A/B Testing | LaunchDarkly | S | Same as 39. |
| 42 | MLOps | MLflow | S | Run as service. |
|  |  | Weights & Biases | I | SaaS. |
|  |  | LangSmith | S | SaaS. |
| 43 | Synthetic Data | Gretel | I | SaaS. |
|  |  | SDV | L | Python library; integrated into our pipelines. |
| 44 | Blockchain | Hyperledger Fabric | I | Run a network; chaincode we develop. |
| 45 | Quantum‑Safe Crypto | OpenQuantumSafe | L | Library integrated into our crypto layer. |
|  |  | AWS KMS PQ | I | Cloud service. |
| 46 | Capacity Planning | k6 | L/S | Load testing tool. |
|  |  | Karpenter | S | K8s autoscaler. |
| 47 | Data Governance | DataHub | S | Metadata platform. |
|  |  | Great Expectations | L | Library integrated into pipelines. |
| 48 | Service Catalog | Backstage | S | Already covered. |
| 49 | Session Replication | Redis (cluster) | I | Already covered. |
| 50 | MDM | Microsoft Intune | I | SaaS. |
|  |  | TestFlight | I | Apple service. |
| 51 | Voice | Twilio | I | External API. |
|  |  | Dialogflow | I | Google Cloud service. |
| 52 | Block Storage | Rook/Ceph | S | Run in K8s as storage cluster. |
|  |  | AWS EBS | I | Cloud infrastructure. |
| 53 | Message Transformation | Camel K | S/L | Can be run as operator or embedded. We use as library inside our engine. |
| 54 | Time Sync | chrony | I | System daemon on nodes. |
| 55 | Document Lifecycle | S3 Object Lock | I | Cloud feature; we configure. |
| 56 | HSM | AWS CloudHSM | I | Cloud service. |
|  |  | Vault (HSM backend) | S | Vault with HSM integration. |
| 57 | Network Firewall | AWS Network Firewall | I | Cloud service. |
|  |  | Calico / Cilium | S | K8s CNI with network policies. |
| 58 | IaC | Terraform / Pulumi | I/L | CLI tools; HCL/YAML is the model. |
| 59 | Environment Management | Argo CD | S | GitOps tool. |
| 60 | Schema Migration | Flyway / Liquibase | L | Libraries integrated into our CD pipeline or as init containers. |
| 61 | Data Archival | S3 Glacier | I | Cloud service. |
| 62 | Incident Response | Splunk / Elastic Security | I | External tools. |
|  |  | Velociraptor | S | Run as service for forensics. |
| 63 | Sustainability | Cloud Carbon Footprint | S | Run as service (or SaaS). |
| 64 | Multi‑Cloud | Crossplane | S | K8s controller. |
| 65 | Data Masking | Delphix | I | External appliance. |
|  |  | Tonic | I | SaaS. |

---

*The two tables together form the backbone of a model‑driven, hybrid build‑vs‑buy strategy. All custom engines (E) are designed to execute the standardised models listed in the first table, while all infrastructure and services are configured using those same models.*