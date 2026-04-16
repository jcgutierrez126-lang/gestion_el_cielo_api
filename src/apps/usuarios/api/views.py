from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListAPIView
from coronapi.filtering import filter_by_search
from apps.usuarios.models import User
from apps.usuarios.api.serializers import UserSerializer, GroupSerializer, UserLoginSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.contrib.auth.models import Group
from django.db.models import Q
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.conf import settings
from django.core.cache import cache
from coronapi.correo import enviar_correo_simple, get_access_token, enviar_correo_masivo
import secrets
import string
from datetime import datetime

USUARIO_NO_ENCONTRADO = "Usuario no encontrado."
NOT_FOUND_DETAIL = "Not found."


def generate_login_response(user, request):
    """
    Método auxiliar para generar la respuesta de inicio de sesión.
    """

    refresh = RefreshToken.for_user(user)

    # Construir la URL completa de la imagen
    image_url = None
    if user.image:
        image_url = request.build_absolute_uri(user.image.url)

    # Datos del usuario
    user_data = {
        'user_id': user.id,
        'email': user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "image": image_url,
        "full_name": user.full_name,
        "role_id": user.role.id if user.role else None,
        "role_name": user.role.name if user.role else None,
        "is_admin": user.is_admin
    }

    # Combinar tokens y datos del usuario
    response_data = {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        **user_data
    }

    return response_data


def generate_verification_code(length=6):
    """Genera un código de verificación numérico."""
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def get_email_base_styles():
    """Retorna los estilos CSS base para los correos corporativos."""
    return """
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f3f4f6;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #1F2937 0%, #374151 100%);
            padding: 30px 40px;
            text-align: center;
        }
        .header img {
            max-width: 180px;
            height: auto;
            margin-bottom: 15px;
        }
        .header h1 {
            color: #10B981;
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }
        .header p {
            color: #9CA3AF;
            margin: 8px 0 0 0;
            font-size: 14px;
        }
        .content {
            padding: 40px;
        }
        .greeting {
            color: #1F2937;
            font-size: 18px;
            margin-bottom: 20px;
        }
        .message {
            color: #4B5563;
            line-height: 1.7;
            font-size: 15px;
        }
        .code-container {
            background: linear-gradient(135deg, #10B981 0%, #059669 100%);
            padding: 25px;
            border-radius: 12px;
            margin: 30px 0;
            text-align: center;
        }
        .code {
            color: white;
            font-size: 36px;
            font-weight: bold;
            letter-spacing: 10px;
            margin: 0;
        }
        .code-label {
            color: rgba(255,255,255,0.8);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 10px;
        }
        .timer {
            display: inline-block;
            background: #FEF3C7;
            color: #92400E;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 14px;
            margin-top: 20px;
        }
        .info-box {
            background: #ECFDF5;
            border-left: 4px solid #10B981;
            color: #065F46;
            padding: 20px;
            border-radius: 0 12px 12px 0;
            margin: 25px 0;
        }
        .info-box-title {
            font-weight: 600;
            font-size: 14px;
            margin-bottom: 8px;
            color: #047857;
        }
        .warning {
            background: #FEF2F2;
            border-left: 4px solid #EF4444;
            color: #991B1B;
            padding: 15px 20px;
            border-radius: 0 8px 8px 0;
            margin-top: 25px;
            font-size: 14px;
        }
        .user-card {
            background: #F9FAFB;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 20px;
            margin: 25px 0;
        }
        .user-card-row {
            display: flex;
            padding: 8px 0;
            border-bottom: 1px solid #E5E7EB;
        }
        .user-card-row:last-child {
            border-bottom: none;
        }
        .user-card-label {
            color: #6B7280;
            font-size: 13px;
            width: 120px;
        }
        .user-card-value {
            color: #1F2937;
            font-weight: 500;
            font-size: 14px;
        }
        .button {
            display: inline-block;
            background: linear-gradient(135deg, #10B981 0%, #059669 100%);
            color: white;
            padding: 14px 32px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            font-size: 14px;
            margin-top: 20px;
        }
        .footer {
            background: #F9FAFB;
            text-align: center;
            color: #6B7280;
            font-size: 12px;
            padding: 25px 40px;
            border-top: 1px solid #E5E7EB;
        }
        .footer-brand {
            color: #1F2937;
            font-weight: 600;
            font-size: 14px;
            margin-bottom: 8px;
        }
        .footer a {
            color: #10B981;
            text-decoration: none;
        }
    """


