# AETHERYON Dev Pattern

---

## Tabla Comparativa de Niveles

| Nivel | Nombre            | Equipo   | Complejidad | Testing  | MVVM | Cuándo usarlo                                           |
|-------|-------------------|----------|-------------|----------|------|---------------------------------------------------------|
| 1     | Standalone Script | 1 dev    | Mínima      | No       | No   | Prototipo, validación rápida, scripts de automatización |
| 2     | BF                | 1-2 devs | Baja        | No       | No   | Proyecto pequeño con lógica separada de presentación    |
| 3     | AUDI              | 2-4 devs | Media       | Opcional | No   | Proyecto con dominio definido y crecimiento esperado    |
| 4     | AUDDITS           | 3-6 devs | Alta        | Sí       | No   | Producto en producción con múltiples módulos            |
| 5     | AUDDITS + MVVM    | 4+ devs  | Muy alta    | Sí       | Sí   | Sistema complejo con UI rica y múltiples vistas         |

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

### Ejemplo: Standalone Script con todos los modos

```python
#!/usr/bin/env python3
"""
proyecto.py - Script único con múltiples modos operativos
"""

import sys
import argparse
import json
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== DOMAIN ====================
class TipoUsuario(Enum):
    ADMIN = "admin"
    USUARIO = "usuario"
    INVITADO = "invitado"

@dataclass
class Usuario:
    """Entidad de dominio - contiene reglas de negocio"""
    id: Optional[int]
    nombre: str
    email: str
    tipo: TipoUsuario
    activo: bool = True
    
    def cambiar_email(self, nuevo_email: str) -> None:
        if '@' not in nuevo_email:
            raise ValueError("Email inválido: debe contener @")
        self.email = nuevo_email
    
    def desactivar(self) -> None:
        self.activo = False

# ==================== APPLICATION ====================
class ServicioUsuario:
    """Capa de aplicación - orquesta casos de uso"""
    
    def __init__(self):
        self._usuarios: List[Usuario] = []
        self._next_id = 1
    
    def crear_usuario(self, nombre: str, email: str, tipo: str) -> Usuario:
        if not nombre or len(nombre) < 3:
            raise ValueError("Nombre debe tener al menos 3 caracteres")
        if not email or '@' not in email:
            raise ValueError("Email inválido")
        usuario = Usuario(id=self._next_id, nombre=nombre, email=email, tipo=TipoUsuario(tipo))
        self._usuarios.append(usuario)
        self._next_id += 1
        logger.info(f"Usuario creado: {usuario.nombre} (ID: {usuario.id})")
        return usuario
    
    def listar_usuarios(self, solo_activos: bool = False) -> List[Usuario]:
        if solo_activos:
            return [u for u in self._usuarios if u.activo]
        return self._usuarios.copy()
    
    def obtener_usuario(self, usuario_id: int) -> Optional[Usuario]:
        return next((u for u in self._usuarios if u.id == usuario_id), None)
    
    def eliminar_usuario(self, usuario_id: int) -> bool:
        usuario = self.obtener_usuario(usuario_id)
        if usuario:
            usuario.desactivar()
            return True
        return False

# ==================== INTERFACES ====================
class CLI:
    def __init__(self, servicio: ServicioUsuario):
        self.servicio = servicio
    
    def ejecutar(self, args: argparse.Namespace) -> None:
        comandos = {
            'crear': self._crear,
            'listar': self._listar,
            'obtener': self._obtener,
            'eliminar': self._eliminar
        }
        if args.comando in comandos:
            comandos[args.comando](args)
    
    def _crear(self, args):
        try:
            usuario = self.servicio.crear_usuario(args.nombre, args.email, args.tipo)
            print(f"✅ Usuario creado: {usuario.nombre} (ID: {usuario.id})")
        except ValueError as e:
            print(f"❌ Error: {e}")
    
    def _listar(self, args):
        usuarios = self.servicio.listar_usuarios(args.solo_activos)
        if not usuarios:
            print("No hay usuarios")
            return
        print(f"\n{'ID':<4} {'NOMBRE':<20} {'EMAIL':<25} {'TIPO':<10} {'ESTADO':<8}")
        print("-" * 70)
        for u in usuarios:
            estado = "ACTIVO" if u.activo else "INACTIVO"
            print(f"{u.id:<4} {u.nombre:<20} {u.email:<25} {u.tipo.value:<10} {estado:<8}")
    
    def _obtener(self, args):
        usuario = self.servicio.obtener_usuario(args.id)
        if usuario:
            print(f"\nID: {usuario.id}\nNombre: {usuario.nombre}\nEmail: {usuario.email}")
        else:
            print(f"❌ Usuario con ID {args.id} no encontrado")
    
    def _eliminar(self, args):
        if self.servicio.eliminar_usuario(args.id):
            print(f"✅ Usuario {args.id} desactivado")
        else:
            print(f"❌ Usuario con ID {args.id} no encontrado")

# ==================== MAIN ====================
def main():
    parser = argparse.ArgumentParser(description='Sistema de Gestión de Usuarios')
    parser.add_argument('--modo', choices=['cli', 'ui', 'batch'], default='cli')
    subparsers = parser.add_subparsers(dest='comando')
    
    crear_p = subparsers.add_parser('crear')
    crear_p.add_argument('nombre')
    crear_p.add_argument('email')
    crear_p.add_argument('tipo', choices=['admin', 'usuario', 'invitado'])
    
    listar_p = subparsers.add_parser('listar')
    listar_p.add_argument('--solo-activos', action='store_true')
    
    obtener_p = subparsers.add_parser('obtener')
    obtener_p.add_argument('id', type=int)
    
    eliminar_p = subparsers.add_parser('eliminar')
    eliminar_p.add_argument('id', type=int)
    
    args = parser.parse_args()
    servicio = ServicioUsuario()
    
    if args.comando:
        CLI(servicio).ejecutar(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
```

### Ejemplo de uso

```bash
python proyecto.py crear "Juan Pérez" "juan@email.com" admin
python proyecto.py listar
python proyecto.py listar --solo-activos
python proyecto.py obtener 1
python proyecto.py eliminar 1
```

### Estructura

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

### Ejemplo: Backend-Frontend con Tkinter

