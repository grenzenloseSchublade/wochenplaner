"""Internationalisierung – Deutsch / English."""

from typing import Literal

Lang = Literal["de", "en"]

LANG_FLAGS: dict[Lang, str] = {
    "de": "🇩🇪 Deutsch",
    "en": "🇬🇧 English",
}

WOCHENTAGE_I18N: dict[Lang, list[str]] = {
    "de": [
        "Montag",
        "Dienstag",
        "Mittwoch",
        "Donnerstag",
        "Freitag",
        "Samstag",
        "Sonntag",
    ],
    "en": [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ],
}

WOCHENTAGE_KURZ_I18N: dict[Lang, list[str]] = {
    "de": ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
    "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
}

# Interner Key → Display-Name pro Sprache (Wochentage)
# JSON speichert immer deutsche Keys für Abwärtskompatibilität.
_DE_DAYS = WOCHENTAGE_I18N["de"]
_EN_DAYS = WOCHENTAGE_I18N["en"]
DAY_DISPLAY: dict[Lang, dict[str, str]] = {
    "de": {d: d for d in _DE_DAYS},
    "en": dict(zip(_DE_DAYS, _EN_DAYS, strict=True)),
}
DAY_FROM_DISPLAY: dict[Lang, dict[str, str]] = {
    lang: {v: k for k, v in mapping.items()} for lang, mapping in DAY_DISPLAY.items()
}

