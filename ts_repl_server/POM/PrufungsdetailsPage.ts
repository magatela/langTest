import type { Page, Locator } from "playwright"
declare const page: Page;
// DIESE ZEILE IST SEHR WICHTIG!! NICHT LÖSCHEN #NBELPH69

// Hilfsfunktion für das Highlighten (wie in deinem vorherigen Beispiel)
async function setBorder(element: any, style: 'red' | 'blue' | 'none') {
    let elementStyle: string = ''
    if (style != 'none') {
        elementStyle = `5px solid ${style}`;
    } else {
        elementStyle = 'none'
    }
    await element.evaluate((el: any, newStyle: string) => { el.style.border = newStyle }, elementStyle)
}

// ############ UI Mapping - Definition aller Elemente
const UIPruefungsDetails = {
    buttons: {
        SCHLIESSEN: 'Prüfung schließen',
        PRUEFUNGSDETAILS_TOGGLE: 'Prüfungsdetails',
        ZUORDNUNG_TOGGLE: 'Zuordnung',
        PRUEFUNGSKAUFTRAGE_TOGGLE: 'Prüfungsaufträge',
        PRUEFUNGSAUFRUFE_TOGGLE: 'Prüfungsaufrufe',
        ABBRECHEN: 'Abbrechen',
        SPEICHERN: 'Speichern',
    },
    textboxes: {
        STEUERNUMMER: 'Steuernummer',
        PRUEFUNG_NUMMER: 'Prüfungsnummer',
        ZEITAUFWAND: 'Zeitaufwand der Prüfung (in Tagen)',
        NAME: 'Name',
        VOR_ERSTES_PRUEFUNGJAHR: 'Voraussichtliches erstes Prüfungsjahr',
        PGPL: 'PGPL',
        STATISTISCHE_ZUORDNUNG: 'Statistische Zuordnung dieser Prüfung',
        MEHR_MINDERSTEUERN: 'Mehr-/Mindersteuern (in EUR)',
        BETRIEBSART: 'Betriebsart / Sonstige Fallart dieser Prüfung',
        PLANSETZUNGSGRUND: 'Plansetzungsgrund',
        ZUGEORDNETES_SACHGEBIET: 'Zugeordnetes Sachgebiet',
    },
    comboboxes: {
        PRUEFUNGSART: 'Prüfungsart',
        STATUS: 'Status',
    },
    checkboxes: {
        STEUERFAHNDUNG: 'Steuerfahndung',
        UMS_SONDERPRUEFUNG: 'Umsatzsteuer-Sonderprüfung',
        LST_AUSSENPRUEFUNG: 'Lohnsteuer-Außenprüfung',
        MITWIRKUNG_BZST: 'Mitwirkung BZSt',
        MITWIRKUNG_FKS: 'Mitwirkung FKS',
        MITWIRKUNG_ZOLL: 'Mitwirkung Zoll',
        VORGESETZTER: 'Vorgesetzter Dienstbehörde',
        DIENSTSTELLENLEITUNG: 'Dienststellenleitung',
        TEILNAHME_GEMEINDE: 'Teilnahme Gemeinde',
        ZEITNAHE_BP: 'Zeitnahe Betriebsprüfung',
    },
    headings: {
        MAIN: 'Prüfungsdetails', // level 1
        SECTION_DETAILS: 'Prüfungsdetails', // level 2
        SECTION_ZUORDNUNG: 'Zuordnung', // level 2
        SECTION_KOMBIPRUEFUNG: 'Kombi-Prüfung', // level 3
        SECTION_MITWIRKUNG: 'Mitwirkung', // level 3
        SECTION_BETEILIGUNG: 'Beteiligung', // level 3
        SECTION_GEMEINDEN: 'Gemeinden', // level 3
        SECTION_BP: 'Betriebsprüfung', // level 3
        SECTION_AKTIONEN: 'Aktionsbereich', // level 2
    },
    tables: {
        PRUEFENDE_PERSON: 'Zugeordnete prüfende Person',
        PRUEFUNGSKAUFTRAGE: 'Prüfungsaufträge',
        PRUEFUNGSAUFRUFE: 'Prüfungsaufrufe',
    }
} as const;

type UIElementKey = keyof typeof UIPruefungsDetails.buttons |
    keyof typeof UIPruefungsDetails.textboxes |
    keyof typeof UIPruefungsDetails.comboboxes |
    keyof typeof UIPruefungsDetails.checkboxes |
    keyof typeof UIPruefungsDetails.headings |
    keyof typeof UIPruefungsDetails.tables;

export class PruefungsDetailsPage {
    readonly page: Page;

