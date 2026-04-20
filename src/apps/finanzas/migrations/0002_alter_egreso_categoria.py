from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finanzas', '0001_initial'),
    ]

    operations = [
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
                    ('no_aplica', 'No aplica'),
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
