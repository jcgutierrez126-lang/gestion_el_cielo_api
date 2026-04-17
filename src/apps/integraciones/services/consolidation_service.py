from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from django.db import transaction
import logging

from apps.integraciones.models import Pedido, TrazabilidadPedido, LogConsulta
from apps.integraciones.services.supplos_service import SuplosService, SuplosServiceException
from apps.integraciones.services.graph_search_service import GraphSearchService, GraphSearchException

logger = logging.getLogger(__name__)


class ConsolidationService:
    """
    Servicio para consolidar datos de pedidos de multiples fuentes.
    Flujo:
    1. Consultar Supplos (fuente principal)
    2. Buscar en Graph/Correos (observaciones del proveedor)
    3. Consolidar y guardar con trazabilidad
    """

    def __init__(self, user=None):
        self.supplos_service = SuplosService()
        self.graph_service = GraphSearchService()
        self.user = user

    def buscar_y_consolidar(
        self,
        numero_pedido: int,
        empresas: List[str] = None,
        buscar_correos: bool = True
    ) -> Dict[str, Any]:
        """
        Busca un pedido en Supplos y Graph, consolida la informacion
        y la almacena en base de datos con trazabilidad.

        Args:
            numero_pedido: Numero del pedido a buscar
            empresas: Lista de empresas para buscar en Supplos
            buscar_correos: Si debe buscar en correos (Graph)

        Returns:
            Resultado consolidado con datos del pedido
        """
        inicio = timezone.now()
        resultado = {
            "numero_pedido": numero_pedido,
            "supplos": None,
            "graph": None,
            "consolidado": False,
            "pedidos_guardados": [],
            "errores": []
        }

        # 1. Buscar en Supplos (fuente principal)
        try:
            logger.info(f"Buscando pedido {numero_pedido} en Supplos")
            supplos_data = self.supplos_service.consultar_pedido(numero_pedido, empresas)
            resultado["supplos"] = supplos_data

            self._registrar_log(
                tipo=LogConsulta.TipoConsulta.SUPPLOS,
                parametros={"numero_pedido": numero_pedido, "empresas": empresas},
                exitosa=True,
                inicio=inicio
            )
        except SuplosServiceException as e:
            error_msg = f"Error Supplos: {str(e)}"
            resultado["errores"].append(error_msg)
            logger.error(error_msg)

            self._registrar_log(
                tipo=LogConsulta.TipoConsulta.SUPPLOS,
                parametros={"numero_pedido": numero_pedido},
                exitosa=False,
                mensaje_error=str(e),
                inicio=inicio
            )

        # 2. Buscar en Graph (correos) para obtener observaciones del proveedor
        if buscar_correos:
            try:
                logger.info(f"Buscando correos para pedido {numero_pedido}")
                graph_data = self.graph_service.buscar_correos_por_pedido(str(numero_pedido))
                resultado["graph"] = graph_data

                self._registrar_log(
                    tipo=LogConsulta.TipoConsulta.GRAPH,
                    parametros={"numero_pedido": numero_pedido},
                    exitosa=True,
                    inicio=inicio
                )
            except GraphSearchException as e:
                error_msg = f"Error Graph: {str(e)}"
                resultado["errores"].append(error_msg)
                logger.error(error_msg)

                self._registrar_log(
                    tipo=LogConsulta.TipoConsulta.GRAPH,
                    parametros={"numero_pedido": numero_pedido},
                    exitosa=False,
                    mensaje_error=str(e),
                    inicio=inicio
                )

        # 3. Consolidar y guardar
        try:
            pedidos_guardados = self._consolidar_y_guardar(
                numero_pedido,
                resultado["supplos"],
                resultado["graph"]
            )
            resultado["pedidos_guardados"] = pedidos_guardados
            resultado["consolidado"] = True

            self._registrar_log(
                tipo=LogConsulta.TipoConsulta.CONSOLIDACION,
                parametros={
                    "numero_pedido": numero_pedido,
                    "pedidos_creados": len(pedidos_guardados)
                },
                exitosa=True,
                inicio=inicio
            )
        except Exception as e:
            error_msg = f"Error consolidando: {str(e)}"
            resultado["errores"].append(error_msg)
            resultado["consolidado"] = False
            logger.error(error_msg, exc_info=True)

        return resultado

    @transaction.atomic
    def _consolidar_y_guardar(
        self,
        numero_pedido: int,
        supplos_data: Optional[Dict],
        graph_data: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Consolida datos de ambas fuentes y guarda/actualiza en base de datos.
        """
        if supplos_data and supplos_data.get("status") == "OK":
            return self._procesar_items_supplos(supplos_data, numero_pedido, graph_data)

        if graph_data and graph_data.get("status") == "OK" and graph_data.get("data"):
            return self._procesar_solo_graph(graph_data, numero_pedido)

        return []

    def _procesar_items_supplos(
        self,
        supplos_data: Dict,
        numero_pedido: int,
        graph_data: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """Procesa todos los items de Supplos y los consolida con datos de Graph."""
        pedidos_guardados = []
        data = supplos_data.get("data", {})

        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("data", data.get("items", [data]))
            if not isinstance(items, list):
                items = [items]

        logger.info(f"Procesando {len(items)} items de Supplos")

        for item in items:
            if not item:
                continue
            entrada = self._procesar_item_supplos(item, numero_pedido, graph_data)
            if entrada:
                pedidos_guardados.append(entrada)

        return pedidos_guardados

    def _procesar_item_supplos(
        self,
        item: Dict[str, Any],
        numero_pedido: int,
        graph_data: Optional[Dict]
    ) -> Optional[Dict[str, Any]]:
        """Procesa un item individual de Supplos: mapea, enriquece, guarda y registra."""
        doc_compras = str(item.get("documento_compras", item.get("npedido", numero_pedido)))
        posicion = str(item.get("pos", item.get("posicion", ""))) or None

        pedido_existente = Pedido.objects.filter(
            documento_compras=doc_compras,
            posicion=posicion
        ).first()
        estado_anterior = pedido_existente.estado_pedido if pedido_existente else None

        pedido_data = self._mapear_supplos_a_dict(item, numero_pedido)
        observaciones_graph = self._enriquecer_con_graph(pedido_data, graph_data, posicion)

        pedido = self._guardar_pedido(pedido_data)
        self._registrar_trazabilidad(
            pedido=pedido,
            estado_anterior=estado_anterior,
            fuente=TrazabilidadPedido.FuenteDatos.SUPPLOS,
            datos_raw=item,
            observaciones_graph=observaciones_graph
        )

        if graph_data and graph_data.get("status") == "OK":
            self._marcar_correos_procesados(graph_data.get("data", []), pedido)

        return {
            "id": pedido.id,
            "documento_compras": pedido.documento_compras,
            "posicion": pedido.posicion,
            "estado": pedido.estado_pedido,
            "es_nuevo": estado_anterior is None
        }

    def _enriquecer_con_graph(
        self,
        pedido_data: Dict[str, Any],
        graph_data: Optional[Dict],
        posicion: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Enriquece pedido_data con observaciones extraidas de correos Graph."""
        if not (graph_data and graph_data.get("status") == "OK"):
            return None

        observaciones_graph = self._extraer_observaciones_graph(graph_data.get("data", []))
        if not observaciones_graph:
            return None

        posiciones_correo = observaciones_graph.get("posiciones_correo", [])
        if posiciones_correo and posicion:
            obs_posicion = self._buscar_obs_por_posicion(posicion, posiciones_correo)
            if obs_posicion:
                pedido_data["observaciones"] = obs_posicion
        elif observaciones_graph.get("observaciones"):
            pedido_data["observaciones"] = observaciones_graph.get("observaciones")

        if observaciones_graph.get("observaciones_cielo"):
            pedido_data["observaciones_cielo"] = observaciones_graph.get("observaciones_cielo")
        pedido_data["fuente_graph"] = True

        return observaciones_graph

    def _procesar_solo_graph(
        self,
        graph_data: Dict,
        numero_pedido: int
    ) -> List[Dict[str, Any]]:
        """Crea un registro basico cuando solo hay datos de Graph (sin Supplos)."""
        logger.info("Solo hay datos de Graph, creando registro basico")
        observaciones = self._extraer_observaciones_graph(graph_data.get("data", []))

        pedido_data = {
            "documento_compras": str(numero_pedido),
            "fuente_supplos": False,
            "fuente_graph": True,
            "observaciones": observaciones.get("observaciones") if observaciones else None,
        }

        pedido = self._guardar_pedido(pedido_data)

        if observaciones:
            self._registrar_trazabilidad(
                pedido=pedido,
                estado_anterior=None,
                fuente=TrazabilidadPedido.FuenteDatos.GRAPH,
                datos_raw=None,
                observaciones_graph=observaciones
            )

        self._marcar_correos_procesados(graph_data.get("data", []), pedido)

        return [{
            "id": pedido.id,
            "documento_compras": pedido.documento_compras,
            "posicion": pedido.posicion,
            "solo_graph": True
        }]

    def _marcar_correos_procesados(self, correos: List[Dict], pedido: Pedido) -> None:
        """
        Marca los correos como procesados para evitar duplicados en futuras consultas.
        """
        for correo in correos:
            try:
                self.graph_service.marcar_correo_procesado(
                    email_id=correo.get("email_id"),
                    buzon=correo.get("buzon", ""),
                    subject=correo.get("subject", ""),
                    fecha_email=correo.get("received_date"),
                    pedido=pedido
                )
            except Exception as e:
                logger.warning(f"Error marcando correo como procesado: {str(e)}")

    def _mapear_supplos_a_dict(self, item: Dict[str, Any], numero_pedido: int) -> Dict[str, Any]:
        """
        Mapea datos de Supplos a un diccionario para crear/actualizar Pedido.
        """
        return {
            "documento_compras": str(item.get("documento_compras", item.get("npedido", numero_pedido))),
            "posicion": str(item.get("pos", item.get("posicion", ""))) or None,
            "proveedor_centro_suministrador": item.get("proveedor_centro_suministrador", item.get("proveedor", "")),
            "razon_social": item.get("razon_social", ""),
            "comprador": self._extraer_comprador(item.get("comprador")),
            "organizacion_compras": item.get("organizacion_compras", item.get("org_compras", "")),
            "planta": item.get("planta", ""),
            "material": item.get("material", item.get("codigo_material", "")),
            "texto_breve": item.get("texto_breve", item.get("descripcion", "")),
            "cantidad_pedido": self._safe_decimal(item.get("cantidad_pedido", item.get("cantidad", 0))),
            "por_entregar": self._safe_decimal(item.get("por_entregar", item.get("pendiente", 0))),
            "precio_neto": self._safe_decimal(item.get("precio_neto", item.get("precio", 0))),
            "fecha_entrega": self._parsear_fecha(item.get("fecha_entrega")),
            "fecha_programada": self._parsear_fecha(item.get("fecha_programada")),
            "estado_pedido": self._mapear_estado(item.get("estado_pedido", item.get("estado", "Vigente"))),
            "motivo": item.get("motivo", ""),
            "observaciones": item.get("observacion_proveedor", item.get("observaciones", "")),
            "estado": item.get("estado", ""),
            "observaciones_cielo": item.get("observacion_corona", item.get("observaciones_cielo", "")),
            "fuente_supplos": True,
            "datos_raw_supplos": item,
        }

    def _buscar_obs_por_posicion(self, posicion: str, posiciones_correo: List[Dict]) -> Optional[str]:
        """
        Busca la observacion correspondiente a una posicion especifica.
        Normaliza posiciones: Supplos usa '00030', el correo usa '30'.
        """
        try:
            pos_num = int(posicion)
        except (ValueError, TypeError):
            return None

        for pos_data in posiciones_correo:
            try:
                pos_correo_num = int(pos_data.get("posicion", "0"))
            except (ValueError, TypeError):
                continue
            if pos_num == pos_correo_num:
                return pos_data.get("comentario")

        return None

    def _extraer_comprador(self, comprador_data) -> str:
        """Extrae el nombre del comprador de diferentes formatos."""
        if isinstance(comprador_data, dict):
            return comprador_data.get("nombre", str(comprador_data))
        return str(comprador_data) if comprador_data else ""

    def _extraer_observaciones_graph(self, correos: List[Dict]) -> Optional[Dict[str, Any]]:
        """
        Extrae observaciones del proveedor de los correos encontrados.

        - Guarda SOLO el comentario mas reciente en observaciones
        - Guarda todos los correos en historial_correos para trazabilidad
        """
        if not correos:
            return None

        correos_ordenados = sorted(
            correos,
            key=lambda x: x.get("received_date") or "",
            reverse=True
        )

        observacion_mas_reciente = None
        observacion_cielo_mas_reciente = None
        email_info = None
        historial_correos = []

        for correo in correos_ordenados:
            obs_proveedor, obs_cielo = self._extraer_obs_correo(correo)
            historial_correos.append(self._construir_entrada_historial(correo, obs_proveedor, obs_cielo))

            if not observacion_mas_reciente and obs_proveedor:
                observacion_mas_reciente = obs_proveedor
                email_info = self._extraer_email_info(correo)

            if not observacion_cielo_mas_reciente and obs_cielo:
                observacion_cielo_mas_reciente = obs_cielo

            if not observacion_mas_reciente:
                observacion_mas_reciente, email_info = self._fallback_datos_extraidos(correo, email_info)

        if not observacion_mas_reciente and not observacion_cielo_mas_reciente and not historial_correos:
            return None

        posiciones_correo = next(
            (c.get("posiciones_correo", []) for c in correos_ordenados if c.get("posiciones_correo")),
            []
        )

        logger.info(f"Correos encontrados: {len(historial_correos)}")
        logger.info(f"Observacion mas reciente: {observacion_mas_reciente}")
        logger.info(f"Posiciones con observacion: {len(posiciones_correo)}")

        return {
            "observaciones": observacion_mas_reciente,
            "observaciones_cielo": observacion_cielo_mas_reciente,
            "posiciones_correo": posiciones_correo,
            "historial_correos": historial_correos,
            "total_correos": len(historial_correos),
            **(email_info or {})
        }

    def _extraer_obs_correo(self, correo: Dict) -> tuple:
        """Extrae observaciones_proveedor y observaciones_cielo de un correo."""
        return correo.get("observaciones_proveedor"), correo.get("observaciones_cielo")

    def _construir_entrada_historial(self, correo: Dict, obs_proveedor, obs_cielo) -> Dict:
        """Construye la entrada de historial para un correo."""
        return {
            "email_id": correo.get("email_id"),
            "subject": correo.get("subject"),
            "from": correo.get("from"),
            "received_date": str(correo.get("received_date")) if correo.get("received_date") else None,
            "observaciones_proveedor": obs_proveedor,
            "observaciones_cielo": obs_cielo,
            "posiciones": correo.get("posiciones_correo", [])
        }

    def _extraer_email_info(self, correo: Dict) -> Dict:
        """Extrae informacion del email como dict."""
        return {
            "email_id": correo.get("email_id"),
            "email_subject": correo.get("subject"),
            "email_from": correo.get("from"),
            "email_date": correo.get("received_date"),
        }

    def _fallback_datos_extraidos(self, correo: Dict, email_info) -> tuple:
        """Usa datos_extraidos como fallback si no hay observaciones directas."""
        datos = correo.get("datos_extraidos", {})
        obs = datos.get("observaciones_proveedor")
        if obs and not email_info:
            return obs, self._extraer_email_info(correo)
        return obs, email_info

    def _guardar_pedido(
        self,
        pedido_data: Dict[str, Any]
    ) -> Pedido:
        """
        Guarda o actualiza el pedido usando update_or_create.
        """
        documento_compras = pedido_data.pop("documento_compras")
        posicion = pedido_data.pop("posicion", None)

        # Limpiar datos None para evitar sobrescribir con valores vacios
        defaults = {k: v for k, v in pedido_data.items() if v is not None and v != ""}

        pedido, created = Pedido.objects.update_or_create(
            documento_compras=documento_compras,
            posicion=posicion,
            defaults=defaults
        )

        logger.info(f"Pedido {documento_compras} {'creado' if created else 'actualizado'}")
        return pedido

    def _registrar_trazabilidad(
        self,
        pedido: Pedido,
        estado_anterior: Optional[str],
        fuente: str,
        datos_raw: Optional[Dict],
        observaciones_graph: Optional[Dict] = None
    ) -> None:
        """
        Registra un evento en la trazabilidad del pedido.
        Guarda el historial completo de correos encontrados.
        """
        trazabilidad_data = {
            "pedido": pedido,
            "fuente": fuente,
            "estado_anterior": estado_anterior,
            "estado_nuevo": pedido.estado_pedido,
            "observaciones": pedido.observaciones,
            "datos_raw": datos_raw,
        }

        # Agregar info del correo si existe
        if observaciones_graph:
            trazabilidad_data.update({
                "observaciones_proveedor": observaciones_graph.get("observaciones"),
                "email_id": observaciones_graph.get("email_id"),
                "email_subject": observaciones_graph.get("email_subject"),
                "email_from": observaciones_graph.get("email_from"),
                "email_date": observaciones_graph.get("email_date"),
            })

            # Guardar historial completo de correos en datos_raw
            historial = observaciones_graph.get("historial_correos", [])
            if historial:
                if trazabilidad_data.get("datos_raw"):
                    trazabilidad_data["datos_raw"]["historial_correos"] = historial
                    trazabilidad_data["datos_raw"]["total_correos"] = len(historial)
                else:
                    trazabilidad_data["datos_raw"] = {
                        "historial_correos": historial,
                        "total_correos": len(historial)
                    }
                logger.info(f"Guardando historial de {len(historial)} correos en trazabilidad")

        TrazabilidadPedido.objects.create(**trazabilidad_data)
        logger.info(f"Trazabilidad registrada para pedido {pedido.documento_compras}")

    def _parsear_fecha(self, fecha_str: Any) -> Optional[datetime]:
        """Parsea diferentes formatos de fecha."""
        if not fecha_str or fecha_str == "None":
            return None

        if isinstance(fecha_str, (datetime,)):
            return fecha_str

        fecha_str = str(fecha_str).strip()

        # Formato Supplos: DDMMYYYY o DDMMYYYY HH:MM:SS.mmm
        if len(fecha_str) >= 8 and fecha_str[:8].isdigit():
            try:
                day = int(fecha_str[0:2])
                month = int(fecha_str[2:4])
                year = int(fecha_str[4:8])
                return datetime(year, month, day)
            except ValueError:
                pass

        # Formatos estandar
        formatos = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%d.%m.%Y",
        ]

        for formato in formatos:
            try:
                return datetime.strptime(fecha_str, formato)
            except ValueError:
                continue

        logger.warning(f"No se pudo parsear fecha: {fecha_str}")
        return None

    def _mapear_estado(self, estado: str) -> str:
        """Mapea el estado de Supplos al enum del modelo."""
        if not estado:
            return Pedido.EstadoPedido.VIGENTE

        estado_lower = str(estado).lower().strip()

        mapeo = {
            'vigente': Pedido.EstadoPedido.VIGENTE,
            'pendiente': Pedido.EstadoPedido.PENDIENTE,
            'en proceso': Pedido.EstadoPedido.PENDIENTE,
            'en_proceso': Pedido.EstadoPedido.PENDIENTE,
            'entregado': Pedido.EstadoPedido.ENTREGADO,
            'parcial': Pedido.EstadoPedido.PARCIAL,
            'entrega parcial': Pedido.EstadoPedido.PARCIAL,
            'cancelado': Pedido.EstadoPedido.CANCELADO,
            'en transito': Pedido.EstadoPedido.EN_TRANSITO,
            'en tránsito': Pedido.EstadoPedido.EN_TRANSITO,
        }

        return mapeo.get(estado_lower, Pedido.EstadoPedido.VIGENTE)

    def _safe_decimal(self, value: Any) -> Decimal:
        """Convierte un valor a Decimal de forma segura."""
        if value is None or value == "" or value == "None":
            return Decimal("0")
        try:
            # Limpiar caracteres no numericos excepto punto y coma
            if isinstance(value, str):
                value = value.replace(",", ".").replace(" ", "")
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return Decimal("0")

    def _registrar_log(
        self,
        tipo: str,
        parametros: Dict,
        exitosa: bool,
        inicio: datetime,
        mensaje_error: str = None
    ) -> None:
        """Registra la consulta en el log."""
        fin = timezone.now()
        tiempo_ms = int((fin - inicio).total_seconds() * 1000)

        LogConsulta.objects.create(
            tipo=tipo,
            parametros=parametros,
            respuesta_exitosa=exitosa,
            mensaje_error=mensaje_error,
            tiempo_respuesta_ms=tiempo_ms,
            usuario=self.user
        )
