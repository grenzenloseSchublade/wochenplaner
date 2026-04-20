"""Tests für die Verwaltung eigener Aktivitäten (_delete_custom_activity)."""

from __future__ import annotations

import unittest
from typing import Any
from unittest.mock import MagicMock, patch


class _FakeSessionState(dict):
    """Dict mit zusätzlichem Attribut-Zugriff, wie streamlit.session_state."""

    def __getattr__(self, key: str) -> Any:
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value


class TestDeleteCustomActivity(unittest.TestCase):
    def _session(
        self,
        custom: list[str],
        colors: dict[str, str],
    ) -> _FakeSessionState:
        ss = _FakeSessionState()
        ss["custom_activities"] = list(custom)
        ss["activity_colors"] = dict(colors)
        ss["_ls_wc"] = 0
        return ss

    def _run(self, ss: _FakeSessionState, name: str) -> bool:
        import app

        fake_st = MagicMock()
        fake_st.session_state = ss
        with (
            patch.object(app, "st", fake_st),
            patch.object(app, "ls_save"),
        ):
            return app._delete_custom_activity(name)

    def test_removes_from_custom_and_colors(self) -> None:
        ss = self._session(
            ["Lernen", "Nebenjob"],
            {"Lernen": "#AABBCC", "Nebenjob": "#112233"},
        )
        changed = self._run(ss, "Lernen")
        self.assertTrue(changed)
        self.assertEqual(ss["custom_activities"], ["Nebenjob"])
        self.assertNotIn("Lernen", ss["activity_colors"])
        self.assertIn("Nebenjob", ss["activity_colors"])

    def test_preset_names_are_protected(self) -> None:
        import app

        preset_name = next(iter(app.AKTIVITAETEN_FARBEN))
        ss = self._session([], {preset_name: "#EEEEEE"})
        changed = self._run(ss, preset_name)
        self.assertFalse(changed)
        self.assertIn(preset_name, ss["activity_colors"])

    def test_unknown_name_is_noop(self) -> None:
        ss = self._session(["A"], {"A": "#ABCDEF"})
        changed = self._run(ss, "NichtDa")
        self.assertFalse(changed)
        self.assertEqual(ss["custom_activities"], ["A"])
        self.assertEqual(ss["activity_colors"], {"A": "#ABCDEF"})

    def test_removes_even_when_only_in_colors(self) -> None:
        """Legacy-Fall: Color-Map enthält Custom-Namen ohne custom_activities-Eintrag."""
        ss = self._session([], {"Altfarbe": "#123456"})
        changed = self._run(ss, "Altfarbe")
        self.assertTrue(changed)
        self.assertNotIn("Altfarbe", ss["activity_colors"])

    def test_removes_even_when_only_in_custom_list(self) -> None:
        ss = self._session(["NurName"], {})
        changed = self._run(ss, "NurName")
        self.assertTrue(changed)
        self.assertEqual(ss["custom_activities"], [])


if __name__ == "__main__":
    unittest.main()
