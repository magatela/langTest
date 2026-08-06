import yaml
from langchain_openai import ChatOpenAI
from typing import TypedDict, Annotated, List 
import operator
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage

from langgraph.graph import StateGraph, END

with open('config/config.yaml', 'r') as file:
    modelsConfigData = yaml.safe_load(file)
# es gibt nur drei Modelle 0 1 2
writerModelIndex = 0 # Model, das den Test Schreibt
reviewerModelIndex = 0 # Model, das den Test korrigiert

numberOfAttempts = 20

apiBase = modelsConfigData['apiBase']
apiKey = modelsConfigData['apiKey']

writerModelInfo = modelsConfigData['models'][writerModelIndex]
writerModel = writerModelInfo['model']
writerModelTemperature = writerModelInfo['temperature']

reviewerModelInfo = modelsConfigData['models'][writerModelIndex]
reviewerModel = writerModelInfo['model']
reviewerModelTemperature = writerModelInfo['temperature']

llmWriter = ChatOpenAI(
    model = writerModel,
    openai_api_key = apiKey,
    openai_api_base = apiBase,
    temperature = writerModelTemperature
)

llmReviewer = ChatOpenAI(
    model = reviewerModel,
    openai_api_key = apiKey,
    openai_api_base = apiBase,
    temperature = reviewerModelTemperature
)

# state
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage],operator.add]
    promptReviewer: str
    userStory : str
    iteration : int
    numberOfAttempts: int
    navigationsLogik : str
    targetView: str

# Nodes
def writerNode(state: AgentState):
    iteration = state.get('iteration', 0)
    # print(f'iteration Writer = {iteration} ')
    reponse = llmWriter.invoke(state['messages'])
    return {'messages': [reponse], 'iteration': iteration + 1 }

def reviewerNode(state: AgentState):
    lastMessageContent = state['messages'][-1].content
    state['solution'] = lastMessageContent
    userStory = state['userStory']
    reviewInstruction = f'''
        {state['promptReviewer']}
        ### INPUT FÜR DIE ANALYSE: ###
        - NAVIGATIONS LOGIK: {state['navigationsLogik']}
        - {state['targetView']}
        - USER STORY: {userStory}
        - VORSCHLAG DES WRITERS: {lastMessageContent}
    '''
    reponse = llmReviewer.invoke([HumanMessage(content=reviewInstruction)])
    iteration = state.get('iteration', 0)
    # print(f'\n\nzu korrigieren ({iteration}): {reponse}\n\n')
    return {'messages': [reponse]}

# control logic
def shouldContinue(state: AgentState):
    lastMessageContent = state['messages'][-1].content.upper()
    if 'ERLEDIG' in lastMessageContent:
        print(f'Reviewer ist fertig')
        return END
    if state['iteration'] >= state['numberOfAttempts']:
        print(f'Ende der Versuche ')
        return END
    return "writer"

workflow = StateGraph(AgentState)
workflow.add_node('writer', writerNode)
workflow.add_node('reviewer', reviewerNode)
workflow.set_entry_point('writer')
workflow.add_edge('writer', 'reviewer')
workflow.add_conditional_edges(
    'reviewer',
    shouldContinue,
    {
        'writer':'writer',
        END: END
    }
)

app = workflow.compile()

with open('prompt/testCaseWriter.md', 'r', encoding='utf-8') as file:
    systemPromptText = file.read()
with open('prompt/navigation.md', 'r', encoding='utf-8') as file:
    navigationsLogikText = file.read()
with open('prompt/us.txt', 'r', encoding='utf-8') as file:
    userStoryText = file.read()
with open('prompt/testCaseReviewer.md', 'r', encoding='utf-8') as file:
    promptReviewerText = file.read()

systemPrompt = SystemMessage(content=systemPromptText)
navigationsLogikPrompt = SystemMessage(content=navigationsLogikText)
targetViewPrompt = HumanMessage(content=f"die zu testende Maske ist 'Prüfungsfeststellungen'")
userStoryPrompt = HumanMessage(content=f'USER STORY: {userStoryText}')

inputs = {
    'messages' : [
        systemPrompt,
        navigationsLogikPrompt,
        userStoryPrompt
    ],
    'promptReviewer': promptReviewerText,
    'userStory': userStoryText,
    'iteration': 0,
    'numberOfAttempts' : numberOfAttempts,
    'navigationsLogik' :  navigationsLogikText,
    'targetView': f"die zu testende Maske ist 'Prüfungsfeststellungen'"
}

import json
solution = 0
listOfMessages = []
for event in app.stream(inputs):
    print('im doning your work also wait ;)')
    for node, value in event.items():
        for msg in value['messages']:
            neu_content = {
                'node': node,
                'content': msg.content
            }
            listOfMessages.append(neu_content)
            if 'ERLEDIG' in msg.content:
                solution = listOfMessages.index(neu_content)
            
with open('steps.json', 'w', encoding='utf-8') as f:
    jsondata = json.loads(listOfMessages[solution - 1 if solution else 0]['content'].replace('```json','').replace('```',''))
    json.dump(jsondata, f, ensure_ascii=False, indent=4)
print(f'############# FERTIG\n\n')