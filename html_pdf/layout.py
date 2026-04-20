"""Layout-Daten für HTML→PDF (Wochenraster, Kacheln) aus [`PdfExportContext`](../pdf_context.py)."""

from __future__ import annotations

from constants import PX_PER_MIN, WOCHENTAGE
from i18n import WOCHENTAGE_KURZ_I18N, t
from pdf_context import PdfExportContext
from pdf_export import MIN_MINUTES_FOR_NAME, minutes_to_hhmm
from utils import (
    get_secondary_text_color,
    get_text_color,
    inline_note_fits_block_height,
    validate_color,
)


def _plan_note_display(plan_note: str) -> str:
    s = plan_note.strip()
    if len(s) > 90:
        return s[:90] + "…"
    return s


def _size_tier(dur_min: int, h_pct: float) -> str:
    """Kachelgröße für Typo-Stufen (xs = sehr flach … lg = groß)."""
    if dur_min <= 22 or h_pct < 2.6:
        return "xs"
    if dur_min <= 48 or h_pct < 6.5:
        return "sm"
    if dur_min <= 100 or h_pct < 14.0:
        return "md"
    return "lg"


def build_week_template_vars(ctx: PdfExportContext) -> dict:
    """Kontext + berechnete Kachel-Positionen für Jinja2."""
    start_hour = ctx["start_hour"]
    end_hour = ctx["end_hour"]
    total_minutes = max(1, (end_hour - start_hour) * 60)
    lang = ctx["lang"]

    short_days = WOCHENTAGE_KURZ_I18N[lang]
    hours_range = list(range(start_hour, end_hour + 1))
    hour_span = max(1, end_hour - start_hour)
    axis_hours = [
        {
            "top_pct": round(100.0 * (h - start_hour) / hour_span, 4),
            "label": f"{h:02d}:00",
        }
        for h in hours_range
    ]
    slot_count = end_hour - start_hour
    half_slot_count = slot_count * 2

    # Pro Wochentag: Liste von Kacheln (top/height in % der Zeitskala)
    columns: list[dict] = []
    for day_idx, day_key in enumerate(WOCHENTAGE):
        # Stabile Rendering-Reihenfolge: aufsteigend nach Startzeit,
        # damit Overlaps deterministisch gestapelt werden.
        day_acts = [a for a in ctx["activities"] if a.get("day") == day_key]
        day_acts.sort(key=lambda a: str(a.get("start", "")))

        blocks: list[dict] = []
        for act in day_acts:
            try:
                sh, sm = map(int, act["start"].split(":"))
                eh, em = map(int, act["end"].split(":"))
            except (KeyError, ValueError):
                continue

            s_min = sh * 60 + sm
            e_min = eh * 60 + em
            duration = e_min - s_min
            if duration <= 0:
                continue

            s_clamped = max(s_min, start_hour * 60)
            e_clamped = min(e_min, end_hour * 60)
            if s_clamped >= e_clamped:
                continue

            dur_min = int(e_clamped - s_clamped)
            offset_min = s_clamped - start_hour * 60
            top_pct = 100.0 * offset_min / total_minutes
            h_pct = 100.0 * (e_clamped - s_clamped) / total_minutes

            # Farbe immer validieren (Fallback statt ValueError in get_text_color).
            color_hex = validate_color(str(act.get("color", "") or ""))
            note_s = str(act.get("note", "") or "").strip()
            ht_px_equiv = float(dur_min) * PX_PER_MIN
            want_note = bool(note_s) and inline_note_fits_block_height(ht_px_equiv)
            tier = _size_tier(dur_min, h_pct)

            blocks.append(
                {
                    "name": act["name"],
                    "bg": color_hex,
                    "text_color": get_text_color(color_hex),
                    "note_color": get_secondary_text_color(color_hex),
                    "start_str": minutes_to_hhmm(s_clamped),
                    "note": note_s,
                    "show_note": want_note and tier != "xs",
                    "top_pct": round(top_pct, 4),
                    "height_pct": round(h_pct, 4),
                    "dur_min": dur_min,
                    "show_name": dur_min >= MIN_MINUTES_FOR_NAME,
                    "show_corner": ctx["show_block_times"] and dur_min >= 12,
                    "size_tier": tier,
                }
            )
        columns.append(
            {
                "day_label": short_days[day_idx],
                "weekday_index": day_idx,
                "blocks": blocks,
            }
        )

    pn = ctx["plan_note"].strip()
    return {
        "title": ctx["title"],
        "plan_note": _plan_note_display(ctx["plan_note"]) if pn else "",
        "has_plan_note": bool(pn),
        "lang": lang,
        "footer": t("pdf_footer", lang),
        "start_hour": start_hour,
        "end_hour": end_hour,
        "total_minutes": total_minutes,
        "hours_range": hours_range,
        "axis_hours": axis_hours,
        "slot_count": slot_count,
        "half_slot_count": half_slot_count,
        "columns": columns,
        "show_axis_times": ctx["show_axis_times"],
        "show_block_times": ctx["show_block_times"],
        "continuous_horizontal_grid": ctx["continuous_horizontal_grid"],
        "paper_format": ctx["paper_format"],
        "pdf_style_theme": ctx.get("pdf_style_theme", "structured"),
    }
