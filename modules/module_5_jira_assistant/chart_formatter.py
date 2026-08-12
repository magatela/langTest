# modules/module_5_jira_assistant/chart_formatter.py
"""
Formateador Gráfico y Visual (Charts, Mermaid y Tablas Markdown) para el Módulo 5.

Transforma estadísticas agregadas y listados de datos de Jira traídos del almacenamiento
local en gráficos de Mermaid, tablas comparativas y tarjetas ejecutivas para enriquecer
la interfaz de Chat del agente.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class ChartFormatter:
    """
    Clase utilitaria para formatear agregaciones de datos en vistas de Chat y gráficos Markdown/Mermaid.
    """

    @staticmethod
    def format_issues_table(
        issues: List[Dict[str, Any]],
        title: str = "Lista de Issues",
        max_rows: int = 15
    ) -> str:
        """
        Genera una tabla Markdown limpia a partir de una lista de issues.

        Args:
            issues: Lista de diccionarios de issues.
            title: Título de la tabla.
            max_rows: Límite máximo de filas mostradas en la tabla.

        Returns:
            str: Tabla en formato GitHub Markdown.
        """
        if not issues:
            return f"### {title}\n*No se encontraron issues para mostrar.*"

        lines = [
            f"### {title} (Mostrando {min(len(issues), max_rows)} de {len(issues)})",
            "",
            "| Key | Tipo | Resumen | Estado | Prioridad | Asignado |",
            "|---|---|---|---|---|---|",
        ]

        for issue in issues[:max_rows]:
            key = issue.get("key", "")
            itype = issue.get("issue_type", "Unknown")
            summary = (issue.get("summary", "") or "").replace("|", "\\|")
            if len(summary) > 50:
                summary = summary[:47] + "..."
            status = issue.get("status", "Unknown")
            prio = issue.get("priority", "Medium")
            assignee = issue.get("assignee", "Unassigned")
            lines.append(f"| `{key}` | {itype} | {summary} | **{status}** | {prio} | {assignee} |")

        return "\n".join(lines)

    @staticmethod
    def format_mermaid_pie_chart(
        data_dict: Dict[str, int],
        title: str = "Distribución de Issues por Estado"
    ) -> str:
        """
        Genera un diagrama de tarta Mermaid (Pie Chart).

        Args:
            data_dict: Diccionario de pares (Categoría: Cantidad).
            title: Título del gráfico.

        Returns:
            str: Bloque de código Mermaid pie chart.
        """
        if not data_dict:
            return ""

        lines = [
            "```mermaid",
            f'pie title {title}',
        ]
        for key, val in data_dict.items():
            clean_key = str(key).replace('"', "'")
            lines.append(f'    "{clean_key}" : {val}')
        lines.append("```")

        return "\n".join(lines)

    @staticmethod
    def format_mermaid_bar_chart(
        data_dict: Dict[str, int],
        title: str = "Métricas por Categoria",
        x_label: str = "Categorías",
        y_label: str = "Cantidad"
    ) -> str:
        """
        Genera un diagrama de barras en Mermaid usando la sintaxis xychart-beta.

        Args:
            data_dict: Diccionario de pares (Categoría: Cantidad).
            title: Título del gráfico.
            x_label: Etiqueta del eje X.
            y_label: Etiqueta del eje Y.

        Returns:
            str: Bloque de código Mermaid xychart-beta.
        """
        if not data_dict:
            return ""

        keys = [f'"{str(k)}"' for k in data_dict.keys()]
        vals = [str(v) for v in data_dict.values()]

        lines = [
            "```mermaid",
            "xychart-beta",
            f'    title "{title}"',
            f'    x-axis [{", ".join(keys)}]',
            f'    y-axis "{y_label}" 0 --> {max(data_dict.values(), default=10) + 2}',
            f'    bar [{", ".join(vals)}]',
            "```"
        ]

        return "\n".join(lines)

    @staticmethod
    def format_summary_card(stats: Dict[str, Any]) -> str:
        """
        Genera una tarjeta resumen formateada en Markdown con estadísticas clave del proyecto QA.

        Args:
            stats: Diccionario retornado por `JiraLocalStorage.get_summary_stats()`.

        Returns:
            str: Texto formateado con tarjetas métricas.
        """
        total = stats.get("total_issues", 0)
        by_type = stats.get("by_type", {})
        by_status = stats.get("by_status", {})
        bugs = stats.get("bugs_by_status", {})

        type_summary = ", ".join(f"**{k}**: {v}" for k, v in by_type.items()) if by_type else "Sin datos"
        status_summary = ", ".join(f"**{k}**: {v}" for k, v in by_status.items()) if by_status else "Sin datos"

        card = f"""> [!NOTE]
> **Resumen Ejecutivo de Jira en Almacenamiento Local**
> - **Total de Issues Indexados:** `{total}`
> - **Distribución por Tipo:** {type_summary}
> - **Estados Clave:** {status_summary}
"""
        if bugs:
            bugs_summary = ", ".join(f"**{k}**: {v}" for k, v in bugs.items())
            card += f"> - **Estado de Bugs (Defectos):** {bugs_summary}\n"

        return card
