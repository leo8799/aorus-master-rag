from __future__ import annotations

from .models import QueryIntent
from .text import contains_alias

GPU_MEMORY_HINTS = (
    "GPU",
    "graphics",
    "graphics card",
    "VRAM",
    "GDDR",
    "顯卡",
    "顯示卡",
    "顯示晶片",
)


class QueryParser:
    def __init__(self, spec: dict):
        self.model_aliases: list[tuple[str, str]] = []
        for variant in spec["variants"]:
            model = variant["model"]
            aliases = [model, *variant.get("aliases", [])]
            for alias in aliases:
                self.model_aliases.append((alias, model))

        self.field_aliases: list[tuple[str, str]] = []
        for field, aliases in spec.get("field_aliases", {}).items():
            self.field_aliases.append((field, field))
            for alias in aliases:
                self.field_aliases.append((alias, field))

        self.model_aliases.sort(key=lambda item: len(item[0]), reverse=True)
        self.field_aliases.sort(key=lambda item: len(item[0]), reverse=True)

    def parse(self, question: str) -> QueryIntent:
        models: list[str] = []
        fields: list[str] = []

        for alias, model in self.model_aliases:
            if contains_alias(question, alias) and model not in models:
                models.append(model)

        for alias, field in self.field_aliases:
            if contains_alias(question, alias) and field not in fields:
                fields.append(field)

        if "顯示晶片" in fields and "記憶體" in fields:
            if any(contains_alias(question, alias) for alias in GPU_MEMORY_HINTS):
                fields = [field for field in fields if field != "記憶體"]

        return QueryIntent(raw_query=question, models=tuple(models), fields=tuple(fields))
