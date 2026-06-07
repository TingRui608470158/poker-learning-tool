# Poker Learning Tool

德州撲克學習工具專案。本機已架設 **Ollama 本地 LLM 服務**，可用於 AI 輔助分析、問答與策略討論。

## 專案結構

```
poker_learning_tool/
├── src/poker_learning_tool/   # Python 套件
│   ├── perspective/           # ① 高手思維（含 xiao_liu 小六）
│   ├── env/                   # ② 德州撲克環境（PokerTable、HoldemSession）
│   ├── app/                   # ③ 整合應用（LearningSession、UI）
│   ├── api/                   # ④ FastAPI（React 前端用）
│   └── common/                # 共用工具
├── main.py                    # Streamlit 入口（fallback）
├── api_main.py                # FastAPI 入口
├── run_dev.ps1                # 一鍵啟動 API + React
├── frontend/                  # React 可視化界面
├── doc/
├── scripts/xiao-liu-youtube/
├── .agents/skills/
└── readme.md
```

### 三模組分工

| 模組 | 職責 |
|------|------|
| `perspective` | 高手思維教練（`XiaoLiuSkill` 等） |
| `env` | 牌局環境（`PokerTable`、`HoldemSession`） |
| `app` | 串接 env + perspective（`LearningSession`、可視化 UI） |

## 可視化學習界面

### React + FastAPI（推薦）

橢圓真實牌桌、**2～9 人桌**、翻前位置術語（UTG / BTN / SB / BB 等 + 繁中）、SVG 撲克牌、步進學習 + **三種學習模式**（完整學習 / 翻前策略 / 職業點評）+ **HU GTO 翻前表與 EV**。Hero 固定於畫面下方，其餘座位均為 RL 對手。

**前提**：Ollama 需在運行（局末點評用）。

```powershell
# 一鍵啟動 API (8000) + 前端 (5173)
.\run_dev.ps1

# 或分開啟動（PowerShell）：
uv run uvicorn api_main:app --reload --port 8000
cd frontend; npm install; npm run dev
```

