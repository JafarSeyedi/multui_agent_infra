import numpy as np


def normalize_embedding(vec):

    v = np.array(vec)
    norm = np.linalg.norm(v)

    if norm == 0:
        return vec

    return (v / norm).tolist()
