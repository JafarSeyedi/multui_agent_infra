class WeightManager:

    def __init__(self):
        self.weights = {
            "vector": 1.00,
            "keyword": 0.85,
            "graph": 0.70,
            "reflection": 0.80,
            "agentic": 0.75,
        }

        self.learning_rate = 0.05

    def get(self, source: str) -> float:
        return self.weights.get(source, 1.0)

    def update(self, source: str, reward: float):
        """
        reward between -1 and +1
        """
        w = self.weights[source]
        w = w + self.learning_rate * reward
        w = max(0.1, min(w, 2.5))  # clamp
        self.weights[source] = w

    def all(self):
        return self.weights
