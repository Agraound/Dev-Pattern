# Patrón: Shutdown automático al cerrar el navegador (Windows + Unix)

## Problema

Cuando una app Python/FastAPI se lanza desde `run.py` y el usuario cierra
la pestaña del navegador, el proceso queda huérfano en terminal.
Los métodos "obvios" no funcionan:

| Método | Por qué falla |
|--------|--------------|
| `beforeunload` + `fetch` | El browser cancela requests al cerrar |
| `beforeunload` + `sendBeacon` | Poco confiable en Windows/localhost |
| `os.kill(os.getpid(), SIGTERM)` | Solo mata el worker; el watchdog de uvicorn `--reload` relanza uno nuevo |
| `os.killpg(pgid, SIGTERM)` | El PGID de uvicorn `--reload` no es predecible |
| `asyncio.create_task` + sleep | El event loop se cancela antes de ejecutar la tarea |
| `NO_COLOR=1` / `TERM=dumb` en env | Uvicorn CLI ignora estas vars, genera ANSI igual |

---

## Solución probada y funcionando

### Arquitectura de puertos

```
run.py
  ├── http.server en :8080  →  sirve index.html (thread daemon, sin ANSI)
  └── subprocess → backend/serve.py → uvicorn.run() en :8000
                                         └── app.py (FastAPI)
```

Separar frontend y API en puertos distintos es clave:
- Evita que el browser bloquee fetches a `location.host` al cerrar
- Permite URLs hardcodeadas y confiables en el frontend
- `http.server` nativo de Python no genera ANSI

### Mecanismo de shutdown: ping polling

```
Frontend (cada 2s)          Backend
    │                           │
    │  GET /api/ping  ──────►  │  _last_ping = time.time()
    │                           │
    │  (usuario cierra tab)     │
    │                           │  _ping_watcher thread:
    │                           │    while time.time() - _last_ping > 6.0:
    │                           │      _do_shutdown("ping-timeout")
```

No depende de eventos del browser. Funciona en todos los OS y browsers.

---

## Implementación

### run.py

```python
import http.server, functools, threading

API_PORT   = 8000
FRONT_PORT = 8080

def start_frontend_server(front_dir):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass  # silenciar logs
        def end_headers(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            super().end_headers()

    HandlerWithDir = functools.partial(Handler, directory=front_dir)
    server = http.server.HTTPServer(("127.0.0.1", FRONT_PORT), HandlerWithDir)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server

# Arrancar uvicorn via serve.py (no CLI) para evitar ANSI
api_proc = subprocess.Popen([sys.executable, "backend/serve.py"], env=env)
front_srv = start_frontend_server("frontend/")
```

### backend/serve.py — uvicorn sin ANSI

```python
import uvicorn

LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "plain": {"fmt": "%(levelname)s: %(message)s"}
    },
    "handlers": {
        "default": {"class": "logging.StreamHandler",
                    "formatter": "plain", "stream": "ext://sys.stderr"}
    },
    "loggers": {
        "uvicorn":        {"handlers": ["default"], "level": "INFO",    "propagate": False},
        "uvicorn.error":  {"handlers": ["default"], "level": "INFO",    "propagate": False},
        "uvicorn.access": {"handlers": [],          "level": "WARNING", "propagate": False},
    },
}

uvicorn.run("backend.app:app", host="127.0.0.1", port=8000,
            reload=True, reload_dirs=["backend/"], log_config=LOG_CONFIG)
```

### backend/app.py — ping watcher + shutdown multiplataforma

```python
import time, threading, os, signal, platform, subprocess

IS_WIN = platform.system() == "Windows"
_last_ping   = 0.0
_ping_active = False

def _do_shutdown(reason="unknown"):
    launcher = os.environ.get("PROMPTFORGE_LAUNCHER_PID")
    print(f"  [App] Shutdown ({reason})", flush=True)
    if IS_WIN:
        target = launcher or str(os.getppid())
        subprocess.Popen(["taskkill", "/F", "/T", "/PID", target],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        for p in (os.getppid(), os.getpid()):
            try: os.kill(p, signal.SIGTERM)
            except ProcessLookupError: pass

def _ping_watcher():
    # Esperar primer ping (max 60s)
    for _ in range(120):
        if _ping_active: break
        time.sleep(0.5)
    else:
        return  # nunca conectó, no hacer nada

    # Monitorear continuamente
    while True:
        time.sleep(1.0)
        if time.time() - _last_ping > 6.0:
            _do_shutdown("ping-timeout")
            return

threading.Thread(target=_ping_watcher, daemon=True).start()

@app.get("/api/ping")
def ping():
    global _last_ping, _ping_active
    _last_ping   = time.time()
    _ping_active = True
    return {"ok": True}
```

### frontend/index.html — ping cada 2s

```javascript
(function startPing() {
  const PING_URL     = 'http://127.0.0.1:8000/api/ping';
  const SHUTDOWN_URL = 'http://127.0.0.1:8000/api/shutdown';

  function ping() {
    fetch(PING_URL, { method: 'GET' }).catch(() => {});
  }
  ping();
  setInterval(ping, 2000);

  // beforeunload como refuerzo opcional
  window.addEventListener('beforeunload', () => {
    try { navigator.sendBeacon(SHUTDOWN_URL); } catch(e) {}
    try { fetch(SHUTDOWN_URL, { method: 'POST', keepalive: true,
                                headers: {'Content-Type':'application/json'},
                                body: '{}' }); } catch(e) {}
  });
})();
```

---

## Comportamiento esperado en terminal

```
==========================================
         MiApp  Launcher
==========================================
  API      -> http://127.0.0.1:8000
  App      -> http://127.0.0.1:8080
  PID      -> 3800

  Esperando API...
  [App] Ping watcher iniciado
  Abriendo en navegador -> http://127.0.0.1:8080
  [App] Browser conectado — monitoreando...

(usuario cierra la pestaña, ~6 segundos después)

  [App] Shutdown (ping-timeout) launcher=3800 ppid=664 pid=2912
  Deteniendo...
  MiApp detenido.
```

---

## Notas

- El timeout de 6s es deliberado: tolera recargas de página sin apagar el servidor
- Si hay múltiples pestañas, el servidor se apaga cuando se cierra la última
  (porque `_ping_active` solo es `True` mientras alguna pestaña esté enviando pings)
- En desarrollo con `--reload`, uvicorn reinicia el worker ante cambios de archivo;
  el `_ping_active`/`_last_ping` se resetea, pero el watcher espera el primer ping
  nuevo antes de activarse de nuevo
- `PROMPTFORGE_LAUNCHER_PID` se pasa como variable de entorno desde `run.py`
  para que `taskkill` en Windows apunte al proceso correcto

-----------------------------------------------------------------------------------------------------------------------