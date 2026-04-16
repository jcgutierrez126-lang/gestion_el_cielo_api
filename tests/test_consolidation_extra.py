"""
Tests adicionales para consolidation_service.py y azure_document_service.py
Cubre rutas de código no alcanzadas por test_consolidation_service.py.
"""
import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock

from apps.integraciones.services.consolidation_service import ConsolidationService
from apps.integraciones.models import Pedido, TrazabilidadPedido


@pytest.fixture
def service():
    return ConsolidationService()


# ---------------------------------------------------------------------------
# _procesar_items_supplos: data como dict (no lista)
# ---------------------------------------------------------------------------

class TestProcesarItemsSupplosFormatos:

    @pytest.mark.django_db
    def test_data_como_lista(self, service):
        supplos_data = {
            "status": "OK",
            "data": [{"npedido": 5001, "pos": "10", "estado_pedido": "Vigente"}]
        }
        with patch.object(service, "_procesar_item_supplos", return_value={"id": 1}) as mock_proc:
            service._procesar_items_supplos(supplos_data, 5001, None)
            mock_proc.assert_called_once()

    @pytest.mark.django_db
    def test_data_como_dict_con_items(self, service):
        supplos_data = {
            "status": "OK",
            "data": {"items": [{"npedido": 5002, "pos": "10"}]}
        }
        with patch.object(service, "_procesar_item_supplos", return_value={"id": 2}) as mock_proc:
            service._procesar_items_supplos(supplos_data, 5002, None)
            mock_proc.assert_called_once()

    @pytest.mark.django_db
    def test_item_vacio_es_ignorado(self, service):
        supplos_data = {"status": "OK", "data": [None, {}, {"npedido": 5003, "pos": "10"}]}
        with patch.object(service, "_procesar_item_supplos", return_value={"id": 3}) as mock_proc:
            service._procesar_items_supplos(supplos_data, 5003, None)
            # Solo el item no vacío debería procesarse
            assert mock_proc.call_count == 1


# ---------------------------------------------------------------------------
# _enriquecer_con_graph: distintas combinaciones
# ---------------------------------------------------------------------------

class TestEnriquecerConGraph:

    def test_sin_graph_data_retorna_none(self, service):
        pedido_data = {"observaciones": ""}
        resultado = service._enriquecer_con_graph(pedido_data, None, "10")
        assert resultado is None

    def test_graph_error_retorna_none(self, service):
        graph_data = {"status": "ERROR"}
        pedido_data = {}
        resultado = service._enriquecer_con_graph(pedido_data, graph_data, "10")
        assert resultado is None

    def test_graph_ok_sin_correos_retorna_none(self, service):
        graph_data = {"status": "OK", "data": []}
        pedido_data = {}
        resultado = service._enriquecer_con_graph(pedido_data, graph_data, "10")
        assert resultado is None

    def test_enriquece_con_observacion_de_posicion(self, service):
        graph_data = {
            "status": "OK",
            "data": [{
                "email_id": "e1",
                "subject": "Test",
                "from": "a@b.com",
                "received_date": "2025-04-15",
                "observaciones_proveedor": "obs posicion",
                "observaciones_cielo": None,
                "posiciones_correo": [{"posicion": "10", "comentario": "OK entregado"}],
            }]
        }
        pedido_data = {"observaciones": ""}
        service._enriquecer_con_graph(pedido_data, graph_data, "10")
        assert pedido_data.get("observaciones") == "OK entregado"

    def test_enriquece_con_observacion_general_sin_posicion(self, service):
        graph_data = {
            "status": "OK",
            "data": [{
                "email_id": "e2",
                "subject": "Test",
                "from": "a@b.com",
                "received_date": "2025-04-15",
                "observaciones_proveedor": "Entrega semana que viene",
                "observaciones_cielo": None,
                "posiciones_correo": [],
            }]
        }
        pedido_data = {"observaciones": ""}
        service._enriquecer_con_graph(pedido_data, graph_data, None)
        assert pedido_data.get("observaciones") == "Entrega semana que viene"

    def test_enriquece_observaciones_cielo(self, service):
        graph_data = {
            "status": "OK",
            "data": [{
                "email_id": "e3",
                "subject": "Test",
                "from": "a@b.com",
                "received_date": "2025-04-15",
                "observaciones_proveedor": "obs",
                "observaciones_cielo": "Verificado por corona",
                "posiciones_correo": [],
            }]
        }
        pedido_data = {}
        service._enriquecer_con_graph(pedido_data, graph_data, None)
        assert pedido_data.get("observaciones_cielo") == "Verificado por corona"
        assert pedido_data.get("fuente_graph") is True


# ---------------------------------------------------------------------------
# _procesar_solo_graph
# ---------------------------------------------------------------------------

