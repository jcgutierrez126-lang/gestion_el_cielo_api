# Corona Integration API

Sistema de consolidacion de pedidos de compra para Corona. Integra multiples fuentes de datos — ERP (Supplos), correos corporativos (Microsoft Graph), procesamiento documental (Azure Document Intelligence) e inteligencia artificial (Azure OpenAI) — en una API REST unificada.

## Arquitectura

**Service-Oriented Layered Architecture (SOA)** desplegada en servidor propio via Docker.

```
┌──────────────────────────────────────────────────────────────────┐
│  Clientes: Bot de Teams (Node.js / Python) · Integraciones       │
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTPS + X-API-Key
┌────────────────────────────▼─────────────────────────────────────┐
│  Servidor (Docker Compose)                                        │
│  ┌─────────────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Gunicorn Web        │  │ Celery Worker │  │ Celery Beat  │    │
│  │ 4 workers × 4 thds  │  │ Tareas async  │  │ Scheduler    │    │
│  │ Django REST + JWT    │  │ Consolidacion │  │              │    │
│  └─────────┬───────────┘  └──────┬───────┘  └──────────────┘    │
│            │  Service Layer       │                               │
│  ┌─────────▼──────────────────────▼──────────────────────────┐   │
│  │ ConsolidationService · GraphSearchService · SuplosService │   │
│  │ AIExtractionService · AzureDocumentService                │   │
│  └───────────────────────────────────────────────────────────┘   │
└──────┬─────────────┬─────────────┬───────────────────────────────┘
       │             │             │
┌──────▼──────┐ ┌────▼────┐ ┌─────▼──────────────────────────────┐
│ SQL Server  │ │  Redis  │ │ Servicios Externos                 │
│ (externo)   │ │  7      │ │ · Microsoft Graph (correos)        │
│             │ │ Alpine  │ │ · Supplos API (ERP pedidos)        │
│ 6 modelos   │ │ Docker  │ │ · Azure OpenAI GPT (IA)            │
│             │ │ Broker  │ │ · Azure Doc Intelligence (OCR)     │
└─────────────┘ └─────────┘ │ · Azure AD / Entra ID (OAuth)     │
                             └────────────────────────────────────┘
```

## Stack Tecnologico

| Capa | Tecnologia |
|------|------------|
| Framework | Django 5.1.6 + Django REST Framework 3.15.2 |
| Auth | API Key (`X-API-Key`) + JWT (SimpleJWT) — 30 min access, 7 dias refresh |
| Base de datos | SQL Server (mssql-django + ODBC Driver 18) |
| Cache / Broker | Redis 7 (contenedor Docker) |
| Async | Celery 5.4 (worker + beat) |
| IA | Azure OpenAI GPT (structuring + orchestrator) |
| OCR | Azure Document Intelligence (prebuilt-layout) |
| Correos | Microsoft Graph API + MSAL |
| ERP | Supplos REST API |
| Server | Gunicorn (gthread, 4×4 = 16 concurrent) |
| Container | Docker + Docker Compose |
| CI/CD | GitHub Actions → Docker Hub → SSH deploy |

---

## Autenticacion

La API soporta dos metodos:

| Metodo | Header | Uso |
|--------|--------|-----|
| **API Key** | `X-API-Key: <key>` | Bots, integraciones automatizadas |
| **JWT** | `Authorization: Bearer <token>` | Login de usuarios (solo `/users/`) |

Los endpoints de pedidos (`/api/v1/pedidos/`) requieren exclusivamente **API Key**.

### Generar una API Key

```bash
docker exec corona_integration_web python manage.py crear_api_key "nombre-cliente"
```

Se puede tener multiples keys (una por cliente/bot).

---

## Endpoints API

Base URL: `/api/v1/`

### Pedidos

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| POST | `/pedidos/consultar/` | Endpoint unificado — consultar/crear/actualizar pedido. Soporta `async=true` |
| POST | `/pedidos/busqueda-ia/` | Busqueda inteligente — consulta en lenguaje natural con IA |
| POST | `/pedidos/buscar/` | Buscar y consolidar pedido desde Supplos + Graph |
| GET | `/pedidos/` | Listar pedidos (paginado, filtros) |
| GET | `/pedidos/{numero}/` | Detalle por numero de pedido |
| GET | `/pedidos/detalle/{id}/` | Detalle por ID interno |
| PATCH | `/pedidos/{id}/actualizar/` | Actualizar estado/observaciones |
| POST | `/pedidos/{numero}/resincronizar/` | Forzar resincronizacion |
| GET | `/pedidos/{numero}/trazabilidad/` | Historial de cambios |
| GET | `/pedidos/tarea/{task_id}/` | Estado de tarea asincrona (Celery) |
| GET | `/pedidos/estadisticas/` | Estadisticas por estado y fuente |
| GET | `/pedidos/logs/` | Logs de consultas |

