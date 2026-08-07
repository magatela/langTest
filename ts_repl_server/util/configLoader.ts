import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import yaml from 'js-yaml';
import dotenv from 'dotenv';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '../../');

// Cargar .env si existe en la raíz del proyecto
const envPath = path.join(rootDir, '.env');
if (fs.existsSync(envPath)) {
    dotenv.config({ path: envPath });
}

export interface JiraConfig {
    base_url: string;
    prefix: string;
    user: string;
    password: string;
    proxies?: {
        http?: string;
        https?: string;
    };
}

export interface PlaywrightConfig {
    use_custom_chrome_path: boolean;
    chrome_path: string;
    headless: boolean;
    results_dir: string;
}

let cachedConfig: any = null;

function loadConfigData(): any {
    if (cachedConfig) return cachedConfig;

    const yamlPath = path.join(rootDir, 'config', 'config.yaml');
    const exampleYamlPath = path.join(rootDir, 'config', 'config.yaml.example');
    let targetPath = fs.existsSync(yamlPath) ? yamlPath : (fs.existsSync(exampleYamlPath) ? exampleYamlPath : null);

    if (targetPath) {
        try:
            const content = fs.readFileSync(targetPath, 'utf-8');
            cachedConfig = yaml.load(content) || {};
        } catch (e) {
            cachedConfig = {};
        }
    } else {
        cachedConfig = {};
    }
    return cachedConfig;
}

export function getJiraConfig(): JiraConfig {
    const configData = loadConfigData();
    const jData = configData.jira || {};

    const httpProxy = process.env.HTTP_PROXY || process.env.http_proxy;
    const httpsProxy = process.env.HTTPS_PROXY || process.env.https_proxy;
    let proxies = jData.proxies;
    if (!proxies && (httpProxy || httpsProxy)) {
        proxies = {
            http: httpProxy || httpsProxy,
            https: httpsProxy || httpProxy
        };
    }

    return {
        base_url: process.env.JIRA_BASE_URL || jData.base_url || 'https://jira.example.com/',
        prefix: process.env.JIRA_PREFIX || jData.prefix || 'PDNEU',
        user: process.env.JIRA_USER || jData.user || '',
        password: process.env.JIRA_PASSWORD || jData.password || '',
        proxies: proxies
    };
}

export function getPlaywrightConfig(): PlaywrightConfig {
    const configData = loadConfigData();
    const pData = configData.playwright || {};

    const envUseCustom = process.env.PLAYWRIGHT_USE_CUSTOM_CHROME;
    const use_custom_chrome_path = envUseCustom !== undefined 
        ? (envUseCustom.toLowerCase() === 'true' || envUseCustom === '1')
        : (pData.use_custom_chrome_path === true);

    const chrome_path = process.env.PLAYWRIGHT_CHROME_PATH || pData.chrome_path || '';

    const envHeadless = process.env.PLAYWRIGHT_HEADLESS;
    const headless = envHeadless !== undefined 
        ? (envHeadless.toLowerCase() === 'true' || envHeadless === '1')
        : (pData.headless === true);

    const defaultResults = path.join(rootDir, 'results');
    const results_dir = process.env.PLAYWRIGHT_RESULTS_DIR || pData.results_dir || defaultResults;

    return {
        use_custom_chrome_path,
        chrome_path,
        headless,
        results_dir
    };
}
