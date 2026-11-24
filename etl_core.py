from collections import defaultdict
from datetime import date

METER_FIELDS = ("reading_id", "date", "site", "energy_kwh")
RATE_FIELDS = ("site", "cents_per_kwh")

def transform(readings, tariffs):
    rates = {}
    for row in tariffs:
        site = row["site"].strip().upper()
        rate = int(row["cents_per_kwh"])
        if not site or rate <= 0 or site in rates:
            raise ValueError("Tariffs must have unique sites and positive rates")
        rates[site] = rate

    seen, clean, rejected = {}, [], []
    duplicates = 0
    daily = defaultdict(lambda: [0, 0])
    for raw in readings:
        key = tuple(raw[k].strip() for k in METER_FIELDS)
        reading_id, day, site, kwh_text = key
        site = site.upper()
        if reading_id and reading_id in seen:
            if key != seen[reading_id]:
                raise ValueError(f"Conflicting rows for {reading_id}")
            duplicates += 1
            continue
        if reading_id:
            seen[reading_id] = key

        try:
            if not reading_id:
                raise ValueError("Missing reading ID")
            if date.fromisoformat(day).isoformat() != day:
                raise ValueError("Use ISO date YYYY-MM-DD")
            try:
                kwh = int(kwh_text)
            except ValueError:
                raise ValueError("Energy must be a whole number") from None
            if kwh <= 0:
                raise ValueError("Energy must be positive")
            if site not in rates:
                raise ValueError("No tariff for site")
        except ValueError as exc:
            rejected.append((*key, str(exc)))
            continue

        rate = rates[site]
        cost = kwh * rate
        clean.append((reading_id, day, site, kwh, rate, cost))
        daily[day, site][0] += kwh
        daily[day, site][1] += cost

    summary = [(day, site, *amounts) for (day, site), amounts in sorted(daily.items())]
    assert len(readings) == len(clean) + len(rejected) + duplicates
    return clean, rejected, summary, duplicates
