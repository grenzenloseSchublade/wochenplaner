# Wochenplaner

Lokale Streamlit-App für einen **visuell proportionalen** Wochenplan
mit direktem **PDF-Export** (DIN A4 / A5 Querformat).

---

## Schnellstart (mit `uv`)

```bash
# 1. Abhängigkeiten installieren
uv sync

# 2. App starten
uv run streamlit run app.py
```

Öffnet automatisch http://localhost:8501 im Browser.

---

## Features

| Feature | Beschreibung |
|---|---|
| **Proportionale Zeitblöcke** | 4h-Block ist doppelt so groß wie 2h-Block |
| **Aktivitäten bearbeiten** | Einträge per Bearbeiten-Button anpassen, nicht nur löschen |
| **Eigene Aktivitäten** | Neben vordefinierten auch eigene Aktivitätsnamen anlegen |
| **Überlappungswarnung** | Zeitkonflikte werden erkannt; Speichern ist optional trotzdem möglich |
| **Farb-Picker** | Freie Farbwahl, Schrift automatisch kontrastoptimiert |
| **15-Minuten-Raster** | Feinere Zeitplanung im Viertelstundentakt |
| **Sortierte Einträge** | Aktivitäten nach Tag und Uhrzeit sortiert angezeigt |
| **Wochenplan-Import** | JSON-Dateien aus `data/` per Dropdown laden |
| **JSON-Upload** | Externe JSON-Dateien direkt per Datei-Upload importieren |
| **Export mit Dateiname** | Pläne unter eigenem Namen speichern (z. B. `2026-03-18_arbeitswoche.json`) |
| **PDF-Export + Download** | DIN A4 oder A5 Querformat, Titel zentriert, direkter Download |
| **CSV-Export** | Wochenplan als CSV für Tabellenkalkulationen exportieren |
| **Zeitbereich** | Frei einstellbar (Standard: 06:00–22:00) |
| **Statistik-Tab** | Zeitverteilung pro Aktivität als Balkendiagramm mit Gesamtstunden |
| **Datenpersistenz** | Alle Daten lokal in `data/*.json` |

---

## Projektstruktur

```
wochenplaner/
├── app.py              # Haupt-App (Streamlit UI-Orchestrator)
├── constants.py        # Gemeinsame Konstanten (Tage, Farben, Pfade)
├── utils.py            # Hilfsfunktionen (Zeitkonvertierung, Validierung)
├── calendar_render.py  # Kalender-Rendering (HTML/CSS/JS)
├── pdf_export.py       # PDF-Generierung (reportlab)
├── pyproject.toml      # Abhängigkeiten (uv)
├── README.md
├── static/
│   └── calendar.css    # Kalender-Stylesheet (externalisiert)
├── .streamlit/
│   └── config.toml     # Streamlit-Konfiguration (Theme etc.)
├── .devcontainer/      # VS Code DevContainer-Konfiguration
│   ├── Dockerfile
│   ├── devcontainer.json
│   └── post-create.sh
└── data/
    ├── wochenplan.json # Automatisch erstellt (Nutzer-Daten)
    ├── beispiel.json   # Beispiel-Datensatz
    └── plans/          # Exportierte PDFs
```

---

## Bedienung

### Aktivität hinzufügen
1. Aktivität aus Dropdown wählen – oder „Eigene Aktivität" aktivieren und Namen eingeben
2. Farbe anpassen (wird automatisch gesetzt, aber frei änderbar)
3. Tag wählen (Mo–So)
4. Von / Bis aus Zeitdropdown wählen (15-Minuten-Raster)
5. „+ Hinzufügen" klicken
6. Bei Überschneidung: Warnung prüfen und optional „Trotzdem speichern"

### Wochenplan speichern / laden
- **Laden:** Sidebar → „Dateiverwaltung" → Dropdown mit allen JSON-Dateien in `data/` → „Laden"
- **Speichern:** Dateiname eingeben (Standard: `YYYY-MM-DD_wochenplan`) → „Speichern unter"
- **Importieren:** JSON-Datei per Drag & Drop oder Datei-Auswahl hochladen
- **Beispieldaten:** `data/beispiel.json` enthält einen vorgefertigten Beispielplan

### PDF exportieren
1. Format wählen: DIN A4 oder DIN A5
2. Titel eintragen (erscheint zentriert im PDF und als Kalender-Überschrift)
3. Startzeit und Endzeit anpassen (optional)
4. „PDF erzeugen" klicken
5. „PDF herunterladen" klicken – die Datei wird auch in `data/plans/` gespeichert

### CSV exportieren
- In der Dateiverwaltung auf „CSV exportieren" klicken
- Die CSV-Datei enthält alle Aktivitäten, sortiert nach Tag und Uhrzeit

---

## Anforderungen

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/) (Paketmanager)

### uv installieren (falls noch nicht vorhanden)

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## Entwicklung

### Linting & Formatierung

Das Projekt verwendet [Ruff](https://docs.astral.sh/ruff/) für Linting und Formatierung:

```bash
# Lint prüfen
uv run ruff check .

# Auto-Fix
uv run ruff check . --fix

# Formatierung
uv run ruff format .
```

### Bekannte Hinweise

#### Matplotlib-Warnung im DevContainer

Im DevContainer kann folgender Fehler auftreten:

```
mkdir -p failed for path /home/vscode/.cache/matplotlib: [Errno 13] Permission denied
```

**Ursache:** Docker-Volumes werden initial als `root` initialisiert, der `vscode`-User
hat kein Schreibrecht auf den Standard-Cache-Pfad.

**Lösung:** Ist bereits im Dockerfile und in `post-create.sh` gefixt.
Nach einem Container-Rebuild (in VS Code: `Ctrl+Shift+P` → „Rebuild Container")
verschwindet die Warnung dauerhaft.

Manueller Workaround (ohne Rebuild):
```bash
export MPLCONFIGDIR=/tmp/matplotlib
uv run streamlit run app.py
```

---

## Lizenz

MIT
