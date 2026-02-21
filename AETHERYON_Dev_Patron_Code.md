# AETHERYON Dev Pattern

## Nivel 1 — Standalone Script
Proyecto desarrollado en un único script completamente funcional.

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

# Configuración de logging
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
        """Regla de negocio: validar formato de email"""
        if '@' not in nuevo_email:
            raise ValueError("Email inválido: debe contener @")
        self.email = nuevo_email
    
    def desactivar(self) -> None:
        """Regla de negocio: desactivar usuario"""
        self.activo = False

# ==================== APPLICATION ====================
class ServicioUsuario:
    """Capa de aplicación - orquesta casos de uso"""
    
    def __init__(self):
        self._usuarios: List[Usuario] = []
        self._next_id = 1
    
    def crear_usuario(self, nombre: str, email: str, tipo: str) -> Usuario:
        """Caso de uso: crear nuevo usuario"""
        # Validaciones de negocio
        if not nombre or len(nombre) < 3:
            raise ValueError("Nombre debe tener al menos 3 caracteres")
        
        if not email or '@' not in email:
            raise ValueError("Email inválido")
        
        # Crear entidad
        usuario = Usuario(
            id=self._next_id,
            nombre=nombre,
            email=email,
            tipo=TipoUsuario(tipo)
        )
        
        # Persistir
        self._usuarios.append(usuario)
        self._next_id += 1
        
        logger.info(f"Usuario creado: {usuario.nombre} (ID: {usuario.id})")
        return usuario
    
    def listar_usuarios(self, solo_activos: bool = False) -> List[Usuario]:
        """Caso de uso: listar usuarios"""
        if solo_activos:
            return [u for u in self._usuarios if u.activo]
        return self._usuarios.copy()
    
    def obtener_usuario(self, usuario_id: int) -> Optional[Usuario]:
        """Caso de uso: obtener usuario por ID"""
        for usuario in self._usuarios:
            if usuario.id == usuario_id:
                return usuario
        return None
    
    def eliminar_usuario(self, usuario_id: int) -> bool:
        """Caso de uso: eliminar usuario (borrado lógico)"""
        usuario = self.obtener_usuario(usuario_id)
        if usuario:
            usuario.desactivar()
            logger.info(f"Usuario desactivado: ID {usuario_id}")
            return True
        return False

# ==================== INTERFACES ====================

class CLI:
    """Interfaz de línea de comandos"""
    
    def __init__(self, servicio: ServicioUsuario):
        self.servicio = servicio
    
    def ejecutar(self, args: argparse.Namespace) -> None:
        """Ejecuta comando según argumentos"""
        comandos = {
            'crear': self._crear,
            'listar': self._listar,
            'obtener': self._obtener,
            'eliminar': self._eliminar
        }
        
        if args.comando in comandos:
            comandos[args.comando](args)
        else:
            self._mostrar_ayuda()
    
    def _crear(self, args: argparse.Namespace) -> None:
        """Crea un nuevo usuario"""
        try:
            usuario = self.servicio.crear_usuario(
                nombre=args.nombre,
                email=args.email,
                tipo=args.tipo
            )
            print(f"✅ Usuario creado: {usuario.nombre} (ID: {usuario.id})")
        except ValueError as e:
            print(f"❌ Error: {e}")
    
    def _listar(self, args: argparse.Namespace) -> None:
        """Lista todos los usuarios"""
        usuarios = self.servicio.listar_usuarios(args.solo_activos)
        
        if not usuarios:
            print("No hay usuarios")
            return
        
        print(f"\n{'ID':<4} {'NOMBRE':<20} {'EMAIL':<25} {'TIPO':<10} {'ESTADO':<8}")
        print("-" * 70)
        
        for u in usuarios:
            estado = "ACTIVO" if u.activo else "INACTIVO"
            print(f"{u.id:<4} {u.nombre:<20} {u.email:<25} {u.tipo.value:<10} {estado:<8}")
    
    def _obtener(self, args: argparse.Namespace) -> None:
        """Obtiene un usuario por ID"""
        usuario = self.servicio.obtener_usuario(args.id)
        
        if usuario:
            print(f"\nID: {usuario.id}")
            print(f"Nombre: {usuario.nombre}")
            print(f"Email: {usuario.email}")
            print(f"Tipo: {usuario.tipo.value}")
            print(f"Estado: {'ACTIVO' if usuario.activo else 'INACTIVO'}")
        else:
            print(f"❌ Usuario con ID {args.id} no encontrado")
    
    def _eliminar(self, args: argparse.Namespace) -> None:
        """Elimina (desactiva) un usuario"""
        if self.servicio.eliminar_usuario(args.id):
            print(f"✅ Usuario {args.id} desactivado")
        else:
            print(f"❌ Usuario con ID {args.id} no encontrado")
    
    def _mostrar_ayuda(self) -> None:
        """Muestra ayuda"""
        print("Comandos disponibles:")
        print("  crear <nombre> <email> <tipo>  - Crear usuario")
        print("  listar [--solo-activos]        - Listar usuarios")
        print("  obtener <id>                    - Ver usuario")
        print("  eliminar <id>                    - Desactivar usuario")

class UI:
    """Interfaz de usuario interactiva"""
    
    def __init__(self, servicio: ServicioUsuario):
        self.servicio = servicio
    
    def ejecutar(self) -> None:
        """Ejecuta interfaz interactiva"""
        print("\n" + "="*50)
        print("SISTEMA DE GESTIÓN DE USUARIOS")
        print("="*50)
        
        while True:
            self._mostrar_menu()
            opcion = input("\nSeleccione opción: ").strip()
            
            if opcion == '1':
                self._crear_usuario_interactivo()
            elif opcion == '2':
                self._listar_usuarios_interactivo()
            elif opcion == '3':
                self._buscar_usuario_interactivo()
            elif opcion == '4':
                self._eliminar_usuario_interactivo()
            elif opcion == '5':
                print("¡Hasta luego!")
                break
            else:
                print("❌ Opción no válida")
    
    def _mostrar_menu(self) -> None:
        """Muestra menú principal"""
        print("\n" + "-"*30)
        print("1. Crear usuario")
        print("2. Listar usuarios")
        print("3. Buscar usuario")
        print("4. Eliminar usuario")
        print("5. Salir")
        print("-"*30)
    
    def _crear_usuario_interactivo(self) -> None:
        """Flujo interactivo para crear usuario"""
        print("\n--- CREAR USUARIO ---")
        
        nombre = input("Nombre: ").strip()
        if not nombre:
            print("❌ Nombre requerido")
            return
        
        email = input("Email: ").strip()
        if not email:
            print("❌ Email requerido")
            return
        
        print("Tipos: admin, usuario, invitado")
        tipo = input("Tipo: ").strip().lower()
        
        try:
            usuario = self.servicio.crear_usuario(nombre, email, tipo)
            print(f"✅ Usuario creado con ID: {usuario.id}")
        except ValueError as e:
            print(f"❌ Error: {e}")
    
    def _listar_usuarios_interactivo(self) -> None:
        """Flujo interactivo para listar usuarios"""
        solo_activos = input("¿Solo activos? (s/n): ").strip().lower() == 's'
        usuarios = self.servicio.listar_usuarios(solo_activos)
        
        if not usuarios:
            print("No hay usuarios")
            return
        
        print(f"\n{'ID':<4} {'NOMBRE':<20} {'EMAIL':<25} {'TIPO':<10} {'ESTADO':<8}")
        print("-" * 70)
        
        for u in usuarios:
            estado = "ACTIVO" if u.activo else "INACTIVO"
            print(f"{u.id:<4} {u.nombre:<20} {u.email:<25} {u.tipo.value:<10} {estado:<8}")
    
    def _buscar_usuario_interactivo(self) -> None:
        """Flujo interactivo para buscar usuario"""
        try:
            usuario_id = int(input("ID del usuario: ").strip())
            usuario = self.servicio.obtener_usuario(usuario_id)
            
            if usuario:
                print(f"\n📋 Datos del usuario:")
                print(f"  ID: {usuario.id}")
                print(f"  Nombre: {usuario.nombre}")
                print(f"  Email: {usuario.email}")
                print(f"  Tipo: {usuario.tipo.value}")
                print(f"  Estado: {'ACTIVO' if usuario.activo else 'INACTIVO'}")
            else:
                print(f"❌ Usuario no encontrado")
        except ValueError:
            print("❌ ID inválido")
    
    def _eliminar_usuario_interactivo(self) -> None:
        """Flujo interactivo para eliminar usuario"""
        try:
            usuario_id = int(input("ID del usuario a eliminar: ").strip())
            
            # Confirmar
            confirm = input(f"¿Desactivar usuario {usuario_id}? (s/n): ").strip().lower()
            
            if confirm == 's':
                if self.servicio.eliminar_usuario(usuario_id):
                    print(f"✅ Usuario desactivado")
                else:
                    print(f"❌ Usuario no encontrado")
        except ValueError:
            print("❌ ID inválido")

class Batch:
    """Modo batch para automatización"""
    
    def __init__(self, servicio: ServicioUsuario):
        self.servicio = servicio
    
    def ejecutar(self, archivo: str) -> None:
        """Ejecuta comandos desde archivo"""
        try:
            with open(archivo, 'r') as f:
                for linea_num, linea in enumerate(f, 1):
                    linea = linea.strip()
                    if not linea or linea.startswith('#'):
                        continue
                    
                    print(f"Ejecutando línea {linea_num}: {linea}")
                    self._ejecutar_comando(linea)
                    
        except FileNotFoundError:
            print(f"❌ Archivo no encontrado: {archivo}")
        except Exception as e:
            print(f"❌ Error en línea {linea_num}: {e}")
    
    def _ejecutar_comando(self, linea: str) -> None:
        """Ejecuta un comando desde línea de texto"""
        partes = linea.split()
        if not partes:
            return
        
        comando = partes[0].lower()
        
        if comando == 'crear' and len(partes) >= 4:
            self.servicio.crear_usuario(partes[1], partes[2], partes[3])
            print(f"  ✅ Usuario creado: {partes[1]}")
        
        elif comando == 'eliminar' and len(partes) >= 2:
            try:
                usuario_id = int(partes[1])
                if self.servicio.eliminar_usuario(usuario_id):
                    print(f"  ✅ Usuario {usuario_id} eliminado")
                else:
                    print(f"  ❌ Usuario {usuario_id} no encontrado")
            except ValueError:
                print(f"  ❌ ID inválido: {partes[1]}")
        
        elif comando == 'exportar' and len(partes) >= 2:
            self._exportar_json(partes[1])
    
    def _exportar_json(self, archivo: str) -> None:
        """Exporta usuarios a JSON"""
        usuarios = self.servicio.listar_usuarios()
        datos = [
            {
                'id': u.id,
                'nombre': u.nombre,
                'email': u.email,
                'tipo': u.tipo.value,
                'activo': u.activo
            }
            for u in usuarios
        ]
        
        with open(archivo, 'w') as f:
            json.dump(datos, f, indent=2)
        
        print(f"  ✅ Datos exportados a {archivo}")

# ==================== MAIN ====================

def main():
    """Punto de entrada principal"""
    parser = argparse.ArgumentParser(description='Sistema de Gestión de Usuarios')
    
    # Modos de operación
    parser.add_argument('--modo', choices=['cli', 'ui', 'batch'], default='cli',
                       help='Modo de operación')
    
    # Subcomandos para modo CLI
    subparsers = parser.add_subparsers(dest='comando', help='Comandos CLI')
    
    # Comando crear
    crear_parser = subparsers.add_parser('crear', help='Crear usuario')
    crear_parser.add_argument('nombre', help='Nombre del usuario')
    crear_parser.add_argument('email', help='Email del usuario')
    crear_parser.add_argument('tipo', choices=['admin', 'usuario', 'invitado'],
                             help='Tipo de usuario')
    
    # Comando listar
    listar_parser = subparsers.add_parser('listar', help='Listar usuarios')
    listar_parser.add_argument('--solo-activos', action='store_true',
                              help='Mostrar solo usuarios activos')
    
    # Comando obtener
    obtener_parser = subparsers.add_parser('obtener', help='Obtener usuario')
    obtener_parser.add_argument('id', type=int, help='ID del usuario')
    
    # Comando eliminar
    eliminar_parser = subparsers.add_parser('eliminar', help='Eliminar usuario')
    eliminar_parser.add_argument('id', type=int, help='ID del usuario')
    
    # Argumentos para modo batch
    parser.add_argument('--archivo', help='Archivo de comandos para modo batch')
    
    args = parser.parse_args()
    
    # Inicializar servicio
    servicio = ServicioUsuario()
    
    # Modos de operación
    if args.modo == 'ui':
        UI(servicio).ejecutar()
    elif args.modo == 'batch':
        if args.archivo:
            Batch(servicio).ejecutar(args.archivo)
        else:
            print("❌ Modo batch requiere --archivo")
    else:  # cli mode
        if args.comando:
            CLI(servicio).ejecutar(args)
        else:
            parser.print_help()

if __name__ == '__main__':
    main()
```

### Ejemplo de uso

```bash
# Modo CLI - Crear usuario
python proyecto.py crear "Juan Pérez" "juan@email.com" admin

# Modo CLI - Listar usuarios
python proyecto.py listar
python proyecto.py listar --solo-activos

# Modo CLI - Obtener usuario
python proyecto.py obtener 1

# Modo CLI - Eliminar usuario
python proyecto.py eliminar 1

# Modo UI (interactivo)
python proyecto.py --modo ui

# Modo Batch (archivo de comandos)
echo "crear Ana ana@email.com usuario" > comandos.txt
echo "crear Carlos carlos@email.com admin" >> comandos.txt  
echo "exportar usuarios.json" >> comandos.txt
python proyecto.py --modo batch --archivo comandos.txt
```

---

## Nivel 2 — Patrón BF (Backend–Frontend)
Separación básica entre lógica y presentación.

```
proyecto/
│
├── backend.py
└── frontend.py
```

### Ejemplo: Backend-Frontend con Tkinter

**backend.py**
```python
"""
backend.py - Lógica de negocio y persistencia
Independiente de la interfaz de usuario
"""

import json
import os
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class Tarea:
    """Modelo de datos"""
    id: int
    titulo: str
    descripcion: str = ""
    completada: bool = False
    fecha_creacion: str = ""
    
    def __post_init__(self):
        if not self.fecha_creacion:
            self.fecha_creacion = datetime.now().isoformat()

class GestorTareas:
    """Lógica de negocio principal"""
    
    def __init__(self, archivo_datos: str = "tareas.json"):
        self.archivo_datos = archivo_datos
        self._tareas: List[Tarea] = []
        self._cargar_datos()
    
    def _cargar_datos(self) -> None:
        """Carga tareas desde archivo JSON"""
        if os.path.exists(self.archivo_datos):
            try:
                with open(self.archivo_datos, 'r') as f:
                    datos = json.load(f)
                    self._tareas = [Tarea(**t) for t in datos]
            except:
                self._tareas = []
    
    def _guardar_datos(self) -> None:
        """Guarda tareas en archivo JSON"""
        with open(self.archivo_datos, 'w') as f:
            json.dump([asdict(t) for t in self._tareas], f, indent=2)
    
    # API Pública - Expuesta al frontend
    
    def obtener_todas(self) -> List[Tarea]:
        """Retorna todas las tareas"""
        return self._tareas.copy()
    
    def obtener_pendientes(self) -> List[Tarea]:
        """Retorna tareas no completadas"""
        return [t for t in self._tareas if not t.completada]
    
    def obtener_completadas(self) -> List[Tarea]:
        """Retorna tareas completadas"""
        return [t for t in self._tareas if t.completada]
    
    def agregar(self, titulo: str, descripcion: str = "") -> Tarea:
        """Agrega una nueva tarea"""
        nuevo_id = max([t.id for t in self._tareas], default=0) + 1
        tarea = Tarea(id=nuevo_id, titulo=titulo, descripcion=descripcion)
        self._tareas.append(tarea)
        self._guardar_datos()
        return tarea
    
    def completar(self, tarea_id: int) -> bool:
        """Marca una tarea como completada"""
        for tarea in self._tareas:
            if tarea.id == tarea_id:
                tarea.completada = True
                self._guardar_datos()
                return True
        return False
    
    def eliminar(self, tarea_id: int) -> bool:
        """Elimina una tarea"""
        for i, tarea in enumerate(self._tareas):
            if tarea.id == tarea_id:
                del self._tareas[i]
                self._guardar_datos()
                return True
        return False
    
    def buscar(self, texto: str) -> List[Tarea]:
        """Busca tareas por texto en título o descripción"""
        texto = texto.lower()
        return [
            t for t in self._tareas
            if texto in t.titulo.lower() or texto in t.descripcion.lower()
        ]
    
    def estadisticas(self) -> Dict[str, Any]:
        """Retorna estadísticas de tareas"""
        total = len(self._tareas)
        completadas = len([t for t in self._tareas if t.completada])
        pendientes = total - completadas
        
        return {
            'total': total,
            'completadas': completadas,
            'pendientes': pendientes,
            'porcentaje_completado': (completadas / total * 100) if total > 0 else 0
        }

