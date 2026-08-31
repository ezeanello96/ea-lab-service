# Sistema de Gestión — Servicio Técnico de PCs
## Documento de especificación para implementación con Claude Code

---

## Contexto del proyecto

Sistema web para gestionar un emprendimiento de servicio técnico de PCs. Permite administrar clientes, equipos, órdenes de trabajo (OT), conectar con Google Calendar y generar reportes e informes.

---

## Stack tecnológico

- **Frontend**: Next.js 14 (App Router) + Tailwind CSS
- **Backend**: Next.js API Routes
- **Base de datos**: PostgreSQL
- **ORM**: Prisma
- **Autenticación**: NextAuth.js (credentials + Google OAuth)
- **PDF**: `@react-pdf/renderer` o `puppeteer`
- **Email**: Nodemailer o Resend
- **Google Calendar**: Google APIs (`googleapis`)
- **Gráficos (reportes)**: Recharts
- **Hosting sugerido**: Vercel (frontend) + Supabase o Railway (PostgreSQL)

---

## Estructura del proyecto

```
/
├── app/
│   ├── (auth)/
│   │   └── login/
│   ├── (dashboard)/
│   │   ├── layout.tsx         # Sidebar + header
│   │   ├── page.tsx           # Dashboard principal
│   │   ├── clientes/
│   │   ├── equipos/
│   │   ├── ordenes/
│   │   ├── usuarios/
│   │   └── reportes/
│   └── api/
│       ├── auth/
│       ├── clientes/
│       ├── equipos/
│       ├── ordenes/
│       ├── usuarios/
│       ├── google-calendar/
│       └── reportes/
├── components/
│   ├── ui/                    # Componentes base (botones, inputs, modals)
│   ├── clientes/
│   ├── equipos/
│   ├── ordenes/
│   └── reportes/
├── lib/
│   ├── prisma.ts
│   ├── google-calendar.ts
│   └── pdf-generator.ts
├── prisma/
│   └── schema.prisma
└── .env.local
```

---

## Modelo de base de datos (Prisma Schema)

```prisma
// prisma/schema.prisma

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model Usuario {
  id           String   @id @default(cuid())
  nombre       String
  email        String   @unique
  password     String
  rol          Rol      @default(TECNICO)
  activo       Boolean  @default(true)
  creadoEn     DateTime @default(now())
  
  ordenesAsignadas OrdenTrabajo[] @relation("TecnicoAsignado")
  ordenesCreadas   OrdenTrabajo[] @relation("UsuarioCreador")
}

enum Rol {
  ADMIN
  TECNICO
}

model Cliente {
  id        String   @id @default(cuid())
  nombre    String
  apellido  String
  email     String?
  telefono  String
  direccion String?
  notas     String?
  activo    Boolean  @default(true)
  creadoEn  DateTime @default(now())
  
  equipos  Equipo[]
  ordenes  OrdenTrabajo[]
}

model Equipo {
  id          String   @id @default(cuid())
  clienteId   String
  tipo        TipoEquipo
  marca       String
  modelo      String
  nroSerie    String?
  descripcion String?
  creadoEn    DateTime @default(now())
  
  cliente Cliente @relation(fields: [clienteId], references: [id])
  ordenes OrdenTrabajo[]
}

enum TipoEquipo {
  PC_ESCRITORIO
  NOTEBOOK
  ALL_IN_ONE
  SERVIDOR
  OTRO
}

model OrdenTrabajo {
  id                String        @id @default(cuid())
  numero            Int           @unique @default(autoincrement())
  clienteId         String
  equipoId          String
  tecnicoId         String?
  creadoPorId       String
  
  estado            EstadoOT      @default(INGRESADO)
  prioridad         Prioridad     @default(NORMAL)
  
  descripcionFalla  String
  diagnostico       String?
  trabajoRealizado  String?
  
  presupuesto       Float?
  costoFinal        Float?
  pagado            Boolean       @default(false)
  
  fechaIngreso      DateTime      @default(now())
  fechaEstimada     DateTime?
  fechaEntrega      DateTime?
  
  googleCalendarId  String?       // ID del evento en Google Calendar
  
  accesorios        String?       // Lista de accesorios entregados con el equipo
  observaciones     String?
  
  creadoEn          DateTime      @default(now())
  actualizadoEn     DateTime      @updatedAt
  
  cliente     Cliente   @relation(fields: [clienteId], references: [id])
  equipo      Equipo    @relation(fields: [equipoId], references: [id])
  tecnico     Usuario?  @relation("TecnicoAsignado", fields: [tecnicoId], references: [id])
  creadoPor   Usuario   @relation("UsuarioCreador", fields: [creadoPorId], references: [id])
  historial   HistorialOT[]
}

enum EstadoOT {
  INGRESADO
  EN_DIAGNOSTICO
  PRESUPUESTADO
  APROBADO
  EN_REPARACION
  LISTO
  ENTREGADO
  CANCELADO
}

enum Prioridad {
  BAJA
  NORMAL
  ALTA
  URGENTE
}

model HistorialOT {
  id           String   @id @default(cuid())
  ordenId      String
  estadoAntes  EstadoOT?
  estadoDespues EstadoOT
  nota         String?
  creadoEn     DateTime @default(now())
  
  orden OrdenTrabajo @relation(fields: [ordenId], references: [id])
}
```