### Correos

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET/POST | `/pedidos/correos/` | CRUD buzones autorizados |
| GET/PUT/DELETE | `/pedidos/correos/{id}/` | Detalle buzon |
| GET | `/pedidos/correos-procesados/` | Correos ya procesados |

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

## Busqueda Inteligente con IA

Convierte lenguaje natural a filtros de base de datos usando Azure OpenAI:

```bash
POST /api/v1/pedidos/busqueda-ia/
X-API-Key: <key>

{
    "consulta": "pedidos retrasados del proveedor PILOTO en los ultimos 3 meses"
}
```

Respuesta:
```json
{
    "consulta": "pedidos retrasados del proveedor PILOTO en los ultimos 3 meses",
    "descripcion_ia": "Pedidos de PILOTO con fecha de entrega vencida en los ultimos 90 dias",
    "filtros_aplicados": {
        "razon_social__icontains": "PILOTO",
        "fecha_entrega__gte": "2025-11-10",
        "estado_pedido__in": ["Vigente", "Parcial", "Pendiente"]
    },
    "total": 12,
    "resultados": [...]
}
```

---

## Endpoint Unificado (async)

Para consultas pesadas se ejecutan en background via Celery:

```bash
POST /api/v1/pedidos/consultar/
X-API-Key: <key>

{
    "numero_pedido": 4501833743,
    "async": true
}
```

Respuesta `202 Accepted`:
```json
{
    "task_id": "abc123-def456",
    "status": "PENDING",
    "message": "Tarea encolada"
}
```

Consultar estado:
```bash
GET /api/v1/pedidos/tarea/abc123-def456/
X-API-Key: <key>
```

---

## Variables de Entorno

```bash
# Django
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=coronapi.lambdaanalytics.co,localhost

# SQL Server
SQL_NAME=coronapi_db
SQL_USER=sa
SQL_PASS=password
SQL_HOST=ip-servidor-sql
SQL_PORT=1433

# Microsoft Graph (correos)
CORREO_CLIENT_ID=your-app-id
CORREO_TENANT_ID=your-tenant-id
CORREO_SECRET_KEY=your-client-secret
EMAIL_HOST_USER=correo@corona.com.co

# Supplos API (ERP)
SUPLOS_API_URL=https://apicoronaqas.suplos.com
SUPLOS_API_EMAIL=your-email
SUPLOS_API_PASSWORD=your-password

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_STRUCTURING_DEPLOYMENT=gpt-4.1-structuring-suplos
AZURE_OPENAI_STRUCTURING_API_VERSION=2025-01-01-preview
AZURE_OPENAI_ORCHESTRATOR_DEPLOYMENT=gpt-5.2-chat-orchestrator-suplos
AZURE_OPENAI_ORCHESTRATOR_API_VERSION=2025-04-01-preview

# Azure Document Intelligence (OCR PDFs/imagenes)
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-key

# Celery (Redis contenedor Docker)
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# CORS
CORS_ALLOWED_ORIGINS=https://coronapi.lambdaanalytics.co,http://localhost:3000
```

---

## Deployment

### Produccion (server-216)

El CI/CD usa GitHub Actions con dos jobs:

1. **test** — corre `pytest tests/` contra una DB PostgreSQL temporal (en el runner)
2. **build-and-deploy** — construye imagen Docker, la sube a Docker Hub y despliega via SSH

**GitHub Secrets requeridos:**

| Secret | Descripcion |
|--------|-------------|
| `DOCKER_USERNAME` | Usuario de Docker Hub |
| `DOCKER_PASSWORD` | Password de Docker Hub |
| `SERVER_HOST` | IP del servidor (216.158.229.228) |
| `SERVER_USER` | Usuario SSH (`deploy`) |
| `SERVER_SSH_KEY` | Llave privada SSH |
| `SERVER_PORT` | Puerto SSH (2244) |

### Docker Compose

```bash
# Primera vez
git clone https://github.com/LambdaAnalyticsSAS/corona_integration.git
cd corona_integration
cp .env.example .env   # completar variables
docker compose up -d --build
docker exec corona_integration_web python manage.py migrate
docker exec corona_integration_web python manage.py crear_api_key "bot-teams"

# Actualizacion
git pull
docker compose up -d --build
docker exec corona_integration_web python manage.py migrate
```

