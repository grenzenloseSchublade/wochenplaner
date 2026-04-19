"""
Gemeinsamer Daten-Context für klassischen ReportLab-PDF-Export und HTML→PDF-Pfad.
Eine Quelle der Wahrheit – vermeidet Drift zwischen den Renderern.
"""

from collections.abc import Sequence
from typing import TypedDict

from i18n import Lang
from utils import Activity


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


def build_pdf_context(
    activities: Sequence[Activity],
    *,
    paper_format: str = "A4",
    start_hour: int = 6,
    end_hour: int = 22,
    title: str = "Wochenplan",
    lang: Lang = "de",
    plan_note: str = "",
    show_axis_times: bool = True,
    show_block_times: bool = True,
    continuous_horizontal_grid: bool = False,
) -> PdfExportContext:
    """Baut den Export-Context aus denselben Parametern wie bisher `generate_pdf`."""
    return PdfExportContext(
        activities=list(activities),
        paper_format=paper_format,
        start_hour=start_hour,
        end_hour=end_hour,
        title=title,
        lang=lang,
        plan_note=plan_note,
        show_axis_times=show_axis_times,
        show_block_times=show_block_times,
        continuous_horizontal_grid=continuous_horizontal_grid,
    )
