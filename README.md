# gestion_el_cielo_api — Backend Finca El Cielo

Backend REST para la plataforma de gestión de **Finca El Cielo**, productora de café y banano en Colombia. Reemplaza el Excel manual que se usaba para egresos, control semanal, ventas y nómina.

## Stack

| Capa | Tecnología |
|------|-----------|
| Framework | Django 5.1.6 + DRF 3.15.2 |
| Auth | JWT (SimpleJWT) — 30 min access, 7 días refresh |
| Base de datos | PostgreSQL 15 |
| IA / OCR | Azure OpenAI + Azure Document Intelligence |
| Server | Gunicorn (gthread, 4×4) |
| Container | Docker Compose |

## Estructura

```
src/
├── cieloapi/          # Módulo principal Django (settings, urls, wsgi)
└── apps/
    ├── usuarios/      # Auth JWT, User custom
    ├── finanzas/      # Cuenta, Proveedor, Egreso, Ingreso, Transaccion, Observacion
    ├── produccion/    # Lote, VentaCafe, VentaCafeTostado, VentaBanano, Floracion, MezclaAbono
    ├── nomina/        # Empleado, ControlSemanal, PrestamoEmpleado, AbonoPrestamo
    └── integraciones/ # Heredado del template Corona — pendiente de limpieza
```

## Variables de entorno

```env
SECRET_KEY=
DEBUG=False
ALLOWED_HOSTS=localhost
DB_NAME=cielo_db
DB_USER=cielo_user
DB_PASS=
DB_HOST=postgres
DB_PORT=5432
CORS_ALLOWED_ORIGINS=http://localhost:3009
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=
AZURE_DOCUMENT_INTELLIGENCE_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
```

## Arranque

```bash
cp .env.example .env          # completar variables
docker compose up -d --build
docker compose exec cielo_api_web python src/manage.py migrate
docker compose exec cielo_api_web python src/manage.py createsuperuser
```

## Servicios Docker

| Contenedor | Descripción | Puerto |
|------------|-------------|--------|
| `cielo_api_web` | API (Gunicorn) | 8001:8000 |
| `cielo_api_postgres` | PostgreSQL 15 | interno |

## Endpoints planeados

| Módulo | Base URL |
|--------|----------|
| Auth | `/api/v1/users/` |
| Finanzas | `/api/v1/finanzas/` |
| Producción | `/api/v1/produccion/` |
| Nómina | `/api/v1/nomina/` |

> Los serializers y viewsets de finanzas, produccion y nomina están pendientes de implementar.

## Módulos prioritarios

1. **Egresos** — registro de todos los gastos con cuenta, categoría y proveedor
2. **Control Semanal** — planilla semanal de labores del personal
