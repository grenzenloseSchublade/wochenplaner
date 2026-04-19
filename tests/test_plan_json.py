"""Tests für Plan-JSON (Import/Datei-Format)."""

from plan_json import (
    PlanParseError,
    build_plan_document,
    load_plan_from_file,
    parse_plan_import,
)
from utils import validate_activity


def test_build_plan_document_shape() -> None:
    doc = build_plan_document([], "Titel", "Hinweis")
    assert doc["format"] == "wochenplaner"
    assert doc["version"] == 1
    assert doc["title"] == "Titel"
    assert doc["plan_note"] == "Hinweis"
    assert doc["activities"] == []


def test_parse_plan_import_legacy_list() -> None:
    raw = [
        {
            "id": "x",
            "name": "A",
            "day": "Montag",
            "start": "10:00",
            "end": "11:00",
            "color": "#fff",
        }
    ]
    acts, tit, pn = parse_plan_import(raw)
    assert len(acts) == 1 and validate_activity(acts[0])
    assert tit is None and pn is None


def test_parse_plan_import_dict_aliases() -> None:
    raw = {
        "activities": [],
        "plan_title": "  P  ",
        "plan_note": None,
    }
    acts, tit, pn = parse_plan_import(raw)
    assert acts == []
    assert tit == "P"
    assert pn == ""


def test_parse_plan_import_invalid_dict() -> None:
    try:
        parse_plan_import({"foo": []})
    except PlanParseError:
        pass
    else:
        raise AssertionError("expected PlanParseError")


def test_load_plan_from_file_legacy_list(tmp_path) -> None:
    fp = tmp_path / "w.json"
    fp.write_text(
        '[{"id":"a","name":"X","day":"Montag","start":"09:00","end":"10:00","color":"#000"}]',
        encoding="utf-8",
    )
    disk = load_plan_from_file(fp)
    assert len(disk.activities) == 1
    assert not disk.title_from_file and not disk.note_from_file
