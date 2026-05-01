from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("produccion", "0010_ventabanano_valor_total_max_digits_15"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ventacafe",
            name="valor_total",
            field=models.DecimalField(decimal_places=2, max_digits=20, verbose_name="Valor total"),
        ),
        migrations.AlterField(
            model_name="ventacafe",
            name="deduccion",
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=20, null=True, verbose_name="Deducción"),
        ),
        migrations.AlterField(
            model_name="ventacafe",
            name="retefuente",
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=20, null=True, verbose_name="Retefuente"),
        ),
        migrations.AlterField(
            model_name="ventacafe",
            name="valor_neto",
            field=models.DecimalField(decimal_places=2, max_digits=20, verbose_name="Valor neto"),
        ),
        migrations.AlterField(
            model_name="ventabanano",
            name="valor_total",
            field=models.DecimalField(decimal_places=2, max_digits=20, verbose_name="Valor total"),
        ),
    ]
