class InteractionStrategy:
    def __init__(self, registry, message_bus, storage):
        self.registry = registry
        self.message_bus = message_bus
        self.storage = storage
    async def run(self, request):
        raise NotImplementedError()
