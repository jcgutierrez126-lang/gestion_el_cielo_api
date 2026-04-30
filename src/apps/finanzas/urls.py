from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    CiudadViewSet, CuentaViewSet, ProveedorViewSet, EgresoViewSet,
    IngresoViewSet, TransaccionViewSet, ObservacionViewSet,
    ResumenView, GraficasView,
)

router = DefaultRouter()
router.register('ciudades', CiudadViewSet, basename='ciudades')
router.register('cuentas', CuentaViewSet, basename='cuentas')
router.register('proveedores', ProveedorViewSet, basename='proveedores')
router.register('egresos', EgresoViewSet, basename='egresos')
router.register('ingresos', IngresoViewSet, basename='ingresos')
router.register('transacciones', TransaccionViewSet, basename='transacciones')
router.register('observaciones', ObservacionViewSet, basename='observaciones')

urlpatterns = router.urls + [
    path('resumen/', ResumenView.as_view(), name='finanzas-resumen'),
    path('graficas/', GraficasView.as_view(), name='finanzas-graficas'),
]
