from django.db import migrations


class Migration(migrations.Migration):
    """Remove Observacion state from finanzas. Table is now owned by produccion — no DB ops."""

    dependencies = [
        ('finanzas', '0007_cuenta_numero_cuenta_banco'),
        ('produccion', '0018_observacion_from_finanzas'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name='Observacion'),
            ],
            database_operations=[],
        ),
    ]
