import type { Page, Locator } from "playwright"
declare const page: Page;
// DIESE ZEILE IST SEHR WICHTIG!! NICHT LÖSCHEN #NBELPH69

export class NavigationPage {
    /** Die Playwright‑Seite, auf der die Navigation ausgeführt wird */
    page: Page;

    /** Vorgabestile für das Hervorheben von Elementen */
    borderStyles = {
        red: (el: any) => { el.style.border = '5px solid red' },
        blue: (el: any) => { el.style.border = '5px solid blue' },
        none: (el: any) => { el.style.border = 'none' },
    }

    constructor(page: Page) {
        this.page = page;
    }

    // -----------------------------------------------------------------
    //   Konstanten für die Navigationsbezeichnungen (mehrstufig)
    // -----------------------------------------------------------------
    private fields1level = {
        FALLINFORMATIONEN: 'Fallinformationen',
        PRUEFUNGSDETAILS: 'Prüfungsdetails',
        KONTAKTINFORMATIONEN: 'Kontaktinformationen',
        VERLAUF: 'Verlauf',
        VORBEREITUNG: 'Vorbereitung',
        DURCHFUEHRUNG: 'Durchführung',
        ABWICKLUNG: 'Abwicklung',
        PRUEFUNGSINFORMATIONEN: 'Prüfungsinformationen',
        BEMERKUNGEN: 'Bemerkungen',
    } as const;

    private fields2level = {
        ZEITRAEUME: 'Zeiträume',
        FESTSETZUNGSDATEN: 'Festsetzungsdaten',
        GEWINNERMITTLUNG: 'Gewinnermittlung',
        STEUERABGLEICH_VOR_PRUEFUNG: 'Steuerabgleich vor Prüfung',
        ANORDNUNG: 'Anordnung',
        PRUEFUNGSFESTSTELLUNGEN: 'Prüfungsfeststellungen',
        STEUER_RUECKSTELLUNGSBERECHNUNG: 'Steuer-/Rückstellungsberechnung',
        MEHR_UND_WENIGERRECHNUNG: 'Mehr- und Wenigerrechnung',
        SCHLUSSBESPRECHUNG: 'Schlussbesprechung',
        KOERPERSCHAFTSTEUER: 'Körperschaftsteuer',
        GEWERBESTEUER: 'Gewerbesteuer',
        UMSATZSTEUER: 'Umsatzsteuer',
        ERGEBNISSE: 'Ergebnisse',
        BERICHTE: 'Berichte',
        AUSWERTUNG: 'Auswertung',
    } as const;

    private fields3level = {
        E_BILANZ_ANSICHT: 'E-Bilanz Ansicht',
        STEUERBILANZ: 'Steuerbilanz',
        E_GEWINN_UND_VERLUSTRECHNUNG: 'E-Gewinn- und Verlustrechnung',
        KAPITALKONTENENTWICKLUNG: 'Kapitalkontenentwicklung',
        BETRIEBSVERMOEGENSVERGLEICH: 'Betriebsvermögensvergleich',
        PRUEFUNGSBILANZ: 'Prüfungsbilanz',
        EUR:'EÜR'
    } as const;

    private fieldsNavigation = {
        PRUEFUNGSPLAN: 'Prüfungen',
        NACHRICHTEN: 'Nachrichten',
    } as const;

    // -----------------------------------------------------------------
    //   Hilfsmethoden
    // -----------------------------------------------------------------

    /** Liefert den Locator für die Seitenleiste, in der die Navigation liegt */
    private getSidebarContext() {
        return this.page.locator('//div[@data-role="application-frame-sidebar"]');
    }

