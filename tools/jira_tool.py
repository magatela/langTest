# tools/jira_tool.py
"""
Módulo Unificado de Herramientas (Tools) para Integración de Jira y Xray.

Proporciona funciones estructuradas, deterministas y tipadas para que los agentes de IA
y la interfaz del sistema interactúen con la API REST de Jira Core y Xray Test Management.
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    from tools.jira.jira_api import JiraAPI
    from tools.jira.xray_api import XrayAPI
except ImportError:
    from jira.jira_api import JiraAPI
    from jira.xray_api import XrayAPI

from config.config_loader import get_jira_credentials

logger = logging.getLogger(__name__)

# ==============================================================================
# CONSTANTES DE CAMPOS PERSONALIZADOS (Jira / Xray Custom Fields)
# ==============================================================================
DEFAULT_PROJECT_KEY: str = "PDNEU"
CUSTOM_FIELD_BAUSTEIN: str = "customfield_10101"
CUSTOM_FIELD_TESTPLAN: str = "customfield_10213"
CUSTOM_FIELD_TESTSET: str = "customfield_10211"
CUSTOM_FIELD_STEPS_TABLE: str = "customfield_12521"
CUSTOM_FIELD_TEST_STEPS_RAW: str = "customfield_10208"
CUSTOM_FIELD_TEST_RUNS: str = "customfield_10219"
CUSTOM_FIELD_SYSTEM_ENV: str = "customfield_20003"
CUSTOM_FIELD_RETEST: str = "customfield_10106"

DEFAULT_FIX_VERSIONS: List[Dict[str, str]] = [
    {"name": "1.0 KapG"},
    {"name": "2.0 EinzelU"},
    {"name": "3.0 PersG"},
]
DEFAULT_COMPONENTS: List[Dict[str, str]] = [{"name": "TP8QS"}]
DEFAULT_ASSIGNEE: Dict[str, str] = {"name": "user@email.de"}


# ==============================================================================
# GESTIÓN Y LAZY INITIALIZATION DE CLIENTES API
# ==============================================================================
_jira_client_instance: Optional[JiraAPI] = None
_xray_client_instance: Optional[XrayAPI] = None


def get_jira_client() -> JiraAPI:
    """
    Inicialización perezosa (Lazy initialization) del cliente JiraAPI.
    Carga credenciales dinámicamente sin fallar en caso de falta de configuración.

    Returns:
        JiraAPI: Instancia configurada del cliente de Jira.
    """
    global _jira_client_instance
    if _jira_client_instance is None:
        creds = get_jira_credentials()
        _jira_client_instance = JiraAPI(
            base_url=creds.get("base_url", "https://jira.example.com/"),
            prefix=creds.get("prefix", DEFAULT_PROJECT_KEY),
            user=creds.get("user", ""),
            password=creds.get("password", ""),
        )
        if creds.get("proxies"):
            _jira_client_instance.set_proxies(creds["proxies"])
    return _jira_client_instance


def get_xray_client() -> XrayAPI:
    """
    Inicialización perezosa (Lazy initialization) del cliente XrayAPI.

    Returns:
        XrayAPI: Instancia configurada del cliente de Xray.
    """
    global _xray_client_instance
    if _xray_client_instance is None:
        creds = get_jira_credentials()
        _xray_client_instance = XrayAPI(
            base_url=creds.get("base_url", "https://jira.example.com/"),
            prefix=creds.get("prefix", DEFAULT_PROJECT_KEY),
            user=creds.get("user", ""),
            password=creds.get("password", ""),
        )
        if creds.get("proxies"):
            _xray_client_instance.set_proxies(creds["proxies"])
    return _xray_client_instance


# ==============================================================================
# FUNCIONES AUXILIARES DE UTILIDAD
# ==============================================================================
def normalize_issue_key(key: Union[str, int], prefix: str = DEFAULT_PROJECT_KEY) -> str:
    """
    Formatea y normaliza una clave de Jira para garantizar que contenga el prefijo correcto.

    Args:
        key: ID o Clave del Issue (ej. '1234' o 'PDNEU-1234' o 'QA-99').
        prefix: Prefijo por defecto del proyecto en Jira.

    Returns:
        str: Clave normalizada (ej. 'PDNEU-1234' o 'QA-99').
    """
    str_key = str(key).strip()
    if "-" in str_key:
        return str_key
    return f"{prefix}-{str_key}"


def clean_formatting_text(text: str) -> str:
    """
    Elimina caracteres especiales de formato Wiki de Jira de un texto.

    Args:
        text: Texto con formato Wiki o tags como {code}.

    Returns:
        str: Texto limpio.
    """
    if not text:
        return ""
    return re.sub(r"\{[^}]*\}", "", text).strip()


# ==============================================================================
# HERRAMIENTAS AUTÓNOMAS (TOOLS)
# ==============================================================================
def fetch_user_story_details(
    issue_key: str, mock_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Tool: Descarga la información clave de una User Story en Jira (título, descripción, criterios de aceptación).

    Args:
        issue_key (str): Clave del Issue en Jira (ej. 'PDNEU-1234' o '1234').
        mock_data (Optional[Dict[str, Any]]): Datos simulados opcionales para pruebas offline.

    Returns:
        Dict[str, Any]: Estructura dict con el resultado de la consulta.
            Status "success" contiene claves: key, summary, description, priority, status, raw.
            Status "error" contiene claves: status, message, error_details.
    """
    if mock_data:
        return {
            "status": "success",
            "key": mock_data.get("key", issue_key),
            "summary": mock_data.get("summary", ""),
            "description": mock_data.get("description", ""),
            "priority": mock_data.get("priority", "Medium"),
            "issue_status": mock_data.get("status", "Open"),
            "raw": mock_data,
        }

    try:
        jira = get_jira_client()
        norm_key = normalize_issue_key(issue_key, jira._prefix)
        response = jira.get_issue_info(norm_key)

        if response.status_code == 200:
            data = response.json()
            fields = data.get("fields", {})
            return {
                "status": "success",
                "key": data.get("key", norm_key),
                "summary": fields.get("summary", ""),
                "description": fields.get("description", ""),
                "priority": fields.get("priority", {}).get("name", "Medium"),
                "issue_status": fields.get("status", {}).get("name", "Open"),
                "raw": data,
            }
        else:
            return {
                "status": "error",
                "message": f"Error HTTP {response.status_code} al consultar Jira",
                "key": norm_key,
                "summary": f"User Story {norm_key} (Sin conexión a Jira)",
                "description": "Modo seguro: No se pudo obtener la descripción original.",
            }
    except Exception as e:
        logger.error("Excepción en fetch_user_story_details: %s", str(e))
        return {
            "status": "error",
            "message": str(e),
            "key": issue_key,
            "summary": f"User Story {issue_key} (Error de Conexión)",
            "description": f"No se pudo completar la solicitud HTTP. Detalles: {str(e)}",
            "is_offline": True,
        }


