from rest_framework.routers import DefaultRouter
from .views import (
    LoteViewSet, VentaCafeViewSet, VentaCafeTostadoViewSet,
    VentaBananoViewSet, FloracionViewSet, MezclaAbonoViewSet,
)

router = DefaultRouter()
router.register('lotes', LoteViewSet, basename='lotes')
router.register('ventas-cafe', VentaCafeViewSet, basename='ventas-cafe')
router.register('ventas-cafe-tostado', VentaCafeTostadoViewSet, basename='ventas-cafe-tostado')
router.register('ventas-banano', VentaBananoViewSet, basename='ventas-banano')
router.register('floraciones', FloracionViewSet, basename='floraciones')
router.register('mezclas-abono', MezclaAbonoViewSet, basename='mezclas-abono')

urlpatterns = router.urls
