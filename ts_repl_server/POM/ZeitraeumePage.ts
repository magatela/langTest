import type {Page, Locator} from "playwright"
declare const page: Page;
// DIESE ZEILE IST SEHR WICHTIG!! NICHT LÖSCHEN #NBELPH69

const years = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027] as const;
type allowedYears = typeof years[number];

const fields = {
    SICHTUNGSZEITRAUM: 'Sichtungszeitraum',
    PRUEFUNGSZEITRAUM: 'Prüfungszeitraum'
} as const;

const buttons = {
    SICHTUNGSZEITRAUM_FESTLEGEN: 'Sichtungszeitraum festlegen',
    PRUEFUNGSZEITRAUM_FESTLEGEN: 'Prüfungszeitraum festlegen',
    WIRTSCHAFTSJAHRE_BERECHNEN:'Wirtschaftsjahre berechnen',
    SPEICHERN:'Speichern'
} as const;

const labelOptions = {
    EINKUNFTSART:'Einkunftsart',
    GEWINNERMITTLUNGSART:'Gewinnermittlungsart'
}

const labelFieldsFinancialyears = {
    VON_BIS:'Von - Bis',
    RECHTSFORMSCHLUESSEL:'Rechtsformschlüssel',
    EINKUNFTSART:'Einkunftsart',
    GEWINNERMITTLUNGSART:'Gewinnermittlungsart'
}

const options = {
    _13EStG: '§ 13 EStG',
    _15EStG: '§ 15 EStG',
    _18EStG: '§ 18 EStG',
    _2ABS1:  '§ 2 Abs. 1 Nr. 4-7 EStG',
    BILANZIERUNG:'Bilanzierung',
    GEWINNERMITTLUNG_4:'Gewinnermittlung § 4 Abs. 3 EStG',
    GEWINNERMITTLUNG_13A: 'Gewinnermittlung § 13a EStG'
}

const modalText = {
    WIRTSCHAFTSJAHRE_BERECHNEN : 'Wirtschaftsjahre berechnen'
} as const;

const errorMsgs = {

} as const;

export class ZeitraeumePage {
    page: Page;

    borderStyles = {
        red: (el: any) => { el.style.border = '5px solid red' },
        blue: (el: any) => { el.style.border = '5px solid blue' },
        none: (el: any) => { el.style.border = 'none' },
    }

    constructor(page:Page) {
        this.page = page;
    }

    private getTimeRangeLocator(label: keyof typeof fields, firstValue: boolean) {
        const yearLabel: string = firstValue ? 'Von' : 'Bis';
        return this.page.locator(`//div[@data-role="screen"]//div[contains(.,"${fields[label]}")]//label[contains(text(), "${yearLabel}")]/ancestor::div[@data-role="layout-grid-column"]//input`);
    }

    private getModalLocator(title: keyof typeof modalText, button? :{button: 'Ja' | 'Nein'}){
        let baseLocator = `//div[@data-role="contentbox-header" and contains(.,"${modalText[title]}")]/parent::div`;
        if (button?.button === 'Ja'){
            baseLocator = `${baseLocator}//button[normalize-space()="Ja"]`
        }
        if (button?.button === 'Nein'){
            baseLocator = `${baseLocator}//button[normalize-space()="Nein"]`
        }
        return this.page.locator(baseLocator);
    }

    async clickButton(buttonName: keyof typeof buttons){
        const element = this.page.getByRole('button', {name:buttons[buttonName]});
        await element.click();
    }

    async setTimeFrame(label: keyof typeof fields, from: string, to: string) {
        const von = true;
        const bis = false;
        const yearLocators = [
            this.getTimeRangeLocator(label, von),
            this.getTimeRangeLocator(label, bis)];
        const dates: string[] = [from, to];
        
        for(let index:number = 0; index < yearLocators.length; index++){
            await yearLocators[index]!.waitFor({state:'visible'});
            await yearLocators[index]!.fill(String(dates[index]))
            await this.page.keyboard.press('Tab');
        }
        
        if(label === 'SICHTUNGSZEITRAUM'){
            await this.clickButton('WIRTSCHAFTSJAHRE_BERECHNEN');
        }

        const isModalVisible = await this.isModalVisible('WIRTSCHAFTSJAHRE_BERECHNEN');
        console.log(`modal: [${isModalVisible}]`);
        if(isModalVisible){
            await this.handleModal('WIRTSCHAFTSJAHRE_BERECHNEN', {button:'Ja'})
        }
    }
            
    async selectOption(label: keyof typeof labelOptions, option: keyof typeof options){
        const element = this.page.locator(`//div[label[contains(text(),"${labelOptions[label]}")]]//select`).first();
        await element.selectOption(options[option])
    }

    async isModalVisible(title: keyof typeof modalText){
        let result:boolean;
        const element = this.getModalLocator(title);
        return await element.isVisible({timeout:5000}); 
    }

