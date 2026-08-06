import type { Page, Locator } from "playwright"
declare const page: Page;
// DIESE ZEILE IST SEHR WICHTIG!! NICHT LÖSCHEN #NBELPH69

async function setBorder(element: any, style: 'red' | 'blue' | 'none') {
    let elementStyle: string = ''
    if (style != 'none') {
        elementStyle = `5px solid ${style}`;
    } else {
        elementStyle = 'none'
    }
    await element.evaluate((el: any, newStyle: string) => { el.style.border = newStyle }, elementStyle)
}

// ############ Übermittlungsschreiben
const UIUbermittlungsschreibenPage = {
    fields: {
        BEKANNTGABE_ERGAENZUNG: 'Bekanntgabe Ergänzung',
        BEKANNTGABEDATUM: 'Bekanntgabedatum',
        VORNAME: 'Vorname*',
        NACHNAME: 'Nachname*',
        STRASSE: 'Straße*',
        HAUSNUMMER: 'Hausnummer',
        HAUSNUMMERZUSATZ: 'Hausnummerzusatz',
        ADRESSERGAENZUNG: 'Adressergaenzung',
        PLZ: 'Postleitzahl*',
        ORT: 'Ort*',
        HINWEISE: 'Hinweise',
        SONSTIGER_TITEL: 'Sonstiger Titel*',
        SONSTIGER_NAMENSVORSATZ: 'Sonstiger Namensvorsatz*',
        SONSTIGER_NAMENSZUSATZ_TEXT: 'Sonstiger Namenszusatz*',
        POSTFACH: 'Postfach*',
        SONSTIGER_STAAT: 'Sonstiger Staat*'
    },
    comboboxes: {
        BEKANNTGABEART: 'Bekanntgabeart*',
        ADRESSAT: 'Adressat*',
        ANREDE: 'Anrede*',
        TITEL: 'Titel',
        NAMENSVORSATZ: 'Namensvorsatz',
        NAMENSZUSATZ: 'Namenszusatz',
        ADRESSART: 'Adressart*',
        ADRESSTYP: 'Adresstyp*',
        STAAT: 'Staat',
        VERTRETUNGSART: 'Vertretungsart*'
    },
    buttons: {
        UEBERNAHME_KONTAKT: 'Übernahme aus Kontaktinformationen',
        SPEICHERN: 'Speichern',
        SCHLIESSEN: 'schließen',
        LOESCHEN: 'Löschen',
        ABBRECHEN: 'Abbrechen',
        VORSCHAU: 'Vorschau'
    },
    links: {
        EINGABEDIALOG: 'Eingabedialog',
        UEBERMITTLUNGSSCHREIBEN: 'Übermittlungsschreiben'
    },
    radios: {
        NATUERLICHE_PERSON: 'natürliche Person',
        NICHT_NATUERLICHE_PERSON: 'nicht natürliche Person'
    },
    headings: {
        ART_BEKANNTGABE: 'Angaben zur Art der Bekanntgabe',
        ADRESSAT_BEKANNTGABE: 'Angaben zum Bekanntgabeadressaten',
        NAMENS_ERG: 'Namensergänzungen',
        NAME: 'Name',
        ADRESSANGABEN: 'Adressangaben',
        HINWEISE: 'Hinweise',
        AKTIONEN: 'Aktionsbereich'
    },
    errorMsgs: {
        // Hier können spezifische Fehlermeldungen ergänzt werden
        GENERAL_ERROR: 'Bitte füllen Sie alle Pflichtfelder aus.',
        INVALID_DATE_FORMAT: 'Es sind nur Daten im Format TT.MM.JJJJ erlaubt.',
        MAX_LENGTH_1500: 'Es sind nur Werte mit maximal 1500 Zeichen erlaubt.',
        MAX_LENGTH_255: 'Es sind nur Werte mit maximal 255 Zeichen erlaubt.',
        MAX_LENGTH_4000: 'Es sind nur Werte mit maximal 4000 Zeichen erlaubt.'
    }
} as const;

type ElementGroupBekanntgabePage = keyof typeof UIUbermittlungsschreibenPage;
type ElementKeyBekanntgabePage<G extends ElementGroupBekanntgabePage> = keyof typeof UIUbermittlungsschreibenPage[G];

export class UbermittlungsschreibenPage {
    private page: Page;

    constructor(page: Page) {
        this.page = page;
    }

