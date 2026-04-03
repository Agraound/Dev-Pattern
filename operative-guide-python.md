# Guía Operativa: Arquitectura Limpia en Python

## 📐 Estructura de Capas

```
project/
├── domain/           # Reglas de negocio puras
│   ├── entities/     # Modelos del dominio
│   ├── services/     # Lógica de dominio
│   └── interfaces/   # Contratos (puertos)
│
├── application/      # Casos de uso y orquestación
│   └── use_cases/    # Flujos de negocio
│
├── infrastructure/   # Implementaciones técnicas
│   ├── database/     # Repositorios concretos
│   ├── api/          # Clientes HTTP
│   ├── files/        # Sistema de archivos
│   └── logging/      # Logs
│
└── interfaces/       # Puntos de entrada
    ├── cli/          # Interfaz de línea de comandos
    ├── web/          # API REST / GraphQL
    └── ui/           # Interfaz gráfica (Flet, etc)
```

```
┌────────────────────┐
│ UI/CLI/API         │ ← Puntos de entrada
├────────────────────┤
│ Application        │ ← Casos de uso (orquestación)
├────────────────────┤
│ Domain             │ ← Reglas puras de negocio
├────────────────────┤
│ Infrastructure     │ ← DB, API, Files, Logs
└────────────────────┘
```

---

## 🎯 Regla de Oro: ¿Dónde va este código?

**Antes de escribir código, preguntate:**

| Pregunta | Respuesta | Capa |
|----------|-----------|------|
| ¿Es una **regla de negocio**? | "El precio no puede ser negativo" | `domain/` |
| ¿Es un **flujo completo**? | "Crear usuario + enviar email + log" | `application/` |
| ¿Es **tecnología concreta**? | PostgreSQL, FastAPI, archivos JSON | `infrastructure/` |
| ¿Es **punto de entrada**? | CLI, botón UI, endpoint HTTP | `interfaces/` |

### ⚠️ Regla Anti-Deuda

**Si mezclás dos categorías en un archivo → estás generando deuda técnica.**

Ejemplo de violación:
```python
# ❌ MAL: Mezclando dominio + infraestructura
class UserService:
    def create_user(self, name):
        user = User(name)  # dominio
        db.session.add(user)  # infraestructura
        db.session.commit()  # infraestructura
```

Correcto:
```python
# ✅ BIEN: Dominio puro
class UserService:
    def create_user(self, name):
        return User(name)

# ✅ BIEN: Caso de uso orquesta
class CreateUserUseCase:
    def __init__(self, user_repository):
        self.user_repository = user_repository
    
    def execute(self, name):
        user = UserService().create_user(name)
        self.user_repository.save(user)
        return user
```

---

## 🚀 Metodología para Nuevas Features

### Proceso Paso a Paso (Orden Obligatorio)

#### **Paso 1: Definir Caso de Uso** (`application/`)

Define **qué** debe hacer la feature, no **cómo**.

```python
# application/use_cases/generate_dialogue.py

class GenerateDialogueUseCase:
    """
    Caso de uso: Generar diálogo entre dos personajes.
    
    Responsabilidades:
    - Validar entrada
    - Invocar generación de IA
    - Registrar log
    - Guardar resultado
    """
    
    def __init__(self, ai_service, dialogue_repository, logger):
        self.ai_service = ai_service
        self.dialogue_repository = dialogue_repository
        self.logger = logger
    
    def execute(self, character_a, character_b, context):
        # Orquestación del flujo
        self.logger.info("Iniciando generación de diálogo")
        
        dialogue = self.ai_service.generate(character_a, character_b, context)
        
        saved_dialogue = self.dialogue_repository.save(dialogue)
        
        self.logger.info(f"Diálogo generado: {saved_dialogue.id}")
        
        return saved_dialogue
```

**Características del caso de uso:**
- ✅ Recibe dependencias inyectadas
- ✅ Orquesta servicios de dominio e infraestructura
- ✅ Una clase = una responsabilidad
- ✅ Sin detalles técnicos (DB, API)

---

#### **Paso 2: Definir Entidades y Reglas** (`domain/`)

Define las **reglas de negocio puras**.

