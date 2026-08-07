# tools/jira/jiraWorker.py
"""
Wrapper de compatibilidad para herramientas de Jira y Xray.
Redirige a tools.jira_tool para consolidación de arquitectura.
"""

from tools.jira_tool import (
    get_jira_client as _get_jira,
    get_xray_client as _get_xray,
    fetch_user_story_details,
    update_test_description,
    publish_test_case_to_jira,
    get_fach_test_keys,
    get_test_steps_from_case,
    delete_all_test_steps,
    add_test_steps,
    create_test_case,
    upload_execution_results,
    set_issue_link,
    create_bug_report,
    normalize_issue_key,
    clean_formatting_text,
)

# Mantener compatibilidad con referencias globales jira y xray
jira = _get_jira()
xray = _get_xray()

# Alias de funciones en formato legacy (camelCase)
def updateTestDescription(user_story, test_case, testplan, sprint):
    return update_test_description(user_story, test_case, testplan, sprint)

def getFachTestKeys(data):
    return get_fach_test_keys(data)

def cleanText(text):
    return clean_formatting_text(text)

def copyStepsToClipBoard(test_case):
    return get_test_steps_from_case(test_case)

def copyUserStoryDescription(user_story):
    return fetch_user_story_details(user_story)

def deleteAllSteps(test_case):
    return delete_all_test_steps(test_case)

def writeNewSteps(test_case):
    return {"status": "info", "message": "Usar add_test_steps(test_case_id, steps)"}

def createTestCase(user_story, sprint, testplan):
    return create_test_case(user_story, sprint, testplan)

def exportResults(test_execution_id, test_id):
    return upload_execution_results(test_execution_id, test_id)

def setLinks(inward_issue, outward_issue):
    return set_issue_link(inward_issue, outward_issue)

def createBug(test_execution, pdgo_version, sprint):
    res = create_bug_report(test_execution, pdgo_version, sprint)
    if res.get("status") == "success":
        return res["bug_key"], res["test_execution_key"], res["test_key"], res["user_story_key"], pdgo_version
    return None, test_execution, None, None, pdgo_version