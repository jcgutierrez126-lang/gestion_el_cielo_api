from rest_framework import serializers
from django.contrib.auth.models import Group
from django.contrib.auth.hashers import make_password
from apps.usuarios.models import User

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']

class UserSerializer(serializers.ModelSerializer):
    role_detail = GroupSerializer(source='role', read_only=True)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'full_name',
            'phone',
            'identification',
            'born_date',
            'email',
            'image',
            'is_admin',
            'role',
            'role_detail',
            'status',
            'password',
        ]
        read_only_fields = ('full_name',)

    def create(self, validated_data):
        # separar campos que NO van al manager
        role = validated_data.pop('role', None)
        password = validated_data.pop('password', None)

        # crear usuario base
        user = User.objects.create_user(
            username=validated_data.pop('username'),
            email=validated_data.pop('email'),
            first_name=validated_data.pop('first_name'),
            last_name=validated_data.pop('last_name'),
            password=password,
        )

        # asignar el resto de campos del modelo
        for attr, value in validated_data.items():
            setattr(user, attr, value)

        if role:
            user.role = role

        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            raise serializers.ValidationError('Debe incluir "username" y "password".')
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError('Credenciales inválidas.')

        if not user.check_password(password):
            raise serializers.ValidationError('Credenciales inválidas.')
        
        if not user.status:
            raise serializers.ValidationError('Esta cuenta de usuario está inactiva.')

        data['username'] = user
        return data