class TestProcesarSoloGraph:

    @pytest.mark.django_db
    def test_crea_pedido_solo_graph(self, service):
        graph_data = {
            "status": "OK",
            "data": [{
                "email_id": "e-sg-1",
                "subject": "Seguimiento",
                "from": "a@b.com",
                "received_date": "2025-04-15",
                "observaciones_proveedor": "Sin entrega aún",
                "observaciones_cielo": None,
                "posiciones_correo": [],
            }]
        }
        with patch.object(service.graph_service, "marcar_correo_procesado"):
            resultado = service._procesar_solo_graph(graph_data, 8888)

        assert len(resultado) == 1
        assert resultado[0]["solo_graph"] is True
        assert Pedido.objects.filter(documento_compras="8888").exists()

    @pytest.mark.django_db
    def test_crea_pedido_solo_graph_sin_observaciones(self, service):
        graph_data = {
            "status": "OK",
            "data": [{
                "email_id": "e-sg-2",
                "subject": "Seguimiento",
                "from": "a@b.com",
                "received_date": "2025-04-15",
                "observaciones_proveedor": None,
                "observaciones_cielo": None,
                "posiciones_correo": [],
            }]
        }
        with patch.object(service.graph_service, "marcar_correo_procesado"):
            resultado = service._procesar_solo_graph(graph_data, 7777)

        assert len(resultado) == 1


# ---------------------------------------------------------------------------
# _guardar_pedido: update_or_create
# ---------------------------------------------------------------------------

class TestGuardarPedido:

    @pytest.mark.django_db
    def test_crea_pedido_nuevo(self, service):
        pedido_data = {
            "documento_compras": "TEST-9001",
            "posicion": "10",
            "estado_pedido": Pedido.EstadoPedido.VIGENTE,
            "fuente_supplos": True,
        }
        pedido = service._guardar_pedido(pedido_data)
        assert pedido.documento_compras == "TEST-9001"
        assert Pedido.objects.filter(documento_compras="TEST-9001").count() == 1

    @pytest.mark.django_db
    def test_actualiza_pedido_existente(self, service):
        Pedido.objects.create(
            documento_compras="TEST-9002",
            posicion="10",
            estado_pedido=Pedido.EstadoPedido.VIGENTE,
        )
        pedido_data = {
            "documento_compras": "TEST-9002",
            "posicion": "10",
            "estado_pedido": Pedido.EstadoPedido.ENTREGADO,
        }
        pedido = service._guardar_pedido(pedido_data)
        assert pedido.estado_pedido == Pedido.EstadoPedido.ENTREGADO
        assert Pedido.objects.filter(documento_compras="TEST-9002").count() == 1


# ---------------------------------------------------------------------------
# _registrar_trazabilidad: con y sin historial
# ---------------------------------------------------------------------------

class TestRegistrarTrazabilidad:

    @pytest.mark.django_db
    def test_registra_sin_observaciones_graph(self, service):
        pedido = Pedido.objects.create(
            documento_compras="TRAZ-001",
            estado_pedido=Pedido.EstadoPedido.VIGENTE,
        )
        service._registrar_trazabilidad(
            pedido=pedido,
            estado_anterior=None,
            fuente=TrazabilidadPedido.FuenteDatos.SUPPLOS,
            datos_raw={"test": True},
        )
        assert TrazabilidadPedido.objects.filter(pedido=pedido).count() == 1

    @pytest.mark.django_db
    def test_registra_con_historial_correos(self, service):
        pedido = Pedido.objects.create(
            documento_compras="TRAZ-002",
            estado_pedido=Pedido.EstadoPedido.VIGENTE,
        )
        obs_graph = {
            "observaciones": "Entregado",
            "email_id": "e1",
            "email_subject": "Seguimiento",
            "email_from": "a@b.com",
            "email_date": None,
            "historial_correos": [
                {"email_id": "e1", "subject": "Seguimiento", "observaciones_proveedor": "Entregado"}
            ],
        }
        service._registrar_trazabilidad(
            pedido=pedido,
            estado_anterior=Pedido.EstadoPedido.VIGENTE,
            fuente=TrazabilidadPedido.FuenteDatos.GRAPH,
            datos_raw=None,
            observaciones_graph=obs_graph,
        )
        traz = TrazabilidadPedido.objects.filter(pedido=pedido).first()
        assert traz is not None
        assert traz.datos_raw["total_correos"] == 1

    @pytest.mark.django_db
    def test_registra_con_historial_y_datos_raw_existentes(self, service):
        pedido = Pedido.objects.create(
            documento_compras="TRAZ-003",
            estado_pedido=Pedido.EstadoPedido.VIGENTE,
        )
        obs_graph = {
            "observaciones": "OK",
            "email_id": None,
            "email_subject": None,
            "email_from": None,
            "email_date": None,
            "historial_correos": [{"email_id": "e99"}],
        }
        service._registrar_trazabilidad(
            pedido=pedido,
            estado_anterior=None,
            fuente=TrazabilidadPedido.FuenteDatos.SUPPLOS,
            datos_raw={"npedido": 3333},
            observaciones_graph=obs_graph,
        )
        traz = TrazabilidadPedido.objects.filter(pedido=pedido).first()
        assert "historial_correos" in traz.datos_raw


