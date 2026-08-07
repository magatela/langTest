# config/config_loader.py
import os
from pathlib import Path
import yaml
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

def get_jira_credentials() -> dict:
    """
    Obtiene credenciales de Jira desde config/config.yaml o variables de entorno.
    """
    config_file = ROOT_DIR / "config" / "config.yaml"
    
    jira_config = {
        "base_url": os.getenv("JIRA_BASE_URL", "https://jira.example.com/"),
        "prefix": os.getenv("JIRA_PREFIX", "PDNEU"),
        "user": os.getenv("JIRA_USER", "qa_user@example.com"),
        "password": os.getenv("JIRA_PASSWORD", "secret_token_or_password"),
        "proxies": None
    }
    
    # Cargar proxy si está configurado en .env
    http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    if http_proxy or https_proxy:
        jira_config["proxies"] = {
            "http": http_proxy or https_proxy,
            "https": https_proxy or http_proxy
        }
        
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data and "jira" in data:
                    j_data = data["jira"]
                    jira_config["base_url"] = j_data.get("base_url", jira_config["base_url"])
                    jira_config["prefix"] = j_data.get("prefix", jira_config["prefix"])
                    jira_config["user"] = j_data.get("user", jira_config["user"])
                    jira_config["password"] = j_data.get("password", jira_config["password"])
                    if "proxies" in j_data:
                        jira_config["proxies"] = j_data["proxies"]
        except Exception as e:
            pass

    return jira_config

def get_llm_config() -> dict:
    """
    Obtiene la configuración de los modelos LLM desde config/config.yaml o .env.
    """
    config_file = ROOT_DIR / "config" / "config.yaml"
    
    llm_config = {
        "apiBase": os.getenv("OPENAI_API_BASE", os.getenv("LLM_API_BASE", "https://api.openai.com/v1")),
        "apiKey": os.getenv("OPENAI_API_KEY", os.getenv("LLM_API_KEY", "mock-key")),
        "models": [
            {"model": os.getenv("LLM_MODEL_WRITER", "gpt-4o"), "temperature": 0.2},
            {"model": os.getenv("LLM_MODEL_REVIEWER", "gpt-4o"), "temperature": 0.1}
        ]
    }
    
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data:
                    if "apiBase" in data:
                        llm_config["apiBase"] = data["apiBase"]
                    if "apiKey" in data:
                        llm_config["apiKey"] = data["apiKey"]
                    if "models" in data and isinstance(data["models"], list):
                        llm_config["models"] = data["models"]
        except Exception:
            pass

    return llm_config


def get_playwright_config() -> dict:
    """
    Obtiene la configuración de Playwright y ejecutable Chrome desde config/config.yaml o .env.
    """
    config_file = ROOT_DIR / "config" / "config.yaml"

    use_custom_chrome = os.getenv("PLAYWRIGHT_USE_CUSTOM_CHROME", "false").lower() in ["true", "1", "yes"]
    chrome_path = os.getenv("PLAYWRIGHT_CHROME_PATH", "")
    headless = os.getenv("PLAYWRIGHT_HEADLESS", "false").lower() in ["true", "1", "yes"]
    results_dir = os.getenv("PLAYWRIGHT_RESULTS_DIR", str(ROOT_DIR / "results"))

    pw_config = {
        "use_custom_chrome_path": use_custom_chrome,
        "chrome_path": chrome_path,
        "headless": headless,
        "results_dir": results_dir
    }

    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data and "playwright" in data:
                    p_data = data["playwright"]
                    pw_config["use_custom_chrome_path"] = bool(p_data.get("use_custom_chrome_path", pw_config["use_custom_chrome_path"]))
                    pw_config["chrome_path"] = str(p_data.get("chrome_path", pw_config["chrome_path"]))
                    pw_config["headless"] = bool(p_data.get("headless", pw_config["headless"]))
                    pw_config["results_dir"] = str(p_data.get("results_dir", pw_config["results_dir"]))
        except Exception:
            pass

    return pw_config

