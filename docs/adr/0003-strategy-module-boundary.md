# Keep strategy as an independent module

Status: accepted

GTO 翻前 lookup（spot 辨識、chart 深度對齊、13×13 矩陣、action EV）維持在獨立的 **`strategy` 模組**，由 `LearningSession` 呼叫；不併入 `app`，也不將 spot 辨識下沉至 `env`。

GTO 是參考資料查表，不是牌桌規則。`env` 應只關心撲克機制與 `TableView`；`app` 編排學習流程。分離後更換 chart 來源或擴充 postflop 參考時，不必改動 `PokerTable`。

**Considered options:** (B) 併入 `app` — rejected，耦合學習編排與參考資料；(C) spot 下沉 `env` — rejected，讓引擎層感知 GTO 概念。

**Consequences:** `strategy.lookup.resolve_preflop_strategy` 是 app 對 GTO 的唯一入口；API schema 可繼續 re-export `PreflopStrategy` 型別。
