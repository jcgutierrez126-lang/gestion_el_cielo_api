# Documentación API - Corona Integration

## Base URL
```
https://coronapi.lambdaanalytics.co
```

---

# AUTENTICACIÓN

Todos los endpoints (excepto login y registro) requieren token JWT en el header:
```
Authorization: Bearer <access_token>
```

---

## 1. Login

Autentica un usuario y retorna tokens JWT.

**Endpoint:** `POST /api/users/login/`

**Request Body:**
```json
{
    "username": "usuario@corona.com.co",
    "password": "tu_contraseña"
}
```

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| username | string | Sí | Email del usuario |
| password | string | Sí | Contraseña |

**Response (200):**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user_id": 1,
    "email": "usuario@corona.com.co",
    "first_name": "Juan",
    "last_name": "Pérez",
    "image": "https://coronapi.lambdaanalytics.co/media/users/foto.jpg",
    "full_name": "Juan Pérez",
    "role_id": 1,
    "role_name": "Administrador",
    "is_admin": true
}
```

**Tokens:**
- `access`: Token de acceso (expira en 5 minutos)
- `refresh`: Token de refresco (expira en 24 horas)

**Errores:**
- `400`: Credenciales inválidas

---

## 2. Refrescar Token

Obtiene un nuevo access token usando el refresh token.

**Endpoint:** `POST /api/users/token/refresh/`

**Request Body:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200):**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

## 3. Registro de Usuario

Registra un nuevo usuario (queda pendiente de aprobación por admin).

**Endpoint:** `POST /api/users/register/`

**Request Body:**
```json
{
    "email": "nuevo@corona.com.co",
    "password": "contraseña_segura",
    "first_name": "Juan",
    "last_name": "Pérez",
    "phone": "3001234567",
    "identification": "1234567890",
    "born_date": "1990-01-15"
}
```

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| email | string | Sí | Email único |
| password | string | Sí | Contraseña |
| first_name | string | Sí | Nombre |
| last_name | string | Sí | Apellido |
| phone | string | Sí | Teléfono |
| identification | string | Sí | Cédula/NIT |
| born_date | date | No | Fecha de nacimiento (YYYY-MM-DD) |

**Response (201):**
```json
{
    "detail": "Usuario registrado exitosamente. Tu cuenta está pendiente de aprobación.",
    "user_id": 5
}
```

---

## 4. Recuperar Contraseña

### 4.1 Solicitar código de recuperación

**Endpoint:** `POST /api/users/password-reset/`

**Request Body:**
```json
{
    "email": "usuario@corona.com.co"
}
```

**Response (200):**
```json
{
    "detail": "Se ha enviado el código de verificación al correo.",
    "email": "usuario@corona.com.co"
}
```

### 4.2 Verificar código

**Endpoint:** `POST /api/users/password-reset/verify/`

**Request Body:**
```json
{
    "email": "usuario@corona.com.co",
    "code": "123456"
}
```

**Response (200):**
```json
{
    "detail": "Código válido.",
    "valid": true
}
```

### 4.3 Confirmar nueva contraseña

**Endpoint:** `POST /api/users/password-reset/confirm/`

**Request Body:**
```json
{
    "email": "usuario@corona.com.co",
    "code": "123456",
    "password": "nueva_contraseña"
}
```

**Response (200):**
```json
{
    "detail": "Contraseña actualizada exitosamente."
}
```

---

# GESTIÓN DE USUARIOS

*Requiere autenticación*

## 5. Listar Usuarios

**Endpoint:** `GET /api/users/user-list/`

**Query Parameters:**
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| search | string | Buscar por nombre, email o username |
| page | integer | Número de página |
| page_size | integer | Items por página (max: 100) |

**Response:**
```json
{
    "count": 25,
    "next": "http://api/users/user-list/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "email": "admin@corona.com.co",
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Sistema",
            "full_name": "Admin Sistema",
            "phone": "3001234567",
            "identification": "123456789",
            "status": true,
            "is_admin": true,
            "role": {
                "id": 1,
                "name": "Administrador"
            }
        }
    ]
}
```

---

## 6. Detalle de Usuario

**Endpoint:** `GET /api/users/{id}/user-detail/`

---

## 7. Crear Usuario

**Endpoint:** `POST /api/users/user-create/`

**Request Body:**
```json
{
    "email": "nuevo@corona.com.co",
    "password": "contraseña",
    "first_name": "Juan",
    "last_name": "Pérez",
    "phone": "3001234567",
    "identification": "1234567890",
    "status": true,
    "is_admin": false,
    "role": 2
}
```

---

## 8. Actualizar Usuario

**Endpoint:** `PUT /api/users/{id}/user-update/`

---

## 9. Actualizar Parcialmente Usuario

**Endpoint:** `PATCH /api/users/{id}/user-patch/`

**Request Body:**
```json
{
    "status": true
}
```

---

## 10. Eliminar Usuario

**Endpoint:** `DELETE /api/users/{id}/user-delete/`

**Response:** `204 No Content`

---

## 11. Listar Grupos/Roles

**Endpoint:** `GET /api/users/group-list/`

**Response:**
```json
{
    "count": 3,
    "results": [
        {"id": 1, "name": "Administrador"},
        {"id": 2, "name": "Usuario"},
        {"id": 3, "name": "Consulta"}
    ]
}
```

---

# MÓDULO DE PEDIDOS

*Requiere autenticación*

## 12. Correos Autorizados

### 12.1 Listar Correos Autorizados

**Endpoint:** `GET /api/pedidos/correos/`

**Response:**
```json
{
    "total": 2,
    "correos": [
        {
            "id": 1,
            "email": "compras@corona.com.co",
            "nombre": "Buzón de Compras",
            "es_buzon_principal": true,
            "activo": true,
            "created_at": "2025-01-21T10:00:00Z",
            "updated_at": "2025-01-21T10:00:00Z"
        }
    ]
}
```

### 12.2 Crear Correo Autorizado

**Endpoint:** `POST /api/pedidos/correos/`

**Request Body:**
```json
{
    "email": "nuevo@corona.com.co",
    "nombre": "Descripción del buzón",
    "es_buzon_principal": false,
    "activo": true
}
```

### 12.3 Obtener Correo Autorizado

**Endpoint:** `GET /api/pedidos/correos/{id}/`

### 12.4 Actualizar Correo Autorizado

**Endpoint:** `PUT /api/pedidos/correos/{id}/`

### 12.5 Actualizar Parcialmente Correo

**Endpoint:** `PATCH /api/pedidos/correos/{id}/`

### 12.6 Eliminar Correo Autorizado

**Endpoint:** `DELETE /api/pedidos/correos/{id}/`

**Response:** `204 No Content`

---

## 13. Búsqueda y Consolidación de Pedidos

### 13.1 Buscar y Consolidar Pedido

Busca un pedido en Supplos y Graph, consolida la información y la guarda en BD.

**Endpoint:** `POST /api/pedidos/buscar/`

**Request Body:**
```json
{
    "numero_pedido": 4501833743,
    "empresas": ["corona", "alion"],
    "buscar_correos": true
}
```

| Campo | Tipo | Requerido | Default | Descripción |
|-------|------|-----------|---------|-------------|
| numero_pedido | integer | Sí | - | Número del pedido a buscar |
| empresas | array | No | ["corona", "alion"] | Empresas donde buscar en Supplos |
| buscar_correos | boolean | No | true | Si debe buscar en correos (Graph) |

**Response (200):**
```json
{
    "numero_pedido": 4501833743,
    "supplos": {
        "status": "OK",
        "data": [...],
        "source": "supplos"
    },
    "graph": {
        "status": "OK",
        "data": [...],
        "total": 3,
        "buzones_consultados": ["compras@corona.com.co"],
        "source": "graph"
    },
    "consolidado": true,
    "pedidos_guardados": [
        {
            "id": 15,
            "documento_compras": "4501833743",
            "posicion": "40",
            "estado": "Vigente",
            "es_nuevo": true
        }
    ],
    "errores": [],
    "pedidos": [...]
}
```

---

## 14. Gestión de Pedidos

### 14.1 Listar Pedidos

**Endpoint:** `GET /api/pedidos/`

**Query Parameters:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| search | string | Búsqueda en documento, razón social, material, comprador |
| estado | string | Vigente, Entregado, Parcial, Pendiente, Cancelado, En Transito |
| fecha_desde | date | Fecha de entrega desde (YYYY-MM-DD) |
| fecha_hasta | date | Fecha de entrega hasta (YYYY-MM-DD) |
| fuente | string | supplos, graph, ambos |
| page | integer | Número de página |
| page_size | integer | Items por página (max: 100, default: 20) |

**Ejemplo:**
```
GET /api/pedidos/?search=PILOTO&estado=Vigente&page=1&page_size=10
```

**Response:**
```json
{
    "count": 50,
    "next": "https://coronapi.lambdaanalytics.co/api/pedidos/?page=2",
    "previous": null,
    "results": [
        {
            "id": 15,
            "proveedor_centro_suministrador": "1000000104",
            "razon_social": "PILOTO SAS",
            "comprador": "Brenda Rocio Pena Rojas",
            "organizacion_compras": "LC00   LOCERIA COLOMBIANA S.A.S",
            "planta": "LC PR CALDAS",
            "documento_compras": "4501833743",
            "posicion": "40",
            "material": "000000022000018331",
            "texto_breve": "VAJILLA 16P CONGO AZUL MTS",
            "cantidad_pedido": "350.000",
            "por_entregar": "350.000",
            "precio_neto": "5176.00",
            "fecha_entrega": "2025-11-08",
            "fecha_programada": "2025-11-08T00:00:00Z",
            "estado_pedido": "Vigente",
            "estado_pedido_display": "Vigente",
            "motivo": "Otro",
            "observaciones": "ENTREGA PROGRAMADA PARA EL 08/11/2025",
            "estado": "",
            "observaciones_corona": "",
            "fuente_supplos": true,
            "fuente_graph": true,
            "created_at": "2025-01-21T10:30:00Z"
        }
    ]
}
```

### 14.2 Detalle de Pedido por Número

**Endpoint:** `GET /api/pedidos/{numero_pedido}/`

Si hay múltiples posiciones, retorna un array.

### 14.3 Detalle de Pedido por ID

**Endpoint:** `GET /api/pedidos/detalle/{id}/`

### 14.4 Actualizar Pedido

**Endpoint:** `PATCH /api/pedidos/{id}/actualizar/`

**Request Body:**
```json
{
    "estado_pedido": "Entregado",
    "motivo": "Entregado completo",
    "observaciones_corona": "Verificado por almacén"
}
```

### 14.5 Resincronizar Pedido

Vuelve a consultar Supplos y Graph para actualizar.

**Endpoint:** `POST /api/pedidos/{numero_pedido}/resincronizar/`

**Request Body (opcional):**
```json
{
    "buscar_correos": true
}
```

---

## 15. Trazabilidad

**Endpoint:** `GET /api/pedidos/{numero_pedido}/trazabilidad/`

**Response:**
```json
{
    "documento_compras": "4501833743",
    "total_registros": 3,
    "trazabilidad": [
        {
            "id": 3,
            "fecha_registro": "2025-01-21T15:00:00Z",
            "fuente": "MANUAL",
            "fuente_display": "Manual",
            "estado_anterior": "Vigente",
            "estado_nuevo": "Entregado",
            "observaciones": "Actualizado manualmente",
            "observaciones_proveedor": null,
            "email_id": null,
            "email_subject": null,
            "email_from": null,
            "email_date": null
        }
    ]
}
```

---

## 16. Correos Procesados

**Endpoint:** `GET /api/pedidos/correos-procesados/`

**Query Parameters:**
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| buzon | string | Filtrar por buzón |
| fecha_desde | datetime | Fecha de procesamiento desde |

---

## 17. Estadísticas

**Endpoint:** `GET /api/pedidos/estadisticas/`

**Response:**
```json
{
    "total_pedidos": 150,
    "por_estado": [
        {"estado_pedido": "Vigente", "cantidad": 80},
        {"estado_pedido": "Entregado", "cantidad": 50},
        {"estado_pedido": "Parcial", "cantidad": 10},
        {"estado_pedido": "Pendiente", "cantidad": 5},
        {"estado_pedido": "Cancelado", "cantidad": 3},
        {"estado_pedido": "En Transito", "cantidad": 2}
    ],
    "por_fuente": {
        "solo_supplos": 45,
        "solo_graph": 5,
        "ambas_fuentes": 100
    }
}
```

---

## 18. Logs de Consultas

**Endpoint:** `GET /api/pedidos/logs/`

**Query Parameters:**
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| tipo | string | SUPPLOS, GRAPH, CONSOLIDACION |
| exitosa | boolean | true/false |

---

# CÓDIGOS DE ERROR

| Código | Descripción |
|--------|-------------|
| 400 | Bad Request - Parámetros inválidos |
| 401 | Unauthorized - Token no válido o expirado |
| 403 | Forbidden - Sin permisos |
| 404 | Not Found - Recurso no encontrado |
| 500 | Internal Server Error |

**Ejemplo de error:**
```json
{
    "detail": "Token no válido o expirado"
}
```

---

# FLUJO DE USO RECOMENDADO

## Para integraciones (Bot de Teams, Apps externas):

### 1. Autenticarse
```bash
curl -X POST https://coronapi.lambdaanalytics.co/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "bot@corona.com.co", "password": "password123"}'
```

### 2. Usar el access token en todas las peticiones
```bash
curl -X GET https://coronapi.lambdaanalytics.co/api/pedidos/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### 3. Refrescar token cuando expire (cada 5 min)
```bash
curl -X POST https://coronapi.lambdaanalytics.co/api/users/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."}'
```

