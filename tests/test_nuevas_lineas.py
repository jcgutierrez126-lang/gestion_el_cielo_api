"""
Tests para cubrir líneas nuevas de código específicas reportadas por SonarQube:
- graph_search_service: _buscar_en_buzon, _fase1_busqueda_keywords, _fase3_extraccion_ia
- usuarios/models.py: has_rol_perm (user_perms rename)
- usuarios/api/views.py: generate_verification_code (secrets.choice)
"""
import pytest
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# generate_verification_code  (usuarios/api/views.py)
# ---------------------------------------------------------------------------

class TestGenerateVerificationCode:

    def test_retorna_string_de_6_digitos(self):
        from apps.usuarios.api.views import generate_verification_code
        code = generate_verification_code()
        assert len(code) == 6
        assert code.isdigit()

    def test_longitud_personalizada(self):
        from apps.usuarios.api.views import generate_verification_code
        assert len(generate_verification_code(length=4)) == 4
        assert len(generate_verification_code(length=8)) == 8

    def test_cada_llamada_genera_codigo_distinto(self):
        from apps.usuarios.api.views import generate_verification_code
        codigos = {generate_verification_code() for _ in range(20)}
        # Con 20 llamadas la probabilidad de que todos sean iguales es despreciable
        assert len(codigos) > 1


# ---------------------------------------------------------------------------
# has_rol_perm  (usuarios/models.py)
# ---------------------------------------------------------------------------

class TestHasRolPerm:

    @pytest.mark.django_db
    def test_admin_siempre_tiene_permiso(self):
        from apps.usuarios.models import User
        user = User.objects.create_user(
            username="admin_perm",
            email="admin_perm@test.com",
            first_name="Admin",
            last_name="Test",
            password="pass123",
        )
        user.is_admin = True
        user.save()
        assert user.has_rol_perm(["cualquier_permiso"]) is True

    @pytest.mark.django_db
    def test_usuario_con_rol_y_permiso(self):
        from apps.usuarios.models import User
        from django.contrib.auth.models import Group, Permission
        from django.contrib.contenttypes.models import ContentType

        grupo = Group.objects.create(name="Compras-HRP")
        ct = ContentType.objects.first()
        permiso = Permission.objects.create(
            codename="ver_pedidos",
            name="Ver Pedidos",
            content_type=ct,
        )
        grupo.permissions.add(permiso)

        user = User.objects.create_user(
            username="user_rol_perm",
            email="user_rol_perm@test.com",
            first_name="User",
            last_name="Rol",
            password="pass123",
        )
        user.role = grupo
        user.save()

        assert user.has_rol_perm(["ver_pedidos"]) is True

    @pytest.mark.django_db
    def test_usuario_sin_permiso_requerido(self):
        from apps.usuarios.models import User
        from django.contrib.auth.models import Group

        grupo = Group.objects.create(name="Lectura-HRP")
        user = User.objects.create_user(
            username="user_sin_perm",
            email="user_sin_perm@test.com",
            first_name="User",
            last_name="SinPerm",
            password="pass123",
        )
        user.role = grupo
        user.save()

        assert user.has_rol_perm(["permiso_no_asignado"]) is False


# ---------------------------------------------------------------------------
# _buscar_en_buzon  (graph_search_service.py líneas 215-243)
# ---------------------------------------------------------------------------

class TestBuscarEnBuzon:

    @pytest.fixture
    def service(self):
        with patch("apps.integraciones.services.graph_search_service.AIExtractionService"), \
             patch("apps.integraciones.services.graph_search_service.AzureDocumentService"):
            from apps.integraciones.services.graph_search_service import GraphSearchService
            return GraphSearchService()

    @pytest.mark.django_db
    def test_sin_correos_raw_retorna_vacio(self, service):
        with patch.object(service, "_fase1_busqueda_keywords", return_value=[]):
            resultado = service._buscar_en_buzon(
                "buzon@test.com", "4501833743",
                {"Authorization": "Bearer tok"}, 50
            )
        assert resultado == []

    @pytest.mark.django_db
    def test_correos_sin_match_retorna_vacio(self, service):
        correos_raw = [{
            "id": "e1",
            "subject": "Newsletter sin relacion",
            "body": {"content": "Nada relevante"},
            "bodyPreview": "",
            "receivedDateTime": None,
            "hasAttachments": False,
            "from": {},
        }]
        with patch.object(service, "_fase1_busqueda_keywords", return_value=correos_raw):
            resultado = service._buscar_en_buzon(
                "buzon@test.com", "4501833743",
                {"Authorization": "Bearer tok"}, 50
            )
        assert resultado == []

    @pytest.mark.django_db
    def test_correos_con_match_pasan_a_ia(self, service):
        correos_raw = [{
            "id": "e-match-1",
            "subject": "Seguimiento a pedidos pendientes",
            "body": {"content": "El pedido 9999 está en camino"},
            "bodyPreview": "preview",
            "receivedDateTime": "2025-04-15T10:00:00Z",
            "hasAttachments": False,
            "from": {"emailAddress": {"address": "prv@test.com", "name": "Prv"}},
        }]
        datos_ia = {
            "observaciones_proveedor": "En camino",
            "observaciones_cielo": None,
            "posiciones_correo": [],
            "extraido_con_ia": True,
            "resumen_ia": None,
        }
        with patch.object(service, "_fase1_busqueda_keywords", return_value=correos_raw), \
             patch.object(service, "_extraer_datos_con_routing", return_value=datos_ia):
            resultado = service._buscar_en_buzon(
                "buzon@test.com", "9999",
                {"Authorization": "Bearer tok"}, 50
            )
        assert len(resultado) == 1
        assert resultado[0]["observaciones_proveedor"] == "En camino"

    @pytest.mark.django_db
    def test_correo_ya_procesado_omite_ia(self, service):
        from apps.integraciones.models import CorreoProcesado
        CorreoProcesado.objects.create(
            email_id="e-ya-proc",
            buzon="buzon@test.com",
            subject="Seguimiento a pedidos pendientes"
        )

        correos_raw = [{
            "id": "e-ya-proc",
            "subject": "Seguimiento a pedidos pendientes",
            "body": {"content": "pedido 1234 info"},
            "bodyPreview": "preview",
            "receivedDateTime": "2025-04-15T10:00:00Z",
            "hasAttachments": False,
            "from": {"emailAddress": {"address": "prv@test.com", "name": "Prv"}},
        }]
        with patch.object(service, "_fase1_busqueda_keywords", return_value=correos_raw), \
             patch.object(service, "_extraer_datos_con_routing") as mock_ia:
            resultado = service._buscar_en_buzon(
                "buzon@test.com", "1234",
                {"Authorization": "Bearer tok"}, 50
            )
        # IA no debería haberse llamado
        mock_ia.assert_not_called()
        assert len(resultado) == 1


