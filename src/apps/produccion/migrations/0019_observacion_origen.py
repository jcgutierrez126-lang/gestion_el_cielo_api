from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0018_observacion_from_finanzas'),
    ]

    operations = [
        migrations.AddField(
            model_name='observacion',
            name='origen',
            field=models.CharField(
                choices=[('manual', 'Manual'), ('control_semanal', 'Control Semanal')],
                db_index=True, default='manual', max_length=30, verbose_name='Origen',
            ),
        ),
        migrations.AddField(
            model_name='observacion',
            name='control_semanal_id',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='ID Control Semanal'),
        ),
        migrations.AddField(
            model_name='observacion',
            name='semana_ref',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='Semana referencia'),
        ),
    ]
