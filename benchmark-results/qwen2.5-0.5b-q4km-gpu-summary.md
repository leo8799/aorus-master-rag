# GPU TTFT/TPS Benchmark Summary

Date: 2026-06-13

## Setup

- Inference engine: llama.cpp through `llama-cpp-python`
- Package version: `llama-cpp-python==0.2.90`
- CUDA package source: prebuilt `cu122` wheel
- GPU: NVIDIA GeForce RTX 2080 Ti
- Driver: 571.96
- CUDA driver capability shown by `nvidia-smi`: 12.8
- CUDA toolkit: 12.2
- Model: `Qwen/Qwen2.5-0.5B-Instruct-GGUF`
- Quantization: `Q4_K_M`
- Local file: `models/qwen2.5-0.5b-instruct-q4_k_m.gguf`
- GPU layers: `-1`
- Context size: `2048`
- Max generated tokens per question: `160`
- Chat format: `chatml`
- Benchmark cases: `6`

GPU offload was confirmed with verbose llama.cpp load logs:

```text
ggml_cuda_init: found 1 CUDA devices:
  Device 0: NVIDIA GeForce RTX 2080 Ti, compute capability 7.5, VMM: yes
llm_load_tensors: offloaded 25/25 layers to GPU
llm_load_tensors: CUDA0 buffer size = 373.73 MiB
llama_kv_cache_init: CUDA0 KV buffer size = 6.00 MiB
```

## Aggregate Results

| Metric | Value |
|---|---:|
| Average TTFT | 0.115 s |
| Min TTFT | 0.070 s |
| Max TTFT | 0.191 s |
| Average TPS | 146.20 tokens/s |
| Min TPS | 128.28 tokens/s |
| Max TPS | 158.38 tokens/s |
| Average total generation time | 0.369 s |

## CPU vs GPU

| Mode | Avg TTFT | Avg TPS | Avg Total |
|---|---:|---:|---:|
| CPU-only | 4.209 s | 51.85 tokens/s | 5.131 s |
| GPU offload | 0.115 s | 146.20 tokens/s | 0.369 s |

Observed speedup:

- TTFT improved by about 36.6x.
- TPS improved by about 2.8x.
- Total generation time improved by about 13.9x.

## Per-Question Results

| Question | TTFT | TPS | Total |
|---|---:|---:|---:|
| BYH 的顯卡和 VRAM 是多少？ | 0.191 s | 128.28 | 0.440 s |
| Which model has RTX 5070 Ti and what is its maximum graphics power? | 0.099 s | 149.01 | 0.254 s |
| 這台筆電的螢幕解析度、更新率與亮度是多少？ | 0.105 s | 148.17 | 0.395 s |
| How many Thunderbolt ports are listed and which versions are they? | 0.109 s | 150.01 | 0.509 s |
| 電池容量和變壓器瓦數？ | 0.070 s | 158.38 | 0.253 s |
| Compare BXH, BYH and BZH GPU memory. | 0.119 s | 143.36 | 0.363 s |

## Qualitative Notes

The GPU run measures inference speed correctly, but answer quality is still limited by the very small `0.5B` model.

Observed issues:

- The answer for BYH still mixed VRAM and MGP, saying `VRAM: 175W`.
- The display answer still confused brightness with contrast ratio.
- One GPU memory comparison run answered BXH/BYH incorrectly.

Recommendation:

- Keep this as a GPU latency baseline.
- Use `Qwen2.5-1.5B-Instruct-Q4_K_M` or `Qwen2.5-3B-Instruct-Q4_K_M` for the final assistant benchmark.
- Re-run with the same command and `--gpu-layers -1` after downloading the larger GGUF.

Full JSON result:

`benchmark-results/qwen2.5-0.5b-q4km-gpu-generation.json`
