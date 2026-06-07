class GraphVisualizer:

    def __init__(self):

        self.paths = []

    def record_path(self, nodes):

        self.paths.append(nodes)

    def get_paths(self):

        return self.paths
