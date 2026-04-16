# Cielo API — Backend Finca La Holanda

Backend de la plataforma contable y administrativa de **Finca La Holanda**, una finca productora de café y banano ubicada en Colombia. Reemplaza el control manual en hojas de cálculo por una API REST centralizada que gestiona finanzas, producción agrícola, nómina, proveedores y más.

## Contexto del negocio

**Finca La Holanda** opera con dos líneas de producción principales:

- **Café** — venta de café pergamino a cooperativa/agencia, y café tostado propio (bolsas de 250 g, 500 g y 2,5 kg). Incluye seguimiento de floraciones, lotes, árboles, mezcla de abonos y control de enfermedades (broca, roya).
- **Banano** — venta de banano con registro de ingresos por cosecha.

Las operaciones generan múltiples flujos financieros que antes se gestionaban en Excel:

| Área | Descripción |
|---|---|
| Estado de Resultados | Ingresos, costos, utilidad bruta y neta |
| Balance General | Activos corrientes y no corrientes |
| Cuentas y Bancos | Agencia, Bancolombia, efectivo, dividendos |
| Préstamos | Seguimiento de préstamos a empleados y socios |
| Egresos | Clasificados por categoría (fertilizantes, EPM, nómina, transporte, etc.) |
| Nómina | Planilla semanal, seguridad social, vales |
| Producción Café | Floraciones, lotes, árboles, tostión, costos de tueste |
| Producción Banano | Registro de ventas y cosechas |
| Proveedores | Directorio y control de deudas |
| Empleados | Datos, préstamos, planilla frontal/trasera |
| Inventario | Insumos (herbicidas, fertilizantes, herramientas) |
| Ganado | Terneros y activos pecuarios |

## Arquitectura

**Service-Oriented Layered Architecture (SOA)** desplegada en servidor propio via Docker.

```
┌──────────────────────────────────────────────────────────────────┐
│  Clientes: Aplicativo Web · Bots · Integraciones externas        │
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTPS + X-API-Key / JWT
┌────────────────────────────▼─────────────────────────────────────┐
│  Servidor (Docker Compose)                                        │
│  ┌─────────────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Gunicorn Web        │  │ Celery Worker │  │ Celery Beat  │    │
│  │ 4 workers × 4 thds  │  │ Tareas async  │  │ Scheduler    │    │
│  │ Django REST + JWT    │  │               │  │              │    │
│  └─────────────────────┘  └───────────────┘  └──────────────┘   │
└──────┬──────────────┬──────────────────────────────────────────┘
       │              │
┌──────▼──────┐  ┌────▼────────────┐
│ PostgreSQL  │  │  Redis 7        │
│ 15          │  │  Broker/cache   │
└─────────────┘  └─────────────────┘
```

## Stack Tecnologico

| Capa | Tecnologia |
|------|------------|
| Framework | Django 5.1.6 + Django REST Framework 3.15.2 |
| Auth | API Key (`X-API-Key`) + JWT (SimpleJWT) — 30 min access, 7 dias refresh |
| Base de datos | PostgreSQL 15 |
| Cache / Broker | Redis 7 (contenedor Docker) |
| Async | Celery 5.4 (worker + beat) |
| IA | Azure OpenAI GPT (structuring + orchestrator) |
| OCR | Azure Document Intelligence (prebuilt-layout) |
| Correos | Microsoft Graph API + MSAL |
| Server | Gunicorn (gthread, 4×4 = 16 concurrent) |
| Container | Docker + Docker Compose |
| CI/CD | Ordo CI/CD → SSH deploy |

---

## Modulos del Sistema

### Financiero
- Estado de Resultados (ingresos, costos, utilidad)
- Balance General (activos corrientes y no corrientes)
- Cuentas bancarias y efectivo (Agencia, Bancolombia, Dividendos)
- Préstamos a empleados y socios con trazabilidad de pagos
- Registro de egresos por categoría con histórico anual

### Café
- Venta de café pergamino (cooperativa / agencia)
- Café tostado: costos de tueste, trilla, empaque y precio de venta por presentación (250 g, 500 g, 2,5 kg)
- Floraciones: registro y seguimiento por lote
- Lotes y árboles: inventario de la plantación
- Mezcla de abonos y plan de fertilización
- Control de enfermedades: broca, roya

### Banano
- Registro de ventas y cosechas por periodo

### Nómina y RRHH
- Empleados: datos básicos y laborales
- Planilla semanal (frontal y trasera)
- Seguridad social
- Vales y anticipos
- Préstamos a empleados

### Operaciones
- Egresos clasificados: acueducto, EPM, fertilizantes, herbicidas, transporte, mantenimientos, viáticos, siembra, construcciones, animales, herramientas, impuestos, etc.
- Control semanal de gastos
- Planeación semanal
- Inventario de insumos

### Proveedores y Terceros
- Directorio de proveedores
- Deudas y pagos pendientes

### Activos
- Ganado (terneros)
- Propiedades, beneficiadero, equipos, moto
- Gastos diferidos

---

## Autenticacion