**backend.py**
```python
"""
backend.py - Lógica de negocio y persistencia
Independiente de la interfaz de usuario
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any

@dataclass
class Tarea:
    id: Optional[int]
    titulo: str
    descripcion: str = ""
    completada: bool = False
    fecha_creacion: str = ""
    
    def __post_init__(self):
        if not self.fecha_creacion:
            self.fecha_creacion = datetime.now().isoformat()

class GestorTareas:
    def __init__(self):
        self._tareas: List[Tarea] = []
        self._next_id = 1
    
    def agregar(self, titulo: str, descripcion: str = "") -> Tarea:
        if not titulo or len(titulo.strip()) == 0:
            raise ValueError("El título no puede estar vacío")
        tarea = Tarea(id=self._next_id, titulo=titulo.strip(), descripcion=descripcion)
        self._tareas.append(tarea)
        self._next_id += 1
        return tarea
    
    def completar(self, tarea_id: int) -> bool:
        tarea = self._obtener_por_id(tarea_id)
        if tarea:
            tarea.completada = not tarea.completada
            return True
        return False
    
    def eliminar(self, tarea_id: int) -> bool:
        tarea = self._obtener_por_id(tarea_id)
        if tarea:
            self._tareas.remove(tarea)
            return True
        return False
    
    def buscar(self, texto: str) -> List[Tarea]:
        texto_lower = texto.lower()
        return [t for t in self._tareas
                if texto_lower in t.titulo.lower() or texto_lower in t.descripcion.lower()]
    
    def obtener_todas(self) -> List[Tarea]: return self._tareas.copy()
    def obtener_pendientes(self) -> List[Tarea]: return [t for t in self._tareas if not t.completada]
    def obtener_completadas(self) -> List[Tarea]: return [t for t in self._tareas if t.completada]
    def _obtener_por_id(self, tarea_id: int) -> Optional[Tarea]:
        return next((t for t in self._tareas if t.id == tarea_id), None)
    
    def estadisticas(self) -> Dict[str, Any]:
        total = len(self._tareas)
        completadas = len([t for t in self._tareas if t.completada])
        return {
            'total': total,
            'completadas': completadas,
            'pendientes': total - completadas,
            'porcentaje_completado': (completadas / total * 100) if total > 0 else 0
        }

class Backend:
    """Interfaz unificada para el frontend"""
    def __init__(self):
        self.gestor = GestorTareas()
    
    def obtener_tareas(self, filtro: str = "todas") -> List[Tarea]:
        filtros = {"todas": self.gestor.obtener_todas,
                   "pendientes": self.gestor.obtener_pendientes,
                   "completadas": self.gestor.obtener_completadas}
        return filtros.get(filtro, self.gestor.obtener_todas)()
    
    def crear_tarea(self, titulo: str, descripcion: str = "") -> Tarea:
        return self.gestor.agregar(titulo, descripcion)
    
    def toggle_tarea(self, tarea_id: int) -> bool:
        return self.gestor.completar(tarea_id)
    
    def borrar_tarea(self, tarea_id: int) -> bool:
        return self.gestor.eliminar(tarea_id)
    
    def buscar_tareas(self, texto: str) -> List[Tarea]:
        return self.gestor.buscar(texto)
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        return self.gestor.estadisticas()
```

**frontend.py**
```python
"""
frontend.py - Interfaz de usuario con Tkinter
Consume la API del backend sin conocer implementación interna
"""

import tkinter as tk
from tkinter import ttk, messagebox
from backend import Backend

class AplicacionTareas:
    def __init__(self):
        self.backend = Backend()
        self.filtro_actual = "todas"
        self._crear_ventana()
        self._crear_widgets()
        self._cargar_tareas()
    
    def _crear_ventana(self):
        self.root = tk.Tk()
        self.root.title("Gestor de Tareas")
        self.root.geometry("800x600")
    
    def _crear_widgets(self):
        # Barra superior
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, pady=5, padx=10)
        
        ttk.Label(toolbar, text="Título:").pack(side=tk.LEFT)
        self.entry_titulo = ttk.Entry(toolbar, width=30)
        self.entry_titulo.pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="➕ Agregar", command=self._agregar_tarea).pack(side=tk.LEFT)
        
        # Tabla
        self.tree = ttk.Treeview(self.root,
            columns=('id', 'titulo', 'estado'), show='headings', height=20)
        self.tree.heading('id', text='ID')
        self.tree.heading('titulo', text='Título')
        self.tree.heading('estado', text='Estado')
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10)
        
        # Barra de estado
        self.lbl_stats = ttk.Label(self.root, text="")
        self.lbl_stats.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
    
    def _cargar_tareas(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        tareas = self.backend.obtener_tareas(self.filtro_actual)
        for t in tareas:
            estado = "✅ Completada" if t.completada else "⏳ Pendiente"
            self.tree.insert('', 'end', values=(t.id, t.titulo, estado), iid=str(t.id))
        stats = self.backend.obtener_estadisticas()
        self.lbl_stats.config(text=f"Total: {stats['total']} | ✅ {stats['completadas']} | ⏳ {stats['pendientes']}")
    
    def _agregar_tarea(self):
        titulo = self.entry_titulo.get().strip()
        if not titulo:
            messagebox.showwarning("Advertencia", "El título es obligatorio")
            return
        self.backend.crear_tarea(titulo)
        self.entry_titulo.delete(0, tk.END)
        self._cargar_tareas()
    
    def ejecutar(self):
        self.root.mainloop()

if __name__ == '__main__':
    AplicacionTareas().ejecutar()
```

### Estructura

```
proyecto/
│
├── backend.py
└── frontend.py
```

---

## Nivel 3 — Patrón AUDI
Arquitectura por capas fundamentales.

### Cuándo escalar al Nivel 4
Escalar cuando el equipo necesite pruebas automatizadas, cuando haya scripts de migración o seed data recurrentes, o cuando la documentación interna se vuelva necesaria para onboarding.

### Principios Arquitectónicos Fundamentales

Modularidad por responsabilidad, no por tipo técnico. Cada módulo debe tener una única razón para cambiar.

**Regla central:**
- Si **decide** → Domain.
- Si **coordina** → Application.
- Si **ejecuta I/O o integra tecnología** → Infrastructure.
- Si **representa estado o muestra información** → Presentation / User_Interface.

La asincronía no es una capa arquitectónica sino una decisión técnica:
- I/O → async.
- Cálculo puro → sync.

**Separación crítica:**
- Identidad del sistema, reglas y políticas deben estar desacopladas del proveedor tecnológico.
- El proveedor externo puede cambiar sin alterar reglas.
- Las decisiones deben poder testearse sin red.

**Criterios de salud arquitectónica:**
- ¿Puedo cambiar proveedor sin tocar reglas?
- ¿Puedo cambiar reglas sin tocar infraestructura?
- ¿Puedo testear dominio sin internet?
- ¿La UI conoce lógica que no debería?

Un sistema funcional ejecuta. Un sistema evolutivo se adapta. La diferencia es la separación clara de responsabilidades.

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

### Ejemplo: Sistema de Reservas con Capas AUDI

