# modules/module_4_pom_generator/ui.py
"""
Textual TUI-Benutzeroberfläche für Modul 4 (TypeScript POM Generator & ReAct Agent).
Layout:
- Vollbild-Chatbereich mit Aktivitätsanzeige (Loading Indicator / Status).
- Schaltfläche zum Kopieren des Chat-Verlaufs in die Zwischenablage (pyperclip).
- Unterer Eingabebereich mit Aktionsschaltfläche.
"""

import json
from pathlib import Path
from typing import Optional
import pyperclip

from textual.app import App, ComposeResult
from textual.widgets import Button, Static, Input, RichLog, Label, LoadingIndicator
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual import on, work
from textual.binding import Binding

from modules.module_4_pom_generator.agent import stream_pom_agent_turn

TCSS_STYLE = """
Screen {
    layout: vertical;
    background: #4285F4;
    padding: 0;
}

#main-container {
    width: 100%;
    height: 100%;
    layout: vertical;
}

#top-bar {
    height: 3;
    background: #FFFFFF;
    color: #000000;
    padding: 0 2;
    align: left middle;
    border-bottom: solid #E0E0E0;
}

#chat-header {
    text-style: bold;
    color: #000000;
    content-align: left middle;
    width: 20%;
}

#status-label {
    color: #2E7D32;
    text-style: bold;
    content-align: center middle;
    width: 55%;
}

#btn-copy {
    background: #E0E0E0;
    color: #000000;
    border: none;
    text-style: bold;
    min-width: 16;
    width: 25%;
}

#btn-copy:hover {
    background: #BDBDBD;
}

#chat-container {
    height: 72%;
    background: #FFFFFF;
    color: #000000;
    padding: 1 2;
    layout: vertical;
}

#chat-log {
    height: 100%;
    background: #FFFFFF;
    color: #000000;
    border: none;
}

#spinner-bar {
    height: 3;
    background: #FFF9C4;
    color: #F57F17;
    padding: 0 2;
    display: none;
    align: left middle;
}

#spinner-text {
    color: #E65100;
    text-style: bold;
    margin-left: 1;
}

#input-container {
    height: 25%;
    background: #757575;
    color: #FFFFFF;
    padding: 1 2;
    layout: vertical;
}

#input-header {
    text-style: bold;
    color: #FFFFFF;
    margin-bottom: 1;
}

#input-field {
    width: 100%;
    background: #BDBDBD;
    color: #000000;
    border: none;
    margin-bottom: 1;
}

#send-bar {
    align: right middle;
    height: 3;
}

#btn-send {
    background: #FFFFFF;
    color: #000000;
    border: none;
    text-style: bold;
    min-width: 16;
}

#btn-send:hover {
    background: #E0E0E0;
}
"""

