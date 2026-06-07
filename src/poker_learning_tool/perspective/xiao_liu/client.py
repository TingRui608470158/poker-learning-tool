"""XiaoLiuSkill — 以小六視角透過 Ollama 回答撲克問題。"""

from __future__ import annotations

from pathlib import Path

from poker_learning_tool.app.hand_review import HandReview, ReviewSection
from poker_learning_tool.perspective.xiao_liu import ollama
from poker_learning_tool.perspective.xiao_liu.analysis import (
    HAND_REVIEW_SYSTEM,
    MAX_SECTION_CHARS,
    STREET_REVIEW_HINTS,
    STREET_TITLES,
    StreetId,
    limit_review_length,
    normalize_text,
    summarize_to_limit,
)
from poker_learning_tool.perspective.xiao_liu.skill import default_skill_path, load_skill_text

ChatMessage = dict[str, str]


class XiaoLiuSkill:
    """載入 SKILL.md 作為 system prompt，透過本機 Ollama 對話。"""

    def __init__(
        self,
        *,
        skill_path: Path | str | None = None,
        model: str = ollama.DEFAULT_MODEL,
        spot_model: str | None = None,
        base_url: str = ollama.DEFAULT_BASE_URL,
        temperature: float = 0.7,
        spot_temperature: float = 0.35,
        timeout: int = 120,
        review_timeout: int = 90,
        review_max_tokens: int = 800,
        summarize_max_tokens: int = 600,
    ) -> None:
        self._skill_path = Path(skill_path) if skill_path else default_skill_path()
        self._system_prompt = load_skill_text(self._skill_path)
        self._model = model
        self._spot_model = spot_model or model
        self._base_url = base_url
        self._temperature = temperature
        self._spot_temperature = spot_temperature
        self._timeout = timeout
        self._review_timeout = review_timeout
        self._review_max_tokens = review_max_tokens
        self._summarize_max_tokens = summarize_max_tokens

    @property
    def system_prompt(self) -> str:
        return self._system_prompt

    @property
    def skill_path(self) -> Path:
        return self._skill_path

    def _with_system(self, messages: list[ChatMessage]) -> list[ChatMessage]:
        return [{"role": "system", "content": self._system_prompt}, *messages]

    def _chat_review(
        self,
        messages: list[ChatMessage],
        *,
        max_tokens: int,
        allow_reasoning_fallback: bool = True,
    ) -> str:
        return ollama.chat_completion(
            messages,
            base_url=self._base_url,
            model=self._spot_model,
            temperature=self._spot_temperature,
            timeout=self._review_timeout,
            max_tokens=max_tokens,
            allow_reasoning_fallback=allow_reasoning_fallback,
        )

    def _summarize_chat(self, messages: list[dict[str, str]]) -> str:
        return ollama.chat_completion(
            messages,
            base_url=self._base_url,
            model=self._spot_model,
            temperature=0.25,
            timeout=self._review_timeout,
            max_tokens=self._summarize_max_tokens,
            allow_reasoning_fallback=False,
        )

    def ask(self, user_message: str) -> str:
        """單次問答（完整小六 SKILL，適合深度討論）。"""
        return self.chat([{"role": "user", "content": user_message}])

    def ask_spot(self, user_message: str) -> str:
        """舊版決策點精簡分析（保留相容）。"""
        raw = ollama.chat_completion(
            [{"role": "user", "content": user_message}],
            base_url=self._base_url,
            model=self._spot_model,
            temperature=self._spot_temperature,
            timeout=self._timeout,
            max_tokens=120,
        )
        return limit_review_length(raw, 100)

    def ask_street_review(self, street: StreetId, street_prompt: str) -> str:
        """單一街道點評：草稿 → LLM 精簡（重試）。"""
        hint = STREET_REVIEW_HINTS[street]
        user_content = f"{street_prompt}\n\n{hint}\n輸出請用「1.」「2.」條列。"
        draft = self._chat_review(
            [
                {"role": "system", "content": HAND_REVIEW_SYSTEM},
                {"role": "user", "content": user_content},
            ],
            max_tokens=self._review_max_tokens,
        )
        return summarize_to_limit(
            draft,
            max_chars=MAX_SECTION_CHARS,
            chat_fn=self._summarize_chat,
        )

    def ask_hand_review(self, hand_prompt: str) -> HandReview:
        """局末整手牌點評（相容：單 prompt 視為翻前）。"""
        content = self.ask_street_review("preflop", hand_prompt)
        return HandReview(
            sections=[
                ReviewSection(
                    street="preflop",
                    title=STREET_TITLES["preflop"],
                    content=content,
                )
            ]
        )

    def ask_hand_review_sections(
        self,
        street_prompts: list[tuple[StreetId, str]],
    ) -> HandReview:
        """分街點評：僅對有進入的街道各產生一段。"""
        sections: list[ReviewSection] = []
        for street, prompt in street_prompts:
            content = self.ask_street_review(street, prompt)
            sections.append(
                ReviewSection(
                    street=street,
                    title=STREET_TITLES[street],
                    content=normalize_text(content),
                )
            )
        return HandReview(sections=sections)

    def chat(self, messages: list[ChatMessage]) -> str:
        """多輪對話；messages 只需 user/assistant，system 會自動加入。"""
        if not messages:
            raise ValueError("messages 不可為空")
        for msg in messages:
            if msg.get("role") not in {"user", "assistant"}:
                raise ValueError(f"不支援的 role: {msg.get('role')!r}")

        return ollama.chat_completion(
            self._with_system(messages),
            base_url=self._base_url,
            model=self._model,
            temperature=self._temperature,
            timeout=self._timeout,
        )
