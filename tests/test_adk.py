import asyncio
import unittest

from wexspace.adk_fleet import ELIGIBLE_MODEL, build_live_root_agent, run_local_adk_smoke


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
            "governing_engineering_agent",
            "engineering_specialist",
            "verification_specialist",
        ])
        self.assertEqual([len(agent.tools) for agent in root.sub_agents], [1, 1, 1])


if __name__ == "__main__":
    unittest.main()