**Domain/entidades/reserva.py**
```python
"""
Domain/entidades/reserva.py - Entidades y reglas de negocio
"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional
from enum import Enum

class EstadoReserva(Enum):
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    CANCELADA = "cancelada"
    COMPLETADA = "completada"

class TipoHabitacion(Enum):
    INDIVIDUAL = "individual"
    DOBLE = "doble"
    SUITE = "suite"

@dataclass
class Cliente:
    id: Optional[int]
    nombre: str
    email: str
    telefono: str
    
    def validar_email(self) -> bool:
        return '@' in self.email and '.' in self.email
    
    def validar_telefono(self) -> bool:
        return len(self.telefono) >= 9 and self.telefono.isdigit()

@dataclass
class Habitacion:
    id: Optional[int]
    numero: str
    tipo: TipoHabitacion
    precio_noche: float
    disponible: bool = True
    
    def calcular_precio(self, noches: int) -> float:
        precio_base = self.precio_noche * noches
        if noches > 7:
            precio_base *= 0.9  # 10% descuento por estancia larga
        return precio_base

@dataclass
class Reserva:
    id: Optional[int]
    cliente_id: int
    habitacion_id: int
    fecha_inicio: date
    fecha_fin: date
    estado: EstadoReserva = EstadoReserva.PENDIENTE
    fecha_creacion: datetime = None
    
    def __post_init__(self):
        if not self.fecha_creacion:
            self.fecha_creacion = datetime.now()
    
    @property
    def noches(self) -> int:
        return (self.fecha_fin - self.fecha_inicio).days
    
    def confirmar(self) -> None:
        if self.estado != EstadoReserva.PENDIENTE:
            raise ValueError("Solo se pueden confirmar reservas pendientes")
        self.estado = EstadoReserva.CONFIRMADA
    
    def cancelar(self) -> None:
        if self.estado == EstadoReserva.COMPLETADA:
            raise ValueError("No se puede cancelar una reserva completada")
        self.estado = EstadoReserva.CANCELADA
    
    def solapa_con(self, otra: 'Reserva') -> bool:
        return not (self.fecha_fin <= otra.fecha_inicio or
                   self.fecha_inicio >= otra.fecha_fin)

# Domain/excepciones/excepciones_dominio.py
class ErrorDominio(Exception):
    pass

class ClienteNoEncontrado(ErrorDominio):
    def __init__(self, cliente_id: int):
        super().__init__(f"Cliente con ID {cliente_id} no encontrado")

class HabitacionNoDisponible(ErrorDominio):
    def __init__(self, habitacion_id: int, fecha_inicio: date, fecha_fin: date):
        super().__init__(f"Habitación {habitacion_id} no disponible entre {fecha_inicio} y {fecha_fin}")

class FechasInvalidas(ErrorDominio):
    def __init__(self):
        super().__init__("La fecha de fin debe ser posterior a la fecha de inicio")
```

**Application/interfaces/repositorios.py**
```python
from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import date
from Domain.entidades.reserva import Cliente, Habitacion, Reserva

class RepositorioCliente(ABC):
    @abstractmethod
    def obtener_por_id(self, cliente_id: int) -> Optional[Cliente]: pass
    @abstractmethod
    def guardar(self, cliente: Cliente) -> Cliente: pass
    @abstractmethod
    def listar(self) -> List[Cliente]: pass

class RepositorioHabitacion(ABC):
    @abstractmethod
    def obtener_por_id(self, habitacion_id: int) -> Optional[Habitacion]: pass
    @abstractmethod
    def listar_disponibles(self, fecha_inicio: date, fecha_fin: date) -> List[Habitacion]: pass
    @abstractmethod
    def guardar(self, habitacion: Habitacion) -> Habitacion: pass

class RepositorioReserva(ABC):
    @abstractmethod
    def obtener_por_id(self, reserva_id: int) -> Optional[Reserva]: pass
    @abstractmethod
    def obtener_por_habitacion(self, habitacion_id: int,
                               fecha_inicio: date, fecha_fin: date) -> List[Reserva]: pass
    @abstractmethod
    def guardar(self, reserva: Reserva) -> Reserva: pass
    @abstractmethod
    def actualizar_estado(self, reserva_id: int, nuevo_estado) -> bool: pass
```

**Application/servicios/servicio_reserva.py**
```python
from datetime import date
from typing import List
import logging

from Domain.entidades.reserva import (
    Cliente, Habitacion, Reserva, EstadoReserva,
    ClienteNoEncontrado, HabitacionNoDisponible, FechasInvalidas
)
from Application.interfaces.repositorios import (
    RepositorioCliente, RepositorioHabitacion, RepositorioReserva
)
from Application.dto.reserva_dto import ReservaDTO, SolicitudReservaDTO

class ServicioReserva:
    """Casos de uso para gestión de reservas"""
    
    def __init__(self, repo_cliente: RepositorioCliente,
                 repo_habitacion: RepositorioHabitacion,
                 repo_reserva: RepositorioReserva):
        self.repo_cliente = repo_cliente
        self.repo_habitacion = repo_habitacion
        self.repo_reserva = repo_reserva
        self.logger = logging.getLogger(__name__)
    
    def crear_reserva(self, solicitud: SolicitudReservaDTO) -> ReservaDTO:
        self.logger.info(f"Creando reserva para cliente {solicitud.cliente_id}")
        
        if solicitud.fecha_fin <= solicitud.fecha_inicio:
            raise FechasInvalidas()
        
        cliente = self.repo_cliente.obtener_por_id(solicitud.cliente_id)
        if not cliente:
            raise ClienteNoEncontrado(solicitud.cliente_id)
        
        reservas_existentes = self.repo_reserva.obtener_por_habitacion(
            solicitud.habitacion_id, solicitud.fecha_inicio, solicitud.fecha_fin)
        if reservas_existentes:
            raise HabitacionNoDisponible(solicitud.habitacion_id,
                                         solicitud.fecha_inicio, solicitud.fecha_fin)
        
        habitacion = self.repo_habitacion.obtener_por_id(solicitud.habitacion_id)
        reserva = Reserva(
            id=None,
            cliente_id=cliente.id,
            habitacion_id=habitacion.id,
            fecha_inicio=solicitud.fecha_inicio,
            fecha_fin=solicitud.fecha_fin,
            estado=EstadoReserva.PENDIENTE
        )
        
        reserva_guardada = self.repo_reserva.guardar(reserva)
        self.logger.info(f"Reserva creada con ID {reserva_guardada.id}")
        return ReservaDTO.desde_entidad(reserva_guardada, cliente, habitacion)
    
    def confirmar_reserva(self, reserva_id: int) -> ReservaDTO:
        reserva = self.repo_reserva.obtener_por_id(reserva_id)
        if not reserva:
            raise ValueError(f"Reserva {reserva_id} no encontrada")
        reserva.confirmar()
        self.repo_reserva.actualizar_estado(reserva_id, reserva.estado)
        cliente = self.repo_cliente.obtener_por_id(reserva.cliente_id)
        habitacion = self.repo_habitacion.obtener_por_id(reserva.habitacion_id)
        return ReservaDTO.desde_entidad(reserva, cliente, habitacion)
```

