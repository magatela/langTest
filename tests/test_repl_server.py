# tests/test_repl_server.py
import unittest
from pathlib import Path
from config.config_loader import get_playwright_config, get_jira_credentials
from modules.module_2_browser_repl.ts_repl_bridge import TSPlaywrightREPLBridge

class TestReplServerIntegration(unittest.TestCase):
    def test_get_playwright_config_defaults(self):
        pw_config = get_playwright_config()
        self.assertIn("use_custom_chrome_path", pw_config)
        self.assertIn("chrome_path", pw_config)
        self.assertIn("headless", pw_config)
        self.assertIn("results_dir", pw_config)
        self.assertIsInstance(pw_config["use_custom_chrome_path"], bool)

    def test_get_jira_credentials_structure(self):
        jira_config = get_jira_credentials()
        self.assertIn("base_url", jira_config)
        self.assertIn("prefix", jira_config)
        self.assertIn("user", jira_config)
        self.assertIn("password", jira_config)

    def test_ts_repl_bridge_initialization(self):
        bridge = TSPlaywrightREPLBridge()
        self.assertTrue(bridge.server_dir.exists())
        self.assertTrue((bridge.server_dir / "repl" / "repl.ts").exists())

if __name__ == '__main__':
    unittest.main()
