import type {Page, Locator} from "playwright"
declare const page: Page;
// DIESE ZEILE IST SEHR WICHTIG!! NICHT LÖSCHEN #NBELPH69

const bp = new PruefungsberichtMainPage(page)
const stp = new SteuerpflichtigenPage(page)
const ums = new UbermittlungsschreibenPage(page)

const testKey = 'PDNEU-1311'
const resultWriter = new ResultWriter(page, testKey);
const goblaStatus = { status: 'PASS' };
const stepStatus = { status: 'PASS' };
const errors: string[] = [];

let testStep = 'step 1'
await executeStep(
    testStep,
    resultWriter,
    async () => {
        await resultWriter.createEvidence(testStep);
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
        await stp.click('radios', 'NICHT_NATUERLICHE_PERSON');

        const isVisible = stp.isVisible('fields', 'FIRMENNAME');
        await executeAssertion(() => { expect(isVisible).toBeTruthy() }, 'FIRMENNAME NICHT vorhanden ');

        const string250 = randomString(250);
        await stp.setValue('fields', 'FIRMENNAME', string250);
        await stp.highlight('fields', 'FIRMENNAME', 'red');
        await resultWriter.createEvidence(`${testStep}.a`, 'String 250');
        await stp.highlight('fields', 'FIRMENNAME', 'none');

        const string300 = randomString(300);
        await stp.setValue('fields', 'FIRMENNAME', string300);
        await stp.highlight('fields', 'FIRMENNAME', 'red');
        await resultWriter.createEvidence(`${testStep}.b`, 'String 250');
        await stp.highlight('fields', 'FIRMENNAME', 'none');

        await stp.setValue('fields', 'FIRMENNAME', '');

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
        // 1. Sichtbarkeit prüfen
        const isVisible = await stp.isVisible('fields', 'STEUERNUMMER');
        await executeAssertion(() => { 
            expect(isVisible).toBeTruthy() 
        }, 'Steuernummer Feld ist NICHT vorhanden');

        // 2. Element hervorheben
        await stp.highlight('fields', 'STEUERNUMMER', 'red');

        // 3. Wert auslesen
        const stNrValue = await stp.getValue('fields', 'STEUERNUMMER');
        
        // 4. Format prüfen (Regex: \d{4}/0/\d{4}/\d{4}/)
        // Wir nutzen eine JS-RegExp. ^ und $ stellen sicher, dass der gesamte String passt.
        const stNrRegex = /\d{4}\/0\/\d{4}\/\d{4}/;
        
        await executeAssertion(() => { 
            expect(stNrValue).toMatch(stNrRegex) 
        }, `Steuernummer '${stNrValue}' entspricht nicht dem Format \d{4}/0/\d{4}/\d{4}/`);

        // 5. Evidenz erstellen
        await resultWriter.createEvidence(`${testStep}`, `Gelesener Wert: ${stNrValue}`);

        // 6. Highlight entfernen
        await stp.highlight('fields', 'STEUERNUMMER', 'none');
    },
    'Die Steuernummer ist vorhanden, schreibgeschützt und entspricht dem Format \d{4}/0/\d{4}/\d{4}/. (/)',
    'Die Steuernummer fehlt oder besitzt ein ungültiges Format',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 4';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        // Definition der zu prüfenden Elemente [Kategorie, Key]
        const elementsToVerify = [
            { cat: 'fields', key: 'PRUEFUNGSNUMMER' },
            { cat: 'fields', key: 'PRUEFUNGSBEGINN' },
            { cat: 'fields', key: 'PRUEFUNGSANORDNUNG' },
            { cat: 'comboboxes', key: 'STEUERART' },
            { cat: 'fields', key: 'TABELLE_VON' },
            { cat: 'fields', key: 'TABELLE_BIS' },
        ] as const;

        for (const item of elementsToVerify) {
            // 1. Sichtbarkeit prüfen
            const isVisible = await stp.isVisible(item.cat, item.key);
            
            // 2. Assertion: Wenn ein Feld fehlt, bricht der Test hier mit Fehlermeldung ab
            await executeAssertion(
                () => { expect(isVisible).toBeTruthy() }, 
                `Element ${item.key} in Kategorie ${item.cat} ist NICHT sichtbar`
            );

            // 3. Kurz hervorheben für die Evidenz
            await stp.highlight(item.cat, item.key, 'red');
            await resultWriter.createEvidence(`${testStep}-${item.key}`, `Sichtbarkeit von ${item.key} bestätigt`);
            await stp.highlight(item.cat, item.key, 'none');
        }
    },
    'Alle Felder im Bereich Prüfung (Nummer, Beginn, Anordnung, Steuerart, Von, Bis) sind sichtbar. (/)',
    'Eines oder mehrere Felder im Bereich Prüfung sind NICHT sichtbar',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 5';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        // Definition der zu prüfenden Elemente [Kategorie, Key]
        const elementsToVerify = [
            { cat: 'fields', key: 'PRUEFUNGSANORDNUNG' },
        ] as const;

        for (const item of elementsToVerify) {
            // 1. Sichtbarkeit prüfen
            const isVisible = await stp.isEditable(item.cat, item.key);
            const format = await stp.getValue(item.cat, item.key);
            const stNrRegex =/^\d{2}\.\d{2}\.\d{4}$/
            // 2. Assertion: Wenn ein Feld fehlt, bricht der Test hier mit Fehlermeldung ab
            await executeAssertion(
                () => { expect(format).toMatch(stNrRegex) }, 
                `Element ${item.key} has nicht das richtige Format`
            );
            
            await executeAssertion(
                () => { expect(isVisible).toBeFalsy() }, 
                `Element ${item.key} ist editiertbar`
            );

            // 3. Kurz hervorheben für die Evidenz
            await stp.highlight(item.cat, item.key, 'red');
            await resultWriter.createEvidence(`${testStep}-${item.key}`, `Sichtbarkeit von ${item.key} bestätigt`);
            await stp.highlight(item.cat, item.key, 'none');
        }
    },
    'Das Feld *PrüfungsanordnungVom* ist vorhanden und besitzt alle geforderten Attributen. (/)',
    'Das Feld *PrüfungsanordnungVom* ist NICHT vorhanden und besitzt alle geforderten Attributen.',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 6';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        // 1. Sichtbarkeit prüfen
        const isVisible = await stp.isVisible('fields', 'PRUEFUNGSNUMMER');
        await executeAssertion(() => { 
            expect(isVisible).toBeTruthy() 
        }, 'Prüfungsnummer Feld ist NICHT vorhanden');

        // 2. Prüfen, ob das Feld NICHT editierbar ist (read-only / disabled)
        const editable = await stp.isEditable('fields', 'PRUEFUNGSNUMMER');
        await executeAssertion(() => { 
            expect(editable).toBeFalsy() 
        }, 'Die Prüfungsnummer sollte NICHT editierbar sein, ist es aber');

        // 3. Wert auslesen und Format prüfen
        const value = await stp.getValue('fields', 'PRUEFUNGSNUMMER');
        
        // Regex: 
        const pruefungsNrRegex = /\d{4}\s\d{2}\s\d\s\d{5}/;
        
        await executeAssertion(() => { 
            expect(value).toMatch(pruefungsNrRegex) 
        }, `Prüfungsnummer '${value}' entspricht nicht dem Format`);

        // 4. Visuelle Dokumentation (Evidence)
        await stp.highlight('fields', 'PRUEFUNGSNUMMER', 'blue');
        await resultWriter.createEvidence(testStep, `Wert: ${value} | Editierbar: ${editable}`);
        await stp.highlight('fields', 'PRUEFUNGSNUMMER', 'none');
    },
    'Die Prüfungsnummer ist vorhanden, nicht editierbar und folgt dem Format \d{4} \d{2} \d \d{5}. (/)',
    'Die Prüfungsnummer ist editierbar oder hat ein falsches Format',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 7';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        // 1. Sichtbarkeit prüfen
        const isVisible = await stp.isVisible('fields', 'PRUEFUNGSBEGINN');
        await executeAssertion(() => { 
            expect(isVisible).toBeTruthy() 
        }, 'Prüfungsnummer Feld ist NICHT vorhanden');

        // 2. Prüfen, ob das Feld NICHT editierbar ist
        const editable = await stp.isEditable('fields', 'PRUEFUNGSBEGINN');
        await executeAssertion(() => { 
            expect(editable).toBeFalsy() 
        }, 'Die Prüfungsnummer sollte schreibgeschützt sein, ist aber editierbar');

        // 3. Wert auslesen
        const value = await stp.getValue('fields', 'PRUEFUNGSBEGINN');
        
        // Regex 
        const dateRegex = /^\d{2}\.\d{2}\.\d{4}$/;
        
        await executeAssertion(() => { 
            expect(value).toMatch(dateRegex) 
        }, `Der Wert '${value}' entspricht nicht dem Format DD.MM.YYYY`);

        // 4. Visuelle Dokumentation
        await stp.highlight('fields', 'PRUEFUNGSBEGINN', 'blue');
        await resultWriter.createEvidence(testStep, `Wert: ${value} | Read-Only: true`);
        await stp.highlight('fields', 'PRUEFUNGSBEGINN', 'none');
    },
    'Die PRUEFUNGSBEGINN ist vorhanden, nicht editierbar und folgt dem Format DD.MM.YYYY. (/)',
    'Die PRUEFUNGSBEGINN ist editierbar oder das Datumsformat ist ungültig',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 8';
