from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0015_ventabanano_add_proveedor'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lote',
            name='nombre',
            field=models.CharField(max_length=100, verbose_name='Nombre del lote'),
        ),
    ]
