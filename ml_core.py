import math
from statistics import mean

from sklearn.ensemble import RandomForestRegressor

FEATURES = ("site_north", "planned_hours", "load_index", "forecast_temp_c")
CUTOFF = "2026-10-31"

def features(row):
    if row["site"] not in {"NORTH", "SOUTH"}:
        raise ValueError("Unknown site")
    return [int(row["site"] == "NORTH"),
            *(float(row[key]) for key in FEATURES[1:])]

def fit_and_score(history, future):
    train = [r for r in history if r["date"] <= CUTOFF]
    test = [r for r in history if r["date"] > CUTOFF]
    if not train or not test or not future:
        raise ValueError("Provide both historical periods and at least one future plan")
    if any(r["date"] <= max(x["date"] for x in history) for r in future):
        raise ValueError("Forecast dates must be later than historical dates")
    averages = {site: mean(r["total_kwh"] for r in train if r["site"] == site)
                for site in {r["site"] for r in train}}
    model = RandomForestRegressor(n_estimators=100, min_samples_leaf=2, random_state=42, n_jobs=1)
    model.fit([features(r) for r in train], [r["total_kwh"] for r in train])
    mae = mean(abs(r["total_kwh"] - p) for r, p in zip(test, model.predict([features(r) for r in test])))
    baseline = mean(abs(r["total_kwh"] - averages[r["site"]]) for r in test)
    prediction = [(r["date"], r["site"], round(float(p), 2))
                  for r, p in zip(future, model.predict([features(r) for r in future]))]
    assert all(math.isfinite(row[2]) for row in prediction)
    return dict(train=len(train), test=len(test), baseline_mae=baseline, model_mae=mae), prediction
