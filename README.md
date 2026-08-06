# QA Agent System (langTest) 🤖🧪

Sistema Modular de Agentes de Inteligencia Artificial para la Automatización de Pruebas de Software (QA) basado en **LangGraph**, **Playwright TypeScript** y **Jira REST API / Xray**.

---

## 📌 Visión General

`qa_agent_system` es un framework modular diseñado para automatizar el ciclo completo de pruebas QA:
1. **Generación de Casos de Prueba:** Descarga Historias de Usuario desde Jira REST API y utiliza agentes iterativos (Writer y Reviewer en LangGraph) para escribir y revisar casos de prueba estructurados.
2. **Entorno de Ejecución TS REPL:** Inicia un servidor Node.js + TypeScript con Playwright para evaluar snippets e interactuar dinámicamente con el navegador.
3. **Conversión a TypeScript & POM:** Transforma grabaciones de `playwright codegen` en archivos de pruebas `@playwright/test` fuertemente tipados utilizando el patrón Page Object Model (POM).

---

## 📁 Estructura del Proyecto

```text
langTest/
├── .venv/                      # Entorno virtual de Python (excluido en .gitignore)
├── .env.example                # Plantilla de variables de entorno
├── requirements.txt            # Dependencias Python (LangGraph, LangChain, PyYAML, Rich, etc.)
├── .gitignore                  # Reglas de exclusión de git (.venv/, node_modules/, secretos)
├── config/                     # Gestor de configuración y plantillas
│   ├── config_loader.py        # Carga segura de credenciales de Jira y LLM
│   └── config.yaml.example     # Plantilla de configuración YAML
├── core/                       # Núcleo compartido
│   └── schemas.py              # Definiciones Pydantic de datos
├── tools/                      # Herramientas reutilizables en Python
│   ├── jira/                   # Clientes REST para Jira Core y Xray (JiraAPI, XrayAPI, jiraWorker)
│   └── jira_tool.py            # Envoltorio de alto nivel para agentes LangGraph
├── modules/                    # Módulos del sistema de agentes
│   ├── module_1_test_writer/   # Módulo 1: Generador de Test Cases (WriterNode + ReviewerNode)
│   │   ├── agent.py            # Grafo LangGraph del Módulo 1
│   │   └── prompts/            # Prompts especializados (testCaseWriter, testCaseReviewer, navigation)
│   ├── module_2_browser_repl/  # Módulo 2: Agente TS REPL & Runner
│   ├── module_3_test_coder/    # Módulo 3: Conversor Codegen -> Test TypeScript
│   └── module_4_pom_generator/ # Módulo 4: Creador/Actualizador de clases POM (.ts)
├── shared_poms/                # Repositorio central de clases POM TypeScript (*.ts)
├── ts_repl_server/             # Entorno Runner de Node.js + TypeScript (Playwright REPL)
│   ├── package.json            # Dependencias Node.js (@playwright/test, ts-node, typescript)
│   ├── tsconfig.json           # Configuración del compilador TypeScript
│   ├── POM/                    # Clases POM compilables
│   └── repl/                   # Servidor REPL e IPC bridge
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

### 4. Configurar Credenciales
Copia la plantilla `.env.example` a `.env` o `config/config.yaml.example` a `config/config.yaml`:
```bash
cp .env.example .env
```
Edita `.env` con tus datos:
```env
OPENAI_API_KEY=tu_openai_api_key
OPENAI_API_BASE=https://api.openai.com/v1

JIRA_BASE_URL=https://jira.tu-empresa.com/
JIRA_PREFIX=PDNEU
JIRA_USER=tu_usuario@empresa.com
JIRA_PASSWORD=tu_password_o_token
```

---

## 💻 Uso de la CLI Interactiva (`main.py`)

Inicia la consola interactiva con la interfaz estilizada con la librería `rich` y renderizado continuo en Markdown:

```bash
python main.py
```

### Menú de Opciones:
1. 📝 **Generar Casos de Prueba Jira (Módulo 1):** Ingresa un Issue Key (ej. `PDNEU-1234`) y observa el bucle de razonamiento de LangGraph (Writer y Reviewer) renderizado en tiempo real en cuadros Markdown.
2. 💻 **REPL TypeScript & Playwright (Módulo 2):** Instrucciones para levantar el servidor interactivo de Playwright en TS.
3. 🔄 **Codegen -> Test TypeScript (Módulo 3):** Refactorización automática de selecciones directas a Page Object Models.
4. 🏗️ **Generador de POMs TypeScript (Módulo 4):** Creación asistida por IA de clases de interfaz POM.
5. 🧪 **Ejecutar Pruebas Unitarias:** Corre la suite completa de pruebas unitarias 100% offline.
6. ⚙️ **Verificar Entorno:** Muestra la configuración activa y el estado de las credenciales.

---

## 🧪 Pruebas Unitarias Offline

Para verificar el correcto funcionamiento del framework sin requerir conexión a internet ni llamadas activas a las APIs externas de Jira u OpenAI, ejecuta:

```bash
python -m unittest discover tests
```

Salida esperada:
```text
.......
----------------------------------------------------------------------
Ran 7 tests in 0.015s

OK
```

Las pruebas validan:
* `test_config.py`: Carga y fallbacks del gestor de configuración.
* `test_jira_tools.py`: Clientes REST, peticiones mockeadas y formato de respuesta.
* `test_module_1.py`: Carga de prompts y ciclo de ejecución mock de LangGraph.

---

## 📄 Licencia y Contribución
Proyecto de automatización de QA bajo arquitectura modular de agentes de IA. Reservados todos los derechos.
