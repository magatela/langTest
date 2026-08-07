# tests/test_module_1.py
import unittest
from unittest.mock import MagicMock
from modules.module_1_test_writer.agent import (
    run_test_writer_agent,
    load_prompt,
    analyze_and_recommend_jira_references
)

class TestModule1Agent(unittest.TestCase):
    def test_prompts_loading(self):
        writer_prompt = load_prompt("testCaseWriter.md")
        reviewer_prompt = load_prompt("testCaseReviewer.md")
        nav_prompt = load_prompt("navigation.md")

        self.assertGreater(len(writer_prompt), 0)
        self.assertGreater(len(reviewer_prompt), 0)
        self.assertGreater(len(nav_prompt), 0)

    def test_analyze_and_recommend_jira_references_mock_llm(self):
        mock_llm = MagicMock()
        mock_resp = MagicMock()
        mock_resp.content = '{"references": [{"key": "PDNEU-4567", "reason": "Especificación del cuadro modal"}]}'
        mock_llm.invoke.return_value = mock_resp

        refs = analyze_and_recommend_jira_references(
            user_story_text="Texto con PDNEU-4567",
            exclude_key="PDNEU-100",
            llm=mock_llm
        )

        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]["key"], "PDNEU-4567")
        self.assertEqual(refs[0]["reason"], "Especificación del cuadro modal")

    def test_agent_execution_mock(self):
        mock_resp = "```json\n[{\"step\": 1, \"action\": \"Abrir formulario\"}]\n```"
        captured_nodes = []

        def on_step(node, content):
            captured_nodes.append(node)

        mock_recs = [{"key": "PDNEU-888", "reason": "Definición de interfaz"}]

        result = run_test_writer_agent(
            jira_issue_key="PDNEU-TEST",
            target_view="TestView",
            user_story_text="User Story de Prueba con referencia a PDNEU-888",
            mock_recommendations=mock_recs,
            on_step_callback=on_step,
            mock_response=mock_resp
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["solution"], mock_resp)
        self.assertIn("writer", captured_nodes)
        self.assertIn("reviewer", captured_nodes)
        self.assertEqual(result["recommended_references"][0]["key"], "PDNEU-888")

    def test_agent_execution_with_selected_references(self):
        mock_resp = "```json\n[{\"step\": 1, \"action\": \"Paso con contexto\"}]\n```"
        result = run_test_writer_agent(
            jira_issue_key="PDNEU-MAIN",
            target_view="TestView",
            user_story_text="Descripción principal vinculada a PDNEU-777",
            selected_referenced_keys=["PDNEU-777"],
            mock_response=mock_resp
        )

        self.assertTrue(result["success"])
        self.assertIn("PDNEU-777", result["selected_references"])
        self.assertIn("REFERENCED JIRA ISSUE DETAILS (PDNEU-777)", result["final_user_story_text"])

if __name__ == '__main__':
    unittest.main()
