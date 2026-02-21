# AETHERYON Dev Pattern

## Tabla Comparativa de Niveles

| Nivel | Nombre | Equipo | Complejidad | Testing | MVVM | Cuándo usarlo |
|-------|--------|--------|-------------|---------|------|---------------|
| 1 | Standalone Script | 1 dev | Mínima | No | No | Prototipo, validación rápida, scripts de automatización |
| 2 | BF | 1-2 devs | Baja | No | No | Proyecto pequeño con lógica separada de presentación |
| 3 | AUDI | 2-4 devs | Media | Opcional | No | Proyecto con dominio definido y crecimiento esperado |
| 4 | AUDDITS | 3-6 devs | Alta | Sí | No | Producto en producción con múltiples módulos |
| 5 | AUDDITS + MVVM | 4+ devs | Muy alta | Sí | Sí | Sistema complejo con UI rica y múltiples vistas |

---

## Nivel 1 — Standalone Script
Proyecto desarrollado en un único script completamente funcional.

### Cuándo escalar al Nivel 2
Escalar cuando el script supere las 200 líneas, cuando la lógica de negocio y la presentación se mezclen en las mismas funciones, o cuando otro desarrollador necesite trabajar en paralelo.

### Principios del Nivel 1
- Todo en un solo archivo es aceptable mientras el alcance sea claro.
- Preferir funciones puras y evitar estado global innecesario.
- Documentar la intención del script al inicio del archivo.

### Antipatrones a evitar
```python
# ❌ MAL — lógica mezclada con presentación
def calcular_descuento(precio, porcentaje):
    resultado = precio - (precio * porcentaje / 100)
    print(f"Descuento aplicado: {resultado}")  # mezcla cálculo con output
    return resultado

# ✅ BIEN — responsabilidades separadas aunque estén en el mismo archivo
def calcular_descuento(precio, porcentaje):
    return precio - (precio * porcentaje / 100)

def mostrar_resultado(resultado):
    print(f"Descuento aplicado: {resultado}")
```

### Modos Operativos del Sistema

El patrón en este nivel permite validar los siguientes modos:

- Script Mode → Validación rápida y prototipo funcional.
- CLI Mode → Ejecución interactiva por comandos.
- Batch Mode → Automatización por parámetros (--flags).
- UI Mode → Orquestación profesional mediante interfaz gráfica.

Flujo de dependencias conceptual:
Interfaces → Application → Domain.
Infrastructure depende de contratos del Domain, pero Domain nunca depende de Infrastructure.


Proyecto desarrollado en un único script completamente funcional.

```
proyecto/
│
└── proyecto.py
```

---

## Nivel 2 — Patrón BF (Backend–Frontend)
Separación básica entre lógica y presentación.

### Cuándo escalar al Nivel 3
Escalar cuando aparezcan múltiples entidades de negocio con reglas propias, cuando Infrastructure comience a crecer (base de datos, APIs externas), o cuando el equipo crezca y la separación en dos archivos ya no alcance para dividir el trabajo.

### Principios del Nivel 2
- `Backend.py` contiene toda la lógica de negocio y acceso a datos.
- `Frontend.py` solo consume métodos públicos del backend.
- El frontend nunca importa librerías de acceso a datos directamente.

### Antipatrones a evitar
```python
# ❌ MAL — el frontend accede directamente a la base de datos
# En Frontend.py
import sqlite3
conn = sqlite3.connect("db.sqlite")
usuarios = conn.execute("SELECT * FROM usuarios").fetchall()

# ✅ BIEN — el frontend delega al backend
# En Frontend.py
from Backend import Backend
backend = Backend()
usuarios = backend.obtener_usuarios()
```

```
proyecto/
│
├── Backend.py
└── Frontend.py
```

---

## Nivel 3 — Patrón AUDI
Arquitectura por capas fundamentales.

### Cuándo escalar al Nivel 4
Escalar cuando el equipo necesite pruebas automatizadas, cuando haya scripts de migración o seed data recurrentes, o cuando la documentación interna se vuelva necesaria para onboarding.

### Diagrama de Dependencias

```
User_Interface
      │
      ▼
 Application  ←──────────────────┐
      │                          │
      ▼                          │
   Domain               Infrastructure
  (núcleo puro,            (I/O, DB, APIs)
 sin dependencias)
```

**Regla de oro:** las flechas solo apuntan hacia abajo o hacia el centro. Nunca hacia arriba.

