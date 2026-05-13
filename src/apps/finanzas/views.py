from datetime import date
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncMonth
from .models import Ciudad, Cuenta, Proveedor, Egreso, Ingreso, Transaccion, InversionCDT
from .serializers import (
    CiudadSerializer, CuentaSerializer, ProveedorSerializer, EgresoSerializer,
    IngresoSerializer, TransaccionSerializer, InversionCDTSerializer,
)


class CiudadViewSet(viewsets.ModelViewSet):
    serializer_class = CiudadSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['nombre']

    def get_queryset(self):
        return Ciudad.objects.all().order_by('nombre')


class CuentaViewSet(viewsets.ModelViewSet):
    queryset = Cuenta.objects.all().order_by('nombre')
    serializer_class = CuentaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'tipo']
    ordering_fields = ['nombre', 'tipo', 'created_at']


class ProveedorViewSet(viewsets.ModelViewSet):
    serializer_class = ProveedorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'cedula_nit', 'ciudad__nombre', 'email']
    ordering_fields = ['nombre', 'created_at']

    def get_queryset(self):
        qs = Proveedor.objects.select_related('ciudad').all()
        ciudad = self.request.query_params.get('ciudad')
        if ciudad:
            qs = qs.filter(ciudad_id=ciudad)
        return qs.order_by('nombre')


class EgresoViewSet(viewsets.ModelViewSet):
    serializer_class = EgresoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'descripcion', 'nit_proveedor_destino', 'facturado_a']
    ordering_fields = ['fecha', 'valor', 'categoria', 'estado', 'created_at']

    def get_queryset(self):
        qs = Egreso.objects.select_related('cuenta', 'proveedor').all()
        p = self.request.query_params

        fecha_desde = p.get('fecha_desde')
        fecha_hasta = p.get('fecha_hasta')
        categoria = p.get('categoria')
        cuenta = p.get('cuenta')
        estado = p.get('estado')
        proveedor = p.get('proveedor')

        if fecha_desde:
            qs = qs.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha__lte=fecha_hasta)
        if categoria:
            qs = qs.filter(categoria=categoria)
        if cuenta:
            qs = qs.filter(cuenta_id=cuenta)
        if estado:
            qs = qs.filter(estado=estado)
        if proveedor:
            qs = qs.filter(proveedor_id=proveedor)

        return qs.order_by('-fecha')

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        agg = self.filter_queryset(self.get_queryset()).aggregate(total_valor=Sum('valor'))
        response.data['total_valor'] = str(agg['total_valor'] or 0)
        return response


class IngresoViewSet(viewsets.ModelViewSet):
    serializer_class = IngresoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['descripcion', 'origen']
    ordering_fields = ['fecha', 'valor', 'created_at']

    def get_queryset(self):
        qs = Ingreso.objects.select_related('cuenta_destino').all()
        p = self.request.query_params

        fecha_desde = p.get('fecha_desde')
        fecha_hasta = p.get('fecha_hasta')
        cuenta = p.get('cuenta_destino')

        if fecha_desde:
            qs = qs.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha__lte=fecha_hasta)
        if cuenta:
            qs = qs.filter(cuenta_destino_id=cuenta)

        return qs.order_by('-fecha')

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        agg = self.filter_queryset(self.get_queryset()).aggregate(total_valor=Sum('valor'))
        response.data['total_valor'] = str(agg['total_valor'] or 0)
        return response


class TransaccionViewSet(viewsets.ModelViewSet):
    serializer_class = TransaccionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['fecha', 'valor', 'created_at']

    def get_queryset(self):
        qs = Transaccion.objects.select_related('cuenta_origen', 'cuenta_destino').all()
        p = self.request.query_params

        fecha_desde = p.get('fecha_desde')
        fecha_hasta = p.get('fecha_hasta')

        if fecha_desde:
            qs = qs.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha__lte=fecha_hasta)

        return qs.order_by('-fecha')

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        agg = self.filter_queryset(self.get_queryset()).aggregate(total_valor=Sum('valor'))
        response.data['total_valor'] = str(agg['total_valor'] or 0)
        return response


