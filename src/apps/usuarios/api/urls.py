from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.usuarios.api.views import (
    UserLoginView,
    UserListAPIView,
    UserCreateAPIView,
    UserDetailAPIView,
    UserUpdateAPIView,
    UserDeleteAPIView,
    UserPatchAPIView,
    GroupListAPIView,
    PasswordResetRequestAPIView,
    PasswordResetConfirmAPIView,
    VerifyResetCodeAPIView,
    UserRegisterAPIView,
    MeView,
    UserSettingsListView,
    UserSettingsCreateView,
    UserSettingsPatchView,
    UserSettingsDeleteView,
)

urlpatterns = [
    # Autenticación
    path('login/', UserLoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('register/', UserRegisterAPIView.as_view(), name='register'),

    # Restablecimiento de contraseña
    path('password-reset/', PasswordResetRequestAPIView.as_view(), name='password-reset'),
    path('password-reset/verify/', VerifyResetCodeAPIView.as_view(), name='password-reset-verify'),
    path('password-reset/confirm/', PasswordResetConfirmAPIView.as_view(), name='password-reset-confirm'),

    # Gestión de usuarios (requieren autenticación)
    path('user-list/', UserListAPIView.as_view(), name='user-list'),
    path('user-create/', UserCreateAPIView.as_view(), name='user-create'),
    path('<str:pk>/user-detail/', UserDetailAPIView.as_view(), name='user-detail'),
    path('<str:pk>/user-update/', UserUpdateAPIView.as_view(), name='user-update'),
    path('<str:pk>/user-delete/', UserDeleteAPIView.as_view(), name='user-delete'),
    path('<str:pk>/user-patch/', UserPatchAPIView.as_view(), name='user-patch'),

    # Grupos
    path('group-list/', GroupListAPIView.as_view(), name='group-list'),

    # Perfil del usuario autenticado
    path('me/', MeView.as_view(), name='me'),

    # Gestión de usuarios (settings page)
    path('settings/list/', UserSettingsListView.as_view(), name='settings-user-list'),
    path('settings/create/', UserSettingsCreateView.as_view(), name='settings-user-create'),
    path('settings/<int:pk>/patch/', UserSettingsPatchView.as_view(), name='settings-user-patch'),
    path('settings/<int:pk>/delete/', UserSettingsDeleteView.as_view(), name='settings-user-delete'),
]
