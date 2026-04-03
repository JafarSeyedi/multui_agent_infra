# File structure

├── agents/              # کدهای مربوط به عامل‌های AutoGen
│   ├── __init__.py
│   ├── user_proxy.py
│   ├── assistant_agent.py
│   └── ... (سایر عامل‌ها بر اساس فایل PDF)
├── rag/                 # کدهای مربوط به RAG (LlamaIndex/LangChain)
│   ├── __init__.py
│   ├── data_loader.py
│   ├── vector_db.py
│   ├── retriever.py
│   └── query_engine.py
├── tools/               # اسکریپت‌ها و ابزارهای کمکی
│   ├── __init__.py
│   ├── file_converter.py  # برای DWG/DXF و سایر تبدیل‌ها
│   ├── pdf_processor.py
│   └── ...
├── data/                # پوشه برای ذخیره فایل‌های آموزشی و داده‌های موقت
│   ├── documents/       # فایل‌های اصلی آموزشی (PDF, DOCX, ...)
│   ├── processed/       # فایل‌های پردازش شده (مثلاً متن استخراج شده)
│   └── vector_db_files/ # فایل‌های پایگاه داده وکتوری (Chroma/FAISS)
├── config/              # فایل‌های پیکربندی (API keys, تنظیمات)
│   ├── __init__.py
│   └── settings.py
├── main.py              # نقطه ورود اصلی برنامه (برای اجرای عامل‌ها)
├── requirements.txt     # لیست کتابخانه‌های پایتون مورد نیاز
└── README.md            # توضیحات پروژه


# Architecture Tools

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