    /**
     * Klickt ein Navigations‑Element (ListItem) an.
     *
     * @param element_name   Der sichtbare Text oder RegExp des zu klickenden Elements
     * @param container      Optionaler Locator, der das aktuelle Unter‑Container‑Element darstellt
     * @returns Das Locator‑Objekt des angeklickten ListItems
     */
    private async clickOnNavigationItem(
        element_name: string | RegExp,
        container: Locator | undefined = undefined
    ) {
        const listItem = (container || this.getSidebarContext())
            .getByRole('listitem')
            .filter({ hasText: element_name });

        // Prüfen, ob das Element ein Aufklapp‑Button besitzt und dieses ggf. klicken
        const expandButton = listItem.getByRole('button', { name: /Unterpunkte/ }).first();
        if (await expandButton.isVisible() && await expandButton.getAttribute('aria-label') === 'Unterpunkte aufklappen') {
            await expandButton.click();
        } else {
            await listItem.getByText(element_name).click();
        }
       
        return listItem;
    }

    /**
     * Erstellt eine Liste von Navigations‑Labels in der Reihenfolge,
     * in der sie angeklickt werden müssen.
     *
     * @param label1level  Oberste Ebene (Pflicht)
     * @param label2level  Zweite Ebene (optional)
     * @param label3level  Dritte Ebene (optional)
     * @returns Array von Strings, das die zu nutzenden Labels enthält
     */
    private generateNavigationList(
        label1level: keyof typeof this.fields1level,
        label2level?: keyof typeof this.fields2level,
        label3level?: keyof typeof this.fields3level
    ): string[] {
        const listOfLevels = [this.fields1level[label1level] as string];

        if (!label2level) {
            return listOfLevels;
        }
        listOfLevels.push(this.fields2level[label2level] as string);

        if (!label3level) {
            return listOfLevels;
        }
        listOfLevels.push(this.fields3level[label3level] as string);
        return listOfLevels;
    }

    // -----------------------------------------------------------------
    //   Öffentliche API
    // -----------------------------------------------------------------

    /**
     * Navigiert schrittweise durch den Navigationsbaum zu einem Ziel‑Element.
     *
     * @param label1level  Oberste Ebene (z. B. 'FALLINFORMATIONEN')
     * @param label2level  Zweite Ebene (optional)
     * @param label3level  Dritte Ebene (optional)
     */
    async navigateTo(
        label1level: keyof typeof this.fields1level,
        label2level?: keyof typeof this.fields2level,
        label3level?: keyof typeof this.fields3level
    ) {
        const listOfLevels = this.generateNavigationList(label1level, label2level, label3level);
        let currentElement: Locator | undefined = undefined;
        for (const label of listOfLevels) {
            currentElement = await this.clickOnNavigationItem(label, currentElement);
        }
    }

    /**
     * Öffnet einen Eintrag aus der Hauptnavigation (z. B. Prüfungen oder Nachrichten).
     *
     * @param label  Schlüssel aus `fieldsNavigation` (z. B. 'PRUEFUNGSPLAN')
     */
    async menu(label: keyof typeof this.fieldsNavigation) {
        const mainMenu: Locator = this.page.getByRole('navigation', { name: "Hauptnavigation" });
        const item = mainMenu.getByRole('link', { name: this.fieldsNavigation[label] });
        await item.click();
    }

    /**
     * Öffnet eine Prüfung anhand ihrer Nummer, sofern das Element sichtbar ist.
     *
     * @param number  Prüfungs‑ bzw. Steuer‑Nummer als String
     */
    private async open(number: string) {
        const element = this.page
            .getByRole('rowgroup', { name: 'Tabelleninhalt' })
            .getByRole('cell', { name: number });
        await element.click();
    }

    /**
     * Sucht in der Trefferliste nach einer Prüfungs‑ oder Steuer‑Nummer.
     *
     * @param auditNumber  Zu suchende Nummer
     */
    private async search(auditNumber: string) {
        const element: Locator = this.page.getByPlaceholder('Suche');
        await element.fill(auditNumber);
        await element.press('Enter');
    }

    /**
     * Kombiniert Suche und Öffnen einer Prüfung. Unterstützt nur
     * Prüfungs‑ oder Steuer‑Nummern im String‑Format.
     *
     * @param auditNumber  Prüfungs‑ bzw. Steuer‑Nummer
     */
    async searchAndOpen(auditNumber: string) {
        await this.search(auditNumber);
        await this.open(auditNumber);
    }
}