# CLI Dev Pattern
> Parte del ecosistema **AETHERYON Dev Pattern**

---

El CLI Dev Pattern es una especialización del patrón AETHERYON para herramientas de línea de comandos que operan sobre sistemas reales: repositorios, proyectos, pipelines, agentes. No reemplaza los niveles arquitectónicos 1–5 — los especializa para cuando el CLI es la herramienta principal y no solo un modo de entrada.

---

## ¿Cuándo aplica?

Cuando el CLI no es un modo de un sistema mayor, sino el sistema en sí. Señales concretas:

- Manipula **estado persistente** — archivos, base de datos, repositorios git.
- Tiene **subcomandos con comportamientos distintos** — `open`, `close`, `step-add`, `checkpoint`.
- Necesita **conectar con el sistema operativo**, APIs externas o agentes de IA.
- Debe poder **evolucionar hacia una GUI** sin reescribir la lógica de negocio.

Si se cumplen dos o más de estas condiciones, el CLI Dev Pattern es el marco correcto.

---

## Arquitectura — Los tres ejes

El patrón organiza el sistema en **tres ejes verticales** que comparten una única capa de almacenamiento central (el **Core**). Ningún eje conoce a los otros; todos leen y escriben exclusivamente a través del Core.

```
                     ┌───────────────────────────────┐
                     │         FUENTES DE DATO        │
                     │  (ideas, compromisos, notas)   │
                     └───────────────┬───────────────┘
                                     │
                                     ▼
      ┌──────────────────────────────────────────────────────────┐
      │                  CAPA DE ALMACENAMIENTO (Core)           │
      │           SQLite — layers / steps / checkpoints          │
      │       Verdad única · transaccional · sin dependencias UI │
      └──────────┬──────────────────┬──────────────────┬─────────┘
                 │                  │                  │
                 ▼                  ▼                  ▼
      ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
      │   MODELS API     │ │   EXPORT / I/O   │ │ AUTOMATIONS /    │
      │  (dominio puro)  │ │  Markdown · JSON │ │ AGENTS (futuro)  │
      └────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
               │                   │                    │
               ▼                   ▼                    ▼
      ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
      │      CLI         │ │      GUI         │ │    BITÁCORA      │
      │  velocidad       │ │  navegación      │ │  relato          │
      │  scripting       │ │  foco humano     │ │  reporte         │
      │  agentes         │ │  Tkinter / Flet  │ │  estratégico     │
      └────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
               │                   │                    │
               ▼                   ▼                    ▼
      ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
      │    COMANDOS      │ │  CONTROLES GUI   │ │    SALIDAS       │
      │  open / close    │ │  Nueva · Due     │ │  export.md       │
      │  snooze / kill   │ │  Pri · Who       │ │  JSON · informes │
      │  step-add        │ │  Checkpoint      │ │  dashboards      │
      │  checkpoint      │ │  Doing · Done    │ │                  │
      └────────┬─────────┘ └────────┬─────────┘ └──────────────────┘
               └──────────┬─────────┘
                          │
                          ▼
      ┌──────────────────────────────────────────────┐
      │             ESTADOS DE PROGRESO               │
      ├──────────────────────┬───────────────────────┤
      │     CHECKPOINTS      │         STEPS         │
      │  msg + versión       │   idx · estado        │
      │  (memoria viva)      │◀─────────────────────▶│
      │                      │   progreso (%)        │
      └──────────────────────┴───────────────────────┘
```

### Eje CLI — Velocidad y automatización

Comandos atómicos que operan sobre el Core directamente, sin pasar por GUI. Cada subcomando hace exactamente una cosa y retorna un resultado serializable. No acumula estado en memoria entre ejecuciones: el estado vive en el Core.

Uso natural: scripting, pipelines, integración con agentes de IA.

### Eje GUI — Foco humano

Consume los mismos datos del Core que el CLI, pero los presenta visualmente. No duplica lógica: delega en los mismos métodos del dominio. La GUI es intercambiable (Tkinter, Flet, web) porque toda la lógica vive en el Core. Si la GUI desaparece, el sistema sigue funcionando por CLI sin tocar nada.

