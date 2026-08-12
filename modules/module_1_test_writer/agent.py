# modules/module_1_test_writer/agent.py
import json
import operator
import re
from pathlib import Path
from typing import TypedDict, Annotated, List, Optional, Callable, Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END

from config.config_loader import get_llm_config
from tools.jira_tool import fetch_user_story_details, normalize_issue_key

MODULE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = MODULE_DIR / "prompts"

# Cargar prompts por defecto
def load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

def analyze_and_recommend_jira_references(
    user_story_text: str,
    exclude_key: Optional[str] = None,
    llm: Optional[Any] = None,
    mock_recommendations: Optional[List[Dict[str, str]]] = None
) -> List[Dict[str, str]]:
    """
    Analiza el texto de la User Story utilizando el LLM para identificar referencias a otros issues de Jira
    y generar una recomendación explicativa de por qué serían útiles para redactar los casos de prueba.

    Returns:
        List[Dict[str, str]]: Lista de diccionarios con claves 'key' y 'reason'.
        Ejemplo: [{'key': 'PDNEU-4567', 'reason': 'Define el diálogo modal de feststellungen'}]
    """
    if mock_recommendations is not None:
        return mock_recommendations

    if not user_story_text:
        return []

    norm_exclude = normalize_issue_key(exclude_key) if exclude_key else ""

    analysis_prompt = f"""Du bist ein leitender QA-Analyst. Analysiere den folgenden User-Story-Text und identifiziere alle Erwähnungen oder Verweise auf andere Jira-Issues (z.B. PDNEU-1234, QA-56, FT-789) oder relevante Spezifikationen.

STRIKTE SPRACHANFORDERUNG:
Du musst AUSSCHLIESSLICH auf Deutsch antworten.

Für jeden gefundenen Schlüssel (außer {norm_exclude}):
1. Extrahiere den Schlüssel (z.B. "PDNEU-4567").
2. Erkläre kurz auf Deutsch, WARUM dieser Verweis für die Erstellung der Testfälle nützlich ist.

Gib deine Antwort AUSSCHLIESSLICH im JSON-Format wie folgt zurück:
{{
  "references": [
    {{
      "key": "PDNEU-XXXX",
      "reason": "Erklärung warum nützlich"
    }}
  ]
}}

Wenn keine Verweise vorhanden sind, gib {{"references": []}} zurück.

USER STORY TEXT:
{user_story_text}
"""

    if llm is None:
        try:
            llm_cfg = get_llm_config()
            model_name = llm_cfg["models"][0]["model"]
            llm = ChatOpenAI(
                model=model_name,
                openai_api_key=llm_cfg["apiKey"],
                openai_api_base=llm_cfg["apiBase"],
                temperature=0.0
            )
        except Exception:
            llm = None

    if llm is not None:
        try:
            response = llm.invoke([HumanMessage(content=analysis_prompt)])
            content = response.content if hasattr(response, 'content') else str(response)
            
            clean_content = re.sub(r'```(?:json)?\s*', '', str(content)).strip('` \n')
            data = json.loads(clean_content)
            raw_refs = data.get("references", [])
            
            valid_refs = []
            for item in raw_refs:
                key = normalize_issue_key(item.get("key", ""))
                reason = item.get("reason", "Recomendado por el LLM")
                if key and key != norm_exclude and not any(r['key'] == key for r in valid_refs):
                    valid_refs.append({"key": key, "reason": reason})
            return valid_refs
        except Exception:
            pass

    # Fallback determinista en caso de sin conexión o error de formateo JSON del LLM
    matches = re.findall(r'\b[A-Z][A-Z0-9]+-\d+\b', user_story_text)
    fallback_refs = []
    for m in matches:
        norm_m = normalize_issue_key(m)
        if norm_m != norm_exclude and not any(r['key'] == norm_m for r in fallback_refs):
            fallback_refs.append({
                "key": norm_m,
                "reason": f"Referencia detectada en el texto ({norm_m})"
            })
    return fallback_refs