TRANSLATIONS: dict[Lang, dict[str, str]] = {
    "de": {
        # Sidebar
        "app_title": "Wochenplaner",
        "app_caption": "Daten im Browser · kostenlos · Open Source",
        "add_activity": "Aktivität hinzufügen",
        "edit_activity": "Bearbeiten",
        "custom_activity": "Eigene Aktivität",
        "activity_name": "Name der Aktivität",
        "activity": "Aktivität",
        "color": "Farbe",
        "day": "Tag",
        "from_time": "Von",
        "to_time": "Bis",
        "save": "Speichern",
        "add": "+ Hinzufügen",
        "cancel": "Abbrechen",
        "save_anyway": "Trotzdem speichern",
        "entries": "Einträge",
        "delete": "Löschen",
        "duplicate": "Duplizieren",
        "confirm_delete_all": "Wirklich alle löschen?",
        "delete_all": "Alle löschen",
        # Validation
        "enter_name": "Bitte einen Aktivitätsnamen eingeben.",
        "end_after_start": "Endzeit muss nach Startzeit liegen.",
        "overlap_with": "Zeitüberschneidung mit:",
        # PDF
        "generate_pdf": "PDF erzeugen",
        "plan_title": "Plantitel",
        "format": "Format",
        "time_range": "Zeitbereich",
        "start_hour": "Startzeit (Uhr)",
        "end_hour": "Endzeit (Uhr)",
        "generating_pdf": "PDF wird generiert…",
        "no_activities": "Keine Aktivitäten vorhanden.",
        "start_lt_end": "Startzeit muss kleiner als Endzeit sein.",
        "download_pdf": "PDF herunterladen",
        # File management
        "file_mgmt": "Dateiverwaltung",
        "import_json": "JSON importieren",
        "importing_json": "Plan wird geladen…",
        "activities_imported": "Aktivitäten importiert",
        "no_valid_acts": "Keine gültigen Aktivitäten in der Datei.",
        "json_must_list": "JSON muss eine Liste von Aktivitäten sein.",
        "invalid_json": "Ungültige JSON-Datei.",
        "export_csv": "CSV exportieren",
        "download_json": "💾 Plan speichern (JSON)",
        "download_json_hint": 'Speichert den Plan als Datei auf deinem Gerät. Zum Wiederherstellen per "JSON importieren" laden.',
        # Templates
        "templates": "Vorlagen",
        "load_template": "Vorlage laden",
        "template_overwrite": "Vorhandene Aktivitäten werden ersetzt!",
        "template_loaded": "Vorlage geladen:",
        # Sharing
        "share": "Teilen",
        "share_plan": "Plan teilen",
        "share_link": "Teilen-Link",
        "copy_link": "Link kopieren",
        "link_copied": "Link in Zwischenablage kopiert!",
        "plan_loaded_from_link": "Plan aus Link geladen!",
        "share_too_large": "Plan zu groß zum Teilen per URL.",
        "share_help": "Empfänger öffnet den Link und der Plan wird geladen.",
        # Tabs
        "tab_calendar": "Kalender",
        "tab_statistics": "Statistik",
        # Statistics
        "no_stats": "Keine Aktivitäten für Statistik vorhanden.",
        "no_valid_blocks": "Keine gültigen Zeitblöcke.",
        "total_hours": "Gesamtstunden / Woche",
        "hours_label": "Stunden",
        "time_dist": "Zeitverteilung",
        # Calendar
        "add_first": "← Füge im Menü deine erste Aktivität hinzu.",
        # Language
        "language": "Sprache",
        # New plan
        "new_plan": "Neuer Plan",
        # PDF footer
        "pdf_footer": "Wochenplaner – kostenlos erstellt",
    },
    "en": {
        # Sidebar
        "app_title": "Weekly Planner",
        "app_caption": "Data in browser · free · open source",
        "add_activity": "Add activity",
        "edit_activity": "Edit",
        "custom_activity": "Custom activity",
        "activity_name": "Activity name",
        "activity": "Activity",
        "color": "Color",
        "day": "Day",
        "from_time": "From",
        "to_time": "To",
        "save": "Save",
        "add": "+ Add",
        "cancel": "Cancel",
        "save_anyway": "Save anyway",
        "entries": "Entries",
        "delete": "Delete",
        "duplicate": "Duplicate",
        "confirm_delete_all": "Really delete all?",
        "delete_all": "Delete all",
        # Validation
        "enter_name": "Please enter an activity name.",
        "end_after_start": "End time must be after start time.",
        "overlap_with": "Time conflict with:",
        # PDF
        "generate_pdf": "Generate PDF",
        "plan_title": "Plan title",
        "format": "Format",
        "time_range": "Time range",
        "start_hour": "Start hour",
        "end_hour": "End hour",
        "generating_pdf": "Generating PDF…",
        "no_activities": "No activities yet.",
        "start_lt_end": "Start time must be less than end time.",
        "download_pdf": "Download PDF",
        # File management
        "file_mgmt": "File management",
        "import_json": "Import JSON",
        "importing_json": "Loading plan…",
        "activities_imported": "activities imported",
        "no_valid_acts": "No valid activities in file.",
        "json_must_list": "JSON must be a list of activities.",
        "invalid_json": "Invalid JSON file.",
        "export_csv": "Export CSV",
        "download_json": "💾 Save plan (JSON)",
        "download_json_hint": 'Downloads the plan as a file to your device. Restore it later via "Import JSON".',
        # Templates
        "templates": "Templates",
        "load_template": "Load template",
        "template_overwrite": "Existing activities will be replaced!",
        "template_loaded": "Template loaded:",
        # Sharing
        "share": "Share",
        "share_plan": "Share plan",
        "share_link": "Share link",
        "copy_link": "Copy link",
        "link_copied": "Link copied to clipboard!",
        "plan_loaded_from_link": "Plan loaded from link!",
        "share_too_large": "Plan too large for URL sharing.",
        "share_help": "Recipients open the link and the plan loads automatically.",
        # Tabs
        "tab_calendar": "Calendar",
        "tab_statistics": "Statistics",
        # Statistics
        "no_stats": "No activities for statistics.",
        "no_valid_blocks": "No valid time blocks.",
        "total_hours": "Total hours / week",
        "hours_label": "Hours",
        "time_dist": "Time distribution",
        # Calendar
        "add_first": "← Add your first activity in the sidebar.",
        # Language
        "language": "Language",
        # New plan
        "new_plan": "New Plan",
        # PDF footer
        "pdf_footer": "Weekly Planner – created for free",
    },
}


def t(key: str, lang: Lang = "de") -> str:
    """Übersetze einen Schlüssel in die gewählte Sprache."""
    return TRANSLATIONS.get(lang, TRANSLATIONS["de"]).get(
        key, TRANSLATIONS["de"].get(key, key)
    )