await executeStep(
    'step_steuerart_readonly',
    resultWriter,
    async () => {
        // 1. Sichtbarkeit prüfen
        const isVisible = await stp.isVisible('comboboxes', 'STEUERART');
        await executeAssertion(() => { 
            expect(isVisible).toBeTruthy() 
        }, 'Das Feld Steuerart ist NICHT sichtbar');

        // 2. Prüfen, ob die Combobox NICHT editierbar ist
        // Die Methode isEditable prüft intern auf .disabled und .readOnly
        const editable = await stp.isEditable('comboboxes', 'STEUERART');
        await executeAssertion(() => { 
            expect(editable).toBeFalsy() 
        }, 'Die Steuerart sollte schreibgeschützt (disabled) sein, ist aber editierbar');

        // 3. Aktuellen Wert auslesen (zur Dokumentation in der Evidenz)
        // Hinweis: getValue muss im POM für Comboboxen eventuell 
        // über .inputValue() oder .evaluate() gelöst sein.
        const selectedValue = await stp.getValue('comboboxes', 'STEUERART');

        // 4. Visuelle Dokumentation
        await stp.highlight('comboboxes', 'STEUERART', 'blue');
        await resultWriter.createEvidence(
            testStep, 
            `Steuerart: ${selectedValue} | Status: Nicht editierbar`
        );
        await stp.highlight('comboboxes', 'STEUERART', 'none');
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
        // Definition der zu prüfenden Elemente [Kategorie, Key]
        const elementsToVerify = [
            { cat: 'fields', key: 'TABELLE_VON' },
        ] as const;

        for (const item of elementsToVerify) {
            // 1. Sichtbarkeit prüfen
            const isVisible = await stp.isEditable(item.cat, item.key);
            const format = await stp.getValue(item.cat, item.key);
            const stNrRegex = /\d{4}/;
            // 2. Assertion: Wenn ein Feld fehlt, bricht der Test hier mit Fehlermeldung ab
            await executeAssertion(
                () => { expect(format).toMatch(stNrRegex) }, 
                `Element ${item.key} has nicht das richtige Format`
            );
            
            await executeAssertion(
                () => { expect(isVisible).toBeFalsy() }, 
                `Element ${item.key} ist editiertbar`
            );

            // 3. Kurz hervorheben für die Evidenz
            await stp.highlight(item.cat, item.key, 'red');
            await resultWriter.createEvidence(`${testStep}-${item.key}`, `Sichtbarkeit von ${item.key} bestätigt`);
            await stp.highlight(item.cat, item.key, 'none');
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
        // Definition der zu prüfenden Elemente [Kategorie, Key]
        const elementsToVerify = [
            { cat: 'fields', key: 'TABELLE_BIS' },
        ] as const;

        for (const item of elementsToVerify) {
            // 1. Sichtbarkeit prüfen
            const isVisible = await stp.isEditable(item.cat, item.key);
            const format = await stp.getValue(item.cat, item.key);
            const stNrRegex = /\d{4}/;
            // 2. Assertion: Wenn ein Feld fehlt, bricht der Test hier mit Fehlermeldung ab
            await executeAssertion(
                () => { expect(format).toMatch(stNrRegex) }, 
                `Element ${item.key} has nicht das richtige Format`
            );
            
            await executeAssertion(
                () => { expect(isVisible).toBeFalsy() }, 
                `Element ${item.key} ist editiertbar`
            );

            // 3. Kurz hervorheben für die Evidenz
            await stp.highlight(item.cat, item.key, 'red');
            await resultWriter.createEvidence(`${testStep}-${item.key}`, `Sichtbarkeit von ${item.key} bestätigt`);
            await stp.highlight(item.cat, item.key, 'none');
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
        const isVisible = stp.isVisible('fields', 'SONSTIGES');
        await executeAssertion(() => { expect(isVisible).toBeTruthy() }, 'SONSTIGES NICHT vorhanden ');

        const string499 = randomString(499);
        await stp.setValue('fields', 'SONSTIGES', string499);
        await stp.highlight('fields', 'SONSTIGES', 'red');
        await resultWriter.createEvidence(`${testStep}.a`, 'String 499');
        await stp.highlight('fields', 'SONSTIGES', 'none');

        const string501 = randomString(501);
        await stp.setValue('fields', 'SONSTIGES', string501);
        await stp.highlight('fields', 'SONSTIGES', 'red');
        await resultWriter.createEvidence(`${testStep}.b`, 'String 501');
        await stp.highlight('fields', 'SONSTIGES', 'none');

        await stp.setValue('fields', 'SONSTIGES', '');

    },
    'Das Feld SONSTIGES ist vorhanden und besitzt alle geforderten Attributen. (/)',
    'Das Feld SONSTIGES ist NICHT vorhanden',
    errors,
    goblaStatus,
    stepStatus
);
resultWriter.saveResult(testKey, goblaStatus.status);
if (errors.length > 0) {
    throw new Error(errors.join('\n'))
}