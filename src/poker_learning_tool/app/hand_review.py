"""局末分街點評資料結構。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

StreetId = Literal["preflop", "flop", "turn", "river"]


@dataclass
class ReviewSection:
    street: StreetId
    title: str
    content: str


@dataclass
class HandReview:
    sections: list[ReviewSection]

    def to_display_text(self) -> str:
        """拼接為純文字（相容舊 analysis 欄位）。"""
        parts: list[str] = []
        for sec in self.sections:
            parts.append(f"【{sec.title}】\n{sec.content}")
        return "\n\n".join(parts)
