import requests
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

CONTENT_TYPE_JSON = "application/json"


class SuplosServiceException(Exception):
    """Excepcion personalizada para errores del servicio Supplos."""
    pass


class SuplosService:
    """
    Servicio para interactuar con la API de Supplos.
    Maneja autenticacion y consulta de pedidos.
    """

    def __init__(self):
        self.base_url = getattr(settings, 'SUPPLOS_API_URL', 'https://apicoronaqas.suplos.com')
        self.email = getattr(settings, 'SUPPLOS_EMAIL', '')
        self.password = getattr(settings, 'SUPPLOS_PASSWORD', '')

    def _get_or_refresh_token(self) -> str:
        """
        Obtiene un token valido, renovandolo si es necesario.
        Implementa cache en base de datos para persistencia entre requests.
        """
        from apps.integraciones.models import SuplosToken

        # Intentar obtener token de la base de datos
        token_obj = SuplosToken.objects.filter(is_active=True).order_by('-created_at').first()

        if token_obj and token_obj.is_valid:
            logger.info("Usando token existente de Supplos")
            return token_obj.access_token

        # Desactivar tokens anteriores
        SuplosToken.objects.filter(is_active=True).update(is_active=False)

        # Solicitar nuevo token
        logger.info("Solicitando nuevo token a Supplos")
        try:
            response = requests.post(
                f"{self.base_url}/api/login",
                json={
                    "email": self.email,
                    "password": self.password
                },
                headers={
                    "Content-Type": CONTENT_TYPE_JSON,
                    "Accept": CONTENT_TYPE_JSON
                },
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            logger.info("Login Supplos exitoso")

            # El token puede venir en diferentes formatos segun la API
            access_token = None
            if isinstance(data.get("token"), dict):
                access_token = data["token"].get("token")
            elif isinstance(data.get("token"), str):
                access_token = data["token"]
            elif data.get("access_token"):
                access_token = data["access_token"]

            if not access_token:
                raise SuplosServiceException("Respuesta de login no contiene token")

            # El token es valido por 24 horas
            expires_at = timezone.now() + timedelta(hours=24)

            # Guardar en base de datos
            SuplosToken.objects.create(
                access_token=access_token,
                expires_at=expires_at,
                is_active=True
            )

            logger.info("Token de Supplos obtenido y almacenado exitosamente")
            return access_token

        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexion con Supplos: {str(e)}")
            raise SuplosServiceException(f"Error de conexion: {str(e)}")
        except Exception as e:
            logger.error(f"Error inesperado al obtener token: {str(e)}")
            raise SuplosServiceException(f"Error inesperado: {str(e)}")

    def consultar_pedido(
        self,
        numero_pedido: int,
        empresas: List[str] = None
    ) -> Dict[str, Any]:
        """
        Consulta un pedido especifico en Supplos.

        Args:
            numero_pedido: Numero del pedido a consultar
            empresas: Lista de empresas (default: ["corona", "alion"])

        Returns:
            Diccionario con los datos del pedido
        """
        if empresas is None:
            empresas = ["corona", "alion"]

        token = self._get_or_refresh_token()

        payload = {
            "empresa": empresas,
            "filtros": {
                "npedido": numero_pedido
            }
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": CONTENT_TYPE_JSON,
            "Accept": CONTENT_TYPE_JSON
        }

        logger.info(f"Consultando pedido {numero_pedido} en Supplos")
        logger.info(f"Payload: {payload}")

        try:
            response = requests.post(
                f"{self.base_url}/api/v1/pedidos",
                json=payload,
                headers=headers,
                timeout=60
            )
            response.raise_for_status()

            data = response.json()
            logger.info(f"Pedido {numero_pedido} obtenido exitosamente de Supplos")

            return {
                "status": "OK",
                "data": data,
                "source": "supplos"
            }

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                # Token invalido, limpiar y reintentar una vez
                logger.warning("Token de Supplos invalido, reintentando...")
                from apps.integraciones.models import SuplosToken
                SuplosToken.objects.filter(is_active=True).update(is_active=False)

                # Reintentar con nuevo token
                token = self._get_or_refresh_token()
                headers["Authorization"] = f"Bearer {token}"

                response = requests.post(
                    f"{self.base_url}/api/v1/pedidos",
                    json=payload,
                    headers=headers,
                    timeout=60
                )
                response.raise_for_status()
                return {
                    "status": "OK",
                    "data": response.json(),
                    "source": "supplos"
                }

            logger.error(f"Error HTTP de Supplos: {e.response.status_code} - {e.response.text}")
            raise SuplosServiceException(f"Error HTTP: {e.response.status_code} - {e.response.text}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexion consultando pedido: {str(e)}")
            raise SuplosServiceException(f"Error de conexion: {str(e)}")

    def consultar_pedidos_por_fecha(
        self,
        fecha: str,
        empresas: List[str] = None
    ) -> Dict[str, Any]:
        """
        Consulta pedidos por fecha de creacion.

        Args:
            fecha: Fecha en formato DDMMYYYY
            empresas: Lista de empresas

        Returns:
            Diccionario con los pedidos encontrados
        """
        if empresas is None:
            empresas = ["corona", "alion"]

        token = self._get_or_refresh_token()

        payload = {
            "empresa": empresas,
            "filtros": {
                "FechaCreacion": fecha
            }
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": CONTENT_TYPE_JSON,
            "Accept": CONTENT_TYPE_JSON
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/v1/pedidos",
                json=payload,
                headers=headers,
                timeout=60
            )
            response.raise_for_status()

            return {
                "status": "OK",
                "data": response.json(),
                "source": "supplos"
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Error consultando pedidos por fecha: {str(e)}")
            raise SuplosServiceException(f"Error de conexion: {str(e)}")
