#!/usr/bin/env python3
"""
CLI-Dev-Pattern.py
Generador de templates para el patrón AETHERYON Dev Pattern.

Uso interactivo:
    python CLI-Dev-Pattern.py

Uso directo:
    python CLI-Dev-Pattern.py <nivel> <ruta>
    python CLI-Dev-Pattern.py 3 C:\\Users\\usuario\\Documents\\mi_proyecto
"""

import sys
import os
import argparse
from pathlib import Path


# ─────────────────────────────────────────────
#  DEFINICIÓN DE NIVELES
# ─────────────────────────────────────────────

NIVELES = {
    1: "Standalone Script",
    2: "Patrón BF (Backend–Frontend)",
    3: "Patrón AUDI",
    4: "Patrón AUDDITS",
    5: "Patrón AUDDITS + MVVM",
}

COLORES = {
    "cyan":    "\033[96m",
    "green":   "\033[92m",
    "yellow":  "\033[93m",
    "red":     "\033[91m",
    "blue":    "\033[94m",
    "bold":    "\033[1m",
    "reset":   "\033[0m",
    "dim":     "\033[2m",
}

def _ansi_soportado() -> bool:
    """Detecta si la terminal soporta colores ANSI."""
    if not sys.stdout.isatty():
        return False
    if os.name == "nt":
        # Windows 10 v1511+ soporta ANSI si se habilita vía kernel32
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle   = kernel32.GetStdHandle(-11)   # STD_OUTPUT_HANDLE
            mode     = ctypes.c_ulong()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                # Habilitar ENABLE_VIRTUAL_TERMINAL_PROCESSING (0x0004)
                kernel32.SetConsoleMode(handle, mode.value | 0x0004)
                return True
        except Exception:
            pass
        return False
    return True


_ANSI_OK = _ansi_soportado()


def c(texto, color):
    """Aplica color si la terminal lo soporta."""
    if _ANSI_OK:
        return f"{COLORES.get(color, '')}{texto}{COLORES['reset']}"
    return texto


# ─────────────────────────────────────────────
#  TEMPLATES POR NIVEL
# ─────────────────────────────────────────────

