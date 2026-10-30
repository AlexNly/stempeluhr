# AGENTS.md — Stempeluhr für jemanden einrichten

Anleitung für KI-Agenten (Claude Code, Codex, …), die Stempeluhr auf dem Mac
einer Person einrichten. **Zuerst die Sprache klären** (Deutsch oder Englisch) und
dann in dieser Sprache mit der Person sprechen.
(English speakers: follow the same steps; use `config.example.en.toml` and the
English shortcut names in parentheses below.)
Hinweise zur Weiterentwicklung des Codes stehen in `CLAUDE.md`.

## Was du tun kannst — und was nicht

| Schritt | Wer |
|---|---|
| Voraussetzungen prüfen, Repo klonen, `config.toml` schreiben | du |
| Datenordner anlegen, Kurzbefehle bauen | du |
| Kurzbefehle importieren („Kurzbefehl hinzufügen“ klicken) | **die Person** — du öffnest nur die Dateien |
| Dateizugriff beim ersten Lauf erlauben | **die Person** |
| Automationen (10:00 / 18:00) anlegen | **die Person** — dafür gibt es keine CLI |
| Einrichtung auf dem iPhone | **die Person** — Kurzbefehle synchronisieren per iCloud |

## Ablauf

### 1. Voraussetzungen

```sh
sw_vers -productVersion        # macOS; Kurzbefehle-CLI `shortcuts` muss existieren
python3 --version              # ≥ 3.11 (tomllib)
ls ~/Library/Mobile\ Documents/iCloud~is~workflow~my~workflows/Documents
```

Fehlt der letzte Ordner: iCloud Drive für Kurzbefehle ist aus → Person bitten,
in *Systemeinstellungen → Apple-Account → iCloud → iCloud Drive* „Kurzbefehle“
zu aktivieren. Nicht selbst anlegen.

### 2. Klonen und Konfiguration erfragen

```sh
git clone https://github.com/AlexNly/stempeluhr.git ~/stempeluhr   # oder wohin die Person will
cd ~/stempeluhr && cp config.example.toml config.toml      # Englisch: config.example.en.toml
```

Die Person **fragen** (nicht raten) und `config.toml` füllen:

- `sprache` — `"de"` oder `"en"`: Texte der Kurzbefehle und der Auswertung.
  Bestimmt auch die Kurzbefehl-Namen (Feierabend ↔ Clock Out, HO Ende Check ↔
  HO End Check, Wochenstatus ↔ Weekly Status). Datenformat ist in beiden gleich.
- `wochenstunden` — laut Arbeitsvertrag, netto (z.B. 38.5, 40, Teilzeit 20)
- `bundesland` — Kürzel (NW, BY, BE, …), für die Feiertage
- `orte` — wo sie arbeitet, z.B. `["Büro", "Homeoffice"]` oder Stadtnamen.
  Keine `|` oder `,` in Namen.
- `homeoffice` — welcher davon Homeoffice ist (muss in `orte` stehen)
- `ordner` — Standard `Stempeluhr` lassen, außer er existiert schon (siehe 3.)

### 3. Datenordner anlegen

```sh
D=~/Library/Mobile\ Documents/iCloud~is~workflow~my~workflows/Documents/Stempeluhr
ls "$D" 2>/dev/null && echo "EXISTIERT SCHON" || mkdir "$D"
```

**Existiert er schon** (z.B. Neuinstallation): Inhalt zeigen, nichts überschreiben
oder löschen. Vorhandene `zeiten.csv` weiterverwenden.

Ohne diesen Ordner schlagen „Feierabend“ und „HO Check“ mit „Datei existiert nicht“ fehl.

### 4. Kurzbefehle bauen und importieren

```sh
python3 build.py               # → dist/*.shortcut (inkl. Wochenstatus für den Mac)
shortcuts list                 # Namenskonflikte prüfen
```

Gibt es schon Kurzbefehle mit gleichem Namen (`<Ort> Start`, `Feierabend`/`Clock Out`,
`HO Check`, `HO Ende Check`/`HO End Check`, `Wochenstatus`/`Weekly Status`): Person fragen, ob die alten weg
können — sie selbst löschen lassen. Import legt sonst Duplikate an
(„Ersetzen“ ist unzuverlässig).

Dann **einzeln** öffnen und nach jedem die Person „Kurzbefehl hinzufügen“ klicken lassen:

```sh
open "dist/Büro Start.shortcut"   # usw. für jede Datei in dist/
```

Hängt die Kurzbefehle-App beim Import: `killall Shortcuts`, Datei erneut öffnen.

Prüfen: `shortcuts list` enthält alle erwarteten Namen.

### 5. Testen — ohne Daten zu verändern

```sh
shortcuts run "Feierabend"     # ohne laufenden Start: endet still, schreibt nichts
python3 auswertung.py          # mit leerem Ordner: "(noch keine Einträge diese Woche)"
```

**Nicht** zum Testen `<Ort> Start` ausführen: das überschreibt `laufend.txt` und
würde bei einer laufenden Session deren Startzeit zerstören. Den ersten echten
Start macht die Person selbst.

Hat die Person schon einen Eintrag, darf sie zur Probe einmal „Büro Start“ und
eine Minute später „Feierabend“ tippen → `zeiten.csv` bekommt eine Zeile, die
sie danach von Hand löschen kann.

### 6. Automationen und iPhone (Anleitung an die Person)

**Auf dem iPhone**, nur dort: Kurzbefehle → Automation → + → Tageszeit

- 10:00, wöchentlich Mo–Fr, „Sofort ausführen“ → **HO Check**
- 18:00, wöchentlich Mo–Fr, „Sofort ausführen“ → **HO Ende Check**

Nicht auf dem Mac einrichten lassen: Mac-Automationen laufen nur bei wachem Mac
und werden nicht nachgeholt (häufigste Ursache für „um 10 kam nichts“). Du kannst
Automationen nicht auslesen — bei Problemen die Checkliste „Um 10 Uhr kam keine
Frage?“ im README mit der Person durchgehen; `laufend.txt` zeigt, ob sie schon
eingestempelt war.

Auf dem iPhone jeden Kurzbefehl **einmal von Hand** starten und den
Dateizugriff erlauben — sonst blockiert die Rückfrage später die Automation.

## Bestehende Daten übernehmen

Hat die Person Zeiten aus einem anderen System: nach `zeiten.csv` im Format
`datum,start,ende,brutto_min,ort` konvertieren (ohne Kopfzeile, `datum` als
`YYYY-MM-DD`, Zeiten `HH:MM`, `brutto_min` = Ende − Start in Minuten,
chronologisch sortiert, **ohne abschließenden Zeilenumbruch**). Vorher eine
Kopie der Quelle anlegen. Urlaub/Krank als `datum,typ` nach `abwesenheiten.csv`.

## Regeln

- Nie Daten in `iCloud Drive/Shortcuts/<ordner>/` löschen oder überschreiben,
  ohne vorher eine Kopie anzulegen und die Person zu fragen.
- `config.toml`, `dist/` und `backups/` sind persönlich und gitignored — nie committen.
- Kurzbefehle nicht selbst löschen oder umbenennen — das macht die Person.
