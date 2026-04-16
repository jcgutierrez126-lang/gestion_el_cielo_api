from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def consolidar_pedido_task(self, numero_pedido, empresas=None, buscar_correos=True, user_id=None):
    """
    Task de Celery para consolidar un pedido en background.
    Busca en Supplos + Graph, extrae con IA, y guarda en BD.

    Al terminar, los datos quedan en la BD (Pedido + TrazabilidadPedido).
    El frontend consulta GET /api/pedidos/{numero}/ para obtener los resultados.
    """
    from apps.integraciones.services.consolidation_service import ConsolidationService

    user = None
    if user_id:
        from apps.usuarios.models import User
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            pass

    logger.info(f"[Celery] Iniciando consolidacion de pedido {numero_pedido}")

    service = ConsolidationService(user=user)
    resultado = service.buscar_y_consolidar(
        numero_pedido=int(numero_pedido),
        empresas=empresas,
        buscar_correos=buscar_correos
    )

    logger.info(f"[Celery] Consolidacion finalizada para pedido {numero_pedido}")

    # Retornar resumen serializable (JSON)
    return {
        "numero_pedido": str(numero_pedido),
        "consolidado": resultado.get("consolidado", False),
        "pedidos_guardados": len(resultado.get("pedidos_guardados", [])),
        "errores": resultado.get("errores", []),
    }


@shared_task
def limpiar_registros_antiguos():
    """
    Tarea programada (Celery Beat) — se ejecuta cada 24 horas.
    Elimina registros antiguos para evitar crecimiento ilimitado de la DB.

    Limpia:
    - CorreoProcesado con mas de 90 dias
    - LogConsulta con mas de 90 dias
    - Resultados de tareas Celery en Redis expiran automaticamente (CELERY_RESULT_EXPIRES=3600)
    """
    from apps.integraciones.models import CorreoProcesado, LogConsulta

    corte = timezone.now() - timedelta(days=90)

    correos_eliminados, _ = CorreoProcesado.objects.filter(procesado_at__lt=corte).delete()
    logs_eliminados, _ = LogConsulta.objects.filter(created_at__lt=corte).delete()

    logger.info(
        "Limpieza de registros completada",
        extra={
            "correos_procesados_eliminados": correos_eliminados,
            "logs_consulta_eliminados": logs_eliminados,
            "corte_fecha": corte.isoformat(),
        }
    )

    return {
        "correos_procesados_eliminados": correos_eliminados,
        "logs_consulta_eliminados": logs_eliminados,
    }
