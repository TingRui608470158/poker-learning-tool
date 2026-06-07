# GTO 翻前 Chart 生成

本目錄用於**離線**產生 HU 翻前 GTO 參考表，輸出至：

`src/poker_learning_tool/strategy/charts/`

App 執行時只讀 JSON，不會即時跑 solver。

## 快速生成（近似 range，開箱即用）

```powershell
cd poker_learning_tool
uv run python scripts/gto-charts/chart_builder.py
```

## 嘗試 openCFR + 近似表（方案 C）

```powershell
uv sync --extra gto
.\scripts\gto-charts\run_all.ps1
```

若未安裝 openCFR，腳本會自動 fallback 為 `chart_builder` 近似表。

## 關於 TexasSolver

[TexasSolver](https://github.com/bupticybee/TexasSolver/issues/177) **不支援翻前求解**（僅翻後）。翻前 chart 使用 openCFR（可選）或內建近似 range。

## 輸出檔名規則

```
hu_{深度}bb_{位置}_{場景}.json
```

範例：`hu_25bb_btn_rfi.json`、`hu_25bb_bb_bb_vs_btn_open.json`

深度：10 / 25 / 40 / 100 bb。
