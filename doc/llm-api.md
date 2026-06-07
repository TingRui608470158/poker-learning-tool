# LLM API 調用文件

本文件說明如何透過 HTTP API 調用本機 Ollama 服務。

---

## 基本資訊

| 項目 | 值 |
|------|-----|
| Base URL（原生 API） | `http://127.0.0.1:11434` |
| Base URL（OpenAI 相容） | `http://127.0.0.1:11434/v1` |
| 預設模型 | `deepseek-r1:8b` |
| 認證 | 不需要（本機服務） |
| Content-Type | `application/json` |

---

## API 端點一覽

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/tags` | 列出已安裝模型 |
| GET | `/api/version` | 查看 Ollama 版本 |
| POST | `/api/generate` | 文字生成（Ollama 原生） |
| POST | `/api/chat` | 多輪對話（Ollama 原生） |
| POST | `/v1/chat/completions` | 多輪對話（OpenAI 相容） |
| POST | `/v1/completions` | 文字補全（OpenAI 相容） |
| GET | `/v1/models` | 列出模型（OpenAI 相容） |
| POST | `/api/pull` | 下載模型 |
| POST | `/api/show` | 查看模型資訊 |

---

## 1. 列出模型

### 請求

```http
GET http://127.0.0.1:11434/api/tags
```

### PowerShell

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags"
```

### curl

```bash
curl http://127.0.0.1:11434/api/tags
```

### 回應範例

```json
{
  "models": [
    {
      "name": "deepseek-r1:8b",
      "model": "deepseek-r1:8b",
      "modified_at": "2026-05-24T20:44:48.530452+08:00",
      "size": 5225376047,
      "details": {
        "family": "qwen3",
        "parameter_size": "8.2B",
        "quantization_level": "Q4_K_M"
      }
    }
  ]
}
```

---

## 2. 文字生成 — `/api/generate`

適合單次問答，不需對話歷史。

### 請求參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `model` | string | 是 | 模型名稱，如 `deepseek-r1:8b` |
| `prompt` | string | 是 | 輸入提示 |
| `stream` | boolean | 否 | 是否串流回應，預設 `true` |
| `options` | object | 否 | 生成參數（見下方） |

**options 常用參數：**

| 參數 | 說明 | 預設 |
|------|------|------|
| `temperature` | 隨機度，0=確定，1=創意 | 0.8 |
| `num_predict` | 最大生成 token 數 | 128 |
| `top_p` | 核採樣 | 0.9 |
| `top_k` | Top-K 採樣 | 40 |

### curl 範例

```bash
curl http://127.0.0.1:11434/api/generate -d '{
  "model": "deepseek-r1:8b",
  "prompt": "用一句話解釋 pot odds",
  "stream": false,
  "options": {
    "temperature": 0.7,
    "num_predict": 256
  }
}'
```

### PowerShell 範例

```powershell
$body = @{
  model  = "deepseek-r1:8b"
  prompt = "用一句話解釋 pot odds"
  stream = $false
  options = @{
    temperature  = 0.7
    num_predict  = 256
  }
} | ConvertTo-Json -Depth 3

$result = Invoke-RestMethod `
  -Uri "http://127.0.0.1:11434/api/generate" `
  -Method Post `
  -Body $body `
  -ContentType "application/json"

$result.response
```

### 回應範例

```json
{
  "model": "deepseek-r1:8b",
  "created_at": "2026-05-24T12:00:00.000000Z",
  "response": "Pot odds 是底池大小與你需要跟注金額的比例，用來判斷跟注是否有正期望值。",
  "done": true,
  "total_duration": 3500000000,
  "load_duration": 1200000000,
  "prompt_eval_count": 12,
  "eval_count": 45
}
```

---

## 3. 多輪對話 — `/api/chat`

適合有 system / user / assistant 角色的對話。

### 請求參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `model` | string | 是 | 模型名稱 |
| `messages` | array | 是 | 訊息陣列 |
| `stream` | boolean | 否 | 是否串流 |
| `options` | object | 否 | 同 generate |

**messages 格式：**

```json
[
  { "role": "system", "content": "你是一位德州撲克教練，用繁體中文回答。" },
  { "role": "user", "content": "什麼是 3-bet？" }
]
```

### curl 範例

```bash
curl http://127.0.0.1:11434/api/chat -d '{
  "model": "deepseek-r1:8b",
  "messages": [
    {
      "role": "system",
      "content": "你是一位德州撲克教練，用繁體中文簡潔回答。"
    },
    {
      "role": "user",
      "content": "在 CO 位置拿 AJ suited，面對 UTG open，我應該 3-bet 還是 call？"
    }
  ],
  "stream": false
}'
```

### 回應範例

```json
{
  "model": "deepseek-r1:8b",
  "created_at": "2026-05-24T12:00:00.000000Z",
  "message": {
    "role": "assistant",
    "content": "AJ suited 在 CO 對 UTG open 通常偏向 call 而非 3-bet..."
  },
  "done": true
}
```

---

## 4. OpenAI 相容 API — `/v1/chat/completions`

