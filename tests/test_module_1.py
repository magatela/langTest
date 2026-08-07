# tests/test_module_1.py
import unittest
from modules.module_1_test_writer.agent import (
    run_test_writer_agent,
    load_prompt,
    extract_jira_issue_references
)

class TestModule1Agent(unittest.TestCase):
    def test_prompts_loading(self):
        writer_prompt = load_prompt("testCaseWriter.md")
        reviewer_prompt = load_prompt("testCaseReviewer.md")
        nav_prompt = load_prompt("navigation.md")

        self.assertGreater(len(writer_prompt), 0)
        self.assertGreater(len(reviewer_prompt), 0)
        self.assertGreater(len(nav_prompt), 0)

    def test_extract_jira_issue_references(self):
        text = "Verweise: # PDNEU-1234 und auch PDNEU-5678 así como QA-99. Se ignora la propia PDNEU-100."
        refs = extract_jira_issue_references(text, exclude_key="PDNEU-100")
        self.assertIn("PDNEU-1234", refs)
        self.assertIn("PDNEU-5678", refs)
        self.assertIn("QA-99", refs)
        self.assertNotIn("PDNEU-100", refs)

    def test_agent_execution_mock(self):
        mock_resp = "```json\n[{\"step\": 1, \"action\": \"Abrir formulario\"}]\n```"
        captured_nodes = []

        def on_step(node, content):
            captured_nodes.append(node)

        result = run_test_writer_agent(
            jira_issue_key="PDNEU-TEST",
            target_view="TestView",
            user_story_text="User Story de Prueba con referencia a PDNEU-888",
            on_step_callback=on_step,
            mock_response=mock_resp
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["solution"], mock_resp)
        self.assertIn("writer", captured_nodes)
        self.assertIn("reviewer", captured_nodes)
        self.assertIn("PDNEU-888", result["detected_references"])

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
