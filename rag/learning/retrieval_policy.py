class RetrievalPolicy:

    def __init__(self):
        self.q_table = {}

    def get_state(self, query):
        length = len(query.split())

        if length < 5:
            return "short"

        if length < 12:
            return "medium"

        return "long"

    def select(self, query):

        state = self.get_state(query)

        if state not in self.q_table:
            self.q_table[state] = {
                "top_k": 5,
                "rerank": True,
                "compression": True,
            }

        return self.q_table[state]

    def update(self, query, reward):

        state = self.get_state(query)

        if reward > 0:
            self.q_table[state]["top_k"] += 1
        else:
            self.q_table[state]["top_k"] = max(
                3, self.q_table[state]["top_k"] - 1
            )
