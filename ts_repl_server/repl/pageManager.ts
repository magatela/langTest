import { request, chromium } from "playwright";
import type { APIRequestContext } from "playwright/test";
import type { Browser, Page } from "playwright";
import path from "path";
import os from 'os';

// const chromePath = path.join(os.homedir(),'AppData','Local','ms-playwright','chrome-win64','chrome.exe');
const chromePath = path.join(os.homedir(),'Downloads','chrome1200', 'chrome-win64','chrome.exe');

const RAVEN_API_V1 = 'rest/raven/1.0/api/';
const RAVEN_API_V2 = 'rest/raven/2.0/api/';

class PageManager {
    private static browser: Browser;
    private static page: Page;

    constructor() {
    }

    static async getBrowser(): Promise<Browser> {
        if (!PageManager.browser) {
            PageManager.browser = await chromium.launch({ executablePath: chromePath, headless: false, args: ['--start-maximized']});
        }
        return PageManager.browser;
    }

    static async getPage(): Promise<Page> {
        if (!PageManager.page) {
            const browser = await (await PageManager.getBrowser()).newContext({viewport: null, bypassCSP: true});
            browser.setDefaultTimeout(10000);
            console.log(chromePath)
            PageManager.page = await browser.newPage();
        }
        return PageManager.page;
    }

    static async close() {
        await PageManager.browser.close();
    }

    private static async getApiContext(): Promise<APIRequestContext> {
        const user = 'miguel.avendano@fv.nrw.de'
        const password = 'NuestraComida@2025'
        const auth = `${user}:${password}`
        const apiCtx = await request.newContext({
            baseURL: 'https://jira.steuer.niedersachsen.doi-de.net/',
            extraHTTPHeaders: {
                'Accept':'application/json',
                'Content-Type': 'application/json; charset=UTF-8',
                'X-Atlassian-Token': 'no-check',
                'Authorization': `Basic ${Buffer.from(auth).toString('base64')}`
            },
            proxy:{
                server:'http://proxy-user:8080' 
            },
            ignoreHTTPSErrors: true
        });
        return apiCtx;
    }

    static async getTestRunData(execution_id:string, test_id:string){
        const prefix = 'PDNEU-';
        execution_id = `${prefix}${execution_id}`;
        test_id = `${prefix}${test_id}`;
        const apiContext = await PageManager.getApiContext();
        const response = await apiContext.get(`rest/raven/1.0/api/testrun?testExecIssueKey=${execution_id}&testIssueKey=${test_id}`);
        return await response.json();
    }

    static async updateTestStep(testrun_id:string, step_id:string, data:any){
        const apiContext = await PageManager.getApiContext();
        const response = await apiContext.put(`rest/raven/1.0/api/testrun/${testrun_id}/step/${step_id}`, { data: data} );
        return response;
    }

    static async getTestRunDataByID(testrun_id:string){
        const apiContext = await PageManager.getApiContext();
        const response = await apiContext.get(`${RAVEN_API_V2}testrun/${testrun_id}?includeiterations=true` );
        return await response.json();
    }

    static async getIterationStepsResult(testrun_id:string, iteration_id:string){
        const apiContext = await PageManager.getApiContext();
        const response = await apiContext.get(`${RAVEN_API_V2}testrun/${testrun_id}/iteration/${iteration_id}/step` );
        return await response.json();
    }

    static async getSingleIterationStep(testrun_id:string, iteration_id:string, step_id:string){
        const apiContext = await PageManager.getApiContext();
        const response = await apiContext.get(`${RAVEN_API_V2}testrun/${testrun_id}/iteration/${iteration_id}/step/${step_id}`);
        return await response.json();
    }

    static async setSingleIterationStep(testrun_id:string, iteration_id:string, step_id:string, data:any){
        const apiContext = await PageManager.getApiContext();
        const response = await apiContext.put(`${RAVEN_API_V2}testrun/${testrun_id}/iteration/${iteration_id}/step/${step_id}`, { data: data} );
        return response;
    }
}

export default PageManager;


// curl -X POST "https://geco-mockserver-pdgo.qsi.magic-dev-qsi-01.bk.fin.local/mock/contr/prz/pruefungsdienste/services/rest/v1/manual/import/5112000000023" -H sec-ch-ua-platform: "Windows" -H referer: https://geco-mockserver-pdgo.qsi.magic-dev-qsi-01.bk.fin.local/mock/contr/prz/pruefungsdienste/services/rest/v1/api-docs?url=/mock/contr/prz/pruefungsdienste/services/rest/v1/openapi.json -H user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 -H accept: */* -H sec-ch-ua: "Not.A/Brand";v="99", "Chromium";v="136" -H content-type: application/octet-stream -H sec-ch-ua-mobile: ?0