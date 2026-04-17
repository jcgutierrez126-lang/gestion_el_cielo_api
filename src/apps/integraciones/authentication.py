from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission


class IsAPIKeyAuthenticated(BasePermission):
    """
    Exige autenticacion exclusivamente via X-API-Key.
    JWT no es suficiente — el cliente debe tener una key generada.
    """
    message = "Se requiere una API Key valida en el header X-API-Key."

    def has_permission(self, request, view):
        from apps.integraciones.models import APIKey
        return isinstance(request.auth, APIKey)


class APIKeyAuthentication(BaseAuthentication):
    """
    Autenticacion via header X-API-Key.
    El bot de Teams envia este header en cada request.
    Compatible con JWT — DRF prueba ambos en orden.

    Uso en el bot (Node.js):
        headers: { 'X-API-Key': process.env.CIELO_API_KEY }
    """

    def authenticate(self, request):
        raw_key = request.META.get("HTTP_X_API_KEY")
        if not raw_key:
            return None  # No es este metodo, DRF prueba el siguiente (JWT)

        from apps.integraciones.models import APIKey
        api_key = APIKey.validate(raw_key)

        if not api_key:
            raise AuthenticationFailed("API Key invalida o inactiva.")

        # Actualizar ultimo uso
        APIKey.objects.filter(pk=api_key.pk).update(last_used_at=timezone.now())

        # Retornar (user=None, auth=api_key) — los endpoints usan IsAuthenticated
        # pero tambien aceptamos IsAPIKeyAuthenticated para restringir solo al bot
        return (None, api_key)

    def authenticate_header(self, request):
        return "X-API-Key"
