import csv
import math
import statistics
from dataclasses import dataclass
from pathlib import Path


MONTHS = (
    "Január", "Február", "Március", "Április", "Május", "Június",
    "Július", "Augusztus", "Szeptember", "Október", "November", "December"
)


@dataclass
class KDEnergyData:
    year: int
    month: int
    electricity: float
    gas: float

    def __post_init__(self):
        if not 2000 <= self.year <= 2100:
            raise ValueError("Az év 2000 és 2100 közötti legyen.")
        if not 1 <= self.month <= 12:
            raise ValueError("A hónap 1 és 12 közötti legyen.")
        if not math.isfinite(self.electricity) or not 0 <= self.electricity <= 1000000:
            raise ValueError("Az áramfogyasztás 0 és 1 000 000 közötti legyen.")
        if not math.isfinite(self.gas) or not 0 <= self.gas <= 1000000:
            raise ValueError("A gázfogyasztás 0 és 1 000 000 közötti legyen.")


def kd_calculate_statistics(values):
    if not values:
        return None
    return {
        "count": len(values),
        "total": sum(values),
        "average": statistics.mean(values),
        "median": statistics.median(values),
        "deviation": statistics.pstdev(values),
        "minimum": min(values),
        "maximum": max(values),
    }


def kd_save_csv(path, records):
    destination = Path(path)
    with destination.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(("ev", "honap", "aram_kwh", "gaz_m3"))
        for record in sorted(records, key=lambda row: (row.year, row.month)):
            writer.writerow((record.year, record.month, record.electricity, record.gas))


def kd_load_csv(path):
    source = Path(path)
    if not source.exists():
        return []
    records = []
    with source.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file, delimiter=";")
        required = {"ev", "honap", "aram_kwh", "gaz_m3"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValueError("A CSV fejlécének az ev;honap;aram_kwh;gaz_m3 mezőket kell tartalmaznia.")
        for index, row in enumerate(reader, start=2):
            try:
                record = KDEnergyData(
                    int(row["ev"]),
                    int(row["honap"]),
                    float(row["aram_kwh"].replace(",", ".")),
                    float(row["gaz_m3"].replace(",", ".")),
                )
            except (TypeError, ValueError, AttributeError) as error:
                raise ValueError(f"Érvénytelen adat a CSV {index}. sorában: {error}") from error
            if any(previous.year == record.year and previous.month == record.month for previous in records):
                raise ValueError(f"Duplikált év/hónap a CSV {index}. sorában.")
            records.append(record)
    return sorted(records, key=lambda row: (row.year, row.month))


def kd_analyze_year(records, year, electricity_limit, gas_limit):
    if not 2000 <= year <= 2100:
        raise ValueError("Az év 2000 és 2100 közötti legyen.")
    if any(not math.isfinite(value) or value <= 0 for value in (electricity_limit, gas_limit)):
        raise ValueError("Az éves keretek pozitív számok legyenek.")
    yearly = sorted((record for record in records if record.year == year), key=lambda row: row.month)
    by_date = {(record.year, record.month): record for record in records}
    report = {"year": year, "months": len(yearly), "electricity": {}, "gas": {}, "comparisons": [], "alerts": []}
    for field, limit in (("electricity", electricity_limit), ("gas", gas_limit)):
        total = sum(getattr(row, field) for row in yearly)
        projection = total / len(yearly) * 12 if len(yearly) >= 3 else None
        report[field] = {"total": total, "limit": limit, "projection": projection, "over_limit": total > limit or (projection is not None and projection > limit)}
    for record in yearly:
        previous = by_date.get((year - 1, record.month))
        for field in ("electricity", "gas"):
            value = getattr(record, field)
            if previous is not None:
                old_value = getattr(previous, field)
                if old_value > 0:
                    change = (value / old_value - 1) * 100
                    report["comparisons"].append((record.month, field, change))
                    if change > 30:
                        report["alerts"].append((record.month, field, change, "előző év"))
                    continue
            preceding = []
            for shift in (1, 2, 3):
                month_index = year * 12 + record.month - 1 - shift
                old = by_date.get((month_index // 12, month_index % 12 + 1))
                if old is None:
                    break
                preceding.append(getattr(old, field))
            if len(preceding) == 3:
                baseline = statistics.mean(preceding)
                if baseline > 0 and value > baseline * 1.3:
                    report["alerts"].append((record.month, field, (value / baseline - 1) * 100, "előző 3 hónap"))
    return report
