# modules/module_1_test_writer/agent.py
import json
import operator
from pathlib import Path
from typing import TypedDict, Annotated, List, Optional, Callable, Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, END

from config.config_loader import get_llm_config
from tools.jira_tool import fetch_user_story_details

MODULE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = MODULE_DIR / "prompts"

# Cargar prompts por defecto
def load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    promptReviewer: str
    userStory: str
    iteration: int
    numberOfAttempts: int
    navigationsLogik: str
    targetView: str
    solution: Optional[str]

def create_agent_graph(llm_writer=None, llm_reviewer=None):
    """
    Crea y compila el grafo LangGraph para el Módulo 1.
    """
    if llm_writer is None or llm_reviewer is None:
        llm_cfg = get_llm_config()
        writer_cfg = llm_cfg["models"][0]
        reviewer_cfg = llm_cfg["models"][1] if len(llm_cfg["models"]) > 1 else writer_cfg
        
        llm_writer = ChatOpenAI(
            model=writer_cfg["model"],
            openai_api_key=llm_cfg["apiKey"],
            openai_api_base=llm_cfg["apiBase"],
            temperature=writer_cfg["temperature"]
        )
        llm_reviewer = ChatOpenAI(
            model=reviewer_cfg["model"],
            openai_api_key=llm_cfg["apiKey"],
            openai_api_base=llm_cfg["apiBase"],
            temperature=reviewer_cfg["temperature"]
        )

    def writerNode(state: AgentState):
        iteration = state.get('iteration', 0)
        response = llm_writer.invoke(state['messages'])
        return {'messages': [response], 'iteration': iteration + 1}

    def reviewerNode(state: AgentState):
        lastMessageContent = state['messages'][-1].content
        userStory = state['userStory']
        reviewInstruction = f'''
            {state['promptReviewer']}
            ### INPUT FÜR DIE ANALYSE: ###
            - NAVIGATIONS LOGIK: {state['navigationsLogik']}
            - {state['targetView']}
            - USER STORY: {userStory}
            - VORSCHLAG DES WRITERS: {lastMessageContent}
        '''
        response = llm_reviewer.invoke([HumanMessage(content=reviewInstruction)])
        return {'messages': [response]}

    def shouldContinue(state: AgentState):
        lastMessageContent = state['messages'][-1].content.upper()
        if 'ERLEDIG' in lastMessageContent or 'COMPLETED' in lastMessageContent:
            return END
        if state['iteration'] >= state['numberOfAttempts']:
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
            'writer': 'writer',
            END: END
        }
    )

    return workflow.compile()

def run_test_writer_agent(
    jira_issue_key: str = "PDNEU-1234",
    target_view: str = "Prüfungsfeststellungen",
    user_story_text: Optional[str] = None,
    number_of_attempts: int = 5,
    on_step_callback: Optional[Callable[[str, str], None]] = None,
    mock_response: Optional[str] = None
) -> Dict[str, Any]:
    """
    Ejecuta el agente Módulo 1 (Writer + Reviewer) para generar Casos de Prueba.
    Soporta callback para streaming a la CLI de Rich y mock_response para testing offline.
    """
    systemPromptText = load_prompt('testCaseWriter.md')
    navigationsLogikText = load_prompt('navigation.md')
    promptReviewerText = load_prompt('testCaseReviewer.md')

    if not user_story_text:
        us_data = fetch_user_story_details(jira_issue_key)
        user_story_text = f"Title: {us_data.get('summary', '')}\nDescription: {us_data.get('description', '')}"

    systemPrompt = SystemMessage(content=systemPromptText)
    navigationsLogikPrompt = SystemMessage(content=navigationsLogikText)
    userStoryPrompt = HumanMessage(content=f'USER STORY:\n{user_story_text}')
    targetViewPromptText = f"die zu testende Maske ist '{target_view}'"

    inputs = {
        'messages': [systemPrompt, navigationsLogikPrompt, userStoryPrompt],
        'promptReviewer': promptReviewerText,
        'userStory': user_story_text,
        'iteration': 0,
        'numberOfAttempts': number_of_attempts,
        'navigationsLogik': navigationsLogikText,
        'targetView': targetViewPromptText,
        'solution': None
    }

    # Si se provee mock_response (para tests unitarios u offline)
    if mock_response:
        if on_step_callback:
            on_step_callback('writer', mock_response)
            on_step_callback('reviewer', 'ERLEDIGT')
        return {
            'success': True,
            'messages': [{'node': 'writer', 'content': mock_response}],
            'solution': mock_response
        }

    app = create_agent_graph()
    list_of_messages = []
    solution_content = ""

    for event in app.stream(inputs):
        for node, value in event.items():
            for msg in value['messages']:
                node_content = msg.content
                list_of_messages.append({'node': node, 'content': node_content})
                
                if on_step_callback:
                    on_step_callback(node, node_content)

                if 'ERLEDIG' in node_content.upper() or 'COMPLETED' in node_content.upper():
                    if len(list_of_messages) >= 2:
                        solution_content = list_of_messages[-2]['content']

    if not solution_content and list_of_messages:
        solution_content = list_of_messages[-1]['content']

    return {
        'success': True,
        'messages': list_of_messages,
        'solution': solution_content
    }

if __name__ == '__main__':
    res = run_test_writer_agent(mock_response='```json\n{"test": "ok"}\n```')
    print("Mock Output:", res['solution'])