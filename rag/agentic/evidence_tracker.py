class EvidenceTracker:

    def __init__(self):
        self.coverage = {}  # sub_query -> percent or bool
        self.evidence = []

    def add(self, sub_query: str, results):
        self.evidence.extend(results)
        self.coverage[sub_query] = len(results) > 0

    def needs_more(self) -> bool:
        # If any sub-query has no supporting evidence
        return not all(self.coverage.values())
