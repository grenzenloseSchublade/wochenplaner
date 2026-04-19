"""Hilfsfunktionen für Eintrag-Notiz (Kontrast, Mindesthöhe)."""

from constants import PX_PER_MIN
from utils import (
    get_secondary_text_color,
    get_text_color,
    inline_note_fits_block_height,
)


def test_inline_note_fits_tall_enough() -> None:
    # 1 h Rasterhöhe → immer Inline-Notiz
    assert inline_note_fits_block_height(60.0 * PX_PER_MIN)
    assert not inline_note_fits_block_height(20.0 * PX_PER_MIN)


def test_secondary_differs_from_primary() -> None:
    bg = "#F3E5AB"
    p = get_text_color(bg)
    s = get_secondary_text_color(bg)
    assert s != p
    assert s.startswith("#")
