# Configuration settings for the project
# API Keys (use environment variables in production)
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"
AZURE_OPENAI_API_KEY = "YOUR_AZURE_OPENAI_API_KEY" # if using Azure

# Directories
PROJECT_ROOT = "." # Or use absolute path if needed
DATA_DIR = "data/documents"
PROCESSED_DATA_DIR = "data/processed"
VECTOR_DB_DIR = "data/vector_db_files"
CONFIG_DIR = "config"

# LLM Settings
DEFAULT_LLM_MODEL = "gpt-4o" # Or "gpt-3.5-turbo", etc.
EMBEDDING_MODEL = "text-embedding-3-small" # Or other suitable embedding model

# AutoGen Settings
# USER_PROXY_AGENT_CONFIG = {...}
# ASSISTANT_AGENT_CONFIG = {...}

# Other settings can be added here
