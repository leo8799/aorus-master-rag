from __future__ import annotations

from .models import Document


def build_documents(spec: dict) -> list[Document]:
    product = spec["product"]
    source_url = product["source_url"]
    field_aliases = spec.get("field_aliases", {})
    common_specs = spec["common_specs"]
    variants = spec["variants"]

    docs: list[Document] = []
    variant_lines = []
    for variant in variants:
        gpu = variant["variant_specs"]["顯示晶片"]
        alias_text = ", ".join(variant.get("aliases", []))
        variant_lines.append(f"{variant['model']} ({alias_text}): {gpu}")

    docs.append(
        Document(
            doc_id="product-overview",
            content=(
                f"Product: {product['name']}\n"
                f"Listed models: {', '.join(product['listed_models'])}\n"
                "Variant GPU mapping:\n"
                + "\n".join(variant_lines)
                + f"\nSource: {source_url}"
            ),
            metadata={
                "type": "overview",
                "product": product["name"],
                "model": "ALL",
                "model_aliases": ["AM6H", product["name"]],
                "field": "型號總覽",
                "field_aliases": ["model", "variant", "GPU", "型號", "差異"],
                "source_url": source_url,
            },
        )
    )

    for variant in variants:
        merged_specs = dict(common_specs)
        merged_specs.update(variant.get("variant_specs", {}))
        model = variant["model"]
        model_aliases = variant.get("aliases", [])
        gpu_value = merged_specs["顯示晶片"]

        docs.append(
            Document(
                doc_id=f"{_slug(model)}::summary",
                content=(
                    f"Product: {product['name']}\n"
                    f"Model: {model}\n"
                    f"Model aliases: {', '.join(model_aliases)}\n"
                    f"Key variant difference: {gpu_value}\n"
                    f"Common CPU: {merged_specs['中央處理器']}\n"
                    f"Common display: {merged_specs['顯示器']}\n"
                    f"Source: {source_url}"
                ),
                metadata={
                    "type": "summary",
                    "product": product["name"],
                    "model": model,
                    "model_aliases": model_aliases,
                    "field": "型號摘要",
                    "field_aliases": ["summary", "variant", "difference", "比較", "差異"],
                    "source_url": source_url,
                },
            )
        )

        for field_name, value in merged_specs.items():
            aliases = field_aliases.get(field_name, [])
            docs.append(
                Document(
                    doc_id=f"{_slug(model)}::{_slug(field_name)}",
                    content=(
                        f"Product: {product['name']}\n"
                        f"Model: {model}\n"
                        f"Model aliases: {', '.join(model_aliases)}\n"
                        f"Spec field: {field_name}\n"
                        f"Field aliases: {', '.join(aliases)}\n"
                        f"Spec value:\n{value}\n"
                        f"Source: {source_url}"
                    ),
                    metadata={
                        "type": "spec",
                        "product": product["name"],
                        "model": model,
                        "model_aliases": model_aliases,
                        "field": field_name,
                        "field_aliases": aliases,
                        "spec_value": value,
                        "source_url": source_url,
                    },
                )
            )

    return docs


def _slug(text: str) -> str:
    keep = []
    for ch in text.lower():
        if ch.isalnum():
            keep.append(ch)
        elif ch in {" ", "-", "_", "/"}:
            keep.append("-")
    slug = "".join(keep).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug
