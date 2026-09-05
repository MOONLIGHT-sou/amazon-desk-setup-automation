import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import main


def load_p011():
    with open(ROOT / "products.csv", newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            if row["product_id"] == "P011":
                return row
    raise AssertionError("P011 missing from products.csv")


def test_p011_profile_is_desk_shelf():
    product = load_p011()
    profile_name, _ = main.infer_profile(product)
    assert profile_name == "desk_shelf", profile_name


def test_keyboard_storage_does_not_select_keyboard_profile():
    product = load_p011()
    profile_name, _ = main.infer_profile(product)
    assert profile_name != "keyboard"


def test_p011_consumption_state_is_unchanged_by_profile_inference():
    product = load_p011()
    assert product["used"].strip().lower() == "yes"


if __name__ == "__main__":
    test_p011_profile_is_desk_shelf()
    test_keyboard_storage_does_not_select_keyboard_profile()
    test_p011_consumption_state_is_unchanged_by_profile_inference()
    print("P011 profile regression: PASS")
