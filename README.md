# QA Agent System (langTest) 🤖🧪

Sistema Modular de Agentes de Inteligencia Artificial para la Automatización de Pruebas de Software (QA) basado en **LangGraph**, **Playwright TypeScript** y **Jira REST API / Xray**.

---

## 📌 Visión General

`qa_agent_system` es un framework modular diseñado para automatizar el ciclo completo de pruebas QA:
1. **Generación de Casos de Prueba:** Descarga Historias de Usuario desde Jira REST API y utiliza agentes iterativos (Writer y Reviewer en LangGraph) para escribir y revisar casos de prueba estructurados, con análisis asistido por LLM de referencias cruzadas.
2. **Entorno de Ejecución TS REPL:** Inicia un servidor Node.js + TypeScript con Playwright para evaluar snippets e interactuar dinámicamente con el navegador (modo aislado para el usuario o modo IPC para los agentes).
3. **Conversión a TypeScript & POM:** Transforma grabaciones de `playwright codegen` en archivos de pruebas `@playwright/test` fuertemente tipados utilizando el patrón Page Object Model (POM).
4. **Generador y Actualizador de POMs TypeScript:** Analiza componentes web, estructuras ARIA e insumos visuales desde el REPL para crear o actualizar clases Page Object Model en TypeScript (`.ts`) alineadas con los POMs activos del proyecto (`ts_repl_server/POM/`).

---

## 📁 Estructura del Proyecto

```text
langTest/
├── .venv/                      # Entorno virtual de Python (excluido en .gitignore)
├── .env.example                # Plantilla de variables de entorno
├── requirements.txt            # Dependencias Python (LangGraph, LangChain, PyYAML, Rich, etc.)
├── .gitignore                  # Reglas de exclusión de git (.venv/, node_modules/, secretos)
├── config/                     # Gestor de configuración y plantillas
│   ├── config_loader.py        # Carga segura de credenciales de Jira, LLM y Playwright
│   └── config.yaml.example     # Plantilla de configuración YAML
├── core/                       # Núcleo compartido
│   └── schemas.py              # Definiciones Pydantic de datos
├── tools/                      # Herramientas reutilizables en Python
│   ├── jira/                   # Clientes REST para Jira Core y Xray (JiraAPI, XrayAPI, jiraWorker)
│   └── jira_tool.py            # Envoltorio unificado de herramientas para agentes
├── modules/                    # Módulos del sistema de agentes
│   ├── module_1_test_writer/   # Módulo 1: Generador de Test Cases (WriterNode + ReviewerNode)
│   │   ├── agent.py            # Grafo LangGraph del Módulo 1 y recomendador de referencias LLM
│   │   └── prompts/            # Prompts especializados (testCaseWriter, testCaseReviewer, navigation)
│   ├── module_2_browser_repl/  # Módulo 2: Agente TS REPL & Runner
│   │   └── ts_repl_bridge.py   # Puente conector IPC entre Python y Node.js REPL (eval_code, get_aria_snapshot)
│   ├── module_3_test_coder/    # Módulo 3: Conversor Codegen -> Test TypeScript
│   ├── module_4_pom_generator/ # Módulo 4: Creador/Actualizador de clases POM (.ts)
│   │   ├── agent.py            # Agente generador y actualizador de clases POM (.ts)
│   │   └── prompts.py          # Prompts y especificaciones de código TypeScript Playwright
│   └── module_5_jira_assistant/# Módulo 5: Asistente conversacional de Jira (JQL + Caché + Visuals)
├── ts_repl_server/             # Entorno Runner de Node.js + TypeScript (Playwright REPL)
│   ├── package.json            # Dependencias Node.js (@playwright/test, tsx, js-yaml, typescript)
│   ├── tsconfig.json           # Configuración del compilador TypeScript
│   ├── POM/                    # Clases POM en TypeScript (*.ts) en uso activo y registradas en el REPL
│   ├── util/                   # util.ts y configLoader.ts (Cargador YAML para Node.js)
│   └── repl/                   # Servidor REPL e IPC bridge (repl.ts, pageManager.ts)
├── tests/                      # Suite de Pruebas Unitarias Offline
├── main.py                     # CLI Interactivo con interfaz Rich y salida Markdown
└── README.md                   # Documentación principal del proyecto
```

