from pydantic import BaseModel


class RetrievalPlan(BaseModel):

    num_queries: int = 1
    top_k: int = 5

    use_rerank: bool = True

    compression: str = "embedding"
    # embedding | llm | none