# ---------------------------------------------------------------------------
# _fase1_busqueda_keywords  (graph_search_service.py líneas 254-268)
# ---------------------------------------------------------------------------

class TestFase1BusquedaKeywords:

    @pytest.fixture
    def service(self):
        with patch("apps.integraciones.services.graph_search_service.AIExtractionService"), \
             patch("apps.integraciones.services.graph_search_service.AzureDocumentService"):
            from apps.integraciones.services.graph_search_service import GraphSearchService
            return GraphSearchService()

    def test_agrega_resultados_de_todos_los_keywords(self, service):
        correo = {"id": "c1", "subject": "test"}
        with patch.object(service, "_buscar_por_keyword", return_value=[correo]):
            resultado = service._fase1_busqueda_keywords(
                "https://graph.microsoft.com/v1.0/users/b/messages",
                {"Authorization": "Bearer tok"},
                "id,subject",
                50,
                "buzon@test.com"
            )
        # Hay 4 KEYWORDS_BUSQUEDA, cada uno retorna 1 correo
        assert len(resultado) == 4

    def test_maneja_excepcion_en_keyword(self, service):
        def mock_buscar(url, keyword, headers, select, max_r, buzon):
            if keyword == "seguimiento a pedidos pendientes":
                raise Exception("Timeout")
            return [{"id": "c1"}]

        with patch.object(service, "_buscar_por_keyword", side_effect=mock_buscar):
            resultado = service._fase1_busqueda_keywords(
                "https://url", {}, "id", 50, "buzon@test.com"
            )
        # El keyword con error se omite, los otros 3 retornan 1 correo cada uno
        assert len(resultado) == 3


# ---------------------------------------------------------------------------
# _fase3_extraccion_ia  (graph_search_service.py líneas 307-328)
# ---------------------------------------------------------------------------

class TestFase3ExtraccionIA:

    @pytest.fixture
    def service(self):
        with patch("apps.integraciones.services.graph_search_service.AIExtractionService"), \
             patch("apps.integraciones.services.graph_search_service.AzureDocumentService"):
            from apps.integraciones.services.graph_search_service import GraphSearchService
            return GraphSearchService()

    def test_lista_vacia_retorna_vacia(self, service):
        assert service._fase3_extraccion_ia([], "1111", {}, "buzon@test.com") == []

    def test_extrae_datos_con_ia_para_cada_correo(self, service):
        correos = [
            {
                "email_id": "e1",
                "subject": "Seguimiento",
                "from_address": "a@b.com",
                "from_name": "Prv",
                "received_date": None,
                "has_attachments": False,
                "body_preview": "",
                "body_content": "<p>correo</p>",
            }
        ]
        datos_ia = {
            "observaciones_proveedor": "Despacho lunes",
            "observaciones_cielo": None,
            "posiciones_correo": [],
            "extraido_con_ia": True,
            "resumen_ia": None,
        }
        with patch.object(service, "_extraer_datos_con_routing", return_value=datos_ia):
            resultado = service._fase3_extraccion_ia(
                correos, "4501833743", {}, "buzon@test.com"
            )
        assert len(resultado) == 1
        assert resultado[0]["observaciones_proveedor"] == "Despacho lunes"

    def test_maneja_excepcion_en_extraccion(self, service):
        correos = [{
            "email_id": "e2",
            "subject": "Test",
            "from_address": None,
            "from_name": None,
            "received_date": None,
            "has_attachments": False,
            "body_preview": "",
            "body_content": "",
        }]
        with patch.object(service, "_extraer_datos_con_routing", side_effect=Exception("IA down")):
            resultado = service._fase3_extraccion_ia(
                correos, "2222", {}, "buzon@test.com"
            )
        # Error manejado, devuelve resultado con empty extraction
        assert len(resultado) == 1
        assert resultado[0]["extraido_con_ia"] is False
