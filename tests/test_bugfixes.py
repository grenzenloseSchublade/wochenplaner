"""Regressionstests für die behobenen Bugs (A1–A5) + WeasyPrint-Renderer."""

import unittest

from calendar_render import _activity_block, _ctx_menu_js, render_calendar
from pdf_context import build_pdf_context
from pdf_export import generate_pdf_from_context
from utils import validate_activity


def _act(**kw) -> dict:
    base = {
        "id": "x",
        "name": "Block",
        "day": "Montag",
        "start": "08:00",
        "end": "10:00",
        "color": "#F3E5AB",
    }
    base.update(kw)
    return base


class TestNoteNoneDoesNotCrash(unittest.TestCase):
    """A1: `note: null` darf den PDF-/Kalender-Export nicht crashen."""

    def test_classic_pdf_with_note_none(self) -> None:
        acts = [_act(note=None)]
        for grid in (True, False):
            ctx = build_pdf_context(acts, continuous_horizontal_grid=grid)
            data = generate_pdf_from_context(ctx)
            self.assertTrue(data.startswith(b"%PDF"))

    def test_calendar_block_with_note_none(self) -> None:
        # darf nicht werfen und rendert einen Block
        html = _activity_block(_act(note=None), abs_start=6 * 60, eh=22)
        self.assertIn("act-block", html)


class TestTimeValidation(unittest.TestCase):
    """A4: ungültige Uhrzeiten werden abgelehnt."""

    def test_rejects_out_of_range(self) -> None:
        for bad in ("25:00", "12:75", "99:99", "24:00"):
            self.assertFalse(validate_activity(_act(start=bad)), bad)

    def test_accepts_valid(self) -> None:
        for good in ("00:00", "09:15", "23:59", "22:00"):
            self.assertTrue(validate_activity(_act(start=good, end="23:59")), good)


class TestCalendarEscaping(unittest.TestCase):
    """A2: Aktivitätsname darf kein Markup ins Kontextmenü einschleusen."""

    def test_name_html_escaped_in_block(self) -> None:
        html = _activity_block(
            _act(name="<img src=x onerror=alert(1)>"), abs_start=6 * 60, eh=22
        )
        self.assertNotIn("<img", html)
        self.assertIn("&lt;img", html)

    def test_ctx_menu_reescapes_attributes(self) -> None:
        js = _ctx_menu_js("Bearbeiten")
        # data-name/day/start/end laufen über den esc()-Helfer, bevor sie via
        # innerHTML eingesetzt werden (sonst DOM-XSS).
        self.assertIn("function esc(", js)
        self.assertIn("esc(el.getAttribute('data-name'))", js)

    def test_full_render_escapes_name(self) -> None:
        import json

        acts = [_act(name="<script>bad</script>")]
        html = render_calendar(json.dumps(acts), 6, 22, component_mode=True)
        self.assertNotIn("<script>bad", html)


class TestDecodePlanBomb(unittest.TestCase):
    """A3: zlib-Bombe / Übergröße im URL-Decode wird abgewehrt."""

    def test_oversized_input_rejected(self) -> None:
        from app import decode_plan

        self.assertIsNone(decode_plan("x" * 300_000))

    def test_decompression_bomb_rejected(self) -> None:
        import base64
        import zlib

        from app import decode_plan

        raw = zlib.compress(b"A" * 5_000_000)
        self.assertIsNone(decode_plan(base64.urlsafe_b64encode(raw).decode()))


class TestWeasyPrintRenderer(unittest.TestCase):
    """Teil C: browserloser Renderer erzeugt einseitige PDFs (A4 + A5)."""

    def setUp(self) -> None:
        try:
            import weasyprint  # noqa: F401
        except Exception as exc:  # fehlende Lib/Systembibliotheken
            self.skipTest(f"weasyprint nicht verfügbar: {exc}")

    def _pages(self, data: bytes) -> int:
        import io

        from pypdf import PdfReader

        return len(PdfReader(io.BytesIO(data)).pages)

    def test_weasyprint_single_page(self) -> None:
        from html_pdf.render import _pdf_weasyprint, build_week_html

        acts = [_act(note=None), _act(name="Spät", start="20:00", end="22:00")]
        for fmt in ("A4", "A5"):
            ctx = build_pdf_context(
                acts, paper_format=fmt, plan_note="KW 25 – Test"
            )
            data = _pdf_weasyprint(build_week_html(ctx))
            self.assertTrue(data.startswith(b"%PDF"))
            self.assertEqual(self._pages(data), 1, f"{fmt} sollte 1 Seite sein")


if __name__ == "__main__":
    unittest.main()
