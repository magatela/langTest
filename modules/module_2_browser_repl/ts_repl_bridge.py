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

class TSPlaywrightREPLBridge:
    def __init__(self, server_dir: Optional[Path] = None):
        self.server_dir = server_dir or TS_REPL_SERVER_DIR
        self.process: Optional[subprocess.Popen] = None

    def start(self, timeout: int = 15) -> bool:
        """
        Inicia el servidor Node.js REPL en modo IPC (--ipc).
        """
        if self.process and self.process.poll() is None:
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
        """
        if not self.process or self.process.poll() is not None:
            if not self.start():
                return {"status": "error", "error": "No se pudo iniciar el proceso TS REPL"}

        req_id = str(uuid.uuid4())
        payload = {"action": action, "id": req_id, **kwargs}

        try:
            json_str = json.dumps(payload) + "\n"
            self.process.stdin.write(json_str)
            self.process.stdin.flush()

            response_line = self.process.stdout.readline()
            if not response_line:
                return {"status": "error", "error": "Proceso REPL finalizó inesperadamente"}

            return json.loads(response_line)
        except Exception as e:
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
