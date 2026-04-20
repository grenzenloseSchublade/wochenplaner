"""Regression-Tests für html_pdf.layout – ohne Chromium-Abhängigkeit."""

from __future__ import annotations

import unittest

from html_pdf.layout import build_week_template_vars
from html_pdf.render import (
    DEFAULT_PDF_THEME,
    _normalize_paper_format,
    _normalize_pdf_theme,
    build_week_html,
)
from pdf_context import DEFAULT_PDF_STYLE_THEME, build_pdf_context


def _ctx(activities: list[dict]) -> dict:
    return build_pdf_context(
        activities,
        paper_format="A4",
        start_hour=8,
        end_hour=18,
        title="Test",
        lang="de",
    )


class TestLayoutOverlap(unittest.TestCase):
    def test_overlapping_blocks_are_sorted_by_start_time(self) -> None:
        """Überlappende Einträge müssen deterministisch nach Startzeit sortiert erscheinen."""
        activities = [
            {
                "id": "b",
                "name": "Später",
                "day": "Montag",
                "start": "10:00",
                "end": "11:30",
                "color": "#F3E5AB",
            },
            {
                "id": "a",
                "name": "Früher",
                "day": "Montag",
                "start": "09:30",
                "end": "11:00",
                "color": "#F3E5AB",
            },
        ]
        data = build_week_template_vars(_ctx(activities))
        monday = data["columns"][0]
        self.assertEqual(monday["day_label"][:2].lower(), "mo")
        blocks = monday["blocks"]
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0]["start_str"], "09:30")
        self.assertEqual(blocks[1]["start_str"], "10:00")


class TestLayoutColorValidation(unittest.TestCase):
    def test_invalid_color_falls_back(self) -> None:
        """Ungültige Farbe darf keinen ValueError werfen, Fallback-Farbe nutzen."""
        activities = [
            {
                "id": "x",
                "name": "Block",
                "day": "Dienstag",
                "start": "09:00",
                "end": "10:00",
                "color": "rot",
            },
        ]
        data = build_week_template_vars(_ctx(activities))
        tuesday = data["columns"][1]
        self.assertEqual(len(tuesday["blocks"]), 1)
        bg = tuesday["blocks"][0]["bg"]
        self.assertTrue(bg.startswith("#") and len(bg) == 7)

    def test_missing_color_falls_back(self) -> None:
        activities = [
            {
                "id": "x",
                "name": "Block",
                "day": "Dienstag",
                "start": "09:00",
                "end": "10:00",
            },
        ]
        data = build_week_template_vars(_ctx(activities))
        tuesday = data["columns"][1]
        self.assertEqual(len(tuesday["blocks"]), 1)


class TestPaperFormatWhitelist(unittest.TestCase):
    def test_a4_ok(self) -> None:
        self.assertEqual(_normalize_paper_format("a4"), "A4")

    def test_a5_ok(self) -> None:
        self.assertEqual(_normalize_paper_format("A5"), "A5")

    def test_invalid_raises(self) -> None:
        with self.assertRaises(ValueError):
            _normalize_paper_format("Letter")

    def test_empty_raises(self) -> None:
        with self.assertRaises(ValueError):
            _normalize_paper_format("")


class TestPdfThemeWhitelist(unittest.TestCase):
    def test_all_valid(self) -> None:
        for theme in ("minimal", "structured", "balanced"):
            self.assertEqual(_normalize_pdf_theme(theme), theme)

    def test_case_and_whitespace(self) -> None:
        self.assertEqual(_normalize_pdf_theme("  Minimal  "), "minimal")

    def test_invalid_raises(self) -> None:
        with self.assertRaises(ValueError):
            _normalize_pdf_theme("fancy")

    def test_empty_raises(self) -> None:
        with self.assertRaises(ValueError):
            _normalize_pdf_theme("")

    def test_default_is_structured(self) -> None:
        self.assertEqual(DEFAULT_PDF_THEME, "structured")
        self.assertEqual(DEFAULT_PDF_STYLE_THEME, "structured")


class TestThemeRendering(unittest.TestCase):
    def _ctx_with(self, theme: str) -> dict:
        return build_pdf_context(
            [
                {
                    "id": "a",
                    "name": "Block",
                    "day": "Montag",
                    "start": "09:00",
                    "end": "10:00",
                    "color": "#F3E5AB",
                },
            ],
            paper_format="A4",
            start_hour=8,
            end_hour=18,
            title="T",
            lang="de",
            pdf_style_theme=theme,
        )

    def test_theme_class_in_html(self) -> None:
        for theme in ("minimal", "structured", "balanced"):
            html = build_week_html(self._ctx_with(theme))
            self.assertIn(f"theme--{theme}", html)
            self.assertIn("calendar-table", html)
            self.assertIn("day-col--week", html)
            self.assertIn("day-col--weekend", html)

    def test_weekday_to_weekend_classes(self) -> None:
        html = build_week_html(self._ctx_with("structured"))
        # 5 Werktage + 2 Wochenend-Tage → jeweils in .day-col + .day-head.
        self.assertEqual(html.count('day-col--week"'), 5)
        self.assertEqual(html.count('day-col--weekend"'), 2)
        self.assertEqual(html.count('day-head--week"'), 5)
        self.assertEqual(html.count('day-head--weekend"'), 2)

    def test_default_theme_in_context(self) -> None:
        ctx = build_pdf_context([], paper_format="A5")
        self.assertEqual(ctx["pdf_style_theme"], "structured")


if __name__ == "__main__":
    unittest.main()
