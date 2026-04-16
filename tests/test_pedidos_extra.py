import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from apps.integraciones.models import Pedido, TrazabilidadPedido, CorreoProcesado


# ─────────────────────────────────────────────
# Endpoint unificado: POST /api/v1/pedidos/consultar/
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestPedidoUnificado:

    def test_sin_numero_pedido_retorna_400(self, client_con_key):
        url = reverse("integraciones:pedido-unificado")
        response = client_con_key.post(url, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_consultar_pedido_existente_retorna_200(self, client_con_key, pedido):
        """Pedido existe en DB y no se pide forzar → acción 'consultado'."""
        url = reverse("integraciones:pedido-unificado")
        response = client_con_key.post(
            url, {"numero_pedido": pedido.documento_compras}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["accion"] == "consultado"
        assert len(response.data["pedidos"]) >= 1

    def test_actualizar_estado_pedido_existente(self, client_con_key, pedido):
        """Pedido existe + se envía estado_pedido → acción 'actualizado'."""
        url = reverse("integraciones:pedido-unificado")
        response = client_con_key.post(
            url,
            {
                "numero_pedido": pedido.documento_compras,
                "estado_pedido": "Entregado",
                "observaciones_cielo": "Entrega confirmada",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["accion"] == "actualizado"
        pedido.refresh_from_db()
        assert pedido.estado_pedido == "Entregado"

    def test_actualizar_genera_trazabilidad(self, client_con_key, pedido):
        url = reverse("integraciones:pedido-unificado")
        client_con_key.post(
            url,
            {"numero_pedido": pedido.documento_compras, "estado_pedido": "Entregado"},
            format="json",
        )
        assert TrazabilidadPedido.objects.filter(pedido=pedido).exists()

    @patch("apps.integraciones.api.views.ConsolidationService")
    def test_pedido_inexistente_llama_consolidation(self, mock_service, client_con_key):
        """Número que no existe en DB dispara ConsolidationService."""
        mock_instance = MagicMock()
        mock_instance.buscar_y_consolidar.return_value = {
            "supplos": {}, "graph": {}, "consolidado": False, "errores": []
        }
        mock_service.return_value = mock_instance

        url = reverse("integraciones:pedido-unificado")
        response = client_con_key.post(
            url, {"numero_pedido": "9999999999"}, format="json"
        )
        mock_instance.buscar_y_consolidar.assert_called_once()
        # Sin resultados en la BD el endpoint devuelve 404
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_sin_autenticacion_retorna_401(self):
        from rest_framework.test import APIClient
        client = APIClient()
        url = reverse("integraciones:pedido-unificado")
        response = client.post(url, {"numero_pedido": "4501722041"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ─────────────────────────────────────────────
# Correos procesados: GET /api/v1/pedidos/correos-procesados/
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestCorreosProcesados:

    def test_listar_correos_procesados_retorna_200(self, client_con_key):
        url = reverse("integraciones:correos-procesados")
        response = client_con_key.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_lista_vacia_cuando_no_hay_registros(self, client_con_key):
        url = reverse("integraciones:correos-procesados")
        response = client_con_key.get(url)
        assert response.data["count"] == 0

    def test_filtro_por_buzon(self, client_con_key, db):
        CorreoProcesado.objects.create(
            email_id="msg-001",
            buzon="buzon1@fincaelcielo.com",
            subject="Pedido 4501722041",
        )
        CorreoProcesado.objects.create(
            email_id="msg-002",
            buzon="buzon2@fincaelcielo.com",
            subject="Pedido 4501722042",
        )
        url = reverse("integraciones:correos-procesados") + "?buzon=buzon1"
        response = client_con_key.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_sin_autenticacion_retorna_401(self):
        from rest_framework.test import APIClient
        client = APIClient()
        url = reverse("integraciones:correos-procesados")
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ─────────────────────────────────────────────
# Búsqueda IA: POST /api/v1/pedidos/busqueda-ia/
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestBusquedaIA:

    def test_sin_consulta_retorna_400(self, client_con_key):
        url = reverse("integraciones:busqueda-ia")
        response = client_con_key.post(url, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_consulta_demasiado_larga_retorna_400(self, client_con_key):
        url = reverse("integraciones:busqueda-ia")
        response = client_con_key.post(url, {"consulta": "x" * 501}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("apps.integraciones.services.ai_extraction_service.AIExtractionService")
    def test_ia_devuelve_error_retorna_503(self, mock_ai, client_con_key):
        mock_instance = MagicMock()
        mock_instance.generar_filtros_busqueda.return_value = {
            "error": True,
            "descripcion": "Servicio no disponible",
        }
        mock_ai.return_value = mock_instance

        url = reverse("integraciones:busqueda-ia")
        response = client_con_key.post(url, {"consulta": "pedidos retrasados"}, format="json")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    @patch("apps.integraciones.services.ai_extraction_service.AIExtractionService")
    def test_busqueda_exitosa_retorna_200(self, mock_ai, client_con_key, pedido):
        mock_instance = MagicMock()
        mock_instance.generar_filtros_busqueda.return_value = {
            "error": False,
            "filtros": {"fuente_supplos": True},
            "orden": "-fecha_entrega",
            "descripcion": "Pedidos de Supplos",
        }
        mock_ai.return_value = mock_instance

        url = reverse("integraciones:busqueda-ia")
        response = client_con_key.post(url, {"consulta": "pedidos de supplos"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "resultados" in response.data
        assert "total" in response.data

    @patch("apps.integraciones.services.ai_extraction_service.AIExtractionService")
    def test_filtros_inseguros_son_ignorados(self, mock_ai, client_con_key):
        """Campos fuera del whitelist no deben llegar al ORM."""
        mock_instance = MagicMock()
        mock_instance.generar_filtros_busqueda.return_value = {
            "error": False,
            "filtros": {"campo_inexistente__inject": "malo"},
            "orden": "-fecha_entrega",
            "descripcion": "Intento de inyección",
        }
        mock_ai.return_value = mock_instance

        url = reverse("integraciones:busqueda-ia")
        response = client_con_key.post(url, {"consulta": "test"}, format="json")
        # No debe explotar — el whitelist lo filtra y devuelve resultados vacíos
        assert response.status_code == status.HTTP_200_OK
        assert response.data["filtros_aplicados"] == {}

    def test_sin_autenticacion_retorna_401(self):
        from rest_framework.test import APIClient
        client = APIClient()
        url = reverse("integraciones:busqueda-ia")
        response = client.post(url, {"consulta": "test"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