# Backend wrapper para frontend
class Backend:
    """Interfaz unificada para el frontend"""
    
    def __init__(self):
        self.gestor = GestorTareas()
    
    def obtener_tareas(self, filtro: str = "todas") -> List[Tarea]:
        """Obtiene tareas según filtro"""
        filtros = {
            "todas": self.gestor.obtener_todas,
            "pendientes": self.gestor.obtener_pendientes,
            "completadas": self.gestor.obtener_completadas
        }
        return filtros.get(filtro, self.gestor.obtener_todas)()
    
    def crear_tarea(self, titulo: str, descripcion: str = "") -> Tarea:
        """Crea una nueva tarea"""
        return self.gestor.agregar(titulo, descripcion)
    
    def toggle_tarea(self, tarea_id: int) -> bool:
        """Cambia estado de una tarea"""
        return self.gestor.completar(tarea_id)
    
    def borrar_tarea(self, tarea_id: int) -> bool:
        """Elimina una tarea"""
        return self.gestor.eliminar(tarea_id)
    
    def buscar_tareas(self, texto: str) -> List[Tarea]:
        """Busca tareas"""
        return self.gestor.buscar(texto)
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas"""
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
from backend import Backend, Tarea
from typing import Optional

class AplicacionTareas:
    """Interfaz gráfica de la aplicación"""
    
    def __init__(self):
        self.backend = Backend()
        self.tarea_seleccionada: Optional[Tarea] = None
        self.filtro_actual = "todas"
        
        self._crear_ventana()
        self._crear_widgets()
        self._cargar_tareas()
    
    def _crear_ventana(self):
        """Configura la ventana principal"""
        self.root = tk.Tk()
        self.root.title("Gestor de Tareas")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar colores
        self.root.configure(bg='#f0f0f0')
        
    def _crear_widgets(self):
        """Crea todos los widgets de la interfaz"""
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ===== BARRA SUPERIOR =====
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(toolbar, text="Título:").pack(side=tk.LEFT, padx=(0,5))
        self.entry_titulo = ttk.Entry(toolbar, width=30)
        self.entry_titulo.pack(side=tk.LEFT, padx=(0,10))
        
        ttk.Label(toolbar, text="Descripción:").pack(side=tk.LEFT, padx=(0,5))
        self.entry_desc = ttk.Entry(toolbar, width=40)
        self.entry_desc.pack(side=tk.LEFT, padx=(0,10))
        
        ttk.Button(
            toolbar,
            text="➕ Agregar",
            command=self._agregar_tarea,
            style="Accent.TButton"
        ).pack(side=tk.LEFT)
        
        # ===== BARRA DE FILTROS =====
        filter_frame = ttk.LabelFrame(main_frame, text="Filtros", padding="5")
        filter_frame.pack(fill=tk.X, pady=(0,10))
        
        self.filtro_var = tk.StringVar(value="todas")
        
        ttk.Radiobutton(
            filter_frame,
            text="Todas",
            variable=self.filtro_var,
            value="todas",
            command=self._aplicar_filtro
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            filter_frame,
            text="Pendientes",
            variable=self.filtro_var,
            value="pendientes",
            command=self._aplicar_filtro
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            filter_frame,
            text="Completadas",
            variable=self.filtro_var,
            value="completadas",
            command=self._aplicar_filtro
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(filter_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Label(filter_frame, text="Buscar:").pack(side=tk.LEFT, padx=(10,5))
        self.entry_buscar = ttk.Entry(filter_frame, width=30)
        self.entry_buscar.pack(side=tk.LEFT, padx=(0,5))
        self.entry_buscar.bind('<KeyRelease>', self._buscar_tareas)
        
        # ===== LISTA DE TAREAS =====
        list_frame = ttk.LabelFrame(main_frame, text="Lista de Tareas", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0,10))
        
        # Scrollbars
        scroll_y = ttk.Scrollbar(list_frame)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scroll_x = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview
        self.tree = ttk.Treeview(
            list_frame,
            columns=('id', 'titulo', 'descripcion', 'estado', 'fecha'),
            show='headings',
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set,
            height=15
        )
        
        # Configurar columnas
        self.tree.heading('id', text='ID')
        self.tree.heading('titulo', text='Título')
        self.tree.heading('descripcion', text='Descripción')
        self.tree.heading('estado', text='Estado')
        self.tree.heading('fecha', text='Fecha Creación')
        
        self.tree.column('id', width=50, anchor='center')
        self.tree.column('titulo', width=200)
        self.tree.column('descripcion', width=300)
        self.tree.column('estado', width=100, anchor='center')
        self.tree.column('fecha', width=150)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configurar scrollbars
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)
        
        # Eventos
        self.tree.bind('<<TreeviewSelect>>', self._on_seleccionar_tarea)
        self.tree.bind('<Double-1>', self._on_doble_click)
        
        # ===== BOTONES DE ACCIÓN =====
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X)
        
        ttk.Button(
            action_frame,
            text="✅ Completar",
            command=self._completar_tarea,
            state=tk.DISABLED
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            action_frame,
            text="✏️ Editar",
            command=self._editar_tarea,
            state=tk.DISABLED
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            action_frame,
            text="🗑️ Eliminar",
            command=self._eliminar_tarea,
            state=tk.DISABLED
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(action_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Estadísticas
        self.lbl_stats = ttk.Label(action_frame, text="")
        self.lbl_stats.pack(side=tk.RIGHT, padx=5)
        
        # ===== BARRA DE ESTADO =====
        self.status_bar = ttk.Frame(main_frame)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(5,0))
        
        self.lbl_status = ttk.Label(self.status_bar, text="Listo", relief=tk.SUNKEN, padding=2)
        self.lbl_status.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def _cargar_tareas(self):
        """Carga las tareas desde el backend"""
        try:
            tareas = self.backend.obtener_tareas(self.filtro_actual)
            self._actualizar_tabla(tareas)
            self._actualizar_estadisticas()
            self._set_status(f"Cargadas {len(tareas)} tareas")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar tareas: {e}")
    
    def _actualizar_tabla(self, tareas):
        """Actualiza la tabla con las tareas"""
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Insertar tareas
        for tarea in tareas:
            estado = "✅ Completada" if tarea.completada else "⏳ Pendiente"
            fecha = tarea.fecha_creacion[:10]  # Solo fecha
            
            valores = (
                tarea.id,
                tarea.titulo,
                tarea.descripcion[:50] + "..." if len(tarea.descripcion) > 50 else tarea.descripcion,
                estado,
                fecha
            )
            
            # Color según estado
            tags = ('completada',) if tarea.completada else ('pendiente',)
            self.tree.insert('', 'end', values=valores, tags=tags, iid=str(tarea.id))
        
        # Configurar colores de filas
        self.tree.tag_configure('completada', foreground='gray', background='#e8f5e8')
        self.tree.tag_configure('pendiente', foreground='black', background='white')
    
    def _agregar_tarea(self):
        """Agrega una nueva tarea"""
        titulo = self.entry_titulo.get().strip()
        if not titulo:
            messagebox.showwarning("Advertencia", "El título es obligatorio")
            return
        
        descripcion = self.entry_desc.get().strip()
        
        try:
            tarea = self.backend.crear_tarea(titulo, descripcion)
            self._cargar_tareas()
            self.entry_titulo.delete(0, tk.END)
            self.entry_desc.delete(0, tk.END)
            self._set_status(f"Tarea '{titulo}' creada (ID: {tarea.id})")
        except Exception as e:
            messagebox.showerror("Error", f"Error al crear tarea: {e}")
    
    def _on_seleccionar_tarea(self, event):
        """Maneja selección de tarea"""
        seleccion = self.tree.selection()
        
        if seleccion:
            tarea_id = int(seleccion[0])
            tareas = self.backend.obtener_tareas("todas")
            self.tarea_seleccionada = next((t for t in tareas if t.id == tarea_id), None)
            
            # Habilitar botones según estado
            self._habilitar_botones_por_seleccion()
        else:
            self.tarea_seleccionada = None
            self._deshabilitar_botones()
    
    def _habilitar_botones_por_seleccion(self):
        """Habilita botones según tarea seleccionada"""
        if self.tarea_seleccionada:
            # Habilitar todos
            for child in self.root.winfo_children():
                if isinstance(child, ttk.Frame):
                    for btn in child.winfo_children():
                        if isinstance(btn, ttk.Button) and btn['text'] in ['✅ Completar', '✏️ Editar', '🗑️ Eliminar']:
                            btn.config(state=tk.NORMAL)
            
            # Deshabilitar Completar si ya está completada
            if self.tarea_seleccionada.completada:
                for child in self.root.winfo_children():
                    if isinstance(child, ttk.Frame):
                        for btn in child.winfo_children():
                            if isinstance(btn, ttk.Button) and btn['text'] == '✅ Completar':
                                btn.config(state=tk.DISABLED)
    
    def _deshabilitar_botones(self):
        """Deshabilita botones de acción"""
        for child in self.root.winfo_children():
            if isinstance(child, ttk.Frame):
                for btn in child.winfo_children():
                    if isinstance(btn, ttk.Button) and btn['text'] in ['✅ Completar', '✏️ Editar', '🗑️ Eliminar']:
                        btn.config(state=tk.DISABLED)
    
    def _on_doble_click(self, event):
        """Maneja doble click en tarea"""
        self._completar_tarea()
    
    def _completar_tarea(self):
        """Marca tarea como completada"""
        if self.tarea_seleccionada:
            try:
                if self.backend.toggle_tarea(self.tarea_seleccionada.id):
                    self._cargar_tareas()
                    self._set_status(f"Tarea {self.tarea_seleccionada.id} completada")
            except Exception as e:
                messagebox.showerror("Error", f"Error al completar tarea: {e}")
    
    def _editar_tarea(self):
        """Edita tarea seleccionada"""
        if self.tarea_seleccionada:
            # Ventana de edición
            dialog = tk.Toplevel(self.root)
            dialog.title("Editar Tarea")
            dialog.geometry("400x200")
            dialog.transient(self.root)
            dialog.grab_set()
            
            ttk.Label(dialog, text="Título:").pack(pady=(10,0))
            entry_titulo = ttk.Entry(dialog, width=50)
            entry_titulo.insert(0, self.tarea_seleccionada.titulo)
            entry_titulo.pack(pady=5)
            
            ttk.Label(dialog, text="Descripción:").pack()
            entry_desc = ttk.Entry(dialog, width=50)
            entry_desc.insert(0, self.tarea_seleccionada.descripcion)
            entry_desc.pack(pady=5)
            
            def guardar():
                # Aquí iría lógica de actualización
                messagebox.showinfo("Info", "Funcionalidad en desarrollo")
                dialog.destroy()
            
            ttk.Button(dialog, text="Guardar", command=guardar).pack(pady=10)
    
    def _eliminar_tarea(self):
        """Elimina tarea seleccionada"""
        if self.tarea_seleccionada:
            if messagebox.askyesno("Confirmar", f"¿Eliminar tarea '{self.tarea_seleccionada.titulo}'?"):
                try:
                    if self.backend.borrar_tarea(self.tarea_seleccionada.id):
                        self._cargar_tareas()
                        self.tarea_seleccionada = None
                        self._deshabilitar_botones()
                        self._set_status("Tarea eliminada")
                except Exception as e:
                    messagebox.showerror("Error", f"Error al eliminar tarea: {e}")
    
    def _aplicar_filtro(self):
        """Aplica filtro seleccionado"""
        self.filtro_actual = self.filtro_var.get()
        self._cargar_tareas()
    
    def _buscar_tareas(self, event=None):
        """Busca tareas por texto"""
        texto = self.entry_buscar.get().strip()
        
        if texto:
            tareas = self.backend.buscar_tareas(texto)
            self._actualizar_tabla(tareas)
            self._set_status(f"Búsqueda: {len(tareas)} resultados")
        else:
            self._cargar_tareas()
    
    def _actualizar_estadisticas(self):
        """Actualiza las estadísticas en la UI"""
        stats = self.backend.obtener_estadisticas()
        
        texto = f"📊 Total: {stats['total']} | "
        texto += f"✅ {stats['completadas']} | "
        texto += f"⏳ {stats['pendientes']} | "
        texto += f"📈 {stats['porcentaje_completado']:.1f}%"
        
        self.lbl_stats.config(text=texto)
    
    def _set_status(self, mensaje: str):
        """Establece mensaje en barra de estado"""
        self.lbl_status.config(text=f"  {mensaje}")
        self.root.after(3000, lambda: self.lbl_status.config(text="  Listo"))
    
    def ejecutar(self):
        """Inicia la aplicación"""
        self.root.mainloop()

if __name__ == '__main__':
    app = AplicacionTareas()
    app.ejecutar()
```

---

## Nivel 3 — Patrón AUDI
Arquitectura por capas fundamentales.

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

Un sistema funcional ejecuta.
Un sistema evolutivo se adapta.
La diferencia es la separación clara de responsabilidades.

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
    """Entidad Cliente - identidad única"""
    id: Optional[int]
    nombre: str
    email: str
    telefono: str
    
    def validar_email(self) -> bool:
        """Regla de negocio: validación de email"""
        return '@' in self.email and '.' in self.email
    
    def validar_telefono(self) -> bool:
        """Regla de negocio: validación de teléfono"""
        return len(self.telefono) >= 9 and self.telefono.isdigit()

@dataclass
class Habitacion:
    """Entidad Habitación - identidad única"""
    id: Optional[int]
    numero: str
    tipo: TipoHabitacion
    precio_noche: float
    disponible: bool = True
    
    def calcular_precio(self, noches: int) -> float:
        """Regla de negocio: cálculo de precio con descuentos"""
        precio_base = self.precio_noche * noches
        
        # Descuento por estancia larga (> 7 noches)
        if noches > 7:
            precio_base *= 0.9  # 10% descuento
        
        return precio_base

@dataclass
class Reserva:
    """Entidad Reserva - raíz del agregado"""
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
        """Regla de negocio: cálculo de noches"""
        return (self.fecha_fin - self.fecha_inicio).days
    
    def confirmar(self) -> None:
        """Regla de negocio: confirmar reserva"""
        if self.estado != EstadoReserva.PENDIENTE:
            raise ValueError("Solo se pueden confirmar reservas pendientes")
        self.estado = EstadoReserva.CONFIRMADA
    
    def cancelar(self) -> None:
        """Regla de negocio: cancelar reserva"""
        if self.estado == EstadoReserva.COMPLETADA:
            raise ValueError("No se puede cancelar una reserva completada")
        self.estado = EstadoReserva.CANCELADA
    
    def completar(self) -> None:
        """Regla de negocio: completar reserva"""
        if self.estado != EstadoReserva.CONFIRMADA:
            raise ValueError("Solo se pueden completar reservas confirmadas")
        self.estado = EstadoReserva.COMPLETADA
    
    def solapa_con(self, otra: 'Reserva') -> bool:
        """Regla de negocio: verificar solapamiento de fechas"""
        return not (self.fecha_fin <= otra.fecha_inicio or 
                   self.fecha_inicio >= otra.fecha_fin)

# Domain/excepciones/excepciones_dominio.py
class ErrorDominio(Exception):
    """Base para errores de dominio"""
    pass

class ClienteNoEncontrado(ErrorDominio):
    def __init__(self, cliente_id: int):
        super().__init__(f"Cliente con ID {cliente_id} no encontrado")

class HabitacionNoDisponible(ErrorDominio):
    def __init__(self, habitacion_id: int, fecha_inicio: date, fecha_fin: date):
        super().__init__(
            f"Habitación {habitacion_id} no disponible entre "
            f"{fecha_inicio} y {fecha_fin}"
        )

class FechasInvalidas(ErrorDominio):
    def __init__(self):
        super().__init__("La fecha de fin debe ser posterior a la fecha de inicio")
```

**Application/interfaces/repositorios.py**
```python
"""
Application/interfaces/repositorios.py - Contratos abstractos
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import date

