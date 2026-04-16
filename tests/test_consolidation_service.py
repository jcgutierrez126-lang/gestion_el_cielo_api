"""
Tests para apps/integraciones/services/consolidation_service.py
Cubre métodos utilitarios puros y flujo principal con mocks.
"""
import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import patch, MagicMock

from apps.integraciones.services.consolidation_service import ConsolidationService
from apps.integraciones.models import Pedido, TrazabilidadPedido


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def service():
    return ConsolidationService()


# ---------------------------------------------------------------------------
# _parsear_fecha
# ---------------------------------------------------------------------------

class TestParsearFecha:

    def test_retorna_none_para_valor_vacio(self, service):
        assert service._parsear_fecha(None) is None
        assert service._parsear_fecha("") is None
        assert service._parsear_fecha("None") is None

    def test_parsea_formato_supplos_ddmmyyyy(self, service):
        resultado = service._parsear_fecha("15042025")
        assert resultado == datetime(2025, 4, 15)

    def test_parsea_formato_iso(self, service):
        resultado = service._parsear_fecha("2025-04-15")
        assert resultado == datetime(2025, 4, 15)

    def test_parsea_formato_slash(self, service):
        resultado = service._parsear_fecha("15/04/2025")
        assert resultado == datetime(2025, 4, 15)

    def test_parsea_formato_guion_dia_primero(self, service):
        resultado = service._parsear_fecha("15-04-2025")
        assert resultado == datetime(2025, 4, 15)

    def test_parsea_datetime_ya_parseado(self, service):
        dt = datetime(2025, 4, 15)
        assert service._parsear_fecha(dt) == dt

    def test_retorna_none_para_formato_invalido(self, service):
        assert service._parsear_fecha("no-es-fecha") is None


# ---------------------------------------------------------------------------
# _mapear_estado
# ---------------------------------------------------------------------------

class TestMapearEstado:

    def test_estado_vacio_retorna_vigente(self, service):
        assert service._mapear_estado("") == Pedido.EstadoPedido.VIGENTE
        assert service._mapear_estado(None) == Pedido.EstadoPedido.VIGENTE

    def test_mapea_vigente(self, service):
        assert service._mapear_estado("Vigente") == Pedido.EstadoPedido.VIGENTE
        assert service._mapear_estado("VIGENTE") == Pedido.EstadoPedido.VIGENTE

    def test_mapea_entregado(self, service):
        assert service._mapear_estado("Entregado") == Pedido.EstadoPedido.ENTREGADO

    def test_mapea_pendiente(self, service):
        assert service._mapear_estado("Pendiente") == Pedido.EstadoPedido.PENDIENTE
        assert service._mapear_estado("en proceso") == Pedido.EstadoPedido.PENDIENTE

    def test_mapea_parcial(self, service):
        assert service._mapear_estado("Parcial") == Pedido.EstadoPedido.PARCIAL
        assert service._mapear_estado("entrega parcial") == Pedido.EstadoPedido.PARCIAL

    def test_mapea_cancelado(self, service):
        assert service._mapear_estado("Cancelado") == Pedido.EstadoPedido.CANCELADO

    def test_mapea_en_transito(self, service):
        assert service._mapear_estado("en transito") == Pedido.EstadoPedido.EN_TRANSITO

    def test_estado_desconocido_retorna_vigente(self, service):
        assert service._mapear_estado("XYZ_desconocido") == Pedido.EstadoPedido.VIGENTE


# ---------------------------------------------------------------------------
# _safe_decimal
# ---------------------------------------------------------------------------

class TestSafeDecimal:

    def test_valor_none_retorna_cero(self, service):
        assert service._safe_decimal(None) == Decimal("0")

    def test_valor_vacio_retorna_cero(self, service):
        assert service._safe_decimal("") == Decimal("0")
        assert service._safe_decimal("None") == Decimal("0")

    def test_entero(self, service):
        assert service._safe_decimal(10) == Decimal("10")

    def test_float(self, service):
        assert service._safe_decimal(3.14) == Decimal("3.14")

    def test_string_con_coma(self, service):
        assert service._safe_decimal("1,500") == Decimal("1.500")

    def test_string_numerico(self, service):
        assert service._safe_decimal("250.75") == Decimal("250.75")

    def test_valor_invalido_retorna_cero(self, service):
        assert service._safe_decimal("no-es-numero") == Decimal("0")


