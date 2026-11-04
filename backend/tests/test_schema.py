"""Schema tests. Standard library only: run with `python -m unittest discover -s tests -v` or pytest."""
import json
import sqlite3
import unittest

from app import db

EXPECTED_TABLES = {
    "users", "profile_snapshots", "checkins", "exercises", "workout_logs", "nutrition_logs",
    "sleep_logs", "metrics", "evidence_rules", "recommendations", "recommendation_metrics",
    "recommendation_rules", "personas", "simulation_runs",
}


class SchemaTestCase(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(":memory:")
        db.init_db(self.conn)

    def tearDown(self):
        self.conn.close()

    # helpers -------------------------------------------------------------
    def add_user(self, email="a@example.com"):
        cur = self.conn.execute("INSERT INTO users (email, password_hash) VALUES (?, 'x')", (email,))
        return cur.lastrowid

    def add_snapshot(self, user_id, weight=70.0):
        cur = self.conn.execute(
            "INSERT INTO profile_snapshots (user_id, weight, height, training_schedule) VALUES (?, ?, 175, ?)",
            (user_id, weight, json.dumps({"days": ["mon", "wed", "fri"]})),
        )
        return cur.lastrowid

    def add_checkin(self, user_id, snapshot_id, date="2026-10-12"):
        cur = self.conn.execute(
            "INSERT INTO checkins (user_id, snapshot_id, checkin_date) VALUES (?, ?, ?)",
            (user_id, snapshot_id, date),
        )
        return cur.lastrowid

    def add_recommendation(self, user_id):
        cur = self.conn.execute(
            "INSERT INTO recommendations (user_id, content) VALUES (?, 'Keep volume steady this week')", (user_id,)
        )
        return cur.lastrowid

    def count(self, table):
        return self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    # migration -------------------------------------------------------------
    def test_all_er_tables_exist(self):
        rows = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        self.assertEqual({r["name"] for r in rows}, EXPECTED_TABLES)

    def test_init_is_idempotent(self):
        before = self.count("exercises")
        db.init_db(self.conn)
        self.assertEqual(self.count("exercises"), before)

    def test_exercises_are_seeded(self):
        self.assertGreaterEqual(self.count("exercises"), 15)
        groups = {r[0] for r in self.conn.execute("SELECT DISTINCT muscle_group FROM exercises")}
        self.assertEqual(groups, {"chest", "back", "legs", "shoulders", "arms", "core", "general"})

    def test_health_report(self):
        report = db.health(self.conn)
        self.assertEqual(report["database"], "ok")
        self.assertEqual(report["tables"], len(EXPECTED_TABLES))
        self.assertEqual(report["schema_version"], 3)

    # integrity -------------------------------------------------------------
    def test_email_is_unique(self):
        self.add_user("dup@example.com")
        with self.assertRaises(sqlite3.IntegrityError):
            self.add_user("dup@example.com")

    def test_foreign_keys_are_enforced(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.add_snapshot(user_id=999)

    def test_snapshots_are_immutable_fr7(self):
        snap = self.add_snapshot(self.add_user())
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("UPDATE profile_snapshots SET weight = 80 WHERE snapshot_id = ?", (snap,))

    def test_one_checkin_per_snapshot(self):
        user = self.add_user()
        snap = self.add_snapshot(user)
        self.add_checkin(user, snap)
        with self.assertRaises(sqlite3.IntegrityError):
            self.add_checkin(user, snap, date="2026-10-19")

    def test_checkin_cannot_use_another_users_snapshot(self):
        alice, bob = self.add_user("alice@example.com"), self.add_user("bob@example.com")
        bobs_snapshot = self.add_snapshot(bob)
        with self.assertRaises(sqlite3.IntegrityError):
            self.add_checkin(alice, bobs_snapshot)

    def test_one_checkin_per_user_per_date(self):
        user = self.add_user()
        self.add_checkin(user, self.add_snapshot(user), date="2026-10-12")
        with self.assertRaises(sqlite3.IntegrityError):
            self.add_checkin(user, self.add_snapshot(user), date="2026-10-12")

    def test_nutrition_and_sleep_are_optional_and_single(self):
        user = self.add_user()
        checkin = self.add_checkin(user, self.add_snapshot(user))
        self.conn.execute("INSERT INTO nutrition_logs (checkin_id, protein_target_met) VALUES (?, 1)", (checkin,))
        self.conn.execute("INSERT INTO sleep_logs (checkin_id, bed_time, wake_time) VALUES (?, '23:00', '06:30')", (checkin,))
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO nutrition_logs (checkin_id) VALUES (?)", (checkin,))
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO sleep_logs (checkin_id) VALUES (?)", (checkin,))

    def test_workout_log_allows_optional_load(self):
        user = self.add_user()
        checkin = self.add_checkin(user, self.add_snapshot(user))
        exercise = self.conn.execute("SELECT exercise_id FROM exercises WHERE name = 'Squat'").fetchone()[0]
        self.conn.execute("INSERT INTO workout_logs (checkin_id, exercise_id) VALUES (?, ?)", (checkin, exercise))
        self.conn.execute(
            "INSERT INTO workout_logs (checkin_id, exercise_id, sets, reps, weight_used) VALUES (?, ?, 3, 8, 60)",
            (checkin, exercise),
        )
        self.assertEqual(self.count("workout_logs"), 2)
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO workout_logs (checkin_id, exercise_id, reps) VALUES (?, ?, 0)", (checkin, exercise))

    # traceability and simulation ---------------------------------------------
    def test_recommendation_traceability_nfr7(self):
        user = self.add_user()
        rec = self.add_recommendation(user)
        metric = self.conn.execute("INSERT INTO metrics (user_id, metric_type, value) VALUES (?, 'adherence', 0.75)", (user,)).lastrowid
        rule = self.conn.execute("INSERT INTO evidence_rules (description, citation, version) VALUES ('d', 'c', '1')").lastrowid
        self.conn.execute("INSERT INTO recommendation_metrics VALUES (?, ?)", (rec, metric))
        self.conn.execute("INSERT INTO recommendation_rules VALUES (?, ?)", (rec, rule))
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO recommendation_metrics VALUES (?, ?)", (rec, metric))

    def test_simulation_run_links_persona_and_recommendation(self):
        user = self.add_user("persona-1@sim.local")
        rec = self.add_recommendation(user)
        persona = self.conn.execute("INSERT INTO personas (name) VALUES ('Consistent beginner')").lastrowid
        self.conn.execute(
            "INSERT INTO simulation_runs (persona_id, recommendation_id, timepoint_label) VALUES (?, ?, 'week_1')",
            (persona, rec),
        )
        self.assertEqual(self.count("simulation_runs"), 1)

    # privacy ---------------------------------------------------------------
    def test_deleting_a_user_removes_all_their_data(self):
        user = self.add_user()
        snap = self.add_snapshot(user)
        checkin = self.add_checkin(user, snap)
        exercise = self.conn.execute("SELECT exercise_id FROM exercises LIMIT 1").fetchone()[0]
        self.conn.execute("INSERT INTO workout_logs (checkin_id, exercise_id) VALUES (?, ?)", (checkin, exercise))
        self.conn.execute("INSERT INTO sleep_logs (checkin_id) VALUES (?)", (checkin,))
        self.conn.execute("INSERT INTO metrics (user_id, metric_type, value) VALUES (?, 'adherence', 1)", (user,))
        self.add_recommendation(user)
        self.conn.execute("DELETE FROM users WHERE user_id = ?", (user,))
        for table in ("profile_snapshots", "checkins", "workout_logs", "sleep_logs", "metrics", "recommendations"):
            self.assertEqual(self.count(table), 0, f"{table} still has rows after user deletion")
        self.assertGreater(self.count("exercises"), 0, "shared exercise catalogue must survive")


if __name__ == "__main__":
    unittest.main()
