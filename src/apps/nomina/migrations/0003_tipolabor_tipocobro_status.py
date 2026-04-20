from django.db import migrations, models


TIPOS_LABOR = [
    'Recolección', 'Guadaña', 'Abono', 'Arriero', 'Auxilio Labor',
    'Auxilio Transporte', 'Banano', 'Broca', 'Control plagas', 'Cosecha',
    'Deshojada', 'Deschuponar', 'Desbejucar', 'Embolsada', 'Varios',
    'Siembra', 'Permiso', 'Nómina', 'Contrato',
]

TIPOS_COBRO = ['Kilos', 'Jornal', 'Nómina', 'Contrato']


def populate_if_empty(apps, schema_editor):
    TipoLabor = apps.get_model('nomina', 'TipoLabor')
    TipoCobro = apps.get_model('nomina', 'TipoCobro')
    for nombre in TIPOS_LABOR:
        TipoLabor.objects.get_or_create(nombre=nombre)
    for nombre in TIPOS_COBRO:
        TipoCobro.objects.get_or_create(nombre=nombre)


class Migration(migrations.Migration):

    dependencies = [
        ('nomina', '0002_tipo_labor_cobro'),
    ]

    operations = [
        migrations.AddField(
            model_name='tipolabor',
            name='status',
            field=models.BooleanField(default=True, verbose_name='Estado'),
        ),
        migrations.AddField(
            model_name='tipocobro',
            name='status',
            field=models.BooleanField(default=True, verbose_name='Estado'),
        ),
        migrations.RunPython(populate_if_empty, migrations.RunPython.noop),
    ]
