# modules/module_4_pom_generator/agent.py
"""
ReAct-Agent für Modul 4 (Page Object Models in TypeScript) unter Verwendung von LangGraph.
Unterstützt autonome Entscheidungen, Tool-Invocations (REPL, Dateisystem, Aria-Snapshots) und Selbstkorrektur.
"""

import json
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Annotated, Generator
from typing_extensions import TypedDict

from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from config.config_loader import get_llm_config
from modules.module_2_browser_repl.ts_repl_bridge import get_repl_bridge
from modules.module_4_pom_generator.prompts import (
    POM_GENERATOR_SYSTEM_PROMPT,
    POM_UPDATER_SYSTEM_PROMPT
)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
POM_DIR = ROOT_DIR / "ts_repl_server" / "POM"

def get_pom_dir() -> Path:
    """
    Gibt den Pfad zum Verzeichnis zurück, in dem die TypeScript-POMs liegen.
    """
    if not POM_DIR.exists():
        POM_DIR.mkdir(parents=True, exist_ok=True)
    return POM_DIR

# === 🛠️ WERKZEUGE (TOOLS) FÜR DEN AGENTEN ===

@tool
def read_workspace_file(filepath: str) -> str:
    """
    Liest den Inhalt einer Datei im Projekt (z. B. 'ts_repl_server/POM/NavigationPage.ts').
    """
    try:
        p = Path(filepath)
        if not p.is_absolute():
            p = ROOT_DIR / filepath
        if not p.exists():
            return f"Fehler: Die Datei '{filepath}' wurde nicht gefunden."
        return p.read_text(encoding="utf-8")
    except Exception as e:
        return f"Fehler beim Lesen von '{filepath}': {str(e)}"

@tool
def write_workspace_file(filepath: str, content: str) -> str:
    """
    Erstellt oder überschreibt eine Datei im Projekt mit dem angegebenen TypeScript-Code.
    Standardmäßig sollte der Pfad im Ordner 'ts_repl_server/POM/' liegen (z. B. 'ts_repl_server/POM/LoginPage.ts').
    """
    try:
        p = Path(filepath)
        if not p.is_absolute():
            if not filepath.startswith("ts_repl_server"):
                p = POM_DIR / p.name
            else:
                p = ROOT_DIR / filepath

        p.parent.mkdir(parents=True, exist_ok=True)
        # Markdown-Codeblocks bereinigen
        clean_code = content
        pattern = r"```(?:typescript|ts)?\s*([\s\S]*?)\s*```"
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            clean_code = match.group(1).strip()

        p.write_text(clean_code, encoding="utf-8")
        return f"Erfolg: Datei erfolgreich gespeichert unter '{p}'."
    except Exception as e:
        return f"Fehler beim Schreiben von '{filepath}': {str(e)}"

@tool
def eval_in_repl(ts_code: str) -> str:
    """
    Evaluiert TypeScript-Code in Echtzeit in der aktiven Playwright-REPL-Sitzung des Browsers.
    Gibt das Ergebnis der Ausführung oder Fehlermeldungen zurück.
    """
    try:
        bridge = get_repl_bridge()
        if not bridge.ensure_started():
            return json.dumps({"status": "error", "error": "REPL-Server konnte nicht gestartet werden."})
        res = bridge.eval_code(ts_code)
        return json.dumps(res, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False)

@tool
def inspect_aria_snapshot(selector: str = "body") -> str:
    """
    Inspektioniert die aktive Ansicht im REPL-Browser und gibt die ARIA-Baumstruktur (Barrierefreiheitsbaum, Lokatoren und Schaltflächen) zurück.
    """
    try:
        bridge = get_repl_bridge()
        if not bridge.ensure_started():
            return json.dumps({"status": "error", "error": "REPL-Server konnte nicht gestartet werden."})
        res = bridge.get_aria_snapshot(selector)
        return json.dumps(res, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False)

@tool
def take_screenshot(filename: str = "screenshot.png") -> str:
    """
    Erstellt einen Screenshot der aktiven Seite im REPL-Browser und speichert ihn.
    """
    try:
        bridge = get_repl_bridge()
        if not bridge.ensure_started():
            return json.dumps({"status": "error", "error": "REPL-Server konnte nicht gestartet werden."})
        output_path = str(ROOT_DIR / "results" / filename)
        res = bridge.take_screenshot(output_path)
        return json.dumps(res, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False)

