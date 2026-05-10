# rag/retrieval/base_trainer.py
from abc import ABC
from abc import abstractmethod

class BaseTrainer(ABC):
    """قرارداد مشترک تمام Trainer ها"""

    @abstractmethod
    def train(self, samples: list, epochs: int):
        """اجرای فرآیند آموزش"""
