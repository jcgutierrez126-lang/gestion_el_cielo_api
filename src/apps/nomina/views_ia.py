import base64
import json
import os
import logging
from datetime import date, timedelta
from io import BytesIO

import anthropic
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework import status

from .models import Empleado, TipoLabor, TipoCobro, ControlSemanal
from apps.produccion.models import Lote

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
    "C": "cosecha", "V": "varios", "VR": "varios",
    "CT": "contrato", "P": "permiso", "N": "nomina",
    "D": "deshojada", "DC": "deschuponar", "DB": "desbejucar",
    "AL": "auxilio_labor", "AT": "auxilio_transporte",
}

# Correcciones de OCR frecuentes en manuscrito
OCR_CORRECCIONES_LABOR = {
    "AR": "VR",   # V se confunde con A en manuscrito
    "DS": "DB",   # B se confunde con S en manuscrito
    "DE": "DB",   # variante común
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
  Si el lote está ilegible, en blanco o no aplica (ej: auxilio, nomina), usa null. NUNCA uses "Lote" como valor.
- Para labores: usa estos códigos {CODIGOS_LABOR}. Convierte al nombre completo.
- CORRECCIONES OCR FRECUENTES EN MANUSCRITO: La letra "V" se confunde con "A" → si ves código "AR" es probablemente "VR" (varios). La letra "B" se confunde con "S" → si ves "DS" es probablemente "DB" (desbejucar).
- Para tipo_cobro usa: kilos, jornal, contrato, nomina.
- Omite los días donde el trabajador no tiene labor registrada.
- Si ves en observaciones "Gastos varios" con montos (ej: neumático, parchada), inclúyelos en el campo "observaciones" pero NO crees registros de trabajador para ellos.
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
5. Si el trabajador es "Auxilio de Transporte" u otro concepto especial (nomina/vale), tipo_cobro = "nomina", lote = null, valor = el que aparece.
6. Para el lote: lee el nombre/abreviatura del lote para ESE DÍA específico del trabajador. Si no hay lote visible, si está ilegible, o si el concepto no aplica lote → usa null. NUNCA escribas la palabra "Lote" como valor del campo lote.
7. En "observaciones" incluye: texto de observaciones, gastos varios (neumático, parchada, etc.) y el "Total vale semana" si aparece.

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


class LeerPlanillaSemanalExcelView(APIView):
    """Parsea el Excel de planilla semanal (tab Labores) y devuelve registros para revisión."""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    # Columnas 0-indexed por día: (lote, labor, cob, cant)
    _DIA_COLS = [
        (1, 2, 3, 4),      # Lunes:     B C D E
        (5, 6, 7, 8),      # Martes:    F G H I
        (9, 10, 11, 12),   # Miércoles: J K L M
        (13, 14, 15, 16),  # Jueves:    N O P Q
        (17, 18, 19, 20),  # Viernes:   R S T U
        (21, 22, 23, 24),  # Sábado:    V W X Y
    ]
    _DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
    _COL_MEDIO_DIA = 25   # Z  — "X" = sábado medio día
    _COL_PRECIO    = 27   # AB — $ Jornal / $ Kilo
    _COL_TIPO      = 28   # AC — K=kilos, C=contrato, vacío=jornal

    @staticmethod
    def _cel(row, idx):
        """Extrae celda como string limpio, devuelve '' si vacía."""
        if idx < len(row) and row[idx] is not None:
            v = str(row[idx]).strip()
            return v if v.lower() not in ('none', 'nan') else ''
        return ''

    @staticmethod
    def _num(s):
        """Convierte string a float; devuelve None si no parseable."""
        try:
            return float(s.replace(',', '.')) if s else None
        except (ValueError, AttributeError):
            return None

    def post(self, request):
        archivo = request.FILES.get('archivo')
        if not archivo:
            return Response({'error': 'Se requiere el campo "archivo".'}, status=status.HTTP_400_BAD_REQUEST)

        fecha_inicio_str = request.data.get('fecha_inicio', '')
        try:
            fecha_lunes = date.fromisoformat(fecha_inicio_str)
        except (ValueError, TypeError):
            hoy = date.today()
            fecha_lunes = hoy - timedelta(days=hoy.weekday())

        try:
            from openpyxl import load_workbook
            wb = load_workbook(filename=BytesIO(archivo.read()), data_only=True)
            ws = wb['Labores']
        except Exception as e:
            return Response({'error': f'No se pudo leer el archivo: {e}'}, status=status.HTTP_400_BAD_REQUEST)

        registros = []

        for row in ws.iter_rows(min_row=6, max_row=25, values_only=True):
            nombre = self._cel(row, 0)
            if not nombre:
                continue

            tipo_raw = self._cel(row, self._COL_TIPO).upper()
            if tipo_raw == 'K':
                tipo_cobro = 'kilos'
            elif tipo_raw == 'C':
                tipo_cobro = 'contrato'
            else:
                tipo_cobro = 'jornal'

            precio = self._num(self._cel(row, self._COL_PRECIO)) or 0
            medio_dia_sabado = self._cel(row, self._COL_MEDIO_DIA).upper() == 'X'

            for i, (ci_lote, ci_labor, _ci_cob, ci_cant) in enumerate(self._DIA_COLS):
                lote_val  = self._cel(row, ci_lote)
                labor_val = self._cel(row, ci_labor)
                cant_str  = self._cel(row, ci_cant)

                if not lote_val and not labor_val and not cant_str:
                    continue

                es_medio_dia = (i == 5) and medio_dia_sabado
                cant_num     = self._num(cant_str)
                fecha_dia    = fecha_lunes + timedelta(days=i)

                if tipo_cobro == 'kilos':
                    cantidad = cant_num
                    valor    = round(cant_num * precio) if cant_num and precio else None
                elif tipo_cobro == 'jornal':
                    cantidad = 0.5 if es_medio_dia else 1.0
                    valor    = round(precio * cantidad) if precio else None
                else:  # contrato — valor se calcula globalmente, aquí queda None
                    cantidad = cant_num
                    valor    = None

                registros.append({
                    'nombre':     nombre,
                    'dia':        self._DIAS[i],
                    'fecha':      fecha_dia.isoformat(),
                    'lote':       lote_val or None,
                    'labor':      labor_val or None,
                    'cantidad':   cantidad,
                    'tipo_cobro': tipo_cobro,
                    'valor':      valor,
                })

        semana_ref = semana_ref_desde_fecha(fecha_lunes.isoformat())

        return Response({
            'ok': True,
            'datos': {
                'fecha_inicio': fecha_lunes.isoformat(),
                'semana_ref':   semana_ref,
                'registros':    registros,
                'observaciones': None,
            },
        })


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


def _buscar_empleado(nombre: str):
    if not nombre:
        return None
    try:
        return Empleado.objects.get(nombre_completo__iexact=nombre.strip())
    except Empleado.DoesNotExist:
        return Empleado.objects.filter(nombre_completo__icontains=nombre.strip()).first()
    except Empleado.MultipleObjectsReturned:
        return Empleado.objects.filter(nombre_completo__icontains=nombre.strip()).first()


def _buscar_tipo_labor(texto: str):
    if not texto:
        return None
    t = texto.strip().upper()
    t = OCR_CORRECCIONES_LABOR.get(t, t)
    t_original = texto.strip()
    mapped = CODIGOS_LABOR.get(t)
    if mapped:
        resultado = TipoLabor.objects.filter(nombre__iexact=mapped).first()
        if resultado:
            return resultado
    return (
        TipoLabor.objects.filter(abreviatura__iexact=t_original).first() or
        TipoLabor.objects.filter(nombre__icontains=t_original).first()
    )


def _buscar_tipo_cobro(texto: str):
    if not texto:
        return None
    t = texto.strip()
    return TipoCobro.objects.filter(abreviatura__iexact=t).first() or \
           TipoCobro.objects.filter(nombre__icontains=t).first()


def _buscar_lote(texto: str):
    if not texto:
        return None
    t = texto.strip()
    return Lote.objects.filter(abreviatura__iexact=t).first() or \
           Lote.objects.filter(nombre__icontains=t).first()


class GuardarPlanillaView(APIView):
    """Guarda registros parseados de planilla en ControlSemanal resolviendo FKs por nombre/abreviatura."""
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser]

    def post(self, request):
        datos = request.data
        semana_ref = datos.get('semana_ref', '')
        fecha_inicio_str = datos.get('fecha_inicio', '')
        registros_raw = datos.get('registros', [])
        valor_jornal_global = datos.get('valor_jornal')

        try:
            fecha_lunes = date.fromisoformat(fecha_inicio_str)
        except (ValueError, TypeError):
            return Response({'error': 'fecha_inicio inválida (YYYY-MM-DD requerido)'}, status=status.HTTP_400_BAD_REQUEST)

        fecha_sabado = fecha_lunes + timedelta(days=5)
        creados = []
        errores = []

        for i, r in enumerate(registros_raw):
            nombre = r.get('nombre', '')
            labor_txt = r.get('labor', '')
            tipo_cobro_txt = r.get('tipo_cobro', '')
            lote_txt = r.get('lote') or ''
            dia = r.get('dia', '')
            fecha_str = r.get('fecha', '') or fecha_inicio_str
            cantidad = r.get('cantidad')
            valor = r.get('valor')
            costo_unidad = r.get('valor_jornal') or valor_jornal_global or 0

            empleado = _buscar_empleado(nombre)
            tipo_labor = _buscar_tipo_labor(labor_txt)
            tipo_cobro = _buscar_tipo_cobro(tipo_cobro_txt)
            lote = _buscar_lote(lote_txt)

            faltantes = []
            if not empleado:
                faltantes.append(f'empleado "{nombre}"')
            if not tipo_labor:
                faltantes.append(f'labor "{labor_txt}"')
            if not tipo_cobro:
                faltantes.append(f'tipo_cobro "{tipo_cobro_txt}"')

            if faltantes:
                errores.append({'fila': i + 1, 'nombre': nombre, 'motivo': f'No encontrado: {", ".join(faltantes)}'})
                continue

            try:
                fecha_dia = date.fromisoformat(fecha_str)
            except (ValueError, TypeError):
                fecha_dia = fecha_lunes

            kilos = float(cantidad) if tipo_cobro_txt.lower() == 'kilos' and cantidad is not None else None
            jornales = float(cantidad) if tipo_cobro_txt.lower() != 'kilos' and cantidad is not None else None

            ControlSemanal.objects.create(
                empleado=empleado,
                semana_ref=semana_ref,
                dia=dia,
                fecha=fecha_dia,
                fecha_inicio=fecha_lunes,
                fecha_fin=fecha_sabado,
                tipo_labor=tipo_labor,
                tipo_cobro=tipo_cobro,
                lote=lote,
                kilos=kilos,
                jornales=jornales,
                costo_unidad=costo_unidad,
                valor=valor or 0,
            )
            creados.append(nombre)

        return Response({
            'ok': True,
            'creados': len(creados),
            'errores': errores,
            'semana_ref': semana_ref,
        }, status=status.HTTP_201_CREATED)