### Eje Bitácora — Narrativa y estrategia

Exporta el estado del sistema a formatos legibles (Markdown, JSON, voz). Es el único eje de **solo lectura**: nunca escribe al Core. Esto garantiza que los informes sean reproducibles y que un export fallido nunca corrompa datos.

---

## AppState — El coordinador de sesión

En proyectos que combinan GUI y sistema operativo (git, VS Code, GitHub CLI), el `AppState` centraliza el estado de la sesión y coordina los tres ejes sin que ninguno conozca a los otros. Es el equivalente del `backend.py` en el patrón AUDI.

```
┌───────────────────────────────┐
│      ENTRADA DEL USUARIO      │
│ (ruta proyecto, acciones git, │
│  nombre repo, URL clonar)     │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────────────────────────────────┐
│                    AppState (coordinador)                  │
│   proyecto: Clase Proyecto (path, repo)                   │
│   archivos_data: { indice_fila: ruta_relativa }           │
└──────────┬──────────────────┬──────────────────┬──────────┘
           │                  │                  │
           ▼                  ▼                  ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  CLASE PROYECTO  │ │ OPERACIONES UI   │ │  SISTEMA (OS)    │
│  (gitpython)     │ │ (Flet / Tkinter) │ │  VS Code · GH CLI│
└────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
         │                   │                    │
         ▼                   ▼                    ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  MÉTODOS GIT     │ │  ACTUALIZAR UI   │ │ EJECUTAR COMANDOS│
│  init · clone    │ │  actualizar_rama │ │ abrir VS Code    │
│  add · commit    │ │  ver_archivos    │ │ crear repo GH    │
│  push · pull     │ │  show_dialog     │ │                  │
│  status · log    │ │  show_snack      │ │                  │
└────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
         │                   │                    │
         ▼                   ▼                    ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  REPOSITORIO GIT │ │  INTERACCIÓN     │ │  ACCIONES        │
│  archivos        │ │  CON EL USUARIO  │ │  EXTERNAS        │
│  commits · ramas │ │  mensajes        │ │  VS Code         │
│  estado          │ │  alertas         │ │  GitHub          │
└────────┬─────────┘ └──────────────────┘ └──────────────────┘
         │
         ▼
┌──────────────────────────────────────────────┐
│             ESTADO DE LOS ARCHIVOS           │
├──────────────────────┬───────────────────────┤
│  ARCHIVOS            │  ESTADO               │
│  (ruta relativa)     │  untracked · modified │
│                      │  staged · committed   │
│                      │  sin cambios          │
└──────────────────────┴───────────────────────┘
```

**Regla fundamental:** `AppState` es de sesión, no de persistencia. Si el proceso muere, se reconstruye completamente desde el Core. Nunca debe ser la única fuente de verdad.

---

## Las 6 reglas

**CLI-1 — El Core no conoce la interfaz**
La capa de almacenamiento y los modelos de dominio no importan nada de CLI, GUI ni Bitácora. Son el único módulo que puede vivir completamente solo. Si el Core importa algo de los ejes, la arquitectura está rota.

**CLI-2 — Los comandos son atómicos**
Cada subcomando hace exactamente una cosa y retorna un resultado serializable. No hay estado acumulado entre ejecuciones salvo el que vive en el Core. Un comando que requiere que el anterior haya corrido primero es un comando incompleto.

**CLI-3 — GUI y CLI comparten dominio, no código de presentación**
Ambos llaman a los mismos métodos del Core. Si un método existe solo para la GUI o solo para el CLI, la lógica está en el lugar equivocado y debe moverse al Core.

**CLI-4 — AppState es de sesión, no de persistencia**
El estado en memoria (proyecto activo, archivos seleccionados, rama actual) vive en `AppState`. La persistencia real vive en el Core (SQLite, git). Si el proceso muere, `AppState` se reconstruye desde el Core — no al revés.

