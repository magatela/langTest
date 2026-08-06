
import type { Page } from "playwright"
import type { NavigationPage } from "../POM/NavigationPage.ts"
import type { ZeitraeumePage } from "../POM/ZeitraeumePage.ts"

declare const page: Page;
declare const navigation: NavigationPage;
declare const zeitraeume: ZeitraeumePage;

// DIESE ZEILE IST SEHR WICHTIG, NICHT LÖSCHEN! #NBELPH69
const pruefungen = {
'0 00056': {
        PZ : ['2018', '2026'],
        SZ : ['2018', '2026'],
        EINKUNFTSART:'_13EStG'
    },
'0 00062': {
        PZ : ['2018', '2026'],
        SZ : ['2018', '2026'],
        EINKUNFTSART:'_13EStG'
    },
'0 00093': {
        PZ : ['2018', '2026'],
        SZ : ['2018', '2026'],
        EINKUNFTSART:'_13EStG'
    },
'0 00094': {
        PZ : ['2018', '2026'],
        SZ : ['2018', '2026'],
        EINKUNFTSART:'_13EStG'
    },
'0 00095': {
        PZ : ['2018', '2023'],
        SZ : ['2018', '2023'],
        EINKUNFTSART:'_13EStG'
    },
'0 00096': {       ////
        PZ : ['2018', '2026'],
        SZ : ['2018', '2026'],
        EINKUNFTSART:'_13EStG'
    },
'0 00097': { ///
        PZ : ['2018', '2023'],
        SZ : ['2018', '2023'],
        EINKUNFTSART:'_13EStG'
    },
'0 00098': { ////
        PZ : ['2018', '2023'],
        SZ : ['2018', '2023'],
        EINKUNFTSART:'_13EStG'
    },
'0 00099': {
        PZ : ['2018', '2026'],
        SZ : ['2018', '2026'],
        EINKUNFTSART:'_13EStG'
    },
'0 00100': {
        PZ : ['2018', '2026'],
        SZ : ['2018', '2026'],
        EINKUNFTSART:'_13EStG'
    },
'0 00101': {
        PZ : ['2018', '2026'],
        SZ : ['2018', '2026'],
        EINKUNFTSART:'_13EStG'
    },
'0 00102': {
        PZ : ['2018', '2026'],
        SZ : ['2018', '2026'],
        EINKUNFTSART:'_13EStG'
    },
'0 00103': {
        PZ : ['2018', '2026'],
        SZ : ['2018', '2026'],
        EINKUNFTSART:'_13EStG'
    },
'0 00104': {
        PZ : ['2018', '2026'],
        SZ : ['2018', '2026'],
        EINKUNFTSART:'_13EStG'
    },
'0 00208': {
        PZ : ['2018', '2026'],
        SZ : ['2018', '2026'],
        EINKUNFTSART:'_13EStG'
    },
'0 00209': {
        PZ : ['2018', '2026'],
        SZ : ['2018', '2026'],
        EINKUNFTSART:'_13EStG'
    },
'0 00210': {
        PZ : ['2018', '2026'],
        SZ : ['2018', '2026'],
        EINKUNFTSART:'_13EStG'
    },
'0 00233': {
        PZ : ['2018', '2026'],
        SZ : ['2018', '2026'],
        EINKUNFTSART:'_13EStG'
    },
'0 00314': {
        PZ : ['2018', '2026'],
        SZ : ['2018', '2026'],
        EINKUNFTSART:'_13EStG'
    },
'0 00337': {
        PZ : ['2018', '2026'],
        SZ : ['2018', '2026'],
        EINKUNFTSART:'_13EStG'
    },

} as const;

// Setzen PZ und SZ
// for(let pruefung of Object.keys(pruefungen)){
//     const pruefungsnummer = pruefungen[pruefung as keyof typeof pruefungen];
//     await navigation.menu("PRUEFUNGSPLAN");
//     console.log(`Prüfungsnummer: ${pruefung}`);
//     await navigation.searchAndOpen(pruefung);
//     await navigation.navigateTo("VORBEREITUNG", "ZEITRAEUME");
//     await zeitraeume.setTimeFrame("SICHTUNGSZEITRAUM", pruefungsnummer.SZ[0], pruefungsnummer.SZ[1]);
//     await zeitraeume.selectOption('EINKUNFTSART', pruefungsnummer.EINKUNFTSART);
//     await zeitraeume.setTimeFrame("PRUEFUNGSZEITRAUM", pruefungsnummer.PZ[0], pruefungsnummer.PZ[1]);
//     await zeitraeume.clickButton('SPEICHERN');
//     // await page.pause();
// }


// // // test
for(let pruefung of Object.keys(pruefungen)){
    await navigation.menu("PRUEFUNGSPLAN");
    console.log(`Prüfungsnummer: ${pruefung}`);
    await navigation.searchAndOpen(pruefung);
    await navigation.navigateTo("VORBEREITUNG", "FESTSETZUNGSDATEN");
    await page.pause();
    // await navigation.navigateTo("VORBEREITUNG", "ZEITRAEUME");
    // await page.pause();
}

