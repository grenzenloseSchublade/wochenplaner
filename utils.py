"""Hilfsfunktionen für den Wochenplaner."""

import re
import unicodedata
from typing import NotRequired, TypedDict

from constants import END_HOUR, PX_PER_MIN, START_HOUR, WOCHENTAGE


class Activity(TypedDict):
    id: str
    name: str
    day: str
    start: str
    end: str
    color: str
    note: NotRequired[str]


_HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
_TIME_RE = re.compile(r"^\d{2}:\d{2}$")

_REQUIRED_KEYS = {"id", "name", "day", "start", "end", "color"}


def t2m(t: str) -> int:
    h, m = map(int, t.split(":"))
    return h * 60 + m


def get_text_color(bg: str) -> str:
    hx = bg.lstrip("#")
    lum = (
        0.299 * int(hx[0:2], 16) + 0.587 * int(hx[2:4], 16) + 0.114 * int(hx[4:6], 16)
    ) / 255
    return "#333" if lum > 0.5 else "#eee"


def _hex_rgb(h: str) -> tuple[int, int, int]:
    hx = h.lstrip("#")
    if len(hx) == 3:
        hx = "".join(c * 2 for c in hx)
    return int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)


def _rgb_hex(r: int, g: int, b: int) -> str:
    return f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"


def get_secondary_text_color(bg: str, primary: str | None = None) -> str:
    """Sekundärtext auf farbigem Block: Mischung aus Titelfarbe und Hintergrund (~38 %)."""
    bg_v = validate_color(bg)
    pr = primary or get_text_color(bg_v)
    br, bgg, bb = _hex_rgb(bg_v)
    r1, g1, b1 = _hex_rgb(pr)
    t = 0.38
    r = int(r1 * (1 - t) + br * t)
    g = int(g1 * (1 - t) + bgg * t)
    b = int(b1 * (1 - t) + bb * t)
    return _rgb_hex(r, g, b)


def inline_note_fits_block_height(ht_px: float) -> bool:
    """Genug Höhe (Kalender-Pixel oder dur_min * PX_PER_MIN) für Inline-Notiz unter dem Namen."""
    # Volle Stunde im Raster: zuverlässig Inline-Notiz (auch bei etwas größerer Notizschrift)
    if ht_px + 1e-9 >= 60.0 * PX_PER_MIN:
        return True
    slack = 3.0
    need = 0.0
    if ht_px >= 28:
        need += 11.0
    if ht_px >= 22:
        need += 11.0
    need += 22.0  # zwei Notizzeilen (größere Schrift als früher 9px)
    if ht_px >= 38:
        need += 10.0
    return ht_px >= need + slack


def darken(hex_c: str, factor: float = 0.68) -> str:
    hx = hex_c.lstrip("#")
    r = int(int(hx[0:2], 16) * factor)
    g = int(int(hx[2:4], 16) * factor)
    b = int(int(hx[4:6], 16) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


def slugify(text: str) -> str:
    for s, d in [
        ("ä", "ae"),
        ("ö", "oe"),
        ("ü", "ue"),
        ("Ä", "Ae"),
        ("Ö", "Oe"),
        ("Ü", "Ue"),
        ("ß", "ss"),
    ]:
        text = text.replace(s, d)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "wochenplan"


def validate_color(c: str) -> str:
    """Return color if valid hex, else fallback."""
    return c if _HEX_COLOR_RE.match(c) else "#F3E5AB"


def check_overlap(
    acts: list[Activity],
    day: str,
    start: str,
    end: str,
    exclude_id: str | None = None,
) -> list[Activity]:
    ns, ne = t2m(start), t2m(end)
    return [
        a
        for a in acts
        if a["day"] == day
        and (exclude_id is None or a["id"] != exclude_id)
        and t2m(a["start"]) < ne
        and t2m(a["end"]) > ns
    ]


def validate_activity(item: dict) -> bool:
    """Prüft ob ein Dictionary alle Pflichtfelder einer Activity enthält."""
    if not isinstance(item, dict):
        return False
    if not _REQUIRED_KEYS.issubset(item.keys()):
        return False
    if not all(isinstance(item[k], str) for k in _REQUIRED_KEYS):
        return False
    if not (_TIME_RE.match(item["start"]) and _TIME_RE.match(item["end"])):
        return False
    return True


def safe_filename(name: str) -> str:
    """Erstellt einen sicheren Dateinamen ohne Pfad-Traversal."""
    name = name.replace("..", "").replace("/", "").replace("\\", "")
    name = name.strip(". ")
    return name or "wochenplan"


def shift_time(start: str, end: str, delta_min: int) -> tuple[str, str] | None:
    """Shift a start/end time pair by *delta_min* minutes (±15 steps).

    Returns the new (start, end) pair or ``None`` if the result would
    fall outside the visible grid (START_HOUR..END_HOUR).
    """
    s, e = t2m(start) + delta_min, t2m(end) + delta_min
    if s < START_HOUR * 60 or e > END_HOUR * 60:
        return None
    return f"{s // 60:02d}:{s % 60:02d}", f"{e // 60:02d}:{e % 60:02d}"


def shift_day(day: str, delta: int) -> str | None:
    """Shift a German weekday name by *delta* positions (±1).

    Returns the new day name or ``None`` if out of range.
    """
    try:
        idx = WOCHENTAGE.index(day)
    except ValueError:
        return None
    new_idx = idx + delta
    if new_idx < 0 or new_idx >= len(WOCHENTAGE):
        return None
    return WOCHENTAGE[new_idx]