```python
# domain/entities/dialogue.py

from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass
class DialogueLine:
    character: str
    text: str
    timestamp: datetime

class Dialogue:
    """Entidad de dominio: Diálogo"""
    
    def __init__(self, character_a: str, character_b: str):
        self.id = None
        self.character_a = character_a
        self.character_b = character_b
        self.lines: List[DialogueLine] = []
        self.created_at = datetime.now()
    
    def add_line(self, character: str, text: str):
        """Regla: solo personajes válidos pueden hablar"""
        if character not in [self.character_a, self.character_b]:
            raise ValueError(f"Personaje inválido: {character}")
        
        if not text.strip():
            raise ValueError("El texto no puede estar vacío")
        
        line = DialogueLine(character, text, datetime.now())
        self.lines.append(line)
    
    def get_line_count(self) -> int:
        """Regla de negocio"""
        return len(self.lines)
```

```python
# domain/services/dialogue_validator.py

class DialogueValidator:
    """Servicio de dominio: validaciones complejas"""
    
    @staticmethod
    def is_balanced(dialogue) -> bool:
        """Regla: el diálogo debe estar balanceado"""
        count_a = sum(1 for line in dialogue.lines if line.character == dialogue.character_a)
        count_b = sum(1 for line in dialogue.lines if line.character == dialogue.character_b)
        
        return abs(count_a - count_b) <= 2
```

**Características del dominio:**
- ✅ Sin dependencias externas (DB, API, archivos)
- ✅ Solo lógica de negocio
- ✅ Testeable sin mocks
- ✅ Sin I/O

---

#### **Paso 3: Escribir Tests del Caso de Uso**

```python
# tests/application/test_generate_dialogue_use_case.py

import pytest
from application.use_cases.generate_dialogue import GenerateDialogueUseCase
from domain.entities.dialogue import Dialogue

class MockAIService:
    def generate(self, char_a, char_b, context):
        dialogue = Dialogue(char_a, char_b)
        dialogue.add_line(char_a, "Hola")
        dialogue.add_line(char_b, "¿Cómo estás?")
        return dialogue

class MockRepository:
    def save(self, dialogue):
        dialogue.id = 123
        return dialogue

class MockLogger:
    def info(self, msg):
        pass

def test_generate_dialogue_use_case():
    # Arrange
    use_case = GenerateDialogueUseCase(
        ai_service=MockAIService(),
        dialogue_repository=MockRepository(),
        logger=MockLogger()
    )
    
    # Act
    result = use_case.execute("Alice", "Bob", "Reunión casual")
    
    # Assert
    assert result.id == 123
    assert result.character_a == "Alice"
    assert result.character_b == "Bob"
    assert result.get_line_count() == 2
```

**Tests primero:**
- ✅ Validar flujo completo
- ✅ Usar mocks simples
- ✅ Verificar comportamiento

---

#### **Paso 4: Implementar Infraestructura**

```python
# infrastructure/ai/openai_service.py

from domain.entities.dialogue import Dialogue
import openai

class OpenAIDialogueService:
    """Implementación concreta usando OpenAI"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        openai.api_key = api_key
    
    def generate(self, character_a, character_b, context):
        prompt = f"Genera diálogo entre {character_a} y {character_b} en contexto: {context}"
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        
        dialogue = Dialogue(character_a, character_b)
        # Parsear respuesta y agregar líneas...
        return dialogue
```

```python
# infrastructure/database/json_dialogue_repository.py

import json
from pathlib import Path
from domain.entities.dialogue import Dialogue

class JSONDialogueRepository:
    """Implementación concreta usando archivos JSON"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
    
    def save(self, dialogue: Dialogue):
        # Serializar y guardar
        data = {
            "character_a": dialogue.character_a,
            "character_b": dialogue.character_b,
            "lines": [
                {"character": line.character, "text": line.text}
                for line in dialogue.lines
            ]
        }
        
        with open(self.file_path, 'w') as f:
            json.dump(data, f)
        
        dialogue.id = str(self.file_path)
        return dialogue
```

**Características de infraestructura:**
- ✅ Implementa interfaces de dominio
- ✅ Tecnología concreta (OpenAI, JSON, PostgreSQL)
- ✅ Intercambiable sin afectar dominio

---

#### **Paso 5: Conectar Interfaz**

