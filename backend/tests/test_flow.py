"""Onboarding, check-in and suggestion tests. Standard library only (no FastAPI needed)."""
import json
import unittest
from datetime import date
 
from app import checkin_service as cs, db, metrics as m, onboarding_service as ob, suggestion_service as ss, suggestions
 
GOOD = {
    "weight": 74.4, "height": 175, "age": 21, "sex": "male", "activity_level": "moderate",
    "training_level": "novice", "goal": "lose_fat", "training_days": ["fri", "mon", "wed"],
}
 
 
class OnboardingTests(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(":memory:")
        db.init_db(self.conn)
 
    def test_valid_onboarding_creates_user_and_baseline_snapshot(self):
        uid = ob.save_onboarding(self.conn, GOOD)
        profile = ob.load_profile(self.conn, uid)
        self.assertEqual(profile["weight"], 74.4)
        self.assertEqual(profile["training_days"], ["mon", "wed", "fri"])  # sorted, Monday first
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM checkins").fetchone()[0], 0)  # baseline is no check-in
 
    def test_calorie_fields_are_optional(self):
        uid = ob.save_onboarding(self.conn, GOOD)
        p = ob.load_profile(self.conn, uid)
        self.assertIsNone(p["intake_kcal"])
        self.assertIsNone(p["deficit_level"])
        uid2 = ob.save_onboarding(self.conn, {**GOOD, "deficit_level": "moderate"})
        self.assertEqual(ob.load_profile(self.conn, uid2)["deficit_level"], "moderate")
 
    def test_every_problem_is_reported_at_once(self):
        with self.assertRaises(ValueError) as caught:
            ob.save_onboarding(self.conn, {"weight": 5, "sex": "x", "training_days": []})
        text = str(caught.exception)
        for part in ("Weight", "Height", "Age", "Sex", "Activity", "training day"):
            self.assertIn(part, text)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM users").fetchone()[0], 0)  # nothing half-saved
 
    def test_bad_days_and_times_rejected(self):
        for bad in ({"training_days": ["funday"]}, {"bed_time": "25:00"}, {"intake_kcal": 100}):
            with self.assertRaises(ValueError):
                ob.save_onboarding(self.conn, {**GOOD, **bad})
 
 
class CheckinTests(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(":memory:")
        db.init_db(self.conn)
        self.uid = ob.save_onboarding(self.conn, GOOD)
        self.today = date(2026, 10, 20)
        self.squat = self.conn.execute("SELECT exercise_id FROM exercises WHERE name='Squat'").fetchone()[0]
 
    def checkin(self, day, **kw):
        return cs.save_checkin(self.conn, self.uid, {"checkin_date": day, **kw}, today=self.today)
 
    def test_checkin_makes_one_snapshot_and_logs(self):
        r = self.checkin("2026-10-12", weight=74.0, done_days=["mon", "wed"], protein_target_met=True,
                         sleep={"bed_time": "23:00", "wake_time": "06:30"})
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM profile_snapshots").fetchone()[0], 2)  # baseline + 1
        snap = self.conn.execute("SELECT weight, age, training_schedule FROM profile_snapshots WHERE snapshot_id=?",
                                 (r["snapshot_id"],)).fetchone()
        self.assertEqual(snap["weight"], 74.0)
        self.assertEqual(snap["age"], 21)                                     # copied from the previous snapshot
        self.assertEqual(json.loads(snap["training_schedule"])["days"], ["mon", "wed", "fri"])
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM workout_logs").fetchone()[0], 2)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM sleep_logs").fetchone()[0], 1)
        self.assertEqual(self.conn.execute("SELECT protein_target_met FROM nutrition_logs").fetchone()[0], 1)
 
    def test_everything_but_the_date_is_optional(self):
        r = self.checkin("2026-10-12")
        snap = self.conn.execute("SELECT weight FROM profile_snapshots WHERE snapshot_id=?", (r["snapshot_id"],)).fetchone()
        self.assertEqual(snap["weight"], 74.4)  # weight carried over
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM sleep_logs").fetchone()[0], 0)  # "same as usual" = no row
 
    def test_lift_is_attached_to_a_done_day_and_other_days_get_a_placeholder(self):
        self.checkin("2026-10-12", done_days=["mon", "wed"],
                     lifts=[{"exercise_id": self.squat, "weight_used": 60, "reps": 8, "sets": 3, "session_day": "wed"}])
        rows = self.conn.execute("SELECT session_day, weight_used FROM workout_logs ORDER BY session_day").fetchall()
        self.assertEqual([(r["session_day"], r["weight_used"]) for r in rows], [("mon", None), ("wed", 60.0)])
 
    def test_duplicate_date_rejected_and_nothing_extra_saved(self):
        self.checkin("2026-10-12")
        with self.assertRaises(cs.DuplicateCheckin):
            self.checkin("2026-10-12")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM profile_snapshots").fetchone()[0], 2)
 
    def test_bad_input_rejected(self):
        for bad in ({"checkin_date": "2027-01-01"}, {"weight": "abc"}, {"done_days": ["funday"]},
                    {"sleep": {"bed_time": "23:00"}}, {"lifts": [{"exercise_id": 1}]}, {"protein_target_met": "maybe"}):
            with self.assertRaises(ValueError):
                self.checkin("2026-10-12", **bad)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM checkins").fetchone()[0], 0)
 
    def test_unknown_user_and_missing_profile(self):
        with self.assertRaises(LookupError):
            cs.save_checkin(self.conn, 999, {}, today=self.today)
        bare = self.conn.execute("INSERT INTO users (email, password_hash) VALUES ('b@x.com','x')").lastrowid
        with self.assertRaises(LookupError):
            cs.save_checkin(self.conn, bare, {}, today=self.today)
 
    def test_exercise_menu_hides_the_placeholder(self):
        names = {e["name"] for e in cs.list_exercises(self.conn)}
        self.assertIn("Squat", names)
        self.assertNotIn(cs.GENERAL_SESSION, names)
 
 
