from collections import defaultdict


class TokenTracker:

    def __init__(self):

        self.usage = defaultdict(int)

    def record(self, module: str, tokens: int):

        self.usage[module] += tokens

    def total(self):

        return sum(self.usage.values())

    def breakdown(self):

        return dict(self.usage)
