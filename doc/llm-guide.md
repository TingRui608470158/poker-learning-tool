# LLM 使用說明

本文件說明如何在本機使用已架設的 **Ollama + DeepSeek-R1 8B** 語言模型服務。

---

## 一、環境概覽

| 項目 | 說明 |
|------|------|
| 推理引擎 | [Ollama](https://ollama.com/) 0.24.0 |
| 服務位址 | `http://127.0.0.1:11434` |
| 預設模型 | `deepseek-r1:8b` |
| 模型大小 | 約 5.2 GB（磁碟） |
| 量化等級 | Q4_K_M |
| 預設上下文 | 4096 tokens（依 VRAM 自動設定） |
| 顯示卡 | NVIDIA GeForce RTX 4070 Ti SUPER（CUDA） |
| 模型存放 | `C:\Users\s9200\.ollama\models` |
| 是否需要 API Key | 否（僅本機存取） |

> **DeepSeek-R1** 是具備推理（thinking）能力的模型，回答前會先進行內部思考，適合策略分析與邏輯推理類問題。

---

## 二、啟動與停止

### 啟動

Ollama 安裝後通常會隨 Windows 開機自動啟動。若未運行：

1. 在開始選單搜尋 **Ollama** 並開啟
2. 或在 PowerShell 執行：

```powershell
& "C:\Users\s9200\AppData\Local\Programs\Ollama\ollama.exe" serve
```

### 確認是否運行

```powershell
# 方法 1：查看模型列表
ollama list

# 方法 2：API 健康檢查
curl http://127.0.0.1:11434/api/version
```

正常回應範例：

```json
{"version":"0.24.0"}
```

### 停止

- 工作列（系統匣）找到 Ollama 圖示 → 右鍵 → **Quit Ollama**
- 或在 PowerShell：

```powershell
Stop-Process -Name ollama -Force -ErrorAction SilentlyContinue
```

---

## 三、基本使用方式

### 方式 1：命令列對話（最簡單）

```powershell
ollama run deepseek-r1:8b
```

進入互動模式後直接輸入問題，輸入 `/bye` 離開。

**單次提問（不進入互動模式）：**

```powershell
ollama run deepseek-r1:8b "用三句話解釋德州撲克的基本規則"
```

### 方式 2：PowerShell 呼叫 API

```powershell
$body = @{
  model  = "deepseek-r1:8b"
  prompt = "什麼是 preflop 加注？"
  stream = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/generate" `
  -Method Post -Body $body -ContentType "application/json"
```

回應中的 `response` 欄位即為模型回答。

### 方式 3：WSL Ubuntu 中使用

在 WSL 終端機：

```bash
# 確認連線
curl http://127.0.0.1:11434/api/tags

# 對話
curl http://127.0.0.1:11434/api/generate -d '{
  "model": "deepseek-r1:8b",
  "prompt": "Explain pot odds in poker",
  "stream": false
}'
```

> WSL 與 Windows 共用同一個 Ollama 服務，不需要在 WSL 內重複安裝。

### 方式 4：OpenAI 相容介面

許多 AI 工具（Cursor、LangChain、OpenAI SDK）可設定：

```
Base URL: http://127.0.0.1:11434/v1
API Key:  ollama（任意字串，本機不驗證）
Model:    deepseek-r1:8b
```

詳細 API 參數見 [llm-api.md](llm-api.md)。

---

## 四、模型管理

### 查看已安裝模型

```powershell
ollama list
```

目前環境：

```
NAME              SIZE
deepseek-r1:8b    5.2 GB
```

### 下載新模型

```powershell
# 範例：下載 Llama 3.2
ollama pull llama3.2

# 範例：下載較小的 Qwen 模型
ollama pull qwen2.5:7b
```

### 刪除模型

```powershell
ollama rm deepseek-r1:8b
```

### 查看模型詳細資訊

```powershell
ollama show deepseek-r1:8b
```

---

## 五、在撲克學習場景中的使用建議

### 適合的用途

- 解釋撲克術語（pot odds、equity、range 等）
- 分析手牌情境（需提供完整資訊：位置、底池、公共牌、對手行動）
- 策略思路討論與複習
- 將英文撲克教材翻譯或摘要

### 提問範例

```
我在 BTN 位置，手牌 Ah Kh，翻牌 Qh 7h 2c，底池 100，對手 check。
我應該 cbet 嗎？請分析 equity 與對手 range。
```

### 注意事項

- 模型回答僅供**學習參考**，不代表最優 GTO 策略
- 涉及真實金錢決策時，請以專業工具與教練建議為準
- DeepSeek-R1 會輸出「思考過程」，若只需要最終答案，可在 prompt 中要求「只給結論」

---

## 六、常見問題

### Q1：`curl: connection refused` 或無法連線

**原因：** Ollama 服務未啟動。

**解法：** 開啟 Ollama 應用程式，或執行 `ollama serve`。

---

### Q2：回應很慢或第一次很慢

**原因：** 模型需載入至 GPU VRAM，首次推理約需 10–30 秒。

**解法：** 等待載入完成；Ollama 預設會在 5 分鐘無請求後卸載模型（`OLLAMA_KEEP_ALIVE=5m`）。

---

### Q3：WSL 無法連到 11434

**解法：**

```bash
# 使用 Windows 主機 IP
HOST=$(grep nameserver /etc/resolv.conf | awk '{print $2}')
curl http://$HOST:11434/api/tags
```

---

### Q4：VRAM 不足 / CUDA 錯誤

**原因：** 同時載入過多模型或其他程式占用 GPU。

**解法：**

```powershell
# 查看 GPU 使用狀況
nvidia-smi

# 重啟 Ollama
Stop-Process -Name ollama -Force
# 再重新開啟 Ollama
```

---

### Q5：如何讓其他程式（如 Python 專案）使用

在 `.env` 或程式中設定：

```env
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_MODEL=deepseek-r1:8b
LLM_API_KEY=ollama
```

Python 範例見 [llm-api.md](llm-api.md#python-openai-sdk)。

---

## 七、環境變數（進階）

可在 Windows 系統環境變數或 PowerShell 中設定：

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `OLLAMA_HOST` | `127.0.0.1:11434` | 監聽位址 |
| `OLLAMA_MODELS` | `C:\Users\s9200\.ollama\models` | 模型存放路徑 |
| `OLLAMA_KEEP_ALIVE` | `5m` | 模型在記憶體中保留時間 |
| `OLLAMA_NUM_PARALLEL` | `1` | 同時處理請求數 |

---

## 八、相關連結

- [Ollama 官方文件](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [DeepSeek-R1 模型說明](https://ollama.com/library/deepseek-r1)
- [API 調用文件（本專案）](llm-api.md)
