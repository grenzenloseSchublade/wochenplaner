"""Gemeinsame Konstanten für den Wochenplaner."""

from pathlib import Path

WOCHENTAGE = [
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
    "Samstag",
    "Sonntag",
]

AKTIVITAETEN_FARBEN: dict[str, str] = {
    "Arbeit": "#F3E5AB",
    "Laufen": "#FFB6B6",
    "Kraft": "#FFCC99",
    "Sprachkurs": "#B6D7A8",
    "Dehnen": "#A8D8E8",
    "Long Run": "#B8E0C3",
    "Meeting": "#E8C8D8",
    "Freizeit": "#FFEAA7",
    "Schlafen": "#D8D8D8",
    "Kochen": "#F9C784",
}

START_HOUR = 6
END_HOUR = 22
PX_PER_MIN = 1.6
DEFAULT_VON = "09:00"

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "wochenplan.json"
PLANS_DIR = DATA_DIR / "plans"

TIME_OPTIONS: list[str] = [
    f"{h:02d}:{m:02d}"
    for h in range(START_HOUR, END_HOUR + 1)
    for m in (0, 15, 30, 45)
    if not (h == END_HOUR and m > 0)
]
