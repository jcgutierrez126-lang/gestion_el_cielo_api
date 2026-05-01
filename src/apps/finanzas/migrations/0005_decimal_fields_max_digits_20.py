from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("finanzas", "0004_ciudad"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cuenta",
            name="saldo_inicial",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=20, verbose_name="Saldo inicial"),
        ),
        migrations.AlterField(
            model_name="egreso",
            name="cantidad",
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=20, null=True, verbose_name="Cantidad"),
        ),
        migrations.AlterField(
            model_name="egreso",
            name="valor",
            field=models.DecimalField(decimal_places=2, max_digits=20, verbose_name="Valor"),
        ),
        migrations.AlterField(
            model_name="egreso",
            name="abono_deuda",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=20, verbose_name="Abono a deuda"),
        ),
        migrations.AlterField(
            model_name="egreso",
            name="restante",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=20, verbose_name="Restante"),
        ),
        migrations.AlterField(
            model_name="ingreso",
            name="valor",
            field=models.DecimalField(decimal_places=2, max_digits=20, verbose_name="Valor"),
        ),
        migrations.AlterField(
            model_name="transaccion",
            name="valor",
            field=models.DecimalField(decimal_places=2, max_digits=20, verbose_name="Valor"),
        ),
    ]
