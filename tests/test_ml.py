import csv
import json
import unittest
from pathlib import Path

from etl_core import transform
from ml_core import fit_and_score

ROOT = Path(__file__).resolve().parents[1]

def read(name):
    with (ROOT / "data" / name).open(newline="") as stream:
        return list(csv.DictReader(stream))

class MLTests(unittest.TestCase):
    def test_etl_to_forecast(self):
        clean, bad, daily, duplicates = transform(read("meter_history.csv"), read("tariffs.csv"))
        self.assertEqual((len(clean), len(bad), len(daily), duplicates), (224, 1, 112, 1))
        actual = {(d, s): kwh for d, s, kwh, _ in daily}
        historical = [dict(r, total_kwh=actual[r["date"], r["site"]]) for r in read("historical_plans.csv")]
        future = read("future_plans.csv")
        metrics, forecast = fit_and_score(historical, future)
        print(metrics)
        self.assertEqual((metrics["train"], metrics["test"], len(forecast)), (62, 50, 10))
        self.assertLess(metrics["model_mae"], metrics["baseline_mae"])
        self.assertEqual([(d, s) for d, s, _ in forecast], [(r["date"], r["site"]) for r in future])
        with self.assertRaisesRegex(ValueError, "Forecast dates"):
            fit_and_score(historical, historical[:1])

    def test_notebook_matches_module(self):
        nb = json.loads((ROOT / "notebooks/02_energy_forecast.ipynb").read_text())
        cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
        self.assertIn((ROOT / "ml_core.py").read_text(), cells)
        for source in cells:
            if not source.startswith("%pip "):
                compile(source, "notebook", "exec")
