import pytest
from django.urls import reverse
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status


@pytest.mark.django_db
class TestPasswordResetRequest:
    """
    POST /api/v1/users/password-reset/
    Solicita un código de verificación al correo.
    """

    def setup_method(self):
        self.client = APIClient()
        self.url = reverse("usuarios:password-reset")

    def test_sin_email_retorna_400(self):
        response = self.client.post(self.url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_email_no_registrado_retorna_200(self):
        """No debe revelar si el email existe o no."""
        response = self.client.post(self.url, {"email": "noexiste@fincaelcielo.com"})
        assert response.status_code == status.HTTP_200_OK

    def test_email_registrado_con_correo_mockeado(self, usuario):
        """Simula envío exitoso del correo."""
        from unittest.mock import patch
        with patch(
            "apps.usuarios.api.views.enviar_correo_simple",
            return_value={"status": "OK"},
        ):
            response = self.client.post(self.url, {"email": usuario.email})
        assert response.status_code == status.HTTP_200_OK
        assert "email" in response.data

    def test_fallo_envio_correo_retorna_500(self, usuario):
        from unittest.mock import patch
        with patch(
            "apps.usuarios.api.views.enviar_correo_simple",
            return_value={"status": "ERROR", "message": "Timeout"},
        ):
            response = self.client.post(self.url, {"email": usuario.email})
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.django_db
class TestVerifyResetCode:
    """
    POST /api/v1/users/password-reset/verify/
    Verifica si el código es válido sin cambiar la contraseña.
    """

    def setup_method(self):
        self.client = APIClient()
        self.url = reverse("usuarios:password-reset-verify")

    def teardown_method(self):
        cache.clear()

    def test_sin_datos_retorna_400(self):
        response = self.client.post(self.url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_codigo_invalido_retorna_400(self, usuario):
        response = self.client.post(
            self.url, {"email": usuario.email, "code": "000000"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["valid"] is False

    def test_codigo_valido_retorna_200(self, usuario):
        cache.set(f"password_reset_{usuario.email}", "123456", timeout=900)
        response = self.client.post(
            self.url, {"email": usuario.email, "code": "123456"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["valid"] is True

    def test_codigo_expirado_retorna_400(self, usuario):
        """Cache vacío simula código expirado."""
        cache.delete(f"password_reset_{usuario.email}")
        response = self.client.post(
            self.url, {"email": usuario.email, "code": "123456"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["valid"] is False


@pytest.mark.django_db
class TestPasswordResetConfirm:
    """
    POST /api/v1/users/password-reset/confirm/
    Verifica el código y cambia la contraseña.
    """

    def setup_method(self):
        self.client = APIClient()
        self.url = reverse("usuarios:password-reset-confirm")

    def teardown_method(self):
        cache.clear()

    def test_sin_datos_retorna_400(self):
        response = self.client.post(self.url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_codigo_incorrecto_retorna_400(self, usuario):
        cache.set(f"password_reset_{usuario.email}", "123456", timeout=900)
        response = self.client.post(
            self.url,
            {"email": usuario.email, "code": "999999", "password": "NuevaClave1!"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_codigo_expirado_retorna_400(self, usuario):
        response = self.client.post(
            self.url,
            {"email": usuario.email, "code": "123456", "password": "NuevaClave1!"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cambio_exitoso_retorna_200(self, usuario):
        cache.set(f"password_reset_{usuario.email}", "123456", timeout=900)
        response = self.client.post(
            self.url,
            {"email": usuario.email, "code": "123456", "password": "NuevaClave1!"},
        )
        assert response.status_code == status.HTTP_200_OK

    def test_cambio_exitoso_permite_nuevo_login(self, usuario):
        """Tras el reset, el login debe funcionar con la contraseña nueva."""
        cache.set(f"password_reset_{usuario.email}", "654321", timeout=900)
        self.client.post(
            self.url,
            {"email": usuario.email, "code": "654321", "password": "ClaveNueva99!"},
        )
        login_response = APIClient().post(
            reverse("usuarios:login"),
            {"username": usuario.username, "password": "ClaveNueva99!"},
        )
        assert login_response.status_code == status.HTTP_200_OK
        assert "access" in login_response.data

    def test_codigo_se_elimina_tras_uso(self, usuario):
        """El código no puede reutilizarse después de un reset exitoso."""
        cache.set(f"password_reset_{usuario.email}", "111111", timeout=900)
        self.client.post(
            self.url,
            {"email": usuario.email, "code": "111111", "password": "Clave1!"},
        )
        second = self.client.post(
            self.url,
            {"email": usuario.email, "code": "111111", "password": "Clave2!"},
        )
        assert second.status_code == status.HTTP_400_BAD_REQUEST

    def test_email_inexistente_retorna_404(self):
        cache.set("password_reset_noexiste@test.com", "123456", timeout=900)
        response = self.client.post(
            self.url,
            {
                "email": "noexiste@test.com",
                "code": "123456",
                "password": "NuevaClave1!",
            },
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
