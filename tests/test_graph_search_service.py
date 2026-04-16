"""
Tests para apps/integraciones/services/graph_search_service.py
Cubre métodos puros y flujo principal con mocks HTTP/DB.
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock, call

from apps.integraciones.services.graph_search_service import (
    GraphSearchService,
    GraphSearchException,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def service():
    with patch("apps.integraciones.services.graph_search_service.AIExtractionService"), \
         patch("apps.integraciones.services.graph_search_service.AzureDocumentService"):
        return GraphSearchService()


# ---------------------------------------------------------------------------
# _filtrar_correo  (método puro)
# ---------------------------------------------------------------------------

class TestFiltrarCorreo:

    def test_rechaza_asunto_no_permitido(self, service):
        correo = {
            "id": "abc",
            "subject": "Newsletter semanal",
            "body": {"content": "pedido 4501833743"},
            "bodyPreview": "",
            "receivedDateTime": None,
            "hasAttachments": False,
            "from": {},
        }
        assert service._filtrar_correo(correo, "4501833743") is None

    def test_rechaza_correo_sin_numero_pedido_en_body(self, service):
        correo = {
            "id": "abc",
            "subject": "Seguimiento a pedidos pendientes",
            "body": {"content": "<p>No hay pedido aquí</p>"},
            "bodyPreview": "",
            "receivedDateTime": None,
            "hasAttachments": False,
            "from": {},
        }
        assert service._filtrar_correo(correo, "4501833743") is None

    def test_pasa_filtro_asunto_y_numero_en_body(self, service):
        correo = {
            "id": "abc123",
            "subject": "Seguimiento a pedidos pendientes",
            "body": {"content": "El pedido 4501833743 fue despachado"},
            "bodyPreview": "preview",
            "receivedDateTime": "2025-04-15T10:00:00Z",
            "hasAttachments": True,
            "from": {"emailAddress": {"address": "prv@test.com", "name": "Proveedor"}},
        }
        resultado = service._filtrar_correo(correo, "4501833743")
        assert resultado is not None
        assert resultado["email_id"] == "abc123"
        assert resultado["has_attachments"] is True
        assert resultado["from_address"] == "prv@test.com"

    def test_pasa_filtro_numero_en_html_sin_tags(self, service):
        correo = {
            "id": "xyz",
            "subject": "Estado de entrega",
            "body": {"content": "<p>Pedido <b>4501833743</b> entregado</p>"},
            "bodyPreview": "",
            "receivedDateTime": None,
            "hasAttachments": False,
            "from": {},
        }
        assert service._filtrar_correo(correo, "4501833743") is not None

    def test_parsea_fecha_iso_correctamente(self, service):
        correo = {
            "id": "d1",
            "subject": "seguimiento ordenes de compra",
            "body": {"content": "pedido 1111 ok"},
            "bodyPreview": "",
            "receivedDateTime": "2025-04-15T10:00:00Z",
            "hasAttachments": False,
            "from": {},
        }
        resultado = service._filtrar_correo(correo, "1111")
        assert resultado is not None
        assert isinstance(resultado["received_date"], datetime)

    def test_maneja_fecha_invalida(self, service):
        correo = {
            "id": "d2",
            "subject": "estado de entrega",
            "body": {"content": "pedido 2222"},
            "bodyPreview": "",
            "receivedDateTime": "no-es-fecha",
            "hasAttachments": False,
            "from": {},
        }
        resultado = service._filtrar_correo(correo, "2222")
        assert resultado is not None
        assert resultado["received_date"] == "no-es-fecha"


# ---------------------------------------------------------------------------
# _deduplicar_correos  (método puro)
# ---------------------------------------------------------------------------

class TestDeduplicarCorreos:

    def test_elimina_duplicados_por_id(self, service):
        correos = [{"id": "a", "x": 1}, {"id": "a", "x": 2}, {"id": "b", "x": 3}]
        resultado = service._deduplicar_correos(correos)
        assert len(resultado) == 2
        assert resultado[0]["id"] == "a"
        assert resultado[1]["id"] == "b"

    def test_sin_duplicados_retorna_todos(self, service):
        correos = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
        assert len(service._deduplicar_correos(correos)) == 3

    def test_lista_vacia_retorna_vacia(self, service):
        assert service._deduplicar_correos([]) == []

    def test_correo_sin_id_es_ignorado(self, service):
        correos = [{"id": None}, {"id": "a"}, {"id": None}]
        resultado = service._deduplicar_correos(correos)
        # Sin ID no se agrega al set
        assert len(resultado) == 1
        assert resultado[0]["id"] == "a"


# ---------------------------------------------------------------------------
# _construir_resultado  (método puro)
# ---------------------------------------------------------------------------

class TestConstruirResultado:

    def test_construye_campos_correctamente(self, service):
        correo_f = {
            "email_id": "e1",
            "subject": "Seguimiento",
            "from_address": "a@b.com",
            "from_name": "Proveedor",
            "received_date": datetime(2025, 4, 15),
            "has_attachments": False,
            "body_preview": "preview...",
        }
        datos = {
            "observaciones_proveedor": "Entregado",
            "observaciones_corona": None,
            "posiciones_correo": [{"posicion": "10"}],
            "extraido_con_ia": True,
            "resumen_ia": "Resumen",
        }
        resultado = service._construir_resultado(correo_f, "buzon@test.com", datos)
        assert resultado["email_id"] == "e1"
        assert resultado["buzon"] == "buzon@test.com"
        assert resultado["observaciones_proveedor"] == "Entregado"
        assert resultado["extraido_con_ia"] is True
        assert len(resultado["posiciones_correo"]) == 1

    def test_empty_extraction_estructura(self, service):
        resultado = service._empty_extraction()
        assert resultado["observaciones_proveedor"] is None
        assert resultado["extraido_con_ia"] is False
        assert resultado["posiciones_correo"] == []


# ---------------------------------------------------------------------------
# _extraer_datos_contenido  (IA mock)
# ---------------------------------------------------------------------------

class TestExtraerDatosContenido:

    def test_sin_ia_disponible_retorna_error_extraccion(self, service):
        service.ai_service = MagicMock()
        service.ai_service.is_available.return_value = False

        resultado = service._extraer_datos_contenido("<p>html</p>", "1111")
        assert resultado["observaciones_proveedor"] is None
        assert "error_extraccion" in resultado

    def test_extrae_con_ia_exitoso(self, service):
        service.ai_service = MagicMock()
        service.ai_service.is_available.return_value = True
        service.ai_service.extraer_observaciones_correo.return_value = {
            "observaciones_proveedor": "Despacho el lunes",
            "extraido_con_ia": True,
            "posiciones_correo": [],
        }

        resultado = service._extraer_datos_contenido("contenido", "4501833743")
        assert resultado["observaciones_proveedor"] == "Despacho el lunes"

    def test_maneja_excepcion_de_ia(self, service):
        service.ai_service = MagicMock()
        service.ai_service.is_available.return_value = True
        service.ai_service.extraer_observaciones_correo.side_effect = Exception("Timeout")

        resultado = service._extraer_datos_contenido("contenido", "1111")
        assert resultado["observaciones_proveedor"] is None
        assert "error_extraccion" in resultado


# ---------------------------------------------------------------------------
# _separar_procesados  (con DB)
# ---------------------------------------------------------------------------

class TestSepararProcesados:

    @pytest.mark.django_db
    def test_correo_no_procesado_va_a_ia(self, service):
        correos = [{"email_id": "nuevo-id-999", "subject": "test"}]
        resultado, para_ia = service._separar_procesados(correos, "buzon@test.com")
        assert len(resultado) == 0
        assert len(para_ia) == 1

    @pytest.mark.django_db
    def test_correo_ya_procesado_omite_ia(self, service):
        from apps.integraciones.models import CorreoProcesado
        CorreoProcesado.objects.create(
            email_id="ya-procesado-001",
            buzon="buzon@test.com",
            subject="Seguimiento"
        )

        correos = [{"email_id": "ya-procesado-001", "subject": "Seguimiento",
                    "from_address": None, "from_name": None,
                    "received_date": None, "has_attachments": False, "body_preview": ""}]
        resultado, para_ia = service._separar_procesados(correos, "buzon@test.com")
        assert len(resultado) == 1
        assert len(para_ia) == 0


# ---------------------------------------------------------------------------
# _registrar_correo_procesado  (con DB)
# ---------------------------------------------------------------------------

class TestRegistrarCorreoProcesado:

    @pytest.mark.django_db
    def test_crea_registro_nuevo(self, service):
        from apps.integraciones.models import CorreoProcesado
        service._registrar_correo_procesado("nuevo-001", "buzon@test.com", "Asunto", None)
        assert CorreoProcesado.objects.filter(email_id="nuevo-001").exists()

    @pytest.mark.django_db
    def test_no_duplica_registro_existente(self, service):
        from apps.integraciones.models import CorreoProcesado
        service._registrar_correo_procesado("dup-001", "buzon@test.com", "Asunto", None)
        service._registrar_correo_procesado("dup-001", "buzon@test.com", "Asunto", None)
        assert CorreoProcesado.objects.filter(email_id="dup-001").count() == 1


# ---------------------------------------------------------------------------
# buscar_correos_por_pedido  (mock completo)
# ---------------------------------------------------------------------------

class TestBuscarCorreosPorPedido:

    def test_retorna_error_cuando_token_falla(self, service):
        with patch("apps.integraciones.services.graph_search_service.get_access_token") as mock_token:
            mock_token.return_value = {"status": "ERROR", "message": "Sin credenciales"}
            resultado = service.buscar_correos_por_pedido("4501833743")
        assert resultado["status"] == "ERROR"

    @pytest.mark.django_db
    def test_retorna_warning_sin_buzones(self, service):
        with patch("apps.integraciones.services.graph_search_service.get_access_token") as mock_token, \
             patch.object(service, "_get_buzones_autorizados", return_value=[]):
            mock_token.return_value = {"status": "OK", "access": "token-test"}
            resultado = service.buscar_correos_por_pedido("4501833743")
        assert resultado["status"] == "WARNING"

    @pytest.mark.django_db
    def test_busqueda_exitosa_sin_correos(self, service):
        with patch("apps.integraciones.services.graph_search_service.get_access_token") as mock_token, \
             patch.object(service, "_get_buzones_autorizados", return_value=["buzon@test.com"]), \
             patch.object(service, "_buscar_en_buzon", return_value=[]):
            mock_token.return_value = {"status": "OK", "access": "token-test"}
            resultado = service.buscar_correos_por_pedido("4501833743")
        assert resultado["status"] == "OK"
        assert resultado["total"] == 0

    @pytest.mark.django_db
    def test_busqueda_con_correos_encontrados(self, service):
        correo_mock = {
            "email_id": "e1",
            "subject": "Seguimiento",
            "from": "a@b.com",
            "received_date": datetime(2025, 4, 15),
            "observaciones_proveedor": "OK",
        }
        with patch("apps.integraciones.services.graph_search_service.get_access_token") as mock_token, \
             patch.object(service, "_get_buzones_autorizados", return_value=["buzon@test.com"]), \
             patch.object(service, "_buscar_en_buzon", return_value=[correo_mock]):
            mock_token.return_value = {"status": "OK", "access": "token-test"}
            resultado = service.buscar_correos_por_pedido("4501833743")
        assert resultado["status"] == "OK"
        assert resultado["total"] == 1

    @pytest.mark.django_db
    def test_error_en_buzon_no_rompe_busqueda(self, service):
        with patch("apps.integraciones.services.graph_search_service.get_access_token") as mock_token, \
             patch.object(service, "_get_buzones_autorizados", return_value=["b1@test.com", "b2@test.com"]), \
             patch.object(service, "_buscar_en_buzon", side_effect=Exception("Error de red")):
            mock_token.return_value = {"status": "OK", "access": "token-test"}
            resultado = service.buscar_correos_por_pedido("1111")
        assert resultado["status"] == "OK"
        assert resultado["total"] == 0


# ---------------------------------------------------------------------------
# _buscar_por_keyword  (HTTP mock)
# ---------------------------------------------------------------------------

class TestBuscarPorKeyword:

    @patch("apps.integraciones.services.graph_search_service.requests.get")
    def test_retorna_correos_en_200(self, mock_get, service):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"value": [{"id": "a"}, {"id": "b"}]}
        mock_get.return_value = mock_resp

        resultado = service._buscar_por_keyword(
            "https://graph.microsoft.com/v1.0/users/buzon/messages",
            "seguimiento a pedidos pendientes",
            {"Authorization": "Bearer token"},
            "id,subject",
            50,
            "buzon@test.com"
        )
        assert len(resultado) == 2

    @patch("apps.integraciones.services.graph_search_service.requests.get")
    def test_retorna_vacio_en_error_http(self, mock_get, service):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_get.return_value = mock_resp

        resultado = service._buscar_por_keyword(
            "https://graph.microsoft.com/v1.0/users/buzon/messages",
            "keyword",
            {},
            "id",
            50,
            "buzon@test.com"
        )
        assert resultado == []

    @patch("apps.integraciones.services.graph_search_service.requests.get")
    def test_retorna_vacio_en_excepcion(self, mock_get, service):
        mock_get.side_effect = Exception("Timeout")

        resultado = service._buscar_por_keyword(
            "http://url",
            "keyword",
            {},
            "id",
            50,
            "buzon@test.com"
        )
        assert resultado == []


# ---------------------------------------------------------------------------
# obtener_adjuntos  (HTTP mock)
# ---------------------------------------------------------------------------

class TestObtenerAdjuntos:

    @patch("apps.integraciones.services.graph_search_service.get_access_token")
    @patch("apps.integraciones.services.graph_search_service.requests.get")
    def test_retorna_adjuntos_xlsx(self, mock_get, mock_token, service):
        mock_token.return_value = {"status": "OK", "access": "token"}
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"value": [
            {"id": "a1", "name": "reporte.xlsx", "contentType": "application/xlsx", "size": 1024},
            {"id": "a2", "name": "foto.jpg", "contentType": "image/jpeg", "size": 512},
        ]}
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        resultado = service.obtener_adjuntos("email-id-123", buzon="buzon@test.com")
        assert len(resultado) == 1
        assert resultado[0]["name"] == "reporte.xlsx"

    @patch("apps.integraciones.services.graph_search_service.get_access_token")
    @patch("apps.integraciones.services.graph_search_service.requests.get")
    def test_retorna_vacio_en_excepcion(self, mock_get, mock_token, service):
        mock_token.return_value = {"status": "OK", "access": "token"}
        mock_get.side_effect = Exception("Error red")

        resultado = service.obtener_adjuntos("email-id-999", buzon="buzon@test.com")
        assert resultado == []


# ---------------------------------------------------------------------------
# _extraer_datos_con_routing
# ---------------------------------------------------------------------------

class TestExtraerDatosConRouting:

    def test_sin_adjuntos_usa_html(self, service):
        correo_f = {
            "has_attachments": False,
            "body_content": "<p>contenido</p>",
            "subject": "Seguimiento",
            "email_id": "e1",
        }
        service.ai_service = MagicMock()
        service.ai_service.is_available.return_value = False

        resultado = service._extraer_datos_con_routing(correo_f, "1111", {}, "buzon@test.com")
        assert resultado["extraido_con_ia"] is False

    def test_con_adjuntos_azure_no_disponible_usa_html(self, service):
        correo_f = {
            "has_attachments": True,
            "body_content": "<p>html</p>",
            "subject": "Test",
            "email_id": "e2",
        }
        service.azure_service = MagicMock()
        service.azure_service.is_available.return_value = False
        service.ai_service = MagicMock()
        service.ai_service.is_available.return_value = False

        resultado = service._extraer_datos_con_routing(correo_f, "2222", {}, "buzon@test.com")
        assert resultado["extraido_con_ia"] is False

    def test_con_adjuntos_azure_disponible_extrae_adjuntos(self, service):
        correo_f = {
            "has_attachments": True,
            "body_content": "<p>html</p>",
            "subject": "Seguimiento",
            "email_id": "e3",
        }
        service.azure_service = MagicMock()
        service.azure_service.is_available.return_value = True
        service.ai_service = MagicMock()
        service.ai_service.is_available.return_value = True
        service.ai_service.extraer_observaciones_correo.return_value = {
            "observaciones_proveedor": "Desde adjunto",
            "extraido_con_ia": True,
            "posiciones_correo": [],
        }

        with patch.object(service, "_procesar_adjuntos_con_azure", return_value="texto del PDF"):
            resultado = service._extraer_datos_con_routing(correo_f, "3333", {}, "buzon@test.com")

        assert resultado["observaciones_proveedor"] == "Desde adjunto"


# ---------------------------------------------------------------------------
# marcar_correo_procesado  (con DB)
# ---------------------------------------------------------------------------

class TestMarcarCorreoProcesado:

    @pytest.mark.django_db
    def test_registra_correctamente(self, service):
        from apps.integraciones.models import CorreoProcesado
        service.marcar_correo_procesado(
            email_id="pub-001",
            buzon="buzon@test.com",
            subject="Pedido urgente",
            fecha_email=None,
            pedido=None,
        )
        assert CorreoProcesado.objects.filter(email_id="pub-001").exists()


# ---------------------------------------------------------------------------
# _get_buzones_autorizados y _get_buzon_principal  (con DB)
# ---------------------------------------------------------------------------

class TestHelpersBuzones:

    @pytest.mark.django_db
    def test_get_buzones_autorizados_retorna_activos(self, service, correo_autorizado):
        buzones = service._get_buzones_autorizados()
        assert "buzon@corona.com.co" in buzones

    @pytest.mark.django_db
    def test_get_buzon_principal_retorna_principal(self, service, correo_autorizado):
        buzon = service._get_buzon_principal()
        assert buzon == "buzon@corona.com.co"

    @pytest.mark.django_db
    def test_correo_ya_procesado_true(self, service):
        from apps.integraciones.models import CorreoProcesado
        CorreoProcesado.objects.create(
            email_id="ya-proc-check",
            buzon="buzon@test.com",
            subject="Test"
        )
        assert service._correo_ya_procesado("ya-proc-check") is True

    @pytest.mark.django_db
    def test_correo_ya_procesado_false(self, service):
        assert service._correo_ya_procesado("nunca-procesado") is False

    def test_get_token_exitoso(self, service):
        with patch("apps.integraciones.services.graph_search_service.get_access_token") as mock:
            mock.return_value = {"status": "OK", "access": "mi-token"}
            assert service._get_token() == "mi-token"

    def test_get_token_lanza_excepcion_en_error(self, service):
        with patch("apps.integraciones.services.graph_search_service.get_access_token") as mock:
            mock.return_value = {"status": "ERROR", "message": "Sin config"}
            with pytest.raises(GraphSearchException):
                service._get_token()
