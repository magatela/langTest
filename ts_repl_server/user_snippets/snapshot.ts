import type { Page } from "playwright"
import { promises as fs } from "fs";
declare const page: Page;
// DIESE ZEILE IST SEHR WICHTIG!! NICHT LÖSCHEN #NBELPH69

const index = 1
const listLocators = [
    '//body',                                               // 0. page
    '//div[@data-role="application-frame-main"]',           // 1. Applikation Main frame
    '//div[@data-role="modal-overlay-content"]',            // 2. modal assitant in maske bericht
    '//div[@data-role="application-frame-sidebar-wrapper"]' // 3. navigationsbar
]
const snapshot = await page.locator(listLocators[index] as string).ariaSnapshot();
fs.writeFile('aria.txt', snapshot, {encoding: 'utf-8'})
console.log('saved ariaSnapshot');







