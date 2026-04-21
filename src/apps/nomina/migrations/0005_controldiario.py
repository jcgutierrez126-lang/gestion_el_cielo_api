from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nomina', '0004_controlsemanal_lote_fk'),
    ]

    operations = [
        migrations.CreateModel(
            name='ControlDiario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.BooleanField(default=True)),
                ('semana_ref', models.CharField(blank=True, default='', max_length=150, verbose_name='Semana referencia')),
                ('fecha', models.DateField(db_index=True, verbose_name='Fecha')),
                ('dia', models.CharField(blank=True, default='', max_length=20, verbose_name='Día')),
                ('nombre', models.CharField(max_length=200, verbose_name='Nombre trabajador')),
                ('lote', models.CharField(blank=True, default='', max_length=100, verbose_name='Lote')),
                ('labor', models.CharField(max_length=150, verbose_name='Labor')),
                ('cantidad', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Cantidad/Kilos')),
                ('tipo_cobro', models.CharField(blank=True, default='', max_length=50, verbose_name='Tipo cobro')),
                ('valor', models.DecimalField(blank=True, decimal_places=0, max_digits=12, null=True, verbose_name='Valor')),
            ],
            options={
                'verbose_name': 'Control Diario',
                'verbose_name_plural': 'Control Diario',
                'db_table': 'control_diario',
                'ordering': ['-fecha', 'nombre'],
            },
        ),
    ]
