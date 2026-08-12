# tools/jira_tool.py
"""
Unified Tools Module for Jira and Xray Integration.

Provides structured, deterministic, and typed functions for AI agents
and system interfaces to interact with Jira Core REST API and Xray Test Management.
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
# CUSTOM FIELD CONSTANTS (Jira / Xray Custom Fields)
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
# API CLIENT MANAGEMENT & LAZY INITIALIZATION
# ==============================================================================
_jira_client_instance: Optional[JiraAPI] = None
_xray_client_instance: Optional[XrayAPI] = None


def get_jira_client() -> JiraAPI:
    """
    Lazy initialization of the JiraAPI client.
    Loads credentials dynamically without failing if configuration is missing.

    Returns:
        JiraAPI: Configured instance of the Jira client.
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
    Lazy initialization of the XrayAPI client.

    Returns:
        XrayAPI: Configured instance of the Xray client.
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
# UTILITY AUXILIARY FUNCTIONS
# ==============================================================================
def normalize_issue_key(key: Union[str, int], prefix: str = DEFAULT_PROJECT_KEY) -> str:
    """
    Formats and normalizes a Jira issue key to ensure it contains the correct prefix.

    Args:
        key: Issue ID or Key (e.g., '1234', 'PDNEU-1234', or 'QA-99').
        prefix: Default Jira project prefix.

    Returns:
        str: Normalized issue key (e.g., 'PDNEU-1234' or 'QA-99').
    """
    str_key = str(key).strip()
    if "-" in str_key:
        return str_key
    return f"{prefix}-{str_key}"


def clean_formatting_text(text: str) -> str:
    """
    Removes special Jira Wiki formatting characters from a text string.

    Args:
        text: Text containing Jira Wiki formatting or tags like {code}.

    Returns:
        str: Cleaned text string.
    """
    if not text:
        return ""
    return re.sub(r"\{[^}]*\}", "", text).strip()


# ==============================================================================
# AUTONOMOUS TOOLS
# ==============================================================================
def search_jira_by_jql(
    jql_query: str, max_results: int = 50, mock_issues: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Tool: Executes a search query using JQL (Jira Query Language) via Jira REST API.
    Available to all agents in the system.

    Args:
        jql_query (str): JQL query string (e.g., 'project = "PDNEU" AND issuetype = Bug').
        max_results (int): Maximum number of results to fetch.
        mock_issues (Optional[List[Dict[str, Any]]]): Optional mock issues for offline testing.

    Returns:
        Dict[str, Any]: Result dictionary containing 'status', 'total', 'issues', and 'jql'.
    """
    if mock_issues is not None:
        return {
            "status": "success",
            "jql": jql_query,
            "total": len(mock_issues),
            "issues": mock_issues[:max_results],
        }

    try:
        jira = get_jira_client()
        response = jira.jql_requests(jql_query, max_results=max_results)

        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success",
                "jql": jql_query,
                "total": data.get("total", 0),
                "issues": data.get("issues", []),
            }
        else:
            return {
                "status": "error",
                "message": f"HTTP Error {response.status_code} while executing JQL",
                "jql": jql_query,
                "issues": [],
            }
    except Exception as e:
        logger.error("Exception in search_jira_by_jql: %s", str(e))
        return {
            "status": "error",
            "message": str(e),
            "jql": jql_query,
            "issues": [],
        }


def fetch_user_story_details(
    issue_key: str, mock_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Tool: Fetches key details of a User Story in Jira (summary, description, acceptance criteria).

    Args:
        issue_key (str): Jira Issue Key (e.g., 'PDNEU-1234' or '1234').
        mock_data (Optional[Dict[str, Any]]): Optional mock data for offline testing.

    Returns:
        Dict[str, Any]: Dictionary containing story details or error info.
            Status "success" contains keys: key, summary, description, priority, issue_status, raw.
            Status "error" contains keys: status, message, key, summary, description.
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
                "message": f"HTTP Error {response.status_code} while querying Jira",
                "key": norm_key,
                "summary": f"User Story {norm_key} (No connection to Jira)",
                "description": "Safe mode: Original description could not be retrieved.",
            }
    except Exception as e:
        logger.error("Exception in fetch_user_story_details: %s", str(e))
        return {
            "status": "error",
            "message": str(e),
            "key": issue_key,
            "summary": f"User Story {issue_key} (Connection Error)",
            "description": f"HTTP request could not be completed. Details: {str(e)}",
            "is_offline": True,
        }


def update_test_description(
    user_story_id: Union[str, int],
    test_case_id: Union[str, int],
    testplan_id: Union[str, int],
    sprint_id: Union[str, int],
) -> Dict[str, Any]:
    """
    Tool: Updates description, required fields, and fix version of a Test Case in Jira,
    linking it to a User Story and a Test Plan.

    Args:
        user_story_id (Union[str, int]): Source User Story ID or Key.
        test_case_id (Union[str, int]): Test Case ID or Key to update.
        testplan_id (Union[str, int]): Test Plan ID.
        sprint_id (Union[str, int]): Sprint number or identifier.

    Returns:
        Dict[str, Any]: Result dictionary with operation status.
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
                "message": f"User Story {us_key} not found",
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
                "message": f"Test Case {tc_key} successfully updated",
                "test_case_key": tc_key,
                "new_description": new_description,
            }
        else:
            return {
                "status": "error",
                "message": f"HTTP Error {update_resp.status_code} while updating {tc_key}",
                "details": update_resp.text,
            }
    except Exception as e:
        logger.error("Exception in update_test_description: %s", str(e))
        return {"status": "error", "message": str(e)}


