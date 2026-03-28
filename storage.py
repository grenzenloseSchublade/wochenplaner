"""Browser LocalStorage Abstraktionsschicht via streamlit-js-eval."""

import json

from streamlit_js_eval import streamlit_js_eval

_PREFIX = "wochenplaner_"


def _key(name: str) -> str:
    return f"{_PREFIX}{name}"


def ls_save(name: str, data: str, st_key: str) -> None:
    """Write a value to browser LocalStorage (fire-and-forget)."""
    safe = json.dumps(data)  # JSON-encode to safely embed in JS string
    streamlit_js_eval(
        js_expressions=f"window.parent.localStorage.setItem('{_key(name)}', {safe})",
        key=f"ls_w_{st_key}",
    )


def ls_load(name: str, st_key: str) -> str | None:
    """Read a value from browser LocalStorage. Returns None on first render."""
    result = streamlit_js_eval(
        js_expressions=f"window.parent.localStorage.getItem('{_key(name)}')",
        key=f"ls_r_{st_key}",
    )
    if result is None or result == "null":
        return None
    return str(result)


def ls_delete(name: str, st_key: str) -> None:
    """Remove a key from browser LocalStorage."""
    streamlit_js_eval(
        js_expressions=f"window.parent.localStorage.removeItem('{_key(name)}')",
        key=f"ls_d_{st_key}",
    )
