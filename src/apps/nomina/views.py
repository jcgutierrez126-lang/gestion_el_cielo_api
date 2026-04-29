from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count, Avg, Min
from .models import Empleado, ControlSemanal, PrestamoEmpleado, AbonoPrestamo, TipoLabor, TipoCobro
from .serializers import (
    EmpleadoSerializer, ControlSemanalSerializer,
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
    search_fields = ['empleado__nombre_completo', 'observaciones', 'semana_ref']
    ordering_fields = ['fecha_inicio', 'fecha', 'valor', 'created_at']

    def get_queryset(self):
        qs = ControlSemanal.objects.select_related(
            'empleado', 'tipo_labor', 'tipo_cobro', 'lote'
        ).all()
        p = self.request.query_params

        if empleado := p.get('empleado'):
            qs = qs.filter(empleado_id=empleado)
        if fecha_desde := p.get('fecha_desde'):
            qs = qs.filter(fecha_inicio__gte=fecha_desde)
        if fecha_hasta := p.get('fecha_hasta'):
            qs = qs.filter(fecha_inicio__lte=fecha_hasta)
        if tipo_labor := p.get('tipo_labor'):
            qs = qs.filter(tipo_labor_id=tipo_labor)
        if tipo_cobro := p.get('tipo_cobro'):
            qs = qs.filter(tipo_cobro_id=tipo_cobro)
        if es_vale := p.get('es_vale'):
            qs = qs.filter(es_vale=es_vale.lower() == 'true')
        if semana := p.get('semana_ref'):
            qs = qs.filter(semana_ref__icontains=semana)

        return qs.order_by('-fecha_inicio', 'empleado__nombre_completo')

    @action(detail=False, methods=['get'], url_path='semanas')
    def semanas(self, request):
        data = (
            ControlSemanal.objects
            .exclude(semana_ref='')
            .values('semana_ref')
            .annotate(fecha_min=Min('fecha_inicio'))
            .order_by('-fecha_min')
        )
        return Response(list(data))

    @action(detail=False, methods=['get'], url_path='por-semana')
    def por_semana(self, request):
        semana_ref = request.query_params.get('semana_ref', '').strip()
        if not semana_ref:
            return Response({'error': 'semana_ref requerido'}, status=status.HTTP_400_BAD_REQUEST)
        qs = (
            ControlSemanal.objects
            .select_related('empleado', 'tipo_labor', 'tipo_cobro', 'lote')
            .filter(semana_ref=semana_ref)
            .order_by('empleado__nombre_completo', 'fecha')
        )
        return Response(ControlSemanalSerializer(qs, many=True).data)

    @action(detail=False, methods=['delete'], url_path='borrar-semana')
    def borrar_semana(self, request):
        semana_ref = request.query_params.get('semana_ref', '').strip()
        if not semana_ref:
            return Response({'error': 'semana_ref requerido'}, status=status.HTTP_400_BAD_REQUEST)
        count, _ = ControlSemanal.objects.filter(semana_ref=semana_ref).delete()
        return Response({'eliminados': count})

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


class PrestamoEmpleadoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['fecha', 'valor', 'saldo', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return PrestamoEmpleadoListSerializer
        return PrestamoEmpleadoSerializer

    def get_queryset(self):
        qs = PrestamoEmpleado.objects.select_related('empleado').prefetch_related('abonos')
        p = self.request.query_params
        if empleado := p.get('empleado'):
            qs = qs.filter(empleado_id=empleado)
        if con_saldo := p.get('con_saldo'):
            if con_saldo.lower() == 'true':
                qs = qs.filter(saldo__gt=0)
        return qs.order_by('-fecha')

    @action(detail=True, methods=['post'], url_path='abonar')
    def abonar(self, request, pk=None):
        prestamo = self.get_object()
        serializer = AbonoPrestamoSerializer(data={**request.data, 'prestamo': prestamo.id})
        serializer.is_valid(raise_exception=True)
        abono = serializer.save()
        prestamo.recalcular_saldo()
        return Response(AbonoPrestamoSerializer(abono).data, status=status.HTTP_201_CREATED)