class InversionCDTViewSet(viewsets.ModelViewSet):
    serializer_class = InversionCDTSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['fecha_inicio', 'fecha_vencimiento', 'monto', 'estado']

    def get_queryset(self):
        qs = InversionCDT.objects.select_related('cuenta_origen').all()
        estado = self.request.query_params.get('estado')
        if estado:
            qs = qs.filter(estado=estado)
        return qs.order_by('-fecha_inicio')

    @action(detail=True, methods=['post'])
    def liquidar(self, request, pk=None):
        cdt = self.get_object()
        if cdt.estado == 'liquidado':
            return Response({'error': 'Este CDT ya fue liquidado.'}, status=status.HTTP_400_BAD_REQUEST)

        rendimiento = request.data.get('rendimiento_real')
        fecha_liq = request.data.get('fecha_liquidacion') or date.today().isoformat()

        if rendimiento is None:
            rendimiento = cdt.rendimiento_proyectado

        total = cdt.monto + rendimiento

        Ingreso.objects.create(
            fecha=fecha_liq,
            descripcion=f"Liquidación CDT {cdt.entidad} — rendimiento",
            valor=rendimiento,
            cuenta_destino=cdt.cuenta_origen,
            origen=f"CDT #{cdt.id} — {cdt.entidad}",
        )
        Ingreso.objects.create(
            fecha=fecha_liq,
            descripcion=f"Liquidación CDT {cdt.entidad} — capital",
            valor=cdt.monto,
            cuenta_destino=cdt.cuenta_origen,
            origen=f"CDT #{cdt.id} — {cdt.entidad}",
        )

        cdt.estado = 'liquidado'
        cdt.rendimiento_real = rendimiento
        cdt.fecha_liquidacion = fecha_liq
        cdt.save(update_fields=['estado', 'rendimiento_real', 'fecha_liquidacion'])

        return Response({
            'ok': True,
            'rendimiento': str(rendimiento),
            'total': str(total),
        })


