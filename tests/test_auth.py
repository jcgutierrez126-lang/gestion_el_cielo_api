import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


@pytest.mark.django_db
class TestLogin:
    def setup_method(self):
        self.client = APIClient()
        self.url = reverse("usuarios:login")

    def test_login_sin_credenciales(self):
        response = self.client.post(self.url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_credenciales_invalidas(self):
        response = self.client.post(
            self.url,
            {"username": "noexiste", "password": "incorrecta"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestAPIKey:
    def setup_method(self):
        self.client = APIClient()

    def test_pedidos_sin_key_retorna_401(self):
        url = reverse("integraciones:pedido-list")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_pedidos_key_invalida_retorna_401_o_403(self):
        url = reverse("integraciones:pedido-list")
        response = self.client.get(url, HTTP_X_API_KEY="key-invalida")
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_jwt_solo_no_accede_a_integraciones(self, client_con_jwt):
        """JWT sin API Key no debe poder acceder a endpoints de integraciones."""
        url = reverse("integraciones:pedido-list")
        response = client_con_jwt.get(url)
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_api_key_valida_accede_a_integraciones(self, client_con_key):
        url = reverse("integraciones:pedido-list")
        response = client_con_key.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_key_inactiva_retorna_401_o_403(self, db):
        from apps.integraciones.models import APIKey
        _, raw_key = APIKey.create_key("key-inactiva")
        APIKey.objects.filter(key_prefix=raw_key[:8]).update(is_active=False)
        client = APIClient()
        client.credentials(HTTP_X_API_KEY=raw_key)
        url = reverse("integraciones:pedido-list")
        response = client.get(url)
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )
