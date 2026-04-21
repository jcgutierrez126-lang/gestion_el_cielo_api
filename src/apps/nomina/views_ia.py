import base64
import json
import os
import logging
from datetime import date, timedelta

import anthropic
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from rest_framework import status

logger = logging.getLogger(__name__)

TIPOS_LABOR_VALIDOS = [
    'recoleccion', 'guadana', 'abono', 'varios', 'banano',
    'cosecha', 'siembra', 'siembra_banano', 'siembra_cafe', 'embolsada',
    'deshojada', 'deschuponar', 'desbejucar', 'arriero', 'broca',
    'control_plagas', 'platear', 'encalar', 'herbicida', 'machete',
    'beneficio', 'mantenimiento', 'transporte', 'seleccion_cafe',
    'arreglo_banano', 'incapacidad',
    'auxilio_labor', 'auxilio_transporte', 'permiso', 'nomina', 'contrato',
]

LOTES_FINCA = {
    "1": "La Milagrosa", "2": "El Tanque", "3": "La Cruz",
    "4": "San José", "5": "El Niño", "6": "San Charbel",
    "7": "La Ceja Palos", "8": "La Ceja Zocas", "9": "Huerta",
    "10": "Hoyo Caliente", "11": "Guaduas", "12": "La Bola",
    "13": "El Llano", "14": "Destechada",
}

LOTES_ABREV = {
    "M": "La Milagrosa", "T": "El Tanque", "C": "La Cruz",
    "SJ": "San José", "N": "El Niño", "SCH": "San Charbel",
    "CP": "La Ceja Palos", "CZ": "La Ceja Zocas", "H": "Huerta",
    "HC": "Hoyo Caliente", "GU": "Guaduas", "BO": "La Bola",
    "LL": "El Llano", "DT": "Destechada",
}

CODIGOS_LABOR = {
    "R": "recoleccion", "G": "guadana", "A": "abono",
    "B": "banano", "E": "embolsada", "S": "siembra",
    "C": "cosecha", "V": "varios", "CT": "contrato",
    "P": "permiso", "N": "nomina", "D": "deshojada",
    "DC": "deschuponar", "DB": "desbejucar",
    "AL": "auxilio_labor", "AT": "auxilio_transporte",
}

MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def semana_ref_desde_fecha(fecha_str: str) -> str:
    """Genera el texto de referencia de semana a partir de una fecha ISO."""
    try:
        d = date.fromisoformat(fecha_str)
    except (ValueError, TypeError):
        return fecha_str or ""
    lunes = d - timedelta(days=d.weekday())
    sabado = lunes + timedelta(days=5)
    mes = MESES_ES[lunes.month - 1]
    if lunes.month == sabado.month:
        return f"Semana del {lunes.day} al {sabado.day} de {mes} de {lunes.year}"
    mes2 = MESES_ES[sabado.month - 1]
    return f"Semana del {lunes.day} de {mes} al {sabado.day} de {mes2} de {lunes.year}"


# ── Prompts planilla semanal (formato antiguo, para compatibilidad) ────────────

SYSTEM_PROMPT = f"""Eres un asistente de extracción de datos para la plataforma de gestión de Finca El Cielo.
Tu única tarea es leer imágenes de planillas manuscritas y devolver un JSON estructurado.

REGLAS ESTRICTAS:
- Devuelve SOLO JSON válido, sin texto antes ni después, sin ```json```.
- Si un campo está en blanco o ilegible, usa null.
- La planilla usa números para los lotes: {LOTES_FINCA}. Convierte el número al nombre.
- La planilla usa letras para las labores: {CODIGOS_LABOR}. Convierte la letra al nombre.
- Para tipo_labor normaliza al valor más cercano de esta lista exacta:
  recoleccion, guadana, abono, varios, banano, cosecha, siembra,
  embolsada, auxilio_labor, auxilio_transporte, permiso, nomina, contrato
- Para tipo_cobro usa: kilos, jornal, contrato, nomina
- Los valores numéricos sin separador de miles (ej: 277600, no 277.600).
- Las fechas en formato YYYY-MM-DD.
"""

