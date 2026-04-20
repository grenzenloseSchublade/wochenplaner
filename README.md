# Wochenplaner / Weekly Planner

Kostenloser visueller Wochenplaner mit **PDF-Export**, **CSV-Export** und **Notizen** –
ohne Anmeldung, ohne Tracking, Open Source.

Free visual weekly schedule planner with **PDF export**, **CSV export** and **notes** –
no account, no tracking, open source.

> **Kostenlose Alternative zu tryschedule.com** – PDF-Export dort ab $4.90/Woche,
> hier komplett gratis.

### Major update: PDF export (v1.5)

Ab **v1.5.0** gibt es **zwei PDF-Modi** in der Sidebar unter „PDF erzeugen“:

| Modus | Technik | Hinweis |
|-------|---------|---------|
| **Klassisch** | ReportLab (wie bisher) | PDF-Text-Annotations für Eintrag-Notizen, kein Extra-Setup |
| **Modern (HTML)** | Jinja2 + CSS + **Playwright** (headless Chromium) | Material-Design-ähnliches Layout, Schrift **Roboto** (WOFF2, [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0.html), Dateien via [@fontsource-Quellen](https://www.npmjs.com/package/@fontsource/roboto)). |

**Modern-PDF:** nach `uv sync` einmal `uv run playwright install chromium`. Unter Linux braucht Chromium typisch Systembibliotheken (z. B. `libatk`, `libgbm` – im **Devcontainer** sind sie im `Dockerfile` und `post-create.sh` abgedeckt).

**Modern-PDF: drei wählbare Stile** (Sidebar → „PDF-Stil (Modern)"):

| Stil | Charakter |
|------|-----------|
| **Minimal** | ruhig, editorial; keine Akzentfarben, keine Flächen – nur Typografie- und Linien-Hierarchie |
| **Strukturiert** *(Standard)* | dezenter Primär-Akzent unter der Wochentagsleiste, Wochenend-Spalten leicht getönt, weiche Card-Umrandung |
| **Ausgewogen** | Wochenend-Tint + klare Trennlinie Header/Raster, ohne Akzentfarbe |

Die Zeitachse ist **links prominent** mit eigenem Hintergrund, **rechts leise** als Zweitorientierung (auf A4); bei **A5 wird die rechte Achse ausgeblendet**, um mehr Platz für die Blöcke zu gewinnen.

**Ausrichtung im Raster:** Kacheln sind **links** (`text-align: start`) ausgerichtet; die **Stundenachsen** links/rechts sind bewusst **innen** zum Raster hin orientiert (Leserichtung), nicht zwingend zur Papierkante. Der **Footer** ist zentriert.

**Streamlit Community Cloud** stellt oft **keinen** vollständigen Chromium-Stack bereit: dort bei Problemen den **klassischen** Modus nutzen.

---

## Schnellstart / Quick Start

```bash
# Abhängigkeiten installieren / Install dependencies
uv sync

# Optional: Chromium für Modern-PDF (Playwright)
uv run playwright install chromium

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

**Modern-PDF** (Playwright/Chromium) ist dort **standardmäßig nicht nutzbar**, weil Streamlit Community Cloud **keine** Browser-Binaries vorinstalliert. Endnutzer sollten in der Sidebar **Klassisch** wählen.

#### Optional: Modern-PDF doch auf Streamlit Community Cloud (experimentell)

Wer Modern-PDF auf Streamlit Community Cloud erzwingen will, kann folgenden Weg versuchen – **offiziell nicht unterstützt**, Risiken im Abschnitt unten:

1. **Chromium-Systembibliotheken** via `packages.txt` im Repo-Root installieren lassen (Beispiel siehe [`packages.txt`](packages.txt) in diesem Repo – standardmäßig leer gelassen / auskommentiert).
2. **Playwright-Browser** beim App-Start einmalig herunterladen. Dazu früh in `app.py` (vor dem ersten Modern-PDF-Export) z. B. bootstrap-mäßig ausführen:

   ```python
   import os, shutil, subprocess
   if not shutil.which("chrome-headless-shell"):
       subprocess.run(
           ["playwright", "install", "--with-deps=false", "chromium"],
           check=False,
       )
   ```

3. App deployen und Logs prüfen.

**Risiken / Grenzen:**

- **Kaltstart-Verzögerung** beim ersten Lauf (Chromium-Download ~150 MB).
- **Kein persistenter Speicher**: Der Download passiert bei jedem Container-Neustart erneut.
- **Ressourcen-Limits** auf Community Cloud (RAM/CPU) können Chromium killen.
- **Keine offizielle Unterstützung** – bricht ohne Vorwarnung, sobald Streamlit Cloud seine Umgebung ändert.

Empfehlung: Für öffentliche Deployments **Klassisch** belassen; Modern-PDF lokal / self-hosted / im Devcontainer nutzen.

---

## Features

| Feature | DE | EN |
|---|---|---|
| **Proportionale Zeitblöcke** | 4h-Block doppelt so groß wie 2h | 4h block twice as tall as 2h |
| **PDF-Export (kostenlos)** | Klassisch **oder** Modern (HTML, Playwright); DIN A4 / A5 Quer | Classic **or** modern (HTML, Playwright); DIN A4 / A5 landscape |
| **CSV-Export** | Für Excel / Google Sheets | For Excel / Google Sheets |
| **Notizen (pro Eintrag)** | 2-zeilige Notiz pro Aktivität, sichtbar im Kontextmenü | 2-line note per activity, visible in context menu |
| **Notizen (Plan-Ebene)** | Mehrzeilige Notiz für den gesamten Wochenplan | Multi-line note for the whole week |
| **PDF-Notizen (Sticky Notes, nur Klassisch)** | Eintrag-Notizen als klickbare PDF-Annotations im Klassisch-Modus | Activity notes as clickable PDF annotations (Classic mode only) |
| **Kalender-Direktbearbeitung** | Klick auf Block → Bearbeiten ohne Seitenreload | Click block → edit without page reload |
| **Zweisprachig** | Deutsch + Englisch | German + English |
| **Vorlagen** | Student, Fitness, Büro, Schichtplan, Beispiel | Student, Fitness, Office, Shift, Example |
| **Plan teilen** | Per URL-Link (kein Backend) | Via URL link (no backend) |
| **JSON-Download** | Plan als Datei speichern & importieren | Save plan as file & import |
| **Farb-Gedächtnis** | Farbe pro Aktivität wird gespeichert | Color saved per activity name |
| **Eigene Aktivitäten** | Freie Namen + Farbwahl, bleiben erhalten, einzeln löschbar | Custom names + color picker, persisted, deletable one by one |
| **15-Min-Raster** | Viertelstunden-Genauigkeit | Quarter-hour precision |
| **Überlappungswarnung** | Zeitkonflikte erkennen | Detect time conflicts |
| **Sortierte Einträge** | Nach Tag + Uhrzeit | By day + time |
| **Browser-Speicher** | Daten bleiben im Browser (LocalStorage) | Data persists in browser (LocalStorage) |
| **Dark Mode** | Automatisch, umschaltbar | Automatic, switchable |
| **Quick-Move** | Pfeiltasten in der Sidebar | Arrow buttons in sidebar |
| **Statistik** | Zeitverteilung als Balkendiagramm | Time distribution bar chart |
| **Datenschutz** | Alle Daten im Browser | All data in browser |
| **Open Source** | MIT-Lizenz | MIT License |

### Feature-Vergleich / Comparison

| Feature | Wochenplaner | tryschedule.com (Free) | tryschedule.com (Paid) |
|---|:---:|:---:|:---:|
| PDF Export | ✅ kostenlos | ❌ | ✅ ab $4.90/Wo |
| CSV Export | ✅ kostenlos | ❌ | ✅ ab $9.90/Mo |
| Notizen + PDF-Annotations | ✅ | ❌ | ❌ |
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
├── app.py                          # Streamlit UI (main entry point)
├── pdf_context.py                  # Gemeinsamer PDF-Export-Context (klassisch + modern)
├── constants.py                    # Shared constants (days, colors, paths)
├── utils.py                        # Utilities (time conversion, validation)
├── html_pdf/                       # Modern-PDF: Jinja2, CSS, Roboto, Playwright
├── calendar_render.py              # Calendar HTML/CSS/JS rendering
├── calendar_component/             # Bidirectional Streamlit component
│   ├── __init__.py                 # Python wrapper (declare_component)
│   └── frontend/
│       └── index.html              # Component iframe (Streamlit ↔ JS bridge)
├── pdf_export.py                   # PDF generation (reportlab) + annotations
├── i18n.py                         # Translations DE/EN
├── templates.py                    # Predefined weekly plan templates
├── storage.py                      # Browser LocalStorage abstraction
├── pyproject.toml                  # Dependencies (uv)
├── .python-version                 # Python 3.13 (Streamlit Cloud)
├── README.md
├── static/
│   └── calendar.css                # Calendar stylesheet (dark mode support)
├── .streamlit/
│   └── config.toml                 # Streamlit config (theme, analytics)
├── .devcontainer/                  # VS Code DevContainer config
│   ├── Dockerfile
│   ├── devcontainer.json
│   └── post-create.sh
└── data/
    └── plans/                      # Exported PDFs (local only)
```

---

## Architektur / Architecture

### Kalender-Komponente

Der Kalender ist als **bidirektionale Streamlit-Komponente** (`declare_component`) implementiert.
Klicks auf Aktivitätsblöcke kommunizieren direkt über `postMessage` an das Python-Backend,
ohne einen vollständigen Browser-Reload auszulösen.

### Performance-Optimierungen

- **`@st.fragment`** auf dem Eingabeformular: Widget-Interaktionen (Dropdown, Farbwahl) lösen nur einen isolierten Fragment-Rerun aus
- **`@st.fragment`** auf dem Statistik-Tab: Plotly-Chart wird nicht bei jeder Sidebar-Aktion neu gerendert
- **Stabile Widget-Keys**: Alle Formular-Widgets haben explizite, unveränderliche `key`-Parameter
- **Session-State-Verwaltung**: Formularwerte werden zentral verwaltet und nach dem Speichern bereinigt

### Notizen im PDF

**Eintrag-Notizen** erscheinen im PDF **als kurzer Text unter dem Aktivitätsnamen** im farbigen Block (wenn der Block hoch genug ist); die Farbe passt sich der Blockfarbe an.
Im **Klassisch-Modus** bleiben zusätzlich **Text-Annotations (Sticky Notes)** erhalten: kleine Icons mit vollem Notiztext per Klick. Der **Modern-Modus** (HTML+Chromium) erzeugt kein Sticky-Note-Layer – dort ist der sichtbare Inline-Text die einzige Notiz im PDF.
Die **Plan-Notiz** (über dem Raster) wird wie bisher als Untertitel unter dem Plantitel gerendert.

---

## Bedienung / Usage

### Aktivität hinzufügen / Add activity
1. Aktivität wählen oder eigene anlegen / Choose or create custom activity
2. Farbe anpassen / Adjust color
3. Tag + Zeitraum wählen (15-Min-Raster) / Pick day + time range (15-min grid)
4. Optional: Notiz hinzufügen (2-zeilig) / Optionally add a note (2 lines)
5. „Hinzufügen" klicken / Click "Add"

### Kalender-Bearbeitung / Calendar editing
- Klick auf einen Block im Kalender öffnet das Kontextmenü mit Notiz-Vorschau
- „Bearbeiten" öffnet das Formular mit vorausgefüllten Werten (kein Seitenreload)
- **Eintrag-Notiz im Raster**: Steht der Block hoch genug, erscheint die Notiz **unter dem Aktivitätsnamen** (kleiner, nicht fett, Farbe mit Kontrast zur Blockfarbe); bei sehr flachen Blöcken nur ein Stift-Icon als Hinweis

### Notizen / Notes
- **Eintrag-Notiz**: Pro Aktivität ein 2-zeiliges Textfeld (z.B. „Raum 204, mit Max")
- **Plan-Notiz**: Mehrzeiliges Feld im PDF-Bereich (z.B. „KW 15 – Urlaubswoche")
- **JSON**: Plantitel, Plan-Notiz und Eintrags-Notizen werden in der JSON-Datei gespeichert
- **CSV**: nur Eintrags-Notizen (Spalte „Notiz“), kein Plantitel und keine Plan-Notiz
- **PDF**: Plantitel, Plan-Notiz; Eintrags-Notizen im Block (soweit Platz) **und** als Sticky-Annotation

### Plan speichern & laden / Save & load
- **Plan speichern (JSON)** → Datei auf Gerät speichern (einheitliches Format mit Titel, Plan-Notiz und Aktivitäten)
- Dateiverwaltung → **JSON importieren** → gespeicherte Datei laden (ältere reine Aktivitäten-Listen werden weiterhin akzeptiert)

### Vorlagen / Templates
- Sidebar → Vorlagen → Vorlage auswählen → Laden
- 5 Vorlagen: Student, Fitness, Büro, Schichtplan, Beispiel

### Plan teilen / Share
- Für typische vollständige Wochenpläne: **JSON-Datei** speichern und per Messenger, E-Mail oder Cloud versenden
- Bestehende Links mit `?plan=…` (nur Aktivitäten, komprimiert) funktionieren weiter; für große Pläne ist die URL oft zu kurz bemessen

### PDF-Export
1. Format: DIN A4 oder A5 (Querformat)
2. Titel + Plan-Notiz eingeben
3. „PDF erzeugen" → „PDF herunterladen"
4. Eintrag-Notizen: sichtbar im Block (bei ausreichend hohem Termin); im Klassisch-Modus **zusätzlich** als klickbare Sticky-Note-Icons, im Modern-Modus nur der Inline-Text
5. Im farbigen Termin: **Startzeit** optional oben links; **Name und Notiz** darunter **oben** und **zeilenweise am Zeilenanfang** ausgerichtet (nicht vertikal zentriert), mit an die Blockhöhe angepassten Schriftgrößen (**Modern-PDF:** Stufen `xs`–`lg`)

### CSV-Export
- Sidebar → Dateiverwaltung → „CSV exportieren"
- Enthält Notiz-Spalte

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
- [x] **Notizen** – Pro Eintrag (2-zeilig) + Plan-Ebene (mehrzeilig) + PDF-Annotations
- [x] **Kalender-Direktbearbeitung** – Bidirektionale Komponente, kein Browser-Reload
- [x] **Performance-Optimierung** – Fragment-Isolierung, stabile Widget-Keys
- [ ] **Drag & Drop** – Zeitblöcke per Drag verschieben/resizen
- [ ] **ICS/iCal Import** – Google Calendar / Outlook Export einlesen
- [ ] **Print CSS** – `@media print` für direkte Browser-Druckfunktion
- [ ] **Landing Page** – GitHub Pages mit SEO-optimierter Landingpage
- [ ] **Weitere Sprachen** – FR, ES, etc. (i18n-System ist erweiterbar)

---

## Lizenz / License

MIT – siehe [LICENSE](LICENSE)
