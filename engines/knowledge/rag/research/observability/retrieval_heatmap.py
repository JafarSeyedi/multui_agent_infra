from collections import defaultdict


class RetrievalHeatmap:

    def __init__(self):

        self.chunk_hits = defaultdict(int)

    def record(self, chunk_id):

        self.chunk_hits[chunk_id] += 1

    def top_chunks(self, k=50):

        return sorted(
            self.chunk_hits.items(),
            key=lambda x: x[1],
            reverse=True
        )[:k]