| Metodo | Header | Uso |
|--------|--------|-----|
| **API Key** | `X-API-Key: <key>` | Bots, integraciones automatizadas |
| **JWT** | `Authorization: Bearer <token>` | Login de usuarios del aplicativo |

### Generar una API Key

```bash
docker exec cielo_api_web python manage.py crear_api_key "nombre-cliente"
```

---

## Endpoints API

Base URL: `/api/v1/`

> Los endpoints de dominio se agregarán a medida que se implementen los modelos.

### Usuarios

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| POST | `/users/login/` | Login (retorna JWT access + refresh) |
| POST | `/users/register/` | Registro |
| POST | `/users/token/refresh/` | Refrescar access token |
| GET | `/users/user-list/` | Listar usuarios |
| POST | `/users/user-create/` | Crear usuario (admin) |
| GET/PUT/PATCH/DELETE | `/users/{id}/user-*` | CRUD usuario |

---

## Variables de Entorno

```bash
# Django
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=cieloapi.lambdaanalytics.co,localhost

# PostgreSQL
DB_NAME=cielo_db
DB_USER=cielo_user
DB_PASS=tu-password
DB_HOST=postgres       # nombre del servicio en Docker Compose
DB_PORT=5432

# Microsoft Graph (correos)
CORREO_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
CORREO_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
CORREO_SECRET_KEY=tu-client-secret
EMAIL_HOST_USER=correo@fincaelcielo.com

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://tu-recurso.openai.azure.com/
AZURE_OPENAI_API_KEY=tu-key
AZURE_OPENAI_STRUCTURING_DEPLOYMENT=gpt-4.1-structuring
AZURE_OPENAI_STRUCTURING_API_VERSION=2025-01-01-preview
AZURE_OPENAI_ORCHESTRATOR_DEPLOYMENT=gpt-5.2-chat-orchestrator
AZURE_OPENAI_ORCHESTRATOR_API_VERSION=2025-04-01-preview

# Azure Document Intelligence (OCR)
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://tu-recurso.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=tu-key

# Celery + Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# CORS
CORS_ALLOWED_ORIGINS=https://cieloapi.lambdaanalytics.co,http://localhost:3000
```

---

## Deployment

### Docker Compose

```bash
# Primera vez
git clone https://github.com/jcgutierrez126-lang/gestion_el_cielo_api.git
cd gestion_el_cielo_api
cp .env.example .env   # completar variables
docker compose up -d --build
docker exec cielo_api_web python manage.py migrate
docker exec cielo_api_web python manage.py crear_api_key "cliente-principal"

# Actualizacion
git pull
docker compose up -d --build
docker exec cielo_api_web python manage.py migrate
```

### Servicios Docker

| Contenedor | Descripcion | Puerto |
|------------|-------------|--------|
| `cielo_api_web` | API (Gunicorn) | 8001:8000 |
| `cielo_api_worker` | Celery worker (tareas async) | — |
| `cielo_api_beat` | Celery scheduler | — |
| `cielo_api_redis` | Broker + backend resultados | interno |
| `cielo_api_postgres` | Base de datos PostgreSQL 15 | interno |

### Migraciones

```bash
# Generar (local)
set PYTHONPATH=src
python manage.py makemigrations usuarios
python manage.py makemigrations integraciones
git add src/apps/*/migrations/
git push

# Aplicar (servidor)
docker exec cielo_api_web python manage.py migrate
```

---

## Estructura del Proyecto

```
gestion_el_cielo_api/
├── src/
│   ├── apps/
│   │   ├── integraciones/        # Motor principal de consolidacion
│   │   │   ├── api/              # Views, serializers, URLs
│   │   │   ├── services/         # Logica de negocio (Supplos, Graph, IA, OCR)
│   │   │   ├── models.py         # Modelos de datos
│   │   │   └── tasks.py          # Tareas Celery
│   │   └── usuarios/             # Auth + CRUD usuarios
│   └── cieloapi/
│       ├── settings.py           # Configuracion Django
│       ├── celery.py             # Config Celery
│       ├── urls.py               # URL root
│       └── correo.py             # Auth MSAL (Graph)
├── tests/                        # Suite de tests (pytest)
├── docs/                         # Documentacion y fuentes de datos
├── docker-compose.yml            # Web + Worker + Beat + Redis + Postgres
├── Dockerfile                    # Python 3.13-slim + psycopg2
├── requirements.txt
└── .ordo/
    ├── ci.yml                    # CI: tests automatizados
    └── cd.yml                    # CD: build y deploy SSH
```

---

## Escalabilidad

| Workers | Threads | Conexiones simultaneas | RAM aprox. |
|---------|---------|------------------------|------------|
| 4 | 4 | 16 | 600 MB |
| 6 | 4 | 24 | 900 MB |
| 8 | 4 | 32 | 1200 MB |

- Tareas pesadas en **Celery** con `async=true`
- Gunicorn atiende lecturas rapidas de BD directamente
- Redis cachea resultados de tareas por 1 hora
- Rate limiting: 200 req/min por usuario autenticado
