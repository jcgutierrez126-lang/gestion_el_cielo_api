import base64
import json
import anthropic as _anthropic
from django.db import transaction
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from django.db.models import Sum
from django.db.models.functions import TruncWeek, TruncMonth, TruncYear
from .models import (
    TipoBanano, TipoCafe, VariedadLote,
    Lote, VentaCafe, VentaCafeTostado, VentaBanano,
    Floracion, MezclaAbono,
)
from .serializers import (
    TipoBananoSerializer, TipoCafeSerializer, VariedadLoteSerializer,
    LoteSerializer, VentaCafeSerializer, VentaCafeTostadoSerializer,
    VentaBananoSerializer, FloracionSerializer, MezclaAbonoSerializer,
)


class TipoBananoViewSet(viewsets.ModelViewSet):
    serializer_class = TipoBananoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['nombre']

    def get_queryset(self):
        qs = TipoBanano.objects.all()
        activo = self.request.query_params.get('activo')
        if activo is not None:
            qs = qs.filter(status=activo.lower() == 'true')
        return qs.order_by('nombre')


class TipoCafeViewSet(viewsets.ModelViewSet):
    serializer_class = TipoCafeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['nombre']

    def get_queryset(self):
        qs = TipoCafe.objects.all()
        activo = self.request.query_params.get('activo')
        if activo is not None:
            qs = qs.filter(status=activo.lower() == 'true')
        return qs.order_by('nombre')


class VariedadLoteViewSet(viewsets.ModelViewSet):
    serializer_class = VariedadLoteSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['nombre']

    def get_queryset(self):
        return VariedadLote.objects.all().order_by('nombre')


