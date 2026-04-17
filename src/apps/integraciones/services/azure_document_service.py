import os
import base64
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class AzureDocumentService:
    """
    Servicio para extraer texto y tablas de documentos PDF e imagenes
    usando Azure AI Document Intelligence (formerly Form Recognizer).
    """

    def __init__(self):
        self.endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        self.api_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
        self.client = None

        if self.endpoint and self.api_key:
            try:
                from azure.ai.documentintelligence import DocumentIntelligenceClient
                from azure.core.credentials import AzureKeyCredential
                self.client = DocumentIntelligenceClient(
                    endpoint=self.endpoint,
                    credential=AzureKeyCredential(self.api_key)
                )
            except ImportError:
                logger.warning(
                    "azure-ai-documentintelligence no instalado. "
                    "Instale con: pip install azure-ai-documentintelligence"
                )
            except Exception as e:
                logger.error(f"Error inicializando Azure Document Intelligence: {e}")

    def is_available(self) -> bool:
        """Verifica si el servicio esta disponible."""
        return self.client is not None

    def extraer_texto_documento(self, contenido_bytes: bytes) -> Optional[str]:
        """
        Extrae texto y tablas de un documento PDF o imagen usando el modelo
        'prebuilt-layout' de Azure Document Intelligence.

        Args:
            contenido_bytes: Bytes del archivo (PDF o imagen)

        Returns:
            Texto extraido como string, o None si falla
        """
        if not self.is_available():
            logger.warning("Azure Document Intelligence no disponible")
            return None

        try:
            from azure.ai.documentintelligence.models import AnalyzeDocumentRequest

            base64_content = base64.b64encode(contenido_bytes).decode("utf-8")

            poller = self.client.begin_analyze_document(
                model_id="prebuilt-layout",
                analyze_request=AnalyzeDocumentRequest(
                    bytes_source=base64_content
                ),
                content_type="application/json"
            )
            result = poller.result()

            return self._formatear_resultado(result)

        except Exception as e:
            logger.error(f"Error extrayendo texto con Azure DI: {e}")
            return None

    def extraer_texto_multiples(self, adjuntos: List[Dict[str, Any]]) -> Optional[str]:
        """
        Extrae texto de multiples adjuntos y los concatena.

        Args:
            adjuntos: Lista de dicts con keys 'contenido_bytes', 'content_type', 'name'

        Returns:
            Texto concatenado de todos los adjuntos, o None si no se extrae nada
        """
        textos = []
        for adjunto in adjuntos:
            texto = self.extraer_texto_documento(
                contenido_bytes=adjunto["contenido_bytes"]
            )
            if texto:
                textos.append(f"--- Adjunto: {adjunto.get('name', 'sin nombre')} ---\n{texto}")

        if textos:
            return "\n\n".join(textos)
        return None

    def _formatear_resultado(self, result) -> str:
        """
        Formatea el resultado de Azure DI, extrayendo contenido de texto
        y tablas de forma estructurada.
        """
        partes = []

        if hasattr(result, 'content') and result.content:
            partes.append(result.content)

        if hasattr(result, 'tables') and result.tables:
            for idx, table in enumerate(result.tables):
                tabla_texto = self._tabla_a_texto(table)
                if tabla_texto:
                    partes.append(f"\n[TABLA {idx + 1}]\n{tabla_texto}")

        return "\n".join(partes) if partes else ""

    def _tabla_a_texto(self, table) -> str:
        """
        Convierte una tabla de Azure DI a texto plano con separadores pipe.
        """
        if not hasattr(table, 'cells') or not table.cells:
            return ""

        max_row = max(cell.row_index for cell in table.cells) + 1
        max_col = max(cell.column_index for cell in table.cells) + 1

        grid = [["" for _ in range(max_col)] for _ in range(max_row)]
        for cell in table.cells:
            content = cell.content.strip() if cell.content else ""
            grid[cell.row_index][cell.column_index] = content

        lines = []
        for row in grid:
            lines.append(" | ".join(row))

        return "\n".join(lines)
