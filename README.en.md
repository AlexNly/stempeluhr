# Stempeluhr

[🇩🇪 Deutsch](README.md) · 🇬🇧 English

Time tracking with Apple Shortcuts — clock in and out with a tap, widget or Siri
on iPhone and Mac, data as CSV in iCloud Drive. Plus a weekly report with an
hours account following German rules (breaks per the Working Hours Act / ArbZG,
public holidays per state).

- **No server, no account, no app** — just Shortcuts and a CSV file.
- **Reminders**: at 10:00 "Home Office today?" if you forgot to clock in;
  at 18:00 "done for today?" if a home-office session is still running.
- **Report** (Mac): weekly balance, hours account, absences.

## Installation

> 🤖 Using an AI agent (Claude Code, Codex, …)? Just say:
> *"Set up Stempeluhr for me in English: https://github.com/AlexNly/stempeluhr"* —
> the agent instructions are in [`AGENTS.md`](AGENTS.md).

### 1. Create the data folder

In the **Files** app (iPhone) or Finder: `iCloud Drive → Shortcuts` →
new folder **`Stempeluhr`**.

### 2. Import the shortcuts

Open the files from [`kurzbefehle/en/`](kurzbefehle/en/) on iPhone or Mac and
tap **"Add Shortcut"** for each:

| Shortcut | What it does |
|---|---|
| **Office Start** / **Home Office Start** | Clock in with a location |
| **Clock Out** | Clock out — appends a line to `zeiten.csv` |
| **HO Check** | For the 10:00 automation: not clocked in yet? → "Home Office today?" → start time |
| **HO End Check** | For the 18:00 automation: home office still running? → Clock out now / Stopped earlier … / Still working |

On first run iOS asks whether the shortcut may access the folder → **Allow**.
Run each shortcut once by hand before an automation uses it.

Other locations than "Office"/"Home Office"? → [Build your own shortcuts](#build-your-own-shortcuts).

### 3. Set up automations (optional)

Shortcuts → **Automation** → **+** → **Time of Day**:

| Time | Repeat | Shortcut |
|---|---|---|
| 10:00 | Weekly, Mon–Fri | HO Check |
| 18:00 | Weekly, Mon–Fri | HO End Check |

Choose **"Run Immediately"** and turn off "Notify When Run".

**Set them up on the iPhone, not the Mac.** Mac automations only run while the
Mac is awake — if the lid is closed at 10:00, nothing happens and it isn't made
up later. And only on **one** device, or every question shows up twice.

**Run each shortcut once by hand first** and allow file access. Otherwise the
first automatic run silently gets stuck on that prompt.

#### No question at 10:00?

1. Were you already clocked in? Then HO Check stays quiet on purpose.
2. Automation on the Mac instead of the iPhone? → The Mac was probably closed.
3. Automation set to "Ask Before Running" instead of "Run Immediately"?
4. All weekdays selected in the repeat setting?
5. Run HO Check by hand: if it asks, the automation is the problem; if you see
   an error or an access prompt, that was the cause.

## Data

Everything lives in `iCloud Drive/Shortcuts/Stempeluhr/` and can be edited in any
text editor or Excel/Numbers. File names and columns are the same in both
languages, so you can switch language at any time.

**`zeiten.csv`** — one line per work block (no header):

```
2026-10-26,09:12,17:40,508,Office
2026-10-27,08:55,12:30,215,Home Office
2026-10-27,13:15,17:05,230,Home Office
```

`date,start,end,gross_minutes,location`. Add forgotten days by hand.

**`abwesenheiten.csv`** (optional, by hand) — days without a target:

```
2026-08-03,Vacation
2026-08-04,Vacation
2026-11-12,Sick
```

The type is free text (Vacation, Sick, Day off, …) and is counted in the report.

**`laufend.txt`** — the last start (`Location|2026-10-27 08:55:00`); never
cleared — Clock Out uses `zeiten.csv` to tell whether you already clocked out.

> ⚠️ When editing by hand: don't let the file **end with an empty line** — the
> shortcuts append "on a new line", otherwise a blank line appears (the report
> ignores it, though).

## Report (Mac)

Requires Python ≥ 3.11 (`python3 --version`).

```sh
git clone https://github.com/AlexNly/stempeluhr.git
cd stempeluhr
cp config.example.en.toml config.toml   # weekly hours, state, … (sprache = "en")
python3 auswertung.py
```

```
=== Week of Mon 26.10.2026 ===
  Mon 26.10  gross 8h 06  break 30min  net 7h 36  balance -0h 06  (Office 8h 06)

=== Hours account ===
  Total balance:           +12h 40  (93 logged days)  ✅
  Ø last 10 days:           +0h 25
```

Rules:

- **Target** = weekly hours / 5 per weekday (Mon–Fri). Weekends, public holidays
  and days in `abwesenheiten.csv` have a target of 0 — work there counts as bonus.
- **Days without entries are ignored** (no deficit). Still log vacation/sick days
  if you want them counted.
- **Breaks** per § 4 ArbZG, only on days with *one* block (several blocks = the
  gaps are the break): more than 6 h of work → 30 min, more than 9 h → 45 min.
  The threshold applies to net time — 6h15 gross gives 6h00 net, not 5h45.
- **Public holidays**: statewide statutory holidays of the chosen German state.
  Holidays that only apply regionally (Assumption Day in parts of Bavaria, …):
  add them as `Day off` in `abwesenheiten.csv`.
- **Backup**: once a week the report copies the data to `backups/` (local,
  outside iCloud).

Tip: `python3 build.py` additionally creates the **Weekly Status** shortcut in
`dist/`, which shows the report with one click (or Siri) on the Mac.

## Build your own shortcuts

For your own locations, a different folder name or other tweaks (macOS
required — signing only works there):

```sh
cp config.example.en.toml config.toml   # orte = ["Office", "Client", "Home Office"], …
python3 build.py                        # → dist/*.shortcut
```

The config keys stay German (`orte` = locations, `wochenstunden` = weekly hours,
…); the comments in [`config.example.en.toml`](config.example.en.toml) explain
them. All texts live in [`texte.py`](texte.py).

When re-importing a changed version, delete the old shortcut first — "Replace"
sometimes creates a duplicate.

Tests: `python3 -m unittest discover -s tests`

## Limitations

- **HO Check doesn't know public holidays** — just tap "Cancel" on holidays.
- Automations only run while the device is on — on the Mac not while asleep and
  without catching up. Hence: iPhone.
- iCloud sync: clocking on two devices in quick succession can cause a sync
  conflict. The weekly backups help then.
- Not a legally binding time record — meant for your own overview.

## License

MIT — see [LICENSE](LICENSE).
