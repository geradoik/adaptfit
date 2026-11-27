"""History and compare tests (frames 05a and 05b)."""
import os
import tempfile
import unittest

from app import db, demo_seed, history_service

try:
    from fastapi.testclient import TestClient
except ImportError:  # pragma: no cover
    TestClient = None


class TimelineTests(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(":memory:")
        db.init_db(self.conn)
        self.uid = demo_seed.seed_demo(self.conn)

    def test_newest_first_with_changes(self):
        entries = history_service.timeline(self.conn, self.uid)["entries"]
        self.assertEqual(len(entries), 6)
        self.assertEqual(entries[0]["date"], "2026-10-12")
        self.assertEqual(entries[-1]["date"], "2026-09-07")
        self.assertEqual(entries[0]["weight"], 72.3)
        self.assertEqual(entries[0]["change"], -0.4)      # 72.3 - 72.7
        self.assertIsNone(entries[-1]["change"])           # nothing before the oldest one
        self.assertTrue(all(e["kind"] == "Check-in" for e in entries))

    def test_unknown_user(self):
        with self.assertRaises(LookupError):
            history_service.timeline(self.conn, 999)

    def test_user_with_no_snapshots(self):
        uid = self.conn.execute("INSERT INTO users (email, password_hash) VALUES ('x@x.test', 'x')").lastrowid
        self.conn.commit()
        self.assertEqual(history_service.timeline(self.conn, uid), {"entries": []})


class CompareTests(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(":memory:")
        db.init_db(self.conn)
        self.uid = demo_seed.seed_demo(self.conn)

    def test_weight_and_change(self):
        result = history_service.compare(self.conn, self.uid, "2026-09-07", "2026-10-12")
        self.assertEqual(result["from"]["weight"], 74.4)
        self.assertEqual(result["to"]["weight"], 72.3)
        self.assertEqual(result["change"]["weight"], -2.1)

    def test_not_enough_data_early_on(self):
        # adherence needs 2 weeks of data, sleep consistency needs 3 check-ins
        result = history_service.compare(self.conn, self.uid, "2026-09-07", "2026-09-14")
        self.assertIsNone(result["from"]["adherence_pct"])
        self.assertIsNone(result["from"]["sleep_consistency_min"])
        self.assertIsNotNone(result["to"]["adherence_pct"])      # two weeks by 14 Sep
        self.assertIsNone(result["to"]["sleep_consistency_min"])  # still only 2 sleep entries
        self.assertIsNone(result["change"]["adherence_pct"])      # no change when one side is missing

    def test_adherence_uses_only_data_up_to_the_date(self):
        result = history_service.compare(self.conn, self.uid, "2026-09-14", "2026-10-12")
        # by 14 Sep: weeks (3,3) and (3,2) = 5 of 6
        self.assertAlmostEqual(result["from"]["adherence_pct"], 100 * 5 / 6)
        # by 12 Oct, last 4 weeks: 3,2,3,3 done of 3 planned = 11 of 12 (same as the Home screen)
        self.assertAlmostEqual(result["to"]["adherence_pct"], 100 * 11 / 12)
        self.assertAlmostEqual(result["change"]["adherence_pct"], round(100 * 11 / 12 - 100 * 5 / 6, 1))

    def test_suggestion_found_for_the_seeded_date(self):
        result = history_service.compare(self.conn, self.uid, "2026-09-07", "2026-10-12")
        self.assertIsNone(result["from"]["suggestion"])          # the seed only made one, on 12 Oct
        self.assertIsInstance(result["to"]["suggestion"], str)

    def test_bad_input(self):
        with self.assertRaises(ValueError):
            history_service.compare(self.conn, self.uid, "last week", "2026-10-12")
        with self.assertRaises(ValueError):
            history_service.compare(self.conn, self.uid, "2026-10-12", "2026-09-07")   # wrong order
        with self.assertRaises(ValueError):
            history_service.compare(self.conn, self.uid, "2026-09-08", "2026-10-12")   # no check-in that day
        with self.assertRaises(LookupError):
            history_service.compare(self.conn, 999, "2026-09-07", "2026-10-12")

    def test_compare_does_not_write_anything(self):
        before = [self.conn.execute("SELECT COUNT(*) FROM " + t).fetchone()[0]
                  for t in ("metrics", "recommendations", "checkins", "profile_snapshots")]
        history_service.compare(self.conn, self.uid, "2026-09-07", "2026-10-12")
        history_service.timeline(self.conn, self.uid)
        after = [self.conn.execute("SELECT COUNT(*) FROM " + t).fetchone()[0]
                 for t in ("metrics", "recommendations", "checkins", "profile_snapshots")]
        self.assertEqual(before, after)


@unittest.skipIf(TestClient is None, "fastapi/httpx not installed")
class HistoryApiTests(unittest.TestCase):
    def test_history_and_compare_endpoints(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["ADAPTFIT_DB"] = os.path.join(tmp, "t.db")
            from app.main import app
            with TestClient(app) as client:
                uid = client.get("/api/demo/user").json()["user_id"]

                history = client.get(f"/api/users/{uid}/history")
                self.assertEqual(history.status_code, 200)
                self.assertEqual(len(history.json()["entries"]), 6)
                self.assertEqual(client.get("/api/users/999/history").status_code, 404)

                url = f"/api/users/{uid}/compare"
                good = client.get(url, params={"from_date": "2026-09-07", "to_date": "2026-10-12"})
                self.assertEqual(good.status_code, 200)
                self.assertEqual(good.json()["change"]["weight"], -2.1)
                self.assertEqual(client.get(url, params={"from_date": "x", "to_date": "2026-10-12"}).status_code, 422)
                self.assertEqual(client.get(url).status_code, 422)  # missing query parameters
                self.assertEqual(client.get("/api/users/999/compare",
                                            params={"from_date": "2026-09-07", "to_date": "2026-10-12"}).status_code, 404)


if __name__ == "__main__":
    unittest.main()
