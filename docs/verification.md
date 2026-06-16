# Verification Report

Date: 2026-06-12

Environment:

- Python: 3.12.10
- uv: 0.11.21
- OS shell: Windows PowerShell
- uv cache redirected to workspace: `C:\Users\leo87\Documents\Codex\2026-06-12\ai-ai-gigabyte-aorus-master-16\.uv-cache`

## Commands Run

Syntax check:

```powershell
..\..\tools\bin\python.cmd -m compileall src tests
```

Result: passed.

Install dev environment:

```powershell
..\..\tools\bin\uv.exe sync --extra dev --python C:\Users\leo87\AppData\Local\Programs\Python\Python312\python.exe
```

Result: passed.

Unit tests:

```powershell
..\..\tools\bin\uv.exe run pytest -q
```

Result:

```text
8 passed in 0.11s
```

Retrieval benchmark:

```powershell
..\..\tools\bin\uv.exe run aorus-rag eval --mode retrieval
```

Result:

```text
field_recall_at_k = 1.0
model_recall_at_k = 1.0
fact_recall_at_k = 1.0
mrr = 1.0
```

CLI smoke test:

```powershell
..\..\tools\bin\uv.exe run aorus-rag retrieve --question "Compare BXH, BYH and BZH GPU memory." --top-k 5
```

Result: top 3 documents are the three GPU spec chunks:

- BXH: RTX 5090 Laptop GPU, 24GB GDDR7, 175W MGP
- BYH: RTX 5080 Laptop GPU, 16GB GDDR7, 175W MGP
- BZH: RTX 5070 Ti Laptop GPU, 12GB GDDR7, 140W MGP

## Fix Applied During Verification

The benchmark exposed an ambiguity in the query `GPU memory`: the word `memory` was initially pulling system RAM chunks above GPU chunks. The query parser now treats `memory` as VRAM when GPU, graphics, VRAM, GDDR, 顯卡, 顯示卡, or 顯示晶片 are present.

Regression tests were added for this case.

## Generation Extra Status

The core RAG project runs successfully. Full local llama.cpp Python binding installation was then completed separately.

First attempt:

```powershell
..\..\tools\bin\uv.exe sync --extra dev --extra generation
```

Findings from earlier attempts:

- `llama-cpp-python==0.3.28` failed on Windows CP950 shell while compiling llama.cpp vendor tools.
- The project was adjusted to `llama-cpp-python>=0.2.90,<0.3.0`.
- `llama-cpp-python==0.2.90` compiled successfully in about 14 minutes, but wheel packaging failed when the uv cache lived under the long workspace path. The failure was caused by a deep vendor path exceeding practical Windows path limits during package file scanning.

Successful command:

```powershell
$env:UV_CACHE_DIR = "C:\uvcache"
$env:TEMP = "C:\uvtmp"
$env:TMP = "C:\uvtmp"
$env:CMAKE_BUILD_PARALLEL_LEVEL = "4"
..\..\tools\bin\uv.exe sync --extra dev --extra generation --python C:\Users\leo87\AppData\Local\Programs\Python\Python312\python.exe
```

Result:

```text
Built llama-cpp-python==0.2.90
Installed llama-cpp-python==0.2.90
```

Verification:

```powershell
..\..\tools\bin\uv.exe run python -c "import llama_cpp; print(llama_cpp.__version__)"
```

Result:

```text
0.2.90
```

The generation code is now installed and importable. End-to-end TTFT/TPS generation still needs a local GGUF model file, for example `models/Qwen2.5-3B-Instruct-Q4_K_M.gguf`.
