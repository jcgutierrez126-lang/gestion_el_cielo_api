from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    EmpleadoViewSet, ControlSemanalViewSet,
    PrestamoEmpleadoViewSet, TipoLaborViewSet, TipoCobroViewSet,
)
from .views_ia import (
    LeerPlanillaView, LeerPlanillaDiariaView, LeerPlanillaSemanalExcelView,
    GuardarPlanillaView, MatchEmpleadoView, ListEmpleadosActivosView,
)

router = DefaultRouter()
router.register('empleados', EmpleadoViewSet, basename='empleados')
router.register('control-semanal', ControlSemanalViewSet, basename='control-semanal')
router.register('prestamos', PrestamoEmpleadoViewSet, basename='prestamos')
router.register('tipos-labor', TipoLaborViewSet, basename='tipos-labor')
router.register('tipos-cobro', TipoCobroViewSet, basename='tipos-cobro')

urlpatterns = router.urls + [
    path('leer-planilla/', LeerPlanillaView.as_view(), name='leer-planilla'),
    path('leer-planilla-diaria/', LeerPlanillaDiariaView.as_view(), name='leer-planilla-diaria'),
    path('leer-planilla-excel/', LeerPlanillaSemanalExcelView.as_view(), name='leer-planilla-excel'),
    path('guardar-planilla/', GuardarPlanillaView.as_view(), name='guardar-planilla'),
    path('match-empleado/', MatchEmpleadoView.as_view(), name='match-empleado'),
    path('empleados-activos/', ListEmpleadosActivosView.as_view(), name='empleados-activos'),
]
