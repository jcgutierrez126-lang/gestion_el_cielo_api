import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.usuarios.models import User


@pytest.mark.django_db
class TestLogin:
    def test_login_exitoso(self, usuario):
        client = APIClient()
        response = client.post(
            reverse("usuarios:login"),
            {"username": usuario.username, "password": "testpass123"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_password_incorrecto(self, usuario):
        client = APIClient()
        response = client.post(
            reverse("usuarios:login"),
            {"username": usuario.username, "password": "wrongpassword"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_usuario_inexistente(self):
        client = APIClient()
        response = client.post(
            reverse("usuarios:login"),
            {"username": "noexiste", "password": "pass123"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestRefreshToken:
    def test_refresh_token_valido(self, usuario):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(usuario)
        client = APIClient()
        response = client.post(
            reverse("usuarios:token-refresh"),
            {"refresh": str(refresh)},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_refresh_token_invalido(self):
        client = APIClient()
        response = client.post(
            reverse("usuarios:token-refresh"),
            {"refresh": "token-invalido"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserCRUD:
    def test_listar_usuarios_requiere_autenticacion(self):
        client = APIClient()
        response = client.get(reverse("usuarios:user-list"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_listar_usuarios_autenticado(self, client_con_jwt):
        response = client_con_jwt.get(reverse("usuarios:user-list"))
        assert response.status_code == status.HTTP_200_OK

    def test_detalle_usuario(self, client_con_jwt, usuario):
        url = reverse("usuarios:user-detail", kwargs={"pk": usuario.pk})
        response = client_con_jwt.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == usuario.email

    def test_detalle_usuario_inexistente_retorna_404(self, client_con_jwt):
        url = reverse("usuarios:user-detail", kwargs={"pk": 99999})
        response = client_con_jwt.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_actualizar_usuario(self, admin_client_con_jwt, usuario):
        url = reverse("usuarios:user-patch", kwargs={"pk": usuario.pk})
        response = admin_client_con_jwt.patch(url, {"first_name": "NuevoNombre"}, format="json")
        assert response.status_code == status.HTTP_200_OK

    def test_eliminar_usuario(self, admin_client_con_jwt, usuario):
        url = reverse("usuarios:user-delete", kwargs={"pk": usuario.pk})
        response = admin_client_con_jwt.delete(url)
        assert response.status_code in (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT)
