# stempeluhr

Public, German-language time tracking with Apple Shortcuts + CSV in iCloud Drive.
Audience: German colleagues — UI, docs and messages in German.

- `build.py` generates the Shortcuts from `config.toml` (fallback
  `config.example.toml`); `--fertig` rebuilds the committed default set in
  `kurzbefehle/` (no Wochenstatus — it embeds an absolute local path).
  Helpers in `shortcuts/sclib.py`; signing via `shortcuts sign -m anyone` (macOS only).
- File references use `WFFileLocationType: Shortcuts` + `relativeSubpath` only —
  never commit device/account-specific IDs (crossDeviceItemID, fileProviderDomainID).
- Data (`iCloud Drive/Shortcuts/<ordner>/`): `laufend.txt` = `Ort|yyyy-MM-dd HH:mm:ss`
  (never cleared), `zeiten.csv` = `datum,start,ende,brutto_min,ort` without header,
  appended "on new line" (so files must not end in a newline), `abwesenheiten.csv`
  = `datum,typ`.
- Gotchas: the "Time" ask returns the *next* occurrence of that time → always take
  the date from "now", only HH:mm from the input. "Get File" fails if the data
  folder doesn't exist (README step 1). Re-import "Replace" can duplicate.
- `auswertung.py`: holidays per Bundesland, ArbZG break rule on net time. Tests:
  `python3 -m unittest discover -s tests`.
- Never commit personal data (no real `zeiten.csv`, no `config.toml`, no `backups/`).
