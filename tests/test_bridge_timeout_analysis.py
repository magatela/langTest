import time
import pytest
from modules.module_2_browser_repl.ts_repl_bridge import get_repl_bridge, reset_repl_bridge, analyze_playwright_error

def test_analyze_playwright_error_unit():
    # 1. Timeout locator error
    timeout_err = "locator.click: Timeout 30000ms exceeded.\nCall log:\n  - waiting for locator('button#submit')"
    diag = analyze_playwright_error(timeout_err, "await page.locator('button#submit').click()")
    assert diag["error_type"] == "LOCATOR_TIMEOUT"
    assert len(diag["suggested_actions"]) > 0
    assert any("get_aria_snapshot" in act for act in diag["suggested_actions"])

    # 2. Strict mode violation error
    strict_err = "Error: strict mode violation: locator('button') resolved to 3 elements"
    diag_strict = analyze_playwright_error(strict_err, "await page.locator('button').click()")
    assert diag_strict["error_type"] == "STRICT_MODE_VIOLATION"
    assert any(".first()" in act for act in diag_strict["suggested_actions"])

    # 3. Element obscured error
    obscured_err = "elementHandle.click: <div class='modal-backdrop'></div> intercepts pointer events"
    diag_obs = analyze_playwright_error(obscured_err, "await page.locator('#btn').click()")
    assert diag_obs["error_type"] == "ELEMENT_OBSCURED"

def test_bridge_execution_with_logs_and_timeout():
    reset_repl_bridge()
    bridge = get_repl_bridge()

    # Probar ejecución con logs de consola y espera asíncrona
    code = """
        console.log('Log de prueba 1');
        console.info('Log informativo');
        await new Promise(resolve => setTimeout(resolve, 1000));
        return { ok: true, value: 99 };
    """
    res = bridge.eval_code(code, timeout=60.0)
    print("Respuesta con logs:", res)
    assert res.get("status") == "success"
    assert res.get("result") == {"ok": True, "value": 99}
    assert "Log de prueba 1" in res.get("logs", [])
    assert any("Log informativo" in log for log in res.get("logs", []))

    # Probar que un error en tiempo de ejecución devuelva el análisis enriquecido sin romper la sesión
    error_code = """
        console.log('Antes del error');
        throw new Error("locator.click: Timeout 30000ms exceeded waiting for locator('input#custom')");
    """
    err_res = bridge.eval_code(error_code, timeout=60.0)
    print("Respuesta de error analizada:", err_res)
    assert err_res.get("status") == "error"
    assert "analysis" in err_res
    assert err_res["analysis"]["error_type"] == "LOCATOR_TIMEOUT"
    assert len(err_res["analysis"]["suggested_actions"]) > 0
    assert bridge.is_running()

    # Detener el puente
    bridge.stop()
    assert not bridge.is_running()

if __name__ == "__main__":
    test_analyze_playwright_error_unit()
    test_bridge_execution_with_logs_and_timeout()
    print("Todas las pruebas de timeout y análisis pasaron exitosamente.")
