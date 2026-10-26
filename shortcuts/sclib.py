"""Mini-Bibliothek zum Erzeugen signierter .shortcut-Dateien (nur native Aktionen).

Ein Kurzbefehl ist eine Plist mit einer Liste von Aktionen. Die Formate hier sind
aus echten Kurzbefehlen abgeschaut (~/Library/Shortcuts/Shortcuts.sqlite,
Tabelle ZSHORTCUTACTIONS). Signiert wird mit `shortcuts sign` (nur macOS).
"""
from __future__ import annotations

import plistlib
import subprocess
import tempfile
import uuid
from pathlib import Path

CONTAINS, NOT_CONTAINS = 99, 999


class Shortcut:
    def __init__(self, ordner: str):
        self.actions: list[dict] = []
        # Ordner relativ zu "iCloud Drive/Shortcuts" — ohne geräte-/kontospezifische IDs,
        # dadurch funktioniert der Kurzbefehl nach dem Import bei jedem.
        self.folder = {"displayName": ordner, "filename": ordner,
                       "fileLocation": {"WFFileLocationType": "Shortcuts",
                                        "relativeSubpath": ordner}}
        self.ordner = ordner

    # --- Grundbausteine -------------------------------------------------------
    def act(self, ident: str, **params) -> str:
        u = params.setdefault("UUID", uid())
        self.actions.append({"WFWorkflowActionIdentifier": f"is.workflow.actions.{ident}",
                             "WFWorkflowActionParameters": params})
        return u

    # --- Häufige Muster -------------------------------------------------------
    def now(self) -> str:
        return self.act("date")

    def fmt_date(self, date: dict, pattern: str | None = None) -> str:
        """Datum formatieren; pattern=None → Standardformat (macht aus Text ein Datum)."""
        params = {"WFDate": text("￼", date)}
        if pattern:
            params |= {"WFDateFormatStyle": "Custom", "WFDateFormat": pattern}
        return self.act("format.date", **params)

    def text(self, template: str, *refs: dict) -> str:
        return self.act("gettext", WFTextActionText=text(template, *refs))

    def read_file(self, name: str) -> str:
        """Datei aus dem Datenordner lesen → Text (leer, falls nicht vorhanden)."""
        f = self.act("documentpicker.open", WFFile=self.folder, WFGetFilePath=name,
                     WFFileErrorIfNotFound=False)
        return self.act("detect.text", WFInput=attach(f, "File"))

    def save_file(self, name: str, text_uuid: str) -> None:
        """Datei im Datenordner überschreiben."""
        self.act("documentpicker.save", WFInput=attach(text_uuid, "Text"),
                 WFAskWhereToSave=False, WFSaveFileOverwrite=True,
                 WFFileDestinationPath=f"{self.ordner}/{name}")

    def append_line(self, name: str, text_uuid: str) -> None:
        self.act("file.append", WFFile=self.folder, WFFilePath=name, WFAppendOnNewLine=True,
                 WFInput=text("￼", ref(text_uuid, "Text")))

    def exit_if(self, text_uuid: str, condition: int, needle: dict | str,
                message: dict | None = None, out_name: str = "Text") -> None:
        """Beenden (optional mit Mitteilung), wenn Text `needle` (nicht) enthält."""
        g = uid()
        self.act("conditional", GroupingIdentifier=g, WFControlFlowMode=0,
                 WFInput={"Type": "Variable", "Variable": attach(text_uuid, out_name)},
                 WFCondition=condition,
                 WFConditionalActionString=text(needle) if isinstance(needle, str)
                 else text("￼", needle))
        if message:
            self.act("notification", WFNotificationActionBody=message)
        self.act("exit")
        self.act("conditional", GroupingIdentifier=g, WFControlFlowMode=2)

    def notify(self, template: str, *refs: dict) -> None:
        self.act("notification", WFNotificationActionBody=text(template, *refs))

    def write(self, out: Path, glyph: int = 59511, color: int = 2071128575) -> Path:
        workflow = {
            "WFWorkflowActions": self.actions,
            "WFWorkflowClientVersion": "4528.0.4.3",
            "WFWorkflowMinimumClientVersion": 900,
            "WFWorkflowIcon": {"WFWorkflowIconGlyphNumber": glyph,
                               "WFWorkflowIconStartColor": color},
            "WFWorkflowImportQuestions": [],
            "WFWorkflowInputContentItemClasses": [],
            "WFWorkflowTypes": [],
        }
        out.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw.shortcut"
            raw.write_bytes(plistlib.dumps(workflow, fmt=plistlib.FMT_BINARY))
            subprocess.run(["shortcuts", "sign", "-m", "anyone", "-i", raw, "-o", out],
                           check=True, capture_output=True)
        return out


def uid() -> str:
    return str(uuid.uuid4()).upper()


def ref(u: str, name: str) -> dict:
    """Ausgabe einer früheren Aktion."""
    return {"OutputUUID": u, "OutputName": name, "Type": "ActionOutput"}


def var(name: str) -> dict:
    """Benannte Variable (setvariable)."""
    return {"Type": "Variable", "VariableName": name}


def attach(u: str, name: str) -> dict:
    return {"Value": ref(u, name), "WFSerializationType": "WFTextTokenAttachment"}


def text(template: str, *refs: dict) -> dict:
    """Text mit Variablen: jedes '￼' im Template wird der Reihe nach belegt."""
    pos = [i for i, c in enumerate(template) if c == "￼"]
    return {"Value": {"string": template,
                      "attachmentsByRange": {f"{{{p}, 1}}": r for p, r in zip(pos, refs)}},
            "WFSerializationType": "WFTextTokenString"}
