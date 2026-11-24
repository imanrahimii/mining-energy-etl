import csv
from datetime import date, timedelta
from random import Random

rng = Random(42)
plans, readings, future = [], [], []
for offset in range(61):
    day = (date(2026, 10, 1) + timedelta(days=offset)).isoformat()
    for site in ("NORTH", "SOUTH"):
        hours = rng.randint(9, 22)
        load = rng.randint(30, 95)
        temp = rng.randint(17, 35)
        plan = (day, site, hours, load, temp)
        if offset >= 56:
            future.append(plan)
            continue
        plans.append(plan)
        total = round(hours * (19 + 0.65 * load) + 4 * temp + 70 * (site == "SOUTH") + rng.gauss(0, 28))
        readings.extend([(f"{offset}-{site}-1", day, site, total // 2),
                         (f"{offset}-{site}-2", day, site, total - total // 2)])
readings += [readings[0], ("BAD", plans[0][0], "NORTH", -12)]
for filename, header, rows in [
    ("meter_history.csv", "reading_id,date,site,energy_kwh", readings),
    ("historical_plans.csv", "date,site,planned_hours,load_index,forecast_temp_c", plans),
    ("future_plans.csv", "date,site,planned_hours,load_index,forecast_temp_c", future),
]:
    with open("data/" + filename, "w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(header.split(","))
        writer.writerows(rows)
