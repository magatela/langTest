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
    list_available_reference_poms,
    read_reference_poms,
    clean_typescript_code,
    POMGeneratorAgent,
    run_pom_generator_agent
)

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
        (self.pom_dir / "BerichtMainPage.ts").write_text(
            "export class BerichtMainPage { constructor(public page: any) {} }",
            encoding="utf-8"
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_clean_typescript_code(self):
        raw_code = """```typescript
export class TestPage {
    readonly page: Page;
}
```"""
        cleaned = clean_typescript_code(raw_code)
        self.assertTrue(cleaned.startswith("export class TestPage"))
        self.assertFalse("```" in cleaned)

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
        self.assertIn("submit", prompt)

    def test_build_pom_update_prompt(self):
        prompt = build_pom_update_prompt(
            existing_pom_code="export class OldPage {}",
            aria_snapshot="- textbox 'Username'",
            user_instructions="Agregar campo username"
        )
        self.assertIn("OldPage", prompt)
        self.assertIn("textbox 'Username'", prompt)
        self.assertIn("username", prompt)

    @patch("modules.module_4_pom_generator.agent.get_pom_dir")
    def test_list_and_read_reference_poms(self, mock_get_pom_dir):
        mock_get_pom_dir.return_value = self.pom_dir

        poms = list_available_reference_poms()
        self.assertIn("NavigationPage.ts", poms)
        self.assertIn("BerichtMainPage.ts", poms)

        combined = read_reference_poms(["NavigationPage.ts"])
        self.assertIn("export class NavigationPage", combined)

    @patch("modules.module_4_pom_generator.agent.get_pom_dir")
    def test_run_pom_generator_create_mock(self, mock_get_pom_dir):
        mock_get_pom_dir.return_value = self.pom_dir

        mock_response = """```typescript
import { Page, Locator } from '@playwright/test';

export class CustomFormPage {
    readonly page: Page;
    constructor(page: Page) {
        this.page = page;
    }
}
```"""

        result = run_pom_generator_agent(
            mode="create",
            target_name="CustomFormPage.ts",
            reference_files=["NavigationPage.ts"],
            aria_snapshot="- button 'Submit'",
            mock_response=mock_response
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["filename"], "CustomFormPage.ts")
        self.assertIn("export class CustomFormPage", result["code"])
        self.assertTrue((self.pom_dir / "CustomFormPage.ts").exists())

    @patch("modules.module_4_pom_generator.agent.get_pom_dir")
    def test_run_pom_generator_update_mock(self, mock_get_pom_dir):
        mock_get_pom_dir.return_value = self.pom_dir

        # Crear archivo previo a actualizar
        (self.pom_dir / "EditPage.ts").write_text("export class EditPage {}", encoding="utf-8")

        mock_response = """```typescript
export class EditPage {
    readonly newField: Locator;
}
```"""

        result = run_pom_generator_agent(
            mode="update",
            target_name="EditPage.ts",
            user_instructions="Agregar newField",
            mock_response=mock_response
        )

        self.assertEqual(result["status"], "success")
        self.assertIn("readonly newField: Locator;", result["code"])

if __name__ == "__main__":
    unittest.main()
