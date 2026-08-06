# tests/test_jira_tools.py
import unittest
from unittest.mock import MagicMock, patch
from tools.jira.base_api import RestAPIClient
from tools.jira.jira_api import JiraAPI
from tools.jira.xray_api import XrayAPI
from tools.jira_tool import fetch_user_story_details

class TestJiraTools(unittest.TestCase):
    def test_rest_api_client_initialization(self):
        client = RestAPIClient("https://jira.test.com/", "test_user", "test_pass")
        self.assertEqual(client.base_url, "https://jira.test.com/")
        self.assertEqual(client.auth.username, "test_user")

    @patch("requests.Session.request")
    def test_jira_api_get_issue(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "key": "PDNEU-100",
            "fields": {"summary": "Test US", "description": "AC 1"}
        }
        mock_request.return_value = mock_resp

        jira = JiraAPI("https://jira.test.com/", "PDNEU", "user", "pass")
        resp = jira.get_issue_info("100")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["key"], "PDNEU-100")

    def test_fetch_user_story_details_mock(self):
        mock_data = {
            "key": "PDNEU-999",
            "summary": "Mocked Story Title",
            "description": "Mocked ACs"
        }
        result = fetch_user_story_details("PDNEU-999", mock_data=mock_data)
        self.assertEqual(result["key"], "PDNEU-999")
        self.assertEqual(result["summary"], "Mocked Story Title")

if __name__ == '__main__':
    unittest.main()