```python
# interfaces/cli/main.py

from application.use_cases.generate_dialogue import GenerateDialogueUseCase
from infrastructure.ai.openai_service import OpenAIDialogueService
from infrastructure.database.json_dialogue_repository import JSONDialogueRepository
from infrastructure.logging.console_logger import ConsoleLogger

def main():
    # Dependency Injection manual
    ai_service = OpenAIDialogueService(api_key="sk-...")
    repository = JSONDialogueRepository("dialogues.json")
    logger = ConsoleLogger()
    
    use_case = GenerateDialogueUseCase(
        ai_service=ai_service,
        dialogue_repository=repository,
        logger=logger
    )
    
    # Interfaz CLI
    print("=== Generador de Diálogos ===")
    char_a = input("Personaje A: ")
    char_b = input("Personaje B: ")
    context = input("Contexto: ")
    
    result = use_case.execute(char_a, char_b, context)
    
    print(f"\n✅ Diálogo generado (ID: {result.id})")
    for line in result.lines:
        print(f"{line.character}: {line.text}")

if __name__ == "__main__":
    main()
```

**Características de interfaces:**
- ✅ Solo invoca casos de uso
- ✅ Maneja input/output del usuario
- ✅ Configura dependencias
- ✅ Sin lógica de negocio

---

## 📦 Imports y Ejecución

### ✅ Siempre Imports Absolutos

```python
# ✅ CORRECTO
from domain.entities.user import User
from domain.services.user_validator import UserValidator
from application.use_cases.create_user import CreateUserUseCase
from infrastructure.database.postgres_repository import PostgresUserRepository

# ❌ INCORRECTO
from ..domain.entities.user import User  # NO
from .services.validator import UserValidator  # NO
```

### 🏃 Ejecución desde Raíz del Proyecto

```bash
# ✅ CORRECTO: Ejecutar desde raíz
python -m interfaces.cli.main
python -m interfaces.web.app
python -m tests.run_all

# ❌ INCORRECTO: Ejecutar archivos internos
python domain/entities/user.py  # NO
python application/use_cases/create_user.py  # NO
```

**Estructura del proyecto:**
```
my_project/
├── domain/
├── application/
├── infrastructure/
├── interfaces/
│   ├── cli/
│   │   └── main.py
│   └── web/
│       └── app.py
└── README.md

# Ejecutar:
$ cd my_project
$ python -m interfaces.cli.main
```

---

## 🔄 Migrar Script Existente a Arquitectura Profesional

### Proceso de Refactorización

**Si ya tenés un script funcionando:**

#### Script Original (monolítico)
```python
# script.py - TODO EN UN ARCHIVO

import openai
import json

openai.api_key = "sk-..."

def generate_dialogue(char_a, char_b):
    # Lógica mezclada
    prompt = f"Diálogo entre {char_a} y {char_b}"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    
    result = response.choices[0].message.content
    
    with open("output.json", "w") as f:
        json.dump({"dialogue": result}, f)
    
    print("✅ Guardado")

generate_dialogue("Alice", "Bob")
```

#### Paso 1: Extraer Dominio

```python
# domain/entities/dialogue.py

class Dialogue:
    def __init__(self, character_a, character_b):
        self.character_a = character_a
        self.character_b = character_b
        self.content = ""
    
    def set_content(self, content: str):
        if not content.strip():
            raise ValueError("Contenido vacío")
        self.content = content
```

#### Paso 2: Crear Caso de Uso

```python
# application/use_cases/generate_dialogue.py

class GenerateDialogueUseCase:
    def __init__(self, ai_service, repository):
        self.ai_service = ai_service
        self.repository = repository
    
    def execute(self, char_a, char_b):
        dialogue = Dialogue(char_a, char_b)
        content = self.ai_service.generate(char_a, char_b)
        dialogue.set_content(content)
        self.repository.save(dialogue)
        return dialogue
```

#### Paso 3: Implementar Infraestructura

```python
# infrastructure/ai/openai_service.py

import openai

class OpenAIService:
    def __init__(self, api_key):
        openai.api_key = api_key
    
    def generate(self, char_a, char_b):
        response = openai.ChatCompletion.create(...)
        return response.choices[0].message.content

# infrastructure/database/json_repository.py

import json

class JSONRepository:
    def save(self, dialogue):
        with open("output.json", "w") as f:
            json.dump({
                "char_a": dialogue.character_a,
                "char_b": dialogue.character_b,
                "content": dialogue.content
            }, f)
```

#### Paso 4: Nueva Interfaz

