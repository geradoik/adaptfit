"""Schema version 3 tests: the new recommendations columns and the upgrade of an older database file."""
import sqlite3
import unittest
 
from app import db, demo_seed, suggestion_service
 
 
class UpgradeTests(unittest.TestCase):
    def test_old_database_gets_the_new_columns_once(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("CREATE TABLE recommendations (recommendation_id INTEGER PRIMARY KEY, user_id INTEGER, "
                     "generated_at TEXT, content TEXT NOT NULL)")
        conn.execute("INSERT INTO recommendations (user_id, content) VALUES (1, 'old advice')")
        db._upgrade_old_database(conn)
        db._upgrade_old_database(conn)                         # running it twice must be harmless
        row = conn.execute("SELECT * FROM recommendations").fetchone()
        self.assertEqual((row["source"], row["question"]), ("rules", None))   # old rows count as rule-based
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO recommendations (user_id, content, source) VALUES (1, 'x', 'robot')")
        conn.close()
 
    def test_fresh_database_has_schema_version_3_and_the_columns(self):
        conn = db.connect(":memory:")
        db.init_db(conn)
        self.assertEqual(db.health(conn)["schema_version"], 3)
        names = {r["name"] for r in conn.execute("PRAGMA table_info(recommendations)")}
        self.assertTrue({"source", "question"} <= names)
        conn.close()
 
    def test_free_question_rows_never_become_this_weeks_suggestion(self):
        conn = db.connect(":memory:")
        db.init_db(conn)
        self.addCleanup(conn.close)
        uid = demo_seed.seed_demo(conn)
        before = suggestion_service.latest_suggestion(conn, uid)
        conn.execute("INSERT INTO recommendations (user_id, content, source, question) VALUES (?, 'an AI answer', "
                     "'llm', 'a question')", (uid,))
        conn.commit()
        after = suggestion_service.latest_suggestion(conn, uid)
        self.assertEqual(before["recommendation_id"], after["recommendation_id"])
 
 
if __name__ == "__main__":
    unittest.main()
