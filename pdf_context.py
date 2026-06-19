"""
Gemeinsamer Daten-Context für klassischen ReportLab-PDF-Export und HTML→PDF-Pfad.
Eine Quelle der Wahrheit – vermeidet Drift zwischen den Renderern.
"""

from collections.abc import Sequence
from typing import Literal, TypedDict

from i18n import Lang
from pdf_colors import (
    DEFAULT_COLOR_SCHEME,
    ColorScheme,
    build_color_overrides,
    plan_mono_hue,
)
from utils import Activity, default_plan_title

PdfStyleTheme = Literal["minimal", "structured", "balanced"]
DEFAULT_PDF_STYLE_THEME: PdfStyleTheme = "balanced"


class PdfExportContext(TypedDict):
    """Parameter für generate_pdf / render_html_pdf (identische Semantik)."""

    activities: list[Activity]
    paper_format: str  # "A4" | "A5"
    start_hour: int
    end_hour: int
    title: str
    lang: Lang
    plan_note: str
    show_axis_times: bool
    show_block_times: bool
    continuous_horizontal_grid: bool
    # Nur Modern-PDF: visuelle Variante des Kalender-Chromes.
    pdf_style_theme: PdfStyleTheme
    # Farbschema (beide Renderer): "color" | "grayscale" | "monochrome".
    color_scheme: ColorScheme
    # Vorab berechnete Kachelfarben pro Aktivitätsname (leer bei "color").
    # Eine Quelle der Wahrheit für klassischen und modernen Renderer.
    color_overrides: dict[str, str]
    # Plan-Farbton (0..1) für "monochrome": zirkulärer Mittelwert der
    # Aktivitätsfarben (Blau-Fallback bei farblosen Plänen). Speist Kacheln
    # *und* Chrome in beiden Renderern. Bei anderen Schemata bedeutungslos.
    mono_hue: float


def build_pdf_context(
    activities: Sequence[Activity],
    *,
    paper_format: str = "A4",
    start_hour: int = 6,
    end_hour: int = 22,
    title: str | None = None,
    lang: Lang = "de",
    plan_note: str = "",
    show_axis_times: bool = True,
    show_block_times: bool = True,
    continuous_horizontal_grid: bool = True,
    pdf_style_theme: PdfStyleTheme = DEFAULT_PDF_STYLE_THEME,
    color_scheme: ColorScheme = DEFAULT_COLOR_SCHEME,
) -> PdfExportContext:
    """Baut den Export-Context aus denselben Parametern wie bisher `generate_pdf`."""
    resolved_title = default_plan_title() if title is None else title
    acts = list(activities)
    return PdfExportContext(
        activities=acts,
        paper_format=paper_format,
        start_hour=start_hour,
        end_hour=end_hour,
        title=resolved_title,
        lang=lang,
        plan_note=plan_note,
        show_axis_times=show_axis_times,
        show_block_times=show_block_times,
        continuous_horizontal_grid=continuous_horizontal_grid,
        pdf_style_theme=pdf_style_theme,
        color_scheme=color_scheme,
        color_overrides=build_color_overrides(acts, color_scheme),
        mono_hue=plan_mono_hue(acts),
    )
