from __future__ import annotations

from collections.abc import Iterable

from .text import estimate_token_count


class LlamaCppGenerator:
    def __init__(
        self,
        model_path: str,
        n_ctx: int = 4096,
        n_gpu_layers: int = -1,
        n_threads: int | None = None,
        temperature: float = 0.1,
        max_tokens: int = 512,
        chat_format: str | None = None,
    ):
        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError("llama-cpp-python is required for generation") from exc

        kwargs = {
            "model_path": model_path,
            "n_ctx": n_ctx,
            "n_gpu_layers": n_gpu_layers,
            "n_threads": n_threads,
            "verbose": False,
        }
        if chat_format:
            kwargs["chat_format"] = chat_format
        self.llm = Llama(**kwargs)
        self.temperature = temperature
        self.max_tokens = max_tokens

    def stream_chat(self, messages: list[dict[str, str]]) -> Iterable[str]:
        stream = self.llm.create_chat_completion(
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
        )
        for chunk in stream:
            choice = chunk["choices"][0]
            delta = choice.get("delta", {})
            text = delta.get("content") or choice.get("text") or ""
            if text:
                yield text

    def count_tokens(self, text: str) -> int:
        try:
            return len(self.llm.tokenize(text.encode("utf-8")))
        except Exception:
            return estimate_token_count(text)
