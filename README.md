# Stempeluhr

Arbeitszeiterfassung mit Apple-Kurzbefehlen — ein- und ausstempeln per Tap, Widget
oder Siri auf iPhone und Mac, Daten als CSV in iCloud Drive. Dazu eine
Wochenauswertung mit Stundenkonto nach deutschen Regeln (Pausen nach ArbZG,
Feiertage pro Bundesland).

- **Kein Server, kein Konto, keine App** — nur Kurzbefehle und eine CSV-Datei.
- **Erinnerungen**: um 10 Uhr „Homeoffice heute?“, falls du vergessen hast
  einzustempeln; um 18 Uhr „Feierabend?“, falls du im Homeoffice noch läufst.
- **Auswertung** (Mac): Wochensaldo, Stundenkonto, Abwesenheiten.

## Installation

> 🤖 Mit einem KI-Agenten (Claude Code, Codex, …)? Einfach sagen:
> *„Richte mir Stempeluhr ein: https://github.com/AlexNly/stempeluhr“* —
> die Anleitung für den Agenten steht in [`AGENTS.md`](AGENTS.md).

### 1. Datenordner anlegen

In der **Dateien**-App (iPhone) bzw. im Finder: `iCloud Drive → Shortcuts` →
neuer Ordner **`Stempeluhr`**.

### 2. Kurzbefehle importieren

Die Dateien aus [`kurzbefehle/`](kurzbefehle/) auf iPhone oder Mac öffnen und
jeweils **„Kurzbefehl hinzufügen“** tippen:

| Kurzbefehl | Was er tut |
|---|---|
| **Büro Start** / **Homeoffice Start** | Einstempeln mit Ort |
| **Feierabend** | Ausstempeln — schreibt eine Zeile nach `zeiten.csv` |
| **HO Check** | Für die 10-Uhr-Automation: noch nicht eingestempelt? → „Homeoffice heute?“ → Startzeit |
| **HO Ende Check** | Für die 18-Uhr-Automation: Homeoffice läuft noch? → Jetzt / Früher aufgehört … / Arbeite noch |

Beim ersten Ausführen fragt iOS, ob der Kurzbefehl auf den Ordner zugreifen darf
→ **Erlauben**. Am besten jeden Kurzbefehl einmal von Hand starten, bevor eine
Automation ihn nutzt.

Andere Orte als „Büro“/„Homeoffice“? → [Eigene Kurzbefehle bauen](#eigene-kurzbefehle-bauen).

### 3. Automationen einrichten (optional)

Kurzbefehle → **Automation** → **+** → **Tageszeit**:

| Uhrzeit | Wiederholen | Kurzbefehl |
|---|---|---|
| 10:00 | Wöchentlich, Mo–Fr | HO Check |
| 18:00 | Wöchentlich, Mo–Fr | HO Ende Check |

Jeweils **„Sofort ausführen“** wählen und „Bei Ausführung mitteilen“ ausschalten.

**Auf dem iPhone einrichten, nicht auf dem Mac.** Mac-Automationen laufen nur,
wenn der Mac wach ist — ist er um 10 Uhr zugeklappt, passiert nichts, und es wird
auch nicht nachgeholt. Und nur auf **einem** Gerät, sonst kommt jede Frage doppelt.

**Vorher jeden Kurzbefehl einmal von Hand starten** und den Dateizugriff
erlauben. Sonst bleibt die erste automatische Ausführung still an dieser
Rückfrage hängen.

#### Um 10 Uhr kam keine Frage?

1. Warst du schon eingestempelt? Dann fragt HO Check absichtlich nicht.
2. Automation auf dem Mac statt dem iPhone? → Mac war vermutlich zu.
3. Automation steht auf „Vor Ausführen fragen“ statt „Sofort ausführen“?
4. Wochentage in der Wiederholung vollständig ausgewählt?
5. HO Check einmal von Hand starten: fragt er, liegt es an der Automation;
   kommt eine Fehlermeldung oder Zugriffsabfrage, war das die Ursache.

## Daten

Alles liegt in `iCloud Drive/Shortcuts/Stempeluhr/` und lässt sich mit jedem
Texteditor oder Excel/Numbers bearbeiten:

**`zeiten.csv`** — eine Zeile pro Arbeitsblock (ohne Kopfzeile):

```
2026-10-26,09:12,17:40,508,Büro
2026-10-27,08:55,12:30,215,Homeoffice
2026-10-27,13:15,17:05,230,Homeoffice
```

`datum,start,ende,brutto_min,ort`. Vergessene Tage einfach von Hand nachtragen.

**`abwesenheiten.csv`** (optional, von Hand) — Tage ohne Soll:

```
2026-08-03,Urlaub
2026-08-04,Urlaub
2026-11-12,Krank
```

Der Typ ist frei wählbar (Urlaub, Krank, Frei, …) und wird in der Auswertung gezählt.

**`laufend.txt`** — der letzte Start (`Ort|2026-10-27 08:55:00`); wird nicht
geleert, der Feierabend erkennt an `zeiten.csv`, ob schon ausgestempelt wurde.

> ⚠️ Beim Bearbeiten von Hand: die Datei **nicht mit einer Leerzeile enden** lassen —
> die Kurzbefehle hängen neue Zeilen „auf neuer Zeile“ an, sonst entsteht eine
> Leerzeile (wird von der Auswertung aber ignoriert).

## Auswertung (Mac)

Voraussetzung: Python ≥ 3.11 (`python3 --version`).

```sh
git clone https://github.com/AlexNly/stempeluhr.git
cd stempeluhr
cp config.example.toml config.toml   # Wochenstunden, Bundesland, … anpassen
python3 auswertung.py
```

```
=== Woche ab Mo 26.10.2026 ===
  Mon 26.10  brutto 8h 06  pause 30min  netto 7h 36  saldo -0h 06  (Büro 8h 06)

=== Stundenkonto ===
  Saldo gesamt:            +12h 40  (93 geloggte Tage)  ✅
  Ø letzte 10 Tage:         +0h 25
```

Regeln:

- **Soll** = Wochenstunden / 5 pro Werktag (Mo–Fr). Wochenenden, Feiertage und
  Tage in `abwesenheiten.csv` haben Soll 0 — Arbeit dort zählt als Bonus.
- **Nicht erfasste Tage werden ignoriert** (kein Minus). Urlaub/Krankheit trotzdem
  eintragen, wenn du sie gezählt haben willst.
- **Pause** nach § 4 ArbZG, nur bei Tagen mit *einem* Block (mehrere Blöcke =
  die Lücken sind die Pause): mehr als 6 h Arbeit → 30 min, mehr als 9 h → 45 min.
  Die Schwelle gilt für die Nettozeit — 6h15 brutto ergibt 6h00 netto, nicht 5h45.
- **Feiertage**: landesweite gesetzliche Feiertage des Bundeslands. Nur regional
  geltende (Mariä Himmelfahrt in Teilen Bayerns, Augsburger Friedensfest, …)
  als `Frei` in `abwesenheiten.csv` eintragen.
- **Backup**: einmal pro Woche kopiert die Auswertung die Daten nach `backups/`
  (lokal, außerhalb von iCloud).

Tipp: `python3 build.py` erzeugt in `dist/` zusätzlich den Kurzbefehl
**Wochenstatus**, der die Auswertung per Klick (oder Siri) auf dem Mac zeigt.

## Eigene Kurzbefehle bauen

Für eigene Orte, einen anderen Ordnernamen oder Anpassungen (macOS nötig — das
Signieren geht nur dort):

```sh
cp config.example.toml config.toml   # orte = ["Büro", "Kunde", "Homeoffice"], …
python3 build.py                     # → dist/*.shortcut
```

Die Kurzbefehle werden in [`build.py`](build.py) als Python-Code beschrieben
(Bausteine in [`shortcuts/sclib.py`](shortcuts/sclib.py)) und mit
`shortcuts sign` signiert. Beim erneuten Import einer geänderten Version den alten
Kurzbefehl vorher löschen — „Ersetzen“ legt teils ein Duplikat an.

Tests: `python3 -m unittest discover -s tests`

## Grenzen

- **HO Check kennt keine Feiertage** — an Feiertagen einfach „Abbrechen“.
- Automationen laufen nur, wenn das Gerät an ist — auf dem Mac nicht im
  Ruhezustand und ohne Nachholen. Deshalb aufs iPhone.
- iCloud-Sync: Wer auf zwei Geräten kurz hintereinander stempelt, kann einen
  Sync-Konflikt bekommen. Die wöchentlichen Backups helfen dann.
- Keine rechtsverbindliche Zeiterfassung — gedacht für den eigenen Überblick.

## Lizenz

MIT — siehe [LICENSE](LICENSE).