def sanitize_messages(messages: List[Any]) -> List[BaseMessage]:
    """
    Garantiza que todos los elementos de la lista de mensajes sean objetos BaseMessage válidos.
    Sanea strings, dicts y otros tipos para prevenir errores del tipo:
    'str' object has no attribute 'model_dump'.
    """
    clean_list: List[BaseMessage] = []
    for msg in messages:
        if isinstance(msg, BaseMessage):
            clean_list.append(msg)
        elif isinstance(msg, str):
            clean_list.append(HumanMessage(content=msg))
        elif isinstance(msg, dict):
            role = msg.get("role", "user")
            content = msg.get("content", str(msg))
            if role == "system":
                clean_list.append(SystemMessage(content=content))
            elif role in ["assistant", "ai"]:
                clean_list.append(AIMessage(content=content))
            else:
                clean_list.append(HumanMessage(content=content))
        else:
            clean_list.append(HumanMessage(content=str(msg)))
    return clean_list

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
        messages = sanitize_messages(state.get('messages', []))
        response = llm_writer.invoke(messages)
        if isinstance(response, str):
            response = AIMessage(content=response)
        return {'messages': [response], 'iteration': iteration + 1}

    def reviewerNode(state: AgentState):
        messages = sanitize_messages(state.get('messages', []))
        last_msg = messages[-1] if messages else HumanMessage(content="")
        lastMessageContent = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)

        userStory = state.get('userStory', '')
        reviewInstruction = f'''
            {state.get('promptReviewer', '')}
            ### INPUT FÜR DIE ANALYSE: ###
            - NAVIGATIONS LOGIK: {state.get('navigationsLogik', '')}
            - {state.get('targetView', '')}
            - USER STORY: {userStory}
            - VORSCHLAG DES WRITERS: {lastMessageContent}
        '''
        response = llm_reviewer.invoke([HumanMessage(content=reviewInstruction)])
        if isinstance(response, str):
            response = AIMessage(content=response)
        return {'messages': [response]}

    def shouldContinue(state: AgentState):
        messages = sanitize_messages(state.get('messages', []))
        last_msg = messages[-1] if messages else None
        lastMessageContent = ""
        if last_msg:
            lastMessageContent = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)
        
        upper_content = str(lastMessageContent).upper()
        if 'ERLEDIG' in upper_content or 'COMPLETED' in upper_content:
            return END
        if state.get('iteration', 0) >= state.get('numberOfAttempts', 5):
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
    on_references_found_callback: Optional[Callable[[List[Dict[str, str]]], List[str]]] = None,
    selected_referenced_keys: Optional[List[str]] = None,
    mock_recommendations: Optional[List[Dict[str, str]]] = None,
    mock_response: Optional[str] = None
) -> Dict[str, Any]:
    """
    Ejecuta el agente Módulo 1 (Writer + Reviewer) para generar Casos de Prueba.
    
    Analiza la User Story usando el LLM para recomendar referencias a otros issues de Jira.
    Solicita al usuario cuáles referencias recomendadas deben incluirse para la generación.
    """
    systemPromptText = load_prompt('testCaseWriter.md')
    navigationsLogikText = load_prompt('navigation.md')
    promptReviewerText = load_prompt('testCaseReviewer.md')

    if not user_story_text:
        us_data = fetch_user_story_details(jira_issue_key)
        user_story_text = f"Title: {us_data.get('summary', '')}\nDescription: {us_data.get('description', '')}"

    # Step 1: Analizar el texto con el LLM para obtener recomendaciones explicativas de referencias
    recommended_references = analyze_and_recommend_jira_references(
        user_story_text,
        exclude_key=jira_issue_key,
        mock_recommendations=mock_recommendations
    )
    selected_references: List[str] = []

    if recommended_references:
        if on_references_found_callback:
            selected_references = on_references_found_callback(recommended_references)
        elif selected_referenced_keys is not None:
            selected_references = selected_referenced_keys

    # Step 2: Cargar el contenido de las referencias seleccionadas y anexarlo como contexto adicional
    if selected_references:
        ref_blocks = []
        for ref_key in selected_references:
            ref_details = fetch_user_story_details(ref_key)
            ref_blocks.append(
                f"### REFERENCED JIRA ISSUE DETAILS ({ref_key}) ###\n"
                f"Title: {ref_details.get('summary', '')}\n"
                f"Description: {ref_details.get('description', '')}"
            )
        user_story_text += "\n\n" + "\n\n".join(ref_blocks)

    systemPrompt = SystemMessage(content=systemPromptText)
    navigationsLogikPrompt = SystemMessage(content=navigationsLogikText)
    userStoryPrompt = HumanMessage(content=f'USER STORY:\n{user_story_text}')
    targetViewPromptText = f"die zu testende Maske ist '{target_view}'"

    inputs = {
        'messages': sanitize_messages([systemPrompt, navigationsLogikPrompt, userStoryPrompt]),
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
            'solution': mock_response,
            'recommended_references': recommended_references,
            'selected_references': selected_references,
            'final_user_story_text': user_story_text
        }

    app = create_agent_graph()
    list_of_messages = []
    solution_content = ""

    for event in app.stream(inputs):
        for node, value in event.items():
            msgs = value.get('messages', [])
            for msg in msgs:
                node_content = msg.content if hasattr(msg, 'content') else str(msg)
                list_of_messages.append({'node': node, 'content': node_content})
                
                if on_step_callback:
                    on_step_callback(node, node_content)

                if 'ERLEDIG' in str(node_content).upper() or 'COMPLETED' in str(node_content).upper():
                    if len(list_of_messages) >= 2:
                        solution_content = list_of_messages[-2]['content']

    if not solution_content and list_of_messages:
        solution_content = list_of_messages[-1]['content']

    return {
        'success': True,
        'messages': list_of_messages,
        'solution': solution_content,
        'recommended_references': recommended_references,
        'selected_references': selected_references,
        'final_user_story_text': user_story_text
    }

if __name__ == '__main__':
    res = run_test_writer_agent(mock_response='```json\n{"test": "ok"}\n```')
    print("Mock Output:", res['solution'])