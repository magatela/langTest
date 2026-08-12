# modules/module_5_jira_assistant/agent.py
"""
Grafo de LangGraph y CLI interactiva para el Módulo 5 (Jira Assistant Agent).

Procesa consultas en lenguaje natural:
1. Consultas puntuales/específicas (un solo issue como PDNEU-1234, pasos de prueba o detalles directos):
   Accede directamente a las herramientas especializadas de Jira (`tools/jira_tool.py`) como `fetch_user_story_details`
   y `get_test_steps_from_case`.
2. Consultas complejas/masivas:
   Formula JQL, descarga e indexa los datos en la base de datos local SQLite para no desbordar el contexto del LLM.

Responde en formato Chat enriquecido con tarjetas detalladas de issue, gráficos Mermaid y tablas de resumen.
Interfaz CLI formateada en Rich UI con colores diferenciados para Usuario y Asistente.
"""

from __future__ import annotations

import json
import logging
import operator
import re
import sys
from typing import Any, Dict, List, Optional, TypedDict, Annotated, Union

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END

try:
    from config.config_loader import get_llm_config
    from tools.jira_tool import (
        fetch_user_story_details,
        get_test_steps_from_case,
        normalize_issue_key,
        DEFAULT_PROJECT_KEY,
    )
    from modules.module_5_jira_assistant.storage import JiraLocalStorage
    from modules.module_5_jira_assistant.jql_engine import JQLEngine
    from modules.module_5_jira_assistant.chart_formatter import ChartFormatter
    from modules.module_5_jira_assistant.prompts import (
        JQL_TRANSLATOR_SYSTEM_PROMPT,
        QA_ASSISTANT_SYSTEM_PROMPT,
    )
except ImportError:
    from config.config_loader import get_llm_config
    from jira_tool import (
        fetch_user_story_details,
        get_test_steps_from_case,
        normalize_issue_key,
        DEFAULT_PROJECT_KEY,
    )
    from storage import JiraLocalStorage
    from jql_engine import JQLEngine
    from chart_formatter import ChartFormatter
    from prompts import (
        JQL_TRANSLATOR_SYSTEM_PROMPT,
        QA_ASSISTANT_SYSTEM_PROMPT,
    )

logger = logging.getLogger(__name__)


def sanitize_messages(messages: List[Any]) -> List[BaseMessage]:
    """Sanea la lista de mensajes para asegurar objetos BaseMessage válidos."""
    clean_list: List[BaseMessage] = []
    for msg in messages:
        if isinstance(msg, BaseMessage):
            clean_list.append(msg)
        elif isinstance(msg, str):
            clean_list.append(HumanMessage(content=msg))
        elif isinstance(msg, dict):
            role = msg.get("role", "user")
            content = msg.get("content", str(msg))
            if role == "system":
                clean_list.append(SystemMessage(content=content))
            elif role in ["assistant", "ai"]:
                clean_list.append(AIMessage(content=content))
            else:
                clean_list.append(HumanMessage(content=content))
        else:
            clean_list.append(HumanMessage(content=str(msg)))
    return clean_list


class JiraAgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    user_query: str
    target_issue_keys: List[str]
    is_single_issue: bool
    jql_query: str
    single_issue_details: List[Dict[str, Any]]
    aggregated_data: Dict[str, Any]
    chart_output: str
    iteration: int


def extract_issue_keys(text: str, default_prefix: str = DEFAULT_PROJECT_KEY) -> List[str]:
    """
    Detecta referencias a claves de Jira en el texto (ej. 'PDNEU-1234', 'QA-56' o '1234').

    Args:
        text: Texto de la consulta.
        default_prefix: Prefijo por defecto del proyecto.

    Returns:
        List[str]: Claves de Jira detectadas únicas.
    """
    keys = []
    matches_full = re.findall(r"\b[A-Za-z][A-Za-z0-9]+-\d+\b", text)
    for m in matches_full:
        norm = normalize_issue_key(m, default_prefix)
        if norm not in keys:
            keys.append(norm)

    if not keys:
        matches_num = re.findall(r"(?:issue|key|story|bug|test|#)\s*#?(\d+)", text, re.IGNORECASE)
        for num in matches_num:
            norm = normalize_issue_key(num, default_prefix)
            if norm not in keys:
                keys.append(norm)

    return keys


