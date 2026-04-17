"""
PDF Export für den Wochenplaner.
Erzeugt ein pixelgenaues DIN A4 (Querformat) oder DIN A5 (Querformat) PDF.
"""

import io
from collections.abc import Sequence

from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import A4, A5, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfdoc import PDFArray, PDFDictionary, PDFString
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from constants import WOCHENTAGE
from i18n import WOCHENTAGE_KURZ_I18N, Lang, t
from utils import Activity

# Mindestdauer in Minuten, ab der der Aktivitätsname im Block erscheint (nicht nur Ecke/Kurzform)
MIN_MINUTES_FOR_NAME = 18

BLOCK_PAD_PT = 3.0
CORNER_PAD_PT = 2.5
# Ab dieser Blockhöhe (pt) wird die Startzeit oben links gezeichnet (gleich Schwelle wie Mikro)
MIN_HEIGHT_FOR_CORNER_PT = 12.0
# Sehr flache Blöcke: nur eine Zeile, Priorität Name (Zeit steht im Raster)
MICRO_BLOCK_PT = 12.0

LABEL_PAD_MM = 1.0


def minutes_to_hhmm(total_minutes: int) -> str:
    """Minuten seit Mitternacht als HH:MM (für PDF-Ecke = sichtbarer Raster-Start)."""
    m = max(0, int(total_minutes)) % (24 * 60)
    return f"{m // 60:02d}:{m % 60:02d}"


def _hex_to_color(hex_str: str) -> Color:
    h = hex_str.lstrip("#")
    return Color(int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255)


def _text_color(hex_str: str) -> Color:
    from utils import get_text_color

    return HexColor(get_text_color(hex_str))


def _truncate_line(text: str, font: str, size: float, max_w: float) -> str:
    """Shorten a single line to fit *max_w*, appending '…' if needed."""
    if stringWidth(text, font, size) <= max_w:
        return text
    while len(text) > 1 and stringWidth(text + "…", font, size) > max_w:
        text = text[:-1]
    return text.rstrip() + "…"


def _wrap_text(
    text: str, font: str, size: float, max_w: float, max_lines: int
) -> list[str]:
    """Word-wrap *text* into at most *max_lines* lines of width *max_w*.

    The last line is truncated with '…' if the text still overflows.
    """
    if stringWidth(text, font, size) <= max_w:
        return [text]

    words = text.split()
    lines: list[str] = []
    current = ""

    for word in words:
        test = f"{current} {word}".strip()
        if stringWidth(test, font, size) <= max_w:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
            if len(lines) >= max_lines:
                break
    if current and len(lines) < max_lines:
        lines.append(current)

    if not lines:
        lines = [_truncate_line(text, font, size, max_w)]

    if len(lines) > max_lines:
        lines = lines[:max_lines]

    remaining_words = words[sum(len(ln.split()) for ln in lines) :]
    if remaining_words:
        lines[-1] = _truncate_line(lines[-1], font, size, max_w)

    for i, line in enumerate(lines):
        if stringWidth(line, font, size) > max_w:
            lines[i] = _truncate_line(line, font, size, max_w)

    return lines