# ---------------------------------------------------------------------------
# _extraer_comprador
# ---------------------------------------------------------------------------

class TestExtraerComprador:

    def test_dict_con_nombre(self, service):
        assert service._extraer_comprador({"nombre": "Juan Pérez"}) == "Juan Pérez"

    def test_string_directo(self, service):
        assert service._extraer_comprador("María López") == "María López"

    def test_ninguno_retorna_vacio(self, service):
        assert service._extraer_comprador(None) == ""

    def test_dict_sin_nombre_usa_str(self, service):
        resultado = service._extraer_comprador({"otro": "campo"})
        assert isinstance(resultado, str)


# ---------------------------------------------------------------------------
# _buscar_obs_por_posicion
# ---------------------------------------------------------------------------

class TestBuscarObsPorPosicion:

    def test_encuentra_posicion_exacta(self, service):
        posiciones = [
            {"posicion": "30", "comentario": "Entregado"},
            {"posicion": "40", "comentario": "Pendiente"},
        ]
        assert service._buscar_obs_por_posicion("30", posiciones) == "Entregado"

    def test_encuentra_posicion_con_ceros(self, service):
        # Supplos usa "00030", el correo usa "30"
        posiciones = [{"posicion": "30", "comentario": "OK"}]
        assert service._buscar_obs_por_posicion("00030", posiciones) == "OK"

    def test_posicion_inexistente_retorna_none(self, service):
        posiciones = [{"posicion": "30", "comentario": "X"}]
        assert service._buscar_obs_por_posicion("99", posiciones) is None

    def test_posicion_invalida_retorna_none(self, service):
        assert service._buscar_obs_por_posicion("abc", []) is None


# ---------------------------------------------------------------------------
# _extraer_observaciones_graph
# ---------------------------------------------------------------------------

class TestExtraerObservacionesGraph:

    def test_lista_vacia_retorna_none(self, service):
        assert service._extraer_observaciones_graph([]) is None

    def test_extrae_observacion_mas_reciente(self, service):
        correos = [
            {
                "email_id": "1",
                "subject": "Re: Pedido",
                "from": "proveedor@test.com",
                "received_date": "2025-04-15T10:00:00",
                "observaciones_proveedor": "Entregado hoy",
                "observaciones_corona": None,
                "posiciones_correo": [],
            },
            {
                "email_id": "2",
                "subject": "Re: Pedido",
                "from": "proveedor@test.com",
                "received_date": "2025-04-10T10:00:00",
                "observaciones_proveedor": "Despacho semana que viene",
                "observaciones_corona": None,
                "posiciones_correo": [],
            },
        ]
        resultado = service._extraer_observaciones_graph(correos)
        assert resultado is not None
        assert resultado["observaciones"] == "Entregado hoy"
        assert resultado["total_correos"] == 2

    def test_usa_fallback_datos_extraidos(self, service):
        correos = [{
            "email_id": "3",
            "subject": "Seguimiento",
            "from": "x@y.com",
            "received_date": "2025-04-01",
            "observaciones_proveedor": None,
            "observaciones_corona": None,
            "posiciones_correo": [],
            "datos_extraidos": {"observaciones_proveedor": "Desde fallback"},
        }]
        resultado = service._extraer_observaciones_graph(correos)
        assert resultado["observaciones"] == "Desde fallback"

    def test_extrae_posiciones_correo(self, service):
        posiciones = [{"posicion": "10", "comentario": "OK"}]
        correos = [{
            "email_id": "4",
            "subject": "Test",
            "from": "x@y.com",
            "received_date": "2025-04-01",
            "observaciones_proveedor": "obs",
            "observaciones_corona": None,
            "posiciones_correo": posiciones,
        }]
        resultado = service._extraer_observaciones_graph(correos)
        assert resultado["posiciones_correo"] == posiciones


