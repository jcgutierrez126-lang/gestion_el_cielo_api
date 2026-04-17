from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListAPIView
from cieloapi.filtering import filter_by_search
from apps.usuarios.models import User
from apps.usuarios.api.serializers import UserSerializer, GroupSerializer
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import Group

USER_NOT_FOUND = "Not found."

class UserPagination(PageNumberPagination):
    """
    Clase para la paginación de usuarios.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    
class UserListAPIView(ListAPIView):
    """
    Vista para listar los usuarios.
    """
    serializer_class = UserSerializer
    pagination_class = UserPagination
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = User.objects.all()
        search_query = self.request.query_params.get('search', '').strip()

        if search_query:
            queryset = list(queryset)
            queryset = filter_by_search(queryset, search_query, ['full_name'])

        return queryset

class UserCreateAPIView(APIView):
    """
    Vista para crear un usuario.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDetailAPIView(APIView):
    """
    Vista para ver los detalles de un usuario.
    """
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
        return Response({"detail": USER_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
    
class UserUpdateAPIView(APIView):
    """
    Vista para actualizar un usuario.
    """
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None
    
    def put(self, request, pk):
        user = self.get_object(pk)
        if user is not None:
            serializer = UserSerializer(user, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": USER_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

class UserDeleteAPIView(APIView):
    """
    Vista para eliminar un usuario.
    """
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None
    
    def delete(self, request, pk):
        user = self.get_object(pk)
        if user is not None:
            user.delete()
            return Response({"detail": "Deleted."})
        return Response({"detail": USER_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
    
class UserPatchAPIView(APIView):
    """
    Vista para actualizar parcialmente un usuario.
    """
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None
    
    def patch(self, request, pk):
        user = self.get_object(pk)
        if user is not None:
            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": USER_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
    
class GroupListAPIView(ListAPIView):
    """
    Vista para listar los grupos.
    """
    serializer_class = GroupSerializer 
    pagination_class = UserPagination
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Group.objects.all()