def _draw_activity_text(
    c: Canvas,
    *,
    x: float,
    y: float,
    w: float,
    height: float,
    tc: Color,
    name: str,
    start_str: str,
    dur_min: int,
    max_text_w: float,
    show_block_times: bool = True,
) -> None:
    """Startzeit oben links, Name darunter im Restbereich vertikal zentriert; Clipping."""
    cx = x + w / 2
    pad = BLOCK_PAD_PT
    max_inner = max(0.0, height - 2 * pad)
    inner_top = y + height - pad
    inner_bottom = y + pad

    show_name = dur_min >= MIN_MINUTES_FOR_NAME
    corner_fs = max(4.5, min(5.5, height * 0.065))
    reserved_corner_est = corner_fs * 1.15 + CORNER_PAD_PT + 1.5
    # Ecke unabhängig vom Namensbudget; nur Platz für die Eckzeile selbst nötig
    show_corner = (
        height >= MIN_HEIGHT_FOR_CORNER_PT and max_inner >= reserved_corner_est
    )
    draw_corner = show_corner and show_block_times

    c.saveState()
    path = c.beginPath()
    path.rect(x, y, w, height)
    c.clipPath(path, stroke=0, fill=0)
    if max_inner < 5.0:
        c.setFont("Helvetica-Bold", 4.5)
        c.setFillColor(tc)
        c.drawCentredString(
            cx,
            y + height / 2 - 1.5,
            _truncate_line(name, "Helvetica-Bold", 4.5, max_text_w),
        )
        c.restoreState()
        return

    if height < MICRO_BLOCK_PT:
        c.setFont("Helvetica-Bold", max(4.5, min(6.5, height * 0.45)))
        c.setFillColor(tc)
        fs0 = max(4.5, min(6.5, height * 0.45))
        c.drawCentredString(
            cx,
            y + height / 2 - fs0 * 0.35,
            _truncate_line(name, "Helvetica-Bold", fs0, max_text_w),
        )
        c.restoreState()
        return

    reserved_corner = (
        corner_fs * 1.15 + CORNER_PAD_PT + 1.5 if draw_corner else 0.0
    )

    fs = max(5.0, min(7.5, height * 0.2))
    name_lines: list[str] = []

    for _ in range(28):
        lh = fs * 1.18
        title_zone_top = inner_top - reserved_corner
        zone_h = max(0.0, title_zone_top - inner_bottom)
        avail_for_names = zone_h - 2.0
        max_lines = max(1, min(5, int(avail_for_names / lh))) if show_name else 0
        if show_name and max_lines > 0:
            name_lines = _wrap_text(name, "Helvetica-Bold", fs, max_text_w, max_lines)
        else:
            name_lines = []

        content_h = len(name_lines) * lh
        if content_h <= avail_for_names or (fs <= 4.35 and max_lines <= 1):
            break
        if max_lines > 1:
            name_lines = _wrap_text(
                name, "Helvetica-Bold", fs, max_text_w, max_lines - 1
            )
            content_h = len(name_lines) * lh
            if content_h <= avail_for_names:
                break
        fs = max(4.35, fs - 0.3)

    lh = fs * 1.18
    title_zone_top = inner_top - reserved_corner
    zone_h = max(0.0, title_zone_top - inner_bottom)
    content_h = len(name_lines) * lh if name_lines else 0.0

    while name_lines and len(name_lines) * lh > zone_h + 0.5 and len(name_lines) > 1:
        name_lines = _wrap_text(
            name, "Helvetica-Bold", fs, max_text_w, len(name_lines) - 1
        )
    content_h = len(name_lines) * lh if name_lines else 0.0
    if name_lines and content_h > zone_h + 0.5:
        name_lines = [_truncate_line(name, "Helvetica-Bold", fs, max_text_w)]
        content_h = lh

    if draw_corner:
        c.setFont("Helvetica-Bold", corner_fs)
        c.setFillColor(tc)
        time_baseline = inner_top - corner_fs * 0.78
        c.drawString(x + CORNER_PAD_PT, time_baseline, start_str)

    if show_name and name_lines:
        safe_content_h = min(content_h, max(0.0, zone_h))
        first_baseline = title_zone_top - (zone_h - safe_content_h) / 2 - fs * 0.72
        last_baseline = first_baseline - (len(name_lines) - 1) * lh
        if last_baseline < inner_bottom + 1.0 or zone_h < fs:
            nfs = max(4.35, min(fs, 6.5))
            c.setFont("Helvetica-Bold", nfs)
            c.setFillColor(tc)
            c.drawCentredString(
                cx,
                y + height / 2 - nfs * 0.35,
                _truncate_line(name, "Helvetica-Bold", nfs, max_text_w),
            )
            c.restoreState()
            return
        cur = first_baseline
        for line in name_lines:
            c.setFont("Helvetica-Bold", fs)
            c.setFillColor(tc)
            c.drawCentredString(cx, cur, line)
            cur -= lh
    elif not show_name:
        nfs = max(4.5, fs - 0.5)
        c.setFont("Helvetica-Bold", nfs)
        c.setFillColor(tc)
        c.drawCentredString(
            cx,
            y + height / 2 - nfs * 0.35,
            _truncate_line(name, "Helvetica-Bold", nfs, max_text_w),
        )

    c.restoreState()


