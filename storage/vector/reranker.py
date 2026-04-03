from typing import List, Dict


class SimpleReranker:

    def rerank(self, query, docs: List[Dict]):

        # placeholder
        # later can plug cross-encoder
        return sorted(
            docs,
            key=lambda x: x.get("score", 0),
            reverse=True
        )