    async handleModal(title: keyof typeof modalText, button :{button: 'Ja' | 'Nein'}){
        const element = this.getModalLocator(title, button);
        await element.click();
    }

    async handleLegalFormCode(option: optionsLeLegalFormCode){
        const xpath = '//div[@data-role="textline-control" and .//label[contains(text(),"Rechtsformschlüssel")] and .//div[contains(text(),"Dieses Feld ist ein Pflichtfeld.")]]//input'
        const elements = await this.page.locator(xpath).all();
        for(let element of elements){
            await element.fill(option);
            await this.page.keyboard.press('Tab');
        }
    }
}

const optionen = [ 
    '000 gelöscht',
    '110 Hausgewerbetreibende und gleichgest. Personen',
    '120 Sonstige Einzelgewerbetreibende (außer Hausgewerbe und gleichgest.)',
    '130 Land- und Forstwirte',
    '140 Angehörige der freien Berufe',
    '150 Sonstige selbständig tätige Personen',
    '160 Personen mit Beteiligungen',
    '190 Sonstige natürliche Personen',
    '991 Ersatzwert',
    '250 Aktiengesellschaft und Co. KG',
    '260 Aktiengesellschaft und Co. OHG',
    '200 atypische stille Gesellschaft',
    '280 Europäische wirtschaft. Interessenvereinigung (EWIV)',
    '291 Gemeinschaft (z.B. Erben-, Grundstücks-)',
    '230 Ges. mit beschr. Haftung und Co.KG',
    '240 Ges. mit beschr. Haftung und Co.OHG',
    '270 Gesellschaft des bürgerlichen Rechts',
    '220 Kommanditgesellschaft',
    '210 Offene Handelsgesellschaft',
    '292 Partenreederei (§§489 ff HGB)',
    '293 Partnerschaft (§1 PartGG)',
    '290 sonstige Personengesellschaft',
    '295 Unterbeteiligung',
    '221 Investmentkommanditgesellschaft',
    '310 Aktiengesellschaft',
    '340 Bergrechtliche Gesellschaft',
    '360 Europäische Gesellschaft (SE)',
    '350 Gesellschaft mit beschränkter Haftung',
    '330 Kolonialgesellschaft',
    '320 Kommanditgesellschaft auf Aktien',
    '390 sonstige Kapitalgesellschaft',
    '370 Unternehmergesellschaft (haftungsbeschränkt)',
    '391 Investmentaktiengesellschaft',
    '460 eingetragene Genossenschaft',
    '450 Europäische Genossenschaft',
    '490 sonstige Genossenschaft i. S. des Genossenschaftsgesetzes',
    '510 Versicherungsverein auf Gegenseitigkeit',
    '511 Pensionsfondsverein auf Gegenseitigkeit',
    '520 eingetragener Verein (rechtsfähig)',
    '650 nichtrechtsfähige Stiftung des Privatrechts',
    '540 rechtsfähige Stiftung des Privatrechts',
    '590 sonstige juristische Person des privaten Rechts',
    '610 Vereine ohne Rechtspersönlichkeit, nicht rechtsfähige Anstalten, Stiftungen oder andere Zweckvermögen',
    '621 Verein ohne Rechtspersönlichkeit',
    '624 Sonstige Zweckvermögen',
    '623 Wirtschaftlicher Verein',
    '611 Sondervermögen',
    '831 berufsständische Körperschaft des öffentlichen Rechts',
    '837 europäischer Verbund für territoriale Zusammenarbeit',
    '810 Gebietskörperschaft',
    '838 nichtrechtsfähige Anstalt des öffentlichen Rechts',
    '850 nichtrechtsfähige Stiftung des öffentlichen Rechts',
    '820 öffentlich-rechtliche Religionsgesellschaft',
    '811 rechtsfähige Anstalt des öffentlichen Rechts',
    '840 rechtsfähige Stiftung des öffentlichen Rechts',
    '834 sonstige juristische Person des öffentlichen Rechts',
    '960 ausländische Körperschaft des öffentlichen Rechts',
    '950 ausländische Rechtsform, die einer Personenvereinigung oder Vermögensmasse i. S. des § 1 Abs. 1 Nr. 5 KStG entspricht',
    '940 ausländische Rechtsform, die einer sonstigen juristischen Person des privaten Rechts entspricht',
    '930 ausländische Rechtsform, die einer Genossenschaft entspricht',
    '900 sonstige ausländische Rechtsform',
    '910 ausländische Rechtsform, die einer Kapitalgesellschaft entspricht',
    '920 ausländische Rechtsform, die einer Personengesellschaft entspricht',
    '901 ausländische Rechtsform, die einem Zweckvermögen nach § 1 Abs. 1 Nr. 5 KStG entspricht',
    '990 sonstige nicht-nat. Rechtsform'
] as const;

type optionsLeLegalFormCode = typeof optionen[number]

