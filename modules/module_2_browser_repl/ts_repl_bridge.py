# modules/module_2_browser_repl/ts_repl_bridge.py
"""
Puente IPC para conectar los Agentes de Python con el servidor REPL de Playwright en TypeScript (Node.js).
"""

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
TS_REPL_SERVER_DIR = ROOT_DIR / "ts_repl_server"

# Instancia global compartida para gestionar la sesión del REPL
_GLOBAL_REPL_BRIDGE: Optional["TSPlaywrightREPLBridge"] = None

def get_repl_bridge(server_dir: Optional[Path] = None) -> "TSPlaywrightREPLBridge":
    """
    Obtiene la instancia global compartida del puente IPC con el REPL (Singleton).
    """
    global _GLOBAL_REPL_BRIDGE
    if _GLOBAL_REPL_BRIDGE is None:
        _GLOBAL_REPL_BRIDGE = TSPlaywrightREPLBridge(server_dir=server_dir)
    return _GLOBAL_REPL_BRIDGE

def reset_repl_bridge():
    """
    Resetea la instancia global del REPL.
    """
    global _GLOBAL_REPL_BRIDGE
    if _GLOBAL_REPL_BRIDGE is not None:
        _GLOBAL_REPL_BRIDGE.stop()
        _GLOBAL_REPL_BRIDGE = None

class TSPlaywrightREPLBridge:
    def __init__(self, server_dir: Optional[Path] = None):
        self.server_dir = server_dir or TS_REPL_SERVER_DIR
        self.process: Optional[subprocess.Popen] = None

    def is_running(self) -> bool:
        """
        Comprueba si el subproceso Node.js del REPL está en ejecución.
        """
        return self.process is not None and self.process.poll() is None

    def is_alive(self) -> bool:
        """
        Verifica si el servidor REPL y el navegador están vivos y respondiendo.
        Si la ventana fue cerrada por el usuario o el proceso finalizó, reinicia el estado interno.
        """
        if not self.is_running():
            return False
        try:
            req_id = str(uuid.uuid4())
            payload = json.dumps({"action": "eval", "id": req_id, "code": "1+1"}) + "\n"
            self.process.stdin.write(payload)
            self.process.stdin.flush()
            line = self.process.stdout.readline()
            if line:
                res = json.loads(line)
                if res.get("status") == "success":
                    return True
        except Exception:
            pass

        self.process = None
        return False

    def ensure_started(self, timeout: int = 15) -> bool:
        """
        Garantiza que el servidor REPL y el navegador estén abiertos y listos.
        Si están cerrados o no responden, los inicia o reinicia automáticamente.
        """
        if self.is_alive():
            return True
        return self.start(timeout=timeout)

    def start(self, timeout: int = 15) -> bool:
        """
        Inicia el servidor Node.js REPL en modo IPC (--ipc).
        """
        if self.is_running():
            return True

        if not self.server_dir.exists():
            raise FileNotFoundError(f"Directorio ts_repl_server no encontrado en: {self.server_dir}")

        cmd = ["npx.cmd" if sys.platform == "win32" else "npx", "tsx", "./repl/repl.ts", "--ipc"]
        
        env = os.environ.copy()
        env["REPL_MODE"] = "ipc"

        self.process = subprocess.Popen(
            cmd,
            cwd=str(self.server_dir),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env
        )

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

    def send_command(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Envía un comando JSON al proceso Node.js y espera la respuesta por stdout.
        Re-inicia el servidor automáticamente si se detecta que estaba cerrado.
        """
        if not self.ensure_started():
            return {"status": "error", "error": "No se pudo iniciar el proceso TS REPL"}

        req_id = str(uuid.uuid4())
        payload = {"action": action, "id": req_id, **kwargs}

        try:
            json_str = json.dumps(payload) + "\n"
            self.process.stdin.write(json_str)
            self.process.stdin.flush()

            response_line = self.process.stdout.readline()
            if not response_line:
                self.process = None
                return {"status": "error", "error": "Proceso REPL finalizó inesperadamente o el navegador fue cerrado."}

            return json.loads(response_line)
        except Exception as e:
            self.process = None
            return {"status": "error", "error": str(e)}

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
        """
        code = f"await page.locator({json.dumps(selector)}).ariaSnapshot();"
        return self.eval_code(code)

    def take_screenshot(self, path: Optional[str] = None) -> Dict[str, Any]:
        """
        Toma una captura de pantalla de la página activa mediante la sesión del REPL.
        """
        if path:
            escaped_path = path.replace("\\", "/")
            code = f"await page.screenshot({{ path: '{escaped_path}', fullPage: true }});"
        else:
            code = "await page.screenshot({ fullPage: true });"
        return self.eval_code(code)

    def stop(self):
        """
        Detiene la sesión del navegador y el servidor REPL.
        """
        if self.process and self.process.poll() is None:
            try:
                self.send_command("close")
            except Exception:
                pass
            self.process.terminate()
            self.process = None

