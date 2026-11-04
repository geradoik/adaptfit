"""Weight projection tests (pure functions, standard library only)."""
import unittest
 
from app import projection as p
 
 
class ProjectionTests(unittest.TestCase):
    def test_both_rates_give_the_range_between_them(self):
        r = p.project_weight(72.3, -0.4, 0.45, 4)
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["basis"], "both")
        self.assertEqual((r["change_low_kg"], r["change_high_kg"]), (-1.8, -1.6))
        self.assertEqual((r["weight_low_kg"], r["weight_high_kg"]), (70.5, 70.7))
 
    def test_measured_only_is_plus_minus_25_percent(self):
        r = p.project_weight(80, -0.4, None, 4)   # -1.6 kg in 4 weeks, spread 25%
        self.assertEqual(r["basis"], "measured")
        self.assertEqual((r["change_low_kg"], r["change_high_kg"]), (-2.0, -1.2))
 
    def test_plan_only_low_end_is_half(self):
        r = p.project_weight(80, None, 0.5, 4)    # plan says -2.0 kg; low end is half of that
        self.assertEqual(r["basis"], "plan")
        self.assertEqual((r["change_low_kg"], r["change_high_kg"]), (-2.0, -1.0))
 
    def test_no_rates_means_not_enough_data_not_a_guess(self):
        self.assertEqual(p.project_weight(80, None, None, 4)["status"], "not_enough_data")
        self.assertEqual(p.project_weight(None, -0.4, 0.4, 4)["status"], "not_enough_data")
 
    def test_a_gaining_trend_can_give_a_range_that_includes_gain(self):
        r = p.project_weight(72.3, 0.1, 0.45, 4)
        self.assertLess(r["change_low_kg"], 0)
        self.assertGreater(r["change_high_kg"], 0)
 
    def test_weeks_must_be_1_to_12(self):
        for bad in (0, 13, -1, 2.5, "4", None):
            with self.assertRaises(ValueError):
                p.project_weight(80, -0.4, 0.4, bad)
 
    def test_describe_is_plain_and_labelled_as_an_estimate(self):
        text = p.describe(p.project_weight(72.3, -0.4, 0.45, 4))
        self.assertIn("4 weeks", text)
        self.assertIn("-1.8 to -1.6 kg", text)
        self.assertIn("estimate", text)
        self.assertIn("not enough data", p.describe({"status": "not_enough_data"}))
 
 
if __name__ == "__main__":
    unittest.main()
