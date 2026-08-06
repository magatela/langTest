import type { Page } from "playwright"
import type { NavigationPage } from "../POM/NavigationPage.ts"
import type { ZeitraeumePage } from "../POM/ZeitraeumePage.ts"
import { promises as fs } from "fs";

declare const page: Page;
declare const navigation: NavigationPage;
declare const zeitraeume: ZeitraeumePage;

// DIESE ZEILE IST SEHR WICHTIG!! NICHT LÖSCHEN #NBELPH69

const listaTextbox = await page.locator('//div[@data-role="text-output-text"]').all();
const listaPn: string[] = [];
for (let item of listaTextbox) {
    const regEx = /\d{4} \d{2} 0 \d{4}/
    const text = await item.innerText()
    if (regEx.test(text)) {
        listaPn.push(text)
    }
}
console.log(listaPn)
const dic:any = {}
const separator = '#'+'N'+'B'+'E'+'L'+'P'+'H'+'6'+'9'; // es muss leider so geschrieben werden sonst wird der Trener gelöscht
let file = `
import type { Page } from "playwright"
import type { NavigationPage } from "../POM/NavigationPage.ts"
import type { ZeitraeumePage } from "../POM/ZeitraeumePage.ts"

declare const page: Page;
declare const navigation: NavigationPage;
declare const zeitraeume: ZeitraeumePage;

// DIESE ZEILE IST SEHR WICHTIG, NICHT LÖSCHEN! ${separator}
const pruefungen = {\n`
for(let item of listaPn){
    file += `'${item}': {
        PZ : ['2018', '2026'],
        SZ : ['2018', '2026'],
        EINKUNFTSART:'_13EStG'
    },\n`
}
file += `\n} as const;

for(let pruefung of Object.keys(pruefungen)){
    const pruefungsnummer = pruefungen[pruefung as keyof typeof pruefungen];
    console.log(pruefungsnummer.PZ, pruefungsnummer.SZ)
    await navigation.menu("PRUEFUNGSPLAN");
    await navigation.searchAndOpen(pruefung);
    await navigation.navigateTo("VORBEREITUNG", "ZEITRAEUME");
    await zeitraeume.setTimeFrame("SICHTUNGSZEITRAUM", pruefungsnummer.SZ[0], pruefungsnummer.SZ[1]);
    await zeitraeume.selectOption('EINKUNFTSART','_13EStG');
    await zeitraeume.setTimeFrame("PRUEFUNGSZEITRAUM", pruefungsnummer.PZ[0], pruefungsnummer.PZ[1]);
    await zeitraeume.clickButton('SPEICHERN');
    await page.pause();
}
`
await fs.writeFile('src/snippets/setSZandPZ.ts', file)


