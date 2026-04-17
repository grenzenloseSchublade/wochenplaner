"""Smoke tests for PDF export."""

import unittest

from pdf_export import generate_pdf, minutes_to_hhmm


class TestPdfExport(unittest.TestCase):
    def test_generates_valid_pdf_header(self) -> None:
        activities = [
            {
                "day": "Montag",
                "start": "09:00",
                "end": "09:20",
                "name": "Kurz",
                "color": "#F3E5AB",
                "id": "a",
            },
            {
                "day": "Donnerstag",
                "start": "10:00",
                "end": "12:00",
                "name": "Längerer Block mit mehr Text",
                "color": "#FFB6B6",
                "id": "b",
            },
        ]
        data = generate_pdf(activities, paper_format="A4")
        self.assertGreater(len(data), 500)
        self.assertTrue(data.startswith(b"%PDF"))

    def test_a5_format(self) -> None:
        data = generate_pdf([], paper_format="A5")
        self.assertTrue(data.startswith(b"%PDF"))

    def test_minutes_to_hhmm(self) -> None:
        self.assertEqual(minutes_to_hhmm(8 * 60), "08:00")
        self.assertEqual(minutes_to_hhmm(8 * 60 + 5), "08:05")
        self.assertEqual(minutes_to_hhmm(24 * 60 - 1), "23:59")

    def test_clamped_start_for_corner_matches_grid(self) -> None:
        """Wie generate_pdf: s_clamped bestimmt die Anzeige-Uhrzeit in der Ecke."""
        sh, sm = 5, 0
        start_hour = 8
        s_min = sh * 60 + sm
        s_clamped = max(s_min, start_hour * 60)
        self.assertEqual(minutes_to_hhmm(s_clamped), "08:00")
        activities = [
            {
                "day": "Mittwoch",
                "start": "05:00",
                "end": "10:00",
                "name": "Früh",
                "color": "#A8D8E8",
                "id": "early",
            },
        ]
        data = generate_pdf(
            activities,
            paper_format="A4",
            start_hour=start_hour,
            end_hour=22,
        )
        self.assertTrue(data.startswith(b"%PDF"))

    def test_long_duration_block(self) -> None:
        """Langer Block (z. B. 8 h) darf ohne Fehler erzeugt werden."""
        activities = [
            {
                "day": "Dienstag",
                "start": "08:00",
                "end": "16:00",
                "name": "Arbeit",
                "color": "#F3E5AB",
                "id": "long",
            },
        ]
        data = generate_pdf(
            activities,
            paper_format="A4",
            start_hour=6,
            end_hour=22,
        )
        self.assertGreater(len(data), 500)
        self.assertTrue(data.startswith(b"%PDF"))

    def test_axis_times_off_block_times_on(self) -> None:
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
        data = generate_pdf(
            activities,
            paper_format="A4",
            show_axis_times=False,
            show_block_times=True,
        )
        self.assertTrue(data.startswith(b"%PDF"))

    def test_axis_times_on_block_times_off(self) -> None:
        activities = [
            {
                "day": "Dienstag",
                "start": "11:00",
                "end": "12:00",
                "name": "Ohne Ecke",
                "color": "#FFB6B6",
                "id": "b",
            },
        ]
        data = generate_pdf(
            activities,
            paper_format="A4",
            show_axis_times=True,
            show_block_times=False,
        )
        self.assertTrue(data.startswith(b"%PDF"))

    def test_both_time_displays_off(self) -> None:
        activities = [
            {
                "day": "Mittwoch",
                "start": "14:00",
                "end": "15:00",
                "name": "Minimal",
                "color": "#A8D8E8",
                "id": "c",
            },
        ]
        data = generate_pdf(
            activities,
            paper_format="A4",
            show_axis_times=False,
            show_block_times=False,
        )
        self.assertTrue(data.startswith(b"%PDF"))

    def test_continuous_horizontal_grid_over_blocks(self) -> None:
        activities = [
            {
                "day": "Montag",
                "start": "10:00",
                "end": "11:00",
                "name": "Termin",
                "color": "#F3E5AB",
                "id": "x",
            },
        ]
        data = generate_pdf(
            activities,
            paper_format="A4",
            continuous_horizontal_grid=True,
        )
        self.assertTrue(data.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
