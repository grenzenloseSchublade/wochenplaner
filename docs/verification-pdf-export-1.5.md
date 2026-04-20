# Verifikation: PDF-Export v1.5 (klassisch + Modern HTML)

Abnahme-Checkliste für Release **1.5.0** und nachfolgende Modern-PDF-Updates. Abhaken, wenn erledigt oder **N/A** mit Kurzgrund.

## Pfad A – Klassisch (ReportLab)

- [ ] PDF erzeugen mit mehreren Terminen; Layout wie gewohnt
- [ ] Eintrag-Notizen: PDF-Annotations (Sticky) vorhanden, wo erwartet
- [ ] Optionen: Achsenzeiten, Blockzeiten, durchgängiges Raster – sichtbar korrekt

## Pfad B – Modern (HTML, Playwright / Chromium)

- [ ] PDF erzeugen; Datei beginnt mit `%PDF`
- [ ] **Einseitigkeit**: A4 und A5, jeweils mit und ohne Plan-Notiz, ergeben genau **eine** Seite
- [ ] Sichtbarer Druckrand rundum (A4 ~6/7 mm, A5 ~3/4 mm) – Kalender klebt nicht am Papierrand
- [ ] Typografie wirkt einheitlich (Roboto); keine fehlenden Glyphen (DE/EN)
- [ ] Titel ≥ 14 pt, deutlich als Überschrift erkennbar; Plan-Notiz ≤ 7 pt, zentriert
- [ ] Plantitel und Plan-Notiz erscheinen wie im UI
- [ ] Kurze und lange Blöcke: Titel/Notiz lesbar (Stufen-Typo), kein „Staub“ bei Notizen
- [ ] **Textgrößen** in Blöcken deutlich lesbar: xs ~4.6pt, sm-Titel ~6pt, md-Titel ~7pt, lg-Titel ~8.2pt (Titel klar erkennbar in allen Größen)
- [ ] Großer Block (z.B. „Arbeit" 09–17 Uhr): Titel sichtbar nahe am oberen Rand, Notiz darunter, nichts abgeschnitten
- [ ] A4 und A5 Quer: kein harter Umbruch mitten in der Kopfzeile (visuell)
- [ ] Kalender als **eine** Tabelle lesbar: Wochentagsleiste und Raster teilen Rahmen/Border, keine sichtbare Fuge
- [ ] Zeitachse links mit eigenem Hintergrund, Achsen-Zahlen lesbar (≥ 6pt)
- [ ] A4: Achse rechts dezent vorhanden; A5: Achse rechts **ausgeblendet**, Raster nutzt die Breite
- [ ] Raster-Linien: volle Stunde deutlich sichtbar, halbe Stunde schwächer; je nach Theme auch Viertelstunden
- [ ] **Raster-Linien laufen auch über farbige Blöcke durch** (Overlay-Layer): durchgehend an gleicher Position, nicht von Kacheln verdeckt
- [ ] **Stunden-Bänder** (structured/balanced): jede zweite Stunde minimal getönt über volle Raster-Breite (inkl. Achsen); Blockfarben bleiben erkennbar. Minimal-Theme: **keine** Bänder (bewusst ruhig).
- [ ] Startzeit-Ecke in Kacheln: erscheint **nur** ab ~40 min Blockdauer (kürzere Blöcke zeigen nur den Titel, damit nichts klemmt)

### Themes (jeweils A4 + A5)

| Theme | Erwartetes Kalender-Chrome |
|-------|----------------------------|
| **Minimal** | keine Primär-Akzentlinie, kein Wochenend-Tint, keine Card-Shadow; nur Typografie |
| **Strukturiert** | Primary-Linie durchgehend unter der Wochentagsleiste; Wochenend-Spalten leicht getönt; weiche Card-Shadow |
| **Ausgewogen** | keine Primary-Linie; Wochenend-Tint; klare `outline`-Trennlinie Header/Raster |

- [ ] **Minimal**: A4 und A5 visuell geprüft
- [ ] **Strukturiert**: A4 und A5 visuell geprüft
- [ ] **Ausgewogen**: A4 und A5 visuell geprüft

## UI / i18n

- [ ] Radio: Klassisch vs. Modern; Beschriftungen DE und EN plausibel
- [ ] Bei „Modern" sichtbar: zweites Radio **PDF-Stil (Modern)** mit minimal/strukturiert/ausgewogen (Default: ausgewogen)
- [ ] Wechsel zwischen den drei Themes erzeugt unterschiedliche PDFs (manueller Sichtcheck)
- [ ] Pro Klick wird nur **ein** Pfad ausgeführt (kein Doppel-Download ohne erneuten Klick)

## Abhängigkeiten / Umgebung

- [ ] Frische venv: `uv sync`, `uv run playwright install chromium` (für Pfad B)
- [ ] Linux: Systemlibs für Chromium (oder Devcontainer-Image neu gebaut)
- [ ] Bei fehlendem Chromium: sinnvolle Fehlermeldung in der App

## Tests

- [ ] `uv run pytest` grün
- [ ] `uv run ruff check .` ohne neue relevante Fehler

## Dokumentation & Version

- [ ] README: Zwei PDF-Modi, Roboto/Lizenzen, Playwright-Setup, Hinweis Achsen/Footer gelesen
- [ ] `pyproject.toml` Version; Footer in der App passend zur Release-Nummer

## Randfälle (kurz)

- [ ] Leerer Plan / viele Termine / A4 und A5

## Implementierungs-Audit (Definition of Done)

Kurz nach größeren Modern-PDF-Änderungen abarbeiten:

| Bereich | Prüfpunkt |
|--------|-----------|
| Automatisiert | `uv sync` / `uv run pytest tests/` grün |
| Modern (Playwright) | `%PDF`, Stufen-Typo, Plan-Titel/-Notiz, Optionen Achse/Raster |
| Klassisch | Keine Regression ReportLab/Annotations |
| App | Sidebar Klassisch/Modern; verständliche Fehler bei fehlendem Chromium |
| Devcontainer | Dockerfile enthält Systemlibs für Playwright/Chromium |

### Abnahmeprotokoll (manuell)

| Datum | Prüfer | Modern-PDF geprüft | Auffälligkeiten |
|-------|--------|--------------------|-----------------|
| | | ja/nein | |

## Definition of Done

Alle Punkte erledigt oder N/A dokumentiert; verbleibende Risiken als Issue/Follow-up festgehalten.