USER_PROMPT = """Extrae todos los datos de esta planilla semanal de Finca El Cielo.

La planilla tiene dos secciones:

1. REGISTROS DE TRABAJADORES: tabla con columnas #, Trabajador, Cédula,
   y para cada día (Lun-Sáb): labor/kilos recolectados, lote donde trabajó.
   Al final: total jornales, total kilos, valor jornal, valor total.

2. COMPRAS: tabla con columnas #, Fecha, Producto, Cantidad, Lugar, Valor.

Devuelve este JSON exacto:
{
  "semana": {
    "fecha_inicio": "YYYY-MM-DD o null",
    "fecha_fin": "YYYY-MM-DD o null"
  },
  "registros": [
    {
      "trabajador": "nombre completo",
      "cedula": "número o null",
      "lote": "nombre del lote o null",
      "tipo_labor": "uno de los tipos válidos",
      "tipo_cobro": "kilos | jornal | contrato | nomina",
      "kilos": número o null,
      "jornales": número o null,
      "costo_unidad": número o null,
      "valor": número o null
    }
  ],
  "compras": [
    {
      "fecha": "YYYY-MM-DD o null",
      "producto": "nombre del producto",
      "cantidad": "texto con cantidad y unidad",
      "lugar": "proveedor o lugar",
      "valor": número o null
    }
  ],
  "observaciones": "texto de observaciones o null"
}
"""


# ── Prompts planilla diaria (nuevo formato) ────────────────────────────────────

SYSTEM_PROMPT_DIARIA = f"""Eres un asistente de extracción de datos para la plataforma de gestión de Finca El Cielo.
Tu única tarea es leer imágenes de planillas semanales manuscritas y devolver un JSON con UN REGISTRO POR TRABAJADOR POR DÍA.

REGLAS ESTRICTAS:
- Devuelve SOLO JSON válido, sin texto antes ni después, sin bloques de código.
- Si un campo está en blanco o ilegible, usa null.
- Fechas en formato YYYY-MM-DD.
- Valores numéricos sin separador de miles (ejemplo: 390000 no 390.000).
- El campo "dia" debe ser exactamente: Lunes, Martes, Miércoles, Jueves, Viernes o Sábado.
- Para lotes: usa estas abreviaturas {LOTES_ABREV} o números {LOTES_FINCA}. Convierte al nombre completo.
- Para labores: usa estos códigos {CODIGOS_LABOR}. Convierte al nombre completo.
- Para tipo_cobro usa: kilos, jornal, contrato, nomina.
- Omite los días donde el trabajador no tiene labor registrada.
"""

USER_PROMPT_DIARIA = """Extrae todos los datos de esta planilla SEMANAL de trabajadores de Finca El Cielo.

ESTRUCTURA de la planilla:
- ENCABEZADO: número de semana y rango de fechas (ej: "Semana 8 del 16 al 22 de Febrero del 2026"), valor jornal diario.
- TABLA: una fila por trabajador. Columnas por día (Lunes a Sábado): labor realizada, kilos si aplica, lote.
  Al final: Valor Jornal (total semana) y Valor Total.
- OBSERVACIONES al pie.

INSTRUCCIONES:
1. Crea UN REGISTRO por cada combinación trabajador-día que tenga labor registrada.
2. Calcula la fecha exacta de cada día a partir del lunes de la semana (lunes=+0 días, martes=+1, miércoles=+2, jueves=+3, viernes=+4, sábado=+5).
3. Si el día tiene kilos → tipo_cobro = "kilos", cantidad = kilos del día. valor = kilos × precio si está visible.
4. Si el día solo tiene labor sin kilos → tipo_cobro = "jornal", cantidad = null, valor = valor_jornal del encabezado.
   IMPORTANTE: Para días de jornal, SIEMPRE asigna valor = valor_jornal (el número del encabezado). No dejes valor en null.
5. Si el trabajador es "Auxilio de Transporte" u otro concepto especial (nomina), tipo_cobro = "nomina", valor = el que aparece.
6. Para el lote: lee el nombre/abreviatura del lote para ESE DÍA específico del trabajador. Si no hay lote visible para ese día, usa null.

Devuelve exactamente este JSON:
{
  "fecha_inicio": "YYYY-MM-DD del lunes de la semana",
  "semana_ref": "texto del encabezado tal como aparece",
  "valor_jornal": número_o_null,
  "registros": [
    {
      "nombre": "nombre completo del trabajador",
      "dia": "Lunes|Martes|Miércoles|Jueves|Viernes|Sábado",
      "fecha": "YYYY-MM-DD de ese día específico",
      "lote": "nombre completo del lote o null",
      "labor": "nombre completo de la labor",
      "cantidad": número_o_null,
      "tipo_cobro": "jornal | kilos | contrato | nomina",
      "valor": número_o_null
    }
  ],
  "observaciones": "texto de observaciones o null"
}
"""


