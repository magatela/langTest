import fs from 'fs';
import path from 'path';
import readline from 'readline';
import * as ts from 'typescript';
import PageManager from "./pageManager.ts";
import type { Page } from "playwright";
import { expect } from "playwright/test";
import { promises as fsy } from "fs";

// Utils
import { formateDate, randomString, executeAssertion, executeStep, ResultWriter} from "../util/util.ts"

//Page Object Models
import {NavigationPage} from "../POM/NavigationPage.ts"
import { ZeitraeumePage } from '../POM/ZeitraeumePage.ts';
import { PruefungsberichtMainPage } from "../POM/BerichtMainPage.ts"
import { SteuerpflichtigenPage } from "../POM/BerichtEingabedialogPage.ts"
import { UbermittlungsschreibenPage } from "../POM/UbermittlungsschreibenPage.ts"
//import { SteuerpflichtigenPage } from "../../../ait-main/e2etests/tests/pages/finalizationReport/ReportInputDialogPage.ts"

const STATIC_UTILS = {
    expect,
    fs: fsy,
    formateDate, 
    randomString, 
    executeAssertion, 
    executeStep, 
    ResultWriter
}

const POM_REGISTRY = {
    navigation: NavigationPage,
    zeitraeume: ZeitraeumePage,
    bericht : PruefungsberichtMainPage,                     // Bericht main page
    bericht_eingabe : SteuerpflichtigenPage,                // Bericht -> Eingabe Dialog
    bericht_ubermittlung : UbermittlungsschreibenPage       // Bericht -> Übermittlungsschreiben 
}

class Executor {
    private page!: Page;
   
    async init() {
        // Browser starten und Page offen halten
        this.page = await PageManager.getPage();
        console.log("Browser und Page gestartet");
    }

    async runUserCode(code: string) {
        try {
            // Compiliert TS Code zu JS code
            const transpileResult = ts.transpileModule(code, {
                compilerOptions: {
                    module: ts.ModuleKind.CommonJS,
                    target: ts.ScriptTarget.ESNext
                }
            });

            const jsCode = transpileResult.outputText;

            const executionContext: Record<string, any> = {
                page: this.page,
                ...STATIC_UTILS
            }

            for(const [key, PomClass] of Object.entries(POM_REGISTRY)){
                executionContext[key] = new PomClass(this.page);
            }

            const contextKeys = Object.keys(executionContext).join(', ')
            // Wrapper funktion
            const wrappedCode = `
                const { ${contextKeys} } = context;
                return (async () => {
                    { 
                        ${jsCode} 
                    }
                })();
            `;
            const fn = new Function("context", wrappedCode);
                     
            // Führt den Code aus und Übergibt die Aktive Playwright-Inztanz
            return await fn(executionContext);
        } catch (err: any) {
            throw new Error(err.message);
        }
    }
}

// --- CLI ---

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

const executor = new Executor();

async function startInteractiveMode() {
    await executor.init();

    console.log("\n--- REPL Playwright ---");
    console.log("Schreiben Sie den Pfad der .ts Datei ('exit' zu Beenden):");

    const askForFile = () => {
        rl.question('LOG## Datei > ', async (filePath) => {
            if (filePath.toLowerCase() === 'exit') {
                await PageManager.close(); // Browser beenden
                rl.close();
                return;
            }

            const absolutePath = path.resolve(filePath);

            if (!fs.existsSync(absolutePath)) {
                console.error(`LOG## Error: Datei nicht gefunden ${absolutePath}`);
            } else {
                try {
                    const code = fs.readFileSync(absolutePath, 'utf-8');
                    // Code vor #NBELPH69 löschen
                    const userCode = code.split('#NBELPH69').slice(1).join();
                    console.log(`LOG## ausführen: ${path.basename(absolutePath)}...`);

                    const result = await executor.runUserCode(userCode);

                    console.log("LOG## Ergebniss:", result || "Ausführung erfolgreich");
                } catch (error: any) {
                    console.error("Fehler bei der Ausführung", error.message);
                    if(error.stack){
                        console.error("Fehler bei der Ausführung", error.stack);
                    }
                }
            }

            // keep CLI alive
            askForFile();
        });
    };

    askForFile();
}

startInteractiveMode();