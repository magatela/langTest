# Plan de Implementación: Sistema Modular de Agentes QA con LangGraph, Playwright (TS Output & REPL) y Herramientas Python (Jira REST API)

## 1. Visión General de la Arquitectura y Modularidad

El sistema consta de un motor de agentes en Python (basado en LangGraph/LangChain) que interactúa con un **Toolkit de Herramientas Python compartidas** (incluyendo integración con **Jira REST API** para la descarga automática de Historias de Usuario), orquesta y genera **código de automatización exclusivamente en TypeScript (`.ts`)** e interactúa con un **REPL de Playwright en TypeScript (Node.js/ts-node)**.

El sistema se compone de **5 módulos independientes**, un **Toolbox de Herramientas Reutilizables** y un **núcleo de integración compartida (Core/Shared)**.

### Estructura de Directorios Propuesta

```text
langTest/
├── .venv/                      # Entorno virtual de Python (aislado y excluido en .gitignore)
├── requirements.txt            # Dependencias Python del proyecto (LangGraph, LangChain, Pydantic, etc.)
├── .gitignore                  # Exclusión de .venv/, node_modules/, .env y temporales
├── config/                     # Configuración global, Jira API tokens y credenciales LLM
├── core/                       # Núcleo compartido (Modelos de datos, utilidades)
│   ├── schemas.py              # Definiciones Pydantic (UserStory, JiraTestCase, NavigationMap, POMMeta)
│   ├── navigation_loader.py    # Carga y validación del mapa de navegación JSON
│   └── logger.py               # Sistema de logs centralizado
├── tools/                      # HERRAMIENTAS PYTHON PROGRAMADAS Y REUTILIZABLES
│   ├── __init__.py             # Registro global de herramientas para agentes
│   ├── jira_tool.py            # Herramienta API REST de Jira (Descargar US por ID, publicar Test Cases)
│   ├── navigation_tool.py      # Herramientas de análisis y consulta del Mapa de Navegación
│   └── custom_tools.py         # Otras utilidades programadas en Python accesibles por los agentes
├── modules/
│   ├── module_1_test_writer/   # Módulo 1: Generador de Test Cases Jira (LangGraph)
│   │   ├── agent.py            # Grafo LangGraph (WriterNode + ReviewerNode con acceso a JiraTool)
│   │   ├── prompts.py          # Prompts especializados para Writer y Reviewer
│   │   └── vision_utils.py     # Manejo multimodal de capturas de pantalla
│   ├── module_2_browser_repl/  # Módulo 2: Agente TypeScript REPL & Ejecución Interactiva
│   │   ├── ts_repl_bridge.py   # Puente IPC/Subproceso de ejecución Node.js/TypeScript REPL
│   │   ├── pom_registry.py     # Carga dinámica de POMs (.ts) por vista para ahorro de tokens
│   │   └── agent.py            # Agente interactivo que evalúa TS en el REPL y consulta Tools
│   ├── module_3_test_coder/    # Módulo 3: Conversor Codegen -> Test TypeScript (@playwright/test)
│   │   ├── agent.py            # Agente que refactoriza grabación TS + Jira + POMs en test TS
│   │   └── test_runner.py      # Validación y auto-corrección del test TS usando el REPL de TS
│   ├── module_4_pom_generator/ # Módulo 4: Creador y Actualizador de POMs TypeScript (ReAct Agent + Textual TUI)
│   │   ├── agent.py            # Grafo ReAct de LangGraph con herramientas y bucle de auto-reparación
│   │   ├── prompts.py          # Prompts y especificaciones en alemán para generación/actualización de POMs
│   │   └── ui.py               # Interfaz gráfica TUI en Textual (Sidebar azul, Chat log, Input panel)
│   └── module_5_jira_assistant/# Módulo 5: Agente de Consulta, Análisis y Soporte Jira (JQL + Storage + Chat/Charts)
│       ├── agent.py            # Grafo LangGraph conversacional (Chat Agent) especializado en Jira
│       ├── jql_engine.py       # Motor de construcción y ejecución de consultas JQL (REST/Xray API)
│       ├── storage.py          # Almacenamiento local (SQLite/VectorDB) para indexación y caché masivo sin desbordar el LLM
│       ├── chart_formatter.py  # Formateador de respuestas conversacionales (Chat) con gráficos/tablas visuales
│       └── prompts.py          # Prompts para análisis sintético, detección de bloqueos y aclaración de dudas
├── ts_repl_server/             # Entorno/Runner Node.js en TypeScript (evaluación viva de Playwright TS)
│   ├── package.json            # Dependencias Node.js (@playwright/test, ts-node, typescript)
│   ├── tsconfig.json           # Configuración del compilador TypeScript
│   ├── POM/                    # Clases POM en TypeScript (*.ts) en uso activo y registradas en el REPL
│   ├── repl/                   # Servidor REPL e IPC bridge (repl.ts, pageManager.ts)
│   └── util/                   # Utilidades de Playwright y cargadores
├── tests/                      # Pruebas unitarias e integrales del propio framework
└── main.py                     # CLI u Orquestador global para ejecutar flujos combinados
```

