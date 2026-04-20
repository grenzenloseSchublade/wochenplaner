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
        "pdf_show_axis_times": "Uhrzeiten am Planrand",
        "pdf_show_axis_times_help": "Stunden (HH:00) links und rechts neben dem Raster.",
        "pdf_show_block_times": "Startzeiten in den Blöcken",
        "pdf_show_block_times_help": "Startzeit oben links in jedem farbigen Termin.",
        "pdf_continuous_hgrid": "Zeitlinien über Terminen",
        "pdf_continuous_hgrid_help": "Horizontale Stunden- und Halbstundenlinien durchgängig sichtbar, auch über farbigen Terminen.",
        "pdf_export_mode": "PDF-Export",
        "pdf_style_classic": "Klassisch (ReportLab)",
        "pdf_style_modern": "Modern (Kalenderlayout)",
        "pdf_style_hint": (
            "Klassisch: kompaktes PDF mit ReportLab; Eintrag-Notizen zusätzlich als klickbare Hinweise. "
            "Modern: farbiges Wochenraster wie in der App (HTML/CSS)."
        ),
        "pdf_modern_hosting_note": (
            "Hinweis: Modern-PDF braucht auf dem Server einen Browser (Chromium). "
            "**Auf Streamlit Community Cloud funktioniert Modern-PDF in der Regel nicht** – dort bitte **Klassisch** wählen. "
            "Lokal oder self-hosted: siehe README."
        ),
        "pdf_theme_label": "PDF-Stil (Modern)",
        "pdf_theme_minimal": "Minimal",
        "pdf_theme_structured": "Strukturiert",
        "pdf_theme_balanced": "Ausgewogen",
        "pdf_theme_hint": (
            "Minimal: ruhig, nur Typografie-Hierarchie. "
            "Strukturiert: Primärlinie unter der Wochentagsleiste, Wochenend-Tint, weiche Card-Umrandung (Standard). "
            "Ausgewogen: Wochenend-Tint, klare Trennlinie ohne Akzentfarbe."
        ),
        "pdf_modern_failed": "Modern-PDF konnte nicht erzeugt werden.",
        "pdf_export_failed": "PDF konnte nicht erzeugt werden.",
        "pdf_error_details": "Technische Details",
        # File management
        "file_mgmt": "Dateiverwaltung",
        "import_json": "JSON importieren",
        "importing_json": "Plan wird geladen…",
        "activities_imported": "Aktivitäten importiert",
        "no_valid_acts": "Keine gültigen Aktivitäten in der Datei.",
        "json_must_list": "JSON muss eine Liste von Aktivitäten sein.",
        "json_invalid_plan": "Ungültiges Plan-JSON (Objekt mit Liste „activities“ erwartet).",
        "json_too_large": "JSON-Datei ist zu groß.",
        "invalid_json": "Ungültige JSON-Datei.",
        "export_csv": "CSV exportieren",
        "download_json": "💾 Plan speichern (JSON)",
        "download_json_hint": (
            "Speichert Plantitel, Plan-Notiz und alle Aktivitäten als Datei auf deinem Gerät. "
            "Zum Wiederherstellen per „JSON importieren“ laden. Enthält alle Notizen – "
            "unbedacht nicht weitergeben."
        ),
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
        "share_via_json_hint": (
            "Volle Wochenpläne passen oft nicht in einen Link. "
            "Nutze „Plan speichern (JSON)“ und sende die Datei per Messenger oder E-Mail."
        ),
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
        # Notes
        "note": "Notiz",
        "note_placeholder": "z.B. Raum, Hinweise…",
        "plan_note": "Plan-Notiz",
        "plan_note_placeholder": "Mus nicht schmecken, muss wirken!",
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
        "pdf_show_axis_times": "Times on planning grid edge",
        "pdf_show_axis_times_help": "Hour labels (HH:00) left and right of the grid.",
        "pdf_show_block_times": "Start times in blocks",
        "pdf_show_block_times_help": "Start time in the top-left of each activity block.",
        "pdf_continuous_hgrid": "Time lines over appointments",
        "pdf_continuous_hgrid_help": "Hour and half-hour horizontal lines visible across the grid, including over colored blocks.",
        "pdf_export_mode": "PDF export",
        "pdf_style_classic": "Classic (ReportLab)",
        "pdf_style_modern": "Modern (calendar layout)",
        "pdf_style_hint": (
            "Classic: compact ReportLab PDF; activity notes also as clickable markers. "
            "Modern: colored week grid like the app (HTML/CSS)."
        ),
        "pdf_modern_hosting_note": (
            "Note: Modern PDF needs a server-side browser (Chromium). "
            "**On Streamlit Community Cloud, Modern PDF usually does not work** — please choose **Classic** there. "
            "Local or self-hosted: see README."
        ),
        "pdf_theme_label": "PDF style (Modern)",
        "pdf_theme_minimal": "Minimal",
        "pdf_theme_structured": "Structured",
        "pdf_theme_balanced": "Balanced",
        "pdf_theme_hint": (
            "Minimal: quiet, typography-only hierarchy. "
            "Structured: primary accent line under the weekday row, weekend tint, soft card outline (default). "
            "Balanced: weekend tint, clear divider without accent color."
        ),
        "pdf_modern_failed": "Could not generate modern PDF.",
        "pdf_export_failed": "Could not generate PDF.",
        "pdf_error_details": "Technical details",
        # File management
        "file_mgmt": "File management",
        "import_json": "Import JSON",
        "importing_json": "Loading plan…",
        "activities_imported": "activities imported",
        "no_valid_acts": "No valid activities in file.",
        "json_must_list": "JSON must be a list of activities.",
        "json_invalid_plan": "Invalid plan JSON (expected an object with an “activities” list).",
        "json_too_large": "JSON file is too large.",
        "invalid_json": "Invalid JSON file.",
        "export_csv": "Export CSV",
        "download_json": "💾 Save plan (JSON)",
        "download_json_hint": (
            "Saves plan title, plan note, and all activities to a file on your device. "
            "Restore via “Import JSON”. Contains all notes—do not share carelessly."
        ),
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
        "share_via_json_hint": (
            "Full weekly plans often do not fit in a link. "
            "Use “Save plan (JSON)” and send the file via messenger or email."
        ),
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
        # Notes
        "note": "Note",
        "note_placeholder": "e.g. room, remarks…",
        "plan_note": "Plan note",
        "plan_note_placeholder": "stay hydrated and give it your all!",
        # PDF footer
        "pdf_footer": "Weekly Planner – created for free",
    },
}


def t(key: str, lang: Lang = "de") -> str:
    """Übersetze einen Schlüssel in die gewählte Sprache."""
    return TRANSLATIONS.get(lang, TRANSLATIONS["de"]).get(
        key, TRANSLATIONS["de"].get(key, key)
    )
