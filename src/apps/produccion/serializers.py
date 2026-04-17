from rest_framework import serializers
from .models import (
    Lote, VentaCafe, VentaCafeTostado, VentaBanano,
    Floracion, MezclaAbono, MezclaAbonoFertilizante,
)


class LoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lote
        fields = [
            'id', 'nombre', 'variedad', 'año_siembra', 'proxima_renovacion',
            'num_arboles', 'gramos_abono_palo',
            'bultos_produccion', 'bultos_urea', 'bultos_dap',
            'activo', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class VentaCafeSerializer(serializers.ModelSerializer):
    cuenta_destino_nombre = serializers.CharField(source='cuenta_destino.nombre', read_only=True)

    class Meta:
        model = VentaCafe
        fields = [
            'id', 'fecha', 'kilos', 'cargas', 'tipo_cafe', 'factor',
            'precio_kilo', 'precio_carga', 'comprador',
            'valor_total', 'deduccion', 'retefuente', 'valor_neto',
            'cuenta_destino', 'cuenta_destino_nombre',
            'facturado_a', 'conversion_cereza_seco',
            'beneficio', 'transportador', 'valor_transporte',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class VentaCafeTostadoSerializer(serializers.ModelSerializer):
    cuenta_destino_nombre = serializers.CharField(source='cuenta_destino.nombre', read_only=True)

    class Meta:
        model = VentaCafeTostado
        fields = [
            'id', 'fecha_venta', 'cliente', 'cantidad', 'presentacion',
            'tipo_cafe', 'seleccionado', 'valor',
            'cuenta_destino', 'cuenta_destino_nombre',
            'fecha_pago', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class VentaBananoSerializer(serializers.ModelSerializer):
    cuenta_destino_nombre = serializers.CharField(source='cuenta_destino.nombre', read_only=True)

    class Meta:
        model = VentaBanano
        fields = [
            'id', 'fecha', 'tipo_platano', 'kilos', 'precio_kilo', 'valor_total',
            'cuenta_destino', 'cuenta_destino_nombre',
            'facturado_a', 'observaciones',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class FloracionSerializer(serializers.ModelSerializer):
    lote_nombre = serializers.CharField(source='lote.nombre', read_only=True, default=None)

    class Meta:
        model = Floracion
        fields = [
            'id', 'fecha', 'lote', 'lote_nombre', 'calidad',
            'abonada_ideal', 'broca_ideal', 'roya_ideal',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class MezclaAbonoFertilizanteSerializer(serializers.ModelSerializer):
    class Meta:
        model = MezclaAbonoFertilizante
        fields = ['id', 'fertilizante', 'num_bultos', 'precio_bulto']


class MezclaAbonoSerializer(serializers.ModelSerializer):
    lote_nombre = serializers.CharField(source='lote.nombre', read_only=True, default=None)
    fertilizantes = MezclaAbonoFertilizanteSerializer(many=True, required=False)

    class Meta:
        model = MezclaAbono
        fields = [
            'id', 'fecha', 'formula', 'lote', 'lote_nombre',
            'num_arboles', 'gramos_por_arbol', 'costo_total',
            'fertilizantes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        fertilizantes_data = validated_data.pop('fertilizantes', [])
        mezcla = MezclaAbono.objects.create(**validated_data)
        for f in fertilizantes_data:
            MezclaAbonoFertilizante.objects.create(mezcla=mezcla, **f)
        return mezcla

    def update(self, instance, validated_data):
        fertilizantes_data = validated_data.pop('fertilizantes', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if fertilizantes_data is not None:
            instance.fertilizantes.all().delete()
            for f in fertilizantes_data:
                MezclaAbonoFertilizante.objects.create(mezcla=instance, **f)
        return instance
