from __future__ import annotations

from typing import Any

import numpy as np


class MetricsCalculator:

    @staticmethod
    def calc(y_true: np.ndarray, y_pred: np.ndarray,
             metrics: list[str] | None = None) -> dict[str, float]:
        if metrics is None:
            metrics = ["accuracy", "f1", "precision", "recall", "r2", "mse"]

        results: dict[str, float] = {}

        if isinstance(y_true, (list, tuple)):
            y_true = np.array(y_true)
        if isinstance(y_pred, (list, tuple)):
            y_pred = np.array(y_pred)

        y_true = y_true.flatten()
        y_pred = y_pred.flatten()

        if y_true.shape != y_pred.shape:
            min_len = min(len(y_true), len(y_pred))
            y_true = y_true[:min_len]
            y_pred = y_pred[:min_len]

        is_classification = bool(
            y_true.dtype.kind in ("i", "u", "O", "b")
            or (y_true.dtype.kind == "f" and bool(np.all(y_true == y_true.astype(int))))
        )

        for metric in metrics:
            try:
                val = MetricsCalculator._compute(metric, y_true, y_pred, is_classification)
                results[metric] = val
            except Exception:
                continue

        return results

    @staticmethod
    def _compute(metric: str, y_true: np.ndarray, y_pred: np.ndarray,
                 is_clf: bool) -> float:
        if metric == "accuracy":
            if not is_clf:
                return 0.0
            return float(np.mean(y_true == y_pred))

        elif metric == "f1":
            if not is_clf:
                return 0.0
            tp = float(np.sum((y_true == 1) & (y_pred == 1)))
            fp = float(np.sum((y_true == 0) & (y_pred == 1)))
            fn = float(np.sum((y_true == 1) & (y_pred == 0)))
            if tp + fp == 0 or tp + fn == 0:
                return 0.0
            p = tp / (tp + fp)
            r = tp / (tp + fn)
            if p + r == 0:
                return 0.0
            return 2 * p * r / (p + r)

        elif metric == "precision":
            tp = float(np.sum((y_true == 1) & (y_pred == 1)))
            fp = float(np.sum((y_true == 0) & (y_pred == 1)))
            if tp + fp == 0:
                return 0.0
            return tp / (tp + fp)

        elif metric == "recall":
            tp = float(np.sum((y_true == 1) & (y_pred == 1)))
            fn = float(np.sum((y_true == 1) & (y_pred == 0)))
            if tp + fn == 0:
                return 0.0
            return tp / (tp + fn)

        elif metric == "mse":
            return float(np.mean((y_true.astype(float) - y_pred.astype(float)) ** 2))

        elif metric == "rmse":
            return float(np.sqrt(np.mean((y_true.astype(float) - y_pred.astype(float)) ** 2)))

        elif metric == "mae":
            return float(np.mean(np.abs(y_true.astype(float) - y_pred.astype(float))))

        elif metric == "r2":
            ss_res = np.sum((y_true.astype(float) - y_pred.astype(float)) ** 2)
            ss_tot = np.sum((y_true.astype(float) - np.mean(y_true.astype(float))) ** 2)
            if ss_tot == 0:
                return 0.0
            return float(1 - ss_res / ss_tot)

        elif metric == "mape":
            yt = y_true.astype(float)
            yp = y_pred.astype(float)
            mask = yt != 0
            if not np.any(mask):
                return 0.0
            return float(np.mean(np.abs((yt[mask] - yp[mask]) / yt[mask])) * 100)

        return 0.0
