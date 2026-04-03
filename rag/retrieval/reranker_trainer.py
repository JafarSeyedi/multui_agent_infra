class RerankerTrainer:

    def __init__(self, model, optimizer):

        self.model = model
        self.optimizer = optimizer


    def train_step(self, query, positive_doc, negative_doc):

        pos_score = self.model.score(query, positive_doc)
        neg_score = self.model.score(query, negative_doc)

        loss = max(0, 1 - pos_score + neg_score)

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return loss
