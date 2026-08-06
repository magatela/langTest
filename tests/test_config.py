# tests/test_config.py
import unittest
from config.config_loader import get_jira_credentials, get_llm_config

class TestConfigLoader(unittest.TestCase):
    def test_jira_credentials_fallback(self):
        jira_cfg = get_jira_credentials()
        self.assertIsInstance(jira_cfg, dict)
        self.assertIn("base_url", jira_cfg)
        self.assertIn("prefix", jira_cfg)
        self.assertIn("user", jira_cfg)
        self.assertIn("password", jira_cfg)

    def test_llm_config_fallback(self):
        llm_cfg = get_llm_config()
        self.assertIsInstance(llm_cfg, dict)
        self.assertIn("apiBase", llm_cfg)
        self.assertIn("apiKey", llm_cfg)
        self.assertIn("models", llm_cfg)
        self.assertGreaterEqual(len(llm_cfg["models"]), 1)

if __name__ == '__main__':
    unittest.main()
