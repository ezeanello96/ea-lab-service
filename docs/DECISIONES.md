# Decisiones técnicas — Fase 0

Registro de las decisiones de diseño tomadas durante el scaffolding inicial del proyecto.

---

## 1. Stack tecnológico

**Decisión**: Python 3.12 + Django 5.x + PostgreSQL + Redis + Celery

**Razón**: Stack probado y maduro para sistemas CRUD con procesamiento en background.
Django provee ORM, admin, auth, migraciones y gestión de sesiones out-of-the-box,
reduciendo el tiempo de desarrollo inicial.

**Alternativas descartadas**: FastAPI (requeriría construir todo el andamiaje admin/auth manualmente),
Flask (demasiado minimal para el alcance del proyecto).

---

## 2. Interfaz sin SPA

**Decisión**: Django Templates + HTMX (sin React/Vue/Next.js)

**Razón**: El sistema es de uso interno con un solo técnico/operador. No justifica la
complejidad de una SPA + API separada. HTMX permite agregar interactividad progresiva
sin abandonar el paradigma server-side rendering de Django.

**Beneficios**: Menos configuración, sin build step de frontend, menor superficie de ataque,
templates renderizados en servidor facilitan el SEO aunque no sea un requisito.

---

## 3. Base de datos: PostgreSQL

**Decisión**: PostgreSQL 16 como única base de datos.

**Razón**: Soporte robusto de JSON fields, índices parciales, transacciones ACID completas.
Para los tests se usa SQLite en memoria para mayor velocidad (ver `config/settings/test.py`).

---

## 4. Gestión de tareas asíncronas: Celery + Redis

**Decisión**: Celery con Redis como broker y result backend.

**Razón**: Necesario para notificaciones por Telegram, resúmenes diarios programados (Celery Beat)
y cualquier tarea que no deba ejecutarse sincrónicamente en el request/response cycle.

---

## 5. Modelo de usuario: UserProfile con OneToOne

**Decisión**: Extender el User de Django con un modelo `UserProfile` mediante OneToOneField,
en lugar de un CustomUser.

**Razón**: Permite mantener compatibilidad con el admin de Django y todas las apps
que dependen de `AUTH_USER_MODEL`. Agregar campos extra mediante perfil es más
simple en esta etapa sin perder flexibilidad futura.

**Nota**: Si en el futuro se necesita cambiar el campo de login (p.ej. usar email),
se puede migrar a un CustomUser reemplazando AUTH_USER_MODEL.

---

## 6. Variables de entorno: python-decouple

**Decisión**: `python-decouple` para leer `.env` y entorno del sistema.

**Razón**: Más explícito que `os.getenv`, soporta tipos, valores default y archivos `.env`
nativamente, sin acoplarse al ecosistema Docker/12-factor específico.

---

## 7. Archivos estáticos: Whitenoise

**Decisión**: Whitenoise para servir estáticos en producción directamente desde Gunicorn.

**Razón**: Elimina la necesidad de configurar Nginx solo para estáticos en un primer deploy.
Cuando el tráfico lo requiera, se puede poner Nginx delante sin cambiar código.

---

## 8. CSS propio sin frameworks externos

**Decisión**: CSS puro con variables custom, sin Bootstrap, Tailwind, ni CDNs.

**Razón**: Control total sobre el diseño, sin dependencias externas en runtime,
funciona offline, sin riesgo de breaking changes de versiones de terceros.
El CSS es deliberadamente simple para mantener facilidad de modificación.

---

## 9. HTMX desde static/vendor/

**Decisión**: El script de HTMX se sirve desde `static/vendor/htmx.min.js`.

**Razón**: No depender de CDNs externos garantiza que el sistema funcione en redes
sin acceso a internet. El archivo se incluirá en la imagen Docker o se puede
descargar manualmente ejecutando:
```
curl -Lo static/vendor/htmx.min.js https://unpkg.com/htmx.org@2/dist/htmx.min.js
```

---

## 10. Estructura de directorios de settings

**Decisión**: `config/settings/{base,local,test}.py`

**Razón**: Separa claramente las configuraciones por entorno. `base.py` contiene
todo lo común. `local.py` y `test.py` solo sobreescriben lo necesario.
Evita el antipatrón de un único `settings.py` con bloques `if DEBUG`.

---

## 11. Migraciones: 0001_initial por app

**Decisión**: Incluir la migración inicial de cada app en el repositorio.

**Razón**: Permite hacer `migrate` desde cero sin necesidad de ejecutar
`makemigrations` en el primer despliegue. Facilita onboarding.
