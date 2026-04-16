# Contexto de Tests — Corona Integration API

## Resumen

Suite de tests unitarios para la API REST de integración de pedidos Corona.
Corre completamente en memoria (SQLite + LocMemCache). No requiere SQL Server,
Redis, Microsoft Graph ni ningún servicio externo para ejecutarse.

**Comando de ejecución:**
```bash
cd /opt/corona_integration
DJANGO_SETTINGS_MODULE=coronapi.settings_test \
  PYTHONPATH=src \
  pytest tests/ -v --tb=short --timeout=30
```

---

## Configuración del entorno de test

| Variable | Valor en test | Propósito |
|----------|--------------|-----------|
| `DJANGO_SETTINGS_MODULE` | `coronapi.settings_test` | Activa SQLite en memoria |
| `PYTHONPATH` | `src` | Apunta al directorio raíz de los módulos Django |

**`settings_test.py` sobreescribe:**
- `DATABASES` → SQLite `:memory:` (no necesita SQL Server)
- `CACHES` → `LocMemCache` (necesario para tests de reset de contraseña)
- `FRONTEND_URL` → `localhost:8000` (evita error en correos corporativos)

**Servicios externos mockeados en todos los tests:**
- `enviar_correo_simple` — Microsoft Graph API
- `ConsolidationService` — Suplos + Graph (en tests de búsqueda)
- `AIExtractionService` — Azure OpenAI

---

## Archivos de test

### `tests/conftest.py` — Fixtures globales

| Fixture | Descripción |
|---------|-------------|
| `limpiar_cache` | `autouse=True` — limpia caché antes/después de cada test (evita contaminación del rate limiter) |
| `usuario` | Usuario estándar activo (`testuser / testpass123`) |
| `admin_user` | Usuario con `is_admin=True` |
| `api_key` | API Key válida en texto plano |
| `client_con_key` | `APIClient` con header `X-API-KEY` configurado |
| `client_con_jwt` | `APIClient` con JWT de usuario estándar |
| `admin_client_con_jwt` | `APIClient` con JWT de admin |
| `pedido` | Pedido `4501722041` en estado Vigente |
| `correo_autorizado` | Buzón principal activo |

---

### `tests/test_auth.py` — Autenticación y API Keys (7 tests)

Cubre el sistema de doble autenticación: JWT para usuarios y API Key para integraciones.

| Test | Qué verifica |
|------|-------------|
| `test_login_sin_credenciales` | POST vacío → 400 |
| `test_login_credenciales_invalidas` | Username/password incorrectos → 401 |
| `test_pedidos_sin_key_retorna_401` | Sin API Key no accede a `/pedidos/` |
| `test_pedidos_key_invalida_retorna_401_o_403` | Key inválida es rechazada |
| `test_jwt_solo_no_accede_a_integraciones` | JWT sin API Key no accede a integraciones |
| `test_api_key_valida_accede_a_integraciones` | Key válida accede → 200 |
| `test_key_inactiva_retorna_401_o_403` | Key desactivada es rechazada |

---

### `tests/test_usuarios.py` — CRUD de usuarios y tokens (13 tests)

| Clase | Tests | Qué cubre |
|-------|-------|-----------|
| `TestLogin` | 3 | Login exitoso, password incorrecto, usuario inexistente |
| `TestRefreshToken` | 2 | Renovar token JWT válido e inválido |
| `TestUserCRUD` | 6 | Listar, detalle, 404, patch (admin), delete (admin) |

**Notas importantes:**
- `UserLoginView` devuelve **400** para campos faltantes y **401** para credenciales incorrectas
- Patch y delete requieren `IsAdminUser` → usan `admin_client_con_jwt`
- Endpoint: `POST /api/v1/users/token/refresh/` con nombre `usuarios:token-refresh`

---

### `tests/test_password_reset.py` — Flujo de reset de contraseña (12 tests)

Flujo completo en 3 pasos: solicitar código → verificar → confirmar.

| Clase | Tests | Qué cubre |
|-------|-------|-----------|
| `TestPasswordResetRequest` | 4 | Sin email, email no registrado (200 sin revelar existencia), envío exitoso, fallo de envío (500) |
| `TestVerifyResetCode` | 4 | Sin datos, código inválido, código válido, código expirado |
| `TestPasswordResetConfirm` | 5 | Sin datos, código incorrecto, expirado, cambio exitoso, código no reutilizable, login con nueva contraseña, email inexistente (404) |

**Dependencia crítica:** Requiere `CACHES = LocMemCache`. Con `DummyCache` todos los tests de código fallan con 400 (el cache nunca guarda nada).

---

### `tests/test_registro.py` — Registro público de usuarios (8 tests)