def get_templates(nivel: int) -> dict:
    """Retorna dict { ruta_relativa: contenido } para el nivel dado."""

    templates = {}

    # ── NIVEL 1 ──────────────────────────────
    if nivel == 1:
        templates["proyecto.py"] = '''\
#!/usr/bin/env python3
"""
proyecto.py - Script único con múltiples modos operativos.
Nivel 1 — Standalone Script (AETHERYON Dev Pattern)
"""

import sys
import argparse
import logging
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# ==================== DOMAIN ====================

class EstadoEntidad(Enum):
    ACTIVO   = "activo"
    INACTIVO = "inactivo"


@dataclass
class Entidad:
    """Entidad principal del dominio. Contiene reglas de negocio."""
    id:     Optional[int]
    nombre: str
    estado: EstadoEntidad = EstadoEntidad.ACTIVO

    def desactivar(self) -> None:
        """Regla de negocio: desactivar entidad."""
        self.estado = EstadoEntidad.INACTIVO

    def activar(self) -> None:
        """Regla de negocio: activar entidad."""
        self.estado = EstadoEntidad.ACTIVO


# ==================== APPLICATION ====================

class Servicio:
    """Orquesta los casos de uso. Sin lógica de presentación."""

    def __init__(self):
        self._entidades: List[Entidad] = []
        self._next_id = 1

    def crear(self, nombre: str) -> Entidad:
        if not nombre or len(nombre.strip()) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres.")
        entidad = Entidad(id=self._next_id, nombre=nombre.strip())
        self._entidades.append(entidad)
        self._next_id += 1
        logger.info(f"Entidad creada: {entidad.nombre} (ID: {entidad.id})")
        return entidad

    def listar(self, solo_activos: bool = False) -> List[Entidad]:
        if solo_activos:
            return [e for e in self._entidades if e.estado == EstadoEntidad.ACTIVO]
        return self._entidades.copy()

    def obtener(self, entidad_id: int) -> Optional[Entidad]:
        return next((e for e in self._entidades if e.id == entidad_id), None)

    def eliminar(self, entidad_id: int) -> bool:
        entidad = self.obtener(entidad_id)
        if entidad:
            entidad.desactivar()
            logger.info(f"Entidad desactivada: ID {entidad_id}")
            return True
        return False


# ==================== INTERFACES ====================

class CLI:
    """Interfaz de línea de comandos."""

    def __init__(self, servicio: Servicio):
        self.servicio = servicio

    def ejecutar(self, args: argparse.Namespace) -> None:
        acciones = {
            "crear":   self._crear,
            "listar":  self._listar,
            "obtener": self._obtener,
            "eliminar": self._eliminar,
        }
        accion = acciones.get(args.comando)
        if accion:
            accion(args)
        else:
            print("Comando no reconocido.")

    def _crear(self, args):
        try:
            e = self.servicio.crear(args.nombre)
            print(f"✅ Creado: {e.nombre} (ID: {e.id})")
        except ValueError as ex:
            print(f"❌ Error: {ex}")

    def _listar(self, args):
        entidades = self.servicio.listar(getattr(args, "solo_activos", False))
        if not entidades:
            print("No hay entidades registradas.")
            return
        print(f"\\n{'ID':<5} {'NOMBRE':<25} {'ESTADO':<10}")
        print("-" * 42)
        for e in entidades:
            print(f"{e.id:<5} {e.nombre:<25} {e.estado.value:<10}")

    def _obtener(self, args):
        e = self.servicio.obtener(args.id)
        if e:
            print(f"\\nID:     {e.id}")
            print(f"Nombre: {e.nombre}")
            print(f"Estado: {e.estado.value}")
        else:
            print(f"❌ Entidad {args.id} no encontrada.")

    def _eliminar(self, args):
        if self.servicio.eliminar(args.id):
            print(f"✅ Entidad {args.id} desactivada.")
        else:
            print(f"❌ Entidad {args.id} no encontrada.")


class UI:
    """Interfaz interactiva por consola."""

    def __init__(self, servicio: Servicio):
        self.servicio = servicio

    def ejecutar(self) -> None:
        print("\\n" + "=" * 40)
        print("   SISTEMA — Nivel 1 Standalone Script")
        print("=" * 40)
        while True:
            print("\\n1. Crear  2. Listar  3. Buscar  4. Eliminar  5. Salir")
            opcion = input("Opción: ").strip()
            if opcion == "1":
                nombre = input("Nombre: ").strip()
                try:
                    e = self.servicio.crear(nombre)
                    print(f"✅ Creado ID: {e.id}")
                except ValueError as ex:
                    print(f"❌ {ex}")
            elif opcion == "2":
                self._mostrar_lista()
            elif opcion == "3":
                self._buscar()
            elif opcion == "4":
                self._eliminar()
            elif opcion == "5":
                print("Hasta luego.")
                break

    def _mostrar_lista(self):
        entidades = self.servicio.listar()
        if not entidades:
            print("Lista vacía.")
            return
        for e in entidades:
            print(f"  [{e.id}] {e.nombre} — {e.estado.value}")

    def _buscar(self):
        try:
            eid = int(input("ID: ").strip())
            e = self.servicio.obtener(eid)
            print(f"{e.nombre} ({e.estado.value})" if e else "No encontrada.")
        except ValueError:
            print("ID inválido.")

    def _eliminar(self):
        try:
            eid = int(input("ID a eliminar: ").strip())
            print("✅ Eliminado." if self.servicio.eliminar(eid) else "No encontrada.")
        except ValueError:
            print("ID inválido.")


# ==================== MAIN ====================

def main():
    parser = argparse.ArgumentParser(description="Proyecto — Nivel 1 AETHERYON")
    parser.add_argument("--modo", choices=["cli", "ui"], default="ui")

    subparsers = parser.add_subparsers(dest="comando")

    crear_p = subparsers.add_parser("crear")
    crear_p.add_argument("nombre")

    listar_p = subparsers.add_parser("listar")
    listar_p.add_argument("--solo-activos", action="store_true")

    obtener_p = subparsers.add_parser("obtener")
    obtener_p.add_argument("id", type=int)

    eliminar_p = subparsers.add_parser("eliminar")
    eliminar_p.add_argument("id", type=int)

    args = parser.parse_args()
    servicio = Servicio()

    if args.modo == "ui" and not args.comando:
        UI(servicio).ejecutar()
    elif args.comando:
        CLI(servicio).ejecutar(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
'''

    # ── NIVEL 2 ──────────────────────────────
    elif nivel == 2:
        templates["backend.py"] = '''\
"""
backend.py - Lógica de negocio y acceso a datos.
Nivel 2 — Patrón BF (AETHERYON Dev Pattern)

Regla: el frontend importa al backend. Nunca al revés.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class Entidad:
    """Entidad principal del dominio."""
    id:             Optional[int]
    nombre:         str
    descripcion:    str = ""
    activo:         bool = True
    fecha_creacion: str = field(default_factory=lambda: datetime.now().isoformat())

    def desactivar(self) -> None:
        self.activo = False


class GestorEntidades:
    """Lógica de negocio pura, sin presentación."""

    def __init__(self):
        self._entidades: List[Entidad] = []
        self._next_id = 1

    def agregar(self, nombre: str, descripcion: str = "") -> Entidad:
        if not nombre or len(nombre.strip()) < 2:
            raise ValueError("Nombre debe tener al menos 2 caracteres.")
        e = Entidad(id=self._next_id, nombre=nombre.strip(), descripcion=descripcion)
        self._entidades.append(e)
        self._next_id += 1
        return e

    def obtener_todas(self) -> List[Entidad]:
        return self._entidades.copy()

    def obtener_activas(self) -> List[Entidad]:
        return [e for e in self._entidades if e.activo]

    def obtener_por_id(self, entidad_id: int) -> Optional[Entidad]:
        return next((e for e in self._entidades if e.id == entidad_id), None)

    def eliminar(self, entidad_id: int) -> bool:
        e = self.obtener_por_id(entidad_id)
        if e:
            e.desactivar()
            return True
        return False

    def buscar(self, texto: str) -> List[Entidad]:
        t = texto.lower()
        return [e for e in self._entidades
                if t in e.nombre.lower() or t in e.descripcion.lower()]

    def estadisticas(self) -> Dict[str, Any]:
        total    = len(self._entidades)
        activas  = len([e for e in self._entidades if e.activo])
        return {"total": total, "activas": activas, "inactivas": total - activas}


class Backend:
    """
    Interfaz unificada para el frontend.
    Oculta la complejidad interna del gestor.
    """

    def __init__(self):
        self._gestor = GestorEntidades()

    def obtener_entidades(self, solo_activas: bool = False) -> List[Entidad]:
        return self._gestor.obtener_activas() if solo_activas else self._gestor.obtener_todas()

    def crear_entidad(self, nombre: str, descripcion: str = "") -> Entidad:
        return self._gestor.agregar(nombre, descripcion)

    def eliminar_entidad(self, entidad_id: int) -> bool:
        return self._gestor.eliminar(entidad_id)

    def buscar_entidades(self, texto: str) -> List[Entidad]:
        return self._gestor.buscar(texto)

    def obtener_estadisticas(self) -> Dict[str, Any]:
        return self._gestor.estadisticas()
'''

        templates["frontend.py"] = '''\
"""
frontend.py - Interfaz de usuario.
Nivel 2 — Patrón BF (AETHERYON Dev Pattern)

Regla: solo consume métodos públicos del backend. Sin lógica de negocio aquí.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from backend import Backend


class Aplicacion:
    """Interfaz gráfica principal."""

    def __init__(self):
        self.backend = Backend()
        self._crear_ventana()
        self._crear_widgets()
        self._cargar_datos()

    def _crear_ventana(self):
        self.root = tk.Tk()
        self.root.title("Proyecto — Nivel 2 BF")
        self.root.geometry("800x500")
        self.root.minsize(600, 400)

    def _crear_widgets(self):
        # ── Barra superior ──
        toolbar = ttk.Frame(self.root, padding=5)
        toolbar.pack(fill=tk.X)

        ttk.Label(toolbar, text="Nombre:").pack(side=tk.LEFT)
        self.entry_nombre = ttk.Entry(toolbar, width=30)
        self.entry_nombre.pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="➕ Crear", command=self._crear).pack(side=tk.LEFT)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        ttk.Label(toolbar, text="Buscar:").pack(side=tk.LEFT)
        self.entry_buscar = ttk.Entry(toolbar, width=20)
        self.entry_buscar.pack(side=tk.LEFT, padx=5)
        self.entry_buscar.bind("<KeyRelease>", self._buscar)

        # ── Tabla ──
        frame_tabla = ttk.Frame(self.root)
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scroll = ttk.Scrollbar(frame_tabla)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(
            frame_tabla,
            columns=("id", "nombre", "descripcion", "estado", "fecha"),
            show="headings",
            yscrollcommand=scroll.set,
        )
        for col, ancho in [("id", 50), ("nombre", 200), ("descripcion", 250),
                           ("estado", 80), ("fecha", 160)]:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=ancho, anchor="center" if col in ("id", "estado") else "w")
        self.tree.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.tree.yview)

        # ── Acciones ──
        acciones = ttk.Frame(self.root, padding=5)
        acciones.pack(fill=tk.X)
        ttk.Button(acciones, text="🗑️ Eliminar", command=self._eliminar).pack(side=tk.LEFT)
        self.lbl_stats = ttk.Label(acciones, text="")
        self.lbl_stats.pack(side=tk.RIGHT, padx=10)

    def _cargar_datos(self, entidades=None):
        for item in self.tree.get_children():
            self.tree.delete(item)
        datos = entidades if entidades is not None else self.backend.obtener_entidades()
        for e in datos:
            self.tree.insert("", "end",
                values=(e.id, e.nombre, e.descripcion,
                        "✅" if e.activo else "❌", e.fecha_creacion[:10]),
                iid=str(e.id))
        stats = self.backend.obtener_estadisticas()
        self.lbl_stats.config(text=f"Total: {stats['total']} | Activas: {stats['activas']}")

    def _crear(self):
        nombre = self.entry_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Aviso", "El nombre es obligatorio.")
            return
        try:
            self.backend.crear_entidad(nombre)
            self.entry_nombre.delete(0, tk.END)
            self._cargar_datos()
        except ValueError as ex:
            messagebox.showerror("Error", str(ex))

    def _eliminar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecciona una entidad.")
            return
        eid = int(sel[0])
        if messagebox.askyesno("Confirmar", f"¿Eliminar entidad {eid}?"):
            self.backend.eliminar_entidad(eid)
            self._cargar_datos()

    def _buscar(self, _event=None):
        texto = self.entry_buscar.get().strip()
        if texto:
            resultados = self.backend.buscar_entidades(texto)
            self._cargar_datos(resultados)
        else:
            self._cargar_datos()

    def ejecutar(self):
        self.root.mainloop()


if __name__ == "__main__":
    Aplicacion().ejecutar()
'''

    # ── NIVELES 3, 4 y 5 (estructura compartida, se expande) ──────────────────
    elif nivel >= 3:
        # ── archivos raíz ──
        templates["backend.py"] = _tpl_backend()
        templates["bootstrap.py"] = _tpl_bootstrap()

        if nivel >= 4:
            templates["config.py"] = _tpl_config()
            templates["requirements.txt"] = _tpl_requirements()
            templates[".env.example"] = _tpl_env()
            templates[".gitignore"] = _tpl_gitignore()

        # ── Domain ──
        templates["Domain/__init__.py"] = '"""Capa de Dominio — Reglas de negocio puras."""\n'
        templates["Domain/entidades/__init__.py"] = ""
        templates["Domain/entidades/entidad.py"] = _tpl_entidad()
        templates["Domain/value_objects/__init__.py"] = ""
        templates["Domain/value_objects/nombre.py"] = _tpl_value_object()
        templates["Domain/eventos/__init__.py"] = ""
        templates["Domain/eventos/eventos_entidad.py"] = _tpl_eventos()
        templates["Domain/excepciones/__init__.py"] = ""
        templates["Domain/excepciones/excepciones_dominio.py"] = _tpl_excepciones()

        # ── Application ──
        templates["Application/__init__.py"] = '"""Capa de Aplicación — Casos de uso."""\n'
        templates["Application/servicios/__init__.py"] = ""
        templates["Application/servicios/servicio_entidad.py"] = _tpl_servicio()
        templates["Application/dto/__init__.py"] = ""
        templates["Application/dto/entidad_dto.py"] = _tpl_dto()
        templates["Application/interfaces/__init__.py"] = ""
        templates["Application/interfaces/repositorio_entidad.py"] = _tpl_repositorio_abc()

        # ── Infrastructure ──
        templates["Infrastructure/__init__.py"] = '"""Capa de Infraestructura — Implementaciones técnicas."""\n'
        templates["Infrastructure/persistencia/__init__.py"] = ""
        templates["Infrastructure/persistencia/base_datos/__init__.py"] = ""
        templates["Infrastructure/persistencia/base_datos/conexion.py"] = _tpl_conexion()
        templates["Infrastructure/persistencia/repositorios/__init__.py"] = ""
        templates["Infrastructure/persistencia/repositorios/repositorio_entidad_sql.py"] = _tpl_repositorio_sql()
        templates["Infrastructure/servicios_externos/__init__.py"] = ""
        templates["Infrastructure/servicios_externos/servicio_externo.py"] = _tpl_servicio_externo()
        templates["Infrastructure/logging/__init__.py"] = ""
        templates["Infrastructure/logging/logger_config.py"] = _tpl_logger()

        # ── User Interface ──
        templates["User_Interface/__init__.py"] = '"""Capa de Interfaz de Usuario."""\n'
        templates["User_Interface/layout.py"] = _tpl_layout()
        templates["User_Interface/vistas/__init__.py"] = ""
        templates["User_Interface/vistas/vista_principal.py"] = _tpl_vista()

        # ── Tests (nivel 4+) ──
        if nivel >= 4:
            templates["Tests/__init__.py"] = ""
            templates["Tests/conftest.py"] = _tpl_conftest()
            templates["Tests/test_domain/__init__.py"] = ""
            templates["Tests/test_domain/test_entidad.py"] = _tpl_test_domain()
            templates["Tests/test_application/__init__.py"] = ""
            templates["Tests/test_application/test_servicio_entidad.py"] = _tpl_test_application()
            templates["Tests/test_infrastructure/__init__.py"] = ""
            templates["Tests/test_infrastructure/test_repositorio.py"] = _tpl_test_infra()

            # ── Scripts ──
            templates["Scripts/__init__.py"] = ""
            templates["Scripts/migraciones.py"] = _tpl_migraciones()
            templates["Scripts/seed_data.py"] = _tpl_seed()

            # ── Docs ──
            templates["Docs/README.md"] = _tpl_readme()
            templates["Docs/arquitectura.md"] = _tpl_arquitectura()

        # ── Presentation MVVM (nivel 5) ──
        if nivel >= 5:
            templates["Presentation/__init__.py"] = '"""Capa de Presentación — MVVM."""\n'
            templates["Presentation/viewmodels/__init__.py"] = ""
            templates["Presentation/viewmodels/viewmodel_base.py"] = _tpl_viewmodel_base()
            templates["Presentation/viewmodels/entidad_viewmodel.py"] = _tpl_viewmodel()
            templates["Presentation/models/__init__.py"] = ""
            templates["Presentation/models/ui_entidad.py"] = _tpl_ui_model()
            templates["Presentation/models/validators.py"] = _tpl_validators()
            templates["Presentation/commands/__init__.py"] = ""
            templates["Presentation/commands/comando_base.py"] = _tpl_comando_base()
            templates["Presentation/commands/comandos_entidad.py"] = _tpl_comandos()

            templates["Tests/test_presentation/__init__.py"] = ""
            templates["Tests/test_presentation/test_entidad_viewmodel.py"] = _tpl_test_viewmodel()
            templates["Docs/guia_estilo.md"] = _tpl_guia_estilo()

    return templates


