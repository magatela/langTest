import type { Page, Locator } from "playwright"

declare const page: Page;

// DIESE ZEILE IST SEHR WICHTIG!! NICHT LÖSCHEN #NBELPH69

/**
 * Hilfsfunktion für das Highlighten von Elementen.
 * Ermöglicht dem LLM/Agenten die visuelle Verifikation des gefundenen Elements.
 */
async function setBorder(element: any, style: 'red' | 'blue' | 'none') {
    let elementStyle: string = style === 'none' ? 'none' : `5px solid ${style}`;
    await element.evaluate((el: any, newStyle: string) => { el.style.border = newStyle }, elementStyle)
}

// ############ UI Mapping - Definition aller statischen Elemente
const UIGrundkennbuchstaben = {
    navigation: {
        LINK_GRUNDKENNBUCHSTABEN: 'Grundkennbuchstaben',
        LINK_WEITERE_GRUNDDATEN: 'Weitere Grunddaten',
    },
    headings: {
        MAIN_TITLE: 'Grundkennbuchstaben', // level 2
    },
    buttons: {
        TOGGLE_GRUNDKENNBUCHSTABEN: 'Grundkennbuchstaben',
    },
    tables: {
        GRUNDKENNBUCHSTABEN: 'Grundkennbuchstaben',
    },
    // Mapping der Spaltennamen auf ihren Index in der Tabelle
    columns: {
        KB_GRUPPE: 0,
        KB: 1,
        BEZEICHNUNG_KB: 2,
        GULTIG_AB: 3,
        GULTIG_BIS: 4,
        WERT: 5,
        AKTION: 6,
    }
} as const;

/**
 * Typdefinition für die Daten einer Tabellenzeile
 */
//export interface KBRowData {
interface KBRowData {
    kbGruppe: string;
    kb: string;
    bezeichnungKb: string;
    gueltigAb: string;
    gueltigBis: string;
    wert: string;
}

//export class GrundkennbuchstabenPage {
class GrundkennbuchstabenPage {
    readonly page: Page;

    constructor(page: Page) {
        this.page = page;
    }

    // =========================================================================
    // INTERNE LOCATOR LOGIK
    // =========================================================================

    private getLocator(role: 'link' | 'button' | 'heading' | 'table', name: string): Locator {
        return this.page.getByRole(role, { name });
    }

    /**
     * Findet eine spezifische Zeile basierend auf einem Textparameter.
     * @param identifier Der Text, nach dem in der Zeile gesucht wird.
     * @param index Falls mehrere Zeilen passen, wird das Element an diesem Index gewählt (default 0).
     */
    private async getRowLocator(identifier: string, index: number = 0): Promise<Locator> {
        const table = this.getLocator('table', UIGrundkennbuchstaben.tables.GRUNDKENNBUCHSTABEN);
        // Suche nach Zeilen, die den Identifier-Text enthalten
        
        const rows = table.getByRole('row', { name: identifier });
        // Validierung ob Zeile existiert
        const count = await rows.count();
        if (count === 0) {
            throw new Error(`Keine Zeile mit dem Text "${identifier}" in der Tabelle gefunden.`);
        }
        
        return rows.nth(index);
    }

    // =========================================================================
    // HAUPTFUNKTIONEN 
    // =========================================================================

    /**
     * Liest alle relevanten Werte einer Zeile aus und gibt sie als Objekt zurück.
     */
    async getRowData(identifier: string, index: number = 0): Promise<KBRowData> {
        const row = await this.getRowLocator(identifier, index);
        const cells = row.locator('cell');
        const texts = await cells.allInnerTexts();

        return {
            kbGruppe: texts[UIGrundkennbuchstaben.columns.KB_GRUPPE] || '',
            kb: texts[UIGrundkennbuchstaben.columns.KB] || '',
            bezeichnungKb: texts[UIGrundkennbuchstaben.columns.BEZEICHNUNG_KB] || '',
            gueltigAb: texts[UIGrundkennbuchstaben.columns.GULTIG_AB] || '',
            gueltigBis: texts[UIGrundkennbuchstaben.columns.GULTIG_BIS] || '',
            wert: texts[UIGrundkennbuchstaben.columns.WERT] || '',
        };
    }

    /**
     * Highlightet entweder eine ganze Zeile oder einen spezifischen Spaltenwert.
     * @param identifier Text zur Identifikation der Zeile.
     * @param column Optional: Der Spaltenschlüssel (z.B. 'KB'). Wenn weggelassen, wird die ganze Zeile markiert.
     * @param index Index bei Mehrfachfunden.
     */
    async highlightElement(identifier: string, column?: keyof typeof UIGrundkennbuchstaben.columns, index: number = 0, style: 'red' | 'blue' | 'none' = 'red') {
        const row = await this.getRowLocator(identifier, index);
        
        if (column) {
            const colIndex = UIGrundkennbuchstaben.columns[column];
            const cell = row.getByRole('cell').nth(colIndex);
            await setBorder(cell, style);
        } else {
            await setBorder(row, style);
        }
    }

    /**
     * Klickt auf einen Navigationslink oder Button.
     */
    async clickNavigation(key: keyof typeof UIGrundkennbuchstaben.navigation | keyof typeof UIGrundkennbuchstaben.buttons) {
        if (key in UIGrundkennbuchstaben.navigation) {
            const name = UIGrundkennbuchstaben.navigation[key];
            await this.getLocator('link', name).click();
        } else if (key in UIGrundkennbuchstaben.buttons) {
            const name = UIGrundkennbuchstaben.buttons[key];
            await this.getLocator('button', name).click();
        }
    }

    /**
     * Überprüft, ob ein bestimmter Wert in der Tabelle existiert.
     */
    async verifyValueExists(value: string): Promise<boolean> {
        const table = this.getLocator('table', UIGrundkennbuchstaben.tables.GRUNDKENNBUCHSTABEN);
        return await table.getByText(value).isVisible();
    }
}

const gkb = new GrundkennbuchstabenPage(page);
await gkb.highlightElement('LSt-Arbeitgeber', 'GULTIG_AB', 2, 'red');