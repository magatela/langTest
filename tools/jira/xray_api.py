# xray_api.py
"""
Xray-API-Client (Testmanagement-Plugin von Jira).

Auch hier wieder: nur Xray-spezifische Endpunkte, alles andere
kommt aus :class:`base_api.RestAPIClient`.
"""

from __future__ import annotations
from typing import Any, Dict
from base_api import RestAPIClient

class XrayAPI(RestAPIClient):
    """Client für Xray (Raven)."""

    # Xray nutzt mehrere unterschiedliche REST-Ressourcen
    RAVEN = "rest/raven/1.0/"
    RAVEN_API = "rest/raven/1.0/api/"
    RAVEN_API_V2 = "rest/raven/2.0/api/"

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
    # Test-Schritte                                                   #
    # --------------------------------------------------------------- #
    def normalize_issue_key(self, key:str):
        issueKey = f'{key}'
        if not issueKey.startswith(self._prefix):
            issueKey = f'{self._prefix}-{issueKey}'
        return issueKey

    def get_test_steps(self, test_id:str):
        return self.get(f"{self.RAVEN_API_V2}test/{self.normalize_issue_key(test_id)}/steps")

    def delete_step(self, test_id:str, step_id: str):
        return self.delete(
            f"{self.RAVEN_API_V2}test/{self.normalize_issue_key(test_id)}/steps/{step_id}"
        )

    def add_test_step(self, test_id:str, data: dict):
        return self.put(f"{self.RAVEN_API}test/{self.normalize_issue_key(test_id)}/step", data)
    
    
    # --------------------------------------------------------------- #
    # Test-Ausführungen                                               #
    # --------------------------------------------------------------- #
    def get_all_test_executions(self, test_id: str):
        return self.get(
            f"{self.RAVEN_API}test/{self.normalize_issue_key(test_id)}/testexecutions"
        )
    
    def get_test_run_results(self, test_id: str):
        return self.get(
            f"{self.RAVEN_API}test/{self.normalize_issue_key(test_id)}/testruns"
        )

    def add_test_to_test_execution(self, execution_id: str, data: Dict[str, Any]):
        # Example:
        # data = {
        #   "add": ["QTD-41", "QTD-40", "QTD-39", "QTD-38"],
        # }
        return self.post(f"{self.RAVEN_API}testexec/{self.normalize_issue_key(execution_id)}/test", data=data)

    # def update_test_run_comment(self, test_run_id: str, comment: str):
    #     # Platzhalter: hier evtl. JSON-Payload erzeugen und self.put(...)
    #     endpoint = f"{self.RAVEN_API}testrun/{test_run_id}"
    #     pattern = r"O://PD-Neu//Testdurchführung///d+ TP-Sprint /d+"
    #     new_text = re.sub(
    #         pattern,
    #         rf'O:/PD-Neu/Testdurchführung/{MySprint["pfad_code"]} TP-Sprint {MySprint["sprint"]}',
    #         comment,
    #     )
    #     return self.put(endpoint, data={"comment": new_text})


    # --------------------------------------------------------------- #
    # Test-Sets & -Pläne                                              #
    # --------------------------------------------------------------- #
    def add_test_to_test_set(self, test_set_id: str, data: Dict[str, Any]):
        return self.post(
            f"{self.RAVEN_API}testset/{self.normalize_issue_key(test_set_id)}/test", data=data
        )

    def edit_tests_in_plan(self, test_plan_id: str, data: Dict[str, Any]):
        """
        Fügt Tests zu einem Testplan hinzu oder entfernt diese.

        Beispiel ``data``::

            {
                "add": ["PDNEU-14"],
                "remove": ["PDNEU-42"]
            }
        """
        return self.post(
            f"{self.RAVEN_API}testplan/{self.normalize_issue_key(test_plan_id)}/test",
            data=data,
        )

    def get_testplan_tables(self):
        return self.get(f"{self.RAVEN_API}testrepository/{self._prefix}/folders")

    def get_test_from_folder(self, folder_id):
        return self.get(f"{self.RAVEN_API}testrepository/{self._prefix}/folders/{folder_id}/tests")
    
    def get_all_test_from_testplan(self, test_plan_id: str, limit=200, page = 1):
        params = { 'limit': limit,
                  'page': page }
        return self.get(
            f"{self.RAVEN_API}testplan/{self.normalize_issue_key(test_plan_id)}/test", params=params)



    # --------------------------------------------------------------- #
    # Test-Run                                                        #
    # --------------------------------------------------------------- #
    def update_testrun(self, testrun_id, data):
        return self.put(
            f'{self.RAVEN_API_V2}testrun/{testrun_id}',data
        )
    
    def get_test_run_data(self, execution_id: str, test_id: str):
        return self.get(
            f"{self.RAVEN_API}testrun?"
            f"testExecIssueKey={self.normalize_issue_key(execution_id)}"
            f"&testIssueKey={self.normalize_issue_key(test_id)}"
        )
    
    def get_test_run_data_by_id(self, testrun_id: str):
        return self.get(
            f"{self.RAVEN_API_V2}testrun/{testrun_id}?includeiterations=true"
        )

    def get_iteration_result(self, testrun_id: str, iteration_id:str):
        return self.get(
            f"{self.RAVEN_API_V2}testrun/{testrun_id}/iteration/{iteration_id}"
        )

    def get_iteration_steps_result(self, testrun_id: str, iteration_id:str):
        return self.get(
            f"{self.RAVEN_API_V2}testrun/{testrun_id}/iteration/{iteration_id}/step"
        )

    def get_iteration_steps_result_by_id(self, testrun_id: str, iteration_id:str, step_id:str):
        return self.get(
            f"{self.RAVEN_API_V2}testrun/{testrun_id}/iteration/{iteration_id}/step/{step_id}"
        )

    
    def get_test_run_id(self, execution_id: str, test_id: str):
        response = self.get_test_run_data(execution_id, test_id)
        if response.ok:
            return response.json().get('id')
        return None

    def read_test_run_comment(self, execution_id: str, test_id: str):
        response = self.get_test_run_data(execution_id, test_id)
        if response.ok:
            return response.json().get('comment')
        return None
    
    def upload_results(self, data):
        response = self.post(f'{self.RAVEN}import/execution', data)
        return response.ok

    def update_test_step(self, testrun_id, step_id, data):
        response = self.post(f"{self.RAVEN_API}testrun/{testrun_id}/step/{step_id}/attachment", data)
        return response.ok
    
    def update_test_step_status(self, testrun_id, step_id, data):
        response = self.put(f"{self.RAVEN_API}testrun/{testrun_id}/step/{step_id}", data)
        return response.ok
    
    def update_iteration_step(self, testrun_id, iteration_id, step_id, data):
        response = self.put(
            f"{self.RAVEN_API_V2}testrun/{testrun_id}/iteration/{iteration_id}/step/{step_id}", data
        )
        return response.ok

