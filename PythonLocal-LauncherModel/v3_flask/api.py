"""
api.py
------
API Flask con endpoints de launcher integrados.
Los endpoints /launcher/* son internos — no los modifiques.
Agrega tus rutas debajo de "TUS RUTAS".
"""

import time, logging, os
from flask import Flask, jsonify
from flask_cors import CORS

# ── Silenciar logs de Werkzeug (el launcher ya no los ve via stdout,
#    pero los filtramos igual por si se corre api.py directo) ─────────────────
_wz = logging.getLogger("werkzeug")
_wz.setLevel(logging.ERROR)   # solo errores reales, no cada request

# Suprimir el banner de arranque de Flask
import flask.cli
flask.cli.show_server_banner = lambda *_: None

# ─────────────────────────────────────────────────────────────────────────────

app = Flask(__name__)
CORS(app)

# ══════════════════════════════════════════════════════════════════════════════
#  ESTADO DE SESION (usado por el launcher — NO MODIFICAR)
# ══════════════════════════════════════════════════════════════════════════════
_state = {
    "last_heartbeat": time.time(),
    "reloading":      False,
    "reload_until":   0,
    "closed":         False,
}

HEARTBEAT_TIMEOUT = 8   # seg sin heartbeat -> pagina cerrada
RELOAD_GRACE      = 4   # seg de gracia durante reload


@app.route("/launcher/heartbeat", methods=["POST"])
def heartbeat():
    _state["last_heartbeat"] = time.time()
    _state["closed"]         = False
    return jsonify({"ok": True})


@app.route("/launcher/reload", methods=["POST"])
def on_reload():
    _state["reloading"]    = True
    _state["reload_until"] = time.time() + RELOAD_GRACE
    return jsonify({"ok": True})


@app.route("/launcher/close", methods=["POST"])
def on_close():
    _state["closed"] = True
    return jsonify({"ok": True})


@app.route("/launcher/status")
def status():
    now = time.time()

    if _state["reloading"]:
        if now < _state["reload_until"]:
            return jsonify({"closed": False, "reason": "reloading"})
        _state["reloading"] = False

    if _state["closed"]:
        return jsonify({"closed": True, "reason": "explicit_close"})

    elapsed = now - _state["last_heartbeat"]
    if elapsed > HEARTBEAT_TIMEOUT:
        return jsonify({"closed": True, "reason": "heartbeat_timeout",
                        "elapsed": round(elapsed, 1)})

    return jsonify({"closed": False, "elapsed": round(elapsed, 1)})


# ══════════════════════════════════════════════════════════════════════════════
#  TUS RUTAS
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def root():
    return jsonify({"status": "ok", "message": "API corriendo"})


@app.route("/api/saludo")
def saludo():
    return jsonify({"saludo": "Hola desde la API!"})


@app.route("/api/datos")
def datos():
    return jsonify({
        "items": [
            {"id": 1, "nombre": "Elemento A", "valor": 42},
            {"id": 2, "nombre": "Elemento B", "valor": 87},
            {"id": 3, "nombre": "Elemento C", "valor": 15},
        ]
    })


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
