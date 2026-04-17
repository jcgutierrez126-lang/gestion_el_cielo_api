from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.views import APIView
from rest_framework.response import Response


class APIRootView(APIView):
    permission_classes = []

    def get(self, request):
        return Response({
            "api": "Finca El Cielo API",
            "version": "1.0",
            "endpoints": {
                "users":      "/api/v1/users/",
                "finanzas":   "/api/v1/finanzas/",
                "produccion": "/api/v1/produccion/",
                "nomina":     "/api/v1/nomina/",
            },
            "status": "operational"
        })


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', APIRootView.as_view(), name='api-root'),

    path('api/v1/users/',      include(('apps.usuarios.api.urls', 'usuarios'), namespace='usuarios')),
    path('api/v1/finanzas/',   include('apps.finanzas.urls')),
    path('api/v1/produccion/', include('apps.produccion.urls')),
    path('api/v1/nomina/',     include('apps.nomina.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
