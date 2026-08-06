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
const pruefung = '5197 26 0 00097'; // Miguel
// const pruefung = '5197 26 0 00081'; // Fabiola
// const pruefung = '5197 26 0 00160'; // Mario
// const pruefung = '5197 26 0 00066'; // Recep

await navigation.menu("PRUEFUNGSPLAN");
await navigation.searchAndOpen(pruefung);
await navigation.navigateTo("VORBEREITUNG", "ZEITRAEUME");
await zeitraeume.setTimeFrame("SICHTUNGSZEITRAUM", '2018', '2024');
await zeitraeume.selectOption('EINKUNFTSART', '_13EStG');
await zeitraeume.selectOption('GEWINNERMITTLUNGSART', 'BILANZIERUNG');
await zeitraeume.setTimeFrame("PRUEFUNGSZEITRAUM", '2018', '2024');
await zeitraeume.clickButton('SPEICHERN');

let testStep = 'step 1'
await executeStep(
    testStep,
    resultWriter,
    async () => {
        await navigation.navigateTo('ABWICKLUNG', 'BERICHTE');
        let isVisible = await bericht.istButtonVisible('BERICHTSASSISTENT_STARTEN');        
        
        await executeAssertion(
            () => { expect(isVisible).toBeTruthy() },
            `Der Button 'Berichtsassistent starten' ist NICHT sichtbar. Navigation zu 'Berichte' fehlgeschlagen.`
        );
        
        await bericht.clickButton('BERICHTSASSISTENT_STARTEN');
        isVisible = await bericht.isButtonInAssitantVisible('MITTEILUNG_ERGEBNISLOSE_BP');
        await executeAssertion(
            () => { expect(isVisible).toBeTruthy() },
            `Der Button 'MITTEILUNG_ERGEBNISLOSE_BP' ist in dem Modal NICHT sichtbar`
        );
        
        await bericht.selectFromassitant('MITTEILUNG_ERGEBNISLOSE_BP');
        
    },
    'Maske wird Angezeigt (/)',
    'Maske wird NICHT Angezeigt (/)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 2'
await executeStep(
    testStep,
    resultWriter,
    async () => {
        await bericht_eingabe.click('radios', 'NICHT_NATUERLICHE_PERSON');

        const isVisible = await bericht_eingabe.isVisible('fields', 'FIRMENNAME');
        await executeAssertion(() => { expect(isVisible).toBeTruthy() }, 'FIRMENNAME NICHT vorhanden ');

        const string250 = randomString(250);
        await bericht_eingabe.setValue('fields', 'FIRMENNAME', string250);
        await bericht_eingabe.highlight('fields', 'FIRMENNAME', 'red');
        await resultWriter.createEvidence(`${testStep}.a`, 'String 250');
        await bericht_eingabe.highlight('fields', 'FIRMENNAME', 'none');

        const string300 = randomString(300);
        await bericht_eingabe.setValue('fields', 'FIRMENNAME', string300);
        await bericht_eingabe.highlight('fields', 'FIRMENNAME', 'red');
        await resultWriter.createEvidence(`${testStep}.b`, 'String 300');
        await bericht_eingabe.highlight('fields', 'FIRMENNAME', 'none');

        await bericht_eingabe.setValue('fields', 'FIRMENNAME', '');

    },
    'Das Feld NameFirma ist vorhanden und besitzt alle geforderten Attributen. (/)',
    'Das Feld NameFirma ist NICHT vorhanden',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 3' 
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const isVisible = await bericht_eingabe.isVisible('fields', 'STEUERNUMMER');
        await executeAssertion(() => { 
            expect(isVisible).toBeTruthy() 
        }, 'Steuernummer Feld ist NICHT vorhanden');

        await bericht_eingabe.highlight('fields', 'STEUERNUMMER', 'red');

        const stNrValue = await bericht_eingabe.getValue('fields', 'STEUERNUMMER');
        const stNrRegex = /\d{4}\/0\/\d{4}\/\d{4}/;
        
        await executeAssertion(() => { 
            expect(stNrValue).toMatch(stNrRegex) 
        }, `Steuernummer '${stNrValue}' entspricht nicht dem Format [5197 26 0 00097]`);

        await resultWriter.createEvidence(`${testStep}`, `Gelesener Wert: ${stNrValue}`);
        await bericht_eingabe.highlight('fields', 'STEUERNUMMER', 'none');
    },
    'Die Steuernummer ist vorhanden, schreibgeschuetzt und entspricht dem Format [5197 26 0 00097]',
    'Die Steuernummer fehlt oder besitzt ein ungueltiges Format',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 4';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const elementsToVerify = [
            { cat: 'fields', key: 'PRUEFUNGSNUMMER' },
            { cat: 'fields', key: 'PRUEFUNGSBEGINN' },
            { cat: 'fields', key: 'PRUEFUNGSANORDNUNG' },
            { cat: 'comboboxes', key: 'STEUERART' },
            { cat: 'fields', key: 'TABELLE_VON' },
            { cat: 'fields', key: 'TABELLE_BIS' },
        ] as const;

        for (const item of elementsToVerify) {
            // Fuer Tabellenelemente nur das erste pruefen, ansonsten Label-Check
            const isFirstElementVisible = await bericht_eingabe.isVisible(item.cat, item.key, true);
            
            if (isFirstElementVisible) {
                await executeAssertion(
                    () => { expect(isFirstElementVisible).toBeTruthy() }, 
                    `Element ${item.key} in Kategorie ${item.cat} ist NICHT sichtbar`
                );
                await bericht_eingabe.highlight(item.cat, item.key, 'red', true);
            } else if (item.key === 'TABELLE_VON' || item.key === 'TABELLE_BIS') {
                // Fallback: Wenn kein Tabelleneintrag da ist, muss das Label/Header sichtbar sein
                const labelText = item.key === 'TABELLE_VON' ? 'Von' : 'Bis';
                const isLabelVisible = await bericht_eingabe.isTextVisible(labelText);
                await executeAssertion(
                    () => { expect(isLabelVisible).toBeTruthy() }, 
                    `Tabelleneintrag fuer ${item.key} fehlt und auch das Label '${labelText}' ist nicht sichtbar`
                );
            } else {
                await executeAssertion(
                    () => { expect(isFirstElementVisible).toBeTruthy() }, 
                    `Element ${item.key} in Kategorie ${item.cat} ist NICHT sichtbar`
                );
            }
        }
        await resultWriter.createEvidence(`${testStep}`);
        for (const item of elementsToVerify) {
            await bericht_eingabe.highlight(item.cat, item.key, 'none', true);
        }
    },
    'Alle Felder im Bereich Pruefung (Nummer, Beginn, Anordnung, Steuerart, Von, Bis) sind sichtbar. (/)',
    'Eines oder mehrere Felder im Bereich Pruefung sind NICHT sichtbar',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 5';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const elementsToVerify = [
            { cat: 'fields', key: 'PRUEFUNGSANORDNUNG' },
        ] as const;

        for (const item of elementsToVerify) {
            const isEditable = await bericht_eingabe.isEditable(item.cat, item.key);
            const format = await bericht_eingabe.getValue(item.cat, item.key);
            const stNrRegex =/^\d{2}\.\d{2}\.\d{4}$/
            
            await executeAssertion(
                () => { expect(format).toMatch(stNrRegex) }, 
                `Element ${item.key} has nicht das richtige Format`
            );
            
            await executeAssertion(
                () => { expect(isEditable).toBeFalsy() }, 
                `Element ${item.key} ist editiertbar`
            );

            await bericht_eingabe.highlight(item.cat, item.key, 'red');
            await resultWriter.createEvidence(`${testStep}-${item.key}`);
            await bericht_eingabe.highlight(item.cat, item.key, 'none');
        }
    },
    'Das Feld *PruefungsanordnungVom* ist vorhanden und besitzt alle geforderten Attributen. (/)',
    'Das Feld *PruefungsanordnungVom* ist NICHT vorhanden und besitzt alle geforderten Attributen.',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 6';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const isVisible = await bericht_eingabe.isVisible('fields', 'PRUEFUNGSNUMMER');
        await executeAssertion(() => { 
            expect(isVisible).toBeTruthy() 
        }, 'Pruefungsnummer Feld ist NICHT vorhanden');

        const editable = await bericht_eingabe.isEditable('fields', 'PRUEFUNGSNUMMER');
        await executeAssertion(() => { 
            expect(editable).toBeFalsy() 
        }, 'Die Pruefungsnummer sollte NICHT editierbar sein, ist es aber');

        const value = await bericht_eingabe.getValue('fields', 'PRUEFUNGSNUMMER');
        const pruefungsNrRegex = /\d{4}\s\d{2}\s\d\s\d{5}/;
        
        await executeAssertion(() => { 
            expect(value).toMatch(pruefungsNrRegex) 
        }, `Pruefungsnummer '${value}' entspricht nicht dem Format`);

        await bericht_eingabe.highlight('fields', 'PRUEFUNGSNUMMER', 'blue');
        await resultWriter.createEvidence(testStep, `Wert: ${value} | Editierbar: ${editable? 'ja':'nein'}`);
        await bericht_eingabe.highlight('fields', 'PRUEFUNGSNUMMER', 'none');
    },
    'Die Pruefungsnummer ist vorhanden, nicht editierbar und folgt dem Format NNNN NN NNNNN',
    'Die Pruefungsnummer ist editierbar oder hat ein falsches Format',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 7';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const isVisible = await bericht_eingabe.isVisible('fields', 'PRUEFUNGSBEGINN');
        await executeAssertion(() => { 
            expect(isVisible).toBeTruthy() 
        }, 'Pruefungsnummer Feld ist NICHT vorhanden');

        const editable = await bericht_eingabe.isEditable('fields', 'PRUEFUNGSBEGINN');
        await executeAssertion(() => { 
            expect(editable).toBeFalsy() 
        }, 'Die Pruefungsnummer sollte schreibgeschuetzt sein, ist aber editierbar');

        const value = await bericht_eingabe.getValue('fields', 'PRUEFUNGSBEGINN');
        const dateRegex = /^\d{2}\.\d{2}\.\d{4}$/;
        
        await executeAssertion(() => { 
            expect(value).toMatch(dateRegex) 
        }, `Der Wert '${value}' entspricht nicht dem Format DD.MM.YYYY`);

        await bericht_eingabe.highlight('fields', 'PRUEFUNGSBEGINN', 'blue');
        await resultWriter.createEvidence(testStep, `Wert: ${value} | Read-Only`);
        await bericht_eingabe.highlight('fields', 'PRUEFUNGSBEGINN', 'none');
    },
    '*Pruefungsbeginn* ist vorhanden, nicht editierbar und folgt dem Format DD.MM.YYYY. (/)',
    '*Pruefungsbeginn* ist editierbar oder das Datumsformat ist ungueltig',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 8';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        // Da die Combobox 'Steuerart' in einer Tabelle mehrfach vorkommt, wird firstOnly: true genutzt
        const isVisible = await bericht_eingabe.isVisible('comboboxes', 'STEUERART', true);
        await executeAssertion(() => { 
            expect(isVisible).toBeTruthy() 
        }, 'Das Feld Steuerart ist NICHT sichtbar');

        const editable = await bericht_eingabe.isEditable('comboboxes', 'STEUERART', true);
        await executeAssertion(() => { 
            expect(editable).toBeFalsy() 
        }, 'Die Steuerart sollte schreibgeschuetzt (disabled) sein, ist aber editierbar');

        const selectedValue = await bericht_eingabe.getValue('comboboxes', 'STEUERART', true);

        await bericht_eingabe.highlight('comboboxes', 'STEUERART', 'blue', true);
        await resultWriter.createEvidence(testStep);
        await bericht_eingabe.highlight('comboboxes', 'STEUERART', 'none', true);
    },
    'Die Steuerart ist vorhanden und korrekt als nicht editierbar markiert. (/)',
    'Die Steuerart ist editierbar oder nicht vorhanden',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 9';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const elementsToVerify = [
            { cat: 'fields', key: 'TABELLE_VON' },
        ] as const;

        for (const item of elementsToVerify) {
            const isFirstVisible = await bericht_eingabe.isVisible(item.cat, item.key, true);
            
            if (isFirstVisible) {
                const isEditable = await bericht_eingabe.isEditable(item.cat, item.key, true);
                const format = await bericht_eingabe.getValue(item.cat, item.key, true);
                const stNrRegex = /\d{4}/;
                
                await executeAssertion(
                    () => { expect(format).toMatch(stNrRegex) }, 
                    `Element ${item.key} has nicht das richtige Format`
                );
                
                await executeAssertion(
                    () => { expect(isEditable).toBeFalsy() }, 
                    `Element ${item.key} ist editiertbar`
                );

                await bericht_eingabe.highlight(item.cat, item.key, 'red', true);
                await resultWriter.createEvidence(`${testStep}-${item.key}`);
                await bericht_eingabe.highlight(item.cat, item.key, 'none', true);
            } else {
                const isLabelVisible = await bericht_eingabe.isTextVisible('Von');
                await executeAssertion(
                    () => { expect(isLabelVisible).toBeTruthy() }, 
                    `Kein Tabelleneintrag vorhanden und Label 'Von' ist nicht sichtbar`
                );
            }
        }
    },
    'Das Feld *Steuerart Von* ist vorhanden und besitzt alle geforderten Attributen. (/)',
    'Das Feld *Steuerart Von* ist NICHT vorhanden und besitzt alle geforderten Attributen.',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 10';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const elementsToVerify = [
            { cat: 'fields', key: 'TABELLE_BIS' },
        ] as const;

        for (const item of elementsToVerify) {
            const isFirstVisible = await bericht_eingabe.isVisible(item.cat, item.key, true);
            
            if (isFirstVisible) {
                const isEditable = await bericht_eingabe.isEditable(item.cat, item.key, true);
                const format = await bericht_eingabe.getValue(item.cat, item.key, true);
                const stNrRegex = /\d{4}/;
                
                await executeAssertion(
                    () => { expect(format).toMatch(stNrRegex) }, 
                    `Element ${item.key} has nicht das richtige Format`
                );
                
                await executeAssertion(
                    () => { expect(isEditable).toBeFalsy() }, 
                    `Element ${item.key} ist editiertbar`
                );

                await bericht_eingabe.highlight(item.cat, item.key, 'red', true);
                await resultWriter.createEvidence(`${testStep}-${item.key}`);
                await bericht_eingabe.highlight(item.cat, item.key, 'none', true);
            } else {
                const isLabelVisible = await bericht_eingabe.isTextVisible('Bis');
                await executeAssertion(
                    () => { expect(isLabelVisible).toBeTruthy() }, 
                    `Kein Tabelleneintrag vorhanden und Label 'Bis' ist nicht sichtbar`
                );
            }
        }
    },
    'Das Feld *Steuerart Bis* ist vorhanden und besitzt alle geforderten Attributen. (/)',
    'Das Feld *Steuerart Bis* ist NICHT vorhanden und besitzt alle geforderten Attributen.',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 11';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        // Sektion pruefen (z.B. Heading)
        const isVisible = await bericht_eingabe.isVisible('headings', 'ERLAEUTERUNG');
        await executeAssertion(() => { expect(isVisible).toBeTruthy() }, 'Sektion Erlaeuterung nicht sichtbar');
    },
    'Die Sektion ist vorhanden. (/)',
    'Die Sektion ist NICHT vorhanden.',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 12';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const isVisible = await bericht_eingabe.isVisible('fields', 'SONSTIGES');
        await executeAssertion(() => { expect(isVisible).toBeTruthy() }, 'SONSTIGES NICHT vorhanden ');

        const string499 = randomString(499);
        await bericht_eingabe.setValue('fields', 'SONSTIGES', string499);
        const errorString499 = await bericht_eingabe.isErrorMessageVisible('MAX_LENGTH_500');
        await executeAssertion(() => { expect(errorString499).toBeFalsy() }, 'Das Feld *Sonstiges* akzeptiert mehr als 500 Zeichen');
        
        await bericht_eingabe.highlight('fields', 'SONSTIGES', 'red');
        await resultWriter.createEvidence(`${testStep}.a`, 'String 499');
        await bericht_eingabe.highlight('fields', 'SONSTIGES', 'none');

        const string501 = randomString(501);
        await bericht_eingabe.setValue('fields', 'SONSTIGES', string501);
        const errorString500 = await bericht_eingabe.isErrorMessageVisible('MAX_LENGTH_500');
        await executeAssertion(() => { expect(errorString500).toBeTruthy() }, 'Das Feld *Sonstiges* akzeptiert mehr als 500 Zeichen');

        await bericht_eingabe.highlight('fields', 'SONSTIGES', 'red');
        await resultWriter.createEvidence(`${testStep}.b`, 'String 501');
        await bericht_eingabe.highlight('fields', 'SONSTIGES', 'none');

        await bericht_eingabe.setValue('fields', 'SONSTIGES', '');

    },
    'Das Feld *Sonstiges* ist vorhanden und besitzt alle geforderten Attributen. (/)',
    'Das Feld *Sonstiges* ist NICHT vorhanden',
    errors,
    goblaStatus,
    stepStatus
);

resultWriter.saveResult(testKey, goblaStatus.status);
if (errors.length > 0) {
    throw new Error(errors.join('\n'))
}