# ---------------------------------------------------------------------------
# _mapear_supplos_a_dict
# ---------------------------------------------------------------------------

class TestMapearSupplosADict:

    def test_mapea_campos_basicos(self, service):
        item = {
            "npedido": 4501833743,
            "pos": "10",
            "razon_social": "Proveedor SA",
            "estado_pedido": "Vigente",
        }
        resultado = service._mapear_supplos_a_dict(item, 4501833743)
        assert resultado["documento_compras"] == "4501833743"
        assert resultado["posicion"] == "10"
        assert resultado["razon_social"] == "Proveedor SA"
        assert resultado["fuente_supplos"] is True

    def test_posicion_vacia_queda_none(self, service):
        item = {"npedido": 111, "pos": ""}
        resultado = service._mapear_supplos_a_dict(item, 111)
        assert resultado["posicion"] is None


# ---------------------------------------------------------------------------
# buscar_y_consolidar (flujo completo con mocks)
# ---------------------------------------------------------------------------

class TestBuscarYConsolidar:

    @pytest.mark.django_db
    @patch("apps.integraciones.services.consolidation_service.SuplosService")
    @patch("apps.integraciones.services.consolidation_service.GraphSearchService")
    def test_consolidacion_exitosa(self, mock_graph_cls, mock_supplos_cls):
        mock_supplos = MagicMock()
        mock_supplos.consultar_pedido.return_value = {
            "status": "OK",
            "data": [{
                "npedido": 4501833743,
                "pos": "10",
                "razon_social": "Proveedor Test",
                "estado_pedido": "Vigente",
            }]
        }
        mock_supplos_cls.return_value = mock_supplos

        mock_graph = MagicMock()
        mock_graph.buscar_correos_por_pedido.return_value = {"status": "ERROR"}
        mock_graph_cls.return_value = mock_graph

        service = ConsolidationService()
        resultado = service.buscar_y_consolidar(numero_pedido=4501833743)

        assert resultado["consolidado"] is True
        assert len(resultado["pedidos_guardados"]) > 0

    @pytest.mark.django_db
    @patch("apps.integraciones.services.consolidation_service.SuplosService")
    @patch("apps.integraciones.services.consolidation_service.GraphSearchService")
    def test_consolidacion_con_error_supplos(self, mock_graph_cls, mock_supplos_cls):
        from apps.integraciones.services.supplos_service import SuplosServiceException
        mock_supplos = MagicMock()
        mock_supplos.consultar_pedido.side_effect = SuplosServiceException("Error conexion")
        mock_supplos_cls.return_value = mock_supplos

        mock_graph = MagicMock()
        mock_graph.buscar_correos_por_pedido.return_value = {"status": "ERROR"}
        mock_graph_cls.return_value = mock_graph

        service = ConsolidationService()
        resultado = service.buscar_y_consolidar(numero_pedido=9999)

        assert len(resultado["errores"]) > 0

    @pytest.mark.django_db
    @patch("apps.integraciones.services.consolidation_service.SuplosService")
    @patch("apps.integraciones.services.consolidation_service.GraphSearchService")
    def test_consolida_sin_buscar_correos(self, mock_graph_cls, mock_supplos_cls):
        mock_supplos = MagicMock()
        mock_supplos.consultar_pedido.return_value = {
            "status": "OK",
            "data": [{"npedido": 1111, "pos": "10", "estado_pedido": "Vigente"}]
        }
        mock_supplos_cls.return_value = mock_supplos
        mock_graph_cls.return_value = MagicMock()

        service = ConsolidationService()
        resultado = service.buscar_y_consolidar(numero_pedido=1111, buscar_correos=False)

        assert resultado["consolidado"] is True
        # No debería llamar a Graph
        mock_graph_cls.return_value.buscar_correos_por_pedido.assert_not_called()