def _draw_horizontal_time_raster(
    c: Canvas,
    *,
    grid_x: float,
    grid_y: float,
    grid_w: float,
    grid_h: float,
    start_hour: int,
    end_hour: int,
    pt_per_min: float,
) -> None:
    """Volle und halbe Stunden als waagerechte Linien über die Rasterbreite."""
    for h in range(start_hour, end_hour + 1):
        y = grid_y + grid_h - (h - start_hour) * 60 * pt_per_min

        c.setStrokeColor(HexColor("#CCCCCC"))
        c.setLineWidth(0.4)
        c.line(grid_x, y, grid_x + grid_w, y)

        if h < end_hour:
            yh = y - 30 * pt_per_min
            c.setStrokeColor(HexColor("#E5E5E5"))
            c.setLineWidth(0.25)
            c.setDash(2, 3)
            c.line(grid_x, yh, grid_x + grid_w, yh)
            c.setDash()


def _draw_axis_time_labels(
    c: Canvas,
    *,
    grid_x: float,
    label_x_right: float,
    grid_y: float,
    grid_h: float,
    start_hour: int,
    end_hour: int,
    pt_per_min: float,
) -> None:
    """Stunden-Zahlen links und rechts am Raster (keine Halbstunden-Labels)."""
    for h in range(start_hour, end_hour + 1):
        y = grid_y + grid_h - (h - start_hour) * 60 * pt_per_min
        c.setFillColor(HexColor("#888888"))
        c.setFont("Helvetica", 5.5)
        c.drawRightString(grid_x - LABEL_PAD_MM, y - 1.5, f"{h:02d}:00")
        c.drawString(label_x_right, y - 1.5, f"{h:02d}:00")


