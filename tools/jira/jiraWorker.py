import json
import re

try:
    import pyperclip
except ImportError:
    pyperclip = None

try:
    from .jira_api import JiraAPI
    from .xray_api import XrayAPI
except ImportError:
    from jira_api import JiraAPI
    from xray_api import XrayAPI

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

xray = XrayAPI(
    base_url=JiraLogin['base_url'],
    prefix=JiraLogin['prefix'],
    user=JiraLogin['user'],
    password=JiraLogin['password'],
)

if JiraLogin.get('proxies'):
    xray.set_proxies(JiraLogin['proxies'])  
    jira.set_proxies(JiraLogin['proxies'])   

def saveResponse(response):
    with open('response.json', 'w', encoding='utf-8') as f:
        json.dump(response, f, ensure_ascii=False, indent=4)

########## COPY DDESCRIPTION ##########
def updateTestDescription(user_story, test_case, testplan, sprint):
    userStoryResponse = jira.get_issue_info(user_story)
    userStoryData = userStoryResponse.json()
    saveResponse(userStoryData)
    description = userStoryData["fields"]["description"]
    summary = userStoryData["fields"]["summary"]
    
    labels = [label for label in userStoryData['fields']['labels']]
    labels.append('TP8QS')
    labels.append(f'Sprint_{sprint}')
    
    newDescription = f"Verweise:\n# PDNEU-{user_story}\n# " + description
    data = {
        "fields": {
            
            "summary": f'TC-STORY-{user_story}:{userStoryData["fields"]["summary"]}',
            "description":newDescription, 
            "priority": {"id": userStoryData['fields']['priority']['id']},
            "fixVersions": [{'name': '1.0 KapG'},{'name': '2.0 EinzelU'},{'name': '3.0 PersG'}],
            "assignee": {"name": "user@email.de"},
            "labels": labels,
            "components": [{'name': 'TP8QS'}],
            "customfield_10101":userStoryData["fields"]["customfield_10101"],
            # "customfield_10215":"03 Benutzeroberfläche (Frontend)/03.150 PrüfAbwg - Prüfungsbericht",
            "customfield_10213": [ #Test plan
                "PDNEU-653",
                f"PDNEU-{testplan}"
            ],
            # "customfield_10211": [ # testSet
            #     "PDNEU-12461"
            # ],
        }
    }

    updatedTestcaseResponse = jira.update_issue(test_case, data)
    print(f"updates test case: {updatedTestcaseResponse.status_code}")
    print(newDescription)

########## GET TEST SPEPS ##########
def getFachTestKeys(data):
    'Obtener los ID de fach test de un archivo de respuesta de una User story'
    listFT = []
    issuelinks = data['fields']['issuelinks']
    for issuelink in issuelinks:
        content = issuelink.get('outwardIssue', None)
        if content:
            name = content.get('fields', {}).get('summary','')
            print(name)
            if name.startswith('FT'):
                listFT.append(content.get('key'))
    return listFT

def cleanText(text):
    return re.sub(r'\{[^}]*\}', '', text)

def copyStepsToClipBoard(test_case):
    
    fachTestCaseResponse = jira.get_issue_info(test_case)
    fachTestCaseData = fachTestCaseResponse.json()
    descriptionFT = fachTestCaseData["fields"]["description"]
    ftSteps = []
    for item in fachTestCaseData["fields"]["customfield_12521"]['steps']:
        newStep = {
            'step':cleanText(item['fields']['Action']),
            'data': cleanText(item['fields']['Data']),   
            'result' :cleanText(item['fields']['Expected Result'])            
        }
        ftSteps.append(newStep)
    
    totalContent = f"""
        Liste mit Schritte, die als Beispiel für den Test dienen:
        {json.dumps(ftSteps, indent=4, ensure_ascii=False)}
    """
    pyperclip.copy(totalContent)
    print('copiado')

