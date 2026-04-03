class RetrievalFeedbackBuffer:

    def __init__(self):
        self.buffer = []

    def add(self, query, positive_chunks, negative_chunks):

        self.buffer.append({
            "query": query,
            "positives": positive_chunks,
            "negatives": negative_chunks
        })

    def get_all(self):
        return self.buffer

    def clear(self):
        self.buffer = []
