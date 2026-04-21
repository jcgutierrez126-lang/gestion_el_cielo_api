from django.db import migrations

# Labores encontradas en el Excel (Vales 2025) que no estaban en el catálogo inicial
TIPOS_LABOR_NUEVOS = [
    'Arreglo Banano',
    'Beneficio',
    'Encalar',
    'Herbicida',
    'Incapacidad',
    'Machete',
    'Mantenimiento',
    'Platear',
    'Selección Café',
    'Siembra Banano',
    'Siembra Café',
    'Transporte',
]


def agregar_labores(apps, schema_editor):
    TipoLabor = apps.get_model('nomina', 'TipoLabor')
    for nombre in TIPOS_LABOR_NUEVOS:
        TipoLabor.objects.get_or_create(nombre=nombre)


class Migration(migrations.Migration):

    dependencies = [
        ('nomina', '0005_controldiario'),
    ]

    operations = [
        migrations.RunPython(agregar_labores, migrations.RunPython.noop),
    ]
