# rag/retrieval/base_trainer.py
from abc import ABC
from abc import abstractmethod

class BaseTrainer(ABC):
    """Common contract for all Trainers"""

    @abstractmethod
    def train(self, samples: list, epochs: int):
        """Execute training process"""
