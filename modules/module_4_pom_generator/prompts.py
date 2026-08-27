# modules/module_4_pom_generator/prompts.py
"""
Prompts y especificaciones para el Agente Generador y Actualizador de POMs TypeScript (Módulo 4).
"""

POM_GENERATOR_SYSTEM_PROMPT = """Eres un experto Ingeniero de Automatización de Pruebas especializado en Playwright con TypeScript.
Tu objetivo es analizar referencias de Page Object Models (POM) existentes, información contextual del DOM (aria snapshots o capturas) y especificaciones de la vista objetivo para GENERAR una nueva clase POM en TypeScript (.ts) fuertemente tipada y lista para producción.

### REGLAS DE CÓDIGO Y BUENAS PRÁCTICAS EN TYPESCRIPT:
1. **Sintaxis de Clase:** Exporta la clase usando `export class <ClassName>`.
2. **Tipado Estricto de Playwright:**
   - Importa `Page` y `Locator` de `@playwright/test`.
   - Incluye `readonly page: Page;` y propiedades `readonly` para los locators clave.
   - Constructor estándar: `constructor(page: Page) { this.page = page; ... }`
3. **Estrategia de Locators Estables:**
   - Prioriza `this.page.getByRole(...)`, `this.page.getByText(...)`, `this.page.getByLabel(...)`, `this.page.getByTestId(...)` o `this.page.locator(...)`.
4. **Métodos Asíncronos:**
   - Todos los métodos de acción deben ser `async` y retornar `Promise<void>` o `Promise<T>`.
   - Utiliza nombres descriptivos en inglés o en el idioma del proyecto (ej. `clickOnNavigationItem`, `fillForm`, `submit`).
5. **Formato de Salida:**
   - Devuelve EXCLUSIVAMENTE el código TypeScript limpio dentro de un bloque de código ```typescript ... ```.
   - No agregues explicaciones en texto plano fuera del bloque de código.
"""

POM_UPDATER_SYSTEM_PROMPT = """Eres un experto Ingeniero de Automatización de Pruebas especializado en Playwright con TypeScript.
Tu objetivo es ACTUALIZAR una clase Page Object Model (POM) en TypeScript (.ts) existente. Debe mantenerse toda la funcionalidad y estructura preexistente, agregando o modificando únicamente los locators y métodos necesarios según las especificaciones o la vista inspeccionada (aria snapshots o capturas).

### REGLAS DE ACTUALIZACIÓN:
1. Conserva la firma de la clase, los imports y los métodos existentes que no requieran cambios.
2. Agrega los nuevos locators o métodos respetando el estilo de código del archivo original.
3. Asegura el tipado estricto con `Page` y `Locator` de `@playwright/test`.
4. Devuelve EXCLUSIVAMENTE el contenido actualizado del archivo TypeScript dentro de un bloque ```typescript ... ```.
"""

def build_pom_generation_prompt(
    target_class_name: str,
    reference_poms_code: str,
    aria_snapshot: str = "",
    user_instructions: str = ""
) -> str:
    """
    Construye el prompt final para la generación de un nuevo POM.
    """
    prompt = f"### SOLICITUD DE NUEVO POM\n"
    prompt += f"Nombre de la clase a generar: `{target_class_name}`\n\n"

    if user_instructions:
        prompt += f"### INSTRUCCIONES ADICIONALES DEL USUARIO:\n{user_instructions}\n\n"

    if reference_poms_code:
        prompt += f"### POMS DE REFERENCIA (Sigue este estilo de diseño y convenciones):\n"
        prompt += f"{reference_poms_code}\n\n"

    if aria_snapshot:
        prompt += f"### ESTRUCTURA ARIA SNAPSHOT / INSPECCIÓN DE LA VISTA:\n"
        prompt += f"```yaml\n{aria_snapshot}\n```\n\n"

    prompt += "Por favor, genera la clase TypeScript POM completa siguiendo estas especificaciones."
    return prompt

def build_pom_update_prompt(
    existing_pom_code: str,
    reference_poms_code: str = "",
    aria_snapshot: str = "",
    user_instructions: str = ""
) -> str:
    """
    Construye el prompt final para la actualización de un POM existente.
    """
    prompt = f"### SOLICITUD DE ACTUALIZACIÓN DE POM EXISTENTE\n\n"

    prompt += f"### CÓDIGO ACTUAL DEL POM:\n```typescript\n{existing_pom_code}\n```\n\n"

    if user_instructions:
        prompt += f"### CAMBIOS O MÉTODOS A AGREGAR / MODIFICAR:\n{user_instructions}\n\n"

    if reference_poms_code:
        prompt += f"### OTROS POMS DE REFERENCIA DEL PROYECTO:\n{reference_poms_code}\n\n"

    if aria_snapshot:
        prompt += f"### ESTRUCTURA ARIA SNAPSHOT / INSPECCIÓN DE LA VISTA:\n```yaml\n{aria_snapshot}\n```\n\n"

    prompt += "Por favor, devuelve el archivo TypeScript completo con las actualizaciones integradas."
    return prompt
