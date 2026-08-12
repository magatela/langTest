# modules/module_5_jira_assistant/jql_engine.py
"""
Motor de Búsqueda y Paginación JQL (Jira Query Language) para el Módulo 5.

Ejecuta consultas JQL complejas interactuando con la API REST de Jira, gestiona la
paginación masiva de resultados y los almacena directamente en la base de datos local SQLite.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

try:
    from tools.jira_tool import get_jira_client, normalize_issue_key, DEFAULT_PROJECT_KEY
    from modules.module_5_jira_assistant.storage import JiraLocalStorage
except ImportError:
    from tools.jira_tool import get_jira_client, normalize_issue_key, DEFAULT_PROJECT_KEY
    from storage import JiraLocalStorage

logger = logging.getLogger(__name__)


class JQLEngine:
    """
    Motor para construir, validar y ejecutar consultas JQL con paginación y caché local.
    """

    def __init__(self, project_key: str = DEFAULT_PROJECT_KEY):
        self.project_key = project_key

    def sanitize_jql(self, jql: str) -> str:
        """
        Sanea y valida una cadena de consulta JQL.

        Args:
            jql: Cadena JQL provista.

        Returns:
            str: Cadena JQL limpia.
        """
        clean_jql = jql.strip()
        if not clean_jql:
            clean_jql = f'project = "{self.project_key}" ORDER BY updated DESC'
        return clean_jql

    def build_jql(
        self,
        text_query: Optional[str] = None,
        issue_types: Optional[List[str]] = None,
        statuses: Optional[List[str]] = None,
        priorities: Optional[List[str]] = None,
        assignee: Optional[str] = None,
        project_key: Optional[str] = None,
    ) -> str:
        """
        Construye una consulta JQL estructurada a partir de parámetros individuales.

        Args:
            text_query: Texto a buscar en summary/description.
            issue_types: Lista de tipos de issue (ej. ['Bug', 'Story', 'Test']).
            statuses: Lista de estados (ej. ['Open', 'In Progress', 'Done']).
            priorities: Lista de prioridades.
            assignee: Nombre o email del asignado.
            project_key: Clave del proyecto.

        Returns:
            str: Consulta JQL resultante.
        """
        clauses = []
        proj = project_key or self.project_key
        if proj:
            clauses.append(f'project = "{proj}"')

        if issue_types:
            types_str = ", ".join(f'"{t}"' for t in issue_types)
            clauses.append(f'issuetype IN ({types_str})')

        if statuses:
            status_str = ", ".join(f'"{s}"' for s in statuses)
            clauses.append(f'status IN ({status_str})')

        if priorities:
            prio_str = ", ".join(f'"{p}"' for p in priorities)
            clauses.append(f'priority IN ({prio_str})')

        if assignee:
            clauses.append(f'assignee = "{assignee}"')

        if text_query:
            clauses.append(f'(summary ~ "{text_query}" OR description ~ "{text_query}")')

        jql_str = " AND ".join(clauses)
        jql_str += " ORDER BY updated DESC"
        return jql_str

    def execute_jql(
        self,
        jql: str,
        max_results: int = 100,
        page_size: int = 50,
        mock_issues: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Ejecuta una consulta JQL paginada contra la API REST de Jira.

        Args:
            jql: Consulta JQL.
            max_results: Cantidad máxima total de resultados a descargar.
            page_size: Tamaño de cada lote/página de descarga.
            mock_issues: Issues simulados opcionales para pruebas offline o unitarias.

        Returns:
            List[Dict[str, Any]]: Lista de objetos JSON de issues descargados.
        """
        if mock_issues is not None:
            return mock_issues[:max_results]

        sanitized_jql = self.sanitize_jql(jql)
        all_issues: List[Dict[str, Any]] = []

        try:
            jira = get_jira_client()
            start_at = 0
            
            while len(all_issues) < max_results:
                current_max = min(page_size, max_results - len(all_issues))
                response = jira.jql_requests(sanitized_jql, max_results=current_max, start_at=start_at)

                if response.status_code != 200:
                    logger.warning("Respuesta HTTP %s al ejecutar JQL '%s'", response.status_code, sanitized_jql)
                    break

                data = response.json()
                issues = data.get("issues", [])
                if not issues:
                    break

                all_issues.extend(issues)
                total_in_jira = data.get("total", len(all_issues))
                start_at += len(issues)

                if start_at >= total_in_jira or len(issues) < current_max:
                    break

        except Exception as e:
            logger.error("Excepción durante ejecución de JQL: %s", str(e))

        return all_issues

    def fetch_and_cache(
        self,
        jql: str,
        storage: JiraLocalStorage,
        max_results: int = 200,
        mock_issues: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta una consulta JQL y guarda los resultados en el almacenamiento local SQLite.

        Args:
            jql: Consulta JQL.
            storage: Instancia de JiraLocalStorage.
            max_results: Máximo de issues a descargar e indexar.
            mock_issues: Datos simulados para modo offline/test.

        Returns:
            Dict[str, Any]: Resumen de la operación (status, total_fetched, stored_count, jql).
        """
        clean_jql = self.sanitize_jql(jql)
        fetched_issues = self.execute_jql(clean_jql, max_results=max_results, mock_issues=mock_issues)

        stored_count = storage.upsert_issues(fetched_issues)

        return {
            "status": "success",
            "jql": clean_jql,
            "total_fetched": len(fetched_issues),
            "stored_count": stored_count,
        }
