# modules/module_2_browser_repl/ts_repl_bridge.py
"""
Puente IPC para conectar los Agentes de Python con el servidor REPL de Playwright en TypeScript (Node.js).
Incluye gestión de procesos únicos, cola asíncrona de lectura, soporte de timeout de hasta 60s,
análisis de logs y diagnóstico inteligente de errores de Playwright para ajuste de comandos.
"""

import json
import os
import queue
import signal
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
TS_REPL_SERVER_DIR = ROOT_DIR / "ts_repl_server"

# Instancia global compartida para gestionar la sesión del REPL (Singleton Thread-Safe)
_GLOBAL_REPL_BRIDGE: Optional["TSPlaywrightREPLBridge"] = None
_GLOBAL_LOCK = threading.RLock()


def analyze_playwright_error(error_msg: str, code: str = "", stack: str = "") -> Dict[str, Any]:
    """
    Analiza el mensaje de error y stack trace devueltos por Playwright / REPL
    y genera un diagnóstico estructurado con sugerencias concretas para ajustar el comando.
    """
    err_lower = (error_msg or "").lower()
    stack_lower = (stack or "").lower()
    combined = f"{err_lower} {stack_lower}"

    analysis: Dict[str, Any] = {
        "error_type": "UNKNOWN_ERROR",
        "description": "Error no clasificado durante la ejecución en Playwright.",
        "suggested_actions": [],
        "relevant_code": code.strip() if code else None
    }

    if "timeout" in combined and ("exceeded" in combined or "waiting for" in combined or "locator" in combined or "waitfor" in combined):
        analysis["error_type"] = "LOCATOR_TIMEOUT"
        analysis["description"] = (
            "Playwright esperó hasta el tiempo límite pero el selector/locator no fue encontrado, "
            "no estuvo visible o la página no completó su navegación."
        )
        analysis["suggested_actions"] = [
            "Verificar si el selector/locator es exacto en la vista activa actual.",
            "Usar 'get_aria_snapshot()' o 'inspect_aria_snapshot()' para inspeccionar la jerarquía accesible y obtener roles o nombres vigentes.",
            "Esperar la estabilización de la red o carga previa con 'await page.waitForLoadState(\"networkidle\")'.",
            "Comprobar si el elemento reside dentro de un iframe ('page.frameLocator(...)') o en un modal/diálogo que debe abrirse primero."
        ]
    elif "strict mode violation" in combined or ("resolved to" in combined and "elements" in combined):
        analysis["error_type"] = "STRICT_MODE_VIOLATION"
        analysis["description"] = (
            "El locator utilizado resolvió a múltiples elementos en el DOM, violando la regla de unicidad en Playwright."
        )
        analysis["suggested_actions"] = [
            "Refinar el selector añadiendo atributos únicos (ej. data-testid, id o contexto contenedor).",
            "Usar '.first()', '.last()' o '.nth(indice)' para seleccionar una coincidencia explícita.",
            "Filtrar por contenido o texto con 'page.locator(sel).filter({ hasText: \"...\" })'."
        ]
    elif "intercepts pointer events" in combined or "is obscured" in combined:
        analysis["error_type"] = "ELEMENT_OBSCURED"
        analysis["description"] = (
            "El elemento no pudo recibir la acción de clic porque otro elemento (overlay, modal, spinner de carga o barra fija) lo tapa."
        )
        analysis["suggested_actions"] = [
            "Esperar a que el spinner u overlay desaparezca: 'await page.locator(\".loading-overlay\").waitFor({ state: \"detached\" })'.",
            "Hacer scroll explícito al elemento antes de la acción: 'await locator.scrollIntoViewIfNeeded()'.",
            "Si es seguro ignorar la superposición cosmética, utilizar clic forzado: 'await locator.click({ force: true })'."
        ]
    elif "not visible" in combined or "is hidden" in combined:
        analysis["error_type"] = "ELEMENT_HIDDEN"
        analysis["description"] = (
            "El elemento existe en el árbol DOM pero su estado es oculto ('display: none', 'visibility: hidden' o colapsado)."
        )
        analysis["suggested_actions"] = [
            "Esperar a que el elemento sea visible: 'await locator.waitFor({ state: \"visible\" })'.",
            "Comprobar si se requiere una acción previa (ej. desplegar un menú acordeón o pestaña) para mostrar el elemento."
        ]
    elif "target closed" in combined or ("closed" in combined and ("browser" in combined or "page" in combined or "context" in combined)):
        analysis["error_type"] = "BROWSER_OR_PAGE_CLOSED"
        analysis["description"] = (
            "La página, contexto o navegador fue cerrado inesperadamente durante la ejecución."
        )
        analysis["suggested_actions"] = [
            "El puente IPC reiniciará la sesión automáticamente en el siguiente comando.",
            "Verificar si el código ejecutó accidentalmente 'page.close()' o una navegación provocó el cierre de la ventana."
        ]
    elif "syntaxerror" in combined or "referenceerror" in combined or "typeerror" in combined or "is not defined" in combined:
        analysis["error_type"] = "JAVASCRIPT_EVAL_ERROR"
        analysis["description"] = (
            "Error de sintaxis, referencia o tipo en el código JavaScript/TypeScript evaluado."
        )
        analysis["suggested_actions"] = [
            "Revisar que las variables, métodos POM o utilidades referenciadas existan en el contexto global de ejecución.",
            "Comprobar la sintaxis de las promesas ('await') y el cierre correcto de bloques y funciones asíncronas."
        ]
    elif "assertion" in combined or "expect(" in combined:
        analysis["error_type"] = "ASSERTION_FAILURE"
        analysis["description"] = (
            "La aserción de Playwright ('expect(...)') falló porque el estado del elemento no coincidió con el valor esperado."
        )
        analysis["suggested_actions"] = [
            "Comparar el valor real con el esperado mediante logs intermedios o 'console.log()'.",
            "Verificar si el estado de la aplicación cambió antes de ejecutar la aserción."
        ]

    return analysis


