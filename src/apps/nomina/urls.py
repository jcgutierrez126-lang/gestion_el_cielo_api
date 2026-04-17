from rest_framework.routers import DefaultRouter
from .views import EmpleadoViewSet, ControlSemanalViewSet, PrestamoEmpleadoViewSet

router = DefaultRouter()
router.register('empleados', EmpleadoViewSet, basename='empleados')
router.register('control-semanal', ControlSemanalViewSet, basename='control-semanal')
router.register('prestamos', PrestamoEmpleadoViewSet, basename='prestamos')

urlpatterns = router.urls
