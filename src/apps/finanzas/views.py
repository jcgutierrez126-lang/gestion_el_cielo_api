from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from .models import Cuenta, Proveedor, Egreso, Ingreso, Transaccion, Observacion
from .serializers import (
    CuentaSerializer, ProveedorSerializer, EgresoSerializer,
    IngresoSerializer, TransaccionSerializer, ObservacionSerializer,
)


class CuentaViewSet(viewsets.ModelViewSet):
    queryset = Cuenta.objects.all().order_by('nombre')
    serializer_class = CuentaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'tipo']
    ordering_fields = ['nombre', 'tipo', 'created_at']


class ProveedorViewSet(viewsets.ModelViewSet):
    serializer_class = ProveedorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'cedula_nit', 'ciudad', 'email']
    ordering_fields = ['nombre', 'ciudad', 'created_at']

    def get_queryset(self):
        qs = Proveedor.objects.all()
        ciudad = self.request.query_params.get('ciudad')
        if ciudad:
            qs = qs.filter(ciudad__icontains=ciudad)
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


class ObservacionViewSet(viewsets.ModelViewSet):
    serializer_class = ObservacionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['fecha', 'created_at']

    def get_queryset(self):
        qs = Observacion.objects.all()
        p = self.request.query_params

        fecha_desde = p.get('fecha_desde')
        fecha_hasta = p.get('fecha_hasta')

        if fecha_desde:
            qs = qs.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha__lte=fecha_hasta)

        return qs.order_by('-fecha')
