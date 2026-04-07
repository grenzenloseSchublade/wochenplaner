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
from reportlab.pdfgen import canvas

from constants import WOCHENTAGE
from i18n import WOCHENTAGE_KURZ_I18N, Lang, t
from utils import Activity


def _hex_to_color(hex_str: str) -> Color:
    h = hex_str.lstrip("#")
    return Color(int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255)


def _text_color(hex_str: str) -> Color:
    from utils import get_text_color

    return HexColor(get_text_color(hex_str))


def _pdf_escape(text: str) -> str:
    """Escape special characters for PDF string literals."""
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


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

    remaining_words = words[sum(len(l.split()) for l in lines) :]
    if remaining_words:
        lines[-1] = _truncate_line(lines[-1], font, size, max_w)

    for i, line in enumerate(lines):
        if stringWidth(line, font, size) > max_w:
            lines[i] = _truncate_line(line, font, size, max_w)

    return lines


def generate_pdf(
    activities: Sequence[Activity],
    paper_format: str = "A4",
    start_hour: int = 6,
    end_hour: int = 22,
    title: str = "Wochenplan",
    lang: Lang = "de",
    plan_note: str = "",
) -> bytes:
    page_size = landscape(A4) if paper_format == "A4" else landscape(A5)
    page_w, page_h = page_size

    # ── Layout-Konstanten ────────────────────────────────────────────────────
    mg_l, mg_r, mg_t, mg_b = 12 * mm, 8 * mm, 8 * mm, 8 * mm
    header_h = 10 * mm  # Tagesheader
    title_h = 7 * mm  # Titelzeile
    time_w = 9 * mm  # Zeitspalte
    footer_h = 4 * mm

    plan_note_stripped = plan_note.strip()
    subtitle_h = 4 * mm if plan_note_stripped else 0

    grid_x = mg_l + time_w
    grid_y = mg_b + footer_h
    grid_w = page_w - mg_l - mg_r - time_w
    grid_h = page_h - mg_t - mg_b - header_h - title_h - subtitle_h - footer_h

    col_w = grid_w / 7
    total_minutes = (end_hour - start_hour) * 60
    pt_per_min = grid_h / total_minutes

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=page_size)
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

    # ── Gitterlinien ─────────────────────────────────────────────────────────
    for h in range(start_hour, end_hour + 1):
        y = grid_y + grid_h - (h - start_hour) * 60 * pt_per_min

        # Vollstunden
        c.setStrokeColor(HexColor("#CCCCCC"))
        c.setLineWidth(0.4)
        c.line(grid_x, y, grid_x + grid_w, y)

        # Zeit-Label
        c.setFillColor(HexColor("#888888"))
        c.setFont("Helvetica", 5.5)
        c.drawRightString(grid_x - 1 * mm, y - 1.5, f"{h:02d}:00")

        # Halbstunde (gestrichelt)
        if h < end_hour:
            yh = y - 30 * pt_per_min
            c.setStrokeColor(HexColor("#E5E5E5"))
            c.setLineWidth(0.25)
            c.setDash(2, 3)
            c.line(grid_x, yh, grid_x + grid_w, yh)
            c.setDash()

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

        # Clamp to grid
        s_clamped = max(s_min, start_hour * 60)
        e_clamped = min(e_min, end_hour * 60)
        if s_clamped >= e_clamped:
            continue

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

        # Text
        tc = _text_color(color_hex)
        c.setFillColor(tc)

        name = act["name"]
        dh, dm = duration // 60, duration % 60
        dur_str = f"{dh}h {dm}min" if dh and dm else f"{dh}h" if dh else f"{dm}min"

        max_text_w = w - 4
        cx = x + w / 2

        if height >= 18:
            fs = min(7.5, height * 0.28)
            fs = max(fs, 5.5)
            lh = fs * 1.25
            show_dur = height >= 28
            dur_fs = max(fs - 1, 4.5)
            dur_h = (dur_fs * 1.3) if show_dur else 0
            avail_name_h = height - 6 - dur_h
            max_lines = max(1, int(avail_name_h / lh))

            c.setFont("Helvetica-Bold", fs)
            name_lines = _wrap_text(name, "Helvetica-Bold", fs, max_text_w, max_lines)

            block_h = len(name_lines) * lh + dur_h
            top_y = y + height / 2 + block_h / 2 - fs * 0.2

            for li, line in enumerate(name_lines):
                c.setFont("Helvetica-Bold", fs)
                c.setFillColor(tc)
                c.drawCentredString(cx, top_y - li * lh, line)

            if show_dur:
                c.setFont("Helvetica", dur_fs)
                c.setFillColor(tc)
                c.drawCentredString(
                    cx, top_y - len(name_lines) * lh - dur_fs * 0.15, dur_str
                )
        else:
            c.setFont("Helvetica-Bold", 5)
            draw_name = _truncate_line(name, "Helvetica-Bold", 5, max_text_w)
            c.drawCentredString(cx, y + height / 2 - 2, draw_name)

        # ── PDF Text Annotation (Sticky Note) for activity notes ─────────
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
            ann["F"] = 4  # Print flag
            ann["C"] = PDFArray([1, 0.85, 0])
            c._addAnnotation(ann)

    # ── Footer ───────────────────────────────────────────────────────────────
    c.setFillColor(HexColor("#AAAAAA"))
    c.setFont("Helvetica", 5)
    c.drawRightString(page_w - mg_r, mg_b / 2, t("pdf_footer", lang))

    c.save()
    buf.seek(0)
    return buf.read()
