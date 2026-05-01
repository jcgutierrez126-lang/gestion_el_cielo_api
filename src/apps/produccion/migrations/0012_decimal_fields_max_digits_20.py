from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("produccion", "0011_decimal_fields_max_digits_20"),
    ]

    operations = [
        migrations.AlterField(
            model_name="lote",
            name="bultos_produccion",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, verbose_name="Bultos producción"),
        ),
        migrations.AlterField(
            model_name="lote",
            name="bultos_urea",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, verbose_name="Bultos urea"),
        ),
        migrations.AlterField(
            model_name="lote",
            name="bultos_dap",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, verbose_name="Bultos DAP"),
        ),
        migrations.AlterField(
            model_name="ventacafe",
            name="kilos",
            field=models.DecimalField(decimal_places=2, max_digits=20, verbose_name="Kilos"),
        ),
        migrations.AlterField(
            model_name="ventacafe",
            name="cargas",
            field=models.DecimalField(decimal_places=3, max_digits=20, verbose_name="Cargas"),
        ),
        migrations.AlterField(
            model_name="ventacafe",
            name="factor",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, verbose_name="Factor"),
        ),
        migrations.AlterField(
            model_name="ventacafe",
            name="precio_kilo",
            field=models.DecimalField(decimal_places=2, max_digits=20, verbose_name="Precio x kilo"),
        ),
        migrations.AlterField(
            model_name="ventacafe",
            name="precio_carga",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, verbose_name="Precio x carga"),
        ),
        migrations.AlterField(
            model_name="ventacafe",
            name="conversion_cereza_seco",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, verbose_name="Conversión cereza/seco"),
        ),
        migrations.AlterField(
            model_name="ventacafe",
            name="valor_transporte",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, verbose_name="Valor transporte"),
        ),
        migrations.AlterField(
            model_name="ventacafetostado",
            name="valor",
            field=models.DecimalField(decimal_places=2, max_digits=20, verbose_name="Valor"),
        ),
        migrations.AlterField(
            model_name="mezclaabono",
            name="gramos_por_arbol",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, verbose_name="Gramos por árbol"),
        ),
        migrations.AlterField(
            model_name="mezclaabono",
            name="costo_total",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, verbose_name="Costo total"),
        ),
        migrations.AlterField(
            model_name="mezclaabonofertilizante",
            name="num_bultos",
            field=models.DecimalField(decimal_places=2, max_digits=20, verbose_name="Número de bultos"),
        ),
        migrations.AlterField(
            model_name="mezclaabonofertilizante",
            name="precio_bulto",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, verbose_name="Precio x bulto"),
        ),
        migrations.AlterField(
            model_name="ventabanano",
            name="kilos",
            field=models.DecimalField(decimal_places=2, max_digits=20, verbose_name="Kilos"),
        ),
        migrations.AlterField(
            model_name="ventabanano",
            name="precio_kilo",
            field=models.DecimalField(decimal_places=2, max_digits=20, verbose_name="Precio x kilo"),
        ),
    ]
