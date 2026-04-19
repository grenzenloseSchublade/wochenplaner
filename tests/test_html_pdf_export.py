"""Smoke tests for HTML→PDF (Playwright)."""

import unittest

from html_pdf import render_html_pdf
from pdf_context import build_pdf_context


class TestHtmlPdfExport(unittest.TestCase):
    def test_render_html_pdf_valid_header(self) -> None:
        activities = [
            {
                "day": "Montag",
                "start": "09:00",
                "end": "10:00",
                "name": "Block",
                "color": "#F3E5AB",
                "id": "a",
            },
        ]
        ctx = build_pdf_context(
            activities,
            paper_format="A4",
            start_hour=8,
            end_hour=18,
            title="Test",
            lang="de",
        )
        data = render_html_pdf(ctx)
        self.assertGreater(len(data), 500)
        self.assertTrue(data.startswith(b"%PDF"))

    def test_render_html_pdf_empty_plan(self) -> None:
        ctx = build_pdf_context([], paper_format="A5", lang="en")
        data = render_html_pdf(ctx)
        self.assertTrue(data.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