def copyUserStoryDescription(user_story):
    ftSteps = []
    userStoryResponse = jira.get_issue_info(user_story)
    userStoryData = userStoryResponse.json()
    descriptionUS = userStoryData["fields"]["description"]
    
    
    listFachTst = getFachTestKeys(userStoryData)
    for test in listFachTst:
        fachTestCaseResponse = jira.get_issue_info(test)
        fachTestCaseData = fachTestCaseResponse.json()
        descriptionFT = fachTestCaseData["fields"]["description"]
        if descriptionUS in descriptionFT:
            for item in fachTestCaseData["fields"]["customfield_12521"]['steps']:
                newStep = {
                    'step':cleanText(item['fields']['Action']),
                    'data': cleanText(item['fields']['Data']),   
                    'result' :cleanText(item['fields']['Expected Result'])            
                }
                ftSteps.append(newStep)
    
    cleanDescription = re.sub(r'\n+', r'\n', descriptionUS)
    #cleanDescription = descriptionUS
    totalContent = f"""{cleanDescription}"""
    with open('prompt/us.txt', 'w', encoding='utf-8') as file:
        file.write(cleanDescription)
    pyperclip.copy(totalContent)
    print('copiado')
    

# Refactor
def getTestContext(test_case):
    testCaseResponse = jira.get_issue_info(test_case)
    testCaseData = testCaseResponse.json()
    description = testCaseData.get('fields').get('description')
    testSteps = testCaseData.get('fields').get('customfield_10208')
    context = { "description user story": description,
            "list of Steps": testSteps }
    print(context)
    return context
    

def deleteAllSteps(test_case):
    testCaseStepsResponse = xray.get_test_steps(test_case)
    testCaseStepsData = testCaseStepsResponse.json()
    for testStep in testCaseStepsData["steps"]:
        stepId = testStep['id']
        stepIdResponse = xray.delete_step(test_case, stepId)
        print(f"deleting step {stepId} from: PDNEU-{test_case} -> status code: {stepIdResponse.status_code}")

def writeNewSteps(test_case):
    with open('steps.json', 'r', encoding='utf-8') as f:
        data = json.loads(f.read())
    # for j, step in enumerate(data):
    #     stepInfo = step
    #     print(f'adding step {stepInfo} to test : {test_case}')
    #     response = xray.add_test_step(test_case, stepInfo)
        
    
    for j, step in enumerate(data['steps']):
        stepInfo = step['fields']
        response = xray.add_test_step(test_case, stepInfo)
        print(f'adding step {j}:status code: {response.status_code}')

def createTestCase(user_story, sprint, testplan):
    userStoryResponse = jira.get_issue_info(user_story)
    userStoryData = userStoryResponse.json()
    
    labels = [label for label in userStoryData['fields']['labels']]
    labels.append('TP8QS')
    labels.append(f'Sprint_{sprint}')

    description = userStoryData["fields"]["description"]
    testDescription = f"Verweise:\n# PDNEU-{user_story}\n# " + description
    newTest = {
            "fields": {
                "project": {"key": "PDNEU"},
                "summary": f'TC-STORY-{user_story}:{userStoryData["fields"]["summary"]}',
                "description":testDescription, 
                 "issuetype": {"name": "Test"},
                "priority": {"id": userStoryData['fields']['priority']['id']},
                "fixVersions": [{'name': '1.0 KapG'},{'name': '2.0 EinzelU'},{'name': '3.0 PersG'}],
                "assignee": {"name": "user@email.de"},
                "labels": labels,
                "components": [{'name': 'TP8QS'}],
                "customfield_10101":userStoryData["fields"]["customfield_10101"],
                # "customfield_10215":"03 Benutzeroberfläche (Frontend)/03.150 PrüfAbwg - Prüfungsbericht",
                "customfield_10213": [ #Test plan
                    "PDNEU-653",
                    f"PDNEU-{testplan}"
                ],
                "customfield_10211": [ # testSet
                    "PDNEU-12461"
                ],
            }
        }
    #print(json.dumps(newTest,indent=4))
    testCaseResponse = jira.create_issue(newTest)
    testCaseData = testCaseResponse.json()
    saveResponse(testCaseResponse.json())
    key = testCaseData["key"]
    print(f'Created {key}')
    writeNewSteps(key)
    
    transitionUserStory = {
        "transition":{
           "id": "861"
        }
    }

    transitionTestCase = {
        "transition":{
           "id": "4",
        }
    }
    # setTransitionUSResponse = jira.set_issue_transition(key=user_story, data=transitionUserStory)
    # print(f'transition user story: {setTransitionUSResponse.status_code}')

    setTransitionTCResponse = jira.set_issue_transition(key=key, data=transitionTestCase)
    print(f'transition Test Case: {setTransitionTCResponse.status_code}')

    issueLinkData = {
        "type":{
            "name": "Befund",
        },
        "inwardIssue": {
                "key": userStoryData['key'], #STORY
        },
        "outwardIssue":{
                "key": key, #TEST
        }
    }
    issueLinkResponse = jira.set_issuelink(issueLinkData)
    print(f'issueLink: {issueLinkResponse.status_code}')