### Asincronía en AUDI

La asincronía no es una capa, es una decisión técnica que aplica en lugares específicos:

```python
# Infrastructure — async para I/O
class RepositorioUsuarioSQL:
    async def obtener_por_id(self, id: int) -> Usuario:
        async with self.session() as db:
            return await db.get(UsuarioModel, id)

# Application — propaga async según necesidad
class ServicioUsuario:
    async def obtener_usuario(self, id: int) -> UsuarioDTO:
        usuario = await self.repositorio.obtener_por_id(id)
        return UsuarioDTO.desde_entidad(usuario)

# Domain — siempre sync (lógica pura, sin I/O)
class Usuario:
    def aplicar_descuento(self, porcentaje: float) -> float:
        if porcentaje < 0 or porcentaje > 100:
            raise DescuentoInvalidoError(porcentaje)
        return self.precio * (1 - porcentaje / 100)
```

**Regla:** si una función en Domain necesita `async`, es una señal de que algo de Infrastructure se filtró hacia arriba.

### Principios Arquitectónicos Fundamentales

Modularidad por responsabilidad, no por tipo técnico. Cada módulo debe tener una única razón para cambiar.

Regla central:
- Si decide → Domain.
- Si coordina → Application.
- Si ejecuta I/O o integra tecnología → Infrastructure.
- Si representa estado o muestra información → Presentation / User_Interface.

La asincronía no es una capa arquitectónica sino una decisión técnica:
- I/O → async.
- Cálculo puro → sync.

Separación crítica:
- Identidad del sistema, reglas y políticas deben estar desacopladas del proveedor tecnológico.
- El proveedor externo puede cambiar sin alterar reglas.
- Las decisiones deben poder testearse sin red.

Criterios de salud arquitectónica:
- ¿Puedo cambiar proveedor sin tocar reglas?
- ¿Puedo cambiar reglas sin tocar infraestructura?
- ¿Puedo testear dominio sin internet?
- ¿La UI conoce lógica que no debería?

Un sistema funcional ejecuta.
Un sistema evolutivo se adapta.
La diferencia es la separación clara de responsabilidades.


Arquitectura por capas fundamentales.

```
proyecto/
│
├── backend.py
├── bootstrap.py
│
├── Application/
│   ├── __init__.py
│   ├── servicios/
│   ├── dto/
│   └── interfaces/
│
├── Domain/
│   ├── __init__.py
│   ├── entidades/
│   ├── value_objects/
│   ├── eventos/
│   └── excepciones/
│
├── Infrastructure/
│   ├── __init__.py
│   ├── persistencia/
│   ├── servicios_externos/
│   └── logging/
│
└── User_Interface/
    ├── __init__.py
    ├── layout.py
    └── vistas/
```

---

## Nivel 4 — Patrón AUDDITS
Extensión productiva con testing, scripts y documentación.

### Cuándo escalar al Nivel 5
Escalar cuando la UI se vuelva compleja con múltiples vistas y estado compartido, cuando los ViewModels necesiten ser testeables sin levantar la interfaz, o cuando se prevea reutilizar la lógica de presentación en múltiples frameworks.

### Reglas de Desarrollo

**Regla #1 — Responsabilidad Única**
- Cada archivo tiene una única responsabilidad bien definida.
- Cada clase tiene una sola razón para cambiar.
- Cada función hace una sola cosa y la hace correctamente.

Antipatrón frecuente: un servicio que valida, persiste y envía email en el mismo método.
```python
# ❌ MAL — tres responsabilidades en un método
class ServicioUsuario:
    def registrar(self, datos):
        if not datos.email:           # validación
            raise ValueError()
        self.db.guardar(datos)        # persistencia
        self.email.enviar_bienvenida() # notificación

# ✅ BIEN — cada responsabilidad en su lugar
class ServicioRegistro:
    def registrar(self, dto: RegistroDTO) -> Usuario:
        usuario = self.validador.validar(dto)
        self.repositorio.guardar(usuario)
        self.eventos.publicar(UsuarioRegistrado(usuario.id))
        return usuario
```

**Regla #2 — Dependencias Direccionales**
- Domain no depende de ninguna otra capa.
- Application solo depende de Domain.
- Infrastructure puede depender de Application y Domain.
- User_Interface depende de Application, nunca directamente de Infrastructure.

**Regla #3 — Nomenclatura**
- Clases → PascalCase.
- Métodos y variables → snake_case.
- Constantes → MAYUSCULAS.
- Archivos → snake_case.py.

