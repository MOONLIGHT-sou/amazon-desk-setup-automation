import unittest

from main import infer_profile


class ProfileInferenceTests(unittest.TestCase):
    def assert_profile(self, product_id, product_name, expected):
        profile_name, _ = infer_profile(
            {
                "product_id": product_id,
                "product_name": product_name,
                "category": "Minimal Desk Setup",
                "amazon_link": "https://www.amazon.in/dp/B000000000",
                "used": "No",
            }
        )
        self.assertEqual(profile_name, expected)

    def test_p016_desk_mat_wins_over_incidental_keyboard_word(self):
        self.assert_profile(
            "P016",
            "DailyObjects Reversible Desk Matte Sand Premium Vegan Leather Desk Mat|Anti-Skid|Anti-Slip|85 * 45cm|Spread Turf Desk /Laptop Mat for Work from Home /Gaming- Extended Mouse pad and Keyboard Desk-Black",
            "desk_mat",
        )

    def test_extended_mouse_pad_desk_mat_is_not_keyboard(self):
        self.assert_profile(
            "P012",
            "Storite 900x400x3mm Extended Gaming Mouse Pad, Desk Mat, Black",
            "desk_mat",
        )

    def test_real_keyboard_remains_keyboard(self):
        self.assert_profile("P003", "Mechanical Keyboard", "keyboard")

    def test_cooling_pad_remains_cooling_pad(self):
        self.assert_profile(
            "P007",
            "Zebronics ZEB-NC3300 USB Powered Laptop Cooling Pad with Dual Fan, Dual USB Port and Blue LED Lights",
            "cooling_pad",
        )

    def test_shelf_with_keyboard_storage_remains_desk_shelf(self):
        self.assert_profile(
            "P011",
            "Wooden Computer Monitor Stand Riser For Desk Shelf Desktop TV Laptop Riser with Keyboard Storage Desk (Walnut Finish)",
            "desk_shelf",
        )


if __name__ == "__main__":
    unittest.main()