from Domain.entidades.reserva import Cliente, Habitacion, Reserva

class RepositorioCliente(ABC):
    """Contrato para repositorio de clientes"""
    
    @abstractmethod
    def obtener_por_id(self, cliente_id: int) -> Optional[Cliente]:
        pass
    
    @abstractmethod
    def obtener_por_email(self, email: str) -> Optional[Cliente]:
        pass
    
    @abstractmethod
    def guardar(self, cliente: Cliente) -> Cliente:
        pass
    
    @abstractmethod
    def actualizar(self, cliente: Cliente) -> bool:
        pass
    
    @abstractmethod
    def listar(self) -> List[Cliente]:
        pass

class RepositorioHabitacion(ABC):
    """Contrato para repositorio de habitaciones"""
    
    @abstractmethod
    def obtener_por_id(self, habitacion_id: int) -> Optional[Habitacion]:
        pass
    
    @abstractmethod
    def obtener_por_numero(self, numero: str) -> Optional[Habitacion]:
        pass
    
    @abstractmethod
    def listar_disponibles(self, fecha_inicio: date, fecha_fin: date) -> List[Habitacion]:
        pass
    
    @abstractmethod
    def guardar(self, habitacion: Habitacion) -> Habitacion:
        pass

class RepositorioReserva(ABC):
    """Contrato para repositorio de reservas"""
    
    @abstractmethod
    def obtener_por_id(self, reserva_id: int) -> Optional[Reserva]:
        pass
    
    @abstractmethod
    def obtener_por_cliente(self, cliente_id: int) -> List[Reserva]:
        pass
    
    @abstractmethod
    def obtener_por_habitacion(self, habitacion_id: int, 
                              fecha_inicio: date, fecha_fin: date) -> List[Reserva]:
        pass
    
    @abstractmethod
    def guardar(self, reserva: Reserva) -> Reserva:
        pass
    
    @abstractmethod
    def actualizar_estado(self, reserva_id: int, nuevo_estado) -> bool:
        pass
```

**Application/servicios/servicio_reserva.py**
```python
"""
Application/servicios/servicio_reserva.py - Casos de uso
"""

from datetime import date
from typing import List, Optional
import logging

from Domain.entidades.reserva import (
    Cliente, Habitacion, Reserva, EstadoReserva,
    ClienteNoEncontrado, HabitacionNoDisponible, FechasInvalidas
)
from Application.interfaces.repositorios import (
    RepositorioCliente, RepositorioHabitacion, RepositorioReserva
)
from Application.dto.reserva_dto import (
    ClienteDTO, HabitacionDTO, ReservaDTO, SolicitudReservaDTO
)

class ServicioReserva:
    """Casos de uso para gestión de reservas"""
    
    def __init__(
        self,
        repo_cliente: RepositorioCliente,
        repo_habitacion: RepositorioHabitacion,
        repo_reserva: RepositorioReserva
    ):
        self.repo_cliente = repo_cliente
        self.repo_habitacion = repo_habitacion
        self.repo_reserva = repo_reserva
        self.logger = logging.getLogger(__name__)
    
    def crear_reserva(self, solicitud: SolicitudReservaDTO) -> ReservaDTO:
        """
        Caso de uso: Crear una nueva reserva
        """
        self.logger.info(f"Creando reserva para cliente {solicitud.cliente_id}")
        
        # 1. Validar fechas
        if solicitud.fecha_fin <= solicitud.fecha_inicio:
            raise FechasInvalidas()
        
        # 2. Obtener cliente
        cliente = self.repo_cliente.obtener_por_id(solicitud.cliente_id)
        if not cliente:
            raise ClienteNoEncontrado(solicitud.cliente_id)
        
        # 3. Verificar disponibilidad de habitación
        reservas_existentes = self.repo_reserva.obtener_por_habitacion(
            solicitud.habitacion_id,
            solicitud.fecha_inicio,
            solicitud.fecha_fin
        )
        
        if reservas_existentes:
            raise HabitacionNoDisponible(
                solicitud.habitacion_id,
                solicitud.fecha_inicio,
                solicitud.fecha_fin
            )
        
        # 4. Obtener habitación para cálculos
        habitacion = self.repo_habitacion.obtener_por_id(solicitud.habitacion_id)
        if not habitacion:
            raise ValueError(f"Habitación {solicitud.habitacion_id} no encontrada")
        
        # 5. Crear entidad reserva
        reserva = Reserva(
            id=None,
            cliente_id=cliente.id,
            habitacion_id=habitacion.id,
            fecha_inicio=solicitud.fecha_inicio,
            fecha_fin=solicitud.fecha_fin,
            estado=EstadoReserva.PENDIENTE
        )
        
        # 6. Persistir
        reserva_guardada = self.repo_reserva.guardar(reserva)
        self.logger.info(f"Reserva creada con ID {reserva_guardada.id}")
        
        # 7. Retornar DTO
        return ReservaDTO.desde_entidad(reserva_guardada, cliente, habitacion)
    
    def confirmar_reserva(self, reserva_id: int) -> ReservaDTO:
        """
        Caso de uso: Confirmar una reserva pendiente
        """
        self.logger.info(f"Confirmando reserva {reserva_id}")
        
        # 1. Obtener reserva
        reserva = self.repo_reserva.obtener_por_id(reserva_id)
        if not reserva:
            raise ValueError(f"Reserva {reserva_id} no encontrada")
        
        # 2. Aplicar regla de negocio
        reserva.confirmar()
        
        # 3. Persistir cambio
        self.repo_reserva.actualizar_estado(reserva_id, reserva.estado)
        
        # 4. Obtener datos completos para DTO
        cliente = self.repo_cliente.obtener_por_id(reserva.cliente_id)
        habitacion = self.repo_habitacion.obtener_por_id(reserva.habitacion_id)
        
        return ReservaDTO.desde_entidad(reserva, cliente, habitacion)
    
    def buscar_disponibilidad(self, fecha_inicio: date, fecha_fin: date) -> List[HabitacionDTO]:
        """
        Caso de uso: Buscar habitaciones disponibles
        """
        self.logger.info(f"Buscando disponibilidad entre {fecha_inicio} y {fecha_fin}")
        
        if fecha_fin <= fecha_inicio:
            raise FechasInvalidas()
        
        habitaciones = self.repo_habitacion.listar_disponibles(fecha_inicio, fecha_fin)
        
        return [HabitacionDTO.desde_entidad(h) for h in habitaciones]
    
    def obtener_reservas_cliente(self, cliente_id: int) -> List[ReservaDTO]:
        """
        Caso de uso: Obtener reservas de un cliente
        """
        cliente = self.repo_cliente.obtener_por_id(cliente_id)
        if not cliente:
            raise ClienteNoEncontrado(cliente_id)
        
        reservas = self.repo_reserva.obtener_por_cliente(cliente_id)
        resultados = []
        
        for r in reservas:
            habitacion = self.repo_habitacion.obtener_por_id(r.habitacion_id)
            resultados.append(ReservaDTO.desde_entidad(r, cliente, habitacion))
        
        return resultados
```

**Infrastructure/persistencia/repositorios_sql.py**
```python
"""
Infrastructure/persistencia/repositorios_sql.py - Implementaciones concretas
"""

import sqlite3
from typing import Optional, List
from datetime import date, datetime
import json

from Domain.entidades.reserva import Cliente, Habitacion, Reserva, EstadoReserva, TipoHabitacion
from Application.interfaces.repositorios import (
    RepositorioCliente, RepositorioHabitacion, RepositorioReserva
)

class RepositorioClienteSQL(RepositorioCliente):
    """Implementación SQLite para clientes"""
    
    def __init__(self, conexion: sqlite3.Connection):
        self.conn = conexion
        self._crear_tabla()
    
    def _crear_tabla(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                telefono TEXT NOT NULL,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
    
    def obtener_por_id(self, cliente_id: int) -> Optional[Cliente]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, nombre, email, telefono FROM clientes WHERE id = ?",
            (cliente_id,)
        )
        fila = cursor.fetchone()
        
        if fila:
            return Cliente(
                id=fila[0],
                nombre=fila[1],
                email=fila[2],
                telefono=fila[3]
            )
        return None
    
    def obtener_por_email(self, email: str) -> Optional[Cliente]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, nombre, email, telefono FROM clientes WHERE email = ?",
            (email,)
        )
        fila = cursor.fetchone()
        
        if fila:
            return Cliente(
                id=fila[0],
                nombre=fila[1],
                email=fila[2],
                telefono=fila[3]
            )
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
    
    def actualizar(self, cliente: Cliente) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE clientes SET nombre = ?, email = ?, telefono = ? WHERE id = ?",
            (cliente.nombre, cliente.email, cliente.telefono, cliente.id)
        )
        self.conn.commit()
        return cursor.rowcount > 0
    
    def listar(self) -> List[Cliente]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, nombre, email, telefono FROM clientes")
        
        return [
            Cliente(id=f[0], nombre=f[1], email=f[2], telefono=f[3])
            for f in cursor.fetchall()
        ]

class RepositorioHabitacionSQL(RepositorioHabitacion):
    """Implementación SQLite para habitaciones"""
    
    def __init__(self, conexion: sqlite3.Connection):
        self.conn = conexion
        self._crear_tabla()
    
    def _crear_tabla(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habitaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero TEXT UNIQUE NOT NULL,
                tipo TEXT NOT NULL,
                precio_noche REAL NOT NULL,
                disponible BOOLEAN DEFAULT TRUE
            )
        """)
        self.conn.commit()
    
    def obtener_por_id(self, habitacion_id: int) -> Optional[Habitacion]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, numero, tipo, precio_noche, disponible FROM habitaciones WHERE id = ?",
            (habitacion_id,)
        )
        fila = cursor.fetchone()
        
        if fila:
            return Habitacion(
                id=fila[0],
                numero=fila[1],
                tipo=TipoHabitacion(fila[2]),
                precio_noche=fila[3],
                disponible=bool(fila[4])
            )
        return None
    
    def obtener_por_numero(self, numero: str) -> Optional[Habitacion]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, numero, tipo, precio_noche, disponible FROM habitaciones WHERE numero = ?",
            (numero,)
        )
        fila = cursor.fetchone()
        
        if fila:
            return Habitacion(
                id=fila[0],
                numero=fila[1],
                tipo=TipoHabitacion(fila[2]),
                precio_noche=fila[3],
                disponible=bool(fila[4])
            )
        return None
    
    def listar_disponibles(self, fecha_inicio: date, fecha_fin: date) -> List[Habitacion]:
        cursor = self.conn.cursor()
        
        # Subquery para habitaciones con reservas en el período
        cursor.execute("""
            SELECT h.id, h.numero, h.tipo, h.precio_noche, h.disponible
            FROM habitaciones h
            WHERE h.disponible = 1
            AND NOT EXISTS (
                SELECT 1 FROM reservas r
                WHERE r.habitacion_id = h.id
                AND r.estado IN ('pendiente', 'confirmada')
                AND (
                    (r.fecha_inicio <= ? AND r.fecha_fin > ?) OR
                    (r.fecha_inicio < ? AND r.fecha_fin >= ?) OR
                    (r.fecha_inicio >= ? AND r.fecha_fin <= ?)
                )
            )
        """, (
            fecha_fin.isoformat(), fecha_inicio.isoformat(),
            fecha_fin.isoformat(), fecha_inicio.isoformat(),
            fecha_inicio.isoformat(), fecha_fin.isoformat()
        ))
        
        return [
            Habitacion(
                id=f[0],
                numero=f[1],
                tipo=TipoHabitacion(f[2]),
                precio_noche=f[3],
                disponible=bool(f[4])
            )
            for f in cursor.fetchall()
        ]
    
    def guardar(self, habitacion: Habitacion) -> Habitacion:
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO habitaciones (numero, tipo, precio_noche, disponible) 
               VALUES (?, ?, ?, ?)""",
            (habitacion.numero, habitacion.tipo.value, habitacion.precio_noche, habitacion.disponible)
        )
        self.conn.commit()
        habitacion.id = cursor.lastrowid
        return habitacion