**Regla #4 — Importaciones Correctas**
```python
from Domain.entidades import Usuario
from Application.dto import UsuarioDTO
from Infrastructure.persistencia.repositorios import RepositorioUsuarioSQL
```

Evitar:
```python
from ..Domain import Usuario
from Application.servicios import *
```

**Regla #5 — Manejo de Errores**
- Excepciones de negocio en Domain/excepciones/.
- Excepciones técnicas en Infrastructure.
- La UI solo expone mensajes amigables.

**Regla #6 — Inyección de Dependencias**
```python
# ✅ BIEN — dependencia inyectada, testeable
class ServicioUsuario:
    def __init__(self, repositorio: RepositorioUsuario):
        self.repositorio = repositorio

# ❌ MAL — dependencia oculta, imposible de mockear
class ServicioUsuario:
    def __init__(self):
        self.repositorio = RepositorioUsuarioSQL()  # acoplado al proveedor concreto
```

Evitar dependencias ocultas instanciadas dentro de la clase.

**Regla #7 — DTOs vs Entidades**
- Las entidades de dominio no se exponen directamente a la UI.
- Los DTOs transportan datos entre capas.
- Las entidades contienen lógica; los DTOs solo estructura.

**Regla #8 — backend.py como Adaptador**
- Actúa como capa de adaptación entre UI y Application.
- Configura dependencias.
- Expone métodos públicos limpios para la interfaz.

**Regla #9 — bootstrap.py como Orquestador**
- Configura logging.
- Inicializa Backend.
- Levanta la UI o modo operativo correspondiente.

**Regla #10 — Pruebas**
- Cada módulo tiene su archivo de test.
- Pruebas independientes y repetibles.
- Uso de mocks para servicios externos.
- Cobertura recomendada ≥ 80%.

**Regla #11 — Documentación**
- Docstrings obligatorios en servicios públicos.
- Tipado explícito en funciones críticas.

