# Poker Learning Tool

德州撲克步進式學習工具：玩家在牌桌上實戰，可對照 GTO 翻前參考，並在局末取得高手思維教練的分街點評。

## Language

### 學習流程

**Learning session**:
一次從開局到可再次開局的完整學習運行；由 `LearningSession` 編排，包含步進打牌、模式設定與局末點評請求。
_Avoid_: Session（單獨使用時易與 API 或舊版引擎混淆）、Game session

**Learning mode**:
決定 UI 與輔助資訊露出方式的三種模式：`full`（完整學習）、`preflop_gto`（翻前策略）、`coach_review`（職業點評）。
_Avoid_: 模式、Mode（不帶 learning 前綴時）

**Phase**:
Learning session 在單局內的互動階段：`awaiting_next`（等待步進）、`awaiting_human_action`（輪到 Hero 行動）、`hand_over`（本局結束）。
_Avoid_: State、Status

**Step-through play**:
玩家與對手依序行動、一次推進一個 action 的學習方式；非即時全自動發牌至結束。
_Avoid_: 步進模式（作為泛稱時）、Auto-play

### 牌局與座位

**Hand**:
從發牌到該局結束（攤牌或 fold 出結果）的一完整局；每局重新發牌、重新分配各座位起始深度。
_Avoid_: Round（易與下注圈混淆）、Game

**Street**:
一手牌內的四個下注階段：`preflop`、`flop`、`turn`、`river`。
_Avoid_: Stage（程式內 `stage` 為 UI 標籤，domain 層用 street）

**Hero**:
由人類玩家操控的座位；畫面固定於牌桌下方。
_Avoid_: 玩家、User、Human player

**Seat**:
牌桌上的單一座位編號（0 起算）；含位置、籌碼、手牌與玩家種類。
_Avoid_: Player（易與 Hero 或對手概念混淆）

**Opponent**:
Hero 以外、由程式自動行動的座位（目前均為 RL 對手）。
_Avoid_: AI player、Bot

**Stack depth**:
某座位以 big blind 為單位的有效籌碼深度（bb）；每局各座位獨立隨機 1～100bb，不累積上一局。
_Avoid_: Chips、Stack（不帶 depth 時）

**Position**:
翻前座位角色（如 UTG、BTN、SB、BB）；對外同時提供英文縮寫與繁中標籤。
_Avoid_: Seat label、Role

### 牌桌引擎

**Core stack**:
重構後的唯一目標架構：`LearningSession` → `PokerTable` → `TableView`，由 Primary UI（React + FastAPI）驅動。
_Avoid_: Main path、New stack

**PokerTable**:
Core stack 的牌局引擎；支援 2～9 人、Human/RL 座位可配置。
_Avoid_: Table、Game engine

**HoldemSession**:
已棄用中的舊版 2 人牌局引擎；**Slice 2** 自 core stack 移除，不再新增功能。
_Avoid_: Session（單獨使用）、Legacy table

**TableView**:
牌桌在某一時刻的可讀快照（底池、公牌、各 seat、合法 action 等）；PokerTable 的對外視圖。
_Avoid_: GameView（屬 HoldemSession 舊視圖）、Snapshot

**Step record**:
單次 action 步進的紀錄（誰、做了什麼、對應 log 行）。
_Avoid_: Event、Move

### 教練與點評

**Coach perspective**:
可注入應用層的高手思維教練協定；目前實作為小六（`XiaoLiuSkill`）。
_Avoid_: Coach、LLM、Perspective module

**Hand review**:
一局結束後，教練依四個 street 產出的結構化點評（`HandReview` + 各 `ReviewSection`）。
_Avoid_: Analysis、Feedback、Commentary

**Hand record**:
單局行動軌跡的累積紀錄（`HandEvent` 序列），供生成 hand review 的 prompt。
_Avoid_: Action log、History

**Spot advice**:
決策當下、針對特定局面的一次性教練問答（舊版 `ask_spot` 路徑）。
_Avoid_: Real-time coaching

### GTO 翻前參考

**Strategy reference**:
GTO 等參考資料的獨立模組（`strategy`）；負責 preflop spot 辨識、chart 載入與 lookup，不混入牌桌規則（`env`）或學習編排（`app`）。
_Avoid_: GTO module、Strategy layer、Solver

**Preflop spot**:
從當前牌桌快照辨識出的翻前局面（Hero 位置、場景如 open/facing raise、有效深度、對齊後的 chart 深度）。
_Avoid_: Situation、Scenario（domain 層用 spot）

**Preflop strategy**:
某 preflop spot 對應的完整 GTO 翻前參考（13×13 矩陣、Hero 手牌 cell、各 action 的 EV 與 GTO%）。
_Avoid_: GTO table、Chart data、Strategy object

**Chart depth**:
GTO 資料檔所對應的標準深度（10 / 25 / 40 / 100bb）；實際 stack depth 會 snap 到最近標準檔。
_Avoid_: Stack size、Effective stack

**HU**:
Heads-up，兩人桌；目前 GTO 翻前表僅支援 HU。
_Avoid_: 2-max、Two-handed

### API 與介面

**Server session**:
API 層以 `session_id` 索引的伺服器端 Learning session 實例（記憶體 `SessionStore`）。
_Avoid_: Session（單獨使用）、Client session

**Primary UI**:
React + FastAPI 可視化學習介面（推薦路徑）。
_Avoid_: 新版 UI、Web app

**Fallback UI**:
已棄用中的 Streamlit 入口；**Slice 1** 移除，不再作為正式學習介面。
_Avoid_: 舊版、Legacy UI、Streamlit app

**CoachSession**:
已棄用中的舊版整合層（HoldemSession + coach）；**Slice 2** 移除。
_Avoid_: Learning session（兩者不同）
