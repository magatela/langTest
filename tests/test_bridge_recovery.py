import time
import psutil
from modules.module_2_browser_repl.ts_repl_bridge import get_repl_bridge, reset_repl_bridge

def test_bridge_lifecycle_and_recovery():
    reset_repl_bridge()
    bridge = get_repl_bridge()

    print("[1] Iniciando REPL Bridge y ejecutando código simple...")
    res = bridge.eval_code("return 1 + 1;")
    print("Respuesta 1:", res)
    assert res.get("status") == "success"
    assert res.get("result") == 2
    assert bridge.is_running()

    pid = bridge.process.pid
    print(f"PID del subproceso REPL: {pid}")

    # Verificar que el proceso existe en psutil
    proc = psutil.Process(pid)
    children = proc.children(recursive=True)
    print(f"Procesos hijos detectados ({len(children)}): {[c.pid for c in children]}")

    print("\n[2] Simulando crash inducido matando el subproceso directamente...")
    for c in children:
        try:
            c.kill()
        except Exception:
            pass
    proc.kill()
    time.sleep(0.5)


    print("\n[3] Enviando nuevo comando para probar auto-recuperación...")
    res2 = bridge.eval_code("return 40 + 2;")
    print("Respuesta 2 (tras recuperación):", res2)
    assert res2.get("status") == "success"
    assert res2.get("result") == 42
    assert bridge.is_running()

    new_pid = bridge.process.pid
    print(f"Nuevo PID del subproceso REPL: {new_pid} (diferente al original: {new_pid != pid})")
    assert new_pid != pid

    print("\n[4] Deteniendo REPL Bridge limpiamente...")
    bridge.stop()
    assert not bridge.is_running()
    print("Verificando que no queden procesos residuales del nuevo PID...")
    assert not psutil.pid_exists(new_pid)
    print("Todas las pruebas pasaron exitosamente!")

if __name__ == "__main__":
    test_bridge_lifecycle_and_recovery()