| Test | Qué verifica |
|------|-------------|
| `test_registro_exitoso_retorna_201` | Registro completo → 201 |
| `test_usuario_creado_queda_inactivo` | `status=False` hasta aprobación admin |
| `test_usuario_no_es_admin` | `is_admin=False` por defecto |
| `test_campo_requerido_faltante_retorna_400` | Itera los 6 campos obligatorios |
| `test_email_duplicado_retorna_400` | Email ya registrado → 400 |
| `test_identificacion_duplicada_retorna_400` | Identificación duplicada → 400 |
| `test_usuario_inactivo_no_puede_loguearse` | Usuario pendiente de aprobación → 401/400 |
| `test_username_generado_desde_email` | `username` = parte local del email |

**Mock requerido:** `enviar_correo_simple` (el registro envía correo de bienvenida y notificación al admin).

---

### `tests/test_pedidos.py` — Pedidos: listado, detalle, actualización (14 tests)

| Clase | Tests | Qué cubre |
|-------|-------|-----------|
| `TestPedidoList` | 5 | Listar, filtro estado, filtro fuente supplos, búsqueda general |
| `TestPedidoDetail` | 4 | Por número, 404, por ID interno, 404 por ID |
| `TestPedidoUpdate` | 3 | Actualizar observaciones, cambio de estado genera trazabilidad, 404 |
| `TestTrazabilidad` | 2 | Historial existente, 404 |
| `TestResincronizar` | 2 | Número no numérico → 400, resincronización exitosa (mock) |
| `TestBuscarPedido` | 2 | Búsqueda válida (mock), sin número → 400 |
| `TestEstadisticas` | 1 | Estructura de respuesta: `total_pedidos`, `por_estado`, `por_fuente` |
| `TestLogs` | 1 | Listado de logs → 200 |

---

### `tests/test_pedidos_extra.py` — Pedido unificado, correos procesados, búsqueda IA (14 tests)

| Clase | Tests | Qué cubre |
|-------|-------|-----------|
| `TestPedidoUnificado` | 6 | Sin número (400), consultar existente, actualizar estado + trazabilidad, búsqueda cuando no existe (mock ConsolidationService), sin auth (401) |
| `TestCorreosProcesados` | 4 | Listar, lista vacía, filtro por buzón, sin auth |
| `TestBusquedaIA` | 6 | Sin consulta (400), consulta larga (400), error de IA (503), búsqueda exitosa, filtros inseguros ignorados (whitelist), sin auth |

**Mock requerido para IA:** `apps.integraciones.services.ai_extraction_service.AIExtractionService`
(se importa localmente dentro de la función, no a nivel de módulo).

---

### `tests/test_correos.py` — Correos autorizados CRUD (10 tests)

| Clase | Tests | Qué cubre |
|-------|-------|-----------|
| `TestCorreoAutorizadoList` | 4 | Listar, crear, email inválido (400), sin datos (400) |
| `TestBuzonPrincipal` | 1 | Solo puede haber un buzón principal activo |
| `TestCorreoAutorizadoDetail` | 6 | GET, 404, PUT, PATCH, DELETE, DELETE 404 |

---

## Resumen de cobertura

| Módulo | Cobertura |
|--------|-----------|
| Autenticación JWT + API Key | ✅ Completa |
| Login / Refresh Token | ✅ Completa |
| Reset de contraseña (3 pasos) | ✅ Completa |
| Registro de usuarios | ✅ Completa |
| CRUD de usuarios | ✅ Completa |
| Pedidos (list, detail, update, trazabilidad) | ✅ Completa |
| Pedido unificado (`/consultar/`) | ✅ Completa |
| Correos autorizados | ✅ Completa |
| Correos procesados | ✅ Completa |
| Búsqueda IA | ✅ Completa |
| Estadísticas y logs | ✅ Completa |
| Integración real con Graph API | ❌ Solo en staging (requiere credenciales) |
| Integración real con Suplos API | ❌ Solo en staging (requiere credenciales) |
| Integración real con Azure OpenAI | ❌ Solo en staging (requiere credenciales) |

**Total: 88 tests — tiempo de ejecución ~50s**

---

## Paso recomendado para el workflow de ORDO

```yaml
- name: Tests unitarios
  run: |
    cd /opt/corona_integration
    pip install -r requirements.txt -q
    pip install pytest-timeout -q
    DJANGO_SETTINGS_MODULE=coronapi.settings_test \
      PYTHONPATH=src \
      pytest tests/ -v --tb=short --timeout=30
  timeout: 180
```

El flag `--timeout=30` es obligatorio para evitar que tests con llamadas a servicios externos
sin mockear cuelguen el pipeline indefinidamente.
