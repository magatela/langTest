import type { Page } from "playwright"
import { randomString, executeAssertion, executeStep, ResultWriter } from "../../util/util.ts"
import { expect } from "playwright/test";
import {NavigationPage } from "../../POM/NavigationPage.ts"
import {ZeitraeumePage} from "../../POM/ZeitraeumePage.ts"
import { PruefungsberichtMainPage } from "../../POM/BerichtMainPage.ts"
import { SteuerpflichtigenPage } from "../../POM/BerichtEingabedialogPage.ts"

declare const page: Page;
declare const navigation: NavigationPage;
declare const zeitraeume: ZeitraeumePage;
declare const bericht: PruefungsberichtMainPage;
declare const bericht_eingabe: SteuerpflichtigenPage;
// DIESE ZEILE IST SEHR WICHTIG!! NICHT LoeSCHEN #NBELPH69

const testKey = 'PDNEU-1311'
const resultWriter = new ResultWriter(page, testKey);
const goblaStatus = { status: 'PASS' };
const stepStatus = { status: 'PASS' };
const errors: string[] = [];

// Vorbereitung 
const pruefung = '5197 26 0 00095'; // Miguel
// const pruefung = ''; // Fabiola
// const pruefung = ''; // Mario
// const pruefung = ''; // Recep

await navigation.menu("PRUEFUNGSPLAN");
await navigation.searchAndOpen(pruefung);
await navigation.navigateTo("VORBEREITUNG", "ZEITRAEUME");
await zeitraeume.setTimeFrame("SICHTUNGSZEITRAUM", '2018', '2023');
await zeitraeume.selectOption('EINKUNFTSART', '_13EStG');
await zeitraeume.selectOption('GEWINNERMITTLUNGSART', 'BILANZIERUNG');
await zeitraeume.setTimeFrame("PRUEFUNGSZEITRAUM", '2018', '2023');
await zeitraeume.clickButton('SPEICHERN');

let testStep = 'step 1'
await executeStep(
    testStep,
    resultWriter,
    async () => {
        
        
    },
    'Maske wird Angezeigt (/)',
    'Maske wird NICHT Angezeigt (/)',
    errors,
    goblaStatus,
    stepStatus
);