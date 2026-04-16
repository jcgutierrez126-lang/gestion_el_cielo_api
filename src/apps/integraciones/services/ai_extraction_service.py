import os
import json
import logging
from typing import Optional, Dict, Any
from openai import OpenAI

logger = logging.getLogger(__name__)


class AIExtractionService:
    """
    Servicio para extraer observaciones de correos usando OpenAI GPT.
    Reemplaza la extraccion con regex por IA para mayor precision.
    """

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Modelo por defecto

        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)

    def is_available(self) -> bool:
        """Verifica si el servicio esta disponible."""
        return self.client is not None

    def extraer_observaciones_correo(
        self,
        contenido_correo: str,
        numero_pedido: str,
        asunto: str = ""
    ) -> Dict[str, Any]:
        """
        Extrae observaciones y datos relevantes del contenido de un correo
        usando GPT.

        Args:
            contenido_correo: Contenido HTML o texto del correo
            numero_pedido: Numero del pedido para contexto
            asunto: Asunto del correo

        Returns:
            Diccionario con observaciones extraidas
        """
        if not self.is_available():
            logger.warning("OpenAI no configurado, retornando vacio")
            return self._empty_response()

        try:
            # Limpiar y truncar contenido si es muy largo
            contenido_limpio = self._limpiar_contenido(contenido_correo)

            prompt = self._build_prompt(contenido_limpio, numero_pedido, asunto)

            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ]

            response = self._call_openai_with_retry(messages)

            resultado = response.choices[0].message.content
            datos = json.loads(resultado)

            logger.info(f"Extraccion IA exitosa para pedido {numero_pedido}")
            return self._normalizar_respuesta(datos)

        except json.JSONDecodeError as e:
            logger.error(f"Error parseando respuesta JSON de GPT: {str(e)}")
            return self._empty_response()
        except Exception as e:
            logger.error(f"Error en extraccion con IA: {str(e)}")
            return self._empty_response()

    def _call_openai_with_retry(self, messages, max_retries=2):
        """Llama a OpenAI con reintentos para fallas transitorias."""
        import time
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=1500,
                    response_format={"type": "json_object"}
                )
                return response
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    time.sleep(1 * (attempt + 1))
                    logger.warning(f"OpenAI retry {attempt + 1}/{max_retries}: {str(e)}")
                else:
                    raise last_error

    def _get_system_prompt(self) -> str:
        """Retorna el prompt del sistema para la extraccion."""
        return """Eres un asistente especializado en extraer informacion de correos
relacionados con pedidos de compra entre proveedores y Finca el Cielo.

CONTEXTO: Los correos de seguimiento a pedidos pueden tener dos formatos:

1. FORMATO TABLA: El correo contiene una tabla HTML con columnas como:
   "Fecha de entrega | Planta | Documento compras | Pos. | Material | Texto breve | Cantidad de pedido | Comentarios"
   - Debes encontrar las filas donde "Documento compras" coincide con el numero de pedido proporcionado
   - Para cada fila que coincida, extrae el numero de "Pos." y el contenido de "Comentarios"
   - Formatea como: "Pos 30: comentario aqui | Pos 40: otro comentario"
   - Si una fila NO tiene comentario o esta vacio, omitela

2. FORMATO PARRAFO: El correo contiene texto en prosa describiendo el estado
   del pedido, fechas de entrega, confirmaciones, problemas, etc.
   - Extrae la informacion relevante como observacion del proveedor

Tu tarea es extraer UNICAMENTE las observaciones, comentarios o notas que el
PROVEEDOR haya escrito sobre el pedido especifico. Estos pueden incluir:
- Comentarios por posicion de la tabla (formato "Pos X: comentario")
- Fechas de entrega prometidas o reprogramadas
- Confirmaciones de despacho o entrega
- Problemas, retrasos o motivos de demora
- Cualquier nota relevante del proveedor sobre ese pedido

NO extraigas:
- Datos de la tabla como material, cantidad, precio (solo los comentarios)
- Firmas de correo o pies de pagina
- Textos genericos o plantillas
- Saludos o despedidas
- Informacion sobre pedidos DIFERENTES al numero proporcionado

IMPORTANTE: Si el correo contiene multiples pedidos en una tabla, SOLO extrae
los comentarios de las filas que corresponden al numero de pedido indicado.

Responde SIEMPRE en formato JSON con esta estructura:
{
    "observaciones_proveedor": "Pos 30: Se entrego hoy | Pos 40: Se programa entrega en la fecha indicada",
    "observaciones_cielo": "texto de observaciones de Finca el Cielo si existe, o null",
    "estado_mencionado": "estado del pedido si se menciona o null",
    "fecha_entrega_mencionada": "fecha si se menciona en formato YYYY-MM-DD o null",
    "motivo": "motivo o razon si se menciona o null",
    "posiciones": [
        {
            "posicion": "30",
            "comentario": "Se entrego hoy",
            "fecha_entrega": "2025-10-14"
        }
    ],
    "resumen": "breve resumen de 1 linea del contenido relevante del correo"
}

Si no hay observaciones o comentarios del proveedor, responde con observaciones_proveedor como null."""

    def _build_prompt(
        self,
        contenido: str,
        numero_pedido: str,
        asunto: str
    ) -> str:
        """Construye el prompt para el usuario."""
        return f"""Extrae las observaciones del proveedor del siguiente correo.

NUMERO DE PEDIDO A BUSCAR: {numero_pedido}
ASUNTO DEL CORREO: {asunto}

INSTRUCCIONES:
- Si el correo tiene una tabla, busca las filas donde "Documento compras" contiene "{numero_pedido}"
- Para cada fila encontrada, extrae el numero de posicion ("Pos.") y el comentario de "Comentarios"
- Si el correo tiene texto en parrafos, extrae las observaciones relevantes al pedido {numero_pedido}
- Si hay "Observaciones Cielo:" en el texto, extrae esa informacion por separado en observaciones_cielo

CONTENIDO DEL CORREO:
{contenido}

Recuerda responder SOLO en formato JSON."""

    def _limpiar_contenido(self, html: str) -> str:
        """Limpia el contenido HTML y lo trunca si es necesario."""
        import re

        # Remover tags de estilo y script
        texto = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        texto = re.sub(r'<script[^>]*>.*?</script>', '', texto, flags=re.DOTALL | re.IGNORECASE)

        # Reemplazar <br> y </p> con saltos de linea
        texto = re.sub(r'<br\s*/?>', '\n', texto, flags=re.IGNORECASE)
        texto = re.sub(r'</p>', '\n', texto, flags=re.IGNORECASE)
        texto = re.sub(r'</tr>', '\n', texto, flags=re.IGNORECASE)
        texto = re.sub(r'</td>', ' | ', texto, flags=re.IGNORECASE)
        texto = re.sub(r'</th>', ' | ', texto, flags=re.IGNORECASE)

        # Remover otros tags HTML
        texto = re.sub(r'<[^>]+>', ' ', texto)

        # Decodificar entidades HTML
        texto = texto.replace('&nbsp;', ' ')
        texto = texto.replace('&amp;', '&')
        texto = texto.replace('&lt;', '<')
        texto = texto.replace('&gt;', '>')
        texto = texto.replace('&quot;', '"')
        texto = texto.replace('&#39;', "'")

        # Limpiar espacios multiples
        texto = re.sub(r'[ \t]+', ' ', texto)
        texto = re.sub(r'\n\s*\n', '\n\n', texto)

        # Truncar si es muy largo (GPT tiene limite de tokens)
        max_chars = 12000
        if len(texto) > max_chars:
            texto = texto[:max_chars] + "\n...[contenido truncado]"

        return texto.strip()

    def _normalizar_respuesta(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza la respuesta de GPT al formato esperado."""
        return {
            "observaciones_proveedor": datos.get("observaciones_proveedor"),
            "observaciones_cielo": datos.get("observaciones_cielo"),
            "estado_mencionado": datos.get("estado_mencionado"),
            "fecha_entrega_mencionada": datos.get("fecha_entrega_mencionada"),
            "motivo": datos.get("motivo"),
            "posiciones_correo": datos.get("posiciones", []),
            "resumen_ia": datos.get("resumen"),
            "extraido_con_ia": True
        }

    def _empty_response(self) -> Dict[str, Any]:
        """Retorna respuesta vacia cuando no se puede extraer."""
        return {
            "observaciones_proveedor": None,
            "observaciones_cielo": None,
            "estado_mencionado": None,
            "fecha_entrega_mencionada": None,
            "motivo": None,
            "posiciones_correo": [],
            "resumen_ia": None,
            "extraido_con_ia": False
        }

    # =========================================================================
    # BUSQUEDA INTELIGENTE EN BASE DE DATOS
    # =========================================================================

    def generar_filtros_busqueda(self, consulta: str) -> Dict[str, Any]:
        """
        Convierte una consulta en lenguaje natural a filtros Django ORM
        para buscar pedidos en la base de datos.

        Args:
            consulta: Texto en lenguaje natural (ej: "pedidos retrasados de PILOTO")

        Returns:
            Dict con 'filtros' (Django ORM lookups) y 'descripcion' (explicacion)
        """
        if not self.is_available():
            logger.warning("OpenAI no disponible para busqueda inteligente")
            return {"filtros": {}, "descripcion": "IA no disponible", "error": True}

        try:
            from datetime import date
            hoy = date.today().isoformat()

            messages = [
                {"role": "system", "content": self._get_search_system_prompt(hoy)},
                {"role": "user", "content": f"CONSULTA: {consulta}"}
            ]

            response = self._call_openai_with_retry(messages)
            resultado = json.loads(response.choices[0].message.content)

            logger.info(f"Busqueda IA: '{consulta}' -> {resultado.get('filtros', {})}")
            return resultado

        except Exception as e:
            logger.error(f"Error generando filtros de busqueda: {e}")
            return {"filtros": {}, "descripcion": f"Error: {str(e)}", "error": True}

    def _get_search_system_prompt(self, fecha_hoy: str) -> str:
        """Prompt del sistema para busqueda inteligente."""
        return f"""Eres un asistente que convierte consultas en lenguaje natural a filtros
de base de datos para un sistema de pedidos de compra de Finca el Cielo.

FECHA DE HOY: {fecha_hoy}

ESQUEMA DE LA TABLA PEDIDOS:
- documento_compras: Numero del pedido (ej: "4501833743")
- razon_social: Nombre del proveedor (ej: "PILOTO SAS", "CERAMICA ITALIA")
- comprador: Nombre del comprador (ej: "Brenda Rocio Pena Rojas")
- organizacion_compras: Organizacion (ej: "LC00 LOCERIA COLOMBIANA S.A.S")
- planta: Planta de entrega (ej: "LC PR CALDAS")
- material: Codigo de material
- texto_breve: Descripcion del producto
- estado_pedido: Estado actual. Valores EXACTOS: "Vigente", "Entregado", "Parcial", "Pendiente", "Cancelado", "En Transito"
- fecha_entrega: Fecha de entrega (formato YYYY-MM-DD)
- observaciones: Observaciones del proveedor
- observaciones_cielo: Observaciones internas de Finca el Cielo
- motivo: Motivo o razon
- cantidad_pedido: Cantidad pedida (decimal)
- por_entregar: Cantidad pendiente (decimal)
- precio_neto: Precio unitario (decimal)

FILTROS DJANGO ORM DISPONIBLES:
- campo: valor exacto
- campo__icontains: contiene texto (case insensitive)
- campo__gte: mayor o igual
- campo__lte: menor o igual
- campo__gt: mayor que
- campo__lt: menor que
- campo__in: dentro de lista de valores
- campo__isnull: es null (true/false)

REGLAS:
1. Para buscar por proveedor usa razon_social__icontains
2. Para estados usa estado_pedido exacto con el valor correcto del enum
3. Para fechas usa fecha_entrega__gte o fecha_entrega__lte con formato YYYY-MM-DD
4. "Retrasados" = fecha_entrega < hoy AND estado_pedido != "Entregado" AND estado_pedido != "Cancelado"
5. "Pendientes" = por_entregar__gt: 0
6. Para buscar por producto usa texto_breve__icontains
7. Si mencionan "ultimo mes", "ultimos 3 meses" etc, calcula la fecha relativa a hoy
8. Puedes combinar multiples filtros

Responde SIEMPRE en JSON:
{{
    "filtros": {{"campo__lookup": "valor", ...}},
    "orden": "-fecha_entrega",
    "descripcion": "Explicacion corta de la busqueda en espanol"
}}

Valores validos para "orden": "fecha_entrega", "-fecha_entrega", "razon_social", "-created_at", "precio_neto", "-precio_neto"

Si la consulta no es clara o no se puede traducir a filtros, retorna filtros vacio con descripcion explicando por que."""