def exportResults(test_execution_id, test_id):
    # base_path = os.path.join(['C:','Users','t011669','Documents','Resultados',f'PDNEU-{test_id}'])
    # jsonResults = os.path.join([base_path, f'PDNEU-{test_id}.json'])
    
    test_id = normalize_issue_key(test_id)
    test_execution_id = normalize_issue_key(test_execution_id)

    testRunResponse = xray.get_test_run_data(test_execution_id, test_id)
    testRunData = testRunResponse.json() if testRunResponse.ok else None
    with open(f'C:/Users/t011669/Documents/Resultados/{test_id}/{test_id}.json', 'r') as file:
        runResutls = json.loads(file.read())
    
    payload = {
        "testExecutionKey": f"{test_execution_id}",
        "tests" : [
            runResutls
        ]
    }
    response = xray.upload_results(payload)
    print(response)

def updateStep(test_execution_id, test_id, step):
    test_id = normalize_issue_key(test_id)
    test_execution_id = normalize_issue_key(test_execution_id)
    testRunResponse = xray.get_test_run_data(test_execution_id, test_id)
    testRunData = testRunResponse.json()
    testRunID = testRunData['id']
    stepId = ''
    for items in testRunData['steps']:
        if step == items['index']:
            stepId = items['id']
    print(f'ID: {stepId}')

    image = {
                "data": "iVBORw0KGgoAAAANSUhEUgAABrYAAAUYCAIAAABiCXUp"
                "filename": "step 4.png",
                "contentType": "image/png"
            }
    print(xray.update_test_step(testRunID, stepId, image))

    testRunResponse = xray.get_test_run_data(test_execution_id, test_id)
    testRunData = testRunResponse.json()
    xray.save_response(testRunResponse)

def updateStepStatus(test_execution_id, test_id, step):
    test_id = normalize_issue_key(test_id)
    test_execution_id = normalize_issue_key(test_execution_id)
    
    testRunResponse = xray.get_test_run_data(test_execution_id, test_id)
    testRunResponseJson = testRunResponse.json()
    testRunID = testRunResponseJson.get('id', 'ERROR')
    
    testRunIterationsResponse = xray.get_test_run_data_by_id(testRunID)
    testRunIterationsResponseJson = testRunIterationsResponse.json()
    iterationID = testRunIterationsResponseJson['iterations'][0]['id']
    
    iterationResult = xray.get_iteration_steps_result(testRunID, iterationID)
    iterationResultJson = iterationResult.json()
    stepID = iterationResultJson[1]['id']
    print(stepID)
    # 
    # 
    # # testRunData = testRunResponse.json()
    # testRunID = testRunData['id']
    # stepId = ''
    # for items in testRunData['steps']:
    #     if step == items['index']:
    #         stepId = items['id']
    # print(f'ID: {stepId}')

    image = {
        
        "status": "TODO",
        "actualResult": "test",
        "evidences": {
            "add":[
                {
        
                "data": "iVBORw0KGgoAAAANSUhEUgAABrYAAAUYCAIAAABiCXUpAAAQ",
                "filename": "step 10.a.png",
                "contentType": "image/png"
            
            },
            ]
            
        }
    }
    print(testRunID, iterationID, stepID)
    print(xray.update_iteration_step(testRunID, iterationID, stepID, image))
    z = xray.get_iteration_steps_result_by_id(testRunID, iterationID, stepID)

    # testRunResponse = xray.get_test_run_data(test_execution_id, test_id)
    # testRunData = testRunResponse.json()
    xray.save_response(z)


