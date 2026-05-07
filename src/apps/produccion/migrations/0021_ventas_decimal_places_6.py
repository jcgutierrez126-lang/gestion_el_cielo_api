from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0020_drop_ventas_cafe_tostado'),
    ]

    operations = [
        # VentaCafe
        migrations.AlterField(
            model_name='ventacafe',
            name='kilos',
            field=models.DecimalField(max_digits=20, decimal_places=6, verbose_name='Kilos'),
        ),
        migrations.AlterField(
            model_name='ventacafe',
            name='factor',
            field=models.DecimalField(max_digits=20, decimal_places=6, blank=True, null=True, verbose_name='Factor'),
        ),
        migrations.AlterField(
            model_name='ventacafe',
            name='precio_kilo',
            field=models.DecimalField(max_digits=20, decimal_places=6, verbose_name='Precio x kilo'),
        ),
        migrations.AlterField(
            model_name='ventacafe',
            name='precio_carga',
            field=models.DecimalField(max_digits=20, decimal_places=6, blank=True, null=True, verbose_name='Precio x carga'),
        ),
        migrations.AlterField(
            model_name='ventacafe',
            name='valor_total',
            field=models.DecimalField(max_digits=20, decimal_places=6, verbose_name='Valor total'),
        ),
        migrations.AlterField(
            model_name='ventacafe',
            name='deduccion',
            field=models.DecimalField(max_digits=20, decimal_places=6, default=0, blank=True, null=True, verbose_name='Deducción'),
        ),
        migrations.AlterField(
            model_name='ventacafe',
            name='retefuente',
            field=models.DecimalField(max_digits=20, decimal_places=6, default=0, blank=True, null=True, verbose_name='Retefuente'),
        ),
        migrations.AlterField(
            model_name='ventacafe',
            name='valor_neto',
            field=models.DecimalField(max_digits=20, decimal_places=6, verbose_name='Valor neto'),
        ),
        migrations.AlterField(
            model_name='ventacafe',
            name='conversion_cereza_seco',
            field=models.DecimalField(max_digits=20, decimal_places=6, blank=True, null=True, verbose_name='Conversión cereza/seco'),
        ),
        migrations.AlterField(
            model_name='ventacafe',
            name='valor_transporte',
            field=models.DecimalField(max_digits=20, decimal_places=6, blank=True, null=True, verbose_name='Valor transporte'),
        ),
        # VentaBanano
        migrations.AlterField(
            model_name='ventabanano',
            name='kilos',
            field=models.DecimalField(max_digits=20, decimal_places=6, verbose_name='Kilos'),
        ),
        migrations.AlterField(
            model_name='ventabanano',
            name='precio_kilo',
            field=models.DecimalField(max_digits=20, decimal_places=6, verbose_name='Precio x kilo'),
        ),
        migrations.AlterField(
            model_name='ventabanano',
            name='valor_total',
            field=models.DecimalField(max_digits=20, decimal_places=6, verbose_name='Valor total'),
        ),
    ]
