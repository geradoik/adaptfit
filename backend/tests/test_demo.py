"""Demo persona and metrics endpoint tests."""
import os
import tempfile
import unittest
from datetime import date

from app import db, demo_seed, metrics_service

try:
    from fastapi.testclient import TestClient
except ImportError:  # pragma: no cover
    TestClient = None


class DemoSeedTests(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(":memory:")
        db.init_db(self.conn)

    def test_seed_is_idempotent(self):
        first = demo_seed.seed_demo(self.conn)
        self.assertEqual(demo_seed.seed_demo(self.conn), first)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM checkins").fetchone()[0], 6)

    def test_demo_metrics_are_what_the_docs_say(self):
        uid = demo_seed.seed_demo(self.conn)
        res = {r.metric_type.split(":")[0]: r for r in metrics_service.compute_all(self.conn, uid, date(2026, 10, 12), store=False)}
        self.assertAlmostEqual(res["adherence_pct"].value, 100 * 11 / 12)  # last 4 weeks done 3,2,3,3 of 3
        self.assertTrue(res["adherence_pct"].ok and res["sleep_consistency_min"].ok)
        self.assertAlmostEqual(res["weight_trend_kg_per_week"].value, -0.425)
        self.assertEqual(res["loss_vs_expected_ratio"].detail["status"], "on_track")
        self.assertTrue(res["strength_progression_pct_per_week"].value > 0)


class ReportTests(unittest.TestCase):
    """Same logic the endpoints use, tested without FastAPI."""
    def setUp(self):
        self.conn = db.connect(":memory:")
        db.init_db(self.conn)
        self.uid = demo_seed.seed_demo(self.conn)

    def test_report_shape_and_default_date(self):
        r = metrics_service.metrics_report(self.conn, self.uid)
        self.assertEqual(r["as_of"], "2026-10-12")
        types = {m["metric_type"] for m in r["metrics"]}
        self.assertTrue({"adherence_pct", "weight_trend_kg_per_week", "sleep_consistency_min", "bmr_kcal",
                         "tdee_kcal", "expected_loss_kg_per_week", "muscle_gain_kg_per_week",
                         "loss_vs_expected_ratio"} <= types)
        self.assertTrue(any(t.startswith("strength_progression_pct_per_week:") for t in types))

    def test_unknown_user_and_bad_date(self):
        with self.assertRaises(LookupError):
            metrics_service.metrics_report(self.conn, 999)
        with self.assertRaises(ValueError):
            metrics_service.metrics_report(self.conn, self.uid, "nope")

    def test_report_is_json_serialisable(self):
        import json
        json.dumps(metrics_service.metrics_report(self.conn, self.uid))


@unittest.skipIf(TestClient is None, "fastapi/httpx not installed")
class MetricsEndpointTests(unittest.TestCase):
    def test_demo_and_user_endpoints(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["ADAPTFIT_DB"] = os.path.join(tmp, "t.db")
            from app.main import app
            with TestClient(app) as client:
                demo = client.get("/api/demo/metrics")
                self.assertEqual(demo.status_code, 200)
                body = demo.json()
                self.assertEqual(body["as_of"], "2026-10-12")
                types = {m["metric_type"] for m in body["metrics"]}
                self.assertIn("adherence_pct", types)
                self.assertIn("tdee_kcal", types)
                again = client.get(f"/api/users/{body['user_id']}/metrics").json()
                self.assertEqual(again["as_of"], "2026-10-12")
                self.assertEqual(client.get("/api/users/999/metrics").status_code, 404)
                self.assertEqual(client.get(f"/api/users/{body['user_id']}/metrics?as_of=nope").status_code, 422)


if __name__ == "__main__":
    unittest.main()
