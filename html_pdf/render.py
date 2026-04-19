"""HTML → PDF: Playwright (headless Chromium)."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright

from pdf_context import PdfExportContext

from .layout import build_week_template_vars

_PKG = Path(__file__).resolve().parent
_TEMPLATES = _PKG / "templates"
_STATIC = _PKG / "static"


def _css_bundle_for_pdf() -> str:
    """Eingebettetes Stylesheet inkl. `file:`-URLs für Roboto."""
    fonts_dir = (_STATIC / "fonts").resolve().as_uri() + "/"
    typo = (_STATIC / "typography.css").read_text(encoding="utf-8")
    typo = typo.replace('url("fonts/', f'url("{fonts_dir}')
    tokens = (_STATIC / "tokens.css").read_text(encoding="utf-8")
    raw_print = (_STATIC / "print.css").read_text(encoding="utf-8")
    lines = raw_print.splitlines()
    rest = "\n".join(ln for ln in lines if not ln.strip().startswith("@import"))
    return f"{tokens}\n{typo}\n{rest}"


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


def _pdf_playwright(html: str, paper_format: str) -> bytes:
    fmt = paper_format.strip().upper()
    paper_size = "A4" if fmt == "A4" else "A5"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.set_content(html, wait_until="load")
            page.evaluate("() => document.fonts.ready")
            return page.pdf(
                format=paper_size,
                landscape=True,
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
        finally:
            browser.close()


def render_html_pdf(ctx: PdfExportContext) -> bytes:
    """Modern-PDF: Jinja2 + CSS, Rendering mit Playwright/Chromium."""
    html = build_week_html(ctx)
    return _pdf_playwright(html, ctx["paper_format"])
