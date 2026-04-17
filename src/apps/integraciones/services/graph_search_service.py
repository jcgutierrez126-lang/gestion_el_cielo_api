import os
import re
import base64
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, Any, List
from datetime import datetime
from cieloapi.correo import get_access_token
import logging
from apps.integraciones.services.ai_extraction_service import AIExtractionService
from apps.integraciones.services.azure_document_service import AzureDocumentService

logger = logging.getLogger(__name__)

# Asuntos de correo permitidos para busqueda de observaciones
# Se validan con substring match case-insensitive
ASUNTOS_PERMITIDOS = [
    "seguimiento a pedidos pendientes",
    "estado de entrega",
    "seguimiento órdenes de compra",
    "seguimiento ordenes de compra",
    "pedidos de compras",
    "seguiminetos pedidos",
    "seguimineto loceria",
]

# Keywords usados para buscar en Graph API ($search)
KEYWORDS_BUSQUEDA = [
    "seguimiento a pedidos pendientes",
    "estado de entrega",
    "seguimiento ordenes compra",
    "pedidos de compras",
]

# Extensiones de adjuntos procesables con Azure Document Intelligence
EXTENSIONES_AZURE_DI = ('.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp')


class GraphSearchException(Exception):
    """Excepcion personalizada para errores del servicio Graph."""
    pass


