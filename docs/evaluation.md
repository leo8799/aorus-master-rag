# System Evaluation

## Objective

The assistant must answer product-spec questions for GIGABYTE AORUS MASTER 16 AM6H without confusing the three listed variants:

- `AORUS MASTER 16 BXH`: RTX 5090 Laptop GPU, 24GB GDDR7, 175W MGP
- `AORUS MASTER 16 BYH`: RTX 5080 Laptop GPU, 16GB GDDR7, 175W MGP
- `AORUS MASTER 16 BZH`: RTX 5070 Ti Laptop GPU, 12GB GDDR7, 140W MGP

Most other fields are shared across variants.

## Quantitative Metrics

### Retrieval

Run:

```powershell
uv run aorus-rag eval --mode retrieval
```

Metrics:

- `field_recall_at_k`: expected spec fields appear in top-k retrieved documents.
- `model_recall_at_k`: expected variants appear in top-k retrieved documents.
- `fact_recall_at_k`: expected facts are present in the joined top-k context.
- `mrr`: first relevant document rank, averaged across cases.

Expected target for this tiny structured corpus:

- `field_recall_at_k >= 0.95`
- `model_recall_at_k >= 0.95`
- `fact_recall_at_k >= 0.95`
- `mrr >= 0.75`

### Generation

Run:

```powershell
uv run aorus-rag eval --mode generation --model-path models/Qwen2.5-3B-Instruct-Q4_K_M.gguf
```

Metrics:

- `ttft_seconds`: wall-clock time from starting `create_chat_completion(stream=True)` to first streamed text chunk.
- `tokens_per_second`: generated tokens divided by post-first-token generation time. If llama.cpp tokenization is available, exact llama tokens are used; otherwise a conservative mixed Chinese/English estimate is used.

Suggested benchmark matrix:

| Model | Quant | Context | GPU layers | Target |
|---|---:|---:|---:|---|
| Qwen2.5-1.5B-Instruct | Q4_K_M | 3072 | all | lowest VRAM, faster TTFT |
| Qwen2.5-3B-Instruct | Q4_K_M | 4096 | all or partial | better Chinese/English answers under 4GB |

## Qualitative Checks

Use these prompts:

1. `BYH 的顯卡和 VRAM 是多少？`
2. `Which model has RTX 5070 Ti and what is its maximum graphics power?`
3. `請比較 BXH、BYH、BZH 的 GPU 差異`
4. `這台筆電的螢幕解析度、更新率與亮度是多少？`
5. `How many Thunderbolt ports are listed and which versions are they?`
6. `有沒有指紋辨識？`

Pass criteria:

- The answer cites the correct variant when a variant is specified.
- Unknown details, such as fingerprint reader information, are answered as not provided by the spec table.
- Units and numbers are preserved exactly, including `99Wh`, `330W`, `240Hz`, and GPU memory values.
- Mixed Chinese/English questions produce natural answers in the user's language.

## Pipeline Assessment

Strengths:

- Key-value chunking prevents one large spec table from mixing unrelated fields.
- Variant metadata avoids the common failure where a BYH question receives BXH GPU details.
- Hybrid scoring uses vector similarity, lexical overlap, model boost, and field boost; this is simple, inspectable, and well suited to small spec corpora.
- Hashing embeddings keep VRAM entirely for the LLM and make the system usable on consumer laptops.

Risks:

- Hashing embeddings are not a replacement for semantic embeddings on broad documents. For a larger support corpus, use a llama.cpp embedding GGUF such as BGE-M3 and keep it on CPU.
- Vendor pages can change. A production pipeline should periodically re-fetch and diff the official table before rebuilding the JSON.
- Very small SLMs may still hallucinate. The prompt instructs refusal when context is missing, but benchmark answers should be reviewed for unsupported claims.