---

## 🚀 Instalación y Configuración

### 1. Requisitos Previos
* **Python 3.10+**
* **Node.js 18+** y `npm`

### 2. Configurar el Entorno Python
```bash
# Crear el entorno virtual
python -m venv .venv

# Activar el entorno virtual
# En Windows (PowerShell):
.venv\Scripts\Activate.ps1
# En Linux/macOS:
source .venv/bin/activate

# Instalar dependencias de Python
pip install -r requirements.txt
```

### 3. Configurar el Entorno Node.js (TypeScript / Playwright)
```bash
cd ts_repl_server
npm install
npx playwright install chromium
cd ..
```

### 4. Configurar Credenciales Centralizadas
Copia `config/config.yaml.example` a `config/config.yaml` o `.env.example` a `.env`:
```bash
cp config/config.yaml.example config/config.yaml
```
Edita `config/config.yaml`:
```yaml
apiBase: "https://api.openai.com/v1"
apiKey: "tu_openai_api_key"

models:
  - model: "gpt-4o"
    temperature: 0.2
  - model: "gpt-4o"
    temperature: 0.1

jira:
  base_url: "https://jira.tu-empresa.com/"
  prefix: "PDNEU"
  user: "tu_usuario@empresa.com"
  password: "tu_password_o_token"

playwright:
  use_custom_chrome_path: false
  chrome_path: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
  headless: false
  results_dir: "./results"
```

---

## 💻 Uso del Servidor REPL de TypeScript (`ts_repl_server`)

El servidor REPL en TypeScript admite dos modalidades de uso: **aislado para el usuario humano** e **integrado dinámicamente con los agentes de IA (IPC)**.

### Option A: Uso Aislado para el Usuario Humano 🖥️

Puedes ejecutar e interactuar libremente con el REPL sin intermediación de agentes:

1. **Desde la terminal directa:**
   ```bash
   cd ts_repl_server
   npm start
   ```
2. **Desde el CLI interactivo (`main.py`):**
   * Ejecuta `python main.py` $\rightarrow$ Selecciona **Opción 2** $\rightarrow$ Selecciona **Opción 1 (Modo Usuario Humano)**.

**Características del Modo Humano:**
* Acepta la ruta a cualquier archivo `.ts` (con o sin el delimitador `#NBELPH69`) o código TypeScript pegado directamente en la consola (`LOG## Datei/Code > `).
* Procesa sentencias `import` y `export` de manera transparente cargando de fondo los Page Object Models (POMs) e inyectando las instancias globales (`page`, `navigation`, `zeitraeume`, `expect`, `executeStep`, etc.).

---

### Option B: Uso Integrado con Agentes de IA (Puente IPC JSON-RPC) 🤖

Los agentes de Python (Módulo 2, 3 y 4) controlan el servidor REPL mediante el conector **`TSPlaywrightREPLBridge`** (`modules/module_2_browser_repl/ts_repl_bridge.py`):

1. **Invocación desde Código Python:**
   ```python
   from modules.module_2_browser_repl.ts_repl_bridge import TSPlaywrightREPLBridge

   bridge = TSPlaywrightREPLBridge()
   if bridge.start():
       # Evaluar código TypeScript en tiempo real dentro del navegador activo
       result = bridge.eval_code("await navigation.clickOnNavigationItem('Zeiträume');")
       print(result) # {"status": "success", "result": "Ausführung erfolgreich"}
       bridge.stop()
   ```

2. **Prueba Interactiva del Puente IPC:**
   * Ejecuta `python main.py` $\rightarrow$ Selecciona **Opción 2** $\rightarrow$ Selecciona **Opción 2 (Probar Puente IPC de Agentes)**.

**Características del Modo Agente (IPC):**
* Arranca el subproceso con el parámetro `--ipc`.
* Intercambia objetos JSON por `stdin`/`stdout` evitando bloqueos de consola.
* Permite al agente enviar fragmentos de TypeScript, evaluar la navegación en vivo y capturar excepciones para autocorrección de código.

