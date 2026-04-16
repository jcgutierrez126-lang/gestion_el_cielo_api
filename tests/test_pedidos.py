import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.integraciones.models import Pedido, TrazabilidadPedido


@pytest.mark.django_db
class TestPedidoList:
    def test_listar_pedidos_retorna_200(self, client_con_key):
        response = client_con_key.get(reverse("integraciones:pedido-list"))
        assert response.status_code == status.HTTP_200_OK

    def test_listar_pedidos_retorna_lista(self, client_con_key, pedido):
        response = client_con_key.get(reverse("integraciones:pedido-list"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1

    def test_filtro_por_estado(self, client_con_key, pedido):
        url = reverse("integraciones:pedido-list") + "?estado=Vigente"
        response = client_con_key.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_filtro_por_fuente_supplos(self, client_con_key, pedido):
        url = reverse("integraciones:pedido-list") + "?fuente=supplos"
        response = client_con_key.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_busqueda_general(self, client_con_key, pedido):
        url = reverse("integraciones:pedido-list") + "?search=4501722041"
        response = client_con_key.get(url)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestPedidoDetail:
    def test_pedido_existente_retorna_200(self, client_con_key, pedido):
        url = reverse("integraciones:pedido-detail", kwargs={"numero_pedido": pedido.documento_compras})
        response = client_con_key.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_pedido_no_existente_retorna_404(self, client_con_key):
        url = reverse("integraciones:pedido-detail", kwargs={"numero_pedido": "9999999999"})
        response = client_con_key.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_pedido_por_id_retorna_200(self, client_con_key, pedido):
        url = reverse("integraciones:pedido-detail-by-id", kwargs={"pk": pedido.pk})
        response = client_con_key.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_pedido_por_id_inexistente_retorna_404(self, client_con_key):
        url = reverse("integraciones:pedido-detail-by-id", kwargs={"pk": 99999})
        response = client_con_key.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestPedidoUpdate:
    def test_actualizar_observaciones_retorna_200(self, client_con_key, pedido):
        url = reverse("integraciones:pedido-update", kwargs={"pk": pedido.pk})
        response = client_con_key.patch(url, {"observaciones_corona": "Actualizado en QA"})
        assert response.status_code == status.HTTP_200_OK

    def test_actualizar_estado_registra_trazabilidad(self, client_con_key, pedido):
        url = reverse("integraciones:pedido-update", kwargs={"pk": pedido.pk})
        response = client_con_key.patch(url, {"estado_pedido": "Entregado"})
        assert response.status_code == status.HTTP_200_OK
        assert TrazabilidadPedido.objects.filter(pedido=pedido).exists()

    def test_actualizar_pedido_inexistente_retorna_404(self, client_con_key):
        url = reverse("integraciones:pedido-update", kwargs={"pk": 99999})
        response = client_con_key.patch(url, {"observaciones_corona": "test"})
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestTrazabilidad:
    def test_trazabilidad_pedido_existente(self, client_con_key, pedido):
        url = reverse("integraciones:pedido-trazabilidad", kwargs={"numero_pedido": pedido.documento_compras})
        response = client_con_key.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "trazabilidad" in response.data

    def test_trazabilidad_pedido_inexistente_retorna_404(self, client_con_key):
        url = reverse("integraciones:pedido-trazabilidad", kwargs={"numero_pedido": "9999999999"})
        response = client_con_key.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestResincronizar:
    def test_numero_pedido_no_numerico_retorna_400(self, client_con_key):
        url = reverse("integraciones:pedido-resync", kwargs={"numero_pedido": "abc-invalido"})
        response = client_con_key.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("apps.integraciones.api.views.ConsolidationService")
    def test_resincronizar_pedido_exitoso(self, mock_service, client_con_key, pedido):
        mock_instance = MagicMock()
        mock_instance.buscar_y_consolidar.return_value = {"estado": "ok", "pedidos_procesados": 1}
        mock_service.return_value = mock_instance

        url = reverse("integraciones:pedido-resync", kwargs={"numero_pedido": pedido.documento_compras})
        response = client_con_key.post(url)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestBuscarPedido:
    @patch("apps.integraciones.api.views.ConsolidationService")
    def test_buscar_pedido_valido(self, mock_service, client_con_key):
        mock_instance = MagicMock()
        mock_instance.buscar_y_consolidar.return_value = {"estado": "ok", "pedidos_procesados": 0}
        mock_service.return_value = mock_instance

        url = reverse("integraciones:buscar-pedido")
        response = client_con_key.post(url, {"numero_pedido": 4501722041}, format="json")
        assert response.status_code == status.HTTP_200_OK

    def test_buscar_pedido_sin_numero_retorna_400(self, client_con_key):
        url = reverse("integraciones:buscar-pedido")
        response = client_con_key.post(url, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestEstadisticas:
    def test_estadisticas_retorna_200(self, client_con_key):
        url = reverse("integraciones:estadisticas")
        response = client_con_key.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "total_pedidos" in response.data
        assert "por_estado" in response.data
        assert "por_fuente" in response.data


@pytest.mark.django_db
class TestLogs:
    def test_logs_retorna_200(self, client_con_key):
        url = reverse("integraciones:log-list")
        response = client_con_key.get(url)
        assert response.status_code == status.HTTP_200_OK