if __name__ == '__main__':
   
    from meinLogin import JiraLogin
    xray = XrayAPI(
        base_url=JiraLogin['base_url'],
        prefix=JiraLogin['prefix'],
        user=JiraLogin['user'],
        password=JiraLogin['password'],
        proxies=JiraLogin['proxies'],
    )
    
    
    # import json
    # data = {
    #             "add": ["QTD-41", "QTD-40", "QTD-39", "QTD-38"],
    # }

    # print(xray.edit_tests_in_plan("45", data).json())

    # save issue info to json file
    # import json

    # with open('C:/Users/t011669/Documents/Resultados/PDNEU-1126.json', 'r', encoding='utf-8') as f:
    #     data = json.loads(f.read())
    # response = xray.upload_results(data)
    # print(response)

    ## GET TEST RUN DATA
    # import json
    # print(xray.get_test_run_id('9415', '1108'))
    # # with open('response.json', 'w', encoding='utf-8') as f:
    # #     json.dump(xray.get_test_run_data('9415', '1108').json(), f, ensure_ascii=False, indent=4)
    # with open('response.json', 'w', encoding='utf-8') as f:
    #     print(xray.get_test_run_data_by_id(1623860))
    #     json.dump(xray.get_test_run_data_by_id(1623860).json(), f, ensure_ascii=False, indent=4)
    
    # listGlobalDefects = {
    #     "steps": [
    #         {
    #             "id": 77563,
    #             "status": "FAIL",
    #             "defects": {"add":['PDNEU-3908']}
    #         }
    #     ],
    #     "defects": {"add":['PDNEU-3908']}
    # }

    # response = xray.get_last_test_execution_key(903)
    # with open('response.json', 'w', encoding='utf-8') as f:
    #     data = response
    #     json.dump(data, f, ensure_ascii=False, indent=4)
    # steps = []
    # for step in data['steps']:
    #     stepInfo = {
    #         "index": step["index"],
    #         "step": step["step"]["raw"],
    #         "data": step["data"]["raw"],
    #         "result": step["result"]["raw"],
    #         "status": step["status"]
    #     }
    #     steps.append(stepInfo)
    # pyperclip.copy(json.dumps(steps, indent=4, ensure_ascii=False))
    

    import json
    
    
    with open('response.json', 'w', encoding='utf-8') as f:
        # print(xray.get_all_test_from_testplan('9603', 50))
        json.dump(xray.get_all_test_from_testplan('9603', 200, 1).json(), f, ensure_ascii=False, indent=4)