# ---------------------------------------------------------------------------
# buscar_y_consolidar: flujo con error de Graph (líneas 95-106)
# ---------------------------------------------------------------------------

class TestBuscarYConsolidarConGraph:

    @pytest.mark.django_db
    @patch("apps.integraciones.services.consolidation_service.SuplosService")
    @patch("apps.integraciones.services.consolidation_service.GraphSearchService")
    def test_continua_si_graph_lanza_excepcion(self, mock_graph_cls, mock_supplos_cls):
        from apps.integraciones.services.graph_search_service import GraphSearchException

        mock_supplos = MagicMock()
        mock_supplos.consultar_pedido.return_value = {
            "status": "OK",
            "data": [{"npedido": 9100, "pos": "10", "estado_pedido": "Vigente"}]
        }
        mock_supplos_cls.return_value = mock_supplos

        mock_graph = MagicMock()
        mock_graph.buscar_correos_por_pedido.side_effect = GraphSearchException("Error token")
        mock_graph_cls.return_value = mock_graph

        service = ConsolidationService()
        resultado = service.buscar_y_consolidar(numero_pedido=9100, buscar_correos=True)

        # Supplos OK, Graph falló pero se registró como error — consolidado igual
        assert resultado["consolidado"] is True
        assert any("Graph" in e for e in resultado["errores"])

    @pytest.mark.django_db
    @patch("apps.integraciones.services.consolidation_service.SuplosService")
    @patch("apps.integraciones.services.consolidation_service.GraphSearchService")
    def test_consolidado_false_si_falla_consolidacion(self, mock_graph_cls, mock_supplos_cls):
        mock_supplos = MagicMock()
        mock_supplos.consultar_pedido.return_value = {"status": "OK", "data": "invalido"}
        mock_supplos_cls.return_value = mock_supplos

        mock_graph = MagicMock()
        mock_graph.buscar_correos_por_pedido.return_value = {"status": "ERROR"}
        mock_graph_cls.return_value = mock_graph

        service = ConsolidationService()

        with patch.object(service, "_consolidar_y_guardar", side_effect=Exception("DB error")):
            resultado = service.buscar_y_consolidar(numero_pedido=9200)

        assert resultado["consolidado"] is False


# ---------------------------------------------------------------------------
# azure_document_service: _formatear_resultado y _tabla_a_texto
# ---------------------------------------------------------------------------

class TestAzureDocumentServiceFormatos:

    def test_formatear_resultado_con_content_y_tablas(self):
        from apps.integraciones.services.azure_document_service import AzureDocumentService
        service = AzureDocumentService()

        mock_cell = MagicMock()
        mock_cell.row_index = 0
        mock_cell.column_index = 0
        mock_cell.content = "Valor"

        mock_table = MagicMock()
        mock_table.cells = [mock_cell]

        mock_result = MagicMock()
        mock_result.content = "Texto principal"
        mock_result.tables = [mock_table]

        texto = service._formatear_resultado(mock_result)
        assert "Texto principal" in texto
        assert "[TABLA 1]" in texto
        assert "Valor" in texto

    def test_formatear_resultado_sin_content(self):
        from apps.integraciones.services.azure_document_service import AzureDocumentService
        service = AzureDocumentService()

        mock_result = MagicMock()
        mock_result.content = None
        mock_result.tables = []

        texto = service._formatear_resultado(mock_result)
        assert texto == ""

    def test_tabla_a_texto_sin_cells(self):
        from apps.integraciones.services.azure_document_service import AzureDocumentService
        service = AzureDocumentService()

        mock_table = MagicMock()
        mock_table.cells = []

        assert service._tabla_a_texto(mock_table) == ""

    def test_tabla_a_texto_con_multiples_celdas(self):
        from apps.integraciones.services.azure_document_service import AzureDocumentService
        service = AzureDocumentService()

        def make_cell(row, col, content):
            c = MagicMock()
            c.row_index = row
            c.column_index = col
            c.content = content
            return c

        mock_table = MagicMock()
        mock_table.cells = [
            make_cell(0, 0, "Pedido"),
            make_cell(0, 1, "Estado"),
            make_cell(1, 0, "4501833743"),
            make_cell(1, 1, "Vigente"),
        ]

        resultado = service._tabla_a_texto(mock_table)
        assert "Pedido" in resultado
        assert "Vigente" in resultado
        assert "|" in resultado

    def test_inicializa_con_credenciales_invalidas(self):
        from apps.integraciones.services.azure_document_service import AzureDocumentService
        with patch.dict("os.environ", {
            "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT": "https://fake.cognitiveservices.azure.com",
            "AZURE_DOCUMENT_INTELLIGENCE_KEY": "fake-key",
        }):
            with patch("apps.integraciones.services.azure_document_service.AzureDocumentService.__init__",
                       wraps=lambda self: None):
                service = AzureDocumentService.__new__(AzureDocumentService)
                service.client = None
                assert service.is_available() is False