def update_test_description(
    user_story_id: Union[str, int],
    test_case_id: Union[str, int],
    testplan_id: Union[str, int],
    sprint_id: Union[str, int],
) -> Dict[str, Any]:
    """
    Tool: Actualiza la descripción, campos requeridos y versión de fijación de un Test Case en Jira
    vinculándolo a una User Story y un Test Plan.

    Args:
        user_story_id (Union[str, int]): ID o Clave de la US origen.
        test_case_id (Union[str, int]): ID o Clave del Caso de Prueba a actualizar.
        testplan_id (Union[str, int]): ID del Plan de Pruebas.
        sprint_id (Union[str, int]): Número o identificador del Sprint.

    Returns:
        Dict[str, Any]: Resultado dict con estado de la operación.
    """
    try:
        jira = get_jira_client()
        us_key = normalize_issue_key(user_story_id, jira._prefix)
        tc_key = normalize_issue_key(test_case_id, jira._prefix)
        tp_key = normalize_issue_key(testplan_id, jira._prefix)

        us_resp = jira.get_issue_info(us_key)
        if not us_resp.ok:
            return {
                "status": "error",
                "message": f"No se encontró la User Story {us_key}",
            }

        us_data = us_resp.json()
        us_fields = us_data.get("fields", {})
        description = us_fields.get("description", "")

        labels = list(us_fields.get("labels", []))
        if "TP8QS" not in labels:
            labels.append("TP8QS")
        sprint_label = f"Sprint_{sprint_id}"
        if sprint_label not in labels:
            labels.append(sprint_label)

        new_description = f"Verweise:\n# {us_key}\n# {description}"
        priority_id = us_fields.get("priority", {}).get("id", "3")
        baustein = us_fields.get(CUSTOM_FIELD_BAUSTEIN)

        update_payload = {
            "fields": {
                "summary": f"TC-STORY-{user_story_id}:{us_fields.get('summary', '')}",
                "description": new_description,
                "priority": {"id": priority_id},
                "fixVersions": DEFAULT_FIX_VERSIONS,
                "assignee": DEFAULT_ASSIGNEE,
                "labels": labels,
                "components": DEFAULT_COMPONENTS,
                CUSTOM_FIELD_BAUSTEIN: baustein,
                CUSTOM_FIELD_TESTPLAN: ["PDNEU-653", tp_key],
            }
        }

        update_resp = jira.update_issue(tc_key, update_payload)
        if update_resp.ok:
            return {
                "status": "success",
                "message": f"Test Case {tc_key} actualizado correctamente",
                "test_case_key": tc_key,
                "new_description": new_description,
            }
        else:
            return {
                "status": "error",
                "message": f"Error HTTP {update_resp.status_code} al actualizar {tc_key}",
                "details": update_resp.text,
            }
    except Exception as e:
        logger.error("Excepción en update_test_description: %s", str(e))
        return {"status": "error", "message": str(e)}


