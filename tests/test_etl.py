import csv
import json
from pathlib import Path
import unittest

from etl_core import transform

ROOT = Path(__file__).resolve().parents[1]

def read(name):
    with (ROOT / "data" / name).open(newline="") as stream:
        return list(csv.DictReader(stream))

class ETLTests(unittest.TestCase):
    def setUp(self):
        self.rows, self.rates = read("meter_readings.csv"), read("tariffs.csv")

    def test_reconciliation_and_costs(self):
        good, bad, daily, duplicates = transform(self.rows, self.rates)
        self.assertEqual((len(good), len(bad), duplicates), (6, 3, 1))
        self.assertEqual({row[0] for row in bad}, {"R07", "R08", "R09"})
        expected = [(r["date"], r["site"], int(r["total_kwh"]), int(r["total_cost_cents"]))
                    for r in read("expected_daily.csv")]
        self.assertEqual(daily, expected)

    def test_conflicting_reading_stops(self):
        with self.assertRaisesRegex(ValueError, "Conflicting rows"):
            transform(self.rows + [dict(self.rows[0], energy_kwh="101")], self.rates)

    def test_duplicate_rate_stops(self):
        with self.assertRaisesRegex(ValueError, "unique sites"):
            transform(self.rows, self.rates + [self.rates[0]])

    def test_notebook_uses_tested_logic(self):
        nb = json.loads((ROOT / "notebooks/01_mining_energy_etl.ipynb").read_text())
        code = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
        self.assertIn((ROOT / "etl_core.py").read_text(), code)
        for source in code:
            compile(source, "notebook", "exec")
