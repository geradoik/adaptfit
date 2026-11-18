import csv
import os
import tempfile
import unittest
 
from app import db, evaluation, personas
from app.llm_client import FakeClient, LLMUnavailable
 
 
class PersonaTests(unittest.TestCase):
    def run_one(self, name, client=None):
        conn = db.connect(":memory:")
        db.init_db(conn)
        self.addCleanup(conn.close)
        return conn, personas.run_persona(conn, name, client=client)
 
    def test_each_persona_triggers_its_own_rule_at_week_12(self):
        for name, spec in personas.PERSONAS.items():
            _, rows = self.run_one(name)
            self.assertEqual([r["week"] for r in rows], [1, 6, 12])
            self.assertEqual(rows[0]["rule"], "R1", name)             # one check-in is never enough
            self.assertEqual(rows[2]["rule"], spec["expected"], name)
 
    def test_runs_are_saved_with_persona_email_and_timepoints(self):
        conn, _ = self.run_one("skipper")
        email = conn.execute("SELECT email FROM users").fetchone()[0]
        self.assertEqual(email, "persona-skipper@sim.local")
        labels = [r[0] for r in conn.execute("SELECT timepoint_label FROM simulation_runs ORDER BY run_id")]
        self.assertEqual(labels, ["week_1", "week_6", "week_12"])
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM checkins").fetchone()[0], 12)
 
    def test_results_are_the_same_every_time(self):
        _, first = self.run_one("crash_dieter")
        _, second = self.run_one("crash_dieter")
        self.assertEqual(first, second)
 
    def test_ai_answers_are_collected_when_a_client_is_given(self):
        _, rows = self.run_one("steady_lifter", FakeClient("Keep going [E6]."))
        self.assertTrue(all(r["ai_source"] == "llm" for r in rows))
        _, rows = self.run_one("steady_lifter", FakeClient(error=LLMUnavailable("down")))
        self.assertTrue(all(r["ai_source"] == "rules" for r in rows))   # the fallback is part of the evaluation
 
 
class EvaluationTests(unittest.TestCase):
    def test_all_personas_pass(self):
        rows, failures = evaluation.evaluate()
        self.assertEqual(failures, [])
        self.assertEqual(len(rows), 15)
 
    def test_table_and_csv(self):
        rows, _ = evaluation.evaluate()
        table = evaluation.format_table(rows)
        self.assertEqual(len(table.splitlines()), 16) # header + 15 rows
        self.assertIn("plateau", table)
        path = os.path.join(tempfile.mkdtemp(), "out.csv")
        self.assertEqual(evaluation.main(["--csv", path]), 0)
        with open(path, newline="", encoding="utf-8") as handle:
            saved = list(csv.DictReader(handle))
        self.assertEqual(len(saved), 15)
        self.assertEqual(saved[0]["persona"], "steady_lifter")
 
    def test_a_wrong_expectation_is_reported_as_a_failure(self):
        original = personas.PERSONAS["skipper"]["expected"]
        personas.PERSONAS["skipper"]["expected"] = "R7"
        try:
            _, failures = evaluation.evaluate()
        finally:
            personas.PERSONAS["skipper"]["expected"] = original
        self.assertEqual(failures, ["skipper: week 12 gave R3, expected R7"])
 
 
if __name__ == "__main__":
    unittest.main()
