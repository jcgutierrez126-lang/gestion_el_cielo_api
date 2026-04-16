"""
Tests para servicios externos con mocks:
- AIExtractionService
- AzureDocumentService
- SuplosService
"""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from decimal import Decimal


# ---------------------------------------------------------------------------
# AIExtractionService
# ---------------------------------------------------------------------------

class TestAIExtractionService:

    def test_no_disponible_sin_api_key(self):
        from apps.integraciones.services.ai_extraction_service import AIExtractionService
        with patch.dict("os.environ", {}, clear=True):
            service = AIExtractionService()
            assert service.is_available() is False

    def test_retorna_vacio_cuando_no_disponible(self):
        from apps.integraciones.services.ai_extraction_service import AIExtractionService
        with patch.dict("os.environ", {}, clear=True):
            service = AIExtractionService()
            resultado = service.extraer_observaciones_correo("contenido", "4501833743")
            assert resultado["observaciones_proveedor"] is None

    def test_extrae_observaciones_con_mock_openai(self):
        from apps.integraciones.services.ai_extraction_service import AIExtractionService
        import json

        service = AIExtractionService()
        service.client = MagicMock()

        respuesta_ia = {
            "observaciones_proveedor": "Entrega programada para el lunes",
            "observaciones_corona": None,
            "estado_mencionado": None,
            "fecha_entrega_mencionada": None,
            "posiciones_correo": [],
        }
        mock_msg = MagicMock()
        mock_msg.choices[0].message.content = json.dumps(respuesta_ia)
        service.client.chat.completions.create.return_value = mock_msg

        resultado = service.extraer_observaciones_correo(
            contenido_correo="El pedido 4501833743 se entregará el lunes",
            numero_pedido="4501833743",
            asunto="Re: Pedido Corona"
        )

        assert resultado["observaciones_proveedor"] == "Entrega programada para el lunes"

    def test_maneja_json_invalido_de_openai(self):
        from apps.integraciones.services.ai_extraction_service import AIExtractionService

        service = AIExtractionService()
        service.client = MagicMock()

        mock_msg = MagicMock()
        mock_msg.choices[0].message.content = "esto no es json"
        service.client.chat.completions.create.return_value = mock_msg

        resultado = service.extraer_observaciones_correo("contenido", "1111")
        assert resultado["observaciones_proveedor"] is None

    def test_maneja_excepcion_de_openai(self):
        from apps.integraciones.services.ai_extraction_service import AIExtractionService

        service = AIExtractionService()
        service.client = MagicMock()
        service.client.chat.completions.create.side_effect = Exception("Timeout")

        resultado = service.extraer_observaciones_correo("contenido", "1111")
        assert resultado["observaciones_proveedor"] is None

    def test_limpiar_contenido_html(self):
        from apps.integraciones.services.ai_extraction_service import AIExtractionService
        service = AIExtractionService()
        html = "<p>Hola <b>mundo</b></p>"
        resultado = service._limpiar_contenido(html)
        assert "<" not in resultado
        assert "Hola" in resultado
        assert "mundo" in resultado

    def test_limpiar_contenido_trunca_largo(self):
        from apps.integraciones.services.ai_extraction_service import AIExtractionService
        service = AIExtractionService()
        texto_largo = "a" * 20000
        resultado = service._limpiar_contenido(texto_largo)
        assert len(resultado) <= 12100  # Con margen por el aviso de truncado

    def test_normalizar_respuesta_completa(self):
        from apps.integraciones.services.ai_extraction_service import AIExtractionService
        service = AIExtractionService()
        datos = {
            "observaciones_proveedor": "Entregado",
            "observaciones_corona": "Verificado",
            "estado_mencionado": "Entregado",
            "fecha_entrega_mencionada": "2025-04-20",
            "posiciones": [{"posicion": "10", "comentario": "OK"}],
        }
        resultado = service._normalizar_respuesta(datos)
        assert resultado["observaciones_proveedor"] == "Entregado"
        assert resultado["posiciones_correo"][0]["posicion"] == "10"

    def test_genera_filtros_busqueda_con_mock(self):
        from apps.integraciones.services.ai_extraction_service import AIExtractionService
        import json

        service = AIExtractionService()
        service.client = MagicMock()

        filtros_ia = {
            "filtros": {"estado_pedido": "Vigente"},
            "order_by": "-created_at",
            "limit": 20,
        }
        mock_msg = MagicMock()
        mock_msg.choices[0].message.content = json.dumps(filtros_ia)
        service.client.chat.completions.create.return_value = mock_msg

        resultado = service.generar_filtros_busqueda("pedidos vigentes de corona")
        assert resultado["filtros"]["estado_pedido"] == "Vigente"

    def test_genera_filtros_retorna_defaults_sin_cliente(self):
        from apps.integraciones.services.ai_extraction_service import AIExtractionService
        with patch.dict("os.environ", {}, clear=True):
            service = AIExtractionService()
            resultado = service.generar_filtros_busqueda("cualquier consulta")
            assert "filtros" in resultado


# ---------------------------------------------------------------------------
# AzureDocumentService
# ---------------------------------------------------------------------------

