from __future__ import annotations

import time
from collections.abc import Iterable
from pathlib import Path

from .chunking import build_documents
from .data import load_spec
from .embedding import HashingEmbeddingBackend
from .models import GenerationMetrics, RetrievedDocument
from .prompt import build_messages
from .query import QueryParser
from .retriever import VectorIndex
from .text import contains_cjk, estimate_token_count, normalize_traditional_output


class RagPipeline:
    def __init__(self, spec: dict, index: VectorIndex, query_parser: QueryParser):
        self.spec = spec
        self.index = index
        self.query_parser = query_parser
        self.last_metrics: GenerationMetrics | None = None

    @classmethod
    def from_spec_path(cls, spec_path: str | Path | None = None, embedder=None) -> "RagPipeline":
        spec = load_spec(spec_path)
        documents = build_documents(spec)
        embedder = embedder or HashingEmbeddingBackend()
        index = VectorIndex.build(documents, embedder)
        return cls(spec=spec, index=index, query_parser=QueryParser(spec))

    def retrieve(self, question: str, top_k: int = 5) -> list[RetrievedDocument]:
        intent = self.query_parser.parse(question)
        retrieved = self.index.search(question, intent=intent, top_k=max(top_k * 4, top_k))
        if not intent.models:
            retrieved = dedupe_common_spec_values(retrieved)
        return retrieved[:top_k]

    def stream_answer(self, question: str, generator, top_k: int = 5) -> Iterable[str]:
        retrieved = self.retrieve(question, top_k=top_k)
        messages = build_messages(question, retrieved)
        metrics = GenerationMetrics(
            question=question,
            retrieved_doc_ids=[item.document.doc_id for item in retrieved],
        )

        started = time.perf_counter()
        first_token_at: float | None = None
        answer_parts: list[str] = []
        normalize_traditional = contains_cjk(question)

        for piece in generator.stream_chat(messages):
            now = time.perf_counter()
            if first_token_at is None:
                first_token_at = now
                metrics.ttft_seconds = first_token_at - started
            if normalize_traditional:
                piece = normalize_traditional_output(piece)
            answer_parts.append(piece)
            yield piece

        finished = time.perf_counter()
        answer = "".join(answer_parts)
        metrics.total_seconds = finished - started
        metrics.answer_chars = len(answer)
        if hasattr(generator, "count_tokens"):
            metrics.generated_tokens = generator.count_tokens(answer)
        else:
            metrics.generated_tokens = estimate_token_count(answer)

        token_window = finished - (first_token_at or started)
        if token_window > 0:
            metrics.tokens_per_second = metrics.generated_tokens / token_window
        self.last_metrics = metrics


def dedupe_common_spec_values(retrieved: list[RetrievedDocument]) -> list[RetrievedDocument]:
    seen: set[tuple[str, str]] = set()
    deduped: list[RetrievedDocument] = []
    for item in retrieved:
        metadata = item.document.metadata
        if metadata.get("type") == "spec" and metadata.get("spec_value"):
            key = (str(metadata.get("field")), str(metadata.get("spec_value")))
            if key in seen:
                continue
            seen.add(key)
        deduped.append(item)
    return deduped
