from rest_framework import serializers
from .models import Empleado, ControlSemanal, PrestamoEmpleado, AbonoPrestamo, TipoLabor, TipoCobro


class TipoLaborSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoLabor
        fields = ['id', 'abreviatura', 'nombre', 'activo', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class TipoCobroSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoCobro
        fields = ['id', 'abreviatura', 'nombre', 'activo', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class EmpleadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empleado
        fields = [
            'id', 'nombre_completo', 'cedula', 'telefono', 'labor',
            'jornal', 'fecha_ingreso',
            'salario_mensual', 'salario_semanal',
            'eps', 'pension', 'arl', 'caja_compensacion',
            'activo', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class ControlSemanalSerializer(serializers.ModelSerializer):
    empleado_nombre = serializers.CharField(source='empleado.nombre_completo', read_only=True)
    tipo_labor_nombre = serializers.CharField(source='tipo_labor.nombre', read_only=True)
    tipo_labor_abreviatura = serializers.CharField(source='tipo_labor.abreviatura', read_only=True, default=None)
    tipo_cobro_nombre = serializers.CharField(source='tipo_cobro.nombre', read_only=True)
    tipo_cobro_abreviatura = serializers.CharField(source='tipo_cobro.abreviatura', read_only=True, default=None)
    lote_nombre = serializers.CharField(source='lote.nombre', read_only=True, default=None)
    lote_abreviatura = serializers.CharField(source='lote.abreviatura', read_only=True, default=None)

    class Meta:
        model = ControlSemanal
        fields = [
            'id', 'empleado', 'empleado_nombre',
            'semana_ref', 'dia', 'fecha',
            'fecha_inicio', 'fecha_fin',
            'tipo_labor', 'tipo_labor_nombre', 'tipo_labor_abreviatura',
            'tipo_cobro', 'tipo_cobro_nombre', 'tipo_cobro_abreviatura',
            'lote', 'lote_nombre', 'lote_abreviatura',
            'kilos', 'jornales', 'costo_unidad', 'valor',
            'observaciones', 'es_vale',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class AbonoPrestamoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AbonoPrestamo
        fields = ['id', 'prestamo', 'fecha', 'valor', 'nota', 'created_at']
        read_only_fields = ['created_at']


class PrestamoEmpleadoSerializer(serializers.ModelSerializer):
    empleado_nombre = serializers.CharField(source='empleado.nombre_completo', read_only=True)
    abonos = AbonoPrestamoSerializer(many=True, read_only=True)

    class Meta:
        model = PrestamoEmpleado
        fields = [
            'id', 'empleado', 'empleado_nombre',
            'fecha', 'valor', 'concepto', 'saldo',
            'abonos', 'created_at', 'updated_at',
        ]
        read_only_fields = ['saldo', 'created_at', 'updated_at']

    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.saldo = instance.valor
        instance.save(update_fields=['saldo'])
        return instance


class PrestamoEmpleadoListSerializer(serializers.ModelSerializer):
    empleado_nombre = serializers.CharField(source='empleado.nombre_completo', read_only=True)

    class Meta:
        model = PrestamoEmpleado
        fields = [
            'id', 'empleado', 'empleado_nombre',
            'fecha', 'valor', 'concepto', 'saldo',
            'created_at',
        ]
        read_only_fields = ['saldo', 'created_at']
