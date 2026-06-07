# Single core stack (LearningSession + PokerTable)

Status: accepted

專案曾並存兩條應用路徑：現行的 `LearningSession` / `PokerTable` / React+FastAPI，以及舊版的 `CoachSession` / `HoldemSession` / Streamlit。我們決定以 **core stack** 為唯一長期架構，舊路徑標記 deprecated 並分階段移除。

Primary UI 已承載 learning mode、GTO 翻前參考與分街 hand review；舊路徑功能重疊但較少，維持雙軌會讓 `TableView`/`GameView` 與 public API 持續分叉。收斂後 refactor 與測試只需對齊一條 seam。

**Considered options:** (B) 長期雙軌並抽共用層 —  rejected，複雜度永久加倍；(A) 單一 core — accepted。

**Consequences:** `HoldemSession`、`CoachSession`、`GameView`、Streamlit 入口不再接受新功能；`__init__.py` 公開 export 將逐步縮減並以 deprecation 過渡。