class POMGeneratorTUI(App):
    """
    Textual TUI Anwendung für den interaktiven POM Generator (Vollbild-Chat).
    """
    CSS = TCSS_STYLE
    TITLE = "POM Generator Agent - ReAct TUI"
    BINDINGS = [
        Binding("ctrl+c", "copy_chat", "Chat kopieren", show=True),
        Binding("ctrl+q", "quit", "Beenden", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.chat_history_text = []

    def compose(self) -> ComposeResult:
        with Container(id="main-container"):
            # 1. Obere Leiste mit Titel, Status und Kopier-Button
            with Horizontal(id="top-bar"):
                yield Label("chat", id="chat-header")
                yield Label("🟢 Bereit", id="status-label")
                yield Button("📋 Copiar Chat", id="btn-copy")

            # 2. Status-Banner beim Nachdenken / Werkzeugausführung
            with Horizontal(id="spinner-bar"):
                yield LoadingIndicator()
                yield Label("⏳ Der Agent denkt nach und führt REPL-Werkzeuge aus...", id="spinner-text")

            # 3. Chat-Bereich (Weiß)
            with Container(id="chat-container"):
                yield RichLog(id="chat-log", highlight=True, markup=True)

            # 4. Eingabebereich (Grau)
            with Container(id="input-container"):
                yield Label("User Input", id="input-header")
                yield Input(placeholder="Escribe tu mensaje o instrucción para el agente...", id="input-field")
                with Horizontal(id="send-bar"):
                    yield Button("button send", id="btn-send")

    def on_mount(self) -> None:
        log = self.query_one("#chat-log", RichLog)
        msg = "🤖 [bold green]Agent bereit.[/bold green] Gib eine Anweisung ein (z. B. 'Erstelle LoginPage.ts mit Login-Formular'). Der Agent führt Inspektionen und REPL-Tests autonom durch."
        log.write(msg)
        self.chat_history_text.append("Agent: " + msg)

    @on(Button.Pressed, "#btn-copy")
    def action_copy_chat(self) -> None:
        """
        Kopiert den gesamten Chatverlauf in die System-Zwischenablage via pyperclip.
        """
        full_text = "\n\n".join(self.chat_history_text)
        try:
            pyperclip.copy(full_text)
            status = self.query_one("#status-label", Label)
            status.update("📋 Chat in Zwischenablage kopiert!")
            self.set_timer(3.0, lambda: status.update("🟢 Bereit"))
        except Exception as e:
            log = self.query_one("#chat-log", RichLog)
            log.write(f"[bold red]❌ Fehler beim Kopieren in die Zwischenablage: {e}[/bold red]")

    @on(Button.Pressed, "#btn-send")
    @on(Input.Submitted, "#input-field")
    def action_send_message(self) -> None:
        input_field = self.query_one("#input-field", Input)
        user_text = input_field.value.strip()
        if not user_text:
            return

        input_field.value = ""
        log = self.query_one("#chat-log", RichLog)
        log.write(f"\n[bold blue]👤 User:[/bold blue] {user_text}")
        self.chat_history_text.append(f"User: {user_text}")

        # Status auf 'Arbeitet' setzen und Spinner anzeigen
        self._set_working_state(True)
        self.run_agent_turn(user_text)

    def _set_working_state(self, is_working: bool) -> None:
        spinner_bar = self.query_one("#spinner-bar", Horizontal)
        status_label = self.query_one("#status-label", Label)
        btn_send = self.query_one("#btn-send", Button)
        input_field = self.query_one("#input-field", Input)

        if is_working:
            spinner_bar.styles.display = "block"
            status_label.update("⏳ Agent arbeitet...")
            status_label.styles.color = "#E65100"
            btn_send.disabled = True
            input_field.disabled = True
        else:
            spinner_bar.styles.display = "none"
            status_label.update("🟢 Bereit")
            status_label.styles.color = "#2E7D32"
            btn_send.disabled = False
            input_field.disabled = False
            input_field.focus()

    @work(thread=True)
    def run_agent_turn(self, user_message: str) -> None:
        log = self.query_one("#chat-log", RichLog)
        try:
            for event in stream_pom_agent_turn(user_message=user_message, thread_id="tui_session"):
                event_type = event.get("type")
                if event_type == "tool_call":
                    tool_name = event.get("name")
                    args = json.dumps(event.get("args", {}), ensure_ascii=False)
                    msg = f"🛠️ [dim]Invoking Tool:[/dim] [bold cyan]{tool_name}[/bold cyan]({args})"
                    self.call_from_thread(log.write, msg)
                    self.chat_history_text.append(f"Tool Call: {tool_name}({args})")
                elif event_type == "tool_result":
                    res_content = str(event.get("content", ""))[:200]
                    msg = f"   ↳ [dim]Result:[/dim] {res_content}..."
                    self.call_from_thread(log.write, msg)
                    self.chat_history_text.append(f"Tool Result: {res_content}")
                elif event_type == "ai_response":
                    ai_content = event.get("content", "")
                    msg = f"\n[bold green]🤖 Agent:[/bold green]\n{ai_content}"
                    self.call_from_thread(log.write, msg)
                    self.chat_history_text.append(f"Agent: {ai_content}")
        except Exception as e:
            err_msg = f"[bold red]❌ Agent Error: {e}[/bold red]"
            self.call_from_thread(log.write, err_msg)
            self.chat_history_text.append(f"Error: {e}")
        finally:
            self.call_from_thread(self._set_working_state, False)

if __name__ == "__main__":
    app = POMGeneratorTUI()
    app.run()
