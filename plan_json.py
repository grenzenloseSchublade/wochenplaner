"""Plan-Dokument: einheitliches JSON (Export, Datei, LocalStorage)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from constants import DATA_FILE
from utils import Activity, validate_activity

PLAN_FORMAT = "wochenplaner"
PLAN_VERSION = 1

MAX_JSON_UPLOAD_BYTES = 2_000_000


class PlanParseError(ValueError):
    """Ungültige Plan-JSON-Struktur (Import)."""


@dataclass(frozen=True)
class DiskPlanLoad:
    """Ergebnis beim Laden von data/wochenplan.json (Liste oder Objekt)."""

    activities: list[Activity]
    title_from_file: bool
    title: str
    note_from_file: bool
    plan_note: str


def build_plan_document(
    activities: list[Activity],
    title: str,
    plan_note: str,
) -> dict[str, Any]:
    return {
        "format": PLAN_FORMAT,
        "version": PLAN_VERSION,
        "title": title,
        "plan_note": plan_note,
        "activities": activities,
    }


def plan_document_json(activities: list[Activity], title: str, plan_note: str) -> str:
    doc = build_plan_document(activities, title, plan_note)
    return json.dumps(doc, ensure_ascii=False, indent=2)


def _title_from_dict(data: dict[str, Any]) -> tuple[bool, str]:
    if "title" not in data and "plan_title" not in data:
        return False, ""
    raw = data.get("title")
    if raw is None:
        raw = data.get("plan_title")
    return True, "" if raw is None else str(raw).strip()


def _plan_note_from_dict(data: dict[str, Any]) -> tuple[bool, str]:
    if "plan_note" not in data:
        return False, ""
    raw = data.get("plan_note")
    return True, "" if raw is None else str(raw).strip()


def load_plan_from_file(fp: Path | None = None) -> DiskPlanLoad:
    """Lädt Aktivitäten und optional Titel/Plan-Notiz aus der Datei (Legacy-Liste oder Objekt)."""
    fp = fp or DATA_FILE
    if not fp.exists():
        return DiskPlanLoad([], False, "", False, "")

    try:
        data = json.loads(fp.read_text("utf-8"))
    except (json.JSONDecodeError, OSError):
        return DiskPlanLoad([], False, "", False, "")

    if isinstance(data, list):
        acts = [item for item in data if validate_activity(item)]
        return DiskPlanLoad(acts, False, "", False, "")

    if isinstance(data, dict):
        raw_acts = data.get("activities")
        if not isinstance(raw_acts, list):
            return DiskPlanLoad([], False, "", False, "")
        acts = [item for item in raw_acts if validate_activity(item)]
        tf, title = _title_from_dict(data)
        nf, note = _plan_note_from_dict(data)
        return DiskPlanLoad(acts, tf, title, nf, note)

    return DiskPlanLoad([], False, "", False, "")


def parse_plan_import(raw: Any) -> tuple[list[Activity], str | None, str | None]:
    """
    Import aus Upload: Legacy-Liste oder Objekt mit activities.

    Gibt (activities, title_update, plan_note_update) zurück.
    None bei title/plan_note bedeutet: Session-Felder nicht ändern (nur bei Legacy-Liste).
    """
    if isinstance(raw, list):
        acts = [item for item in raw if validate_activity(item)]
        return acts, None, None

    if not isinstance(raw, dict):
        raise PlanParseError("bad_type")

    if "activities" not in raw or not isinstance(raw["activities"], list):
        raise PlanParseError("missing_activities")

    acts = [item for item in raw["activities"] if validate_activity(item)]

    tit: str | None
    if "title" in raw or "plan_title" in raw:
        tr = raw.get("title")
        if tr is None:
            tr = raw.get("plan_title")
        tit = "" if tr is None else str(tr).strip()
    else:
        tit = None

    pno: str | None
    if "plan_note" in raw:
        pn = raw.get("plan_note")
        pno = "" if pn is None else str(pn).strip()
    else:
        pno = None

    return acts, tit, pno


def activities_from_local_storage_json(ls_data: str) -> list[Activity] | None:
    """Parst gespeicherte Aktivitäten (Legacy-Liste oder vollständiges Plan-Objekt).

    Gibt eine Liste zurück (ggf. leer) oder None, wenn das JSON kein unterstütztes
    Format hat.
    """
    try:
        raw = json.loads(ls_data)
    except (json.JSONDecodeError, TypeError):
        return None

    if isinstance(raw, list):
        return [item for item in raw if validate_activity(item)]

    if isinstance(raw, dict) and isinstance(raw.get("activities"), list):
        return [item for item in raw["activities"] if validate_activity(item)]

    return None
