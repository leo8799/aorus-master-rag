# AORUS MASTER 16 AM6H Pure Python RAG

針對 GIGABYTE AORUS MASTER 16 AM6H 官方規格表的輕量 RAG 問答系統。核心邏輯包含 chunking、vector index、retrieval、prompting、streaming generation 與 TTFT/TPS benchmark，全部以純 Python 撰寫，沒有使用 LangChain 或 LlamaIndex。

由於測驗情境為消費級筆電 AI 助手：所以我就預設在Windows環境下（如果是Linux的話，下面啟動命令的換行符要換成\），所以啟動命令主要是Windows PowerShell的命令。

資料來源：GIGABYTE Taiwan 官方規格頁 `https://www.gigabyte.com/tw/Laptop/AORUS-MASTER-16-AM6H/sp`，擷取日期 `2026-06-12`。

## Quick Start

進入專案：

```powershell
cd aorus-master-rag
```

安裝 Python 依賴：

```powershell
uv sync --extra dev
```

Windows + NVIDIA CUDA 建議直接安裝預建 wheel，避免原生編譯太久：

```powershell
uv pip install --force-reinstall --no-cache `
  --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu122 `
  llama-cpp-python==0.2.90
```

或執行專案腳本：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-llama-cpp-cu122.ps1
```

只有在需要客製編譯時才使用 source build：

```powershell
uv sync --extra dev --extra generation
```

模型檔不提交到 Git，請從 Hugging Face 下載建議模型：

- Model page: `https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF`
- Suggested file: `qwen2.5-3b-instruct-q4_k_m.gguf`
- Local path: `models/qwen2.5-3b-instruct-q4_k_m.gguf`

直接檔案頁面：`https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/blob/main/qwen2.5-3b-instruct-q4_k_m.gguf`

查詢：

```powershell
uv run aorus-rag ask `
  --model-path models/qwen2.5-3b-instruct-q4_k_m.gguf `
  --gpu-layers -1 `
  --ctx-size 2048 `
  --question "BYH 的顯卡和 VRAM 是多少？"
```

只看檢索結果：

```powershell
uv run aorus-rag retrieve --question "Which model has RTX 5070 Ti and what is its MGP?"
```

Retrieval benchmark：

```powershell
uv run aorus-rag eval --mode retrieval
```

Generation benchmark，進度條會顯示在 stderr，JSON 結果輸出到 stdout：

```powershell
uv run aorus-rag eval `
  --mode generation `
  --model-path models/qwen2.5-3b-instruct-q4_k_m.gguf `
  --gpu-layers -1 `
  --ctx-size 2048 `
  --max-tokens 180 `
  --chat-format chatml
