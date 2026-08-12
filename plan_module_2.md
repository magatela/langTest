# Plan de Implementación: Agente Autónomo `module_2_browser_repl` (Navegación, Inspección de DOM/ariaSnapshot, POMs y Pasos PDNEU-4060.ts)

Plan para la transformación del **Módulo 2** en un agente de Inteligencia Artificial para la interacción asistida con el navegador en tiempo real sobre el servidor **Playwright TypeScript REPL (`ts_repl_server`)**.

---

## 🎯 Visión General del Agente

El agente del **Módulo 2 (`modules/module_2_browser_repl/agent.py`)** operará conectado al servidor **Playwright TS REPL** mediante el puente conector IPC (`TSPlaywrightREPLBridge`). Atenderá tres tipos de tareas principales:

1. **Navegación Asistida**:
   - Navegar a vistas o secciones específicas utilizando clases POM existentes (ej. `NavigationPage.ts`) o generando y evaluando código de Playwright en vivo.
2. **Generación / Actualización Asistida de POMs**:
   - Pregunta al usuario si la página ya cuenta con una clase POM o si debe generarse desde cero.
   - Pregunta al usuario la estrategia de inspección a utilizar:
     - **Opción A:** Auto-descubrimiento clásico mediante árbol DOM HTML.
     - **Opción B:** Extracción de estructura semántica usando Playwright `ariaSnapshot()`.
   - Solicita autorización explícita para capturar capturas de pantalla (Base64) e inspeccionar atributos.
   - Genera clases POM TypeScript **siguiendo estrictamente la convención existente** en `NavigationPage.ts` y `BerichtMainPage.ts` (con categorías `fields`, `comboboxes`, `radios`, `buttons` y métodos `isVisible`, `isDisabled`, `isEditable`, `setValue`, `getValue`, `click`, `highlight`).
   - Guarda el archivo generado directamente en `ts_repl_server/POM/<NombreVista>Page.ts`.
3. **Generación de Pasos de Automatización (`PDNEU-4060.ts`)**:
   - Construye bloques de código TypeScript de pruebas aplicando el patrón estándar visto en `user_snippets/PDNEU-4060.ts`:
     - Estructura `executeStep('step X', resultWriter, async () => { ... }, successMsg, errorMsg, errors, goblaStatus, stepStatus)`.
     - Validaciones con `executeAssertion(() => { expect(...).toBeTruthy() }, 'Mensaje')`.
     - Evidencias con `resultWriter.createEvidence(...)` y destacados temporales `highlight('red')` / `highlight('none')`.
   - Ejecuta el código en el REPL, lee la salida de consola/errores de Playwright y auto-corrige si se presentan fallas.

---

## 📋 flujo de Interacción con el Usuario

```text
[Usuario da una tarea en lenguaje natural]
          │
          ├─► 1. ¿Navegar a una vista?
          │     └─► Evalúa snippet en REPL o usa NavigationPage.ts
          │
          ├─► 2. ¿Crear o actualizar POM?
          │     ├─► ¿Ya existe POM o desde cero?
          │     ├─► ¿Permites capturas de pantalla Base64 para el LLM?
          │     └─► ¿Estrategia de inspección: DOM HTML o ariaSnapshot()?
          │           └─► Inspecciona page en REPL ➔ Genera POM en ts_repl_server/POM/
          │
          └─► 3. ¿Crear código de paso (estilo PDNEU-4060.ts)?
                ├─► ¿Existe el POM para los elementos requeridos?
                └─► Genera bloque executeStep(...) ➔ Ejecuta en REPL ➔ Lee consola y valida
```

---

## 🛠️ Modificaciones de Código Propuestas

### Componente: Módulo 2 (`modules/module_2_browser_repl/`)

#### 1. [NEW] [prompts.py](file:///c:/Users/migue/VisualStudio_ws/langTest/modules/module_2_browser_repl/prompts.py)
- Contendrá las plantillas y reglas de razonamiento para el LLM:
  - `AGENT_SYSTEM_PROMPT`: Orquestación de navegación, decisiones de inspección y ejecución de código REPL.
  - `POM_GENERATOR_PROMPT`: Instrucciones para construir clases POM TypeScript con categorías (`fields`, `comboboxes`, `radios`, `buttons`) compatibles con `NavigationPage.ts`.
  - `STEP_CODER_PROMPT`: Reglas estrictas de codificación de pasos según el estándar `PDNEU-4060.ts`.

#### 2. [NEW] [agent.py](file:///c:/Users/migue/VisualStudio_ws/langTest/modules/module_2_browser_repl/agent.py)
- Grafo LangGraph para el Agente del Módulo 2:
  - Estado `BrowserAgentState`: `task`, `current_page`, `poms_list`, `inspection_mode`, `dom_snapshot`, `aria_snapshot`, `screenshot_b64`, `generated_code`, `messages`, `console_output`.
  - Nodos del Grafo:
    - `plannerNode`: Analiza la tarea del usuario y decide la acción (navegar, inspeccionar o codificar).
    - `inspectorNode`: Ejecuta snippets en el REPL (`page.locator().ariaSnapshot()` o consulta DOM) y obtiene capturas Base64 si el usuario lo autoriza.
    - `pomBuilderNode`: Genera el archivo TypeScript `.ts` y lo guarda en `ts_repl_server/POM/`.
    - `stepCoderNode`: Ensambla el bloque `executeStep(...)`, lo envía al REPL y valida los logs devueltos.

#### 3. [MODIFY] [ts_repl_bridge.py](file:///c:/Users/migue/VisualStudio_ws/langTest/modules/module_2_browser_repl/ts_repl_bridge.py)
- Agregar métodos auxiliares de inspección:
  - `get_aria_snapshot()`: Evalúa `await page.locator('body').ariaSnapshot()` a través del REPL.
  - `get_dom_elements()`: Extrae selectores e identificadores clave de inputs, botones y comboboxes.
  - `get_screenshot_b64()`: Captura y devuelve la imagen en formato Base64.

---

### Componente: Servidor REPL (`ts_repl_server/`)

#### 4. [MODIFY] [repl.ts](file:///c:/Users/migue/VisualStudio_ws/langTest/ts_repl_server/repl/repl.ts)
- Soporte para recarga dinámica de clases POM cuando se guarde un nuevo archivo en `ts_repl_server/POM/`.

---

### Componente: CLI Principal (`main.py`)

#### 5. [MODIFY] [main.py](file:///c:/Users/migue/VisualStudio_ws/langTest/main.py)
- Integrar la opción interactiva del **Agente del Módulo 2** dentro de la Opción 2 del menú `Rich`.

---

## 🧪 Plan de Verificación y Pruebas

### Pruebas Automatizadas
- Ejecutar la suite de pruebas offline para garantizar la estabilidad general:
  ```bash
  python -m unittest discover tests
  ```
- Crear `tests/test_module_2_agent.py` para probar la construcción de prompts, los métodos de extracción de `ariaSnapshot` y la generación del formato `PDNEU-4060.ts`.

### Verificación Manual
- Ejecutar `python main.py` -> Opción 2:
  1. Solicitar la creación de un nuevo POM eligiendo la estrategia `ariaSnapshot()`.
  2. Verificar la creación del archivo en `ts_repl_server/POM/`.
  3. Solicitar la generación de un paso de prueba y verificar la ejecución live en el REPL y la lectura de los logs de la consola.
