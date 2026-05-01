from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("nomina", "0009_control_semanal_add_fields_drop_control_diario"),
    ]

    operations = [
        migrations.AlterField(
            model_name="empleado",
            name="jornal",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, verbose_name="Jornal diario"),
        ),
        migrations.AlterField(
            model_name="empleado",
            name="salario_mensual",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, verbose_name="Salario mensual"),
        ),
        migrations.AlterField(
            model_name="empleado",
            name="salario_semanal",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, verbose_name="Salario semanal"),
        ),
        migrations.AlterField(
            model_name="controlsemanal",
            name="kilos",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, verbose_name="Kilos"),
        ),
        migrations.AlterField(
            model_name="controlsemanal",
            name="jornales",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, verbose_name="Jornales"),
        ),
        migrations.AlterField(
            model_name="controlsemanal",
            name="costo_unidad",
            field=models.DecimalField(decimal_places=5, default=0, max_digits=20, verbose_name="Costo x kilo / jornal"),
        ),
        migrations.AlterField(
            model_name="controlsemanal",
            name="valor",
            field=models.DecimalField(decimal_places=2, max_digits=20, verbose_name="Valor total"),
        ),
        migrations.AlterField(
            model_name="prestamoempleado",
            name="valor",
            field=models.DecimalField(decimal_places=2, max_digits=20, verbose_name="Valor"),
        ),
        migrations.AlterField(
            model_name="prestamoempleado",
            name="saldo",
            field=models.DecimalField(decimal_places=2, max_digits=20, verbose_name="Saldo pendiente"),
        ),
        migrations.AlterField(
            model_name="abonoprestamo",
            name="valor",
            field=models.DecimalField(decimal_places=2, max_digits=20, verbose_name="Valor"),
        ),
    ]