# ─────────────────────────────────────────────
#  CONTENIDOS DE TEMPLATES
# ─────────────────────────────────────────────

def _tpl_entidad():
    return '''\
"""
Domain/entidades/entidad.py
Entidad principal del dominio.

Regla: solo lógica de negocio. Sin imports de Application, Infrastructure ni UI.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from Domain.excepciones.excepciones_dominio import NombreInvalido, EstadoInvalido


class EstadoEntidad:
    ACTIVO   = "activo"
    INACTIVO = "inactivo"


@dataclass
class Entidad:
    """
    Entidad principal. Raíz del agregado.
    Contiene identidad única y todas las reglas de negocio.
    """
    id:             Optional[int]
    nombre:         str
    descripcion:    str = ""
    estado:         str = EstadoEntidad.ACTIVO
    fecha_creacion: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        self._validar_nombre(self.nombre)

    # ── Reglas de negocio ──

    def renombrar(self, nuevo_nombre: str) -> None:
        """Regla: el nombre debe ser válido antes de cambiar."""
        self._validar_nombre(nuevo_nombre)
        self.nombre = nuevo_nombre

    def activar(self) -> None:
        """Regla: solo se puede activar si está inactivo."""
        if self.estado == EstadoEntidad.ACTIVO:
            raise EstadoInvalido("La entidad ya está activa.")
        self.estado = EstadoEntidad.ACTIVO

    def desactivar(self) -> None:
        """Regla: solo se puede desactivar si está activo."""
        if self.estado == EstadoEntidad.INACTIVO:
            raise EstadoInvalido("La entidad ya está inactiva.")
        self.estado = EstadoEntidad.INACTIVO

    @property
    def esta_activo(self) -> bool:
        return self.estado == EstadoEntidad.ACTIVO

    # ── Validaciones internas ──

    @staticmethod
    def _validar_nombre(nombre: str) -> None:
        if not nombre or len(nombre.strip()) < 2:
            raise NombreInvalido("El nombre debe tener al menos 2 caracteres.")
'''


def _tpl_value_object():
    return '''\
"""
Domain/value_objects/nombre.py
Value Object: Nombre validado.

Los value objects son inmutables y se comparan por valor, no por identidad.
"""

from dataclasses import dataclass
from Domain.excepciones.excepciones_dominio import NombreInvalido


@dataclass(frozen=True)
class Nombre:
    """Nombre validado. Inmutable."""
    valor: str

    def __post_init__(self):
        if not self.valor or len(self.valor.strip()) < 2:
            raise NombreInvalido("El nombre debe tener al menos 2 caracteres.")
        object.__setattr__(self, "valor", self.valor.strip())

    def __str__(self) -> str:
        return self.valor
'''


def _tpl_eventos():
    return '''\
"""
Domain/eventos/eventos_entidad.py
Eventos de dominio.

Los eventos representan hechos que ocurrieron en el dominio.
Infrastructure puede suscribirse a ellos sin que Domain conozca Infrastructure.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EventoDominio:
    """Base para todos los eventos de dominio."""
    ocurrido_en: datetime = None

    def __post_init__(self):
        object.__setattr__(self, "ocurrido_en", datetime.now())


@dataclass(frozen=True)
class EntidadCreada(EventoDominio):
    entidad_id: int = None
    nombre:     str = ""


@dataclass(frozen=True)
class EntidadDesactivada(EventoDominio):
    entidad_id: int = None
'''


def _tpl_excepciones():
    return '''\
"""
Domain/excepciones/excepciones_dominio.py
Excepciones de negocio.

Regla: las excepciones de dominio no deben contener lógica de infraestructura.
"""


class ErrorDominio(Exception):
    """Base para todos los errores de dominio."""


class NombreInvalido(ErrorDominio):
    """El nombre no cumple las reglas de negocio."""


class EstadoInvalido(ErrorDominio):
    """La transición de estado no está permitida."""


class EntidadNoEncontrada(ErrorDominio):
    def __init__(self, entidad_id: int):
        super().__init__(f"Entidad con ID {entidad_id} no encontrada.")


class OperacionNoPermitida(ErrorDominio):
    """La operación no está permitida en el estado actual."""
'''


def _tpl_repositorio_abc():
    return '''\
"""
Application/interfaces/repositorio_entidad.py
Contrato abstracto del repositorio.

Regla: Application define el contrato. Infrastructure lo implementa.
Domain nunca depende de este archivo.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from Domain.entidades.entidad import Entidad


class RepositorioEntidad(ABC):
    """
    Contrato para el repositorio de Entidad.
    Infrastructure provee la implementación concreta.
    """

    @abstractmethod
    def obtener_por_id(self, entidad_id: int) -> Optional[Entidad]:
        pass

    @abstractmethod
    def listar(self, solo_activos: bool = False) -> List[Entidad]:
        pass

    @abstractmethod
    def guardar(self, entidad: Entidad) -> Entidad:
        pass

    @abstractmethod
    def actualizar(self, entidad: Entidad) -> bool:
        pass

    @abstractmethod
    def eliminar(self, entidad_id: int) -> bool:
        pass
'''


def _tpl_dto():
    return '''\
"""
Application/dto/entidad_dto.py
Data Transfer Objects para Entidad.

Regla: los DTOs transportan datos entre capas.
Las entidades de dominio no se exponen directamente a la UI.
"""

from dataclasses import dataclass
from typing import Optional
from Domain.entidades.entidad import Entidad


@dataclass
class EntidadDTO:
    """Solo estructura. Sin lógica de negocio."""
    id:          Optional[int]
    nombre:      str
    descripcion: str
    estado:      str
    esta_activo: bool

    @classmethod
    def desde_entidad(cls, e: Entidad) -> "EntidadDTO":
        return cls(
            id=e.id,
            nombre=e.nombre,
            descripcion=e.descripcion,
            estado=e.estado,
            esta_activo=e.esta_activo,
        )

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "nombre":      self.nombre,
            "descripcion": self.descripcion,
            "estado":      self.estado,
            "esta_activo": self.esta_activo,
        }


@dataclass
class SolicitudCrearEntidadDTO:
    nombre:      str
    descripcion: str = ""

    @classmethod
    def desde_dict(cls, datos: dict) -> "SolicitudCrearEntidadDTO":
        return cls(
            nombre=datos.get("nombre", ""),
            descripcion=datos.get("descripcion", ""),
        )
'''


def _tpl_servicio():
    return '''\
"""
Application/servicios/servicio_entidad.py
Casos de uso para Entidad.

Regla: coordina, no implementa. Depende de interfaces, no de implementaciones.
"""

import logging
from typing import List, Optional

from Domain.entidades.entidad import Entidad
from Domain.excepciones.excepciones_dominio import EntidadNoEncontrada
from Application.interfaces.repositorio_entidad import RepositorioEntidad
from Application.dto.entidad_dto import EntidadDTO, SolicitudCrearEntidadDTO


class ServicioEntidad:
    """Orquesta los casos de uso de Entidad."""

    def __init__(self, repositorio: RepositorioEntidad):
        self.repositorio = repositorio
        self.logger = logging.getLogger(__name__)

    def crear(self, solicitud: SolicitudCrearEntidadDTO) -> EntidadDTO:
        """Caso de uso: crear una nueva entidad."""
        self.logger.info(f"Creando entidad: {solicitud.nombre}")
        entidad = Entidad(id=None, nombre=solicitud.nombre, descripcion=solicitud.descripcion)
        guardada = self.repositorio.guardar(entidad)
        self.logger.info(f"Entidad creada con ID: {guardada.id}")
        return EntidadDTO.desde_entidad(guardada)

    def obtener(self, entidad_id: int) -> EntidadDTO:
        """Caso de uso: obtener entidad por ID."""
        entidad = self.repositorio.obtener_por_id(entidad_id)
        if not entidad:
            raise EntidadNoEncontrada(entidad_id)
        return EntidadDTO.desde_entidad(entidad)

    def listar(self, solo_activos: bool = False) -> List[EntidadDTO]:
        """Caso de uso: listar todas las entidades."""
        entidades = self.repositorio.listar(solo_activos)
        return [EntidadDTO.desde_entidad(e) for e in entidades]

    def eliminar(self, entidad_id: int) -> bool:
        """Caso de uso: eliminar entidad (borrado lógico)."""
        entidad = self.repositorio.obtener_por_id(entidad_id)
        if not entidad:
            raise EntidadNoEncontrada(entidad_id)
        entidad.desactivar()
        return self.repositorio.actualizar(entidad)
'''


