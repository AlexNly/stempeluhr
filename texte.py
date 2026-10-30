"""Alle sichtbaren Texte (Kurzbefehle + Auswertung) auf Deutsch und Englisch.

Sprache über `sprache = "de" | "en"` in config.toml. Dateinamen und Datenformat
sind sprachunabhängig — ein späterer Wechsel bricht keine Daten.
"""
from __future__ import annotations

SPRACHEN = ("de", "en")

TEXTE: dict[str, dict[str, str]] = {
    "de": {
        # Kurzbefehle — Namen
        "sc_start": "{ort} Start",
        "sc_ende": "Feierabend",
        "sc_ho_check": "HO Check",
        "sc_ho_ende_check": "HO Ende Check",
        "sc_status": "Wochenstatus",
        # Kurzbefehle — Texte
        "gestartet": "{ort} gestartet: ￼",
        "schon_aus": "Schon ausgestempelt.",
        "feierabend": "Feierabend (￼): ￼–￼, ￼ min",
        "ho_titel": "{ho} heute?",
        "ho_frage": "Noch nicht eingestempelt. Ist heute ein {ho}-Tag?",
        "seit_wann": "Seit wann arbeitest du?",
        "ende_prompt": "{ho} seit ￼ — Feierabend?",
        "menu_jetzt": "Jetzt ausstempeln",
        "menu_frueher": "Früher aufgehört …",
        "menu_weiter": "Arbeite noch",
        "wann_aufgehoert": "Wann hast du aufgehört?",
        # Build
        "err_ho": "homeoffice = {ho!r} steht nicht in orte = {orte}",
        "err_ortname": "Ortsnamen dürfen weder '|' noch ',' enthalten.",
        # Auswertung
        "wochentage": "Mo Di Mi Do Fr Sa So",
        "backup": "💾 Backup angelegt: {pfad}\n",
        "err_land": "Unbekanntes Bundesland {land!r} — erlaubt: {alle}",
        "err_ordner": "Datenordner fehlt: {pfad}\nEinmal einen Start-Kurzbefehl ausführen.",
        "laufend": "⏱  {ort} seit {wtag} {zeit} — {dauer}\n",
        "woche_ab": "=== Woche ab Mo {datum} ===",
        "keine_eintraege": "(noch keine Einträge diese Woche)",
        "tag": "  {wtag} {datum}  brutto {brutto}  pause {pause:>2}min  netto {netto}  saldo {saldo}  ({orte}){grund}",
        "wochensumme": "\n  Wochensumme:",
        "brutto_zeile": "    {ort:12} {dauer} brutto",
        "netto_zeile": "    NETTO        {dauer}  ({n} {tage})",
        "saldo_zeile": "    SALDO        {saldo}",
        "tag_1": "Tag", "tag_n": "Tage",
        "vorherige": "\n=== Vorherige {n} Wochen ===",
        "kw_zeile": "  KW {kw:02d} ({von}-{bis}): netto {netto} ({n}d)  saldo {saldo}  ({orte})",
        "konto": "\n=== Stundenkonto ===",
        "saldo_gesamt": "  Saldo gesamt:           {saldo:>8}  ({n} {tage})  {icon}",
        "geloggt_1": "geloggter Tag", "geloggt_n": "geloggte Tage",
        "schnitt_gesamt": "  Ø pro Tag (gesamt):     {saldo:>8}",
        "schnitt_letzte": "  Ø letzte {n:>2} Tage:        {saldo:>8}",
        "abwesenheiten": "\n=== Abwesenheiten ===",
        "abw_zeile": "  {typ:8}{n} {tage}",
        "bonus": "  Gearbeitet an freien Tagen: {dauer} (zählt als Bonus)",
        "zu_viel": "\n  ⚠️  Letzte Zeit deutlich über Soll — runterfahren wäre gut.",
        "zu_wenig": "\n  📉 Letzte Zeit unter Soll — bei Gelegenheit etwas mehr.",
        "gruen": "\n  ✅ Du bist im grünen Bereich.",
        "wochenende": "Wochenende",
    },
    "en": {
        "sc_start": "{ort} Start",
        "sc_ende": "Clock Out",
        "sc_ho_check": "HO Check",
        "sc_ho_ende_check": "HO End Check",
        "sc_status": "Weekly Status",
        "gestartet": "{ort} started: ￼",
        "schon_aus": "Already clocked out.",
        "feierabend": "Clocked out (￼): ￼–￼, ￼ min",
        "ho_titel": "{ho} today?",
        "ho_frage": "Not clocked in yet. Is today a {ho} day?",
        "seit_wann": "Since when have you been working?",
        "ende_prompt": "{ho} since ￼ — done for today?",
        "menu_jetzt": "Clock out now",
        "menu_frueher": "Stopped earlier …",
        "menu_weiter": "Still working",
        "wann_aufgehoert": "When did you stop?",
        "err_ho": "homeoffice = {ho!r} is not in orte = {orte}",
        "err_ortname": "Location names must not contain '|' or ','.",
        "wochentage": "Mon Tue Wed Thu Fri Sat Sun",
        "backup": "💾 Backup created: {pfad}\n",
        "err_land": "Unknown state {land!r} — allowed: {alle}",
        "err_ordner": "Data folder missing: {pfad}\nRun a Start shortcut once.",
        "laufend": "⏱  {ort} since {wtag} {zeit} — {dauer}\n",
        "woche_ab": "=== Week of Mon {datum} ===",
        "keine_eintraege": "(no entries this week yet)",
        "tag": "  {wtag} {datum}  gross {brutto}  break {pause:>2}min  net {netto}  balance {saldo}  ({orte}){grund}",
        "wochensumme": "\n  Week total:",
        "brutto_zeile": "    {ort:12} {dauer} gross",
        "netto_zeile": "    NET          {dauer}  ({n} {tage})",
        "saldo_zeile": "    BALANCE      {saldo}",
        "tag_1": "day", "tag_n": "days",
        "vorherige": "\n=== Previous {n} weeks ===",
        "kw_zeile": "  CW {kw:02d} ({von}-{bis}): net {netto} ({n}d)  balance {saldo}  ({orte})",
        "konto": "\n=== Hours account ===",
        "saldo_gesamt": "  Total balance:          {saldo:>8}  ({n} {tage})  {icon}",
        "geloggt_1": "logged day", "geloggt_n": "logged days",
        "schnitt_gesamt": "  Ø per day (overall):    {saldo:>8}",
        "schnitt_letzte": "  Ø last {n:>2} days:         {saldo:>8}",
        "abwesenheiten": "\n=== Absences ===",
        "abw_zeile": "  {typ:8}{n} {tage}",
        "bonus": "  Worked on days off: {dauer} (counts as bonus)",
        "zu_viel": "\n  ⚠️  Well above target lately — time to slow down.",
        "zu_wenig": "\n  📉 Below target lately — a bit more when you can.",
        "gruen": "\n  ✅ You're on track.",
        "wochenende": "Weekend",
    },
}

# Englische Namen der Feiertage (deutsche Namen sind die Schlüssel in auswertung.holidays)
FEIERTAGE_EN = {
    "Neujahr": "New Year's Day", "Karfreitag": "Good Friday", "Ostermontag": "Easter Monday",
    "Tag der Arbeit": "Labour Day", "Christi Himmelfahrt": "Ascension Day",
    "Pfingstmontag": "Whit Monday", "Tag der Deutschen Einheit": "German Unity Day",
    "1. Weihnachtstag": "Christmas Day", "2. Weihnachtstag": "Boxing Day",
    "Heilige Drei Könige": "Epiphany", "Internationaler Frauentag": "Women's Day",
    "Fronleichnam": "Corpus Christi", "Mariä Himmelfahrt": "Assumption Day",
    "Weltkindertag": "Children's Day", "Reformationstag": "Reformation Day",
    "Allerheiligen": "All Saints' Day", "Buß- und Bettag": "Day of Repentance",
}


def texte(sprache: str) -> dict[str, str]:
    if sprache not in SPRACHEN:
        raise SystemExit(f"sprache = {sprache!r} — erlaubt/allowed: {', '.join(SPRACHEN)}")
    return TEXTE[sprache]