## Configuración inicial de pedidos:

1. **Agregar buzones autorizados** para búsqueda en correos
2. **Buscar y consolidar pedido** para obtener datos de Supplos + Graph
3. **Consultar pedidos guardados** de la BD local
4. **Ver trazabilidad** para historial de cambios

---

# RESUMEN DE ENDPOINTS

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | /api/users/login/ | Login | No |
| POST | /api/users/register/ | Registro | No |
| POST | /api/users/token/refresh/ | Refrescar token | No |
| POST | /api/users/password-reset/ | Solicitar código reset | No |
| POST | /api/users/password-reset/verify/ | Verificar código | No |
| POST | /api/users/password-reset/confirm/ | Confirmar reset | No |
| GET | /api/users/user-list/ | Listar usuarios | Sí |
| POST | /api/users/user-create/ | Crear usuario | Sí |
| GET | /api/users/{id}/user-detail/ | Detalle usuario | Sí |
| PUT | /api/users/{id}/user-update/ | Actualizar usuario | Sí |
| PATCH | /api/users/{id}/user-patch/ | Patch usuario | Sí |
| DELETE | /api/users/{id}/user-delete/ | Eliminar usuario | Sí |
| GET | /api/users/group-list/ | Listar grupos | Sí |
| GET | /api/pedidos/ | Listar pedidos | Sí |
| POST | /api/pedidos/buscar/ | Buscar y consolidar | Sí |
| GET | /api/pedidos/{numero}/ | Detalle por número | Sí |
| GET | /api/pedidos/detalle/{id}/ | Detalle por ID | Sí |
| PATCH | /api/pedidos/{id}/actualizar/ | Actualizar pedido | Sí |
| POST | /api/pedidos/{numero}/resincronizar/ | Resincronizar | Sí |
| GET | /api/pedidos/{numero}/trazabilidad/ | Trazabilidad | Sí |
| GET | /api/pedidos/correos/ | Listar correos auth | Sí |
| POST | /api/pedidos/correos/ | Crear correo auth | Sí |
| GET | /api/pedidos/correos/{id}/ | Detalle correo | Sí |
| PUT | /api/pedidos/correos/{id}/ | Actualizar correo | Sí |
| PATCH | /api/pedidos/correos/{id}/ | Patch correo | Sí |
| DELETE | /api/pedidos/correos/{id}/ | Eliminar correo | Sí |
| GET | /api/pedidos/correos-procesados/ | Correos procesados | Sí |
| GET | /api/pedidos/estadisticas/ | Estadísticas | Sí |
| GET | /api/pedidos/logs/ | Logs consultas | Sí |