class GraphSearchService:
    """
    Servicio para buscar correos relacionados a pedidos usando Microsoft Graph.
    Reutiliza la autenticacion MSAL existente en correo.py.
    Solo busca en los buzones autorizados configurados en CorreoAutorizado.
    Filtra correos por asuntos permitidos (seguimiento, estado de entrega, etc).
    Usa IA (OpenAI GPT) exclusivamente para extraer observaciones de correos.

    Optimizaciones de rendimiento:
    - Busquedas por keyword en paralelo (ThreadPoolExecutor)
    - Busquedas en multiples buzones en paralelo
    - Extraccion IA en paralelo para multiples correos
    - Omite IA para correos ya procesados (CorreoProcesado)
    """

    def __init__(self):
        self.graph_base_url = "https://graph.microsoft.com/v1.0"
        self.ai_service = AIExtractionService()
        self.azure_service = AzureDocumentService()

    def _get_token(self) -> str:
        """Obtiene el token de acceso usando la funcion existente."""
        result = get_access_token()
        if result["status"] != "OK":
            raise GraphSearchException(f"Error obteniendo token: {result.get('message')}")
        return result["access"]

    def _get_buzones_autorizados(self) -> List[str]:
        """Obtiene la lista de buzones autorizados para buscar."""
        from apps.integraciones.models import CorreoAutorizado
        return CorreoAutorizado.get_correos_activos()

    def _get_buzon_principal(self) -> Optional[str]:
        """Obtiene el buzon principal configurado."""
        from apps.integraciones.models import CorreoAutorizado
        buzon = CorreoAutorizado.get_buzon_principal()
        return buzon

    def _correo_ya_procesado(self, email_id: str) -> bool:
        """Verifica si un correo ya fue procesado."""
        from apps.integraciones.models import CorreoProcesado
        return CorreoProcesado.ya_procesado(email_id)

    def _registrar_correo_procesado(
        self,
        email_id: str,
        buzon: str,
        subject: str,
        fecha_email: datetime,
        pedido=None
    ) -> None:
        """Registra un correo como procesado."""
        from apps.integraciones.models import CorreoProcesado

        correo_proc, created = CorreoProcesado.objects.get_or_create(
            email_id=email_id,
            defaults={
                'buzon': buzon,
                'subject': subject[:500] if subject else None,
                'fecha_email': fecha_email,
            }
        )

        if pedido and not created:
            correo_proc.pedidos_relacionados.add(pedido)

    # =========================================================================
    # FLUJO PRINCIPAL DE BUSQUEDA (OPTIMIZADO CON PARALELISMO)
    # =========================================================================

    def buscar_correos_por_pedido(
        self,
        numero_pedido: str,
        max_results: int = 50
    ) -> Dict[str, Any]:
        """
        Busca correos relacionados al pedido en buzones autorizados.
        Ejecuta busquedas en paralelo por buzon y por keyword.
        Extrae observaciones con IA en paralelo.
        Omite IA para correos ya procesados previamente.

        Args:
            numero_pedido: Numero del pedido a buscar
            max_results: Numero maximo de resultados por keyword

        Returns:
            Diccionario con los correos encontrados
        """
        logger.info("=" * 60)
        logger.info(f"INICIANDO BUSQUEDA DE CORREOS PARA PEDIDO: {numero_pedido}")
        logger.info("=" * 60)

        try:
            token = self._get_token()
            logger.info("Token de Graph obtenido correctamente")
        except Exception as e:
            logger.error(f"ERROR obteniendo token: {str(e)}")
            return {
                "status": "ERROR",
                "message": f"Error obteniendo token: {str(e)}",
                "data": [],
                "total": 0,
                "source": "graph"
            }

        buzones = self._get_buzones_autorizados()

        logger.info(f"Buzones autorizados encontrados: {buzones}")

        if not buzones:
            logger.warning("No hay buzones autorizados configurados")
            return {
                "status": "WARNING",
                "message": "No hay buzones autorizados configurados. Configure al menos un buzon en /admin/integraciones/correoautorizado/",
                "data": [],
                "total": 0,
                "source": "graph"
            }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        todos_los_correos = []

        # Buscar en todos los buzones en paralelo
        with ThreadPoolExecutor(max_workers=max(len(buzones), 1)) as executor:
            futures = {
                executor.submit(
                    self._buscar_en_buzon, buzon, numero_pedido, headers, max_results
                ): buzon
                for buzon in buzones
            }
            for future in as_completed(futures):
                buzon = futures[future]
                try:
                    correos_buzon = future.result()
                    todos_los_correos.extend(correos_buzon)
                except Exception as e:
                    logger.warning(f"Error buscando en buzon {buzon}: {str(e)}")

        # Ordenar por fecha (mas reciente primero)
        todos_los_correos.sort(
            key=lambda x: x.get("received_date") or datetime.min,
            reverse=True
        )

        logger.info(f"Encontrados {len(todos_los_correos)} correos totales para pedido {numero_pedido}")

        return {
            "status": "OK",
            "data": todos_los_correos,
            "total": len(todos_los_correos),
            "buzones_consultados": buzones,
            "source": "graph"
        }

    def _buscar_en_buzon(
        self,
        buzon: str,
        numero_pedido: str,
        headers: Dict[str, str],
        max_results: int
    ) -> List[Dict[str, Any]]:
        """
        Busca correos en un buzon especifico en 3 fases:
          1. Busquedas por keyword en paralelo (Graph API)
          2. Filtrado local (asunto + pedido en body)
          3. Extraccion IA en paralelo (omite correos ya procesados)
        """
        url = f"{self.graph_base_url}/users/{buzon}/messages"
        select_fields = "id,subject,from,receivedDateTime,bodyPreview,body,hasAttachments"

        correos_raw = self._fase1_busqueda_keywords(url, headers, select_fields, max_results, buzon)
        correos_unicos = self._deduplicar_correos(correos_raw)
        correos_filtrados = [
            f for c in correos_unicos
            if (f := self._filtrar_correo(c, numero_pedido))
        ]

        logger.info(
            f"Buzon {buzon}: {len(correos_raw)} raw, "
            f"{len(correos_unicos)} unicos, {len(correos_filtrados)} relevantes"
        )

        if not correos_filtrados:
            return []

        correos_resultado, correos_para_ia = self._separar_procesados(correos_filtrados, buzon)
        correos_resultado.extend(
            self._fase3_extraccion_ia(correos_para_ia, numero_pedido, headers, buzon)
        )

        logger.info(
            f"Total correos procesados para pedido {numero_pedido} en {buzon}: "
            f"{len(correos_resultado)} ({len(correos_para_ia)} con IA, "
            f"{len(correos_filtrados) - len(correos_para_ia)} ya procesados)"
        )
        return correos_resultado

    def _fase1_busqueda_keywords(
        self,
        url: str,
        headers: Dict[str, str],
        select_fields: str,
        max_results: int,
        buzon: str
    ) -> List[Dict[str, Any]]:
        """Ejecuta todas las busquedas por keyword en paralelo."""
        todos_los_correos_raw = []
        with ThreadPoolExecutor(max_workers=len(KEYWORDS_BUSQUEDA)) as executor:
            futures = {
                executor.submit(
                    self._buscar_por_keyword, url, keyword, headers, select_fields, max_results, buzon
                ): keyword
                for keyword in KEYWORDS_BUSQUEDA
            }
            for future in as_completed(futures):
                keyword = futures[future]
                try:
                    todos_los_correos_raw.extend(future.result())
                except Exception as e:
                    logger.warning(f"  Error en busqueda por asunto '{keyword}': {str(e)}")
        return todos_los_correos_raw

    def _deduplicar_correos(self, correos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Elimina correos duplicados por email ID."""
        vistos: set = set()
        resultado = []
        for correo in correos:
            eid = correo.get("id")
            if eid and eid not in vistos:
                vistos.add(eid)
                resultado.append(correo)
        return resultado

    def _separar_procesados(
        self,
        correos_filtrados: List[Dict[str, Any]],
        buzon: str
    ) -> tuple:
        """Separa correos ya procesados de los que necesitan extraccion IA."""
        correos_resultado = []
        correos_para_ia = []
        for correo_f in correos_filtrados:
            if self._correo_ya_procesado(correo_f["email_id"]):
                logger.info(f"  Correo ya procesado, omitiendo IA: '{correo_f['subject'][:60]}'")
                correos_resultado.append(
                    self._construir_resultado(correo_f, buzon, self._empty_extraction())
                )
            else:
                correos_para_ia.append(correo_f)
        return correos_resultado, correos_para_ia

    def _fase3_extraccion_ia(
        self,
        correos_para_ia: List[Dict[str, Any]],
        numero_pedido: str,
        headers: Dict[str, str],
        buzon: str
    ) -> List[Dict[str, Any]]:
        """Extrae datos con IA en paralelo para correos no procesados."""
        if not correos_para_ia:
            return []

        correos_resultado = []
        workers_ia = min(len(correos_para_ia), 5)
        with ThreadPoolExecutor(max_workers=workers_ia) as executor:
            futures = {
                executor.submit(
                    self._extraer_datos_con_routing, cf, numero_pedido, headers, buzon
                ): cf
                for cf in correos_para_ia
            }
            for future in as_completed(futures):
                correo_f = futures[future]
                try:
                    datos = future.result()
                except Exception as e:
                    logger.error(f"Error extraccion IA: {str(e)}")
                    datos = self._empty_extraction()
                correos_resultado.append(self._construir_resultado(correo_f, buzon, datos))
                logger.info(f"  MATCH: '{correo_f['subject'][:80]}'")
        return correos_resultado

    # =========================================================================
    # METODOS AUXILIARES DEL FLUJO DE BUSQUEDA
    # =========================================================================

    def _buscar_por_keyword(
        self,
        url: str,
        keyword: str,
        headers: Dict[str, str],
        select_fields: str,
        max_results: int,
        buzon: str
    ) -> List[Dict[str, Any]]:
        """Ejecuta una busqueda $search por keyword en Graph API."""
        params = {
            "$search": f'"{keyword}"',
            "$top": max_results,
            "$select": select_fields,
        }
        try:
            response = requests.get(url, headers=headers, params=params, timeout=60)
            if response.status_code == 200:
                correos = response.json().get("value", [])
                logger.info(f"  '{keyword}' en {buzon}: {len(correos)} correos")
                return correos
            else:
                logger.warning(f"  Busqueda '{keyword}' fallo: {response.status_code}")
                return []
        except Exception as e:
            logger.warning(f"  Error en busqueda '{keyword}': {str(e)}")
            return []

    def _filtrar_correo(
        self,
        correo: Dict[str, Any],
        numero_pedido: str
    ) -> Optional[Dict[str, Any]]:
        """
        Filtra un correo por asunto permitido y numero de pedido en el body.
        Retorna dict con datos relevantes si pasa los filtros, o None.
        No llama a IA - solo filtrado local rapido.
        """
        body_content = correo.get("body", {}).get("content", "")
        subject = correo.get("subject", "") or ""

        # Verificar asunto permitido
        subject_lower = subject.lower()
        if not any(keyword in subject_lower for keyword in ASUNTOS_PERMITIDOS):
            return None

        # Verificar que el pedido aparezca en el body
        body_text = re.sub(r'<[^>]+>', '', body_content)
        if numero_pedido not in body_content and numero_pedido not in body_text:
            return None

        # Parsear fecha
        received_date = correo.get("receivedDateTime")
        if received_date:
            try:
                received_date = datetime.fromisoformat(received_date.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                pass

        return {
            "email_id": correo.get("id"),
            "subject": subject,
            "body_content": body_content,
            "body_preview": correo.get("bodyPreview", ""),
            "from_address": correo.get("from", {}).get("emailAddress", {}).get("address"),
            "from_name": correo.get("from", {}).get("emailAddress", {}).get("name"),
            "received_date": received_date,
            "has_attachments": correo.get("hasAttachments", False),
        }

    def _construir_resultado(
        self,
        correo_filtrado: Dict[str, Any],
        buzon: str,
        datos_extraidos: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Construye el dict de resultado final a partir de correo filtrado + datos IA."""
        return {
            "email_id": correo_filtrado["email_id"],
            "buzon": buzon,
            "subject": correo_filtrado["subject"],
            "from": correo_filtrado["from_address"],
            "from_name": correo_filtrado["from_name"],
            "received_date": correo_filtrado["received_date"],
            "has_attachments": correo_filtrado["has_attachments"],
            "body_preview": correo_filtrado["body_preview"],
            "datos_extraidos": datos_extraidos,
            "observaciones_proveedor": datos_extraidos.get("observaciones_proveedor"),
            "observaciones_cielo": datos_extraidos.get("observaciones_cielo"),
            "posiciones_correo": datos_extraidos.get("posiciones_correo", []),
            "extraido_con_ia": datos_extraidos.get("extraido_con_ia", False),
            "resumen_ia": datos_extraidos.get("resumen_ia"),
        }

    def _empty_extraction(self) -> Dict[str, Any]:
        """Retorna respuesta vacia de extraccion (para correos ya procesados o sin IA)."""
        return {
            "observaciones_proveedor": None,
            "observaciones_cielo": None,
            "estado_mencionado": None,
            "fecha_entrega_mencionada": None,
            "motivo": None,
            "posiciones_correo": [],
            "extraido_con_ia": False,
            "resumen_ia": None,
        }

    # =========================================================================
    # EXTRACCION CON IA
    # =========================================================================

    def _extraer_datos_contenido(
        self,
        html_content: str,
        numero_pedido: str,
        asunto: str = ""
    ) -> Dict[str, Any]:
        """
        Extrae datos estructurados del contenido del correo usando IA (OpenAI GPT).
        No tiene fallback a regex - la IA es el unico metodo de extraccion.

        Args:
            html_content: Contenido HTML del correo
            numero_pedido: Numero de pedido para contexto
            asunto: Asunto del correo para contexto adicional

        Returns:
            Diccionario con datos extraidos
        """
        if not self.ai_service.is_available():
            logger.warning(f"OpenAI no disponible para pedido {numero_pedido}")
            result = self._empty_extraction()
            result["error_extraccion"] = "OpenAI API no configurada. Configure OPENAI_API_KEY."
            return result

        logger.info(f"Usando IA para extraer observaciones del pedido {numero_pedido}")
        try:
            datos_ia = self.ai_service.extraer_observaciones_correo(
                contenido_correo=html_content,
                numero_pedido=numero_pedido,
                asunto=asunto
            )

            if datos_ia.get("extraido_con_ia") and datos_ia.get("observaciones_proveedor"):
                logger.info(f"Extraccion con IA exitosa: {datos_ia.get('observaciones_proveedor', '')[:100]}...")
            else:
                logger.info(f"IA no encontro observaciones en correo para pedido {numero_pedido}")

            return datos_ia

        except Exception as e:
            logger.error(f"Error en extraccion IA para pedido {numero_pedido}: {str(e)}")
            result = self._empty_extraction()
            result["error_extraccion"] = f"Error en extraccion IA: {str(e)}"
            return result

    # =========================================================================
    # ROUTING: AZURE DOCUMENT INTELLIGENCE O HTML
    # =========================================================================

    def _extraer_datos_con_routing(
        self,
        correo_filtrado: Dict[str, Any],
        numero_pedido: str,
        headers: Dict[str, str],
        buzon: str
    ) -> Dict[str, Any]:
        """
        Decide la ruta de extraccion:
        - Si el correo tiene adjuntos PDF/imagen y Azure DI esta disponible:
          descarga adjuntos -> Azure DI -> OpenAI
        - Si no: flujo existente (HTML body -> OpenAI)
        """
        if (
            correo_filtrado.get("has_attachments")
            and self.azure_service.is_available()
        ):
            try:
                texto_adjuntos = self._procesar_adjuntos_con_azure(
                    email_id=correo_filtrado["email_id"],
                    buzon=buzon,
                    headers=headers,
                    numero_pedido=numero_pedido
                )
                if texto_adjuntos:
                    logger.info(
                        f"Usando texto de Azure DI para extraccion IA "
                        f"(pedido {numero_pedido}, {len(texto_adjuntos)} chars)"
                    )
                    return self._extraer_datos_contenido(
                        texto_adjuntos,
                        numero_pedido,
                        correo_filtrado["subject"]
                    )
            except Exception as e:
                logger.warning(
                    f"Error en ruta Azure DI, cayendo al flujo HTML: {e}"
                )

        return self._extraer_datos_contenido(
            correo_filtrado["body_content"],
            numero_pedido,
            correo_filtrado["subject"]
        )

    def _procesar_adjuntos_con_azure(
        self,
        email_id: str,
        buzon: str,
        headers: Dict[str, str],
        numero_pedido: str
    ) -> Optional[str]:
        """
        Descarga adjuntos PDF/imagen de un correo y extrae texto con Azure DI.

        Returns:
            Texto extraido de los adjuntos, o None si no hay adjuntos procesables
        """
        try:
            url = f"{self.graph_base_url}/users/{buzon}/messages/{email_id}/attachments"
            response = requests.get(url, headers=headers, timeout=60)
            response.raise_for_status()
            adjuntos_raw = response.json().get("value", [])
        except Exception as e:
            logger.error(f"Error obteniendo adjuntos de Graph: {e}")
            return None

        adjuntos_procesables = []
        for adjunto in adjuntos_raw:
            odata_type = adjunto.get("@odata.type", "")
            if "#microsoft.graph.fileAttachment" not in odata_type:
                continue

            nombre = (adjunto.get("name") or "").lower()
            if any(nombre.endswith(ext) for ext in EXTENSIONES_AZURE_DI):
                content_bytes_b64 = adjunto.get("contentBytes")
                if content_bytes_b64:
                    try:
                        contenido = base64.b64decode(content_bytes_b64)
                        adjuntos_procesables.append({
                            "name": adjunto.get("name"),
                            "content_type": adjunto.get("contentType", "application/octet-stream"),
                            "contenido_bytes": contenido,
                        })
                    except Exception as e:
                        logger.warning(f"Error decodificando adjunto {nombre}: {e}")

        if not adjuntos_procesables:
            logger.info(f"No hay adjuntos PDF/imagen procesables para pedido {numero_pedido}")
            return None

        logger.info(
            f"Procesando {len(adjuntos_procesables)} adjuntos con Azure DI "
            f"para pedido {numero_pedido}"
        )

        return self.azure_service.extraer_texto_multiples(adjuntos_procesables)

    # =========================================================================
    # OTROS METODOS
    # =========================================================================

    def obtener_adjuntos(self, email_id: str, buzon: str = None) -> List[Dict[str, Any]]:
        """
        Obtiene los adjuntos de un correo especifico.

        Args:
            email_id: ID del correo en Graph
            buzon: Buzon donde esta el correo (si no se especifica, usa el principal)

        Returns:
            Lista de adjuntos con metadatos
        """
        token = self._get_token()

        if not buzon:
            buzon = self._get_buzon_principal()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(
                f"{self.graph_base_url}/users/{buzon}/messages/{email_id}/attachments",
                headers=headers,
                timeout=60
            )
            response.raise_for_status()

            adjuntos = response.json().get("value", [])

            resultado = []
            for adjunto in adjuntos:
                # Filtrar solo archivos relevantes
                nombre = adjunto.get("name", "").lower()
                if nombre.endswith(('.xlsx', '.xls', '.pdf', '.csv')):
                    resultado.append({
                        "id": adjunto.get("id"),
                        "name": adjunto.get("name"),
                        "content_type": adjunto.get("contentType"),
                        "size": adjunto.get("size"),
                    })

            return resultado

        except Exception as e:
            logger.error(f"Error obteniendo adjuntos: {str(e)}")
            return []

    def marcar_correo_procesado(
        self,
        email_id: str,
        buzon: str,
        subject: str,
        fecha_email: datetime,
        pedido=None
    ) -> None:
        """
        Marca un correo como procesado (metodo publico).

        Args:
            email_id: ID del correo
            buzon: Buzon de origen
            subject: Asunto del correo
            fecha_email: Fecha del correo
            pedido: Pedido relacionado (opcional)
        """
        self._registrar_correo_procesado(
            email_id=email_id,
            buzon=buzon,
            subject=subject,
            fecha_email=fecha_email,
            pedido=pedido
        )
