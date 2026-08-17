import importlib.util
import pathlib
import sys
import types
import unittest


if importlib.util.find_spec("openai") is None:
    openai_stub = types.ModuleType("openai")
    openai_stub.OpenAI = object
    sys.modules["openai"] = openai_stub


MODULE_PATH = pathlib.Path(__file__).parents[1] / "__init__.py"
SPEC = importlib.util.spec_from_file_location("comfy_simple_llm", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ReasoningTextFilterTests(unittest.TestCase):
    def test_default_think_mode_removes_multiple_blocks(self):
        source = "<think>first</think>Answer A\n<think>second</think>Answer B"
        self.assertEqual(
            MODULE.filter_reasoning_text(source),
            "Answer A\nAnswer B",
        )

    def test_think_mode_handles_missing_opening_tag(self):
        source = "hidden reasoning from an injected opener</think>\n\nVisible answer"
        self.assertEqual(
            MODULE.filter_reasoning_text(source),
            "Visible answer",
        )

    def test_think_mode_handles_truncated_block(self):
        source = "Visible preface\n<think>unfinished reasoning"
        self.assertEqual(
            MODULE.filter_reasoning_text(source),
            "Visible preface",
        )

    def test_selected_mode_does_not_remove_other_tags(self):
        source = "<analysis>Keep this literal section</analysis>"
        self.assertEqual(
            MODULE.filter_reasoning_text(source, "<think>...</think>"),
            source,
        )

    def test_auto_mode_removes_common_tags_and_unwraps_answer(self):
        source = (
            "<thinking>one</thinking>\n"
            "<reasoning>two</reasoning>\n"
            "<answer>Final text</answer>"
        )
        self.assertEqual(
            MODULE.filter_reasoning_text(source, "自动（常见格式）"),
            "Final text",
        )

    def test_markdown_fence_mode(self):
        source = "```reasoning\nhidden\n```\n\nVisible"
        self.assertEqual(
            MODULE.filter_reasoning_text(source, "Markdown 推理块"),
            "Visible",
        )

    def test_markdown_reasoning_and_final_headings(self):
        source = "Reasoning:\nHidden steps\n\nFinal Answer: Visible answer"
        self.assertEqual(
            MODULE.filter_reasoning_text(source, "Markdown 推理块"),
            "Visible answer",
        )

    def test_markdown_mode_preserves_ordinary_analysis_prose(self):
        source = "Analysis of the result\nAnswer: this entire passage is visible"
        self.assertEqual(
            MODULE.filter_reasoning_text(source, "Markdown 推理块"),
            source,
        )

    def test_harmony_mode_extracts_final_channel(self):
        source = (
            '<|channel|>analysis<|message|>Hidden reasoning<|end|>'
            '<|start|>assistant<|channel|>final<|message|>'
            'Visible answer<|return|>'
        )
        self.assertEqual(
            MODULE.filter_reasoning_text(source, "Harmony analysis/final"),
            "Visible answer",
        )

    def test_node_returns_a_single_string_tuple(self):
        node = MODULE.ChainOfThoughtFilterNode()
        self.assertEqual(
            node.filter_text("<think>hidden</think>shown", "<think>...</think>"),
            ("shown",),
        )


if __name__ == "__main__":
    unittest.main()