class LoteViewSet(viewsets.ModelViewSet):
    serializer_class = LoteSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
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
        qs = VentaCafe.objects.select_related('cuenta_destino', 'tipo_cafe').all()
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
            qs = qs.filter(tipo_cafe_id=tipo_cafe)
        if cuenta:
            qs = qs.filter(cuenta_destino_id=cuenta)

        return qs.order_by('-fecha')

    @action(detail=False, methods=['get'])
    def por_periodo(self, request):
        grupo = request.query_params.get('grupo', 'mes')
        qs = self.get_queryset()
        if grupo == 'semana':
            qs = qs.annotate(periodo=TruncWeek('fecha'))
        elif grupo == 'año':
            qs = qs.annotate(periodo=TruncYear('fecha'))
        else:
            qs = qs.annotate(periodo=TruncMonth('fecha'))
        rows = qs.values('periodo').annotate(valor=Sum('valor_neto')).order_by('periodo')
        result = []
        for row in rows:
            p = row['periodo']
            label = p.strftime('%G-S%V') if grupo == 'semana' else p.strftime('%Y') if grupo == 'año' else p.strftime('%Y-%m')
            result.append({'periodo': label, 'valor': float(row['valor'] or 0)})
        return Response(result)

    @action(detail=False, methods=['get'])
    def por_tipo(self, request):
        qs = self.get_queryset()
        rows = qs.values('tipo_cafe__id', 'tipo_cafe__nombre').annotate(
            valor=Sum('valor_neto')
        ).order_by('-valor')
        return Response([
            {'tipo_id': r['tipo_cafe__id'], 'nombre': r['tipo_cafe__nombre'], 'valor': float(r['valor'] or 0)}
            for r in rows
        ])

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    def parse_factura(self, request):
        imagen = request.FILES.get('imagen')
        if not imagen:
            return Response({'error': 'Se requiere una imagen'}, status=400)

        image_data = base64.standard_b64encode(imagen.read()).decode('utf-8')
        media_type = imagen.content_type or 'image/jpeg'

        try:
            client = _anthropic.Anthropic()
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {"type": "base64", "media_type": media_type, "data": image_data},
                        },
                        {
                            "type": "text",
                            "text": (
                                "Esta es una factura de compra de café (COF) de una cooperativa colombiana.\n"
                                "Extrae los datos y responde SOLO con JSON válido, sin texto ni markdown extra:\n"
                                "{\n"
                                '  "fecha": "YYYY-MM-DD",\n'
                                '  "comprador": "nombre completo de la cooperativa del encabezado",\n'
                                '  "factura": "número de factura",\n'
                                '  "items": [\n'
                                '    {"descripcion": "texto del artículo", "kilos": 128.0, "precio_kilo": 24800.0, "valor_total": 3174400}\n'
                                '  ],\n'
                                '  "retenciones": 0.0,\n'
                                '  "total": 3174400.0\n'
                                "}\n"
                                "La fecha está en el campo FECHA (formato dd-mes-aa → YYYY-MM-DD). "
                                "Columna CANT = kilos, COSTO = precio_kilo. "
                                "Retenciones viene del resumen inferior. "
                                "Números sin puntos de miles ni símbolos."
                            ),
                        },
                    ],
                }],
            )
        except _anthropic.BadRequestError as e:
            return Response({'error': str(e)}, status=502)
        except _anthropic.APIError as e:
            return Response({'error': f'Error del servicio de IA: {e}'}, status=502)

        text = message.content[0].text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        data = json.loads(text)
        return Response(data)

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        items = request.data.get('items', [])
        if not items:
            return Response({'error': 'Se requieren items'}, status=400)

        serializers_list = []
        for item in items:
            s = VentaCafeSerializer(data=item)
            s.is_valid(raise_exception=True)
            serializers_list.append(s)

        with transaction.atomic():
            created = [s.save() for s in serializers_list]

        return Response(VentaCafeSerializer(created, many=True).data, status=201)


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
        qs = VentaBanano.objects.select_related('cuenta_destino', 'tipo_platano').all()
        p = self.request.query_params

        fecha_desde = p.get('fecha_desde')
        fecha_hasta = p.get('fecha_hasta')
        tipo_platano = p.get('tipo_platano')

        if fecha_desde:
            qs = qs.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha__lte=fecha_hasta)
        if tipo_platano:
            qs = qs.filter(tipo_platano_id=tipo_platano)

        return qs.order_by('-fecha')

    @action(detail=False, methods=['get'])
    def por_periodo(self, request):
        grupo = request.query_params.get('grupo', 'mes')
        qs = self.get_queryset()
        if grupo == 'semana':
            qs = qs.annotate(periodo=TruncWeek('fecha'))
        elif grupo == 'año':
            qs = qs.annotate(periodo=TruncYear('fecha'))
        else:
            qs = qs.annotate(periodo=TruncMonth('fecha'))
        rows = qs.values('periodo').annotate(valor=Sum('valor_total')).order_by('periodo')
        result = []
        for row in rows:
            p = row['periodo']
            label = p.strftime('%G-S%V') if grupo == 'semana' else p.strftime('%Y') if grupo == 'año' else p.strftime('%Y-%m')
            result.append({'periodo': label, 'valor': float(row['valor'] or 0)})
        return Response(result)

    @action(detail=False, methods=['get'])
    def por_tipo(self, request):
        qs = self.get_queryset()
        rows = qs.values('tipo_platano__id', 'tipo_platano__nombre').annotate(
            valor=Sum('valor_total')
        ).order_by('-valor')
        return Response([
            {'tipo_id': r['tipo_platano__id'], 'nombre': r['tipo_platano__nombre'], 'valor': float(r['valor'] or 0)}
            for r in rows
        ])

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    def parse_factura(self, request):
        imagen = request.FILES.get('imagen')
        if not imagen:
            return Response({'error': 'Se requiere una imagen'}, status=400)

        image_data = base64.standard_b64encode(imagen.read()).decode('utf-8')
        media_type = imagen.content_type or 'image/jpeg'

        try:
            client = _anthropic.Anthropic()
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {"type": "base64", "media_type": media_type, "data": image_data},
                        },
                        {
                            "type": "text",
                            "text": (
                                "Esta es una factura de liquidación de banano de la Cooperativa COMSAB (Colombia).\n"
                                "Extrae los datos y responde SOLO con JSON válido, sin texto ni markdown extra:\n"
                                "{\n"
                                '  "fecha": "YYYY-MM-DD",\n'
                                '  "items": [\n'
                                '    {"descripcion": "texto exacto de la columna Descripción", "kilos": 253.25, "precio_kilo": 1600.0, "valor_total": 405200}\n'
                                '  ],\n'
                                '  "deducciones": [{"concepto": "nombre exacto", "valor": 2341}],\n'
                                '  "total_pagos": 2256418,\n'
                                '  "total_a_pagar": 2208949\n'
                                "}\n"
                                "La fecha es 'Fecha Liquidación', formato YYYY-MM-DD. "
                                "Columna Cantidad = kilos, Valor Unitario = precio_kilo. "
                                "Los números sin puntos de miles ni símbolos de moneda."
                            ),
                        },
                    ],
                }],
            )
        except _anthropic.BadRequestError as e:
            return Response({'error': str(e)}, status=502)
        except _anthropic.APIError as e:
            return Response({'error': f'Error del servicio de IA: {e}'}, status=502)

        text = message.content[0].text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        data = json.loads(text)
        return Response(data)

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        items = request.data.get('items', [])
        if not items:
            return Response({'error': 'Se requieren items'}, status=400)

        serializers_list = []
        for item in items:
            s = VentaBananoSerializer(data=item)
            s.is_valid(raise_exception=True)
            serializers_list.append(s)

        with transaction.atomic():
            created = [s.save() for s in serializers_list]

        return Response(VentaBananoSerializer(created, many=True).data, status=201)


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
