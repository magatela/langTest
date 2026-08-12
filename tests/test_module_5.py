# tests/test_module_5.py
"""
Pruebas unitarias para el Módulo 5 (Asistente Jira Chat, JQL y Almacenamiento SQLite Local).
Compatible con unittest y pytest.
"""

import unittest
from modules.module_5_jira_assistant.storage import JiraLocalStorage
from modules.module_5_jira_assistant.jql_engine import JQLEngine
from modules.module_5_jira_assistant.chart_formatter import ChartFormatter
from modules.module_5_jira_assistant.agent import JiraAssistantAgent, run_jira_assistant_query


class TestModule5JiraAssistant(unittest.TestCase):

    def setUp(self):
        """Inicializa una base de datos en memoria para cada prueba."""
        self.storage = JiraLocalStorage(":memory:")
        self.mock_jira_issues = [
            {
                "key": "PDNEU-101",
                "fields": {
                    "summary": "Error al iniciar sesión con credenciales inválidas",
                    "description": "El usuario recibe un error HTTP 500 en lugar de 401",
                    "status": {"name": "Open"},
                    "issuetype": {"name": "Bug"},
                    "priority": {"name": "High"},
                    "assignee": {"displayName": "Juan Pérez"},
                    "project": {"key": "PDNEU"},
                    "created": "2026-08-01T10:00:00Z",
                    "updated": "2026-08-02T11:00:00Z",
                }
            },
            {
                "key": "PDNEU-102",
                "fields": {
                    "summary": "Como usuario quiero exportar reportes en PDF",
                    "description": "Requisito para descarga de informes en formato PDF",
                    "status": {"name": "In Progress"},
                    "issuetype": {"name": "Story"},
                    "priority": {"name": "Medium"},
                    "assignee": {"displayName": "Maria Gómez"},
                    "project": {"key": "PDNEU"},
                    "created": "2026-08-03T10:00:00Z",
                    "updated": "2026-08-04T11:00:00Z",
                }
            },
            {
                "key": "PDNEU-103",
                "fields": {
                    "summary": "Verificar la descarga de PDF en navegadores Chrome y Firefox",
                    "description": "Paso 1: Abrir vista. Paso 2: Clic en Exportar",
                    "status": {"name": "Pass"},
                    "issuetype": {"name": "Test"},
                    "priority": {"name": "Low"},
                    "assignee": {"displayName": "Carlos Ruiz"},
                    "project": {"key": "PDNEU"},
                    "created": "2026-08-05T10:00:00Z",
                    "updated": "2026-08-05T12:00:00Z",
                }
            }
        ]

    def tearDown(self):
        """Cierra la conexión SQLite en memoria."""
        self.storage.close()

    def test_storage_upsert_and_query(self):
        """Prueba que el almacenamiento local inserta e indexa issues correctamente."""
        inserted = self.storage.upsert_issues(self.mock_jira_issues)
        self.assertEqual(inserted, 3)

        issue = self.storage.get_issue_by_key("PDNEU-101")
        self.assertIsNotNone(issue)
        self.assertEqual(issue["summary"], "Error al iniciar sesión con credenciales inválidas")
        self.assertEqual(issue["issue_type"], "Bug")
        self.assertEqual(issue["priority"], "High")

        bugs = self.storage.query_issues("issue_type = ?", ("Bug",))
        self.assertEqual(len(bugs), 1)
        self.assertEqual(bugs[0]["key"], "PDNEU-101")

    def test_storage_summary_stats(self):
        """Prueba el cálculo de agregaciones estadísticas de la DB local."""
        self.storage.upsert_issues(self.mock_jira_issues)
        stats = self.storage.get_summary_stats()

        self.assertEqual(stats["total_issues"], 3)
        self.assertEqual(stats["by_type"].get("Bug"), 1)
        self.assertEqual(stats["by_type"].get("Story"), 1)
        self.assertEqual(stats["by_type"].get("Test"), 1)
        self.assertEqual(stats["by_priority"].get("High"), 1)

    def test_storage_text_search(self):
        """Prueba la búsqueda por coincidencia de texto en la base local."""
        self.storage.upsert_issues(self.mock_jira_issues)
        results = self.storage.search_text("exportar")
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["key"], "PDNEU-102")

    def test_jql_engine_build_query(self):
        """Prueba la construcción estructurada de cadenas JQL."""
        engine = JQLEngine(project_key="PDNEU")
        jql = engine.build_jql(
            text_query="login",
            issue_types=["Bug", "Story"],
            statuses=["Open"]
        )
        self.assertIn('project = "PDNEU"', jql)
        self.assertIn('issuetype IN ("Bug", "Story")', jql)
        self.assertIn('status IN ("Open")', jql)
        self.assertIn('(summary ~ "login" OR description ~ "login")', jql)

    def test_jql_engine_fetch_and_cache(self):
        """Prueba el volcado directo de JQL al almacenamiento local."""
        engine = JQLEngine(project_key="PDNEU")
        res = engine.fetch_and_cache(
            jql='project = "PDNEU"',
            storage=self.storage,
            mock_issues=self.mock_jira_issues
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["stored_count"], 3)
        self.assertEqual(self.storage.count_issues(), 3)

    def test_chart_formatter(self):
        """Prueba la generación de tablas Markdown y gráficos Mermaid."""
        table_md = ChartFormatter.format_issues_table(self.mock_jira_issues, title="Tabla de Test")
        self.assertIn("| Schlüssel | Typ | Zusammenfassung |", table_md)
        self.assertIn("`PDNEU-101`", table_md)

        pie_md = ChartFormatter.format_mermaid_pie_chart({"Open": 5, "Closed": 10})
        self.assertIn("```mermaid", pie_md)
        self.assertIn("pie title", pie_md)
        self.assertIn('"Open" : 5', pie_md)

        bar_md = ChartFormatter.format_mermaid_bar_chart({"High": 3, "Low": 8})
        self.assertIn("```mermaid", bar_md)
        self.assertIn("xychart-beta", bar_md)

        card_md = ChartFormatter.format_summary_card({"total_issues": 15, "by_type": {"Bug": 5}})
        self.assertIn("Gesamtzahl indexierter Issues:** `15`", card_md)

    def test_jira_assistant_agent_execution(self):
        """Prueba la ejecución completa del agente conversacional del Módulo 5."""
        agent = JiraAssistantAgent(db_path=":memory:")
        res = agent.ask("Muéstrame los bugs reportados", mock_issues=self.mock_jira_issues)

        self.assertTrue(res["success"])
        self.assertIn("user_query", res)
        self.assertIn("jql_query", res)
        self.assertIn("answer", res)
        self.assertGreater(len(res["answer"]), 0)

    def test_jira_assistant_single_issue_lookup(self):
        """Prueba la detección y consulta directa de un solo issue mediante herramientas de Jira."""
        res = run_jira_assistant_query("Dame información de la historia PDNEU-1234", storage=self.storage)
        self.assertTrue(res["success"])
        self.assertTrue(res["is_single_issue"])
        self.assertIn("PDNEU-1234", res["answer"])


if __name__ == "__main__":
    unittest.main()
