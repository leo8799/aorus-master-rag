from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Document:
    doc_id: str
    content: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class RetrievedDocument:
    document: Document
    score: float
    vector_score: float
    lexical_score: float
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class QueryIntent:
    raw_query: str
    models: tuple[str, ...] = ()
    fields: tuple[str, ...] = ()


@dataclass
class GenerationMetrics:
    question: str
    retrieved_doc_ids: list[str] = field(default_factory=list)
    ttft_seconds: float | None = None
    total_seconds: float | None = None
    generated_tokens: int | None = None
    tokens_per_second: float | None = None
    answer_chars: int = 0
