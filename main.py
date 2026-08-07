# main.py
"""
CLI Interactivo y Orquestador Principal para langTest.
Proporciona una interfaz rica en consola (Rich) con renderizado Markdown.
"""

import sys
import subprocess
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from rich.rule import Rule
from rich.table import Table

from config.config_loader import get_jira_credentials, get_llm_config
from tools.jira_tool import fetch_user_story_details
from modules.module_1_test_writer.agent import run_test_writer_agent

console = Console()

def show_banner():
    banner_text = """
 [bold cyan]QA AGENT SYSTEM[/bold cyan] - Motor Modular de Agentes de Automatización
 [dim]LangGraph • Playwright TypeScript • Jira REST API • Rich UI[/dim]
    """
    console.print(Panel(banner_text, title="🤖 QA Automation Suite", border_style="cyan", expand=False))

def menu_option_1_test_writer():
    console.print(Rule("[bold green]Módulo 1: Generador de Casos de Prueba Jira[/bold green]"))
    
    jira_key = Prompt.ask("[yellow]Ingresa el Issue Key de la User Story en Jira[/yellow]", default="PDNEU-1234")
    target_view = Prompt.ask("[yellow]Ingresa el nombre de la vista a probar[/yellow]", default="Prüfungsfeststellungen")
    
    console.print(f"\n[dim]Descargando detalles de [bold]{jira_key}[/bold] desde Jira...[/dim]")
    us_details = fetch_user_story_details(jira_key)
    
    table = Table(title=f"Detalles de Jira: {us_details.get('key')}", border_style="dim")
    table.add_column("Campo", style="cyan")
    table.add_column("Valor", style="white")
    table.add_row("Título", str(us_details.get("summary", "")))
    table.add_row("Descripción", str(us_details.get("description", ""))[:500] + "...")
    console.print(table)

    is_offline = us_details.get("is_offline", False)
    if is_offline:
        console.print("[bold yellow]ℹ️ Ejecutando en modo sin conexión / Mock data.[/bold yellow]")

    # Análisis y recomendaciones de referencias generadas por el LLM
    raw_us_text = f"Title: {us_details.get('summary', '')}\nDescription: {us_details.get('description', '')}"
    from modules.module_1_test_writer.agent import analyze_and_recommend_jira_references

    console.print("\n[dim]Analizando texto con el LLM para evaluar recomendaciones de referencias de Jira...[/dim]")
    recommended_refs = analyze_and_recommend_jira_references(raw_us_text, exclude_key=jira_key)
    selected_refs = []

    if recommended_refs:
        ref_table = Table(title="🤖 Recomendación del LLM: Referencias de Jira Sugeridas", border_style="yellow")
        ref_table.add_column("Issue Key", style="cyan", no_wrap=True)
        ref_table.add_column("Razón / Recomendación del LLM", style="white")

        for item in recommended_refs:
            ref_table.add_row(item.get("key", ""), item.get("reason", ""))

        console.print(ref_table)

        user_input_refs = Prompt.ask(
            "[yellow]¿Cuáles referencias deseas incluir en la generación del test? (Ingresa las claves separadas por coma, 'todas'/'all', o presiona Enter para ninguna)[/yellow]",
            default="todas"
        ).strip()

        all_keys = [item["key"] for item in recommended_refs]
        if user_input_refs.lower() in ["todas", "all", "t"]:
            selected_refs = all_keys
        elif user_input_refs:
            entered_list = [r.strip().upper() for r in user_input_refs.split(",") if r.strip()]
            selected_refs = [r if "-" in r else f"PDNEU-{r}" for r in entered_list]
            selected_refs = [r for r in selected_refs if r in all_keys or any(r == k for k in all_keys)]

        if selected_refs:
            console.print(f"[bold green]✓ Se tomarán en cuenta las siguientes referencias:[/bold green] {', '.join(selected_refs)}")

    if not Confirm.ask("¿Deseas iniciar la generación con LangGraph?", default=True):
        return

    console.print("\n[bold cyan]🚀 Iniciando ciclo de trabajo LangGraph (Writer -> Reviewer)...[/bold cyan]\n")

    def step_callback(node_name: str, content: str):
        if node_name == "writer":
            console.print(Panel(
                Markdown(content),
                title="📝 Writer Node Output",
                border_style="blue",
                expand=True
            ))
        elif node_name == "reviewer":
            console.print(Panel(
                Markdown(content),
                title="🔍 Reviewer Node Feedback",
                border_style="magenta",
                expand=True
            ))

    use_mock = Confirm.ask("¿Simular respuesta LLM (Modo Offline completo)?", default=False)
    mock_resp = None
    if use_mock:
        mock_resp = """```json
[
    {
        "step": 1,
        "action": "Navegar a la vista Prüfungsfeststellungen",
        "expectedResult": "La tabla de feststellungen es visible"
    },
    {
        "step": 2,
        "action": "Hacer clic en Agregar Feststellung",
        "expectedResult": "El diálogo modal se despliega"
    }
]
```"""

    try:
        result = run_test_writer_agent(
            jira_issue_key=jira_key,
            target_view=target_view,
            user_story_text=raw_us_text,
            selected_referenced_keys=selected_refs,
            on_step_callback=step_callback,
            mock_response=mock_resp
        )
        
        console.print("\n[bold green]✅ Proceso finalizado exitosamente.[/bold green]")
        if result.get("solution"):
            console.print(Panel(Markdown(f"### Resultado Final Aprobado:\n\n{result['solution']}"), title="🏆 Propuesta Final", border_style="green"))
    except Exception as e:
        console.print(f"[bold red]❌ Error durante la ejecución del agente:[/bold red] {e}")

