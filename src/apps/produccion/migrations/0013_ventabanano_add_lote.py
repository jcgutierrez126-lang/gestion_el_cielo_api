import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("produccion", "0012_decimal_fields_max_digits_20"),
    ]

    operations = [
        migrations.AddField(
            model_name="ventabanano",
            name="lote",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="ventas_banano",
                to="produccion.lote",
                verbose_name="Lote",
            ),
        ),
    ]
