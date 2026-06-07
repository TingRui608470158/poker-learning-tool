"""局末點評：prompt 與字數精簡。"""

from __future__ import annotations

import re
from typing import Callable, Literal

StreetId = Literal["preflop", "flop", "turn", "river"]

MAX_SECTION_CHARS = 200
MAX_REVIEW_CHARS = 500
SUMMARIZE_MAX_RETRIES = 3

STREET_TITLES: dict[StreetId, str] = {
    "preflop": "翻前",
    "flop": "翻牌",
    "turn": "轉牌",
    "river": "河牌",
}

STREET_ORDER: tuple[StreetId, ...] = ("preflop", "flop", "turn", "river")

HAND_REVIEW_SYSTEM = """你是台湾职业扑克选手「小六」，正在帮学员复盘德州扑克。
规则：
- 只用繁体中文，口语教学口吻
- 根据行动序列点评 Hero 的关键决策、范围思维与可改进处
- 可提及位置、底池、SPR、对手行动线
- 输出格式：用「1.」「2.」条列，每条一句，不要长段落
- 直接输出教学点评，不要复述题目或规则"""

STREET_REVIEW_HINTS: dict[StreetId, str] = {
    "preflop": "只点评翻牌前（Preflop）Hero 的 open/3bet/跟注/弃牌与 range 思维。",
    "flop": "只点评翻牌圈（Flop）Hero 的 c-bet、check、raise 与公共牌面解读。",
    "turn": "只点评转牌圈（Turn）Hero 的决策与牌力演变。",
    "river": "只点评河牌圈（River）Hero 的 value/bluff 选择与摊牌结果。",
}


def summarize_system(max_chars: int) -> str:
    return f"""你是文字编辑。将下列扑克教学点评精简为繁体中文。
规则：
- 总字数不超过{max_chars}字（含标点）
- 保留小六口语教学风格与最关键的建议
- 维持「1.」「2.」条列格式，每条一句
- 直接输出精简后的点评正文
- 禁止复述用户要求、规则说明或内心独白（如「首先」「用户要求」）"""


def summarize_user_message(draft: str, *, max_chars: int, retry: bool) -> str:
    prefix = f"请将以下点评精简为{max_chars}字以内的繁体中文教学结论"
    if retry:
        prefix += f"（上次仍超过{max_chars}字，请再缩短，保留最重要 2～3 条）"
    return prefix + "：\n\n" + draft


def normalize_text(text: str) -> str:
    """去除首尾空白，保留换行。"""
    lines = [line.strip() for line in text.strip().splitlines()]
    return "\n".join(line for line in lines if line)


def trim_to_boundary(text: str, max_chars: int) -> str:
    """在句號或換行邊界截斷，避免切半句。"""
    normalized = normalize_text(text)
    if len(normalized) <= max_chars:
        return normalized
    suffix = "\n（內容已壓縮）"
    budget = max(max_chars - len(suffix), max_chars // 2)
    chunk = normalized[:budget]
    for sep in ("。", "！", "？", "\n", "；", ".", " "):
        idx = chunk.rfind(sep)
        if idx > budget // 3:
            trimmed = chunk[: idx + 1].rstrip() + suffix
            return trimmed if len(trimmed) <= max_chars else trimmed[:max_chars]
    trimmed = chunk.rstrip() + "…" + suffix
    return trimmed if len(trimmed) <= max_chars else trimmed[:max_chars]


def limit_review_length(text: str, max_chars: int = MAX_REVIEW_CHARS) -> str:
    """Fallback：邊界 trim（非無腦硬切）。"""
    return trim_to_boundary(text, max_chars)


def summarize_to_limit(
    draft: str,
    *,
    max_chars: int,
    chat_fn: Callable[[list[dict[str, str]]], str],
) -> str:
    """LLM 精簡並重試，最後才邊界 trim。"""
    text = normalize_text(draft)
    if len(text) <= max_chars:
        return text
    for attempt in range(SUMMARIZE_MAX_RETRIES):
        messages = [
            {"role": "system", "content": summarize_system(max_chars)},
            {
                "role": "user",
                "content": summarize_user_message(
                    text, max_chars=max_chars, retry=attempt > 0
                ),
            },
        ]
        text = normalize_text(chat_fn(messages))
        if len(text) <= max_chars:
            return text
    return trim_to_boundary(text, max_chars)
