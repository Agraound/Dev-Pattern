#!/usr/bin/env python3
import subprocess
import sys
import time
import os
import webbrowser
import threading
import socket
import http.server
import functools
from pathlib import Path

def install_dependencies():
    """Verifica e instala las dependencias necesarias"""
    required_packages = ['fastapi', 'uvicorn']
    missing_packages = []
    
    print("Verificando dependencias...")
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package} ya instalado")
        except ImportError:
            print(f"  ❌ {package} no instalado")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Instalando dependencias faltantes: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--user"] + missing_packages)
            print("✅ Dependencias instaladas correctamente")
        except subprocess.CalledProcessError as e:
            print(f"Error instalando dependencias: {e}")
            sys.exit(1)
    else:
        print("✅ Todas las dependencias ya están instaladas")

def find_free_port(start_port=8000, max_attempts=100):
    """Encuentra un puerto libre empezando desde start_port"""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except socket.error:
                continue
    raise RuntimeError("No se encontró un puerto libre")

def start_frontend_server(frontend_dir, port):
    """Inicia el servidor HTTP para el frontend (sin logs)"""
    class SilentHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass
    
    HandlerWithDir = functools.partial(SilentHandler, directory=str(frontend_dir))
    server = http.server.HTTPServer(("127.0.0.1", port), HandlerWithDir)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"  🌐 Frontend server: http://127.0.0.1:{port}")
    return server

def main():
    print("\n" + "="*60)
    print("         🚀 Iniciando Aplicación")
    print("="*60)
    
    # Obtener ruta base
    base_path = Path(__file__).parent.absolute()
    print(f"📁 Directorio base: {base_path}")
    
    # Verificar que existe index.html
    index_path = base_path / "frontend" / "index.html"
    if not index_path.exists():
        print(f"❌ Error: No se encuentra {index_path}")
        print("Por favor, asegúrate de que frontend/index.html existe")
        sys.exit(1)
    
    # Verificar/Instalar dependencias
    install_dependencies()
    
    # Configurar puertos
    API_PORT = find_free_port(8000)
    FRONT_PORT = find_free_port(8080)
    
    # Configurar entorno
    env = os.environ.copy()
    env["API_PORT"] = str(API_PORT)
    env["LAUNCHER_PID"] = str(os.getpid())
    
    print(f"\n📡 Configuración de puertos:")
    print(f"  🔷 API: http://127.0.0.1:{API_PORT}")
    print(f"  🌐 Frontend: http://127.0.0.1:{FRONT_PORT}")
    
    # Iniciar API
    print("\n🚀 Iniciando servidores...")
    backend_path = base_path / "backend"
    api_process = subprocess.Popen(
        [sys.executable, str(backend_path / "app.py")],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    print(f"  🔷 API Process PID: {api_process.pid}")
    
    # Esperar a que la API inicie
    time.sleep(3)
    
    # Iniciar frontend
    frontend_path = base_path / "frontend"
    frontend_server = start_frontend_server(frontend_path, FRONT_PORT)
    
    # Abrir navegador
    print("\n🌐 Abriendo navegador...")
    webbrowser.open(f"http://127.0.0.1:{FRONT_PORT}")
    
    print("\n" + "="*60)
    print("✅ Aplicación iniciada correctamente!")
    print("="*60)
    print("\n📋 Instrucciones:")
    print("  • La app se cerrará automáticamente 6 segundos después")
    print("    de cerrar la pestaña del navegador")
    print("  • Recargar la página mantiene la app activa")
    print("  • Presiona Ctrl+C para detener manualmente")
    print("\n" + "="*60 + "\n")
    
    try:
        # Leer salida de la API
        while True:
            line = api_process.stdout.readline()
            if line:
                print(line.strip())
                if "Cerrando aplicación" in line or "Shutdown" in line:
                    print("\n👋 Detectado cierre del navegador - Terminando...")
                    time.sleep(2)  # Dar tiempo para que se ejecute taskkill
                    break
            
            # Verificar si el proceso terminó
            if api_process.poll() is not None:
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo aplicación (Ctrl+C)...")
    finally:
        # Terminar procesos
        if api_process.poll() is None:
            print("  ⏳ Terminando proceso API...")
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/PID", str(api_process.pid)], 
                             capture_output=True, check=False)
            else:
                api_process.terminate()
        
        print("👋 Aplicación detenida")
        os._exit(0)

if __name__ == "__main__":
    main()