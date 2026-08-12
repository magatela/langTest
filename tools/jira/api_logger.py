# tools/jira/api_logger.py
"""
Módulo de Registro Detallado (Logging) de llamadas a las APIs de Jira y Xray.

Guarda un registro estructurado, legible y bien formateado de todas las peticiones HTTP
(método, URL, parámetros JQL, payload de entrada, código de respuesta HTTP, tiempo de ejecución,
total de resultados devueltos y claves de issues) en un archivo de log de texto.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from requests import Response
except ImportError:
    Response = Any  # type: ignore

logger = logging.getLogger(__name__)

# Ruta por defecto del archivo de log
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_FILE_PATH = LOG_DIR / "jira_api_calls.log"


def ensure_log_dir() -> Path:
    """Garantiza que el directorio de logs exista."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return LOG_FILE_PATH


def format_json_safely(data: Any, max_len: int = 1500) -> str:
    """Sanea y formatea un objeto JSON o string para visualización en log."""
    if data is None:
        return "None"
    if isinstance(data, (bytes, bytearray)):
        try:
            data = data.decode("utf-8")
        except Exception:
            return f"<binary data {len(data)} bytes>"

    if isinstance(data, str):
        try:
            parsed = json.loads(data)
            formatted = json.dumps(parsed, ensure_ascii=False, indent=2)
        except Exception:
            formatted = data
    else:
        try:
            formatted = json.dumps(data, ensure_ascii=False, indent=2)
        except Exception:
            formatted = str(data)

    if len(formatted) > max_len:
        return formatted[:max_len] + f"\n... [Truncado. Total {len(formatted)} caracteres]"
    return formatted


def log_api_call(
    method: str,
    url: str,
    status_code: Optional[int] = None,
    duration_sec: float = 0.0,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    request_body: Any = None,
    response: Optional[Any] = None,
    error: Optional[Exception] = None,
    log_file_path: Union[str, Path] = LOG_FILE_PATH,
) -> None:
    """
    Registra una llamada a la API REST de Jira o Xray en un archivo de log formateado.

    Args:
        method: Método HTTP ('GET', 'POST', 'PUT', 'DELETE').
        url: URL o endpoint invocado.
        status_code: Código de estado HTTP retornado (ej. 200, 400, 404, 500).
        duration_sec: Tiempo transcurrido en segundos.
        headers: Cabeceras HTTP enviadas.
        params: Parámetros de consulta (URL query parameters, ej. JQL).
        request_body: Payload o cuerpo enviado en la petición.
        response: Objeto Response de requests.
        error: Excepción ocurrida si la llamada falló a nivel de red/conexión.
        log_file_path: Ruta del archivo de texto log.
    """
    try:
        target_path = Path(log_file_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        status_str = f"{status_code}" if status_code is not None else "ERROR_CONEXION"
        
        # Extraer metadatos de respuesta JSON si están disponibles
        response_json: Optional[Dict[str, Any]] = None
        response_text: str = ""
        if response is not None:
            try:
                response_json = response.json()
                response_text = format_json_safely(response_json)
            except Exception:
                response_text = format_json_safely(getattr(response, "text", ""))

        # Extraer resumen de issues de Jira si es respuesta JQL o search
        jira_summary_lines: List[str] = []
        if response_json and isinstance(response_json, dict):
            total_issues = response_json.get("total")
            issues_list = response_json.get("issues", [])
            if total_issues is not None or issues_list:
                jira_summary_lines.append(f"  • Total Issues reportados por Jira : {total_issues}")
                jira_summary_lines.append(f"  • Cantidad devuelta en este lote : {len(issues_list)}")
                if issues_list:
                    keys = [issue.get("key", "N/A") for issue in issues_list[:10]]
                    key_str = ", ".join(keys)
                    if len(issues_list) > 10:
                        key_str += f", ... (+{len(issues_list)-10} más)"
                    jira_summary_lines.append(f"  • Keys de Issues devueltos         : [{key_str}]")

        summary_block = "\n".join(jira_summary_lines) if jira_summary_lines else "  • N/A"

        log_entry_lines = [
            "=" * 85,
            f"TIMESTAMP       : {timestamp_str}",
            f"MÉTODO HTTP     : {method.upper()}",
            f"URL TARGET      : {url}",
            f"CÓDIGO STATUS   : {status_str} (Tiempo de Respuesta: {duration_sec:.3f} s)",
        ]

        if params:
            log_entry_lines.append(f"PARÁMETROS QUERY: {json.dumps(params, ensure_ascii=False)}")

        if request_body:
            log_entry_lines.append("PAYLOAD SOLICITUD:")
            log_entry_lines.append(format_json_safely(request_body, max_len=800))

        if error:
            log_entry_lines.append("EXCEPCIÓN DE RED / CONEXIÓN:")
            log_entry_lines.append(f"  {type(error).__name__}: {str(error)}")

        log_entry_lines.append("RESUMEN DE RESULTADOS JIRA:")
        log_entry_lines.append(summary_block)

        if response_text:
            log_entry_lines.append("CUERPO DE RESPUESTA HTTP (PREVIEW):")
            log_entry_lines.append(response_text)

        log_entry_lines.append("=" * 85 + "\n")

        formatted_entry = "\n".join(log_entry_lines)

        with open(target_path, "a", encoding="utf-8") as f:
            f.write(formatted_entry)

    except Exception as e:
        logger.error("Error al escribir en el archivo de log API: %s", str(e))