def menu_option_2_repl_ts():
    console.print(Rule("[bold green]Módulo 2: Entorno TypeScript REPL & Playwright Runner[/bold green]"))
    repl_dir = Path(__file__).parent / "ts_repl_server"
    if not repl_dir.exists():
        console.print("[red]Directorio ts_repl_server no encontrado.[/red]")
        return

    console.print("[cyan]Servidor REPL de TypeScript detectado en `ts_repl_server/`.[/cyan]")
    console.print("  [bold white]1.[/bold white] 🖥️ Iniciar REPL Interactivo Aislado (Modo Usuario Humano)")
    console.print("  [bold white]2.[/bold white] 🤖 Probar Puente IPC de Agentes (`TSPlaywrightREPLBridge`)")

    sub_choice = Prompt.ask("\n[bold yellow]Selecciona una opción[/bold yellow]", choices=["1", "2"], default="1")

    if sub_choice == "1":
        console.print("\n[dim]Iniciando REPL en subproceso de consola interactiva...[/dim]\n")
        try:
            npx_cmd = "npx.cmd" if sys.platform == "win32" else "npx"
            subprocess.run([npx_cmd, "tsx", "./repl/repl.ts"], cwd=str(repl_dir))
        except Exception as e:
            console.print(f"[red]Error al iniciar REPL interactivo:[/red] {e}")
    elif sub_choice == "2":
        console.print("\n[dim]Iniciando prueba del puente IPC desde Python...[/dim]\n")
        from modules.module_2_browser_repl.ts_repl_bridge import TSPlaywrightREPLBridge
        bridge = TSPlaywrightREPLBridge()
        try:
            if bridge.start():
                console.print("[bold green]✓ Servidor REPL IPC iniciado y listo.[/bold green]")
                snippet = Prompt.ask(
                    "[yellow]Ingresa un código TypeScript para evaluar[/yellow]",
                    default="console.log('Hola desde el Agente Python'); await page.title();"
                )
                res = bridge.eval_code(snippet)
                console.print(Panel(json.dumps(res, indent=2, ensure_ascii=False), title="Respuesta del Servidor REPL", border_style="cyan"))
                bridge.stop()
            else:
                console.print("[bold red]❌ No se pudo conectar al servidor REPL IPC.[/bold red]")
        except Exception as e:
            console.print(f"[bold red]❌ Error al comunicarse con el REPL IPC:[/bold red] {e}")

