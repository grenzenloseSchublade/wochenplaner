"""Tests für das Farbschema (pdf_colors) + Context-Integration."""

from pdf_colors import (
    build_color_overrides,
    recolor_chrome,
)
from pdf_context import build_pdf_context


def _act(name: str, color: str, day: str = "Montag") -> dict:
    return {
        "id": name,
        "name": name,
        "day": day,
        "start": "08:00",
        "end": "09:00",
        "color": color,
    }


def test_color_scheme_returns_no_overrides() -> None:
    acts = [_act("Sport", "#ff0000"), _act("Lernen", "#00ff00")]
    assert build_color_overrides(acts, "color") == {}


def test_grayscale_overrides_are_pure_gray() -> None:
    acts = [_act("Sport", "#ff0000"), _act("Lernen", "#00ff00")]
    overrides = build_color_overrides(acts, "grayscale")
    assert set(overrides) == {"Sport", "Lernen"}
    for hexc in overrides.values():
        r, g, b = hexc[1:3], hexc[3:5], hexc[5:7]
        assert r == g == b, f"{hexc} ist nicht grau"


def test_distinct_levels_per_activity() -> None:
    """Verschiedene Aktivitäten erhalten klar getrennte Tonstufen."""
    acts = [_act(n, "#808080") for n in ("A", "B", "C", "D")]
    for scheme in ("grayscale", "monochrome"):
        overrides = build_color_overrides(acts, scheme)
        assert len(set(overrides.values())) == 4, (
            f"{scheme}: Tonstufen nicht eindeutig trotz gleicher Originalfarbe"
        )


def test_same_name_shares_one_tone() -> None:
    acts = [
        _act("Sport", "#ff0000", "Montag"),
        _act("Sport", "#ff0000", "Dienstag"),
        _act("Lernen", "#0000ff"),
    ]
    overrides = build_color_overrides(acts, "grayscale")
    assert set(overrides) == {"Sport", "Lernen"}


def test_brighter_original_maps_to_lighter_tone() -> None:
    """Helle Originalfarbe → hellere Tonstufe (intuitive Reihenfolge)."""
    acts = [_act("Hell", "#ffffff"), _act("Dunkel", "#000000")]
    overrides = build_color_overrides(acts, "grayscale")
    hell = int(overrides["Hell"][1:3], 16)
    dunkel = int(overrides["Dunkel"][1:3], 16)
    assert hell > dunkel


def test_deterministic() -> None:
    acts = [_act("B", "#111111"), _act("A", "#222222")]
    assert build_color_overrides(acts, "monochrome") == build_color_overrides(
        acts, "monochrome"
    )


def test_recolor_chrome_color_is_identity() -> None:
    assert recolor_chrome("#4472C4", "color") == "#4472C4"


def test_recolor_chrome_grayscale_is_gray() -> None:
    out = recolor_chrome("#4472C4", "grayscale")
    assert out[1:3] == out[3:5] == out[5:7]


def test_context_builds_overrides() -> None:
    acts = [_act("Sport", "#ff0000"), _act("Lernen", "#00ff00")]
    ctx = build_pdf_context(acts, color_scheme="grayscale")
    assert ctx["color_scheme"] == "grayscale"
    assert set(ctx["color_overrides"]) == {"Sport", "Lernen"}

    ctx_default = build_pdf_context(acts)
    assert ctx_default["color_scheme"] == "color"
    assert ctx_default["color_overrides"] == {}
