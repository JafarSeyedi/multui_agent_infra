import random
from collections import deque

class RetrievalFeedbackBuffer:
    """
    Replay buffer برای یادگیری تدریجی
    capacity: تعداد نمونه‌های ذخیره شده
    """
    def __init__(self, capacity=3000):
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)

    def add(self, vector, keyword, graph, target):
        sample = {
            "vector": float(vector),
            "keyword": float(keyword),
            "graph": float(graph),
            "target": float(target),
        }
        self.buffer.append(sample)

    def sample(self, n=200):
        return random.sample(self.buffer, min(n, len(self.buffer)))

    def __len__(self):
        return len(self.buffer)
