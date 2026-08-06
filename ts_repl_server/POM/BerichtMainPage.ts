import type { Page } from "playwright"
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

// ############ Bericht Main Page - Bericht-Tabelle
const UIMainPage = {
    assistenOptionen: {
        MITTEILUNG_ERGEBNISLOSE_BP: 'Mitteilung über ergebnislose Bp',
        MANUELLER_BERICHT: 'Manueller Bericht'
    },
    tabs: {
        EINGABEDIALOG: 'Eingabedialog',
        UEBERMITTLUNGSSCHREIBEN: 'Übermittlungsschreiben'
    },
    buttons: {
        BERICHTSASSISTENT_STARTEN: 'Berichtsassistent starten',
    },
    columnheaders: {
        ART: "Art",
        STATUS: "Status",
        ADRESSAT: "Adressat",
        EIGENE_ANLAGEN: "eigene Anlagen",
        VERSANDDATUM: "Versanddatum",
        STELLUNGNAHMEFRIST: "Stellungnahmefrist",
        ABLAUF_STELLUNGNAHMEFRIST: "Ablauf Stellungnahmefrist",
        EINGANG_STELLUNGNAHME: "Eingang Stellungnahme",
        STELLUNGNAHME_BEARBEITET: "Stellungnahme bearbeitet",
        AKTION: "Aktion",
    },
    // NEU: Inhalte für den Warn-Dialog
    warnDialog: {
        HEADING: 'Warnung: Angaben zur Schlussbesprechung jetzt nachholen?',
        TEXT: 'Es liegen noch keine Angaben zur Schlussbesprechung vor, die Funktion steht daher (noch) nicht zur Verfügung. Möchten Sie die Angaben zur Schlussbesprechung jetzt nachholen?',
        ACTION_AREA: 'Aktionsbereich',
        BTN_YES: 'Ja',
        BTN_NO: 'Nein'
    }
} as const;

export class PruefungsberichtMainPage {
    page: Page;

    constructor(page: Page) {
        this.page = page;
    }

    // Hilfsmethode für den Modal-Container
    private getModalContainer() {
        return this.page.locator('//div[@data-role="modal-overlay-content"]');
    }

    private getButtonLocator(buttonName: keyof typeof UIMainPage.buttons) {
        return this.page.getByRole('button', { name: UIMainPage.buttons[buttonName] })
    }

    async clickButton(buttonName: keyof typeof UIMainPage.buttons) {
        const element = this.getButtonLocator(buttonName);
        await element.click();
    }

    async highlightButton(buttonName: keyof typeof UIMainPage.buttons, style: 'red' | 'blue' | 'none') {
        const element = this.getButtonLocator(buttonName);
        await setBorder(element, style)
    }

    async istButtonVisible(buttonName: keyof typeof UIMainPage.buttons) {
        const element = this.getButtonLocator(buttonName);
        return await element.isVisible()
    }

    private getModalLocator(option?: keyof typeof UIMainPage.assistenOptionen) {
        const baseLocator = this.getModalContainer();
        if (option) {
            return baseLocator.getByText(UIMainPage.assistenOptionen[option]);
        }
        return baseLocator;
    }

    async highlightOption(style: 'red' | 'blue' | 'none', option?: keyof typeof UIMainPage.assistenOptionen) {
        const element = this.getModalLocator(option)
        await setBorder(element, style)
    }

    async selectFromassitant(label: keyof typeof UIMainPage.assistenOptionen) {
        const element = this.getModalLocator(label);
        await element.click();
    }

    async isButtonInAssitantVisible(label: keyof typeof UIMainPage.assistenOptionen){
        const element = this.getModalLocator(label);
        return element.isVisible();
    }

    // =========================================================================
    // NEUE METHODEN FÜR DEN WARN-DIALOG
    // =========================================================================

    /**
     * Prüft, ob der Warn-Dialog mit dem spezifischen Heading und Text sichtbar ist.
     */
    async isWarnDialogVisible() {
        const modal = this.getModalContainer();
        const heading = modal.getByRole('heading', { level: 1, name: UIMainPage.warnDialog.HEADING });
        const text = modal.getByText(UIMainPage.warnDialog.TEXT);
        
        return await heading.isVisible() && await text.isVisible();
    }

    /**
     * Klickt auf einen der Buttons im Warn-Dialog (Ja oder Nein).
     */
    async clickWarnDialogButton(buttonKey: 'BTN_YES' | 'BTN_NO') {
        const buttonText = UIMainPage.warnDialog[buttonKey];
        const button = this.getModalContainer().getByRole('button', { name: buttonText });
        await button.click();
    }

    /**
     * Optional: Verifiziert, ob der Aktionsbereich im Modal vorhanden ist.
     */
    async isActionAreaVisible() {
        return await this.getModalContainer()
            .getByRole('heading', { level: 2, name: UIMainPage.warnDialog.ACTION_AREA })
            .isVisible();
    }
}