def publish_test_case_to_jira(
    user_story_id: str, test_case_id: str, testplan_id: str, sprint_id: str
) -> Dict[str, Any]:
    """
    Tool: Publishes and synchronizes a Test Case with its User Story in Jira.

    Args:
        user_story_id (str): User Story ID in Jira.
        test_case_id (str): Test Case ID.
        testplan_id (str): Test Plan ID.
        sprint_id (str): Sprint number.

    Returns:
        Dict[str, Any]: Result dictionary with execution status and details.
    """
    return update_test_description(user_story_id, test_case_id, testplan_id, sprint_id)


def get_fach_test_keys(user_story_data: Dict[str, Any]) -> List[str]:
    """
    Extracts Fach Test (FT) issue keys linked to a User Story.

    Args:
        user_story_data (Dict[str, Any]): Full JSON data of the User Story issue.

    Returns:
        List[str]: List of linked Fach Test issue keys found.
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
    Tool: Retrieves structured test steps from a Test Case or Fach Test in Jira/Xray.

    Args:
        test_case_id (Union[str, int]): Test Case ID or Key in Jira.

    Returns:
        Dict[str, Any]: Dictionary containing formatted test steps (Action, Data, Expected Result).
    """
    try:
        jira = get_jira_client()
        norm_key = normalize_issue_key(test_case_id, jira._prefix)
        resp = jira.get_issue_info(norm_key)

        if not resp.ok:
            return {
                "status": "error",
                "message": f"Could not query Test Case {norm_key}",
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
        logger.error("Exception in get_test_steps_from_case: %s", str(e))
        return {"status": "error", "message": str(e)}


def delete_all_test_steps(test_case_id: Union[str, int]) -> Dict[str, Any]:
    """
    Tool: Deletes all test steps from a Test Case in Xray.

    Args:
        test_case_id (Union[str, int]): Test Case ID or Key.

    Returns:
        Dict[str, Any]: Deletion process status and summary count.
    """
    try:
        xray = get_xray_client()
        norm_key = normalize_issue_key(test_case_id, xray._prefix)
        resp = xray.get_test_steps(norm_key)

        if not resp.ok:
            return {
                "status": "error",
                "message": f"Could not retrieve steps for Test Case {norm_key}",
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
            "message": f"Deleted {deleted_count} steps from Test Case {norm_key}",
            "deleted_count": deleted_count,
        }
    except Exception as e:
        logger.error("Exception in delete_all_test_steps: %s", str(e))
        return {"status": "error", "message": str(e)}


def add_test_steps(
    test_case_id: Union[str, int], steps: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Tool: Adds a list of test steps to an existing Test Case in Xray.

    Args:
        test_case_id (Union[str, int]): Test Case ID.
        steps (List[Dict[str, Any]]): List of step definition dictionaries.

    Returns:
        Dict[str, Any]: Status and count of added steps.
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
            "message": f"Added {added_count} steps to {norm_key}",
            "added_count": added_count,
        }
    except Exception as e:
        logger.error("Exception in add_test_steps: %s", str(e))
        return {"status": "error", "message": str(e)}


def create_test_case(
    user_story_id: Union[str, int],
    sprint_id: Union[str, int],
    testplan_id: Union[str, int],
    steps_data: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Tool: Creates a new Test Case in Jira linked to a User Story and assigns its Xray steps.

    Args:
        user_story_id (Union[str, int]): User Story ID in Jira.
        sprint_id (Union[str, int]): Sprint identifier.
        testplan_id (Union[str, int]): Associated Test Plan ID.
        steps_data (Optional[List[Dict[str, Any]]]): Optional steps to insert into the created test.

    Returns:
        Dict[str, Any]: Key of the created Test Case and linking result.
    """
    try:
        jira = get_jira_client()
        us_key = normalize_issue_key(user_story_id, jira._prefix)
        tp_key = normalize_issue_key(testplan_id, jira._prefix)

        us_resp = jira.get_issue_info(us_key)
        if not us_resp.ok:
            return {
                "status": "error",
                "message": f"User Story {us_key} not found",
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
                "message": f"Error creating Test Case: HTTP {create_resp.status_code}",
                "details": create_resp.text,
            }

        created_data = create_resp.json()
        tc_key = created_data.get("key", "")

        if steps_data and tc_key:
            add_test_steps(tc_key, steps_data)

        link_payload = {
            "type": {"name": "Befund"},
            "inwardIssue": {"key": us_data.get("key", us_key)},
            "outwardIssue": {"key": tc_key},
        }
        jira.set_issuelink(link_payload)

        return {
            "status": "success",
            "message": f"Test case {tc_key} created and linked successfully",
            "test_case_key": tc_key,
        }
    except Exception as e:
        logger.error("Exception in create_test_case: %s", str(e))
        return {"status": "error", "message": str(e)}


def upload_execution_results(
    test_execution_id: Union[str, int],
    test_id: Union[str, int],
    results_filepath: Optional[str] = None,
    results_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Tool: Uploads test execution results to Xray (via JSON file path or direct payload).

    Args:
        test_execution_id (Union[str, int]): Test Execution ID.
        test_id (Union[str, int]): Test Case ID.
        results_filepath (Optional[str]): Path to JSON file containing evidence/results.
        results_payload (Optional[Dict[str, Any]]): Direct results payload.

    Returns:
        Dict[str, Any]: Result dictionary from Xray API response.
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
                    "message": f"Results file not found: {results_filepath}",
                }

        if not raw_results:
            return {
                "status": "error",
                "message": "Either results_filepath or results_payload must be provided",
            }

        payload = {
            "testExecutionKey": exec_key,
            "tests": [raw_results] if isinstance(raw_results, dict) else raw_results,
        }

        resp = xray.upload_results(payload)
        if resp.ok:
            return {
                "status": "success",
                "message": f"Results uploaded successfully to {exec_key}",
                "response": resp.json() if resp.text else {},
            }
        else:
            return {
                "status": "error",
                "message": f"HTTP Error {resp.status_code} while uploading results",
                "details": resp.text,
            }
    except Exception as e:
        logger.error("Exception in upload_execution_results: %s", str(e))
        return {"status": "error", "message": str(e)}


def set_issue_link(
    inward_issue: Union[str, int],
    outward_issue: Union[str, int],
    link_type: str = "Befund",
) -> Dict[str, Any]:
    """
    Tool: Establishes an issue link between two Jira issues.

    Args:
        inward_issue (Union[str, int]): Source issue (e.g., User Story).
        outward_issue (Union[str, int]): Destination/related issue (e.g., Bug, Test).
        link_type (str): Name of the link type (default: "Befund").

    Returns:
        Dict[str, Any]: Result dictionary of the link creation process.
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
                "message": f"Link {link_type} created between {in_key} and {out_key}",
            }
        else:
            return {
                "status": "error",
                "message": f"HTTP Error {resp.status_code} while creating link",
            }
    except Exception as e:
        logger.error("Exception in set_issue_link: %s", str(e))
        return {"status": "error", "message": str(e)}


def create_bug_report(
    test_execution_id: Union[str, int],
    pdgo_version: str,
    sprint_id: Union[str, int],
) -> Dict[str, Any]:
    """
    Tool: Generates a Bug report in Jira from a failed Xray Test Execution.

    Args:
        test_execution_id (Union[str, int]): Test Execution ID.
        pdgo_version (str): Application version being tested.
        sprint_id (Union[str, int]): Sprint number.

    Returns:
        Dict[str, Any]: Dictionary containing created Bug details (bug_key, story_key, test_key).
    """
    try:
        jira = get_jira_client()
        exec_key = normalize_issue_key(test_execution_id, jira._prefix)

        exec_resp = jira.get_issue_info(exec_key)
        if not exec_resp.ok:
            return {
                "status": "error",
                "message": f"Test Execution {exec_key} not found",
            }

        exec_data = exec_resp.json()
        runs_field = exec_data.get("fields", {}).get(CUSTOM_FIELD_TEST_RUNS, [])
        if not runs_field:
            return {
                "status": "error",
                "message": f"No tests associated with execution {exec_key}",
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
                "summary": f"BG-STORY-{story_key}: Defect detected in {test_key}",
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
                "message": f"Error creating Bug: HTTP {bug_resp.status_code}",
            }

        bug_data = bug_resp.json()
        bug_key = bug_data.get("key", "")

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
        logger.error("Exception in create_bug_report: %s", str(e))
        return {"status": "error", "message": str(e)}
