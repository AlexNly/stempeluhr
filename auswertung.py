#!/usr/bin/env python3
"""Stempeluhr — Wochenauswertung und Stundenkonto aus zeiten.csv.

    python3 auswertung.py

Liest config.toml (sonst config.example.toml) und die Dateien aus
"iCloud Drive/Shortcuts/<ordner>/". Legt wöchentlich ein lokales Backup an.
"""
from __future__ import annotations

import csv
import datetime as dt
import io
import shutil
import time
import tomllib
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
ICLOUD_SHORTCUTS = Path.home() / "Library/Mobile Documents/iCloud~is~workflow~my~workflows/Documents"
FIELDS = ["datum", "start", "ende", "brutto_min", "ort"]
BACKUP_EVERY_DAYS = 7
ROLLING_WINDOW_DAYS = 10


def load_config() -> dict:
    path = HERE / "config.toml"
    if not path.exists():
        path = HERE / "config.example.toml"
    return tomllib.loads(path.read_text(encoding="utf-8"))


# --- Feiertage ------------------------------------------------------------------

BUNDESLAENDER = {"BW", "BY", "BE", "BB", "HB", "HH", "HE", "MV",
                 "NI", "NW", "RP", "SL", "SN", "ST", "SH", "TH"}


def easter_sunday(year: int) -> dt.date:
    """Gauß'sche Osterformel."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    g = (8 * b + 13) // 25
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return dt.date(year, month, day + 1)


def holidays(year: int, land: str) -> dict[dt.date, str]:
    """Gesetzliche Feiertage (landesweit) für ein Bundesland.

    Nur regional geltende Feiertage (z.B. Mariä Himmelfahrt in Teilen Bayerns,
    Fronleichnam in Teilen Sachsens/Thüringens, Augsburger Friedensfest) fehlen —
    die bei Bedarf als "Frei" in abwesenheiten.csv eintragen.
    """
    easter = easter_sunday(year)
    off = lambda days: easter + dt.timedelta(days=days)
    d = dt.date
    result = {
        d(year, 1, 1): "Neujahr",
        off(-2): "Karfreitag",
        off(1): "Ostermontag",
        d(year, 5, 1): "Tag der Arbeit",
        off(39): "Christi Himmelfahrt",
        off(50): "Pfingstmontag",
        d(year, 10, 3): "Tag der Deutschen Einheit",
        d(year, 12, 25): "1. Weihnachtstag",
        d(year, 12, 26): "2. Weihnachtstag",
    }
    if land in {"BW", "BY", "ST"}:
        result[d(year, 1, 6)] = "Heilige Drei Könige"
    if (land == "BE" and year >= 2019) or (land == "MV" and year >= 2023):
        result[d(year, 3, 8)] = "Internationaler Frauentag"
    if land in {"BW", "BY", "HE", "NW", "RP", "SL"}:
        result[off(60)] = "Fronleichnam"
    if land == "SL":
        result[d(year, 8, 15)] = "Mariä Himmelfahrt"
    if land == "TH" and year >= 2019:
        result[d(year, 9, 20)] = "Weltkindertag"
    if land in {"BB", "MV", "SN", "ST", "TH"} or (land in {"HB", "HH", "NI", "SH"} and year >= 2018):
        result[d(year, 10, 31)] = "Reformationstag"
    if land in {"BW", "BY", "NW", "RP", "SL"}:
        result[d(year, 11, 1)] = "Allerheiligen"
    if land == "SN":
        nov22 = d(year, 11, 22)  # Mittwoch vor dem 23. November
        result[nov22 - dt.timedelta(days=(nov22.weekday() - 2) % 7)] = "Buß- und Bettag"
    return result


# --- Regeln ---------------------------------------------------------------------

def pause_minutes(brutto: int) -> int:
    """Pflichtpause nach § 4 ArbZG für eine durchgehende Session.

    Die Schwellen (> 6h → 30 min, > 9h → 45 min) gelten für die *Arbeitszeit*,
    also netto: der Abzug drückt die Nettozeit nie unter die auslösende Schwelle.
    """
    if brutto <= 360:
        return 0
    if brutto <= 570:
        return min(30, brutto - 360)
    return min(45, 30 + brutto - 570)


def fmt(minutes: int) -> str:
    h, m = divmod(max(minutes, 0), 60)
    return f"{h}h {m:02d}"


def signed_fmt(minutes: int) -> str:
    if minutes == 0:
        return "±0h 00"
    return f"{'+' if minutes > 0 else '-'}{fmt(abs(minutes))}"


# --- Daten ----------------------------------------------------------------------

def read_text_retry(path: Path, retries: int = 6, delay: float = 0.3) -> str:
    """Datei lesen mit Wiederholung — fängt kurze iCloud-Sperren ab."""
    for attempt in range(retries):
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            if attempt == retries - 1:
                raise
            time.sleep(delay)
    return ""


def read_rows(path: Path, fields: list[str]) -> list[dict]:
    """CSV ohne Pflicht-Kopfzeile lesen; leere Zeilen und Kopfzeile werden übersprungen."""
    if not path.exists():
        return []
    rows = []
    for values in csv.reader(io.StringIO(read_text_retry(path))):
        if not values or values[0] == fields[0]:
            continue
        rows.append(dict(zip(fields, (v.strip() for v in values))))
    return rows


def day_summary(entries: list[dict]):
    """Pro Tag: brutto pro Ort, Gesamt-Brutto, Pause, Netto."""
    loc_brutto: dict[str, int] = defaultdict(int)
    for e in entries:
        loc_brutto[e["ort"]] += int(e["brutto_min"])
    total = sum(loc_brutto.values())
    # Bei mehreren Sessions am Tag sind die Lücken echte Pausen → kein Abzug
    pause = pause_minutes(total) if len(entries) == 1 else 0
    return loc_brutto, total, pause, total - pause


def maybe_backup(data: Path) -> None:
    """Lokaler Snapshot nach backups/, wenn der letzte ≥ 7 Tage alt ist."""
    backups = HERE / "backups"
    backups.mkdir(exist_ok=True)
    snapshots = []
    for p in backups.iterdir():
        try:
            snapshots.append(dt.date.fromisoformat(p.name))
        except ValueError:
            pass
    today = dt.date.today()
    if snapshots and (today - max(snapshots)).days < BACKUP_EVERY_DAYS:
        return
    dst = backups / today.isoformat()
    dst.mkdir(exist_ok=True)
    for f in data.iterdir():
        if f.suffix in {".csv", ".txt"}:
            shutil.copy2(f, dst / f.name)
    print(f"💾 Backup angelegt: {dst.relative_to(HERE)}\n")


# --- Auswertung -----------------------------------------------------------------

def main() -> None:
    cfg = load_config()
    land = cfg["bundesland"]
    if land not in BUNDESLAENDER:
        raise SystemExit(f"Unbekanntes Bundesland {land!r} — erlaubt: {' '.join(sorted(BUNDESLAENDER))}")
    data = ICLOUD_SHORTCUTS / cfg["ordner"]
    if not data.is_dir():
        raise SystemExit(f"Datenordner fehlt: {data}\nEinmal einen Start-Kurzbefehl ausführen.")
    daily_target_min = round(cfg["wochenstunden"] * 60 / 5)

    maybe_backup(data)
    rows = read_rows(data / "zeiten.csv", FIELDS)
    absences = {dt.date.fromisoformat(r["datum"]): r["typ"]
                for r in read_rows(data / "abwesenheiten.csv", ["datum", "typ"])}

    def day_off_reason(d: dt.date) -> str | None:
        if d in absences:
            return absences[d]
        if name := holidays(d.year, land).get(d):
            return name
        if d.weekday() >= 5:
            return "Wochenende"
        return None

    def daily_target(d: dt.date) -> int:
        return 0 if day_off_reason(d) else daily_target_min

    by_date: dict[dt.date, list[dict]] = defaultdict(list)
    for row in rows:
        by_date[dt.date.fromisoformat(row["datum"])].append(row)
    days = {d: day_summary(e) for d, e in by_date.items()}
    monday_of = lambda d: d - dt.timedelta(days=d.weekday())

    week_brutto: dict[dt.date, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    week_netto: dict[dt.date, int] = defaultdict(int)
    for d, (loc_brutto, _, _, netto) in days.items():
        for loc, m in loc_brutto.items():
            week_brutto[monday_of(d)][loc] += m
        week_netto[monday_of(d)] += netto

    def week_saldo(monday: dt.date) -> int:
        return sum(days[d][3] - daily_target(d) for d in days if monday_of(d) == monday)

    today = dt.date.today()
    current_monday = monday_of(today)

    # Laufende Session — Start ohne passende Zeile in zeiten.csv
    laufend = data / "laufend.txt"
    if laufend.exists() and "|" in (text := read_text_retry(laufend).strip()):
        ort, stamp = text.split("|", 1)
        try:
            start = dt.datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            start = None
        logged = any(r["datum"] == start.date().isoformat() and r["start"] == start.strftime("%H:%M")
                     for r in rows) if start else True
        if not logged:
            elapsed = int((dt.datetime.now() - start).total_seconds() // 60)
            print(f"⏱  {ort} seit {start.strftime('%a %H:%M')} — {fmt(elapsed)}\n")

    print(f"=== Woche ab Mo {current_monday.strftime('%d.%m.%Y')} ===")
    current_dates = sorted(d for d in days if d >= current_monday)
    if not current_dates:
        print("(noch keine Einträge diese Woche)")
    else:
        for d in current_dates:
            loc_brutto, total, pause, netto = days[d]
            locs = " + ".join(f"{loc} {fmt(m)}" for loc, m in sorted(loc_brutto.items()))
            reason = day_off_reason(d)
            tag = f"  [{reason}]" if reason else ""
            print(f"  {d.strftime('%a %d.%m')}  brutto {fmt(total)}  pause {pause:>2}min  "
                  f"netto {fmt(netto)}  saldo {signed_fmt(netto - daily_target(d))}  ({locs}){tag}")
        print("\n  Wochensumme:")
        for loc, m in sorted(week_brutto[current_monday].items()):
            print(f"    {loc:12} {fmt(m)} brutto")
        n = len(current_dates)
        print(f"    {'NETTO':12} {fmt(week_netto[current_monday])}  ({n} Tag{'e' if n != 1 else ''})")
        print(f"    {'SALDO':12} {signed_fmt(week_saldo(current_monday))}")

    past_weeks = sorted((w for w in week_netto if w < current_monday), reverse=True)[:10]
    if past_weeks:
        print(f"\n=== Vorherige {len(past_weeks)} Wochen ===")
        for w in past_weeks:
            locs = " + ".join(f"{loc} {fmt(m)}" for loc, m in sorted(week_brutto[w].items()))
            n = sum(1 for d in days if monday_of(d) == w)
            print(f"  KW {w.isocalendar().week:02d} ({w.strftime('%d.%m')}-"
                  f"{(w + dt.timedelta(days=6)).strftime('%d.%m')}): netto {fmt(week_netto[w])} "
                  f"({n}d)  saldo {signed_fmt(week_saldo(w))}  ({locs})")

    saldos = [days[d][3] - daily_target(d) for d in sorted(days)]
    if not saldos:
        return
    total_saldo = sum(saldos)
    recent = saldos[-ROLLING_WINDOW_DAYS:]
    recent_avg = sum(recent) // len(recent)
    print("\n=== Stundenkonto ===")
    print(f"  Saldo gesamt:           {signed_fmt(total_saldo):>8}  ({len(saldos)} "
          f"{'geloggter Tag' if len(saldos) == 1 else 'geloggte Tage'})  "
          f"{'✅' if total_saldo >= 0 else '📉'}")
    print(f"  Ø pro Tag (gesamt):     {signed_fmt(total_saldo // len(saldos)):>8}")
    if len(recent) > 1:
        print(f"  Ø letzte {len(recent):>2} Tage:        {signed_fmt(recent_avg):>8}")

    counts = defaultdict(int)
    for typ in absences.values():
        counts[typ] += 1
    bonus = sum(days[d][3] for d in days if day_off_reason(d))
    if counts or bonus:
        print("\n=== Abwesenheiten ===")
        for typ, n in sorted(counts.items()):
            print(f"  {typ + ':':8}{n} Tag{'e' if n != 1 else ''}")
        if bonus:
            print(f"  Gearbeitet an freien Tagen: {fmt(bonus)} (zählt als Bonus)")

    if len(recent) >= 3:
        if recent_avg > 30:
            print("\n  ⚠️  Letzte Zeit deutlich über Soll — runterfahren wäre gut.")
        elif recent_avg < -30:
            print("\n  📉 Letzte Zeit unter Soll — bei Gelegenheit etwas mehr.")
        else:
            print("\n  ✅ Du bist im grünen Bereich.")


if __name__ == "__main__":
    main()
