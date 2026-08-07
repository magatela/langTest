# tests/test_consolidated_tools.py
import unittest
from unittest.mock import MagicMock, patch

from tools.jira_tool import (
    normalize_issue_key,
    clean_formatting_text,
    fetch_user_story_details,
    update_test_description,
    get_test_steps_from_case,
    delete_all_test_steps,
    add_test_steps,
    create_test_case,
    upload_execution_results,
    set_issue_link,
    create_bug_report,
)

class TestConsolidatedJiraTools(unittest.TestCase):
    def test_normalize_issue_key(self):
        self.assertEqual(normalize_issue_key("1234"), "PDNEU-1234")
        self.assertEqual(normalize_issue_key("PDNEU-1234"), "PDNEU-1234")

    def test_clean_formatting_text(self):
        text = "{code}Acción de prueba{code}"
        self.assertEqual(clean_formatting_text(text), "Acción de prueba")

    def test_fetch_user_story_details_offline_mock(self):
        mock_data = {
            "key": "PDNEU-555",
            "summary": "Título Mock",
            "description": "Criterios Mock",
        }
        res = fetch_user_story_details("PDNEU-555", mock_data=mock_data)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["key"], "PDNEU-555")
        self.assertEqual(res["summary"], "Título Mock")

    @patch("tools.jira_tool.get_jira_client")
    def test_update_test_description_mock(self, mock_get_jira):
        mock_jira = MagicMock()
        mock_jira._prefix = "PDNEU"
        mock_us_resp = MagicMock()
        mock_us_resp.ok = True
        mock_us_resp.json.return_value = {
            "fields": {
                "summary": "User Story de prueba",
                "description": "Descripción original",
                "labels": ["EXISTENTE"],
                "priority": {"id": "2"},
            }
        }
        mock_jira.get_issue_info.return_value = mock_us_resp

        mock_update_resp = MagicMock()
        mock_update_resp.ok = True
        mock_jira.update_issue.return_value = mock_update_resp
        mock_get_jira.return_value = mock_jira

        res = update_test_description("100", "200", "300", "36")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["test_case_key"], "PDNEU-200")

    @patch("tools.jira_tool.get_jira_client")
    def test_get_test_steps_from_case_mock(self, mock_get_jira):
        mock_jira = MagicMock()
        mock_jira._prefix = "PDNEU"
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "fields": {
                "customfield_12521": {
                    "steps": [
                        {
                            "fields": {
                                "Action": "Abrir vista",
                                "Data": "URL",
                                "Expected Result": "Vista visible",
                            }
                        }
                    ]
                }
            }
        }
        mock_jira.get_issue_info.return_value = mock_resp
        mock_get_jira.return_value = mock_jira

        res = get_test_steps_from_case("500")
        self.assertEqual(res["status"], "success")
        self.assertEqual(len(res["steps"]), 1)
        self.assertEqual(res["steps"][0]["step"], "Abrir vista")

if __name__ == "__main__":
    unittest.main()
