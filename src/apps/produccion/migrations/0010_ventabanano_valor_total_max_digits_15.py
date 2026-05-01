from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("produccion", "0009_lote_remove_gramos_abono_palo"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ventabanano",
            name="valor_total",
            field=models.DecimalField(decimal_places=2, max_digits=15, verbose_name="Valor total"),
        ),
    ]
