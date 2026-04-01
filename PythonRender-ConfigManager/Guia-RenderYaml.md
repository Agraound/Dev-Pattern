# 🧩 Guía simple: render.yaml + Python

---

## 🚀 Estructura mínima

```yaml
services:
  - name: mi-app
    type: web
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
```

---

## 🐍 Definir versión de Python

### ✅ Método recomendado: variables de entorno

En las enviroments vars crear 
```txt
PYTHON_VERSION = python-3.11.9
```


### ✅ Método recomendado: runtime.txt

Crear archivo en la raíz del repo:

```txt
python-3.11.9
```

---

### 🔁 Alternativa: .python-version

```txt
3.11.9
```

---

## ⚙️ Template base recomendado

```yaml
services:
  - name: api-python
    type: web
    runtime: python
    plan: free
    region: oregon

    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app

    autoDeployTrigger: commit

    envVars:
      - key: NODE_ENV
        value: production
```

---

## 🗄️ Base de datos (Postgres)

```yaml
databases:
  - name: mi-db
    plan: free
```

Conexión:

```yaml
envVars:
  - key: DATABASE_URL
    fromDatabase:
      name: mi-db
      property: connectionString
```

---

## 🔗 Multi-servicio

```yaml
services:
  - name: api
    type: web
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app

  - name: worker
    type: worker
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: python worker.py


databases:
  - name: main-db
```

---

## 🐳 Docker (control total)

```dockerfile
FROM python:3.11.9
```

```yaml
services:
  - name: mi-app
    type: web
    runtime: docker
    dockerfilePath: ./Dockerfile
```

---

## 🔐 Variables de entorno

```yaml
envVars:
  - key: API_KEY
    sync: false

  - key: JWT_SECRET
    generateValue: true
```

---

## 🧠 Tips rápidos

* No hardcodear secretos → usar `sync: false`
* Usar `runtime.txt` para fijar Python
* Si falla deploy → revisar `startCommand`
* Para persistencia → usar DB externa (ej: Supabase)

---

## 🧬 Resumen mental

```
render.yaml =
  servicios
  + bases de datos
  + variables
  + deploy
```