def create_jira_assistant_graph(
    llm: Optional[Any] = None,
    storage: Optional[JiraLocalStorage] = None,
    jql_engine: Optional[JQLEngine] = None
):
    """
    Crea y compila el grafo LangGraph para el Módulo 5.
    """
    if storage is None:
        storage = JiraLocalStorage()

    if jql_engine is None:
        jql_engine = JQLEngine()

    if llm is None:
        try:
            llm_cfg = get_llm_config()
            model_info = llm_cfg["models"][0]
            llm = ChatOpenAI(
                model=model_info["model"],
                openai_api_key=llm_cfg["apiKey"],
                openai_api_base=llm_cfg["apiBase"],
                temperature=0.1
            )
        except Exception:
            llm = None

    def jql_builder_node(state: JiraAgentState) -> Dict[str, Any]:
        """Nodo 1: Analiza la consulta y decide si es un issue directo o una consulta JQL masiva."""
        user_query = state.get("user_query", "")
        issue_keys = extract_issue_keys(user_query)

        is_single = len(issue_keys) > 0 and len(issue_keys) <= 3
        jql_result = ""

        if is_single:
            keys_str = ", ".join(f'"{k}"' for k in issue_keys)
            jql_result = f"key IN ({keys_str})"
        else:
            if llm is not None:
                try:
                    sys_msg = SystemMessage(content=JQL_TRANSLATOR_SYSTEM_PROMPT)
                    usr_msg = HumanMessage(content=f"Benutzeranfrage: {user_query}")
                    res = llm.invoke([sys_msg, usr_msg])
                    content = res.content if hasattr(res, "content") else str(res)

                    clean_json = re.sub(r'```(?:json)?\s*', '', str(content)).strip('` \n')
                    parsed = json.loads(clean_json)
                    jql_result = parsed.get("jql", "")
                except Exception as e:
                    logger.warning("Fallo en traducción LLM a JQL, usando regla fallback: %s", str(e))

            if not jql_result:
                lower_q = user_query.lower()
                if "bug" in lower_q or "fehler" in lower_q or "defecto" in lower_q:
                    jql_result = jql_engine.build_jql(issue_types=["Bug"])
                elif "story" in lower_q or "user story" in lower_q or "historia" in lower_q:
                    jql_result = jql_engine.build_jql(issue_types=["Story"])
                elif "test" in lower_q or "prüfung" in lower_q or "prueba" in lower_q:
                    jql_result = jql_engine.build_jql(issue_types=["Test"])
                else:
                    jql_result = jql_engine.build_jql(text_query=user_query)

        return {
            "target_issue_keys": issue_keys,
            "is_single_issue": is_single,
            "jql_query": jql_result,
        }

    def fetch_and_store_node(state: JiraAgentState) -> Dict[str, Any]:
        """
        Nodo 2: 
        - Para consultas directas a un issue: usa las herramientas directas `fetch_user_story_details` y `get_test_steps_from_case`.
        - Para consultas masivas: usa `JQLEngine.fetch_and_cache` y SQLite storage.
        """
        is_single = state.get("is_single_issue", False)
        target_keys = state.get("target_issue_keys", [])
        jql = state.get("jql_query", "")

        single_details = []

        if is_single and target_keys:
            for key in target_keys:
                details = fetch_user_story_details(key)
                if details.get("status") == "success":
                    raw_data = details.get("raw", {})
                    if raw_data:
                        storage.upsert_issue(raw_data)
                    else:
                        storage.upsert_issue({
                            "key": details.get("key", key),
                            "fields": {
                                "summary": details.get("summary", ""),
                                "description": details.get("description", ""),
                                "priority": {"name": details.get("priority", "Mittel")},
                                "status": {"name": details.get("issue_status", "Offen")},
                            }
                        })

                steps_info = get_test_steps_from_case(key)
                if steps_info.get("status") == "success":
                    details["steps"] = steps_info.get("steps", [])

                single_details.append(details)

            fetch_res = {"status": "success", "mode": "direct_tool", "count": len(single_details)}
        else:
            fetch_res = jql_engine.fetch_and_cache(jql, storage, max_results=150)

        return {
            "single_issue_details": single_details,
            "aggregated_data": fetch_res,
        }

    def local_analysis_node(state: JiraAgentState) -> Dict[str, Any]:
        """Nodo 3: Genera representaciones visuales y resumen estadístico en alemán."""
        is_single = state.get("is_single_issue", False)
        single_details = state.get("single_issue_details", [])

        if is_single and single_details:
            cards = []
            for item in single_details:
                key = item.get("key", "")
                summary = item.get("summary", "")
                desc = item.get("description", "Keine Beschreibung vorhanden.")
                status = item.get("issue_status", item.get("status", "Offen"))
                prio = item.get("priority", "Mittel")
                steps = item.get("steps", [])

                card_lines = [
                    f"### 📋 Jira-Issue Details: `{key}`",
                    f"- **Titel:** {summary}",
                    f"- **Status:** `{status}` | **Priorität:** `{prio}`",
                    f"- **Beschreibung:** {desc if desc else 'Keine Beschreibung vorhanden.'}",
                ]

                if steps:
                    card_lines.append("\n#### Definierte Testschritte (Xray):")
                    card_lines.append("| # | Aktion | Daten | Erwartetes Ergebnis |")
                    card_lines.append("|---|---|---|---|")
                    for idx, step in enumerate(steps, 1):
                        card_lines.append(f"| {idx} | {step.get('step','')} | {step.get('data','')} | {step.get('result','')} |")

                cards.append("\n".join(card_lines))

            charts_combined = "\n\n---\n\n".join(cards)
        else:
            stats = storage.get_summary_stats()
            recent_issues = storage.query_issues(limit=15)

            card = ChartFormatter.format_summary_card(stats)
            table = ChartFormatter.format_issues_table(recent_issues, title="Relevante Issues im lokalen Speicher")

            pie_chart = ""
            if stats.get("by_status"):
                pie_chart = ChartFormatter.format_mermaid_pie_chart(
                    stats["by_status"],
                    title="Verteilung nach Status"
                )

            bar_chart = ""
            if stats.get("by_priority"):
                bar_chart = ChartFormatter.format_mermaid_bar_chart(
                    stats["by_priority"],
                    title="Verteilung nach Priorität",
                    x_label="Priorität",
                    y_label="Issues"
                )

            charts_combined = f"{card}\n\n{table}\n\n{pie_chart}\n\n{bar_chart}".strip()

        return {"chart_output": charts_combined}

    def response_node(state: JiraAgentState) -> Dict[str, Any]:
        """Nodo 4: Construye la respuesta conversacional final en alemán."""
        user_query = state.get("user_query", "")
        jql = state.get("jql_query", "")
        charts = state.get("chart_output", "")
        is_single = state.get("is_single_issue", False)
        stats = storage.get_summary_stats()

        final_text = ""
        if llm is not None:
            try:
                sys_msg = SystemMessage(content=QA_ASSISTANT_SYSTEM_PROMPT)
                prompt_content = f"""BENUTZERANFRAGE: {user_query}
ABFRAGETYP: {'Einzelausgabe / Direktes Werkzeug' if is_single else 'JQL-Abfrage / Massenaggregation'}
JQL / KEY: `{jql}`
AGGREGIERTE LOKALE JIRA-DATEN: {json.dumps(stats, ensure_ascii=False)}

Bitte erstelle eine klare, hilfreiche und gut strukturierte Antwort (im Chat-Format) AUSSCHLIESSLICH AUF DEUTSCH, um die Fragen des Benutzers zu klären.
"""
                usr_msg = HumanMessage(content=prompt_content)
                res = llm.invoke([sys_msg, usr_msg])
                llm_response = res.content if hasattr(res, "content") else str(res)
                final_text = f"{llm_response}\n\n{charts}"
            except Exception as e:
                logger.warning("Excepción en generación LLM de respuesta: %s", str(e))

        if not final_text:
            final_text = (
                f"### Jira QA-Assistent\n\n"
                f"Bearbeitete Anfrage: **\"{user_query}\"**\n"
                f"Verwendete JQL-Abfrage: `{jql}`\n\n"
                f"{charts}"
            )

        ai_message = AIMessage(content=final_text)
        return {"messages": [ai_message]}

    workflow = StateGraph(JiraAgentState)
    workflow.add_node("jql_builder", jql_builder_node)
    workflow.add_node("fetch_and_store", fetch_and_store_node)
    workflow.add_node("local_analysis", local_analysis_node)
    workflow.add_node("response", response_node)

    workflow.set_entry_point("jql_builder")
    workflow.add_edge("jql_builder", "fetch_and_store")
    workflow.add_edge("fetch_and_store", "local_analysis")
    workflow.add_edge("local_analysis", "response")
    workflow.add_edge("response", END)

    return workflow.compile()


