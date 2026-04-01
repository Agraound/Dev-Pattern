"""
launcher.py
-----------
Lanza api.py y abre index.html en el navegador.
Termina cuando la pagina se cierra (no al recargar) o con Ctrl+C.

Uso:
    python launcher.py
"""

import subprocess, sys, os, time, signal, threading, importlib.util, webbrowser

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIGURACION
# ══════════════════════════════════════════════════════════════════════════════
API_FILE      = "api.py"
API_HOST      = "127.0.0.1"
API_PORT      = 5000
INDEX_HTML    = "index.html"
REQUIRED_LIBS = ["flask", "flask_cors"]   # agrega las tuyas aqui
# ══════════════════════════════════════════════════════════════════════════════

R  = "\033[0m"
B  = "\033[1m"
G  = "\033[92m"
Y  = "\033[93m"
RE = "\033[91m"
C  = "\033[96m"
DIM = "\033[2m"

def _log(color, tag, msg):
    # Limpia la linea del status antes de imprimir un log fijo
    print(f"\r\033[K{color}{B}[{tag}]{R} {msg}", flush=True)

def info(m):  _log(C,   "INFO", m)
def ok(m):    _log(G,   " OK ", m)
def warn(m):  _log(Y,   "WARN", m)
def err(m):   _log(RE,  "ERR ", m)

# Habilitar colores ANSI en CMD de Windows 10+
if sys.platform == "win32":
    import ctypes
    ctypes.windll.kernel32.SetConsoleMode(
        ctypes.windll.kernel32.GetStdHandle(-11), 7
    )


# ══════════════════════════════════════════════════════════════════════════════
#  STATUS LINE  (se actualiza in-place, sin generar nuevas lineas)
# ══════════════════════════════════════════════════════════════════════════════
_status_lock   = threading.Lock()
_status_active = False     # True una vez que el watcher esta corriendo

def set_status(text):
    """Sobreescribe la ultima linea con un indicador de estado."""
    if not _status_active:
        return
    with _status_lock:
        print(f"\r\033[K{DIM}  ● {text}{R}", end="", flush=True)


# ══════════════════════════════════════════════════════════════════════════════
#  1. VERIFICAR E INSTALAR LIBRERIAS
# ══════════════════════════════════════════════════════════════════════════════
def ensure_libraries():
    info("Verificando librerias...")
    missing = [
        lib for lib in REQUIRED_LIBS
        if importlib.util.find_spec(lib.replace("-", "_")) is None
    ]
    if not missing:
        ok("Todas las librerias presentes.")
        return

    warn(f"Faltantes: {', '.join(missing)}")
    for lib in missing:
        info(f"Instalando {lib}...")
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", lib, "-q"],
            capture_output=True, text=True
        )
        if r.returncode == 0:
            ok(f"{lib} instalado.")
        else:
            err(f"No se pudo instalar {lib}:\n{r.stderr.strip()}")
            sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
