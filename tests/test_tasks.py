"""
Tests para apps/integraciones/tasks.py
Cubre consolidar_pedido_task y limpiar_registros_antiguos.
"""
import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone
from datetime import timedelta

from apps.integraciones.models import CorreoProcesado, LogConsulta, Pedido


MOCK_CONSOLIDATION = "apps.integraciones.services.consolidation_service.ConsolidationService"


class TestConsolidarPedidoTask:

    @pytest.mark.django_db
    @patch(MOCK_CONSOLIDATION)
    def test_tarea_retorna_resumen_serializable(self, mock_cls):
        from apps.integraciones.tasks import consolidar_pedido_task
        mock_service = MagicMock()
        mock_service.buscar_y_consolidar.return_value = {
            "consolidado": True,
            "pedidos_guardados": [{"id": 1}],
            "errores": [],
        }
        mock_cls.return_value = mock_service

        resultado = consolidar_pedido_task.apply(
            kwargs={"numero_pedido": "4501833743"}
        ).get()

        assert resultado["numero_pedido"] == "4501833743"
        assert resultado["consolidado"] is True
        assert resultado["pedidos_guardados"] == 1
        assert resultado["errores"] == []

    @pytest.mark.django_db
    @patch(MOCK_CONSOLIDATION)
    def test_tarea_con_errores_en_resultado(self, mock_cls):
        from apps.integraciones.tasks import consolidar_pedido_task
        mock_service = MagicMock()
        mock_service.buscar_y_consolidar.return_value = {
            "consolidado": False,
            "pedidos_guardados": [],
            "errores": ["Error en Supplos"],
        }
        mock_cls.return_value = mock_service

        resultado = consolidar_pedido_task.apply(
            kwargs={"numero_pedido": "9999"}
        ).get()

        assert resultado["consolidado"] is False
        assert "Error en Supplos" in resultado["errores"]

    @pytest.mark.django_db
    @patch(MOCK_CONSOLIDATION)
    def test_tarea_con_user_id_valido(self, mock_cls, usuario):
        from apps.integraciones.tasks import consolidar_pedido_task
        mock_service = MagicMock()
        mock_service.buscar_y_consolidar.return_value = {
            "consolidado": True,
            "pedidos_guardados": [],
            "errores": [],
        }
        mock_cls.return_value = mock_service

        resultado = consolidar_pedido_task.apply(
            kwargs={"numero_pedido": "1111", "user_id": usuario.id}
        ).get()

        assert resultado["numero_pedido"] == "1111"
        # Verifica que se pasó el usuario al service
        mock_cls.assert_called_once_with(user=usuario)

    @pytest.mark.django_db
    @patch(MOCK_CONSOLIDATION)
    def test_tarea_con_user_id_inexistente(self, mock_cls):
        from apps.integraciones.tasks import consolidar_pedido_task
        mock_service = MagicMock()
        mock_service.buscar_y_consolidar.return_value = {
            "consolidado": True,
            "pedidos_guardados": [],
            "errores": [],
        }
        mock_cls.return_value = mock_service

        resultado = consolidar_pedido_task.apply(
            kwargs={"numero_pedido": "2222", "user_id": 99999}
        ).get()

        # user_id inexistente no debe romper la tarea
        assert resultado["numero_pedido"] == "2222"
        mock_cls.assert_called_once_with(user=None)


class TestLimpiarRegistrosAntiguos:

    @pytest.mark.django_db
    def test_elimina_correos_procesados_antiguos(self):
        from apps.integraciones.tasks import limpiar_registros_antiguos

        hace_100_dias = timezone.now() - timedelta(days=100)

        correo = CorreoProcesado.objects.create(
            email_id="viejo-001",
            buzon="buzon@corona.com.co",
            subject="Pedido viejo",
        )
        CorreoProcesado.objects.filter(pk=correo.pk).update(procesado_at=hace_100_dias)

        resultado = limpiar_registros_antiguos.apply().get()

        assert resultado["correos_procesados_eliminados"] >= 1
        assert not CorreoProcesado.objects.filter(email_id="viejo-001").exists()

    @pytest.mark.django_db
    def test_no_elimina_correos_recientes(self):
        from apps.integraciones.tasks import limpiar_registros_antiguos

        CorreoProcesado.objects.create(
            email_id="reciente-001",
            buzon="buzon@corona.com.co",
            subject="Pedido reciente",
        )

        resultado = limpiar_registros_antiguos.apply().get()

        assert CorreoProcesado.objects.filter(email_id="reciente-001").exists()
        assert resultado["correos_procesados_eliminados"] == 0

    @pytest.mark.django_db
    def test_elimina_logs_antiguos(self):
        from apps.integraciones.tasks import limpiar_registros_antiguos

        hace_100_dias = timezone.now() - timedelta(days=100)

        log = LogConsulta.objects.create(
            tipo=LogConsulta.TipoConsulta.SUPPLOS,
            parametros={"test": True},
            respuesta_exitosa=True,
            tiempo_respuesta_ms=100,
        )
        LogConsulta.objects.filter(pk=log.pk).update(created_at=hace_100_dias)

        resultado = limpiar_registros_antiguos.apply().get()

        assert resultado["logs_consulta_eliminados"] >= 1

    @pytest.mark.django_db
    def test_retorna_ceros_cuando_no_hay_registros_antiguos(self):
        from apps.integraciones.tasks import limpiar_registros_antiguos

        resultado = limpiar_registros_antiguos.apply().get()

        assert resultado["correos_procesados_eliminados"] == 0
        assert resultado["logs_consulta_eliminados"] == 0
