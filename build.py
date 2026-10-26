#!/usr/bin/env python3
"""Erzeugt die Kurzbefehle aus config.toml nach dist/ (nur macOS: braucht `shortcuts sign`).

    python3 build.py              # alle Kurzbefehle → dist/
    python3 build.py --fertig     # Standard-Set ohne Wochenstatus → kurzbefehle/ (fürs Repo)

Datenformat im Ordner "iCloud Drive/Shortcuts/<ordner>/":
    laufend.txt   "<Ort>|yyyy-MM-dd HH:mm:ss" — letzter Start (wird nie geleert)
    zeiten.csv    datum,start,ende,brutto_min,ort — eine Zeile pro Session
"""
from __future__ import annotations

import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "shortcuts"))
from sclib import CONTAINS, NOT_CONTAINS, Shortcut, attach, ref, text, uid, var  # noqa: E402

ROOT = Path(__file__).parent
LAUFEND, ZEITEN, ABWESEND = "laufend.txt", "zeiten.csv", "abwesenheiten.csv"


def load_config() -> dict:
    path = ROOT / "config.toml"
    if not path.exists() or "--fertig" in sys.argv:
        path = ROOT / "config.example.toml"
    return tomllib.loads(path.read_text(encoding="utf-8"))


# --- Bausteine ----------------------------------------------------------------

def running_session(sc: Shortcut, require: str = "|") -> tuple[str, str, str]:
    """laufend.txt lesen; beenden, falls kein Start drin ist.
    → (ort, zeitstempel-Text, heute) als UUIDs."""
    now = sc.now()
    today = sc.fmt_date(ref(now, "Date"), "yyyy-MM-dd")
    raw = sc.read_file(LAUFEND)
    sc.exit_if(raw, NOT_CONTAINS, require)
    parts = sc.act("text.split", text=text("￼", ref(raw, "Text")),
                   WFTextSeparator="Custom", WFTextCustomSeparator="|")
    ort = sc.act("getitemfromlist", WFInput=attach(parts, "Split Text"),
                 WFItemSpecifier="First Item")
    ts = sc.act("getitemfromlist", WFInput=attach(parts, "Split Text"),
                WFItemSpecifier="Last Item")
    return ort, ts, today


def close_session(sc: Shortcut, ort: str, ts: str, end: dict) -> None:
    """Session (Start ts) mit Ende `end` als Zeile an zeiten.csv anhängen — außer schon geloggt."""
    item = lambda u: ref(u, "Item from List")
    key = sc.fmt_date(item(ts), "yyyy-MM-dd,HH:mm")
    sc.exit_if(sc.read_file(ZEITEN), CONTAINS, ref(key, "Formatted Date"),
               message=text("Schon ausgestempelt."))
    start_dt = sc.fmt_date(item(ts))  # Text → Datum
    datum = sc.fmt_date(item(ts), "yyyy-MM-dd")
    start_hm = sc.fmt_date(item(ts), "HH:mm")
    end_hm = sc.fmt_date(end, "HH:mm")
    minutes = sc.act("gettimebetweendates", WFInput=text("￼", end),
                     WFTimeUntilFromDate=text("￼", ref(start_dt, "Formatted Date")))
    f = lambda u: ref(u, "Formatted Date")
    row = sc.text("￼,￼,￼,￼,￼", f(datum), f(start_hm), f(end_hm),
                  ref(minutes, "Time Between Dates"), item(ort))
    sc.append_line(ZEITEN, row)
    sc.notify("Feierabend (￼): ￼–￼, ￼ min", item(ort), f(start_hm), f(end_hm),
              ref(minutes, "Time Between Dates"))


# --- Kurzbefehle ----------------------------------------------------------------

def start(cfg: dict, ort: str) -> Shortcut:
    sc = Shortcut(cfg["ordner"])
    now = sc.now()
    stamp = sc.fmt_date(ref(now, "Date"), "yyyy-MM-dd HH:mm:ss")
    line = sc.text(f"{ort}|￼", ref(stamp, "Formatted Date"))
    sc.save_file(LAUFEND, line)
    hm = sc.fmt_date(ref(now, "Date"), "HH:mm")
    sc.notify(f"{ort} gestartet: ￼", ref(hm, "Formatted Date"))
    return sc


def feierabend(cfg: dict) -> Shortcut:
    sc = Shortcut(cfg["ordner"])
    ort, ts, _ = running_session(sc)
    end = sc.now()
    close_session(sc, ort, ts, ref(end, "Date"))
    return sc


