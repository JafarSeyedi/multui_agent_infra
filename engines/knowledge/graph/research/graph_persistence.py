import sqlite3


class GraphPersistence:

    def __init__(self, path="research_graph.db"):

        self.conn = sqlite3.connect(path)
        self._init_schema()


    def _init_schema(self):

        cur = self.conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS nodes(
            name TEXT PRIMARY KEY,
            type TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS edges(
            src TEXT,
            dst TEXT,
            relation TEXT,
            confidence REAL,
            evidence_chunk TEXT
        )
        """)

        self.conn.commit()


    def save_node(self, node):

        cur = self.conn.cursor()

        cur.execute(
            "INSERT OR IGNORE INTO nodes VALUES (?,?)",
            (node.name, node.type)
        )

        self.conn.commit()


    def save_edge(self, edge):

        cur = self.conn.cursor()

        cur.execute(
            "INSERT INTO edges VALUES (?,?,?,?,?)",
            (
                edge.src,
                edge.dst,
                edge.relation,
                edge.confidence,
                edge.evidence_chunk
            )
        )

        self.conn.commit()