def generate_pdf(
    activities: Sequence[Activity],
    paper_format: str = "A4",
    start_hour: int = 6,
    end_hour: int = 22,
    title: str = "Wochenplan",
    lang: Lang = "de",
    plan_note: str = "",
    *,
    show_axis_times: bool = True,
    show_block_times: bool = True,
    continuous_horizontal_grid: bool = False,
) -> bytes:
    page_size = landscape(A4) if paper_format == "A4" else landscape(A5)
    page_w, page_h = page_size

    # ── Layout-Konstanten ────────────────────────────────────────────────────
    mg_l, mg_r, mg_t, mg_b = 12 * mm, 8 * mm, 8 * mm, 8 * mm
    header_h = 10 * mm  # Tagesheader
    title_h = 7 * mm  # Titelzeile
    time_w_l = 9 * mm
    time_w_r = 9 * mm
    footer_h = 4 * mm

    plan_note_stripped = plan_note.strip()
    subtitle_h = 4 * mm if plan_note_stripped else 0

    grid_x = mg_l + time_w_l
    grid_y = mg_b + footer_h
    grid_w = page_w - mg_l - mg_r - time_w_l - time_w_r
    grid_h = page_h - mg_t - mg_b - header_h - title_h - subtitle_h - footer_h

    col_w = grid_w / 7
    total_minutes = (end_hour - start_hour) * 60
    pt_per_min = grid_h / total_minutes

    buf = io.BytesIO()
    c = Canvas(buf, pagesize=page_size)
    c.setTitle(title)
    c.setAuthor("Wochenplaner")
    c.setSubject("Wochenplan / Weekly Schedule")
    c.setCreator("Wochenplaner – github.com/grenzenloseSchublade/wochenplaner")

    # ── Hintergrund ──────────────────────────────────────────────────────────
    c.setFillColor(HexColor("#FAFAFA"))
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    # ── Titel ────────────────────────────────────────────────────────────────
    title_y = grid_y + grid_h + header_h + subtitle_h
    c.setFillColor(HexColor("#2C3E50"))
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(page_w / 2, title_y + 1.5 * mm, title)

    # ── Plan-Notiz (Untertitel) ──────────────────────────────────────────────
    if plan_note_stripped:
        note_y = grid_y + grid_h + header_h
        c.setFillColor(HexColor("#888888"))
        c.setFont("Helvetica", 7)
        display_note = (
            plan_note_stripped[:90] + "…"
            if len(plan_note_stripped) > 90
            else plan_note_stripped
        )
        c.drawCentredString(page_w / 2, note_y + 0.8 * mm, display_note)

    # ── Tagesheader ──────────────────────────────────────────────────────────
    header_y = grid_y + grid_h
    short_days = WOCHENTAGE_KURZ_I18N[lang]
    for i, tag in enumerate(short_days):
        x = grid_x + i * col_w
        bg = HexColor("#4472C4") if i < 5 else HexColor("#2E86AB")
        c.setFillColor(bg)
        c.rect(x, header_y, col_w, header_h, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(x + col_w / 2, header_y + header_h / 2 - 1.5, tag)

    # ── Spalten-Hintergrund (abwechselnd) ────────────────────────────────────
    alt_colors = ["#FFFFFF", "#F8F9FF"]
    for i in range(7):
        c.setFillColor(HexColor(alt_colors[i % 2]))
        c.rect(grid_x + i * col_w, grid_y, col_w, grid_h, fill=1, stroke=0)

    # ── Waagerechtes Zeit-Raster + ggf. Achsenbeschriftung ──────────────────
    label_x_right = grid_x + grid_w + LABEL_PAD_MM
    if continuous_horizontal_grid:
        if show_axis_times:
            _draw_axis_time_labels(
                c,
                grid_x=grid_x,
                label_x_right=label_x_right,
                grid_y=grid_y,
                grid_h=grid_h,
                start_hour=start_hour,
                end_hour=end_hour,
                pt_per_min=pt_per_min,
            )
    else:
        _draw_horizontal_time_raster(
            c,
            grid_x=grid_x,
            grid_y=grid_y,
            grid_w=grid_w,
            grid_h=grid_h,
            start_hour=start_hour,
            end_hour=end_hour,
            pt_per_min=pt_per_min,
        )
        if show_axis_times:
            _draw_axis_time_labels(
                c,
                grid_x=grid_x,
                label_x_right=label_x_right,
                grid_y=grid_y,
                grid_h=grid_h,
                start_hour=start_hour,
                end_hour=end_hour,
                pt_per_min=pt_per_min,
            )

    # ── Spaltentrennlinien ───────────────────────────────────────────────────
    c.setStrokeColor(HexColor("#CCCCCC"))
    c.setLineWidth(0.5)
    for i in range(8):
        x = grid_x + i * col_w
        c.line(x, grid_y, x, grid_y + grid_h)

    # Äußerer Rahmen
    c.setStrokeColor(HexColor("#999999"))
    c.setLineWidth(0.8)
    c.rect(grid_x, grid_y, grid_w, grid_h, fill=0, stroke=1)

    # ── Aktivitätsblöcke ─────────────────────────────────────────────────────
    # Bei durchgängigem Raster: erst Flächen, dann Linien, dann Text — sonst
    # liegen die Zeitlinien über der Beschriftung.
    overlay_text_blocks: list[dict[str, object]] = []

    for act in activities:
        if act.get("day") not in WOCHENTAGE:
            continue
        try:
            sh, sm = map(int, act["start"].split(":"))
            eh, em = map(int, act["end"].split(":"))
        except (KeyError, ValueError):
            continue

        day_idx = WOCHENTAGE.index(act["day"])
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
        offset = s_clamped - start_hour * 60
        height = (e_clamped - s_clamped) * pt_per_min
        x = grid_x + day_idx * col_w + 1
        y = grid_y + grid_h - (offset + (e_clamped - s_clamped)) * pt_per_min
        w = col_w - 2

        color_hex = act.get("color", "#F3E5AB")
        c.setFillColor(_hex_to_color(color_hex))
        c.setStrokeColor(HexColor("#999999"))
        c.setLineWidth(0.4)
        c.roundRect(x, y, w, height, 2, fill=1, stroke=1)

        tc = _text_color(color_hex)
        name = act["name"]
        max_text_w = w - 4
        start_display = minutes_to_hhmm(s_clamped)

        if continuous_horizontal_grid:
            overlay_text_blocks.append(
                {
                    "x": x,
                    "y": y,
                    "w": w,
                    "height": height,
                    "tc": tc,
                    "name": name,
                    "start_str": start_display,
                    "dur_min": dur_min,
                    "max_text_w": max_text_w,
                    "note": act.get("note", "").strip(),
                }
            )
        else:
            _draw_activity_text(
                c,
                x=x,
                y=y,
                w=w,
                height=height,
                tc=tc,
                name=name,
                start_str=start_display,
                dur_min=dur_min,
                max_text_w=max_text_w,
                show_block_times=show_block_times,
            )

            note_text = act.get("note", "").strip()
            if note_text:
                ann_s = 10
                ann_x = x + w - ann_s - 1
                ann_y = y + height - ann_s - 1
                ann = PDFDictionary()
                ann["Type"] = "/Annot"
                ann["Subtype"] = "/Text"
                ann["Rect"] = PDFArray(
                    [ann_x, ann_y, ann_x + ann_s, ann_y + ann_s]
                )
                ann["Contents"] = PDFString(note_text)
                ann["T"] = PDFString(name)
                ann["Name"] = "/Comment"
                ann["Open"] = "false"
                ann["F"] = 4
                ann["C"] = PDFArray([1, 0.85, 0])
                c._addAnnotation(ann)

    if continuous_horizontal_grid:
        _draw_horizontal_time_raster(
            c,
            grid_x=grid_x,
            grid_y=grid_y,
            grid_w=grid_w,
            grid_h=grid_h,
            start_hour=start_hour,
            end_hour=end_hour,
            pt_per_min=pt_per_min,
        )
        for ob in overlay_text_blocks:
            _draw_activity_text(
                c,
                x=float(ob["x"]),
                y=float(ob["y"]),
                w=float(ob["w"]),
                height=float(ob["height"]),
                tc=ob["tc"],  # type: ignore[arg-type]
                name=str(ob["name"]),
                start_str=str(ob["start_str"]),
                dur_min=int(ob["dur_min"]),
                max_text_w=float(ob["max_text_w"]),
                show_block_times=show_block_times,
            )
            note_text = str(ob.get("note", "") or "")
            if note_text:
                ann_s = 10
                ox = float(ob["x"])
                oy = float(ob["y"])
                ow = float(ob["w"])
                oh = float(ob["height"])
                ann_x = ox + ow - ann_s - 1
                ann_y = oy + oh - ann_s - 1
                ann = PDFDictionary()
                ann["Type"] = "/Annot"
                ann["Subtype"] = "/Text"
                ann["Rect"] = PDFArray(
                    [ann_x, ann_y, ann_x + ann_s, ann_y + ann_s]
                )
                ann["Contents"] = PDFString(note_text)
                ann["T"] = PDFString(str(ob["name"]))
                ann["Name"] = "/Comment"
                ann["Open"] = "false"
                ann["F"] = 4
                ann["C"] = PDFArray([1, 0.85, 0])
                c._addAnnotation(ann)

    c.setFillColor(HexColor("#AAAAAA"))
    c.setFont("Helvetica", 5)
    c.drawRightString(page_w - mg_r, mg_b / 2, t("pdf_footer", lang))

    c.save()
    buf.seek(0)
    return buf.read()
