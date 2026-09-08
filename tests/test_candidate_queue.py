import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CandidateQueueTests(unittest.TestCase):
    def test_p017_to_p050_queue_is_complete_and_safe(self):
        queue = json.loads((ROOT / "candidate_queue.json").read_text(encoding="utf-8"))
        candidates = queue["candidates"]

        self.assertEqual(len(candidates), 34)
        self.assertEqual([item["product_id"] for item in candidates], [f"P{i:03d}" for i in range(17, 51)])
        self.assertEqual(len({item["asin"] for item in candidates}), 34)

        for item in candidates:
            self.assertRegex(item["asin"], r"^B[0-9A-Z]{9}$")
            self.assertTrue(item["product_name"])
            self.assertTrue(item["variant"])
            self.assertEqual(item["category"], "Minimal Desk Setup")
            self.assertTrue(item["profile"])
            self.assertGreater(item["historical_daily_units"], 0)

    def test_queue_does_not_duplicate_consumed_products(self):
        with (ROOT / "products.csv").open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        consumed_ids = {row["product_id"] for row in rows}
        consumed_names = {row["product_name"] for row in rows}

        queue = json.loads((ROOT / "candidate_queue.json").read_text(encoding="utf-8"))
        candidates = queue["candidates"]
        self.assertTrue(consumed_ids.isdisjoint({item["product_id"] for item in candidates}))
        self.assertTrue(consumed_names.isdisjoint({item["product_name"] for item in candidates}))

    def test_queue_is_not_production_authorized_by_itself(self):
        queue = json.loads((ROOT / "candidate_queue.json").read_text(encoding="utf-8"))
        self.assertEqual(queue["promotion_gate"], "BLOCKED_UNTIL_CURRENT_LISTING_QC")


if __name__ == "__main__":
    unittest.main()
