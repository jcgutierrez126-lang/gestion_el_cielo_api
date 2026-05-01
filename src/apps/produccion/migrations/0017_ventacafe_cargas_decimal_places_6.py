from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0016_lote_nombre_not_unique'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ventacafe',
            name='cargas',
            field=models.DecimalField(decimal_places=6, max_digits=20, verbose_name='Cargas'),
        ),
    ]
