# modules/module_4_pom_generator/agent.py
"""
Agente Generador y Actualizador de Page Object Models (POMs) en TypeScript (Módulo 4).
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config.config_loader import get_llm_config
from modules.module_2_browser_repl.ts_repl_bridge import TSPlaywrightREPLBridge
from modules.module_4_pom_generator.prompts import (
    POM_GENERATOR_SYSTEM_PROMPT,
    POM_UPDATER_SYSTEM_PROMPT,
    build_pom_generation_prompt,
    build_pom_update_prompt
)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
POM_DIR = ROOT_DIR / "ts_repl_server" / "POM"

def get_pom_dir() -> Path:
    """
    Retorna la ruta al directorio donde residen los POMs en TypeScript.
    """
    if not POM_DIR.exists():
        POM_DIR.mkdir(parents=True, exist_ok=True)
    return POM_DIR

def list_available_reference_poms() -> List[str]:
    """
    Lista todos los archivos .ts disponibles en ts_repl_server/POM/.
    """
    p_dir = get_pom_dir()
    if not p_dir.exists():
        return []
    return [f.name for f in p_dir.glob("*.ts")]

def read_reference_poms(selected_files: List[str]) -> str:
    """
    Lee el contenido de los archivos de POM seleccionados como referencia.
    """
    p_dir = get_pom_dir()
    combined_code = []
    for filename in selected_files:
        filepath = p_dir / filename
        if filepath.exists() and filepath.is_file():
            try:
                code = filepath.read_text(encoding="utf-8")
                combined_code.append(f"// === Referencia: {filename} ===\n{code}")
            except Exception as e:
                combined_code.append(f"// Error al leer {filename}: {e}")
    return "\n\n".join(combined_code)

def clean_typescript_code(raw_response: str) -> str:
    """
    Extrae código TypeScript limpio eliminando bloques markdown (```typescript ... ```).
    """
    pattern = r"```(?:typescript|ts)?\s*([\s\S]*?)\s*```"
    match = re.search(pattern, raw_response, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return raw_response.strip()

class POMGeneratorAgent:
    def __init__(self, llm: Optional[Any] = None):
        if llm is None:
            config = get_llm_config()
            model_info = config["models"][0]
            self.llm = ChatOpenAI(
                model=model_info.get("model", "gpt-4o"),
                temperature=model_info.get("temperature", 0.2),
                openai_api_key=config.get("apiKey", "mock-key"),
                openai_api_base=config.get("apiBase", "https://api.openai.com/v1")
            )
        else:
            self.llm = llm

    def generate_pom(
        self,
        target_class_name: str,
        reference_files: List[str],
        aria_snapshot: str = "",
        user_instructions: str = "",
        mock_llm_response: Optional[str] = None
    ) -> str:
        """
        Genera un nuevo POM en TypeScript.
        """
        if mock_llm_response is not None:
            return clean_typescript_code(mock_llm_response)

        ref_code = read_reference_poms(reference_files)
        user_prompt = build_pom_generation_prompt(
            target_class_name=target_class_name,
            reference_poms_code=ref_code,
            aria_snapshot=aria_snapshot,
            user_instructions=user_instructions
        )

        messages = [
            SystemMessage(content=POM_GENERATOR_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        return clean_typescript_code(response.content)

    def update_pom(
        self,
        existing_filename: str,
        reference_files: List[str] = None,
        aria_snapshot: str = "",
        user_instructions: str = "",
        mock_llm_response: Optional[str] = None
    ) -> str:
        """
        Actualiza un POM en TypeScript existente.
        """
        if mock_llm_response is not None:
            return clean_typescript_code(mock_llm_response)

        p_dir = get_pom_dir()
        target_file = p_dir / existing_filename
        if not target_file.exists():
            raise FileNotFoundError(f"El archivo POM {existing_filename} no existe en {p_dir}")

        existing_code = target_file.read_text(encoding="utf-8")
        ref_code = read_reference_poms(reference_files or [])

        user_prompt = build_pom_update_prompt(
            existing_pom_code=existing_code,
            reference_poms_code=ref_code,
            aria_snapshot=aria_snapshot,
            user_instructions=user_instructions
        )

        messages = [
            SystemMessage(content=POM_UPDATER_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        return clean_typescript_code(response.content)

def validate_pom_in_repl(pom_code: str, bridge: Optional[TSPlaywrightREPLBridge] = None) -> Dict[str, Any]:
    """
    Evalúa el código TypeScript del POM generado en el REPL para validar compilación.
    """
    if bridge is None:
        from modules.module_2_browser_repl.ts_repl_bridge import get_repl_bridge
        bridge = get_repl_bridge()

    if not bridge.ensure_started():
        return {"status": "error", "error": "No se pudo iniciar el REPL para validación"}

    return bridge.eval_code(pom_code)

def run_pom_generator_agent(
    mode: str = "create", # "create" o "update"
    target_name: str = "LoginPage.ts",
    reference_files: Optional[List[str]] = None,
    aria_snapshot: str = "",
    user_instructions: str = "",
    validate: bool = False,
    mock_response: Optional[str] = None,
    bridge: Optional[TSPlaywrightREPLBridge] = None
) -> Dict[str, Any]:
    """
    Función de entrada principal para ejecutar el Agente Generador/Actualizador de POMs (Módulo 4).
    """
    agent = POMGeneratorAgent()
    p_dir = get_pom_dir()

    if not target_name.endswith(".ts"):
        target_file_name = f"{target_name}.ts"
    else:
        target_file_name = target_name

    # Extraer nombre de la clase (ej. LoginPage.ts -> LoginPage)
    class_name = Path(target_file_name).stem

    if mode == "update":
        generated_code = agent.update_pom(
            existing_filename=target_file_name,
            reference_files=reference_files or [],
            aria_snapshot=aria_snapshot,
            user_instructions=user_instructions,
            mock_llm_response=mock_response
        )
    else:
        generated_code = agent.generate_pom(
            target_class_name=class_name,
            reference_files=reference_files or [],
            aria_snapshot=aria_snapshot,
            user_instructions=user_instructions,
            mock_llm_response=mock_response
        )

    # Guardar en ts_repl_server/POM/
    output_path = p_dir / target_file_name
    output_path.write_text(generated_code, encoding="utf-8")

    validation_result = None
    if validate:
        validation_result = validate_pom_in_repl(generated_code, bridge=bridge)

    return {
        "status": "success",
        "mode": mode,
        "filename": target_file_name,
        "path": str(output_path),
        "code": generated_code,
        "validation": validation_result
    }
