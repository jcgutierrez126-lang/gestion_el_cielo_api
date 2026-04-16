from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.integraciones.authentication import IsAPIKeyAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.db import transaction

from apps.integraciones.models import (
    Pedido,
    TrazabilidadPedido,
    LogConsulta,
    CorreoAutorizado,
    CorreoProcesado,
)
from apps.integraciones.api.serializers import (
    PedidoSerializer,
    PedidoListSerializer,
    BuscarPedidoRequestSerializer,
    LogConsultaSerializer,
    ActualizarPedidoSerializer,
    TrazabilidadPedidoSerializer,
    CorreoAutorizadoSerializer,
    CorreoProcesadoSerializer,
)
from apps.integraciones.services.consolidation_service import ConsolidationService

PEDIDO_NO_ENCONTRADO = "Pedido no encontrado"
CORREO_NO_ENCONTRADO = "Correo no encontrado"


class PedidoPagination(PageNumberPagination):
    """Paginacion para listado de pedidos."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class BuscarPedidoAPIView(APIView):
    """
    POST /api/pedidos/buscar/

    Busca un pedido en Supplos y Graph, consolida la informacion
    y la almacena en base de datos.

    Request body:
    {
        "numero_pedido": 4501833743,
        "empresas": ["corona", "alion"],  // opcional
        "buscar_correos": true  // opcional
    }
    """
    permission_classes = [IsAPIKeyAuthenticated]

    def post(self, request):
        serializer = BuscarPedidoRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        numero_pedido = serializer.validated_data['numero_pedido']
        empresas = serializer.validated_data.get('empresas', ['corona', 'alion'])
        buscar_correos = serializer.validated_data.get('buscar_correos', True)

        try:
            # Ejecutar consolidacion
            service = ConsolidationService(user=request.user)
            resultado = service.buscar_y_consolidar(
                numero_pedido=numero_pedido,
                empresas=empresas,
                buscar_correos=buscar_correos
            )

            # Obtener pedidos guardados para incluir en respuesta
            pedidos = Pedido.objects.filter(
                documento_compras=str(numero_pedido)
            ).prefetch_related('trazabilidad')
            pedidos_data = PedidoSerializer(pedidos, many=True).data
            resultado['pedidos'] = pedidos_data

            return Response(resultado, status=status.HTTP_200_OK)

        except Exception:
            return Response(
                {"detail": "Error procesando solicitud. Intente nuevamente."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PedidoListAPIView(ListAPIView):
    """
    GET /api/pedidos/

    Lista paginada de todos los pedidos guardados.
    Soporta busqueda y filtros.

    Query params:
    - search: busqueda general
    - estado: filtrar por estado
    - fecha_desde, fecha_hasta: filtrar por rango de fechas
    - fuente: supplos, graph, ambos
    """
    serializer_class = PedidoListSerializer
    pagination_class = PedidoPagination
    permission_classes = [IsAPIKeyAuthenticated]

    def get_queryset(self):
        queryset = Pedido.objects.filter(status=True)

        # Filtro por busqueda general
        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(documento_compras__icontains=search) |
                Q(razon_social__icontains=search) |
                Q(material__icontains=search) |
                Q(texto_breve__icontains=search) |
                Q(comprador__icontains=search) |
                Q(proveedor_centro_suministrador__icontains=search)
            )

        # Filtro por estado
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado_pedido=estado)

        # Filtro por rango de fechas
        fecha_desde = self.request.query_params.get('fecha_desde')
        fecha_hasta = self.request.query_params.get('fecha_hasta')
        if fecha_desde:
            queryset = queryset.filter(fecha_entrega__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_entrega__lte=fecha_hasta)

        # Filtro por fuente de datos
        fuente = self.request.query_params.get('fuente')
        if fuente == 'supplos':
            queryset = queryset.filter(fuente_supplos=True)
        elif fuente == 'graph':
            queryset = queryset.filter(fuente_graph=True)
        elif fuente == 'ambos':
            queryset = queryset.filter(fuente_supplos=True, fuente_graph=True)

        return queryset.order_by('-created_at')


class PedidoDetailAPIView(APIView):
    """
    GET /api/pedidos/<numero_pedido>/

    Obtiene el detalle de un pedido por su numero de documento.
    Incluye trazabilidad historica.
    """
    permission_classes = [IsAPIKeyAuthenticated]

    def get(self, request, numero_pedido):
        # Obtener todos los pedidos con ese numero (diferentes posiciones)
        pedidos = Pedido.objects.filter(
            documento_compras=numero_pedido,
            status=True
        ).prefetch_related('trazabilidad').order_by('posicion')

        if not pedidos.exists():
            return Response(
                {"detail": PEDIDO_NO_ENCONTRADO},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PedidoSerializer(pedidos, many=True)
        return Response(serializer.data)


class PedidoByIdAPIView(RetrieveAPIView):
    """
    GET /api/pedidos/detalle/<id>/

    Obtiene el detalle de un pedido por su ID interno.
    """
    serializer_class = PedidoSerializer
    permission_classes = [IsAPIKeyAuthenticated]
    queryset = Pedido.objects.filter(status=True).prefetch_related('trazabilidad')
    lookup_field = 'pk'


class PedidoUpdateAPIView(APIView):
    """
    PATCH /api/pedidos/<id>/actualizar/

    Actualiza campos editables de un pedido (observaciones Corona).
    """
    permission_classes = [IsAPIKeyAuthenticated]

    def patch(self, request, pk):
        try:
            pedido = Pedido.objects.get(pk=pk, status=True)
        except Pedido.DoesNotExist:
            return Response(
                {"detail": PEDIDO_NO_ENCONTRADO},
                status=status.HTTP_404_NOT_FOUND
            )

        # Guardar estado anterior para trazabilidad
        estado_anterior = pedido.estado_pedido

        serializer = ActualizarPedidoSerializer(
            pedido,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()

            # Registrar en trazabilidad si hubo cambio de estado
            if 'estado_pedido' in request.data and request.data['estado_pedido'] != estado_anterior:
                TrazabilidadPedido.objects.create(
                    pedido=pedido,
                    fuente=TrazabilidadPedido.FuenteDatos.MANUAL,
                    estado_anterior=estado_anterior,
                    estado_nuevo=pedido.estado_pedido,
                    observaciones=f"Actualizado manualmente. {request.data.get('observaciones_corona', '')}"
                )

            return Response(PedidoSerializer(pedido).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResincronizarPedidoAPIView(APIView):
    """
    POST /api/pedidos/<numero_pedido>/resincronizar/

    Vuelve a buscar y actualizar la informacion de un pedido.
    """
    permission_classes = [IsAPIKeyAuthenticated]

    def post(self, request, numero_pedido):
        try:
            service = ConsolidationService(user=request.user)
            try:
                numero_pedido_int = int(numero_pedido)
            except (ValueError, TypeError):
                return Response(
                    {"detail": "El número de pedido debe ser numérico."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            resultado = service.buscar_y_consolidar(
                numero_pedido=numero_pedido_int,
                buscar_correos=request.data.get('buscar_correos', True)
            )

            # Obtener pedidos actualizados
            pedidos = Pedido.objects.filter(
                documento_compras=numero_pedido
            ).prefetch_related('trazabilidad')
            resultado['pedidos'] = PedidoSerializer(pedidos, many=True).data

            return Response(resultado, status=status.HTTP_200_OK)

        except Exception:
            return Response(
                {"detail": "Error resincronizando el pedido. Intente nuevamente."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TrazabilidadPedidoAPIView(APIView):
    """
    GET /api/pedidos/<numero_pedido>/trazabilidad/

    Obtiene el historial completo de trazabilidad de un pedido.
    """
    permission_classes = [IsAPIKeyAuthenticated]

    def get(self, request, numero_pedido):
        # Obtener todos los pedidos con ese numero
        pedidos = Pedido.objects.filter(
            documento_compras=numero_pedido,
            status=True
        )

        if not pedidos.exists():
            return Response(
                {"detail": PEDIDO_NO_ENCONTRADO},
                status=status.HTTP_404_NOT_FOUND
            )

        # Obtener toda la trazabilidad de esos pedidos
        trazabilidad = TrazabilidadPedido.objects.filter(
            pedido__in=pedidos
        ).order_by('-fecha_registro')

        serializer = TrazabilidadPedidoSerializer(trazabilidad, many=True)

        return Response({
            "documento_compras": numero_pedido,
            "total_registros": trazabilidad.count(),
            "trazabilidad": serializer.data
        })


class LogConsultaListAPIView(ListAPIView):
    """
    GET /api/pedidos/logs/

    Lista de logs de consultas realizadas.
    """
    serializer_class = LogConsultaSerializer
    pagination_class = PedidoPagination
    permission_classes = [IsAPIKeyAuthenticated]

    def get_queryset(self):
        queryset = LogConsulta.objects.all()

        # Filtro por tipo
        tipo = self.request.query_params.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo=tipo)

        # Filtro por estado
        exitosa = self.request.query_params.get('exitosa')
        if exitosa is not None:
            queryset = queryset.filter(respuesta_exitosa=exitosa.lower() == 'true')

        return queryset.order_by('-created_at')


class EstadisticasPedidosAPIView(APIView):
    """
    GET /api/pedidos/estadisticas/

    Obtiene estadisticas generales de pedidos.
    """
    permission_classes = [IsAPIKeyAuthenticated]

    def get(self, request):
        from django.db.models import Count, Sum

        total = Pedido.objects.filter(status=True).count()

        por_estado = Pedido.objects.filter(status=True).values(
            'estado_pedido'
        ).annotate(
            cantidad=Count('id')
        )

        por_fuente = {
            'solo_supplos': Pedido.objects.filter(
                fuente_supplos=True,
                fuente_graph=False,
                status=True
            ).count(),
            'solo_graph': Pedido.objects.filter(
                fuente_supplos=False,
                fuente_graph=True,
                status=True
            ).count(),
            'ambas_fuentes': Pedido.objects.filter(
                fuente_supplos=True,
                fuente_graph=True,
                status=True
            ).count(),
        }

        return Response({
            'total_pedidos': total,
            'por_estado': list(por_estado),
            'por_fuente': por_fuente,
        })


# =============================================
# VISTAS PARA CORREOS AUTORIZADOS
# =============================================

class CorreoAutorizadoListCreateAPIView(APIView):
    """
    GET /api/pedidos/correos/
    Lista todos los correos autorizados.

    POST /api/pedidos/correos/
    Crea un nuevo correo autorizado.
    """
    permission_classes = [IsAPIKeyAuthenticated]

    def get(self, request):
        correos = CorreoAutorizado.objects.all().order_by('-es_buzon_principal', 'email')
        serializer = CorreoAutorizadoSerializer(correos, many=True)
        return Response({
            "total": correos.count(),
            "correos": serializer.data
        })

    def post(self, request):
        serializer = CorreoAutorizadoSerializer(data=request.data)

        if serializer.is_valid():
            with transaction.atomic():
                if serializer.validated_data.get('es_buzon_principal', False):
                    CorreoAutorizado.objects.filter(es_buzon_principal=True).update(es_buzon_principal=False)
                serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CorreoAutorizadoDetailAPIView(APIView):
    """
    GET /api/pedidos/correos/<id>/
    Obtiene detalle de un correo autorizado.

    PUT /api/pedidos/correos/<id>/
    Actualiza un correo autorizado.

    DELETE /api/pedidos/correos/<id>/
    Elimina un correo autorizado.
    """
    permission_classes = [IsAPIKeyAuthenticated]

    def get_object(self, pk):
        try:
            return CorreoAutorizado.objects.get(pk=pk)
        except CorreoAutorizado.DoesNotExist:
            return None

    def get(self, request, pk):
        correo = self.get_object(pk)
        if not correo:
            return Response(
                {"detail": CORREO_NO_ENCONTRADO},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = CorreoAutorizadoSerializer(correo)
        return Response(serializer.data)

    def put(self, request, pk):
        correo = self.get_object(pk)
        if not correo:
            return Response(
                {"detail": CORREO_NO_ENCONTRADO},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CorreoAutorizadoSerializer(correo, data=request.data)

        if serializer.is_valid():
            # Si se marca como principal, desmarcar los demas
            if serializer.validated_data.get('es_buzon_principal', False):
                CorreoAutorizado.objects.filter(es_buzon_principal=True).exclude(pk=pk).update(es_buzon_principal=False)

            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        correo = self.get_object(pk)
        if not correo:
            return Response(
                {"detail": CORREO_NO_ENCONTRADO},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CorreoAutorizadoSerializer(correo, data=request.data, partial=True)

        if serializer.is_valid():
            # Si se marca como principal, desmarcar los demas
            if serializer.validated_data.get('es_buzon_principal', False):
                CorreoAutorizado.objects.filter(es_buzon_principal=True).exclude(pk=pk).update(es_buzon_principal=False)

            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        correo = self.get_object(pk)
        if not correo:
            return Response(
                {"detail": CORREO_NO_ENCONTRADO},
                status=status.HTTP_404_NOT_FOUND
            )

        correo.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CorreosProcesadosListAPIView(ListAPIView):
    """
    GET /api/pedidos/correos-procesados/

    Lista los correos que ya fueron procesados (para evitar duplicados).
    """
    serializer_class = CorreoProcesadoSerializer
    pagination_class = PedidoPagination
    permission_classes = [IsAPIKeyAuthenticated]

    def get_queryset(self):
        queryset = CorreoProcesado.objects.all()

        # Filtro por buzon
        buzon = self.request.query_params.get('buzon')
        if buzon:
            queryset = queryset.filter(buzon__icontains=buzon)

        # Filtro por fecha
        fecha_desde = self.request.query_params.get('fecha_desde')
        if fecha_desde:
            queryset = queryset.filter(procesado_at__gte=fecha_desde)

        return queryset.order_by('-procesado_at')


class TestGraphSearchAPIView(APIView):
    """
    GET /api/pedidos/test-graph/<numero_pedido>/

    Endpoint de prueba para verificar la busqueda de correos en Graph.
    Muestra todos los detalles de la consulta para depuracion.
    """
    permission_classes = [IsAPIKeyAuthenticated]

    def get(self, request, numero_pedido):
        from apps.integraciones.services.graph_search_service import GraphSearchService, GraphSearchException
        import traceback

        resultado = {
            "numero_pedido": numero_pedido,
            "pasos": [],
            "errores": [],
            "correos_encontrados": [],
            "debug_info": {}
        }

        try:
            service = GraphSearchService()

            # Paso 1: Verificar buzones configurados
            buzones = service._get_buzones_autorizados()
            resultado["pasos"].append({
                "paso": 1,
                "descripcion": "Obtener buzones autorizados",
                "resultado": buzones if buzones else "NO HAY BUZONES CONFIGURADOS"
            })
            resultado["debug_info"]["buzones"] = buzones

            if not buzones:
                resultado["errores"].append(
                    "No hay buzones configurados. Ve a /admin/integraciones/correoautorizado/ y agrega al menos uno."
                )
                return Response(resultado, status=status.HTTP_200_OK)

            # Paso 2: Obtener token
            try:
                service._get_token()
                resultado["pasos"].append({
                    "paso": 2,
                    "descripcion": "Obtener token de Graph API",
                    "resultado": "OK - Token obtenido correctamente"
                })
            except Exception as e:
                resultado["pasos"].append({
                    "paso": 2,
                    "descripcion": "Obtener token de Graph API",
                    "resultado": f"ERROR: {str(e)}"
                })
                resultado["errores"].append(f"Error obteniendo token: {str(e)}")
                return Response(resultado, status=status.HTTP_200_OK)

            # Paso 3: Buscar correos
            resultado["pasos"].append({
                "paso": 3,
                "descripcion": "Buscar correos en Graph API",
                "resultado": "Iniciando busqueda..."
            })

            # Buscar todos los correos con el pedido en el asunto
            correos_result = service.buscar_correos_por_pedido(
                numero_pedido=str(numero_pedido),
                max_results=20
            )

            resultado["debug_info"]["graph_response"] = {
                "status": correos_result.get("status"),
                "total": correos_result.get("total"),
                "message": correos_result.get("message"),
                "buzones_consultados": correos_result.get("buzones_consultados")
            }

            if correos_result.get("status") == "OK":
                resultado["pasos"].append({
                    "paso": 4,
                    "descripcion": "Procesar resultados",
                    "resultado": f"Encontrados {correos_result.get('total', 0)} correos"
                })

                # Agregar detalles de cada correo
                for correo in correos_result.get("data", []):
                    resultado["correos_encontrados"].append({
                        "subject": correo.get("subject"),
                        "from": correo.get("from"),
                        "from_name": correo.get("from_name"),
                        "received_date": str(correo.get("received_date")) if correo.get("received_date") else None,
                        "body_preview": correo.get("body_preview", "")[:200] + "..." if correo.get("body_preview") else None,
                        "observaciones_proveedor": correo.get("observaciones_proveedor"),
                        "observaciones_corona": correo.get("observaciones_corona"),
                        "posiciones_correo": correo.get("posiciones_correo", []),
                        "datos_extraidos": correo.get("datos_extraidos")
                    })
            else:
                resultado["errores"].append(correos_result.get("message", "Error desconocido"))

        except GraphSearchException as e:
            resultado["errores"].append(f"GraphSearchException: {str(e)}")
            resultado["debug_info"]["traceback"] = traceback.format_exc()
        except Exception as e:
            resultado["errores"].append(f"Exception: {str(e)}")
            resultado["debug_info"]["traceback"] = traceback.format_exc()

        return Response(resultado, status=status.HTTP_200_OK)


class PedidoUnificadoAPIView(APIView):
    """
    POST /api/pedidos/consultar/

    Endpoint unificado para consultar/crear/actualizar pedidos.
    Soporta modo asincrono con Celery para no bloquear workers.

    Request body:
    {
        "numero_pedido": 4501833743,
        "empresas": ["corona", "alion"],      // opcional
        "buscar_correos": true,               // opcional
        "forzar_busqueda": false,             // opcional
        "async": false,                       // opcional, default: false
        // Campos opcionales para actualizar si ya existe:
        "estado_pedido": "Entregado",
        "motivo": "Entregado completo",
        "observaciones_corona": "Verificado"
    }

    Si async=true y necesita consolidacion:
    Response 202:
    {
        "task_id": "abc-123",
        "status": "PENDING",
        "numero_pedido": "4501833743"
    }
    Luego consultar: GET /api/pedidos/tarea/{task_id}/
    """
    permission_classes = [IsAPIKeyAuthenticated]

    def post(self, request):
        numero_pedido = request.data.get('numero_pedido')

        if not numero_pedido:
            return Response(
                {"detail": "numero_pedido es requerido"},
                status=status.HTTP_400_BAD_REQUEST
            )

        numero_pedido_str = str(numero_pedido)
        empresas = request.data.get('empresas', ['corona', 'alion'])
        buscar_correos = request.data.get('buscar_correos', True)
        forzar_busqueda = request.data.get('forzar_busqueda', False)
        usar_async = request.data.get('async', False)

        campos_actualizacion = {
            campo: request.data[campo]
            for campo in ['estado_pedido', 'motivo', 'observaciones_corona']
            if campo in request.data
        }

        resultado = {
            "numero_pedido": numero_pedido_str,
            "accion": None,
            "pedidos": [],
            "trazabilidad": [],
            "fuentes_consultadas": None
        }

        try:
            pedidos_existentes = Pedido.objects.filter(
                documento_compras=numero_pedido_str,
                status=True
            ).prefetch_related('trazabilidad')

            pedido_existe = pedidos_existentes.exists()

            if not pedido_existe or forzar_busqueda:
                respuesta_async = self._procesar_busqueda(
                    request, numero_pedido_str, numero_pedido,
                    empresas, buscar_correos, usar_async, pedido_existe, resultado
                )
                if respuesta_async:
                    return respuesta_async
                pedidos_existentes = Pedido.objects.filter(
                    documento_compras=numero_pedido_str, status=True
                ).prefetch_related('trazabilidad')

            elif campos_actualizacion:
                self._actualizar_pedidos(pedidos_existentes, campos_actualizacion)
                resultado["accion"] = "actualizado"
                pedidos_existentes = Pedido.objects.filter(
                    documento_compras=numero_pedido_str, status=True
                ).prefetch_related('trazabilidad')

            else:
                resultado["accion"] = "consultado"

            if not pedidos_existentes.exists():
                return Response(
                    {
                        "detail": "Pedido no encontrado en ninguna fuente",
                        "numero_pedido": numero_pedido_str,
                        "fuentes_consultadas": resultado.get("fuentes_consultadas")
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            resultado["pedidos"] = PedidoSerializer(
                pedidos_existentes.order_by('posicion'), many=True
            ).data

            trazabilidad = TrazabilidadPedido.objects.filter(
                pedido__in=pedidos_existentes
            ).order_by('-fecha_registro')

            resultado["trazabilidad"] = TrazabilidadPedidoSerializer(trazabilidad, many=True).data
            resultado["total_posiciones"] = pedidos_existentes.count()
            resultado["total_trazabilidad"] = trazabilidad.count()

            return Response(resultado, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"detail": f"Error procesando solicitud: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _procesar_busqueda(self, request, numero_pedido_str, numero_pedido,
                           empresas, buscar_correos, usar_async, pedido_existe, resultado):
        """Ejecuta busqueda/consolidacion (Caso 1). Retorna Response si es async, None si es sync."""
        if usar_async:
            from apps.integraciones.tasks import consolidar_pedido_task
            task = consolidar_pedido_task.delay(
                numero_pedido=numero_pedido_str,
                empresas=empresas,
                buscar_correos=buscar_correos,
                user_id=request.user.id
            )
            return Response({
                "task_id": task.id,
                "status": "PENDING",
                "numero_pedido": numero_pedido_str,
                "accion": "creado_async" if not pedido_existe else "resincronizado_async",
            }, status=status.HTTP_202_ACCEPTED)

        service = ConsolidationService(user=request.user)
        resultado_busqueda = service.buscar_y_consolidar(
            numero_pedido=int(numero_pedido),
            empresas=empresas,
            buscar_correos=buscar_correos
        )
        resultado["fuentes_consultadas"] = {
            "supplos": resultado_busqueda.get("supplos", {}),
            "graph": resultado_busqueda.get("graph", {}),
            "consolidado": resultado_busqueda.get("consolidado", False),
            "errores": resultado_busqueda.get("errores", [])
        }
        resultado["accion"] = "creado" if not pedido_existe else "resincronizado"
        return None

    def _actualizar_pedidos(self, pedidos_existentes, campos_actualizacion):
        """Actualiza campos de los pedidos existentes y registra trazabilidad (Caso 2)."""
        for pedido in pedidos_existentes:
            estado_anterior = pedido.estado_pedido
            for campo, valor in campos_actualizacion.items():
                setattr(pedido, campo, valor)
            pedido.save()
            if 'estado_pedido' in campos_actualizacion and campos_actualizacion['estado_pedido'] != estado_anterior:
                TrazabilidadPedido.objects.create(
                    pedido=pedido,
                    fuente=TrazabilidadPedido.FuenteDatos.MANUAL,
                    estado_anterior=estado_anterior,
                    estado_nuevo=pedido.estado_pedido,
                    observaciones=f"Actualizado via endpoint unificado. {campos_actualizacion.get('observaciones_corona', '')}"
                )


class TareaEstadoAPIView(APIView):
    """
    GET /api/pedidos/tarea/{task_id}/

    Consulta el estado de una tarea de consolidacion asincrona.

    Response:
    - PENDING: La tarea esta en cola
    - STARTED: La tarea se esta ejecutando
    - SUCCESS: Terminada. Incluye resultado y datos del pedido
    - FAILURE: Fallo. Incluye detalle del error
    """
    permission_classes = [IsAPIKeyAuthenticated]

    def get(self, request, task_id):
        from celery.result import AsyncResult

        task = AsyncResult(task_id)

        response_data = {
            "task_id": task_id,
            "status": task.status,
        }

        if task.successful():
            resultado_task = task.result or {}
            numero_pedido = resultado_task.get("numero_pedido")

            response_data["resultado"] = resultado_task

            # Si la tarea termino, incluir los pedidos de la BD
            if numero_pedido:
                pedidos = Pedido.objects.filter(
                    documento_compras=numero_pedido,
                    status=True
                ).prefetch_related('trazabilidad').order_by('posicion')

                response_data["pedidos"] = PedidoSerializer(pedidos, many=True).data

                trazabilidad = TrazabilidadPedido.objects.filter(
                    pedido__in=pedidos
                ).order_by('-fecha_registro')
                response_data["trazabilidad"] = TrazabilidadPedidoSerializer(
                    trazabilidad, many=True
                ).data

        elif task.failed():
            response_data["error"] = str(task.result)

        return Response(response_data, status=status.HTTP_200_OK)


class BusquedaInteligentePedidoAPIView(APIView):
    """
    POST /api/pedidos/busqueda-ia/

    Busqueda de pedidos usando lenguaje natural.
    Usa IA para convertir la consulta en filtros de base de datos.

    Request body:
    {
        "consulta": "pedidos retrasados de PILOTO en los ultimos 3 meses"
    }
    """
    permission_classes = [IsAPIKeyAuthenticated]

    # Campos permitidos para filtrar (whitelist de seguridad)
    CAMPOS_PERMITIDOS = {
        'documento_compras', 'documento_compras__icontains',
        'razon_social', 'razon_social__icontains',
        'comprador', 'comprador__icontains',
        'organizacion_compras', 'organizacion_compras__icontains',
        'planta', 'planta__icontains',
        'material', 'material__icontains',
        'texto_breve', 'texto_breve__icontains',
        'estado_pedido', 'estado_pedido__in',
        'fecha_entrega', 'fecha_entrega__gte', 'fecha_entrega__lte',
        'fecha_entrega__gt', 'fecha_entrega__lt',
        'observaciones__icontains', 'observaciones_corona__icontains',
        'motivo__icontains',
        'cantidad_pedido__gte', 'cantidad_pedido__lte',
        'por_entregar__gt', 'por_entregar__gte', 'por_entregar__lte',
        'precio_neto__gte', 'precio_neto__lte',
        'fuente_supplos', 'fuente_graph',
    }

    ORDENES_PERMITIDOS = {
        'fecha_entrega', '-fecha_entrega',
        'razon_social', '-razon_social',
        'created_at', '-created_at',
        'precio_neto', '-precio_neto',
        'documento_compras', '-documento_compras',
    }

    def post(self, request):
        consulta = request.data.get("consulta", "").strip()
        if not consulta:
            return Response(
                {"detail": "El campo 'consulta' es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(consulta) > 500:
            return Response(
                {"detail": "La consulta no puede exceder 500 caracteres."},
                status=status.HTTP_400_BAD_REQUEST
            )

        from apps.integraciones.services.ai_extraction_service import AIExtractionService
        ai_service = AIExtractionService()

        resultado_ia = ai_service.generar_filtros_busqueda(consulta)

        if resultado_ia.get("error"):
            return Response(
                {"detail": resultado_ia.get("descripcion", "Error en busqueda IA")},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        filtros_raw = resultado_ia.get("filtros", {})
        orden = resultado_ia.get("orden", "-fecha_entrega")
        descripcion = resultado_ia.get("descripcion", "")

        # Sanitizar filtros: solo permitir campos del whitelist
        filtros_seguros = {}
        for campo, valor in filtros_raw.items():
            if campo in self.CAMPOS_PERMITIDOS:
                filtros_seguros[campo] = valor

        # Sanitizar orden
        if orden not in self.ORDENES_PERMITIDOS:
            orden = "-fecha_entrega"

        try:
            queryset = Pedido.objects.filter(status=True, **filtros_seguros).order_by(orden)

            # Paginar
            page_size = min(int(request.data.get("page_size", 50)), 100)
            page = max(int(request.data.get("page", 1)), 1)
            offset = (page - 1) * page_size
            total = queryset.count()
            pedidos = queryset[offset:offset + page_size]

            return Response({
                "consulta": consulta,
                "descripcion_ia": descripcion,
                "filtros_aplicados": filtros_seguros,
                "orden": orden,
                "total": total,
                "page": page,
                "page_size": page_size,
                "resultados": PedidoListSerializer(pedidos, many=True).data,
            })

        except Exception as e:
            return Response(
                {"detail": f"Error ejecutando busqueda: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
