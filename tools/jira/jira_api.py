# jira_api.py
"""
Jira-API-Client.

Erbt von :class:`base_api.RestAPIClient` und implementiert nur die
Jira-spezifischen Endpunkte.
"""

from __future__ import annotations
from typing import Any, Dict
import json

try:
    from .base_api import RestAPIClient
except ImportError:
    from base_api import RestAPIClient

class JiraAPI(RestAPIClient):
    """
    Client für Jira Core.
    Diese Klasse implementiert nur die Jira-spezifischen Endpunkte.
    Erbt von :class:`base_api.RestAPIClient`.
    """

    API_PATH = "rest/api/2/"

    def __init__(
        self,
        base_url: str,
        prefix: str,
        user: str,
        password: str,
        *,
        proxies=None,
    ) -> None:
        super().__init__(base_url, user, password, proxies=proxies)
        self._prefix = prefix


    # --------------------------------------------------------------- #
    # Util                                                            #
    # --------------------------------------------------------------- #
    def normalize_issue_key(self, key:str):
        issueKey = f'{key}'
        if not issueKey.startswith(self._prefix):
            issueKey = f'{self._prefix}-{issueKey}'
        return issueKey
    

    # --------------------------------------------------------------- #
    # Endpunkte                                                      #
    # --------------------------------------------------------------- #

    # GET
    def get_project_info(self):
        """         
        Ruft die Informationen zum Projekt ab.  
        :return: Response-Objekt der GET-Anfrage.
        """
        return self.get(f"{self.API_PATH}project/{self._prefix}")

    def get_issue_info(self, key: str):
        """
        Ruft die Informationen zu einem Issue ab.    
        :param key: Der Key des Issues, inklusive des Projekt-Präfixes.
        :return: Response-Objekt der GET-Anfrage.
        """
        return self.get(f"{self.API_PATH}issue/{self.normalize_issue_key(key)}")

    def get_changelogs(self, key: str):
        """     
        Ruft die Änderungsprotokolle (Changelogs) eines Issues ab. Der Key muss das Projekt-Präfix enthalten.
        :param key: Der Key des Issues, inklusive des Projekt-Präfixes.
        :return: Response-Objekt der GET-Anfrage.
        """
        return self.get(f"{self.API_PATH}issue/{self.normalize_issue_key(key)}/changelog")

    def check_issue_editable_fields(self, key: str):
        """
        Prüft, welche Felder eines Issues bearbeitet werden können. Der Key muss das Projekt-Präfix enthalten.
        :param key: Der Key des Issues, inklusive des Projekt-Präfixes.
        :return: Response-Objekt der GET-Anfrage.
        """
        return self.get(f"{self.API_PATH}issue/{self.normalize_issue_key(key)}/editmeta")

    def get_all_fields(self):
        """
        Ruft alle verfügbaren Felder ab.        
        :return: Response-Objekt der GET-Anfrage.
        """
        return self.get(f"{self.API_PATH}field")

    # def get_issue_fields(self, key: str):
    #     """ 
    #     Ruft die Felder eines Issues ab.    
    #     :param key: Der Key des Issues, inklusive des Projekt-Präfixes.
    #     :return: Response-Objekt der GET-Anfrage.
    #     """
    #     return self.get(f"{self.API_PATH}issue/{self._prefix}-{key}/fields")

    def get_field_reference_data(self):
        """
        Ruft die Referenzdaten für alle Felder ab.      
        :return: Response-Objekt der GET-Anfrage.
        """
        return self.get(f"{self.API_PATH}jql/autocompletedata")

    def jql_requests(self, jql: str, max_results: int = 50, start_at: int = 0):
        """
        Führt eine JQL-Abfrage aus und gibt die Ergebnisse zurück.
        Nutzt query params von requests für korrekte URL-Kodierung.
        :param jql: JQL-Abfrage-String.
        :param max_results: Maximale Anzahl der Ergebnisse (Standard: 50).
        :param start_at: Start-Index für Paginierung (Standard: 0).
        """         
        return self.get(
            f"{self.API_PATH}search",
            params={"jql": jql, "maxResults": max_results, "startAt": start_at}
        )
    
    def get_bugs_linked_to_test(self, test_id: str):
        jql = (
            f'issue in linkedIssues("{self.normalize_issue_key(test_id)}") '
            'AND issuetype = Bug'
        )
        return self.jql_requests(jql)

    def get_test_cases_in_project(self):
        """
        Ruft alle Testfälle in einem Projekt ab.
        :param project_key: Der Schlüssel des Projekts, z.B. "QTD".
        :return: Response-Objekt der GET-Anfrage.
        """
        jql = f'project = "{self._prefix}" AND issuetype = Test'
        return self.jql_requests(jql)

    def get_all_transitions(self, key:str):
        return self.get(f"{self.API_PATH}issue/{self.normalize_issue_key(key)}/transitions")
        
    # POST
    def create_issue(self, data: Dict[str, Any]):
        """
        Erstellt ein neues Issue.       
        :param data: Die zu erstellenden Felder im JSON-Format.
        :return: Response-Objekt der POST-Anfrage.
        """
        return self.post(f"{self.API_PATH}issue", data=data)

    def set_issue_transition(self, key: Any, data: Dict[str, Any]):
        """
        Payload Example:
        ID ändersicht jenachdem welche Workflow für das Issue definiert ist
        payload = {
           'transition':{
                'id': '4'
            }
        }
        """
        return self.post(f"{self.API_PATH}issue/{self.normalize_issue_key(key)}/transitions", data=data)
    
    def set_issuelink(self, data):
        """
        Beispiel Data:
        data = {
        "type":{
            "name": "Befund",
        },
        "inwardIssue": {
                "key": "STORY-123",
        },
        "outwardIssue":{
                "key": "TEST-456"
        }
    }
        """
        return self.post(f"{self.API_PATH}issueLink", data=data)

    # PUT
    def update_issue(self, key: str, data: Dict[str, Any]):
        """
        Aktualisiert ein Issue. Der Key muss das Projekt-Präfix enthalten.
        :param key: Der Key des Issues, inklusive des Projekt-Präfixes.
        :param data: Die zu aktualisierenden Felder im JSON-Format.
        """
        return self.put(f"{self.API_PATH}issue/{self.normalize_issue_key(key)}", data=data)
    
    # DELETE
    def delete_issue(self, key: str):
        """
        Löscht ein Issue. Der Key muss das Projekt-Präfix enthalten.    
        :param key: Der Key des Issues, inklusive des Projekt-Präfixes.
        :return: Response-Objekt der DELETE-Anfrage.
        """
        return self.delete(f"{self.API_PATH}issue/{self.normalize_issue_key(key)}")
    
    # Sonstiges
    def check_user_credentials(self):
        """
        Prüft Benutzer­daten durch einen simplen GET-Call auf die API-Wurzel.
        Gibt das Response-Objekt zurück (Status 200 → OK).
        """
        return self.get(f"{self.API_PATH}project")

