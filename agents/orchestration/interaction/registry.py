class InteractionStrategyRegistry:
    def __init__(self):
        self._strategies = {}
    def register(self, mode, cls):
        self._strategies[mode] = cls
    def get(self, mode):
        return self._strategies[mode]