class RepositorioReservaSQL(RepositorioReserva):
    """Implementación SQLite para reservas"""
    
    def __init__(self, conexion: sqlite3.Connection):
        self.conn = conexion
        self._crear_tabla()
    
    def _crear_tabla(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reservas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                habitacion_id INTEGER NOT NULL,
                fecha_inicio DATE NOT NULL,
                fecha_fin DATE NOT NULL,
                estado TEXT NOT NULL,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id),
                FOREIGN KEY (habitacion_id) REFERENCES habitaciones(id)
            )
        """)
        self.conn.commit()
    
    def obtener_por_id(self, reserva_id: int) -> Optional[Reserva]:
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT id, cliente_id, habitacion_id, fecha_inicio, fecha_fin, estado, fecha_creacion
               FROM reservas WHERE id = ?""",
            (reserva_id,)
        )
        fila = cursor.fetchone()
        
        if fila:
            return Reserva(
                id=fila[0],
                cliente_id=fila[1],
                habitacion_id=fila[2],
                fecha_inicio=date.fromisoformat(fila[3]),
                fecha_fin=date.fromisoformat(fila[4]),
                estado=EstadoReserva(fila[5]),
                fecha_creacion=datetime.fromisoformat(fila[6]) if fila[6] else None
            )
        return None
    
    def obtener_por_cliente(self, cliente_id: int) -> List[Reserva]:
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT id, cliente_id, habitacion_id, fecha_inicio, fecha_fin, estado, fecha_creacion
               FROM reservas WHERE cliente_id = ?
               ORDER BY fecha_inicio DESC""",
            (cliente_id,)
        )
        
        return [
            Reserva(
                id=f[0],
                cliente_id=f[1],
                habitacion_id=f[2],
                fecha_inicio=date.fromisoformat(f[3]),
                fecha_fin=date.fromisoformat(f[4]),
                estado=EstadoReserva(f[5]),
                fecha_creacion=datetime.fromisoformat(f[6]) if f[6] else None
            )
            for f in cursor.fetchall()
        ]
    
    def obtener_por_habitacion(self, habitacion_id: int, 
                              fecha_inicio: date, fecha_fin: date) -> List[Reserva]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, cliente_id, habitacion_id, fecha_inicio, fecha_fin, estado, fecha_creacion
            FROM reservas 
            WHERE habitacion_id = ?
            AND estado IN ('pendiente', 'confirmada')
            AND NOT (fecha_fin <= ? OR fecha_inicio >= ?)
        """, (habitacion_id, fecha_inicio.isoformat(), fecha_fin.isoformat()))
        
        return [
            Reserva(
                id=f[0],
                cliente_id=f[1],
                habitacion_id=f[2],
                fecha_inicio=date.fromisoformat(f[3]),
                fecha_fin=date.fromisoformat(f[4]),
                estado=EstadoReserva(f[5]),
                fecha_creacion=datetime.fromisoformat(f[6]) if f[6] else None
            )
            for f in cursor.fetchall()
        ]
    
    def guardar(self, reserva: Reserva) -> Reserva:
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO reservas 
               (cliente_id, habitacion_id, fecha_inicio, fecha_fin, estado)
               VALUES (?, ?, ?, ?, ?)""",
            (
                reserva.cliente_id,
                reserva.habitacion_id,
                reserva.fecha_inicio.isoformat(),
                reserva.fecha_fin.isoformat(),
                reserva.estado.value
            )
        )
        self.conn.commit()
        reserva.id = cursor.lastrowid
        return reserva
    
    def actualizar_estado(self, reserva_id: int, nuevo_estado) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE reservas SET estado = ? WHERE id = ?",
            (nuevo_estado.value, reserva_id)
        )
        self.conn.commit()
        return cursor.rowcount > 0
```

**Infrastructure/servicios_externos/servicio_pago.py**
```python
"""
Infrastructure/servicios_externos/servicio_pago.py - Integración con pasarela de pagos
"""

import requests
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ResultadoPago:
    exitoso: bool
    transaccion_id: Optional[str]
    mensaje: str

class PasarelaPagoStripe:
    """Adaptador para Stripe (servicio externo)"""
    
    def __init__(self, api_key: str, modo_prueba: bool = True):
        self.api_key = api_key
        self.modo_prueba = modo_prueba
        self.base_url = "https://api.stripe.com/v1" if not modo_prueba else "https://api.stripe.com/v1/test"
        self.logger = logging.getLogger(__name__)
    
    def procesar_pago(self, monto: float, moneda: str, token: str) -> ResultadoPago:
        """
        Procesa un pago a través de Stripe
        """
        try:
            if self.modo_prueba:
                # Simular respuesta en modo prueba
                self.logger.info(f"Modo prueba: Procesando pago de {monto} {moneda}")
                return ResultadoPago(
                    exitoso=True,
                    transaccion_id=f"test_{hash(str(monto))}",
                    mensaje="Pago procesado correctamente (modo prueba)"
                )
            
            # Llamada real a Stripe
            response = requests.post(
                f"{self.base_url}/charges",
                auth=(self.api_key, ""),
                data={
                    "amount": int(monto * 100),  # Stripe usa centavos
                    "currency": moneda.lower(),
                    "source": token,
                    "description": "Reserva hotel"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return ResultadoPago(
                    exitoso=True,
                    transaccion_id=data['id'],
                    mensaje="Pago procesado correctamente"
                )
            else:
                return ResultadoPago(
                    exitoso=False,
                    transaccion_id=None,
                    mensaje=f"Error Stripe: {response.json().get('error', {}).get('message', 'Desconocido')}"
                )
                
        except requests.RequestException as e:
            self.logger.error(f"Error de conexión con Stripe: {e}")
            return ResultadoPago(
                exitoso=False,
                transaccion_id=None,
                mensaje="Error de conexión con pasarela de pagos"
            )

class ServicioEmailSMTP:
    """Servicio de envío de emails"""
    
    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
        self.host = smtp_host
        self.port = smtp_port
        self.username = username
        self.password = password
        self.logger = logging.getLogger(__name__)
    
    def enviar_confirmacion_reserva(self, email_destino: str, datos_reserva: Dict[str, Any]) -> bool:
        """
        Envía email de confirmación de reserva
        """
        try:
            # En una implementación real usaríamos smtplib
            self.logger.info(f"Enviando confirmación a {email_destino}")
            self.logger.debug(f"Datos reserva: {datos_reserva}")
            
            # Simular envío exitoso
            return True
            
        except Exception as e:
            self.logger.error(f"Error enviando email: {e}")
            return False
```

**Infrastructure/logging/logger_config.py**
```python
"""
Infrastructure/logging/logger_config.py - Configuración centralizada de logging
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

