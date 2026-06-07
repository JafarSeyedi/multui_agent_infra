import torch


class RetrieverTrainer:

    def __init__(self, encoder, optimizer):

        self.encoder = encoder
        self.optimizer = optimizer


    def train_step(self, query_text, positive_chunks, negative_chunks):

        q_emb = self.encoder.encode(query_text)

        pos_embs = [
            self.encoder.encode(c)
            for c in positive_chunks
        ]

        neg_embs = [
            self.encoder.encode(c)
            for c in negative_chunks
        ]

        pos_scores = [
            torch.cosine_similarity(q_emb, p, dim=0)
            for p in pos_embs
        ]

        neg_scores = [
            torch.cosine_similarity(q_emb, n, dim=0)
            for n in neg_embs
        ]

        pos_scores = torch.stack(pos_scores)
        neg_scores = torch.stack(neg_scores)

        loss = -torch.log(
            torch.exp(pos_scores).sum() /
            (torch.exp(pos_scores).sum() + torch.exp(neg_scores).sum())
        )

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return loss.item()
