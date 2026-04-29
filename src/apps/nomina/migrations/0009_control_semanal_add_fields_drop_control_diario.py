from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nomina', '0008_tipolabor_tipocobro_add_abreviatura'),
    ]

    operations = [
        # Agregar campos a ControlSemanal
        migrations.AddField(
            model_name='controlsemanal',
            name='semana_ref',
            field=models.CharField(blank=True, db_index=True, default='', max_length=150, verbose_name='Semana referencia'),
        ),
        migrations.AddField(
            model_name='controlsemanal',
            name='dia',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Día'),
        ),
        migrations.AddField(
            model_name='controlsemanal',
            name='fecha',
            field=models.DateField(blank=True, db_index=True, null=True, verbose_name='Fecha'),
        ),
        # Dar default a costo_unidad
        migrations.AlterField(
            model_name='controlsemanal',
            name='costo_unidad',
            field=models.DecimalField(decimal_places=5, default=0, max_digits=12, verbose_name='Costo x kilo / jornal'),
        ),
        # Agregar índice semana_ref
        migrations.AddIndex(
            model_name='controlsemanal',
            index=models.Index(fields=['semana_ref'], name='nomina_ctrl_semana__idx'),
        ),
        # Eliminar tabla ControlDiario
        migrations.DeleteModel(
            name='ControlDiario',
        ),
    ]
