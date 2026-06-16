# 4GB VRAM Quality-Oriented Benchmark

Date: 2026-06-13

## Decision

To improve answer quality under the 4GB VRAM limit, the assistant was upgraded from:

- `Qwen2.5-0.5B-Instruct-GGUF Q4_K_M`

to:

- `Qwen2.5-3B-Instruct-GGUF Q4_K_M`

The 3B Q4_K_M model is larger but still fits the target VRAM budget with full GPU offload at `n_ctx=2048`.

## Model Source

- Repository: `Qwen/Qwen2.5-3B-Instruct-GGUF`
- File: `qwen2.5-3b-instruct-q4_k_m.gguf`
- Quantization: `Q4_K_M`
- Local path: `models/qwen2.5-3b-instruct-q4_k_m.gguf`

## VRAM Evidence

Verbose llama.cpp loading reported:

```text
model params     = 3.40 B
model size       = 1.95 GiB
offloaded 37/37 layers to GPU
CPU buffer size  = 166.92 MiB
CUDA0 buffer size = 1834.83 MiB
CUDA0 KV buffer size = 72.00 MiB
CUDA0 compute buffer size = 300.75 MiB
```

Approximate llama.cpp GPU memory used by model buffers:

```text
1834.83 + 72.00 + 300.75 = 2207.58 MiB
```

This is about `2.16 GiB`, safely under the 4GB VRAM target.

## Pipeline Changes

Quality improvements applied:

- Switched generation model to 3B Q4_K_M.
- Added prompt guardrails:
  - watts must not be labeled as VRAM
  - brightness must be in nits
  - contrast ratio must not be used as brightness
  - Traditional Chinese questions should receive Traditional Chinese output
- Added common-spec deduplication for non-variant questions, so shared fields like display, battery, and ports do not appear three times for BXH/BYH/BZH.
- Added lightweight common Simplified-to-Traditional output normalization for Chinese answers.

## Retrieval Verification

```text
10 passed in 0.15s
field_recall_at_k = 1.0
model_recall_at_k = 1.0
fact_recall_at_k = 1.0
mrr = 1.0
```

## Generation Results

| Metric | Value |
|---|---:|
| Average TTFT | 0.319 s |
| Min TTFT | 0.227 s |
| Max TTFT | 0.411 s |
| Average TPS | 85.61 tokens/s |
| Min TPS | 83.41 tokens/s |
| Max TPS | 88.56 tokens/s |
| Average total generation time | 0.701 s |
| Fact coverage | 6/6 |

## CPU/GPU/Quality Comparison

| Model | Mode | Avg TTFT | Avg TPS | Fact Coverage | Notes |
|---|---|---:|---:|---:|---|
| Qwen2.5-0.5B Q4_K_M | CPU | 4.209 s | 51.85 | partial | baseline only |
| Qwen2.5-0.5B Q4_K_M | GPU | 0.115 s | 146.20 | partial | fast but confused VRAM/MGP and brightness/contrast |
| Qwen2.5-3B Q4_K_M | GPU | 0.319 s | 85.61 | 6/6 | best quality under 4GB VRAM |

## Final 3B Answers

```text
BYH 的顯卡和 VRAM 是多少？
- 顯卡: NVIDIA GeForce RTX 5080 Laptop GPU
- VRAM: 16GB GDDR7

Which model has RTX 5070 Ti and what is its maximum graphics power?
- RTX 5070 Ti model: AORUS MASTER 16 BZH
- Maximum Graphics Power: 140W

這台筆電的螢幕解析度、更新率與亮度是多少？
- 螢幕解析度: WQXGA (2560x1600)
- 更新率: 240Hz
- 亮度: 500 nits peak

How many Thunderbolt ports are listed and which versions are they?
- Thunderbolt ports listed: 2
- Thunderbolt 4: 1 (right side)
- Thunderbolt 5: 1 (left side)

電池容量和變壓器瓦數？
- 電池容量: 99Wh
- 電源瓦數: 330W

Compare BXH, BYH and BZH GPU memory.
- BXH: 24GB GDDR7
- BYH: 16GB GDDR7
- BZH: 12GB GDDR7
```

Full JSON result:

`benchmark-results/qwen2.5-3b-q4km-gpu-generation-improved.json`
