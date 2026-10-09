"""Trend engine tests. Standard library only."""
import json
import unittest
from datetime import date
from statistics import stdev

from app import db, metrics as m, metrics_service as svc


class AdherenceTests(unittest.TestCase):
    def test_three_quarters(self):
        self.assertAlmostEqual(m.adherence_pct([(3, 3), (3, 2), (3, 3), (3, 1)]).value, 75.0)

    def test_extra_sessions_do_not_hide_misses(self):
        self.assertAlmostEqual(m.adherence_pct([(3, 3), (4, 3)]).value, 600 / 7)  # 85.7
        self.assertAlmostEqual(m.adherence_pct([(3, 5), (3, 1)]).value, 4 / 6 * 100)

    def test_only_last_four_weeks(self):
        self.assertAlmostEqual(m.adherence_pct([(3, 0), (3, 3), (3, 3), (3, 3), (3, 3)]).value, 100.0)

    def test_zero_scheduled_weeks_ignored(self):
        self.assertEqual(m.adherence_pct([(0, 2), (3, 3)]).status, m.NOT_ENOUGH)

    def test_one_week_is_not_enough(self):
        r = m.adherence_pct([(3, 3)])
        self.assertEqual((r.status, r.value), (m.NOT_ENOUGH, None))


class WeightTests(unittest.TestCase):
    def test_losing_point_two_per_week(self):
        pts = [(date(2026, 9, 21), 72.0), (date(2026, 10, 5), 71.6)]
        r = m.weight_trend_kg_per_week(pts, date(2026, 10, 12))
        self.assertAlmostEqual(r.value, -0.2)

    def test_window_boundaries_are_open_below(self):
        # 28 days before as_of is excluded; 14 days before belongs to the older window
        pts = [(date(2026, 9, 14), 100.0), (date(2026, 9, 28), 72.0), (date(2026, 10, 12), 71.0)]
        r = m.weight_trend_kg_per_week(pts, date(2026, 10, 12))
        self.assertAlmostEqual(r.value, -0.5)

    def test_missing_window_is_not_enough(self):
        self.assertEqual(m.weight_trend_kg_per_week([(date(2026, 10, 10), 70.0)], date(2026, 10, 12)).status, m.NOT_ENOUGH)


class SleepTests(unittest.TestCase):
    def test_midnight_does_not_wrap(self):
        self.assertEqual(m.bed_minutes_since_18("23:30"), 330)
        self.assertEqual(m.bed_minutes_since_18("00:30"), 390)

    def test_value_matches_hand_calculation(self):
        e = [("23:00", "06:30"), ("23:30", "06:30"), ("00:00", "07:00"), ("23:15", "06:45")]
        expected = (stdev([300, 330, 360, 315]) + stdev([390, 390, 420, 405])) / 2
        self.assertAlmostEqual(m.sleep_consistency_min(e).value, expected)
        self.assertAlmostEqual(expected, 19.99, places=2)

    def test_perfectly_regular_is_zero(self):
        self.assertAlmostEqual(m.sleep_consistency_min([("23:00", "07:00")] * 3).value, 0.0)

    def test_two_entries_not_enough(self):
        self.assertEqual(m.sleep_consistency_min([("23:00", "07:00")] * 2).status, m.NOT_ENOUGH)


class StrengthTests(unittest.TestCase):
    def test_epley(self):
        self.assertAlmostEqual(m.epley_1rm(60, 8), 76.0)
        self.assertAlmostEqual(m.epley_1rm(65, 8), 82.3333333)

    def test_epley_rejects_high_reps_and_bad_input(self):
        self.assertIsNone(m.epley_1rm(40, 15))
        self.assertIsNone(m.epley_1rm(0, 5))
        self.assertIsNone(m.epley_1rm(50, 0))

    def test_progression(self):
        s = [(date(2026, 9, 14), 60, 8), (date(2026, 9, 28), 65, 8)]
        r = m.strength_progression_pct_per_week("Squat", s)
        self.assertAlmostEqual(r.value, 100 * (82.3333333 - 76.0) / 76.0 / 2, places=4)

    def test_too_short_span(self):
        s = [(date(2026, 9, 14), 60, 8), (date(2026, 9, 18), 65, 8)]
        self.assertEqual(m.strength_progression_pct_per_week("Squat", s).status, m.NOT_ENOUGH)


