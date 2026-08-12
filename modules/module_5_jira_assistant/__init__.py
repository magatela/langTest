# modules/module_5_jira_assistant/__init__.py
"""
Módulo 5: Agente de Consulta, Análisis Masivo y Soporte Jira.
Proporciona motor JQL, almacenamiento local en SQLite para preservación del contexto del LLM,
y un agente conversacional (Chat) con formateador visual de tablas y gráficos (Charts).
"""

from .storage import JiraLocalStorage
from .jql_engine import JQLEngine
from .chart_formatter import ChartFormatter
from .agent import run_jira_assistant_chat, JiraAssistantAgent

__all__ = [
    "JiraLocalStorage",
    "JQLEngine",
    "ChartFormatter",
    "run_jira_assistant_chat",
    "JiraAssistantAgent",
]