def ho_check(cfg: dict) -> Shortcut:
    """10 Uhr: heute noch nichts gestempelt → 'Homeoffice heute?' → Startzeit."""
    ho = cfg["homeoffice"]
    sc = Shortcut(cfg["ordner"])
    now = sc.now()
    today = sc.fmt_date(ref(now, "Date"), "yyyy-MM-dd")
    for name in (LAUFEND, ZEITEN, ABWESEND):
        sc.exit_if(sc.read_file(name), CONTAINS, ref(today, "Formatted Date"))
    sc.act("alert", WFAlertActionTitle=f"{ho} heute?",
           WFAlertActionMessage=f"Noch nicht eingestempelt. Ist heute ein {ho}-Tag?",
           WFAlertActionCancelButtonShown=True)
    asked = sc.act("ask", WFAskActionPrompt="Seit wann arbeitest du?", WFInputType="Time")
    # "Uhrzeit"-Abfrage liefert das NÄCHSTE Vorkommen (09:00 um 10:00 gefragt → morgen!),
    # daher Datum von "jetzt", nur HH:mm aus der Eingabe.
    hm = sc.fmt_date(ref(asked, "Provided Input"), "HH:mm")
    line = sc.text(f"{ho}|￼ ￼:00", ref(today, "Formatted Date"), ref(hm, "Formatted Date"))
    sc.save_file(LAUFEND, line)
    sc.notify(f"{ho} gestartet: ￼", ref(hm, "Formatted Date"))
    return sc


def ho_ende_check(cfg: dict) -> Shortcut:
    """18 Uhr: heutige HO-Session läuft noch → Jetzt / Früher aufgehört … / Arbeite noch."""
    ho = cfg["homeoffice"]
    sc = Shortcut(cfg["ordner"])
    ort, ts, today = running_session(sc, require=f"{ho}|")
    sc.exit_if(ts, NOT_CONTAINS, ref(today, "Formatted Date"),  # Start nicht von heute
               out_name="Item from List")
    key = sc.fmt_date(ref(ts, "Item from List"), "yyyy-MM-dd,HH:mm")
    sc.exit_if(sc.read_file(ZEITEN), CONTAINS, ref(key, "Formatted Date"))  # schon aus
    start_hm = sc.fmt_date(ref(ts, "Item from List"), "HH:mm")

    items = ["Jetzt ausstempeln", "Früher aufgehört …", "Arbeite noch"]
    g = uid()
    sc.act("choosefrommenu", GroupingIdentifier=g, WFControlFlowMode=0, WFMenuItems=items,
           WFMenuPrompt=text(f"{ho} seit ￼ — Feierabend?", ref(start_hm, "Formatted Date")))
    sc.act("choosefrommenu", GroupingIdentifier=g, WFControlFlowMode=1, WFMenuItemTitle=items[0])
    d = sc.now()
    sc.act("setvariable", WFVariableName="ende", WFInput=attach(d, "Date"))
    sc.act("choosefrommenu", GroupingIdentifier=g, WFControlFlowMode=1, WFMenuItemTitle=items[1])
    asked = sc.act("ask", WFAskActionPrompt="Wann hast du aufgehört?", WFInputType="Time")
    hm = sc.fmt_date(ref(asked, "Provided Input"), "HH:mm")
    t = sc.text("￼ ￼", ref(today, "Formatted Date"), ref(hm, "Formatted Date"))
    sc.act("setvariable", WFVariableName="ende", WFInput=attach(t, "Text"))
    sc.act("choosefrommenu", GroupingIdentifier=g, WFControlFlowMode=1, WFMenuItemTitle=items[2])
    sc.act("exit")
    sc.act("choosefrommenu", GroupingIdentifier=g, WFControlFlowMode=2)

    close_session(sc, ort, ts, var("ende"))
    return sc


def wochenstatus() -> Shortcut:
    """Nur Mac: führt auswertung.py aus diesem Ordner aus und zeigt das Ergebnis."""
    sc = Shortcut("-")
    script = ROOT.resolve() / "auswertung.py"
    out = sc.act("runshellscript", Script=f'python3 "{script}"', Shell="/bin/zsh",
                 InputMode="as arguments")
    sc.act("showresult", Text=text("￼", ref(out, "Shell Script Result")))
    return sc


def main() -> None:
    cfg = load_config()
    fertig = "--fertig" in sys.argv
    out = ROOT / ("kurzbefehle" if fertig else "dist")
    if cfg["homeoffice"] not in cfg["orte"]:
        sys.exit(f"homeoffice = {cfg['homeoffice']!r} steht nicht in orte = {cfg['orte']}")
    if any("|" in o or "," in o for o in cfg["orte"]):
        sys.exit("Ortsnamen dürfen weder '|' noch ',' enthalten.")

    built = {f"{o} Start": start(cfg, o) for o in cfg["orte"]}
    built |= {"Feierabend": feierabend(cfg), "HO Check": ho_check(cfg),
              "HO Ende Check": ho_ende_check(cfg)}
    if not fertig:
        built["Wochenstatus"] = wochenstatus()
    for name, sc in built.items():
        print(sc.write(out / f"{name}.shortcut").relative_to(ROOT))


if __name__ == "__main__":
    main()
