import pytest
from django.core.cache import cache
from rest_framework.test import APIClient
from apps.usuarios.models import User
from apps.integraciones.models import APIKey, Pedido, CorreoAutorizado


@pytest.fixture(autouse=True)
def limpiar_cache():
    """Limpia la caché antes de cada test para evitar contaminación del rate limiter."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def usuario(db):
    return User.objects.create_user(
        username="testuser",
        email="test@fincaelcielo.com",
        first_name="Test",
        last_name="User",
        password="testpass123",
    )


@pytest.fixture
def admin_user(db):
    user = User.objects.create_user(
        username="adminuser",
        email="admin@fincaelcielo.com",
        first_name="Admin",
        last_name="User",
        password="adminpass123",
    )
    user.is_admin = True
    user.save()
    return user


@pytest.fixture
def api_key(db, usuario):
    _, raw_key = APIKey.create_key("test-bot")
    return raw_key


@pytest.fixture
def client_con_key(api_key):
    client = APIClient()
    client.credentials(HTTP_X_API_KEY=api_key)
    return client


@pytest.fixture
def client_con_jwt(usuario):
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(usuario)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.fixture
def admin_client_con_jwt(admin_user):
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(admin_user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.fixture
def pedido(db):
    return Pedido.objects.create(
        documento_compras="4501722041",
        posicion="10",
        razon_social="Proveedor Test S.A.",
        estado_pedido=Pedido.EstadoPedido.VIGENTE,
        fuente_supplos=True,
    )


@pytest.fixture
def correo_autorizado(db):
    return CorreoAutorizado.objects.create(
        email="buzon@fincaelcielo.com",
        es_buzon_principal=True,
        activo=True,
    )
