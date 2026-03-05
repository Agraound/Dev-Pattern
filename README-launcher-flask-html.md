# Flask + HTML Launcher Pattern

Estructura simple para proyectos donde Python maneja la lógica y HTML/JS la interfaz.

```
project/
│
├─ run.py
├─ backend/
│   └─ app.py
└─ frontend/
    └─ index.html
```

---

# run.py

Este script inicia la API y abre el navegador automáticamente.

```python
import threading
import webbrowser
import time

from backend.app import app


def open_browser():
    time.sleep(1)
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    threading.Thread(target=open_browser).start()
    app.run(port=5000, debug=True)
```

---

# backend/app.py

API Flask simple.

```python
from flask import Flask, jsonify, send_from_directory
import os

app = Flask(__name__)

FRONTEND_DIR = os.path.abspath("frontend")


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/api/hello")
def hello():
    return jsonify({
        "message": "Hola desde Flask",
        "status": "ok"
    })
```

---

# frontend/index.html

Interfaz simple que consume la API.

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Flask UI Test</title>
</head>

<body>
<h1>Interfaz HTML conectada a Flask</h1>

<button onclick="callAPI()">Llamar API</button>

<pre id="output"></pre>

<script>
async function callAPI(){

    const res = await fetch('/api/hello');

    const data = await res.json();

    document.getElementById('output').textContent = JSON.stringify(data, null, 2);

}
</script>

</body>
</html>
```

---

# Ejecutar

```
pip install flask
python run.py
```

Esto:

1. Levanta la API Flask.
2. Sirve el HTML.
3. Abre automáticamente el navegador.
4. El frontend puede llamar endpoints `/api/...`.

Este patrón funciona muy bien para:

* herramientas internas
* prototipos
* apps tipo "desktop web"
* interfaces para scripts Python
