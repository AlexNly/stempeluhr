import datetime as dt
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from auswertung import easter_sunday, holidays, pause_minutes, read_rows  # noqa: E402

D = dt.date


class Ostern(unittest.TestCase):
    def test_bekannte_jahre(self):
        for year, date in [(2024, D(2024, 3, 31)), (2025, D(2025, 4, 20)),
                           (2026, D(2026, 4, 5)), (2027, D(2027, 3, 28))]:
            self.assertEqual(easter_sunday(year), date)


class Feiertage(unittest.TestCase):
    def test_bundesweit(self):
        for land in ("NW", "BE", "SN"):
            h = holidays(2026, land)
            self.assertIn(D(2026, 4, 3), h)    # Karfreitag
            self.assertIn(D(2026, 5, 14), h)   # Himmelfahrt
            self.assertIn(D(2026, 10, 3), h)

    def test_landesspezifisch(self):
        self.assertIn(D(2026, 6, 4), holidays(2026, "NW"))      # Fronleichnam
        self.assertNotIn(D(2026, 6, 4), holidays(2026, "NI"))
        self.assertIn(D(2026, 10, 31), holidays(2026, "NI"))    # Reformationstag
        self.assertNotIn(D(2026, 10, 31), holidays(2026, "NW"))
        self.assertIn(D(2026, 11, 1), holidays(2026, "BY"))     # Allerheiligen
        self.assertIn(D(2026, 3, 8), holidays(2026, "BE"))      # Frauentag
        self.assertIn(D(2026, 9, 20), holidays(2026, "TH"))     # Weltkindertag
        self.assertIn(D(2026, 8, 15), holidays(2026, "SL"))     # Mariä Himmelfahrt

    def test_buss_und_bettag(self):
        for year, date in [(2024, D(2024, 11, 20)), (2025, D(2025, 11, 19)),
                           (2026, D(2026, 11, 18))]:
            self.assertEqual(holidays(year, "SN").get(date), "Buß- und Bettag")
        self.assertNotIn(D(2026, 11, 18), holidays(2026, "BY"))


class Pause(unittest.TestCase):
    def test_schwellen(self):
        cases = {300: 0, 360: 0, 370: 10, 390: 30, 492: 30, 570: 30, 580: 40, 585: 45, 600: 45}
        for brutto, pause in cases.items():
            self.assertEqual(pause_minutes(brutto), pause, brutto)

    def test_netto_nie_unter_schwelle(self):
        for brutto in range(361, 391):
            self.assertEqual(brutto - pause_minutes(brutto), 360)
        for brutto in range(571, 586):
            self.assertEqual(brutto - pause_minutes(brutto), 540)


class CSV(unittest.TestCase):
    def test_ohne_kopfzeile_und_mit_leerzeilen(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "zeiten.csv"
            p.write_text("\n2026-10-26,09:00,17:00,480,Büro\n\n2026-10-27,09:00,12:00,180,Homeoffice")
            rows = read_rows(p, ["datum", "start", "ende", "brutto_min", "ort"])
            self.assertEqual([r["ort"] for r in rows], ["Büro", "Homeoffice"])
            p.write_text("datum,start,ende,brutto_min,ort\n2026-10-26,09:00,17:00,480,Büro")
            self.assertEqual(len(read_rows(p, ["datum", "start", "ende", "brutto_min", "ort"])), 1)


if __name__ == "__main__":
    unittest.main()