def menu_option_3_test_coder():
    console.print(Rule("[bold green]Módulo 3: Conversor Codegen -> Test TypeScript[/bold green]"))
    console.print("[dim]Convierte la grabación de `npx playwright codegen` en tests robustos basados en POMs TypeScript.[/dim]")
    console.print("[yellow]Función en preparación para integración completa en la Fase 5.[/yellow]")

def menu_option_4_pom_generator():
    console.print(Rule("[bold green]Módulo 4: Generador de POMs TypeScript[/bold green]"))
    console.print("[dim]Analiza componentes web y genera plantillas POM TS en `shared_poms/` o `ts_repl_server/POM/`.[/dim]")
    console.print("[yellow]Función en preparación para integración completa en la Fase 4.[/yellow]")

def menu_option_5_run_tests():
    console.print(Rule("[bold green]Ejecución de Pruebas Unitarias Offline[/bold green]"))
    console.print("[dim]Ejecutando la suite de pruebas unitarias pytest sin conexión a internet...[/dim]\n")
    try:
        res = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"], capture_output=True, text=True)
        console.print(res.stdout)
        if res.returncode == 0:
            console.print("[bold green]🎉 Todas las pruebas unitarias pasaron correctamente.[/bold green]")
        else:
            console.print(res.stderr)
            console.print("[bold red]⚠️ Algunas pruebas presentaron fallos.[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Error al ejecutar pytest:[/bold red] {e}")

def menu_option_6_environment():
    console.print(Rule("[bold green]Estado del Entorno y Credenciales[/bold green]"))
    jira_cfg = get_jira_credentials()
    llm_cfg = get_llm_config()

    table = Table(title="Configuración Actual", border_style="cyan")
    table.add_column("Categoría", style="yellow")
    table.add_column("Propiedad", style="white")
    table.add_column("Valor", style="dim white")

    table.add_row("Jira API", "Base URL", jira_cfg["base_url"])
    table.add_row("Jira API", "Prefix", jira_cfg["prefix"])
    table.add_row("Jira API", "Usuario", jira_cfg["user"])
    table.add_row("LLM API", "Base URL", llm_cfg["apiBase"])
    table.add_row("LLM API", "Modelo Writer", llm_cfg["models"][0]["model"])

    console.print(table)

def main():
    show_banner()
    while True:
        console.print("\n[bold cyan]Selecciona una opción del menú:[/bold cyan]")
        console.print("  [bold white]1.[/bold white] 📝 Generar Casos de Prueba Jira (Módulo 1)")
        console.print("  [bold white]2.[/bold white] 💻 REPL TypeScript & Playwright (Módulo 2)")
        console.print("  [bold white]3.[/bold white] 🔄 Codegen -> Test TypeScript (Módulo 3)")
        console.print("  [bold white]4.[/bold white] 🏗️ Generador de POMs TypeScript (Módulo 4)")
        console.print("  [bold white]5.[/bold white] 🧪 Ejecutar Pruebas Unitarias (Offline Test Suite)")
        console.print("  [bold white]6.[/bold white] ⚙️ Verificar Entorno y Configuración")
        console.print("  [bold white]0.[/bold white] ❌ Salir")

        choice = Prompt.ask("\n[bold yellow]Opción[/bold yellow]", choices=["1", "2", "3", "4", "5", "6", "0"], default="1")

        if choice == "1":
            menu_option_1_test_writer()
        elif choice == "2":
            menu_option_2_repl_ts()
        elif choice == "3":
            menu_option_3_test_coder()
        elif choice == "4":
            menu_option_4_pom_generator()
        elif choice == "5":
            menu_option_5_run_tests()
        elif choice == "6":
            menu_option_6_environment()
        elif choice == "0":
            console.print("[cyan]¡Hasta luego![/cyan]")
            sys.exit(0)

if __name__ == "__main__":
    main()
