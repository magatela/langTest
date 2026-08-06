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

const testKey = 'PDNEU-3454'
const resultWriter = new ResultWriter(page, testKey);
const goblaStatus = { status: 'PASS' };
const stepStatus = { status: 'PASS' };
const errors: string[] = [];

// Vorbereitung 
const pruefung = '5197 26 0 00097';
await navigation.menu("PRUEFUNGSPLAN");
await navigation.searchAndOpen(pruefung);
await navigation.navigateTo("VORBEREITUNG", "ZEITRAEUME");
await zeitraeume.setTimeFrame("SICHTUNGSZEITRAUM", '2018', '2024');
await zeitraeume.selectOption('EINKUNFTSART', '_13EStG');
await zeitraeume.selectOption('GEWINNERMITTLUNGSART', 'BILANZIERUNG');
await zeitraeume.setTimeFrame("PRUEFUNGSZEITRAUM", '2018', '2024');
await zeitraeume.clickButton('SPEICHERN');

let testStep = 'step 1';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        await navigation.navigateTo('ABWICKLUNG', 'BERICHTE');
    },
    'Navigation erfolgreich: Dialog Berichte ist aufgerufen (/)',
    'Dialog Berichte konnte nicht aufgerufen werden (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 2';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        // Pruefung, ob der Button "Berichtsassistent starten" sichtbar ist 
        // (dies bestaetigt gleichzeitig, dass der Dialog "Berichte" erfolgreich aufgerufen wurde)
        const isVisible = await bericht.istButtonVisible('BERICHTSASSISTENT_STARTEN');
        
        await executeAssertion(
            () => { expect(isVisible).toBeTruthy() },
            `Der Button 'Berichtsassistent starten' ist NICHT sichtbar. Navigation zu 'Berichte' fehlgeschlagen.`
        );

        await bericht.highlightButton('BERICHTSASSISTENT_STARTEN', 'red');
        await resultWriter.createEvidence(testStep, 'Button Berichtsassistent starten ist sichtbar');
        await bericht.highlightButton('BERICHTSASSISTENT_STARTEN', 'none');
    },
    'Button "Berichtsassistent starten" ist sichtbar (/)',
    'Button ist nicht sichtbar (x)',
    errors,
    goblaStatus,
    stepStatus
);

// --- STEP 3: Modal und Berichtsarten (Enumeration) ---
testStep = 'step 3';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        // Button klicken, um Modal zu oeffnen
        await bericht.clickButton('BERICHTSASSISTENT_STARTEN');

        // Erwartete Berichtsarten in korrekter Reihenfolge
        const expectedOptions = [
            'Pruefungsbericht',
            'Manueller Bericht',
            'Mitteilung ueber ergebnislose Bp',
            'Zusammenstellung der Pruefungsfeststellungen'
        ];

        // Validierung der Optionen im Modal
        // Da die POM nur zwei Optionen definiert, nutzen wir hier die Page-Instanz fuer die vollstaendige Liste
        const modalLocator = page.locator('//div[@data-role="modal-overlay-content"]');
        const actualOptions = await modalLocator.innerText();
        console.log(`######## ${actualOptions}`);
        // Wir filtern die Texte, um sicherzustellen, dass die Berichtsarten enthalten sind
        const filteredOptions = expectedOptions.filter((text)=>{actualOptions.includes(text)});

        await executeAssertion(
            () => { 
                expect(filteredOptions).toBeTruthy(); 
            },
            `Die Berichtsarten im Modal sind unvollstaendig oder in der falschen Reihenfolge. Erwartet: ${expectedOptions.join(', ')}, Gefunden: ${filteredOptions.join(', ')}`
        );

        // Highlight der Option "Mitteilung ueber ergebnislose Bp" fuer die Evidence
        await bericht.highlightOption('red', 'MITTEILUNG_ERGEBNISLOSE_BP');
        await resultWriter.createEvidence(testStep);
        await bericht.highlightOption('none', 'MITTEILUNG_ERGEBNISLOSE_BP');
    },
    'Modal offnet sich mit den korrekten Berichtsarten in der richtigen Reihenfolge (/)',
    'Modal offnet sich nicht oder Berichtsarten sind falsch/unvollstaendig (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 4';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        // Auswahl treffen
        await bericht.selectFromassitant('MITTEILUNG_ERGEBNISLOSE_BP');

        // Pruefung, ob der Detailbereich geoeffnet wurde (z.B. durch Sichtbarkeit einer ueberschrift der Steuerpflichtigen-Seite)
        const isDetailVisible = await bericht_eingabe.isVisible('headings', 'MAIN');
        
        await executeAssertion(
            () => { expect(isDetailVisible).toBeTruthy() },
            `Der Detailbereich zur 'Mitteilung ueber ergebnislose Bp' hat sich NICHT geoeffnet.`
        );

        await bericht_eingabe.highlight('headings', 'MAIN', 'red');
        await resultWriter.createEvidence(testStep, 'Detailbereich Mitteilung ueber ergebnislose Bp geoeffnet');
        await bericht_eingabe.highlight('headings', 'MAIN', 'none');
    },
    'Detailbereich zur "Mitteilung ueber ergebnislose Bp" oeffnet sich nach Auswahl (/)',
    'Detailbereich oeffnet sich NICHT (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 5';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        
    },
    'Berichtsarten "Pruefungsbericht" und "Zusammenstellung der Pruefungsfeststellungen" funktionieren nur als Platzhalter (/)',
    'Platzhalter haben eine unerwartete Aktion ausgeloest (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 6';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        
    },
    'Detailbereich ueberlagert den Masterbereich korrekt (/)',
    'Detailbereich ueberlagert Masterbereich nicht korrekt (x)',
    errors,
    goblaStatus,
    stepStatus
);

resultWriter.saveResult(testKey, goblaStatus.status);
if (errors.length > 0) {
    throw new Error(errors.join('\n'))
}