def _tpl_repositorio_sql():
    return '''\
"""
Infrastructure/persistencia/repositorios/repositorio_entidad_sql.py
Implementación SQLite del repositorio de Entidad.

Regla: implementa el contrato de Application. Domain nunca importa este archivo.
"""

import sqlite3
import logging
from typing import List, Optional
from datetime import datetime

from Domain.entidades.entidad import Entidad, EstadoEntidad
from Application.interfaces.repositorio_entidad import RepositorioEntidad


class RepositorioEntidadSQL(RepositorioEntidad):
    """Implementación SQLite. Puede reemplazarse por PostgreSQL, MongoDB, etc."""

    def __init__(self, conexion: sqlite3.Connection):
        self.conn = conexion
        self.logger = logging.getLogger(__name__)
        self._crear_tabla()

    def _crear_tabla(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS entidades (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre         TEXT    NOT NULL,
                descripcion    TEXT    DEFAULT "",
                estado         TEXT    DEFAULT "activo",
                fecha_creacion TEXT
            )
        """)
        self.conn.commit()

    def obtener_por_id(self, entidad_id: int) -> Optional[Entidad]:
        cursor = self.conn.execute(
            "SELECT id, nombre, descripcion, estado, fecha_creacion FROM entidades WHERE id = ?",
            (entidad_id,)
        )
        fila = cursor.fetchone()
        return self._fila_a_entidad(fila) if fila else None

    def listar(self, solo_activos: bool = False) -> List[Entidad]:
        if solo_activos:
            cursor = self.conn.execute(
                "SELECT id, nombre, descripcion, estado, fecha_creacion FROM entidades WHERE estado = ?",
                (EstadoEntidad.ACTIVO,)
            )
        else:
            cursor = self.conn.execute(
                "SELECT id, nombre, descripcion, estado, fecha_creacion FROM entidades"
            )
        return [self._fila_a_entidad(f) for f in cursor.fetchall()]

    def guardar(self, entidad: Entidad) -> Entidad:
        cursor = self.conn.execute(
            "INSERT INTO entidades (nombre, descripcion, estado, fecha_creacion) VALUES (?, ?, ?, ?)",
            (entidad.nombre, entidad.descripcion, entidad.estado,
             entidad.fecha_creacion.isoformat())
        )
        self.conn.commit()
        entidad.id = cursor.lastrowid
        return entidad

    def actualizar(self, entidad: Entidad) -> bool:
        cursor = self.conn.execute(
            "UPDATE entidades SET nombre = ?, descripcion = ?, estado = ? WHERE id = ?",
            (entidad.nombre, entidad.descripcion, entidad.estado, entidad.id)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def eliminar(self, entidad_id: int) -> bool:
        cursor = self.conn.execute(
            "UPDATE entidades SET estado = ? WHERE id = ?",
            (EstadoEntidad.INACTIVO, entidad_id)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    @staticmethod
    def _fila_a_entidad(fila) -> Entidad:
        return Entidad(
            id=fila[0],
            nombre=fila[1],
            descripcion=fila[2] or "",
            estado=fila[3],
            fecha_creacion=datetime.fromisoformat(fila[4]) if fila[4] else datetime.now(),
        )
'''


def _tpl_conexion():
    return '''\
"""
Infrastructure/persistencia/base_datos/conexion.py
Gestión de conexiones a base de datos.
"""

import sqlite3
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def obtener_conexion(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Crea y retorna una conexión SQLite.
    Usa :memory: para tests.
    """
    ruta = db_path or "data/app.db"

    if ruta != ":memory:":
        import os
        os.makedirs(os.path.dirname(ruta), exist_ok=True)

    conn = sqlite3.connect(ruta)
    conn.row_factory = sqlite3.Row
    logger.info(f"Conexión establecida: {ruta}")
    return conn
'''


def _tpl_servicio_externo():
    return '''\
"""
Infrastructure/servicios_externos/servicio_externo.py
Adaptador para servicios externos (APIs, email, etc.).

Regla: encapsula la comunicación con proveedores externos.
El dominio nunca depende de este módulo.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ResultadoOperacion:
    exitoso:    bool
    mensaje:    str
    datos:      Optional[Dict[str, Any]] = None


class ServicioExternoBase:
    """Base para adaptadores de servicios externos."""

    def __init__(self, config: Dict[str, Any]):
        self.config  = config
        self.logger  = logging.getLogger(__name__)
        self.activo  = config.get("activo", False)

    def verificar_conexion(self) -> bool:
        """Verifica que el servicio externo esté disponible."""
        raise NotImplementedError

    def ejecutar(self, payload: Dict[str, Any]) -> ResultadoOperacion:
        """Ejecuta la operación en el servicio externo."""
        raise NotImplementedError


class ServicioExternoMock(ServicioExternoBase):
    """Implementación mock para desarrollo y tests."""

    def verificar_conexion(self) -> bool:
        self.logger.info("ServicioExternoMock: conexión OK (simulada)")
        return True

    def ejecutar(self, payload: Dict[str, Any]) -> ResultadoOperacion:
        self.logger.info(f"ServicioExternoMock ejecutado con: {payload}")
        return ResultadoOperacion(exitoso=True, mensaje="Operación simulada correctamente.")
'''


def _tpl_logger():
    return '''\
"""
Infrastructure/logging/logger_config.py
Configuración centralizada de logging.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional


def configurar_logging(
    nivel:   str = "INFO",
    archivo: Optional[str] = None,
    formato: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
) -> None:
    """Configura el sistema de logging para toda la aplicación."""
    nivel_num = getattr(logging, nivel.upper(), logging.INFO)
    handlers  = [logging.StreamHandler(sys.stdout)]

    if archivo:
        Path(archivo).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(
            logging.handlers.RotatingFileHandler(
                archivo, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
            )
        )

    logging.basicConfig(level=nivel_num, format=formato, handlers=handlers, force=True)
    logging.getLogger(__name__).info(f"Logging configurado: nivel={nivel}")
'''


def _tpl_layout():
    return '''\
"""
User_Interface/layout.py
Orquestador de la interfaz gráfica principal.

Regla: la UI depende de Application (a través de backend.py), nunca de Infrastructure.
"""

import tkinter as tk
from tkinter import ttk
from User_Interface.vistas.vista_principal import VistaPrincipal


def crear_interfaz(backend) -> tk.Tk:
    """Crea y retorna la ventana principal configurada."""
    root = tk.Tk()
    root.title("Proyecto — AETHERYON Dev Pattern")
    root.geometry("1024x768")
    root.minsize(800, 600)

    # ── Barra de menú ──
    menubar = tk.Menu(root)
    menu_archivo = tk.Menu(menubar, tearoff=0)
    menu_archivo.add_command(label="Salir", command=root.quit)
    menubar.add_cascade(label="Archivo", menu=menu_archivo)
    root.config(menu=menubar)

    # ── Vista principal ──
    vista = VistaPrincipal(root, backend)
    vista.frame.pack(fill=tk.BOTH, expand=True)

    # ── Barra de estado ──
    barra_estado = ttk.Label(root, text="Listo", relief=tk.SUNKEN, padding=2)
    barra_estado.pack(side=tk.BOTTOM, fill=tk.X)

    return root
'''


def _tpl_vista():
    return '''\
"""
User_Interface/vistas/vista_principal.py
Vista principal de la aplicación.

Regla: solo widgets y binding. Sin lógica de negocio.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from Application.dto.entidad_dto import SolicitudCrearEntidadDTO


class VistaPrincipal:
    """Vista principal. Consume backend a través de métodos públicos."""

    def __init__(self, parent, backend):
        self.parent  = parent
        self.backend = backend
        self.frame   = ttk.Frame(parent)
        self._crear_widgets()
        self._cargar_datos()

    def _crear_widgets(self):
        # ── Barra de herramientas ──
        toolbar = ttk.Frame(self.frame, padding=5)
        toolbar.pack(fill=tk.X)

        ttk.Label(toolbar, text="Nombre:").pack(side=tk.LEFT)
        self.entry_nombre = ttk.Entry(toolbar, width=30)
        self.entry_nombre.pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="➕ Crear", command=self._crear).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="🔄 Refrescar", command=self._cargar_datos).pack(side=tk.LEFT, padx=5)

        # ── Tabla ──
        frame_tabla = ttk.Frame(self.frame)
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scroll_y = ttk.Scrollbar(frame_tabla)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(
            frame_tabla,
            columns=("id", "nombre", "descripcion", "estado"),
            show="headings",
            yscrollcommand=scroll_y.set,
        )
        for col, ancho in [("id", 60), ("nombre", 200), ("descripcion", 300), ("estado", 80)]:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=ancho)
        self.tree.pack(fill=tk.BOTH, expand=True)
        scroll_y.config(command=self.tree.yview)

        # ── Acciones ──
        acciones = ttk.Frame(self.frame, padding=5)
        acciones.pack(fill=tk.X)
        ttk.Button(acciones, text="🗑️ Eliminar", command=self._eliminar).pack(side=tk.LEFT)
        self.lbl_info = ttk.Label(acciones, text="")
        self.lbl_info.pack(side=tk.RIGHT)

    def _cargar_datos(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            entidades = self.backend.obtener_entidades()
            for e in entidades:
                self.tree.insert("", "end",
                    values=(e.id, e.nombre, e.descripcion, e.estado), iid=str(e.id))
            self.lbl_info.config(text=f"{len(entidades)} registros")
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def _crear(self):
        nombre = self.entry_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Aviso", "El nombre es obligatorio.")
            return
        try:
            self.backend.crear_entidad(SolicitudCrearEntidadDTO(nombre=nombre))
            self.entry_nombre.delete(0, tk.END)
            self._cargar_datos()
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def _eliminar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecciona un registro.")
            return
        eid = int(sel[0])
        if messagebox.askyesno("Confirmar", f"¿Eliminar registro {eid}?"):
            try:
                self.backend.eliminar_entidad(eid)
                self._cargar_datos()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
'''


