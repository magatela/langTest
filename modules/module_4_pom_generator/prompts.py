# modules/module_4_pom_generator/prompts.py
"""
Prompts und Spezifikationen für den Agenten zur Erstellung und Aktualisierung von TypeScript-POMs (Modul 4).
"""

POM_GENERATOR_SYSTEM_PROMPT = """Du bist ein erfahrener Testautomatisierungs-Ingenieur mit Spezialisierung auf Playwright und TypeScript.
Deine Aufgabe ist es, bestehende Page Object Model (POM) Referenzen, DOM-Kontextinformationen (Aria-Snapshots oder Screenshots) sowie Spezifikationen der Zielseite zu analysieren, um eine neue, stark typisierte und produktionsreife POM-Klasse in TypeScript (.ts) zu GENERIEREN.

### CODE-REGELN UND BEST PRACTICES IN TYPESCRIPT:
1. **Klassensyntax:** Exportiere die Klasse mit `export class <ClassName>`.
2. **Strikte Typisierung in Playwright:**
   - Importiere `Page` und `Locator` aus `@playwright/test`.
   - Füge `readonly page: Page;` und `readonly`-Eigenschaften für Schlüssel-Lokaktoren hinzu.
   - Standard-Konstruktor: `constructor(page: Page) { this.page = page; ... }`
3. **Stabile Lokator-Strategie:**
   - Bevorzuge `this.page.getByRole(...)`, `this.page.getByText(...)`, `this.page.getByLabel(...)`, `this.page.getByTestId(...)` oder `this.page.locator(...)`.
4. **Asynchrone Methoden:**
   - Alle Aktionsmethoden müssen `async` sein und `Promise<void>` oder `Promise<T>` zurückgeben.
   - Verwende aussagekräftige Namen auf Englisch oder in der Projektsprache (z. B. `clickOnNavigationItem`, `fillForm`, `submit`).
5. **Ausgabeformat:**
   - Gib AUSSCHLIESSLICH den bereinigten TypeScript-Code innerhalb eines Code-Blocks ```typescript ... ``` zurück.
   - Füge keine Erklärungen in Klartext außerhalb des Code-Blocks hinzu.
"""

POM_UPDATER_SYSTEM_PROMPT = """Du bist ein erfahrener Testautomatisierungs-Ingenieur mit Spezialisierung auf Playwright und TypeScript.
Deine Aufgabe ist es, eine bestehende Page Object Model (POM) Klasse in TypeScript (.ts) zu AKTUALISIEREN. Alle bestehenden Funktionalitäten und Strukturen müssen erhalten bleiben; füge nur die notwendigen Lokatoren und Methoden gemäß den Spezifikationen oder der inspektionierten Ansicht (Aria-Snapshots) hinzu oder passe diese an.

### AKTUALISIERUNGSREGELN:
1. Behalte die Klassensignatur, die Imports und die bestehenden Methoden bei, die keine Änderungen erfordern.
2. Füge neue Lokatoren oder Methoden unter Einhaltung des Codestils der Originaldatei hinzu.
3. Gewährleiste die strikte Typisierung mit `Page` und `Locator` aus `@playwright/test`.
4. Gib AUSSCHLIESSLICH den aktualisierten Inhalt der TypeScript-Datei innerhalb eines ```typescript ... ``` Blocks zurück.
"""

def build_pom_generation_prompt(
    target_class_name: str,
    reference_poms_code: str,
    aria_snapshot: str = "",
    user_instructions: str = ""
) -> str:
    """
    Erstellt den finalen Prompt für die Generierung eines neuen POMs.
    """
    prompt = f"### ANFORDERUNG FÜR NEUES POM\n"
    prompt += f"Name der zu generierenden Klasse: `{target_class_name}`\n\n"

    if user_instructions:
        prompt += f"### ZUSÄTZLICHE BENUTZERANWEISUNGEN:\n{user_instructions}\n\n"

    if reference_poms_code:
        prompt += f"### REFERENZ-POMS (Befolge diesen Designstil und diese Konventionen):\n"
        prompt += f"{reference_poms_code}\n\n"

    if aria_snapshot:
        prompt += f"### ARIA-SNAPSHOT-STRUKTUR / ANSICHTSINSPEKTION:\n"
        prompt += f"```yaml\n{aria_snapshot}\n```\n\n"

    prompt += "Bitte generiere die vollständige TypeScript-POM-Klasse gemäß diesen Spezifikationen."
    return prompt

def build_pom_update_prompt(
    existing_pom_code: str,
    reference_poms_code: str = "",
    aria_snapshot: str = "",
    user_instructions: str = ""
) -> str:
    """
    Erstellt den finalen Prompt für die Aktualisierung eines bestehenden POMs.
    """
    prompt = f"### ANFORDERUNG ZUR AKTUALISIERUNG EINES BESTEHENDEN POMS\n\n"

    prompt += f"### AKTUELLER CODE DES POMS:\n```typescript\n{existing_pom_code}\n```\n\n"

    if user_instructions:
        prompt += f"### ÄNDERUNGEN ODER HINZUZUFÜGENDE / ZU ÄNDERNDE METHODEN:\n{user_instructions}\n\n"

    if reference_poms_code:
        prompt += f"### WEITERE REFERENZ-POMS DES PROJEKTS:\n{reference_poms_code}\n\n"

    if aria_snapshot:
        prompt += f"### ARIA-SNAPSHOT-STRUKTUR / ANSICHTSINSPEKTION:\n```yaml\n{aria_snapshot}\n```\n\n"

    prompt += "Bitte gib die vollständige TypeScript-Datei mit den integrierten Aktualisierungen zurück."
    return prompt
