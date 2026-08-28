# tests/test_module_4.py
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

from modules.module_4_pom_generator.prompts import (
    build_pom_generation_prompt,
    build_pom_update_prompt,
    POM_GENERATOR_SYSTEM_PROMPT,
    POM_UPDATER_SYSTEM_PROMPT
)
from modules.module_4_pom_generator.agent import (
    get_pom_dir,
    read_workspace_file,
    write_workspace_file,
    create_pom_agent_graph,
    stream_pom_agent_turn
)
from modules.module_4_pom_generator.ui import POMGeneratorTUI

class TestModule4POMGenerator(unittest.TestCase):

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.pom_dir = self.temp_dir / "POM"
        self.pom_dir.mkdir(parents=True, exist_ok=True)

        # Crear archivos POM de prueba
        (self.pom_dir / "NavigationPage.ts").write_text(
            "export class NavigationPage { constructor(public page: any) {} }",
            encoding="utf-8"
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_build_pom_generation_prompt(self):
        prompt = build_pom_generation_prompt(
            target_class_name="LoginPage",
            reference_poms_code="export class RefPage {}",
            aria_snapshot="- button 'Login'",
            user_instructions="Incluir método submit"
        )
        self.assertIn("LoginPage", prompt)
        self.assertIn("RefPage", prompt)
        self.assertIn("button 'Login'", prompt)

    def test_build_pom_update_prompt(self):
        prompt = build_pom_update_prompt(
            existing_pom_code="export class OldPage {}",
            aria_snapshot="- textbox 'Username'",
            user_instructions="Agregar campo username"
        )
        self.assertIn("OldPage", prompt)
        self.assertIn("textbox 'Username'", prompt)

    @patch("modules.module_4_pom_generator.agent.ROOT_DIR")
    def test_workspace_file_tools(self, mock_root_dir):
        mock_root_dir.__truediv__.return_value = self.temp_dir
        
        test_file = self.temp_dir / "test.txt"
        test_file.write_text("Hello World", encoding="utf-8")

        res_read = read_workspace_file.invoke({"filepath": str(test_file)})
        self.assertEqual(res_read, "Hello World")

        res_write = write_workspace_file.invoke({
            "filepath": str(self.temp_dir / "out.ts"),
            "content": "export class OutPage {}"
        })
        self.assertIn("Erfolg", res_write)

    def test_create_pom_agent_graph(self):
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm
        graph = create_pom_agent_graph(llm_instance=mock_llm)
        self.assertIsNotNone(graph)

    def test_tui_app_instantiation(self):
        app = POMGeneratorTUI()
        self.assertEqual(app.TITLE, "POM Generator Agent - ReAct TUI")

if __name__ == "__main__":
    unittest.main()
