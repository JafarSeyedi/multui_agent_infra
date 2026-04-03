class GraphTraverser:
    def __init__(self, graph_index):
        self.graph = graph_index

    async def find_connections(self, start_entity: str, max_hops=2):
        # الگوریتم جستجوی multi-hop برای پیدا کردن evidence‌های پنهان
        connections = self.graph.get_neighbors(start_entity, depth=max_hops)
        return connections