Servicios:
| Contenedor | Descripcion | Puerto |
|------------|-------------|--------|
| `corona_integration_web` | API (Gunicorn) | 8001:8000 |
| `corona_integration_worker` | Celery worker (tareas async) | — |
| `corona_integration_beat` | Celery scheduler | — |
| `corona_integration_redis` | Broker + backend resultados | interno |

### Migraciones (primera vez con SQL Server)

```bash
# Local — generar migraciones (no necesita conexion a BD)
set PYTHONPATH=src
python manage.py makemigrations usuarios
python manage.py makemigrations integraciones
git add src/apps/*/migrations/
git commit -m "feat: initial migrations for SQL Server"
git push

# Servidor — aplicar
docker exec corona_integration_web python manage.py migrate
```

---

## Estructura del Proyecto

```
corona_integration/
├── src/
│   ├── apps/
│   │   ├── integraciones/
│   │   │   ├── api/
│   │   │   │   ├── views.py             # API views
│   │   │   │   ├── serializers.py       # DRF serializers
│   │   │   │   └── urls.py              # URL routing
│   │   │   ├── services/
│   │   │   │   ├── consolidation_service.py   # Orquestador principal
│   │   │   │   ├── supplos_service.py         # Integracion Supplos ERP
│   │   │   │   ├── graph_search_service.py    # Busqueda correos Graph
│   │   │   │   ├── ai_extraction_service.py   # Azure OpenAI (extraccion + IA)
│   │   │   │   └── azure_document_service.py  # Azure Document Intelligence
│   │   │   ├── authentication.py        # APIKeyAuthentication + IsAPIKeyAuthenticated
│   │   │   ├── models.py                # 6 modelos
│   │   │   ├── tasks.py                 # Tareas Celery
│   │   │   └── management/commands/
│   │   │       └── crear_api_key.py     # Comando para generar API Keys
│   │   └── usuarios/                    # Auth + CRUD usuarios
│   └── coronapi/
│       ├── settings.py                  # Configuracion Django
│       ├── celery.py                    # Config Celery
│       ├── urls.py                      # URL root
│       └── correo.py                    # Auth MSAL (Graph)
├── tests/
│   ├── test_auth.py                     # Tests de autenticacion y API Key
│   ├── test_pedidos.py                  # Tests de endpoints de pedidos
│   └── test_usuarios.py                 # Tests de login y refresh token
├── docs/
│   └── azure-deploy-diagram.svg
├── docker-compose.yml                   # Web + Worker + Beat + Redis
├── Dockerfile                           # Python 3.13-slim + ODBC Driver 18
├── requirements.txt
├── pytest.ini
└── .github/workflows/deploy.yml         # CI/CD: test → build → deploy SSH
```

---

## Modelos de Datos

| Modelo | Descripcion |
|--------|-------------|
| **Pedido** | Pedido consolidado (Supplos + Graph). Unique: documento_compras + posicion |
| **TrazabilidadPedido** | Historial de cambios por pedido (audit trail) |
| **LogConsulta** | Log de consultas a APIs externas |
| **CorreoAutorizado** | Buzones habilitados para busqueda en Graph |
| **CorreoProcesado** | Correos ya procesados (evita duplicados) |
| **APIKey** | Keys de acceso para bots e integraciones (hash SHA-256) |

---

## Procesamiento de Correos

```
Correo tiene adjuntos PDF/imagen + Azure DI configurado?
  SI  → Graph descarga adjuntos → Azure DI extrae texto → Azure OpenAI estructura JSON
  NO  → Body HTML del correo → Azure OpenAI estructura JSON (flujo default)
```

Fallbacks:
1. Azure DI no configurado → flujo HTML transparente
2. Azure DI falla → warning + flujo HTML
3. Sin adjuntos PDF/imagen → flujo HTML directo

---

## Escalabilidad

| Workers | Threads | Conexiones simultaneas | RAM |
|---------|---------|------------------------|-----|
| 4 | 4 | 16 | 600MB |
| 6 | 4 | 24 | 900MB |
| 8 | 4 | 32 | 1200MB |

Estrategias:
- Consultas pesadas (Supplos + Graph + IA) en **Celery** con `async=true`
- Gunicorn maneja lecturas rapidas de DB directamente
- Redis cachea resultados de tareas por 1 hora
- Busquedas de correos en **paralelo** (ThreadPoolExecutor)
- Rate limiting: 200 req/min por usuario autenticado