class ResumenView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.produccion.models import VentaCafe, VentaBanano
        from apps.nomina.models import Empleado
        from decimal import Decimal

        # ── Per-account flows (bulk queries, one pass each) ──────────────────
        def _agg(qs, group_field, value_field):
            return {
                row[group_field]: row['total']
                for row in qs.values(group_field).annotate(total=Sum(value_field))
                if row['total']
            }

        # Ingresos = fuente de verdad para todo: manuales + ventas (sincronizadas vía signals)
        ing_map      = _agg(Ingreso.objects.all(),                                       'cuenta_destino_id', 'valor')
        egr_map      = _agg(Egreso.objects.all(),                                        'cuenta_id',         'valor')
        # Pagos = Transacciones con cuenta_origen nula (pagos externos entrantes)
        pagos_map    = _agg(Transaccion.objects.filter(cuenta_origen__isnull=True),      'cuenta_destino_id', 'valor')
        # From = Transacciones entre cuentas internas (entrantes)
        from_map     = _agg(Transaccion.objects.filter(cuenta_origen__isnull=False),     'cuenta_destino_id', 'valor')
        # To = Transacciones salientes de esta cuenta
        to_map       = _agg(Transaccion.objects.filter(cuenta_origen__isnull=False),     'cuenta_origen_id',  'valor')

        D = Decimal
        cuentas = []
        saldo_total = D('0')

        for c in Cuenta.objects.filter(status=True).order_by('nombre'):
            cid = c.id
            ingresos_c  = D(str(ing_map.get(cid, 0)))
            egresos_c   = D(str(egr_map.get(cid, 0)))
            pagos_c     = D(str(pagos_map.get(cid, 0)))
            from_c      = D(str(from_map.get(cid, 0)))
            to_c        = D(str(to_map.get(cid, 0)))
            saldo_c     = c.saldo_inicial + ingresos_c - egresos_c + pagos_c + from_c - to_c

            cuentas.append({
                'nombre':   c.nombre,
                'tipo':     c.tipo,
                'saldo':    str(saldo_c),
                'ingresos': str(ingresos_c),
                'egresos':  str(egresos_c),
                'pagos':    str(pagos_c),
                'from':     str(from_c),
                'to':       str(to_c),
            })
            saldo_total += saldo_c

        # ── Global aggregates ─────────────────────────────────────────────────
        from apps.nomina.models import ControlSemanal
        from django.db.models import Q
        egresos_agg  = Egreso.objects.aggregate(total=Sum('valor'), count=Count('id'))
        ingresos_agg = Ingreso.objects.aggregate(total=Sum('valor'), count=Count('id'))
        # Ingresos manuales: los que no vienen de signals (origen null o vacío)
        ingresos_manuales_agg = Ingreso.objects.filter(
            Q(origen__isnull=True) | Q(origen='')
        ).aggregate(total=Sum('valor'), count=Count('id'))
        nomina_agg   = ControlSemanal.objects.aggregate(total=Sum('valor'), count=Count('id'))
        cafe_agg = VentaCafe.objects.aggregate(
            total_kilos=Sum('kilos'), total_valor=Sum('valor_neto'), count=Count('id')
        )
        banano_agg = VentaBanano.objects.aggregate(
            total_kilos=Sum('kilos'), total_valor=Sum('valor_total'), count=Count('id')
        )

        # ── Egresos por categoría ─────────────────────────────────────────────
        egresos_cat = list(
            Egreso.objects.values('categoria')
            .annotate(total=Sum('valor'), count=Count('id'))
            .order_by('-total')
        )

        # ── KPIs financieros ──────────────────────────────────────────────────
        # total_ingresos = ventas reales + ingresos manuales (evita doble conteo
        # cuando los signals crean Ingreso Y también existen entradas manuales para las mismas ventas)
        total_ingresos = (
            D(str(cafe_agg['total_valor'] or 0))
            + D(str(banano_agg['total_valor'] or 0))
            + D(str(ingresos_manuales_agg['total'] or 0))
        )
        total_costos = D(str(egresos_agg['total'] or 0))
        utilidad = total_ingresos - total_costos
        roi = round((utilidad / total_costos * 100), 2) if total_costos > 0 else D('0')
        cobertura = round((total_ingresos / total_costos * 100), 2) if total_costos > 0 else D('0')

        return Response({
            'cuentas': cuentas,
            'saldo_total': str(saldo_total),
            'egresos': {
                'total': str(egresos_agg['total'] or 0),
                'count': egresos_agg['count'],
            },
            'ingresos': {
                'total': str(ingresos_agg['total'] or 0),
                'count': ingresos_agg['count'],
            },
            'nomina': {
                'total': str(nomina_agg['total'] or 0),
                'count': nomina_agg['count'],
            },
            'ventas_cafe': {
                'total_kilos': str(cafe_agg['total_kilos'] or 0),
                'total_valor': str(cafe_agg['total_valor'] or 0),
                'count': cafe_agg['count'],
            },
            'ventas_banano': {
                'total_kilos': str(banano_agg['total_kilos'] or 0),
                'total_valor': str(banano_agg['total_valor'] or 0),
                'count': banano_agg['count'],
            },
            'egresos_por_categoria': [
                {'categoria': r['categoria'], 'total': str(r['total']), 'count': r['count']}
                for r in egresos_cat
            ],
            'empleados_activos': Empleado.objects.filter(activo=True).count(),
            'kpis': {
                'total_ingresos':  str(total_ingresos),
                'total_costos':    str(total_costos),
                'utilidad':        str(utilidad),
                'roi':             str(roi),
                'cobertura':       str(cobertura),
                'punto_equilibrio': str(total_costos),
                'ganando':         utilidad >= 0,
            },
        })


