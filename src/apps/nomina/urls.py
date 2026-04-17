from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import EmpleadoViewSet, ControlSemanalViewSet, PrestamoEmpleadoViewSet
from .views_ia import LeerPlanillaView

router = DefaultRouter()
router.register('empleados', EmpleadoViewSet, basename='empleados')
router.register('control-semanal', ControlSemanalViewSet, basename='control-semanal')
router.register('prestamos', PrestamoEmpleadoViewSet, basename='prestamos')

urlpatterns = router.urls + [
    path('leer-planilla/', LeerPlanillaView.as_view(), name='leer-planilla'),
]