    // --- Interner Locator-Generator ---
    private getLocator(group: ElementGroupBekanntgabePage, key: any): Locator {
        const name = (UIUbermittlungsschreibenPage as any)[group][key];

        switch (group) {
            case 'fields':
                return this.page.getByRole('textbox', { name, exact: true });
            case 'comboboxes':
                return this.page.getByRole('combobox', { name });
            case 'buttons':
                return this.page.getByRole('button', { name });
            case 'links':
                return this.page.getByRole('link', { name });
            case 'radios':
                return this.page.getByRole('radio', { name, exact: true });
            case 'headings':
                // Da "Adressangaben" mehrfach vorkommt, nehmen wir hier 
                // standardmäßig das erste Vorkommen. Falls spezifische 
                // Ebenen nötig sind, müsste getByRole('heading', { name, level: x }) genutzt werden.
                return this.page.getByRole('heading', { name }).first();
            default:
                return this.page.getByText(name);
        }
    }

    // --- Universelle Methoden ---

    /**
     * Klickt auf ein beliebiges Element
     */
    async click(group: ElementGroupBekanntgabePage, key: any) {
        const locator = this.getLocator(group, key);
        await locator.click();
    }

    /**
     * Schreibt einen Wert in ein Element oder wählt eine Option aus.
     */
    async setValue(group: ElementGroupBekanntgabePage, key: any, value: string) {
        const locator = this.getLocator(group, key);
        if (group === 'fields') {
            await locator.fill(value);
            await this.page.keyboard.press('Tab');
        } else if (group === 'comboboxes') {
            await locator.selectOption({ label: value });
        } else if (group === 'radios') {
            await locator.check();
        } else {
            throw new Error(`setValue ist für die Gruppe ${group} nicht definiert.`);
        }
    }

    /**
     * Liest den Wert eines Elements aus
     */
    async getValue(group: ElementGroupBekanntgabePage, key: any): Promise<string | boolean | null> {
        const locator = this.getLocator(group, key);
        if (group === 'fields' || group === 'comboboxes') {
            return await locator.inputValue();
        } else if (group === 'radios') {
            return await locator.isChecked();
        } else {
            return await locator.textContent();
        }
    }

    /**
     * Prüft, ob ein Element sichtbar ist
     */
    async isVisible(group: ElementGroupBekanntgabePage, key: any): Promise<boolean> {
        return await this.getLocator(group, key).isVisible();
    }

    /**
     * Prüft, ob ein Element editierbar ist
     */
    async isEditable(group: ElementGroupBekanntgabePage, key: any): Promise<boolean> {
        return await this.getLocator(group, key).isEditable();
    }

    /**
     * Highlightet ein Element mittels setBorder
     */
    async highlight(group: ElementGroupBekanntgabePage, key: any, color: 'red' | 'blue' | 'none' = 'none') {
        const locator = this.getLocator(group, key);
        await setBorder(locator, color);
    }

    // --- Spezialfunktionen ---

    /**
     * Liest alle verfügbaren Optionen einer Combobox aus
     */
    async getComboboxOptions(key: keyof typeof UIUbermittlungsschreibenPage.comboboxes): Promise<string[]> {
        const locator = this.getLocator('comboboxes', key);
        // Wir suchen alle option-Elemente innerhalb der Combobox
        // Falls es sich um ein Standard-HTML-Select handelt:
        return await locator.locator('option').allTextContents();
    }

    /**
     * Überprüfung von Fehlermeldungen
     */
    async isErrorMessageVisible(errorKey: keyof typeof UIUbermittlungsschreibenPage.errorMsgs): Promise<boolean> {
        const msg = UIUbermittlungsschreibenPage.errorMsgs[errorKey];
        return await this.page.getByText(msg, { exact: false }).isVisible();
    }
    /**
     * Liest alle verfügbaren Optionen einer Combobox aus, 
     * wenn mehrere Elemente mit demselben Namen existieren.
     * @param key Der Key aus der POM
     * @param index Der Index des Elements (0 = erstes, 1 = zweites, etc.)
     */
    async getComboboxOptionsByIndex(key: keyof typeof UIUbermittlungsschreibenPage.comboboxes, index: number = 0): Promise<string[]> {
        const name = UIUbermittlungsschreibenPage.comboboxes[key];
        // Wir nutzen .nth(index), um das spezifische Element aus der Liste der Treffer auszuwählen
        const locator = this.page.getByRole('combobox', { name }).nth(index);
        return await locator.locator('option').allTextContents();
    }
}