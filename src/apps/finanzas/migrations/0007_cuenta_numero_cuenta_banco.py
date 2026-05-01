from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finanzas', '0006_inversioncdt'),
    ]

    operations = [
        migrations.AddField(
            model_name='cuenta',
            name='numero_cuenta',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Número de cuenta'),
        ),
        migrations.AddField(
            model_name='cuenta',
            name='banco',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Banco / Entidad'),
        ),
    ]
