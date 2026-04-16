import pytest
from django.urls import reverse
from rest_framework import status
from apps.integraciones.models import CorreoAutorizado


@pytest.mark.django_db
class TestCorreoAutorizadoList:
    def test_listar_correos_retorna_200(self, client_con_key):
        response = client_con_key.get(reverse("integraciones:correos-list-create"))
        assert response.status_code == status.HTTP_200_OK
        assert "correos" in response.data
        assert "total" in response.data

    def test_crear_correo_retorna_201(self, client_con_key):
        response = client_con_key.post(
            reverse("integraciones:correos-list-create"),
            {"email": "nuevo@fincaelcielo.com", "es_buzon_principal": False, "activo": True},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert CorreoAutorizado.objects.filter(email="nuevo@fincaelcielo.com").exists()

    def test_crear_correo_email_invalido_retorna_400(self, client_con_key):
        response = client_con_key.post(
            reverse("integraciones:correos-list-create"),
            {"email": "no-es-un-email", "activo": True},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_crear_correo_sin_datos_retorna_400(self, client_con_key):
        response = client_con_key.post(
            reverse("integraciones:correos-list-create"),
            {},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestBuzonPrincipal:
    def test_solo_un_buzon_principal(self, client_con_key, correo_autorizado):
        """Al crear un segundo correo como principal, el primero debe dejar de serlo."""
        client_con_key.post(
            reverse("integraciones:correos-list-create"),
            {"email": "segundo@fincaelcielo.com", "es_buzon_principal": True, "activo": True},
            format="json",
        )
        assert CorreoAutorizado.objects.filter(es_buzon_principal=True).count() == 1
        assert CorreoAutorizado.objects.get(es_buzon_principal=True).email == "segundo@fincaelcielo.com"


@pytest.mark.django_db
class TestCorreoAutorizadoDetail:
    def test_obtener_correo_existente(self, client_con_key, correo_autorizado):
        url = reverse("integraciones:correos-detail", kwargs={"pk": correo_autorizado.pk})
        response = client_con_key.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == correo_autorizado.email

    def test_obtener_correo_inexistente_retorna_404(self, client_con_key):
        url = reverse("integraciones:correos-detail", kwargs={"pk": 99999})
        response = client_con_key.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_actualizar_correo(self, client_con_key, correo_autorizado):
        url = reverse("integraciones:correos-detail", kwargs={"pk": correo_autorizado.pk})
        response = client_con_key.put(
            url,
            {"email": "actualizado@fincaelcielo.com", "es_buzon_principal": True, "activo": True},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        correo_autorizado.refresh_from_db()
        assert correo_autorizado.email == "actualizado@fincaelcielo.com"

    def test_patch_correo(self, client_con_key, correo_autorizado):
        url = reverse("integraciones:correos-detail", kwargs={"pk": correo_autorizado.pk})
        response = client_con_key.patch(url, {"activo": False}, format="json")
        assert response.status_code == status.HTTP_200_OK
        correo_autorizado.refresh_from_db()
        assert correo_autorizado.activo is False

    def test_eliminar_correo(self, client_con_key, correo_autorizado):
        url = reverse("integraciones:correos-detail", kwargs={"pk": correo_autorizado.pk})
        response = client_con_key.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not CorreoAutorizado.objects.filter(pk=correo_autorizado.pk).exists()

    def test_eliminar_correo_inexistente_retorna_404(self, client_con_key):
        url = reverse("integraciones:correos-detail", kwargs={"pk": 99999})
        response = client_con_key.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