def getBugTemplate(execution_id, test_id, story_id, version):
    return f"""
    *Aktuelles Ergebnis*
    <Beschreibung der Schritte, wie man zu dem Fehler kommt inklusive Vorbedingung und Testdaten ggfs. mit Bildern>
    <WICHTIG - Bitte Testfallschrittnummer angeben>
    
    *Erwartetes Ergebnis*
    <Beschreibung des Erwarteten Ergebnis mit dem Verweis auf den Testschritt in Xray>
    
    *Verweis*
    Story: {story_id}
    Testfall: {test_id}
    Testausführung : {execution_id}
    
    *Benutzer*
    || Anmeldung als || Rolle || Passwort |
    | t-Kennung | pP | N/A |
    
    *Testumgebung*
    || Thema || Name/TU Link || Version || Build || Info || Eingesetzt ||
    || Betriebssystem | Windows 11 Enterprise |32H2| 22631.5189 | 64 Bit | (/) |
    || Browser | Microsoft Edge | 138.0.3351.77 | Offizielles Build | 64-Bit | (/) |
    || QSI | [QSI| url_hier ]| 1.{version}| ---- | ---- | (x) |
    || QSP | [AIT/QSP| url_hier]| 1.{version} | ---- |  ---- | (/) |
    """    

def getRetestTemplate(version):
    f"""
    h3. ReTest 
    h3. Version:
    ||Frontend (FE)||V1.{version}||
    ||Backend (BE)||----||
    h3. Testumgebung
    ||Thema||Name||Version||Build||Info||
    ||Betriebsystem|Windows 11 Enterprise |32H2|22631.5189|64 Bit|
    ||Browser|Microsoft Edge| 138.0.3351.77|Offizielles Build|64-Bit|
    ||View|Desktop|—|—|----|
    || TU LINK | [QSP| url_hier/ ]| 1.{version} | ---- | ---- |
    ||Benutzer|t-Kennung|
    h3. Test Tools
    ||Manueller Test (Jira-Xray)|(/)|
    ||Automatisierter Test (Playweright)|(x)|
    h3. Vorbedingung
    ||Steuernummer| |
    h3. Testergebniss
    ||Anzahl||Ergebnis||Testfall||Testausführung||Testschritt||
    ||1|(/) erfolgreich|TC-PDNEU-1219|TE-PDNEU-11277|6|
    h3. Testbelege
    <Ergänzende Belege zur Testdurchführung>
    """
def normalize_issue_key(key:str):
        issueKey = f'{key}'
        if not issueKey.startswith('PDNEU'):
            issueKey = f'PDNEU-{issueKey}'
        return issueKey

def setLinks(inwardIssue, outwardIssue):
    issueLinkData = {
        "type":{
            "name": "Befund",
        },
        "inwardIssue": {
                "key": normalize_issue_key(inwardIssue), #STORY o elemeto que genera
        },
        "outwardIssue":{
                "key": normalize_issue_key(outwardIssue), # test, bug o elemento generado
        }
    }
    print(f'setLinks: {inwardIssue}-{outwardIssue}: {jira.set_issuelink(issueLinkData)}')