def configurar_logging(
    nivel: str = "INFO",
    archivo: Optional[str] = None,
    formato: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
) -> None:
    """
    Configura el sistema de logging para toda la aplicación
    """
    # Crear directorio para logs si no existe
    if archivo:
        Path(archivo).parent.mkdir(parents=True, exist_ok=True)
    
    # Configurar nivel
    nivel_log = getattr(logging, nivel.upper())
    
    # Configuración básica
    handlers = []
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(formato))
    handlers.append(console_handler)
    
    # Handler para archivo si se especifica
    if archivo:
        file_handler = logging.handlers.RotatingFileHandler(
            archivo,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(logging.Formatter(formato))
        handlers.append(file_handler)
    
    # Configurar logging
    logging.basicConfig(
        level=nivel_log,
        handlers=handlers
    )
    
    # Log de inicio
    logging.info(f"Logging configurado - Nivel: {nivel}")
```

**Application/dto/reserva_dto.py**
```python
"""
Application/dto/reserva_dto.py - Objetos de transferencia de datos
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
from Domain.entidades.reserva import Cliente, Habitacion, Reserva, EstadoReserva, TipoHabitacion

@dataclass
class ClienteDTO:
    """DTO para cliente"""
    id: int
    nombre: str
    email: str
    telefono: str
    
    @classmethod
    def desde_entidad(cls, cliente: Cliente) -> 'ClienteDTO':
        return cls(
            id=cliente.id,
            nombre=cliente.nombre,
            email=cliente.email,
            telefono=cliente.telefono
        )
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'nombre': self.nombre,
            'email': self.email,
            'telefono': self.telefono
        }

@dataclass
class HabitacionDTO:
    """DTO para habitación"""
    id: int
    numero: str
    tipo: str
    precio_noche: float
    disponible: bool
    
    @classmethod
    def desde_entidad(cls, habitacion: Habitacion) -> 'HabitacionDTO':
        return cls(
            id=habitacion.id,
            numero=habitacion.numero,
            tipo=habitacion.tipo.value,
            precio_noche=habitacion.precio_noche,
            disponible=habitacion.disponible
        )
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'numero': self.numero,
            'tipo': self.tipo,
            'precio_noche': self.precio_noche,
            'disponible': self.disponible
        }

@dataclass
class ReservaDTO:
    """DTO para reserva con datos completos"""
    id: int
    cliente: ClienteDTO
    habitacion: HabitacionDTO
    fecha_inicio: date
    fecha_fin: date
    noches: int
    precio_total: float
    estado: str
    fecha_creacion: datetime
    
    @classmethod
    def desde_entidad(cls, reserva: Reserva, cliente: Cliente, habitacion: Habitacion) -> 'ReservaDTO':
        precio_total = habitacion.calcular_precio(reserva.noches)
        
        return cls(
            id=reserva.id,
            cliente=ClienteDTO.desde_entidad(cliente),
            habitacion=HabitacionDTO.desde_entidad(habitacion),
            fecha_inicio=reserva.fecha_inicio,
            fecha_fin=reserva.fecha_fin,
            noches=reserva.noches,
            precio_total=precio_total,
            estado=reserva.estado.value,
            fecha_creacion=reserva.fecha_creacion
        )
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'cliente': self.cliente.to_dict(),
            'habitacion': self.habitacion.to_dict(),
            'fecha_inicio': self.fecha_inicio.isoformat(),
            'fecha_fin': self.fecha_fin.isoformat(),
            'noches': self.noches,
            'precio_total': self.precio_total,
            'estado': self.estado,
            'fecha_creacion': self.fecha_creacion.isoformat()
        }

@dataclass
class SolicitudReservaDTO:
    """DTO para solicitud de nueva reserva"""
    cliente_id: int
    habitacion_id: int
    fecha_inicio: date
    fecha_fin: date
    
    @classmethod
    def desde_dict(cls, datos: dict) -> 'SolicitudReservaDTO':
        return cls(
            cliente_id=datos['cliente_id'],
            habitacion_id=datos['habitacion_id'],
            fecha_inicio=date.fromisoformat(datos['fecha_inicio']),
            fecha_fin=date.fromisoformat(datos['fecha_fin'])
        )
```

**User_Interface/vistas/vista_reservas.py**
```python
"""
User_Interface/vistas/vista_reservas.py - Vista con Tkinter
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from typing import Optional

from backend import Backend
from Application.dto.reserva_dto import SolicitudReservaDTO

class VistaReservas:
    """Vista de gestión de reservas"""
    
    def __init__(self, parent, backend: Backend):
        self.parent = parent
        self.backend = backend
        self.reserva_seleccionada = None
        
        self._crear_widgets()
        self._cargar_datos_iniciales()
    
    def _crear_widgets(self):
        """Crea los widgets de la interfaz"""
        
        # Notebook para pestañas
        self.notebook = ttk.Notebook(self.parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña: Nueva Reserva
        self.frame_nueva = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_nueva, text="➕ Nueva Reserva")
        self._crear_pestana_nueva()
        
        # Pestaña: Listado
        self.frame_listado = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_listado, text="📋 Listado Reservas")
        self._crear_pestana_listado()
        
        # Pestaña: Disponibilidad
        self.frame_disponibilidad = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_disponibilidad, text="🏨 Disponibilidad")
        self._crear_pestana_disponibilidad()
    
    def _crear_pestana_nueva(self):
        """Crea formulario de nueva reserva"""
        
        # Frame para el formulario
        form = ttk.LabelFrame(self.frame_nueva, text="Datos de la Reserva", padding=20)
        form.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Cliente
        ttk.Label(form, text="Cliente:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.combo_cliente = ttk.Combobox(form, width=40, state="readonly")
        self.combo_cliente.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Button(
            form,
            text="👤 Nuevo Cliente",
            command=self._abrir_dialogo_cliente
        ).grid(row=0, column=2, padx=5)
        
        # Habitación
        ttk.Label(form, text="Habitación:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.combo_habitacion = ttk.Combobox(form, width=40, state="readonly")
        self.combo_habitacion.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ttk.Button(
            form,
            text="🔄 Ver Disponibles",
            command=self._actualizar_habitaciones_disponibles
        ).grid(row=1, column=2, padx=5)
        
        # Fechas
        ttk.Label(form, text="Fecha Entrada:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.entry_fecha_entrada = ttk.Entry(form, width=20)
        self.entry_fecha_entrada.insert(0, datetime.now().date().isoformat())
        self.entry_fecha_entrada.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(form, text="Fecha Salida:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.entry_fecha_salida = ttk.Entry(form, width=20)
        self.entry_fecha_salida.insert(0, (datetime.now().date() + timedelta(days=3)).isoformat())
        self.entry_fecha_salida.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        # Botón crear
        ttk.Button(
            form,
            text="✅ Crear Reserva",
            command=self._crear_reserva,
            style="Accent.TButton"
        ).grid(row=4, column=1, pady=20)
        
        # Configurar grid
        form.columnconfigure(1, weight=1)
    
    def _crear_pestana_listado(self):
        """Crea tabla de reservas"""
        
        # Frame para filtros
        filtros = ttk.Frame(self.frame_listado)
        filtros.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(filtros, text="Filtrar por estado:").pack(side=tk.LEFT, padx=5)
        self.filtro_estado = ttk.Combobox(
            filtros,
            values=["Todas", "Pendientes", "Confirmadas", "Canceladas", "Completadas"],
            state="readonly",
            width=15
        )
        self.filtro_estado.set("Todas")
        self.filtro_estado.pack(side=tk.LEFT, padx=5)
        self.filtro_estado.bind('<<ComboboxSelected>>', self._aplicar_filtro)
        
        ttk.Button(
            filtros,
            text="🔄 Refrescar",
            command=self._refrescar_reservas
        ).pack(side=tk.RIGHT, padx=5)
        
        # Frame para la tabla
        frame_tabla = ttk.Frame(self.frame_listado)
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Scrollbars
        scroll_y = ttk.Scrollbar(frame_tabla)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scroll_x = ttk.Scrollbar(frame_tabla, orient=tk.HORIZONTAL)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview
        self.tree_reservas = ttk.Treeview(
            frame_tabla,
            columns=('id', 'cliente', 'habitacion', 'entrada', 'salida', 'noches', 'total', 'estado'),
            show='headings',
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set,
            height=15
        )
        
        # Configurar columnas
        columnas = [
            ('id', 'ID', 50),
            ('cliente', 'Cliente', 150),
            ('habitacion', 'Habitación', 80),
            ('entrada', 'Entrada', 100),
            ('salida', 'Salida', 100),
            ('noches', 'Noches', 60),
            ('total', 'Total', 80),
            ('estado', 'Estado', 100)
        ]
        
        for col, texto, ancho in columnas:
            self.tree_reservas.heading(col, text=texto)
            self.tree_reservas.column(col, width=ancho, anchor='center')
        
        self.tree_reservas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configurar scrollbars
        scroll_y.config(command=self.tree_reservas.yview)
        scroll_x.config(command=self.tree_reservas.xview)
        
        # Eventos
        self.tree_reservas.bind('<<TreeviewSelect>>', self._on_seleccionar_reserva)
        self.tree_reservas.bind('<Double-1>', self._ver_detalle_reserva)
        
        # Botones de acción
        acciones = ttk.Frame(self.frame_listado)
        acciones.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(
            acciones,
            text="✅ Confirmar",
            command=self._confirmar_reserva,
            state=tk.DISABLED
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            acciones,
            text="❌ Cancelar",
            command=self._cancelar_reserva,
            state=tk.DISABLED
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            acciones,
            text="👁️ Ver Detalle",
            command=self._ver_detalle_reserva,
            state=tk.DISABLED
        ).pack(side=tk.LEFT, padx=2)
    
    def _crear_pestana_disponibilidad(self):
        """Crea vista de disponibilidad"""
        
        # Frame para búsqueda
        busqueda = ttk.LabelFrame(self.frame_disponibilidad, text="Buscar Disponibilidad", padding=10)
        busqueda.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(busqueda, text="Fecha Entrada:").grid(row=0, column=0, padx=5, pady=5)
        self.entry_buscar_entrada = ttk.Entry(busqueda, width=15)
        self.entry_buscar_entrada.insert(0, datetime.now().date().isoformat())
        self.entry_buscar_entrada.grid(row=0, column=1, padx=5)
        
        ttk.Label(busqueda, text="Fecha Salida:").grid(row=0, column=2, padx=5, pady=5)
        self.entry_buscar_salida = ttk.Entry(busqueda, width=15)
        self.entry_buscar_salida.insert(0, (datetime.now().date() + timedelta(days=3)).isoformat())
        self.entry_buscar_salida.grid(row=0, column=3, padx=5)
        
        ttk.Button(
            busqueda,
            text="🔍 Buscar",
            command=self._buscar_disponibilidad
        ).grid(row=0, column=4, padx=20)
        
        # Tabla de disponibilidad
        frame_tabla = ttk.Frame(self.frame_disponibilidad)
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scroll_y = ttk.Scrollbar(frame_tabla)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree_disponibilidad = ttk.Treeview(
            frame_tabla,
            columns=('numero', 'tipo', 'precio', 'disponible'),
            show='headings',
            yscrollcommand=scroll_y.set
        )
        
        self.tree_disponibilidad.heading('numero', text='Número')
        self.tree_disponibilidad.heading('tipo', text='Tipo')
        self.tree_disponibilidad.heading('precio', text='Precio/Noche')
        self.tree_disponibilidad.heading('disponible', text='Disponible')
        
        self.tree_disponibilidad.column('numero', width=100)
        self.tree_disponibilidad.column('tipo', width=150)
        self.tree_disponibilidad.column('precio', width=100)
        self.tree_disponibilidad.column('disponible', width=100)
        
        self.tree_disponibilidad.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.config(command=self.tree_disponibilidad.yview)
    
    def _cargar_datos_iniciales(self):
        """Carga datos iniciales en los combos"""
        try:
            # Cargar clientes
            clientes = self.backend.obtener_clientes()
            self.combo_cliente['values'] = [
                f"{c.id} - {c.nombre} ({c.email})" for c in clientes
            ]
            
            # Cargar reservas
            self._refrescar_reservas()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando datos: {e}")
    
    def _actualizar_habitaciones_disponibles(self):
        """Actualiza el combo de habitaciones disponibles"""
        try:
            fecha_entrada = date.fromisoformat(self.entry_fecha_entrada.get())
            fecha_salida = date.fromisoformat(self.entry_fecha_salida.get())
            
            habitaciones = self.backend.buscar_disponibilidad(fecha_entrada, fecha_salida)
            
            self.combo_habitacion['values'] = [
                f"{h.id} - {h.numero} ({h.tipo}) - ${h.precio_noche}/noche"
                for h in habitaciones
            ]
            
            if habitaciones:
                self.combo_habitacion.set(self.combo_habitacion['values'][0])
                
        except Exception as e:
            messagebox.showerror("Error", f"Error buscando disponibilidad: {e}")
    
    def _abrir_dialogo_cliente(self):
        """Abre diálogo para crear nuevo cliente"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Nuevo Cliente")
        dialog.geometry("400x250")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Nombre:").pack(pady=(20,5))
        entry_nombre = ttk.Entry(dialog, width=40)
        entry_nombre.pack()
        
        ttk.Label(dialog, text="Email:").pack(pady=(10,5))
        entry_email = ttk.Entry(dialog, width=40)
        entry_email.pack()
        
        ttk.Label(dialog, text="Teléfono:").pack(pady=(10,5))
        entry_telefono = ttk.Entry(dialog, width=40)
        entry_telefono.pack()
        
        def guardar():
            try:
                cliente = self.backend.crear_cliente(
                    entry_nombre.get(),
                    entry_email.get(),
                    entry_telefono.get()
                )
                messagebox.showinfo("Éxito", f"Cliente creado: {cliente.nombre}")
                dialog.destroy()
                self._cargar_datos_iniciales()
            except Exception as e:
                messagebox.showerror("Error", f"Error creando cliente: {e}")
        
        ttk.Button(dialog, text="Guardar", command=guardar).pack(pady=20)
    
    def _crear_reserva(self):
        """Crea una nueva reserva"""
        try:
            # Obtener IDs seleccionados
            cliente_texto = self.combo_cliente.get()
            if not cliente_texto:
                messagebox.showwarning("Advertencia", "Debe seleccionar un cliente")
                return
            
            cliente_id = int(cliente_texto.split(' - ')[0])
            
            habitacion_texto = self.combo_habitacion.get()
            if not habitacion_texto:
                messagebox.showwarning("Advertencia", "Debe seleccionar una habitación")
                return
            
            habitacion_id = int(habitacion_texto.split(' - ')[0])
            
            # Crear solicitud
            solicitud = SolicitudReservaDTO(
                cliente_id=cliente_id,
                habitacion_id=habitacion_id,
                fecha_inicio=date.fromisoformat(self.entry_fecha_entrada.get()),
                fecha_fin=date.fromisoformat(self.entry_fecha_salida.get())
            )
            
            # Crear reserva
            reserva = self.backend.crear_reserva(solicitud)
            
            messagebox.showinfo(
                "Éxito",
                f"Reserva creada correctamente\n"
                f"ID: {reserva.id}\n"
                f"Total: ${reserva.precio_total:.2f}"
            )
            
            # Limpiar formulario
            self.combo_cliente.set('')
            self.combo_habitacion.set('')
            
            # Actualizar listado
            self._refrescar_reservas()
            
            # Cambiar a pestaña de listado
            self.notebook.select(1)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error creando reserva: {e}")
    
    def _refrescar_reservas(self):
        """Actualiza la tabla de reservas"""
        try:
            # Limpiar tabla
            for item in self.tree_reservas.get_children():
                self.tree_reservas.delete(item)
            
            # Obtener reservas
            filtro = self.filtro_estado.get().lower() if hasattr(self, 'filtro_estado') else "todas"
            reservas = self.backend.obtener_reservas(filtro)
            
            # Insertar en tabla
            for r in reservas:
                valores = (
                    r.id,
                    r.cliente.nombre,
                    f"{r.habitacion.numero}",
                    r.fecha_inicio.strftime("%d/%m/%Y"),
                    r.fecha_fin.strftime("%d/%m/%Y"),
                    r.noches,
                    f"${r.precio_total:.2f}",
                    r.estado.upper()
                )
                
                # Color según estado
                tags = (r.estado,)
                self.tree_reservas.insert(
                    '', 'end',
                    values=valores,
                    tags=tags,
                    iid=str(r.id)
                )
            
            # Configurar colores
            self.tree_reservas.tag_configure('pendiente', background='#fff3cd')
            self.tree_reservas.tag_configure('confirmada', background='#d4edda')
            self.tree_reservas.tag_configure('cancelada', background='#f8d7da')
            self.tree_reservas.tag_configure('completada', background='#d1ecf1')
            
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando reservas: {e}")
    
    def _on_seleccionar_reserva(self, event):
        """Maneja selección de reserva"""
        seleccion = self.tree_reservas.selection()
        
        if seleccion:
            self.reserva_seleccionada = int(seleccion[0])
            
            # Habilitar botones según estado
            item = self.tree_reservas.item(seleccion[0])
            estado = item['values'][7].lower()
            
            # Buscar botones
            for child in self.frame_listado.winfo_children():
                if isinstance(child, ttk.Frame) and child.winfo_children():
                    for btn in child.winfo_children():
                        if isinstance(btn, ttk.Button):
                            if btn['text'] == "✅ Confirmar":
                                btn.config(state=tk.NORMAL if estado == 'pendiente' else tk.DISABLED)
                            elif btn['text'] in ["❌ Cancelar", "👁️ Ver Detalle"]:
                                btn.config(state=tk.NORMAL)
    
    def _confirmar_reserva(self):
        """Confirma la reserva seleccionada"""
        if not self.reserva_seleccionada:
            return
        
        try:
            reserva = self.backend.confirmar_reserva(self.reserva_seleccionada)
            messagebox.showinfo("Éxito", f"Reserva {reserva.id} confirmada")
            self._refrescar_reservas()
        except Exception as e:
            messagebox.showerror("Error", f"Error confirmando reserva: {e}")
    
    def _cancelar_reserva(self):
        """Cancela la reserva seleccionada"""
        if not self.reserva_seleccionada:
            return
        
        if messagebox.askyesno("Confirmar", "¿Está seguro de cancelar esta reserva?"):
            try:
                self.backend.cancelar_reserva(self.reserva_seleccionada)
                messagebox.showinfo("Éxito", "Reserva cancelada")
                self._refrescar_reservas()
            except Exception as e:
                messagebox.showerror("Error", f"Error cancelando reserva: {e}")
    
    def _ver_detalle_reserva(self, event=None):
        """Muestra detalle de la reserva"""
        if not self.reserva_seleccionada:
            return
        
        try:
            reserva = self.backend.obtener_reserva(self.reserva_seleccionada)
            
            # Ventana de detalle
            dialog = tk.Toplevel(self.parent)
            dialog.title(f"Detalle Reserva #{reserva.id}")
            dialog.geometry("500x400")
            dialog.transient(self.parent)
            dialog.grab_set()
            
            # Frame principal
            main = ttk.Frame(dialog, padding=20)
            main.pack(fill=tk.BOTH, expand=True)
            
            # Datos
            ttk.Label(main, text=f"RESERVA #{reserva.id}", font=('Arial', 16, 'bold')).pack(pady=10)
            
            info = [
                ("Cliente:", f"{reserva.cliente.nombre} ({reserva.cliente.email})"),
                ("Habitación:", f"{reserva.habitacion.numero} - {reserva.habitacion.tipo}"),
                ("Fecha Entrada:", reserva.fecha_inicio.strftime("%d/%m/%Y")),
                ("Fecha Salida:", reserva.fecha_fin.strftime("%d/%m/%Y")),
                ("Noches:", str(reserva.noches)),
                ("Precio por noche:", f"${reserva.habitacion.precio_noche:.2f}"),
                ("Precio Total:", f"${reserva.precio_total:.2f}"),
                ("Estado:", reserva.estado.upper()),
                ("Fecha Creación:", reserva.fecha_creacion.strftime("%d/%m/%Y %H:%M"))
            ]
            
            for label, valor in info:
                frame = ttk.Frame(main)
                frame.pack(fill=tk.X, pady=2)
                ttk.Label(frame, text=label, width=15, anchor='e').pack(side=tk.LEFT, padx=5)
                ttk.Label(frame, text=valor, anchor='w').pack(side=tk.LEFT, padx=5)
            
            ttk.Button(main, text="Cerrar", command=dialog.destroy).pack(pady=20)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error obteniendo detalle: {e}")
    
    def _aplicar_filtro(self, event=None):
        """Aplica filtro de estado"""
        self._refrescar_reservas()
    
    def _buscar_disponibilidad(self):
        """Busca habitaciones disponibles"""
        try:
            fecha_entrada = date.fromisoformat(self.entry_buscar_entrada.get())
            fecha_salida = date.fromisoformat(self.entry_buscar_salida.get())
            
            habitaciones = self.backend.buscar_disponibilidad(fecha_entrada, fecha_salida)
            
            # Limpiar tabla
            for item in self.tree_disponibilidad.get_children():
                self.tree_disponibilidad.delete(item)
            
            # Insertar resultados
            for h in habitaciones:
                self.tree_disponibilidad.insert(
                    '', 'end',
                    values=(
                        h.numero,
                        h.tipo,
                        f"${h.precio_noche:.2f}",
                        "✅ Sí" if h.disponible else "❌ No"
                    )
                )
            
        except Exception as e:
            messagebox.showerror("Error", f"Error buscando disponibilidad: {e}")
```

---

## Nivel 4 — Patrón AUDDITS
Extensión productiva con testing, scripts y documentación.

### Reglas de Desarrollo

**Regla #1 — Responsabilidad Única**
- Cada archivo tiene una única responsabilidad bien definida.
- Cada clase tiene una sola razón para cambiar.
- Cada función hace una sola cosa y la hace correctamente.

**Ejemplo:**
```python
# ✅ Correcto - Una responsabilidad por archivo
# archivo: validadores_email.py
def validar_formato_email(email: str) -> bool:
    """Solo valida formato, no envía emails"""
    return '@' in email and '.' in email

# archivo: servicio_email.py
def enviar_email(destino: str, asunto: str, cuerpo: str) -> bool:
    """Solo envía emails, no valida formato"""
    # Implementación de envío
    pass

# ❌ Incorrecto - Múltiples responsabilidades
def procesar_y_enviar_email(destino: str, asunto: str, cuerpo: str) -> bool:
    """Valida formato, guarda en BD y envía email - TODO EN UNA"""
    if '@' not in destino:  # Validación
        return False
    
    # Guardar en BD
    cursor.execute("INSERT INTO emails...")  # Persistencia
    
    # Enviar
    smtp.send(...)  # Envío
    return True
```

**Regla #2 — Dependencias Direccionales**
- Domain no depende de ninguna otra capa.
- Application solo depende de Domain.
- Infrastructure puede depender de Application y Domain.
- User_Interface depende de Application, nunca directamente de Infrastructure.

**Ejemplo:**
```python
# Domain/entidades/usuario.py - ✅ No importa nada externo
from dataclasses import dataclass

@dataclass
class Usuario:
    nombre: str
    email: str

# Application/servicios/servicio_usuario.py - ✅ Solo importa Domain
from Domain.entidades.usuario import Usuario
from Application.interfaces.repositorio_usuario import RepositorioUsuario

# Infrastructure/persistencia/repositorio_usuario_sql.py - ✅ Importa Application
from Domain.entidades.usuario import Usuario
from Application.interfaces.repositorio_usuario import RepositorioUsuario

# User_Interface/vistas/vista_usuarios.py - ✅ Importa Application/backend
from Application.dto.usuario_dto import UsuarioDTO
from backend import Backend

# ❌ Incorrecto - UI importa Infrastructure directamente
from Infrastructure.persistencia import conexion  # ¡MAL!
```

**Regla #3 — Nomenclatura**
- Clases → PascalCase.
- Métodos y variables → snake_case.
- Constantes → MAYUSCULAS.
- Archivos → snake_case.py.

**Ejemplo:**
```python
# Constantes
MAX_INTENTOS_LOGIN = 3
RUTA_BASE_DATOS = "data/app.db"
TIEMPO_ESPERA_SEGUNDOS = 30

# Clase
class GestorAutenticacion:
    
    def __init__(self):
        self.usuario_actual = None
        self.intentos_fallidos = 0
    
    def validar_credenciales(self, usuario: str, password: str) -> bool:
        """Método en snake_case"""
        pass

# Variable local
nombre_completo = "Juan Pérez"
fecha_actual = datetime.now()
```

**Regla #4 — Importaciones Correctas**
```python
# ✅ Correcto - Importaciones absolutas
from Domain.entidades import Usuario
from Application.dto import UsuarioDTO
from Infrastructure.persistencia.repositorios import RepositorioUsuarioSQL

# ✅ Correcto - Orden: estándar, terceros, locales
import os
import sys
from datetime import datetime

import requests
import pandas as pd

from Domain.entidades import Usuario, Producto
from Application.servicios import ServicioUsuario

# ❌ Incorrecto
from ..Domain import Usuario  # Relativa confusa
from Application.servicios import *  # Wildcard
```

**Regla #5 — Manejo de Errores**
- Excepciones de negocio en Domain/excepciones/.
- Excepciones técnicas en Infrastructure.
- La UI solo expone mensajes amigables.

**Ejemplo:**
```python
# Domain/excepciones/excepciones_dominio.py
class ErrorDominio(Exception):
    """Base para errores de dominio"""
    pass

class SaldoInsuficiente(ErrorDominio):
    def __init__(self, saldo_actual: float, monto_requerido: float):
        super().__init__(
            f"Saldo insuficiente: ${saldo_actual} < ${monto_requerido}"
        )

# Application/servicios/servicio_cuenta.py
def retirar(self, cuenta_id: int, monto: float):
    cuenta = self.repositorio.obtener_por_id(cuenta_id)
    
    if cuenta.saldo < monto:
        raise SaldoInsuficiente(cuenta.saldo, monto)  # Error de negocio
    
    cuenta.saldo -= monto

# Infrastructure/persistencia/repositorio_cuenta.py
def obtener_por_id(self, cuenta_id: int):
    try:
        # Código BD
        pass
    except DatabaseError as e:
        raise ErrorInfraestructura(f"Error de BD: {e}")  # Error técnico

# User_Interface/vistas/vista_cuenta.py
try:
    servicio.retirar(cuenta_id, monto)
    messagebox.showinfo("Éxito", "Retiro realizado")
except SaldoInsuficiente as e:
    messagebox.showwarning("Saldo insuficiente", str(e))  # Mensaje amigable
except ErrorInfraestructura:
    messagebox.showerror("Error", "Error del sistema. Intente más tarde")
```

**Regla #6 — Inyección de Dependencias**
```python
# ✅ Correcto
class ServicioUsuario:
    def __init__(self, repositorio: RepositorioUsuario):
        self.repositorio = repositorio  # Inyectada
    
    def crear_usuario(self, datos):
        return self.repositorio.guardar(datos)

# Uso correcto
repositorio = RepositorioUsuarioSQL()
servicio = ServicioUsuario(repositorio)

# ❌ Incorrecto
class ServicioUsuario:
    def __init__(self):
        # Dependencia oculta - difícil de testear
        self.repositorio = RepositorioUsuarioSQL()
    
    def crear_usuario(self, datos):
        return self.repositorio.guardar(datos)

# Para testing - inyección de mock
class RepositorioUsuarioMock(RepositorioUsuario):
    def guardar(self, datos):
        return {"id": 1, **datos}

# Test con inyección
def test_crear_usuario():
    repo_mock = RepositorioUsuarioMock()
    servicio = ServicioUsuario(repo_mock)  # Fácil de testear
    resultado = servicio.crear_usuario({"nombre": "Test"})
    assert resultado["id"] == 1
```

**Regla #7 — DTOs vs Entidades**
- Las entidades de dominio no se exponen directamente a la UI.
- Los DTOs transportan datos entre capas.
- Las entidades contienen lógica; los DTOs solo estructura.

**Ejemplo:**
```python
# Domain/entidades/usuario.py - Con lógica de negocio
class Usuario:
    def __init__(self, nombre, email, password_hash):
        self._nombre = nombre
        self._email = email
        self._password_hash = password_hash
        self._intentos_fallidos = 0
    
    def cambiar_password(self, password_nueva):
        """Lógica de negocio para cambio de password"""
        if len(password_nueva) < 8:
            raise ValueError("Password demasiado corto")
        self._password_hash = hash(password_nueva)
        self._intentos_fallidos = 0
    
    def incrementar_intentos(self):
        """Lógica de negocio para intentos fallidos"""
        self._intentos_fallidos += 1
        if self._intentos_fallidos >= 3:
            self._bloquear()
    
    @property
    def email(self):
        return self._email

# Application/dto/usuario_dto.py - Solo datos
from dataclasses import dataclass

@dataclass
class UsuarioDTO:
    """Solo transporta datos, sin lógica"""
    id: int
    nombre: str
    email: str
    esta_bloqueado: bool
    
    @classmethod
    def desde_entidad(cls, usuario: Usuario):
        return cls(
            id=usuario.id,
            nombre=usuario.nombre,
            email=usuario.email,
            esta_bloqueado=usuario.esta_bloqueado
        )
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'nombre': self.nombre,
            'email': self.email,
            'bloqueado': self.esta_bloqueado
        }

# ✅ Uso correcto - UI usa DTO
def mostrar_usuario(usuario_dto: UsuarioDTO):
    print(f"Nombre: {usuario_dto.nombre}")
    print(f"Email: {usuario_dto.email}")

# ❌ Incorrecto - UI usando entidad directamente
def mostrar_usuario(usuario: Usuario):
    print(f"Nombre: {usuario._nombre}")  # Acceso a privado
    # La UI podría llamar a métodos de negocio indebidamente
```

**Regla #8 — backend.py como Adaptador**
```python
# backend.py - Capa de adaptación entre UI y Application
"""
backend.py - Interfaz unificada para la UI
Configura dependencias y expone servicios de forma simple.
"""

from typing import List, Optional, Dict, Any
import logging

from Application.servicios.servicio_usuario import ServicioUsuario
from Application.servicios.servicio_producto import ServicioProducto
from Application.dto.usuario_dto import UsuarioDTO, SolicitudUsuarioDTO
from Application.dto.producto_dto import ProductoDTO

from Infrastructure.persistencia.repositorios import (
    RepositorioUsuarioSQL,
    RepositorioProductoSQL
)
from Infrastructure.persistencia.base_datos import obtener_conexion
from Infrastructure.logging.logger_config import configurar_logging

class Backend:
    """
    Adaptador entre UI y Application.
    Oculta la complejidad de infraestructura.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        self._inicializar_logging()
        self._inicializar_servicios()
        self._inicializar_conexiones()
    
    def _inicializar_logging(self):
        """Configura logging"""
        configurar_logging(
            nivel=self.config.get('log_level', 'INFO'),
            archivo=self.config.get('log_file')
        )
    
    def _inicializar_servicios(self):
        """Configura e inyecta dependencias"""
        # Obtener conexión
        self.conexion = obtener_conexion(self.config.get('db_path'))
        
        # Crear repositorios
        self.repo_usuario = RepositorioUsuarioSQL(self.conexion)
        self.repo_producto = RepositorioProductoSQL(self.conexion)
        
        # Crear servicios con inyección
        self.servicio_usuario = ServicioUsuario(self.repo_usuario)
        self.servicio_producto = ServicioProducto(self.repo_producto)
    
    def _inicializar_conexiones(self):
        """Verifica conexiones"""
        try:
            self.repo_usuario.verificar_conexion()
            self.logger.info("Conexiones establecidas correctamente")
        except Exception as e:
            self.logger.error(f"Error en conexiones: {e}")
            raise
    
    # ============= API PÚBLICA PARA UI =============
    
    # --- Usuarios ---
    def obtener_usuarios(self, filtros: Optional[Dict] = None) -> List[UsuarioDTO]:
        """Obtiene lista de usuarios"""
        try:
            usuarios = self.servicio_usuario.listar(filtros)
            return [UsuarioDTO.desde_entidad(u) for u in usuarios]
        except Exception as e:
            self.logger.error(f"Error obteniendo usuarios: {e}")
            return []
    
    def crear_usuario(self, datos: Dict) -> Optional[UsuarioDTO]:
        """Crea un nuevo usuario"""
        try:
            solicitud = SolicitudUsuarioDTO.desde_dict(datos)
            usuario = self.servicio_usuario.crear(solicitud)
            return UsuarioDTO.desde_entidad(usuario)
        except Exception as e:
            self.logger.error(f"Error creando usuario: {e}")
            raise  # La UI manejará la excepción
    
    def obtener_usuario(self, usuario_id: int) -> Optional[UsuarioDTO]:
        """Obtiene un usuario por ID"""
        try:
            usuario = self.servicio_usuario.obtener_por_id(usuario_id)
            return UsuarioDTO.desde_entidad(usuario) if usuario else None
        except Exception as e:
            self.logger.error(f"Error obteniendo usuario {usuario_id}: {e}")
            return None
    
    def actualizar_usuario(self, usuario_id: int, datos: Dict) -> bool:
        """Actualiza un usuario"""
        try:
            return self.servicio_usuario.actualizar(usuario_id, datos)
        except Exception as e:
            self.logger.error(f"Error actualizando usuario {usuario_id}: {e}")
            return False
    
    def eliminar_usuario(self, usuario_id: int) -> bool:
        """Elimina un usuario"""
        try:
            return self.servicio_usuario.eliminar(usuario_id)
        except Exception as e:
            self.logger.error(f"Error eliminando usuario {usuario_id}: {e}")
            return False
    
    # --- Productos ---
    def obtener_productos(self, categoria: Optional[str] = None) -> List[ProductoDTO]:
        """Obtiene lista de productos"""
        try:
            productos = self.servicio_producto.listar(categoria)
            return [ProductoDTO.desde_entidad(p) for p in productos]
        except Exception as e:
            self.logger.error(f"Error obteniendo productos: {e}")
            return []
    
    # --- Utilidades ---
    def cerrar(self):
        """Cierra conexiones y libera recursos"""
        try:
            if hasattr(self, 'conexion'):
                self.conexion.close()
            self.logger.info("Backend cerrado correctamente")
        except Exception as e:
            self.logger.error(f"Error cerrando backend: {e}")
```

**Regla #9 — bootstrap.py como Orquestador**
```python
# bootstrap.py - Punto de entrada de la aplicación
"""
bootstrap.py - Orquestador principal
Configura e inicia la aplicación según el modo.
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Optional

# Añadir directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend import Backend
from User_Interface.layout import crear_interfaz
from Scripts.seed_data import cargar_datos_prueba
from Infrastructure.logging.logger_config import configurar_logging

class Application:
    """Clase principal que orquesta la aplicación"""
    
    def __init__(self):
        self.backend: Optional[Backend] = None
        self.modo: str = "desarrollo"
        self._cargar_configuracion()
    
    def _cargar_configuracion(self):
        """Carga configuración desde variables de entorno"""
        from dotenv import load_dotenv
        
        env_file = Path('.env')
        if env_file.exists():
            load_dotenv(env_file)
    
    def inicializar(self, modo: str = "desarrollo", datos_prueba: bool = False):
        """Inicializa todos los componentes"""
        self.modo = modo
        
        # Configurar logging según modo
        nivel_log = "DEBUG" if modo == "desarrollo" else "INFO"
        archivo_log = f"logs/app_{modo}.log"
        configurar_logging(nivel=nivel_log, archivo=archivo_log)
        
        # Configuración específica por modo
        config = self._obtener_config_modo(modo)
        
        # Inicializar backend
        self.backend = Backend(config)
        
        # Cargar datos de prueba si es necesario
        if datos_prueba or modo == "desarrollo":
            self._cargar_datos_prueba()
        
        print(f"✅ Aplicación inicializada en modo: {modo}")
    
    def _obtener_config_modo(self, modo: str) -> dict:
        """Obtiene configuración según modo"""
        configs = {
            "desarrollo": {
                "db_path": "data/dev.db",
                "log_level": "DEBUG",
                "log_file": "logs/dev.log",
                "debug": True
            },
            "produccion": {
                "db_path": os.getenv("DB_PATH", "data/prod.db"),
                "log_level": "INFO",
                "log_file": "logs/prod.log",
                "debug": False
            },
            "test": {
                "db_path": ":memory:",
                "log_level": "ERROR",
                "log_file": None,
                "debug": True
            }
        }
        return configs.get(modo, configs["desarrollo"])
    
    def _cargar_datos_prueba(self):
        """Carga datos de prueba"""
        try:
            print("📦 Cargando datos de prueba...")
            cargar_datos_prueba(self.backend)
            print("✅ Datos de prueba cargados")
        except Exception as e:
            print(f"⚠️ Error cargando datos de prueba: {e}")
    
    def ejecutar(self):
        """Ejecuta la aplicación"""
        if not self.backend:
            raise RuntimeError("Aplicación no inicializada")
        
        try:
            print(f"🚀 Iniciando aplicación...")
            
            # Crear y ejecutar interfaz
            app = crear_interfaz(self.backend)
            app.mainloop()
            
        except KeyboardInterrupt:
            print("\n👋 Aplicación detenida por el usuario")
        except Exception as e:
            print(f"❌ Error en ejecución: {e}")
            return 1
        finally:
            self.cerrar()
        
        return 0
    
    def cerrar(self):
        """Limpia recursos"""
        if self.backend:
            self.backend.cerrar()
        print("👋 Aplicación cerrada")

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Mi Aplicación")
    parser.add_argument(
        "--modo",
        choices=["desarrollo", "produccion", "test"],
        default="desarrollo",
        help="Modo de ejecución"
    )
    parser.add_argument(
        "--datos-prueba",
        action="store_true",
        help="Cargar datos de prueba"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="1.0.0"
    )
    
    args = parser.parse_args()
    
    # Crear y ejecutar aplicación
    app = Application()
    app.inicializar(modo=args.modo, datos_prueba=args.datos_prueba)
    sys.exit(app.ejecutar())

if __name__ == "__main__":
    main()
```

**Regla #10 — Pruebas**
- Cada módulo tiene su archivo de test.
- Pruebas independientes y repetibles.
- Uso de mocks para servicios externos.
- Cobertura recomendada ≥ 80%.

**Ejemplo: Tests/test_domain/test_usuario.py**
```python
"""
Tests/test_domain/test_usuario.py - Pruebas de dominio
"""

import pytest
from datetime import datetime
from Domain.entidades.usuario import Usuario, EmailInvalido
from Domain.value_objects.email import Email

class TestUsuario:
    """Pruebas para la entidad Usuario"""
    
    def setup_method(self):
        """Configuración antes de cada prueba"""
        self.email_valido = Email("test@example.com")
        self.usuario = Usuario(
            id=1,
            nombre="Juan Pérez",
            email=self.email_valido
        )
    
    def test_crear_usuario_valido(self):
        """Debe crear usuario con datos válidos"""
        assert self.usuario.nombre == "Juan Pérez"
        assert self.usuario.email == self.email_valido
        assert self.usuario.activo is True
        assert isinstance(self.usuario.fecha_registro, datetime)
    
    def test_cambiar_email_valido(self):
        """Debe permitir cambiar a email válido"""
        nuevo_email = Email("juan.perez@example.com")
        self.usuario.cambiar_email(nuevo_email)
        assert self.usuario.email == nuevo_email
    
    def test_cambiar_email_invalido_lanza_error(self):
        """Debe lanzar error al cambiar a email inválido"""
        with pytest.raises(EmailInvalido) as exc_info:
            self.usuario.cambiar_email(Email("email-invalido"))
        assert "inválido" in str(exc_info.value).lower()
    
    def test_desactivar_usuario(self):
        """Debe desactivar usuario correctamente"""
        self.usuario.desactivar()
        assert self.usuario.activo is False
    
    @pytest.mark.parametrize("nombre,email", [
        ("Ana García", "ana@email.com"),
        ("Carlos López", "carlos@email.com"),
        ("María González", "maria@email.com")
    ])
    def test_crear_varios_usuarios(self, nombre, email):
        """Prueba parametrizada para crear usuarios"""
        usuario = Usuario(
            id=2,
            nombre=nombre,
            email=Email(email)
        )
        assert usuario.nombre == nombre
        assert usuario.email.valor == email

class TestEmailValueObject:
    """Pruebas para el Value Object Email"""
    
    def test_email_valido(self):
        """Debe aceptar emails válidos"""
        emails_validos = [
            "test@example.com",
            "usuario.nombre@dominio.com",
            "email+etiqueta@sub.dominio.es"
        ]
        
        for email_str in emails_validos:
            email = Email(email_str)
            assert email.valor == email_str
    
    def test_email_invalido_lanza_error(self):
        """Debe rechazar emails inválidos"""
        emails_invalidos = [
            "",
            "sin arroba",
            "@sinusuario.com",
            "usuario@sinpunto"
        ]
        
        for email_str in emails_invalidos:
            with pytest.raises(EmailInvalido):
                Email(email_str)
```

**Ejemplo: Tests/test_application/test_servicio_usuario.py**
```python
"""
Tests/test_application/test_servicio_usuario.py - Pruebas de aplicación
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from Application.servicios.servicio_usuario import ServicioUsuario
from Application.dto.usuario_dto import SolicitudUsuarioDTO
from Domain.entidades.usuario import Usuario
from Domain.value_objects.email import Email
from Domain.excepciones import UsuarioNoEncontrado, EmailInvalido

class TestServicioUsuario:
    """Pruebas para ServicioUsuario"""
    
    @pytest.fixture
    def mock_repositorio(self):
        """Fixture para repositorio mock"""
        repo = Mock()
        
        # Configurar comportamientos por defecto
        repo.guardar.return_value = Usuario(
            id=1,
            nombre="Test",
            email=Email("test@example.com")
        )
        repo.obtener_por_id.return_value = Usuario(
            id=1,
            nombre="Test",
            email=Email("test@example.com")
        )
        
        return repo
    
    @pytest.fixture
    def servicio(self, mock_repositorio):
        """Fixture para servicio con mock"""
        return ServicioUsuario(repositorio=mock_repositorio)
    
    def test_crear_usuario_exitoso(self, servicio, mock_repositorio):
        """Debe crear usuario con datos válidos"""
        # Arrange
        solicitud = SolicitudUsuarioDTO(
            nombre="Juan Pérez",
            email="juan@example.com",
            telefono="123456789"
        )
        
        # Act
        resultado = servicio.crear(solicitud)
        
        # Assert
        assert resultado.nombre == "Juan Pérez"
        assert resultado.email.valor == "juan@example.com"
        mock_repositorio.guardar.assert_called_once()
    
    def test_crear_usuario_email_invalido(self, servicio, mock_repositorio):
        """Debe fallar al crear con email inválido"""
        solicitud = SolicitudUsuarioDTO(
            nombre="Juan Pérez",
            email="email-invalido",
            telefono="123456789"
        )
        
        with pytest.raises(EmailInvalido):
            servicio.crear(solicitud)
        
        mock_repositorio.guardar.assert_not_called()
    
    def test_obtener_usuario_existente(self, servicio, mock_repositorio):
        """Debe obtener usuario existente"""
        usuario = servicio.obtener_por_id(1)
        
        assert usuario is not None
        assert usuario.id == 1
        mock_repositorio.obtener_por_id.assert_called_with(1)
    
    def test_obtener_usuario_inexistente(self, servicio, mock_repositorio):
        """Debe retornar None para usuario inexistente"""
        mock_repositorio.obtener_por_id.return_value = None
        
        usuario = servicio.obtener_por_id(999)
        
        assert usuario is None
    
    def test_actualizar_usuario_exitoso(self, servicio, mock_repositorio):
        """Debe actualizar usuario existente"""
        mock_repositorio.actualizar.return_value = True
        
        resultado = servicio.actualizar(1, {"nombre": "Nuevo Nombre"})
        
        assert resultado is True
        mock_repositorio.actualizar.assert_called_once()
    
    def test_eliminar_usuario_exitoso(self, servicio, mock_repositorio):
        """Debe eliminar usuario existente"""
        mock_repositorio.eliminar.return_value = True
        
        resultado = servicio.eliminar(1)
        
        assert resultado is True
        mock_repositorio.eliminar.assert_called_with(1)
    
    def test_listar_usuarios(self, servicio, mock_repositorio):
        """Debe listar usuarios"""
        mock_repositorio.listar.return_value = [
            Usuario(id=1, nombre="A", email=Email("a@e.com")),
            Usuario(id=2, nombre="B", email=Email("b@e.com"))
        ]
        
        usuarios = servicio.listar()
        
        assert len(usuarios) == 2
        mock_repositorio.listar.assert_called_once()
```

**Ejemplo: Tests/test_infrastructure/test_repositorios.py**
```python
"""
Tests/test_infrastructure/test_repositorios.py - Pruebas de integración
"""

import pytest
import sqlite3
from datetime import datetime

from Infrastructure.persistencia.repositorios.repositorio_usuario_sql import (
    RepositorioUsuarioSQL
)
from Domain.entidades.usuario import Usuario
from Domain.value_objects.email import Email

@pytest.fixture
def db_conexion():
    """Fixture para base de datos en memoria"""
    conn = sqlite3.connect(":memory:")
    
    # Crear tablas
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            activo BOOLEAN DEFAULT TRUE,
            fecha_registro TIMESTAMP
        )
    """)
    conn.commit()
    
    yield conn
    conn.close()

@pytest.fixture
def repositorio(db_conexion):
    """Fixture para repositorio con BD en memoria"""
    return RepositorioUsuarioSQL(db_conexion)

class TestRepositorioUsuarioSQL:
    """Pruebas de integración para repositorio SQL"""
    
    def test_guardar_y_obtener_usuario(self, repositorio):
        """Debe guardar y recuperar un usuario"""
        # Arrange
        usuario = Usuario(
            id=None,
            nombre="Usuario Test",
            email=Email("test@example.com")
        )
        
        # Act - Guardar
        usuario_guardado = repositorio.guardar(usuario)
        
        # Assert
        assert usuario_guardado.id is not None
        
        # Act - Obtener
        usuario_recuperado = repositorio.obtener_por_id(usuario_guardado.id)
        
        # Assert
        assert usuario_recuperado is not None
        assert usuario_recuperado.nombre == "Usuario Test"
        assert usuario_recuperado.email.valor == "test@example.com"
    
    def test_obtener_por_email(self, repositorio):
        """Debe buscar usuario por email"""
        # Arrange
        usuario = Usuario(
            id=None,
            nombre="Email Test",
            email=Email("unico@example.com")
        )
        repositorio.guardar(usuario)
        
        # Act
        encontrado = repositorio.obtener_por_email("unico@example.com")
        
        # Assert
        assert encontrado is not None
        assert encontrado.nombre == "Email Test"
    
    def test_actualizar_usuario(self, repositorio):
        """Debe actualizar datos de usuario"""
        # Arrange
        usuario = Usuario(
            id=None,
            nombre="Original",
            email=Email("original@example.com")
        )
        usuario = repositorio.guardar(usuario)
        
        # Act
        usuario.nombre = "Actualizado"
        resultado = repositorio.actualizar(usuario)
        
        # Assert
        assert resultado is True
        
        usuario_actualizado = repositorio.obtener_por_id(usuario.id)
        assert usuario_actualizado.nombre == "Actualizado"
    
    def test_eliminar_usuario(self, repositorio):
        """Debe eliminar usuario (borrado lógico)"""
        # Arrange
        usuario = Usuario(
            id=None,
            nombre="Eliminar",
            email=Email("eliminar@example.com")
        )
        usuario = repositorio.guardar(usuario)
        
        # Act
        resultado = repositorio.eliminar(usuario.id)
        
        # Assert
        assert resultado is True
        
        usuario_eliminado = repositorio.obtener_por_id(usuario.id)
        assert usuario_eliminado.activo is False
    
    def test_listar_activos(self, repositorio):
        """Debe listar solo usuarios activos"""
        # Arrange
        usuario1 = Usuario(id=None, nombre="Activo 1", email=Email("a1@e.com"))
        usuario2 = Usuario(id=None, nombre="Activo 2", email=Email("a2@e.com"))
        usuario3 = Usuario(id=None, nombre="Inactivo", email=Email("i@e.com"))
        
        repositorio.guardar(usuario1)
        repositorio.guardar(usuario2)
        usuario3 = repositorio.guardar(usuario3)
        repositorio.eliminar(usuario3.id)  # Desactivar
        
        # Act
        activos = repositorio.listar(solo_activos=True)
        
        # Assert
        assert len(activos) == 2
        assert all(u.activo for u in activos)
```

**Regla #11 — Documentación**
- Docstrings obligatorios en servicios públicos.
- Tipado explícito en funciones críticas.

**Ejemplo:**
```python
def procesar_pago(
    usuario_id: int,
    monto: float,
    metodo_pago: str,
    token_tarjeta: Optional[str] = None
) -> Dict[str, any]:
    """
    Procesa un pago para un usuario específico.
    
    Esta función coordina todo el flujo de procesamiento de pagos,
    incluyendo validaciones, comunicación con pasarela de pago,
    y actualización del estado de la transacción.
    
    Args:
        usuario_id (int): Identificador único del usuario
            Debe ser un ID válido existente en la base de datos
        monto (float): Cantidad a cobrar
            Debe ser mayor a 0 y menor a 10000
        metodo_pago (str): Método de pago seleccionado
            Valores aceptados: 'tarjeta', 'transferencia', 'efectivo'
        token_tarjeta (str, opcional): Token de tarjeta para método tarjeta
    
    Returns:
        Dict[str, Any]: Diccionario con los siguientes campos:
            - 'exitoso' (bool): True si el pago fue exitoso
            - 'transaccion_id' (str): ID de la transacción (si existe)
            - 'mensaje' (str): Mensaje descriptivo del resultado
            - 'timestamp' (str): Fecha y hora del procesamiento
            - 'monto' (float): Monto procesado
    
    Raises:
        UsuarioNoEncontrado: Si el usuario_id no existe
        PagoRechazado: Si la pasarela de pago rechaza la transacción
        MetodoPagoInvalido: Si metodo_pago no es válido
        ValueError: Si los parámetros no cumplen las validaciones
    
    Example:
        >>> resultado = procesar_pago(
        ...     usuario_id=123,
        ...     monto=99.99,
        ...     metodo_pago='tarjeta',
        ...     token_tarjeta='tok_visa_123'
        ... )
        >>> if resultado['exitoso']:
        ...     print(f"Pago exitoso: {resultado['transaccion_id']}")
        ... else:
        ...     print(f"Error: {resultado['mensaje']}")
    
    Note:
        - Para método 'efectivo' no se requiere token
        - Los pagos se registran en la tabla 'transacciones'
        - Se envía email de confirmación al usuario
    """
    # Validaciones básicas
    if monto <= 0:
        raise ValueError("El monto debe ser positivo")
    
    if monto > 10000:
        raise ValueError("Monto máximo excedido")
    
    # Lógica del pago...
    pass
```

**Regla #12 — Git Workflow**
- main → Producción.
- develop → Integración.
- feature/* → Nuevas funcionalidades.
- hotfix/* → Correcciones urgentes.
- release/* → Preparación de versiones.

**Convenciones de commits:**
```bash
# Formato: tipo(alcance): descripción

# Tipos principales:
feat:     # Nueva característica
fix:      # Corrección de bug
docs:     # Documentación
style:    # Formato, estilo (no afecta código)
refactor: # Refactorización
test:     # Pruebas
chore:    # Tareas de mantenimiento

# Ejemplos:
git commit -m "feat(usuarios): añadir búsqueda por email"
git commit -m "fix(pagos): corregir cálculo de impuestos"
git commit -m "docs(api): actualizar documentación de endpoints"
git commit -m "test(usuarios): añadir pruebas para registro"
git commit -m "refactor(backend): simplificar inyección de dependencias"
```

**.gitignore recomendado:**
```gitignore
# Python
__pycache__/
*.py[cod]
*.so
.Python
venv/
env/
ENV/
pip-log.txt
pip-delete-this-directory.txt

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Base de datos
*.db
*.sqlite3
*.sqlite

# Logs
*.log
logs/

# Archivos de entorno
.env
.env.local
.env.*.local

# Archivos de configuración local
config.local.py

# Directorios de datos
data/
uploads/
temp/
downloads/

# Archivos de sistema
.DS_Store
Thumbs.db
desktop.ini

# Archivos de caché
.cache/
.pytest_cache/
.coverage
htmlcov/

# Archivos de distribución
dist/
build/
*.egg-info/

# Archivos de documentación
/docs/_build/
```

### Flujo de Inicialización

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate      # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con configuraciones locales

# Inicializar base de datos
python Scripts/migraciones.py init

# Cargar datos de prueba (opcional)
python Scripts/seed_data.py

# Ejecutar aplicación
python bootstrap.py --modo desarrollo --datos-prueba

# Ejecutar pruebas
pytest Tests/
pytest Tests/ --cov=Application --cov=Domain --cov-report=html

# Ejecutar linter
flake8 Application/ Domain/ Infrastructure/
black . --check
```

**Estructura completa Nivel 4:**
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
├── User_Interface/
│   ├── __init__.py
│   ├── layout.py
│   └── vistas/
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

Capas totales:
- Domain
- Application
- Infrastructure
- User_Interface
- Scripts
- Tests
- Docs
- **Presentation** (nueva)

### Reglas MVVM

**Regla #13 — Separación MVVM**
Vista → ViewModel → Modelo.
- La Vista contiene solo widgets y lógica de presentación.
- El ViewModel contiene estado observable y lógica de UI.
- El Modelo contiene datos (UI o negocio según capa).
- La Vista nunca accede directamente a Domain o Infrastructure.

**Ejemplo:**
```python
# Vista (User_Interface) - Solo widgets y binding
class VistaUsuarios:
    def __init__(self, parent, viewmodel):
        self.viewmodel = viewmodel
        self.viewmodel.suscribir(self._on_cambio)
        self._crear_widgets()
    
    def _crear_widgets(self):
        self.entry_nombre = ttk.Entry()
        self.entry_nombre.bind('<KeyRelease>', self._actualizar_nombre)
        self.tree = ttk.Treeview()
    
    def _actualizar_nombre(self, event):
        self.viewmodel.nombre_editado = self.entry_nombre.get()
    
    def _on_cambio(self, evento):
        if evento.nombre == 'usuarios':
            self._actualizar_tabla()

# ViewModel (Presentation) - Estado y lógica de UI
class UsuarioViewModel(ViewModelBase):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self._usuarios = []
        self._nombre_editado = ""
    
    @property
    def nombre_editado(self):
        return self._nombre_editado
    
    @nombre_editado.setter
    def nombre_editado(self, valor):
        self._nombre_editado = valor
        self.notificar_cambio('nombre_editado')
    
    def cargar_usuarios(self):
        self._usuarios = self.backend.obtener_usuarios()
        self.notificar_cambio('usuarios')
```

**Regla #14 — ViewModelBase obligatorio**
- Todos los ViewModels heredan de `ViewModelBase`.
- Deben notificar cambios mediante un sistema observable.
- El estado (`ocupado`, `mensaje_estado`, errores) vive en el ViewModel.
- No deben importar nada de `User_Interface`.

**Ejemplo:**
```python
# Presentation/viewmodels/viewmodel_base.py
class ViewModelBase:
    """Clase base para todos los ViewModels"""
    
    def __init__(self):
        self._suscriptores = []
        self._propiedades = {}
        self._errores = {}
        self._ocupado = False
        self._mensaje_estado = ""
    
    def suscribir(self, callback):
        """Suscribe una vista a los cambios"""
        self._suscriptores.append(callback)
    
    def notificar_cambio(self, nombre_propiedad, valor_anterior=None):
        """Notifica cambio a todas las vistas suscritas"""
        evento = {
            'nombre': nombre_propiedad,
            'valor_anterior': valor_anterior,
            'valor_nuevo': self._propiedades.get(nombre_propiedad)
        }
        
        for callback in self._suscriptores:
            try:
                callback(evento)
            except Exception as e:
                print(f"Error notificando: {e}")
    
    def establecer_propiedad(self, nombre, valor):
        """Establece propiedad y notifica si cambió"""
        valor_anterior = self._propiedades.get(nombre)
        
        if valor_anterior != valor:
            self._propiedades[nombre] = valor
            self.notificar_cambio(nombre, valor_anterior)
            return True
        return False
    
    @property
    def ocupado(self):
        return self._ocupado
    
    @ocupado.setter
    def ocupado(self, valor):
        self.establecer_propiedad('_ocupado', valor)
    
    @property
    def mensaje_estado(self):
        return self._mensaje_estado
    
    @mensaje_estado.setter
    def mensaje_estado(self, mensaje):
        self.establecer_propiedad('_mensaje_estado', mensaje)
    
    def agregar_error(self, propiedad, mensaje):
        self._errores[propiedad] = mensaje
        self.notificar_cambio(f"error_{propiedad}")
    
    def limpiar_error(self, propiedad):
        if propiedad in self._errores:
            del self._errores[propiedad]
            self.notificar_cambio(f"error_{propiedad}")
```

**Regla #15 — Modelos de UI**
- Son `dataclasses` simples.
- No contienen lógica de negocio.
- Pueden contener validaciones de formato (no reglas de negocio).
- Deben poder convertirse a DTO (`to_dict()` o adaptador similar).

**Ejemplo:**
```python
# Presentation/models/ui_usuario.py
from dataclasses import dataclass
from typing import Optional
import re

@dataclass
class UIUsuario:
    """Modelo específico para la UI"""
    id: Optional[int] = None
    nombre: str = ""
    email: str = ""
    telefono: str = ""
    activo: bool = True
    
    # Estado de UI
    seleccionado: bool = False
    editando: bool = False
    expandido: bool = False
    
    def validar_formato(self) -> dict:
        """Validaciones de formato (no reglas de negocio)"""
        errores = {}
        
        if self.nombre and len(self.nombre.strip()) < 3:
            errores['nombre'] = "Mínimo 3 caracteres"
        
        if self.email and not re.match(r'^[^@]+@[^@]+\.[^@]+$', self.email):
            errores['email'] = "Formato email inválido"
        
        if self.telefono and not re.match(r'^[\d\s-]{8,}$', self.telefono):
            errores['telefono'] = "Formato teléfono inválido"
        
        return errores
    
    def to_dict(self) -> dict:
        """Convierte a dict para enviar al backend"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'email': self.email,
            'telefono': self.telefono,
            'activo': self.activo
        }
    
    @classmethod
    def from_dto(cls, dto) -> 'UIUsuario':
        """Crea desde DTO del backend"""
        return cls(
            id=dto.id,
            nombre=dto.nombre,
            email=dto.email,
            telefono=getattr(dto, 'telefono', ''),
            activo=getattr(dto, 'activo', True)
        )
```

**Regla #16 — ViewModels Específicos**
- Encapsulan filtros, selección, estado de edición.
- Transforman DTOs en modelos de UI.
- Coordinan llamadas al backend.
- Nunca contienen acceso directo a base de datos.

**Ejemplo:**
```python
# Presentation/viewmodels/usuario_viewmodel.py
from typing import List, Optional
from Presentation.viewmodels.viewmodel_base import ViewModelBase
from Presentation.models.ui_usuario import UIUsuario

class UsuarioViewModel(ViewModelBase):
    """ViewModel para gestión de usuarios"""
    
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self._usuarios: List[UIUsuario] = []
        self._usuario_seleccionado: Optional[UIUsuario] = None
        self._filtro_nombre: str = ""
        self._modo_edicion: bool = False
        
        self.cargar_usuarios()
    
    @property
    def usuarios(self) -> List[UIUsuario]:
        """Lista filtrada de usuarios"""
        if not self._filtro_nombre:
            return self._usuarios
        
        filtro = self._filtro_nombre.lower()
        return [
            u for u in self._usuarios
            if filtro in u.nombre.lower()
        ]
    
    @property
    def filtro_nombre(self) -> str:
        return self._filtro_nombre
    
    @filtro_nombre.setter
    def filtro_nombre(self, valor: str):
        self.establecer_propiedad('_filtro_nombre', valor)
        self.notificar_cambio('usuarios')
    
    @property
    def usuario_seleccionado(self) -> Optional[UIUsuario]:
        return self._usuario_seleccionado
    
    @usuario_seleccionado.setter
    def usuario_seleccionado(self, usuario: Optional[UIUsuario]):
        self.establecer_propiedad('_usuario_seleccionado', usuario)
        
        if usuario and not self._modo_edicion:
            self._modo_edicion = False
    
    @property
    def modo_edicion(self) -> bool:
        return self._modo_edicion
    
    @modo_edicion.setter
    def modo_edicion(self, valor: bool):
        self.establecer_propiedad('_modo_edicion', valor)
    
    def cargar_usuarios(self):
        """Carga usuarios desde backend"""
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
    
    def crear_nuevo(self):
        """Prepara creación de nuevo usuario"""
        self._usuario_seleccionado = UIUsuario()
        self.modo_edicion = True
        self.notificar_cambio('usuario_seleccionado')
    
    def guardar_actual(self) -> bool:
        """Guarda el usuario en edición"""
        if not self._usuario_seleccionado:
            return False
        
        # Validar formato
        errores = self._usuario_seleccionado.validar_formato()
        if errores:
            for campo, msg in errores.items():
                self.agregar_error(campo, msg)
            return False
        
        self.ocupado = True
        self.mensaje_estado = "Guardando..."
        
        try:
            if self._usuario_seleccionado.id:
                # Actualizar existente
                self.backend.actualizar_usuario(
                    self._usuario_seleccionado.id,
                    self._usuario_seleccionado.to_dict()
                )
            else:
                # Crear nuevo
                dto = self.backend.crear_usuario(
                    self._usuario_seleccionado.to_dict()
                )
                self._usuario_seleccionado.id = dto.id
            
            self.mensaje_estado = "Guardado correctamente"
            self.modo_edicion = False
            self.cargar_usuarios()  # Recargar lista
            return True
            
        except Exception as e:
            self.mensaje_estado = f"Error: {e}"
            return False
        finally:
            self.ocupado = False
    
    def eliminar_seleccionado(self) -> bool:
        """Elimina usuario seleccionado"""
        if not self._usuario_seleccionado or not self._usuario_seleccionado.id:
            return False
        
        self.ocupado = True
        self.mensaje_estado = "Eliminando..."
        
        try:
            self.backend.eliminar_usuario(self._usuario_seleccionado.id)
            self.mensaje_estado = "Usuario eliminado"
            self._usuario_seleccionado = None
            self.cargar_usuarios()
            return True
        except Exception as e:
            self.mensaje_estado = f"Error: {e}"
            return False
        finally:
            self.ocupado = False
```

**Regla #17 — Comandos**
- Las acciones complejas se encapsulan en clases `Comando*`.
- Deben exponer `ejecutar()`.
- Opcionalmente pueden implementar `deshacer()`.
- Deben verificar `puede_ejecutar()` antes de actuar.

**Ejemplo:**
```python
# Presentation/commands/comando_base.py
from abc import ABC, abstractmethod
from typing import Any, Optional

class ComandoBase(ABC):
    """Clase base para todos los comandos"""
    
    def __init__(self, viewmodel):
        self.viewmodel = viewmodel
        self._ejecutado = False
    
    @abstractmethod
    def ejecutar(self, *args, **kwargs) -> Any:
        """Ejecuta el comando"""
        pass
    
    def puede_ejecutar(self) -> bool:
        """Verifica si puede ejecutarse"""
        return not self.viewmodel.ocupado
    
    def deshacer(self):
        """Deshace la acción (opcional)"""
        pass
    
    @property
    def ejecutado(self) -> bool:
        return self._ejecutado

# Presentation/commands/comandos_usuario.py
class ComandoCargarUsuarios(ComandoBase):
    """Comando para cargar usuarios"""
    
    def ejecutar(self, *args, **kwargs):
        if not self.puede_ejecutar():
            return
        
        self.viewmodel.cargar_usuarios()
        self._ejecutado = True

class ComandoGuardarUsuario(ComandoBase):
    """Comando para guardar usuario"""
    
    def __init__(self, viewmodel):
        super().__init__(viewmodel)
        self._respaldo = None
    
    def ejecutar(self, *args, **kwargs):
        if not self.puede_ejecutar():
            return False
        
        # Guardar respaldo por si se necesita deshacer
        if self.viewmodel.usuario_seleccionado:
            self._respaldo = self.viewmodel.usuario_seleccionado.to_dict()
        
        resultado = self.viewmodel.guardar_actual()
        if resultado:
            self._ejecutado = True
        
        return resultado
    
    def deshacer(self):
        """Deshace el guardado"""
        if self._ejecutado and self._respaldo:
            # Lógica para restaurar estado anterior
            self.viewmodel.mensaje_estado = "Operación deshecha"
            self.viewmodel.cargar_usuarios()
```

**Regla #18 — Binding Vista–ViewModel**
- La Vista se suscribe a cambios del ViewModel (Observer).
- El binding es bidireccional cuando corresponde.
- La Vista nunca manipula directamente colecciones internas del ViewModel.

**Ejemplo:**
```python
# User_Interface/vistas/vista_usuarios.py
class VistaUsuarios:
    """Vista con binding al ViewModel"""
    
    def __init__(self, parent, viewmodel):
        self.parent = parent
        self.viewmodel = viewmodel
        self._binding_activo = True
        
        # Suscribirse a cambios del ViewModel
        self.viewmodel.suscribir(self._on_viewmodel_changed)
        
        self._crear_widgets()
        self._configurar_bindings()
    
    def _crear_widgets(self):
        """Crea widgets de la interfaz"""
        self.entry_filtro = ttk.Entry()
        self.entry_nombre = ttk.Entry()
        self.entry_email = ttk.Entry()
        self.tree = ttk.Treeview()
        self.lbl_estado = ttk.Label()
    
    def _configurar_bindings(self):
        """Configura bindings con ViewModel"""
        # Binding de entrada → ViewModel
        self.entry_filtro.bind(
            '<KeyRelease>',
            lambda e: self._actualizar_filtro()
        )
        
        self.entry_nombre.bind(
            '<KeyRelease>',
            lambda e: self._actualizar_usuario()
        )
        
        self.entry_email.bind(
            '<KeyRelease>',
            lambda e: self._actualizar_usuario()
        )
        
        # Binding de selección
        self.tree.bind(
            '<<TreeviewSelect>>',
            self._on_seleccionar
        )
    
    def _actualizar_filtro(self):
        """Actualiza filtro en ViewModel"""
        if self._binding_activo:
            self.viewmodel.filtro_nombre = self.entry_filtro.get()
    
    def _actualizar_usuario(self):
        """Actualiza usuario en edición"""
        if not self._binding_activo:
            return
        
        if self.viewmodel.usuario_seleccionado:
            self.viewmodel.usuario_seleccionado.nombre = self.entry_nombre.get()
            self.viewmodel.usuario_seleccionado.email = self.entry_email.get()
    
    def _on_seleccionar(self, event):
        """Maneja selección en tabla"""
        seleccion = self.tree.selection()
        if seleccion:
            usuario_id = int(seleccion[0])
            # Buscar en ViewModel
            for u in self.viewmodel._usuarios:
                if u.id == usuario_id:
                    self.viewmodel.usuario_seleccionado = u
                    break
    
    def _on_viewmodel_changed(self, evento):
        """Callback cuando cambia el ViewModel"""
        if not self._binding_activo:
            return
        
        nombre = evento['nombre']
        
        if nombre == 'usuarios':
            self._actualizar_tabla()
        elif nombre == '_usuario_seleccionado':
            self._actualizar_formulario()
        elif nombre == '_mensaje_estado':
            self.lbl_estado.config(text=evento['valor_nuevo'])
        elif nombre.startswith('error_'):
            campo = nombre.replace('error_', '')
            self._mostrar_error(campo, evento['valor_nuevo'])
    
    def _actualizar_tabla(self):
        """Actualiza tabla con datos del ViewModel"""
        self._binding_activo = False
        
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Insertar usuarios
        for usuario in self.viewmodel.usuarios:
            self.tree.insert(
                '', 'end',
                values=(usuario.id, usuario.nombre, usuario.email),
                iid=str(usuario.id)
            )
        
        self._binding_activo = True
    
    def _actualizar_formulario(self):
        """Actualiza formulario con usuario seleccionado"""
        self._binding_activo = False
        
        usuario = self.viewmodel.usuario_seleccionado
        if usuario:
            self.entry_nombre.delete(0, 'end')
            self.entry_nombre.insert(0, usuario.nombre)
            
            self.entry_email.delete(0, 'end')
            self.entry_email.insert(0, usuario.email)
        else:
            self.entry_nombre.delete(0, 'end')
            self.entry_email.delete(0, 'end')
        
        self._binding_activo = True
    
    def _mostrar_error(self, campo, mensaje):
        """Muestra error en campo específico"""
        # Implementación según UI
        pass
```

**Regla #19 — Backend como Proveedor de ViewModels**
- backend.py inicializa y expone los ViewModels.
- Centraliza la configuración de dependencias.
- La UI obtiene los ViewModels desde el backend.

**Ejemplo:**
```python
# backend.py
from Presentation.viewmodels.usuario_viewmodel import UsuarioViewModel
from Presentation.viewmodels.producto_viewmodel import ProductoViewModel

class Backend:
    def __init__(self, config=None):
        # ... inicialización existente ...
        self._inicializar_viewmodels()
    
    def _inicializar_viewmodels(self):
        """Inicializa todos los ViewModels"""
        self.viewmodel_usuario = UsuarioViewModel(self)
        self.viewmodel_producto = ProductoViewModel(self)
    
    # Métodos para acceder a ViewModels
    def obtener_viewmodel_usuario(self) -> UsuarioViewModel:
        return self.viewmodel_usuario
    
    def obtener_viewmodel_producto(self) -> ProductoViewModel:
        return self.viewmodel_producto

# bootstrap.py
def crear_interfaz(backend):
    vm_usuarios = backend.obtener_viewmodel_usuario()
    vista = VistaUsuarios(root, vm_usuarios)
    return vista
```

**Regla #20 — Bootstrap Integrado**
- bootstrap.py obtiene ViewModels desde backend.
- Crea las vistas inyectando sus ViewModels.
- No debe contener lógica de negocio.

**Ejemplo:**
```python
# bootstrap.py
def ejecutar_aplicacion():
    # Inicializar backend
    backend = Backend(config)
    
    # Crear ventana principal
    root = tk.Tk()
    root.title("Mi Aplicación")
    
    # Notebook para múltiples vistas
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    # Crear vistas con sus ViewModels
    vm_usuarios = backend.obtener_viewmodel_usuario()
    vista_usuarios = VistaUsuarios(notebook, vm_usuarios)
    notebook.add(vista_usuarios, text="👥 Usuarios")
    
    vm_productos = backend.obtener_viewmodel_producto()
    vista_productos = VistaProductos(notebook, vm_productos)
    notebook.add(vista_productos, text="📦 Productos")
    
    root.mainloop()
```

### Beneficios del MVVM

- **Separación clara**: UI solo muestra datos, ViewModel maneja lógica.
- **Testabilidad**: ViewModels se prueban sin interfaz gráfica.
- **Reutilización**: Mismo ViewModel con diferentes frameworks (Tkinter, Qt, Web).
- **Estado explícito**: Todo el estado de UI centralizado en ViewModel.
- **Validación de UI**: Separada de reglas de negocio del dominio.
- **Mantenibilidad**: Cambios en UI no afectan lógica y viceversa.

### Checklist MVVM

- [ ] El ViewModel hereda de ViewModelBase.
- [ ] Las propiedades notifican cambios mediante `notificar_cambio()`.
- [ ] Los comandos encapsulan acciones complejas.
- [ ] Los modelos de UI son dataclasses simples.
- [ ] La Vista no contiene lógica de negocio (solo binding y widgets).
- [ ] El ViewModel no importa nada de `User_Interface`.
- [ ] El binding es bidireccional cuando corresponde.
- [ ] Los errores de UI se manejan en el ViewModel.
- [ ] backend.py expone los ViewModels a la UI.

---

## Estructura Completa — Nivel 5

```
proyecto/
│
├── backend.py                 # Adaptador, expone servicios y ViewModels
├── bootstrap.py               # Orquestador principal
├── config.py                  # Configuraciones globales
├── requirements.txt           # Dependencias
├── .env                       # Variables de entorno
├── .gitignore                 # Archivos ignorados
│
├── Application/               # Casos de uso
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
├── Domain/                     # Reglas de negocio
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
├── Infrastructure/             # Implementaciones técnicas
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
├── Presentation/               # NUEVA CAPA MVVM
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
├── User_Interface/              # Vistas (solo widgets y binding)
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
├── Tests/                        # Pruebas
│   ├── __init__.py
│   ├── test_domain/
│   ├── test_application/
│   ├── test_infrastructure/
│   ├── test_presentation/        # Pruebas de ViewModels
│   │   ├── __init__.py
│   │   ├── test_usuario_viewmodel.py
│   │   └── test_validators.py
│   └── conftest.py
│
├── Scripts/                       # Utilidades
│   ├── __init__.py
│   ├── migraciones.py
│   ├── seed_data.py
│   └── backup.py
│
└── Docs/                          # Documentación
    ├── README.md
    ├── arquitectura.md
    ├── guia_estilo.md
    └── api_referencia.md
```

---

## Conclusión

El patrón AETHERYON proporciona una arquitectura progresiva y escalable:

- **Nivel 1**: Script único - Para prototipos rápidos.
- **Nivel 2**: BF - Separación básica lógica/presentación.
- **Nivel 3**: AUDI - Arquitectura limpia por capas.
- **Nivel 4**: AUDDITS - Añade testing, scripts y documentación.
- **Nivel 5**: AUDDITS+MVVM - Añade capa de presentación con ViewModels.

Cada nivel añade complejidad controlada y mejores prácticas, permitiendo evolucionar el proyecto según crecen los requisitos, manteniendo siempre la separación de responsabilidades y la testabilidad.

**Principios clave recordar:**
- Domain nunca depende de nadie.
- Application coordina, no implementa.
- Infrastructure implementa contratos.
- Presentation maneja estado de UI.
- UI solo muestra y captura eventos.
- Todo se inyecta, nada se crea internamente.
- Las pruebas son ciudadanos de primera clase.
```

Este documento completo incluye:

1. **Ejemplos de código funcionales** para cada nivel y regla
2. **Explicaciones claras** de cada concepto
3. **Código comentado** mostrando tanto lo correcto como lo incorrecto
4. **Estructuras de carpetas** detalladas
5. **Flujos de trabajo** completos
6. **Buenas prácticas** de testing, logging y documentación
7. **Patrón MVVM** completamente implementado con ejemplos

Todo el código está listo para ser copiado y utilizado como base para proyectos reales.