```python
# interfaces/cli/main.py

from application.use_cases.generate_dialogue import GenerateDialogueUseCase
from infrastructure.ai.openai_service import OpenAIService
from infrastructure.database.json_repository import JSONRepository

def main():
    use_case = GenerateDialogueUseCase(
        ai_service=OpenAIService("sk-..."),
        repository=JSONRepository()
    )
    
    result = use_case.execute("Alice", "Bob")
    print("✅ Guardado")

if __name__ == "__main__":
    main()
```

**No reescribir todo. Refactorizar progresivamente.**

---

## ✅ Checklist por Capa

### `domain/` - Reglas Puras

- [ ] Sin dependencias externas (no `import requests`, no `import sqlite3`)
- [ ] Sin I/O (no archivos, no DB, no red)
- [ ] Solo lógica de negocio
- [ ] Testeable sin mocks complejos
- [ ] Entidades ricas en comportamiento
- [ ] Servicios de dominio para lógica compleja

**Ejemplo válido:**
```python
class Order:
    def calculate_total(self):
        return sum(item.price * item.quantity for item in self.items)
```

**Ejemplo inválido:**
```python
class Order:
    def save_to_database(self):  # ❌ I/O en dominio
        db.session.add(self)
```

---

### `application/` - Casos de Uso

- [ ] Orquesta dominio + infraestructura
- [ ] Define flujos completos (happy path + errores)
- [ ] Recibe dependencias inyectadas (constructor)
- [ ] Un caso de uso = una responsabilidad
- [ ] Sin detalles técnicos (SQL, HTTP, filesystem)
- [ ] Método `execute()` o `handle()`

**Ejemplo válido:**
```python
class CreateOrderUseCase:
    def __init__(self, order_repository, email_service):
        self.order_repository = order_repository
        self.email_service = email_service
    
    def execute(self, customer_id, items):
        order = Order(customer_id, items)
        saved_order = self.order_repository.save(order)
        self.email_service.send_confirmation(order)
        return saved_order
```

---

### `infrastructure/` - Implementaciones

- [ ] Implementa interfaces definidas en dominio
- [ ] Tecnología concreta (PostgreSQL, Redis, OpenAI)
- [ ] Intercambiable sin cambiar dominio
- [ ] Maneja errores técnicos (conexión, timeout)
- [ ] Configuración externa (env vars, configs)

**Ejemplo:**
```python
class PostgresOrderRepository:
    def save(self, order: Order):
        # SQL específico aquí
        pass

class MongoOrderRepository:
    def save(self, order: Order):
        # MongoDB específico aquí
        pass
```

---

### `interfaces/` - Puntos de Entrada

- [ ] Solo invoca casos de uso
- [ ] Maneja input del usuario (validación básica)
- [ ] Presenta output formateado
- [ ] No contiene lógica de negocio
- [ ] Configura dependencias (DI container)

**Ejemplo:**
```python
@app.post("/orders")
def create_order(request: OrderRequest):
    use_case = CreateOrderUseCase(repo, email)
    result = use_case.execute(request.customer_id, request.items)
    return {"order_id": result.id}
```

---

## 🚨 Señales de Alerta (Code Smells)

### ❌ Estás haciendo algo mal si:

1. **Domain importa de Infrastructure**
   ```python
   # domain/entities/user.py
   from infrastructure.database import db  # ❌ NUNCA
   ```

2. **Caso de uso escribe directamente en DB**
   ```python
   class CreateUserUseCase:
       def execute(self, name):
           db.execute("INSERT INTO users...")  # ❌ NO
   ```

3. **UI contiene lógica de negocio**
   ```python
   # interfaces/web/app.py
   @app.post("/users")
   def create_user(name):
       if len(name) < 3:  # ❌ Validación en UI
           return error
       user = User(name)
       user.calculate_score()  # ❌ Lógica en UI
   ```

4. **Necesitás mocks complejos para testear dominio**
   ```python
   def test_calculate_price():
       mock_db = MagicMock()  # ❌ Dominio no debe depender de DB
       mock_api = MagicMock()
       order.calculate_price(mock_db, mock_api)
   ```

5. **Archivos gigantes (>300 líneas)**
   - Violación del Single Responsibility Principle
   - Mezcla de responsabilidades

---

## 💡 Regla Mental (Pausa Obligatoria)

### Antes de escribir código, preguntate:

> **"¿Estoy escribiendo una REGLA, una ORQUESTACIÓN o una IMPLEMENTACIÓN TÉCNICA?"**

