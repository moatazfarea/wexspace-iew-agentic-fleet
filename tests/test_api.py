import json
import unittest
from pathlib import Path
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
        with patch.dict(
            "os.environ",
            {
                "GOOGLE_GENAI_USE_VERTEXAI": "FALSE",
                "GOOGLE_API_KEY": "",
                "GEMINI_API_KEY": "",
            },
            clear=True,
        ):
            response = client.post("/adk/live", json=payload)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"]["status"], "BLOCKED_MISSING_GEMINI_API_KEY")

    def test_pae006_endpoint_fails_closed_without_google_route(self):
        payload = json.loads(
            Path("data/PAE006_FRESH_MOTIVE_AIR_SENSITIVITY_R01_INPUT.json").read_text(
                encoding="utf-8"
            )
        )
        client = TestClient(app)
        with patch.dict(
            "os.environ",
            {
                "GOOGLE_GENAI_USE_VERTEXAI": "FALSE",
                "GOOGLE_API_KEY": "",
                "GEMINI_API_KEY": "",
            },
            clear=True,
        ):
            response = client.post(
                "/adk/pae006/fresh",
                json={
                    "goal": "Execute PAE-006 fresh motive-air sensitivity study",
                    "engineering_input": payload,
                    "asynchronous": False,
                },
            )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"]["status"], "BLOCKED_MISSING_GOOGLE_ROUTE")


if __name__ == "__main__":
    unittest.main()
