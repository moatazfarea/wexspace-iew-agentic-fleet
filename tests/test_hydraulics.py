import json
import unittest
from pathlib import Path

from wexspace.hydraulics import calculate_network, independently_verify, validate_network_input


ROOT = Path(__file__).resolve().parents[1]


class HydraulicTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(
            (ROOT / "data/UTL-NET-001_SYNTHETIC_INPUT.json").read_text(encoding="utf-8")
        )

    def test_deterministic_calculation_passes_engineering_checks(self):
        first = calculate_network(self.payload)
        second = calculate_network(self.payload)
        self.assertEqual(first, second)
        self.assertTrue(first["accepted"])
        self.assertEqual(len(first["segments"]), 3)
        self.assertEqual(first["node_balance_m3_h"]["J-101"], 0.0)

    def test_independent_recalculation_passes(self):
        primary = calculate_network(self.payload)
        validation = independently_verify(self.payload, primary)
        self.assertTrue(validation["verified"])
        self.assertTrue(validation["checks"]["segment_differences_within_5_percent"])

    def test_missing_input_is_rejected_without_guessing(self):
        incomplete = json.loads(
            (ROOT / "data/UTL-NET-001_MISSING_INPUT.json").read_text(encoding="utf-8")
        )
        errors = validate_network_input(incomplete)
        self.assertTrue(errors)
        with self.assertRaises(ValueError):
            calculate_network(incomplete)


if __name__ == "__main__":
    unittest.main()