def publish_test_case_to_jira(
    user_story_id: str, test_case_id: str, testplan_id: str, sprint_id: str
) -> Dict[str, Any]:
    """
    Tool: Publica y sincroniza un Caso de Prueba con su Historia de Usuario en Jira.

    Args:
        user_story_id (str): ID de la US en Jira.
        test_case_id (str): ID del Caso de Prueba.
        testplan_id (str): ID del Test Plan.
        sprint_id (str): Número del Sprint.

    Returns:
        Dict[str, Any]: Resultado dict con estado y detalles de ejecución.
    """
    return update_test_description(user_story_id, test_case_id, testplan_id, sprint_id)


def get_fach_test_keys(user_story_data: Dict[str, Any]) -> List[str]:
    """
    Extrae los identificadores de Fach Test (FT) vinculados a una User Story.

    Args:
        user_story_data (Dict[str, Any]): Datos JSON completos del Issue de la US.

    Returns:
        List[str]: Lista de Issue Keys de los Fach Tests encontrados.
    """
    list_ft: List[str] = []
    issuelinks = user_story_data.get("fields", {}).get("issuelinks", [])
    for link in issuelinks:
        content = link.get("outwardIssue")
        if content:
            fields = content.get("fields", {})
            name = fields.get("summary", "")
            if name.startswith("FT"):
                key = content.get("key")
                if key:
                    list_ft.append(key)
    return list_ft


def get_test_steps_from_case(test_case_id: Union[str, int]) -> Dict[str, Any]:
    """
    Tool: Obtiene los pasos de prueba estructurados de un Test Case o Fach Test.

    Args:
        test_case_id (Union[str, int]): ID o Clave del Test Case en Jira.

    Returns:
        Dict[str, Any]: Estructura con la lista de pasos formateados (Action, Data, Expected Result).
    """
    try:
        jira = get_jira_client()
        norm_key = normalize_issue_key(test_case_id, jira._prefix)
        resp = jira.get_issue_info(norm_key)

        if not resp.ok:
            return {
                "status": "error",
                "message": f"No se pudo consultar el Test Case {norm_key}",
            }

        data = resp.json()
        custom_steps = (
            data.get("fields", {})
            .get(CUSTOM_FIELD_STEPS_TABLE, {})
            .get("steps", [])
        )

        formatted_steps: List[Dict[str, str]] = []
        for item in custom_steps:
            item_fields = item.get("fields", {})
            formatted_steps.append({
                "step": clean_formatting_text(item_fields.get("Action", "")),
                "data": clean_formatting_text(item_fields.get("Data", "")),
                "result": clean_formatting_text(item_fields.get("Expected Result", "")),
            })

        return {
            "status": "success",
            "test_case_key": norm_key,
            "steps": formatted_steps,
        }
    except Exception as e:
        logger.error("Excepción en get_test_steps_from_case: %s", str(e))
        return {"status": "error", "message": str(e)}


