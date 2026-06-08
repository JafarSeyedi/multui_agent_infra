# Flow:
## Agent execution Data flow
 Orchestrator → AgentInput (base model)
 if agent subclass needs it → convert
 Agent → AgentOutputSubclass
 Orchestrator only saves Base AgentOutput
 ExecutionTrace هم فقط base formats را log می‌کند
 Orchestration → فقط workflow را مدیریت می‌کند
 Interaction → فقط گفتگو و نوبت‌ها را مدیریت می‌کند
 Agent Adapter → تبدیل payload ↔ مدل داخلی agent را انجام می‌دهد
 
 
 Orchestrator / Interaction
         │
         │  AgentInput
         ▼
    AgentAdapter
         │
         │ convert
         ▼
  AgentSpecificInput
         │
         ▼
        Agent
         │
         ▼
  AgentSpecificOutput
         │
         │ convert
         ▼
      AgentOutput
     

## Interaction
  
 AgentMessage
     sender
     receiver
     content
        
 AgentMessage
      ↓
 AgentInput
      ↓
 AgentAdapter
      ↓
 Agent
  
  
## Orchestrator

 execute_task(task)

 ## Running flow /layers

 class AgentRegistry:
     def __init__(self):
         self.adapters = {}
     def register(self, agent_name, adapter):
         self.adapters[agent_name] = adapter
     async def execute(self, input: AgentInput):
         adapter = self.adapters[input.agent_name]
         return await adapter.execute(input)

- Orchestration Engine فقط workflow را مدیریت می‌کند.
- TaskExecutor وظیفه dispatch دارد.
- هر نوع task یک runtime اختصاصی دارد.
- adapterها مسئول تبدیل قرارداد داده هستند.

             Orchestration Workflow Engine
                     │
                     ▼
                Orchestration Tasks
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
     UserTask    Executable   WorkflowTask
                     │
                     ▼
                 TaskExecutor
                     │
     ┌───────────────┼────────────────┬────────────────┐
     ▼               ▼                ▼                ▼
  AgentTask     InteractionTask     ToolTask      BusinessRuleTask      
     │               │                │
     ▼               ▼                ▼
    Agent    InteractionRuntime     Tool
                     │
                     ▼
            InteractionStrategy
                     │
                     │
                     ▼
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
   AgentCall     AgentCall     AgentCall
       │             │             │
       └───────┬─────┴─────┬───────┘
               ▼           ▼
               AgentRegistry
                    │
                    ▼
                AgentAdapter
                    │
                    ▼
                  Agent
                    │
                    ▼
                   Tool
                    │
         ┌──────────┼──────────┬───────────┐
         ▼          ▼          ▼           ▼
      LLMTool    RAGTool   LocalTool    APITool
                               DB          │
                                           ▼
                                        MCPTool

 Orchestration Workflow → Orchestration Tasks
 Orchestration Task → Sub Workflow
 Orchestration Task → Interaction
 Orchestration Task → Agent
 Orchestration Task → Tool
 Interaction → Agents → Tools
 Agent → WorkflowAgent
 Agent → InteractionAgent
 Agent → ToolAgent
 Task
  └─ Executable
 class OrchestrationTask:
     id
     executable
     depends_on
 Executable:
   Workflow
   Interaction
   Agent
   Tool
 Agent → تصمیم‌گیر
 Tool → اجراکننده capability
 LLM → موتور استدلال
 RAG → یک capability بازیابی
 LLM ≠ Task
 RAG ≠ Task
 LLM = inference engine
 RAG = retrieval capability
 و هر دو معمولاً از طریق Tool layer در دسترس قرار می‌گیرند.
 Task
  ├─ AgentTask
  ├─ InteractionTask
  ├─ ToolTask
  └─ SubWorkflowTask
 Agents use Tools
 Tools can use Tools
 LLM = Tool
 LLMCompletionTool
 ChatCompletionTool
 EmbeddingTool
 RAGTool
    ├─ RetrieverTool
    ├─ RerankTool
    └─ LLMTool
 RAGAnswerTool
    ├─ VectorSearchTool
    ├─ ContextBuilderTool
    └─ LLMTool
 Local Tool
 Remote Tool
 MCP Tool


tools/
   base_tool.py
   composite_tool.py
   llm/
       completion_tool.py
       embedding_tool.py
   rag/
       rag_tool.py
       retriever_tool.py
   mcp/
       mcp_client_tool.py

## tools:
LLM
RAG
Search
Database
Filesystem
GitHub
Browser


# Decision Matrix — Workflow vs Interaction vs Agent vs Tool