class GraficasView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.produccion.models import VentaCafe, VentaBanano
        from decimal import Decimal

        anio = request.query_params.get('anio')

        def _filter(qs, field='fecha'):
            if anio:
                qs = qs.filter(**{f'{field}__year': anio})
            return qs

        MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun',
                 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

        def _by_month(qs, date_field, value_field, label='total'):
            rows = (
                qs.annotate(mes=TruncMonth(date_field))
                .values('mes')
                .annotate(total=Sum(value_field))
                .order_by('mes')
            )
            return [
                {'mes': MESES[r['mes'].month - 1], 'mes_num': r['mes'].month, label: str(r['total'] or 0)}
                for r in rows if r['mes']
            ]

        # Café por mes (kilos y valor_neto)
        cafe_qs = _filter(VentaCafe.objects.all())
        cafe_mensual = (
            cafe_qs.annotate(mes=TruncMonth('fecha'))
            .values('mes')
            .annotate(kilos=Sum('kilos'), valor=Sum('valor_neto'))
            .order_by('mes')
        )
        cafe_mensual_data = [
            {
                'mes': MESES[r['mes'].month - 1],
                'mes_num': r['mes'].month,
                'kilos': str(r['kilos'] or 0),
                'valor': str(r['valor'] or 0),
            }
            for r in cafe_mensual if r['mes']
        ]

        # Banano por mes
        banano_qs = _filter(VentaBanano.objects.all())
        banano_mensual = (
            banano_qs.annotate(mes=TruncMonth('fecha'))
            .values('mes')
            .annotate(kilos=Sum('kilos'), valor=Sum('valor_total'))
            .order_by('mes')
        )
        banano_mensual_data = [
            {
                'mes': MESES[r['mes'].month - 1],
                'mes_num': r['mes'].month,
                'kilos': str(r['kilos'] or 0),
                'valor': str(r['valor'] or 0),
            }
            for r in banano_mensual if r['mes']
        ]

        # Ingresos por mes
        ing_mensual = _by_month(_filter(Ingreso.objects.all()), 'fecha', 'valor', 'valor')

        # Egresos por mes
        egr_mensual = _by_month(_filter(Egreso.objects.all()), 'fecha', 'valor', 'valor')

        # Ventas café detalle por fecha (para gráfica de cargas y precio)
        cafe_detalle = list(
            cafe_qs
            .exclude(tipo_cafe__in=['pasilla', 'corriente'])
            .order_by('fecha')
            .values('fecha', 'cargas', 'precio_kilo', 'tipo_cafe', 'kilos', 'valor_neto')
        )
        cafe_detalle_data = [
            {
                'fecha': str(r['fecha']),
                'cargas': str(r['cargas'] or 0),
                'precio_kilo': str(r['precio_kilo'] or 0),
                'tipo_cafe': r['tipo_cafe'],
                'kilos': str(r['kilos'] or 0),
                'valor_neto': str(r['valor_neto'] or 0),
            }
            for r in cafe_detalle
        ]

        # Totales para pie chart de ingresos
        D = Decimal
        total_cafe = D(str(cafe_qs.aggregate(t=Sum('valor_neto'))['t'] or 0))
        total_banano = D(str(banano_qs.aggregate(t=Sum('valor_total'))['t'] or 0))
        total_ingresos = D(str(_filter(Ingreso.objects.all()).aggregate(t=Sum('valor'))['t'] or 0))

        return Response({
            'cafe_mensual': cafe_mensual_data,
            'banano_mensual': banano_mensual_data,
            'ingresos_mensual': ing_mensual,
            'egresos_mensual': egr_mensual,
            'cafe_detalle': cafe_detalle_data,
            'totales_ingresos': {
                'cafe': str(total_cafe),
                'banano': str(total_banano),
                'otros': str(total_ingresos),
            },
        })
