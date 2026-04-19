# Verifikation: PDF-Export v1.5 (klassisch + Modern HTML)

Abnahme-Checkliste für Release **1.5.0** und nachfolgende Modern-PDF-Updates. Abhaken, wenn erledigt oder **N/A** mit Kurzgrund.

## Pfad A – Klassisch (ReportLab)

- [ ] PDF erzeugen mit mehreren Terminen; Layout wie gewohnt
- [ ] Eintrag-Notizen: PDF-Annotations (Sticky) vorhanden, wo erwartet
- [ ] Optionen: Achsenzeiten, Blockzeiten, durchgängiges Raster – sichtbar korrekt

## Pfad B – Modern (HTML, Playwright / Chromium)

- [ ] PDF erzeugen; Datei beginnt mit `%PDF`
- [ ] Typografie wirkt einheitlich (Roboto); keine fehlenden Glyphen (DE/EN)
- [ ] Plantitel und Plan-Notiz erscheinen wie im UI
- [ ] Kurze und lange Blöcke: Titel/Notiz lesbar (Stufen-Typo), kein „Staub“ bei Notizen
- [ ] A4 und A5 Quer: kein harter Umbruch mitten in der Kopfzeile (visuell)

## UI / i18n

- [ ] Radio: Klassisch vs. Modern; Beschriftungen DE und EN plausibel
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