AGENT_TOOLS = [
    read_workspace_file,
    write_workspace_file,
    eval_in_repl,
    inspect_aria_snapshot,
    take_screenshot
]

# === 🧠 AGENTEN-ZUSTAND UND PROMPTS ===

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

SYSTEM_AGENT_PROMPT = """Du bist ein autonomer Testautomatisierungs-Agent (ReAct Agent) für Playwright in TypeScript.
Du hast direkten Zugriff auf Werkzeuge zur Analyse von Webseiten (inspect_aria_snapshot, take_screenshot), zum Lesen/Schreiben von Dateien (read_workspace_file, write_workspace_file) und zur Ausführung im REPL-Browser (eval_in_repl).

DEIN WORKFLOW:
1. Analysiere die Anfrage des Benutzers. Wenn du vorhandene POMs prüfen musst, nutze `read_workspace_file`.
2. Wenn du die aktive Ansicht untersuchen musst, nutze `inspect_aria_snapshot`.
3. Erstelle oder aktualisiere die Page Object Model (POM) Klasse unter Einhaltung strenger TypeScript-Best-Practices (`Page`, `Locator`, `async`).
4. Teste den generierten Code mit `eval_in_repl` im Browser. Wenn ein Fehler auftritt, korrigiere den Code selbstständig.
5. Speichere die finale Datei mit `write_workspace_file` im Ordner `ts_repl_server/POM/`.
6. Antworte dem Benutzer präzise auf Deutsch.
"""

def create_pom_agent_graph(llm_instance: Optional[Any] = None):
    """
    Erstellt und kompiliert den LangGraph ReAct StateGraph mit MemorySaver.
    """
    if llm_instance is None:
        config = get_llm_config()
        model_info = config["models"][0]
        llm = ChatOpenAI(
            model=model_info.get("model", "gpt-4o"),
            temperature=model_info.get("temperature", 0.2),
            openai_api_key=config.get("apiKey", "mock-key"),
            openai_api_base=config.get("apiBase", "https://api.openai.com/v1")
        )
    else:
        llm = llm_instance

    llm_with_tools = llm.bind_tools(AGENT_TOOLS)

    def agent_node(state: AgentState):
        messages = [SystemMessage(content=SYSTEM_AGENT_PROMPT)] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    builder = StateGraph(AgentState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(AGENT_TOOLS))

    builder.set_entry_point("agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")

    memory = MemorySaver()
    return builder.compile(checkpointer=memory)

# Instanz des Graphen
_COMPILED_GRAPH = None

def get_pom_agent_graph(llm_instance: Optional[Any] = None):
    global _COMPILED_GRAPH
    if _COMPILED_GRAPH is None or llm_instance is not None:
        _COMPILED_GRAPH = create_pom_agent_graph(llm_instance=llm_instance)
    return _COMPILED_GRAPH

def stream_pom_agent_turn(
    user_message: str,
    thread_id: str = "default_session",
    llm_instance: Optional[Any] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Streamt die Interaktionen des Agenten (Gedanken, Tool-Aufrufe, Tool-Ergebnisse, finale Antworten)
    für die Benutzeroberfläche.
    """
    app = get_pom_agent_graph(llm_instance=llm_instance)
    config = {"configurable": {"thread_id": thread_id}}
    inputs = {"messages": [HumanMessage(content=user_message)]}

    for event in app.stream(inputs, config=config, stream_mode="values"):
        last_msg = event["messages"][-1]
        
        if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
            for tc in last_msg.tool_calls:
                yield {
                    "type": "tool_call",
                    "name": tc["name"],
                    "args": tc["args"],
                    "id": tc.get("id")
                }
        elif isinstance(last_msg, ToolMessage):
            yield {
                "type": "tool_result",
                "name": last_msg.name,
                "content": last_msg.content
            }
        elif isinstance(last_msg, AIMessage) and last_msg.content:
            yield {
                "type": "ai_response",
                "content": last_msg.content
            }
