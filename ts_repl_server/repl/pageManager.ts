import { request, chromium } from "playwright";
import type { APIRequestContext } from "playwright/test";
import type { Browser, Page } from "playwright";
import { getJiraConfig, getPlaywrightConfig } from "../util/configLoader.ts";

const RAVEN_API_V1 = 'rest/raven/1.0/api/';
const RAVEN_API_V2 = 'rest/raven/2.0/api/';

class PageManager {
    private static browser: Browser;
    private static page: Page;
    private static initPromise: Promise<Page> | null = null;

    constructor() {}

    static async getBrowser(): Promise<Browser> {
        if (!PageManager.browser || !PageManager.browser.isConnected()) {
            const pwConfig = getPlaywrightConfig();
            const launchOptions: any = {
                headless: pwConfig.headless,
                args: ['--start-maximized']
            };

            if (pwConfig.use_custom_chrome_path && pwConfig.chrome_path) {
                launchOptions.executablePath = pwConfig.chrome_path;
            }

            PageManager.browser = await chromium.launch(launchOptions);
            PageManager.browser.on('disconnected', () => {
                PageManager.browser = null as any;
                PageManager.page = null as any;
            });
        }
        return PageManager.browser;
    }

    static async getPage(): Promise<Page> {
        if (PageManager.initPromise) {
            return PageManager.initPromise;
        }

        PageManager.initPromise = (async () => {
            try {
                const browserInstance = await PageManager.getBrowser();

                // 1. Si la página actual sigue abierta y válida, retornarla de inmediato
                if (PageManager.page && !PageManager.page.isClosed()) {
                    return PageManager.page;
                }

                // 2. Reutilizar contexto existente o crear uno nuevo si no existe ninguno
                let context = browserInstance.contexts()[0];
                if (!context) {
                    context = await browserInstance.newContext({ viewport: null, bypassCSP: true });
                    context.setDefaultTimeout(10000);
                }

                // 3. Reutilizar pestaña/página viva dentro del contexto o abrir una nueva
                let activePage = context.pages().find(p => !p.isClosed());
                if (!activePage) {
                    activePage = await context.newPage();
                }

                PageManager.page = activePage;
                PageManager.page.on('close', () => {
                    PageManager.page = null as any;
                });

                return PageManager.page;
            } finally {
                PageManager.initPromise = null;
            }
        })();

        return PageManager.initPromise;
    }

    static async close() {
        if (PageManager.browser) {
            try {
                await PageManager.browser.close();
            } catch {}
            PageManager.browser = null as any;
            PageManager.page = null as any;
        }
    }

    private static async getApiContext(): Promise<APIRequestContext> {
        const jiraConfig = getJiraConfig();
        const auth = `${jiraConfig.user}:${jiraConfig.password}`;

        const apiContextOptions: any = {
            baseURL: jiraConfig.base_url,
            extraHTTPHeaders: {
                'Accept': 'application/json',
                'Content-Type': 'application/json; charset=UTF-8',
                'X-Atlassian-Token': 'no-check',
                'Authorization': `Basic ${Buffer.from(auth).toString('base64')}`
            },
            ignoreHTTPSErrors: true
        };

        if (jiraConfig.proxies && (jiraConfig.proxies.http || jiraConfig.proxies.https)) {
            apiContextOptions.proxy = {
                server: jiraConfig.proxies.http || jiraConfig.proxies.https
            };
        }

        return await request.newContext(apiContextOptions);
    }

    static async getTestRunData(execution_id: string, test_id: string) {
        const jiraConfig = getJiraConfig();
        const prefix = `${jiraConfig.prefix}-`;
        const execKey = execution_id.startsWith(jiraConfig.prefix) ? execution_id : `${prefix}${execution_id}`;
        const testKey = test_id.startsWith(jiraConfig.prefix) ? test_id : `${prefix}${test_id}`;
        const apiContext = await PageManager.getApiContext();
        const response = await apiContext.get(`${RAVEN_API_V1}testrun?testExecIssueKey=${execKey}&testIssueKey=${testKey}`);
        return await response.json();
    }

    static async updateTestStep(testrun_id: string, step_id: string, data: any) {
        const apiContext = await PageManager.getApiContext();
        const response = await apiContext.put(`${RAVEN_API_V1}testrun/${testrun_id}/step/${step_id}`, { data });
        return response;
    }

    static async getTestRunDataByID(testrun_id: string) {
        const apiContext = await PageManager.getApiContext();
        const response = await apiContext.get(`${RAVEN_API_V2}testrun/${testrun_id}?includeiterations=true`);
        return await response.json();
    }

    static async getIterationStepsResult(testrun_id: string, iteration_id: string) {
        const apiContext = await PageManager.getApiContext();
        const response = await apiContext.get(`${RAVEN_API_V2}testrun/${testrun_id}/iteration/${iteration_id}/step`);
        return await response.json();
    }

    static async getSingleIterationStep(testrun_id: string, iteration_id: string, step_id: string) {
        const apiContext = await PageManager.getApiContext();
        const response = await apiContext.get(`${RAVEN_API_V2}testrun/${testrun_id}/iteration/${iteration_id}/step/${step_id}`);
        return await response.json();
    }

    static async setSingleIterationStep(testrun_id: string, iteration_id: string, step_id: string, data: any) {
        const apiContext = await PageManager.getApiContext();
        const response = await apiContext.put(`${RAVEN_API_V2}testrun/${testrun_id}/iteration/${iteration_id}/step/${step_id}`, { data });
        return response;
    }
}

export default PageManager;