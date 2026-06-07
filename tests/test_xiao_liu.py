"""小六 Skill 模組單元測試（不需 Ollama）。"""



from __future__ import annotations



import unittest

from unittest.mock import MagicMock, patch

import json



from poker_learning_tool.common.project import find_project_root

from poker_learning_tool.perspective.xiao_liu import ollama

from poker_learning_tool.perspective.xiao_liu.analysis import (
    MAX_SECTION_CHARS,
    limit_review_length,
    normalize_text,
    summarize_to_limit,
    trim_to_boundary,
)
from poker_learning_tool.perspective.xiao_liu.client import XiaoLiuSkill

from poker_learning_tool.perspective.xiao_liu.skill import (

    SKILL_RELATIVE,

    default_skill_path,

    load_skill_text,

)





class TestSkillLoader(unittest.TestCase):

    def test_find_project_root(self) -> None:

        root = find_project_root()

        self.assertTrue((root / SKILL_RELATIVE).is_file())



    def test_load_skill_text(self) -> None:

        text = load_skill_text()

        self.assertIn("小六", text)

        self.assertIn("xiao-liu-perspective", text)



    def test_load_skill_text_custom_path(self) -> None:

        skill_file = find_project_root() / SKILL_RELATIVE

        text = load_skill_text(skill_file)

        self.assertGreater(len(text), 1000)



    def test_default_skill_path(self) -> None:

        path = default_skill_path()

        self.assertEqual(path.name, "SKILL.md")

        self.assertTrue(path.is_file())





class TestAnalysisText(unittest.TestCase):
    def test_normalize_preserves_lines(self) -> None:
        self.assertEqual(normalize_text("a\n\n  b"), "a\nb")

    def test_trim_to_boundary_not_mid_sentence(self) -> None:
        text = "第一句很好。第二句" + "很" * 300
        result = trim_to_boundary(text, 20)
        self.assertLessEqual(len(result), 20)
        self.assertIn("內容已壓縮", result)

    def test_limit_review_length_uses_boundary(self) -> None:
        long_text = "開頭。" + "字" * 600
        result = limit_review_length(long_text, max_chars=50)
        self.assertLessEqual(len(result), 60)

    def test_summarize_to_limit_retries(self) -> None:
        calls: list[int] = []

        def fake_chat(_messages: list[dict[str, str]]) -> str:
            calls.append(1)
            if len(calls) == 1:
                return "字" * 300
            return "1. 精簡建議"

        result = summarize_to_limit(
            "草" * 400,
            max_chars=MAX_SECTION_CHARS,
            chat_fn=fake_chat,
        )
        self.assertLessEqual(len(result), MAX_SECTION_CHARS + 20)
        self.assertGreaterEqual(len(calls), 2)


class TestOllama(unittest.TestCase):

    def test_strip_thinking(self) -> None:

        think_open = "<" + "think" + ">"

        think_close = "</" + "think" + ">"

        raw = f"{think_open}\ninternal\n{think_close}\n\n這是回答"

        self.assertEqual(ollama.strip_thinking(raw), "這是回答")



    def test_strip_thinking_no_block(self) -> None:

        self.assertEqual(ollama.strip_thinking("直接回答"), "直接回答")

    @patch("poker_learning_tool.perspective.xiao_liu.ollama.urllib.request.urlopen")
    def test_chat_completion_reasoning_fallback(self, mock_urlopen: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "",
                            "reasoning": "翻前先建 range，AK 可 open。",
                        }
                    }
                ]
            }
        ).encode()
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        result = ollama.chat_completion([{"role": "user", "content": "hi"}])
        self.assertEqual(result, "翻前先建 range，AK 可 open。")

    @patch("poker_learning_tool.perspective.xiao_liu.ollama.urllib.request.urlopen")
    def test_chat_completion_no_reasoning_when_disabled(self, mock_urlopen: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "",
                            "reasoning": "內心獨白",
                        }
                    }
                ]
            }
        ).encode()
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        with self.assertRaises(RuntimeError):
            ollama.chat_completion(
                [{"role": "user", "content": "hi"}],
                allow_reasoning_fallback=False,
            )