| Tipo | Pregunta de Validación | Capa |
|------|------------------------|------|
| **REGLA** | ¿Es verdad sin importar la tecnología? | `domain/` |
| **ORQUESTACIÓN** | ¿Coordina múltiples pasos? | `application/` |
| **IMPLEMENTACIÓN** | ¿Depende de una biblioteca externa? | `infrastructure/` |
| **ENTRADA/SALIDA** | ¿Interactúa con el usuario? | `interfaces/` |

**Si no lo sabés → PAUSA y definilo primero.**

---

## 📊 Flujo de Dependencias

### Principio Fundamental

**Cada capa solo conoce la capa inferior. Nunca al revés.**

```
interfaces ──→ application ──→ domain
                   ↓
            infrastructure
```

### Dependency Inversion Principle

```python
# ✅ CORRECTO: Domain define la interfaz

# domain/repositories/user_repository.py
class UserRepository(ABC):
    @abstractmethod
    def save(self, user: User):
        pass

# infrastructure/database/postgres_user_repository.py
class PostgresUserRepository(UserRepository):  # Implementa la interfaz
    def save(self, user: User):
        # PostgreSQL específico
        pass

# application/use_cases/create_user.py
class CreateUserUseCase:
    def __init__(self, user_repository: UserRepository):  # Depende de abstracción
        self.user_repository = user_repository
```

**Domain define contratos, Infrastructure los implementa.**

---

## 🎓 Ejemplos Completos

### Feature: "Enviar Notificación de Pedido"

#### 1. Domain
```python
# domain/entities/notification.py
class Notification:
    def __init__(self, recipient: str, message: str):
        if not recipient:
            raise ValueError("Destinatario requerido")
        self.recipient = recipient
        self.message = message
        self.sent_at = None
```

#### 2. Application
```python
# application/use_cases/send_order_notification.py
class SendOrderNotificationUseCase:
    def __init__(self, notification_service, logger):
        self.notification_service = notification_service
        self.logger = logger
    
    def execute(self, order_id: str, customer_email: str):
        self.logger.info(f"Enviando notificación para pedido {order_id}")
        
        notification = Notification(
            recipient=customer_email,
            message=f"Tu pedido {order_id} ha sido confirmado"
        )
        
        self.notification_service.send(notification)
        
        self.logger.info(f"Notificación enviada a {customer_email}")
```

#### 3. Infrastructure
```python
# infrastructure/email/smtp_notification_service.py
import smtplib

class SMTPNotificationService:
    def __init__(self, smtp_host: str, smtp_port: int):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
    
    def send(self, notification: Notification):
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.sendmail(
                "noreply@example.com",
                notification.recipient,
                notification.message
            )
```

#### 4. Interface
```python
# interfaces/web/api.py
from fastapi import FastAPI

app = FastAPI()

@app.post("/orders/{order_id}/notify")
def notify_order(order_id: str, email: str):
    use_case = SendOrderNotificationUseCase(
        notification_service=SMTPNotificationService("smtp.gmail.com", 587),
        logger=ConsoleLogger()
    )
    
    use_case.execute(order_id, email)
    
    return {"status": "notificación enviada"}
```

---

## 🔧 Herramientas Útiles

### Testing
```bash
pytest tests/
pytest tests/domain/  # Solo dominio
pytest tests/application/  # Solo casos de uso
```

### Linting
```bash
pylint domain/ application/ infrastructure/ interfaces/
mypy .  # Type checking
```

### Coverage
```bash
pytest --cov=domain --cov=application
```

---

## 📚 Resumen Ejecutivo

### Para cada nueva feature:

1. ✅ **Definir caso de uso** (application)
2. ✅ **Definir entidades/reglas** (domain)
3. ✅ **Escribir tests**
4. ✅ **Implementar infraestructura**
5. ✅ **Conectar interfaz**

### Mantra del desarrollador:

> **"Regla → Domain | Flujo → Application | Tecnología → Infrastructure | Entrada → Interface"**

### Antes de commitear:

- [ ] ¿Cada archivo tiene una sola responsabilidad?
- [ ] ¿Domain no importa nada de infrastructure?
- [ ] ¿Casos de uso reciben dependencias inyectadas?
- [ ] ¿Interfaces solo invocan casos de uso?
- [ ] ¿Tests pasan?

---

**Arquitectura limpia = Código mantenible, testeable y escalable.**

**Inversión inicial → Beneficio a largo plazo.**
