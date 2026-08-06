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

// ############ EINGABEDIALOG
const UISteuerpflichtigenPage = {
    fields: {
        STEUERNUMMER: 'Steuernummer',
        VORNAME: 'Vorname*',
        NACHNAME: 'Nachname*',
        FIRMENNAME: 'Firmenname*',
        STRASSE: 'Straße*',
        HAUSNUMMER: 'Hausnummer',
        HAUSNUMMERZUSATZ: 'Hausnummerzusatz',
        ADRESSERGAENZUNG: 'Adressergaenzung',
        PLZ: 'Postleitzahl*',
        ORT: 'Ort*',
        PRUEFUNGSNUMMER: 'Prüfungsnummer',
        PRUEFUNGSBEGINN: 'Prüfungsbeginn',
        PRUEFUNGSANORDNUNG: 'Prüfungsanordnung vom',
        SONSTIGES: 'Sonstiges',
        TABELLE_VON: 'Von',
        TABELLE_BIS: 'Bis',
        SONSTIGER_TITEL: 'Sonstiger Titel*',
        SONSTIGER_NAMENSVORSATZ: 'Sonstiger Namensvorsatz*',
        SONSTIGER_NAMENSZUSATZ_TEXT: 'Sonstiger Namenszusatz*',
        POSTFACH: 'Postfach*',
        SONSTIGER_STAAT: 'Sonstiger Staat*'
    },
    comboboxes: {
        ANREDE: 'Anrede*',
        TITEL: 'Titel',
        NAMENSVORSATZ: 'Namensvorsatz',
        NAMENSZUSATZ: 'Namenszusatz',
        ADRESSAT: 'Adressat*',
        ADRESSART: 'Adressart*',
        ADRESSTYP: 'Adresstyp*',
        STAAT: 'Staat',
        STEUERART: 'Steuerart'
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
        MAIN: 'Angaben zum Steuerpflichtigen',
        NAMENS_ERG: 'Namensergänzungen',
        NAME: 'Name',
        ADRESSE: 'Adressangaben',
        PRUEFUNG: 'Prüfung',
        ERLAEUTERUNG: 'Erläuterung',
        AKTIONEN: 'Aktionsbereich'
    },
    errorMsgs: {
        MAX_LENGTH_255: 'Es sind nur Werte mit maximal 255 Zeichen erlaubt.',
        MAX_LENGTH_500: 'Es sind nur Werte mit maximal 500 Zeichen erlaubt.'
    }
} as const;

type ElementGroupSteuerpflichtigen = keyof typeof UISteuerpflichtigenPage;
type ElementKeySteuerpflichtigen<G extends ElementGroupSteuerpflichtigen> = keyof typeof UISteuerpflichtigenPage[G];

export class SteuerpflichtigenPage {
    private page: Page;

    constructor(page: Page) {
        this.page = page;
    }

    // --- Interner Locator-Generator ---
    private getLocator(group: ElementGroupSteuerpflichtigen, key: any, firstOnly: boolean = false): Locator {
        const name = (UISteuerpflichtigenPage as any)[group][key];
        let locator: Locator;

        switch (group) {
            case 'fields':
                locator = this.page.getByRole('textbox', { name, exact: true});
                break;
            case 'comboboxes':
                locator = this.page.getByRole('combobox', { name, exact: true });
                break;
            case 'buttons':
                locator = this.page.getByRole('button', { name, exact: true });
                break;
            case 'links':
                locator = this.page.getByRole('link', { name, exact: true });
                break;
            case 'radios':
                locator = this.page.getByRole('radio', { name, exact: true });
                break;
            case 'headings':
                locator = this.page.getByRole('heading', { name, exact: true });
                break;
            default:
                locator = this.page.getByText(name);
        }

        return firstOnly ? locator.first() : locator;
    }

    // --- Universelle Methoden für alle Elemente ---

    async click(group: ElementGroupSteuerpflichtigen, key: any, firstOnly: boolean = false) {
        const locator = this.getLocator(group, key, firstOnly);
        await locator.click();
    }

    async setValue(group: ElementGroupSteuerpflichtigen, key: any, value: string, firstOnly: boolean = false) {
        const locator = this.getLocator(group, key, firstOnly);
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

    async getValue(group: ElementGroupSteuerpflichtigen, key: any, firstOnly: boolean = false): Promise<string | boolean | null> {
        const locator = this.getLocator(group, key, firstOnly);
        if (group === 'fields') {
            return await locator.inputValue();
        } else if (group === 'comboboxes') {
            return await locator.inputValue();
        } else if (group === 'radios') {
            return await locator.isChecked();
        } else {
            return await locator.textContent();
        }
    }

    async isVisible(group: ElementGroupSteuerpflichtigen, key: any, firstOnly: boolean = false): Promise<boolean> {
        return await this.getLocator(group, key, firstOnly).isVisible();
    }

    async isEditable(group: ElementGroupSteuerpflichtigen, key: any, firstOnly: boolean = false): Promise<boolean> {
        return await this.getLocator(group, key, firstOnly).isEditable();
    }

    async highlight(group: ElementGroupSteuerpflichtigen, key: any, color: 'red' | 'blue' | 'none' = 'none', firstOnly: boolean = false) {
        const locator = this.getLocator(group, key, firstOnly);
        await setBorder(locator, color);
    }

    /**
     * Prüft, ob ein beliebiger Text (z.B. ein Label oder Header) sichtbar ist.
     */
    async isTextVisible(text: string): Promise<boolean> {
        return await this.page.getByText(text, { exact: false }).isVisible();
    }

    // --- Spezialfunktionen ---

    async setTableDateRange(rowText: string, von: string, bis: string) {
        const row = this.page.getByRole('row', { name: rowText });
        await row.getByRole('textbox', { name: UISteuerpflichtigenPage.fields.TABELLE_VON }).fill(von);
        await row.getByRole('textbox', { name: UISteuerpflichtigenPage.fields.TABELLE_BIS }).fill(bis);
    }

    async isErrorMessageVisible(errorKey: keyof typeof UISteuerpflichtigenPage.errorMsgs): Promise<boolean> {
        return await this.page.getByText(UISteuerpflichtigenPage.errorMsgs[errorKey], { exact: false }).isVisible();
    }

    async getComboboxOptions(key: keyof typeof UISteuerpflichtigenPage.comboboxes): Promise<string[]> {
        const locator = this.getLocator('comboboxes', key);
        return await locator.locator('option').allTextContents();
    }
}