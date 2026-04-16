import pytest
from unittest.mock import patch
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.usuarios.models import User


REGISTRO_URL = "usuarios:register"

DATOS_VALIDOS = {
    "email": "nuevo@corona.com.co",
    "password": "Segura123!",
    "first_name": "Nuevo",
    "last_name": "Usuario",
    "phone": "3001234567",
    "identification": "123456789",
}

MOCK_PATH = "apps.usuarios.api.views.enviar_correo_simple"


@pytest.mark.django_db
class TestRegistroUsuario:
    """
    POST /api/v1/users/register/
    Registro público de usuarios. Quedan inactivos hasta aprobación admin.
    """

    def setup_method(self):
        self.client = APIClient()
        self.url = reverse(REGISTRO_URL)

    @patch(MOCK_PATH, return_value={"status": "OK"})
    def test_registro_exitoso_retorna_201(self, _mock):
        response = self.client.post(self.url, DATOS_VALIDOS, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    @patch(MOCK_PATH, return_value={"status": "OK"})
    def test_usuario_creado_queda_inactivo(self, _mock):
        self.client.post(self.url, DATOS_VALIDOS, format="json")
        user = User.objects.get(email=DATOS_VALIDOS["email"])
        assert user.status is False

    @patch(MOCK_PATH, return_value={"status": "OK"})
    def test_usuario_no_es_admin(self, _mock):
        self.client.post(self.url, DATOS_VALIDOS, format="json")
        user = User.objects.get(email=DATOS_VALIDOS["email"])
        assert user.is_admin is False

    def test_campo_requerido_faltante_retorna_400(self):
        for campo in ["email", "password", "first_name", "last_name", "phone", "identification"]:
            datos = {k: v for k, v in DATOS_VALIDOS.items() if k != campo}
            response = self.client.post(self.url, datos, format="json")
            assert response.status_code == status.HTTP_400_BAD_REQUEST, (
                f"Se esperaba 400 cuando falta '{campo}'"
            )

    @patch(MOCK_PATH, return_value={"status": "OK"})
    def test_email_duplicado_retorna_400(self, _mock, usuario):
        datos = {**DATOS_VALIDOS, "email": usuario.email, "identification": "999"}
        response = self.client.post(self.url, datos, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch(MOCK_PATH, return_value={"status": "OK"})
    def test_identificacion_duplicada_retorna_400(self, _mock):
        self.client.post(self.url, DATOS_VALIDOS, format="json")
        datos_dup = {**DATOS_VALIDOS, "email": "otro@corona.com.co"}
        response = self.client.post(self.url, datos_dup, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch(MOCK_PATH, return_value={"status": "OK"})
    def test_usuario_inactivo_no_puede_loguearse(self, _mock):
        self.client.post(self.url, DATOS_VALIDOS, format="json")
        login = self.client.post(
            reverse("usuarios:login"),
            {
                "username": DATOS_VALIDOS["email"].split("@")[0],
                "password": DATOS_VALIDOS["password"],
            },
        )
        assert login.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_400_BAD_REQUEST)

    @patch(MOCK_PATH, return_value={"status": "OK"})
    def test_username_generado_desde_email(self, _mock):
        self.client.post(self.url, DATOS_VALIDOS, format="json")
        user = User.objects.get(email=DATOS_VALIDOS["email"])
        assert user.username == DATOS_VALIDOS["email"].split("@")[0]
