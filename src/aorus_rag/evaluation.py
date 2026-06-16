from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any

from .models import RetrievedDocument
from .text import fold_text


@dataclass(frozen=True)
class EvaluationCase:
    question: str
    expected_models: tuple[str, ...]
    expected_fields: tuple[str, ...]
    expected_facts: tuple[str, ...]


DEFAULT_EVAL_CASES = [
    EvaluationCase(
        question="BYH 的顯卡和 VRAM 是多少？",
        expected_models=("AORUS MASTER 16 BYH",),
        expected_fields=("顯示晶片",),
        expected_facts=("RTX 5080", "16GB GDDR7"),
    ),
    EvaluationCase(
        question="Which model has RTX 5070 Ti and what is its maximum graphics power?",
        expected_models=("AORUS MASTER 16 BZH",),
        expected_fields=("顯示晶片",),
        expected_facts=("RTX 5070 Ti", "140W"),
    ),
    EvaluationCase(
        question="這台筆電的螢幕解析度、更新率與亮度是多少？",
        expected_models=(),
        expected_fields=("顯示器",),
        expected_facts=("2560x1600", "240Hz", "500 nits"),
    ),
    EvaluationCase(
        question="How many Thunderbolt ports are listed and which versions are they?",
        expected_models=(),
        expected_fields=("連接埠",),
        expected_facts=("Thunderbolt 5", "Thunderbolt 4"),
    ),
    EvaluationCase(
        question="電池容量和變壓器瓦數？",
        expected_models=(),
        expected_fields=("電池", "變壓器"),
        expected_facts=("99Wh", "330W"),
    ),
    EvaluationCase(
        question="Compare BXH, BYH and BZH GPU memory.",
        expected_models=("AORUS MASTER 16 BXH", "AORUS MASTER 16 BYH", "AORUS MASTER 16 BZH"),
        expected_fields=("顯示晶片",),
        expected_facts=("24GB GDDR7", "16GB GDDR7", "12GB GDDR7"),
    ),
]


class ProgressBar:
    def __init__(self, total: int, label: str, enabled: bool = True, width: int = 24):
        self.total = total
        self.label = label
        self.enabled = enabled
        self.width = width

    def render(self, completed: int, detail: str = ""):
        if not self.enabled:
            return
        ratio = completed / self.total if self.total else 1.0
        filled = min(self.width, int(round(self.width * ratio)))
        bar = "#" * filled + "-" * (self.width - filled)
        suffix = f" {truncate(detail, 52)}" if detail else ""
        print(f"\r{self.label} [{bar}] {completed}/{self.total}{suffix}", end="", file=sys.stderr, flush=True)

    def finish(self):
        if self.enabled:
            print(file=sys.stderr, flush=True)


def truncate(text: str, limit: int) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def evaluate_retrieval(
    pipeline,
    cases: list[EvaluationCase] | None = None,
    top_k: int = 6,
    show_progress: bool = False,
) -> dict[str, Any]:
    cases = cases or DEFAULT_EVAL_CASES
    rows = []
    field_hits = 0
    model_hits = 0
    fact_hits = 0
    reciprocal_ranks = []
    progress = ProgressBar(total=len(cases), label="retrieval", enabled=show_progress)
    progress.render(0)

    try:
        for idx, case in enumerate(cases, start=1):
            retrieved = pipeline.retrieve(case.question, top_k=top_k)
            retrieved_models = {item.document.metadata.get("model") for item in retrieved}
            retrieved_fields = {item.document.metadata.get("field") for item in retrieved}
            joined_context = fold_text("\n".join(item.document.content for item in retrieved))

            field_hit = all(field in retrieved_fields for field in case.expected_fields)
            model_hit = all(model in retrieved_models for model in case.expected_models)
            fact_hit = all(fold_text(fact) in joined_context for fact in case.expected_facts)

            first_good_rank = first_relevant_rank(case, retrieved)
            if first_good_rank:
                reciprocal_ranks.append(1 / first_good_rank)
            else:
                reciprocal_ranks.append(0.0)

            field_hits += int(field_hit)
            model_hits += int(model_hit)
            fact_hits += int(fact_hit)
            rows.append(
                {
                    "question": case.question,
                    "field_hit": field_hit,
                    "model_hit": model_hit,
                    "fact_hit": fact_hit,
                    "first_relevant_rank": first_good_rank,
                    "top_docs": [
                        {
                            "doc_id": item.document.doc_id,
                            "score": round(item.score, 4),
                            "model": item.document.metadata.get("model"),
                            "field": item.document.metadata.get("field"),
                        }
                        for item in retrieved
                    ],
                }
            )
            progress.render(idx, case.question)
    finally:
        progress.finish()

    total = len(cases)
    return {
        "cases": total,
        "field_recall_at_k": field_hits / total,
        "model_recall_at_k": model_hits / total,
        "fact_recall_at_k": fact_hits / total,
        "mrr": sum(reciprocal_ranks) / total,
        "rows": rows,
    }


def first_relevant_rank(case: EvaluationCase, retrieved: list[RetrievedDocument]) -> int | None:
    for rank, item in enumerate(retrieved, start=1):
        model = item.document.metadata.get("model")
        field = item.document.metadata.get("field")
        model_ok = not case.expected_models or model in case.expected_models or model == "ALL"
        field_ok = not case.expected_fields or field in case.expected_fields or field in {"型號摘要", "型號總覽"}
        if model_ok and field_ok:
            return rank
    return None


def run_generation_benchmark(
    pipeline,
    generator,
    cases: list[EvaluationCase] | None = None,
    top_k: int = 6,
    show_progress: bool = False,
):
    cases = cases or DEFAULT_EVAL_CASES
    rows = []
    progress = ProgressBar(total=len(cases), label="generation", enabled=show_progress)
    progress.render(0)

    try:
        for idx, case in enumerate(cases, start=1):
            progress.render(idx - 1, case.question)
            answer = "".join(pipeline.stream_answer(case.question, generator=generator, top_k=top_k))
            metrics = pipeline.last_metrics
            rows.append(
                {
                    "question": case.question,
                    "answer": answer,
                    "metrics": metrics.__dict__ if metrics else None,
                }
            )
            progress.render(idx, case.question)
    finally:
        progress.finish()
    return {"cases": len(cases), "rows": rows}


def dump_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)