建議使用 **64 位 Node.js**（`node -p process.arch` 應顯示 `x64`）。若目前是 `ia32`，可到 [nodejs.org](https://nodejs.org/) 安裝 64 位版本。

前端已改用 **Tailwind v3 + PostCSS** 與 **Rollup WASM**，避免 Windows 原生模組（`lightningcss` / `@rollup/*`）缺失問題。若仍報錯，請重裝依賴：

```powershell
cd frontend
Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
Remove-Item -Force package-lock.json -ErrorAction SilentlyContinue
npm install
npm run dev
```

瀏覽器打開 http://127.0.0.1:5173

### 學習模式

| 模式 | 說明 |
|------|------|
| **完整學習**（預設） | 翻前顯示 GTO 表 + EV；右側可切換「GTO 翻前／專家點評」；局末可取得小六點評 |
| **翻前策略** | 鎖 2 人桌 + 固定深度（10/25/40/100bb）；右側僅 GTO 13×13 表；不提供局末點評 |
| **職業點評** | 專心實戰；右側僅小六點評；不顯示 GTO |

GTO 翻前表目前僅 **2 人桌（HU）**；深度會自動對齊最近標準檔（10/25/40/100bb）。下注尺寸與 solver 不同，頻率與 EV 僅供參考。

重新生成 chart：`scripts/gto-charts/README.md`（使用 openCFR 或近似 range；TexasSolver 不支援翻前）。

界面操作：
1. 側欄選 **學習模式** 與 **打牌人數（2～9，預設 2 人桌）**；翻前策略模式固定 2 人桌與練習深度
2. 牌桌顯示各座位翻前位置（例：UTG 槍口、BTN 按鈕位）與 Dealer 按鈕
3. **對手自動出牌**，輪到你時選 action；翻前可見 **EV 與 GTO%**（非職業點評模式）
4. 局結束後按 **取得小六點評**（完整學習／職業點評；分 **翻前／翻牌／轉牌／河牌** 四段）
5. 可「再玩一局」或「套用並新一局」開始新局

建立牌局 API（`POST /api/sessions`）：

```json
{
  "num_players": 2,
  "hero_seat": 0,
  "learning_mode": "full",
  "gto_stack_bb": 25
}
```

`learning_mode`：`full` | `preflop_gto` | `coach_review`

每局會自動隨機**發牌**，且**各座位獨立 1～100bb** 起始深度（盲注 1/2）；**每一手都重新分配，不累積上一手結餘**。無需指定 `seed` 或 `chips`。回應 `view.seats[].starting_bb` 為該座位本局起始 bb 數。

回應 `view.seats[]` 含 `position_en`、`position_zh`、`is_dealer`、`stack_remaining` 等欄位。

API 文件：http://127.0.0.1:8000/docs

### Streamlit（舊版 fallback）

```powershell
uv sync
uv run streamlit run main.py
```

DQN 模型可放在 `models/dqn_agent_player_1.pth`（或從 `fun_learning_poker/experiments/` 複製）。

## 步進學習（LearningSession）

```python
from poker_learning_tool import LearningSession, XiaoLiuSkill

session = LearningSession(
    coach=XiaoLiuSkill(),
    num_players=2,
    hero_seat=0,
)
session.start_hand()
# 進行中只記錄行動；局結束後：
review = session.request_hand_review()  # 分街點評 HandReview
print(review.sections[0].content)
session.click_next()  # RL 走一步，或進入 Hero 選 action
```

## 環境安裝（uv）

本專案使用 [uv](https://docs.astral.sh/uv/) 管理 Python 環境與依賴。

```powershell
# 初次或 pyproject.toml 變更後
uv sync

# 可選：Whisper 字幕轉寫依賴
uv sync --extra whisper
```

## 整合使用（CoachSession）

```python
from poker_learning_tool import CoachSession, HoldemSession, XiaoLiuSkill

session = CoachSession(coach=XiaoLiuSkill(), table=HoldemSession())
session.start_hand()
print(session.get_advice())  # 需 Ollama 運行
```

## 高手思維模組（perspective / 小六）

載入 `.agents/skills/xiao-liu-perspective/SKILL.md` 作為 system prompt，透過本機 Ollama 回答撲克問題。

**前提**：Ollama 需在運行（預設模型 `deepseek-r1:8b`）。

```python
from poker_learning_tool import XiaoLiuSkill

xiaoliu = XiaoLiuSkill()
answer = xiaoliu.ask("BTN 15BB，AJo，UTG open 2.5x，我該怎麼打？")
print(answer)
```

多輪對話：

```python
history = [{"role": "user", "content": "什麼情況要 fold？"}]
reply = xiaoliu.chat(history)
history.append({"role": "assistant", "content": reply})
history.append({"role": "user", "content": "給我一個 MTT 泡沫期的例子"})
print(xiaoliu.chat(history))
```

用 uv 執行腳本時：

```powershell
uv run python your_script.py
```

## 小六 YouTube 字幕下载

批量下载 [@SixPoker666](https://www.youtube.com/@SixPoker666) 公开字幕，供 `xiao-liu-perspective` Skill 使用。

**详细说明（已做过的事、cookies、故障排除）：** [scripts/xiao-liu-youtube/README.md](scripts/xiao-liu-youtube/README.md)

## 本機 LLM 快速開始

| 項目 | 值 |
|------|-----|
| 服務 | Ollama 0.24.0 |
| 位址 | `http://127.0.0.1:11434` |
| 模型 | `deepseek-r1:8b`（約 8.2B 參數，Q4_K_M） |
| GPU | NVIDIA GeForce RTX 4070 Ti SUPER（16 GB VRAM） |
| API Key | 不需要（本機服務） |

### 1. 確認服務是否運行

**PowerShell：**

```powershell
curl http://127.0.0.1:11434/api/tags
```

**命令列對話（最簡單）：**

```powershell
ollama run deepseek-r1:8b
```

### 2. 發送一則問題

```powershell
curl http://127.0.0.1:11434/api/generate -d "{\"model\":\"deepseek-r1:8b\",\"prompt\":\"什麼是德州撲克？\",\"stream\":false}"
```

### 3. 詳細文件

- [LLM 使用說明](doc/llm-guide.md) — 安裝、啟動、模型管理、WSL 存取
- [LLM API 調用文件](doc/llm-api.md) — 完整 API 端點與程式範例

## WSL 存取方式

WSL Ubuntu 可透過 Windows 主機位址存取同一個 Ollama 服務：

```bash
curl http://127.0.0.1:11434/api/tags
```

若 `127.0.0.1` 無法連線，可改用：

```bash
curl http://$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):11434/api/tags
```

## 相關指令速查

| 操作 | 指令 |
|------|------|
| 查看已安裝模型 | `ollama list` |
| 下載新模型 | `ollama pull <模型名稱>` |
| 刪除模型 | `ollama rm <模型名稱>` |
| 查看版本 | `ollama --version` |
| 停止 Ollama | 工作列圖示 → Quit Ollama |
