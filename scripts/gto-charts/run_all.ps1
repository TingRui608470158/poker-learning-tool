# 重新生成 HU 翻前 GTO chart JSON
Set-Location $PSScriptRoot\..\..
uv run python scripts/gto-charts/generate_hu_preflop.py