```

## Current Results

`Qwen2.5-3B-Instruct Q4_K_M` GPU benchmark：

- Average TTFT: `0.319 s`
- Average TPS: `85.61 tokens/s`
- Fact coverage: `6/6`
- Retrieval benchmark: `field/model/fact recall = 1.0`, `mrr = 1.0`
- Approx llama.cpp GPU buffers: `2.16 GiB`, under the 4GB VRAM target

完整報告：

```text
benchmark-results/qwen2.5-3b-q4km-gpu-quality-summary.md
```

## Design Summary

- 環境管理：`uv`
- 推論引擎：`llama-cpp-python`
- 建議模型：`Qwen2.5-3B-Instruct-Q4_K_M.gguf`
- 4GB VRAM 策略：使用 3B GGUF 4-bit 量化，embedding 預設使用 CPU hashing vector
- 問答語言：支援繁體中文與英文混合提問
- 資料結構：規格表以 key-value 保存，並將 `BXH/BYH/BZH` 三個子型號分開建模
- 使用介面：CLI only，沒有 HTTP API/server

## Why This Model

本專案選擇 `Qwen2.5-3B-Instruct Q4_K_M`，目標不是追求最高 TPS，而是在 `4GB VRAM` 限制下讓產品規格問答盡可能準確。這個任務的錯誤成本主要來自「數字與單位混淆」，例如把 `175W` 當成 VRAM、把對比度當亮度、或把 BXH/BYH/BZH 的 GPU 規格混在一起。因此模型需要有足夠的指令理解與中英混合能力，而不只是能快速吐字。

選型考量：

- `Qwen2.5` 對繁體中文與英文混合提問表現穩定，適合台灣產品規格頁與中英混合硬體術語。
- `3B` 是品質與資源的平衡點：明顯比 `0.5B` 更能遵守 prompt 與區分規格欄位，又比 `7B` 更容易放進 4GB VRAM。
- `Instruct` 版本適合問答與格式化輸出，不需要額外 fine-tune 就能依照 RAG context 回答。
- `Q4_K_M` 是 llama.cpp 常用的 4-bit 量化格式，保留合理品質，同時大幅降低 VRAM footprint。
- Embedding 不佔 VRAM：預設使用 CPU hashing embedding，讓 GPU 記憶體主要留給生成模型。

實測 VRAM 證據，使用 `n_ctx=2048`、`n_gpu_layers=-1`：

```text
model size            = 1.95 GiB
offloaded layers      = 37/37
CUDA0 model buffer    = 1834.83 MiB
CUDA0 KV buffer       =   72.00 MiB
CUDA0 compute buffer  =  300.75 MiB
approx GPU buffers    = 2207.58 MiB ≈ 2.16 GiB
```

這代表模型可全層 GPU offload，且 llama.cpp 主要 GPU buffers 約 `2.16 GiB`，低於 `4GB VRAM` 限制。即使加上 runtime overhead，仍比 7B 量化模型安全得多。

候選模型比較：

| Candidate | 優點 | 問題 | 結論 |
|---|---|---|---|
| `Qwen2.5-0.5B-Instruct Q4_K_M` | 非常快，GPU TTFT 約 `0.115s`、TPS 約 `146.20` | 實測會混淆 VRAM/MGP、亮度/對比度，規格 QA 風險高 | 只適合作為 latency baseline |
| `Qwen2.5-1.5B-Instruct Q4_K_M` | 更省 VRAM，品質應高於 0.5B | 品質緩衝較小，遇到欄位比較仍可能不穩 | 可作低記憶體 fallback |
| `Qwen2.5-3B-Instruct Q4_K_M` | 4GB VRAM 內品質最佳，fact coverage `6/6` | TPS 比 0.5B 低 | 本專案主選 |
| `7B Q4` | 理論品質更好 | 4GB VRAM 下 KV cache、桌面環境與 runtime overhead 太緊 | 不適合此限制 |

實測結論：

| Model | Mode | Avg TTFT | Avg TPS | Fact Coverage | Notes |
|---|---|---:|---:|---:|---|
| Qwen2.5-0.5B Q4_K_M | GPU | `0.115s` | `146.20 tok/s` | partial | 快，但混淆規格欄位 |
| Qwen2.5-3B Q4_K_M | GPU | `0.319s` | `85.61 tok/s` | `6/6` | 品質最佳且符合 4GB VRAM |

因此最終選擇是：`Qwen2.5-3B-Instruct Q4_K_M + llama.cpp CUDA offload + CPU hashing retrieval`。它的 TTFT 仍低於半秒，TPS 足夠互動式問答使用，同時能正確回答 VRAM、MGP、螢幕亮度、Thunderbolt 數量與三個 GPU variant 的比較。

## Why CPU Hashing Retrieval

本專案的 retrieval 預設使用 `CPU hashing retrieval`，而不是額外載入 embedding 模型。它的意思是：在 CPU 上把 query 與規格 chunk tokenize，將每個 token 用 deterministic hash 映射到固定維度向量，接著用向量相似度與 lexical/metadata 加權排序。

簡化流程：

```text
query / spec chunk
→ tokenize
→ hash each token into a fixed-size vector
→ normalize vector
→ dot product similarity
→ hybrid score with model/field boosts
→ top-k context
```

選這個方法，是因為本任務不是開放領域知識庫，而是一份很小、很結構化的產品規格表。使用者問的多半是精確欄位、型號、數字與單位：

- `BYH`
- `RTX 5080`
- `16GB GDDR7`
- `175W`
- `Thunderbolt 5`
- `99Wh`
- `330W`

這類問題最重要的是「不要抓錯型號或欄位」，而不是理解大段文章的抽象語意。因此 retrieval pipeline 採用 hybrid scoring：

```text
hashing vector similarity
+ lexical token overlap
+ model alias boost
+ field alias boost
+ structured key-value metadata
```

例子：

- 問到 `BYH`，`AORUS MASTER 16 BYH` 的文件會加分。
- 問到 `VRAM / GPU / 顯卡`，`顯示晶片` 欄位會加分。
- 問到 `battery / 電池`，`電池` 欄位會加分。
- 問到 `GPU memory`，會將 `memory` 視為顯示記憶體語境，避免誤抓系統 RAM。

這個設計的好處：

- 不佔 VRAM，4GB VRAM 可留給生成模型。
- 不需要下載或維護額外 embedding 模型。
- deterministic，同一個 query 每次結果一致，方便 debug 與 benchmark。
- 純 Python，符合不使用 LangChain/LlamaIndex 的限制。
- 對 key-value 規格表很有效，尤其適合型號、欄位、數字與單位的精準命中。

為什麼不預設使用 semantic embedding model？因為這題的主要風險不是「語意相似找不到」，而是「規格欄位混淆」：

```text
問 BYH，卻抓到 BXH
問 VRAM，卻回答 175W
問亮度，卻回答對比度
```

對這類錯誤，可解釋的 structured retrieval 比黑箱 semantic embedding 更容易控制。若未來資料擴充成大量客服文章、使用手冊或非結構化 FAQ，仍可用 `--embedding-model-path` 切換到 llama.cpp embedding GGUF；但在目前產品規格 QA 範圍內，CPU hashing retrieval 已經達到：

```text
field_recall_at_k = 1.0
model_recall_at_k = 1.0
fact_recall_at_k  = 1.0
mrr               = 1.0
```

## Layout

```text
data/                         官方規格表的結構化 JSON
src/aorus_rag/                純 Python RAG 實作
tests/                        無 LLM 依賴的核心測試
benchmark-results/            TTFT/TPS 與品質評測結果
docs/                         架構與評測說明
scripts/                      Windows CUDA wheel 安裝輔助腳本
```

## Notes

- 官方頁面註明規格會依國家地區出貨而有所變動，本系統回答以 `data/aorus_master_16_am6h_specs.json` 保存版本為準。
- 若問題沒有足夠 context，prompt 會要求模型回答「規格表未提供」，避免自由編造。
- Hashing embedding 是為資源受限環境設計；若要更強語意召回，可指定 llama.cpp embedding GGUF，但建議放 CPU 執行。
