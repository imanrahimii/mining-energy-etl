from pathlib import Path
import json

cells = []
def add(kind, source):
    cell = dict(cell_type=kind, metadata={}, source=source.splitlines(keepends=True), id=f"etl-{len(cells)}")
    if kind == "code":
        cell.update(execution_count=None, outputs=[])
    cells.append(cell)

add("markdown", "# Mining Energy ETL\nRun one code cell at a time. Setup first, then upload the two CSV inputs, then run Extract, Transform and Load.")
add("code", """import csv
import re
from pathlib import Path

CATALOG = "dbw_sales_iman01"  # Change only if your workspace uses another catalog.
SCHEMA = "iman_energy_etl_lab"
VOLUME = "incoming"
USE_HISTORY = False  # True for the machine learning exercise
assert re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", CATALOG)
prefix = f"`{CATALOG}`.`{SCHEMA}`"
volume = Path(f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {prefix}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {prefix}.`{VOLUME}`")
print(volume)
""")
add("markdown", "## Extract\nUpload tariffs.csv and meter_readings.csv (or meter_history.csv if USE_HISTORY=True) before running this cell. The files stay in the volume.")
add("code", """def extract(filename, expected_header):
    with (volume / filename).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != expected_header:
            raise ValueError(f"Unexpected header in {filename}: {reader.fieldnames}")
        rows = list(reader)
        if any(None in row or None in row.values() for row in rows):
            raise ValueError(f"A row has the wrong number of fields in {filename}")
        return rows

readings = extract("meter_history.csv" if USE_HISTORY else "meter_readings.csv", ["reading_id", "date", "site", "energy_kwh"])
tariffs = extract("tariffs.csv", ["site", "cents_per_kwh"])
print(f"Extracted {len(readings)} readings and {len(tariffs)} tariffs")
""")
add("markdown", "## Transform\nCalculate each reading cost using its site's tariff. Keep rejected records with reasons; count repeated records separately. Monetary values are stored as integer cents.")
add("code", Path("etl_core.py").read_text())
add("code", """clean, rejected, daily, duplicates = transform(readings, tariffs)
print(f"Valid: {len(clean)} | Rejected: {len(rejected)} | Duplicates: {duplicates}")
for row in rejected:
    print(row)
if USE_HISTORY:
    assert (len(clean), len(rejected), duplicates, len(daily)) == (224, 1, 1, 112)
else:
    assert (len(clean), len(rejected), duplicates, len(daily)) == (6, 3, 1, 4)
    assert sum(row[3] for row in daily) == 32000
""")
add("markdown", "## Load\nWrite three Delta tables. Re-running replaces the tables in this practice schema; it does not append rows.")
add("code", """from pyspark.sql import functions as F

def load(rows, schema, name, cast_date=False):
    frame = spark.createDataFrame(rows, schema=schema)
    if cast_date:
        frame = frame.withColumn("date", F.to_date("date"))
    frame.write.format("delta").mode("overwrite").saveAsTable(f"{prefix}.`{name}`")

load(clean, "reading_id STRING, date STRING, site STRING, energy_kwh LONG, cents_per_kwh LONG, cost_cents LONG",
     "silver_energy_readings", cast_date=True)
load(rejected, "reading_id STRING, date STRING, site STRING, energy_kwh STRING, reason STRING",
     "rejected_energy_readings")
load(daily, "date STRING, site STRING, total_kwh LONG, total_cost_cents LONG",
     "gold_daily_energy_cost", cast_date=True)

display(spark.sql(f'''
    SELECT date, site, total_kwh, total_cost_cents / 100.0 AS total_cost_aud
    FROM {prefix}.gold_daily_energy_cost
    ORDER BY date, site
'''))
""")
Path("notebooks/01_mining_energy_etl.ipynb").write_text(json.dumps(dict(
    cells=cells, metadata={"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"}},
    nbformat=4, nbformat_minor=5), indent=2) + "\n")

cells.clear()
add("markdown", "# Forecast daily mine energy consumption\nRun the first notebook in history mode first. Upload historical_plans.csv and future_plans.csv into the same volume. Run the package cell, then the remaining cells in order.")
add("code", "%pip install scikit-learn==1.8.0")
add("code", """import csv
import re
from pathlib import Path

CATALOG = "dbw_sales_iman01"  # Same value as notebook 01.
SCHEMA = "iman_energy_etl_lab"
assert re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", CATALOG)
prefix = f"`{CATALOG}`.`{SCHEMA}`"
volume = Path(f"/Volumes/{CATALOG}/{SCHEMA}/incoming")

def plans(filename):
    with (volume / filename).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))

actual = {(str(r.date), r.site): r.total_kwh
          for r in spark.table(f"{prefix}.gold_daily_energy_cost").take(113)}
past_plans = plans("historical_plans.csv")
keys = {(r["date"], r["site"]) for r in past_plans}
if len(actual) != 112 or len(past_plans) != 112 or keys != actual.keys():
    raise ValueError("Run notebook 01 with USE_HISTORY=True before training")
history = [dict(r, total_kwh=actual[r["date"], r["site"]]) for r in past_plans]
future = plans("future_plans.csv")
""")
add("markdown", "## Train and evaluate\nUse October for training and later observed days for testing. Compare with each site's training mean; the target is daily kWh. Future rows have no actual kWh.")
add("code", Path("ml_core.py").read_text())
add("code", """metrics, forecasts = fit_and_score(history, future)
print(metrics)
assert (metrics["train"], metrics["test"], len(forecasts)) == (62, 50, 10)
""")
add("code", """from pyspark.sql import functions as F

forecast_table = f"{prefix}.gold_energy_forecast"
frame = spark.createDataFrame(forecasts, "date STRING, site STRING, predicted_kwh DOUBLE")
frame = frame.withColumn("date", F.to_date("date"))
frame.write.format("delta").mode("overwrite").saveAsTable(forecast_table)
display(spark.table(forecast_table).orderBy("date", "site"))
""")
Path("notebooks/02_energy_forecast.ipynb").write_text(json.dumps(dict(
    cells=cells, metadata={"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"}},
    nbformat=4, nbformat_minor=5), indent=2) + "\n")
