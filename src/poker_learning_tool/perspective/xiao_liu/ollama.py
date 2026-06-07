"""本機 Ollama chat API 客戶端（stdlib only）。"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any

DEFAULT_BASE_URL = "http://127.0.0.1:11434/v1/chat/completions"
DEFAULT_MODEL = "deepseek-r1:8b"

_THINK_OPEN = "<" + "think" + ">"
_THINK_CLOSE = "</" + "think" + ">"
_THINKING_RE = re.compile(
    re.escape(_THINK_OPEN) + r".*?" + re.escape(_THINK_CLOSE) + r"\s*",
    re.DOTALL | re.IGNORECASE,
)


def strip_thinking(content: str) -> str:
    """移除 deepseek-r1 等模型的 think 區塊。"""
    return _THINKING_RE.sub("", content).strip()


def chat_completion(
    messages: list[dict[str, str]],
    *,
    base_url: str = DEFAULT_BASE_URL,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    timeout: int = 120,
    max_tokens: int | None = None,
    think: bool | None = None,
    allow_reasoning_fallback: bool = True,
) -> str:
    """呼叫 Ollama OpenAI 相容 chat API，回傳 assistant 文字。"""
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if think is not None:
        payload["think"] = think
    req = urllib.request.Request(
        base_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Ollama 不可用 ({base_url}): {exc}") from exc

    message = data["choices"][0]["message"]
    if not isinstance(message, dict):
        raise RuntimeError(f"Ollama 回應格式異常: {data!r}")
    text = message.get("content", "")
    reasoning = message.get("reasoning", "")
    if not isinstance(text, str):
        text = ""
    if not isinstance(reasoning, str):
        reasoning = ""

    result = strip_thinking(text)
    if not result.strip() and reasoning.strip() and allow_reasoning_fallback:
        result = strip_thinking(reasoning)
    if not result.strip():
        raise RuntimeError(
            "Ollama 回傳空內容。若使用 deepseek-r1，請確認模型正常或改用 qwen2.5 等模型。"
        )
    return result
