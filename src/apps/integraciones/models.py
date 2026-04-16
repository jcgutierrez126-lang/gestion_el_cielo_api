from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import secrets
import hashlib

FECHA_CREACION_LABEL = "Fecha de Creacion"


class APIKey(models.Model):
    """
    API Keys para clientes de servicio (ej: Bot de Teams).
    El bot envia: X-API-Key: <key> en cada request.
    La key se almacena hasheada — nunca en texto plano.
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre del cliente")
    key_prefix = models.CharField(max_length=8, verbose_name="Prefijo (identificacion)")
    key_hash = models.CharField(max_length=64, unique=True, verbose_name="Hash de la key")
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "api_keys"
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"

    def __str__(self):
        return f"{self.name} ({self.key_prefix}...)"

    @classmethod
    def create_key(cls, name: str):
        """Genera una nueva API key. Retorna (instancia, key_en_texto_plano)."""
        raw_key = secrets.token_urlsafe(32)
        prefix = raw_key[:8]
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        instance = cls.objects.create(name=name, key_prefix=prefix, key_hash=key_hash)
        return instance, raw_key

    @classmethod
    def validate(cls, raw_key: str):
        """Valida una key en texto plano. Retorna la instancia si es valida."""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        return cls.objects.filter(key_hash=key_hash, is_active=True).first()


class SuplosToken(models.Model):
    """
    Modelo para almacenar y gestionar el token de Supplos.
    """
    access_token = models.TextField(verbose_name="Token de Acceso")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=FECHA_CREACION_LABEL)
    expires_at = models.DateTimeField(verbose_name="Fecha de Expiracion")
    is_active = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        db_table = "supplos_tokens"
        verbose_name = "Token Supplos"
        verbose_name_plural = "Tokens Supplos"

    def __str__(self):
        return f"Token Supplos - Expira: {self.expires_at}"

    @property
    def is_valid(self):
        """Verifica si el token aun es valido."""
        from django.utils import timezone
        from datetime import timedelta
        return self.is_active and self.expires_at > timezone.now() + timedelta(minutes=5)


class Pedido(models.Model):
    """
    Modelo principal para almacenar pedidos consolidados de Supplos y Graph.
    Representa el estado actual del pedido.
    """

    class EstadoPedido(models.TextChoices):
        VIGENTE = 'Vigente', 'Vigente'
        ENTREGADO = 'Entregado', 'Entregado'
        PARCIAL = 'Parcial', 'Entrega Parcial'
        PENDIENTE = 'Pendiente', 'Pendiente'
        CANCELADO = 'Cancelado', 'Cancelado'
        EN_TRANSITO = 'En Transito', 'En Transito'

    # Identificacion del pedido
    proveedor_centro_suministrador = models.CharField(
        max_length=100,
        blank=True,
        null=True,  # NOSONAR
        verbose_name="Proveedor/Centro Suministrador"
    )
    razon_social = models.CharField(
        max_length=255,
        blank=True,
        null=True,  # NOSONAR
        verbose_name="Razon Social"
    )
    comprador = models.CharField(
        max_length=255,
        blank=True,
        null=True,  # NOSONAR
        verbose_name="Comprador"
    )
    organizacion_compras = models.CharField(
        max_length=100,
        blank=True,
        null=True,  # NOSONAR
        verbose_name="Organizacion de Compras"
    )
    planta = models.CharField(
        max_length=100,
        blank=True,
        null=True,  # NOSONAR
        verbose_name="Planta"
    )
    documento_compras = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name="Documento de Compras / Numero de Pedido"
    )
    posicion = models.CharField(
        max_length=20,
        blank=True,
        null=True,  # NOSONAR
        verbose_name="Posicion"
    )

    # Datos del material
    material = models.CharField(
        max_length=100,
        blank=True,
        null=True,  # NOSONAR
        verbose_name="Material"
    )
    texto_breve = models.TextField(
        blank=True,
        null=True,  # NOSONAR
        verbose_name="Texto Breve / Descripcion"
    )

    # Cantidades y precios
    cantidad_pedido = models.DecimalField(
        max_digits=15,
        decimal_places=3,
        default=Decimal('0.000'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Cantidad Pedido"
    )
    por_entregar = models.DecimalField(
        max_digits=15,
        decimal_places=3,
        default=Decimal('0.000'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Por Entregar"
    )
    precio_neto = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Precio Neto"
    )

    # Fechas
    fecha_entrega = models.DateField(
        blank=True,
        null=True,  # NOSONAR
        verbose_name="Fecha de Entrega"
    )
    fecha_programada = models.DateTimeField(
        blank=True,
        null=True,  # NOSONAR
        verbose_name="Fecha Programada"
    )

    # Estado y observaciones
    estado_pedido = models.CharField(
        max_length=30,
        choices=EstadoPedido.choices,
        default=EstadoPedido.VIGENTE,
        verbose_name="Estado del Pedido"
    )
    motivo = models.TextField(
        blank=True,
        null=True,  # NOSONAR
        verbose_name="Motivo"
    )
    observaciones = models.TextField(
        blank=True,
        null=True,  # NOSONAR
        verbose_name="Observaciones (Proveedor)"
    )
    estado = models.CharField(
        max_length=50,
        blank=True,
        null=True,  # NOSONAR
        verbose_name="Estado Interno"
    )
    observaciones_cielo = models.TextField(
        blank=True,
        null=True,  # NOSONAR
        verbose_name="Observaciones Cielo"
    )

    # Metadatos de sincronizacion
    fuente_supplos = models.BooleanField(
        default=False,
        verbose_name="Datos de Supplos"
    )
    fuente_graph = models.BooleanField(
        default=False,
        verbose_name="Datos de Graph/Email"
    )
    ultima_sincronizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Ultima Sincronizacion"
    )
    datos_raw_supplos = models.JSONField(
        blank=True,
        null=True,  # NOSONAR
        verbose_name="Datos crudos Supplos"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=FECHA_CREACION_LABEL)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualizacion")
    status = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        db_table = "pedidos"
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-created_at']
        unique_together = ['documento_compras', 'posicion']
        indexes = [
            models.Index(fields=['documento_compras']),
            models.Index(fields=['estado_pedido']),
            models.Index(fields=['fecha_entrega']),
            models.Index(fields=['razon_social']),
        ]

    def __str__(self):
        return f"Pedido {self.documento_compras} - Pos {self.posicion or 'N/A'}"


class TrazabilidadPedido(models.Model):
    """
    Modelo para almacenar el historial de cambios/actualizaciones de un pedido.
    Permite ver la evolucion del pedido en el tiempo.
    """

    class FuenteDatos(models.TextChoices):
        SUPPLOS = 'SUPPLOS', 'Supplos'
        GRAPH = 'GRAPH', 'Graph/Email'
        MANUAL = 'MANUAL', 'Manual'

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='trazabilidad',
        verbose_name="Pedido"
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Registro"
    )
    fuente = models.CharField(
        max_length=20,
        choices=FuenteDatos.choices,
        verbose_name="Fuente de Datos"
    )

    # Cambios de estado
    estado_anterior = models.CharField(
        max_length=30,
        blank=True,
        null=True,  # NOSONAR
        verbose_name="Estado Anterior"
    )
    estado_nuevo = models.CharField(
        max_length=30,
        blank=True,
        null=True,  # NOSONAR
        verbose_name="Estado Nuevo"
    )

    # Observaciones del momento
    observaciones = models.TextField(
        blank=True,
        null=True,  # NOSONAR
        verbose_name="Observaciones"
    )
    observaciones_proveedor = models.TextField(
        blank=True,
        null=True,  # NOSONAR
        verbose_name="Observaciones del Proveedor"
    )

    # Referencia al correo si viene de Graph
    email_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,  # NOSONAR
        verbose_name="ID del Email"
    )
    email_subject = models.CharField(
        max_length=500,
        blank=True,
        null=True,  # NOSONAR
        verbose_name="Asunto del Email"
    )
    email_from = models.CharField(
        max_length=255,
        blank=True,
        null=True,  # NOSONAR
        verbose_name="Remitente del Email"
    )
    email_date = models.DateTimeField(
        blank=True,
        null=True,  # NOSONAR
        verbose_name="Fecha del Email"
    )

    # Datos crudos para referencia
    datos_raw = models.JSONField(
        blank=True,
        null=True,  # NOSONAR
        verbose_name="Datos Crudos"
    )

    class Meta:
        db_table = "trazabilidad_pedidos"
        verbose_name = "Trazabilidad de Pedido"
        verbose_name_plural = "Trazabilidad de Pedidos"
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"Trazabilidad {self.pedido.documento_compras} - {self.fecha_registro}"


class LogConsulta(models.Model):
    """
    Modelo para registrar el historial de consultas realizadas a las APIs.
    """

    class TipoConsulta(models.TextChoices):
        SUPPLOS = 'SUPPLOS', 'Consulta Supplos'
        GRAPH = 'GRAPH', 'Consulta Graph'
        CONSOLIDACION = 'CONSOLIDACION', 'Consolidacion'

    tipo = models.CharField(
        max_length=20,
        choices=TipoConsulta.choices,
        verbose_name="Tipo de Consulta"
    )
    parametros = models.JSONField(verbose_name="Parametros de Consulta")
    respuesta_exitosa = models.BooleanField(default=False, verbose_name="Respuesta Exitosa")
    mensaje_error = models.TextField(blank=True, null=True, verbose_name="Mensaje de Error")  # NOSONAR
    tiempo_respuesta_ms = models.PositiveIntegerField(default=0, verbose_name="Tiempo de Respuesta (ms)")
    usuario = models.ForeignKey(
        'usuarios.User',
        on_delete=models.SET_NULL,
        null=True,  # NOSONAR
        blank=True,
        related_name='consultas_integracion',
        verbose_name="Usuario"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=FECHA_CREACION_LABEL)

    class Meta:
        db_table = "log_consultas"
        verbose_name = "Log de Consulta"
        verbose_name_plural = "Logs de Consultas"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.tipo} - {self.created_at}"


class CorreoAutorizado(models.Model):
    """
    Modelo para gestionar los correos/buzones autorizados para buscar pedidos.
    Solo se buscara en los buzones que esten en esta lista.
    """
    email = models.EmailField(
        unique=True,
        verbose_name="Correo Electronico"
    )
    nombre = models.CharField(
        max_length=255,
        blank=True,
        null=True,  # NOSONAR
        verbose_name="Nombre/Descripcion"
    )
    es_buzon_principal = models.BooleanField(
        default=False,
        verbose_name="Es Buzon Principal",
        help_text="Si es True, se usara como buzon para enviar busquedas"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=FECHA_CREACION_LABEL)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualizacion")

    class Meta:
        db_table = "correos_autorizados"
        verbose_name = "Correo Autorizado"
        verbose_name_plural = "Correos Autorizados"
        ordering = ['-es_buzon_principal', 'email']

    def __str__(self):
        return f"{self.email} {'(Principal)' if self.es_buzon_principal else ''}"

    @classmethod
    def get_correos_activos(cls):
        """Retorna lista de emails activos."""
        return list(cls.objects.filter(activo=True).values_list('email', flat=True))

    @classmethod
    def get_buzon_principal(cls):
        """Retorna el buzon principal para hacer busquedas."""
        buzon = cls.objects.filter(es_buzon_principal=True, activo=True).first()
        return buzon.email if buzon else None


class CorreoProcesado(models.Model):
    """
    Modelo para registrar los correos que ya fueron procesados.
    Evita procesar el mismo correo multiples veces.
    """
    email_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name="ID del Email en Graph"
    )
    buzon = models.CharField(
        max_length=255,
        verbose_name="Buzon de Origen"
    )
    subject = models.CharField(
        max_length=500,
        blank=True,
        null=True,  # NOSONAR
        verbose_name="Asunto"
    )
    fecha_email = models.DateTimeField(
        blank=True,
        null=True,  # NOSONAR
        verbose_name="Fecha del Email"
    )
    pedidos_relacionados = models.ManyToManyField(
        Pedido,
        blank=True,
        related_name='correos_procesados',
        verbose_name="Pedidos Relacionados"
    )
    procesado_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Procesamiento"
    )

    class Meta:
        db_table = "correos_procesados"
        verbose_name = "Correo Procesado"
        verbose_name_plural = "Correos Procesados"
        ordering = ['-procesado_at']

    def __str__(self):
        return f"{self.subject[:50]}... - {self.procesado_at}"

    @classmethod
    def ya_procesado(cls, email_id: str) -> bool:
        """Verifica si un correo ya fue procesado."""
        return cls.objects.filter(email_id=email_id).exists()
