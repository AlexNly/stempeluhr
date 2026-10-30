#!/usr/bin/env python3
"""Erzeugt die Kurzbefehle aus config.toml nach dist/ (nur macOS: braucht `shortcuts sign`).

    python3 build.py              # alle Kurzbefehle → dist/
    python3 build.py --fertig     # Standard-Sets (de + en, ohne Wochenstatus) → kurzbefehle/<sprache>/

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
from texte import texte  # noqa: E402

ROOT = Path(__file__).parent
# Dateinamen sind sprachunabhängig, damit ein Sprachwechsel keine Daten bricht
LAUFEND, ZEITEN, ABWESEND = "laufend.txt", "zeiten.csv", "abwesenheiten.csv"
BEISPIELE = {"de": "config.example.toml", "en": "config.example.en.toml"}


def load_config(path: Path) -> dict:
    cfg = tomllib.loads(path.read_text(encoding="utf-8"))
    cfg.setdefault("sprache", "de")
    cfg["T"] = texte(cfg["sprache"])
    return cfg


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


def close_session(sc: Shortcut, T: dict, ort: str, ts: str, end: dict) -> None:
    """Session (Start ts) mit Ende `end` als Zeile an zeiten.csv anhängen — außer schon geloggt."""
    item = lambda u: ref(u, "Item from List")
    key = sc.fmt_date(item(ts), "yyyy-MM-dd,HH:mm")
    sc.exit_if(sc.read_file(ZEITEN), CONTAINS, ref(key, "Formatted Date"),
               message=text(T["schon_aus"]))
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
    sc.notify(T["feierabend"], item(ort), f(start_hm), f(end_hm),
              ref(minutes, "Time Between Dates"))


# --- Kurzbefehle ----------------------------------------------------------------

def start(cfg: dict, ort: str) -> Shortcut:
    sc = Shortcut(cfg["ordner"])
    now = sc.now()
    stamp = sc.fmt_date(ref(now, "Date"), "yyyy-MM-dd HH:mm:ss")
    line = sc.text(f"{ort}|￼", ref(stamp, "Formatted Date"))
    sc.save_file(LAUFEND, line)
    hm = sc.fmt_date(ref(now, "Date"), "HH:mm")
    sc.notify(cfg["T"]["gestartet"].format(ort=ort), ref(hm, "Formatted Date"))
    return sc


def feierabend(cfg: dict) -> Shortcut:
    sc = Shortcut(cfg["ordner"])
    ort, ts, _ = running_session(sc)
    end = sc.now()
    close_session(sc, cfg["T"], ort, ts, ref(end, "Date"))
    return sc


def ho_check(cfg: dict) -> Shortcut:
    """10 Uhr: heute noch nichts gestempelt → 'Homeoffice heute?' → Startzeit."""
    ho, T = cfg["homeoffice"], cfg["T"]
    sc = Shortcut(cfg["ordner"])
    now = sc.now()
    today = sc.fmt_date(ref(now, "Date"), "yyyy-MM-dd")
    for name in (LAUFEND, ZEITEN, ABWESEND):
        sc.exit_if(sc.read_file(name), CONTAINS, ref(today, "Formatted Date"))
    sc.act("alert", WFAlertActionTitle=T["ho_titel"].format(ho=ho),
           WFAlertActionMessage=T["ho_frage"].format(ho=ho),
           WFAlertActionCancelButtonShown=True)
    asked = sc.act("ask", WFAskActionPrompt=T["seit_wann"], WFInputType="Time")
    # "Uhrzeit"-Abfrage liefert das NÄCHSTE Vorkommen (09:00 um 10:00 gefragt → morgen!),
    # daher Datum von "jetzt", nur HH:mm aus der Eingabe.
    hm = sc.fmt_date(ref(asked, "Provided Input"), "HH:mm")
    line = sc.text(f"{ho}|￼ ￼:00", ref(today, "Formatted Date"), ref(hm, "Formatted Date"))
    sc.save_file(LAUFEND, line)
    sc.notify(T["gestartet"].format(ort=ho), ref(hm, "Formatted Date"))
    return sc


def ho_ende_check(cfg: dict) -> Shortcut:
    """18 Uhr: heutige HO-Session läuft noch → Jetzt / Früher aufgehört … / Arbeite noch."""
    ho, T = cfg["homeoffice"], cfg["T"]
    sc = Shortcut(cfg["ordner"])
    ort, ts, today = running_session(sc, require=f"{ho}|")
    sc.exit_if(ts, NOT_CONTAINS, ref(today, "Formatted Date"),  # Start nicht von heute
               out_name="Item from List")
    key = sc.fmt_date(ref(ts, "Item from List"), "yyyy-MM-dd,HH:mm")
    sc.exit_if(sc.read_file(ZEITEN), CONTAINS, ref(key, "Formatted Date"))  # schon aus
    start_hm = sc.fmt_date(ref(ts, "Item from List"), "HH:mm")

    items = [T["menu_jetzt"], T["menu_frueher"], T["menu_weiter"]]
    g = uid()
    sc.act("choosefrommenu", GroupingIdentifier=g, WFControlFlowMode=0, WFMenuItems=items,
           WFMenuPrompt=text(T["ende_prompt"].format(ho=ho), ref(start_hm, "Formatted Date")))
    sc.act("choosefrommenu", GroupingIdentifier=g, WFControlFlowMode=1, WFMenuItemTitle=items[0])
    d = sc.now()
    sc.act("setvariable", WFVariableName="ende", WFInput=attach(d, "Date"))
    sc.act("choosefrommenu", GroupingIdentifier=g, WFControlFlowMode=1, WFMenuItemTitle=items[1])
    asked = sc.act("ask", WFAskActionPrompt=T["wann_aufgehoert"], WFInputType="Time")
    hm = sc.fmt_date(ref(asked, "Provided Input"), "HH:mm")
    t = sc.text("￼ ￼", ref(today, "Formatted Date"), ref(hm, "Formatted Date"))
    sc.act("setvariable", WFVariableName="ende", WFInput=attach(t, "Text"))
    sc.act("choosefrommenu", GroupingIdentifier=g, WFControlFlowMode=1, WFMenuItemTitle=items[2])
    sc.act("exit")
    sc.act("choosefrommenu", GroupingIdentifier=g, WFControlFlowMode=2)

    close_session(sc, T, ort, ts, var("ende"))
    return sc


def wochenstatus() -> Shortcut:
    """Nur Mac: führt auswertung.py aus diesem Ordner aus und zeigt das Ergebnis."""
    sc = Shortcut("-")
    script = ROOT.resolve() / "auswertung.py"
    out = sc.act("runshellscript", Script=f'python3 "{script}"', Shell="/bin/zsh",
                 InputMode="as arguments")
    sc.act("showresult", Text=text("￼", ref(out, "Shell Script Result")))
    return sc


def build_set(cfg: dict, out: Path, mit_status: bool) -> None:
    T = cfg["T"]
    if cfg["homeoffice"] not in cfg["orte"]:
        sys.exit(T["err_ho"].format(ho=cfg["homeoffice"], orte=cfg["orte"]))
    if any("|" in o or "," in o for o in cfg["orte"]):
        sys.exit(T["err_ortname"])
    built = {T["sc_start"].format(ort=o): start(cfg, o) for o in cfg["orte"]}
    built |= {T["sc_ende"]: feierabend(cfg), T["sc_ho_check"]: ho_check(cfg),
              T["sc_ho_ende_check"]: ho_ende_check(cfg)}
    if mit_status:
        built[T["sc_status"]] = wochenstatus()
    for name, sc in built.items():
        print(sc.write(out / f"{name}.shortcut").relative_to(ROOT))


def main() -> None:
    if "--fertig" in sys.argv:
        for sprache, beispiel in BEISPIELE.items():
            build_set(load_config(ROOT / beispiel), ROOT / "kurzbefehle" / sprache, False)
        return
    path = ROOT / "config.toml"
    if not path.exists():
        path = ROOT / BEISPIELE["de"]
    build_set(load_config(path), ROOT / "dist", True)


if __name__ == "__main__":
    main()
