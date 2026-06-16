from __future__ import annotations

from collections import Counter

from .embedding import dot
from .models import Document, QueryIntent, RetrievedDocument
from .text import tokenize


class VectorIndex:
    def __init__(self, documents: list[Document], embeddings: list[list[float]], embedder):
        if len(documents) != len(embeddings):
            raise ValueError("documents and embeddings must have the same length")
        self.documents = documents
        self.embeddings = embeddings
        self.embedder = embedder
        self.doc_token_sets = [set(tokenize(doc.content)) for doc in documents]

    @classmethod
    def build(cls, documents: list[Document], embedder) -> "VectorIndex":
        embeddings = embedder.embed(doc.content for doc in documents)
        return cls(documents, embeddings, embedder)

    def search(
        self,
        query: str,
        intent: QueryIntent | None = None,
        top_k: int = 5,
        strict_single_model: bool = True,
    ) -> list[RetrievedDocument]:
        intent = intent or QueryIntent(raw_query=query)
        query_vec = self.embedder.embed([query])[0]
        query_tokens = set(tokenize(query))
        scored: list[RetrievedDocument] = []

        for doc, doc_vec, doc_tokens in zip(self.documents, self.embeddings, self.doc_token_sets):
            metadata = doc.metadata
            model = metadata.get("model")
            if strict_single_model and len(intent.models) == 1 and model not in intent.models and model != "ALL":
                continue

            vector_score = dot(query_vec, doc_vec)
            lexical_score = token_overlap_score(query_tokens, doc_tokens)
            reasons: list[str] = []
            boost = 0.0

            if model in intent.models:
                boost += 0.22
                reasons.append("model")
            elif model == "ALL" and intent.models:
                boost += 0.04
                reasons.append("overview")

            field = metadata.get("field")
            if field in intent.fields:
                boost += 0.28
                reasons.append("field")

            if metadata.get("type") == "spec":
                boost += 0.03

            score = (0.72 * vector_score) + (0.28 * lexical_score) + boost
            scored.append(
                RetrievedDocument(
                    document=doc,
                    score=score,
                    vector_score=vector_score,
                    lexical_score=lexical_score,
                    reasons=tuple(reasons),
                )
            )

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]


def token_overlap_score(query_tokens: set[str], doc_tokens: set[str]) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0
    query_counts = Counter(query_tokens)
    doc_counts = Counter(doc_tokens)
    overlap = sum((query_counts & doc_counts).values())
    return overlap / max(1, len(query_tokens))
