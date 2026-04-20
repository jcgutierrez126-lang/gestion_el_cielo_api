from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ventabanano',
            name='tipo_platano',
            field=models.CharField(
                choices=[
                    ('banano_extra', 'Banano Extra'),
                    ('banano_primera', 'Banano Primera'),
                    ('banano_segunda', 'Banano Segunda'),
                    ('platano_extra', 'Plátano Extra x dedo'),
                    ('platano_segunda', 'Plátano Segunda x dedo'),
                    ('africa_extra', 'África Extra'),
                    ('africa_primera', 'África Primera'),
                    ('africa_segunda', 'África Segunda'),
                    ('dominico_extra', 'Dominico Extra'),
                    ('dominico_primera', 'Dominico Primera'),
                    ('dominico_segunda', 'Dominico Segunda'),
                    ('guineo', 'Guineo'),
                    ('harton_extra', 'Hartón Extra'),
                    ('harton_primera', 'Hartón Primera'),
                    ('harton_segunda', 'Hartón Segunda'),
                    ('murrapo_primera', 'Murrapo Primera'),
                    ('murrapo_segunda', 'Murrapo Segunda'),
                ],
                db_index=True,
                max_length=30,
                verbose_name='Tipo',
            ),
        ),
    ]
