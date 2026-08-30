import asyncio
import json
import os
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from wexspace.adk_fleet import (
    ELIGIBLE_MODEL,
    build_live_root_agent,
    configure_gemini_developer_api,
    configure_vertex_ai,
    run_local_adk_smoke,
    run_live_gemini_payload,
)


class AdkTests(unittest.TestCase):
    def test_local_google_adk_executes_three_agent_sequence(self):
        result = asyncio.run(run_local_adk_smoke())
        self.assertTrue(result["passed"])
        self.assertEqual(len(result["observed_agents"]), 3)
        self.assertEqual(result["mode"], "LOCAL_MODEL_DOUBLE_NO_GEMINI_CLAIM")

    def test_live_topology_targets_eligible_model_and_bounded_tools(self):
        root = build_live_root_agent()
        self.assertEqual(len(root.sub_agents), 3)
        self.assertTrue(all(agent.model == ELIGIBLE_MODEL for agent in root.sub_agents))
        self.assertEqual([agent.name for agent in root.sub_agents], [
            "wexspace_governing_agent",
            "iew_engineering_specialist",
            "wexspace_verification_evidence_specialist",
        ])
        self.assertEqual([len(agent.tools) for agent in root.sub_agents], [1, 1, 1])
        self.assertEqual(ELIGIBLE_MODEL, "gemini-3.7-flash")

    def test_gemini_route_is_pinned_without_secret_logging(self):
        with patch.dict(os.environ, {}, clear=True):
            route = configure_gemini_developer_api("test-only-not-a-real-key")
            self.assertEqual(os.environ["GOOGLE_GENAI_USE_VERTEXAI"], "FALSE")
            self.assertEqual(os.environ["GOOGLE_API_KEY"], "test-only-not-a-real-key")
            self.assertNotIn("GOOGLE_CLOUD_PROJECT", os.environ)
            self.assertNotIn("GOOGLE_CLOUD_LOCATION", os.environ)
            self.assertEqual(route["backend"], "GEMINI_DEVELOPER_API")
            self.assertFalse(route["vertex_project_location_configured"])
            self.assertFalse(route["secret_values_logged"])

    def test_vertex_route_uses_adc_without_api_key(self):
        payload = json.loads(
            Path("data/UTL-NET-001_SYNTHETIC_INPUT.json").read_text(encoding="utf-8")
        )
        events = {
            "events": [
                {"author": "wexspace_governing_agent"},
                {"author": "iew_engineering_specialist"},
                {"author": "wexspace_verification_evidence_specialist"},
            ]
        }
        environment = {
            "GOOGLE_GENAI_USE_VERTEXAI": "TRUE",
            "GOOGLE_CLOUD_PROJECT": "wexspace-agentic-2026",
            "GOOGLE_CLOUD_LOCATION": "global",
        }
        with patch.dict(os.environ, environment, clear=True):
            with patch(
                "wexspace.adk_fleet._run_agent",
                new=AsyncMock(return_value=events),
            ):
                result = asyncio.run(run_live_gemini_payload(payload))
            self.assertTrue(result["passed"])
            self.assertEqual(result["execution_route"]["backend"], "VERTEX_AI")
            self.assertEqual(
                result["execution_route"]["credential_source"],
                "APPLICATION_DEFAULT_CREDENTIALS",
            )
            self.assertFalse(result["execution_route"]["api_key_required"])
            self.assertNotIn("GOOGLE_API_KEY", os.environ)
            self.assertNotIn("GEMINI_API_KEY", os.environ)

    def test_vertex_configuration_never_logs_or_requires_key(self):
        with patch.dict(os.environ, {}, clear=True):
            route = configure_vertex_ai("wexspace-agentic-2026", "global")
            self.assertEqual(os.environ["GOOGLE_GENAI_USE_VERTEXAI"], "TRUE")
            self.assertEqual(route["backend"], "VERTEX_AI")
            self.assertFalse(route["api_key_required"])
            self.assertFalse(route["secret_values_logged"])


if __name__ == "__main__":
    unittest.main()