def _tpl_backend():
    return '''\
"""
backend.py - Adaptador entre User_Interface y Application.

Regla #8: Configura dependencias e inyecta servicios.
Expone métodos públicos limpios para la interfaz.
"""

import logging
from typing import List, Optional, Dict, Any

from Application.servicios.servicio_entidad import ServicioEntidad
from Application.dto.entidad_dto import EntidadDTO, SolicitudCrearEntidadDTO
from Infrastructure.persistencia.base_datos.conexion import obtener_conexion
from Infrastructure.persistencia.repositorios.repositorio_entidad_sql import RepositorioEntidadSQL
from Infrastructure.logging.logger_config import configurar_logging


class Backend:
    """
    Adaptador: oculta la complejidad de Infrastructure a la UI.
    Único punto de entrada para todos los casos de uso.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self._inicializar()

    def _inicializar(self):
        configurar_logging(
            nivel=self.config.get("log_level", "INFO"),
            archivo=self.config.get("log_file"),
        )
        self._conexion       = obtener_conexion(self.config.get("db_path"))
        self._repo_entidad   = RepositorioEntidadSQL(self._conexion)
        self._svc_entidad    = ServicioEntidad(self._repo_entidad)
        self.logger.info("Backend inicializado correctamente.")

    # ── API pública ──

    def obtener_entidades(self, solo_activos: bool = False) -> List[EntidadDTO]:
        return self._svc_entidad.listar(solo_activos)

    def crear_entidad(self, solicitud: SolicitudCrearEntidadDTO) -> EntidadDTO:
        return self._svc_entidad.crear(solicitud)

    def eliminar_entidad(self, entidad_id: int) -> bool:
        return self._svc_entidad.eliminar(entidad_id)

    def cerrar(self):
        if hasattr(self, "_conexion"):
            self._conexion.close()
        self.logger.info("Backend cerrado.")
'''


def _tpl_bootstrap():
    return '''\
"""
bootstrap.py - Orquestador principal de la aplicación.

Regla #9: Configura e inicia según el modo. Sin lógica de negocio.
"""

import sys
import os
import argparse
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend import Backend
from User_Interface.layout import crear_interfaz


def _cargar_env():
    env = Path(".env")
    if env.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env)
        except ImportError:
            pass  # dotenv opcional


def _config_por_modo(modo: str) -> dict:
    return {
        "desarrollo": {"db_path": "data/dev.db",    "log_level": "DEBUG", "log_file": "logs/dev.log"},
        "produccion": {"db_path": os.getenv("DB_PATH", "data/prod.db"),
                       "log_level": "INFO",  "log_file": "logs/prod.log"},
        "test":       {"db_path": ":memory:", "log_level": "ERROR", "log_file": None},
    }.get(modo, {})


def main():
    parser = argparse.ArgumentParser(description="Proyecto — AETHERYON Dev Pattern")
    parser.add_argument("--modo", choices=["desarrollo", "produccion", "test"],
                        default="desarrollo")
    args = parser.parse_args()

    _cargar_env()
    config  = _config_por_modo(args.modo)
    backend = Backend(config)

    try:
        print(f"🚀 Iniciando en modo: {args.modo}")
        root = crear_interfaz(backend)
        root.mainloop()
    except KeyboardInterrupt:
        print("\\n👋 Detenido por el usuario.")
    except Exception as ex:
        print(f"❌ Error: {ex}")
        return 1
    finally:
        backend.cerrar()
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def _tpl_config():
    return '''\
"""
config.py - Configuraciones globales de la aplicación.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

CONFIG = {
    "desarrollo": {
        "db_path":   str(BASE_DIR / "data" / "dev.db"),
        "log_level": "DEBUG",
        "log_file":  str(BASE_DIR / "logs" / "dev.log"),
        "debug":     True,
    },
    "produccion": {
        "db_path":   os.getenv("DB_PATH", str(BASE_DIR / "data" / "prod.db")),
        "log_level": "INFO",
        "log_file":  str(BASE_DIR / "logs" / "prod.log"),
        "debug":     False,
    },
    "test": {
        "db_path":   ":memory:",
        "log_level": "ERROR",
        "log_file":  None,
        "debug":     True,
    },
}
'''


def _tpl_requirements():
    return '''\
# Dependencias del proyecto
# Generado por CLI-Dev-Pattern.py — AETHERYON Dev Pattern

# Core (sin dependencias externas para niveles básicos)
# python >= 3.9

# Opcionales según necesidad:
# python-dotenv>=1.0.0   # Variables de entorno
# pytest>=7.0.0          # Testing
# pytest-cov>=4.0.0      # Cobertura
# flake8>=6.0.0          # Linter
# black>=23.0.0          # Formateador
# requests>=2.28.0       # HTTP cliente
# sqlalchemy>=2.0.0      # ORM alternativo
'''


def _tpl_env():
    return '''\
# .env.example — Copiar a .env y completar valores reales
# Nunca commitear el archivo .env real

DB_PATH=data/prod.db
LOG_LEVEL=INFO
DEBUG=False
SECRET_KEY=cambiar_esto_en_produccion

# Servicios externos (descomentar según necesidad)
# API_KEY=
# SMTP_HOST=
# SMTP_PORT=587
# SMTP_USER=
# SMTP_PASS=
'''


def _tpl_gitignore():
    return '''\
# Python
__pycache__/
*.py[cod]
*.so
.Python
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*~

# Base de datos
*.db
*.sqlite3
*.sqlite
data/

# Logs
*.log
logs/

# Entorno
.env
.env.local
.env.*.local

# Tests
.pytest_cache/
.coverage
htmlcov/

# Distribución
dist/
build/
*.egg-info/

# Sistema
.DS_Store
Thumbs.db
'''


def _tpl_conftest():
    return '''\
"""
Tests/conftest.py
Fixtures compartidos entre todos los tests.

Regla: los tests de dominio no necesitan BD.
Los tests de infrastructure usan BD en memoria (:memory:).
"""

import pytest
import sqlite3
from backend import Backend


@pytest.fixture
def db_memoria():
    """Conexión SQLite en memoria para tests de infrastructure."""
    conn = sqlite3.connect(":memory:")
    yield conn
    conn.close()


@pytest.fixture
def backend_test():
    """Backend configurado para tests."""
    b = Backend({"db_path": ":memory:", "log_level": "ERROR"})
    yield b
    b.cerrar()
'''


def _tpl_test_domain():
    return '''\
"""
Tests/test_domain/test_entidad.py
Pruebas de la capa de Dominio.

Regla: sin mocks, sin BD, sin red. Lógica pura.
"""

import pytest
from Domain.entidades.entidad import Entidad, EstadoEntidad
from Domain.excepciones.excepciones_dominio import NombreInvalido, EstadoInvalido


class TestEntidad:

    def setup_method(self):
        self.entidad = Entidad(id=1, nombre="Entidad Test")

    def test_crear_entidad_valida(self):
        assert self.entidad.nombre == "Entidad Test"
        assert self.entidad.esta_activo is True
        assert self.entidad.estado == EstadoEntidad.ACTIVO

    def test_nombre_invalido_lanza_error(self):
        with pytest.raises(NombreInvalido):
            Entidad(id=None, nombre="x")  # menos de 2 chars

    def test_nombre_vacio_lanza_error(self):
        with pytest.raises(NombreInvalido):
            Entidad(id=None, nombre="")

    def test_desactivar(self):
        self.entidad.desactivar()
        assert self.entidad.esta_activo is False
        assert self.entidad.estado == EstadoEntidad.INACTIVO

    def test_desactivar_dos_veces_lanza_error(self):
        self.entidad.desactivar()
        with pytest.raises(EstadoInvalido):
            self.entidad.desactivar()

    def test_activar_entidad_inactiva(self):
        self.entidad.desactivar()
        self.entidad.activar()
        assert self.entidad.esta_activo is True

    def test_renombrar(self):
        self.entidad.renombrar("Nuevo Nombre")
        assert self.entidad.nombre == "Nuevo Nombre"

    def test_renombrar_invalido(self):
        with pytest.raises(NombreInvalido):
            self.entidad.renombrar("")
'''


def _tpl_test_application():
    return '''\
"""
Tests/test_application/test_servicio_entidad.py
Pruebas de la capa de Aplicación con mocks.
"""

import pytest
from unittest.mock import MagicMock
from Application.servicios.servicio_entidad import ServicioEntidad
from Application.dto.entidad_dto import SolicitudCrearEntidadDTO
from Domain.entidades.entidad import Entidad
from Domain.excepciones.excepciones_dominio import EntidadNoEncontrada


@pytest.fixture
def repo_mock():
    return MagicMock()


@pytest.fixture
def servicio(repo_mock):
    return ServicioEntidad(repo_mock)


class TestServicioEntidad:

    def test_crear_entidad(self, servicio, repo_mock):
        repo_mock.guardar.return_value = Entidad(id=1, nombre="Test")
        resultado = servicio.crear(SolicitudCrearEntidadDTO(nombre="Test"))
        assert resultado.id == 1
        assert resultado.nombre == "Test"
        repo_mock.guardar.assert_called_once()

    def test_obtener_entidad_existente(self, servicio, repo_mock):
        repo_mock.obtener_por_id.return_value = Entidad(id=1, nombre="Test")
        resultado = servicio.obtener(1)
        assert resultado.nombre == "Test"

    def test_obtener_entidad_inexistente(self, servicio, repo_mock):
        repo_mock.obtener_por_id.return_value = None
        with pytest.raises(EntidadNoEncontrada):
            servicio.obtener(99)

    def test_listar_entidades(self, servicio, repo_mock):
        repo_mock.listar.return_value = [
            Entidad(id=1, nombre="A"),
            Entidad(id=2, nombre="B"),
        ]
        resultado = servicio.listar()
        assert len(resultado) == 2

    def test_eliminar_entidad(self, servicio, repo_mock):
        repo_mock.obtener_por_id.return_value = Entidad(id=1, nombre="Test")
        repo_mock.actualizar.return_value = True
        assert servicio.eliminar(1) is True
'''


def _tpl_test_infra():
    return '''\
"""
Tests/test_infrastructure/test_repositorio.py
Pruebas de integración para Infrastructure (BD en memoria).
"""

import pytest
import sqlite3
from Infrastructure.persistencia.repositorios.repositorio_entidad_sql import RepositorioEntidadSQL
from Domain.entidades.entidad import Entidad, EstadoEntidad


@pytest.fixture
def repositorio(db_memoria):
    return RepositorioEntidadSQL(db_memoria)


class TestRepositorioEntidadSQL:

    def test_guardar_y_obtener(self, repositorio):
        entidad = Entidad(id=None, nombre="Test SQL")
        guardada = repositorio.guardar(entidad)
        assert guardada.id is not None
        recuperada = repositorio.obtener_por_id(guardada.id)
        assert recuperada.nombre == "Test SQL"

    def test_listar_todos(self, repositorio):
        repositorio.guardar(Entidad(id=None, nombre="A"))
        repositorio.guardar(Entidad(id=None, nombre="B"))
        assert len(repositorio.listar()) == 2

    def test_listar_solo_activos(self, repositorio):
        e1 = repositorio.guardar(Entidad(id=None, nombre="Activo"))
        e2 = repositorio.guardar(Entidad(id=None, nombre="Inactivo"))
        repositorio.eliminar(e2.id)
        activos = repositorio.listar(solo_activos=True)
        assert len(activos) == 1
        assert activos[0].nombre == "Activo"

    def test_actualizar(self, repositorio):
        e = repositorio.guardar(Entidad(id=None, nombre="Original"))
        e.nombre = "Actualizado"
        repositorio.actualizar(e)
        recuperado = repositorio.obtener_por_id(e.id)
        assert recuperado.nombre == "Actualizado"

    def test_eliminar_logico(self, repositorio):
        e = repositorio.guardar(Entidad(id=None, nombre="A eliminar"))
        repositorio.eliminar(e.id)
        recuperado = repositorio.obtener_por_id(e.id)
        assert recuperado.esta_activo is False
'''


def _tpl_migraciones():
    return '''\
"""
Scripts/migraciones.py
Gestión de migraciones de base de datos.

