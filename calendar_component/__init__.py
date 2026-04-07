"""Bidirectional Streamlit component for the weekly calendar."""

from pathlib import Path

import streamlit.components.v1 as components

_FRONTEND_DIR = Path(__file__).parent / "frontend"
_component_func = components.declare_component(
    "calendar_component", path=str(_FRONTEND_DIR)
)


def calendar_component(
    calendar_html: str, height: int, key: str | None = None
) -> dict | None:
    """Render the calendar and return interaction events.

    Returns ``{"action": "edit", "id": "<activity-id>"}`` when the user
    clicks *Edit* on an activity block, or ``None`` otherwise.
    """
    result = _component_func(
        calendar_html=calendar_html, height=height, key=key, default=None
    )
    if isinstance(result, dict):
        return result
    return None
