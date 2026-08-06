import type {Page, Locator} from "playwright"
declare const page: Page;
// DIESE ZEILE IST SEHR WICHTIG!! NICHT LÖSCHEN #NBELPH69

await page.goto('https://pdgo-qsi.fin-nrw.testa-de.net/index.html');
await page.locator('//input[@id="username"]').fill('fake');
await page.locator('//input[@id="password"]').fill('fake');
await page.locator('//*[@id="kc-login"]').click();