    constructor(page: Page) {
        this.page = page;
    }

    // =========================================================================
    // INTERNE LOCATOR LOGIK (Verhindert Namenskonflikte durch Rollen-Trennung)
    // =========================================================================
    private getLocator(role: 'button' | 'textbox' | 'combobox' | 'checkbox' | 'heading' | 'table', name: string): Locator {
        switch (role) {
            case 'button': return this.page.getByRole('button', { name });
            case 'textbox': return this.page.getByRole('textbox', { name });
            case 'combobox': return this.page.getByRole('combobox', { name });
            case 'checkbox': return this.page.getByRole('checkbox', { name });
            case 'heading': return this.page.getByRole('heading', { name });
            case 'table': return this.page.getByRole('table', { name });
        }
    }

    // Helper, um den Namen aus dem Mapping-Objekt zu holen
    private getName(category: keyof typeof UIPruefungsDetails, key: string): string {
        const cat = UIPruefungsDetails[category] as any;
        return cat[key];
    }

    // =========================================================================
    // HAUPTFUNKTIONEN
    // =========================================================================

    /**
     * Wert eines Textfeldes lesen oder schreiben
     */
    async setValue(key: keyof typeof UIPruefungsDetails.textboxes, value: string) {
        const name = UIPruefungsDetails.textboxes[key];
        await this.getLocator('textbox', name).fill(value);
    }

    async getValue(key: keyof typeof UIPruefungsDetails.textboxes): Promise<string> {
        const name = UIPruefungsDetails.textboxes[key];
        return await this.getLocator('textbox', name).inputValue();
    }

    /**
     * Prüfen, ob ein Element editierbar ist (nicht disabled)
     */
    async isEditable(role: 'textbox' | 'combobox' | 'checkbox', key: any): Promise<boolean> {
        const name = this.getName(role === 'combobox' ? 'comboboxes' : role === 'textbox' ? 'textboxes' : 'checkboxes', key);
        const element = this.getLocator(role, name);
        return !(await element.isDisabled());
    }

    /**
     * Sichtbarkeit prüfen
     */
    async isVisible(role: 'button' | 'textbox' | 'combobox' | 'checkbox' | 'heading' | 'table', key: any): Promise<boolean> {
        const category = this.getCategoryByRole(role);
        const name = this.getName(category, key);
        return await this.getLocator(role, name).isVisible();
    }

    /**
     * Element highlighten
     */
    async highlight(role: 'button' | 'textbox' | 'combobox' | 'checkbox' | 'heading' | 'table', key: any, style: 'red' | 'blue' | 'none' = 'red') {
        const category = this.getCategoryByRole(role);
        const name = this.getName(category, key);
        await setBorder(this.getLocator(role, name), style);
    }

    /**
     * Click auf ein Element
     */
    async click(role: 'button' | 'combobox' | 'checkbox', key: any) {
        const category = this.getCategoryByRole(role);
        const name = this.getName(category, key);
        await this.getLocator(role, name).click();
    }

    /**
     * Verifizieren, dass ein Element NICHT existiert (ohne Fehler)
     */
    async verifyNotExist(role: 'button' | 'textbox' | 'combobox' | 'checkbox' | 'heading' | 'table', key: any): Promise<boolean> {
        const category = this.getCategoryByRole(role);
        const name = this.getName(category, key);
        const count = await this.getLocator(role, name).count();
        return count === 0;
    }

    /**
     * Alle Optionen einer Combobox lesen
     */
    async getComboBoxOptions(key: keyof typeof UIPruefungsDetails.comboboxes): Promise<string[]> {
        const name = UIPruefungsDetails.comboboxes[key];
        const combo = this.getLocator('combobox', name);
        // Wir suchen alle option-Elemente innerhalb oder assoziiert mit der combobox
        // Da ARIA Snapshots oft vereinfacht sind, wählen wir hier die Optionen im Unterbaum
        const options = combo.locator('option');
        return await options.allInnerTexts();
    }

    // =========================================================================
    // INTERNE HELPER
    // =========================================================================
    private getCategoryByRole(role: 'button' | 'textbox' | 'combobox' | 'checkbox' | 'heading' | 'table'): keyof typeof UIPruefungsDetails {
        const map: Record<'button' | 'textbox' | 'combobox' | 'checkbox' | 'heading' | 'table', keyof typeof UIPruefungsDetails> = {
            'button': 'buttons',
            'textbox': 'textboxes',
            'combobox': 'comboboxes',
            'checkbox': 'checkboxes',
            'heading': 'headings',
            'table': 'tables'
        };
        return map[role];
    }
}

