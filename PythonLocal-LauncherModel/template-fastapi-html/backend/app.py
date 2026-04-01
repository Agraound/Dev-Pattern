import time
import threading
import os
import sys
import platform
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configurar encoding para Windows
if platform.system() == "Windows":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

app = FastAPI()

# Configurar CORS para permitir todas las conexiones
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables para el sistema de ping
IS_WIN = platform.system() == "Windows"
_last_ping = 0
_ping_active = False
_launcher_pid = int(os.environ.get("LAUNCHER_PID", 0))

print(f"\n[API] Iniciada - PID: {os.getpid()}, Launcher PID: {_launcher_pid}")
sys.stdout.flush()

def shutdown_app():
    """Función para detener toda la aplicación"""
    print(f"\n[API] Detectado cierre del navegador - Cerrando aplicacion...")
    print(f"[API] PID: {os.getpid()}, Launcher PID: {_launcher_pid}")
    sys.stdout.flush()
    
    # Pequeña pausa para asegurar que los mensajes se impriman
    time.sleep(1)
    
    if IS_WIN and _launcher_pid > 0:
        try:
            # Matar el proceso padre (run.py)
            os.system(f"taskkill /F /PID {_launcher_pid} > nul 2>&1")
        except:
            pass
    
    # Matar este proceso también
    os._exit(0)

def ping_watcher():
    """Hilo que monitorea los pings"""
    global _ping_active
    
    print("[API] Esperando primer ping del navegador...")
    sys.stdout.flush()
    
    # Esperar primer ping (max 30 segundos)
    for i in range(60):
        if _ping_active:
            break
        time.sleep(0.5)
    
    if not _ping_active:
        print("[API] No se recibio ping inicial")
        return
    
    print("[API] Navegador conectado - Monitor activado (timeout: 6s)")
    sys.stdout.flush()
    
    # Monitorear pings continuamente
    while True:
        time.sleep(1)
        tiempo_sin_ping = time.time() - _last_ping
        if tiempo_sin_ping > 6.0:  # 6 segundos sin ping
            print(f"[API] Timeout: {tiempo_sin_ping:.1f}s sin ping")
            sys.stdout.flush()
            shutdown_app()
            return

# Iniciar el watcher en un hilo
watcher_thread = threading.Thread(target=ping_watcher, daemon=True)
watcher_thread.start()

@app.get("/")
async def root():
    return {"message": "API funcionando", "status": "ok"}

@app.get("/ping")
async def ping():
    """Endpoint simplificado para ping"""
    global _last_ping, _ping_active
    _last_ping = time.time()
    if not _ping_active:
        _ping_active = True
        print("[API] Primer ping recibido - Navegador conectado")
        sys.stdout.flush()
    return {"status": "ok", "time": _last_ping}

@app.get("/api/ping")  # Mantener por compatibilidad
async def api_ping():
    return await ping()

@app.get("/api/hello")
async def hello():
    return {"message": "Hello from FastAPI!", "status": "success"}

@app.get("/api/time")
async def get_time():
    from datetime import datetime
    now = datetime.now()
    return {
        "current_time": now.isoformat(),
        "timestamp": now.timestamp(),
        "formatted_time": now.strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/hello")  # Ruta alternativa sin /api
async def hello_simple():
    return {"message": "Hello from FastAPI!"}

@app.get("/time")  # Ruta alternativa sin /api
async def time_simple():
    from datetime import datetime
    return {"time": datetime.now().isoformat()}

if __name__ == "__main__":
    port = int(os.environ.get("API_PORT", 8000))
    print(f"\n[API] Iniciando en http://127.0.0.1:{port}")
    print("[API] Endpoints disponibles:")
    print("  - GET /ping")
    print("  - GET /api/ping")
    print("  - GET /hello")
    print("  - GET /api/hello")
    print("  - GET /time")
    print("  - GET /api/time")
    print()
    sys.stdout.flush()
    
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=port, 
        log_level="info",
        access_log=True
    )