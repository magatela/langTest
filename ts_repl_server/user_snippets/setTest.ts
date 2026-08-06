import type { Page, Locator } from "playwright"
import type { NavigationPage } from "../POM/NavigationPage.ts"
import type { ZeitraeumePage } from "../POM/ZeitraeumePage.ts"

declare const page: Page;
declare const navigation: NavigationPage;
declare const zeitraeume: ZeitraeumePage;

// DIESE ZEILE IST SEHR WICHTIG!! NICHT LÖSCHEN #NBELPH69

const test = '4969';

if (test === '4969') {
    const alleSteuernummer = ['5121/0/5702/4083', '5121/0/5759/4988', '5121/0/5707/4478', '5121/0/5707/5415', '5121/0/5719/4593', '5121/0/5724/5107', '5121/0/5726/4134', '5121/0/5171/4420', '5121/0/5190/6192', '5121/0/5739/5176', '5121/0/5831/5037', '5121/0/5270/5720', '5121/0/5299/6146', '5121/0/5766/4030', '5121/0/5396/4983', '5121/0/5775/4916', '5121/0/5700/5216']
    // const alleSteuernummer = ['5121/0/5270/5720', '5121/0/5299/6146', '5121/0/5766/4030', '5121/0/5396/4983', '5121/0/5775/4916', '5121/0/5700/5216']
    for (let steuernummern of alleSteuernummer) {
        console.log(`->${steuernummern}`);
        await navigation.menu("PRUEFUNGSPLAN");
        await navigation.searchAndOpen(steuernummern);
        // await navigation.navigateTo("VORBEREITUNG", "ZEITRAEUME");
        // await zeitraeume.setTimeFrame("SICHTUNGSZEITRAUM", 2018 as number, 2022 as number);
        // await zeitraeume.selectOption('EINKUNFTSART', '_13EStG');
        // await zeitraeume.setTimeFrame("PRUEFUNGSZEITRAUM", 2018 as number, 2022 as number);
        // await zeitraeume.clickButton('SPEICHERN');
        // await navigation.navigateTo("VORBEREITUNG", "GEWINNERMITTLUNG", "E_BILANZ_ANSICHT");

        // const ebilanzCheckBoxLocator = '//input[@data-role="checkbox-input"]';

        // try {
        //     await page.locator(ebilanzCheckBoxLocator).first().waitFor();

        // } catch (e) {
        //     console.log(`\t${steuernummern}  no E bilanz`);
        //     continue;
        // }
        // const listInput = await page.locator(ebilanzCheckBoxLocator).all();
        // for (let i = 0; i < listInput.length; i++) {
        //     try {
        //         const element = listInput[i]!;
        //         const enable = await element.isEnabled()
        //         if (enable) {
        //             await element.click();
        //         }
        //     } catch (e) {
        //         console.log(`ERROR ${e}`)
        //     }

        // }
        await navigation.navigateTo("VORBEREITUNG", "GEWINNERMITTLUNG", "KAPITALKONTENENTWICKLUNG");
        await page.pause();
    }
}

if (test == '1218') {

    await navigation.menu("PRUEFUNGSPLAN");
    await navigation.searchAndOpen('2000 00 0 00023');
    await navigation.navigateTo("VORBEREITUNG", "ZEITRAEUME");
    await zeitraeume.setTimeFrame("SICHTUNGSZEITRAUM", 2020 as number, 2022 as number);
    await zeitraeume.selectOption('EINKUNFTSART', '_13EStG');
    await zeitraeume.setTimeFrame("PRUEFUNGSZEITRAUM", 2020 as number, 2022 as number);
    await zeitraeume.clickButton('SPEICHERN');
    await navigation.navigateTo("VORBEREITUNG", "GEWINNERMITTLUNG", "E_BILANZ_ANSICHT");

    const ebilanzCheckBoxLocator = '//input[@data-role="checkbox-input"]';
    await page.locator(ebilanzCheckBoxLocator).first().waitFor();
    const listInput = await page.locator(ebilanzCheckBoxLocator).all();
    for (let i = 0; i < listInput.length; i++) {
        try {
            const element = listInput[i]!;
            const enable = await element.isEnabled()
            if (enable) {
                await element.click();
            }
        } catch (e) {
            console.log(`ERROR ${e}`)
        }

    }
    await navigation.navigateTo("VORBEREITUNG", "GEWINNERMITTLUNG", "KAPITALKONTENENTWICKLUNG");
    await page.pause();
}

//  5121/0/5724/5107  no E bilanz
//  5121/0/5270/5720
//  5121/0/5396/4983
