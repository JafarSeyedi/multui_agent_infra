# رفتار اجرای Pipeline
فرض کن این workflow را داریم:

```
[
  task1 -> ResearchAgent
  task2 -> WriterAgent
  task3 -> ReviewerAgent
]
```

## Execution:

```
ResearchAgent
     ↓
context update
     ↓
WriterAgent
     ↓
context update
     ↓
ReviewerAgent
```

## نمونه Orchestration Request
```python
{
 "interaction_mode": "pipeline",
 "context": {
     "topic": "Large Language Models"
 },
 "tasks": [
   {
     "task_id": "research",
     "agent_name": "research_agent"
   },
   {
     "task_id": "write",
     "agent_name": "writer_agent"
   },
   {
     "task_id": "review",
     "agent_name": "review_agent"
   }
 ]
}
```

## رویدادهایی که MessageBus می‌گیرد
```text
task_started
task_completed
task_failed
```
مثال:

```text
{
 "event": "task_completed",
 "task_id": "write",
 "agent": "writer_agent"
}
```
### چرا این Pipeline حرفه‌ای است؟
✅ context propagation
✅ error isolation
✅ event emission
✅ agent registry integration
✅ extensible


# DAGStrategy
این جایی است که:

```text
parallel agents
dependency graphs
dynamic scheduling
```
اتفاق می‌افتد.

یعنی:

```text
      A
     / \
    B   C
     \ /
      D
```
و B و C همزمان اجرا می‌شوند.

پیاده‌سازی حرفه‌ای DAG در سیستم چندعامله خیلی جالب و چالش‌برانگیز است.

## معماری DAG Strategy
در این مدل هر task می‌تواند وابسته به چند task دیگر باشد.

مثال:

```text
        research
        /     \
   keywords   facts
        \     /
         writer
           |
        reviewer
```
## ویژگی‌ها:

- اجرای موازی taskها
- رعایت dependency
- تشخیص cycle
- مدیریت context مشترک
- انتشار event
- مدیریت failure

## الگوریتم اجرای DAG
مراحل اجرا:

### 1️⃣ ساخت Graph
از TaskDefinition.depends_on گراف dependency ساخته می‌شود.

```text
task_id -> dependencies
```

### 2️⃣ Cycle Detection
اگر گراف cycle داشته باشد orchestration باید fail شود.

مثال invalid:

```text
A -> B
B -> C
C -> A
```

### 3️⃣ Scheduling
Taskهایی که dependency ندارند:

```text
ready_tasks
```
این‌ها همزمان اجرا می‌شوند.

### 4️⃣ Execution Loop
تا زمانی که task باقی مانده:

### 1️⃣ اجرای همه ready tasks با asyncio.gather

### 2️⃣ آپدیت context

### 3️⃣ آزاد شدن taskهای بعدی

### 4️⃣ تکرار

## نکتهٔ مهم: Context Safety
چون execution موازی است باید:

```text
context updates
```
با lock مدیریت شوند.

## قابلیت‌های حرفه‌ای این DAG
### ✅ Parallel Execution
```text
B and C run simultaneously
```
با asyncio.gather.

### ✅ Cycle Detection
قبل از اجرا:

```text
DFS validation
```
اگر cycle باشد:

```text
ValueError
```
### ✅ Thread‑Safe Context
```text
asyncio.Lock
```
برای جلوگیری از race condition.

### ✅ Event Driven Integration
events:

```text
task_started
task_completed
task_failed
```
### ✅ Fault Isolation
اگر یک task fail شود:

```text
workflow stops
```
و خروجی partial برمی‌گردد.

### مثال واقعی
```text
tasks = [

research

keywords(depends_on=research)

facts(depends_on=research)

writer(depends_on=[keywords,facts])

review(depends_on=writer)

]
```
#### Execution:

```text
research
   ↓
keywords  facts   (parallel)
   ↓       ↓
      writer
        ↓
      review
```

# Debate / Negotiation Strategy
مدلی که AutoGen استفاده می‌کند:

``` text
agent A
agent B
critic
loop
```
مثال:

```text
writer ↔ critic
تا زمانی که quality خوب شود.
```

این استراتژی پایهٔ:

AI reviewers
AI debate
self‑improving agents
است.


در این مدل چند agent با هم دیالوگ iterative دارند تا خروجی بهتر شود.

## معماری Debate Strategy
### ساختار پایه:

```text
Agent A (Proposer / Writer)
        ↓
Agent B (Critic / Reviewer)
        ↓
Agent A (Refine)
        ↓
Agent B (Evaluate)
        ↓
loop ...
```
تا زمانی که:

quality کافی شود
یا max_round برسد
## اجزای کلیدی
### 1️⃣ Proposer Agent
عامل تولیدکننده:

```text
writer_agent
```
وظیفه:

```text
generate solution
```
### 2️⃣ Critic Agent
عامل نقدکننده:

```text
critic_agent
```
وظیفه:

```text
evaluate / critique
```
### 3️⃣ Iterative Loop Controller
کنترل حلقه:

```text
for round in range(max_rounds)
```
### 4️⃣ Stopping Conditions
چند شرط توقف:

#### 1️⃣ max_rounds
#### 2️⃣ critic says “APPROVED”
#### 3️⃣ score threshold

### 5️⃣ Shared Debate Context
```text
context = {

 topic
 current_answer
 critique
 round
 history
}
```

## نمونه Workflow
```text
topic: "Explain transformers"

Round 1

Writer:
initial answer

Critic:
missing attention explanation

Round 2

Writer:
improved explanation

Critic:
APPROVED
```

## نمونه Orchestration Request
```python
{
 "interaction_mode": "debate",

 "context": {
     "topic": "Explain transformers"
 },

 "metadata": {
     "max_rounds": 4
 },

 "tasks": [

   {
     "task_id": "writer",
     "agent_name": "writer_agent"
   },

   {
     "task_id": "critic",
     "agent_name": "critic_agent"
   }

 ]
}
```
## نمونه Critic Output
Critic باید چیزی مثل این بدهد:

```python
{
 "approved": False,
 "feedback": "Explain attention mechanism more clearly"
}
```
یا:

```python
{
 "approved": True,
 "feedback": "Explanation is complete"
}
```
### رویدادهای MessageBus
```text
debate_round_started
debate_round_completed
debate_finished
```
### قدرت واقعی Debate Strategy
#### کاربردها:

AI writing refinement
```text
writer ↔ reviewer
```
AI research validation
```text
researcher ↔ verifier
```
AI reasoning debate
```text
agent1 ↔ agent2 ↔ judge
```

# Broadcast Strategy
یکی از کاربردی‌ترین الگوهای چندعامله برای:

- Ensemble Reasoning
- Multi‑Model Aggregation
- Multi‑Agent Voting
- Parallel Inference
- Multi‑Perspective Analysis

یک task → چند agent → merge results

### Conditional Routing
```text
if score > threshold
   go to review
else
   go to rewrite
```
### Self‑Refine Strategy
```text
generate
evaluate
improve
loop
```
این همان معماری Self‑Improving Agents است.


## 🎯 معماری Broadcast Strategy
### ساختار:

```text
                 → Agent A
               /
Input → Fan‑Out → Agent B
               \
                 → Agent C

Aggregator ← Collect ← all outputs
```
### ویژگی‌ها:

- تمام agentها همزمان اجرا می‌شوند.
- هر agent یک خروجی تولید می‌کند.
- یک aggregate function خروجی نهایی را می‌سازد.
- مدیریت کامل خطا، context، و event‑ها انجام می‌شود.
## 📦 رفتار استراتژی
1) Fan‑Out
تمام taskهای تعریف‌شده در request همزمان اجرا می‌شوند.

2) Gather
نتیجه هر agent به صورت:

```text
TaskResult
```
جمع‌آوری می‌شود.

3) Aggregation
یک تابع نهایی (انتخابی و قابل تنظیم) کارهای زیر را انجام می‌دهد:

- merge نتایج
- vote
- rank
- score
- summarize

پیش‌فرض:

ترکیب کردن خروجی‌ها در قالب یک dict:

```json
{
 "agent_name": output
}
```

## 🚀 ویژگی‌های حرفه‌ای این استراتژی
### 1) Parallel Execution
تمام agentها همزمان اجرا می‌شوند.

### 2) Multi‑Aggregator Support
حالت‌های aggregation:

- "merge" (پیش‌فرض)
- "list"
- "vote"
- حالت‌های سفارشی قابل افزودن
### 3) Full Event Hooks
Event‑هایی که emit می‌شوند:

```text
broadcast_task_started
broadcast_task_completed
```
این باعث می‌شود dashboard‑ها یا tracer‑ها بتوانند به راحتی سیستم را مانیتور کنند.

### 4) Error Isolation
اگر یک agent fail شود:

- فقط همان agent
- نتیجه کلی مختل نمی‌شود

## 📌 نمونه OrchestrationRequest
```python
{
 "interaction_mode": "broadcast",

 "context": {
     "question": "Explain Transformers"
 },

 "metadata": {
     "aggregator": "merge"
 },

 "tasks": [
     { "task_id": "t1", "agent_name": "llama_agent" },
     { "task_id": "t2", "agent_name": "gpt_agent" },
     { "task_id": "t3", "agent_name": "mixtral_agent" }
 ]
}
```
## 📌 خروجی مثال
```python
{
 "llama_agent": "... explanation ...",
 "gpt_agent": "... explanation ...",
 "mixtral_agent": "... explanation ..."
}
```