---

## Fases de implementación

### Fase 1: Base del sistema

**Objetivo**: Tener el sistema funcionando con login, usuarios, clientes y equipos.

#### Tareas:

1. **Setup inicial**
   - Inicializar proyecto Next.js 14 con App Router
   - Configurar Tailwind CSS
   - Configurar Prisma con PostgreSQL
   - Configurar NextAuth.js con Credentials Provider
   - Crear seed de usuario admin inicial

2. **Layout del dashboard**
   - Sidebar con navegación principal
   - Header con nombre de usuario y logout
   - Protección de rutas (middleware)

3. **ABM de Usuarios** (`/usuarios`)
   - Listado con filtro por rol/estado
   - Formulario de creación/edición (nombre, email, contraseña, rol)
   - Activar/desactivar usuario
   - Solo accesible para ADMIN

4. **ABM de Clientes** (`/clientes`)
   - Listado con búsqueda por nombre/teléfono/email
   - Formulario de creación/edición
   - Vista de detalle con equipos y órdenes del cliente
   - Soft delete (campo `activo`)

5. **ABM de Equipos** (`/equipos`)
   - Los equipos pertenecen a un cliente
   - Formulario vinculado al cliente (selector de cliente)
   - Listado global y por cliente
   - Tipos de equipo con enum

---

### Fase 2: Órdenes de trabajo

**Objetivo**: Crear, gestionar y generar PDFs de las órdenes de trabajo.

#### Tareas:

1. **ABM de Órdenes de Trabajo** (`/ordenes`)
   - Listado con filtros por estado, fecha, técnico, cliente
   - Búsqueda por número de OT o nombre de cliente
   - Código de colores por estado y prioridad

2. **Formulario de nueva OT**
   - Selección de cliente (con opción de crear nuevo cliente inline)
   - Selección de equipo del cliente (con opción de crear nuevo equipo inline)
   - Campos: descripción de falla, accesorios, presupuesto estimado, fecha estimada, técnico asignado, prioridad, observaciones

3. **Vista de detalle de OT**
   - Toda la información de la orden
   - Cambio de estado con botones de acción (el flujo de estados va en orden)
   - Historial de cambios de estado con fechas
   - Campos editables: diagnóstico, trabajo realizado, costo final, pagado

4. **Generación de PDF**
   - Botón "Generar recibo de recepción" disponible desde el ingreso de la OT
   - El PDF incluye:
     - Logo/nombre del negocio
     - Número de OT y fecha
     - Datos del cliente
     - Datos del equipo (tipo, marca, modelo, N° serie)
     - Accesorios entregados
     - Descripción de la falla reportada
     - Presupuesto estimado (si existe)
     - Firma/observaciones del cliente
   - Descargar como PDF y/o enviar por email al cliente

5. **Historial de estados**
   - Cada cambio de estado queda registrado en `HistorialOT`
   - Se muestra como timeline en la vista de detalle

---

### Fase 3: Integración con Google Calendar

**Objetivo**: Crear y gestionar eventos de Google Calendar directamente desde las OTs.

#### Tareas:

1. **Configurar Google OAuth**
   - Crear proyecto en Google Cloud Console
   - Habilitar Google Calendar API
   - Configurar credenciales OAuth 2.0
   - Agregar scope de Calendar a NextAuth
   - Guardar `access_token` y `refresh_token` del usuario admin

