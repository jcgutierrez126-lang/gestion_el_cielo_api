from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count, Avg, Max, Min
from .models import Empleado, ControlSemanal, ControlDiario, PrestamoEmpleado, AbonoPrestamo, TipoLabor, TipoCobro
from .serializers import (
    EmpleadoSerializer, ControlSemanalSerializer, ControlDiarioSerializer,
    PrestamoEmpleadoSerializer, PrestamoEmpleadoListSerializer,
    AbonoPrestamoSerializer, TipoLaborSerializer, TipoCobroSerializer,
)


class TipoLaborViewSet(viewsets.ModelViewSet):
    serializer_class = TipoLaborSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre']
    ordering_fields = ['nombre']

    def get_queryset(self):
        qs = TipoLabor.objects.all()
        activo = self.request.query_params.get('activo')
        if activo is not None:
            qs = qs.filter(activo=activo.lower() == 'true')
        return qs.order_by('nombre')


class TipoCobroViewSet(viewsets.ModelViewSet):
    serializer_class = TipoCobroSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre']
    ordering_fields = ['nombre']

    def get_queryset(self):
        qs = TipoCobro.objects.all()
        activo = self.request.query_params.get('activo')
        if activo is not None:
            qs = qs.filter(activo=activo.lower() == 'true')
        return qs.order_by('nombre')


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
    ordering_fields = ['fecha_inicio', 'fecha_fin', 'valor', 'created_at']

    def get_queryset(self):
        qs = ControlSemanal.objects.select_related(
            'empleado', 'tipo_labor', 'tipo_cobro', 'lote'
        ).all()
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
            qs = qs.filter(tipo_labor_id=tipo_labor)
        if tipo_cobro:
            qs = qs.filter(tipo_cobro_id=tipo_cobro)
        if es_vale is not None:
            qs = qs.filter(es_vale=es_vale.lower() == 'true')
        if lote:
            qs = qs.filter(lote__icontains=lote)

        return qs.order_by('-fecha_inicio')

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = self.get_queryset()
        agg = qs.aggregate(
            total_valor=Sum('valor'),
            total_kilos=Sum('kilos'),
            total_jornales=Sum('jornales'),
            num_registros=Count('id'),
            num_empleados=Count('empleado', distinct=True),
            promedio_valor=Avg('valor'),
        )
        # Distribución por tipo_labor (top 5)
        por_labor = (
            qs.values('tipo_labor__nombre')
            .annotate(total=Sum('valor'), registros=Count('id'))
            .order_by('-total')[:6]
        )
        return Response({
            'total_valor': str(agg['total_valor'] or 0),
            'total_kilos': str(agg['total_kilos'] or 0),
            'total_jornales': str(agg['total_jornales'] or 0),
            'num_registros': agg['num_registros'] or 0,
            'num_empleados': agg['num_empleados'] or 0,
            'promedio_valor': str(agg['promedio_valor'] or 0),
            'por_labor': list(por_labor),
        })


class ControlDiarioViewSet(viewsets.ModelViewSet):
    serializer_class = ControlDiarioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'labor', 'lote', 'semana_ref']
    ordering_fields = ['fecha', 'nombre', 'created_at']

    def get_queryset(self):
        qs = ControlDiario.objects.all()
        p = self.request.query_params
        if semana := p.get('semana_ref'):
            qs = qs.filter(semana_ref__icontains=semana)
        if fecha_desde := p.get('fecha_desde'):
            qs = qs.filter(fecha__gte=fecha_desde)
        if fecha_hasta := p.get('fecha_hasta'):
            qs = qs.filter(fecha__lte=fecha_hasta)
        if nombre := p.get('nombre'):
            qs = qs.filter(nombre__icontains=nombre)
        return qs

    @action(detail=False, methods=['delete'], url_path='borrar-semana')
    def borrar_semana(self, request):
        semana_ref = request.query_params.get('semana_ref', '').strip()
        if not semana_ref:
            return Response({'error': 'semana_ref requerido'}, status=status.HTTP_400_BAD_REQUEST)
        count, _ = ControlDiario.objects.filter(semana_ref=semana_ref).delete()
        return Response({'eliminados': count})


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
