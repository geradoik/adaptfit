"""API smoke test. Skipped automatically until FastAPI is installed (pip install -r requirements.txt)."""
import os
import tempfile
import unittest

try:
    from fastapi.testclient import TestClient
except ImportError:  # pragma: no cover
    TestClient = None


@unittest.skipIf(TestClient is None, "fastapi/httpx not installed")
class HealthTestCase(unittest.TestCase):
    def test_health_reports_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["ADAPTFIT_DB"] = os.path.join(tmp, "test.db")
            from app.main import app

            with TestClient(app) as client:
                response = client.get("/api/health")
            self.assertEqual(response.status_code, 200)
            body = response.json()
            self.assertEqual(body["status"], "ok")
            self.assertEqual(body["database"], "ok")
            self.assertEqual(body["tables"], 14)


if __name__ == "__main__":
    unittest.main()