if __name__ == '__main__':
    try:
        from meinLogin import JiraLogin
    except ImportError:
        from config.config_loader import get_jira_credentials
        JiraLogin = get_jira_credentials()
        
    jira = JiraAPI(
        base_url=JiraLogin['base_url'],
        prefix=JiraLogin['prefix'],
        user=JiraLogin['user'],
        password=JiraLogin['password'],
    )
    # jira.set_proxies(None)   # Proxy deaktivieren
    jira.set_proxies({'http':'http://proxy-user:8080','https':'http://proxy-user:8080'})   # Proxy aktivieren

    #with open('jsonRepo/epics.json', 'r', encoding='utf-8') as f:
    # with open('jsonRepo/test_plan.json', 'r', encoding='utf-8') as f:
    #     data = json.loads(f.read())
    #for item in data:
    #    print(item)
    
    #print(json.dumps(jira.get_issue_info(42).json(), indent=4, ensure_ascii=False))

    # save issue info to json file
    # with open('response.json', 'w', encoding='utf-8') as f:
    #    #  data = json.dump(jira.check_issue_editable_fields(5905).json(), f, ensure_ascii=False, indent=4)
    #     # payload = {
    #     #     'transition':{
    #     #             'id': '4'
    #     #         }
    #     # }
    #     # responseJson = jira.jql_requests('assignee = "miguel.avendano@fv.nrw.de"  AND issuetype = "Test Execution" AND status = Offen').json()
    #     responseJson = jira.check_issue_editable_fields(5782).json()
    #     data = json.dump(responseJson, f, ensure_ascii=False, indent=4)
    
    # lista = []
    # for item in responseJson['issues']:
    #     lista.append(item['key'][6:])
    
    # data = {
    #     "fields": {
    #          "summary": "texto",     
    #     }
    # }
    # response = jira.update_issue(5782, data)
    # print(f'{response.status_code}')  
    
    
    # save issue info to json file
    jira.save_response(jira.get_issue_info(353))


    # data = {
    #     "fields": {
    #         "customfield_10231":[]       
    #     }
    # }
    # response = jira.update_issue(5804, data)
    # print(response)

    # with open('jsonRepo/response.json', 'r', encoding='utf-8') as f:
    #     data = json.loads(f.read())
    # for item in data['issues']:
    #     print(item['key'])
    
# QTD: Scrum Default Issue Screen (2)

    # # linkIssues
    # data = {
    #     "type":{
    #         "name": "Befund",
    #     },
    #     "inwardIssue": {
    #             "key": "PDNEU-4979", #STORY
    #     },
    #     "outwardIssue":{
    #             "key": "PDNEU-6136", #TEST
    #     }
    # }
    # with open('response.json', 'w', encoding='utf-8') as f:
    #     response = jira.set_issuelink(data)
    #     print(response)