**Infrastructure/persistencia/repositorios_sql.py**
```python
import sqlite3
from typing import Optional, List
from datetime import date, datetime

from Domain.entidades.reserva import Cliente, Habitacion, Reserva, EstadoReserva, TipoHabitacion
from Application.interfaces.repositorios import RepositorioCliente, RepositorioReserva

class RepositorioClienteSQL(RepositorioCliente):
    def __init__(self, conexion: sqlite3.Connection):
        self.conn = conexion
        self._crear_tabla()
    
    def _crear_tabla(self):
        self.conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                telefono TEXT
            )
        """)
        self.conn.commit()
    
    def obtener_por_id(self, cliente_id: int) -> Optional[Cliente]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, nombre, email, telefono FROM clientes WHERE id = ?", (cliente_id,))
        fila = cursor.fetchone()
        if fila:
            return Cliente(id=fila[0], nombre=fila[1], email=fila[2], telefono=fila[3] or "")
        return None
    
    def guardar(self, cliente: Cliente) -> Cliente:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO clientes (nombre, email, telefono) VALUES (?, ?, ?)",
            (cliente.nombre, cliente.email, cliente.telefono)
        )
        self.conn.commit()
        cliente.id = cursor.lastrowid
        return cliente
    
    def listar(self) -> List[Cliente]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, nombre, email, telefono FROM clientes")
        return [Cliente(id=f[0], nombre=f[1], email=f[2], telefono=f[3] or "")
                for f in cursor.fetchall()]

class RepositorioReservaSQL(RepositorioReserva):
    def __init__(self, conexion: sqlite3.Connection):
        self.conn = conexion
        self._crear_tabla()
    
    def _crear_tabla(self):
        self.conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS reservas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                habitacion_id INTEGER NOT NULL,
                fecha_inicio TEXT NOT NULL,
                fecha_fin TEXT NOT NULL,
                estado TEXT NOT NULL,
                fecha_creacion TEXT
            )
        """)
        self.conn.commit()
    
    def obtener_por_habitacion(self, habitacion_id: int,
                               fecha_inicio: date, fecha_fin: date) -> List[Reserva]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, cliente_id, habitacion_id, fecha_inicio, fecha_fin, estado, fecha_creacion
            FROM reservas WHERE habitacion_id = ?
            AND estado IN ('pendiente', 'confirmada')
            AND NOT (fecha_fin <= ? OR fecha_inicio >= ?)
        """, (habitacion_id, fecha_inicio.isoformat(), fecha_fin.isoformat()))
        return [Reserva(id=f[0], cliente_id=f[1], habitacion_id=f[2],
                        fecha_inicio=date.fromisoformat(f[3]),
                        fecha_fin=date.fromisoformat(f[4]),
                        estado=EstadoReserva(f[5]))
                for f in cursor.fetchall()]
    
    def guardar(self, reserva: Reserva) -> Reserva:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO reservas (cliente_id, habitacion_id, fecha_inicio, fecha_fin, estado) VALUES (?, ?, ?, ?, ?)",
            (reserva.cliente_id, reserva.habitacion_id,
             reserva.fecha_inicio.isoformat(), reserva.fecha_fin.isoformat(), reserva.estado.value)
        )
        self.conn.commit()
        reserva.id = cursor.lastrowid
        return reserva
    
    def actualizar_estado(self, reserva_id: int, nuevo_estado) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("UPDATE reservas SET estado = ? WHERE id = ?",
                       (nuevo_estado.value, reserva_id))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def obtener_por_id(self, reserva_id: int) -> Optional[Reserva]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, cliente_id, habitacion_id, fecha_inicio, fecha_fin, estado FROM reservas WHERE id = ?",
            (reserva_id,))
        fila = cursor.fetchone()
        if fila:
            return Reserva(id=fila[0], cliente_id=fila[1], habitacion_id=fila[2],
                           fecha_inicio=date.fromisoformat(fila[3]),
                           fecha_fin=date.fromisoformat(fila[4]),
                           estado=EstadoReserva(fila[5]))
        return None
```

### Estructura

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

Antipatrón frecuente: un servicio que valida, persiste y notifica en el mismo método.
```python
# ❌ MAL — tres responsabilidades en un método
class ServicioUsuario:
    def registrar(self, datos):
        if not datos.email: raise ValueError()   # validación
        self.db.guardar(datos)                    # persistencia
        self.email.enviar_bienvenida()            # notificación

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

```python
# Domain/entidades/usuario.py — No importa nada externo
from dataclasses import dataclass

@dataclass
class Usuario:
    nombre: str
    email: str

# Application/servicios/servicio_usuario.py — Solo importa Domain
from Domain.entidades.usuario import Usuario
from Application.interfaces.repositorio_usuario import RepositorioUsuario

# Infrastructure/persistencia/repositorio_usuario_sql.py — Implementa contratos
from Domain.entidades.usuario import Usuario
from Application.interfaces.repositorio_usuario import RepositorioUsuario

# User_Interface/vistas/vista_usuarios.py — Consume Application
from Application.dto.usuario_dto import UsuarioDTO
from backend import Backend
```

**Regla #3 — Nomenclatura**
- Clases → PascalCase.
- Métodos y variables → snake_case.
- Constantes → MAYUSCULAS.
- Archivos → snake_case.py.

**Regla #4 — Importaciones Correctas**
```python
# ✅ Correcto
from Domain.entidades import Usuario
from Application.dto import UsuarioDTO
from Infrastructure.persistencia.repositorios import RepositorioUsuarioSQL

# ❌ Evitar
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

**Regla #7 — DTOs vs Entidades**
- Las entidades de dominio no se exponen directamente a la UI.
- Los DTOs transportan datos entre capas.
- Las entidades contienen lógica; los DTOs solo estructura.

```python
# Domain — con lógica de negocio
class Usuario:
    def cambiar_password(self, password_nueva):
        if len(password_nueva) < 8:
            raise ValueError("Password demasiado corto")
        self._password_hash = hash(password_nueva)
        self._intentos_fallidos = 0

# Application — solo datos, sin lógica
@dataclass
class UsuarioDTO:
    id: int
    nombre: str
    email: str
    esta_bloqueado: bool
    
    @classmethod
    def desde_entidad(cls, usuario: Usuario):
        return cls(id=usuario.id, nombre=usuario.nombre,
                   email=usuario.email, esta_bloqueado=usuario.esta_bloqueado)
    
    def to_dict(self) -> dict:
        return {'id': self.id, 'nombre': self.nombre,
                'email': self.email, 'bloqueado': self.esta_bloqueado}
```

**Regla #8 — backend.py como Adaptador**
- Actúa como capa de adaptación entre UI y Application.
- Configura dependencias.
- Expone métodos públicos limpios para la interfaz.

```python
# backend.py
class Backend:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._inicializar_logging()
        self._inicializar_servicios()
    
    def _inicializar_servicios(self):
        self.conexion = obtener_conexion(self.config.get('db_path'))
        self.repo_usuario = RepositorioUsuarioSQL(self.conexion)
        self.servicio_usuario = ServicioUsuario(self.repo_usuario)
    
    def obtener_usuarios(self, filtros=None) -> List[UsuarioDTO]:
        try:
            usuarios = self.servicio_usuario.listar(filtros)
            return [UsuarioDTO.desde_entidad(u) for u in usuarios]
        except Exception as e:
            self.logger.error(f"Error obteniendo usuarios: {e}")
            return []
    
    def crear_usuario(self, datos: Dict) -> Optional[UsuarioDTO]:
        solicitud = SolicitudUsuarioDTO.desde_dict(datos)
        usuario = self.servicio_usuario.crear(solicitud)
        return UsuarioDTO.desde_entidad(usuario)
    
    def cerrar(self):
        if hasattr(self, 'conexion'):
            self.conexion.close()
```