---

## 💻 Uso de la CLI Interactiva (`main.py`)

Inicia la consola interactiva con la interfaz estilizada con la librería `rich` y renderizado continuo en Markdown:

```bash
python main.py
```

### Menú de Opciones:
1. 📝 **Generar Casos de Prueba Jira (Módulo 1):** Ingresa un Issue Key (ej. `PDNEU-1234`), analiza referencias cruzadas mediante LLM y observa el bucle de razonamiento de LangGraph (Writer y Reviewer).
2. 💻 **REPL TypeScript & Playwright (Módulo 2):** Permite arrancar el REPL independiente para uso humano o probar la comunicación IPC del puente con los agentes.
3. 🔄 **Codegen -> Test TypeScript (Módulo 3):** Refactorización automática de selecciones directas a Page Object Models.
4. 🏗️ **Generador de POMs TypeScript (Módulo 4):** Creación asistida por IA de clases de interfaz POM.
5. 🧪 **Ejecutar Pruebas Unitarias:** Corre la suite completa de pruebas unitarias 100% offline.
6. ⚙️ **Verificar Entorno:** Muestra la configuración activa y el estado de las credenciales.

---

## 🏗️ Uso del Generador y Actualizador de POMs TypeScript (Módulo 4)

El **Módulo 4** (`modules/module_4_pom_generator`) permite crear nuevas clases **Page Object Model (POM)** o actualizar archivos `.ts` existentes respetando las convenciones del proyecto y el tipado fuerte de `@playwright/test`.

### Formas de Uso:

#### Option A: Desde la CLI Interactiva (`main.py`)
1. Ejecuta `python main.py`.
2. Selecciona la **Opción 4** (`🏗️ Generador de POMs TypeScript`).
3. Sigue los pasos interactivos:
   - Selecciona entre **Crear un nuevo POM** o **Actualizar uno existente**.
   - Ingresa el nombre de la clase/archivo objetivo (ej. `LoginPage.ts`).
   - Elige los **POMs referenciales** activos en `ts_repl_server/POM/` que el LLM debe usar como modelo de código.
   - *(Opcional)* Conecta con el servidor REPL (Módulo 2) para capturar el **Aria Snapshot** del elemento o componente web activo.
   - Ingresa instrucciones adicionales (ej. *"Añadir método para enviar el formulario de registro"*).

#### Option B: Invocación Programática en Python
```python
from modules.module_4_pom_generator.agent import run_pom_generator_agent

result = run_pom_generator_agent(
    mode="create",  # "create" o "update"
    target_name="LoginPage.ts",
    reference_files=["NavigationPage.ts", "BerichtMainPage.ts"],
    aria_snapshot="- button 'Login'",
    user_instructions="Crear locators estables para login",
    validate=False
)

print(f"POM generado en: {result['path']}")
print(result["code"])
```

---

## 🧪 Pruebas Unitarias Offline

Para verificar el correcto funcionamiento del framework sin requerir conexión a internet ni llamadas activas a las APIs externas de Jira u OpenAI, ejecuta:

```bash
python -m unittest discover tests
```

Salida esperada:
```text
...............................
----------------------------------------------------------------------
Ran 31 tests in 2.888s

OK
```

Las pruebas validan:
* `test_config.py`: Carga y fallbacks del gestor de configuración YAML/env.
* `test_jira_tools.py`: Clientes REST, peticiones mockeadas y formato de respuesta.
* `test_module_1.py`: Carga de prompts, recomendador asistido por LLM y ciclo de ejecución mock de LangGraph.
* `test_repl_server.py`: Estructura del servidor REPL de TypeScript y cargadores de configuración de Playwright.
* `test_module_4.py`: Prompts de TypeScript, lectura de referencias `ts_repl_server/POM/`, parseo de código y modos de creación/actualización con mock LLM.
* `test_module_5.py`: Asistente Jira, motor JQL, almacenamiento SQLite local y generador de respuestas visuales.

---

## 📄 Licencia y Contribución
Proyecto de automatización de QA bajo arquitectura modular de agentes de IA. Reservados todos los derechos.