class EndToEndTests(unittest.TestCase):
    """A new user onboards, checks in for four weeks, and gets a suggestion with its reasons."""
 
    def setUp(self):
        self.conn = db.connect(":memory:")
        db.init_db(self.conn)
        self.uid = ob.save_onboarding(self.conn, {**GOOD, "deficit_level": "moderate"})
        self.today = date(2026, 10, 30)
 
    def week(self, day, weight, done, bed, wake):
        cs.save_checkin(self.conn, self.uid, {"checkin_date": day, "weight": weight, "done_days": done,
                                              "sleep": {"bed_time": bed, "wake_time": wake}}, today=self.today)
 
    def test_one_checkin_gives_the_need_more_data_suggestion(self):
        self.week("2026-10-05", 74.4, ["mon", "wed", "fri"], "23:00", "06:30")
        rec = ss.generate_suggestion(self.conn, self.uid)
        out = ss.latest_suggestion(self.conn, self.uid)
        self.assertEqual(out["recommendation_id"], rec)
        self.assertIn("one more weekly check-in", out["text"])
        self.assertIn("R1", out["evidence"][0]["description"])
        self.assertEqual(out["based_on"], [])
 
    def test_low_adherence_suggestion_cites_the_exact_metric(self):
        self.week("2026-10-05", 74.4, ["mon"], "23:00", "06:30")
        self.week("2026-10-12", 74.2, [], "23:00", "06:30")
        ss.generate_suggestion(self.conn, self.uid)
        out = ss.latest_suggestion(self.conn, self.uid)
        self.assertIn("17%", out["text"])                               # 1 of 6 planned sessions
        self.assertEqual(out["based_on"][0]["label"], "Adherence")
        self.assertEqual(out["based_on"][0]["value_text"], "17%")
        self.assertIn("R3", out["evidence"][0]["description"])
        self.assertEqual(out["evidence"][0]["version"], suggestions.RULE_SET_VERSION)
        self.assertEqual(out["tags"], ["Rules"])
        self.assertIn("not medical advice", out["disclaimer"])
        # traceability: the link rows point at real stored metric rows
        n = self.conn.execute("""SELECT COUNT(*) FROM recommendation_metrics rm
                                 JOIN metrics m ON m.metric_id = rm.metric_id""").fetchone()[0]
        self.assertEqual(n, 1)
 
    def test_good_weeks_give_on_track(self):
        for day, w in (("2026-09-21", 74.4), ("2026-09-28", 74.0), ("2026-10-05", 73.6), ("2026-10-12", 73.2)):
            self.week(day, w, ["mon", "wed", "fri"], "23:00", "06:30")
        ss.generate_suggestion(self.conn, self.uid)
        out = ss.latest_suggestion(self.conn, self.uid)
        self.assertTrue(out["text"].startswith("Nothing we measure") or "slowly" in out["text"] or "faster" in out["text"])
        self.assertTrue(len(out["based_on"]) >= 1)
 
    def test_previous_results_is_none_for_the_first_check_in_and_present_after(self):
        from datetime import date
        self.week("2026-10-05", 74.4, ["mon", "wed", "fri"], "23:00", "06:30")
        self.assertIsNone(ss._previous_results(self.conn, self.uid, date(2026, 10, 5)))
        self.week("2026-10-12", 74.0, ["mon", "wed", "fri"], "23:00", "06:30")
        before = self.conn.execute("SELECT COUNT(*) FROM metrics").fetchone()[0]
        previous = ss._previous_results(self.conn, self.uid, date(2026, 10, 12))
        self.assertIsNotNone(previous)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM metrics").fetchone()[0], before)  # nothing stored
 
    def test_no_suggestion_before_one_is_generated(self):
        self.assertIsNone(ss.latest_suggestion(self.conn, self.uid))
        with self.assertRaises(LookupError):
            ss.generate_suggestion(self.conn, 999)
 
 
