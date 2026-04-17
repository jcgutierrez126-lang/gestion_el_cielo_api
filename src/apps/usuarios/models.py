from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, Group
from django.utils import timezone
from django.contrib.auth.hashers import make_password

DEFAULT_IMG_USER = 'user/profile.jpeg'

class UserManager(BaseUserManager):
    def create_user(self, username, email, first_name, last_name, password=None):
        """
        Crea y guarda un usuario con el username, correo electrónico, nombre, apellido y contraseña.
        """
        if not username:
            raise ValueError('El usuario debe tener un nombre de usuario.')
        if not email:
            raise ValueError('El usuario debe tener un correo electrónico.')
        if not first_name:
            raise ValueError('El usuario debe tener un nombre.')
        if not last_name:
            raise ValueError('El usuario debe tener un apellido.')

        user = self.model(
            username=username,
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
        )
        
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, email, first_name, last_name, password=None):
        """
        Crea y guarda un superusuario con los detalles dados.
        """
        user = self.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
        )
        user.is_admin = True
        user.status = True
        user.is_superuser = True
        user.save()
        return user

class User(AbstractBaseUser):
    """
    Modelo de usuario personalizado que admite el inicio de sesión con el correo electrónico en lugar del nombre de usuario.
    """
    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True, db_index=True, blank=True, null=True, verbose_name="Usuario")
    first_name = models.CharField(max_length=150, blank=False, verbose_name="Nombres")
    last_name = models.CharField(max_length=255, blank=False, verbose_name="Apellidos")
    full_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nombre completo")
    phone = models.CharField(max_length=100, blank=False, verbose_name="Teléfono")
    identification = models.CharField(max_length=100, blank=False, verbose_name="Identificación")
    born_date = models.DateField(blank=True, null=True ,verbose_name="Fecha de nacimiento")
    email = models.EmailField(unique=True, db_index=True, verbose_name="Correo electrónico")
    image = models.ImageField(upload_to='user/', blank=True, null=True, default=DEFAULT_IMG_USER, verbose_name="Imagen de usuario")    
    is_admin = models.BooleanField(default=False, verbose_name="Administrador")
    role = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='users', null=True, blank=True, verbose_name="Rol")
    status = models.BooleanField(default=True, verbose_name="Estado")
    created_at = models.DateTimeField(default=timezone.now, db_index=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")
    last_login = models.DateTimeField(blank=True, null=True, verbose_name="Último inicio de sesión")
    objects = UserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email' ,'first_name', 'last_name']
 
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        if not self.full_name:
            self.full_name = f"{self.first_name} {self.last_name}"

        if self.password and not self.password.startswith('pbkdf2_'):
            self.set_password(self.password)

        super(User, self).save(*args, **kwargs)
        
    def has_perm(self, perm, obj=None):
        "El usuario tiene un permiso especifico?"
        return True
    
    def has_rol_perm(self, perms):
        if self.is_admin:
            return True
        user_perms = [p.codename for p in self.role.permissions.all()]

        return any(perm in user_perms for perm in perms)

    def has_module_perms(self, app_label):
        "El usuario tiene permisos a un modulo especifico?"
        return True

    @property
    def is_staff(self):
        "El usuario es un administrador?"
        return self.is_admin
    
    class Meta:
        db_table = "users"

    def __str__(self):
        return self.email
