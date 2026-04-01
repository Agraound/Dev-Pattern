# py-launcher

Sistema para lanzar una API Python (Flask o FastAPI) enlazada con una interfaz web, desde terminal, con detección de cierre de ventana, logs limpios y apagado ordenado.

---

## Estructura del proyecto

```
proyecto/
├── launcher.py     ← orquestador: instala dependencias, lanza la API, abre el browser
├── api.py          ← tu API Flask o FastAPI (incluye endpoints /launcher/* internos)
└── index.html      ← tu interfaz web (envía heartbeats al servidor)
```

Los tres archivos deben estar en la misma carpeta. El único comando necesario es:

```
python launcher.py
```

---

## Cómo funciona

### El problema que resuelve

Monitorear el proceso del navegador desde Python no funciona de forma confiable. Chrome, Edge y Firefox mantienen procesos en background aunque no haya ninguna ventana abierta, haciendo imposible distinguir "cerré la pestaña" de "el browser sigue corriendo".

### La solución: heartbeat invertido

En lugar de que el launcher mire al browser, **la página le habla al servidor**:

```
index.html  ──POST /launcher/heartbeat (cada 2s)──►  api.py
index.html  ──sendBeacon /launcher/reload──────────►  api.py   (en beforeunload)
launcher.py ──GET /launcher/status (cada 3s)───────►  api.py
```

La API mantiene un estado interno con el timestamp del último heartbeat. El launcher consulta ese estado periódicamente. Si los heartbeats se detienen más de `HEARTBEAT_TIMEOUT` segundos (y no hay un reload activo), el launcher apaga todo.

### Distinguir recarga de cierre real

El evento `beforeunload` del browser se dispara tanto al cerrar como al recargar. La lógica para distinguirlos:

1. En `beforeunload`, la página siempre envía `sendBeacon(/launcher/reload)`.
2. La API activa una **gracia de `RELOAD_GRACE` segundos** durante la cual no considera que la sesión terminó.
3. Si la página se **recargó**, el nuevo documento manda un heartbeat inmediato → la gracia se cancela y todo sigue normal.
4. Si la página se **cerró**, nunca llega un heartbeat nuevo → la gracia expira → `status` devuelve `closed: true` → el launcher apaga.

`sendBeacon` es la única API del browser que **garantiza** que el request se completa aunque la página ya esté destruida.

### Logger de terminal

El output de Flask/Werkzeug se redirige: `stdout → DEVNULL`, `stderr → PIPE`. Un hilo lector filtra las líneas de ruido de Werkzeug (`* Serving Flask`, `127.0.0.1 -`, etc.) y solo muestra errores reales de Python (tracebacks, imports fallidos). La terminal queda limpia y muestra una **status line** que se actualiza in-place:

```
[ OK ] API corriendo (PID 4964).
[ OK ] Pagina abierta.
[INFO] Sesion activa. Ctrl+C para salir.
  ● 11:24:36  sesion activa  |  ultimo hb hace 1s  |  checks: 84
```

---

## Configuración

### launcher.py

```python
API_FILE      = "api.py"       # nombre del archivo de tu API
API_HOST      = "127.0.0.1"
API_PORT      = 5000
INDEX_HTML    = "index.html"
REQUIRED_LIBS = ["flask", "flask_cors"]   # librerías a verificar/instalar
```

Al arrancar, `launcher.py` verifica cada librería con `importlib.util.find_spec`. Las que falten se instalan automáticamente con `pip` antes de continuar.

### api.py — tiempos

```python
HEARTBEAT_TIMEOUT = 8   # segundos sin heartbeat -> cierre detectado
RELOAD_GRACE      = 4   # segundos de gracia durante un reload
```

### index.html — frecuencia de heartbeat

```javascript
setInterval(sendHeartbeat, 2000);   // cada 2 segundos
```

**Tabla de latencia de detección de cierre:**

| `HEARTBEAT_TIMEOUT` | `RELOAD_GRACE` | Heartbeat interval | Latencia aprox. |
|---|---|---|---|
| 8s | 4s | 2s | ~4–6s |
| 12s | 8s | 4s | ~8–12s |
| 5s | 3s | 1s | ~3–4s |

---

## Endpoints internos `/launcher/*`

Estos endpoints los usa exclusivamente `launcher.py`. No los expongas públicamente ni los modifiques.

| Endpoint | Método | Quién lo llama | Qué hace |
|---|---|---|---|
| `/launcher/heartbeat` | POST | `index.html` cada 2s | Actualiza `last_heartbeat` |
| `/launcher/reload` | POST | `index.html` en `beforeunload` | Activa gracia de reload |
| `/launcher/close` | POST | `index.html` (opcional) | Marca cierre explícito |
| `/launcher/status` | GET | `launcher.py` cada 3s | Devuelve `{"closed": bool}` |

