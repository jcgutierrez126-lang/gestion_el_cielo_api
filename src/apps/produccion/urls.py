from rest_framework.routers import DefaultRouter
from .views import (
    TipoBananoViewSet, TipoCafeViewSet, VariedadLoteViewSet,
    LoteViewSet, VentaCafeViewSet,
    VentaBananoViewSet, FloracionViewSet, MezclaAbonoViewSet,
    ObservacionViewSet,
)

router = DefaultRouter()
router.register('tipos-banano', TipoBananoViewSet, basename='tipos-banano')
router.register('tipos-cafe', TipoCafeViewSet, basename='tipos-cafe')
router.register('variedades-lote', VariedadLoteViewSet, basename='variedades-lote')
router.register('lotes', LoteViewSet, basename='lotes')
router.register('ventas-cafe', VentaCafeViewSet, basename='ventas-cafe')
router.register('ventas-banano', VentaBananoViewSet, basename='ventas-banano')
router.register('floraciones', FloracionViewSet, basename='floraciones')
router.register('mezclas-abono', MezclaAbonoViewSet, basename='mezclas-abono')
router.register('observaciones', ObservacionViewSet, basename='observaciones')

urlpatterns = router.urls
