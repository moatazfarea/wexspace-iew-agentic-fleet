import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from wexspace.api import app


class ApiTests(unittest.TestCase):
    def test_health_and_agent_discovery(self):
        client = TestClient(app)
        health = client.get("/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "ok")
        agents = client.get("/agents")
        self.assertEqual(agents.status_code, 200)
        self.assertEqual(len(agents.json()["agents"]), 3)

    def test_live_adk_fails_closed_without_api_key(self):
        client = TestClient(app)
        payload = {
            "goal": "Analyze synthetic cooling-water network",
            "engineering_input": {
                "project_id": "incomplete-on-purpose"
            },
        }
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "", "GEMINI_API_KEY": ""}):
            response = client.post("/adk/live", json=payload)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"]["status"], "BLOCKED_MISSING_GEMINI_API_KEY")


if __name__ == "__main__":
    unittest.main()