Uso:
    python Scripts/migraciones.py init
    python Scripts/migraciones.py status
"""

import sys
import os
import sqlite3
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


MIGRACIONES = [
    ("001_crear_entidades", """
        CREATE TABLE IF NOT EXISTS entidades (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre         TEXT    NOT NULL,
            descripcion    TEXT    DEFAULT "",
            estado         TEXT    DEFAULT "activo",
            fecha_creacion TEXT
        );
    """),
]


def aplicar_migraciones(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _migraciones (
            nombre TEXT PRIMARY KEY,
            aplicada_en TEXT
        )
    """)
    conn.commit()

    aplicadas = {r[0] for r in conn.execute("SELECT nombre FROM _migraciones")}

    for nombre, sql in MIGRACIONES:
        if nombre not in aplicadas:
            print(f"  Aplicando: {nombre}")
            conn.executescript(sql)
            from datetime import datetime
            conn.execute("INSERT INTO _migraciones VALUES (?, ?)",
                         (nombre, datetime.now().isoformat()))
            conn.commit()
        else:
            print(f"  Ya aplicada: {nombre}")

    conn.close()
    print("✅ Migraciones completadas.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("comando", choices=["init", "status"])
    parser.add_argument("--db", default="data/dev.db")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.db), exist_ok=True)

    if args.comando == "init":
        aplicar_migraciones(args.db)
    elif args.comando == "status":
        conn = sqlite3.connect(args.db)
        try:
            filas = conn.execute("SELECT nombre, aplicada_en FROM _migraciones").fetchall()
            for f in filas:
                print(f"  ✅ {f[0]} — {f[1]}")
        except Exception:
            print("  Sin migraciones registradas.")
        conn.close()


if __name__ == "__main__":
    main()
'''


def _tpl_seed():
    return '''\
"""
Scripts/seed_data.py
Carga datos de prueba para desarrollo.

Uso:
    python Scripts/seed_data.py
    python Scripts/seed_data.py --limpiar
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import Backend
from Application.dto.entidad_dto import SolicitudCrearEntidadDTO


DATOS_PRUEBA = [
    {"nombre": "Entidad Alpha",   "descripcion": "Primera entidad de prueba"},
    {"nombre": "Entidad Beta",    "descripcion": "Segunda entidad de prueba"},
    {"nombre": "Entidad Gamma",   "descripcion": "Tercera entidad de prueba"},
]


def cargar_datos_prueba(backend: Backend):
    print("📦 Cargando datos de prueba...")
    for dato in DATOS_PRUEBA:
        try:
            e = backend.crear_entidad(SolicitudCrearEntidadDTO(**dato))
            print(f"  ✅ Creada: {e.nombre} (ID: {e.id})")
        except Exception as ex:
            print(f"  ⚠️  {dato['nombre']}: {ex}")
    print("✅ Datos de prueba cargados.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--modo", default="desarrollo")
    args = parser.parse_args()

    backend = Backend({"db_path": "data/dev.db", "log_level": "ERROR"})
    cargar_datos_prueba(backend)
    backend.cerrar()


if __name__ == "__main__":
    main()
'''


def _tpl_readme():
    return '''\
# Proyecto — AETHERYON Dev Pattern

Generado con `CLI-Dev-Pattern.py`.

## Inicio rápido

```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\\Scripts\\activate            # Windows

pip install -r requirements.txt
cp .env.example .env

python Scripts/migraciones.py init
python Scripts/seed_data.py
python bootstrap.py --modo desarrollo
```

## Tests

```bash
pytest Tests/
pytest Tests/ --cov=Application --cov=Domain --cov-report=html
```

## Estructura

Ver `Docs/arquitectura.md` para el detalle de cada capa.
'''


def _tpl_arquitectura():
    return '''\
# Arquitectura — AETHERYON Dev Pattern

## Diagrama de dependencias

```
User_Interface
      │
      ▼
 Application  ←──────────────────┐
      │                          │
      ▼                          │
   Domain               Infrastructure
  (núcleo puro)          (I/O, DB, APIs)
```

## Reglas fundamentales

- **Domain** nunca depende de ninguna otra capa.
- **Application** solo depende de Domain.
- **Infrastructure** implementa contratos de Application.
- **User_Interface** depende de Application (vía backend.py), nunca de Infrastructure.

## Criterios de salud

- ¿Puedo cambiar el proveedor de BD sin tocar Domain?
- ¿Puedo testear Domain sin internet ni BD?
- ¿La UI solo muestra y captura eventos?
- ¿Todo se inyecta, nada se instancia internamente?
'''


# ── Templates MVVM (Nivel 5) ─────────────────

def _tpl_viewmodel_base():
    return '''\
"""
Presentation/viewmodels/viewmodel_base.py
Clase base para todos los ViewModels.

Implementa el patrón Observer: las vistas se suscriben y reciben notificaciones.
"""

from typing import Any, Callable, Dict, List, Optional


class ViewModelBase:
    """
    Base observable para ViewModels.

    Regla: no importa nada de User_Interface.
    Regla: el estado de UI vive aquí, no en la Vista.
    """

    def __init__(self):
        self._suscriptores: List[Callable]    = []
        self._propiedades:  Dict[str, Any]    = {}
        self._errores:      Dict[str, str]    = {}
        self._ocupado:      bool              = False
        self._mensaje:      str               = ""

    # ── Sistema observable ──

    def suscribir(self, callback: Callable) -> None:
        """La Vista llama a este método para recibir cambios."""
        if callback not in self._suscriptores:
            self._suscriptores.append(callback)

    def desuscribir(self, callback: Callable) -> None:
        self._suscriptores = [s for s in self._suscriptores if s != callback]

    def notificar_cambio(self, nombre: str, valor_anterior: Any = None) -> None:
        evento = {
            "nombre":          nombre,
            "valor_anterior":  valor_anterior,
            "valor_nuevo":     self._propiedades.get(nombre),
        }
        for callback in self._suscriptores:
            try:
                callback(evento)
            except Exception as ex:
                print(f"[ViewModelBase] Error en suscriptor: {ex}")

    def establecer_propiedad(self, nombre: str, valor: Any) -> bool:
        """Establece propiedad y notifica solo si cambió."""
        anterior = self._propiedades.get(nombre)
        if anterior != valor:
            self._propiedades[nombre] = valor
            self.notificar_cambio(nombre, anterior)
            return True
        return False

    # ── Estado estándar ──

    @property
    def ocupado(self) -> bool:
        return self._ocupado

    @ocupado.setter
    def ocupado(self, valor: bool):
        if self._ocupado != valor:
            self._ocupado = valor
            self.notificar_cambio("ocupado")

    @property
    def mensaje(self) -> str:
        return self._mensaje

    @mensaje.setter
    def mensaje(self, texto: str):
        self._mensaje = texto
        self.notificar_cambio("mensaje")

    # ── Errores de validación UI ──

    def agregar_error(self, campo: str, mensaje: str) -> None:
        self._errores[campo] = mensaje
        self.notificar_cambio(f"error_{campo}")

    def limpiar_error(self, campo: str) -> None:
        if campo in self._errores:
            del self._errores[campo]
            self.notificar_cambio(f"error_{campo}")

    def limpiar_errores(self) -> None:
        self._errores.clear()
        self.notificar_cambio("errores")

    def tiene_errores(self) -> bool:
        return bool(self._errores)

    def obtener_error(self, campo: str) -> Optional[str]:
        return self._errores.get(campo)
'''


def _tpl_viewmodel():
    return '''\
"""
Presentation/viewmodels/entidad_viewmodel.py
ViewModel para gestión de Entidad.