class EnergyTests(unittest.TestCase):
    def test_bmr_men_and_women(self):
        self.assertAlmostEqual(m.bmr_mifflin(70, 175, 21, "male").value, 1693.75)
        self.assertAlmostEqual(m.bmr_mifflin(60, 165, 21, "female").value, 600 + 1031.25 - 105 - 161)

    def test_bmr_needs_every_input(self):
        r = m.bmr_mifflin(70, 175, None, "male")
        self.assertEqual((r.status, r.value), (m.NOT_ENOUGH, None))
        self.assertEqual(m.bmr_mifflin(70, 175, 21, None).status, m.NOT_ENOUGH)

    def test_tdee_and_range(self):
        r = m.tdee_kcal(70, 175, 21, "male", "moderate")
        self.assertAlmostEqual(r.value, 1693.75 * 1.55)
        self.assertAlmostEqual(r.detail["low"], r.value * 0.9)
        self.assertAlmostEqual(r.detail["high"], r.value * 1.1)
        self.assertEqual(m.tdee_kcal(70, 175, 21, "male", None).status, m.NOT_ENOUGH)

    def test_expected_loss_from_intake(self):
        r = m.expected_loss_kg_per_week(2625, 70, intake_kcal=2125)
        self.assertAlmostEqual(r.value, 500 * 7 / 7700)  # 0.4545
        self.assertFalse(r.detail["capped"])

    def test_expected_loss_from_deficit_level(self):
        self.assertAlmostEqual(m.expected_loss_kg_per_week(2625, 70, deficit_level="moderate").value, 500 * 7 / 7700)

    def test_intake_beats_deficit_level(self):
        r = m.expected_loss_kg_per_week(2625, 70, intake_kcal=2125, deficit_level="large")
        self.assertEqual(r.detail["deficit_kcal"], 500)

    def test_loss_is_capped_at_one_percent(self):
        r = m.expected_loss_kg_per_week(4000, 60, intake_kcal=1500)  # raw 2.27 kg/week
        self.assertAlmostEqual(r.value, 0.6)
        self.assertTrue(r.detail["capped"])

    def test_no_deficit_means_no_loss_and_no_input_is_not_enough(self):
        self.assertEqual(m.expected_loss_kg_per_week(2000, 70, intake_kcal=2500).value, 0.0)
        self.assertEqual(m.expected_loss_kg_per_week(2000, 70).status, m.NOT_ENOUGH)  # calories are optional

    def test_muscle_range(self):
        r = m.muscle_gain_range_kg_per_week(70, "novice", "male")
        self.assertAlmostEqual(r.detail["low"], 0.161)
        self.assertAlmostEqual(r.detail["high"], 0.245)
        w = m.muscle_gain_range_kg_per_week(70, "novice", "female")
        self.assertAlmostEqual(w.detail["high"], 0.1225)
        self.assertEqual(m.muscle_gain_range_kg_per_week(70, None, "male").status, m.NOT_ENOUGH)

    def test_comparison_bands(self):
        exp = m.expected_loss_kg_per_week(2625, 70, intake_kcal=2125)  # 0.4545
        def trend(v): return m.MetricResult("weight_trend_kg_per_week", m.OK, v, "kg/week")
        self.assertEqual(m.loss_comparison(trend(-0.45), exp).detail["status"], "on_track")
        self.assertEqual(m.loss_comparison(trend(-0.1), exp).detail["status"], "slower_than_expected")
        self.assertEqual(m.loss_comparison(trend(-0.8), exp).detail["status"], "faster_than_expected")
        self.assertEqual(m.loss_comparison(trend(0.3), exp).detail["status"], "slower_than_expected")
        self.assertEqual(m.loss_comparison(trend(-0.4), m.expected_loss_kg_per_week(2000, 70)).status, m.NOT_ENOUGH)


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(":memory:")
        db.init_db(self.conn)
        self.uid = self.conn.execute("INSERT INTO users (email, password_hash) VALUES ('a@x.com','x')").lastrowid
        self.squat = self.conn.execute("SELECT exercise_id FROM exercises LIMIT 1").fetchone()[0]

    def checkin(self, day, weight, completed_days=(), bed=None, wake=None, lift=None, sched=("mon", "wed", "fri")):
        sid = self.conn.execute(
            "INSERT INTO profile_snapshots (user_id, created_at, weight, height, training_schedule) VALUES (?,?,?,175,?)",
            (self.uid, f"{day}T08:00:00.000Z", weight, json.dumps({"days": list(sched)}))).lastrowid
        cid = self.conn.execute("INSERT INTO checkins (user_id, snapshot_id, checkin_date) VALUES (?,?,?)",
                                (self.uid, sid, day)).lastrowid
        for sd in completed_days:
            w, r = lift if lift else (None, None)
            self.conn.execute("INSERT INTO workout_logs (checkin_id, exercise_id, session_day, sets, reps, weight_used) VALUES (?,?,?,3,?,?)",
                              (cid, self.squat, sd, r, w))
        if bed:
            self.conn.execute("INSERT INTO sleep_logs (checkin_id, bed_time, wake_time) VALUES (?,?,?)", (cid, bed, wake))

    def test_full_history(self):
        self.checkin("2026-09-14", 72.0, ("mon", "wed", "fri"), "23:00", "06:30", lift=(60, 8))
        self.checkin("2026-09-21", 72.0, ("mon", "wed"), "23:30", "06:30")
        self.checkin("2026-09-28", 71.6, ("mon", "wed", "fri"), "00:00", "07:00", lift=(65, 8))
        self.checkin("2026-10-05", 71.6, ("mon",), "23:15", "06:45")
        res = {r.metric_type.split(":")[0]: r for r in svc.compute_all(self.conn, self.uid, date(2026, 10, 12))}
        self.assertAlmostEqual(res["adherence_pct"].value, 9 / 12 * 100)
        self.assertAlmostEqual(res["weight_trend_kg_per_week"].value, -0.1)  # older (09-14,09-28]: 72.0,71.6 -> 71.8; recent: 71.6
        self.assertTrue(res["sleep_consistency_min"].ok)
        self.assertTrue(res["strength_progression_pct_per_week"].ok)
        stored = self.conn.execute("SELECT COUNT(*) FROM metrics").fetchone()[0]
        self.assertEqual(stored, 4)

    def test_four_exercises_one_session_counts_once(self):
        self.checkin("2026-09-14", 70.0, ("mon", "mon", "mon", "mon"))
        self.checkin("2026-09-21", 70.0, ("mon",))
        r = svc.compute_all(self.conn, self.uid, date(2026, 10, 12), store=False)[0]
        self.assertEqual(r.detail["completed"], 2)

    def test_energy_metrics_from_latest_profile(self):
        self.checkin("2026-09-21", 72.0)
        self.checkin("2026-10-05", 71.6)
        self.conn.execute("""INSERT INTO profile_snapshots (user_id, created_at, weight, height, age, sex,
            activity_level, training_level, deficit_level) VALUES (?, '2026-10-06T08:00:00.000Z', 71.6, 175, 21,
            'male', 'moderate', 'novice', 'moderate')""", (self.uid,))
        res = {r.metric_type: r for r in svc.compute_all(self.conn, self.uid, date(2026, 10, 12))}
        self.assertTrue(res["bmr_kcal"].ok and res["tdee_kcal"].ok and res["muscle_gain_kg_per_week"].ok)
        self.assertAlmostEqual(res["expected_loss_kg_per_week"].value, 500 * 7 / 7700)
        self.assertIn("loss_vs_expected_ratio", res)

    def test_optional_calorie_fields_absent_still_works(self):
        self.checkin("2026-10-12", 70.0)
        res = {r.metric_type: r for r in svc.compute_all(self.conn, self.uid, date(2026, 10, 12))}
        self.assertEqual(res["expected_loss_kg_per_week"].status, m.NOT_ENOUGH)

    def test_thin_data_stores_nothing(self):
        self.checkin("2026-10-12", 70.0)
        res = svc.compute_all(self.conn, self.uid, date(2026, 10, 12))
        self.assertTrue(all(r.status == m.NOT_ENOUGH for r in res))
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM metrics").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