class LeerPlanillaDiariaView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        imagen = request.FILES.get('imagen')
        if not imagen:
            return Response({'error': 'Se requiere el campo "imagen".'}, status=status.HTTP_400_BAD_REQUEST)

        api_key = os.getenv('ANTHROPIC_API_KEY', '')
        if not api_key:
            return Response({'error': 'ANTHROPIC_API_KEY no configurada.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        contenido = imagen.read()
        media_type = imagen.content_type or 'image/jpeg'
        if media_type not in ('image/jpeg', 'image/png', 'image/webp', 'image/gif'):
            media_type = 'image/jpeg'

        imagen_b64 = base64.standard_b64encode(contenido).decode('utf-8')

        try:
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model='claude-sonnet-4-6',
                max_tokens=8192,
                system=SYSTEM_PROMPT_DIARIA,
                messages=[
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'image',
                                'source': {
                                    'type': 'base64',
                                    'media_type': media_type,
                                    'data': imagen_b64,
                                },
                            },
                            {'type': 'text', 'text': USER_PROMPT_DIARIA},
                        ],
                    }
                ],
            )

            raw = message.content[0].text.strip()
            if raw.startswith('```'):
                raw = raw.split('\n', 1)[1]
                raw = raw.rsplit('```', 1)[0]

            datos = json.loads(raw)

            # Soporta formato semanal (fecha_inicio) y diario (fecha)
            fecha = datos.get('fecha_inicio') or datos.get('fecha') or ''
            if not datos.get('semana_ref'):
                datos['semana_ref'] = semana_ref_desde_fecha(fecha)
            # Compat: asegurar campo 'fecha' para el frontend
            if not datos.get('fecha') and fecha:
                datos['fecha'] = fecha

            return Response({
                'ok': True,
                'datos': datos,
                'tokens_usados': message.usage.input_tokens + message.usage.output_tokens,
            })

        except json.JSONDecodeError as e:
            logger.error('Claude devolvió JSON inválido: %s', raw[:500])
            return Response({'error': 'No se pudo parsear la respuesta de Claude.', 'detalle': str(e)},
                            status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except anthropic.APIError as e:
            logger.error('Error API Anthropic: %s', e)
            return Response({'error': 'Error al llamar a la API de Claude.', 'detalle': str(e)},
                            status=status.HTTP_502_BAD_GATEWAY)


class LeerPlanillaView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        imagen = request.FILES.get('imagen')
        if not imagen:
            return Response({'error': 'Se requiere el campo "imagen".'}, status=status.HTTP_400_BAD_REQUEST)

        api_key = os.getenv('ANTHROPIC_API_KEY', '')
        if not api_key:
            return Response({'error': 'ANTHROPIC_API_KEY no configurada.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        contenido = imagen.read()
        media_type = imagen.content_type or 'image/jpeg'
        if media_type not in ('image/jpeg', 'image/png', 'image/webp', 'image/gif'):
            media_type = 'image/jpeg'

        imagen_b64 = base64.standard_b64encode(contenido).decode('utf-8')

        try:
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model='claude-sonnet-4-6',
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'image',
                                'source': {
                                    'type': 'base64',
                                    'media_type': media_type,
                                    'data': imagen_b64,
                                },
                            },
                            {'type': 'text', 'text': USER_PROMPT},
                        ],
                    }
                ],
            )

            raw = message.content[0].text.strip()

            if raw.startswith('```'):
                raw = raw.split('\n', 1)[1]
                raw = raw.rsplit('```', 1)[0]

            datos = json.loads(raw)

            for r in datos.get('registros', []):
                tl = (r.get('tipo_labor') or '').lower().strip()
                if tl not in TIPOS_LABOR_VALIDOS:
                    r['tipo_labor'] = 'varios'

            return Response({
                'ok': True,
                'datos': datos,
                'tokens_usados': message.usage.input_tokens + message.usage.output_tokens,
            })

        except json.JSONDecodeError as e:
            logger.error('Claude devolvió JSON inválido: %s', raw[:500])
            return Response({'error': 'No se pudo parsear la respuesta de Claude.', 'detalle': str(e)},
                            status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except anthropic.APIError as e:
            logger.error('Error API Anthropic: %s', e)
            return Response({'error': 'Error al llamar a la API de Claude.', 'detalle': str(e)},
                            status=status.HTTP_502_BAD_GATEWAY)
