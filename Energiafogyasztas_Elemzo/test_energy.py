import tempfile
import unittest
from pathlib import Path

from kd_energy import KDEnergyData, kd_calculate_statistics, kd_load_csv, kd_save_csv


class EnergyTests(unittest.TestCase):
    def test_statistics(self):
        result = kd_calculate_statistics([10, 20, 30])
        self.assertEqual(result["average"], 20)
        self.assertEqual(result["median"], 20)
        self.assertAlmostEqual(result["deviation"], 8.1649658093)
        self.assertEqual(result["total"], 60)

    def test_empty_statistics(self):
        self.assertIsNone(kd_calculate_statistics([]))

    def test_csv_roundtrip(self):
        records = [KDEnergyData(2026, 2, 50.5, 20), KDEnergyData(2026, 1, 100, 80)]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "test.csv"
            kd_save_csv(path, records)
            self.assertEqual(kd_load_csv(path), list(reversed(records)))

    def test_invalid_values(self):
        for value in (-1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                KDEnergyData(2026, 1, value, 0)


if __name__ == "__main__":
    unittest.main()

class YearAnalysisTests(unittest.TestCase):
    def test_projection_and_budget_warning(self):
        from kd_energy import kd_analyze_year
        rows = [KDEnergyData(2026, i, 300, 110) for i in range(1, 5)]
        data = kd_analyze_year(rows, 2026, 3000, 1200)
        self.assertEqual(data["electricity"]["projection"], 3600)
        self.assertTrue(data["electricity"]["over_limit"])
        self.assertEqual(data["months"], 4)

    def test_year_over_year_anomaly(self):
        from kd_energy import kd_analyze_year
        rows = [KDEnergyData(2025, 1, 100, 50), KDEnergyData(2026, 1, 150, 40)]
        data = kd_analyze_year(rows, 2026, 3000, 1200)
        self.assertEqual(data["alerts"], [(1, "electricity", 50, "előző év")])

    def test_previous_three_months_anomaly(self):
        from kd_energy import kd_analyze_year
        rows = [KDEnergyData(2026, i, 100 if i < 4 else 150, 50) for i in range(1, 5)]
        data = kd_analyze_year(rows, 2026, 3000, 1200)
        self.assertEqual(data["alerts"], [(4, "electricity", 50, "előző 3 hónap")])

    def test_no_projection_with_insufficient_months(self):
        from kd_energy import kd_analyze_year
        data = kd_analyze_year([KDEnergyData(2026, 1, 100, 40)], 2026, 3000, 1200)
        self.assertIsNone(data["electricity"]["projection"])

    def test_invalid_limit(self):
        from kd_energy import kd_analyze_year
        with self.assertRaises(ValueError):
            kd_analyze_year([], 2026, -10, 1200)
