"""可选：用本机 Ollama 整理 Whisper 转写文本（标点、分段，不增删内容）"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434/v1/chat/completions"
DEFAULT_MODEL = "deepseek-r1:8b"

SYSTEM_PROMPT = """你是文字整理助手。用户会给你一段语音转写的扑克教学 raw 文本。
你的任务 ONLY：
1. 加正确标点（繁体中文为主）
2. 按语义分段（空行分隔段落）
3. 修正 obvious 的同音错字（扑克术语：底池、翻牌、河牌、ICM、range 等）

禁止：
- 添加原文没有的内容
- 总结或改写观点
- 删除句子

只输出整理后的正文，不要解释。"""

_THINK_OPEN = "<" + "think" + ">"
_THINK_CLOSE = "</" + "think" + ">"
_THINKING_RE = re.compile(
    re.escape(_THINK_OPEN) + r".*?" + re.escape(_THINK_CLOSE) + r"\s*",
    re.DOTALL | re.IGNORECASE,
)


def polish_transcript(
    raw_text: str,
    *,
    base_url: str = DEFAULT_OLLAMA_URL,
    model: str = DEFAULT_MODEL,
    timeout: int = 300,
) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": raw_text[:12000]},
        ],
        "temperature": 0.2,
        "stream": False,
    }
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

    content = data["choices"][0]["message"]["content"].strip()
    content = _THINKING_RE.sub("", content).strip()
    return content
