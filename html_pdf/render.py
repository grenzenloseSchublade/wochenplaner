"""HTML → PDF via WeasyPrint (browserlos, Cloud-tauglich).

WeasyPrint ist eine reine Python-Bibliothek (+ pango/cairo-Systembibliotheken)
und braucht **keinen** Browser. Das macht den Modern-PDF-Export auf der
Streamlit Community Cloud out-of-the-box lauffähig – die nötigen `apt`-Libs
liegen in ``packages.txt``, ein Browser-Download (~150 MB) entfällt.
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from pdf_colors import ALLOWED_COLOR_SCHEMES, DEFAULT_COLOR_SCHEME
from pdf_context import PdfExportContext

from .layout import build_week_template_vars

_PKG = Path(__file__).resolve().parent
_TEMPLATES = _PKG / "templates"
_STATIC = _PKG / "static"

ALLOWED_PAPER_FORMATS: frozenset[str] = frozenset({"A4", "A5"})
ALLOWED_PDF_THEMES: frozenset[str] = frozenset({"minimal", "structured", "balanced"})
DEFAULT_PDF_THEME = "balanced"

_WEASYPRINT_MISSING_MSG = (
    "WeasyPrint (oder seine Systembibliotheken pango/cairo) wurde nicht gefunden. "
    "Lokal: `uv sync` und die Pango/Cairo-Libs installieren (siehe README / "
    "packages.txt). Alternativ den Klassisch-Modus nutzen."
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
    """Rendert das Wochen-HTML (Jinja2) mit eingebettetem CSS-Bundle."""
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


def _normalize_color_scheme(scheme: str) -> str:
    """Validiert das Farbschema auf eine Whitelist."""
    val = str(scheme or "").strip().lower()
    if val not in ALLOWED_COLOR_SCHEMES:
        msg = (
            f"color_scheme muss einer von {sorted(ALLOWED_COLOR_SCHEMES)} sein, "
            f"erhalten: {scheme!r}"
        )
        raise ValueError(msg)
    return val


def _pdf_weasyprint(html: str) -> bytes:
    """Browserloses Rendering via WeasyPrint (pango/cairo, kein Browser).

    Seitenformat und -ränder kommen vollständig aus `@page` in print.css.
    """
    try:
        from weasyprint import HTML  # lazy: Import-/Lib-Fehler klar melden
    except Exception as exc:  # OSError (fehlende Libs) oder ImportError
        raise RuntimeError(_WEASYPRINT_MISSING_MSG) from exc
    # base_url, damit relative Ressourcen aufgelöst werden (Fonts liegen
    # ohnehin bereits als absolute file:-URIs im CSS-Bundle).
    base = _STATIC.resolve().as_uri() + "/"
    return HTML(string=html, base_url=base).write_pdf()


def render_html_pdf(ctx: PdfExportContext) -> bytes:
    """Modern-PDF: Jinja2 + CSS → WeasyPrint (browserlos)."""
    # Früh validieren: Fehlermeldung kommt so oder so vor dem Rendern.
    _normalize_paper_format(ctx["paper_format"])
    _normalize_pdf_theme(ctx.get("pdf_style_theme", DEFAULT_PDF_THEME))
    _normalize_color_scheme(ctx.get("color_scheme", DEFAULT_COLOR_SCHEME))
    return _pdf_weasyprint(build_week_html(ctx))
