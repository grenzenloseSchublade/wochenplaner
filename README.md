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
| **Überlappungswarnung** | Zeitkonflikte werden erkannt; Speichern ist optional trotzdem möglich |
| **Farb-Picker** | Freie Farbwahl, Schrift automatisch kontrastoptimiert |
| **Wochenplan-Import** | JSON-Dateien aus `data/` per Dropdown laden |
| **Export mit Dateiname** | Pläne unter eigenem Namen speichern (z. B. `2026-03-18_arbeitswoche.json`) |
| **PDF-Export + Download** | DIN A4 oder A5 Querformat, Titel zentriert, direkter Download |
| **Zeitbereich** | Frei einstellbar (Standard: 06:00–22:00) |
| **Statistik-Tab** | Zeitverteilung pro Aktivität als Balkendiagramm |
| **Datenpersistenz** | Alle Daten lokal in `data/*.json` |

---

## Projektstruktur

```
wochenplaner/
├── app.py              # Haupt-App (Streamlit)
├── pdf_export.py       # PDF-Generierung (reportlab)
├── run_desktop.py      # Startet die App im nativen Desktop-Fenster
├── pyproject.toml      # Abhängigkeiten (uv)
├── README.md
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
1. Aktivität aus Dropdown wählen
2. Farbe anpassen (wird automatisch gesetzt, aber frei änderbar)
3. Tag wählen (Mo–So)
4. Von / Bis aus Zeitdropdown wählen (30-Minuten-Raster)
5. „+ Hinzufügen" klicken
6. Bei Überschneidung: Warnung prüfen und optional „Trotzdem speichern"

### Wochenplan speichern / laden
- **Laden:** Sidebar → „Dateiverwaltung" → Dropdown mit allen JSON-Dateien in `data/` → „Laden"
- **Speichern:** Dateiname eingeben (Standard: `YYYY-MM-DD_wochenplan`) → „Speichern unter"
- **Beispieldaten:** `data/beispiel.json` enthält einen vorgefertigten Beispielplan

### PDF exportieren
1. Format wählen: DIN A4 oder DIN A5
2. Titel eintragen (erscheint zentriert im PDF und als Kalender-Überschrift)
3. Startzeit und Endzeit anpassen (optional)
4. „PDF erzeugen" klicken
5. Optional: „PDF herunterladen" klicken oder die Datei in `data/plans/` verwenden

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

## Bekannte Hinweise

### Matplotlib-Warnung im DevContainer

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

## Standalone Desktop-App (EXE) erstellen

Die App kann als **eigenständige Desktop-Anwendung** verpackt werden –
ohne installierten Browser, ohne Terminal, ohne Python-Installation auf dem Zielrechner.

**Verwendete Technologie:** [`streamlit-desktop-app`](https://github.com/ohtaman/streamlit-desktop-app)
(nutzt `pywebview` für ein natives Fenster, baut intern auf `PyInstaller` auf).

> **Hinweis:** Die WASM-basierte Alternative (stlite/Electron) funktioniert hier **nicht**,
> da `reportlab` (PDF-Export) kein WebAssembly unterstützt.

### Voraussetzungen (Zielrechner)

| Betriebssystem | Voraussetzungen |
|---|---|
| **Windows** | Microsoft Edge Webview2 (meist bereits installiert), .NET Framework 4.0+ |
| **macOS** | Keine zusätzlichen Abhängigkeiten |
| **Linux** | `libgtk-3-dev`, `libwebkit2gtk-4.0-dev` |

### Machbarkeit mit Win11 + WSL + Linux-Devcontainer

Kurzfassung: **Windows-EXE aus diesem Linux-Devcontainer heraus ist nicht möglich**
(kein Cross-Compile von Linux nach Windows mit PyInstaller).

Konkrete Optionen:

1. **Windows-EXE bauen (empfohlen für Win11-Nutzung):**
    Build direkt auf Windows (PowerShell/CMD), nicht in WSL/Devcontainer.
2. **Linux-Binary bauen:**
    Im Devcontainer möglich, aber Testen nur auf Linux-Desktop mit GUI (nicht headless Container).
3. **Im Devcontainer nur entwickeln/testen:**
    Für Packaging auf dem Ziel-OS wechseln.

### Schritt-für-Schritt: Windows-EXE (empfohlen bei Win11)

1. **Auf Windows arbeiten (nicht im Devcontainer/WSL bauen).**
2. **Projekt lokal auf Windows öffnen** (z. B. in VS Code oder Terminal).
3. **Desktop-Abhängigkeiten installieren:**

```bash
uv sync --group desktop
```

4. **Datenpfad in `app.py` prüfen** (Block mit `if getattr(sys, "frozen", False): ...`).
5. **Desktop-Start lokal testen:**

```bash
uv run python run_desktop.py
```

6. **EXE bauen:**

```bash
uv run streamlit-desktop-app build app.py \
    --name Wochenplaner \
    --pyinstaller-options --onefile \
    --pyinstaller-options "--collect-all=streamlit" \
    --pyinstaller-options "--copy-metadata=streamlit"
```

7. **Ergebnis prüfen:**
   `dist/Wochenplaner.exe` sollte vorhanden sein.
8. **Datenordner neben die EXE legen:**

```bash
mkdir dist\data
xcopy data dist\data /E /I /Y
```

9. **EXE testen:**
   App starten, Plan laden/speichern, PDF erzeugen.

### Schritt-für-Schritt: Linux-Binary (optional)

1. Im Linux-System (oder Devcontainer) Desktop-Abhängigkeiten installieren:

```bash
uv sync --group desktop
```

2. Binary bauen:

```bash
uv run streamlit-desktop-app build app.py \
    --name Wochenplaner \
    --pyinstaller-options --onefile \
    --pyinstaller-options "--collect-all=streamlit" \
    --pyinstaller-options "--copy-metadata=streamlit"
```

3. Ergebnis prüfen:
   `dist/Wochenplaner`
4. Datenordner kopieren:

```bash
cp -r data dist/data
```

5. Hinweis:
   GUI-Test ist im headless Devcontainer nicht möglich; Test auf Linux-Desktop durchführen.

### Wichtige CLI-Hinweise

`streamlit-desktop-app` akzeptiert als direkte Optionen nur:
`--name`, `--icon`, `--pyinstaller-options`, `--streamlit-options`.

PyInstaller-Flags wie `--onefile`, `--collect-all`, `--copy-metadata`
immer über `--pyinstaller-options` durchreichen.

### Hinweise zur Größe und Performance

- Die EXE ist typischerweise **150–250 MB** groß (Python + alle Pakete gebündelt).
- `--onefile` entpackt sich beim ersten Start in ein Temp-Verzeichnis → kurze Ladezeit.
  Mit `--onedir` (kein `--onefile`) startet die App deutlich schneller, erzeugt
  aber einen Ordner statt einer einzelnen Datei.
- UPX-Komprimierung (~30 % kleiner):
  ```bash
    uv run streamlit-desktop-app build app.py \
            --name Wochenplaner \
            --pyinstaller-options --onefile \
            --pyinstaller-options "--upx-dir=/pfad/zu/upx"
  ```

---

## Lizenz

MIT
