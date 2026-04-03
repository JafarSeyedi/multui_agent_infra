class CoverageScorer:

    def score(self, evidences):

        if not evidences:
            return 0.0

        total_len = sum(len(e.text) for e in evidences)

        if total_len == 0:
            return 0.0

        return min(1.0, total_len / 5000)
