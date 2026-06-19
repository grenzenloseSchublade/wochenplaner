"""Browser LocalStorage Abstraktionsschicht via streamlit-js-eval.

Performance: Schreib-/Löschvorgänge nutzen einen **stabilen** Component-Key pro
Slot (nicht pro Aufruf einen neuen) und `want_output=False`. Dadurch entsteht
keine neue iframe-Instanz pro Save (kein „double rerun", kein iframe-Leak über
lange Sessions). Ein modulinterner Nonce im JS-Ausdruck stellt sicher, dass jeder
Aufruf trotzdem ausgeführt wird (das Frontend evaluiert nur bei geändertem
`js_expressions`) — Schreibsemantik wie zuvor, nur ohne den erzwungenen Rerun.
"""

import itertools
import json

from streamlit_js_eval import streamlit_js_eval

_PREFIX = "wochenplaner_"

# Modulinterner, prozessweiter Zähler: garantiert pro Aufruf einen anderen
# JS-Ausdruck, damit das Frontend (`new_value !== data_from_streamlit`) den
# Schreib-/Löschvorgang nicht als „unverändert" überspringt.
_write_seq = itertools.count(1)


def _key(name: str) -> str:
    return f"{_PREFIX}{name}"


def ls_save(name: str, data: str) -> None:
    """Write a value to browser LocalStorage (fire-and-forget, kein Rückkanal)."""
    safe = json.dumps(data)  # JSON-encode to safely embed in JS string
    n = next(_write_seq)
    streamlit_js_eval(
        js_expressions=(
            f"window.parent.localStorage.setItem('{_key(name)}', {safe}) /*{n}*/"
        ),
        key=f"ls_w_{name}",
        want_output=False,
    )


def ls_load(name: str) -> str | None:
    """Read a value from browser LocalStorage. Returns None on first render."""
    result = streamlit_js_eval(
        js_expressions=f"window.parent.localStorage.getItem('{_key(name)}')",
        key=f"ls_r_{name}",
    )
    if result is None or result == "null":
        return None
    return str(result)


def ls_delete(name: str) -> None:
    """Remove a key from browser LocalStorage (fire-and-forget, kein Rückkanal)."""
    n = next(_write_seq)
    streamlit_js_eval(
        js_expressions=(
            f"window.parent.localStorage.removeItem('{_key(name)}') /*{n}*/"
        ),
        key=f"ls_d_{name}",
        want_output=False,
    )
