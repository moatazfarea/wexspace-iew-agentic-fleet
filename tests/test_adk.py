import asyncio
import os
import unittest
from unittest.mock import patch

from wexspace.adk_fleet import (
    ELIGIBLE_MODEL,
    build_live_root_agent,
    configure_gemini_developer_api,
    run_local_adk_smoke,
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


if __name__ == "__main__":
    unittest.main()
