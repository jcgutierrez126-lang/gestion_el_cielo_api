from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.views import APIView
from rest_framework.response import Response

class APIRootView(APIView):
    """
    API Root - Finca el Cielo
    """
    permission_classes = []

    def get(self, request):
        return Response({
            "api": "Finca el Cielo API",
            "version": "1.0",
            "endpoints": {
                "users": "/api/v1/users/",
                "pedidos": "/api/v1/pedidos/",
                "docs": "https://cieloapi.lambdaanalytics.co/docs/",
            },
            "status": "operational"
        })


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API Root
    path('api/', APIRootView.as_view(), name='api-root'),

    # API v1 (versionado)
    path('api/v1/users/', include(('apps.usuarios.api.urls', 'usuarios'), namespace='usuarios')),
    path('api/v1/pedidos/', include(('apps.integraciones.api.urls', 'integraciones'), namespace='integraciones')),

    # Legacy URLs (backwards compatibility) - redirigen a v1
    path('api/users/', include('apps.usuarios.api.urls')),
    path('api/pedidos/', include('apps.integraciones.api.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
