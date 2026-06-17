 ساختار پوشه Storage
text
storage/
├── base_storage.py          # abstractionها
├── sql_storage.py           # پایگاه داده رابطه‌ای
├── redis_storage.py         # حافظه سریع (state / cache)
├── vector_storage.py        # RAG و semantic retrieval
├── document_storage.py      # مدیریت اسناد و Chunkها
└── log_storage.py           # ثبت execution و event logs

1️⃣ BaseStorage  (هسته همه آداپتورها)
📄 storage/base_storage.py

این فایل پایه اشتراکی برای انواع Storage Adapter هاست.

الگوی طراحی: Template Pattern + ABC Interface

هدف: هر کلاس ذخیره‌سازی (SQL، Redis، VectorDB، Memory و غیره) باید از این پایه ارث ببرد.


2️⃣ SQL Storage Adapter
📄 storage/sql_storage.py

برای داده‌های ساخت‌یافته (execution records, user profiles، و …)

در این سطح فقط abstraction طراحی می‌کنیم (نه ORM).


pip install "sqlalchemy[asyncio]>=2.0"
pip install alembic
pip install asyncpg
pip install psycopg2-binary


SQLAlchemy[asyncio] → ORM مدرن با async
Alembic → migration system
asyncpg → بهترین driver برای PostgreSQL async
psycopg2 → fallback sync driver


در ریشه پروژه اجرا کن:

alembic init migrations


✅ کاربردها:

ذخیره نسخه‌های محتوا (ContentVersion)
لاگ اجرای عامل‌ها
ذخیره Metadata سیستم
storage/redis_storage.py

3️⃣ Redis Storage Adapter
📄 storage/redis_storage.py
برای داده‌های موقت یا Cached (state عامل‌ها، context، حافظه کوتاه‌مدت).

در محیط Production از Redis واقعی استفاده می‌شود؛ این فقط اینترفیس است.

✅ کاربردها:

ذخیره حافظه کوتاه‌مدت عامل‌ها
نگهداری sessionهای فعال کاربر
cache نتایج LLM و RAG


Isolation: اگر Redis Cluster تو در دیتاسنتر جابه‌جا شود، فقط RedisManager تغییر می‌کند؛ ایجنت‌های تو اصلاً روحشان هم خبردار نمی‌شود.
Resilience: با استفاده از Retry و Health Checks در لایه Connection، سیستم در برابر قطعی‌های لحظه‌ای شبکه (Network Blips) ضدضربه است.
Scalability: ایجنت‌ها می‌توانند روی Redis Streams با مدل Consumer Group کار کنند. یعنی اگر تعداد دانش‌آموزان سیستم تو زیاد شد، کافیست ۱۰ تا ایجنت جدید بالا بیاوری؛ Redis بار را بین آن‌ها پخش می‌کند.
Data Integrity: با اضافه شدن JSON Module (که در لایه Storage می‌توانیم توسعه دهیم)، دیگر لازم نیست کل داکیومنت را برای تغییر یک فیلد آپدیت کنیم (Atomic Updates).

4️⃣ VectorDB Adapter
📄 storage/vector_storage.py

برای Embedding و Retrieval (مثل Qdrant, Pinecone, Weaviate, یا FAISS).

با این abstraction، سیستم می‌تواند backend را آزادانه عوض کند.



5️⃣ Document Storage
📄 storage/document_storage.py

برای نگهداری اسناد، Chunkها و داده‌های متنی بازیابی‌شونده.

✅ کاربردها:

حافظه متنی RAG
جستجو در منابع درسی

6️⃣ Log Storage
📄 storage/log_storage.py

برای نگهداری ساختارمند تمام execution/event logs عامل‌ها.
# 1️⃣ Key‑Value
## برای:

state
session
feature flags
config
short memory

# 2️⃣ Relational
## برای:

users
workflow
metadata
transactions
structured data

# 3️⃣ Object / Blob
## برای:

PDF
DOCX
XLSX
DWG
images
audio
video
فایل خام.

# 4️⃣ Vector
## برای:

embeddings
semantic search
similarity

# 5️⃣ Graph
## برای:

knowledge graph
entity relationships

# 6️⃣ Time‑Series
## برای:

metrics
observability
events timeline

# 7️⃣ Log / Event Stream
## برای:

event sourcing
message replay
pipelines

# 8️⃣ Cache
## برای:

temporary computed data
fast retrieval


# Redis 
## می‌تواند:

KeyValue
Cache
Stream
Queue
PubSub
Vector

# 1️⃣ Object / File Storage
## برای فایل‌های خام

PDF
DOCX
XLSX
DWG
Images
ZIP

## مثال backend:

S3
MinIO
Local FS

# 2️⃣ Document Database
## برای metadata اسناد

document_id
title
tags
owner
created_at
source
file_path

## Backend:

PostgreSQL
MongoDB

# 3️⃣ Vector Storage
## برای:

embeddings
semantic search

## مثل:

Qdrant
Weaviate
Pinecone
FAISS

# 4️⃣ Graph Storage
## برای:

knowledge graph
entity relations

## مثل:

Neo4j
ArangoDB

# 5️⃣ Cache / Streams
## برای:

events
queues
memory

## مثل:

Redis
Kafka