**Regla #9 — bootstrap.py como Orquestador**
- Configura logging.
- Inicializa Backend.
- Levanta la UI o modo operativo correspondiente.

```python
# bootstrap.py
class Application:
    def __init__(self):
        self.backend = None
        self._cargar_configuracion()
    
    def _cargar_configuracion(self):
        from dotenv import load_dotenv
        if Path('.env').exists():
            load_dotenv('.env')
    
    def inicializar(self, modo: str = "desarrollo"):
        config = {
            "desarrollo": {"db_path": "data/dev.db", "log_level": "DEBUG"},
            "produccion": {"db_path": os.getenv("DB_PATH"), "log_level": "INFO"},
            "test":       {"db_path": ":memory:", "log_level": "ERROR"}
        }.get(modo, {})
        self.backend = Backend(config)
        print(f"✅ Aplicación inicializada en modo: {modo}")
    
    def ejecutar(self):
        app = crear_interfaz(self.backend)
        app.mainloop()
    
    def cerrar(self):
        if self.backend:
            self.backend.cerrar()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--modo', choices=['desarrollo', 'produccion', 'test'], default='desarrollo')
    args = parser.parse_args()
    app = Application()
    app.inicializar(modo=args.modo)
    sys.exit(app.ejecutar())

if __name__ == "__main__":
    main()
```

**Regla #10 — Pruebas**
- Cada módulo tiene su archivo de test.
- Pruebas independientes y repetibles.
- Uso de mocks para servicios externos.
- Cobertura recomendada ≥ 80%.

```python
# Tests/test_domain/test_usuario.py
import pytest
from Domain.entidades.usuario import Usuario, EmailInvalido
from Domain.value_objects.email import Email

class TestUsuario:
    def setup_method(self):
        self.usuario = Usuario(id=1, nombre="Juan Pérez", email=Email("test@example.com"))
    
    def test_crear_usuario_valido(self):
        assert self.usuario.nombre == "Juan Pérez"
        assert self.usuario.activo is True
    
    def test_cambiar_email_invalido_lanza_error(self):
        with pytest.raises(EmailInvalido):
            self.usuario.cambiar_email(Email("email-invalido"))
    
    def test_desactivar_usuario(self):
        self.usuario.desactivar()
        assert self.usuario.activo is False

# Tests/test_application/test_servicio_usuario.py
import pytest
from unittest.mock import MagicMock, patch
from Application.servicios.servicio_usuario import ServicioUsuario
from Domain.entidades.usuario import Usuario
from Domain.value_objects.email import Email

@pytest.fixture
def mock_repositorio():
    return MagicMock()

@pytest.fixture
def servicio(mock_repositorio):
    return ServicioUsuario(mock_repositorio)

class TestServicioUsuario:
    def test_crear_usuario_exitoso(self, servicio, mock_repositorio):
        mock_repositorio.guardar.return_value = Usuario(
            id=1, nombre="Test", email=Email("test@e.com"))
        resultado = servicio.crear({"nombre": "Test", "email": "test@e.com"})
        assert resultado.id == 1
        mock_repositorio.guardar.assert_called_once()

# Tests/test_infrastructure/test_repositorios.py
@pytest.fixture
def db_conexion():
    conn = sqlite3.connect(":memory:")
    conn.cursor().execute("""
        CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
            activo BOOLEAN DEFAULT TRUE
        )""")
    conn.commit()
    yield conn
    conn.close()

class TestRepositorioUsuarioSQL:
    def test_guardar_y_obtener_usuario(self, repositorio):
        usuario = Usuario(id=None, nombre="Test", email=Email("test@example.com"))
        guardado = repositorio.guardar(usuario)
        assert guardado.id is not None
        recuperado = repositorio.obtener_por_id(guardado.id)
        assert recuperado.nombre == "Test"
```

**Regla #11 — Documentación**
- Docstrings obligatorios en servicios públicos.
- Tipado explícito en funciones críticas.

```python
def procesar_pago(
    usuario_id: int,
    monto: float,
    metodo_pago: str,
    token_tarjeta: Optional[str] = None
) -> Dict[str, Any]:
    """
    Procesa un pago para un usuario específico.
    
    Args:
        usuario_id: Identificador único del usuario en la base de datos.
        monto: Cantidad a cobrar. Debe ser mayor a 0 y menor a 10000.
        metodo_pago: 'tarjeta', 'transferencia' o 'efectivo'.
        token_tarjeta: Token requerido solo para método 'tarjeta'.
    
    Returns:
        Dict con campos: exitoso (bool), transaccion_id (str), mensaje (str).
    
    Raises:
        UsuarioNoEncontrado: Si el usuario_id no existe.
        PagoRechazado: Si la pasarela rechaza la transacción.
    
    Example:
        >>> resultado = procesar_pago(123, 99.99, 'tarjeta', 'tok_visa_123')
        >>> if resultado['exitoso']:
        ...     print(resultado['transaccion_id'])
    """
    pass
```

