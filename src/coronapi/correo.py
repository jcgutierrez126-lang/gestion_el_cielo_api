import os
import time
import requests
from msal import ConfidentialClientApplication
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.conf import settings
from django.apps import apps
from dotenv import load_dotenv
from io import BytesIO
import base64

load_dotenv()

user_id = os.getenv('EMAIL_HOST_USER')

def get_access_token():
    print("Inicio función get_access_token()")

    try:
        client_id = os.getenv('CORREO_CLIENT_ID')
        tenant_id = os.getenv('CORREO_TENANT_ID')
        secret = os.getenv('CORREO_SECRET_KEY')

        print("Antes de construir la app...")

        try:
            app = ConfidentialClientApplication(
                client_id,
                authority=f"https://login.microsoftonline.com/{tenant_id}",
                client_credential=secret,
            )
            print("App construida.")
        except Exception as e:
            print("Error construyendo la app:", e)
            return {"status": "ERROR", "message": f"Error construyendo la app: {e}"}

        scopes = ["https://graph.microsoft.com/.default"]

        try:
            print("Solicitando token...")
            result = app.acquire_token_for_client(scopes=scopes)
        except Exception as e:
            print("Error al solicitar token:", e)
            return {"status": "ERROR", "message": f"Error al solicitar token: {e}"}

        if "access_token" in result:
            print("Token obtenido correctamente.")
            return {"status": "OK", "access": result["access_token"]}
        else:
            print("No se pudo obtener token:", result.get("error_description", "Respuesta inválida"))
            return {"status": "ERROR", "message": result.get("error_description", "Respuesta inválida")}

    except Exception as e:
        print("Error general:", e)
        return {"status": "ERROR", "message": str(e)}


def enviar_correo_masivo(asunto: str, contexto: dict, plantilla: str, destinatarios: list, token: str):
    try:
        print("Enviando correo masivo...")
        template = get_template(plantilla)
        msg = template.render(contexto)

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        body = {
            "message": {
                "subject": asunto,
                "body": {
                    "contentType": "HTML",
                    "content": msg
                },
                "toRecipients": [{"emailAddress": {"address": email}} for email in destinatarios],
            },
            "saveToSentItems": "true"
        }

        response = requests.post(
            f"https://graph.microsoft.com/v1.0/users/{user_id}/sendMail",
            headers=headers,
            json=body
        )

        print("Estado de la respuesta:", response.status_code)
        if response.status_code == 202:
            print("Correo enviado exitosamente.")
            return {"status": "OK", "message": "Correo enviado exitosamente"}
        else:
            print("Error en el envío:", response.status_code, response.text)
            return {"status": "ERROR", "message": f"Error: {response.status_code} - {response.text}"}

    except Exception as e:
        print("Error al enviar el correo:", e)
        return {"status": "ERROR", "message": str(e)}


def enviar_correo_simple(asunto: str, contenido_html: str, destinatarios: list):
    """
    Envía un correo simple sin plantilla usando Microsoft Graph API.
    """
    try:
        token_result = get_access_token()
        if token_result["status"] != "OK":
            return token_result

        token = token_result["access"]

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        body = {
            "message": {
                "subject": asunto,
                "body": {
                    "contentType": "HTML",
                    "content": contenido_html
                },
                "toRecipients": [{"emailAddress": {"address": email}} for email in destinatarios],
            },
            "saveToSentItems": "true"
        }

        response = requests.post(
            f"https://graph.microsoft.com/v1.0/users/{user_id}/sendMail",
            headers=headers,
            json=body
        )

        if response.status_code == 202:
            return {"status": "OK", "message": "Correo enviado exitosamente"}
        else:
            return {"status": "ERROR", "message": f"Error: {response.status_code} - {response.text}"}

    except Exception as e:
        return {"status": "ERROR", "message": str(e)}


def enviar_correo_con_plantilla(asunto: str, plantilla: str, contexto: dict, destinatarios: list):
    """
    Envía un correo usando una plantilla Django y Microsoft Graph API.
    """
    try:
        token_result = get_access_token()
        if token_result["status"] != "OK":
            return token_result

        token = token_result["access"]
        return enviar_correo_masivo(asunto, contexto, plantilla, destinatarios, token)

    except Exception as e:
        return {"status": "ERROR", "message": str(e)}