# Conditional Strategy
این استراتژی در واقع چیزی است که یک workflow ساده را تبدیل می‌کند به یک dynamic decision graph. یعنی مسیر اجرا در زمان اجرا (runtime) بر اساس خروجی agentها تغییر می‌کند.

## ایدهٔ اصلی Conditional Strategy
### ساختار کلی:

```text
            Router Agent
                 │
        ┌────────┴────────┐
        │                 │
   condition A       condition B
        │                 │
     Agent X           Agent Y
```
یعنی:

یک task اجرا می‌شود (معمولاً یک router agent).
خروجی آن بررسی می‌شود.
بر اساس شرط‌ها مسیر workflow تعیین می‌شود.
مثال واقعی
``text
task1 → classifier_agent

if score > 0.8
    → expert_agent
else
    → fallback_agent
```
یا:

```text
intent_classifier

intent = "math" → math_agent
intent = "code" → coding_agent
intent = "history" → history_agent
```
### مدل منطقی اجرا
هر TaskDefinition می‌تواند چیزی مثل این داشته باشد:

```text
conditions = [
   { "if": "score > 0.8", "next": "expert_task" },
   { "if": "score <= 0.8", "next": "fallback_task" }
]
```
یا ساده‌تر:

```text
routes = {
   "math": "math_solver",
   "code": "coding_agent"
}
```
## الگوریتم اجرای Conditional Strategy
مراحل:

- 1️⃣ اجرای اولین task
- 2️⃣ گرفتن output
- 3️⃣ ارزیابی condition
- 4️⃣ انتخاب task بعدی
- 5️⃣ ادامه اجرا

این یک dynamic pipeline می‌سازد.


## مثال TaskDefinition
```text
classifier_task
```

routes:

```python
{
 "math": "math_agent",
 "code": "coding_agent",
 "default": "general_agent"
}
```

## نمونه OrchestrationRequest
```python
{
 "interaction_mode": "conditional",

 "metadata": {
     "start_task": "router"
 },

 "tasks": [

   {
     "task_id": "router",
     "agent_name": "intent_classifier",
     "routes": {
        "math": "math_solver",
        "code": "code_agent",
        "default": "chat_agent"
     }
   },

   {
     "task_id": "math_solver",
     "agent_name": "math_agent"
   },

   {
     "task_id": "code_agent",
     "agent_name": "programming_agent"
   },

   {
     "task_id": "chat_agent",
     "agent_name": "general_agent"
   }

 ]
}
```

## مثال خروجی Router Agent
```text
{
 "route": "math"
}
```
سیستم مسیر را این‌گونه اجرا می‌کند:

```text
router
   ↓
math_solver
```

## قابلیت‌های حرفه‌ای
### Dynamic Workflow
مسیر اجرا در runtime تعیین می‌شود.

### Intent Routing
برای AI assistants:

```text
user intent → specialized agent
```
### Error‑Safe Routing
اگر route پیدا نشود:

```text
default
```

### Loop Protection
اگر task تکرار شود:

```text
RuntimeError
```


# Event‑Driven Strategy

این استراتژی عملاً سیستم را از یک orchestrated workflow تبدیل می‌کند به یک Reactive Multi‑Agent System.

در این مدل دیگر ترتیب اجرای agentها از قبل مشخص نیست؛ بلکه eventها تعیین می‌کنند چه چیزی بعد اجرا شود. این همان معماری‌ای است که در:

- microservice architectures
- distributed systems
- reactive AI platforms
استفاده می‌شود.


## ایدهٔ اصلی Event‑Driven Strategy
### ساختار کلی:

```text
User Input
    │
    ▼
 Event: user_message
    │
 ┌──┴───────────────┐
 │                  │
Agent A          Agent B
 │                  │
 ▼                  ▼
Event: result_A   Event: result_B
 │                  │
 └───────┬──────────┘
         ▼
      Agent C
```
یعنی:

- یک event منتشر می‌شود.
- agentهایی که به آن event subscribe کرده‌اند اجرا می‌شوند.
- خروجی آن‌ها eventهای جدید تولید می‌کند.
- سیستم ادامه پیدا می‌کند.

## تفاوت با Pipeline و DAG
### Pipeline:

```text
A → B → C
```

### DAG:

```text
A → {B,C} → D
```

### Event‑Driven:

```text
event → agent
agent → event
event → agent
```
یعنی یک reaction graph.

## اجزای معماری
### 1️⃣ Event
ساختار:

```text
{
  "type": "user_message",
  "payload": {...}
}
```
### 2️⃣ Subscription
هر task مشخص می‌کند:

```text
on_event = "user_message"
```
### 3️⃣ Emitted Events
agent خروجی تولید می‌کند:

```text
{
  "emit_event": "analysis_complete",
  "data": {...}
}
```


## نمونه TaskDefinition
```text
user_input_agent
```

```python
{
 "task_id": "input_handler",
 "agent_name": "input_agent",
 "on_events": "start"
}
```
```text
analysis_agent
```

```python
{
 "task_id": "analysis",
 "agent_name": "analysis_agent",
 "on_events": "user_message"
}
```
## مثال خروجی agent
```text
{
 "analysis": "...",
 "emit_events": [
     {
       "type": "analysis_complete",
       "payload": { "score": 0.92 }
     }
 ]
}
```
## جریان کامل اجرا
```text
start event
   ↓