Regla #16: transforma DTOs en modelos de UI, coordina llamadas al backend.
"""

from typing import List, Optional
from Presentation.viewmodels.viewmodel_base import ViewModelBase
from Presentation.models.ui_entidad import UIEntidad


class EntidadViewModel(ViewModelBase):

    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self._entidades:           List[UIEntidad]     = []
        self._entidad_seleccionada: Optional[UIEntidad] = None
        self._filtro:               str                = ""
        self._modo_edicion:         bool               = False
        self.cargar()

    # ── Propiedades observables ──

    @property
    def entidades(self) -> List[UIEntidad]:
        if not self._filtro:
            return self._entidades
        f = self._filtro.lower()
        return [e for e in self._entidades if f in e.nombre.lower()]

    @property
    def filtro(self) -> str:
        return self._filtro

    @filtro.setter
    def filtro(self, valor: str):
        self._filtro = valor
        self.notificar_cambio("entidades")

    @property
    def entidad_seleccionada(self) -> Optional[UIEntidad]:
        return self._entidad_seleccionada

    @entidad_seleccionada.setter
    def entidad_seleccionada(self, e: Optional[UIEntidad]):
        self._entidad_seleccionada = e
        self.notificar_cambio("entidad_seleccionada")

    @property
    def modo_edicion(self) -> bool:
        return self._modo_edicion

    @modo_edicion.setter
    def modo_edicion(self, valor: bool):
        self._modo_edicion = valor
        self.notificar_cambio("modo_edicion")

    # ── Casos de uso de UI ──

    def cargar(self):
        self.ocupado = True
        self.mensaje = "Cargando..."
        try:
            dtos = self.backend.obtener_entidades()
            self._entidades = [UIEntidad.from_dto(d) for d in dtos]
            self.mensaje = f"{len(self._entidades)} registros cargados."
            self.notificar_cambio("entidades")
        except Exception as ex:
            self.mensaje = f"Error al cargar: {ex}"
        finally:
            self.ocupado = False

    def nueva(self):
        self._entidad_seleccionada = UIEntidad()
        self.modo_edicion = True

    def guardar(self) -> bool:
        if not self._entidad_seleccionada:
            return False

        errores = self._entidad_seleccionada.validar()
        if errores:
            for campo, msg in errores.items():
                self.agregar_error(campo, msg)
            return False

        self.limpiar_errores()
        self.ocupado = True
        self.mensaje = "Guardando..."
        try:
            from Application.dto.entidad_dto import SolicitudCrearEntidadDTO
            if self._entidad_seleccionada.id:
                # TODO: implementar actualizar en backend
                pass
            else:
                dto = self.backend.crear_entidad(
                    SolicitudCrearEntidadDTO(
                        nombre=self._entidad_seleccionada.nombre,
                        descripcion=self._entidad_seleccionada.descripcion,
                    )
                )
                self._entidad_seleccionada.id = dto.id

            self.mensaje = "Guardado correctamente."
            self.modo_edicion = False
            self.cargar()
            return True
        except Exception as ex:
            self.mensaje = f"Error al guardar: {ex}"
            return False
        finally:
            self.ocupado = False

    def eliminar_seleccionada(self) -> bool:
        if not self._entidad_seleccionada or not self._entidad_seleccionada.id:
            return False
        self.ocupado = True
        try:
            self.backend.eliminar_entidad(self._entidad_seleccionada.id)
            self._entidad_seleccionada = None
            self.notificar_cambio("entidad_seleccionada")
            self.mensaje = "Eliminado correctamente."
            self.cargar()
            return True
        except Exception as ex:
            self.mensaje = f"Error al eliminar: {ex}"
            return False
        finally:
            self.ocupado = False
'''


def _tpl_ui_model():
    return '''\
"""
Presentation/models/ui_entidad.py
Modelo de UI para Entidad.

Regla #15: dataclass simple, sin lógica de negocio.
Puede contener validaciones de formato.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict
from Application.dto.entidad_dto import EntidadDTO


@dataclass
class UIEntidad:
    """Modelo de UI. Solo datos y estado de presentación."""
    id:           Optional[int] = None
    nombre:       str           = ""
    descripcion:  str           = ""
    estado:       str           = "activo"
    seleccionado: bool          = False
    editando:     bool          = False

    def validar(self) -> Dict[str, str]:
        """Validaciones de formato (no reglas de negocio)."""
        errores = {}
        if not self.nombre or len(self.nombre.strip()) < 2:
            errores["nombre"] = "Mínimo 2 caracteres."
        if len(self.nombre) > 100:
            errores["nombre"] = "Máximo 100 caracteres."
        return errores

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "nombre":      self.nombre,
            "descripcion": self.descripcion,
            "estado":      self.estado,
        }

    @classmethod
    def from_dto(cls, dto: EntidadDTO) -> "UIEntidad":
        return cls(
            id=dto.id,
            nombre=dto.nombre,
            descripcion=dto.descripcion,
            estado=dto.estado,
        )
'''


def _tpl_validators():
    return '''\
"""
Presentation/models/validators.py
Validadores de formato reutilizables para la UI.

Nota: estas validaciones son de formato (no reglas de negocio).
Las reglas de negocio viven en Domain.
"""

import re
from typing import Optional


def validar_no_vacio(valor: str, campo: str = "Campo") -> Optional[str]:
    if not valor or not valor.strip():
        return f"{campo} es obligatorio."
    return None


def validar_longitud(valor: str, minimo: int = 2, maximo: int = 100,
                     campo: str = "Campo") -> Optional[str]:
    if len(valor) < minimo:
        return f"{campo} debe tener al menos {minimo} caracteres."
    if len(valor) > maximo:
        return f"{campo} no puede superar {maximo} caracteres."
    return None


def validar_email(valor: str) -> Optional[str]:
    patron = r"^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$"
    if not re.match(patron, valor):
        return "Formato de email inválido."
    return None


def validar_entero_positivo(valor: str, campo: str = "Campo") -> Optional[str]:
    try:
        n = int(valor)
        if n <= 0:
            return f"{campo} debe ser un número positivo."
    except ValueError:
        return f"{campo} debe ser un número entero."
    return None
'''


def _tpl_comando_base():
    return '''\
"""
Presentation/commands/comando_base.py
Clase base para el patrón Command.

Los comandos encapsulan acciones complejas con soporte opcional de deshacer.
"""

from abc import ABC, abstractmethod
from typing import Any


class ComandoBase(ABC):
    """
    Comando base. Encapsula una acción de UI.

    Regla #17: expone ejecutar(), puede_ejecutar() y opcionalmente deshacer().
    """

    def __init__(self, viewmodel):
        self.viewmodel   = viewmodel
        self._ejecutado  = False
        self._resultado  = None

    @abstractmethod
    def ejecutar(self, *args, **kwargs) -> Any:
        """Ejecuta el comando."""

    def puede_ejecutar(self) -> bool:
        """Verifica precondiciones antes de ejecutar."""
        return not self.viewmodel.ocupado

    def deshacer(self) -> None:
        """Deshace la acción (implementación opcional)."""

    @property
    def ejecutado(self) -> bool:
        return self._ejecutado

    @property
    def resultado(self) -> Any:
        return self._resultado
'''


def _tpl_comandos():
    return '''\
"""
Presentation/commands/comandos_entidad.py
Comandos para operaciones sobre Entidad.
"""

from Presentation.commands.comando_base import ComandoBase


class ComandoCargar(ComandoBase):
    def ejecutar(self, *args, **kwargs):
        if not self.puede_ejecutar():
            return
        self.viewmodel.cargar()
        self._ejecutado = True


class ComandoGuardar(ComandoBase):
    def __init__(self, viewmodel):
        super().__init__(viewmodel)
        self._respaldo = None

    def ejecutar(self, *args, **kwargs) -> bool:
        if not self.puede_ejecutar():
            return False
        if self.viewmodel.entidad_seleccionada:
            self._respaldo = self.viewmodel.entidad_seleccionada.to_dict()
        resultado = self.viewmodel.guardar()
        if resultado:
            self._ejecutado = True
        self._resultado = resultado
        return resultado

    def deshacer(self):
        if self._ejecutado and self._respaldo:
            self.viewmodel.mensaje = "Operación deshecha."
            self.viewmodel.cargar()


class ComandoEliminar(ComandoBase):
    def puede_ejecutar(self) -> bool:
        return (super().puede_ejecutar()
                and self.viewmodel.entidad_seleccionada is not None
                and self.viewmodel.entidad_seleccionada.id is not None)

    def ejecutar(self, *args, **kwargs) -> bool:
        if not self.puede_ejecutar():
            return False
        resultado = self.viewmodel.eliminar_seleccionada()
        if resultado:
            self._ejecutado = True
        self._resultado = resultado
        return resultado


class ComandoNueva(ComandoBase):
    def ejecutar(self, *args, **kwargs):
        if not self.puede_ejecutar():
            return
        self.viewmodel.nueva()
        self._ejecutado = True
