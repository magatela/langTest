import type { Page } from "playwright"
import { randomString, executeAssertion, executeStep, ResultWriter } from "../util/util.ts"
import { expect } from "playwright/test";
import { NavigationPage } from "../POM/NavigationPage.ts"
import { ZeitraeumePage } from "../POM/ZeitraeumePage.ts"
import { PruefungsberichtMainPage } from "../POM/BerichtMainPage.ts"
import { SteuerpflichtigenPage } from "../POM/BerichtEingabedialogPage.ts"
import { UbermittlungsschreibenPage } from "../POM/UbermittlungsschreibenPage.ts"

declare const page: Page;
declare const navigation: NavigationPage;
declare const zeitraeume: ZeitraeumePage;
declare const bericht: PruefungsberichtMainPage;
declare const bericht_eingabe: SteuerpflichtigenPage;
declare const bericht_ubermittlung: UbermittlungsschreibenPage;
// DIESE ZEILE IST SEHR WICHTIG!! NICHT LÖSCHEN #NBELPH69

const isVisible = await bericht_ubermittlung.isVisible('links', 'UEBERMITTLUNGSSCHREIBEN');
await executeAssertion(
    () => { expect(isVisible).toBeTruthy() },
    `Das Feld 'Übermittlungschreiben' ist NICHT sichtbar`
);
await bericht_ubermittlung.click('links', 'UEBERMITTLUNGSSCHREIBEN');
await bericht_ubermittlung.highlight('links', 'UEBERMITTLUNGSSCHREIBEN', 'red');
await bericht_ubermittlung.highlight('links', 'UEBERMITTLUNGSSCHREIBEN', 'none');