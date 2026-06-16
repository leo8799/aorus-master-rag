from __future__ import annotations

import hashlib
import math
from collections.abc import Iterable

from .text import tokenize


class HashingEmbeddingBackend:
    """Deterministic vectorizer for tiny, structured spec corpora.

    It keeps retrieval fully local and CPU-only. For this project the corpus is
    mostly key-value specs, so character n-grams plus exact unit tokens are a
    strong low-memory baseline.
    """

    def __init__(self, dimensions: int = 768):
        self.dimensions = dimensions

    def embed(self, texts: Iterable[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self.dimensions
        for token in tokenize(text):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            value = int.from_bytes(digest, "little")
            index = value % self.dimensions
            sign = 1.0 if ((value >> 63) & 1) == 0 else -1.0
            weight = 1.0 + min(len(token), 12) / 24.0
            vec[index] += sign * weight
        return normalize(vec)


class LlamaCppEmbeddingBackend:
    """Embedding backend using llama.cpp GGUF embedding models."""

    def __init__(
        self,
        model_path: str,
        n_ctx: int = 512,
        n_threads: int | None = None,
        n_gpu_layers: int = 0,
    ):
        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError("llama-cpp-python is required for GGUF embeddings") from exc

        self.llm = Llama(
            model_path=model_path,
            embedding=True,
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_gpu_layers=n_gpu_layers,
            verbose=False,
        )

    def embed(self, texts: Iterable[str]) -> list[list[float]]:
        text_list = list(texts)
        result = self.llm.create_embedding(input=text_list)
        return [normalize(item["embedding"]) for item in result["data"]]


def normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vec))
    if norm == 0:
        return vec
    return [value / norm for value in vec]


def dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))
