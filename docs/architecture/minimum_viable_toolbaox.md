### Minimum Viable Toolbox

The toolbox below selects lean, proven tools that collectively satisfy all sixty‑five domains while avoiding overlap. The organisation’s own process engine is central; Dapr is optional but not required.

**Foundation & Orchestration**  
- Kubernetes – container orchestration, self‑healing, scheduling  
- Our Process Engine – BPMN, CMMN, DMN, state machines, human tasks, agentic workflows

**Global & Edge Traffic (Domains 15, 57, 64)**  
- Cloudflare / AWS Route 53 – global DNS, DDoS, WAF  
- Nginx / HAProxy – edge L7 reverse proxy, TLS termination, consistent hashing  
- Terraform / Crossplane – multi‑cloud infrastructure provisioning

**API Gateway & Integration (Domains 5, 19, 28, 48, 53)**  
- Kong – API management, authentication, rate limiting, MCP tool gateway  
- MCP Servers – standardised tool exposure, tool registry, parameter mapping  
- Backstage – developer portal, service catalog, API documentation

**Experience Delivery (Domains 14, 38, 41, 50, 51)**  
- Next.js – SSR, BFF API routes, static export  
- Socket.IO – real‑time WebSocket server  
- Nx / Turborepo – monorepo for React web and React Native  
- Storybook + Figma + Style Dictionary – design system  
- Alibaba Formily – schema‑driven forms  
- Crowdin / Lokalise – translation management  
- LaunchDarkly / Unleash – feature flags and A/B testing  
- Microsoft Intune / Jamf – mobile device management  
- Twilio / Amazon Connect – voice and conversational channels

**Application Core (Domains 3, 6, 13, 20, 35, 36, 44)**  
- Kafka / NATS – event backbone, A2A task queues  
- Agent Workers (custom, LangChain) – agent logic  
- MCP Clients – tool invocation  
- Custom Content Processing Engine – unified document model, chunking, embedding (or Pandoc, Tika, LibreOffice)  
- Temporal / Airflow – scheduled and durable workflows (complementing the process engine)

**Application‑Adjacent Runtimes (Domains 4, 10, 17, 18, 37, 40, 42, 43, 45, 46)**  
- Linkerd / Istio – service mesh, mTLS, resilience  
- Our Process Engine – also spans here as the primary workflow engine  
- Grafana / Superset – BI and analytics  
- MLflow / LangSmith – ML/LLM experiment tracking and observability  
- Qdrant / pgvector – vector store (also used for agent memory)  
- Elasticsearch / OpenSearch – full‑text search  
- Novu / Courier – unified notifications  
- Gretel / Tonic – synthetic data generation  
- OpenQuantumSafe – PQC algorithm integration

**Persistence & Data Pipelines (Domains 7, 9, 16, 27, 34, 49, 52, 54, 55, 60, 61)**  
- PostgreSQL – relational, with pgvector for vectors  
- Redis – caching, session store, rate limiting  
- Kafka / NATS – event streaming and persistence  
- MinIO / S3 – object storage  
- Debezium + Kafka Connect – CDC pipelines  
- dbt + Airflow – data transformations  
- Velero / Kasten – backup and DR  
- Flyway / Liquibase – database schema migrations  
- S3 Object Lifecycle / Glacier – archival

**Foundation & Governance (Domains 1, 2, 8, 11, 12, 21, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33, 47, 56, 58, 59, 62, 63, 65)**  
- Kubernetes – orchestration, also edge (K3s)  
- Consul – service discovery, agent registry, KV configuration  
- Vault – secrets management, encryption as a service, HSM integration  
- Keycloak / Ory – OAuth2/OIDC, user and agent identity  
- OPA – policy enforcement  
- Argo CD / Flux – GitOps, environment promotion  
- GitHub Actions / Jenkins / Tekton – CI/CD  
- k6 / Playwright / Pact – testing  
- OpenTelemetry + Grafana LGTM – observability  
- LangSmith – LLM trace analysis  
- Cloud Carbon Footprint / Kepler – sustainability monitoring  
- InfraCost / Kubecost – FinOps  
- DataHub – data catalog and governance  
- Splunk / Elastic Security – SIEM and incident response  
- Tonic / Delphix – data masking for non‑production

---

This seven‑layer model and the converged toolbox cover the full spectrum from global traffic to developer inner loop, from blockchain to voice assistants. Every domain is addressed with decoupled components, and the platform can evolve from a simple startup stack to a fully regulated, multi‑cloud, agent‑augmented enterprise system.
