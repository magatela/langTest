# modules/module_4_pom_generator/ui.py
"""
Textual TUI-Benutzeroberfläche für Modul 4 (TypeScript POM Generator & Agent).
Reproduziert exakt das Layout der Referenzgrafik:
- Linke Sidebar (Blau) mit grünen Buttons für Aria-Snapshot und Screenshot.
- Rechter Hauptbereich:
  - Oben: 'chat' Bereich (Weiß) mit Log-Verlauf des Agenten und der Werkzeuge.
  - Unten: 'User Input' Bereich (Grau) mit Eingabefeld und weißer 'button send' Schaltfläche.
"""

import json
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.widgets import Button, Static, Input, RichLog, Label
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual import on, work
from textual.worker import Worker, WorkerState

from modules.module_4_pom_generator.agent import (
    stream_pom_agent_turn,
    inspect_aria_snapshot,
    take_screenshot
)

TCSS_STYLE = """
Screen {
    layout: horizontal;
    background: #4285F4;
}

#sidebar {
    width: 25%;
    height: 100%;
    background: #4285F4;
    padding: 1 1;
    border-right: solid #3367D6;
}

.btn-green {
    width: 100%;
    margin-bottom: 1;
    background: #8BC34A;
    color: #000000;
    border: none;
    text-style: bold;
    height: 3;
}

.btn-green:hover {
    background: #7CB342;
}

#main-panel {
    width: 75%;
    height: 100%;
    layout: vertical;
}

#chat-container {
    height: 75%;
    background: #FFFFFF;
    color: #000000;
    padding: 1 2;
    layout: vertical;
}

#chat-header {
    text-style: bold;
    color: #000000;
    margin-bottom: 1;
}

#chat-log {
    height: 100%;
    background: #FFFFFF;
    color: #000000;
    border: none;
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
    Textual TUI Anwendung für den interaktiven POM Generator.
    """
    CSS = TCSS_STYLE
    TITLE = "POM Generator Agent - ReAct TUI"

    def compose(self) -> ComposeResult:
        # 1. Linke Sidebar (Blau)
        with Container(id="sidebar"):
            yield Button("Add aria Snapshot", id="btn-aria", classes="btn-green")
            yield Button("Add screenshot", id="btn-screenshot", classes="btn-green")

        # 2. Rechter Hauptbereich
        with Container(id="main-panel"):
            # Chat Bereich (Weiß)
            with Container(id="chat-container"):
                yield Label("chat", id="chat-header")
                yield RichLog(id="chat-log", highlight=True, markup=True)

            # User Input Bereich (Grau)
            with Container(id="input-container"):
                yield Label("User Input", id="input-header")
                yield Input(placeholder="Escribe tu mensaje o instrucción para el agente...", id="input-field")
                with Horizontal(id="send-bar"):
                    yield Button("button send", id="btn-send")

    def on_mount(self) -> None:
        log = self.query_one("#chat-log", RichLog)
        log.write("[bold green]🤖 Agent bereit.[/bold green] Gib eine Anweisung ein oder nutze die Buttons auf der linken Seite.")

    @on(Button.Pressed, "#btn-aria")
    def action_add_aria_snapshot(self) -> None:
        log = self.query_one("#chat-log", RichLog)
        input_field = self.query_one("#input-field", Input)
        log.write("[bold yellow]📸 Inspektioniere Aria-Snapshot im REPL-Browser...[/bold yellow]")
        
        @work(thread=True)
        def fetch_aria():
            try:
                res_str = inspect_aria_snapshot.invoke({"selector": "body"})
                res = json.loads(res_str)
                if res.get("status") == "success":
                    snapshot_text = res.get("result", "")
                    self.call_from_thread(self._append_context_to_input, f"\n[Context Aria Snapshot]:\n{snapshot_text[:500]}")
                    self.call_from_thread(log.write, "[bold green]✓ Aria Snapshot erfolgreich zum Kontext hinzugefügt![/bold green]")
                else:
                    self.call_from_thread(log.write, f"[bold red]❌ Fehler beim Aria Snapshot: {res.get('error')}[/bold red]")
            except Exception as e:
                self.call_from_thread(log.write, f"[bold red]❌ Fehler: {e}[/bold red]")

        fetch_aria()

    @on(Button.Pressed, "#btn-screenshot")
    def action_add_screenshot(self) -> None:
        log = self.query_one("#chat-log", RichLog)
        log.write("[bold yellow]📸 Erstelle Screenshot im REPL-Browser...[/bold yellow]")
        
        @work(thread=True)
        def fetch_shot():
            try:
                res_str = take_screenshot.invoke({"filename": "tui_context_shot.png"})
                res = json.loads(res_str)
                if res.get("status") == "success":
                    self.call_from_thread(self._append_context_to_input, "\n[Context Screenshot]: tui_context_shot.png")
                    self.call_from_thread(log.write, "[bold green]✓ Screenshot erfolgreich erstellt![/bold green]")
                else:
                    self.call_from_thread(log.write, f"[bold red]❌ Fehler beim Screenshot: {res.get('error')}[/bold red]")
            except Exception as e:
                self.call_from_thread(log.write, f"[bold red]❌ Fehler: {e}[/bold red]")

        fetch_shot()

    def _append_context_to_input(self, text: str) -> None:
        input_field = self.query_one("#input-field", Input)
        input_field.value += text

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

        self.run_agent_turn(user_text)

    @work(thread=True)
    def run_agent_turn(self, user_message: str) -> None:
        log = self.query_one("#chat-log", RichLog)
        try:
            for event in stream_pom_agent_turn(user_message=user_message, thread_id="tui_session"):
                event_type = event.get("type")
                if event_type == "tool_call":
                    tool_name = event.get("name")
                    args = json.dumps(event.get("args", {}), ensure_ascii=False)
                    self.call_from_thread(log.write, f"🛠️ [dim]Invoking Tool:[/dim] [bold cyan]{tool_name}[/bold cyan]({args})")
                elif event_type == "tool_result":
                    res_content = str(event.get("content", ""))[:150]
                    self.call_from_thread(log.write, f"   ↳ [dim]Result:[/dim] {res_content}...")
                elif event_type == "ai_response":
                    ai_content = event.get("content", "")
                    self.call_from_thread(log.write, f"\n[bold green]🤖 Agent:[/bold green]\n{ai_content}")
        except Exception as e:
            self.call_from_thread(log.write, f"[bold red]❌ Agent Error: {e}[/bold red]")

if __name__ == "__main__":
    app = POMGeneratorTUI()
    app.run()
