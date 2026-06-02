"""Tests für Plan-Notiz (Zeilenumbrüche, PDF/HTML)."""

import unittest

from html_pdf.layout import build_week_template_vars
from pdf_context import build_pdf_context
from utils import normalize_plan_note_newlines, plan_note_lines, plan_note_multiline


class TestPlanNote(unittest.TestCase):
    def test_normalize_br_tags_to_newlines(self) -> None:
        raw = "Zeile 1<br>Zeile 2<br/>Zeile 3"
        self.assertEqual(
            normalize_plan_note_newlines(raw),
            "Zeile 1\nZeile 2\nZeile 3",
        )

    def test_plan_note_multiline_preserves_user_newlines(self) -> None:
        self.assertEqual(
            plan_note_multiline("A\nB"),
            "A\nB",
        )

    def test_html_layout_no_literal_br_in_plan_note(self) -> None:
        ctx = build_pdf_context([], plan_note="Linie 1\nLinie 2")
        layout = build_week_template_vars(ctx)
        self.assertIn("\n", layout["plan_note"])
        self.assertNotIn("<br>", layout["plan_note"])

    def test_plan_note_lines_for_classic_pdf(self) -> None:
        self.assertEqual(
            plan_note_lines("Erste<br>Zweite"),
            ["Erste", "Zweite"],
        )


if __name__ == "__main__":
    unittest.main()
