import asyncio
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from wexspace.adk_fleet import (
    ELIGIBLE_MODEL,
    build_live_pae006_root_agent,
    run_live_pae006_payload,
)
from wexspace.pae006 import (
    MANIFEST_FILENAME,
    REQUIRED_FILENAMES,
    independently_verify_pae006_study,
    pae006_fresh_motive_air_sensitivity,
    validate_pae006_input,
)


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data/PAE006_FRESH_MOTIVE_AIR_SENSITIVITY_R01_INPUT.json"


class Pae006Tests(unittest.TestCase):
    def payload(self):
        return json.loads(INPUT_PATH.read_text(encoding="utf-8"))

    def test_controlled_input_and_fresh_12_point_artifacts(self):
        payload = self.payload()
        self.assertEqual(validate_pae006_input(payload), [])
        with tempfile.TemporaryDirectory() as temp:
            with patch.dict(os.environ, {"WEXSPACE_PAE_OUTPUT_ROOT": temp}):
                result = pae006_fresh_motive_air_sensitivity(
                    json.dumps(payload, sort_keys=True)
                )
                verification = independently_verify_pae006_study(
                    json.dumps(payload, sort_keys=True)
                )
            self.assertEqual(result["point_count"], 12)
            self.assertTrue(result["all_points_choked"])
            self.assertTrue(verification["verified"])
            self.assertEqual(verification["workflow_state"], "AWAITING_HUMAN_REVIEW")
            for filename in REQUIRED_FILENAMES:
                self.assertIn(filename, verification["artifacts"])
                self.assertTrue(Path(verification["artifacts"][filename]["path"]).is_file())
            self.assertIn(MANIFEST_FILENAME, verification["artifacts"])
            curve = Path(verification["artifacts"][REQUIRED_FILENAMES[2]]["path"])
            self.assertEqual(curve.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
            csv_path = Path(verification["artifacts"][REQUIRED_FILENAMES[1]]["path"])
            self.assertEqual(len(csv_path.read_text(encoding="utf-8").splitlines()), 13)

    def test_scaling_and_choking_are_physically_consistent(self):
        payload = self.payload()
        with tempfile.TemporaryDirectory() as temp:
            with patch.dict(os.environ, {"WEXSPACE_PAE_OUTPUT_ROOT": temp}):
                result = pae006_fresh_motive_air_sensitivity(
                    json.dumps(payload, sort_keys=True)
                )
        matrix = result["matrix"]
        at_4_bar = {
            point["throat_diameter_mm"]: point
            for point in matrix
            if point["pressure_gauge_bar"] == 4.0
        }
        at_7_bar = {
            point["throat_diameter_mm"]: point
            for point in matrix
            if point["pressure_gauge_bar"] == 7.0
        }
        self.assertAlmostEqual(
            at_4_bar[1.8]["mass_flow_kg_s"] / at_4_bar[1.4]["mass_flow_kg_s"],
            (1.8 / 1.4) ** 2,
            places=8,
        )
        self.assertAlmostEqual(
            at_7_bar[1.6]["mass_flow_kg_s"] / at_4_bar[1.6]["mass_flow_kg_s"],
            (101325.0 + 700000.0) / (101325.0 + 400000.0),
            places=8,
        )
        self.assertTrue(
            all(
                point["backpressure_to_stagnation_ratio"]
                < point["critical_pressure_ratio"]
                for point in matrix
            )
        )

    def test_live_pae_topology_targets_same_three_agents_and_tools(self):
        root = build_live_pae006_root_agent()
        self.assertEqual([agent.name for agent in root.sub_agents], [
            "wexspace_governing_agent",
            "iew_engineering_specialist",
            "wexspace_verification_evidence_specialist",
        ])
        self.assertTrue(all(agent.model == ELIGIBLE_MODEL for agent in root.sub_agents))
        self.assertEqual([len(agent.tools) for agent in root.sub_agents], [1, 1, 1])

    def test_vertex_adk_evidence_gate_requires_all_agents_and_tools(self):
        payload = self.payload()
        input_json = json.dumps(payload, sort_keys=True)
        events = {
            "events": [
                {
                    "author": "wexspace_governing_agent",
                    "model_version": "gemini-3.7-flash",
                    "function_calls": [
                        {"name": "govern_pae006_study_request", "id": "g"}
                    ],
                    "function_responses": [
                        {"name": "govern_pae006_study_request", "id": "g"}
                    ],
                },
                {
                    "author": "iew_engineering_specialist",
                    "model_version": "gemini-3.7-flash",
                    "function_calls": [
                        {"name": "pae006_fresh_motive_air_sensitivity", "id": "e"}
                    ],
                    "function_responses": [
                        {"name": "pae006_fresh_motive_air_sensitivity", "id": "e"}
                    ],
                },
                {
                    "author": "wexspace_verification_evidence_specialist",
                    "model_version": "gemini-3.7-flash",
                    "function_calls": [
                        {"name": "independently_verify_pae006_study", "id": "v"}
                    ],
                    "function_responses": [
                        {"name": "independently_verify_pae006_study", "id": "v"}
                    ],
                },
            ]
        }
        with tempfile.TemporaryDirectory() as temp:
            environment = {
                "GOOGLE_GENAI_USE_VERTEXAI": "TRUE",
                "GOOGLE_CLOUD_PROJECT": "wexspace-agentic-2026",
                "GOOGLE_CLOUD_LOCATION": "global",
                "WEXSPACE_CLOUD_EXECUTION_SURFACE": "Google Cloud Shell",
                "WEXSPACE_PAE_OUTPUT_ROOT": temp,
            }
            with patch.dict(os.environ, environment, clear=True):
                pae006_fresh_motive_air_sensitivity(input_json)
                independently_verify_pae006_study(input_json)
                with patch(
                    "wexspace.adk_fleet._run_agent",
                    new=AsyncMock(return_value=events),
                ):
                    result = asyncio.run(run_live_pae006_payload(payload))
            self.assertTrue(result["passed"])
            self.assertEqual(result["workflow_state"], "AWAITING_HUMAN_REVIEW")
            self.assertEqual(result["google_stack_gate"]["status"], "PASS")
            self.assertTrue(result["artifact_manifest_valid"])
            self.assertFalse(result["release_performed"])
            evidence = result["execution_evidence"]
            self.assertEqual(evidence["actual_framework"], "Google ADK")
            self.assertEqual(evidence["actual_model"], "gemini-3.7-flash")
            self.assertTrue(evidence["provider_model_identity_verified"])
            self.assertEqual(evidence["backend"], "VERTEX_AI")
            self.assertEqual(evidence["cloud_execution_surface"], "Google Cloud Shell")


if __name__ == "__main__":
    unittest.main()
