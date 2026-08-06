import { promises as fs } from "fs";
import path from 'path';
import type { Page } from "playwright"
import  stripAnsi from "strip-ansi"

export class ResultWriter {
    results: {[key:string]: any} = {};
    evidence:{[key:string]: any}[] = [];
    actualResult:string[] = [];
    page:Page;
    base_path:string;
    constructor(page:Page, test_id:string){
        this.page = page;
        this.results.testKey = test_id;
        this.results.status = null;
	    this.results.steps = []
        this.base_path = path.join('C:','Users','t011669','Documents','Resultados', test_id);
    }
    
    setTestStatus(status:string){
        this.results.status = status;
    }
    
    resolveStep(status:string, actualResult:string = ''){
        let stepResult = {
            'status': status,
            'actualResult':`${actualResult}\n${this.actualResult.join('\n')}`,
            'evidences': this.evidence
        }
        this.results.steps.push(stepResult);
        this.evidence = [];
        this.actualResult = [];
        this.results.status = null;
    }
    
    async createEvidence(screenshotName:string, screenshotHeader:string = ''){
        const screenshotPath = path.join(this.base_path,`${screenshotName}.png`);
        const screenShotBuffer = await this.page.screenshot({path:screenshotPath, type:'png', fullPage:true});
        const base64Screenshot = screenShotBuffer.toString('base64');
        const stepEvidence = {
            "data": base64Screenshot,
            "filename": `${screenshotName}.png`,
            "contentType": "image/png"
        }
        this.evidence.push(stepEvidence);
        this.actualResult.push(`${screenshotHeader? screenshotHeader + '\n': screenshotHeader}!${screenshotName}.png|thumbnail!`);
    }

    async saveResult(fileName:string, status:string){
        this.setTestStatus(status);
        try{
            const content = stripAnsi(JSON.stringify(this.results, null, 4)); 
            let results_path = path.join(this.base_path,`${fileName}.json`);
            await fs.writeFile(results_path, content, {encoding: 'utf-8'})
        } catch (error) {
            console.log(error);
        }
    }
}

type StepFunction = () => Promise<void>;

export async function executeStep(
    stepName: string,
    resultWriter:ResultWriter,
    stepFunction: StepFunction,
    successMsg: string,
    errorMsg: string,
    errors: string[],
    goblaStatus: {status: string},
    stepStatus: {status: string}
){
    try{
        console.log(`Executing Step ${stepName}`)
        stepStatus.status='PASS';
        await stepFunction();
        resultWriter.resolveStep(stepStatus.status, successMsg);
    } catch (error){
        const stringError = `${error}`
        await resultWriter.createEvidence(`${stepName} ERROR SCREEN`, `${removeAnsiCodes(stringError)}`);
        stepStatus.status = 'FAIL'
        resultWriter.resolveStep(stepStatus.status, errorMsg);
        goblaStatus.status = 'FAIL';
        errors.push(`ERROR ${stepName}:\n${error}`);
    } 
}

function removeAnsiCodes(str: string): string {
  return str.replace(
    // Regex que elimina códigos ANSI
    // eslint-disable-next-line no-control-regex
    /\x1b\[[0-9;]*m/g,
    ''
  );
}

export async function executeAssertion(assertion: () => void | Promise<void>, message: string) {
    try {
        await assertion();
    }
    catch (err) {
        throw new Error(`${message}\n${(err as Error).message}`);
    }
};

export function randomString(length: number) {
    const alphanum = 'ABCDEFGHIJKLNMOPQRSTUVWXYZabcdefghijklnmopqrstuvwxyz0123456789';
    const especial = '!"§$%&/()=?*ÜÄÖ_:;';
    let result = '';
    for(let i = 0; i < length; i++){
        const randomIndex = Math.floor(Math.random() * alphanum.length)
        result += alphanum[randomIndex]
    }
    return result;
        
};

export function formateDate(date: Date):string{
    const dd = String(date.getDate()).padStart(2, '0');
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const yyyy = String(date.getFullYear())
    return `${dd}.${mm}.${yyyy}`;
}

export async function showAlert(page:Page, msg: string){
    await Promise.all([
        page.waitForEvent('dialog'),
        page.evaluate((m)=>{alert(m)}, msg)
    ]);
}