class RuleTests(unittest.TestCase):
    """The rules alone, with hand-made metric results."""
 
    @staticmethod
    def r(metric_type, value, **detail):
        return m.MetricResult(metric_type, m.OK, value, "", detail)
 
    ADH_OK = None
 
    def adherence(self, pct, scheduled=9, weeks=3):
        return self.r("adherence_pct", pct, weeks_used=weeks, completed=0, scheduled=scheduled)
 
    def fast(self):
        return self.r("loss_vs_expected_ratio", 1.6, status="faster_than_expected")
 
    def test_priority_safety_beats_everything(self):
        results = [self.adherence(20), self.r("sleep_consistency_min", 90), self.fast()]
        previous = [self.fast()]
        self.assertEqual(suggestions.choose_suggestion(results, previous).rule_key, "R2")
 
    def test_r2_needs_two_fast_check_ins_in_a_row(self):
        results = [self.adherence(90), self.fast()]
        # first fast check-in, or no earlier check-in at all: R2 waits and R7 mentions it
        for previous in (None, [], [self.r("loss_vs_expected_ratio", 1.0, status="on_track")]):
            s = suggestions.choose_suggestion(results, previous)
            self.assertEqual(s.rule_key, "R7")
            self.assertIn("a little faster than planned", s.text)
        # two in a row: R2, with the softer wording
        s = suggestions.choose_suggestion(results, [self.fast()])
        self.assertEqual(s.rule_key, "R2")
        self.assertIn("smaller deficit", s.text)
 
    def test_r3_never_goes_below_two_sessions(self):
        three = suggestions.choose_suggestion([self.adherence(30, scheduled=9, weeks=3)])
        self.assertIn("try 2 sessions a week", three.text)
        four = suggestions.choose_suggestion([self.adherence(30, scheduled=12, weeks=3)])
        self.assertIn("try 3 sessions a week", four.text)
        two = suggestions.choose_suggestion([self.adherence(30, scheduled=6, weeks=3)])
        self.assertIn("stay at 2 sessions a week", two.text)
        one = suggestions.choose_suggestion([self.adherence(30, scheduled=3, weeks=3)])
        self.assertIn("Keep your 1 session a week", one.text)
        for s in (three, four, two, one):
            self.assertEqual(s.rule_key, "R3")
            self.assertNotIn("try 1 session", s.text)
 
    def test_r6_offers_reps_or_load(self):
        strong = self.r("strength_progression_pct_per_week:Squat", 3.0)
        s = suggestions.choose_suggestion([self.adherence(90), strong])
        self.assertEqual(s.rule_key, "R6")
        self.assertIn("one rep to each set", s.text)
 
    def test_rule_set_is_v2_and_every_citation_says_what_is_a_design_choice(self):
        self.assertEqual(suggestions.RULE_SET_VERSION, "v2")
        for key in ("R2", "R3", "R4", "R5", "R6"):
            self.assertIn("design choice", suggestions.RULES[key]["citation"])
 
    def test_low_adherence_suggests_a_smaller_plan(self):
        s = suggestions.choose_suggestion([self.adherence(40, scheduled=12, weeks=4)])
        self.assertEqual(s.rule_key, "R3")
        self.assertIn("2 sessions a week", s.text)  # 3 a week planned, minus one
 
    def test_sleep_then_slow_loss_then_strength_then_default(self):
        self.assertEqual(suggestions.choose_suggestion([self.adherence(90), self.r("sleep_consistency_min", 60)]).rule_key, "R4")
        slow = self.r("loss_vs_expected_ratio", 0.4, status="slower_than_expected")
        self.assertEqual(suggestions.choose_suggestion([self.adherence(90), slow]).rule_key, "R5")
        strong = self.r("strength_progression_pct_per_week:Squat", 3.0)
        self.assertEqual(suggestions.choose_suggestion([self.adherence(90), strong]).rule_key, "R6")
        self.assertEqual(suggestions.choose_suggestion([self.adherence(90)]).rule_key, "R7")
 
    def test_no_data_means_r1(self):
        nothing = [m.MetricResult("adherence_pct", m.NOT_ENOUGH), m.MetricResult("weight_trend_kg_per_week", m.NOT_ENOUGH)]
        self.assertEqual(suggestions.choose_suggestion(nothing).rule_key, "R1")
        self.assertEqual(suggestions.choose_suggestion([]).rule_key, "R1")
 
    def test_every_rule_key_used_exists(self):
        self.assertEqual(set(suggestions.RULES), {"R1", "R2", "R3", "R4", "R5", "R6", "R7"})
 
    def test_display_formats(self):
        self.assertEqual(suggestions.display_for("weight_trend_kg_per_week", -0.425)["value_text"], "-0.42 kg/week")
        self.assertEqual(suggestions.display_for("strength_progression_pct_per_week:Squat", 5.0)["label"], "Strength (Squat)")
 
 
if __name__ == "__main__":
    unittest.main()
 