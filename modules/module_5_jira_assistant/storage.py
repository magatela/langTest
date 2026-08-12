# modules/module_5_jira_assistant/storage.py
"""
Base de Datos Local y Motor de Caché SQLite para el Módulo 5.

Permite indexar, guardar y agregar masivamente datos de Jira (issues, bugs, user stories,
test plans, ejecuciones Xray y comentarios) para realizar consultas locales y agregaciones
estadísticas rápidamente, previniendo el desbordamiento de la ventana de contexto del LLM.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

DEFAULT_DB_DIR = Path(__file__).resolve().parent / "storage"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "jira_cache.db"


class JiraLocalStorage:
    """
    Gestor de base de datos SQLite local para almacenamiento estructurado de datos de Jira.
    """

    def __init__(self, db_path: Union[str, Path] = DEFAULT_DB_PATH):
        """
        Inicializa la conexión a la base de datos local SQLite.

        Args:
            db_path: Ruta del archivo SQLite o ':memory:' para pruebas en memoria.
        """
        if str(db_path) != ":memory:":
            path_obj = Path(db_path)
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            self.db_path = str(path_obj)
        else:
            self.db_path = ":memory:"

        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        """Crea las tablas necesarias si no existen."""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS issues (
                    key TEXT PRIMARY KEY,
                    summary TEXT,
                    description TEXT,
                    status TEXT,
                    issue_type TEXT,
                    priority TEXT,
                    assignee TEXT,
                    created TEXT,
                    updated TEXT,
                    project_key TEXT,
                    raw_json TEXT
                )
            """)

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS test_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_key TEXT,
                    test_key TEXT,
                    status TEXT,
                    comment TEXT,
                    raw_json TEXT
                )
            """)

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    issue_key TEXT,
                    author TEXT,
                    body TEXT,
                    created TEXT
                )
            """)

            # Índices para optimizar consultas rápidas
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_issues_type ON issues(issue_type)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_issues_status ON issues(status)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_issues_priority ON issues(priority)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_test_runs_exec ON test_runs(execution_key)")

    def upsert_issue(self, raw_issue: Dict[str, Any]) -> str:
        """
        Inserta o actualiza un issue individual en la base de datos local.

        Args:
            raw_issue: Diccionario con la estructura JSON retornada por la API REST de Jira.

        Returns:
            str: Clave del issue procesado (ej. 'PDNEU-123').
        """
        key = raw_issue.get("key", "")
        if not key:
            return ""

        fields = raw_issue.get("fields", {})
        summary = fields.get("summary", "")
        description = fields.get("description", "") or ""
        
        status_field = fields.get("status")
        status = status_field.get("name", "") if isinstance(status_field, dict) else str(status_field or "")

        issuetype_field = fields.get("issuetype")
        issue_type = issuetype_field.get("name", "") if isinstance(issuetype_field, dict) else str(issuetype_field or "")

        priority_field = fields.get("priority")
        priority = priority_field.get("name", "") if isinstance(priority_field, dict) else str(priority_field or "Medium")

        assignee_field = fields.get("assignee")
        assignee = assignee_field.get("displayName", "") if isinstance(assignee_field, dict) else str(assignee_field or "Unassigned")

        project_field = fields.get("project")
        project_key = project_field.get("key", "") if isinstance(project_field, dict) else str(project_field or "")

        created = fields.get("created", "")
        updated = fields.get("updated", "")

        raw_json_str = json.dumps(raw_issue, ensure_ascii=False)

        with self.conn:
            self.conn.execute(
                """
                INSERT INTO issues (key, summary, description, status, issue_type, priority, assignee, created, updated, project_key, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    summary=excluded.summary,
                    description=excluded.description,
                    status=excluded.status,
                    issue_type=excluded.issue_type,
                    priority=excluded.priority,
                    assignee=excluded.assignee,
                    created=excluded.created,
                    updated=excluded.updated,
                    project_key=excluded.project_key,
                    raw_json=excluded.raw_json
                """,
                (key, summary, description, status, issue_type, priority, assignee, created, updated, project_key, raw_json_str)
            )

        # Procesar comentarios incorporados si existen
        comment_field = fields.get("comment", {})
        comments_list = comment_field.get("comments", []) if isinstance(comment_field, dict) else []
        if comments_list:
            self.upsert_comments(key, comments_list)

        return key

    def upsert_issues(self, issues_list: List[Dict[str, Any]]) -> int:
        """
        Inserta o actualiza un conjunto masivo de issues.

        Args:
            issues_list: Lista de diccionarios JSON de issues de Jira.

        Returns:
            int: Cantidad de issues insertados/actualizados.
        """
        count = 0
        for issue in issues_list:
            if self.upsert_issue(issue):
                count += 1
        return count

    def upsert_comments(self, issue_key: str, comments_list: List[Dict[str, Any]]) -> int:
        """Inserta comentarios de un issue en la base de datos local."""
        with self.conn:
            self.conn.execute("DELETE FROM comments WHERE issue_key = ?", (issue_key,))
            for item in comments_list:
                author_field = item.get("author", {})
                author = author_field.get("displayName", "") if isinstance(author_field, dict) else str(author_field or "")
                body = item.get("body", "")
                created = item.get("created", "")
                self.conn.execute(
                    "INSERT INTO comments (issue_key, author, body, created) VALUES (?, ?, ?, ?)",
                    (issue_key, author, body, created)
                )
        return len(comments_list)

    def upsert_test_runs(self, execution_key: str, test_runs_list: List[Dict[str, Any]]) -> int:
        """Inserta o actualiza registros de ejecuciones de test (Xray Test Runs)."""
        with self.conn:
            self.conn.execute("DELETE FROM test_runs WHERE execution_key = ?", (execution_key,))
            for run in test_runs_list:
                test_key = run.get("testKey", "") or run.get("key", "")
                status = run.get("status", "TODO")
                comment = run.get("comment", "")
                raw_json_str = json.dumps(run, ensure_ascii=False)
                self.conn.execute(
                    "INSERT INTO test_runs (execution_key, test_key, status, comment, raw_json) VALUES (?, ?, ?, ?, ?)",
                    (execution_key, test_key, status, comment, raw_json_str)
                )
        return len(test_runs_list)

    def get_issue_by_key(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """Obtiene un issue específico almacenado localmente."""
        cursor = self.conn.execute("SELECT * FROM issues WHERE key = ?", (issue_key,))
        row = cursor.fetchone()
        if not row:
            return None
        res = dict(row)
        res["raw_json"] = json.loads(res["raw_json"]) if res["raw_json"] else {}
        return res

    def query_issues(
        self,
        where_clause: str = "",
        params: Tuple[Any, ...] = (),
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Realiza una consulta a los issues almacenados localmente.

        Args:
            where_clause: Cláusula WHERE opcional de SQL (ej. "issue_type = ? AND status = ?").
            params: Parámetros para sustituir en el WHERE.
            limit: Límite máximo de resultados.
            offset: Desplazamiento para paginación.

        Returns:
            List[Dict[str, Any]]: Lista de registros de issues.
        """
        sql = "SELECT key, summary, status, issue_type, priority, assignee, created, updated FROM issues"
        if where_clause:
            sql += f" WHERE {where_clause}"
        sql += " ORDER BY updated DESC LIMIT ? OFFSET ?"

        query_params = list(params) + [limit, offset]
        cursor = self.conn.execute(sql, query_params)
        return [dict(row) for row in cursor.fetchall()]

    def search_text(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Búsqueda por coincidencia de texto en summary o description.

        Args:
            keyword: Término de búsqueda.
            limit: Máximo de resultados.

        Returns:
            List[Dict[str, Any]]: Matching issues.
        """
        pattern = f"%{keyword}%"
        cursor = self.conn.execute(
            """
            SELECT key, summary, status, issue_type, priority, assignee
            FROM issues
            WHERE summary LIKE ? OR description LIKE ?
            LIMIT ?
            """,
            (pattern, pattern, limit)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Calcula agregaciones y estadísticas de resumen de la base de datos local.

        Returns:
            Dict[str, Any]: Estadísticas por issue_type, status, priority, etc.
        """
        stats: Dict[str, Any] = {}

        # Total issues
        cursor = self.conn.execute("SELECT COUNT(*) as total FROM issues")
        stats["total_issues"] = cursor.fetchone()["total"]

        # Conteo por tipo de issue
        cursor = self.conn.execute("SELECT issue_type, COUNT(*) as count FROM issues GROUP BY issue_type")
        stats["by_type"] = {row["issue_type"] or "Unknown": row["count"] for row in cursor.fetchall()}

        # Conteo por estado
        cursor = self.conn.execute("SELECT status, COUNT(*) as count FROM issues GROUP BY status")
        stats["by_status"] = {row["status"] or "Unknown": row["count"] for row in cursor.fetchall()}

        # Conteo por prioridad
        cursor = self.conn.execute("SELECT priority, COUNT(*) as count FROM issues GROUP BY priority")
        stats["by_priority"] = {row["priority"] or "Unknown": row["count"] for row in cursor.fetchall()}

        # Conteo de Bugs por estado
        cursor = self.conn.execute(
            "SELECT status, COUNT(*) as count FROM issues WHERE LOWER(issue_type) = 'bug' GROUP BY status"
        )
        stats["bugs_by_status"] = {row["status"] or "Unknown": row["count"] for row in cursor.fetchall()}

        # Conteo de ejecuciones de test por estado
        cursor = self.conn.execute("SELECT status, COUNT(*) as count FROM test_runs GROUP BY status")
        stats["test_runs_by_status"] = {row["status"] or "Unknown": row["count"] for row in cursor.fetchall()}

        return stats

    def count_issues(self, where_clause: str = "", params: Tuple[Any, ...] = ()) -> int:
        """Devuelve la cantidad total de registros que coinciden con el filtro."""
        sql = "SELECT COUNT(*) as count FROM issues"
        if where_clause:
            sql += f" WHERE {where_clause}"
        cursor = self.conn.execute(sql, params)
        return cursor.fetchone()["count"]

    def clear_cache(self) -> None:
        """Limpia todo el contenido del caché local."""
        with self.conn:
            self.conn.execute("DELETE FROM issues")
            self.conn.execute("DELETE FROM test_runs")
            self.conn.execute("DELETE FROM comments")

    def close(self) -> None:
        """Cierra la conexión a SQLite."""
        if self.conn:
            self.conn.close()
