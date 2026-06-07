class TopKOptimizer:
    def __init__(self):
        self.stats = {}

    def choose(self, query):
        length = len(query.split())
        learned = self.stats.get(length, {}).get("k")
        if learned is not None:
            return max(3, min(20, int(learned)))
        if length < 5:
            return 5
        if length < 12:
            return 8
        return 12

    def update(self, query, reward):
        key = len(query.split())
        bucket = self.stats.setdefault(key, {"k": self.choose(query)})
        bucket["k"] += 1 if reward > 0 else -1
        bucket["k"] = max(3, min(20, bucket["k"]))
