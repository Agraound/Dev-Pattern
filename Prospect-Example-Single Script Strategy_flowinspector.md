# FlowInspector.py (MVP – Single Script Strategy)

## Visión

FlowInspector comienza como un único script autocontenido.

La prioridad no es la perfección arquitectónica.
La prioridad es:

* Funcionar rápido
* Generar claridad estructural real
* Validar el concepto
* Iterar

Luego, el propio FlowInspector ayudará a modularizarse.

---

# Filosofía de Construcción

Fase inicial:

✔ Un solo archivo: `flow_inspector.py`
✔ Clases internas bien delimitadas
✔ Sin sobreingeniería
✔ Sin paquetes múltiples
✔ Enfoque pragmático

Cuando el MVP esté validado:

→ Se separará en módulos usando su propio análisis estructural.

---

# Estructura Interna del Script

```
flow_inspector.py

 ├── class FlowInspector
 ├── class RepositoryLoader
 ├── class ASTParser
 ├── class FileDependencyAnalyzer
 ├── class StructureAnalyzer
 ├── class CallGraphAnalyzer
 ├── class DependencyGraphBuilder
 └── class ReportBuilder
```

Todas las clases viven en el mismo archivo.
Responsabilidades claras.
Sin acoplamiento innecesario.

---

# Flujo de Ejecución (Dentro del Script)

```
main()
  → RepositoryLoader
  → ASTParser
  → FileDependencyAnalyzer
  → StructureAnalyzer
  → CallGraphAnalyzer
  → DependencyGraphBuilder
  → ReportBuilder
```

---

# Componentes del MVP

## 1. RepositoryLoader

Responsable de:

* Leer directorio o archivo .txt generado por repo_inspector
* Extraer archivos .py

Output:

```
Dict[str, str]  # {ruta_archivo: contenido}
```

---

## 2. ASTParser

Responsable de:

* Convertir cada archivo en AST
* Manejar errores de parseo sin romper ejecución

Output:

```
Dict[str, ast.Module]
```

---

## 3. FileDependencyAnalyzer

Detecta:

* import X
* from X import Y

Output:

```
{
  archivo: [modulos_importados]
}
```

---

## 4. StructureAnalyzer

Detecta:

* Clases
* Métodos
* Funciones globales
* Herencia

Output:

```
{
  archivo: {
    "classes": {...},
    "functions": [...]
  }
}
```

---

## 5. CallGraphAnalyzer

Detecta:

* ast.Call
* Relación función → función
* Método → método

Output:

```
{
  archivo: {
    "caller": ["callee1", "callee2"]
  }
}
```

---

## 6. DependencyGraphBuilder

Construye grafo dirigido interno:

Nodos:

* Archivos
* Clases
* Funciones

Aristas:

* Importa
* Define
* Llama

Preparado para futura exportación.

---

## 7. ReportBuilder

Genera salida en consola estructurada:

Ejemplo:

```
[Archivo] conversation_aggregate.py
 ├─ importa: toon_analyzer

[Clase] ConversationAggregate
 ├─ método aplicar_mensaje()
 │    ├─ llama: _analyzer.analizar()
 │    └─ llama: datetime.now()
```

Opcional:

* JSON
* Markdown

---

# Alcance del MVP

Incluye:

✔ Detección de imports
✔ Detección de clases y métodos
✔ Detección básica de llamadas
✔ Reporte en consola

No incluye aún:

✖ Visualización gráfica
✖ Métricas complejas
✖ Detección avanzada de circularidad

---

# Estrategia de Evolución

Paso 1 → Script único funcional
Paso 2 → Validación en repos reales
Paso 3 → Medición de acoplamientos
Paso 4 → Modularización automática

En ese momento:

FlowInspector se analizará a sí mismo.

Y se dividirá con precisión quirúrgica.

---

# Principio Rector

Primero claridad.
Después elegancia.
Después optimización.

Siempre intervención mínima.
Siempre conciencia estructural.
