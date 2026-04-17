from django.urls import path
from apps.integraciones.api.views import (
    BuscarPedidoAPIView,
    PedidoListAPIView,
    PedidoDetailAPIView,
    PedidoByIdAPIView,
    PedidoUpdateAPIView,
    ResincronizarPedidoAPIView,
    TrazabilidadPedidoAPIView,
    LogConsultaListAPIView,
    EstadisticasPedidosAPIView,
    CorreoAutorizadoListCreateAPIView,
    CorreoAutorizadoDetailAPIView,
    CorreosProcesadosListAPIView,
    TestGraphSearchAPIView,
    PedidoUnificadoAPIView,
    TareaEstadoAPIView,
    BusquedaInteligentePedidoAPIView,
)

urlpatterns = [
    # Endpoint unificado (consultar/crear/actualizar)
    path('consultar/', PedidoUnificadoAPIView.as_view(), name='pedido-unificado'),

    # Busqueda y consolidacion
    path('buscar/', BuscarPedidoAPIView.as_view(), name='buscar-pedido'),

    # Busqueda inteligente con IA
    path('busqueda-ia/', BusquedaInteligentePedidoAPIView.as_view(), name='busqueda-ia'),

    # Estadisticas (debe ir antes de <str:numero_pedido>)
    path('estadisticas/', EstadisticasPedidosAPIView.as_view(), name='estadisticas'),

    # Logs
    path('logs/', LogConsultaListAPIView.as_view(), name='log-list'),

    # Correos autorizados (CRUD)
    path('correos/', CorreoAutorizadoListCreateAPIView.as_view(), name='correos-list-create'),
    path('correos/<int:pk>/', CorreoAutorizadoDetailAPIView.as_view(), name='correos-detail'),
    path('correos-procesados/', CorreosProcesadosListAPIView.as_view(), name='correos-procesados'),

    # Estado de tarea asincrona (Celery)
    path('tarea/<str:task_id>/', TareaEstadoAPIView.as_view(), name='tarea-estado'),

    # Test de Graph (para depuracion)
    path('test-graph/<str:numero_pedido>/', TestGraphSearchAPIView.as_view(), name='test-graph'),

    # Listado general
    path('', PedidoListAPIView.as_view(), name='pedido-list'),

    # Detalle por ID interno
    path('detalle/<int:pk>/', PedidoByIdAPIView.as_view(), name='pedido-detail-by-id'),

    # Actualizar pedido
    path('<int:pk>/actualizar/', PedidoUpdateAPIView.as_view(), name='pedido-update'),

    # Detalle por numero de pedido
    path('<str:numero_pedido>/', PedidoDetailAPIView.as_view(), name='pedido-detail'),

    # Trazabilidad de un pedido
    path('<str:numero_pedido>/trazabilidad/', TrazabilidadPedidoAPIView.as_view(), name='pedido-trazabilidad'),

    # Resincronizar pedido
    path('<str:numero_pedido>/resincronizar/', ResincronizarPedidoAPIView.as_view(), name='pedido-resync'),
]
