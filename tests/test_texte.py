import string
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from texte import SPRACHEN, TEXTE  # noqa: E402


def platzhalter(s: str) -> set[str]:
    return {f for _, f, _, _ in string.Formatter().parse(s) if f}


class Texte(unittest.TestCase):
    def test_gleiche_schluessel(self):
        for sprache in SPRACHEN:
            self.assertEqual(TEXTE[sprache].keys(), TEXTE["de"].keys(), sprache)

    def test_gleiche_platzhalter(self):
        # {…}-Platzhalter und ￼-Variablen (Kurzbefehle) müssen in jeder Sprache gleich sein
        for key, de in TEXTE["de"].items():
            for sprache in SPRACHEN:
                other = TEXTE[sprache][key]
                self.assertEqual(platzhalter(other), platzhalter(de), (sprache, key))
                self.assertEqual(other.count("￼"), de.count("￼"), (sprache, key))

    def test_sieben_wochentage(self):
        for sprache in SPRACHEN:
            self.assertEqual(len(TEXTE[sprache]["wochentage"].split()), 7)

    def test_menue_eindeutig(self):
        for sprache in SPRACHEN:
            t = TEXTE[sprache]
            self.assertEqual(len({t["menu_jetzt"], t["menu_frueher"], t["menu_weiter"]}), 3)


if __name__ == "__main__":
    unittest.main()
