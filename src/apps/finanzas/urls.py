from rest_framework.routers import DefaultRouter
from .views import (
    CuentaViewSet, ProveedorViewSet, EgresoViewSet,
    IngresoViewSet, TransaccionViewSet, ObservacionViewSet,
)

router = DefaultRouter()
router.register('cuentas', CuentaViewSet, basename='cuentas')
router.register('proveedores', ProveedorViewSet, basename='proveedores')
router.register('egresos', EgresoViewSet, basename='egresos')
router.register('ingresos', IngresoViewSet, basename='ingresos')
router.register('transacciones', TransaccionViewSet, basename='transacciones')
router.register('observaciones', ObservacionViewSet, basename='observaciones')

urlpatterns = router.urls
