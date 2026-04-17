from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Empleado, ControlSemanal, PrestamoEmpleado, AbonoPrestamo
from .serializers import (
    EmpleadoSerializer, ControlSemanalSerializer,
    PrestamoEmpleadoSerializer, PrestamoEmpleadoListSerializer,
    AbonoPrestamoSerializer,
)


class EmpleadoViewSet(viewsets.ModelViewSet):
    serializer_class = EmpleadoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre_completo', 'cedula', 'labor']
    ordering_fields = ['nombre_completo', 'fecha_ingreso', 'created_at']

    def get_queryset(self):
        qs = Empleado.objects.all()
        activo = self.request.query_params.get('activo')
        if activo is not None:
            qs = qs.filter(activo=activo.lower() == 'true')
        return qs.order_by('nombre_completo')


class ControlSemanalViewSet(viewsets.ModelViewSet):
    serializer_class = ControlSemanalSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['lote', 'observaciones']
    ordering_fields = ['fecha_inicio', 'fecha_fin', 'valor', 'tipo_labor', 'created_at']

    def get_queryset(self):
        qs = ControlSemanal.objects.select_related('empleado').all()
        p = self.request.query_params

        empleado = p.get('empleado')
        fecha_desde = p.get('fecha_desde')
        fecha_hasta = p.get('fecha_hasta')
        tipo_labor = p.get('tipo_labor')
        tipo_cobro = p.get('tipo_cobro')
        es_vale = p.get('es_vale')
        lote = p.get('lote')

        if empleado:
            qs = qs.filter(empleado_id=empleado)
        if fecha_desde:
            qs = qs.filter(fecha_inicio__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha_inicio__lte=fecha_hasta)
        if tipo_labor:
            qs = qs.filter(tipo_labor=tipo_labor)
        if tipo_cobro:
            qs = qs.filter(tipo_cobro=tipo_cobro)
        if es_vale is not None:
            qs = qs.filter(es_vale=es_vale.lower() == 'true')
        if lote:
            qs = qs.filter(lote__icontains=lote)

        return qs.order_by('-fecha_inicio')


class PrestamoEmpleadoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['fecha', 'valor', 'saldo', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return PrestamoEmpleadoListSerializer
        return PrestamoEmpleadoSerializer

    def get_queryset(self):
        qs = PrestamoEmpleado.objects.select_related('empleado').prefetch_related('abonos').all()
        p = self.request.query_params

        empleado = p.get('empleado')
        con_saldo = p.get('con_saldo')

        if empleado:
            qs = qs.filter(empleado_id=empleado)
        if con_saldo == 'true':
            qs = qs.filter(saldo__gt=0)

        return qs.order_by('-fecha')

    @action(detail=True, methods=['post'], url_path='abonos')
    def crear_abono(self, request, pk=None):
        prestamo = self.get_object()
        serializer = AbonoPrestamoSerializer(data={**request.data, 'prestamo': prestamo.id})
        serializer.is_valid(raise_exception=True)
        abono = serializer.save()
        prestamo.recalcular_saldo()
        return Response(AbonoPrestamoSerializer(abono).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='abonos')
    def listar_abonos(self, request, pk=None):
        prestamo = self.get_object()
        abonos = prestamo.abonos.all().order_by('-fecha')
        serializer = AbonoPrestamoSerializer(abonos, many=True)
        return Response(serializer.data)
