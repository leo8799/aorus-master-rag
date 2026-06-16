from __future__ import annotations

from .models import RetrievedDocument

SYSTEM_PROMPT = """You are a precise hardware specification assistant for GIGABYTE AORUS MASTER 16 AM6H.
Answer only from the supplied context. If the context does not contain the answer, say that the specification table does not provide it.
Preserve model names, units, numbers, and caveats. If the user asks in Traditional Chinese, answer only in Traditional Chinese characters. If the user asks in English, answer in English.
When a question is variant-specific, do not mix BXH, BYH, and BZH specs.
Map every requested attribute to the exact value in the same spec field. Never relabel watts as VRAM: VRAM is GB GDDR7, while Maximum Graphics Power is W. For display questions, brightness is nits; contrast ratio is not brightness."""


def build_messages(question: str, retrieved: list[RetrievedDocument]) -> list[dict[str, str]]:
    context = format_context(retrieved)
    user_prompt = (
        "Context documents:\n"
        f"{context}\n\n"
        "User question:\n"
        f"{question}\n\n"
        "Answer with concise bullet points when multiple specs are involved. "
        "Use exact field names and values from the context; do not invent or swap units."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def format_context(retrieved: list[RetrievedDocument]) -> str:
    lines: list[str] = []
    for idx, item in enumerate(retrieved, start=1):
        doc = item.document
        lines.append(
            f"[D{idx}] id={doc.doc_id} score={item.score:.4f} "
            f"model={doc.metadata.get('model')} field={doc.metadata.get('field')} "
            f"source={doc.metadata.get('source_url')}\n{doc.content}"
        )
    return "\n\n".join(lines)