適合已有 OpenAI SDK 的程式，只需更換 Base URL。

### curl 範例

```bash
curl http://127.0.0.1:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-r1:8b",
    "messages": [
      {"role": "user", "content": "Explain fold equity"}
    ],
    "temperature": 0.7,
    "max_tokens": 512
  }'
```

### 回應範例

```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1779627000,
  "model": "deepseek-r1:8b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Fold equity refers to..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 85,
    "total_tokens": 97
  }
}
```

---

## 5. 串流回應（Streaming）

設定 `"stream": true` 時，回應以 **NDJSON**（每行一個 JSON）逐段返回。

### curl 串流範例

```bash
curl http://127.0.0.1:11434/api/generate -d '{
  "model": "deepseek-r1:8b",
  "prompt": "列出五個撲克位置名稱",
  "stream": true
}'
```

每行 JSON 的 `response` 欄位為增量文字，最後一行 `"done": true`。

### Python 串流範例

```python
import json
import requests

url = "http://127.0.0.1:11434/api/generate"
payload = {
    "model": "deepseek-r1:8b",
    "prompt": "列出五個撲克位置名稱",
    "stream": True,
}

with requests.post(url, json=payload, stream=True) as resp:
    resp.raise_for_status()
    for line in resp.iter_lines():
        if line:
            chunk = json.loads(line)
            print(chunk.get("response", ""), end="", flush=True)
            if chunk.get("done"):
                print()
```

---

## 程式語言範例

### Python — requests（無需額外套件）

```python
import requests

def ask_llm(prompt: str, model: str = "deepseek-r1:8b") -> str:
    resp = requests.post(
        "http://127.0.0.1:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["response"]

if __name__ == "__main__":
    answer = ask_llm("什麼是 range 在撲克中的意思？")
    print(answer)
```

### Python — OpenAI SDK

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:11434/v1",
    api_key="ollama",  # 本機 Ollama 不驗證，任意字串即可
)

response = client.chat.completions.create(
    model="deepseek-r1:8b",
    messages=[
        {"role": "system", "content": "你是德州撲克教練。"},
        {"role": "user", "content": "解釋 implied odds"},
    ],
    temperature=0.7,
    max_tokens=512,
)

print(response.choices[0].message.content)
```

安裝：

```bash
pip install openai
```

### Node.js — fetch（Node 18+）

```javascript
async function askLLM(prompt) {
  const resp = await fetch("http://127.0.0.1:11434/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "deepseek-r1:8b",
      prompt,
      stream: false,
    }),
  });

  const data = await resp.json();
  return data.response;
}

askLLM("What is a continuation bet?").then(console.log);
```

### Node.js — OpenAI SDK

```javascript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "http://127.0.0.1:11434/v1",
  apiKey: "ollama",
});

const completion = await client.chat.completions.create({
  model: "deepseek-r1:8b",
  messages: [{ role: "user", content: "Explain pot odds" }],
});

console.log(completion.choices[0].message.content);
```

---

## 錯誤處理

### 常見 HTTP 狀態碼

| 狀態碼 | 原因 | 解法 |
|--------|------|------|
| 連線失敗 | Ollama 未啟動 | 開啟 Ollama 應用 |
| 404 | 模型不存在 | `ollama pull <model>` 下載 |
| 500 | GPU/記憶體不足 | 重啟 Ollama，關閉其他 GPU 程式 |

### 錯誤回應範例

```json
{
  "error": "model 'xxx' not found"
}
```

---

## 在 Cursor / VS Code 中使用

若擴充功能或 Agent 支援自訂 OpenAI 端點：

```
Provider: OpenAI Compatible
Base URL: http://127.0.0.1:11434/v1
API Key:  ollama
Model:    deepseek-r1:8b
```

---

## 在 Docker / WSL 容器中使用

容器內需使用 Windows 主機位址，而非 `127.0.0.1`：

| 環境 | Base URL |
|------|----------|
| WSL Ubuntu | `http://127.0.0.1:11434/v1`（通常可用） |
| Docker Desktop | `http://host.docker.internal:11434/v1` |
| WSL 若 127.0.0.1 不通 | `http://<Windows主機IP>:11434/v1` |

---

## 撲克專案整合範例

以下為在本專案中封裝 LLM 呼叫的建議模式：

```python
# llm_client.py（建議用法）
import os
import requests

OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:8b")

def poker_coach_chat(user_message: str, history: list | None = None) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "你是德州撲克教練。用繁體中文回答。"
                "若資訊不足，先列出需要的手牌資訊再分析。"
            ),
        },
    ]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    resp = requests.post(
        f"{OLLAMA_BASE}/api/chat",
        json={"model": DEFAULT_MODEL, "messages": messages, "stream": False},
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]
```

**.env 設定：**

```env
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=deepseek-r1:8b
```

---

## 相關文件

- [LLM 使用說明](llm-guide.md)
- [Ollama 官方 API 文件](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [OpenAI 相容 API 說明](https://github.com/ollama/ollama/blob/main/docs/openai.md)
