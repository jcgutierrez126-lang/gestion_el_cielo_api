from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0007_variedadlote'),
    ]

    operations = [
        migrations.AddField(
            model_name='lote',
            name='tipo_cultivo',
            field=models.CharField(
                blank=True, null=True, max_length=10,
                choices=[
                    ('siembra', 'Siembra'),
                    ('zoca_1', 'Zoca 1'),
                    ('zoca_2', 'Zoca 2'),
                    ('zoca_3', 'Zoca 3'),
                ],
                verbose_name='Tipo de cultivo',
            ),
        ),
    ]