def run_jira_assistant_query(
    user_query: str,
    storage: Optional[JiraLocalStorage] = None,
    mock_issues: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Ejecuta una consulta única en el agente del Módulo 5.

    Args:
        user_query: Pregunta en lenguaje natural del usuario.
        storage: Instancia de JiraLocalStorage (opcional).
        mock_issues: Issues simulados para pruebas offline/unitarias.

    Returns:
        Dict[str, Any]: Resultado con respuesta, JQL y gráficos generados.
    """
    if storage is None:
        storage = JiraLocalStorage()

    jql_engine = JQLEngine()
    if mock_issues is not None:
        storage.upsert_issues(mock_issues)

    app = create_jira_assistant_graph(storage=storage, jql_engine=jql_engine)

    inputs = {
        "messages": [HumanMessage(content=user_query)],
        "user_query": user_query,
        "target_issue_keys": [],
        "is_single_issue": False,
        "jql_query": "",
        "single_issue_details": [],
        "aggregated_data": {},
        "chart_output": "",
        "iteration": 0,
    }

    final_state = app.invoke(inputs)

    messages = final_state.get("messages", [])
    last_msg = messages[-1] if messages else AIMessage(content="")
    answer = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

    return {
        "success": True,
        "user_query": user_query,
        "is_single_issue": final_state.get("is_single_issue", False),
        "jql_query": final_state.get("jql_query", ""),
        "answer": answer,
        "chart_output": final_state.get("chart_output", ""),
    }


def run_jira_assistant_chat(storage_path: Optional[str] = None) -> None:
    """
    Inicia una sesión interactiva en modo CLI Chat con el Asistente de Jira usando Rich UI.
    Formatea la salida simulando una interfaz de chat con colores diferenciados:
    - Usuario: Panel e identificador VERDE ([bold green]).
    - Asistente: Panel e identificador CYAN ([bold cyan]) con Markdown.
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.padding import Padding
    from rich.rule import Rule

    console = Console()
    console.print()
    console.print(Rule("[bold cyan]🤖 JIRA QA ASSISTANT CHAT (DEUTSCH / CHAT UI)[/bold cyan]"))
    console.print("[dim white]  - Einzelausgaben: 'PDNEU-1234' oder 'Details zu PDNEU-567'[/dim white]")
    console.print("[dim white]  - Massenabfragen: 'Zeige offene Bugs' oder 'Teststatus-Übersicht'[/dim white]")
    console.print("[dim yellow]  - Eingabe 'exit' oder 'salir' zum Beenden.[/dim yellow]\n")

    storage = JiraLocalStorage(storage_path or JiraLocalStorage().db_path)

    while True:
        try:
            user_input = console.input("\n[bold green]👤 Benutzer (Usuario) > [/bold green]").strip()
            if not user_input:
                continue

            if user_input.lower() in ["exit", "salir", "quit"]:
                console.print("\n[bold yellow]Auf Wiedersehen! / ¡Hasta luego![/bold yellow]\n")
                break

            # 1. Mensaje del Usuario en Panel VERDE (Estilo Burbuja Chat)
            user_panel = Panel(
                user_input,
                title="[bold green]👤 Benutzer / User[/bold green]",
                border_style="green",
                expand=False,
                padding=(0, 2)
            )
            console.print()
            console.print(Padding(user_panel, (0, 0, 0, 4)))

            console.print("\n[dim cyan]🔄 [Jira Assistant] Suche in Jira und Synchronisierung der lokalen Datenbank...[/dim cyan]\n")
            result = run_jira_assistant_query(user_input, storage=storage)

            answer_text = result.get("answer", "")

            # 2. Respuesta del Asistente en Panel CYAN (Estilo Burbuja Chat con Markdown y espaciado)
            bot_panel = Panel(
                Markdown(answer_text),
                title="[bold cyan]🤖 Jira QA-Assistent[/bold cyan]",
                border_style="cyan",
                expand=True,
                padding=(1, 2)
            )
            console.print(Padding(bot_panel, (1, 4, 1, 0)))
            console.print(Rule(style="dim cyan"))

        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold yellow]Sitzung beendet.[/bold yellow]\n")
            break


class JiraAssistantAgent:
    """
    Clase contenedora para instanciar y usar el Módulo 5 programáticamente.
    """

    def __init__(self, db_path: Union[str, Path] = ":memory:"):
        self.storage = JiraLocalStorage(db_path)
        self.jql_engine = JQLEngine()
        self.app = create_jira_assistant_graph(storage=self.storage, jql_engine=self.jql_engine)

    def ask(self, query: str, mock_issues: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Ejecuta una consulta contra el agente de Jira."""
        return run_jira_assistant_query(query, storage=self.storage, mock_issues=mock_issues)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--chat", "-c"]:
        run_jira_assistant_chat()
    else:
        demo_agent = JiraAssistantAgent(":memory:")
        res = demo_agent.ask("Zeige Informationen zu PDNEU-101")
        print(res["answer"])
