from django.db import migrations, models
import django.db.models.deletion


BANANO_NOMBRES = [
    "África", "Banano Cali", "Banano Exito", "Banano Extra",
    "Banano Pos Supermercado", "Banano Primera", "Banano Segunda",
    "Dominico", "Dominico Extra", "Dominico Primera", "Dominico Segunda",
    "Guineo", "Harton Extra", "Harton Primera", "Harton Segunda",
    "Murrapo", "Plátano Exito", "Plátano Extra", "Plátano Segunda",
]

CAFE_NOMBRES = ["Corriente", "El Encuentro", "Pasilla", "Pergamino"]

# Mapeo de slugs viejos → nombre nuevo en el maestro
BANANO_MAP = {
    'banano_extra':    'Banano Extra',
    'banano_primera':  'Banano Primera',
    'banano_segunda':  'Banano Segunda',
    'platano_extra':   'Plátano Extra',
    'platato_segunda': 'Plátano Segunda',
    'platano_segunda': 'Plátano Segunda',
    'africa_extra':    'África',
    'africa_primera':  'África',
    'africa_segunda':  'África',
    'dominico_extra':  'Dominico Extra',
    'dominico_primera':'Dominico Primera',
    'dominico_segunda':'Dominico Segunda',
    'guineo':          'Guineo',
    'harton_extra':    'Harton Extra',
    'harton_primera':  'Harton Primera',
    'harton_segunda':  'Harton Segunda',
    'murrapo_primera': 'Murrapo',
    'murrapo_segunda': 'Murrapo',
}

CAFE_MAP = {
    'pergamino_seco': 'Pergamino',
    'pasilla':        'Pasilla',
    'corriente':      'Corriente',
    'cereza':         'Cereza',
    'verde':          'Verde',
}


def populate_and_migrate(apps, schema_editor):
    TipoBanano = apps.get_model('produccion', 'TipoBanano')
    TipoCafe = apps.get_model('produccion', 'TipoCafe')
    VentaBanano = apps.get_model('produccion', 'VentaBanano')
    VentaCafe = apps.get_model('produccion', 'VentaCafe')

    # Crear tipos de banano del maestro
    for nombre in BANANO_NOMBRES:
        TipoBanano.objects.get_or_create(nombre=nombre)

    # Crear tipos de café del maestro
    for nombre in CAFE_NOMBRES:
        TipoCafe.objects.get_or_create(nombre=nombre)

    # Crear tipos de café adicionales si hay datos históricos con esos valores
    valores_cafe_existentes = set(
        VentaCafe.objects.values_list('tipo_cafe_old', flat=True).distinct()
    )
    for slug in valores_cafe_existentes:
        nombre = CAFE_MAP.get(slug, slug.replace('_', ' ').title())
        TipoCafe.objects.get_or_create(nombre=nombre)

    # Migrar registros de VentaBanano
    for venta in VentaBanano.objects.all():
        slug = venta.tipo_platano_old
        nombre = BANANO_MAP.get(slug, slug.replace('_', ' ').title())
        tipo, _ = TipoBanano.objects.get_or_create(nombre=nombre)
        venta.tipo_platano_id = tipo.id
        venta.save(update_fields=['tipo_platano_id'])

    # Migrar registros de VentaCafe
    for venta in VentaCafe.objects.all():
        slug = venta.tipo_cafe_old
        nombre = CAFE_MAP.get(slug, slug.replace('_', ' ').title())
        tipo, _ = TipoCafe.objects.get_or_create(nombre=nombre)
        venta.tipo_cafe_id = tipo.id
        venta.save(update_fields=['tipo_cafe_id'])


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0004_tipos_maestros_create'),
    ]

    operations = [
        migrations.RunPython(populate_and_migrate, reverse_noop),

        # Hacer las FKs no-nulas ahora que todos los registros tienen valor
        migrations.AlterField(
            model_name='ventabanano',
            name='tipo_platano',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to='produccion.tipobanano',
                verbose_name='Tipo',
            ),
        ),
        migrations.AlterField(
            model_name='ventacafe',
            name='tipo_cafe',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to='produccion.tipocafe',
                verbose_name='Tipo de café',
            ),
        ),

        # Eliminar los campos de texto viejos
        migrations.RemoveField(model_name='ventabanano', name='tipo_platano_old'),
        migrations.RemoveField(model_name='ventacafe', name='tipo_cafe_old'),
    ]
