"""Farbschema-Transformation für den PDF-Export (klassisch + modern).

Eine Quelle der Wahrheit, damit ReportLab- und HTML→PDF-Pfad identische
Farben erzeugen. Drei Schemata:

- ``"color"``      – Originalfarben, kein Eingriff (Standard).
- ``"grayscale"``  – Aktivitäten auf **distinkte Graustufen**; Chrome
                     luminanz-erhaltend in Grau.
- ``"monochrome"`` – wie ``grayscale``, aber in Tönen **einer Grundfarbe**
                     (Blau, Hue 212).

Ziel: saubere Ausdrucke auf Schwarz-Weiß-Druckern. Verschiedene Aktivitäten
bleiben durch klar getrennte Tonstufen unterscheidbar, weil jeder eindeutige
Aktivitätsname eine eigene Lightness-Stufe bekommt (statt nur die Luminanz der
Originalfarbe zu übernehmen, wo zwei Farben gleich grau werden könnten).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from utils import Activity, validate_color

ColorScheme = Literal["color", "grayscale", "monochrome"]
DEFAULT_COLOR_SCHEME: ColorScheme = "color"
ALLOWED_COLOR_SCHEMES: frozenset[str] = frozenset(
    {"color", "grayscale", "monochrome"}
)

# Tonstufen-Bereich (HSL-Lightness). Bewusst weg von den Extremen: oben nicht
# bis 1.0, damit helle Kacheln nicht mit dem weißen Papier verschmelzen; unten
# nicht bis 0.0, damit dunkle Kacheln Text noch tragen und nicht „zulaufen".
_L_LIGHT = 0.86
_L_DARK = 0.34

# Grundfarbe für „monochrome" – ein ruhiges Blau, gut druckbar.
_MONO_HUE = 212.0 / 360.0
_MONO_SAT = 0.42


def _hex_rgb(h: str) -> tuple[int, int, int]:
    hx = h.lstrip("#")
    if len(hx) == 3:
        hx = "".join(c * 2 for c in hx)
    return int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)


def _luminance(hex_c: str) -> float:
    """Wahrgenommene Helligkeit (0..1), gleiche Gewichtung wie get_text_color."""
    r, g, b = _hex_rgb(hex_c)
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _hsl_to_hex(h: float, s: float, lightness: float) -> str:
    """HSL (jeweils 0..1) → ``#rrggbb``."""

    def _channel(p: float, q: float, t: float) -> float:
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p

    if s == 0:
        r = g = b = lightness
    else:
        q = (
            lightness * (1 + s)
            if lightness < 0.5
            else lightness + s - lightness * s
        )
        p = 2 * lightness - q
        r = _channel(p, q, h + 1 / 3)
        g = _channel(p, q, h)
        b = _channel(p, q, h - 1 / 3)
    return (
        f"#{round(_clamp01(r) * 255):02x}"
        f"{round(_clamp01(g) * 255):02x}"
        f"{round(_clamp01(b) * 255):02x}"
    )


def _gray_hex(lightness: float) -> str:
    v = round(_clamp01(lightness) * 255)
    return f"#{v:02x}{v:02x}{v:02x}"


def _tone_hex(scheme: str, lightness: float) -> str:
    """Tonwert für eine Lightness-Stufe gemäß Schema."""
    if scheme == "monochrome":
        return _hsl_to_hex(_MONO_HUE, _MONO_SAT, lightness)
    return _gray_hex(lightness)


def build_color_overrides(
    activities: Sequence[Activity], scheme: str
) -> dict[str, str]:
    """Map *Aktivitätsname → Tonfarbe* für ``grayscale``/``monochrome``.

    Für ``color`` (oder unbekannte Schemata) wird eine leere Map zurückgegeben –
    die Renderer fallen dann auf die Originalfarben zurück.

    Jeder eindeutige Name erhält eine eigene, klar getrennte Lightness-Stufe.
    Die Sortierung nach Original-Helligkeit (hell → dunkel) hält die Zuordnung
    intuitiv und deterministisch (Name als Tiebreaker).
    """
    if scheme not in ("grayscale", "monochrome"):
        return {}

    reps: dict[str, str] = {}
    for act in activities:
        name = str(act.get("name", ""))
        if name not in reps:
            reps[name] = validate_color(str(act.get("color", "") or ""))

    names = sorted(reps, key=lambda n: (-_luminance(reps[n]), n))
    n = len(names)
    out: dict[str, str] = {}
    for i, name in enumerate(names):
        frac = 0.5 if n <= 1 else i / (n - 1)
        lightness = _L_LIGHT - frac * (_L_LIGHT - _L_DARK)
        out[name] = _tone_hex(scheme, lightness)
    return out


def recolor_chrome(hex_c: str, scheme: str) -> str:
    """Neutralisiert eine Chrome-Farbe (Header, Titel …) luminanz-erhaltend.

    ``color`` lässt die Farbe unverändert; ``grayscale`` ersetzt sie durch das
    Grau gleicher Helligkeit; ``monochrome`` durch den Blauton gleicher
    Helligkeit. So bleibt der Hell-Dunkel-Kontrast des Layouts erhalten.
    """
    if scheme not in ("grayscale", "monochrome"):
        return hex_c
    return _tone_hex(scheme, _luminance(validate_color(hex_c)))