def get_email_header(title, subtitle="Sistema de Gestión - Planta de Desposte"):
    """Genera el header del correo con logo y título."""
    logo_url = f"https://{settings.FRONTEND_URL}/images/euro_logo.png"
    return f"""
        <div class="header">
            <img src="{logo_url}" alt="Euro Cárnicos Logo" />
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
    """


def get_email_footer():
    """Genera el footer del correo."""
    year = datetime.now().year
    return f"""
        <div class="footer">
            <p class="footer-brand">Euro Cárnicos - Planta de Desposte</p>
            <p>Este es un correo automático, por favor no responder.</p>
            <p>&copy; {year} Todos los derechos reservados</p>
        </div>
    """


class UserLoginView(APIView):
    """
    Vista para iniciar sesión.
    """
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['username']
            response_data = generate_login_response(user, request)
            return Response(response_data, status=status.HTTP_200_OK)
        errors = serializer.errors
        non_field_errors = errors.get('non_field_errors', [])
        is_auth_error = any(
            'Credenciales' in str(e) or 'inactiva' in str(e)
            for e in non_field_errors
        )
        http_status = status.HTTP_401_UNAUTHORIZED if is_auth_error else status.HTTP_400_BAD_REQUEST
        return Response(errors, status=http_status)


class PasswordResetRequestAPIView(APIView):
    """
    Solicita el restablecimiento de contraseña enviando un código al correo.
    Usa Microsoft Graph API para enviar el correo.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"detail": "Debe proporcionar un correo."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Aún así devolvemos OK para no revelar si un email existe o no
            return Response({"detail": "Si existe una cuenta con este email, recibirás un código de verificación."}, status=status.HTTP_200_OK)

        # Generar código de 6 dígitos
        code = generate_verification_code()

        # Guardar el código en cache por 15 minutos (asociado al email)
        cache_key = f"password_reset_{email}"
        cache.set(cache_key, code, timeout=900)  # 15 minutos

        # Crear el contenido HTML del correo con diseño corporativo
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                {get_email_base_styles()}
            </style>
        </head>
        <body>
            <div class="container">
                {get_email_header("Restablecer Contraseña")}
                <div class="content">
                    <p class="greeting">Hola <strong>{user.full_name or user.first_name}</strong>,</p>
                    <p class="message">
                        Has solicitado restablecer tu contraseña en el Sistema de Gestión de la Planta de Desposte.
                        Utiliza el siguiente código de verificación para continuar con el proceso:
                    </p>
                    <div class="code-container">
                        <p class="code-label">Tu código de verificación</p>
                        <p class="code">{code}</p>
                    </div>
                    <div style="text-align: center;">
                        <span class="timer">Este código expira en 15 minutos</span>
                    </div>
                    <div class="warning">
                        <strong>Importante:</strong> Si no solicitaste este cambio, ignora este mensaje. Tu cuenta permanecerá segura.
                    </div>
                </div>
                {get_email_footer()}
            </div>
        </body>
        </html>
        """

        # Enviar correo usando Microsoft Graph
        result = enviar_correo_simple(
            asunto="Código de Verificación - Restablecer Contraseña",
            contenido_html=html_content,
            destinatarios=[user.email]
        )

        if result["status"] == "OK":
            return Response({
                "detail": "Se ha enviado el código de verificación al correo.",
                "email": email
            }, status=status.HTTP_200_OK)
        else:
            print("Error al enviar correo de restablecimiento:", result.get("message", ""))
            return Response({
                "detail": "Error al enviar el correo. Intente nuevamente.",
                "error": result.get("message", "")
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PasswordResetConfirmAPIView(APIView):
    """
    Verifica el código y cambia la contraseña.
    """
    permission_classes = [AllowAny]

    def post(self, request, uidb64=None, token=None):
        email = request.data.get("email")
        code = request.data.get("code")
        password = request.data.get("password")

        if not email or not code or not password:
            return Response({
                "detail": "Debe proporcionar email, código y nueva contraseña."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verificar el código en cache
        cache_key = f"password_reset_{email}"
        stored_code = cache.get(cache_key)

        if not stored_code:
            return Response({
                "detail": "El código ha expirado o no existe. Solicite uno nuevo."
            }, status=status.HTTP_400_BAD_REQUEST)

        if stored_code != code:
            return Response({
                "detail": "El código de verificación es incorrecto."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Buscar el usuario
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                "detail": "Usuario no encontrado."
            }, status=status.HTTP_404_NOT_FOUND)

        # Cambiar contraseña
        user.set_password(password)
        user.save()

        # Eliminar el código de cache
        cache.delete(cache_key)

        return Response({
            "detail": "Contraseña actualizada exitosamente."
        }, status=status.HTTP_200_OK)


class VerifyResetCodeAPIView(APIView):
    """
    Verifica si el código de restablecimiento es válido sin cambiar la contraseña.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")

        if not email or not code:
            return Response({
                "detail": "Debe proporcionar email y código."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verificar el código en cache
        cache_key = f"password_reset_{email}"
        stored_code = cache.get(cache_key)

        if not stored_code:
            return Response({
                "detail": "El código ha expirado o no existe.",
                "valid": False
            }, status=status.HTTP_400_BAD_REQUEST)

        if stored_code != code:
            return Response({
                "detail": "El código de verificación es incorrecto.",
                "valid": False
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "detail": "Código válido.",
            "valid": True
        }, status=status.HTTP_200_OK)


class UserRegisterAPIView(APIView):
    """
    Vista pública para registro de nuevos usuarios.
    El usuario queda inactivo hasta que un admin lo apruebe.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data.copy()

        # Validaciones básicas
        required_fields = ['email', 'password', 'first_name', 'last_name', 'phone', 'identification']
        for field in required_fields:
            if not data.get(field):
                return Response({
                    "detail": f"El campo '{field}' es requerido."
                }, status=status.HTTP_400_BAD_REQUEST)

        # Verificar si el email ya existe
        if User.objects.filter(email=data['email']).exists():
            return Response({
                "detail": "Ya existe un usuario con este correo electrónico."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verificar si el username ya existe (si se proporciona)
        if data.get('username') and User.objects.filter(username=data['username']).exists():
            return Response({
                "detail": "Ya existe un usuario con este nombre de usuario."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verificar si la identificación ya existe
        if User.objects.filter(identification=data['identification']).exists():
            return Response({
                "detail": "Ya existe un usuario con esta identificación."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Crear el usuario
            user = User(
                email=data['email'],
                username=data.get('username', data['email'].split('@')[0]),
                first_name=data['first_name'],
                last_name=data['last_name'],
                phone=data['phone'],
                identification=data['identification'],
                born_date=data.get('born_date'),
                status=False,  # Inactivo hasta que un admin lo apruebe
                is_admin=False
            )
            user.set_password(data['password'])
            user.save()

            # Enviar correo de confirmación al usuario con diseño corporativo
            html_content_user = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    {get_email_base_styles()}
                </style>
            </head>
            <body>
                <div class="container">
                    {get_email_header("Registro Exitoso")}
                    <div class="content">
                        <p class="greeting">Hola <strong>{user.full_name}</strong>,</p>
                        <p class="message">
                            Tu cuenta ha sido creada exitosamente en el Sistema de Gestión de la Planta de Desposte.
                        </p>
                        <div class="info-box">
                            <p class="info-box-title">Estado de tu cuenta</p>
                            <p style="margin: 0;"><strong>Pendiente de aprobación</strong></p>
                            <p style="margin: 8px 0 0 0; font-size: 14px;">
                                Un administrador revisará tu solicitud y activará tu cuenta pronto.
                                Recibirás una notificación cuando tu cuenta sea activada.
                            </p>
                        </div>
                        <div class="user-card">
                            <p style="margin: 0 0 15px 0; font-weight: 600; color: #1F2937;">Datos de tu cuenta:</p>
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 8px 0; color: #6B7280; font-size: 13px; width: 120px;">Nombre:</td>
                                    <td style="padding: 8px 0; color: #1F2937; font-weight: 500;">{user.full_name}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #6B7280; font-size: 13px;">Email:</td>
                                    <td style="padding: 8px 0; color: #1F2937; font-weight: 500;">{user.email}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #6B7280; font-size: 13px;">Identificación:</td>
                                    <td style="padding: 8px 0; color: #1F2937; font-weight: 500;">{user.identification}</td>
                                </tr>
                            </table>
                        </div>
                    </div>
                    {get_email_footer()}
                </div>
            </body>
            </html>
            """

            enviar_correo_simple(
                asunto="Registro Exitoso - Pendiente de Aprobación",
                contenido_html=html_content_user,
                destinatarios=[user.email]
            )

            # Notificar a los administradores
            admins = User.objects.filter(is_admin=True, status=True)
            admin_emails = [admin.email for admin in admins if admin.email]

            if admin_emails:
                # URL del sistema para el botón
                system_url = f"https://{settings.FRONTEND_URL}/dashboard/usuarios"

                html_content_admin = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        {get_email_base_styles()}
                        .alert-badge {{
                            display: inline-block;
                            background: #FEF3C7;
                            color: #92400E;
                            padding: 6px 12px;
                            border-radius: 20px;
                            font-size: 12px;
                            font-weight: 600;
                            margin-bottom: 20px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        {get_email_header("Nuevo Usuario Registrado")}
                        <div class="content">
                            <span class="alert-badge">Requiere aprobación</span>
                            <p class="message">
                                Se ha registrado un nuevo usuario en el sistema que requiere tu aprobación para activar su cuenta.
                            </p>
                            <div class="user-card">
                                <p style="margin: 0 0 15px 0; font-weight: 600; color: #1F2937;">Datos del nuevo usuario:</p>
                                <table style="width: 100%; border-collapse: collapse;">
                                    <tr>
                                        <td style="padding: 10px 0; color: #6B7280; font-size: 13px; width: 120px; border-bottom: 1px solid #E5E7EB;">Nombre:</td>
                                        <td style="padding: 10px 0; color: #1F2937; font-weight: 500; border-bottom: 1px solid #E5E7EB;">{user.full_name}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 10px 0; color: #6B7280; font-size: 13px; border-bottom: 1px solid #E5E7EB;">Email:</td>
                                        <td style="padding: 10px 0; color: #1F2937; font-weight: 500; border-bottom: 1px solid #E5E7EB;">{user.email}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 10px 0; color: #6B7280; font-size: 13px; border-bottom: 1px solid #E5E7EB;">Identificación:</td>
                                        <td style="padding: 10px 0; color: #1F2937; font-weight: 500; border-bottom: 1px solid #E5E7EB;">{user.identification}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 10px 0; color: #6B7280; font-size: 13px;">Teléfono:</td>
                                        <td style="padding: 10px 0; color: #1F2937; font-weight: 500;">{user.phone}</td>
                                    </tr>
                                </table>
                            </div>
                            <div style="text-align: center; margin-top: 30px;">
                                <a href="{system_url}" class="button" style="color: white;">
                                    Revisar Usuario
                                </a>
                            </div>
                        </div>
                        {get_email_footer()}
                    </div>
                </body>
                </html>
                """

                enviar_correo_simple(
                    asunto="Nuevo Usuario Pendiente de Aprobación",
                    contenido_html=html_content_admin,
                    destinatarios=admin_emails
                )

            return Response({
                "detail": "Usuario registrado exitosamente. Tu cuenta está pendiente de aprobación.",
                "user_id": user.id
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "detail": f"Error al crear el usuario: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserListAPIView(ListAPIView):
    serializer_class = UserSerializer
    pagination_class = UserPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = User.objects.all()
        search_query = self.request.query_params.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(full_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(username__icontains=search_query)
            )
        return queryset


class UserCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None

    def get(self, request, pk):
        user = self.get_object(pk)
        if user is not None:
            serializer = UserSerializer(user)
            return Response(serializer.data)
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)


class UserUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": USUARIO_NO_ENCONTRADO}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserPatchAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": USUARIO_NO_ENCONTRADO}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": USUARIO_NO_ENCONTRADO}, status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GroupListAPIView(ListAPIView):
    serializer_class = GroupSerializer
    pagination_class = UserPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Group.objects.all()