'''


def _tpl_test_viewmodel():
    return '''\
"""
Tests/test_presentation/test_entidad_viewmodel.py
Pruebas del ViewModel sin interfaz gráfica.

Ventaja MVVM: los ViewModels son completamente testeables sin UI.
"""

import pytest
from unittest.mock import MagicMock
from Presentation.viewmodels.entidad_viewmodel import EntidadViewModel
from Application.dto.entidad_dto import EntidadDTO


@pytest.fixture
def backend_mock():
    mock = MagicMock()
    mock.obtener_entidades.return_value = [
        EntidadDTO(id=1, nombre="A", descripcion="", estado="activo", esta_activo=True),
        EntidadDTO(id=2, nombre="B", descripcion="", estado="activo", esta_activo=True),
    ]
    return mock


@pytest.fixture
def viewmodel(backend_mock):
    return EntidadViewModel(backend_mock)


class TestEntidadViewModel:

    def test_carga_inicial(self, viewmodel):
        assert len(viewmodel.entidades) == 2

    def test_filtro(self, viewmodel):
        viewmodel.filtro = "A"
        assert len(viewmodel.entidades) == 1
        assert viewmodel.entidades[0].nombre == "A"

    def test_filtro_vacio_muestra_todos(self, viewmodel):
        viewmodel.filtro = "A"
        viewmodel.filtro = ""
        assert len(viewmodel.entidades) == 2

    def test_nueva_activa_modo_edicion(self, viewmodel):
        viewmodel.nueva()
        assert viewmodel.modo_edicion is True
        assert viewmodel.entidad_seleccionada is not None
        assert viewmodel.entidad_seleccionada.id is None

    def test_notificaciones(self, viewmodel):
        cambios = []
        viewmodel.suscribir(lambda e: cambios.append(e["nombre"]))
        viewmodel.filtro = "test"
        assert "entidades" in cambios

    def test_guardar_con_nombre_invalido(self, viewmodel):
        viewmodel.nueva()
        viewmodel.entidad_seleccionada.nombre = "x"  # inválido
        resultado = viewmodel.guardar()
        assert resultado is False
        assert viewmodel.tiene_errores()
'''


def _tpl_guia_estilo():
    return '''\
# Guía de Estilo — AETHERYON Dev Pattern

## Nomenclatura

| Elemento | Convención | Ejemplo |
|----------|-----------|---------|
| Clases | PascalCase | `ServicioEntidad` |
| Métodos y variables | snake_case | `obtener_por_id` |
| Constantes | MAYUSCULAS | `ESTADO_ACTIVO` |
| Archivos | snake_case.py | `servicio_entidad.py` |

## Importaciones

```python
# ✅ Correcto
from Domain.entidades.entidad import Entidad
from Application.dto.entidad_dto import EntidadDTO

# ❌ Evitar
from ..Domain import Entidad
from Application.servicios import *
```

## Docstrings

```python
def crear(self, solicitud: SolicitudCrearEntidadDTO) -> EntidadDTO:
    """
    Caso de uso: crear una nueva entidad.

    Args:
        solicitud: DTO con nombre y descripción.

    Returns:
        EntidadDTO con los datos de la entidad creada.

    Raises:
        NombreInvalido: si el nombre no cumple las reglas.
    """
```

## Commits

```
feat(entidades): agregar búsqueda por nombre
fix(repositorio): corregir filtro de activos
test(dominio): agregar tests para desactivación
refactor(backend): simplificar inyección de servicios
```
'''


# ─────────────────────────────────────────────
#  GENERADOR DE ESTRUCTURA
# ─────────────────────────────────────────────

def generar_estructura(nivel: int, ruta: Path) -> None:
    """Crea todos los archivos y directorios del nivel indicado."""
    templates = get_templates(nivel)
    creados   = 0
    omitidos  = 0

    for ruta_relativa, contenido in templates.items():
        archivo = ruta / ruta_relativa

        # Crear directorios intermedios
        archivo.parent.mkdir(parents=True, exist_ok=True)

        if archivo.exists():
            omitidos += 1
            print(f"  {c('~', 'yellow')} {ruta_relativa} (ya existe, omitido)")
        else:
            archivo.write_text(contenido, encoding="utf-8")
            creados += 1
            print(f"  {c('✓', 'green')} {ruta_relativa}")

    print()
    print(f"  {c(f'{creados} archivos creados', 'green')}", end="")
    if omitidos:
        print(f"  {c(f'| {omitidos} omitidos', 'yellow')}", end="")
    print()


# ─────────────────────────────────────────────
#  INTERFAZ DE USUARIO
# ─────────────────────────────────────────────

def banner():
    print()
    print(c("  ╔══════════════════════════════════════════╗", "cyan"))
    print(c("  ║     AETHERYON  Dev  Pattern  Generator    ║", "cyan"))
    print(c("  ╚══════════════════════════════════════════╝", "cyan"))
    print()


def mostrar_niveles():
    print(c("  Niveles disponibles:", "bold"))
    print()
    descripciones = {
        1: "Script único con múltiples modos operativos",
        2: "Separación básica lógica / presentación",
        3: "Arquitectura por capas (Domain, Application, Infrastructure, UI)",
        4: "AUDI + Testing, Scripts y Documentación",
        5: "AUDDITS + Capa de Presentación MVVM",
    }
    for n, nombre in NIVELES.items():
        print(f"  {c(str(n), 'cyan')}  {c(nombre, 'bold')}")
        print(f"     {c(descripciones[n], 'dim')}")
    print()


def pedir_nivel() -> int:
    while True:
        try:
            valor = input(c("  ¿Qué nivel de arquitectura quieres? [1-5]: ", "cyan")).strip()
            nivel = int(valor)
            if 1 <= nivel <= 5:
                return nivel
            print(c("  ⚠️  Ingresa un número entre 1 y 5.", "yellow"))
        except ValueError:
            print(c("  ⚠️  Debe ser un número entero.", "yellow"))
        except (EOFError, KeyboardInterrupt):
            print("\n  Cancelado.")
            sys.exit(0)


def pedir_ruta() -> Path:
    print()
    print(c("  ¿Dónde generar el proyecto?", "cyan"))
    print(c("  (Ruta absoluta o relativa. Se crea si no existe)", "dim"))
    while True:
        try:
            valor = input(c("  Ruta: ", "cyan")).strip()
            if not valor:
                print(c("  ⚠️  La ruta no puede estar vacía.", "yellow"))
                continue
            return Path(valor).expanduser().resolve()
        except (EOFError, KeyboardInterrupt):
            print("\n  Cancelado.")
            sys.exit(0)


def confirmar(nivel: int, ruta: Path) -> bool:
    print()
    print(c("  Resumen:", "bold"))
    print(f"  Nivel : {c(str(nivel), 'cyan')} — {NIVELES[nivel]}")
    print(f"  Ruta  : {c(str(ruta), 'cyan')}")
    print()
    try:
        resp = input(c("  ¿Continuar? [S/n]: ", "green")).strip().lower()
        return resp in ("", "s", "si", "sí", "y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generador de templates AETHERYON Dev Pattern",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python CLI-Dev-Pattern.py                          (modo interactivo)
  python CLI-Dev-Pattern.py 3 ./mi_proyecto
  python CLI-Dev-Pattern.py 5 C:\\Users\\usuario\\Documentos\\mi_app
        """,
    )
    parser.add_argument("nivel", nargs="?", type=int, choices=range(1, 6),
                        help="Nivel de arquitectura (1-5)")
    parser.add_argument("ruta",  nargs="?", type=str,
                        help="Ruta de destino del proyecto")
    parser.add_argument("--forzar", action="store_true",
                        help="Sobreescribir archivos existentes sin preguntar")

    args = parser.parse_args()

    # ── Modo directo (argumentos por CLI) ──
    if args.nivel and args.ruta:
        nivel = args.nivel
        ruta  = Path(args.ruta).expanduser().resolve()

    # ── Modo interactivo ──
    else:
        banner()
        mostrar_niveles()
        nivel = pedir_nivel()
        ruta  = pedir_ruta()
        if not confirmar(nivel, ruta):
            print(c("\n  Cancelado.", "yellow"))
            sys.exit(0)

    # ── Crear estructura ──
    print()
    print(c(f"  Generando Nivel {nivel} — {NIVELES[nivel]}", "bold"))
    print(c(f"  → {ruta}", "dim"))
    print()

    ruta.mkdir(parents=True, exist_ok=True)
    generar_estructura(nivel, ruta)

    print()
    print(c("  ✅ Proyecto generado correctamente.", "green"))
    print()

    if nivel >= 4:
        print(c("  Pasos siguientes:", "bold"))
        print("  1.  cd " + str(ruta))
        print("  2.  python -m venv venv")
        print("  3.  pip install -r requirements.txt")
        print("  4.  python Scripts/migraciones.py init")
        print("  5.  python Scripts/seed_data.py")
        print("  6.  python bootstrap.py --modo desarrollo")
        print("  7.  pytest Tests/")
    elif nivel >= 3:
        print(c("  Pasos siguientes:", "bold"))
        print("  1.  cd " + str(ruta))
        print("  2.  python bootstrap.py")
    elif nivel == 2:
        print(c("  Pasos siguientes:", "bold"))
        print("  1.  cd " + str(ruta))
        print("  2.  python frontend.py")
    else:
        print(c("  Pasos siguientes:", "bold"))
        print("  1.  cd " + str(ruta))
        print("  2.  python proyecto.py --modo ui")
    print()


if __name__ == "__main__":
    main()