from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from .models import (
    Lote, VentaCafe, VentaCafeTostado, VentaBanano,
    Floracion, MezclaAbono,
)
from .serializers import (
    LoteSerializer, VentaCafeSerializer, VentaCafeTostadoSerializer,
    VentaBananoSerializer, FloracionSerializer, MezclaAbonoSerializer,
)


class LoteViewSet(viewsets.ModelViewSet):
    serializer_class = LoteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'variedad']
    ordering_fields = ['nombre', 'num_arboles', 'created_at']

    def get_queryset(self):
        qs = Lote.objects.all()
        activo = self.request.query_params.get('activo')
        if activo is not None:
            qs = qs.filter(activo=activo.lower() == 'true')
        return qs.order_by('nombre')


class VentaCafeViewSet(viewsets.ModelViewSet):
    serializer_class = VentaCafeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['comprador', 'beneficio', 'transportador', 'facturado_a']
    ordering_fields = ['fecha', 'kilos', 'valor_neto', 'tipo_cafe', 'created_at']

    def get_queryset(self):
        qs = VentaCafe.objects.select_related('cuenta_destino').all()
        p = self.request.query_params

        fecha_desde = p.get('fecha_desde')
        fecha_hasta = p.get('fecha_hasta')
        tipo_cafe = p.get('tipo_cafe')
        cuenta = p.get('cuenta_destino')

        if fecha_desde:
            qs = qs.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha__lte=fecha_hasta)
        if tipo_cafe:
            qs = qs.filter(tipo_cafe=tipo_cafe)
        if cuenta:
            qs = qs.filter(cuenta_destino_id=cuenta)

        return qs.order_by('-fecha')


class VentaCafeTostadoViewSet(viewsets.ModelViewSet):
    serializer_class = VentaCafeTostadoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['cliente']
    ordering_fields = ['fecha_venta', 'valor', 'presentacion', 'created_at']

    def get_queryset(self):
        qs = VentaCafeTostado.objects.select_related('cuenta_destino').all()
        p = self.request.query_params

        fecha_desde = p.get('fecha_desde')
        fecha_hasta = p.get('fecha_hasta')
        presentacion = p.get('presentacion')

        if fecha_desde:
            qs = qs.filter(fecha_venta__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha_venta__lte=fecha_hasta)
        if presentacion:
            qs = qs.filter(presentacion=presentacion)

        return qs.order_by('-fecha_venta')


class VentaBananoViewSet(viewsets.ModelViewSet):
    serializer_class = VentaBananoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['facturado_a', 'observaciones']
    ordering_fields = ['fecha', 'kilos', 'valor_total', 'tipo_platano', 'created_at']

    def get_queryset(self):
        qs = VentaBanano.objects.select_related('cuenta_destino').all()
        p = self.request.query_params

        fecha_desde = p.get('fecha_desde')
        fecha_hasta = p.get('fecha_hasta')
        tipo_platano = p.get('tipo_platano')

        if fecha_desde:
            qs = qs.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha__lte=fecha_hasta)
        if tipo_platano:
            qs = qs.filter(tipo_platano=tipo_platano)

        return qs.order_by('-fecha')


class FloracionViewSet(viewsets.ModelViewSet):
    serializer_class = FloracionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['fecha', 'calidad', 'created_at']

    def get_queryset(self):
        qs = Floracion.objects.select_related('lote').all()
        p = self.request.query_params

        fecha_desde = p.get('fecha_desde')
        fecha_hasta = p.get('fecha_hasta')
        lote = p.get('lote')
        calidad = p.get('calidad')

        if fecha_desde:
            qs = qs.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha__lte=fecha_hasta)
        if lote:
            qs = qs.filter(lote_id=lote)
        if calidad:
            qs = qs.filter(calidad=calidad)

        return qs.order_by('-fecha')


class MezclaAbonoViewSet(viewsets.ModelViewSet):
    serializer_class = MezclaAbonoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['formula']
    ordering_fields = ['fecha', 'costo_total', 'created_at']

    def get_queryset(self):
        qs = MezclaAbono.objects.select_related('lote').prefetch_related('fertilizantes').all()
        p = self.request.query_params

        fecha_desde = p.get('fecha_desde')
        fecha_hasta = p.get('fecha_hasta')
        lote = p.get('lote')

        if fecha_desde:
            qs = qs.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha__lte=fecha_hasta)
        if lote:
            qs = qs.filter(lote_id=lote)

        return qs.order_by('-fecha')
