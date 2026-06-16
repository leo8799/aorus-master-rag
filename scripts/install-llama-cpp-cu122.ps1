param(
    [string]$Version = "0.2.90",
    [string]$WheelIndex = "https://abetlen.github.io/llama-cpp-python/whl/cu122"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$uvCommand = Get-Command uv -ErrorAction SilentlyContinue
if ($uvCommand) {
    $uv = $uvCommand.Source
} else {
    $fallbackUv = Join-Path $projectRoot "..\..\tools\bin\uv.exe"
    if (-not (Test-Path $fallbackUv)) {
        throw "uv was not found on PATH and fallback uv.exe was not found at $fallbackUv"
    }
    $uv = $fallbackUv
}

if (-not $env:UV_CACHE_DIR) {
    $env:UV_CACHE_DIR = Join-Path $projectRoot ".uv-cache"
}

Write-Host "Using uv: $uv"
Write-Host "Using UV_CACHE_DIR: $env:UV_CACHE_DIR"
Write-Host "Syncing dev environment..."
& $uv sync --extra dev

Write-Host "Installing llama-cpp-python $Version from CUDA wheel index:"
Write-Host $WheelIndex
& $uv pip install --force-reinstall --no-cache --extra-index-url $WheelIndex "llama-cpp-python==$Version"

Write-Host "Verifying llama_cpp import..."
& $uv run python -c "import llama_cpp; print(llama_cpp.__version__)"