def delete_all_test_steps(test_case_id: Union[str, int]) -> Dict[str, Any]:
    """
    Tool: Elimina todos los pasos de prueba de un Test Case en Xray.

    Args:
        test_case_id (Union[str, int]): ID o Clave del Caso de Prueba.

    Returns:
        Dict[str, Any]: Estado del proceso y resumen de eliminación.
    """
    try:
        xray = get_xray_client()
        norm_key = normalize_issue_key(test_case_id, xray._prefix)
        resp = xray.get_test_steps(norm_key)

        if not resp.ok:
            return {
                "status": "error",
                "message": f"No se pudieron obtener los pasos del Test Case {norm_key}",
            }

        steps_data = resp.json()
        deleted_count = 0
        for step in steps_data.get("steps", []):
            step_id = step.get("id")
            if step_id:
                del_resp = xray.delete_step(norm_key, step_id)
                if del_resp.ok:
                    deleted_count += 1

        return {
            "status": "success",
            "message": f"Se eliminaron {deleted_count} pasos del Test Case {norm_key}",
            "deleted_count": deleted_count,
        }
    except Exception as e:
        logger.error("Excepción en delete_all_test_steps: %s", str(e))
        return {"status": "error", "message": str(e)}


def add_test_steps(
    test_case_id: Union[str, int], steps: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Tool: Agrega una lista de pasos de prueba a un Test Case existente en Xray.

    Args:
        test_case_id (Union[str, int]): ID del Caso de Prueba.
        steps (List[Dict[str, Any]]): Lista de diccionarios con la definición del paso.

    Returns:
        Dict[str, Any]: Estado de adición y cantidad de pasos agregados.
    """
    try:
        xray = get_xray_client()
        norm_key = normalize_issue_key(test_case_id, xray._prefix)
        added_count = 0

        for idx, step_info in enumerate(steps):
            payload = step_info.get("fields", step_info)
            resp = xray.add_test_step(norm_key, payload)
            if resp.ok:
                added_count += 1

        return {
            "status": "success",
            "message": f"Se agregaron {added_count} pasos a {norm_key}",
            "added_count": added_count,
        }
    except Exception as e:
        logger.error("Excepción en add_test_steps: %s", str(e))
        return {"status": "error", "message": str(e)}


def create_test_case(
    user_story_id: Union[str, int],
    sprint_id: Union[str, int],
    testplan_id: Union[str, int],
    steps_data: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Tool: Crea un nuevo Caso de Prueba en Jira vinculado a una User Story y le asigna sus pasos en Xray.

    Args:
        user_story_id (Union[str, int]): ID de la US en Jira.
        sprint_id (Union[str, int]): Identificador del Sprint.
        testplan_id (Union[str, int]): ID del Test Plan asociable.
        steps_data (Optional[List[Dict[str, Any]]]): Pasos opcionales a insertar en el test creado.

    Returns:
        Dict[str, Any]: Clave del Test Case creado y resultado de la vinculación.
    """
    try:
        jira = get_jira_client()
        us_key = normalize_issue_key(user_story_id, jira._prefix)
        tp_key = normalize_issue_key(testplan_id, jira._prefix)

        us_resp = jira.get_issue_info(us_key)
        if not us_resp.ok:
            return {
                "status": "error",
                "message": f"No se encontró la User Story {us_key}",
            }

        us_data = us_resp.json()
        us_fields = us_data.get("fields", {})

        labels = list(us_fields.get("labels", []))
        if "TP8QS" not in labels:
            labels.append("TP8QS")
        labels.append(f"Sprint_{sprint_id}")

        description = us_fields.get("description", "")
        test_description = f"Verweise:\n# {us_key}\n# {description}"

        new_test_payload = {
            "fields": {
                "project": {"key": jira._prefix},
                "summary": f"TC-STORY-{user_story_id}:{us_fields.get('summary', '')}",
                "description": test_description,
                "issuetype": {"name": "Test"},
                "priority": {"id": us_fields.get("priority", {}).get("id", "3")},
                "fixVersions": DEFAULT_FIX_VERSIONS,
                "assignee": DEFAULT_ASSIGNEE,
                "labels": labels,
                "components": DEFAULT_COMPONENTS,
                CUSTOM_FIELD_BAUSTEIN: us_fields.get(CUSTOM_FIELD_BAUSTEIN),
                CUSTOM_FIELD_TESTPLAN: ["PDNEU-653", tp_key],
                CUSTOM_FIELD_TESTSET: ["PDNEU-12461"],
            }
        }

        create_resp = jira.create_issue(new_test_payload)
        if not create_resp.ok:
            return {
                "status": "error",
                "message": f"Error al crear Test Case: HTTP {create_resp.status_code}",
                "details": create_resp.text,
            }

        created_data = create_resp.json()
        tc_key = created_data.get("key", "")

        # Insertar pasos si fueron provistos
        if steps_data and tc_key:
            add_test_steps(tc_key, steps_data)

        # Vincular con la US
        link_payload = {
            "type": {"name": "Befund"},
            "inwardIssue": {"key": us_data.get("key", us_key)},
            "outwardIssue": {"key": tc_key},
        }
        jira.set_issuelink(link_payload)

        return {
            "status": "success",
            "message": f"Caso de prueba {tc_key} creado y vinculado exitosamente",
            "test_case_key": tc_key,
        }
    except Exception as e:
        logger.error("Excepción en create_test_case: %s", str(e))
        return {"status": "error", "message": str(e)}


def upload_execution_results(
    test_execution_id: Union[str, int],
    test_id: Union[str, int],
    results_filepath: Optional[str] = None,
    results_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Tool: Carga los resultados de ejecución de una prueba en Xray (vía archivo JSON o payload directo).

    Args:
        test_execution_id (Union[str, int]): ID de la Ejecución del Test.
        test_id (Union[str, int]): ID del Caso de Prueba.
        results_filepath (Optional[str]): Ruta al archivo JSON con las evidencias/resultados.
        results_payload (Optional[Dict[str, Any]]): Payload de resultados directo.

    Returns:
        Dict[str, Any]: Resultado dict de la subida a Xray API.
    """
    try:
        xray = get_xray_client()
        exec_key = normalize_issue_key(test_execution_id, xray._prefix)

        raw_results = results_payload
        if not raw_results and results_filepath:
            file_path = Path(results_filepath)
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_results = json.loads(f.read())
            else:
                return {
                    "status": "error",
                    "message": f"Archivo de resultados no encontrado: {results_filepath}",
                }

        if not raw_results:
            return {
                "status": "error",
                "message": "Se requiere proporcionar results_filepath o results_payload",
            }

        payload = {
            "testExecutionKey": exec_key,
            "tests": [raw_results] if isinstance(raw_results, dict) else raw_results,
        }

        resp = xray.upload_results(payload)
        if resp.ok:
            return {
                "status": "success",
                "message": f"Resultados subidos correctamente a {exec_key}",
                "response": resp.json() if resp.text else {},
            }
        else:
            return {
                "status": "error",
                "message": f"Error HTTP {resp.status_code} al subir resultados",
                "details": resp.text,
            }
    except Exception as e:
        logger.error("Excepción en upload_execution_results: %s", str(e))
        return {"status": "error", "message": str(e)}


def set_issue_link(
    inward_issue: Union[str, int],
    outward_issue: Union[str, int],
    link_type: str = "Befund",
) -> Dict[str, Any]:
    """
    Tool: Establece un enlace entre dos Issues en Jira.

    Args:
        inward_issue (Union[str, int]): Issue de origen/origen (ej. US).
        outward_issue (Union[str, int]): Issue de destino/relacionado (ej. Bug, Test).
        link_type (str): Nombre del tipo de enlace.

    Returns:
        Dict[str, Any]: Resultado dict de la creación del enlace.
    """
    try:
        jira = get_jira_client()
        in_key = normalize_issue_key(inward_issue, jira._prefix)
        out_key = normalize_issue_key(outward_issue, jira._prefix)

        payload = {
            "type": {"name": link_type},
            "inwardIssue": {"key": in_key},
            "outwardIssue": {"key": out_key},
        }

        resp = jira.set_issuelink(payload)
        if resp.ok:
            return {
                "status": "success",
                "message": f"Enlace {link_type} creado entre {in_key} y {out_key}",
            }
        else:
            return {
                "status": "error",
                "message": f"Error HTTP {resp.status_code} al crear enlace",
            }
    except Exception as e:
        logger.error("Excepción en set_issue_link: %s", str(e))
        return {"status": "error", "message": str(e)}


def create_bug_report(
    test_execution_id: Union[str, int],
    pdgo_version: str,
    sprint_id: Union[str, int],
) -> Dict[str, Any]:
    """
    Tool: Genera un reporte de Bug en Jira a partir de una Ejecución de Test de Xray fallida.

    Args:
        test_execution_id (Union[str, int]): ID de la ejecución de test.
        pdgo_version (str): Versión de la aplicación en prueba.
        sprint_id (Union[str, int]): Número del Sprint.

    Returns:
        Dict[str, Any]: Datos del Bug creado (bug_key, story_key, test_key).
    """
    try:
        jira = get_jira_client()
        exec_key = normalize_issue_key(test_execution_id, jira._prefix)

        exec_resp = jira.get_issue_info(exec_key)
        if not exec_resp.ok:
            return {
                "status": "error",
                "message": f"No se encontró la ejecución {exec_key}",
            }

        exec_data = exec_resp.json()
        runs_field = exec_data.get("fields", {}).get(CUSTOM_FIELD_TEST_RUNS, [])
        if not runs_field:
            return {
                "status": "error",
                "message": f"No hay tests asociados a la ejecución {exec_key}",
            }

        test_key = runs_field[0].get("testKey", "")

        tc_resp = jira.get_issue_info(test_key)
        tc_data = tc_resp.json() if tc_resp.ok else {}
        tc_fields = tc_data.get("fields", {})

        labels = [
            lbl for lbl in tc_fields.get("labels", [])
            if not str(lbl).lower().startswith("sprint")
        ]
        labels.append(f"Sprint_{sprint_id}")

        summary_text = tc_fields.get("summary", "")
        match_re = re.search(r"TC-([A-Z]+-\d+):.+", summary_text)
        story_key = match_re.group(1).replace("STORY-", "") if match_re else exec_key
        story_key = normalize_issue_key(story_key, jira._prefix)

        bug_payload = {
            "fields": {
                "project": {"key": jira._prefix},
                "summary": f"BG-STORY-{story_key}: Defecto detectado en {test_key}",
                "issuetype": {"name": "Bug"},
                "priority": {"id": tc_fields.get("priority", {}).get("id", "3")},
                "fixVersions": DEFAULT_FIX_VERSIONS,
                "versions": [{"name": f"PD-Go 1.{pdgo_version}"}],
                "assignee": DEFAULT_ASSIGNEE,
                "labels": labels,
                "components": DEFAULT_COMPONENTS,
                CUSTOM_FIELD_BAUSTEIN: tc_fields.get(CUSTOM_FIELD_BAUSTEIN),
                CUSTOM_FIELD_SYSTEM_ENV: {"id": "520538"},
            }
        }

        bug_resp = jira.create_issue(bug_payload)
        if not bug_resp.ok:
            return {
                "status": "error",
                "message": f"Error al crear Bug: HTTP {bug_resp.status_code}",
            }

        bug_data = bug_resp.json()
        bug_key = bug_data.get("key", "")

        # Enlazar Bug con la US, Test y Test Execution
        set_issue_link(story_key, bug_key)
        set_issue_link(test_key, bug_key)
        set_issue_link(exec_key, bug_key)

        return {
            "status": "success",
            "bug_key": bug_key,
            "test_execution_key": exec_key,
            "test_key": test_key,
            "user_story_key": story_key,
        }
    except Exception as e:
        logger.error("Excepción en create_bug_report: %s", str(e))
        return {"status": "error", "message": str(e)}
