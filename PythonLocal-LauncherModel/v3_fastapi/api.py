"""
api.py
------
API FastAPI con endpoints de launcher integrados.
Los endpoints /launcher/* son internos — no los modifiques.
Agrega tus rutas debajo de "TUS RUTAS".
"""

import time, logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── Silenciar logs de uvicorn (requests HTTP internos) ────────────────────────
# Solo mostramos errores reales; los access logs de /launcher/* desaparecen.
logging.getLogger("uvicorn.access").setLevel(logging.ERROR)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(docs_url=None, redoc_url=None)   # deshabilita /docs y /redoc en prod

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ══════════════════════════════════════════════════════════════════════════════
#  ESTADO DE SESION (usado por el launcher — NO MODIFICAR)
# ══════════════════════════════════════════════════════════════════════════════
_state = {
    "last_heartbeat": time.time(),
    "reloading":      False,
    "reload_until":   0,
    "closed":         False,
}

HEARTBEAT_TIMEOUT = 20  # seg sin heartbeat -> pagina cerrada
RELOAD_GRACE      = 6   # seg de gracia durante reload


@app.post("/launcher/heartbeat")
def heartbeat():
    _state["last_heartbeat"] = time.time()
    _state["closed"]         = False
    return {"ok": True}


@app.post("/launcher/reload")
def on_reload():
    _state["reloading"]    = True
    _state["reload_until"] = time.time() + RELOAD_GRACE
    return {"ok": True}


@app.post("/launcher/close")
def on_close():
    _state["closed"] = True
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
        return {"closed": True, "reason": "heartbeat_timeout",
                "elapsed": round(elapsed, 1)}

    return {"closed": False, "elapsed": round(elapsed, 1)}


# ══════════════════════════════════════════════════════════════════════════════
#  TUS RUTAS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/")
def root():
    return {"status": "ok", "message": "API corriendo"}


@app.get("/api/saludo")
def saludo():
    return {"saludo": "Hola desde la API!"}


@app.get("/api/datos")
def datos():
    return {
        "items": [
            {"id": 1, "nombre": "Elemento A", "valor": 42},
            {"id": 2, "nombre": "Elemento B", "valor": 87},
            {"id": 3, "nombre": "Elemento C", "valor": 15},
        ]
    }


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=5000,
        log_level="error",    # solo errores reales en stderr
        access_log=False,     # sin access log -> silencia 127.0.0.1 - GET /...
    )