**CLI-5 — El eje Bitácora es de solo lectura**
Los exportadores (Markdown, JSON, voz) solo leen del Core. Nunca escriben. Esto garantiza que los informes sean reproducibles y que un export fallido nunca corrompa los datos del sistema.

**CLI-6 — Los agentes usan el mismo CLI**
Las automatizaciones y agentes de IA invocan los mismos subcomandos que un humano. No existe una API especial para agentes. El log de comandos ejecutados es idéntico para humanos y máquinas: el sistema es **auditable por diseño**.

---

## Relación con los niveles AETHERYON

El CLI Dev Pattern no es un nivel nuevo. Se construye sobre los niveles 3–5 y los especializa para herramientas CLI con múltiples superficies de interacción simultáneas.

| Nivel 3–5 AUDI | CLI Dev Pattern |
|---|---|
| Domain | Core — modelos y reglas de negocio |
| Infrastructure | Core — SQLite, git, sistema operativo |
| Application | AppState + servicios de orquestación |
| backend.py | AppState — coordinador de sesión |
| User_Interface | Eje CLI · Eje GUI · Eje Bitácora |

La diferencia práctica: AUDI tiene una única `User_Interface`. El CLI Dev Pattern tiene **tres interfaces que coexisten** sobre el mismo núcleo y pueden estar activas simultáneamente o de forma independiente.

---

## Estructura de proyecto recomendada

```
proyecto/
│
├── bootstrap.py              # Orquestador: decide qué eje levantar
├── app_state.py              # Coordinador de sesión
├── config.py
├── requirements.txt
├── .env
│
├── Core/                     # Domain + Infrastructure fusionados
│   ├── __init__.py
│   ├── modelos/              # Entidades y reglas de negocio
│   ├── repositorios/         # SQLite, git, persistencia
│   ├── excepciones/
│   └── eventos/
│
├── Application/              # Casos de uso y servicios
│   ├── __init__.py
│   ├── servicios/
│   ├── dto/
│   └── interfaces/
│
├── CLI/                      # Eje 1 — velocidad y scripting
│   ├── __init__.py
│   ├── parser.py             # argparse / typer / click
│   └── comandos/
│       ├── cmd_open.py
│       ├── cmd_close.py
│       ├── cmd_checkpoint.py
│       ├── cmd_step_add.py
│       └── cmd_export.py
│
├── GUI/                      # Eje 2 — foco humano
│   ├── __init__.py
│   ├── layout.py
│   ├── vistas/
│   └── componentes/
│
├── Bitacora/                 # Eje 3 — solo lectura, exportación
│   ├── __init__.py
│   ├── exportar_md.py
│   ├── exportar_json.py
│   └── generar_informe.py
│
├── Tests/
│   ├── test_core/
│   ├── test_application/
│   ├── test_cli/
│   └── conftest.py
│
└── Docs/
    ├── README.md
    ├── comandos.md           # referencia completa de subcomandos
    └── arquitectura.md
```

---

## Inicio rápido

```bash
# Instalar
git clone <repo>
cd <proyecto>
python -m venv venv
source venv/bin/activate      # Linux / Mac
venv\Scripts\activate          # Windows

pip install -r requirements.txt
cp .env.example .env

# Inicializar Core
python bootstrap.py init

# Usar por CLI
python bootstrap.py cli open "nombre-proyecto"
python bootstrap.py cli step-add "primera tarea"
python bootstrap.py cli checkpoint "versión inicial lista"
python bootstrap.py cli export --formato md

# Levantar GUI
python bootstrap.py gui

# Generar Bitácora
python bootstrap.py bitacora --output informe.md
```

---

## Principios clave

- El Core es la única fuente de verdad. Los ejes la leen; no la reemplazan.
- Un comando que falla no deja el sistema en estado inconsistente.
- La GUI puede no existir y el sistema funciona igual por CLI.
- Los agentes son usuarios del CLI, no una capa especial.
- Un informe reproducible es un informe confiable.
- `AppState` se reconstruye; el Core persiste.

---

*CLI Dev Pattern · parte del ecosistema AETHERYON Dev Pattern*