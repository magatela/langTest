# modules/module_2_browser_repl/ts_repl_bridge.py
"""
Puente IPC para conectar los Agentes de Python con el servidor REPL de Playwright en TypeScript (Node.js).
Incluye gestión de procesos únicos, limpieza de procesos huérfanos y auto-recuperación ante fallos.
"""

import json
import os
import signal
import subprocess
import sys
import threading
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import psutil

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
TS_REPL_SERVER_DIR = ROOT_DIR / "ts_repl_server"

# Instancia global compartida para gestionar la sesión del REPL (Singleton Thread-Safe)
_GLOBAL_REPL_BRIDGE: Optional["TSPlaywrightREPLBridge"] = None
_GLOBAL_LOCK = threading.RLock()

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

    def _kill_process_tree(self):
        """
        Mata recursivamente el proceso principal y todos sus procesos hijos (Playwright, Chromium, Node, etc.).
        Cierra explícitamente los descriptores de stdin, stdout y stderr.
        """
        if self.process is None:
            return

        pid = self.process.pid

        # 1. Intentar matar el árbol de procesos con psutil
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            for child in children:
                try:
                    child.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            try:
                parent.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

            # Esperar a que terminen
            _, alive = psutil.wait_procs(children + [parent], timeout=1.5)
            for p in alive:
                try:
                    p.kill()
                except Exception:
                    pass
        except Exception:
            # Mecanismo de respaldo para Windows y Unix/macOS si psutil falla
            try:
                if sys.platform == "win32":
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(pid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=3
                    )
                else:
                    try:
                        pgid = os.getpgid(pid)
                        os.killpg(pgid, signal.SIGKILL)
                    except Exception:
                        os.kill(pid, signal.SIGKILL)
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

    def _force_cleanup(self):
        """
        Fuerza la limpieza del proceso y sus recursos:
        1. Intenta enviar el comando IPC {"action": "close"} con timeout breve (2s).
        2. Invoca _kill_process_tree() para asegurar que no quede ningún proceso en memoria.
        3. Establece self.process = None.
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

    def ensure_started(self, timeout: int = 15) -> bool:
        """
        Garantiza que el servidor REPL esté abierto y listo de forma atómica.
        """
        with self._lock:
            if self.is_running():
                return True
            return self._start_unlocked(timeout=timeout)

    def start(self, timeout: int = 15) -> bool:
        """
        Inicia el servidor Node.js REPL en modo IPC (--ipc).
        """
        with self._lock:
            return self._start_unlocked(timeout=timeout)

    def _start_unlocked(self, timeout: int = 15) -> bool:
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

        # Esperar mensaje de inicio del servidor REPL
        try:
            line = self.process.stdout.readline()
            if line:
                data = json.loads(line)
                if data.get("event") == "ready":
                    return True
        except Exception:
            pass

        return self.process.poll() is None

    def send_command(self, action: str, retry: bool = True, **kwargs) -> Dict[str, Any]:
        """
        Envía un comando JSON al proceso Node.js y espera la respuesta por stdout.
        Re-inicia el servidor automáticamente si se detecta que estaba cerrado.
        En caso de error inesperado o caída del proceso, limpia, reinicia y reintenta exactamente una vez.
        """
        with self._lock:
            if not self.is_running():
                if not self._start_unlocked():
                    return {"status": "error", "error": "No se pudo iniciar el proceso TS REPL"}

            req_id = str(uuid.uuid4())
            payload = {"action": action, "id": req_id, **kwargs}

            try:
                json_str = json.dumps(payload) + "\n"
                self.process.stdin.write(json_str)
                self.process.stdin.flush()
                response_line = self.process.stdout.readline()
                if not response_line:
                    raise IOError("Fin de archivo (EOF) inesperado o proceso REPL finalizado prematuramente.")
                return json.loads(response_line)
            except Exception as e:
                # Auto-recuperación: limpia, arranca nueva sesión y reintenta una sola vez
                if retry:
                    self._force_cleanup()
                    if self._start_unlocked():
                        return self.send_command(action, retry=False, **kwargs)

                self._force_cleanup()
                return {"status": "error", "error": f"Fallo en comunicación IPC con REPL: {str(e)}"}

    def eval_code(self, code: str) -> Dict[str, Any]:
        """
        Evalúa código TypeScript directo en la sesión activa de Playwright.
        """
        return self.send_command("eval", code=code)

    def eval_file(self, file_path: str) -> Dict[str, Any]:
        """
        Ejecuta un archivo .ts en el contexto de Playwright.
        """
        return self.send_command("eval_file", filePath=file_path)

    def get_aria_snapshot(self, selector: str = "body") -> Dict[str, Any]:
        """
        Obtiene el ARIA snapshot del selector indicado mediante la sesión activa del REPL.
        Soporta selectores CSS, roles de Playwright y atributos (ej. [data-role="..."] o data-role="...").
        """
        sel = (selector or "body").strip()
        # Normalizar automáticamente atributos del tipo data-role="val" o id="val" ingresados sin corchetes [...]
        if "=" in sel and not sel.startswith("[") and not sel.startswith("role=") and not sel.startswith("text=") and not sel.startswith("internal:"):
            sel = f"[{sel}]"

        code = f"return await page.locator({json.dumps(sel)}).ariaSnapshot();"
        return self.eval_code(code)

    def take_screenshot(self, path: Optional[str] = None) -> Dict[str, Any]:
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
        res = self.eval_code(code)
        if res.get("status") == "success":
            return {
                "status": "success",
                "result": path or "screenshot_memory",
                "base64": res.get("result", "")
            }
        return res

    def stop(self):
        """
        Detiene la sesión del navegador y el servidor REPL asegurando limpieza total de procesos.
        """
        with self._lock:
            self._force_cleanup()


