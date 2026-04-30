from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0008_lote_tipo_cultivo'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lote',
            name='gramos_abono_palo',
        ),
    ]
