import fs from 'fs';
import path from 'path';
import readline from 'readline';
import { createRequire } from 'module';
import * as ts from 'typescript';
import PageManager from "./pageManager.ts";
import type { Page } from "playwright";
import { expect } from "playwright/test";
import { promises as fsy } from "fs";

// Utils
import { formateDate, randomString, executeAssertion, executeStep, ResultWriter } from "../util/util.ts";

// Page Object Models (Importados explícitamente para compatibilidad estática)
import { NavigationPage } from "../POM/NavigationPage.ts";
import { ZeitraeumePage } from '../POM/ZeitraeumePage.ts';
import { PruefungsberichtMainPage } from "../POM/BerichtMainPage.ts";
import { SteuerpflichtigenPage } from "../POM/BerichtEingabedialogPage.ts";
import { UbermittlungsschreibenPage } from "../POM/UbermittlungsschreibenPage.ts";

const customRequire = createRequire(import.meta.url);

const STATIC_UTILS = {
    expect,
    fs: fsy,
    formateDate,
    randomString,
    executeAssertion,
    executeStep,
    ResultWriter
};

const POM_REGISTRY: Record<string, any> = {
    navigation: NavigationPage,
    zeitraeume: ZeitraeumePage,
    bericht: PruefungsberichtMainPage,
    bericht_eingabe: SteuerpflichtigenPage,
    bericht_ubermittlung: UbermittlungsschreibenPage
};

class Executor {
    async init() {
        await PageManager.getPage();
    }

    async runUserCode(code: string) {
        try {
            const activePage = await PageManager.getPage();

            // 1. Si el código incluye la marca legacy #NBELPH69, tomar el contenido tras ella
            let cleanCode = code.includes('#NBELPH69')
                ? code.split('#NBELPH69').slice(1).join('\n')
                : code;

            // 2. Sanitizar sentencias import/export que producen errores de sintaxis o colisión en new Function()
            cleanCode = cleanCode
                .replace(/^import\s+type\s+.*$/gm, '') // eliminar import type
                .replace(/^import\s+[\s\S]*?from\s+['"].*?['"];?/gm, (match) => `// ${match}`) // comentar imports estáticos
                .replace(/^export\s+default\s+/gm, '')
                .replace(/^export\s+/gm, '');

            const transpileResult = ts.transpileModule(cleanCode, {
                compilerOptions: {
                    module: ts.ModuleKind.CommonJS,
                    target: ts.ScriptTarget.ESNext,
                    allowJs: true
                }
            });

            const jsCode = transpileResult.outputText;

            const moduleExports = {};
            const executionContext: Record<string, any> = {
                page: activePage,
                PageManager: PageManager,
                require: (moduleName: string) => {
                    try {
                        return customRequire(moduleName);
                    } catch {
                        return {};
                    }
                },
                exports: moduleExports,
                module: { exports: moduleExports },
                ...STATIC_UTILS
            };

            for (const [key, PomClass] of Object.entries(POM_REGISTRY)) {
                if (typeof PomClass === 'function') {
                    executionContext[key] = new PomClass(activePage);
                }
            }

            const contextKeys = Object.keys(executionContext).join(', ');
            const wrappedCode = `
                const { ${contextKeys} } = context;
                return (async () => {
                    {
                        ${jsCode}
                    }
                })();
            `;
            const fn = new Function("context", wrappedCode);
            return await fn(executionContext);
        } catch (err: any) {
            throw new Error(err.message || String(err));
        }
    }
}

const executor = new Executor();

// --- MODO AGENTE IPC (JSON-RPC sobre stdin/stdout) ---
async function startIPCMode() {
    await executor.init();
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout,
        terminal: false
    });

    console.log(JSON.stringify({ event: "ready", message: "REPL IPC Server listo" }));

    rl.on('line', async (line) => {
        const trimmed = line.trim();
        if (!trimmed) return;

        let req: any;
        try {
            req = JSON.parse(trimmed);
        } catch (e: any) {
            console.log(JSON.stringify({ status: "error", error: "JSON inválido enviado al REPL" }));
            return;
        }

        const id = req.id || "0";
        try {
            if (req.action === "eval") {
                const result = await executor.runUserCode(req.code || "");
                console.log(JSON.stringify({ id, status: "success", result: result || "Ausführung erfolgreich" }));
            } else if (req.action === "eval_file") {
                const absPath = path.resolve(req.filePath);
                if (!fs.existsSync(absPath)) {
                    console.log(JSON.stringify({ id, status: "error", error: `Archivo no encontrado: ${absPath}` }));
                } else {
                    const code = fs.readFileSync(absPath, 'utf-8');
                    const result = await executor.runUserCode(code);
                    console.log(JSON.stringify({ id, status: "success", result: result || "Ausführung erfolgreich" }));
                }
            } else if (req.action === "close") {
                await PageManager.close();
                console.log(JSON.stringify({ id, status: "success", result: "Navegador cerrado" }));
                process.exit(0);
            } else {
                console.log(JSON.stringify({ id, status: "error", error: `Acción desconocida: ${req.action}` }));
            }
        } catch (error: any) {
            console.log(JSON.stringify({ id, status: "error", error: error.message, stack: error.stack }));
        }
    });
}

// --- MODO CLI INTERACTIVO (Aislado para el usuario humano) ---
async function startInteractiveMode() {
    await executor.init();

    console.log("\n--- REPL Playwright ---");
    console.log("Ingrese la ruta de una archivo .ts o escriba código directo ('exit' para salir):");

    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });

    const ask = () => {
        rl.question('LOG## Datei/Code > ', async (inputVal) => {
            const trimmed = inputVal.trim();
            if (trimmed.toLowerCase() === 'exit') {
                await PageManager.close();
                rl.close();
                return;
            }

            if (!trimmed) {
                ask();
                return;
            }

            try {
                let codeToRun = trimmed;
                const absolutePath = path.resolve(trimmed);

                if (fs.existsSync(absolutePath) && fs.statSync(absolutePath).isFile()) {
                    console.log(`LOG## Ejecutando archivo: ${path.basename(absolutePath)}...`);
                    codeToRun = fs.readFileSync(absolutePath, 'utf-8');
                } else {
                    console.log(`LOG## Ejecutando código directo...`);
                }

                const result = await executor.runUserCode(codeToRun);
                console.log("LOG## Ergebnis:", result || "Ausführung erfolgreich");
            } catch (error: any) {
                console.error("Fehler bei der Ausführung:", error.message);
            }

            ask();
        });
    };

    ask();
}

// Determinar modo de ejecución
const isIPC = process.argv.includes('--ipc') || process.env.REPL_MODE === 'ipc';
if (isIPC) {
    startIPCMode();
} else {
    startInteractiveMode();
}