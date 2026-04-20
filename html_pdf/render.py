"""HTML → PDF: Playwright (headless Chromium)."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from pdf_context import PdfExportContext

from .layout import build_week_template_vars

_PKG = Path(__file__).resolve().parent
_TEMPLATES = _PKG / "templates"
_STATIC = _PKG / "static"

ALLOWED_PAPER_FORMATS: frozenset[str] = frozenset({"A4", "A5"})
ALLOWED_PDF_THEMES: frozenset[str] = frozenset({"minimal", "structured", "balanced"})
DEFAULT_PDF_THEME = "balanced"

_CHROMIUM_MISSING_MSG = (
    "Chromium für Playwright wurde nicht gefunden. "
    "Lokal einmalig ausführen: `uv run playwright install chromium`. "
    "Auf Streamlit Community Cloud funktioniert Modern-PDF meist nicht – "
    "dort bitte den Klassisch-Modus nutzen (siehe README)."
)


def _css_bundle_for_pdf() -> str:
    """Eingebettetes Stylesheet inkl. `file:`-URLs für Roboto.

    Reihenfolge: tokens (Basis-Variablen) → typography (Fonts) →
    print (Layout) → themes (Variant-Token-Overrides). Themes kommen
    zuletzt, damit `.theme--X` Basis-Tokens überschreiben kann.
    """
    fonts_dir = (_STATIC / "fonts").resolve().as_uri() + "/"
    typo = (_STATIC / "typography.css").read_text(encoding="utf-8")
    typo = typo.replace('url("fonts/', f'url("{fonts_dir}')
    tokens = (_STATIC / "tokens.css").read_text(encoding="utf-8")
    raw_print = (_STATIC / "print.css").read_text(encoding="utf-8")
    lines = raw_print.splitlines()
    rest = "\n".join(ln for ln in lines if not ln.strip().startswith("@import"))
    themes = (_STATIC / "themes.css").read_text(encoding="utf-8")
    return f"{tokens}\n{typo}\n{rest}\n{themes}"


def build_week_html(ctx: PdfExportContext) -> str:
    """Rendert das Wochen-HTML für Playwright."""
    data = build_week_template_vars(ctx)
    data["css_bundle"] = _css_bundle_for_pdf()
    env = Environment(
        loader=FileSystemLoader(_TEMPLATES),
        autoescape=select_autoescape(["html", "xml"]),
    )
    tpl = env.get_template("week.html")
    return tpl.render(**data)


def _normalize_paper_format(paper_format: str) -> str:
    """Validiert `paper_format` auf eine Whitelist (`A4`/`A5`)."""
    fmt = str(paper_format or "").strip().upper()
    if fmt not in ALLOWED_PAPER_FORMATS:
        msg = (
            f"paper_format muss einer von {sorted(ALLOWED_PAPER_FORMATS)} sein, "
            f"erhalten: {paper_format!r}"
        )
        raise ValueError(msg)
    return fmt


def _normalize_pdf_theme(theme: str) -> str:
    """Validiert Modern-PDF-Theme auf eine Whitelist."""
    val = str(theme or "").strip().lower()
    if val not in ALLOWED_PDF_THEMES:
        msg = (
            f"pdf_style_theme muss einer von {sorted(ALLOWED_PDF_THEMES)} sein, "
            f"erhalten: {theme!r}"
        )
        raise ValueError(msg)
    return val


"""
Papierformate in Millimeter (quer / landscape). Werden genutzt, um den
Browser-Viewport exakt auf die spätere Druckseite zu setzen – sonst
layoutet Chromium in seinem Default-Viewport (1280×720 px ≈ 338×190 mm),
und `100vh`/`prefer_css_page_size=True` geraten auseinander → mehrseitige
Exporte trotz passender CSS-Maße.
"""
_PAPER_MM_LANDSCAPE: dict[str, tuple[float, float]] = {
    "A4": (297.0, 210.0),
    "A5": (210.0, 148.0),
}
_MM_PER_INCH: float = 25.4
_BROWSER_DPI: float = 96.0


def _viewport_px_for(paper_format: str) -> dict[str, int]:
    """Viewport-Größe (CSS-Pixel @ 96dpi) für `landscape=True` Ausgabe."""
    w_mm, h_mm = _PAPER_MM_LANDSCAPE[paper_format]
    return {
        "width": round(w_mm * _BROWSER_DPI / _MM_PER_INCH),
        "height": round(h_mm * _BROWSER_DPI / _MM_PER_INCH),
    }


def _pdf_playwright(html: str, paper_format: str) -> bytes:
    paper_size = _normalize_paper_format(paper_format)
    viewport = _viewport_px_for(paper_size)
    with sync_playwright() as p:
        # Preflight: Chromium-Start. Schlägt mit klarer Meldung fehl,
        # wenn das Browser-Binary nicht installiert ist (häufig auf
        # Streamlit Community Cloud).
        try:
            browser = p.chromium.launch(headless=True)
        except PlaywrightError as exc:
            raise RuntimeError(_CHROMIUM_MISSING_MSG) from exc

        try:
            # Viewport auf Page-Size → `100vh`, `min-height: 100vh` und
            # `.page`-Padding rechnen in exakt derselben Geometrie, die
            # später als PDF-Seite ausgegeben wird.
            page = browser.new_page(viewport=viewport)
            page.set_content(html, wait_until="load")
            page.evaluate("() => document.fonts.ready")
            # Margins werden ausschließlich in print.css (@page) definiert;
            # `margin=0` hier hält Chromium davon ab, Default-Ränder einzuziehen.
            return page.pdf(
                format=paper_size,
                landscape=True,
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                prefer_css_page_size=True,
            )
        finally:
            browser.close()


def render_html_pdf(ctx: PdfExportContext) -> bytes:
    """Modern-PDF: Jinja2 + CSS, Rendering mit Playwright/Chromium."""
    # Früh validieren: Fehlermeldung kommt so oder so vor dem Browser-Start.
    _normalize_paper_format(ctx["paper_format"])
    _normalize_pdf_theme(ctx.get("pdf_style_theme", DEFAULT_PDF_THEME))
    html = build_week_html(ctx)
    return _pdf_playwright(html, ctx["paper_format"])