def createBug(test_execution, pdgo_Version, sprint):
    test_execution = normalize_issue_key(test_execution)
    testExecutionResponse = jira.get_issue_info(test_execution)
    testExecutionData = testExecutionResponse.json()
    testKey = testExecutionData['fields']['customfield_10219'][0]['testKey']
    
    testCaseResponse = jira.get_issue_info(testKey)
    testCaseData = testCaseResponse.json()
    
    labels = [label for label in testCaseData['fields']['labels'] if not label.lower().startswith('sprint')]
    labels.append(f'Sprint_{sprint}') ############ PARAMETRO
    pattern = r'TC-([A-Z]+-\d+):.+'
    matchRe = re.search(pattern, testCaseData['fields']['summary'])
    
    if matchRe:
        storyKey = matchRe.group(1) or ''
    storyKey = storyKey.replace('STORY-', '')
    storyKey = normalize_issue_key(storyKey)
    
    newBug = {
            "fields": {
                "project": {"key": "PDNEU"},
                "summary": f'BG-STORY-{storyKey}:',
                "issuetype": {"name": "Bug"},
                "priority": {"id": testCaseData['fields']['priority']['id']},
                "fixVersions": [{'name': '1.0 KapG'}, {'name': '2.0 EinzelU'}, {'name': '3.0 PersG'}],
                "versions": [{'name': f'PD-Go 1.{pdgo_Version}'}],
                "assignee": {"name": "user@email.de"},
                "labels": labels,
                "components": [{'name': 'TP8QS'}],
                "customfield_10101":testCaseData["fields"]["customfield_10101"], # 
                "customfield_20003" : {"id": "520538"},
            }
        }  
    # print(f'TE: {test_execution}, T:{testKey}, US:{storyKey}, PD-Go{pdgo_Version}')
    response = jira.create_issue(newBug)
    dugData = response.json()
    saveResponse(dugData)
    bugKey = dugData['key']
    print(f'BugKEy: {bugKey}')

    setLinks(storyKey, bugKey)
    setLinks(testKey, bugKey)
    setLinks(test_execution, bugKey)
    # baseurl = f'https://jira.steuer.niedersachsen.doi-de.net/browse/{bugKey}'
    # print(baseurl)
    # webbrowser.open(baseurl)
    return bugKey, test_execution, testKey, storyKey, pdgo_Version
    # return '1258', test_execution, testKey, storyKey, pdgo_Version

def updateBug(bugKey, test_execution, testKey, storyKey, pdgo_Version):
    bugKey = normalize_issue_key(bugKey)
    test_execution = normalize_issue_key(test_execution)
    testKey = normalize_issue_key(testKey)
    storyKey = normalize_issue_key(storyKey)
    newBug = {
            "fields": {
                "description": getBugTemplate(test_execution, testKey, storyKey, pdgo_Version),
                "customfield_10106": None
            }
        }   
    response = jira.update_issue(bugKey, newBug)
    
# user_story = 2156
# test_case = 6128
# copyStepsToClipBoard(12810)
# copyUserStoryDescription(10209)


# copyTestInfoInClipBoard(321)
# copyStepsToClipBoard(12804)

# updateTestDescription(10209, 15335, 15154, 36)
# deleteAllSteps(1510)
# writeNewSteps(1510)
# createTestCase(12816, 36, 15154)


# bugKey, test_execution, testKey, storyKey, pdgo_Version = createBug(12994, 27, 33)
# updateBug(bugKey, test_execution, testKey, storyKey, pdgo_Version)

if __name__ == '__main__':
    pass
# exportResults(15345, 3454)  
# updateStepStatus(14765, 1461, 1)

# with open('response.json', 'w', encoding='utf-8') as f:
#     response = jira.get_issue_info(9610)
#     print(f'RESPONSE: {response.text}')
#     json.dump(jira.get_issue_info(10533).json(), f, ensure_ascii=False, indent=4)

 
        