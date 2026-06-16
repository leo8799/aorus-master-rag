from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .data import default_spec_path
from .embedding import HashingEmbeddingBackend, LlamaCppEmbeddingBackend
from .evaluation import dump_json, evaluate_retrieval, run_generation_benchmark
from .generator import LlamaCppGenerator
from .pipeline import RagPipeline


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "handler"):
        parser.print_help()
        return 2
    return args.handler(args)


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--spec-path", default=str(default_spec_path()))
    common.add_argument("--embedding-model-path", default=None)
    common.add_argument("--embedding-gpu-layers", type=int, default=0)
    common.add_argument("--top-k", type=int, default=5)

    parser = argparse.ArgumentParser(prog="aorus-rag")
    subparsers = parser.add_subparsers(dest="command")

    retrieve = subparsers.add_parser("retrieve", parents=[common])
    retrieve.add_argument("--question", required=True)
    retrieve.set_defaults(handler=handle_retrieve)

    ask = subparsers.add_parser("ask", parents=[common])
    add_generation_args(ask)
    ask.add_argument("--question", required=True)
    ask.set_defaults(handler=handle_ask)

    eval_parser = subparsers.add_parser("eval", parents=[common])
    eval_parser.add_argument("--mode", choices=["retrieval", "generation"], default="retrieval")
    eval_parser.add_argument("--no-progress", action="store_true")
    add_generation_args(eval_parser, required=False)
    eval_parser.set_defaults(handler=handle_eval)

    return parser


def add_generation_args(parser: argparse.ArgumentParser, required: bool = True):
    parser.add_argument("--model-path", required=required)
    parser.add_argument("--ctx-size", type=int, default=4096)
    parser.add_argument("--gpu-layers", type=int, default=-1)
    parser.add_argument("--threads", type=int, default=None)
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--chat-format", default=None)


def handle_retrieve(args) -> int:
    pipeline = build_pipeline(args)
    retrieved = pipeline.retrieve(args.question, top_k=args.top_k)
    for idx, item in enumerate(retrieved, start=1):
        doc = item.document
        print(f"[{idx}] score={item.score:.4f} model={doc.metadata.get('model')} field={doc.metadata.get('field')}")
        print(doc.content)
        print()
    return 0


def handle_ask(args) -> int:
    pipeline = build_pipeline(args)
    generator = build_generator(args)
    for token in pipeline.stream_answer(args.question, generator=generator, top_k=args.top_k):
        print(token, end="", flush=True)
    print()
    if pipeline.last_metrics:
        print(json.dumps(pipeline.last_metrics.__dict__, ensure_ascii=False), file=sys.stderr)
    return 0


def handle_eval(args) -> int:
    pipeline = build_pipeline(args)
    show_progress = not args.no_progress
    if args.mode == "retrieval":
        print(dump_json(evaluate_retrieval(pipeline, top_k=args.top_k, show_progress=show_progress)))
        return 0

    if not args.model_path:
        print("--model-path is required for generation benchmark", file=sys.stderr)
        return 2
    generator = build_generator(args)
    print(dump_json(run_generation_benchmark(pipeline, generator, top_k=args.top_k, show_progress=show_progress)))
    return 0


def build_pipeline(args) -> RagPipeline:
    embedder = build_embedder(args)
    return RagPipeline.from_spec_path(Path(args.spec_path), embedder=embedder)


def build_embedder(args):
    if args.embedding_model_path:
        return LlamaCppEmbeddingBackend(
            args.embedding_model_path,
            n_gpu_layers=args.embedding_gpu_layers,
        )
    return HashingEmbeddingBackend()


def build_generator(args) -> LlamaCppGenerator:
    return LlamaCppGenerator(
        model_path=args.model_path,
        n_ctx=args.ctx_size,
        n_gpu_layers=args.gpu_layers,
        n_threads=args.threads,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        chat_format=args.chat_format,
    )


if __name__ == "__main__":
    raise SystemExit(main())
