# Prompt para replicar el sistema FastAPI con auto-shutdown

## Objetivo
Crear una aplicación web con FastAPI que se cierre automáticamente cuando el usuario cierra la pestaña del navegador, pero que mantenga la sesión activa al recargar la página.

## Estructura de archivos requerida
```
project/
├── run.py                 # Orquestador principal
├── backend/
│   └── app.py             # API FastAPI con lógica de shutdown
└── frontend/
    └── index.html         # Interfaz de usuario con sistema de ping
```

## Requisitos funcionales

### 1. Sistema de puertos separados
- API FastAPI debe correr en puerto 8000
- Servidor frontend (HTTP server nativo de Python) debe correr en puerto 8080
- Los puertos deben ser configurables y buscar puertos libres automáticamente

### 2. Mecanismo de auto-shutdown
- Frontend debe enviar pings cada 2 segundos al endpoint `/ping` de la API
- Backend debe monitorear estos pings y cerrar la aplicación si pasan más de 6 segundos sin recibir uno
- Al cerrar la pestaña del navegador, los pings se detienen y la aplicación debe terminar después del timeout
- Al recargar la página, los pings continúan y la aplicación se mantiene activa

### 3. Características técnicas del backend
- FastAPI con CORS configurado para permitir peticiones desde cualquier origen
- Endpoints principales:
  - `GET /ping` - Recibe pings del frontend
  - `GET /api/hello` - Endpoint de ejemplo
  - `GET /api/time` - Endpoint que devuelve la hora actual
- Hilo watcher que monitorea el tiempo desde el último ping
- Función de shutdown que mata el proceso padre usando `taskkill` en Windows
- Manejo de encoding para Windows (evitar errores con caracteres Unicode)

### 4. Características técnicas del frontend
- HTML/CSS/JavaScript puro (sin frameworks)
- Sistema de ping con fetch API y timeout de 3 segundos
- Manejo de errores con reconexión automática (hasta 5 intentos)
- Interfaz visual que muestra:
  - Estado de conexión (conectado/desconectado)
  - Contador de pings enviados
  - Temporizador de tiempo sin ping
  - Log de depuración
- Deshabilitar botones durante llamadas a la API
- Uso de AbortController para manejar timeouts
- Eventos `beforeunload` y `visibilitychange` para manejo de cierre

### 5. Características del orquestador (run.py)
- Verificar e instalar dependencias automáticamente (fastapi, uvicorn)
- Buscar puertos libres automáticamente
- Iniciar proceso de la API como subprocess
- Iniciar servidor HTTP estático para frontend (silencioso, sin logs)
- Abrir navegador automáticamente
- Monitorear salida de la API para detectar shutdown
- Terminar todos los procesos al finalizar

## Comportamiento esperado
1. Al ejecutar `python run.py`:
   - Se instalan dependencias si es necesario
   - Se inicia la API en puerto 8000
   - Se inicia el frontend en puerto 8080
   - Se abre el navegador automáticamente

2. Con el navegador abierto:
   - La interfaz muestra "Conectado"
   - Los pings se envían cada 2 segundos
   - Los botones permiten probar los endpoints

3. Al cerrar la pestaña:
   - Los pings se detienen
   - Después de 6 segundos, la API detecta el timeout
   - La API mata el proceso padre (run.py)
   - Toda la aplicación termina

4. Al recargar la página:
   - Los pings continúan
   - La aplicación se mantiene activa

5. Al perder conexión:
   - La interfaz muestra "Desconectado"
   - Intenta reconectar automáticamente
   - Los botones se deshabilitan apropiadamente

## Código base para cada archivo

### run.py
```python
#!/usr/bin/env python3
import subprocess, sys, time, os, webbrowser, threading, socket, http.server, functools
from pathlib import Path

# Funciones:
# - install_dependencies()
# - find_free_port()
# - start_frontend_server()
# - main() con manejo de procesos y shutdown
```

### backend/app.py
```python
import time, threading, os, sys, platform
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configurar encoding para Windows
if platform.system() == "Windows":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Variables globales: _last_ping, _ping_active, _launcher_pid
# Funciones: shutdown_app(), ping_watcher()
# Endpoints: /, /ping, /api/hello, /api/time
```

### frontend/index.html
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>FastAPI App</title>
    <style>
        /* Estilos para interfaz limpia con indicadores de estado */
    </style>
</head>
<body>
    <div class="container">
        <!-- Interfaz con status, botones y logs -->
    </div>
    <script>
        const API_URL = 'http://127.0.0.1:8000';
        // Sistema de ping con fetch, manejo de errores, reconexión
        // Funciones: ping(), callAPI(), updateConnectionStatus()
        // Eventos: window.onload, beforeunload, visibilitychange
    </script>
</body>
</html>
```

## Notas adicionales
- Evitar el uso de emojis en prints para compatibilidad con Windows
- Implementar timeouts en todas las peticiones fetch
- Usar AbortController para cancelar peticiones colgadas
- En Windows, usar `taskkill /F /PID` para matar procesos
- El servidor frontend debe ser silencioso (override log_message)
- La aplicación debe funcionar en Windows, Linux y Mac

Este sistema es ideal para aplicaciones locales que necesitan controlar su ciclo de vida basado en la actividad del navegador.