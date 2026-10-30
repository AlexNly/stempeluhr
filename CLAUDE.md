# stempeluhr

Public, German-language time tracking with Apple Shortcuts + CSV in iCloud Drive.
Audience: German colleagues — UI, docs and messages in German.
`AGENTS.md` = setup guide for agents installing it for a user; keep it in sync
with README/build.py when setup steps change.

- `build.py` generates the Shortcuts from `config.toml` (fallback
  `config.example.toml`); `--fertig` rebuilds the committed default sets in
  `kurzbefehle/<sprache>/` (no Wochenstatus — it embeds an absolute local path).
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
- Languages: `sprache = "de" | "en"` in config. Every user-visible string lives in
  `texte.py` (`TEXTE[sprache][key]`, same keys/placeholders in both — enforced by
  `tests/test_texte.py`); never hard-code UI text in `build.py`/`auswertung.py`.
  Config keys, file names and CSV format stay German/identical across languages.
  `--fertig` builds `kurzbefehle/de/` (config.example.toml) and `kurzbefehle/en/`
  (config.example.en.toml). Docs: `README.md` (de) + `README.en.md` — keep in sync.
- `auswertung.py`: holidays per Bundesland, ArbZG break rule on net time. Tests:
  `python3 -m unittest discover -s tests`.
- Never commit personal data (no real `zeiten.csv`, no `config.toml`, no `backups/`).