**Regla #12 — Git Workflow**
- main → Producción.
- develop → Integración.
- feature/* → Nuevas funcionalidades.
- hotfix/* → Correcciones urgentes.
- release/* → Preparación de versiones.

```bash
# Convenciones de commits: tipo(alcance): descripción
feat(usuarios): añadir búsqueda por email
fix(pagos): corregir cálculo de impuestos
docs(api): actualizar documentación de endpoints
test(usuarios): añadir pruebas para registro
refactor(backend): simplificar inyección de dependencias
```

### Flujo de Inicialización

```bash
python -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate           # Windows

pip install -r requirements.txt
cp .env.example .env

python Scripts/migraciones.py init
python Scripts/seed_data.py
python bootstrap.py --modo desarrollo

pytest Tests/
pytest Tests/ --cov=Application --cov=Domain --cov-report=html
flake8 Application/ Domain/ Infrastructure/
```

### Estructura

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

### Reglas MVVM

**Regla #13 — Separación MVVM**
Vista → ViewModel → Modelo.
- La Vista contiene solo widgets y lógica de presentación.
- El ViewModel contiene estado observable y lógica de UI.
- El Modelo contiene datos (UI o negocio según capa).
- La Vista nunca accede directamente a Domain o Infrastructure.

```python
# Vista (User_Interface) — solo widgets y binding
class VistaUsuarios:
    def __init__(self, parent, viewmodel):
        self.viewmodel = viewmodel
        self.viewmodel.suscribir(self._on_cambio)
        self._crear_widgets()
    
    def _on_cambio(self, evento):
        if evento['nombre'] == 'usuarios':
            self._actualizar_tabla()

# ViewModel (Presentation) — estado y lógica de UI
class UsuarioViewModel(ViewModelBase):
    def cargar_usuarios(self):
        self._usuarios = self.backend.obtener_usuarios()
        self.notificar_cambio('usuarios')
```

**Regla #14 — ViewModelBase obligatorio**
```python
# Presentation/viewmodels/viewmodel_base.py
class ViewModelBase:
    def __init__(self):
        self._suscriptores = []
        self._propiedades = {}
        self._errores = {}
        self._ocupado = False
        self._mensaje_estado = ""
    
    def suscribir(self, callback):
        self._suscriptores.append(callback)
    
    def notificar_cambio(self, nombre_propiedad, valor_anterior=None):
        evento = {'nombre': nombre_propiedad, 'valor_anterior': valor_anterior,
                  'valor_nuevo': self._propiedades.get(nombre_propiedad)}
        for callback in self._suscriptores:
            try:
                callback(evento)
            except Exception as e:
                print(f"Error notificando: {e}")
    
    def establecer_propiedad(self, nombre, valor):
        valor_anterior = self._propiedades.get(nombre)
        if valor_anterior != valor:
            self._propiedades[nombre] = valor
            self.notificar_cambio(nombre, valor_anterior)
            return True
        return False
    
    @property
    def ocupado(self): return self._ocupado
    @ocupado.setter
    def ocupado(self, valor): self.establecer_propiedad('_ocupado', valor)
    
    @property
    def mensaje_estado(self): return self._mensaje_estado
    @mensaje_estado.setter
    def mensaje_estado(self, msg): self.establecer_propiedad('_mensaje_estado', msg)
    
    def agregar_error(self, propiedad, mensaje):
        self._errores[propiedad] = mensaje
        self.notificar_cambio(f"error_{propiedad}")
```

**Regla #15 — Modelos de UI**
```python
# Presentation/models/ui_usuario.py
@dataclass
class UIUsuario:
    id: Optional[int] = None
    nombre: str = ""
    email: str = ""
    activo: bool = True
    seleccionado: bool = False
    editando: bool = False
    
    def validar_formato(self) -> dict:
        errores = {}
        if self.nombre and len(self.nombre.strip()) < 3:
            errores['nombre'] = "Mínimo 3 caracteres"
        if self.email and not re.match(r'^[^@]+@[^@]+\.[^@]+$', self.email):
            errores['email'] = "Formato email inválido"
        return errores
    
    def to_dict(self) -> dict:
        return {'id': self.id, 'nombre': self.nombre, 'email': self.email, 'activo': self.activo}
    
    @classmethod
    def from_dto(cls, dto) -> 'UIUsuario':
        return cls(id=dto.id, nombre=dto.nombre, email=dto.email,
                   activo=getattr(dto, 'activo', True))
```

**Regla #16 — ViewModels Específicos**
```python
# Presentation/viewmodels/usuario_viewmodel.py
class UsuarioViewModel(ViewModelBase):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self._usuarios: List[UIUsuario] = []
        self._usuario_seleccionado: Optional[UIUsuario] = None
        self._filtro_nombre: str = ""
        self.cargar_usuarios()
    
    @property
    def usuarios(self) -> List[UIUsuario]:
        if not self._filtro_nombre:
            return self._usuarios
        filtro = self._filtro_nombre.lower()
        return [u for u in self._usuarios if filtro in u.nombre.lower()]
    
    @property
    def filtro_nombre(self) -> str: return self._filtro_nombre
    @filtro_nombre.setter
    def filtro_nombre(self, valor: str):
        self.establecer_propiedad('_filtro_nombre', valor)
        self.notificar_cambio('usuarios')
    
    def cargar_usuarios(self):
        self.ocupado = True
        self.mensaje_estado = "Cargando usuarios..."
        try:
            dto_usuarios = self.backend.obtener_usuarios()
            self._usuarios = [UIUsuario.from_dto(u) for u in dto_usuarios]
            self.mensaje_estado = f"{len(self._usuarios)} usuarios cargados"
            self.notificar_cambio('usuarios')
        except Exception as e:
            self.mensaje_estado = f"Error: {e}"
        finally:
            self.ocupado = False
    
    def guardar_actual(self) -> bool:
        if not self._usuario_seleccionado:
            return False
        errores = self._usuario_seleccionado.validar_formato()
        if errores:
            for campo, msg in errores.items():
                self.agregar_error(campo, msg)
            return False
        self.ocupado = True
        try:
            if self._usuario_seleccionado.id:
                self.backend.actualizar_usuario(self._usuario_seleccionado.id,
                                                self._usuario_seleccionado.to_dict())
            else:
                dto = self.backend.crear_usuario(self._usuario_seleccionado.to_dict())
                self._usuario_seleccionado.id = dto.id
            self.mensaje_estado = "Guardado correctamente"
            self.cargar_usuarios()
            return True
        except Exception as e:
            self.mensaje_estado = f"Error: {e}"
            return False
        finally:
            self.ocupado = False
```

**Regla #17 — Comandos**
```python
# Presentation/commands/comando_base.py
from abc import ABC, abstractmethod

class ComandoBase(ABC):
    def __init__(self, viewmodel):
        self.viewmodel = viewmodel
        self._ejecutado = False
    
    @abstractmethod
    def ejecutar(self, *args, **kwargs): pass
    
    def puede_ejecutar(self) -> bool:
        return not self.viewmodel.ocupado
    
    def deshacer(self): pass

class ComandoGuardarUsuario(ComandoBase):
    def __init__(self, viewmodel):
        super().__init__(viewmodel)
        self._respaldo = None
    
    def ejecutar(self, *args, **kwargs):
        if not self.puede_ejecutar():
            return False
        if self.viewmodel.usuario_seleccionado:
            self._respaldo = self.viewmodel.usuario_seleccionado.to_dict()
        resultado = self.viewmodel.guardar_actual()
        if resultado:
            self._ejecutado = True
        return resultado
    
    def deshacer(self):
        if self._ejecutado and self._respaldo:
            self.viewmodel.mensaje_estado = "Operación deshecha"
            self.viewmodel.cargar_usuarios()
```

**Regla #18 — Binding Vista–ViewModel**
```python
# User_Interface/vistas/vista_usuarios.py
class VistaUsuarios:
    def __init__(self, parent, viewmodel):
        self.viewmodel = viewmodel
        self._binding_activo = True
        self.viewmodel.suscribir(self._on_viewmodel_changed)
        self._crear_widgets()
        self._configurar_bindings()
    
    def _configurar_bindings(self):
        self.entry_filtro.bind('<KeyRelease>',
            lambda e: setattr(self.viewmodel, 'filtro_nombre', self.entry_filtro.get()))
        self.tree.bind('<<TreeviewSelect>>', self._on_seleccionar)
    
    def _on_viewmodel_changed(self, evento):
        if not self._binding_activo: return
        nombre = evento['nombre']
        if nombre == 'usuarios':
            self._actualizar_tabla()
        elif nombre == '_usuario_seleccionado':
            self._actualizar_formulario()
        elif nombre == '_mensaje_estado':
            self.lbl_estado.config(text=evento['valor_nuevo'])
    
    def _actualizar_tabla(self):
        self._binding_activo = False
        for item in self.tree.get_children():
            self.tree.delete(item)
        for usuario in self.viewmodel.usuarios:
            self.tree.insert('', 'end',
                values=(usuario.id, usuario.nombre, usuario.email), iid=str(usuario.id))
        self._binding_activo = True
```

**Regla #19 — Backend como Proveedor de ViewModels**
```python
# backend.py
class Backend:
    def __init__(self, config=None):
        self._inicializar_servicios(config)
        self._inicializar_viewmodels()
    
    def _inicializar_viewmodels(self):
        self.viewmodel_usuario = UsuarioViewModel(self)
        self.viewmodel_producto = ProductoViewModel(self)
    
    def obtener_viewmodel_usuario(self) -> UsuarioViewModel:
        return self.viewmodel_usuario
    
    def obtener_viewmodel_producto(self) -> ProductoViewModel:
        return self.viewmodel_producto
```

**Regla #20 — Bootstrap Integrado**
```python
# bootstrap.py
def ejecutar_aplicacion():
    backend = Backend(config)
    root = tk.Tk()
    root.title("Mi Aplicación")
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    vista_usuarios = VistaUsuarios(notebook, backend.obtener_viewmodel_usuario())
    notebook.add(vista_usuarios, text="👥 Usuarios")
    
    vista_productos = VistaProductos(notebook, backend.obtener_viewmodel_producto())
    notebook.add(vista_productos, text="📦 Productos")
    
    root.mainloop()
```

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
            self._usuarios = [UIUsuario.from_dto(dto) for dto in dtos]
            self.mensaje_estado = f"{len(self._usuarios)} usuarios cargados"
        except Exception as e:
            self.mensaje_estado = f"Error: {str(e)}"
        finally:
            self.ocupado = False
            self.notificar_cambio("ocupado")
            self.notificar_cambio("usuarios")
            self.notificar_cambio("mensaje_estado")
```

**Regla:** el ViewModel nunca bloquea el hilo principal. Si la operación es async, `ocupado` debe activarse antes del await y desactivarse en el bloque `finally`.

### Beneficios del MVVM

- Separación clara entre UI y lógica de presentación.
- ViewModels testeables sin interfaz gráfica.
- Reutilización con múltiples frameworks (Tkinter, Qt, Web).
- Estado explícito y centralizado.
- Validación de UI desacoplada de reglas de negocio.

### Checklist MVVM

- [ ] El ViewModel hereda de ViewModelBase.
- [ ] Las propiedades notifican cambios mediante `notificar_cambio()`.
- [ ] Los comandos encapsulan acciones complejas.
- [ ] Los modelos de UI son dataclasses simples.
- [ ] La Vista no contiene lógica de negocio.
- [ ] El ViewModel no importa nada de `User_Interface`.
- [ ] Los errores de UI se manejan en el ViewModel.
- [ ] backend.py expone los ViewModels a la UI.

---

## Migración entre Niveles

Migrar un proyecto entre niveles es un proceso incremental, no una reescritura. El orden importa: mover primero lo que menos impacto tiene en el sistema activo.

### De Nivel 1 a Nivel 2

1. Identificar funciones que interactúan con el usuario (prints, inputs, widgets).
2. Moverlas a `Frontend.py`.
3. Lo que queda (lógica, datos) se convierte en `Backend.py`.
4. El frontend importa al backend. Nunca al revés.

**Señal de que la migración está bien hecha:** se puede ejecutar `Backend.py` directamente en modo script sin que importe nada de presentación.

### De Nivel 2 a Nivel 3

**Orden recomendado:**

1. Crear las carpetas `Domain/`, `Application/`, `Infrastructure/`, `User_Interface/`.
2. Mover primero las entidades con lógica a `Domain/entidades/`.
3. Extraer las interfaces (contratos) de repositorios a `Application/interfaces/`.
4. Mover el acceso a datos a `Infrastructure/persistencia/`.
5. Mover los servicios orquestadores a `Application/servicios/`.
6. La UI existente se convierte en `User_Interface/`.
7. Crear `backend.py` y `bootstrap.py` al final.

**Error frecuente:** empezar por crear carpetas vacías sin mover nada. Migrar entidad por entidad es más seguro que refactorizar todo a la vez.

### De Nivel 3 a Nivel 4

1. Agregar la carpeta `Tests/` con la estructura espejo de las capas.
2. Escribir primero los tests del Domain (los más simples, sin mocks).
3. Agregar tests de Application con mocks de Infrastructure.
4. Crear `Scripts/` para las migraciones existentes que estaban en `bootstrap.py`.
5. Crear `Docs/` con al menos un `README.md` funcional.

**Meta mínima:** alcanzar 80% de cobertura en Domain antes de pasar a Application.

### De Nivel 4 a Nivel 5

1. Crear la carpeta `Presentation/` con `viewmodels/`, `models/`, `commands/`.
2. Crear `ViewModelBase` primero.
3. Migrar la lógica de estado de `User_Interface/` hacia ViewModels, uno por vista.
4. Reemplazar acceso directo al backend desde la UI por llamadas al ViewModel.
5. Agregar `test_presentation/` en Tests.

**No migrar todo a la vez.** Empezar por la vista más compleja y validar el patrón antes de continuar con el resto.

---

## Estructura Completa — Nivel 5

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
│   │   ├── servicio_usuario.py
│   │   └── servicio_producto.py
│   ├── dto/
│   │   ├── usuario_dto.py
│   │   └── producto_dto.py
│   └── interfaces/
│       ├── repositorio_usuario.py
│       └── repositorio_producto.py
│
├── Domain/
│   ├── __init__.py
│   ├── entidades/
│   │   ├── usuario.py
│   │   └── producto.py
│   ├── value_objects/
│   │   ├── email.py
│   │   └── direccion.py
│   ├── eventos/
│   │   └── eventos_usuario.py
│   └── excepciones/
│       └── excepciones_dominio.py
│
├── Infrastructure/
│   ├── __init__.py
│   ├── persistencia/
│   │   ├── base_datos/
│   │   │   ├── conexion.py
│   │   │   └── modelos.py
│   │   └── repositorios/
│   │       ├── repositorio_usuario_sql.py
│   │       └── repositorio_producto_sql.py
│   ├── servicios_externos/
│   │   ├── api_cliente.py
│   │   └── servicios_email.py
│   └── logging/
│       └── logger_config.py
│
├── Presentation/
│   ├── __init__.py
│   ├── viewmodels/
│   │   ├── viewmodel_base.py
│   │   ├── usuario_viewmodel.py
│   │   ├── producto_viewmodel.py
│   │   └── login_viewmodel.py
│   ├── models/
│   │   ├── ui_usuario.py
│   │   ├── ui_producto.py
│   │   └── validators.py
│   └── commands/
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
│   │   ├── tabla_datos.py
│   │   ├── formulario.py
│   │   └── menu_lateral.py
│   └── vistas/
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
│   │   ├── test_usuario_viewmodel.py
│   │   └── test_validators.py
│   └── conftest.py
│
├── Scripts/
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

---

## CLI Dev Pattern

El CLI Dev Pattern es una extensión del patrón AETHERYON orientada específicamente a herramientas de línea de comandos que operan sobre sistemas reales: repositorios, proyectos, pipelines, agentes. No reemplaza los niveles 1–5, sino que los complementa definiendo cómo organizar un CLI cuando la herramienta necesita orquestar capas heterogéneas (datos, sistema operativo, servicios externos, UI opcional).

### ¿Cuándo aplica el CLI Dev Pattern?

Aplica cuando el CLI no es solo un modo operativo de un sistema mayor, sino la herramienta principal. Señales concretas:

- El CLI manipula estado persistente (archivos, BD, repositorios git).
- Tiene subcomandos con comportamientos distintos (`open`, `close`, `step-add`, `checkpoint`).
- Necesita conectar con el sistema operativo, APIs externas o agentes.
- Puede evolucionar hacia una GUI sin reescribir la lógica.

### Anatomía del CLI Dev Pattern

El patrón organiza el sistema en tres ejes verticales que comparten una capa de almacenamiento central:

```
                     ┌───────────────────────────────┐
                     │         FUENTES DE DATO       │
                     │  (ideas, compromisos, notas)  │
                     └───────────────┬───────────────┘
                                     │
                                     ▼
      ┌──────────────────────────────────────────────────────────┐
      │                  CAPA DE ALMACENAMIENTO (Core)           │
      │           SQLite — tabla layers / steps / checkpoints    │
      │       Verdad única · transaccional · sin dependencias UI │
      └──────────┬──────────────────┬──────────────────┬─────────┘
                 │                  │                  │
                 ▼                  ▼                  ▼
      ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
      │   MODELS API     │ │   EXPORT / I/O   │ │ AUTOMATIONS /    │
      │  (dominio puro)  │ │  Markdown · JSON │ │ AGENTS (futuro)  │
      └────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
               │                    │                    │
               ▼                    ▼                    ▼
      ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
      │       CLI        │ │       GUI        │ │    BITÁCORA      │
      │  velocidad,      │ │  navegación,     │ │  relato,         │
      │  scripting,      │ │  foco humano     │ │  reporte,        │
      │  agentes         │ │  (Tkinter/Flet)  │ │  estratégico     │
      └────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
               │                    │                    │
               ▼                    ▼                    ▼
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
      │             ESTADOS DE PROGRESO              │
      ├──────────────────────┬───────────────────────┤
      │     CHECKPOINTS      │         STEPS         │
      │  msg + versión       │   idx · estado        │
      │  (memoria viva)      │◀────────────────────▶│
      │                      │   progreso (%)        │
      └──────────────────────┴───────────────────────┘
```

### Los tres ejes

**Eje CLI** — Velocidad y automatización. Comandos atómicos que operan sobre el Core sin pasar por GUI. Ideal para scripting y agentes. Cada subcomando debe poder ejecutarse sin estado previo en memoria.

**Eje GUI** — Foco humano. Consume los mismos datos del Core que el CLI pero los presenta visualmente. No duplica lógica: delega en los mismos métodos del dominio. La GUI es intercambiable (Tkinter, Flet, web) porque la lógica vive en el Core.

**Eje Bitácora** — Narrativa y estrategia. Exporta el estado del sistema a formatos legibles (Markdown, JSON, voz). Es el eje de salida: no escribe al Core, solo lee.

### AppState como coordinador

En proyectos que combinan GUI y sistema operativo (git, VS Code, GitHub CLI), el `AppState` actúa como el equivalente del `backend.py` del patrón AUDI: centraliza el estado de la sesión y coordina los tres ejes sin que ninguno conozca a los otros directamente.

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

### Reglas del CLI Dev Pattern

**Regla CLI-1 — El Core no conoce la interfaz.**
La capa de almacenamiento y los modelos de dominio no importan nada de CLI, GUI ni Bitácora. Son el único módulo que puede vivir solo.

**Regla CLI-2 — Los comandos son atómicos.**
Cada subcomando (`open`, `checkpoint`, `step-add`) hace exactamente una cosa y retorna un resultado serializable. No hay estado acumulado entre comandos salvo el que vive en el Core.

**Regla CLI-3 — GUI y CLI comparten dominio, no código de presentación.**
Ambos llaman a los mismos métodos del Core. Si un método existe solo para la GUI o solo para el CLI, es una señal de que la lógica está en el lugar equivocado.

**Regla CLI-4 — AppState es de sesión, no de persistencia.**
El estado de la aplicación en memoria (proyecto activo, archivos seleccionados, rama actual) vive en `AppState`. La persistencia real vive en el Core (SQLite, git). Si el proceso muere, `AppState` se puede reconstruir desde el Core.

**Regla CLI-5 — El eje Bitácora es de solo lectura.**
Los exportadores (Markdown, JSON, voz) solo leen del Core. Nunca escriben. Esto garantiza que los informes sean reproducibles y que un export fallido no corrompa datos.

**Regla CLI-6 — Los agentes usan el mismo CLI.**
Cuando se integren automatizaciones o agentes de IA, invocan los mismos subcomandos que un humano. No hay una API especial para agentes. Esto hace el sistema auditable: el log de comandos ejecutados es igual para humanos y máquinas.

### Relación con los niveles AETHERYON

El CLI Dev Pattern se apoya sobre la arquitectura de capas de los niveles 3–5. El Core corresponde a `Domain` + `Infrastructure`. `AppState` corresponde a `backend.py`. Los tres ejes (CLI, GUI, Bitácora) son instancias distintas de `User_Interface` que comparten el mismo `Application`.

```
Nivel 3–5 AUDI          CLI Dev Pattern
─────────────────────   ──────────────────────
Domain                → Core (modelos, reglas)
Infrastructure        → Core (SQLite, git, OS)
Application           → AppState + servicios
backend.py            → AppState (coordinador)
User_Interface (CLI)  → Eje CLI
User_Interface (GUI)  → Eje GUI
User_Interface (...)  → Eje Bitácora
```

---

## Conclusión

El patrón AETHERYON proporciona una arquitectura progresiva y escalable:

- **Nivel 1** — Script único para prototipos rápidos.
- **Nivel 2** — BF: separación básica lógica/presentación.
- **Nivel 3** — AUDI: arquitectura limpia por capas.
- **Nivel 4** — AUDDITS: agrega testing, scripts y documentación.
- **Nivel 5** — AUDDITS + MVVM: agrega capa de presentación con ViewModels.

Cada nivel añade complejidad controlada y mejores prácticas, permitiendo evolucionar el proyecto según crecen los requisitos, manteniendo siempre la separación de responsabilidades y la testabilidad.

**Principios clave a recordar:**
- Domain nunca depende de nadie.
- Application coordina, no implementa.
- Infrastructure implementa contratos.
- Presentation maneja estado de UI.
- UI solo muestra y captura eventos.
- Todo se inyecta, nada se crea internamente.
- Las pruebas son ciudadanos de primera clase.