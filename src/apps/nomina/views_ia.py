import base64
import json
import os
import logging

import anthropic
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from rest_framework import status

logger = logging.getLogger(__name__)

TIPOS_LABOR_VALIDOS = [
    'recoleccion', 'guadana', 'abono', 'varios', 'banano',
    'cosecha', 'siembra', 'embolsada', 'auxilio_labor',
    'auxilio_transporte', 'permiso', 'nomina', 'contrato',
]

LOTES_FINCA = {
    "1": "La Milagrosa", "2": "El Tanque", "3": "La Cruz",
    "4": "San José", "5": "El Niño", "6": "San Charbel",
    "7": "La Ceja Palos", "8": "La Ceja Zocas", "9": "Huerta",
    "10": "Hoyo Caliente", "11": "Guaduas", "12": "La Bola",
    "13": "El Llano", "14": "Destechada",
}

CODIGOS_LABOR = {
    "R": "recoleccion", "G": "guadana", "A": "abono", "B": "banano",
    "E": "embolsada", "S": "siembra", "C": "cosecha", "V": "varios",
    "CT": "contrato", "P": "permiso", "N": "nomina",
}

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

            # Limpiar posibles bloques de código
            if raw.startswith('```'):
                raw = raw.split('\n', 1)[1]
                raw = raw.rsplit('```', 1)[0]

            datos = json.loads(raw)

            # Normalizar tipos de labor
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
