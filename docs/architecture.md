# Architecture Notes

## Constraints

This project is designed for a resource-limited consumer laptop:

- VRAM budget: 4GB
- Environment manager: uv
- Inference engine: llama.cpp through `llama-cpp-python`
- RAG implementation: pure Python, no LangChain, no LlamaIndex
- Language support: Traditional Chinese and English mixed questions

## Model Strategy

Primary recommendation:

- `Qwen2.5-3B-Instruct-Q4_K_M.gguf`
- `n_ctx=4096`
- `n_gpu_layers=-1` when the laptop has enough free VRAM

Lower-memory fallback:

- `Qwen2.5-1.5B-Instruct-Q4_K_M.gguf`
- `n_ctx=3072`
- partial GPU offload if the OS or browser consumes too much VRAM

Qwen is chosen because it is strong in Chinese/English mixed prompts. A 7B model is avoided because it is too tight for a dependable 4GB VRAM deployment once context, KV cache, and desktop overhead are included.

## Data Parsing

The official GIGABYTE page exposes the product as `AORUS MASTER 16 AM6H`, while the spec table lists three variants:

- `AORUS MASTER 16 BXH`
- `AORUS MASTER 16 BYH`
- `AORUS MASTER 16 BZH`

The structured data file keeps common fields separate from per-variant overrides. During chunking, every variant receives its own key-value documents. This gives the retriever a precise target for questions such as:

- `BYH 的顯卡和 VRAM 是多少？`
- `Which model has RTX 5070 Ti?`

Each generated document contains:

- product name
- model name
- model aliases
- spec field
- field aliases
- spec value
- source URL

This is deliberate. The LLM is not asked to infer table structure from a long unstructured dump; it only receives top-ranked, already-normalized key-value chunks.

## Retrieval

The vector index is implemented in `aorus_rag.retriever.VectorIndex`.

Scoring combines:

- cosine similarity over embeddings
- lexical token overlap
- model alias boost
- field alias boost
- a small preference for exact spec documents

Default embedding is `HashingEmbeddingBackend`, a deterministic CPU vectorizer. It uses Latin tokens, CJK character n-grams, and unit tokens such as `99Wh`, `330W`, `240Hz`, and `16GB`. This keeps VRAM for the LLM.

For larger corpora, pass `--embedding-model-path` to use a llama.cpp embedding GGUF.

## Generation

`LlamaCppGenerator` wraps:

```python
llm.create_chat_completion(..., stream=True)
```

The pipeline records:

- TTFT: start of generation to first streamed chunk
- TPS: generated tokens divided by post-first-token elapsed time

The prompt explicitly requires answers to stay inside retrieved context and to say the spec table does not provide an answer when information is missing.

## CLI Streaming

The project exposes streaming through the CLI:

```powershell
uv run aorus-rag ask --model-path models/qwen2.5-3b-instruct-q4_k_m.gguf --question "BYH 的顯卡和 VRAM 是多少？"
```

Generation benchmark progress is written to stderr so JSON output remains usable for saved benchmark reports. The project intentionally keeps the surface area to CLI commands, making the evaluation project easier to inspect and maintain.
