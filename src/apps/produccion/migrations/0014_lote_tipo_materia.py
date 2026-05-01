from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0013_ventabanano_add_lote'),
    ]

    operations = [
        migrations.AddField(
            model_name='lote',
            name='tipo_materia',
            field=models.CharField(
                blank=True, max_length=10, null=True,
                choices=[('cafe', 'Café'), ('banano', 'Banano')],
                verbose_name='Tipo de materia',
            ),
        ),
    ]
