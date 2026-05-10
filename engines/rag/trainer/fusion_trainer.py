from __future__ import annotations

from .base_trainer import BaseTrainer

class FusionTrainer(BaseTrainer):
    """Online trainer for the lightweight fusion model."""

    def __init__(self, fusion_mlp=None, lr: float = 1e-2, batch_size: int = 32):
        self.fusion_mlp = fusion_mlp
        self.lr = lr
        self.batch_size = batch_size

    def ensure_optimizer(self) -> None:
        return None

    def train_epoch(self, samples: list) -> float:
        if self.fusion_mlp is None or not samples:
            return 0.0

        total_loss = 0.0
        for sample in samples:
            features = [sample["vector"], sample["keyword"], sample.get("graph", 0.0)]
            prediction = self.fusion_mlp.predict(features)
            target = float(sample["target"])
            error = prediction - target
            total_loss += error * error

            for idx, value in enumerate(features):
                self.fusion_mlp.weights[idx] -= self.lr * error * value
            self.fusion_mlp.bias -= self.lr * error

        return total_loss / len(samples)

    def train(self, samples: list, epochs: int = 3):
        loss = 0.0
        for _ in range(epochs):
            loss = self.train_epoch(samples)
        return loss
