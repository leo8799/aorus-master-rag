# TTFT/TPS Benchmark Summary

Date: 2026-06-13

## Setup

- Inference engine: llama.cpp through `llama-cpp-python`
- Package version: `llama-cpp-python==0.2.90`
- Model: `Qwen/Qwen2.5-0.5B-Instruct-GGUF`
- Quantization: `Q4_K_M`
- Local file: `models/qwen2.5-0.5b-instruct-q4_k_m.gguf`
- Model size: about 468 MiB
- GPU layers: `0`
- Runtime mode: CPU-only
- Context size: `2048`
- Max generated tokens per question: `160`
- Chat format: `chatml`
- Benchmark cases: `6`

## Aggregate Results

| Metric | Value |
|---|---:|
| Average TTFT | 4.209 s |
| Min TTFT | 2.924 s |
| Max TTFT | 5.278 s |
| Average TPS | 51.85 tokens/s |
| Min TPS | 49.64 tokens/s |
| Max TPS | 53.98 tokens/s |
| Average total generation time | 5.131 s |

## Per-Question Results

| Question | TTFT | TPS | Total |
|---|---:|---:|---:|
| BYH 的顯卡和 VRAM 是多少？ | 4.237 s | 51.89 | 4.853 s |
| Which model has RTX 5070 Ti and what is its maximum graphics power? | 3.958 s | 52.88 | 5.357 s |
| 這台筆電的螢幕解析度、更新率與亮度是多少？ | 4.189 s | 49.64 | 5.317 s |
| How many Thunderbolt ports are listed and which versions are they? | 4.669 s | 51.44 | 5.835 s |
| 電池容量和變壓器瓦數？ | 2.924 s | 53.98 | 3.461 s |
| Compare BXH, BYH and BZH GPU memory. | 5.278 s | 51.28 | 5.961 s |

## Qualitative Notes

This run is useful as a llama.cpp smoke benchmark on a very small model. Retrieval was correct, but answer quality was not fully reliable with `Qwen2.5-0.5B-Instruct-Q4_K_M`.

Observed issues:

- One answer mixed VRAM and MGP, saying `VRAM: 175W`.
- One display answer used the contrast ratio as brightness.
- Some Traditional Chinese answers contained Simplified Chinese words.

Recommendation:

- Use `Qwen2.5-1.5B-Instruct-Q4_K_M` or `Qwen2.5-3B-Instruct-Q4_K_M` for the actual product QA assistant.
- Keep this 0.5B result as a lower-bound latency baseline.
- Re-run the same benchmark with GPU offload after installing a CUDA-enabled `llama-cpp-python` build.

Full JSON result:

`benchmark-results/qwen2.5-0.5b-q4km-cpu-generation.json`
