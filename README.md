# Wochenplaner / Weekly Planner

Kostenloser visueller Wochenplaner mit **PDF-Export** und **CSV-Export** –
ohne Anmeldung, ohne Tracking, Open Source.

Free visual weekly schedule planner with **PDF export** and **CSV export** –
no account, no tracking, open source.

> **Kostenlose Alternative zu tryschedule.com** – PDF-Export dort ab $4.90/Woche,
> hier komplett gratis.

---

## Schnellstart / Quick Start

```bash
# Abhängigkeiten installieren / Install dependencies
uv sync

# App starten / Start app
uv run streamlit run app.py
```

Öffnet automatisch http://localhost:8501 im Browser.
Opens http://localhost:8501 in your browser automatically.

### Deployment auf Streamlit Community Cloud

1. Repository auf GitHub pushen
2. [share.streamlit.io](https://share.streamlit.io) → „New app" → Repository auswählen
3. Main file: `app.py`
4. Fertig – `uv.lock` und `.python-version` werden automatisch erkannt

---

## Features

| Feature | DE | EN |
|---|---|---|
| **Proportionale Zeitblöcke** | 4h-Block doppelt so groß wie 2h | 4h block twice as tall as 2h |
| **PDF-Export (kostenlos)** | DIN A4 / A5 Querformat | DIN A4 / A5 landscape |
| **CSV-Export** | Für Excel / Google Sheets | For Excel / Google Sheets |
| **Zweisprachig** | Deutsch + Englisch | German + English |
| **Vorlagen** | Student, Fitness, Büro, Schichtplan, Beispiel | Student, Fitness, Office, Shift, Example |
| **Plan teilen** | Per URL-Link (kein Backend) | Via URL link (no backend) |
| **JSON-Download** | Plan als Datei speichern & importieren | Save plan as file & import |
| **Farb-Gedächtnis** | Farbe pro Aktivität wird gespeichert | Color saved per activity name |
| **Eigene Aktivitäten** | Bleiben als Dropdown-Optionen erhalten | Persist as dropdown options |
| **15-Min-Raster** | Viertelstunden-Genauigkeit | Quarter-hour precision |
| **Eigene Aktivitäten** | Freie Namen + Farbwahl | Custom names + color picker |
| **Überlappungswarnung** | Zeitkonflikte erkennen | Detect time conflicts |
| **Sortierte Einträge** | Nach Tag + Uhrzeit | By day + time |
| **JSON-Import/Export** | Pläne laden/speichern | Load/save plans |
| **Browser-Speicher** | Daten bleiben im Browser | Data persists in browser |
| **Dark Mode** | Standard, umschaltbar | Default, switchable |
| **Quick-Move** | Pfeiltasten in der Sidebar | Arrow buttons in sidebar |
| **Statistik** | Zeitverteilung als Balkendiagramm | Time distribution bar chart |
| **Datenschutz** | Alle Daten im Browser | All data in browser |
| **Open Source** | MIT-Lizenz | MIT License |

### Feature-Vergleich / Comparison

| Feature | Wochenplaner | tryschedule.com (Free) | tryschedule.com (Paid) |
|---|:---:|:---:|:---:|
| PDF Export | ✅ kostenlos | ❌ | ✅ ab $4.90/Wo |
| CSV Export | ✅ kostenlos | ❌ | ✅ ab $9.90/Mo |
| Vorlagen/Templates | ✅ | ❌ | ✅ |
| Kein Account nötig | ✅ | ✅ | ❌ |
| Datenschutz/DSGVO | ✅ kein Tracking | ❌ 211 Ad-Partner | ❌ |
| Open Source | ✅ MIT | ❌ | ❌ |
| URL-Sharing | ✅ | ❌ | ❌ |
| i18n (DE+EN) | ✅ | nur EN | nur EN |

---

## Projektstruktur / Project Structure

```
wochenplaner/
├── app.py              # Streamlit UI (main entry point)
├── constants.py        # Shared constants (days, colors, paths)
├── utils.py            # Utilities (time conversion, validation)
├── calendar_render.py  # Calendar HTML/CSS/JS rendering
├── pdf_export.py       # PDF generation (reportlab)
├── i18n.py             # Translations DE/EN
├── templates.py        # Predefined weekly plan templates
├── storage.py          # Browser LocalStorage abstraction
├── pyproject.toml      # Dependencies (uv)
├── .python-version     # Python 3.13 (Streamlit Cloud)
├── README.md
├── static/
│   └── calendar.css    # Calendar stylesheet (dark mode support)
├── .streamlit/
│   └── config.toml     # Streamlit config (theme, analytics)
├── .devcontainer/      # VS Code DevContainer config
│   ├── Dockerfile
│   ├── devcontainer.json
│   └── post-create.sh
└── data/
    └── plans/          # Exported PDFs (local only)
```

---

## Bedienung / Usage

### Aktivität hinzufügen / Add activity
1. Aktivität wählen oder eigene anlegen / Choose or create custom activity
2. Farbe anpassen / Adjust color
3. Tag + Zeitraum wählen (15-Min-Raster) / Pick day + time range (15-min grid)
4. „Hinzufügen" klicken / Click "Add"

### Plan speichern & laden / Save & load
- 💾 **Plan speichern (JSON)** → Datei auf Gerät speichern (manuelle Versionierung)
- Dateiverwaltung → **JSON importieren** → gespeicherte Datei laden

### Vorlagen / Templates
- Sidebar → Vorlagen → Vorlage auswählen → Laden
- 5 Vorlagen: Student, Fitness, Büro, Schichtplan, Beispiel

### Plan teilen / Share
- Sidebar → Teilen → Link kopieren → Empfänger öffnet Link
- Plan wird per URL übertragen (kein Backend nötig, ~20 Aktivitäten max)

### PDF-Export
1. Format: DIN A4 oder A5 (Querformat)
2. Titel eingeben
3. „PDF erzeugen" → „PDF herunterladen"

### CSV-Export
- Sidebar → Dateiverwaltung → „CSV exportieren"

---

## Anforderungen / Requirements

- Python >= 3.13
- [uv](https://docs.astral.sh/uv/) (Paketmanager / package manager)

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## Entwicklung / Development

```bash
# Lint
uv run ruff check .

# Auto-Fix
uv run ruff check . --fix

# Format
uv run ruff format .
```

---

## Nächste Schritte / Next Steps

- [x] **Streamlit Community Cloud Deployment** – Repository verbinden, App deployen
- [ ] **Drag & Drop** – Zeitblöcke per Drag verschieben/resizen
- [ ] **ICS/iCal Import** – Google Calendar / Outlook Export einlesen
- [ ] **Print CSS** – `@media print` für direkte Browser-Druckfunktion
- [ ] **Landing Page** – GitHub Pages mit SEO-optimierter Landingpage
- [ ] **Weitere Sprachen** – FR, ES, etc. (i18n-System ist erweiterbar)

---

## Lizenz / License

MIT – siehe [LICENSE](LICENSE)
