from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('finanzas', '0007_cuenta_numero_cuenta_banco'),
        ('produccion', '0014_lote_tipo_materia'),
    ]

    operations = [
        migrations.AddField(
            model_name='ventabanano',
            name='proveedor',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='ventas_banano',
                to='finanzas.proveedor',
                verbose_name='Proveedor / Cooperativa',
            ),
        ),
    ]