#  2. ARRANCAR LA API
# ══════════════════════════════════════════════════════════════════════════════
def start_api():
    if not os.path.exists(API_FILE):
        err(f"No se encontro '{API_FILE}' en esta carpeta.")
        sys.exit(1)

    info(f"Iniciando API en http://{API_HOST}:{API_PORT} ...")

    # stdout -> DEVNULL  (los request logs los maneja api.py internamente)
    # stderr -> PIPE     (capturado para mostrar errores reales de Python)
    proc = subprocess.Popen(
        [sys.executable, "-u", API_FILE],
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Lee stderr en background; filtra el ruido de Werkzeug
    _NOISE = (
        "* Serving Flask", "* Debug mode", "WARNING: This is a development",
        "Use a production WSGI", "* Running on", "Press CTRL+C", "127.0.0.1 -",
    )
    def _stderr_reader():
        for line in proc.stderr:
            line = line.rstrip()
            if not line or any(n in line for n in _NOISE):
                continue
            _log(RE, "API ", line)
    threading.Thread(target=_stderr_reader, daemon=True).start()

    time.sleep(1.5)
    if proc.poll() is not None:
        err("La API cerro inesperadamente. Revisa los errores de arriba.")
        sys.exit(1)

    ok(f"API corriendo (PID {proc.pid}).")
    return proc


# ══════════════════════════════════════════════════════════════════════════════
#  3. ABRIR NAVEGADOR
# ══════════════════════════════════════════════════════════════════════════════
def open_browser():
    path = os.path.abspath(INDEX_HTML)
    if not os.path.exists(path):
        err(f"No se encontro '{INDEX_HTML}'.")
        sys.exit(1)

    url = "file:///" + path.replace("\\", "/")
    info("Abriendo navegador...")
    webbrowser.open(url)
    ok("Pagina abierta.")


# ══════════════════════════════════════════════════════════════════════════════
#  4. VIGILAR HEARTBEATS
#
#  - index.html envia POST /launcher/heartbeat cada 2 seg.
#  - Al cerrar/recargar envia sendBeacon /launcher/reload.
#  - Si pasan 8 seg sin heartbeat (y sin reload activo) -> apagar.
# ══════════════════════════════════════════════════════════════════════════════
def watch_heartbeat(api_proc, stop_event):
    global _status_active
    import urllib.request, urllib.error, json

    base   = f"http://{API_HOST}:{API_PORT}/launcher"
    errors = 0
    checks = 0

    # Esperar a que el browser cargue
    time.sleep(4)
    _status_active = True
    info("Sesion activa. Ctrl+C para salir.")

    while not stop_event.is_set():
        try:
            with urllib.request.urlopen(f"{base}/status", timeout=3) as resp:
                data = json.loads(resp.read())
            errors  = 0
            checks += 1

            if data.get("closed"):
                _status_active = False
                print(flush=True)
                warn(f"Pagina cerrada  ({data.get('reason', '')}). Terminando...")
                shutdown(api_proc, stop_event)
                return

            # Actualizar status line
            reason  = data.get("reason", "")
            elapsed = data.get("elapsed", 0)
            ts      = time.strftime("%H:%M:%S")

            if reason == "reloading":
                set_status(f"{ts}  recargando pagina...")
            else:
                set_status(f"{ts}  sesion activa  |  ultimo hb hace {elapsed:.0f}s  |  checks: {checks}")

        except urllib.error.URLError:
            errors += 1
            set_status(f"API sin respuesta ({errors}/5)...")
            if errors >= 5:
                _status_active = False
                print(flush=True)
                warn("API sin respuesta. Terminando...")
                shutdown(api_proc, stop_event)
                return

        time.sleep(3)


# ══════════════════════════════════════════════════════════════════════════════
#  5. APAGADO ORDENADO
# ══════════════════════════════════════════════════════════════════════════════
def shutdown(api_proc, stop_event=None):
    if stop_event:
        stop_event.set()

    info("Cerrando API...")
    try:
        api_proc.send_signal(signal.CTRL_BREAK_EVENT)
        api_proc.wait(timeout=4)
        ok("API terminada.")
    except Exception:
        api_proc.kill()
        warn("API forzada a cerrar.")

    print(f"\n{G}{B}  Launcher cerrado correctamente.{R}\n", flush=True)
    os._exit(0)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    print(f"\n{C}{B}{'═'*51}", flush=True)
    print(f"   LAUNCHER  |  {API_FILE}  |  puerto {API_PORT}")
    print(f"{'═'*51}{R}\n", flush=True)

    ensure_libraries()
    api_proc   = start_api()
    stop_event = threading.Event()

    def handle_ctrl_c(sig, frame):
        global _status_active
        _status_active = False
        print(flush=True)
        warn("Ctrl+C recibido.")
        shutdown(api_proc, stop_event)

    signal.signal(signal.SIGINT, handle_ctrl_c)

    open_browser()

    watcher = threading.Thread(
        target=watch_heartbeat,
        args=(api_proc, stop_event),
        daemon=True
    )
    watcher.start()

    while not stop_event.is_set():
        time.sleep(0.5)


if __name__ == "__main__":
    main()