---

## 2. Fases de Implementación y Pasos Detallados

### Fase 1: Configuración de Entornos, Núcleo Compartido y Herramientas Python (`core/` y `tools/`)

- **Paso 1.0:** Configuración Inicial de Entornos y Dependencias:
  - Crear el entorno virtual Python `.venv/` en la raíz y configurar `requirements.txt` (`langgraph`, `langchain`, `pydantic`, `httpx`, `jinja2`, etc.).
  - Inicializar `ts_repl_server/package.json` e instalar dependencias Node.js (`@playwright/test`, `ts-node`, `typescript`).
  - Crear `.gitignore` asegurando la exclusión de `.venv/`, `ts_repl_server/node_modules/` y variables de entorno `.env`.
- **Paso 1.1:** Definir modelos Pydantic centralizados (`core/schemas.py`):
  - `NavigationMap`: Vistas, rutas, selectores TypeScript/CSS/XPath clave, condiciones y parámetros.
  - `JiraTestCase`: Título, prerrequisitos, pasos (acción/resultado esperado), criterios de aceptación vinculados, ID de la US en Jira.
  - `POMMetadata`: Nombre de clase TS, vista asociada, métodos exportados, locators.
- **Paso 1.2:** Implementar `tools/jira_tool.py` (Herramienta Jira REST API):
  - Descarga automática de detalles de Historias de Usuario (título, descripción, criterios de aceptación, adjuntos) usando el Issue Key de Jira (`fetch_user_story(issue_key)`).
  - Publicación / Actualización opcional de los casos de prueba generados directamente en Jira mediante la REST API (`create_jira_test_issue(...)`).
- **Paso 1.3:** Registrar el Toolbox global (`tools/`):
  - Exponer herramientas estructuradas (LangChain `@tool`) para que cualquier módulo las pueda invocar de forma estándar.

### Fase 2: Módulo 1 — Agente Generador de Casos de Prueba Jira (`modules/module_1_test_writer`)

- **Paso 2.1:** Rediseñar el estado del grafo LangGraph (`AgentState`):
  - Campos: `jira_issue_key`, `user_story` (extraída automáticamente por `jira_tool`), `navigation_map`, `screenshots` (List[str] en base64 opcionales), `jira_test_draft`, `review_feedback`, `iteration`, `is_approved`.
- **Paso 2.2:** Implementar `WriterNode`:
  - Utiliza `jira_tool` para obtener la Historia de Usuario por su ID si no se pasa el texto plano.
  - Procesa la Historia de Usuario, el Mapa de Navegación y la lista opcional de imágenes multimodales (*vision prompt*).
  - Genera/corrige el caso de prueba en formato Jira.
- **Paso 2.3:** Implementar `ReviewerNode`:
  - Prompt enfocado exclusivamente en la verificación de Criterios de Aceptación (AC) traídos directamente desde Jira y la coherencia de la navegación.
  - Devuelve aprobación explícita o lista de correcciones.
- **Paso 2.4:** Probar el módulo conectándose a Jira REST API y con capturas de pantalla opcionales.

### Fase 3: Módulo 2 — Agente con REPL de Playwright en TypeScript y Acceso a Tools (`modules/module_2_browser_repl`)

- **Paso 3.1:** Crear `TSPlaywrightREPLBridge` y `ts_repl_server/`:
  - Servidor/Runner en **Node.js + TypeScript (`ts-node`)** que mantiene una sesión viva de Playwright TS (`chromium.launch()`, `context`, `page`).
  - Puente IPC (stdin/stdout JSON-RPC o WebSocket) desde el agente Python para evaluar código **TypeScript** en tiempo real.
  - **Canal compartido:** Permite que el **usuario** envíe directamente snippets de TypeScript al REPL o ejecute acciones interactivas.
