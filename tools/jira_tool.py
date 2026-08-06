# tools/jira_tool.py
"""
Herramientas reutilizables para interacción con Jira y Xray.
"""

from typing import Dict, Any, Optional
from tools.jira.jiraWorker import jira, xray, updateTestDescription

def fetch_user_story_details(issue_key: str, mock_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Descarga la información clave de una User Story en Jira (título, descripción, criterios).
    Si mock_data está presente o si no hay conexión a Jira, devuelve datos simulados.
    """
    if mock_data:
        return mock_data
        
    try:
        response = jira.get_issue_info(issue_key)
        if response.status_code == 200:
            data = response.json()
            fields = data.get("fields", {})
            return {
                "key": data.get("key", issue_key),
                "summary": fields.get("summary", ""),
                "description": fields.get("description", ""),
                "priority": fields.get("priority", {}).get("name", "Medium"),
                "status": fields.get("status", {}).get("name", "Open"),
                "raw": data
            }
        else:
            return {
                "key": issue_key,
                "summary": f"User Story {issue_key} (Sin conexión a Jira Server)",
                "description": "Criterios de Aceptación: 1. El usuario navega a la vista. 2. Realiza la validación requerida.",
                "error": f"Jira status {response.status_code}"
            }
    except Exception as e:
        return {
            "key": issue_key,
            "summary": f"User Story {issue_key} (Modo Offline / Error HTTP)",
            "description": f"Detalles mock para desarrollo offline de {issue_key}. Error: {str(e)}",
            "is_offline": True
        }

def publish_test_case_to_jira(user_story_id: str, test_case_id: str, testplan_id: str, sprint_id: str) -> bool:
    """
    Actualiza la descripción de un caso de prueba en Jira asociándolo con una User Story.
    """
    try:
        updateTestDescription(user_story_id, test_case_id, testplan_id, sprint_id)
        return True
    except Exception as e:
        print(f"[jira_tool] No se pudo actualizar el Test Case en Jira: {e}")
        return False
