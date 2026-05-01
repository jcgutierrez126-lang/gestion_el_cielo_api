import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("finanzas", "0005_decimal_fields_max_digits_20"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cuenta",
            name="tipo",
            field=models.CharField(
                choices=[
                    ("bancaria", "Bancaria"),
                    ("efectivo", "Efectivo"),
                    ("prestamo", "Préstamo"),
                    ("agencia", "Agencia / Cooperativa"),
                    ("dividendos", "Dividendos"),
                    ("inversion", "Inversión / CDT"),
                ],
                max_length=20,
                verbose_name="Tipo",
            ),
        ),
        migrations.CreateModel(
            name="InversionCDT",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("entidad", models.CharField(max_length=150, verbose_name="Entidad bancaria")),
                ("monto", models.DecimalField(decimal_places=2, max_digits=20, verbose_name="Monto invertido")),
                ("tasa_ea", models.DecimalField(decimal_places=4, max_digits=8, verbose_name="Tasa E.A. (%)")),
                ("fecha_inicio", models.DateField(verbose_name="Fecha inicio")),
                ("fecha_vencimiento", models.DateField(verbose_name="Fecha vencimiento")),
                ("estado", models.CharField(choices=[("activo", "Activo"), ("liquidado", "Liquidado"), ("renovado", "Renovado")], db_index=True, default="activo", max_length=20, verbose_name="Estado")),
                ("rendimiento_real", models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, verbose_name="Rendimiento real")),
                ("fecha_liquidacion", models.DateField(blank=True, null=True, verbose_name="Fecha liquidación")),
                ("observaciones", models.TextField(blank=True, null=True, verbose_name="Observaciones")),
                ("cuenta_origen", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="cdts", to="finanzas.cuenta", verbose_name="Cuenta origen")),
            ],
            options={"db_table": "inversiones_cdt", "verbose_name": "Inversión CDT", "verbose_name_plural": "Inversiones CDT", "ordering": ["-fecha_inicio"]},
        ),
    ]