class TestXiaoLiuSkill(unittest.TestCase):

    def setUp(self) -> None:

        self.skill = XiaoLiuSkill()



    def test_system_prompt_loaded(self) -> None:

        self.assertIn("思维操作系统", self.skill.system_prompt)



    def test_with_system_prepends_system_message(self) -> None:

        messages = self.skill._with_system([{"role": "user", "content": "hi"}])

        self.assertEqual(messages[0]["role"], "system")

        self.assertEqual(messages[0]["content"], self.skill.system_prompt)

        self.assertEqual(messages[1]["content"], "hi")



    def test_chat_rejects_empty_messages(self) -> None:

        with self.assertRaises(ValueError):

            self.skill.chat([])



    def test_chat_rejects_invalid_role(self) -> None:

        with self.assertRaises(ValueError):

            self.skill.chat([{"role": "system", "content": "bad"}])



    @patch("poker_learning_tool.perspective.xiao_liu.client.ollama.chat_completion")
    def test_ask_spot_limits_length(self, mock_chat: MagicMock) -> None:
        mock_chat.return_value = "字" * 150
        answer = self.skill.ask_spot("階段：preflop")
        self.assertLessEqual(len(answer), 100)

    @patch("poker_learning_tool.perspective.xiao_liu.client.ollama.chat_completion")
    def test_ask_hand_review_two_stage(self, mock_chat: MagicMock) -> None:
        mock_chat.side_effect = ["字" * 400, "1. 精简后的点评"]
        answer = self.skill.ask_hand_review("hand history")
        self.assertEqual(answer.sections[0].content, "1. 精简后的点评")
        self.assertEqual(answer.sections[0].title, "翻前")
        self.assertEqual(mock_chat.call_count, 2)
        summarize_kwargs = mock_chat.call_args_list[1].kwargs
        self.assertFalse(summarize_kwargs["allow_reasoning_fallback"])

    @patch("poker_learning_tool.perspective.xiao_liu.client.ollama.chat_completion")
    def test_ask_hand_review_sections(self, mock_chat: MagicMock) -> None:
        mock_chat.side_effect = [
            "翻前草稿" * 10,
            "1. 翻前建議",
            "翻牌草稿" * 10,
            "1. 翻牌建議",
        ]
        review = self.skill.ask_hand_review_sections(
            [
                ("preflop", "preflop prompt"),
                ("flop", "flop prompt"),
            ]
        )
        self.assertEqual(len(review.sections), 2)
        self.assertEqual(review.sections[0].street, "preflop")
        self.assertEqual(review.sections[1].street, "flop")

    @patch("poker_learning_tool.perspective.xiao_liu.client.ollama.chat_completion")
    def test_ask_calls_ollama(self, mock_chat: MagicMock) -> None:

        mock_chat.return_value = "先建 range 再選 action"

        answer = self.skill.ask("什麼是 range？")

        self.assertEqual(answer, "先建 range 再選 action")

        mock_chat.assert_called_once()

        sent_messages = mock_chat.call_args.args[0]

        self.assertEqual(sent_messages[0]["role"], "system")

        self.assertEqual(sent_messages[-1]["content"], "什麼是 range？")



    @patch("poker_learning_tool.perspective.xiao_liu.client.ollama.chat_completion")

    def test_chat_multi_turn(self, mock_chat: MagicMock) -> None:

        mock_chat.return_value = "泡沫期 medium stack 要收紧"

        history = [

            {"role": "user", "content": "什麼情況 fold？"},

            {"role": "assistant", "content": "EV 负就 fold"},

            {"role": "user", "content": "MTT 泡沫呢？"},

        ]

        reply = self.skill.chat(history)

        self.assertEqual(reply, "泡沫期 medium stack 要收紧")

        sent = mock_chat.call_args.args[0]

        self.assertEqual(len(sent), 4)  # system + 3 history





class TestXiaoLiuCompatShim(unittest.TestCase):

    def test_legacy_import_path(self) -> None:

        from poker_learning_tool.xiao_liu import XiaoLiuSkill as LegacySkill



        self.assertIs(LegacySkill, XiaoLiuSkill)





if __name__ == "__main__":

    unittest.main()

