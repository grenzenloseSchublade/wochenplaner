"""Tests für das Farbschema (pdf_colors) + Context-Integration."""

from pdf_colors import (
    _MONO_HUE,
    _hex_hsl,
    build_color_overrides,
    mono_chrome_colors,
    plan_mono_hue,
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


# ── Plan-Farbton (dynamisches monochrome) ────────────────────────────────────


def test_plan_mono_hue_grayscale_falls_back_to_blue() -> None:
    # Reine Graustufen tragen keinen Farbton → Blau-Fallback.
    grays = [_act("a", "#888888"), _act("b", "#cccccc")]
    assert plan_mono_hue(grays) == _MONO_HUE


def test_plan_mono_hue_empty_falls_back_to_blue() -> None:
    assert plan_mono_hue([]) == _MONO_HUE


def test_plan_mono_hue_follows_green_plan() -> None:
    green = [_act("a", "#C5E1A5"), _act("b", "#8BC34A"), _act("c", "#66BB6A")]
    deg = plan_mono_hue(green) * 360.0
    assert 80.0 < deg < 160.0  # Grünbereich


def test_plan_mono_hue_is_circular_not_arithmetic() -> None:
    # Zwei Rottöne knapp beidseits von 0°/360°: korrektes Mittel liegt nahe 0,
    # ein arithmetisches Mittel läge fälschlich bei ~180° (Türkis).
    reds = [_act("a", "#ff0033"), _act("b", "#ff3300")]
    deg = plan_mono_hue(reds) * 360.0
    assert deg < 30.0 or deg > 330.0


def test_mono_chrome_fallback_matches_legacy_blue() -> None:
    # Bei _MONO_HUE reproduzieren die Chrome-Akzente die alten statischen Werte.
    primary, tertiary = mono_chrome_colors(_MONO_HUE)
    # Beide Akzente liegen im selben Blau (~212°); 8-bit-Rundung erlaubt minimale
    # Abweichung je Lightness.
    assert abs(_hex_hsl(primary)[0] * 360 - 212) < 2
    assert abs(_hex_hsl(tertiary)[0] * 360 - 212) < 2


def test_context_stores_plan_mono_hue() -> None:
    green = [_act("a", "#C5E1A5"), _act("b", "#8BC34A")]
    ctx = build_pdf_context(green, color_scheme="monochrome")
    assert 80.0 < ctx["mono_hue"] * 360.0 < 160.0
    # Kacheln tragen denselben (grünen) Farbton.
    sample = next(iter(ctx["color_overrides"].values()))
    assert 80.0 < _hex_hsl(sample)[0] * 360.0 < 160.0
