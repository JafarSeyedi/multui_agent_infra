class FailureAnalyzer:

    def __init__(self):

        self.failures = []

    def record(self, module, error):

        self.failures.append({
            "module": module,
            "error": str(error)
        })

    def recent(self, n=20):

        return self.failures[-n:]