2. **Funcionalidad de eventos**
   - Botón "Crear evento en Calendar" en la vista de OT
   - Modal para configurar: título del evento, fecha/hora, duración, descripción, recordatorio
   - Al crear el evento, guardar el `googleCalendarId` en la OT
   - Botón "Ver en Calendar" si ya tiene evento vinculado
   - Botón "Actualizar evento" para sincronizar cambios
   - Al marcar OT como ENTREGADO, opción de eliminar el evento del calendario

3. **Vista de calendario** (opcional, Fase 3+)
   - Vista mensual/semanal dentro del sistema mostrando las OTs con fecha estimada
   - Puede ser simple (lista agrupada por fecha) o visual con una librería como `react-big-calendar`

---

### Fase 4: Reportes e informes

**Objetivo**: Dashboard con KPIs y reportes de gestión.

#### Secciones:

1. **Dashboard principal** (`/`)
   - Cantidad de OTs por estado (tarjetas con número)
   - OTs con entrega próxima (próximos 7 días)
   - OTs sin técnico asignado
   - Últimas OTs ingresadas

2. **Reporte de OTs** (`/reportes/ordenes`)
   - Filtros: rango de fechas, estado, técnico
   - Tabla exportable a CSV/Excel
   - Gráfico de barras: OTs por mes
   - Gráfico de torta: distribución por estado

3. **Reporte de tiempos** (`/reportes/tiempos`)
   - Tiempo promedio de resolución por OT (fecha ingreso → fecha entrega)
   - Tiempo promedio por técnico
   - OTs que superaron la fecha estimada

4. **Reporte de presupuestos y facturación** (`/reportes/financiero`)
   - Total presupuestado vs cobrado por período
   - OTs con cobro pendiente (LISTO o ENTREGADO y no pagadas)
   - Promedio de ticket por OT

---

## Variables de entorno (.env.local)

```env
# Base de datos
DATABASE_URL="postgresql://usuario:password@localhost:5432/servicio_tecnico"

# NextAuth
NEXTAUTH_URL="http://localhost:3000"
NEXTAUTH_SECRET="tu_secret_aleatorio_aqui"

# Google OAuth (para Calendar)
GOOGLE_CLIENT_ID="tu_client_id"
GOOGLE_CLIENT_SECRET="tu_client_secret"

# Email (opcional, para enviar PDFs)
EMAIL_SERVER_HOST="smtp.gmail.com"
EMAIL_SERVER_PORT=587
EMAIL_SERVER_USER="tu_email@gmail.com"
EMAIL_SERVER_PASSWORD="tu_app_password"
EMAIL_FROM="tu_email@gmail.com"

# Datos del negocio (para el PDF)
BUSINESS_NAME="Tu Nombre o Razón Social"
BUSINESS_PHONE="+54 11 0000-0000"
BUSINESS_EMAIL="contacto@tunegocio.com"
BUSINESS_ADDRESS="Tu dirección"
```

---

## Notas de implementación para Claude Code

### Orden de implementación sugerido:
1. Setup del proyecto + Prisma + NextAuth básico
2. Layout del dashboard + middleware de protección de rutas
3. ABM de Usuarios
4. ABM de Clientes
5. ABM de Equipos
6. ABM de Órdenes de Trabajo (listado + formulario)
7. Vista de detalle de OT + cambio de estados
8. Generación de PDF
9. Integración Google Calendar
10. Dashboard y reportes

### Convenciones de código:
- Componentes en PascalCase
- Server Actions para mutaciones (no fetch desde cliente cuando sea posible)
- Validación con Zod en formularios y API routes
- Toast/notificaciones para feedback de acciones
- Skeleton loaders para estados de carga
- Tabla de OTs debe ser paginada (25 por página)

### Flujo de estados de OT:
```
INGRESADO → EN_DIAGNOSTICO → PRESUPUESTADO → APROBADO → EN_REPARACION → LISTO → ENTREGADO
                                                                              ↓
                                                                          CANCELADO (desde cualquier estado)
```

### El PDF de recepción se genera al momento del ingreso o en cualquier momento posterior. Debe ser descargable y también enviable por email si el cliente tiene email registrado.

