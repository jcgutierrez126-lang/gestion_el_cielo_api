"""
Tests para apps/usuarios/api/api.py
Cubre las vistas CRUD básicas: list, create, detail, update, delete, patch, groups.
"""
import pytest
from rest_framework.test import APIRequestFactory, force_authenticate
from django.contrib.auth.models import Group

from apps.usuarios.api.api import (
    UserListAPIView,
    UserCreateAPIView,
    UserDetailAPIView,
    UserUpdateAPIView,
    UserDeleteAPIView,
    UserPatchAPIView,
    GroupListAPIView,
)
from apps.usuarios.models import User

factory = APIRequestFactory()

DATOS_USUARIO_NUEVO = {
    "username": "nuevo@corona.com.co",
    "email": "nuevo@corona.com.co",
    "first_name": "Nuevo",
    "last_name": "Usuario",
    "phone": "3001234567",
    "identification": "99999999",
    "password": "claveSegura123",
}


# ---------------------------------------------------------------------------
# UserListAPIView
# ---------------------------------------------------------------------------

class TestUserListAPIView:

    @pytest.mark.django_db
    def test_lista_usuarios_autenticado(self, usuario):
        request = factory.get("/api/usuarios/user-list/")
        force_authenticate(request, user=usuario)
        response = UserListAPIView.as_view()(request)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_lista_usuarios_sin_autenticacion_retorna_401(self):
        request = factory.get("/api/usuarios/user-list/")
        response = UserListAPIView.as_view()(request)
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_lista_con_busqueda(self, usuario):
        request = factory.get("/api/usuarios/user-list/", {"search": "test"})
        force_authenticate(request, user=usuario)
        response = UserListAPIView.as_view()(request)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# UserCreateAPIView
# ---------------------------------------------------------------------------

class TestUserCreateAPIView:

    @pytest.mark.django_db
    def test_crear_usuario_datos_validos(self, usuario):
        request = factory.post("/api/usuarios/user-create/", DATOS_USUARIO_NUEVO, format="json")
        force_authenticate(request, user=usuario)
        response = UserCreateAPIView.as_view()(request)
        assert response.status_code == 201

    @pytest.mark.django_db
    def test_crear_usuario_datos_invalidos_retorna_400(self, usuario):
        request = factory.post("/api/usuarios/user-create/", {"email": "mal"}, format="json")
        force_authenticate(request, user=usuario)
        response = UserCreateAPIView.as_view()(request)
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_crear_usuario_sin_autenticacion_retorna_401(self):
        request = factory.post("/api/usuarios/user-create/", DATOS_USUARIO_NUEVO, format="json")
        response = UserCreateAPIView.as_view()(request)
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# UserDetailAPIView
# ---------------------------------------------------------------------------

class TestUserDetailAPIView:

    @pytest.mark.django_db
    def test_detalle_usuario_existente(self, usuario):
        request = factory.get(f"/api/usuarios/{usuario.pk}/user-detail/")
        force_authenticate(request, user=usuario)
        response = UserDetailAPIView.as_view()(request, pk=str(usuario.pk))
        assert response.status_code == 200
        assert response.data["email"] == usuario.email

    @pytest.mark.django_db
    def test_detalle_usuario_inexistente_retorna_404(self, usuario):
        request = factory.get("/api/usuarios/99999/user-detail/")
        force_authenticate(request, user=usuario)
        response = UserDetailAPIView.as_view()(request, pk="99999")
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_detalle_sin_autenticacion_retorna_401(self, usuario):
        request = factory.get(f"/api/usuarios/{usuario.pk}/user-detail/")
        response = UserDetailAPIView.as_view()(request, pk=str(usuario.pk))
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# UserUpdateAPIView
# ---------------------------------------------------------------------------

class TestUserUpdateAPIView:

    @pytest.mark.django_db
    def test_actualizar_usuario_exitoso(self, usuario):
        datos = {
            "username": usuario.username,
            "email": usuario.email,
            "first_name": "NuevoNombre",
            "last_name": usuario.last_name,
            "phone": "3001234567",
            "identification": "12345678",
            "password": "claveNueva123",
        }
        request = factory.put(f"/api/usuarios/{usuario.pk}/user-update/", datos, format="json")
        force_authenticate(request, user=usuario)
        response = UserUpdateAPIView.as_view()(request, pk=str(usuario.pk))
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_actualizar_usuario_inexistente_retorna_404(self, usuario):
        request = factory.put("/api/usuarios/99999/user-update/", {}, format="json")
        force_authenticate(request, user=usuario)
        response = UserUpdateAPIView.as_view()(request, pk="99999")
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_actualizar_datos_invalidos_retorna_400(self, usuario):
        request = factory.put(
            f"/api/usuarios/{usuario.pk}/user-update/",
            {"email": "no-es-un-email"},
            format="json"
        )
        force_authenticate(request, user=usuario)
        response = UserUpdateAPIView.as_view()(request, pk=str(usuario.pk))
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# UserDeleteAPIView
# ---------------------------------------------------------------------------

class TestUserDeleteAPIView:

    @pytest.mark.django_db
    def test_eliminar_usuario_exitoso(self, usuario, admin_user):
        request = factory.delete(f"/api/usuarios/{usuario.pk}/user-delete/")
        force_authenticate(request, user=admin_user)
        response = UserDeleteAPIView.as_view()(request, pk=str(usuario.pk))
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_eliminar_usuario_inexistente_retorna_404(self, usuario):
        request = factory.delete("/api/usuarios/99999/user-delete/")
        force_authenticate(request, user=usuario)
        response = UserDeleteAPIView.as_view()(request, pk="99999")
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_eliminar_sin_autenticacion_retorna_401(self, usuario):
        request = factory.delete(f"/api/usuarios/{usuario.pk}/user-delete/")
        response = UserDeleteAPIView.as_view()(request, pk=str(usuario.pk))
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# UserPatchAPIView
# ---------------------------------------------------------------------------

class TestUserPatchAPIView:

    @pytest.mark.django_db
    def test_patch_campo_valido(self, usuario):
        request = factory.patch(
            f"/api/usuarios/{usuario.pk}/user-patch/",
            {"first_name": "Modificado"},
            format="json"
        )
        force_authenticate(request, user=usuario)
        response = UserPatchAPIView.as_view()(request, pk=str(usuario.pk))
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_patch_usuario_inexistente_retorna_404(self, usuario):
        request = factory.patch("/api/usuarios/99999/user-patch/", {}, format="json")
        force_authenticate(request, user=usuario)
        response = UserPatchAPIView.as_view()(request, pk="99999")
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_patch_sin_autenticacion_retorna_401(self, usuario):
        request = factory.patch(
            f"/api/usuarios/{usuario.pk}/user-patch/",
            {"first_name": "X"},
            format="json"
        )
        response = UserPatchAPIView.as_view()(request, pk=str(usuario.pk))
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# GroupListAPIView
# ---------------------------------------------------------------------------

class TestGroupListAPIView:

    @pytest.mark.django_db
    def test_lista_grupos_autenticado(self, usuario):
        Group.objects.create(name="Compras")
        request = factory.get("/api/usuarios/group-list/")
        force_authenticate(request, user=usuario)
        response = GroupListAPIView.as_view()(request)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_lista_grupos_sin_autenticacion_retorna_401(self):
        request = factory.get("/api/usuarios/group-list/")
        response = GroupListAPIView.as_view()(request)
        assert response.status_code == 401