| معیار | Workflow (Orchestration) | Interaction | Agent | Tool |
|------|---------------------------|-------------|-------|------|
| هدف اصلی | کنترل جریان اجرای کارها | هماهنگی بین چند agent | انجام reasoning یا task تخصصی | انجام یک capability |
| سطح تصمیم‌گیری | global flow decisions | conversation/coordination decisions | task-level reasoning | هیچ تصمیمی |
| نوع منطق | workflow logic | interaction pattern | domain logic | functional logic |
| scope اجرا | چند task | چند agent | یک capability پیچیده | یک operation |
| state | execution state | conversation state | agent memory/state | معمولاً stateless |
| identity مستقل | ندارد | ندارد | دارد | ندارد |
| policy مستقل | ندارد | interaction policy | agent policy | ندارد |
| orchestration می‌کند؟ | بله | محدود (بین agentها) | خیر | خیر |
| agent اجرا می‌کند؟ | بله | بله | خیر | خیر |
| tool اجرا می‌کند؟ | ممکن است | خیر | بله | خیر |
| recursion ممکن است؟ | بله (sub-workflow) | گاهی | بله (tool/workflow) | خیر |
| abstraction level | system level | coordination level | intelligence unit | capability unit |

---

# تشخیص سریع (Quick Decision Tree)

وقتی یک component جدید طراحی می‌کنی این سؤال‌ها را بپرس:

### 1️⃣ آیا این component جریان اجرای کارها را کنترل می‌کند؟

مثلاً:

- DAG execution
- dependency
- retries
- parallel execution

✅ بله → **Workflow**

---

### 2️⃣ آیا این component چند agent را با یک الگوی گفتگو هماهنگ می‌کند؟

مثلاً:

- debate
- group chat
- round robin
- critique loop

✅ بله → **Interaction**

---

### 3️⃣ آیا این component دارای behavior یا reasoning مستقل است؟

مثلاً:

- ResearchAgent
- CriticAgent
- PlannerAgent
- SummarizerAgent

✅ بله → **Agent**

---

### 4️⃣ آیا این component فقط یک قابلیت انجام می‌دهد؟

مثلاً:

- LLM call
- vector search
- API call
- DB query
- file read

✅ بله → **Tool**

---

# مثال‌های واقعی

| Component | Layer |
|-----------|-------|
| DAG executor | Workflow |
| task dependency resolver | Workflow |
| debate strategy | Interaction |
| group chat | Interaction |
| research agent | Agent |
| critique agent | Agent |
| planner agent | Agent |
| LLM inference | Tool |
| RAG retrieval | Tool |
| HTTP API call | Tool |
| database query | Tool |

---

# مثال کامل یک Execution

فرض کن یک سوال پژوهشی داریم:

```
User Question
```

### Workflow

```
ResearchWorkflow
 ├─ Interaction: Debate
 ├─ Agent: SummarizerAgent
 └─ Tool: ExportPDF
```

---

### Interaction

```
DebateInteraction
 ├─ ResearchAgent
 ├─ CriticAgent
 └─ JudgeAgent
```

---

### Agent

```
ResearchAgent
   ├─ LLMTool
   ├─ RAGTool
   └─ WebSearchTool
```

---

### Tool

```
LLMTool → OpenAI API
RAGTool → VectorDB
WebSearchTool → HTTP API
```



┌──────────────────────────────┐
│     Orchestration Engine     │
│                              │
│ WorkflowEngine               │
│ TaskExecutor                 │
│ WorkflowTask                 │
│ ExecutableTask               │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│      Interaction Engine      │
│                              │
│ InteractionRuntime           │
│ InteractionStrategy          │
│ AgentCall                    │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│          Agent Layer         │
│                              │
│ AgentRegistry                │
│ AgentAdapter                 │
│ Agent                        │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│         Tool Layer           │
│                              │
│ LLMTool                      │
│ RAGTool                      │
│ APITool                      │
│ LocalTool                    │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│        Knowledge Layer       │
│                              │
│ VectorEngine                 │
│ GraphEngine                  │
│ DocumentEngine               │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│          Storage             │
│                              │
│ VectorDB                     │
│ GraphDB                      │
│ Redis                        │
└──────────────────────────────┘


## Python dependencies

### AutoGen
pyautogen

### RAG Frameworks (Choose one or both)
llama-index
langchain

### LLM Providers
openai

### Vector Databases (Choose at least one)
chromadb
faiss-cpu # or faiss-gpu if you have GPU
pinecone-client
weaviate-client

### File Processing
python-docx
PyMuPDF

### Utilities
python-dotenv # To load environment variables from a .env file

### Other specific libraries