class TestAzureDocumentService:

    def test_no_disponible_sin_configuracion(self):
        from apps.integraciones.services.azure_document_service import AzureDocumentService
        with patch.dict("os.environ", {}, clear=True):
            service = AzureDocumentService()
            assert service.is_available() is False

    def test_retorna_none_cuando_no_disponible(self):
        from apps.integraciones.services.azure_document_service import AzureDocumentService
        with patch.dict("os.environ", {}, clear=True):
            service = AzureDocumentService()
            resultado = service.extraer_texto_documento(b"contenido")
            assert resultado is None

    def test_extrae_texto_con_mock_cliente(self):
        from apps.integraciones.services.azure_document_service import AzureDocumentService

        service = AzureDocumentService()
        mock_cliente = MagicMock()
        service.client = mock_cliente

        mock_result = MagicMock()
        mock_result.content = "Texto extraído del PDF"
        mock_result.tables = []
        mock_cliente.begin_analyze_document.return_value.result.return_value = mock_result

        resultado = service.extraer_texto_documento(b"pdf bytes")
        assert "Texto extraído del PDF" in resultado

    def test_extrae_multiples_adjuntos(self):
        from apps.integraciones.services.azure_document_service import AzureDocumentService

        service = AzureDocumentService()
        mock_cliente = MagicMock()
        service.client = mock_cliente

        mock_result = MagicMock()
        mock_result.content = "Contenido adjunto"
        mock_result.tables = []
        mock_cliente.begin_analyze_document.return_value.result.return_value = mock_result

        adjuntos = [
            {"contenido_bytes": b"pdf1", "content_type": "application/pdf", "name": "doc1.pdf"},
            {"contenido_bytes": b"pdf2", "content_type": "application/pdf", "name": "doc2.pdf"},
        ]
        resultado = service.extraer_texto_multiples(adjuntos)
        assert resultado is not None
        assert "doc1.pdf" in resultado
        assert "doc2.pdf" in resultado

    def test_extrae_multiples_retorna_none_sin_contenido(self):
        from apps.integraciones.services.azure_document_service import AzureDocumentService
        with patch.dict("os.environ", {}, clear=True):
            service = AzureDocumentService()
            resultado = service.extraer_texto_multiples([
                {"contenido_bytes": b"x", "content_type": "application/pdf", "name": "f.pdf"}
            ])
            assert resultado is None

    def test_maneja_excepcion_en_extraccion(self):
        from apps.integraciones.services.azure_document_service import AzureDocumentService

        service = AzureDocumentService()
        mock_cliente = MagicMock()
        service.client = mock_cliente
        mock_cliente.begin_analyze_document.side_effect = Exception("Azure error")

        resultado = service.extraer_texto_documento(b"bytes")
        assert resultado is None


# ---------------------------------------------------------------------------
# SuplosService
# ---------------------------------------------------------------------------

class TestSuplosService:

    @pytest.mark.django_db
    @patch("apps.integraciones.services.supplos_service.requests.post")
    def test_obtiene_token_nuevo(self, mock_post):
        from apps.integraciones.services.supplos_service import SuplosService

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"token": "mi-token-123"}
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        service = SuplosService()
        token = service._get_or_refresh_token()

        assert token == "mi-token-123"

    @pytest.mark.django_db
    @patch("apps.integraciones.services.supplos_service.requests.post")
    def test_consultar_pedido_exitoso(self, mock_post):
        from apps.integraciones.services.supplos_service import SuplosService
        from apps.integraciones.models import SuplosToken
        from django.utils import timezone
        from datetime import timedelta

        # Crear token válido en DB para evitar el login
        SuplosToken.objects.create(
            access_token="token-valido",
            expires_at=timezone.now() + timedelta(hours=12),
            is_active=True,
        )

        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"npedido": 4501833743, "estado": "Vigente"}]
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        service = SuplosService()
        resultado = service.consultar_pedido(numero_pedido=4501833743)

        assert resultado["status"] == "OK"
        assert resultado["source"] == "supplos"

    @pytest.mark.django_db
    @patch("apps.integraciones.services.supplos_service.requests.post")
    def test_consultar_pedido_lanza_excepcion_en_error_http(self, mock_post):
        from apps.integraciones.services.supplos_service import SuplosService, SuplosServiceException
        from apps.integraciones.models import SuplosToken
        from django.utils import timezone
        from datetime import timedelta
        import requests

        SuplosToken.objects.create(
            access_token="token-valido",
            expires_at=timezone.now() + timedelta(hours=12),
            is_active=True,
        )

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        http_error = requests.exceptions.HTTPError(response=mock_resp)
        mock_resp.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_resp

        service = SuplosService()
        with pytest.raises(SuplosServiceException):
            service.consultar_pedido(numero_pedido=9999)

    @pytest.mark.django_db
    @patch("apps.integraciones.services.supplos_service.requests.post")
    def test_login_falla_lanza_excepcion(self, mock_post):
        from apps.integraciones.services.supplos_service import SuplosService, SuplosServiceException
        import requests

        mock_post.side_effect = requests.exceptions.ConnectionError("Sin conexión")

        service = SuplosService()
        with pytest.raises(SuplosServiceException):
            service._get_or_refresh_token()