- **Paso 3.2:** Integración con Herramientas Python (`tools/`):
  - El agente del Módulo 2 puede ejecutar herramientas Python (ej. consultar detalles extra de Jira, buscar en el `NavigationMap`, o invocar scripts de apoyo) mientras interactúa con el REPL de TS.
- **Paso 3.3:** Diseñar el `DynamicPOMLoader`:
  - Escanea `shared_poms/*.ts`.
  - Transpila e inyecta en el REPL de Node.js **únicamente los POMs (.ts) necesarios** para la vista solicitada según el `NavigationMap` (*ahorro crítico de tokens*).

### Fase 4: Módulo 4 — Agente Generador/Actualizador de POMs en TypeScript (`modules/module_4_pom_generator`)

- **Paso 4.1:** Agente ReAct Autónomo en LangGraph (`agent.py` & `prompts.py`):
  - **Bucle de Razonamiento y Herramientas (`StateGraph`):** El agente opera en un bucle autónomo utilizando herramientas de sistema (`read_workspace_file`, `write_workspace_file`, `eval_in_repl`, `inspect_aria_snapshot`, `take_screenshot`). Puede leer POMs de referencia en `ts_repl_server/POM/`, inspeccionar vistas activas, evaluar snippets en el REPL y auto-corregir errores de compilación o de locators de forma transparente.
  - **Prompts y Guías en Alemán (`prompts.py`):** Especificaciones de código TypeScript Playwright fuertemente tipado (`Page`, `Locator`, métodos `async`).
  - **Persistencia de Memoria:** Utiliza `MemorySaver` de LangGraph para mantener conversaciones multiturno continuas por `thread_id`.

- **Paso 4.2:** Interfaz Gráfica TUI con Textual (`ui.py`):
  - Aplicación `POMGeneratorTUI` construida con la librería **Textual** que recrea el diseño visual especificado:
    - **Sidebar Izquierdo (Blau `#4285F4`):** Botones verdes `Add aria Snapshot` y `Add screenshot` para inyectar inspecciones del REPL en vivo al contexto del chat.
    - **Panel Principal Derecho:**
      - **Sección Chat Superior (Weiß `#FFFFFF`):** Área `RichLog` que renderiza el historial de mensajes, pensamiento de la IA, invocaciones a herramientas y respuestas finales.
      - **Sección User Input Inferior (Grau `#757575`):** Área de entrada de texto con la propiedad de título `User Input` y botón redondeado en blanco `button send`.

- **Flujo de Trabajo del Agente:**
  1. El usuario inicia la TUI (`python main.py` opción 4 o `python -m modules.module_4_pom_generator.ui`).
  2. Presiona los botones del Sidebar (`Add aria Snapshot` / `Add screenshot`) para incluir contexto visual/DOM si lo requiere.
  3. Escribe las instrucciones y hace clic en `button send` (o presiona `Enter`).
  4. El agente ejecuta autónomamente el bucle ReAct: inspecciona, genera o actualiza el POM `.ts`, valida en el REPL y se auto-corrige si ocurren errores.
  5. El archivo `.ts` se guarda automáticamente en `ts_repl_server/POM/` y el agente informa el resultado en el panel de chat.


### Fase 5: Módulo 3 — Agente Conversor de Grabación a Test en TypeScript (`modules/module_3_test_coder`)

- **Paso 5.1:** Captura de entradas y acceso a Jira:
  - Recibe el código generado por `npx playwright codegen` (en sintaxis TypeScript / `@playwright/test`).
  - Obtiene el Caso de Prueba de Jira (directamente desde la REST API mediante `jira_tool` o del Módulo 1).
  - Recibe la plantilla/formato de test deseado en TypeScript.
- **Paso 5.2:** Agente Refactorizador a POMs TypeScript:
  - Reemplaza las líneas grabadas directas (`page.locator(...)`) por invocaciones a métodos de las clases POM en TypeScript (`shared_poms/*.ts`).
  - Mantiene el tipado de TypeScript y la coherencia con los pasos del Caso de Prueba de Jira.
- **Paso 5.3:** Ejecución y Autocorrección en el REPL TypeScript:
  - Envía el código de prueba `.ts` generado al REPL de Node.js (Módulo 2) para su ejecución en tiempo real.
  - Si la ejecución lanza excepciones, el agente auto-corrige el código `.ts` iterativamente.

### Fase 6: Comunicación Inter-Módulo y Pipeline E2E (`main.py`)

