Aquí está simplificado como una serie de órdenes y condiciones en texto plano:

---

## AETHERYON – Open Core Architecture

**1. Estructura del proyecto**

- Código público va en GitHub
- Configuración privada NO entra al repositorio
- Incluir `.env.example` con nombres genéricos

**2. Reglas de seguridad**

- SI es variable sensible (API key, DB key, secret) → NO declarar en `render.yaml`
- OBLIGATORIO configurar solo desde dashboard de Render

**3. Sistema de modos**

- SI `MODE=demo` → funcionalidad limitada, IA desactivada
- SI `MODE=production` → sistema completo, validar que todas las keys existan

**4. Control en código**

- AL iniciar app → validar que si `MODE=production` todas las variables requeridas estén presentes
- SI falta alguna variable en producción → lanzar error, no iniciar servicio
- SI `FEATURE_MULTIAGENT != true` → bloquear funcionalidades multiagente
- SI no existe `API_KEY` → retornar mensaje de demo, no ejecutar llamada real

**5. Configuración avanzada**

- OPCIONAL: usar `CORE_CONFIG` como JSON cifrado en base64
- SI se usa `CORE_CONFIG` → desencriptar con `CONFIG_SECRET` antes de cargar
- SI no hay `CORE_CONFIG` o `CONFIG_SECRET` → caer a modo demo automáticamente

**6. Modelo de negocio**

- Repositorio público → atrae usuarios, muestra valor
- Configuración privada + despliegue → es el producto pagado
- SI alguien obtiene el 100% del valor solo clonando el repo → arquitectura mal diseñada

**7. Escalabilidad**

- MANTENER mismo patrón en Convbot, Emailer Agent y Portal
- CADA cliente puede tener su propia configuración cifrada
- USAR Config Manager centralizado como módulo compartido