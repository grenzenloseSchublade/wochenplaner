"""Smoke tests for HTML→PDF (Playwright)."""

import io
import unittest

import pypdf

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


class TestHtmlPdfSinglePage(unittest.TestCase):
    """
    Regression: Wochenplan muss auf **eine** Seite passen.
    Prüft sowohl A4 als auch A5 quer, mit/ohne Plan-Notiz und gut gefülltem
    Plan (alle 7 Tage). Verhindert künftige Layout-Regressionen (z.B. doppeltes
    Page-Padding, Viewport/Page-Size-Mismatch, überdimensionale Header).
    """

    FULL_ACTIVITIES = [
        {"id": "w", "name": "Arbeit", "day": "Montag",
         "start": "09:00", "end": "17:00", "color": "#BFD7FF",
         "note": "Großraumbüro"},
        {"id": "m", "name": "Meeting", "day": "Dienstag",
         "start": "10:00", "end": "11:30", "color": "#F3E5AB"},
        {"id": "s", "name": "Sport", "day": "Mittwoch",
         "start": "07:00", "end": "08:00", "color": "#FFD1DC"},
        {"id": "l", "name": "Lernen", "day": "Donnerstag",
         "start": "08:00", "end": "12:00", "color": "#C5E1A5"},
        {"id": "k", "name": "Kochen", "day": "Freitag",
         "start": "18:00", "end": "19:30", "color": "#FFE0B2"},
        {"id": "e", "name": "Einkaufen", "day": "Samstag",
         "start": "10:00", "end": "11:00", "color": "#D7CCC8"},
        {"id": "r", "name": "Ruhen", "day": "Sonntag",
         "start": "14:00", "end": "16:00", "color": "#E1BEE7"},
    ]

    def _assert_one_page(self, paper_format: str, plan_note: str) -> None:
        ctx = build_pdf_context(
            self.FULL_ACTIVITIES,
            paper_format=paper_format,
            start_hour=6,
            end_hour=22,
            title="Wochenplan",
            plan_note=plan_note,
            lang="de",
            show_block_times=True,
        )
        data = render_html_pdf(ctx)
        reader = pypdf.PdfReader(io.BytesIO(data))
        self.assertEqual(
            len(reader.pages), 1,
            f"{paper_format} mit note={bool(plan_note)} ergab "
            f"{len(reader.pages)} Seiten – muss 1 sein.",
        )

    def test_a4_with_note_single_page(self) -> None:
        self._assert_one_page("A4", "Viel Erfolg diese Woche — bleib dran!")

    def test_a4_without_note_single_page(self) -> None:
        self._assert_one_page("A4", "")

    def test_a5_with_note_single_page(self) -> None:
        self._assert_one_page("A5", "Viel Erfolg diese Woche — bleib dran!")

    def test_a5_without_note_single_page(self) -> None:
        self._assert_one_page("A5", "")


if __name__ == "__main__":
    unittest.main()
