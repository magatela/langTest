# Plan de Implementación: Sistema Modular de Agentes QA con LangGraph, Playwright (TS Output & REPL) y Herramientas Python (Jira REST API)

## 1. Visión General de la Arquitectura y Modularidad

El sistema consta de un motor de agentes en Python (basado en LangGraph/LangChain) que interactúa con un **Toolkit de Herramientas Python compartidas** (incluyendo integración con **Jira REST API** para la descarga automática de Historias de Usuario), orquesta y genera **código de automatización exclusivamente en TypeScript (`.ts`)** e interactúa con un **REPL de Playwright en TypeScript (Node.js/ts-node)**.

El sistema se compone de **4 módulos independientes**, un **Toolbox de Herramientas Reutilizables** y un **núcleo de integración compartida (Core/Shared)**.

### Estructura de Directorios Propuesta

```text
qa_agent_system/
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
│   └── module_4_pom_generator/ # Módulo 4: Creador y Actualizador de POMs TypeScript
│       ├── agent.py            # Agente para analizar vistas y generar/actualizar clases POM (.ts)
│       └── templates/          # Plantillas de POM TS por tipo de vista (Form.ts.j2, Table.ts.j2, etc.)
├── shared_poms/                # Repositorio de clases POM en TypeScript (*.ts)
├── ts_repl_server/             # Entorno/Runner Node.js en TypeScript (evaluación viva de Playwright TS)
│   ├── package.json
│   ├── tsconfig.json
│   └── repl_server.ts          # Servidor REPL en TS que mantiene el browser context activo
├── tests/                      # Pruebas unitarias e integrales del propio framework
├── plan.txt                    # Documentación del plan de desarrollo (formato Markdown)
└── main.py                     # CLI u Orquestador global para ejecutar flujos combinados
```

---

## 2. Fases de Implementación y Pasos Detallados

### Fase 1: Núcleo Compartido, Contratos de Datos y Herramientas Python (`core/` y `tools/`)

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

- **Paso 4.1:** Crear motor de plantillas de POM en TypeScript (`templates/`):
  - Plantillas Jinja2 configurables para generar clases TypeScript Playwright (ej. `FormPage.ts`, `TablePage.ts`, `ModalPage.ts`).
  - Utiliza tipado fuerte de TypeScript (`Page`, `Locator`, interfaces de datos).
- **Paso 4.2:** Implementar Agente de POMs:
  - Analiza la estructura DOM/HTML o especificaciones de una vista.
  - Genera una nueva clase TypeScript POM o actualiza un archivo `.ts` existente respetando la plantilla elegida por el usuario.
- **Paso 4.3:** Validación del POM TS:
  - Importa dinámicamente el nuevo POM `.ts` en el REPL de TypeScript (Módulo 2) y valida la resolución de locators y llamadas a métodos en vivo.

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
- **Paso 6.2:** Exponer CLI para ejecución individual por módulo:
  ```bash
  python -m modules.module_1_test_writer --jira-id QA-123 --nav nav.json
  python -m modules.module_2_browser_repl --interactive-ts
  ```

---

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
