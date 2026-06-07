# Deprecate legacy UI before legacy engine

Status: accepted

在 ADR-0001（single core stack）之下，舊路徑的移除順序為 **UI 先行**：先刪 Streamlit 入口與 `run_learning_ui`，再移除 `HoldemSession` / `CoachSession` / `GameView`。

Fallback UI 與 Primary UI 功能不對等，維護兩套入口的混淆大於保留 Streamlit 的價值。引擎程式可暫留一個 slice，讓 `test_env.py` / `test_app.py` 有時間遷移或刪除，避免同時動 UI 與引擎測試。

**Slice 1（UI）：** `main.py`、`app/ui/streamlit_app.py`、`run_learning_ui` export、readme Streamlit 章節。  
**Slice 2（引擎）：** `HoldemSession`、`CoachSession`、`GameView`、相關 export；刪除 `tests/test_app.py`；`tests/test_env.py` 僅保留 label/path 等工具測試，移除 HoldemSession 整合段。