input_agent
   ↓ emit user_message
analysis_agent
   ↓ emit analysis_complete
decision_agent
```
## ویژگی‌های حرفه‌ای این معماری
### Reactive Architecture
agentها reactive هستند نه sequential.

### Loose Coupling
agentها همدیگر را نمی‌شناسند.

ارتباط فقط از طریق events است.

### Parallel Execution
اگر چند listener وجود داشته باشد:

```text
event → {agentA, agentB, agentC}
```
همه همزمان اجرا می‌شوند.

### Infinite Workflows (Controlled)
سیستم می‌تواند agent loops بسازد.

مثلاً:

```text
critic → refine → critic → refine
```
با max_iterations کنترل می‌شود.


# Self‑Refine Strategy
کی از قدرتمندترین الگوهای چندعامله:

این همان الگویی است که باعث می‌شود agentها:

```text
generate
criticize
improve
repeat
```
و کیفیت خروجی چند برابر شود.

در سیستم‌های:

- DeepMind Reflexion
- Self‑Refine
- AutoGPT Improvement Loops
استفاده می‌شود.


این همان الگویی است که در کارهای پژوهشی مثل:

- Self‑Refine (Stanford)
- Reflexion (DeepMind)
- LLM Self‑Improvement Loops
- AutoGPT critique loops
استفاده می‌شود.

ایده ساده است اما اثرش بزرگ است:

به جای یک بار تولید پاسخ، سیستم خودش خروجی را نقد می‌کند و اصلاح می‌کند.

## ایدهٔ اصلی Self‑Refine
### چرخه اصلی:

```text
Generator → Critic → Refiner
      ↑                  ↓
      └──── repeat ──────┘
```
### مراحل:

#### 1️⃣ Generate

یک agent پاسخ اولیه تولید می‌کند.

#### 2️⃣ Critique

یک agent دیگر پاسخ را بررسی می‌کند.

#### 3️⃣ Refine

agent سوم نسخه بهبود یافته تولید می‌کند.

#### 4️⃣ اگر کیفیت کافی نبود → دوباره تکرار.

## مزیت واقعی
این چرخه باعث می‌شود:

- hallucination کمتر شود
- استدلال بهتر شود
- کیفیت پاسخ بالا برود
برای همین در سیستم‌های long‑reasoning خیلی استفاده می‌شود.

## معماری Strategy
### ساختار ساده:

```text
input
  ↓
generator_agent
  ↓
critic_agent
  ↓
refiner_agent
  ↓
repeat (max_iterations)
```
## پارامترهای مهم
در metadata:

```text
max_refinements
stop_if_perfect
quality_threshold
```

## نمونه OrchestrationRequest
```python
{
 "interaction_mode": "self_refine",

 "context": {
    "question": "Explain backpropagation"
 },

 "metadata": {

    "generator_agent": "answer_generator",

    "critic_agent": "answer_critic",

    "refiner_agent": "answer_refiner",

    "max_refinements": 3,

    "quality_threshold": 0.9
 }
}
```
## مثال خروجی critic
```text
{
 "issues": [
   "Explanation missing gradient intuition",
   "Example not clear"
 ],
 "score": 0.65
}
```
## مثال refine
refiner با استفاده از critique پاسخ جدید می‌سازد.

### چرخه واقعی
```text
Generate
  ↓
Critique (score 0.6)
  ↓
Refine
  ↓
Critique (score 0.82)
  ↓
Refine
  ↓
Critique (score 0.93)
  ↓
STOP
```
## ویژگی‌های حرفه‌ای این پیاده‌سازی
### Quality‑Driven Stop
loop وقتی متوقف می‌شود که:

```text
score >= threshold
```
### Controlled Iterations

برای جلوگیری از loop بی‌نهایت:

```text
max_refinements
```

### Event Hooks
events:

```text
self_refine_started
self_refine_iteration
self_refine_converged
```
### Modular Agents

هر مرحله agent جدا دارد:

```text
generator
critic
refiner
```
می‌توانند حتی مدل‌های مختلف LLM باشند.