- **Paso 6.1:** Crear el orquestador global (`main.py`):
  - **Flujo Completo Integrado:**
    1. **Módulo 1:** Solicita Jira Issue Key $\rightarrow$ `jira_tool` descarga la US vía REST API $\rightarrow$ Genera Caso de Prueba Jira.
    2. **Módulo 4:** Analiza las vistas del test $\rightarrow$ Crea/actualiza POMs en TypeScript (`shared_poms/`).
    3. **Usuario / Playwright Codegen (TS):** Graba interacción en la aplicación web.
    4. **Módulo 3:** Grabación TS + Caso de Prueba Jira + POMs TS $\rightarrow$ Archivo de test automatizado `@playwright/test` en TypeScript.
    5. **Módulo 2 (TS REPL + Tools Python):** Ejecución interactiva, prueba y auto-corrección en vivo.
    6. **Módulo 5 (Jira Assistant Chat & Analytics):** Asistente conversacional de consulta en tiempo real para análisis de bugs, test plans y trazabilidad Jira.
- **Paso 6.2:** Exponer CLI para ejecución individual por módulo:
  ```bash
  python -m modules.module_1_test_writer --jira-id QA-123 --nav nav.json
  python -m modules.module_2_browser_repl --interactive-ts
  python -m modules.module_5_jira_assistant --chat
  ```

---

### Fase 7: Módulo 5 — Agente de Consulta, Análisis Masivo y Soporte Jira (`modules/module_5_jira_assistant`)

- **Paso 7.1:** Diseñar el Motor de Almacenamiento y Caché Local (`storage.py`):
  - Base de datos local (SQLite / DuckDB / Vector Store) para persistir e indexar grandes volúmenes de issues, bugs, user stories, comentarios y ejecuciones de test de Xray.
  - Implementar paginación y almacenamiento diferido/por lotes que evita cargar miles de elementos directamente en la ventana de contexto del LLM (*Context Window Management*).
  - Permitir búsquedas híbridas (SQL/vectorial/filtrado por metadatos) sobre el almacenamiento local.
- **Paso 7.2:** Implementar el Motor JQL (`jql_engine.py`):
  - Integración avanzada con la REST API de Jira y Xray para construir y ejecutar consultas JQL complejas (filtrado por proyecto, sprint, estado, assignee, etiquetas, componentes, etc.).
  - Paginación automática de respuestas de la API de Jira y volcado directo al almacenamiento local (`storage.py`).
- **Paso 7.3:** Desarrollar el Agente Conversor y Formateador Visual (`chart_formatter.py`):
  - Interfaz y formato de respuesta tipo **Chat** conversacional.
  - Generación de resúmenes sintéticos con apoyo visual de tipo **Chart / Tabla / Mermaid**:
    - Distribución y volumen de bugs por prioridad/estado.
    - Avance y porcentaje de éxito/fallo en Test Plans y Test Executions.
    - Matriz de trazabilidad entre User Stories, Test Cases y Defectos.
- **Paso 7.4:** Implementar el Grafo Conversacional y Prompts (`agent.py` & `prompts.py`):
  - Grafo LangGraph conversacional que mantiene el historial de chat con el usuario.
  - Lógica de decisión: dada la consulta en lenguaje natural del usuario, traduce la intención a JQL, consulta/actualiza el almacenamiento local, realiza operaciones de agregación local y presenta explicaciones claras para resolver problemas, dudas o cuellos de botella.
- **Paso 7.5:** Pruebas e Integración:
  - Validar consultas masivas de >500 issues comprobando la conservación del contexto del LLM y la rapidez del almacenamiento local.
  - Verificar las respuestas en modo interactivo CLI y formato gráfico Markdown/Mermaid/Tabla.

## 3. Preguntas y Aclaraciones para el Usuario

> [!QUESTION]
> Para ajustar los detalles de la integración con Jira REST API y las herramientas Python:

1. **Jira REST API:**
   - ¿Qué autenticación utiliza tu servidor de Jira? (ej. API Token personal, Basic Auth con correo + token, u OAuth2).
   - ¿En qué campos de Jira se almacenan habitualmente las historias de usuario y los criterios de aceptación en tu organización?

2. **Herramientas Python Existentes:**
   - ¿Cuáles son los nombres/módulos de las herramientas Python que ya tienes programadas para añadirlas directamente al registro en `tools/`?

3. **Proveedor y Modelo de LLM:**
   - ¿Utilizarás OpenAI (GPT-4o), Anthropic (Claude 3.5 Sonnet) u otro modelo para los agentes?