---

## Portarlo a FastAPI

Reemplazar Flask por FastAPI requiere tres cambios puntuales.

### 1. Dependencias

```python
REQUIRED_LIBS = ["fastapi", "uvicorn", "python-multipart"]
```

### 2. api.py con FastAPI

```python
import time, uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

_state = {
    "last_heartbeat": time.time(),
    "reloading": False,
    "reload_until": 0,
    "closed": False,
}

HEARTBEAT_TIMEOUT = 8
RELOAD_GRACE      = 4

@app.post("/launcher/heartbeat")
def heartbeat():
    _state["last_heartbeat"] = time.time()
    _state["closed"] = False
    return {"ok": True}

@app.post("/launcher/reload")
def on_reload():
    _state["reloading"]    = True
    _state["reload_until"] = time.time() + RELOAD_GRACE
    return {"ok": True}

@app.get("/launcher/status")
def status():
    now = time.time()
    if _state["reloading"]:
        if now < _state["reload_until"]:
            return {"closed": False, "reason": "reloading"}
        _state["reloading"] = False
    if _state["closed"]:
        return {"closed": True, "reason": "explicit_close"}
    elapsed = now - _state["last_heartbeat"]
    if elapsed > HEARTBEAT_TIMEOUT:
        return {"closed": True, "reason": "heartbeat_timeout", "elapsed": round(elapsed, 1)}
    return {"closed": False, "elapsed": round(elapsed, 1)}

# Tus rutas van aquí
@app.get("/")
def root():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="error")
```

`log_level="error"` en uvicorn cumple la misma función que filtrar Werkzeug en Flask: silencia los logs de requests HTTP sin suprimir errores reales.

### 3. Filtro de ruido en launcher.py

El lector de stderr filtra líneas de Werkzeug. Con FastAPI/uvicorn hay que actualizar `_NOISE`:

```python
_NOISE = (
    "INFO:     ", "WARNING:  ", "Started server process",
    "Waiting for application startup", "Application startup complete",
    "127.0.0.1:",
)
```

---

## Comportamiento ante cada escenario

| Escenario | Qué pasa |
|---|---|
| Página abierta en primer plano | Heartbeats cada 2s, status line actualizada |
| Página en pestaña de fondo | Heartbeats continúan (Web Lock activo), sin cambios |
| Reload (F5 o botón) | `sendBeacon(/reload)` → gracia de 4s → nuevo heartbeat inmediato → sin apagado |
| Cierre de pestaña (X) | `sendBeacon(/reload)` → gracia de 4s → sin heartbeat nuevo → apagado a los ~4–6s |
| Cierre del browser completo | Idem cierre de pestaña |
| `Ctrl+C` en terminal | `SIGINT` → apagado ordenado → `CTRL_BREAK_EVENT` al subproceso de la API |
| API crashea sola | `stderr` del proceso aparece en terminal con prefijo `[API ]` en rojo |
| Puerto ocupado | Error visible en `[API ]`, launcher termina con código 1 |

---

## Web Lock: mantener la pestaña activa

Los browsers modernos pueden throttlear o suspender pestañas inactivas, lo que interrumpiría los heartbeats. El `index.html` usa la Web Locks API para prevenir esto:

```javascript
if (navigator.locks) {
    navigator.locks.request("keep_alive", { mode: "shared" }, () => new Promise(() => {}));
}
```

Una promesa que nunca resuelve mantiene el lock indefinidamente. El modo `"shared"` permite múltiples instancias simultáneas sin bloqueos.

---

## Checklist para un proyecto nuevo

```
[ ] Copiar launcher.py, api.py, index.html al proyecto
[ ] Editar REQUIRED_LIBS en launcher.py con las dependencias reales
[ ] Agregar las rutas de la app en api.py debajo de "TUS RUTAS"
[ ] No modificar ni eliminar los endpoints /launcher/*
[ ] Verificar que index.html apunte al puerto correcto (const API = "http://127.0.0.1:5000")
[ ] Ejecutar: python launcher.py
```

---

## Requisitos mínimos

- Python 3.7+
- Windows 10+ (para colores ANSI en CMD y `CREATE_NEW_PROCESS_GROUP`)
- Flask: `pip install flask flask-cors`
- FastAPI: `pip install fastapi uvicorn`

En Linux/macOS reemplazar `signal.CTRL_BREAK_EVENT` por `signal.SIGTERM` en la función `shutdown` de `launcher.py`.