from rest_framework import serializers
from .models import Ciudad, Cuenta, Proveedor, Egreso, Ingreso, Transaccion, Observacion, InversionCDT


class CuentaSerializer(serializers.ModelSerializer):
    saldo = serializers.DecimalField(
        source='saldo_inicial', max_digits=15, decimal_places=2, required=False
    )
    activa = serializers.BooleanField(source='status', required=False, default=True)

    class Meta:
        model = Cuenta
        fields = ['id', 'nombre', 'tipo', 'saldo', 'activa', 'numero_cuenta', 'banco', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class CiudadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ciudad
        fields = ['id', 'nombre', 'status']


class ProveedorSerializer(serializers.ModelSerializer):
    ciudad_nombre = serializers.CharField(source='ciudad.nombre', read_only=True, default=None)

    class Meta:
        model = Proveedor
        fields = [
            'id', 'nombre', 'telefono', 'celular', 'cedula_nit',
            'direccion', 'ciudad', 'ciudad_nombre', 'email', 'comentarios',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class EgresoSerializer(serializers.ModelSerializer):
    cuenta_nombre = serializers.CharField(source='cuenta.nombre', read_only=True)
    proveedor_nombre = serializers.CharField(source='proveedor.nombre', read_only=True, default=None)

    class Meta:
        model = Egreso
        fields = [
            'id', 'fecha', 'nombre', 'descripcion', 'cantidad', 'unidad',
            'valor', 'cuenta', 'cuenta_nombre', 'categoria',
            'proveedor', 'proveedor_nombre',
            'nit_proveedor_destino', 'facturado_a',
            'abono_deuda', 'restante', 'estado',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class IngresoSerializer(serializers.ModelSerializer):
    cuenta_destino_nombre = serializers.CharField(source='cuenta_destino.nombre', read_only=True)

    class Meta:
        model = Ingreso
        fields = [
            'id', 'fecha', 'descripcion', 'valor',
            'cuenta_destino', 'cuenta_destino_nombre',
            'origen', 'observaciones',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class TransaccionSerializer(serializers.ModelSerializer):
    cuenta_origen_nombre = serializers.CharField(source='cuenta_origen.nombre', read_only=True, default=None)
    cuenta_destino_nombre = serializers.CharField(source='cuenta_destino.nombre', read_only=True)

    class Meta:
        model = Transaccion
        fields = [
            'id', 'fecha',
            'cuenta_origen', 'cuenta_origen_nombre',
            'cuenta_destino', 'cuenta_destino_nombre',
            'valor', 'observaciones',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class ObservacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Observacion
        fields = ['id', 'fecha', 'observacion', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class InversionCDTSerializer(serializers.ModelSerializer):
    cuenta_origen_nombre = serializers.CharField(source='cuenta_origen.nombre', read_only=True)
    plazo_dias = serializers.IntegerField(read_only=True)
    rendimiento_proyectado = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True)

    class Meta:
        model = InversionCDT
        fields = [
            'id', 'entidad', 'monto', 'tasa_ea',
            'fecha_inicio', 'fecha_vencimiento', 'plazo_dias',
            'estado', 'cuenta_origen', 'cuenta_origen_nombre',
            'rendimiento_proyectado', 'rendimiento_real',
            'fecha_liquidacion', 'observaciones',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
