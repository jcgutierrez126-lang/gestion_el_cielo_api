from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Elimina el tipo 'vale' del catálogo de cuentas y la categoría 'no_aplica' de egresos.
    El Pago Vale (retiro semanal del mayordomo) pasa a registrarse como Transacción
    (Bancolombia → Agencia), no como egreso.
    """

    dependencies = [
        ('finanzas', '0002_alter_egreso_categoria'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cuenta',
            name='tipo',
            field=models.CharField(
                choices=[
                    ('bancaria', 'Bancaria'),
                    ('efectivo', 'Efectivo'),
                    ('prestamo', 'Préstamo'),
                    ('agencia', 'Agencia / Cooperativa'),
                    ('dividendos', 'Dividendos'),
                ],
                max_length=20,
                verbose_name='Tipo',
            ),
        ),
        migrations.AlterField(
            model_name='egreso',
            name='categoria',
            field=models.CharField(
                choices=[
                    ('fertilizantes', 'Fertilizantes'),
                    ('herbicidas', 'Herbicidas'),
                    ('nomina', 'Nómina'),
                    ('seguridad_social', 'Seguridad Social'),
                    ('transporte', 'Transporte'),
                    ('viaticos', 'Viáticos'),
                    ('acueducto', 'Acueducto'),
                    ('epm', 'EPM'),
                    ('comsab', 'Comsab'),
                    ('mantenimientos', 'Mantenimientos'),
                    ('varios', 'Varios'),
                    ('beneficio', 'Beneficio'),
                    ('guadana', 'Guadaña'),
                    ('construcciones', 'Construcciones'),
                    ('impuestos', 'Impuestos'),
                    ('animales', 'Animales'),
                    ('siembra', 'Siembra'),
                    ('herramientas', 'Herramientas'),
                    ('broca', 'Broca'),
                    ('roya', 'Roya'),
                    ('moto', 'Moto'),
                    ('prestamo_empleados', 'Préstamo empleados'),
                    ('activos_fijos', 'Activos fijos'),
                    ('banano', 'Banano'),
                    ('compra_finca', 'Compra Finca'),
                    ('capacitaciones', 'Capacitaciones'),
                    ('venta_cafe', 'Venta Café'),
                ],
                db_index=True,
                max_length=50,
                verbose_name='Categoría',
            ),
        ),
    ]
