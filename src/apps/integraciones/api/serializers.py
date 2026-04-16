from rest_framework import serializers
from apps.integraciones.models import (
    Pedido,
    TrazabilidadPedido,
    LogConsulta,
    CorreoAutorizado,
    CorreoProcesado,
)


class TrazabilidadPedidoSerializer(serializers.ModelSerializer):
    """Serializer para la trazabilidad de pedidos."""

    fuente_display = serializers.CharField(source='get_fuente_display', read_only=True)

    class Meta:
        model = TrazabilidadPedido
        fields = [
            'id',
            'fecha_registro',
            'fuente',
            'fuente_display',
            'estado_anterior',
            'estado_nuevo',
            'observaciones',
            'observaciones_proveedor',
            'email_id',
            'email_subject',
            'email_from',
            'email_date',
        ]


class PedidoSerializer(serializers.ModelSerializer):
    """Serializer principal para pedidos."""

    estado_pedido_display = serializers.CharField(
        source='get_estado_pedido_display',
        read_only=True
    )
    trazabilidad = TrazabilidadPedidoSerializer(many=True, read_only=True)

    class Meta:
        model = Pedido
        fields = [
            'id',
            'proveedor_centro_suministrador',
            'razon_social',
            'comprador',
            'organizacion_compras',
            'planta',
            'documento_compras',
            'posicion',
            'material',
            'texto_breve',
            'cantidad_pedido',
            'por_entregar',
            'precio_neto',
            'fecha_entrega',
            'fecha_programada',
            'estado_pedido',
            'estado_pedido_display',
            'motivo',
            'observaciones',
            'estado',
            'observaciones_cielo',
            'fuente_supplos',
            'fuente_graph',
            'ultima_sincronizacion',
            'trazabilidad',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'fuente_supplos',
            'fuente_graph',
            'ultima_sincronizacion',
            'created_at',
            'updated_at'
        ]


class PedidoListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listados de pedidos."""

    estado_pedido_display = serializers.CharField(
        source='get_estado_pedido_display',
        read_only=True
    )

    class Meta:
        model = Pedido
        fields = [
            'id',
            'proveedor_centro_suministrador',
            'razon_social',
            'comprador',
            'organizacion_compras',
            'planta',
            'documento_compras',
            'posicion',
            'material',
            'texto_breve',
            'cantidad_pedido',
            'por_entregar',
            'precio_neto',
            'fecha_entrega',
            'fecha_programada',
            'estado_pedido',
            'estado_pedido_display',
            'motivo',
            'observaciones',
            'estado',
            'observaciones_cielo',
            'fuente_supplos',
            'fuente_graph',
            'created_at',
        ]


class BuscarPedidoRequestSerializer(serializers.Serializer):
    """Serializer para la solicitud de busqueda de pedidos."""

    numero_pedido = serializers.IntegerField(
        required=True,
        help_text="Numero del pedido a buscar"
    )
    empresas = serializers.ListField(
        child=serializers.ChoiceField(choices=['corona', 'alion']),
        required=False,
        default=['corona', 'alion'],
        help_text="Lista de empresas donde buscar"
    )
    buscar_correos = serializers.BooleanField(
        required=False,
        default=True,
        help_text="Si debe buscar en correos de Graph"
    )

    def validate_numero_pedido(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "El numero de pedido debe ser positivo"
            )
        return value


class BuscarPedidoResponseSerializer(serializers.Serializer):
    """Serializer para la respuesta de busqueda de pedidos."""

    numero_pedido = serializers.IntegerField()
    supplos = serializers.DictField(allow_null=True)
    graph = serializers.DictField(allow_null=True)
    consolidado = serializers.BooleanField()
    pedidos_guardados = serializers.ListField(child=serializers.DictField())
    errores = serializers.ListField(child=serializers.CharField())


class LogConsultaSerializer(serializers.ModelSerializer):
    """Serializer para logs de consulta."""

    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    usuario_email = serializers.CharField(source='usuario.email', read_only=True, allow_null=True)

    class Meta:
        model = LogConsulta
        fields = [
            'id',
            'tipo',
            'tipo_display',
            'parametros',
            'respuesta_exitosa',
            'mensaje_error',
            'tiempo_respuesta_ms',
            'usuario',
            'usuario_email',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ActualizarPedidoSerializer(serializers.ModelSerializer):
    """Serializer para actualizar campos editables del pedido (observaciones Cielo)."""

    class Meta:
        model = Pedido
        fields = [
            'estado_pedido',
            'motivo',
            'observaciones_cielo',
        ]


class CorreoAutorizadoSerializer(serializers.ModelSerializer):
    """Serializer para correos autorizados."""

    class Meta:
        model = CorreoAutorizado
        fields = [
            'id',
            'email',
            'nombre',
            'es_buzon_principal',
            'activo',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_email(self, value):
        """Valida que el email sea unico (excluyendo la instancia actual en updates)."""
        instance = self.instance
        if CorreoAutorizado.objects.filter(email=value).exclude(
            pk=instance.pk if instance else None
        ).exists():
            raise serializers.ValidationError("Este correo ya esta registrado.")
        return value

    def validate(self, data):
        """Si se marca como principal, desmarcar los demas."""
        if data.get('es_buzon_principal', False):
            # Se manejara en la vista para desmarcar otros
            pass
        return data


class CorreoProcesadoSerializer(serializers.ModelSerializer):
    """Serializer para correos procesados."""

    class Meta:
        model = CorreoProcesado
        fields = [
            'id',
            'email_id',
            'buzon',
            'subject',
            'fecha_email',
            'procesado_at',
        ]
        read_only_fields = ['id', 'procesado_at']
