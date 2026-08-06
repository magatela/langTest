# tests/test_module_1.py
import unittest
from modules.module_1_test_writer.agent import run_test_writer_agent, load_prompt

class TestModule1Agent(unittest.TestCase):
    def test_prompts_loading(self):
        writer_prompt = load_prompt("testCaseWriter.md")
        reviewer_prompt = load_prompt("testCaseReviewer.md")
        nav_prompt = load_prompt("navigation.md")

        self.assertGreater(len(writer_prompt), 0)
        self.assertGreater(len(reviewer_prompt), 0)
        self.assertGreater(len(nav_prompt), 0)

    def test_agent_execution_mock(self):
        mock_resp = "```json\n[{\"step\": 1, \"action\": \"Abrir formulario\"}]\n```"
        captured_nodes = []

        def on_step(node, content):
            captured_nodes.append(node)

        result = run_test_writer_agent(
            jira_issue_key="PDNEU-TEST",
            target_view="TestView",
            user_story_text="User Story de Prueba",
            on_step_callback=on_step,
            mock_response=mock_resp
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["solution"], mock_resp)
        self.assertIn("writer", captured_nodes)
        self.assertIn("reviewer", captured_nodes)

if __name__ == '__main__':
    unittest.main()