def get_repl_bridge(server_dir: Optional[Path] = None) -> "TSPlaywrightREPLBridge":
    """
    Obtiene la instancia global compartida del puente IPC con el REPL (Singleton Thread-Safe).
    """
    global _GLOBAL_REPL_BRIDGE
    with _GLOBAL_LOCK:
        if _GLOBAL_REPL_BRIDGE is None:
            _GLOBAL_REPL_BRIDGE = TSPlaywrightREPLBridge(server_dir=server_dir)
        return _GLOBAL_REPL_BRIDGE


def reset_repl_bridge():
    """
    Resetea la instancia global del REPL.
    """
    global _GLOBAL_REPL_BRIDGE
    with _GLOBAL_LOCK:
        if _GLOBAL_REPL_BRIDGE is not None:
            _GLOBAL_REPL_BRIDGE.stop()
            _GLOBAL_REPL_BRIDGE = None


class TSPlaywrightREPLBridge:
    def __init__(self, server_dir: Optional[Path] = None):
        self.server_dir = server_dir or TS_REPL_SERVER_DIR
        self.process: Optional[subprocess.Popen] = None
        self._known_child_pids: List[int] = []
        self._stdout_queue: Optional[queue.Queue] = None
        self._reader_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()

    def is_running(self) -> bool:
        """
        Comprueba si el subproceso Node.js del REPL está en ejecución.
        """
        return self.process is not None and self.process.poll() is None

    def is_alive(self) -> bool:
        """
        Verifica si el servidor REPL está vivo.
        """
        return self.is_running()

    def _update_child_pids(self):
        """
        Actualiza la lista de PIDs de los subprocesos hijos activos.
        """
        if self.process and self.process.pid:
            try:
                parent = psutil.Process(self.process.pid)
                children = parent.children(recursive=True)
                self._known_child_pids = [c.pid for c in children]
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    def _kill_process_tree(self):
        """
        Mata recursivamente el proceso principal y todos sus procesos hijos (Playwright, Chromium, Node, etc.).
        Cierra explícitamente los descriptores de stdin, stdout y stderr.
        """
        if self.process is None:
            return

        pid = self.process.pid
        pids_to_kill = set()
        if pid:
            pids_to_kill.add(pid)

        # 1. Recolectar hijos activos actuales si el padre aún existe
        try:
            parent = psutil.Process(pid)
            for child in parent.children(recursive=True):
                pids_to_kill.add(child.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        # 2. Agregar hijos registrados previamente en _known_child_pids
        if self._known_child_pids:
            pids_to_kill.update(self._known_child_pids)

        # 3. Terminar todos los PIDs recolectados
        for p in list(pids_to_kill):
            try:
                proc = psutil.Process(p)
                proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # 4. Mecanismo de respaldo para Windows y Unix/macOS
        if sys.platform == "win32" and pid:
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=3
                )
            except Exception:
                pass
        elif sys.platform != "win32" and pid:
            try:
                pgid = os.getpgid(pid)
                os.killpg(pgid, signal.SIGKILL)
            except Exception:
                pass

        # Cerrar explícitamente descriptores de archivo
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            if stream:
                try:
                    stream.close()
                except Exception:
                    pass

        try:
            self.process.wait(timeout=1)
        except Exception:
            pass

        self._known_child_pids = []

    def _force_cleanup(self):
        """
        Fuerza la limpieza del proceso y sus recursos:
        1. Intenta enviar el comando IPC {"action": "close"} con timeout breve (2s).
        2. Invoca _kill_process_tree() para asegurar que no quede ningún proceso en memoria.
        3. Establece self.process = None y reinicia la cola de lectura.
        """
        if self.process is not None and self.process.poll() is None:
            try:
                req_id = str(uuid.uuid4())
                payload = json.dumps({"action": "close", "id": req_id}) + "\n"
                if self.process.stdin and not self.process.stdin.closed:
                    self.process.stdin.write(payload)
                    self.process.stdin.flush()
                self.process.wait(timeout=2.0)
            except Exception:
                pass

        self._kill_process_tree()
        self.process = None
        self._stdout_queue = None
        self._reader_thread = None

    def ensure_started(self, timeout: float = 15.0) -> bool:
        """
        Garantiza que el servidor REPL esté abierto y listo de forma atómica.
        """
        with self._lock:
            if self.is_running():
                return True
            return self._start_unlocked(timeout=timeout)

    def start(self, timeout: float = 15.0) -> bool:
        """
        Inicia el servidor Node.js REPL en modo IPC (--ipc).
        """
        with self._lock:
            return self._start_unlocked(timeout=timeout)

    def _start_unlocked(self, timeout: float = 15.0) -> bool:
        if self.is_running():
            return True

        # Asegurar limpieza previa antes de inicializar cualquier nuevo subproceso
        self._force_cleanup()

        if not self.server_dir.exists():
            raise FileNotFoundError(f"Directorio ts_repl_server no encontrado en: {self.server_dir}")

        cmd = ["npx.cmd" if sys.platform == "win32" else "npx", "tsx", "./repl/repl.ts", "--ipc"]
        
        env = os.environ.copy()
        env["REPL_MODE"] = "ipc"

        popen_kwargs: Dict[str, Any] = {
            "cwd": str(self.server_dir),
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
            "encoding": "utf-8",
            "env": env
        }

        # En sistemas Unix/macOS, aislar el grupo de procesos
        if sys.platform != "win32":
            popen_kwargs["preexec_fn"] = os.setsid

        self.process = subprocess.Popen(cmd, **popen_kwargs)
        self._stdout_queue = queue.Queue()

        def _enqueue_stdout(pipe, q: queue.Queue):
            try:
                for line in iter(pipe.readline, ''):
                    if line:
                        q.put(line)
                    else:
                        break
            except Exception:
                pass
            finally:
                try:
                    pipe.close()
                except Exception:
                    pass

        self._reader_thread = threading.Thread(
            target=_enqueue_stdout,
            args=(self.process.stdout, self._stdout_queue),
            daemon=True
        )
        self._reader_thread.start()

        # Esperar mensaje "ready" del servidor REPL
        start_time = time.time()
        ready = False
        while time.time() - start_time < timeout:
            if not self.is_running():
                break
            try:
                line = self._stdout_queue.get(timeout=0.5)
                trimmed = line.strip()
                if trimmed:
                    try:
                        data = json.loads(trimmed)
                        if data.get("event") == "ready":
                            ready = True
                            break
                    except json.JSONDecodeError:
                        pass
            except queue.Empty:
                continue

        if ready:
            self._update_child_pids()
            return True

        return self.is_running()


    def send_command(self, action: str, timeout: float = 60.0, retry: bool = True, **kwargs) -> Dict[str, Any]:
        """
        Envía un comando JSON al proceso Node.js y espera la respuesta por stdout.
        Espera hasta `timeout` segundos (por defecto 60s) para permitir operaciones lentas de Playwright.
        Captura logs de consola y diagnostica cualquier error para facilitar el ajuste del comando.
        """
        with self._lock:
            if not self.is_running():
                if not self._start_unlocked():
                    err_msg = "No se pudo iniciar el proceso TS REPL."
                    return {
                        "status": "error",
                        "error": err_msg,
                        "analysis": analyze_playwright_error(err_msg, str(kwargs.get("code", "")))
                    }

            req_id = str(uuid.uuid4())
            payload = {"action": action, "id": req_id, **kwargs}
            code_snippet = str(kwargs.get("code") or kwargs.get("filePath") or "")

            try:
                json_str = json.dumps(payload) + "\n"
                self.process.stdin.write(json_str)
                self.process.stdin.flush()

                collected_logs: List[str] = []
                response_data: Optional[Dict[str, Any]] = None
                start_time = time.time()

                # Esperar hasta `timeout` segundos por la respuesta JSON correspondiente
                while time.time() - start_time < timeout:
                    if not self.is_running():
                        raise IOError("El proceso REPL finalizó inesperadamente o el navegador fue cerrado durante la ejecución.")

                    try:
                        line = self._stdout_queue.get(timeout=0.5) if self._stdout_queue else None
                    except queue.Empty:
                        continue

                    if not line:
                        continue

                    trimmed_line = line.strip()
                    if not trimmed_line:
                        continue

                    # Deserializar respuesta JSON-RPC
                    try:
                        parsed = json.loads(trimmed_line)
                        if isinstance(parsed, dict) and parsed.get("id") == req_id:
                            response_data = parsed
                            break
                        elif isinstance(parsed, dict) and "event" in parsed:
                            continue
                        else:
                            collected_logs.append(trimmed_line)
                    except json.JSONDecodeError:
                        collected_logs.append(trimmed_line)

                if response_data is None:
                    timeout_err = f"Timeout de espera ({timeout}s) excedido para la acción '{action}'. Playwright no respondió a tiempo."
                    raise TimeoutError(timeout_err)

                # Combinar logs capturados con los devueltos internamente por el REPL
                if "logs" in response_data and isinstance(response_data["logs"], list):
                    response_data["logs"] = collected_logs + [l for l in response_data["logs"] if l not in collected_logs]
                elif collected_logs:
                    response_data["logs"] = collected_logs

                # Si hubo error en Playwright/Node, enriquecer con análisis diagnóstico
                if response_data.get("status") == "error":
                    error_msg = response_data.get("error", "Error desconocido en REPL")
                    stack = response_data.get("stack", "")
                    response_data["analysis"] = analyze_playwright_error(error_msg, code_snippet, stack)

                return response_data

            except Exception as e:
                err_str = str(e)
                # Auto-recuperación ante crash o interrupción si retry está activo
                if retry:
                    self._force_cleanup()
                    if self._start_unlocked():
                        return self.send_command(action, timeout=timeout, retry=False, **kwargs)

                self._force_cleanup()
                return {
                    "status": "error",
                    "error": f"Fallo en comunicación IPC con REPL: {err_str}",
                    "analysis": analyze_playwright_error(err_str, code_snippet)
                }

    def eval_code(self, code: str, timeout: float = 60.0) -> Dict[str, Any]:
        """
        Evalúa código TypeScript directo en la sesión activa de Playwright con soporte de timeout de hasta 60s.
        """
        return self.send_command("eval", timeout=timeout, code=code)

    def eval_file(self, file_path: str, timeout: float = 60.0) -> Dict[str, Any]:
        """
        Ejecuta un archivo .ts en el contexto de Playwright con soporte de timeout de hasta 60s.
        """
        return self.send_command("eval_file", timeout=timeout, filePath=file_path)

    def get_aria_snapshot(self, selector: str = "body", timeout: float = 60.0) -> Dict[str, Any]:
        """
        Obtiene el ARIA snapshot del selector indicado mediante la sesión activa del REPL.
        Soporta selectores CSS, roles de Playwright y atributos (ej. [data-role="..."] o data-role="...").
        """
        sel = (selector or "body").strip()
        # Normalizar automáticamente atributos del tipo data-role="val" o id="val" ingresados sin corchetes [...]
        if "=" in sel and not sel.startswith("[") and not sel.startswith("role=") and not sel.startswith("text=") and not sel.startswith("internal:"):
            sel = f"[{sel}]"

        code = f"return await page.locator({json.dumps(sel)}).ariaSnapshot();"
        return self.eval_code(code, timeout=timeout)

    def take_screenshot(self, path: Optional[str] = None, timeout: float = 60.0) -> Dict[str, Any]:
        """
        Toma una captura de pantalla de la página activa mediante la sesión del REPL.
        Retorna la ruta y el string en base64 de la imagen.
        """
        if path:
            escaped_path = path.replace("\\", "/")
            code = f"""
                const buf = await page.screenshot({{ path: '{escaped_path}', fullPage: true }});
                return buf.toString('base64');
            """
        else:
            code = """
                const buf = await page.screenshot({ fullPage: true });
                return buf.toString('base64');
            """
        res = self.eval_code(code, timeout=timeout)
        if res.get("status") == "success":
            return {
                "status": "success",
                "result": path or "screenshot_memory",
                "base64": res.get("result", ""),
                "logs": res.get("logs", [])
            }
        return res

    def stop(self):
        """
        Detiene la sesión del navegador y el servidor REPL asegurando limpieza total de procesos.
        """
        with self._lock:
            self._force_cleanup()