**Regla #12 — Git Workflow**
- main → Producción.
- develop → Integración.
- feature/* → Nuevas funcionalidades.
- hotfix/* → Correcciones urgentes.
- release/* → Preparación de versiones.

### Flujo de Inicialización

```bash
python -m venv venv
pip install -r requirements.txt
python bootstrap.py
pytest Tests/
python Scripts/seed_data.py
```


```
proyecto/
│
├── backend.py
├── bootstrap.py
│
├── Application/
├── Domain/
├── Infrastructure/
├── User_Interface/
│
├── Tests/
│   ├── __init__.py
│   ├── test_domain/
│   ├── test_application/
│   └── test_infrastructure/
│
├── Scripts/
│   ├── __init__.py
│   ├── migraciones.py
│   └── seed_data.py
│
└── Docs/
    ├── README.md
    └── arquitectura.md
```

---

## Nivel 5 — Patrón AUDDITS + MVVM
Extensión completa con separación de presentación mediante MVVM.

### Cuándo NO usar MVVM
MVVM agrega overhead real. No está justificado cuando:
- La UI tiene una sola vista sin estado complejo.
- El proyecto es interno o de vida corta.
- El equipo no tiene experiencia con el patrón (curva de aprendizaje alta).
- No hay necesidad de testear la lógica de presentación por separado.

En esos casos, quedarse en Nivel 4 con una `User_Interface` simple es una decisión válida.

Capas totales:
- Domain
- Application
- Infrastructure
- User_Interface
- Scripts
- Tests
- Docs
- Presentation

Archivos raíz:
- backend.py
- bootstrap.py
- config.py
- requirements.txt
- .env
- .gitignore

### Reglas MVVM

**Regla #13 — Separación MVVM**
Vista → ViewModel → Modelo.
- La Vista contiene solo widgets y lógica de presentación.
- El ViewModel contiene estado observable y lógica de UI.
- El Modelo contiene datos (UI o negocio según capa).
- La Vista nunca accede directamente a Domain o Infrastructure.

**Regla #14 — ViewModelBase obligatorio**
- Todos los ViewModels heredan de `ViewModelBase`.
- Deben notificar cambios mediante un sistema observable.
- El estado (`ocupado`, `mensaje_estado`, errores) vive en el ViewModel.
- No deben importar nada de `User_Interface`.

**Regla #15 — Modelos de UI**
- Son `dataclasses` simples.
- No contienen lógica de negocio.
- Pueden contener validaciones de formato (no reglas de negocio).
- Deben poder convertirse a DTO (`to_dict()` o adaptador similar).

**Regla #16 — ViewModels Específicos**
- Encapsulan filtros, selección, estado de edición.
- Transforman DTOs en modelos de UI.
- Coordinan llamadas al backend.
- Nunca contienen acceso directo a base de datos.

**Regla #17 — Comandos**
- Las acciones complejas se encapsulan en clases `Comando*`.
- Deben exponer `ejecutar()`.
- Opcionalmente pueden implementar `deshacer()`.
- Deben verificar `puede_ejecutar()` antes de actuar.

**Regla #18 — Binding Vista–ViewModel**
- La Vista se suscribe a cambios del ViewModel (Observer).
- El binding es bidireccional cuando corresponde.
- La Vista nunca manipula directamente colecciones internas del ViewModel.

**Regla #19 — Backend como Proveedor de ViewModels**
- backend.py inicializa y expone los ViewModels.
- Centraliza la configuración de dependencias.
- La UI obtiene los ViewModels desde el backend.

**Regla #20 — Bootstrap Integrado**
- bootstrap.py obtiene ViewModels desde backend.
- Crea las vistas inyectando sus ViewModels.
- No debe contener lógica de negocio.

---

### Asincronía en MVVM

El estado `ocupado` y `mensaje_estado` del ViewModel son el puente entre las operaciones async y la UI reactiva:

```python
class UsuarioViewModel(ViewModelBase):
    async def cargar_usuarios(self):
        self.ocupado = True
        self.mensaje_estado = "Cargando usuarios..."
        self.notificar_cambio("ocupado")
        try:
            dtos = await self.backend.obtener_usuarios()
            self.usuarios = [UIUsuario.desde_dto(dto) for dto in dtos]
            self.mensaje_estado = f"{len(self.usuarios)} usuarios cargados"
        except Exception as e:
            self.mensaje_estado = f"Error: {str(e)}"
        finally:
            self.ocupado = False
            self.notificar_cambio("ocupado")
            self.notificar_cambio("usuarios")
            self.notificar_cambio("mensaje_estado")
```

**Regla:** el ViewModel nunca bloquea el hilo principal. Si la operación es async, el estado `ocupado` debe activarse antes del await y desactivarse en el bloque `finally`.

### Beneficios del MVVM

- Separación clara entre UI y lógica de presentación.
- ViewModels testeables sin interfaz gráfica.
- Reutilización con múltiples frameworks (Tkinter, Qt, Web).
- Estado explícito y centralizado.
- Validación de UI desacoplada de reglas de negocio.

### Checklist MVVM

- El ViewModel hereda de ViewModelBase.
- Las propiedades notifican cambios.
- Los comandos encapsulan acciones.
- Los modelos de UI son simples.
- La Vista no contiene lógica de negocio.
- El ViewModel no importa `User_Interface`.


---

# Migración entre Niveles

Migrar un proyecto entre niveles es un proceso incremental, no una reescritura. El orden importa: mover primero lo que menos impacto tiene en el sistema activo.

## De Nivel 1 a Nivel 2

1. Identificar funciones que interactúan con el usuario (prints, inputs, widgets).
2. Moverlas a `Frontend.py`.
3. Lo que queda (lógica, datos) se convierte en `Backend.py`.
4. El frontend importa al backend. Nunca al revés.

**Señal de que la migración está bien hecha:** se puede ejecutar `Backend.py` directamente en modo script sin que importe nada de presentación.

## De Nivel 2 a Nivel 3

**Orden recomendado:**

1. Crear las carpetas `Domain/`, `Application/`, `Infrastructure/`, `User_Interface/`.
2. Mover primero las entidades con lógica a `Domain/entidades/`.
3. Extraer las interfaces (contratos) de repositorios a `Application/interfaces/`.
4. Mover el acceso a datos a `Infrastructure/persistencia/`.
5. Mover los servicios orquestadores a `Application/servicios/`.
6. La UI existente se convierte en `User_Interface/`.
7. Crear `backend.py` y `bootstrap.py` al final.

**Error frecuente:** empezar por crear carpetas vacías sin mover nada. Migrar entidad por entidad es más seguro que refactorizar todo a la vez.

## De Nivel 3 a Nivel 4

1. Agregar la carpeta `Tests/` con la estructura espejo de las capas.
2. Escribir primero los tests del Domain (los más simples, sin mocks).
3. Agregar tests de Application con mocks de Infrastructure.
4. Crear `Scripts/` para las migraciones existentes que estaban en `bootstrap.py`.
5. Crear `Docs/` con al menos un `README.md` funcional.

**Meta mínima:** alcanzar 80% de cobertura en Domain antes de pasar a Application.

## De Nivel 4 a Nivel 5

1. Crear la carpeta `Presentation/` con `viewmodels/`, `models/`, `commands/`.
2. Crear `ViewModelBase` primero.
3. Migrar la lógica de estado de `User_Interface/` hacia ViewModels, uno por vista.
4. Reemplazar acceso directo al backend desde la UI por llamadas al ViewModel.
5. Agregar `test_presentation/` en Tests.

**No migrar todo a la vez.** Empezar por la vista más compleja (generalmente la principal) y validar el patrón antes de continuar con el resto.

---

# Estructura Completa — Nivel 5


```
proyecto/
│
├── backend.py
├── bootstrap.py
├── config.py
├── requirements.txt
├── .env
├── .gitignore
│
├── Application/
│   ├── __init__.py
│   ├── servicios/
│   │   ├── __init__.py
│   │   ├── servicio_usuario.py
│   │   └── servicio_producto.py
│   ├── dto/
│   │   ├── __init__.py
│   │   ├── usuario_dto.py
│   │   └── producto_dto.py
│   └── interfaces/
│       ├── __init__.py
│       ├── repositorio_usuario.py
│       └── repositorio_producto.py
│
├── Domain/
│   ├── __init__.py
│   ├── entidades/
│   │   ├── __init__.py
│   │   ├── usuario.py
│   │   └── producto.py
│   ├── value_objects/
│   │   ├── __init__.py
│   │   ├── email.py
│   │   └── direccion.py
│   ├── eventos/
│   │   ├── __init__.py
│   │   └── eventos_usuario.py
│   └── excepciones/
│       ├── __init__.py
│       └── excepciones_dominio.py
│
├── Infrastructure/
│   ├── __init__.py
│   ├── persistencia/
│   │   ├── __init__.py
│   │   ├── base_datos/
│   │   │   ├── __init__.py
│   │   │   ├── conexion.py
│   │   │   └── modelos.py
│   │   └── repositorios/
│   │       ├── __init__.py
│   │       ├── repositorio_usuario_sql.py
│   │       └── repositorio_producto_sql.py
│   ├── servicios_externos/
│   │   ├── __init__.py
│   │   ├── api_cliente.py
│   │   └── servicios_email.py
│   └── logging/
│       ├── __init__.py
│       └── logger_config.py
│
├── Presentation/
│   ├── __init__.py
│   ├── viewmodels/
│   │   ├── __init__.py
│   │   ├── viewmodel_base.py
│   │   ├── usuario_viewmodel.py
│   │   ├── producto_viewmodel.py
│   │   ├── login_viewmodel.py
│   │   └── reportes_viewmodel.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── ui_usuario.py
│   │   ├── ui_producto.py
│   │   └── validators.py
│   └── commands/
│       ├── __init__.py
│       ├── comando_base.py
│       ├── comandos_usuario.py
│       └── comandos_navegacion.py
│
├── User_Interface/
│   ├── __init__.py
│   ├── layout.py
│   ├── modals.py
│   ├── styles.py
│   ├── assets/
│   │   ├── imagenes/
│   │   ├── iconos/
│   │   └── fuentes/
│   ├── components/
│   │   ├── __init__.py
│   │   ├── tabla_datos.py
│   │   ├── formulario.py
│   │   ├── barra_herramientas.py
│   │   ├── menu_lateral.py
│   │   └── graficos.py
│   └── vistas/
│       ├── __init__.py
│       ├── vista_principal.py
│       ├── vista_usuarios.py
│       └── vista_reportes.py
│
├── Tests/
│   ├── __init__.py
│   ├── test_domain/
│   ├── test_application/
│   ├── test_infrastructure/
│   ├── test_presentation/
│   │   ├── __init__.py
│   │   ├── test_usuario_viewmodel.py
│   │   └── test_validators.py
│   └── conftest.py
│
├── Scripts/
│   ├── __init__.py
│   ├── migraciones.py
│   ├── seed_data.py
│   └── backup.py
│
└── Docs/
    ├── README.md
    ├── arquitectura.md
    ├── guia_estilo.md
    └── api_referencia.md
```