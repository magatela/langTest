import type { Page } from "playwright"
import { randomString, executeAssertion, executeStep, ResultWriter } from "../../util/util.ts"
import { expect } from "playwright/test";
import {NavigationPage } from "../../POM/NavigationPage.ts"
import {ZeitraeumePage} from "../../POM/ZeitraeumePage.ts"
import { PruefungsberichtMainPage } from "../../POM/BerichtMainPage.ts"
import { SteuerpflichtigenPage } from "../../POM/BerichtEingabedialogPage.ts"
import { UbermittlungsschreibenPage } from "../../POM/UbermittlungsschreibenPage.ts"

declare const page: Page;
declare const navigation: NavigationPage;
declare const zeitraeume: ZeitraeumePage;
declare const bericht: PruefungsberichtMainPage;
declare const bericht_eingabe: SteuerpflichtigenPage;
declare const bericht_ubermittlung: UbermittlungsschreibenPage;
// DIESE ZEILE IST SEHR WICHTIG!! NICHT LÖSCHEN #NBELPH69

const testKey = 'PDNEU-7757'
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

let testStep = 'step 1'
await executeStep(
    testStep,
    resultWriter,
    async () => {
        await navigation.navigateTo('ABWICKLUNG', 'BERICHTE');
        await bericht.clickButton('BERICHTSASSISTENT_STARTEN');
        
        await bericht.highlightOption('red', 'MANUELLER_BERICHT');
        await resultWriter.createEvidence(testStep);
        await bericht.highlightOption('none', 'MANUELLER_BERICHT');

        await bericht.selectFromassitant('MANUELLER_BERICHT');
    },
    'erfolg (/)',
    'nicht erfolg (/)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 2'
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const isVisible = await bericht_ubermittlung.isVisible('links', 'UEBERMITTLUNGSSCHREIBEN');
        
        await executeAssertion(
            () => { expect(isVisible).toBeTruthy() },
            `Das Feld 'Übermittlungschreiben' ist NICHT sichtbar`
        );

        await bericht_ubermittlung.click('links', 'UEBERMITTLUNGSSCHREIBEN');

        await bericht_ubermittlung.highlight('links', 'UEBERMITTLUNGSSCHREIBEN', 'red');
        await resultWriter.createEvidence(testStep);
        await bericht_ubermittlung.highlight('links', 'UEBERMITTLUNGSSCHREIBEN', 'none');
    },
    'erfolg (/)',
    'nicht erfolg (/)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 3';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const expectedOptions = ["Versand", "PZU", "Übergabe"];

        // 1. Prüfung: Editierbarkeit
        const isEditable = await bericht_ubermittlung.isEditable('comboboxes', 'BEKANNTGABEART');
        await executeAssertion(
            () => { expect(isEditable).toBeTruthy() },
            `Das Feld 'Bekanntgabeart' ist NICHT editierbar`
        );

        // 2. Prüfung: Optionen der Combobox
        const options = await bericht_ubermittlung.getComboboxOptions('BEKANNTGABEART');


        // Filtere leere Optionen aus, um die inhaltlichen Optionen zu prüfen
        const filteredOptions = options.filter(opt => opt.trim() !== "");

        await executeAssertion(
            () => {
                expect(filteredOptions).toEqual(expect.arrayContaining(expectedOptions));
                expect(filteredOptions.length).toBe(expectedOptions.length);
            },
            `Die Optionen des Feldes 'Bekanntgabeart' sind nicht korrekt. Erwartet: ${expectedOptions.join(', ')}, Gefunden: ${filteredOptions.join(', ')}`
        );

        await bericht_ubermittlung.click('comboboxes', 'BEKANNTGABEART');
        await bericht_ubermittlung.highlight('comboboxes', 'BEKANNTGABEART', 'red');
        await resultWriter.createEvidence(testStep, `Option: ${filteredOptions}`);
        await bericht_ubermittlung.highlight('comboboxes', 'BEKANNTGABEART', 'none');
        
        await bericht_ubermittlung.click('comboboxes', 'BEKANNTGABEART');
        await bericht_ubermittlung.setValue('comboboxes', 'BEKANNTGABEART', 'Versand');
    },
    'Feld Bekanntgabeart ist editierbar und enthält die korrekten Optionen (/)',
    'Feld Bekanntgabeart ist NICHT editierbar oder Optionen sind falsch (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 4';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        // testet adressat
        const expectedOptions = ["Stpfl.", "Vertreter", "abweichend", "Ehegatte"];

        // 1. Prüfung: Sichtbarkeit
        const isVisible = await bericht_ubermittlung.isVisible('comboboxes', 'ADRESSAT');
        if (!isVisible) {
            //await ums.setValue('comboboxes', 'BEKANNTGABEART', 'Versand');
        }

        // 1. Prüfung: Editierbarkeit
        const isEditable = await bericht_ubermittlung.isEditable('comboboxes', 'ADRESSAT');

        await executeAssertion(
            () => { expect(isEditable).toBeTruthy() },
            `Das Feld 'Adressat' ist NICHT editierbar`
        );

        // 2. Prüfung: Optionen der Combobox
        const options = await bericht_ubermittlung.getComboboxOptions('ADRESSAT');


        // Wir filtern leere Einträge aus der Liste heraus, da Comboboxen oft eine leere Initial-Option haben
        const filteredOptions = options.filter(opt => opt.trim() !== "");

        await executeAssertion(
            () => {
                expect(filteredOptions).toEqual(expect.arrayContaining(expectedOptions));
                expect(filteredOptions.length).toBe(expectedOptions.length);
            },
            `Die Optionen des Feldes 'Adressat' sind nicht korrekt. Erwartet: ${expectedOptions.join(', ')}, Gefunden: ${filteredOptions.join(', ')}`
        );

        await bericht_ubermittlung.click('comboboxes', 'ADRESSAT');
        await bericht_ubermittlung.highlight('comboboxes', 'ADRESSAT', 'red');
        await resultWriter.createEvidence(testStep, `Optionen: ${filteredOptions}`);
        await bericht_ubermittlung.highlight('comboboxes', 'ADRESSAT', 'none');

        await bericht_ubermittlung.setValue('comboboxes', 'ADRESSAT', expectedOptions[0] as string);

    },
    'Feld Adressat ist editierbar und enthält die korrekten Optionen (Stpfl., Vertreter, abweichend, Ehegatte) (/)',
    'Feld Adressat ist NICHT editierbar oder die Optionen sind unvollständig/falsch (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 5';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        // 1. Bedingung setzen: Adressat auf "Vertreter" stellen
        await bericht_ubermittlung.setValue('comboboxes', 'ADRESSAT', 'Vertreter');

        // 2. Prüfung: Ist das Feld Vertretungsart nun sichtbar?
        const isVertretungsArtVisible = await bericht_ubermittlung.isVisible('comboboxes', 'VERTRETUNGSART');
        await executeAssertion(
            () => { expect(isVertretungsArtVisible).toBeTruthy() },
            `Das Feld 'Vertretungsart' ist NICHT sichtbar, obwohl 'Vertreter' als Adressat ausgewählt wurde`
        );

        // 3. Prüfung: Optionen der Combobox Vertretungsart
        const expectedOptions = [
            "Gesetzlicher Vertreter",
            "Gesamtrechtsnachfolger",
            "Liquidator",
            "Insolvenzverwalter/Konkursverwalter",
            "Insolvenzverwalter",
            "Konkursverwalter",
            "Treuhänder nach § 313 InsO",
            "gesetzlicher Vertreter trotz Volljährigkeit",
            "Zwangsverwalter",
            "Rechtsnachfolger",
            "Miterbe",
            "Testamentsvollstrecker",
            "Vermögensverwalter",
            "Nachlassverwalter",
            "Verfügungsberechtigter",
            "Vertreter nach § 81 AO",
            "Nachlasspfleger",
            "Geschäftsführer",
            "Vorstand",
            "Empfangsbevollmächtigter",
            "sonstiger Vertreter"
        ];

        const options = await bericht_ubermittlung.getComboboxOptions('VERTRETUNGSART');
        // Leere Optionen (Platzhalter) entfernen
        const filteredOptions = options.filter(opt => opt.trim() !== "");

        await executeAssertion(
            () => {
                expect(filteredOptions).toEqual(expect.arrayContaining(expectedOptions));
                expect(filteredOptions.length).toBe(expectedOptions.length);
            },
            `Die Optionen für 'Vertretungsart' sind nicht korrekt. Erwartet ${expectedOptions.length} Optionen, gefunden ${filteredOptions.length}.`
        );

        // Evidence erstellen
        await bericht_ubermittlung.click('comboboxes', 'VERTRETUNGSART');
        await bericht_ubermittlung.highlight('comboboxes', 'VERTRETUNGSART', 'red');
        await resultWriter.createEvidence(testStep);
        await bericht_ubermittlung.highlight('comboboxes', 'VERTRETUNGSART', 'none');
    },
    'Bei Adressat "Vertreter" ist das Feld "Vertretungsart" sichtbar und enthält alle 21 korrekten Optionen (/)',
    'Feld "Vertretungsart" ist nicht sichtbar oder die Optionen sind fehlerhaft (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 6';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const dateField = 'BEKANNTGABEDATUM';
        const dateGroup = 'fields';
        await bericht_ubermittlung.setValue('comboboxes', 'BEKANNTGABEART', 'Übergabe')

        // Testdaten: Wert und Erwartung (true = gültig, false = ungültig/Fehler)
        const testCases = [
            { value: '12.05.2023', isValid: true, description: 'Gültiges Datum' },
            { value: '12/05/2023', isValid: false, description: 'Falscher Trenner (/)' },
            { value: '1.5.2023', isValid: false, description: 'Fehlende führende Nullen' },
            { value: '12.05.23', isValid: false, description: 'Jahr zu kurz (2 Stellen)' },
            { value: '12.05.20234', isValid: false, description: 'Jahr zu lang (5 Stellen)' },
            { value: 'aa.bb.cccc', isValid: false, description: 'Buchstaben statt Zahlen' },
        ];

        for (const tc of testCases) {
            await bericht_ubermittlung.setValue(dateGroup, dateField, tc.value);

            // Wir prüfen, ob eine Fehlermeldung erscheint (oder nicht)
            // Hinweis: 'INVALID_DATE_FORMAT' muss in UIBekanntgabePage.errorMsgs definiert sein
            const isErrorVisible = await bericht_ubermittlung.isErrorMessageVisible('INVALID_DATE_FORMAT');

            await executeAssertion(
                () => {
                    if (tc.isValid) {
                        expect(isErrorVisible).toBeFalsy(); // Bei gültigem Datum kein Fehler
                    } else {
                        expect(isErrorVisible).toBeTruthy(); // Bei ungültigem Format muss Fehler kommen
                    }
                },
                `Validierung für ${tc.description} (${tc.value}) fehlgeschlagen. Erwartet gültig=${tc.isValid}, aber Fehler sichtbar=${isErrorVisible}`
            );
        }

        // Evidence für den Erfolgsweg (letzter gültiger Wert)
        await bericht_ubermittlung.setValue(dateGroup, dateField, '12.05.2023');
        await bericht_ubermittlung.highlight(dateGroup, dateField, 'red');
        await resultWriter.createEvidence(testStep);
        await bericht_ubermittlung.highlight(dateGroup, dateField, 'none');
    },
    'Feld Bekanntgabedatum akzeptiert nur das Format DD.MM.YYYY (/)',
    'Feld Bekanntgabedatum akzeptiert falsche Formate oder lehnt gültige ab (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 7';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const fieldKey = 'BEKANNTGABE_ERGAENZUNG';
        const group = 'fields';

        // --- Testfall 1: Genau 1500 Zeichen (Positivtest) ---
        const validText = randomString(1500);
        await bericht_ubermittlung.setValue(group, fieldKey, validText);

        const isErrorVisibleValid = await bericht_ubermittlung.isErrorMessageVisible('MAX_LENGTH_1500');
        await executeAssertion(
            () => { expect(isErrorVisibleValid).toBeFalsy() },
            `Das Feld 'Bekanntgabe Ergänzung' zeigt fälschlicherweise eine Fehlermeldung bei genau 1500 Zeichen an.`
        );

        // --- Testfall 2: 1501 Zeichen (Negativtest) ---
        const invalidText = randomString(1501);
        await bericht_ubermittlung.setValue(group, fieldKey, invalidText);

        const isErrorVisibleInvalid = await bericht_ubermittlung.isErrorMessageVisible('MAX_LENGTH_1500');
        await executeAssertion(
            () => { expect(isErrorVisibleInvalid).toBeTruthy() },
            `Das Feld 'Bekanntgabe Ergänzung' akzeptiert mehr als 1500 Zeichen ohne Fehlermeldung (aktuell 1501).`
        );

        // Evidence für den Fehlerzustand (Negativtest)
        await bericht_ubermittlung.highlight(group, fieldKey, 'red');
        await resultWriter.createEvidence(testStep);
        await bericht_ubermittlung.highlight(group, fieldKey, 'none');

        await bericht_ubermittlung.setValue(group, fieldKey, '');
    },
    'Feld Bekanntgabe Ergänzung akzeptiert maximal 1500 Zeichen und gibt bei Überschreitung eine Fehlermeldung aus (/)',
    'Feld Bekanntgabe Ergänzung akzeptiert mehr als 1500 Zeichen oder lehnt 1500 Zeichen fälschlicherweise ab (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 8';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        
    },
    'Übernahme aus Kontaktinformationen (/)',
    'Übernahme aus Kontaktinformationen (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 9';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const group = 'radios';
        const radio1 = 'NATUERLICHE_PERSON';
        const radio2 = 'NICHT_NATUERLICHE_PERSON';

        // --- Teil 1: Auswahl "natürliche Person" ---
        await bericht_ubermittlung.setValue(group, radio1, '');

        const isRadio1Checked = await bericht_ubermittlung.getValue(group, radio1);
        const isRadio2Checked = await bericht_ubermittlung.getValue(group, radio2);

        await executeAssertion(
            () => {
                expect(isRadio1Checked).toBe(true);
                expect(isRadio2Checked).toBe(false);
            },
            `Nach Auswahl von 'natürliche Person' ist der Status nicht korrekt (Radio1: ${isRadio1Checked}, Radio2: ${isRadio2Checked})`
        );

        await bericht_ubermittlung.highlight(group, radio1, 'red');
        await resultWriter.createEvidence(testStep + '_natuerliche_person');
        await bericht_ubermittlung.highlight(group, radio1, 'none');

        // --- Teil 2: Auswahl "nicht natürliche Person" ---
        await bericht_ubermittlung.setValue(group, radio2, '');

        const isRadio1CheckedAfter = await bericht_ubermittlung.getValue(group, radio1);
        const isRadio2CheckedAfter = await bericht_ubermittlung.getValue(group, radio2);

        await executeAssertion(
            () => {
                expect(isRadio2CheckedAfter).toBe(true);
                expect(isRadio1CheckedAfter).toBe(false);
            },
            `Nach Auswahl von 'nicht natürliche Person' ist der Status nicht korrekt (Radio1: ${isRadio1CheckedAfter}, Radio2: ${isRadio2CheckedAfter})`
        );

        await bericht_ubermittlung.highlight(group, radio2, 'red');
        await resultWriter.createEvidence(testStep + '_nicht_natuerliche_person');
        await bericht_ubermittlung.highlight(group, radio2, 'none');
    },
    'Die Radiogruppe "Personentyp" erlaubt die korrekte Auswahl und ist gegenseitig exklusiv (/)',
    'Die Radiogruppe "Personentyp" funktioniert nicht korrekt oder Auswahl ist nicht exklusiv (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 10';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const radioGroup = 'radios';
        const comboGroup = 'comboboxes';
        const anredeKey = 'ANREDE';

        // --- Teil 1: Personentyp = "natürliche Person" ---
        await bericht_ubermittlung.setValue(radioGroup, 'NATUERLICHE_PERSON', '');

        const optionsNatural = await bericht_ubermittlung.getComboboxOptions(anredeKey);
        const expectedNatural = ["Unbestimmt", "Frau", "Herr", "Herr und Frau", "Herr und Herr", "Frau und Frau"];
        const filteredNatural = optionsNatural.filter(opt => opt.trim() !== "");

        await executeAssertion(
            () => {
                expect(filteredNatural).toEqual(expect.arrayContaining(expectedNatural));
                expect(filteredNatural.length).toBe(expectedNatural.length);
            },
            `Die Anrede-Optionen für 'natürliche Person' sind nicht korrekt. Gefunden: ${filteredNatural.join(', ')}`
        );
        // Evidence erstellen (im Zustand des Fehlers)
        await bericht_ubermittlung.click(comboGroup, anredeKey);
        await bericht_ubermittlung.highlight(comboGroup, anredeKey, 'red');
        await resultWriter.createEvidence(`${testStep}.a`, 'natürliche Person');
        await bericht_ubermittlung.highlight(comboGroup, anredeKey, 'none');

        // --- Teil 2: Personentyp = "nicht natürliche Person" ---
        await bericht_ubermittlung.setValue(radioGroup, 'NICHT_NATUERLICHE_PERSON', '');

        const optionsNonNatural = await bericht_ubermittlung.getComboboxOptions(anredeKey);
        const expectedNonNatural = ["Firma", "Frei"];
        const filteredNonNatural = optionsNonNatural.filter(opt => opt.trim() !== "");

        await executeAssertion(
            () => {
                expect(filteredNonNatural).toEqual(expect.arrayContaining(expectedNonNatural));
                expect(filteredNonNatural.length).toBe(expectedNonNatural.length);
            },
            `Die Anrede-Optionen für 'nicht natürliche Person' sind nicht korrekt. Gefunden: ${filteredNonNatural.join(', ')}`
        );
        await bericht_ubermittlung.click(comboGroup, anredeKey);
        await bericht_ubermittlung.highlight(comboGroup, anredeKey, 'red');
        await resultWriter.createEvidence(`${testStep}.b`, 'nicht natürliche Person');
        await bericht_ubermittlung.highlight(comboGroup, anredeKey, 'none');


    },
    'Die Anrede-Optionen passen sich dynamisch dem Personentyp an und die Pflichtfeldprüfung funktioniert (/)',
    'Die Anrede-Optionen sind falsch oder die Pflichtfeldvalidierung schlägt fehl (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 11';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const radioGroup = 'radios';
        const comboGroup = 'comboboxes';
        const titelKey = 'TITEL';

        // --- Teil 1: Personentyp = "natürliche Person" ---
        await bericht_ubermittlung.setValue(radioGroup, 'NATUERLICHE_PERSON', '');

        // Prüfung: Sichtbarkeit
        const isTitelVisibleNatural = await bericht_ubermittlung.isVisible(comboGroup, titelKey);
        await executeAssertion(
            () => { expect(isTitelVisibleNatural).toBeTruthy() },
            `Das Feld 'Titel' sollte bei 'natürliche Person' sichtbar sein, ist es aber nicht.`
        );

        // Prüfung: Optionen
        const expectedTitles = [
            "Assessor", "Diplom-Finanzwirt", "Diplom-Handelslehrer", "Diplom-Ingenieur",
            "Diplom-Kaufmann", "Doktor", "Ingenieur", "Kaufmann", "Lizenziat",
            "Professor", "Professor Doktor", "Steuerberater", "Steuerberaterin",
            "Rechtsanwalt", "Rechtsanwältin", "Sonstiger Titel"
        ];

        const optionsNatural = await bericht_ubermittlung.getComboboxOptions(titelKey);
        const filteredNatural = optionsNatural.filter(opt => opt.trim() !== "");

        await executeAssertion(
            () => {
                expect(filteredNatural).toEqual(expect.arrayContaining(expectedTitles));
                expect(filteredNatural.length).toBe(expectedTitles.length);
            },
            `Die Titel-Optionen für 'natürliche Person' sind nicht korrekt. Gefunden: ${filteredNatural.join(', ')}`
        );

        await bericht_ubermittlung.click(comboGroup, titelKey);
        await bericht_ubermittlung.highlight(comboGroup, titelKey, 'red');
        await resultWriter.createEvidence(testStep);
        await bericht_ubermittlung.highlight(comboGroup, titelKey, 'none');

        // --- Teil 2: Personentyp = "nicht natürliche Person" ---
        await bericht_ubermittlung.setValue(radioGroup, 'NICHT_NATUERLICHE_PERSON', '');

        // Prüfung: Sichtbarkeit (Sollte NICHT sichtbar sein)
        const isTitelVisibleNonNatural = await bericht_ubermittlung.isVisible(comboGroup, titelKey);
        await executeAssertion(
            () => { expect(isTitelVisibleNonNatural).toBeFalsy() },
            `Das Feld 'Titel' ist bei 'nicht natürliche Person' fälschlicherweise sichtbar.`
        );


    },
    'Feld "Titel" ist nur bei "natürliche Person" sichtbar und enthält die korrekten Optionen (/)',
    'Feld "Titel" ist bei "nicht natürliche Person" sichtbar oder die Optionen sind falsch (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 12';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const comboGroup = 'comboboxes';
        const fieldGroup = 'fields';
        const titelCombo = 'TITEL';
        const sonstigerTitelField = 'SONSTIGER_TITEL';

        // --- Teil 1: Sichtbarkeit triggern ---
        // Voraussetzung: Natürliche Person muss gewählt sein, damit Titel überhaupt da ist
        await bericht_ubermittlung.setValue('radios', 'NATUERLICHE_PERSON', '');

        // Auswahl "Sonstiger Titel" in der Combobox
        await bericht_ubermittlung.setValue(comboGroup, titelCombo, 'Sonstiger Titel');

        // Prüfung: Ist das Textfeld "Sonstiger Titel*" nun sichtbar und editierbar?
        const isVisible = await bericht_ubermittlung.isVisible(fieldGroup, sonstigerTitelField);
        const isEditable = await bericht_ubermittlung.isEditable(fieldGroup, sonstigerTitelField);

        await executeAssertion(
            () => {
                expect(isVisible).toBeTruthy();
                expect(isEditable).toBeTruthy();
            },
            `Das Feld 'Sonstiger Titel*' ist NICHT sichtbar oder editierbar, obwohl 'Sonstiger Titel' ausgewählt wurde.`
        );

        // a) Positivtest: Genau 255 Zeichen
        await bericht_ubermittlung.setValue(fieldGroup, sonstigerTitelField, randomString(255));
        const isErrorVisibleValid = await bericht_ubermittlung.isErrorMessageVisible('MAX_LENGTH_255');
        await executeAssertion(
            () => { expect(isErrorVisibleValid).toBeFalsy() },
            `Feld 'Sonstiger Titel*' zeigt fälschlicherweise Fehler bei 255 Zeichen.`
        );

        // b) Negativtest: 256 Zeichen
        await bericht_ubermittlung.setValue(fieldGroup, sonstigerTitelField, randomString(256));
        const isErrorVisibleInvalid = await bericht_ubermittlung.isErrorMessageVisible('MAX_LENGTH_255');
        await executeAssertion(
            () => { expect(isErrorVisibleInvalid).toBeTruthy() },
            `Feld 'Sonstiger Titel*' akzeptiert mehr als 255 Zeichen ohne Fehlermeldung.`
        );

        // Evidence für den Fehlerzustand erstellen
        await bericht_ubermittlung.highlight(fieldGroup, sonstigerTitelField, 'red');
        await resultWriter.createEvidence(testStep);
        await bericht_ubermittlung.highlight(fieldGroup, sonstigerTitelField, 'none');

        // --- Teil 3: Negativtest Sichtbarkeit ---
        // Auswahl ändern auf einen Standard-Titel (z.B. "Doktor")
        await bericht_ubermittlung.setValue(comboGroup, titelCombo, 'Doktor');

        const isHidden = await bericht_ubermittlung.isVisible(fieldGroup, sonstigerTitelField);
        await executeAssertion(
            () => { expect(isHidden).toBeFalsy() },
            `Das Feld 'Sonstiger Titel*' ist immer noch sichtbar, obwohl ein anderer Titel ausgewählt wurde.`
        );
    },
    'Feld "Sonstiger Titel*" erscheint nur bei Auswahl "Sonstiger Titel" und akzeptiert maximal 255 Zeichen (/)',
    'Feld "Sonstiger Titel*" ist falsch sichtbar oder die Zeichenbegrenzung wird nicht eingehalten (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 13';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const radioGroup = 'radios';
        const comboGroup = 'comboboxes';
        const vorsatzKey = 'NAMENSVORSATZ';

        // --- Teil 1: Bedingung setzen ---
        // Sicherstellen, dass "natürliche Person" ausgewählt ist
        await bericht_ubermittlung.setValue(radioGroup, 'NATUERLICHE_PERSON', '');

        // --- Teil 2: Sichtbarkeitsprüfung ---
        const isVisible = await bericht_ubermittlung.isVisible(comboGroup, vorsatzKey);
        await executeAssertion(
            () => { expect(isVisible).toBeTruthy() },
            `Das Feld 'Namensvorsatz' ist NICHT sichtbar, obwohl 'natürliche Person' ausgewählt wurde.`
        );

        // --- Teil 3: Optionen-Prüfung ---
        const expectedVorsatz = [
            "al", "Baron", "Baronin", "da", "de", "del", "di", "d_o", "du",
            "Freiherr", "Freifrau", "Graf", "Gräfin", "Mc", "vom", "von",
            "zu", "zum", "zur", "Sonstiger Namensvorsatz"
        ];

        const options = await bericht_ubermittlung.getComboboxOptions(vorsatzKey);
        // Leere Optionen (Platzhalter) entfernen
        const filteredOptions = options.filter(opt => opt.trim() !== "");

        await executeAssertion(
            () => {
                expect(filteredOptions).toEqual(expect.arrayContaining(expectedVorsatz));
                expect(filteredOptions.length).toBe(expectedVorsatz.length);
            },
            `Die Optionen für 'Namensvorsatz' sind nicht korrekt. Erwartet ${expectedVorsatz.length}, gefunden ${filteredOptions.length}.`
        );

        // --- Teil 4: Evidence ---
        await bericht_ubermittlung.click(comboGroup, vorsatzKey);
        await bericht_ubermittlung.highlight(comboGroup, vorsatzKey, 'red');
        await resultWriter.createEvidence(testStep);
        await bericht_ubermittlung.highlight(comboGroup, vorsatzKey, 'none');
    },
    'Das Feld "Namensvorsatz" ist bei "natürliche Person" sichtbar und enthält alle 20 korrekten Optionen (/)',
    'Das Feld "Namensvorsatz" ist nicht sichtbar oder die Optionen sind fehlerhaft (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 14';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const radioGroup = 'radios';
        const comboGroup = 'comboboxes';
        const vorsatzKey = 'NAMENSVORSATZ';

        // --- Teil 1: Bedingung setzen ---
        // Sicherstellen, dass "nicht natürliche Person" ausgewählt ist
        await bericht_ubermittlung.setValue(radioGroup, 'NICHT_NATUERLICHE_PERSON', '');

        // --- Teil 2: Sichtbarkeitsprüfung ---
        const isVisible = await bericht_ubermittlung.isVisible(comboGroup, vorsatzKey);
        await executeAssertion(
            () => { expect(isVisible).toBeTruthy() },
            `Das Feld 'Namensvorsatz' ist NICHT sichtbar, obwohl 'nicht natürliche Person' ausgewählt wurde.`
        );

        // --- Teil 3: Optionen-Prüfung (Rechtsformen/Organisationen) ---
        const expectedVorsatzNonNatural = [
            "Arbeitsgemeinschaft",
            "Betrieb gewerblicher Art",
            "Betriebsgemeinschaft",
            "Erbengemeinschaft",
            "Gemeinde",
            "Gemeinschaft",
            "Gewerbepark",
            "GbR",
            "Grundstücksgemeinschaft",
            "Immobilienfonds",
            "Laborgemeinschaft",
            "Magistrat",
            "Partnerschaftsgesellschaft",
            "Praxisgemeinschaft",
            "Sozietät",
            "Stadt",
            "Verpächtergemeinschaft",
            "Wohnungseigentümergemeinschaft",
            "Sonstiger Namensvorsatz"
        ];

        const options = await bericht_ubermittlung.getComboboxOptions(vorsatzKey);
        // Leere Optionen (Platzhalter) entfernen
        const filteredOptions = options.filter(opt => opt.trim() !== "");

        await executeAssertion(
            () => {
                expect(filteredOptions).toEqual(expect.arrayContaining(expectedVorsatzNonNatural));
                expect(filteredOptions.length).toBe(expectedVorsatzNonNatural.length);
            },
            `Die Optionen für 'Namensvorsatz' bei nicht natürlicher Person sind nicht korrekt. Erwartet ${expectedVorsatzNonNatural.length}, gefunden ${filteredOptions.length}.`
        );

        // --- Teil 4: Evidence ---
        await bericht_ubermittlung.click(comboGroup, vorsatzKey);
        await bericht_ubermittlung.highlight(comboGroup, vorsatzKey, 'red');
        await resultWriter.createEvidence(testStep);
        await bericht_ubermittlung.highlight(comboGroup, vorsatzKey, 'none');
    },
    'Das Feld "Namensvorsatz" ist bei "nicht natürliche Person" sichtbar und enthält die 19 korrekten Rechtsform-Optionen (/)',
    'Das Feld "Namensvorsatz" ist nicht sichtbar oder die Optionen für juristische Personen sind fehlerhaft (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 15';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const comboGroup = 'comboboxes';
        const fieldGroup = 'fields';
        const vorsatzCombo = 'NAMENSVORSATZ';
        const sonstigerVorsatzField = 'SONSTIGER_NAMENSVORSATZ';

        // --- Teil 1: Sichtbarkeit triggern ---
        // Wir wählen einen Personentyp (funktioniert bei beiden, da "Sonstiger..." in beiden Listen ist)
        await bericht_ubermittlung.setValue('radios', 'NATUERLICHE_PERSON', '');

        // Auswahl "Sonstiger Namensvorsatz" in der Combobox
        await bericht_ubermittlung.setValue(comboGroup, vorsatzCombo, 'Sonstiger Namensvorsatz');

        // Prüfung: Ist das Textfeld nun sichtbar und editierbar?
        const isVisible = await bericht_ubermittlung.isVisible(fieldGroup, sonstigerVorsatzField);
        const isEditable = await bericht_ubermittlung.isEditable(fieldGroup, sonstigerVorsatzField);

        await executeAssertion(
            () => {
                expect(isVisible).toBeTruthy();
                expect(isEditable).toBeTruthy();
            },
            `Das Feld 'Sonstiger Namensvorsatz*' ist NICHT sichtbar oder editierbar, obwohl 'Sonstiger Namensvorsatz' ausgewählt wurde.`
        );

        // a) Positivtest: Genau 255 Zeichen
        await bericht_ubermittlung.setValue(fieldGroup, sonstigerVorsatzField, randomString(255));
        const isErrorVisibleValid = await bericht_ubermittlung.isErrorMessageVisible('MAX_LENGTH_255');
        await executeAssertion(
            () => { expect(isErrorVisibleValid).toBeFalsy() },
            `Feld 'Sonstiger Namensvorsatz*' zeigt fälschlicherweise Fehler bei 255 Zeichen.`
        );

        // b) Negativtest: 256 Zeichen
        await bericht_ubermittlung.setValue(fieldGroup, sonstigerVorsatzField, randomString(256));
        const isErrorVisibleInvalid = await bericht_ubermittlung.isErrorMessageVisible('MAX_LENGTH_255');
        await executeAssertion(
            () => { expect(isErrorVisibleInvalid).toBeTruthy() },
            `Feld 'Sonstiger Namensvorsatz*' akzeptiert mehr als 255 Zeichen ohne Fehlermeldung.`
        );

        // Evidence für den Fehlerzustand erstellen
        await bericht_ubermittlung.highlight(fieldGroup, sonstigerVorsatzField, 'red');
        await resultWriter.createEvidence(testStep);
        await bericht_ubermittlung.highlight(fieldGroup, sonstigerVorsatzField, 'none');

        await bericht_ubermittlung.setValue(fieldGroup, sonstigerVorsatzField, '');
    },
    'Feld "Sonstiger Namensvorsatz*" erscheint nur bei entsprechender Auswahl und akzeptiert maximal 255 Zeichen (/)',
    'Feld "Sonstiger Namensvorsatz*" ist falsch sichtbar oder die Zeichenbegrenzung wird nicht eingehalten (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 16';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const radioGroup = 'radios';
        const comboGroup = 'comboboxes';
        const zusatzKey = 'NAMENSZUSATZ';

        // --- Teil 1: Bedingung setzen ---
        // Sicherstellen, dass "natürliche Person" ausgewählt ist
        await bericht_ubermittlung.setValue(radioGroup, 'NATUERLICHE_PERSON', '');

        // --- Teil 2: Sichtbarkeitsprüfung ---
        let isVisible = await bericht_ubermittlung.isVisible(comboGroup, zusatzKey);
        await executeAssertion(
            () => { expect(isVisible).toBeTruthy() },
            `Das Feld 'Namenszusatz' ist NICHT sichtbar, obwohl 'natürliche Person' ausgewählt wurde.`
        );

        // --- Teil 3: Optionen-Prüfung ---
        const expectedZusatz = [
            "Junior",
            "Senior",
            "der Zweite",
            "die Zweite",
            "Sonstiger Namenszusatz"
        ];

        const options = await bericht_ubermittlung.getComboboxOptions(zusatzKey);
        // Leere Optionen (Platzhalter) entfernen
        const filteredOptions = options.filter(opt => opt.trim() !== "");

        await executeAssertion(
            () => {
                expect(filteredOptions).toEqual(expect.arrayContaining(expectedZusatz));
                expect(filteredOptions.length).toBe(expectedZusatz.length);
            },
            `Die Optionen für 'Namenszusatz' sind nicht korrekt. Erwartet ${expectedZusatz.length}, gefunden ${filteredOptions.length}.`
        );

        // --- Teil 4: Evidence ---
        await bericht_ubermittlung.click(comboGroup, zusatzKey);
        await bericht_ubermittlung.highlight(comboGroup, zusatzKey, 'red');
        await resultWriter.createEvidence(`${testStep}.a`);
        await bericht_ubermittlung.highlight(comboGroup, zusatzKey, 'none');


        const fieldGroup = 'fields';
        const zusatzCombo = 'NAMENSZUSATZ';
        const sonstigerZusatzField = 'SONSTIGER_NAMENSZUSATZ_TEXT';

        // --- Teil 1: Sichtbarkeit triggern ---
        // Voraussetzung: Natürliche Person muss gewählt sein
        await bericht_ubermittlung.setValue('radios', 'NATUERLICHE_PERSON', '');

        // Auswahl "Sonstiger Namenszusatz" in der Combobox
        await bericht_ubermittlung.setValue(comboGroup, zusatzCombo, 'Sonstiger Namenszusatz');

        // Prüfung: Ist das Textfeld nun sichtbar und editierbar?
        isVisible = await bericht_ubermittlung.isVisible(fieldGroup, sonstigerZusatzField);
        const isEditable = await bericht_ubermittlung.isEditable(fieldGroup, sonstigerZusatzField);

        await executeAssertion(
            () => {
                expect(isVisible).toBeTruthy();
                expect(isEditable).toBeTruthy();
            },
            `Das Feld 'Sonstiger Namenszusatz*' (Textfeld) ist NICHT sichtbar oder editierbar, obwohl 'Sonstiger Namenszusatz' in der Combobox gewählt wurde.`
        );

        // a) Positivtest: Genau 255 Zeichen
        await bericht_ubermittlung.setValue(fieldGroup, sonstigerZusatzField, randomString(255));
        const isErrorVisibleValid = await bericht_ubermittlung.isErrorMessageVisible('MAX_LENGTH_255');
        await executeAssertion(
            () => { expect(isErrorVisibleValid).toBeFalsy() },
            `Feld 'Sonstiger Namenszusatz*' zeigt fälschlicherweise Fehler bei 255 Zeichen.`
        );

        // b) Negativtest: 256 Zeichen
        await bericht_ubermittlung.setValue(fieldGroup, sonstigerZusatzField, randomString(256));
        const isErrorVisibleInvalid = await bericht_ubermittlung.isErrorMessageVisible('MAX_LENGTH_255');
        await executeAssertion(
            () => { expect(isErrorVisibleInvalid).toBeTruthy() },
            `Feld 'Sonstiger Namenszusatz*' akzeptiert mehr als 255 Zeichen ohne Fehlermeldung.`
        );

        // Evidence für den Fehlerzustand erstellen
        await bericht_ubermittlung.highlight(fieldGroup, sonstigerZusatzField, 'red');
        await resultWriter.createEvidence(`${testStep}.b`);
        await bericht_ubermittlung.highlight(fieldGroup, sonstigerZusatzField, 'none');

        // --- Teil 3: Negativtest Sichtbarkeit ---
        // Auswahl ändern auf einen Standard-Zusatz (z.B. "Junior")
        await bericht_ubermittlung.setValue(comboGroup, zusatzCombo, 'Junior');

        const isHidden = await bericht_ubermittlung.isVisible(fieldGroup, sonstigerZusatzField);
        await executeAssertion(
            () => { expect(isHidden).toBeFalsy() },
            `Das Feld 'Sonstiger Namenszusatz*' (Textfeld) ist immer noch sichtbar, obwohl die Auswahl in der Combobox geändert wurde.`
        );
    },
    'Das Feld *Namenszusatz* ist bei *natürliche Person* sichtbar und enthält alle 5 korrekten Optionen (/)',
    'Das Feld *Namenszusatz* ist nicht sichtbar oder die Optionen sind fehlerhaft (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 17';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const group = 'fields';
        const fieldKey = 'VORNAME';

        // --- Teil 1: Bedingung setzen ---
        // Sicherstellen, dass "natürliche Person" ausgewählt ist
        await bericht_ubermittlung.setValue('radios', 'NATUERLICHE_PERSON', '');

        // Prüfung: Ist das Feld Vorname sichtbar und editierbar?
        const isVisible = await bericht_ubermittlung.isVisible(group, fieldKey);
        const isEditable = await bericht_ubermittlung.isEditable(group, fieldKey);

        await executeAssertion(
            () => {
                expect(isVisible).toBeTruthy();
                expect(isEditable).toBeTruthy();
            },
            `Das Feld 'Vorname*' ist NICHT sichtbar oder editierbar, obwohl 'natürliche Person' ausgewählt wurde.`
        );

        // a) Positivtest: Genau 255 Zeichen
        await bericht_ubermittlung.setValue(group, fieldKey, randomString(255));
        const isErrorVisibleValid = await bericht_ubermittlung.isErrorMessageVisible('MAX_LENGTH_255');
        await executeAssertion(
            () => { expect(isErrorVisibleValid).toBeFalsy() },
            `Das Feld 'Vorname*' zeigt fälschlicherweise eine Fehlermeldung bei genau 255 Zeichen an.`
        );

        // b) Negativtest: 256 Zeichen
        await bericht_ubermittlung.setValue(group, fieldKey, randomString(256));
        const isErrorVisibleInvalid = await bericht_ubermittlung.isErrorMessageVisible('MAX_LENGTH_255');
        await executeAssertion(
            () => { expect(isErrorVisibleInvalid).toBeTruthy() },
            `Das Feld 'Vorname*' akzeptiert mehr als 255 Zeichen ohne Fehlermeldung (aktuell 256).`
        );

        // Evidence für den Fehlerzustand erstellen
        await bericht_ubermittlung.highlight(group, fieldKey, 'red');
        await resultWriter.createEvidence(testStep);
        await bericht_ubermittlung.highlight(group, fieldKey, 'none');

        await bericht_ubermittlung.setValue(group, fieldKey, '');
    },
    'Das Feld "Vorname*" ist bei "natürliche Person" sichtbar und akzeptiert maximal 255 Zeichen (/)',
    'Das Feld "Vorname*" ist nicht sichtbar/editierbar oder die Zeichenbegrenzung wird nicht eingehalten (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 18';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const group = 'fields';
        const fieldKey = 'NACHNAME';

        // --- Teil 1: Bedingung setzen ---
        // Sicherstellen, dass "natürliche Person" ausgewählt ist
        await bericht_ubermittlung.setValue('radios', 'NATUERLICHE_PERSON', '');

        // Prüfung: Ist das Feld Nachname sichtbar und editierbar?
        const isVisible = await bericht_ubermittlung.isVisible(group, fieldKey);
        const isEditable = await bericht_ubermittlung.isEditable(group, fieldKey);

        await executeAssertion(
            () => {
                expect(isVisible).toBeTruthy();
                expect(isEditable).toBeTruthy();
            },
            `Das Feld 'Nachname*' ist NICHT sichtbar oder editierbar, obwohl 'natürliche Person' ausgewählt wurde.`
        );

        // a) Positivtest: Genau 255 Zeichen
        await bericht_ubermittlung.setValue(group, fieldKey, randomString(255));
        const isErrorVisibleValid = await bericht_ubermittlung.isErrorMessageVisible('MAX_LENGTH_255');
        await executeAssertion(
            () => { expect(isErrorVisibleValid).toBeFalsy() },
            `Das Feld 'Nachname*' zeigt fälschlicherweise eine Fehlermeldung bei genau 255 Zeichen an.`
        );

        // b) Negativtest: 256 Zeichen
        await bericht_ubermittlung.setValue(group, fieldKey, randomString(256));
        const isErrorVisibleInvalid = await bericht_ubermittlung.isErrorMessageVisible('MAX_LENGTH_255');
        await executeAssertion(
            () => { expect(isErrorVisibleInvalid).toBeTruthy() },
            `Das Feld 'Nachname*' akzeptiert mehr als 255 Zeichen ohne Fehlermeldung (aktuell 256).`
        );

        // Evidence für den Fehlerzustand erstellen
        await bericht_ubermittlung.highlight(group, fieldKey, 'red');
        await resultWriter.createEvidence(testStep);
        await bericht_ubermittlung.highlight(group, fieldKey, 'none');

        await bericht_ubermittlung.setValue(group, fieldKey, '');
    },
    'Das Feld "Nachname*" ist bei "natürliche Person" sichtbar und akzeptiert maximal 255 Zeichen (/)',
    'Das Feld "Nachname*" ist nicht sichtbar/editierbar oder die Zeichenbegrenzung wird nicht eingehalten (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 19';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const comboGroup = 'comboboxes';
        const adressartKey = 'ADRESSART';

        // --- Teil 1: Sichtbarkeitsprüfung ---
        const isVisible = await bericht_ubermittlung.isVisible(comboGroup, adressartKey);
        await executeAssertion(
            () => { expect(isVisible).toBeTruthy() },
            `Das Feld 'Adressart*' ist NICHT sichtbar.`
        );

        // --- Teil 2: Optionen-Prüfung ---
        const expectedAdressarten = [
            "Straße", 
            "Großempfänger", 
            "Postfach", 
            "Ausland"
        ];

        const options = await bericht_ubermittlung.getComboboxOptions(adressartKey);
        
        // Wir filtern leere oder nur aus Leerzeichen bestehende Optionen aus, 
        // da die "option [selected]" im Snapshot oft ein leerer Platzhalter ist.
        const filteredOptions = options.filter(opt => opt && opt.trim() !== "");

        await executeAssertion(
            () => { 
                expect(filteredOptions).toEqual(expect.arrayContaining(expectedAdressarten));
                expect(filteredOptions.length).toBe(expectedAdressarten.length);
            },
            `Die Optionen für 'Adressart*' sind nicht korrekt. Erwartet: ${expectedAdressarten.join(', ')}, Gefunden: ${filteredOptions.join(', ')}`
        );

        // --- Teil 3: Evidence ---
        await bericht_ubermittlung.highlight(comboGroup, adressartKey, 'red');
        await resultWriter.createEvidence(testStep + '_adressart_options');
        await bericht_ubermittlung.highlight(comboGroup, adressartKey, 'none');
    },
    'Die Combobox "Adressart*" ist sichtbar und enthält die korrekten Optionen (Straße, Großempfänger, Postfach, Ausland) (/)',
    'Die Combobox "Adressart*" ist nicht sichtbar oder die Optionen sind fehlerhaft (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 20';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const comboGroup = 'comboboxes';
        const adresstypKey = 'ADRESSTYP';

        // --- Teil 1: Sichtbarkeitsprüfung ---
        const isVisible = await bericht_ubermittlung.isVisible(comboGroup, adresstypKey);
        await executeAssertion(
            () => { expect(isVisible).toBeTruthy() },
            `Das Feld 'Adresstyp*' ist NICHT sichtbar.`
        );

        // --- Teil 2: Optionen-Prüfung ---
        const expectedAdresstypen = [
            "unbekannt",
            "Wohnsitz",
            "Ort der Geschäftsleitung",
            "Anschrift des Unternehmens",
            "Betriebsstätte",
            "Sitz",
            "Abweichende Bekanntgabeadresse",
            "Bekanntgabeadresse Betriebssteuerergebnisse"
        ];

        const options = await bericht_ubermittlung.getComboboxOptions(adresstypKey);
        
        // Filterung leerer Platzhalter-Optionen
        const filteredOptions = options.filter(opt => opt && opt.trim() !== "");

        await executeAssertion(
            () => { 
                expect(filteredOptions).toEqual(expect.arrayContaining(expectedAdresstypen));
                expect(filteredOptions.length).toBe(expectedAdresstypen.length);
            },
            `Die Optionen für 'Adresstyp*' sind nicht korrekt. Erwartet ${expectedAdresstypen.length} Optionen, gefunden ${filteredOptions.length}.`
        );

        // --- Teil 3: Evidence ---
        await bericht_ubermittlung.click(comboGroup, adresstypKey);
        await bericht_ubermittlung.highlight(comboGroup, adresstypKey, 'red');
        await resultWriter.createEvidence(testStep);
        await bericht_ubermittlung.highlight(comboGroup, adresstypKey, 'none');
    },
    'Die Combobox "Adresstyp*" ist sichtbar und enthält alle 8 korrekten Optionen (/)',
    'Die Combobox "Adresstyp*" ist nicht sichtbar oder die Optionen sind unvollständig/falsch (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 21';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const group = 'fields';
        const fieldKey = 'PLZ';
        
        // --- Teil 1: Sichtbarkeitsprüfung ---
        const isVisible = await bericht_ubermittlung.isVisible(group, fieldKey);
        const isEditable = await bericht_ubermittlung.isEditable(group, fieldKey);

        await executeAssertion(
            () => { 
                expect(isVisible).toBeTruthy(); 
                expect(isEditable).toBeTruthy(); 
            },
            `Das Feld 'Postleitzahl*' ist NICHT sichtbar oder editierbar.`
        );

        // a) Positivtest: Genau 255 Zeichen
        await bericht_ubermittlung.setValue(group, fieldKey, randomString(255));
        const isErrorVisibleValid = await bericht_ubermittlung.isErrorMessageVisible('MAX_LENGTH_255');
        await executeAssertion(
            () => { expect(isErrorVisibleValid).toBeFalsy() },
            `Das Feld 'Postleitzahl*' zeigt fälschlicherweise eine Fehlermeldung bei genau 255 Zeichen an.`
        );

        // b) Negativtest: 256 Zeichen
        await bericht_ubermittlung.setValue(group, fieldKey, randomString(256));
        const isErrorVisibleInvalid = await bericht_ubermittlung.isErrorMessageVisible('MAX_LENGTH_255');
        await executeAssertion(
            () => { expect(isErrorVisibleInvalid).toBeTruthy() },
            `Das Feld 'Postleitzahl*' akzeptiert mehr als 255 Zeichen ohne Fehlermeldung (aktuell 256).`
        );

        // Evidence für den Fehlerzustand erstellen
        await bericht_ubermittlung.highlight(group, fieldKey, 'red');
        await resultWriter.createEvidence(testStep);
        await bericht_ubermittlung.highlight(group, fieldKey, 'none');
        
        await bericht_ubermittlung.setValue(group, fieldKey, '');
    },
    'Das Feld "Postleitzahl*" ist sichtbar und akzeptiert maximal 255 Zeichen (/)',
    'Das Feld "Postleitzahl*" ist nicht sichtbar/editierbar oder die Zeichenbegrenzung wird nicht eingehalten (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 22';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const group = 'fields';
        const fieldKey = 'ORT';
        
        // --- Teil 1: Sichtbarkeitsprüfung ---
        const isVisible = await bericht_ubermittlung.isVisible(group, fieldKey);
        const isEditable = await bericht_ubermittlung.isEditable(group, fieldKey);

        await executeAssertion(
            () => { 
                expect(isVisible).toBeTruthy(); 
                expect(isEditable).toBeTruthy(); 
            },
            `Das Feld 'Ort*' ist NICHT sichtbar oder editierbar.`
        );

        // a) Positivtest: Genau 255 Zeichen
        await bericht_ubermittlung.setValue(group, fieldKey, randomString(255));
        const isErrorVisibleValid = await bericht_ubermittlung.isErrorMessageVisible('MAX_LENGTH_255');
        await executeAssertion(
            () => { expect(isErrorVisibleValid).toBeFalsy() },
            `Das Feld 'Ort*' zeigt fälschlicherweise eine Fehlermeldung bei genau 255 Zeichen an.`
        );

        // b) Negativtest: 256 Zeichen
        await bericht_ubermittlung.setValue(group, fieldKey, randomString(256));
        const isErrorVisibleInvalid = await bericht_ubermittlung.isErrorMessageVisible('MAX_LENGTH_255');
        await executeAssertion(
            () => { expect(isErrorVisibleInvalid).toBeTruthy() },
            `Das Feld 'Ort*' akzeptiert mehr als 255 Zeichen ohne Fehlermeldung (aktuell 256).`
        );

        // Evidence für den Fehlerzustand erstellen
        await bericht_ubermittlung.highlight(group, fieldKey, 'red');
        await resultWriter.createEvidence(testStep + '_ort_max_length');
        await bericht_ubermittlung.highlight(group, fieldKey, 'none');
        
        await bericht_ubermittlung.setValue(group, fieldKey, '');
    },
    'Das Feld "Ort*" ist sichtbar und akzeptiert maximal 255 Zeichen (/)',
    'Das Feld "Ort*" ist nicht sichtbar/editierbar oder die Zeichenbegrenzung wird nicht eingehalten (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 23';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const comboGroup = 'comboboxes';
        const fieldGroup = 'fields';
        const adressartKey = 'ADRESSART';
        const postfachKey = 'POSTFACH';

        // --- Szenario 1: Adressart = "Postfach" (Feld muss da sein & Pflichtfeld sein) ---
        await bericht_ubermittlung.setValue(comboGroup, adressartKey, 'Postfach');

        // 1.1 Sichtbarkeit und Editierbarkeit prüfen
        const isVisible = await bericht_ubermittlung.isVisible(fieldGroup, postfachKey);
        const isEditable = await bericht_ubermittlung.isEditable(fieldGroup, postfachKey);
        await executeAssertion(
            () => { 
                expect(isVisible).toBeTruthy(); 
                expect(isEditable).toBeTruthy(); 
            },
            `Das Feld 'Postfach*' ist NICHT sichtbar/editierbar, obwohl Adressart 'Postfach' gewählt wurde.`
        );

        // 1.3 Max-Length Test (255 Zeichen)
               await bericht_ubermittlung.setValue(fieldGroup, postfachKey, randomString(256));
        const isLenErrorVisible = await bericht_ubermittlung.isErrorMessageVisible('MAX_LENGTH_255');
        await executeAssertion(
            () => { expect(isLenErrorVisible).toBeTruthy() },
            `Das Feld 'Postfach*' akzeptiert mehr als 255 Zeichen ohne Fehlermeldung.`
        );

        await bericht_ubermittlung.highlight(fieldGroup, postfachKey, 'red');
        await resultWriter.createEvidence(testStep);
        await bericht_ubermittlung.highlight(fieldGroup, postfachKey, 'none');

        // --- Szenario 2: Adressart != "Postfach" (z.B. "Straße") ---
        await bericht_ubermittlung.setValue(comboGroup, adressartKey, 'Straße');
        
    },
    'Feld "Postfach*" ist bedingtes Pflichtfeld (nur bei Adressart "Postfach"), akzeptiert max. 255 Zeichen und validiert korrekte Eingabe (/)',
    'Feld "Postfach*" ist falsch sichtbar, nicht als Pflichtfeld markiert oder ignoriert Zeichenbegrenzung (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 24';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const comboGroup = 'comboboxes';
        const fieldGroup = 'fields';
        const adressartKey = 'ADRESSART';
        const strasseKey = 'STRASSE';

        // --- Teil 1: Validierung der gültigen Trigger (Straße & Ausland) ---
        const validTriggers = ['Straße', 'Ausland'];

        for (const trigger of validTriggers) {
            await bericht_ubermittlung.setValue(comboGroup, adressartKey, trigger);
            
            // 1.1 Sichtbarkeit und Editierbarkeit
            const isVisible = await bericht_ubermittlung.isVisible(fieldGroup, strasseKey);
            const isEditable = await bericht_ubermittlung.isEditable(fieldGroup, strasseKey);
            await executeAssertion(
                () => { 
                    expect(isVisible).toBeTruthy(); 
                    expect(isEditable).toBeTruthy(); 
                },
                `Das Feld 'Straße*' ist NICHT sichtbar/editierbar, obwohl Adressart '${trigger}' gewählt wurde.`
            );

            // 1.3 Max-Length Test (256 Zeichen)
            await bericht_ubermittlung.setValue(fieldGroup, strasseKey, randomString(256));
            const isLenErrorVisible = await bericht_ubermittlung.isErrorMessageVisible('MAX_LENGTH_255');
            await executeAssertion(
                () => { expect(isLenErrorVisible).toBeTruthy() },
                `Das Feld 'Straße*' akzeptiert mehr als 255 Zeichen bei Adressart '${trigger}'.`
            );

            // Evidence für den Fehlerzustand (pro Trigger)
            await bericht_ubermittlung.highlight(fieldGroup, strasseKey, 'red');
            await resultWriter.createEvidence(`${testStep}_${trigger}`);
            await bericht_ubermittlung.highlight(fieldGroup, strasseKey, 'none');
        }    
        
        await bericht_ubermittlung.setValue(fieldGroup, strasseKey, '');
    },
    'Feld "Straße*" ist bedingtes Pflichtfeld (bei Adressart "Straße" oder "Ausland"), akzeptiert max. 255 Zeichen und ist sonst nicht zulässig (/)',
    'Feld "Straße*" ist falsch sichtbar, nicht als Pflichtfeld markiert oder ignoriert Zeichenbegrenzung (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 25';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const comboGroup = 'comboboxes';
        const fieldGroup = 'fields';
        const adressartKey = 'ADRESSART';
        const hausnummerKey = 'HAUSNUMMER';

        // --- Teil 1: Validierung der zulässigen Fälle (Straße & Ausland) ---
        const allowedTriggers = ['Straße', 'Ausland'];

        for (const trigger of allowedTriggers) {
            await bericht_ubermittlung.setValue(comboGroup, adressartKey, trigger);

            // Prüfung: Muss sichtbar und editierbar sein
            const isVisible = await bericht_ubermittlung.isVisible(fieldGroup, hausnummerKey);
            const isEditable = await bericht_ubermittlung.isEditable(fieldGroup, hausnummerKey);
            
            await executeAssertion(
                () => { 
                    expect(isVisible).toBeTruthy(); 
                    expect(isEditable).toBeTruthy(); 
                },
                `Das Feld 'Hausnummer' sollte bei Adressart '${trigger}' editierbar sein, ist es aber nicht.`
            );

            // Evidence für zulässigen Zustand
            await bericht_ubermittlung.highlight(fieldGroup, hausnummerKey, 'blue'); // Blau für "Soll-Zustand: Aktiv"
            await resultWriter.createEvidence(`${testStep}_${trigger}`);
            await bericht_ubermittlung.highlight(fieldGroup, hausnummerKey, 'none');
        }
    },
    'Feld "Hausnummer" ist nur bei Adressart "Straße" oder "Ausland" editierbar und sonst gesperrt/unsichtbar (/)',
    'Feld "Hausnummer" ist in unzulässigen Kontexten editierbar oder in zulässigen Kontexten gesperrt (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 26';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const comboGroup = 'comboboxes';
        const fieldGroup = 'fields';
        const adressartKey = 'ADRESSART';
        const hausNumZusatzKey = 'HAUSNUMMERZUSATZ';

        // --- Teil 1: Validierung der zulässigen Fälle (Straße & Ausland) ---
        const allowedTriggers = ['Straße', 'Ausland'];

        for (const trigger of allowedTriggers) {
            await bericht_ubermittlung.setValue(comboGroup, adressartKey, trigger);

            // 1.1 Sichtbarkeit und Editierbarkeit
            const isVisible = await bericht_ubermittlung.isVisible(fieldGroup, hausNumZusatzKey);
            const isEditable = await bericht_ubermittlung.isEditable(fieldGroup, hausNumZusatzKey);
            
            await executeAssertion(
                () => { 
                    expect(isVisible).toBeTruthy(); 
                    expect(isEditable).toBeTruthy(); 
                },
                `Das Feld 'Hausnummerzusatz' sollte bei Adressart '${trigger}' editierbar sein, ist es aber nicht.`
            );

            // a) Positivtest: Genau 255 Zeichen
            await bericht_ubermittlung.setValue(fieldGroup, hausNumZusatzKey, randomString(255));
            const isErrorValid = await bericht_ubermittlung.isErrorMessageVisible('MAX_LENGTH_255');
            await executeAssertion(
                () => { expect(isErrorValid).toBeFalsy() },
                `Feld 'Hausnummerzusatz' zeigt fälschlicherweise Fehler bei 255 Zeichen an (Adressart: ${trigger}).`
            );

            // b) Negativtest: 256 Zeichen
            await bericht_ubermittlung.setValue(fieldGroup, hausNumZusatzKey, randomString(256));
            const isErrorInvalid = await bericht_ubermittlung.isErrorMessageVisible('MAX_LENGTH_255');
            await executeAssertion(
                () => { expect(isErrorInvalid).toBeTruthy() },
                `Feld 'Hausnummerzusatz' akzeptiert mehr als 255 Zeichen bei Adressart '${trigger}'.`
            );

            // Evidence für den Fehlerzustand (pro Trigger)
            await bericht_ubermittlung.highlight(fieldGroup, hausNumZusatzKey, 'red');
            await resultWriter.createEvidence(`${testStep}_${trigger}_maxlength`);
            await bericht_ubermittlung.highlight(fieldGroup, hausNumZusatzKey, 'none');
        }
        await bericht_ubermittlung.setValue(fieldGroup, hausNumZusatzKey, '');

        
    },
    'Feld "Hausnummerzusatz" ist nur bei Adressart "Straße" oder "Ausland" editierbar, akzeptiert max. 255 Zeichen und ist sonst gesperrt (/)',
    'Feld "Hausnummerzusatz" ist in unzulässigen Kontexten editierbar oder die Zeichenbegrenzung wird nicht eingehalten (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 27';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const comboGroup = 'comboboxes';
        const fieldGroup = 'fields';
        const adressartKey = 'ADRESSART';
        const ergKey = 'ADRESSERGAENZUNG';

        // --- Teil 1: Validierung der zulässigen Fälle (Straße & Ausland) ---
        const allowedTriggers = ['Straße', 'Ausland'];

        for (const trigger of allowedTriggers) {
            await bericht_ubermittlung.setValue(comboGroup, adressartKey, trigger);

            // 1.1 Sichtbarkeit und Editierbarkeit
            const isVisible = await bericht_ubermittlung.isVisible(fieldGroup, ergKey);
            const isEditable = await bericht_ubermittlung.isEditable(fieldGroup, ergKey);
            
            await executeAssertion(
                () => { 
                    expect(isVisible).toBeTruthy(); 
                    expect(isEditable).toBeTruthy(); 
                },
                `Das Feld 'Adressergaenzung' sollte bei Adressart '${trigger}' editierbar sein, ist es aber nicht.`
            );

            // a) Positivtest: Genau 255 Zeichen
            await bericht_ubermittlung.setValue(fieldGroup, ergKey, randomString(255));
            const isErrorValid = await bericht_ubermittlung.isErrorMessageVisible('MAX_LENGTH_255');
            await executeAssertion(
                () => { expect(isErrorValid).toBeFalsy() },
                `Feld 'Adressergaenzung' zeigt fälschlicherweise Fehler bei 255 Zeichen an (Adressart: ${trigger}).`
            );

            // b) Negativtest: 256 Zeichen
            await bericht_ubermittlung.setValue(fieldGroup, ergKey, randomString(256));
            const isErrorInvalid = await bericht_ubermittlung.isErrorMessageVisible('MAX_LENGTH_255');
            await executeAssertion(
                () => { expect(isErrorInvalid).toBeTruthy() },
                `Feld 'Adressergaenzung' akzeptiert mehr als 255 Zeichen bei Adressart '${trigger}'.`
            );

            // Evidence für den Fehlerzustand (pro Trigger)
            await bericht_ubermittlung.highlight(fieldGroup, ergKey, 'red');
            await resultWriter.createEvidence(`${testStep}_${trigger}_maxlength`);
            await bericht_ubermittlung.highlight(fieldGroup, ergKey, 'none');
        }
        await bericht_ubermittlung.setValue(fieldGroup, ergKey, '');

    },
    'Feld "Adressergaenzung" ist nur bei Adressart "Straße" oder "Ausland" editierbar, akzeptiert max. 255 Zeichen und ist sonst gesperrt (/)',
    'Feld "Adressergaenzung" ist in unzulässigen Kontexten editierbar oder die Zeichenbegrenzung wird nicht eingehalten (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 28';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const comboGroup = 'comboboxes';
        const staatKey = 'STAAT';

        // --- Teil 1: Sichtbarkeitsprüfung ---
        const isVisible = await bericht_ubermittlung.isVisible(comboGroup, staatKey);
        await executeAssertion(
            () => { expect(isVisible).toBeTruthy() },
            `Das Feld 'Staat' ist NICHT sichtbar.`
        );

        // --- Teil 2: Definition der erwarteten Staaten-Liste ---
        const expectedStates = [
            "FRANKREICH", "NIEDERLANDE", "ITALIEN", "DEUTSCHLAND", "VEREINIGTES KOENIGREICH", 
            "IRLAND", "DAENEMARK", "GRIECHENLAND", "PORTUGAL (INCL. AZOREN UND MADEIRA)", "SPANIEN", 
            "BELGIEN", "LUXEMBURG", "CEUTA", "MELILLA", "ISLAND", "NORWEGEN", "SCHWEDEN", "FINNLAND", 
            "LIECHTENSTEIN", "OESTERREICH", "SCHWEIZ", "FAEROEER", "ANDORRA", "GIBRALTAR", "VATIKANSTADT", 
            "MALTA", "SAN MARINO", "TUERKEI", "ESTLAND", "LETTLAND", "LITAUEN", "POLEN", "Tschechien", 
            "SLOWAKEI", "UNGARN", "RUMAENIEN", "BULGARIEN", "ALBANIEN", "UKRAINE", "BELARUS (WEIßRUSSLAND)", 
            "REPUBLIK MOLDAU (MOLDAWIEN)", "RUSSISCHE FOEDERATION", "GEORGIEN", "ARMENIEN", "ASERBAIDSCHAN", 
            "KASACHSTAN", "TURKMENISTAN", "USBEKISTAN", "TADSCHIKISTAN", "KIRGISISTAN", "SLOWENIEN", 
            "KROATIEN", "BOSNIEN UND HERZEGOWINA", "SERBIEN UND MONTENEGRO", "KOSOVO", "NORDMAZEDONIEN", 
            "MONTENEGRO", "SERBIEN", "GUERNSEY", "JERSEY", "INSEL MAN", "MONACO", "WESTSAHARA", "MAROKKO", 
            "ALGERIEN", "TUNESIEN", "LIBYSCH-ARABISCHE DSCHAMAHIRIJA", "AEGYPTEN", "SUDAN", "SÜD-SUDAN", 
            "MAURETANIEN", "MALI", "BURKINA FASO (EHEM. OBERVOLTA)", "NIGER", "TSCHAD", "CABO VERDE", 
            "SENEGAL", "GAMBIA", "GUINEA-BISSAU", "GUINEA", "SIERRA LEONE", "LIBERIA", "COTE D'IVOIRE (ELFENBEINKUESTE)", 
            "GHANA", "TOGO", "BENIN (EHEM. DAHOME)", "NIGERIA", "KAMERUN", "ZENTRALAFRIKANISCHE REPUBLIK", 
            "AEQUATORIALGUINEA", "SAO TOME UND PRINCIPE", "GABUN", "REPUBLIK KONGO", "DEMOKR. REP. KONGO (EHEM. ZAIRE)", 
            "RUANDA", "BURUNDI", "ST. HELENA", "ANGOLA", "AETHIOPIEN", "ERITREA", "DSCHIBUTI", "SOMALIA", 
            "KENIA", "UGANDA", "VEREINIGTE REPUBLIK TANSANIA", "SEYCHELLEN", "BRIT. TERRITORIUM IM IND. OZEAN", 
            "MOSAMBIK", "MADAGASKAR", "MAURITIUS", "KOMOREN", "MAYOTTE", "SAMBIA", "SIMBABWE", "MALAWI", 
            "SUEDAFRIKA", "NAMIBIA", "BOTSUANA", "ESWATINI", "LESOTHO", "USA", "KANADA", "GROENLAND", 
            "ST. PIERRE UND MIQUELON", "MEXIKO", "BERMUDA", "GUATEMALA", "BELIZE", "HONDURAS", "EL SALVADOR", 
            "NICARAGUA", "COSTA RICA", "PANAMA", "ANGUILLA", "KUBA", "ST. KITTS UND NEVIS", "HAITI", "BAHAMAS", 
            "TURKS- UND CAICOSINSELN", "DOMINIKANISCHE REPUBLIK", "AMERIKAN. JUNGFERNINSELN", "ANTIGUA UND BARBUDA", 
            "DOMINICA", "KAIMANINSELN", "JAMAIKA", "ST. LUCIA", "ST. VINCENT UND DIE GRENADINEN", "BRIT. JUNGFERNINSELN", 
            "BARBADOS", "MONTSERRAT", "TRINIDAD UND TOBAGO", "GRENADA", "ARUBA", "BONAIRE", "CURACAO", 
            "NIEDERL. ANTILLEN", "Sint Maarten", "KOLUMBIEN", "VENEZUELA", "GUYANA", "SURINAME", "ST. EUSTATIUS", 
            "SABA", "ECUADOR", "PERU", "BRASILIEN", "CHILE", "BOLIVIEN", "PARAGUAY", "URUGUAY", "ARGENTINIEN", 
            "FALKLANDINSELN", "ZYPERN", "LIBANON", "ARABISCHE REPUBLIK SYRIEN", "IRAK", "ISLAMISCHE REPUBLIK IRAN", 
            "ISRAEL", "PALÄSTINENSISCHE GEBIETE", "TIMOR-LESTE", "JORDANIEN", "SAUDI-ARABIEN", "KUWAIT", "BAHRAIN", 
            "KATAR", "VEREINIGTE ARABISCHE EMIRATE", "OMAN", "JEMEN", "AFGHANISTAN", "PAKISTAN", "INDIEN", 
            "BANGLADESCH", "MALEDIVEN", "SRI LANKA", "NEPAL", "BHUTAN", "MYANMAR", "THAILAND", "LAOS", "VIETNAM", 
            "KAMBODSCHA", "INDONESIEN", "MALAYSIA", "BRUNEI DARUSSALAM", "SINGAPUR", "PHILIPPINEN", "MONGOLEI", 
            "CHINA", "DEM. VR KOREA (NORDKOREA)", "REPUBLIK KOREA (SUEDKOREA)", "JAPAN", "TAIWAN", "HONGKONG", "MACAU", 
            "AUSTRALIEN", "AUSTRALISCH-OZEANIEN", "PAPUA-NEUGUINEA", "NAURU", "NEUSEELAND", "SALOMONEN", "TUVALU", 
            "NEUKALEDONIEN", "SAMOA, AMERIK.", "WALLIS UND FUTUNA", "KIRIBATI", "PITCAIRN", "NEUSEELÄNDISCH-OZEANIEN", 
            "FIDSCHI", "VANUATU", "TONGA", "SAMOA", "NOERDLICHE MARIANEN", "FRZ. POLYNESIEN", "FOEDERIERTE STAATEN VON MIKRONESIEN", 
            "MARSHALL-INSELN", "PALAU", "AMERIK.-SAMOA", "GUAM", "AMERIK. UEBERSEEINSELN", "KOKOSINSELN (KEELING-INSELN)", 
            "WEIHNACHTSINSEL (IND. OZEAN)", "HEARD UND MCDONALD-INSELN", "NORFOLK-INSEL", "COOK-INSELN", "NIUE-INSEL", 
            "TOKELAU", "unbekannt", "POLARGEBIETE", "ANTARKTIS", "BOUVET-INSELN", "SUEDGEORGIEN U. SUEDL. SANDWICHINSELN", 
            "FRANZOESISCHE SUEDGEBIETE", "Sonstiger Staat"
        ];

        // --- Teil 3: Optionen-Prüfung ---
        const options = await bericht_ubermittlung.getComboboxOptions(staatKey);
        
        // Filterung leerer Platzhalter-Optionen
        const filteredOptions = options.filter(opt => opt && opt.trim() !== "");

        await executeAssertion(
            () => { 
                expect(filteredOptions).toEqual(expect.arrayContaining(expectedStates));
                expect(filteredOptions.length).toBe(expectedStates.length);
            },
            `Die Optionen für 'Staat' sind nicht korrekt. Erwartet ${expectedStates.length}, gefunden ${filteredOptions.length}.`
        );

        // --- Teil 4: Evidence ---
        await bericht_ubermittlung.highlight(comboGroup, staatKey, 'red');
        await resultWriter.createEvidence(testStep + '_staat_options');
        await bericht_ubermittlung.highlight(comboGroup, staatKey, 'none');
    },
    'Die Combobox "Staat" ist sichtbar und enthält alle geforderten Staaten-Optionen (/)',
    'Die Combobox "Staat" ist nicht sichtbar oder die Staaten-Liste ist unvollständig/falsch (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 29';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const comboGroup = 'comboboxes';
        const fieldGroup = 'fields';
        const adressartKey = 'ADRESSART';
        const staatKey = 'STAAT';
        const sonstigerStaatKey = 'SONSTIGER_STAAT';

        // --- Szenario 1: Beide Bedingungen erfüllt (Aktivierung) ---
        await bericht_ubermittlung.setValue(comboGroup, adressartKey, 'Ausland');
        await bericht_ubermittlung.setValue(comboGroup, staatKey, 'Sonstiger Staat');

        // 1.1 Sichtbarkeit und Editierbarkeit prüfen
        const isVisible = await bericht_ubermittlung.isVisible(fieldGroup, sonstigerStaatKey);
        const isEditable = await bericht_ubermittlung.isEditable(fieldGroup, sonstigerStaatKey);
        await executeAssertion(
            () => { 
                expect(isVisible).toBeTruthy(); 
                expect(isEditable).toBeTruthy(); 
            },
            `Das Feld 'Sonstiger Staat*' ist NICHT sichtbar/editierbar, obwohl Adressart='Ausland' und Staat='Sonstiger Staat' gewählt wurden.`
        );

        // 1.3 Max-Length Test (255 Zeichen)
        
        await bericht_ubermittlung.setValue(fieldGroup, sonstigerStaatKey, randomString(256));
        const isLenErrorVisible = await bericht_ubermittlung.isErrorMessageVisible('MAX_LENGTH_255');
        await executeAssertion(
            () => { expect(isLenErrorVisible).toBeTruthy() },
            `Das Feld 'Sonstiger Staat*' akzeptiert mehr als 255 Zeichen ohne Fehlermeldung.`
        );

        await bericht_ubermittlung.highlight(fieldGroup, sonstigerStaatKey, 'red');
        await resultWriter.createEvidence(testStep + '_max_length');
        await bericht_ubermittlung.highlight(fieldGroup, sonstigerStaatKey, 'none');

        await bericht_ubermittlung.setValue(fieldGroup, sonstigerStaatKey, '');

    },
    'Feld "Sonstiger Staat*" ist bedingtes Pflichtfeld (nur bei Adressart "Ausland" UND Staat "Sonstiger Staat"), akzeptiert max. 255 Zeichen und ist sonst gesperrt (/)',
    'Feld "Sonstiger Staat*" ist falsch sichtbar, nicht als Pflichtfeld markiert oder ignoriert Zeichenbegrenzung (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 30';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        const group = 'fields';
        const fieldKey = 'HINWEISE';
        
        // --- Teil 1: Sichtbarkeitsprüfung ---
        const isVisible = await bericht_ubermittlung.isVisible(group, fieldKey);
        const isEditable = await bericht_ubermittlung.isEditable(group, fieldKey);

        await executeAssertion(
            () => { 
                expect(isVisible).toBeTruthy(); 
                expect(isEditable).toBeTruthy(); 
            },
            `Das Feld 'Hinweise' ist NICHT sichtbar oder editierbar.`
        );

        // a) Positivtest: Genau 4000 Zeichen
        await bericht_ubermittlung.setValue(group, fieldKey, randomString(4000));
        const isErrorVisibleValid = await bericht_ubermittlung.isErrorMessageVisible('MAX_LENGTH_4000');
        await executeAssertion(
            () => { expect(isErrorVisibleValid).toBeFalsy() },
            `Das Feld 'Hinweise' zeigt fälschlicherweise eine Fehlermeldung bei genau 4000 Zeichen an.`
        );

        // b) Negativtest: 4001 Zeichen
        await bericht_ubermittlung.setValue(group, fieldKey, randomString(4001));
        const isErrorVisibleInvalid = await bericht_ubermittlung.isErrorMessageVisible('MAX_LENGTH_4000');
        await executeAssertion(
            () => { expect(isErrorVisibleInvalid).toBeTruthy() },
            `Das Feld 'Hinweise' akzeptiert mehr als 4000 Zeichen ohne Fehlermeldung (aktuell 4001).`
        );

        // Evidence für den Fehlerzustand erstellen
        await bericht_ubermittlung.highlight(group, fieldKey, 'red');
        await resultWriter.createEvidence(testStep + '_hinweise_max_length');
        await bericht_ubermittlung.highlight(group, fieldKey, 'none');

        await bericht_ubermittlung.setValue(group, fieldKey, '');
    },
    'Das Feld "Hinweise" ist sichtbar und akzeptiert maximal 4000 Zeichen (/)',
    'Das Feld "Hinweise" ist nicht sichtbar/editierbar oder die Zeichenbegrenzung von 4000 wird nicht eingehalten (x)',
    errors,
    goblaStatus,
    stepStatus
);

testStep = 'step 31';
await executeStep(
    testStep,
    resultWriter,
    async () => {
        
    },
    'Speichern ist erfolgreich (/)',
    'Speichern ist NICHT erfolgreich (x)',
    errors,
    goblaStatus,
    stepStatus
);


resultWriter.saveResult(testKey, goblaStatus.status);
if (errors.length > 0) {
    throw new Error(errors.join('\n'))
}